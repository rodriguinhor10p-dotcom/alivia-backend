"""
ALÍVIA™ — core.py
Inicialização compartilhada: Firebase, Telegram Bot, helpers de Firestore.
Todo módulo (handlers/, integracao/, webhooks/) importa daqui — nunca de main.py,
pra evitar import circular.
"""

import os
import firebase_admin
from firebase_admin import credentials, firestore
from telegram.ext import Application
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────
# FIREBASE
# ─────────────────────────────────────────────────────────

cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-key.json"))
firebase_admin.initialize_app(cred)
db = firestore.client()

# ─────────────────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────────────────

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
tg_app = Application.builder().token(TELEGRAM_TOKEN).job_queue(None).build()
# ─────────────────────────────────────────────────────────
# HELPERS FIRESTORE
# ─────────────────────────────────────────────────────────

def get_usuario(usuario_id: str):
    return db.collection("usuarios_alivia").document(usuario_id).get()


def update_usuario(usuario_id: str, data: dict):
    db.collection("usuarios_alivia").document(usuario_id).update(data)


def log_conversa(usuario_id: str, tipo: str, mensagem: str, fase: int):
    db.collection("conversas_alivia").add({
        "usuario_id": usuario_id,
        "timestamp": firestore.SERVER_TIMESTAMP,
        "tipo": tipo,
        "mensagem": mensagem,
        "fase": fase,
    })
