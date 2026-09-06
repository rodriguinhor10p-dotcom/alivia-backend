"""ALÍVIA™ — Comandos gerais do bot (/start, /help)."""

from telegram import Update
from telegram.ext import ContextTypes
from firebase_admin import firestore
from core import db


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario_id = str(update.effective_user.id)
    nome = update.effective_user.first_name

    db.collection("usuarios_alivia").document(usuario_id).set({
        "uid": usuario_id,
        "nome": nome,
        "canal": "telegram",
        "fase_atual": 1,
        "timestamp_primeiro_contato": firestore.SERVER_TIMESTAMP,
        "ativo": True,
    }, merge=True)

    await update.message.reply_text(
        f"Oi {nome}! Sou a ALÍVIA, sua guardiã digital.\n\n"
        f"Você recebeu alguma mensagem estranha nos últimos dias?"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Eu te ajudo a identificar golpes digitais e proteger sua vida online.\n"
        "Manda /start pra começar, ou só conta o que aconteceu."
    )
