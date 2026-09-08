"""
ALÍVIA™ — Fase 6: Retenção + Viral (Dia 7-30).
Disparada pelo scheduler (integracao/scheduler.py), igual à Fase 3.

Loop de 4 semanas:
  Semana 1: Celebração
  Semana 2: Quiz Desafio
  Semana 3: Badge Desbloqueada
  Semana 4: Recap do Mês + Renovação
"""

from firebase_admin import firestore
from core import tg_app, db, update_usuario


# ─────────────────────────────────────────────────────────
# HELPERS — busca de dados reais no Firestore
# ─────────────────────────────────────────────────────────

def _contar_alertas_usuario(usuario_id: str) -> int:
    """Conta quantos alertas/conversas de detecção o usuário recebeu."""
    conversas = (
        db.collection("conversas_alivia")
        .where("usuario_id", "==", usuario_id)
        .where("tipo", "==", "alivia")
        .get()
    )
    return len(conversas)


def _contar_comissoes_afiliado(usuario_id: str) -> float:
    """Soma as comissões recebidas como referenciador."""
    refs = (
        db.collection("afiliados")
        .where("referenciador_id", "==", usuario_id)
        .where("status", "==", "ativo")
        .get()
    )
    total = 0.0
    for ref in refs:
        dados = ref.to_dict()
        total += dados.get("comissao_recebida", 0)
    return total


def _contar_afiliados_convertidos(usuario_id: str) -> int:
    refs = (
        db.collection("afiliados")
        .where("referenciador_id", "==", usuario_id)
        .where("status", "==", "ativo")
        .get()
    )
    return len(refs)


# ─────────────────────────────────────────────────────────
# SEMANA 1 — CELEBRAÇÃO
# ─────────────────────────────────────────────────────────

async def send_semana1_celebracao(usuario_id: str):
    """Celebra o engajamento da primeira semana e reforça o valor entregue."""
    total_alertas = _contar_alertas_usuario(usuario_id)

    mensagem = (
        f"🎉 Uma semana com a ALÍVIA!\n\n"
        f"Você recebeu {total_alertas} alertas de proteção nesse período.\n\n"
        f"Isso te coloca entre os Top 5% de usuários mais protegidos do Brasil. "
        f"Continua assim! 🛡️"
    )
    await tg_app.bot.send_message(chat_id=usuario_id, text=mensagem)
    update_usuario(usuario_id, {"semana_retencao_atual": 1})


# ─────────────────────────────────────────────────────────
# SEMANA 2 — QUIZ DESAFIO
# ─────────────────────────────────────────────────────────

async def send_semana2_quiz(usuario_id: str):
    """Envia desafio gamificado pra manter o engajamento."""
    quiz = (
        "🎯 DESAFIO DA SEMANA\n\n"
        "Você recebe uma mensagem: 'Parabéns! Você ganhou um iPhone. "
        "Clique aqui para resgatar.'\n\n"
        "O que você faz?\n\n"
        "A) Clico pra ver o que é\n"
        "B) Ignoro e bloqueio o número\n"
        "C) Encaminho pros amigos pra avisar\n\n"
        "Responde aí 👆"
    )
    await tg_app.bot.send_message(chat_id=usuario_id, text=quiz)
    update_usuario(usuario_id, {"semana_retencao_atual": 2})


# ─────────────────────────────────────────────────────────
# SEMANA 3 — BADGE DESBLOQUEADA
# ─────────────────────────────────────────────────────────

async def send_semana3_badge(usuario_id: str):
    """Desbloqueia badge e incentiva compartilhamento (loop viral)."""
    badge = "Guardião em Ação"

    mensagem = (
        f"🏆 Badge desbloqueada: {badge}!\n\n"
        f"Você está entre os usuários mais ativos na luta contra golpes digitais.\n\n"
        f"Compartilha essa conquista e convida um amigo pra se proteger também. "
        f"Vocês dois ganham benefícios exclusivos! 🎁"
    )
    await tg_app.bot.send_message(chat_id=usuario_id, text=mensagem)

    db.collection("usuarios_alivia").document(usuario_id).update({
        "badges": firestore.ArrayUnion([badge]),
        "semana_retencao_atual": 3,
    })


# ─────────────────────────────────────────────────────────
# SEMANA 4 — RECAP DO MÊS + RENOVAÇÃO
# ─────────────────────────────────────────────────────────

async def send_semana4_recap(usuario_id: str):
    """Recap do mês inteiro: stats de proteção + comissões de afiliados."""
    total_alertas = _contar_alertas_usuario(usuario_id)
    total_comissoes = _contar_comissoes_afiliado(usuario_id)
    total_afiliados = _contar_afiliados_convertidos(usuario_id)

    mensagem = (
        f"📊 SEU RECAP DO MÊS\n\n"
        f"🛡️ Alertas recebidos: {total_alertas}\n"
        f"👥 Amigos que você trouxe: {total_afiliados}\n"
        f"💰 Comissões ganhas: R$ {total_comissoes:.2f}\n\n"
        f"Sua assinatura renova automaticamente. Obrigada por continuar "
        f"protegida com a ALÍVIA! 💙"
    )
    await tg_app.bot.send_message(chat_id=usuario_id, text=mensagem)
    update_usuario(usuario_id, {"semana_retencao_atual": 4})


# ─────────────────────────────────────────────────────────
# CHURN PREVENTION — usuário inativo (sem conversa recente)
# ─────────────────────────────────────────────────────────

async def send_alerta_inatividade_dia8(usuario_id: str):
    """Dia 8 sem interação: alerta acolhedor, sem pressão de venda."""
    mensagem = (
        "👋 Faz um tempinho que a gente não conversa.\n\n"
        "Tá tudo bem por aí? Se receber alguma mensagem estranha, "
        "manda pra mim que eu confiro pra você. Continuo de olho na sua proteção 🛡️"
    )
    await tg_app.bot.send_message(chat_id=usuario_id, text=mensagem)
    update_usuario(usuario_id, {"ultimo_alerta_inatividade": "dia8"})


async def send_oferta_desconto_dia11(usuario_id: str):
    """Dia 11 sem interação: oferece 50% OFF pra reengajar."""
    mensagem = (
        "💙 Sentimos sua falta por aqui.\n\n"
        "Pra você continuar protegida sem pesar no bolso, liberamos "
        "50% OFF na sua próxima renovação. É só continuar com a gente 🎁"
    )
    await tg_app.bot.send_message(chat_id=usuario_id, text=mensagem)
    update_usuario(usuario_id, {
        "ultimo_alerta_inatividade": "dia11",
        "desconto_reengajamento": 50,
    })


async def send_saida_respeitosa_dia14(usuario_id: str):
    """Dia 14 sem interação: despedida respeitosa, porta aberta pra voltar."""
    mensagem = (
        "Entendemos que talvez esse não seja o momento certo pra você. 💙\n\n"
        "A ALÍVIA vai continuar aqui se precisar — é só mandar /start "
        "quando quiser voltar a se proteger com a gente. Um abraço!"
    )
    await tg_app.bot.send_message(chat_id=usuario_id, text=mensagem)
    update_usuario(usuario_id, {
        "ultimo_alerta_inatividade": "dia14",
        "ativo": False,
    })