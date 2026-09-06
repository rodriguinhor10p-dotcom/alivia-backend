"""ALÍVIA™ — Webhook do Telegram."""

from telegram import Update
from core import tg_app


async def handle_webhook_telegram(update: dict):
    await tg_app.process_update(Update.de_json(update, tg_app.bot))
    return {"ok": True}
