"""ALÍVIA™ — Webhook do Mercado Pago."""

from handlers.fase5 import processar_webhook_mp


async def handle_webhook_mercadopago(payload: dict):
    return await processar_webhook_mp(payload)
