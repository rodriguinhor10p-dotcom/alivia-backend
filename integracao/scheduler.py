"""ALÍVIA™ — Scheduler de mensagens automáticas (Fase 3 + Fase 6) + Coleta Pública."""

import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from core import db, update_usuario
from handlers.fase3 import send_dica_dia1, send_quiz_dia3, send_dica_dia2
from handlers.fase6 import (
    send_semana1_celebracao,
    send_semana2_quiz,
    send_semana3_badge,
    send_semana4_recap,
    send_alerta_inatividade_dia8,
    send_oferta_desconto_dia11,
    send_saida_respeitosa_dia14,
)
from integracao.coleta_publica import (
    executar_coleta_completa,
    atualizar_mapa_risco,
    gerar_boletim_diario,
)

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def scheduled_education():
    """Job a cada 6h: checa quem está na Fase 3 e manda a mensagem certa pro dia."""
    users = db.collection("usuarios_alivia").where("fase_atual", "==", 3).stream()

    for user in users:
        entrada = user.get("data_entrada_fase3")
        if not entrada:
            continue
        dias = (datetime.now() - entrada).days

        if dias == 1:
            asyncio.run(send_dica_dia1(user.id))
        elif dias == 3:
            asyncio.run(send_quiz_dia3(user.id))
        elif dias == 7:
            asyncio.run(send_dica_dia2(user.id))
            update_usuario(user.id, {"fase_atual": 4})


def scheduled_retencao_fase6():
    """
    Job a cada 6h: checa quem está na Fase 6 (convertido/pagante) e dispara
    o loop de retenção de 4 semanas com base em data_entrada_fase6.
    """
    users = db.collection("usuarios_alivia").where("fase_atual", "==", 6).stream()

    for user in users:
        entrada = user.get("data_entrada_fase6")
        if not entrada:
            continue
        dias = (datetime.now() - entrada).days

        if dias == 7:
            asyncio.run(send_semana1_celebracao(user.id))
        elif dias == 14:
            asyncio.run(send_semana2_quiz(user.id))
        elif dias == 21:
            asyncio.run(send_semana3_badge(user.id))
        elif dias == 28:
            asyncio.run(send_semana4_recap(user.id))


def scheduled_churn_prevention():
    """
    Job a cada 6h: checa usuários ativos sem interação recente
    (data_ultima_conversa) e dispara o fluxo de churn prevention.
    """
    users = db.collection("usuarios_alivia").where("ativo", "==", True).stream()

    for user in users:
        ultima_conversa = user.get("data_ultima_conversa")
        if not ultima_conversa:
            continue
        dias_inativo = (datetime.now() - ultima_conversa).days

        if dias_inativo == 8:
            asyncio.run(send_alerta_inatividade_dia8(user.id))
        elif dias_inativo == 11:
            asyncio.run(send_oferta_desconto_dia11(user.id))
        elif dias_inativo == 14:
            asyncio.run(send_saida_respeitosa_dia14(user.id))


def scheduled_coleta_publica():
    """
    Job a cada 6h: executa coleta completa (RSS + API + Scraping)
    e em seguida atualiza o Mapa de Risco com os novos dados.
    """
    logger.info("⏰ Scheduler: iniciando ciclo de coleta pública (6h)")

    async def _run():
        await executar_coleta_completa()
        await atualizar_mapa_risco()

    try:
        asyncio.run(_run())
    except Exception as e:
        logger.error(f"❌ Erro no job de coleta pública: {str(e)}")


def scheduled_boletim_diario():
    """Job 1x/dia (6 AM): gera o Boletim Diário com top 10 alertas."""
    logger.info("⏰ Scheduler: gerando boletim diário")

    try:
        asyncio.run(gerar_boletim_diario())
    except Exception as e:
        logger.error(f"❌ Erro no job de boletim diário: {str(e)}")


def iniciar_scheduler():
    # Fase 3 — educação/gamificação
    scheduler.add_job(scheduled_education, "interval", hours=6)

    # Fase 6 — retenção (loop 4 semanas) + churn prevention
    scheduler.add_job(scheduled_retencao_fase6, "interval", hours=6)
    scheduler.add_job(scheduled_churn_prevention, "interval", hours=6)

    # Coleta Pública — 17 portais (RSS agora, API/Scraping depois)
    scheduler.add_job(scheduled_coleta_publica, "interval", hours=6)

    # Boletim Diário — 6h da manhã, todo dia
    scheduler.add_job(scheduled_boletim_diario, "cron", hour=6, minute=0)

    scheduler.start()
    logger.info(
        "✅ Scheduler iniciado: educação (6h) + retenção fase6 (6h) + "
        "churn prevention (6h) + coleta pública (6h) + boletim (diário 6h)"
    )