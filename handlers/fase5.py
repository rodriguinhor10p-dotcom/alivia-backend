"""
ALÍVIA™ — Fase 5: Conversão
Oferta natural pós-checkup + pagamento via Mercado Pago (PIX / Cartão)
"""

import os
import base64
import io
from datetime import datetime, timedelta

import mercadopago
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from firebase_admin import firestore

from core import db, update_usuario, get_usuario

MP_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

PLANOS = {
    "mensal": {"nome": "ALÍVIA Proteção Mensal", "preco": 7.90, "dias": 30},
    "anual": {"nome": "ALÍVIA Proteção Anual", "preco": 79.00, "dias": 365},
}


# ─────────────────────────────────────────────────────────
# 1. OFERTA NATURAL
# ─────────────────────────────────────────────────────────

async def apresentar_oferta(usuario_id: str, score: int, bot):
    usuario_doc = get_usuario(usuario_id)
    dados = usuario_doc.to_dict() or {}
    nome = dados.get("nome") or ""

    texto = (
        f"{nome}, com {score}% de segurança, você já está à frente da maioria — "
        f"mas os pontos fracos que apareceram no seu checkup são exatamente os que "
        f"os golpistas mais exploram hoje em dia.\n\n"
        f"A ALÍVIA Proteção Completa monitora isso pra você 24h por dia:\n"
        f"✅ Alertas de golpes na sua região em tempo real\n"
        f"✅ Checkup mensal automático\n"
        f"✅ Suporte direto quando cair em algo suspeito\n\n"
        f"Por R$7,90/mês. Cancela quando quiser."
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Quero proteção — Mensal R$7,90", callback_data="plano_mensal")],
        [InlineKeyboardButton("Anual R$79,00 (economize 17%)", callback_data="plano_anual")],
        [InlineKeyboardButton("Agora não", callback_data="plano_recusar")],
    ])

    await bot.send_message(chat_id=usuario_id, text=texto, reply_markup=keyboard)

    update_usuario(usuario_id, {
        "fase_atual": 5,
        "oferta_apresentada_em": firestore.SERVER_TIMESTAMP,
    })


# ─────────────────────────────────────────────────────────
# 2. ESCOLHA DE PLANO
# ─────────────────────────────────────────────────────────

async def callback_escolha_plano(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    usuario_id = str(query.from_user.id)

    if query.data == "plano_recusar":
        await query.edit_message_text(
            "Sem problema! Vou continuar te avisando sobre golpes por aqui de graça. "
            "Se mudar de ideia, é só mandar 'quero proteção' 🙂"
        )
        update_usuario(usuario_id, {"fase_atual": 3})
        return

    plano_id = query.data.replace("plano_", "")
    plano = PLANOS[plano_id]
    update_usuario(usuario_id, {"plano_escolhido": plano_id})

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("PIX (aprovação na hora)", callback_data=f"pag_pix_{plano_id}")],
        [InlineKeyboardButton("Cartão de crédito", callback_data=f"pag_cartao_{plano_id}")],
    ])

    await query.edit_message_text(
        f"Fechado: {plano['nome']} — R${plano['preco']:.2f}\n\nComo prefere pagar?",
        reply_markup=keyboard,
    )


# ─────────────────────────────────────────────────────────
# 3a. PAGAMENTO PIX
# ─────────────────────────────────────────────────────────

async def callback_pagamento_pix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    usuario_id = str(query.from_user.id)
    plano_id = query.data.split("_")[-1]
    plano = PLANOS[plano_id]

    usuario_doc = get_usuario(usuario_id)
    dados = usuario_doc.to_dict() or {}
    email = dados.get("email") or f"{usuario_id}@alivia.temp"

    payment_data = {
        "transaction_amount": plano["preco"],
        "description": plano["nome"],
        "payment_method_id": "pix",
        "payer": {"email": email},
        "notification_url": os.getenv("MP_WEBHOOK_URL"),
        "external_reference": f"{usuario_id}:{plano_id}",
    }

    result = sdk.payment().create(payment_data)
    payment = result["response"]
    print("MP RESPONSE:", result)

    qr_code_base64 = payment["point_of_interaction"]["transaction_data"]["qr_code_base64"]
    qr_code_copia_cola = payment["point_of_interaction"]["transaction_data"]["qr_code"]

    update_usuario(usuario_id, {
        "pagamento_id": str(payment["id"]),
        "pagamento_status": "pendente",
        "pagamento_metodo": "pix",
    })

    await query.edit_message_text(
        "Pronto! Pague via PIX escaneando o QR ou copiando o código abaixo.\n\n"
        "Assim que cair, libero seu acesso automaticamente ⚡"
    )

    qr_bytes = base64.b64decode(qr_code_base64)
    await context.bot.send_photo(chat_id=usuario_id, photo=io.BytesIO(qr_bytes))
    await context.bot.send_message(chat_id=usuario_id, text=f"`{qr_code_copia_cola}`", parse_mode="MarkdownV2")


# ─────────────────────────────────────────────────────────
# 3b. PAGAMENTO CARTÃO
# ─────────────────────────────────────────────────────────

async def callback_pagamento_cartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    usuario_id = str(query.from_user.id)
    plano_id = query.data.split("_")[-1]
    plano = PLANOS[plano_id]

    preference_data = {
        "items": [{
            "title": plano["nome"],
            "quantity": 1,
            "unit_price": plano["preco"],
            "currency_id": "BRL",
        }],
        "external_reference": f"{usuario_id}:{plano_id}",
        "notification_url": os.getenv("MP_WEBHOOK_URL"),
        "back_urls": {"success": os.getenv("MP_SUCCESS_URL", "https://t.me/alivia_bot")},
        "auto_return": "approved",
    }

    result = sdk.preference().create(preference_data)
    checkout_url = result["response"]["init_point"]

    update_usuario(usuario_id, {"pagamento_status": "pendente", "pagamento_metodo": "cartao"})

    await query.edit_message_text(
        f"Aqui está o link seguro de pagamento (Mercado Pago):\n\n{checkout_url}\n\n"
        f"Assim que aprovar, libero seu acesso automaticamente."
    )


# ─────────────────────────────────────────────────────────
# 4. WEBHOOK — chamado por webhooks/mercadopago_webhook.py
# ─────────────────────────────────────────────────────────

async def processar_webhook_mp(payload: dict):
    if payload.get("type") != "payment":
        return {"ok": True}

    payment_id = payload["data"]["id"]
    result = sdk.payment().get(payment_id)
    payment = result["response"]

    if payment["status"] != "approved":
        return {"ok": True, "status": payment["status"]}

    usuario_id, plano_id = payment["external_reference"].split(":")
    plano = PLANOS[plano_id]
    expira_em = datetime.now() + timedelta(days=plano["dias"])

    update_usuario(usuario_id, {
        "assinante": True,
        "plano_ativo": plano_id,
        "assinatura_expira_em": expira_em,
        "pagamento_status": "aprovado",
        "pagamento_confirmado_em": firestore.SERVER_TIMESTAMP,
        "fase_atual": 6,
    })

    await enviar_boas_vindas_assinante(usuario_id)
    return {"ok": True, "status": "approved"}


async def enviar_boas_vindas_assinante(usuario_id: str):
    from core import tg_app  # import tardio evita ciclo com main.py
    texto = (
        "🛡️ Pagamento confirmado! Você agora é ALÍVIA Proteção Completa.\n\n"
        "A partir de hoje eu vou:\n"
        "• Te avisar de golpes na sua região\n"
        "• Rodar seu checkup automaticamente todo mês\n"
        "• Estar aqui se algo suspeito acontecer\n\n"
        "Bem-vindo(a) à rede 💪"
    )
    await tg_app.bot.send_message(chat_id=usuario_id, text=texto)


# ─────────────────────────────────────────────────────────
# REGISTRO DOS HANDLERS
# ─────────────────────────────────────────────────────────

def registrar_handlers_fase5(tg_app):
    tg_app.add_handler(CallbackQueryHandler(callback_escolha_plano, pattern="^plano_"))
    tg_app.add_handler(CallbackQueryHandler(callback_pagamento_pix, pattern="^pag_pix_"))
    tg_app.add_handler(CallbackQueryHandler(callback_pagamento_cartao, pattern="^pag_cartao_"))