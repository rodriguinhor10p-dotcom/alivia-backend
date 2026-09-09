"""
ALÍVIA™ — main.py
Entrypoint: dispatcher de mensagens + rotas FastAPI + startup.
Toda a lógica de negócio vive em handlers/, integracao/ e webhooks/.
"""

import os
from fastapi import FastAPI, HTTPException, Header
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes

from core import tg_app, get_usuario, log_conversa
from handlers.comandos import start_command, help_command, convidar_command
from handlers.fase1 import handle_fase1
from handlers.fase2 import handle_fase2
from handlers.fase4 import handle_fase4
from handlers.fase5 import registrar_handlers_fase5, apresentar_oferta
from integracao.scheduler import iniciar_scheduler
from integracao.coleta_publica import executar_coleta_completa
from integracao.coleta_reclameaqui import coleta_reclameaqui_completa
from webhooks.telegram_webhook import handle_webhook_telegram
from webhooks.mercadopago_webhook import handle_webhook_mercadopago

app = FastAPI(title="ALÍVIA™ Backend")

ADMIN_SECRET = os.getenv("ADMIN_SECRET", "")


# ─────────────────────────────────────────────────────────
# DISPATCHER ÚNICO DE MENSAGENS
# ─────────────────────────────────────────────────────────

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario_id = str(update.effective_user.id)
    texto = update.message.text

    usuario_doc = get_usuario(usuario_id)
    if not usuario_doc.exists:
        await update.message.reply_text("Manda /start pra começarmos 🙂")
        return

    dados = usuario_doc.to_dict()
    fase = dados.get("fase_atual", 1) if dados else 1
    resposta = None

    if fase == 1:
        resposta = await handle_fase1(usuario_id, texto)
    elif fase == 2:
        resposta = await handle_fase2(usuario_id, texto, usuario_doc)
    elif fase == 4:
        resposta = await handle_fase4(usuario_id, texto, usuario_doc, context.bot)
    # fase 3 é dirigida pelo scheduler (integracao/scheduler.py)
    # fase 5 é dirigida pelos botões (CallbackQueryHandler em handlers/fase5.py)
    # fase 6 (retenção) entra num próximo módulo: handlers/fase6.py

    if resposta:
        await update.message.reply_text(resposta)
        log_conversa(usuario_id, "alivia", resposta, fase)


# ─────────────────────────────────────────────────────────
# ROTAS FASTAPI
# ─────────────────────────────────────────────────────────

@app.post("/webhook/telegram")
async def webhook_telegram(update: dict):
    return await handle_webhook_telegram(update)


@app.post("/webhook/mercadopago")
async def webhook_mercadopago(payload: dict):
    return await handle_webhook_mercadopago(payload)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ALÍVIA™"}


# ─────────────────────────────────────────────────────────
# ROTA TEMPORÁRIA DE TESTE — remover depois de validar Fase 5
# ─────────────────────────────────────────────────────────

@app.get("/admin/test-fase5")
async def test_fase5(usuario_id: str, score: int = 85):
    await apresentar_oferta(usuario_id, score, tg_app.bot)
    return {"ok": True}


# ─────────────────────────────────────────────────────────
# ROTA TEMPORÁRIA DE TESTE — remover depois de validar Coleta Pública
# ─────────────────────────────────────────────────────────

@app.get("/admin/test-coleta")
async def test_coleta(x_admin_key: str = Header(None)):
    if not ADMIN_SECRET or x_admin_key != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Não autorizado")

    resumo = await executar_coleta_completa()
    return {"ok": True, "resumo": resumo}


# ─────────────────────────────────────────────────────────
# ROTA TEMPORÁRIA DE TESTE — remover depois de validar Reclame Aqui
# ─────────────────────────────────────────────────────────

@app.get("/admin/test-reclameaqui")
async def test_reclameaqui(x_admin_key: str = Header(None), limite_empresas: int = 5):
    if not ADMIN_SECRET or x_admin_key != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Não autorizado")

    novos = await coleta_reclameaqui_completa(limite_empresas=limite_empresas)
    return {"ok": True, "novos_registros": novos}


# ─────────────────────────────────────────────────────────
# STARTUP
# ─────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    print("🚀 ALÍVIA™ iniciando...")

    tg_app.add_handler(CommandHandler("start", start_command))
    tg_app.add_handler(CommandHandler("help", help_command))
    tg_app.add_handler(CommandHandler("convidar", convidar_command))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    registrar_handlers_fase5(tg_app)

    await tg_app.initialize()
    iniciar_scheduler()

    print("✅ ALÍVIA™ pronta — Fases 1-5 ativas")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)