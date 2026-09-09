"""
ALÍVIA™ — Programa de Afiliados
Gera links de indicação, registra conversões e calcula comissões (25%
do valor da primeira mensalidade/plano) quando um usuário indicado
completa o pagamento na Fase 5.
"""

import os
import logging
from datetime import datetime

from core import db, get_usuario

logger = logging.getLogger(__name__)

BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "alivia_guardiadigital_bot")
PERCENTUAL_COMISSAO = 0.25


# ─────────────────────────────────────────────────────────
# LINK DE INDICAÇÃO
# ─────────────────────────────────────────────────────────

def gerar_link_indicacao(usuario_id: str) -> str:
    """Monta o link de deep-link do Telegram pro usuário compartilhar."""
    return f"https://t.me/{BOT_USERNAME}?start=REF_{usuario_id}"


# ─────────────────────────────────────────────────────────
# REGISTRO DE CONVERSÃO
# ─────────────────────────────────────────────────────────

async def registrar_conversao_afiliado(referenciado_id: str, valor_pago: float):
    """
    Chamada pelo webhook do Mercado Pago (fase5.py) depois de um pagamento
    aprovado. Se o usuário que pagou veio de uma indicação, cria o registro
    em 'afiliados' com a comissão (25% do valor pago) e retorna os dados
    pra quem chamou decidir se notifica o referenciador.
    Retorna None se o usuário não veio de indicação nenhuma.
    """
    usuario_doc = get_usuario(referenciado_id)
    dados = usuario_doc.to_dict() or {}
    referenciador_id = dados.get("referenciado_por")

    if not referenciador_id:
        return None

    comissao = round(valor_pago * PERCENTUAL_COMISSAO, 2)

    afiliado_data = {
        "referenciador_id": referenciador_id,
        "referenciado_id": referenciado_id,
        "status": "ativo",
        "comissao_recebida": comissao,
        "timestamp": datetime.now(),
    }

    try:
        doc_id = f"{referenciador_id}_{referenciado_id}"
        db.collection("afiliados").document(doc_id).set(afiliado_data, merge=True)
        logger.info(
            f"💰 Comissão registrada: {referenciador_id} ganhou R${comissao:.2f} "
            f"pela indicação de {referenciado_id}"
        )
        return afiliado_data
    except Exception as e:
        logger.error(f"Erro ao registrar conversão de afiliado: {str(e)}")
        return None


# ─────────────────────────────────────────────────────────
# NOTIFICAÇÃO AO REFERENCIADOR (Trigger 4 — FOMO)
# ─────────────────────────────────────────────────────────

async def notificar_referenciador(referenciador_id: str, comissao: float):
    """Avisa o referenciador que a indicação converteu e ele ganhou comissão."""
    from core import tg_app  # import tardio evita ciclo com main.py

    texto = (
        "🎉 Boa notícia! Um amigo que você indicou acabou de assinar a ALÍVIA.\n\n"
        f"Você ganhou R${comissao:.2f} de comissão 💰\n\n"
        "Continue convidando pra ganhar ainda mais — manda /convidar pra pegar "
        "seu link de novo quando quiser."
    )

    try:
        await tg_app.bot.send_message(chat_id=referenciador_id, text=texto)
    except Exception as e:
        logger.error(f"Erro ao notificar referenciador {referenciador_id}: {str(e)}")