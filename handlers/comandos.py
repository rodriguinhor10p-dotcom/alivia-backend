"""ALÍVIA™ — Comandos gerais do bot (/start, /help, /convidar)."""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from firebase_admin import firestore
from core import db
from integracao.afiliados import gerar_link_indicacao

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario_id = str(update.effective_user.id)
    nome = update.effective_user.first_name

    doc_ref = db.collection("usuarios_alivia").document(usuario_id)
    usuario_existente = doc_ref.get()

    dados_usuario = {
        "uid": usuario_id,
        "nome": nome,
        "canal": "telegram",
        "fase_atual": 1,
        "timestamp_primeiro_contato": firestore.SERVER_TIMESTAMP,
        "ativo": True,
    }

    # ── Captura de indicação (link de afiliado) ──
    # Só grava referenciado_por na PRIMEIRA vez que o usuário aparece,
    # pra não sobrescrever em /start repetidos.
    if not usuario_existente.exists and context.args:
        payload = context.args[0]
        if payload.startswith("REF_"):
            referenciador_id = payload.replace("REF_", "")
            if referenciador_id and referenciador_id != usuario_id:
                dados_usuario["referenciado_por"] = referenciador_id
                logger.info(f"📌 Novo usuário {usuario_id} veio via indicação de {referenciador_id}")

    doc_ref.set(dados_usuario, merge=True)

    await update.message.reply_text(
        f"Oi {nome}! Sou a ALÍVIA, sua guardiã digital.\n\n"
        f"Você recebeu alguma mensagem estranha nos últimos dias?"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Eu te ajudo a identificar golpes digitais e proteger sua vida online.\n"
        "Manda /start pra começar, ou só conta o que aconteceu."
    )


async def convidar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gera e envia o link de indicação pro usuário compartilhar."""
    usuario_id = str(update.effective_user.id)
    link = gerar_link_indicacao(usuario_id)

    texto = (
        "🎁 Convide seus amigos pra se protegerem também!\n\n"
        "Compartilhe seu link:\n"
        f"{link}\n\n"
        "Quando um amigo assinar a ALÍVIA através dele, você ganha "
        "25% de comissão sobre a primeira mensalidade dele 💰"
    )
    await update.message.reply_text(texto)