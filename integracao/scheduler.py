"""ALÍVIA™ — Scheduler de mensagens automáticas (Fase 3)."""

import asyncio
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from core import db, update_usuario
from handlers.fase3 import send_dica_dia1, send_quiz_dia3, send_dica_dia2

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


def iniciar_scheduler():
    scheduler.add_job(scheduled_education, "interval", hours=6)
    scheduler.start()
