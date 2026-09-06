"""ALÍVIA™ — Fase 3: Educação (Dia 7-8). Disparada pelo scheduler (integracao/scheduler.py)."""

from core import tg_app


async def send_dica_dia1(usuario_id: str):
    dica = (
        "DICA DE SEGURANÇA:\n\n"
        "📱 Golpe real: 'Sua conta será bloqueada. Confirme dados aqui'\n\n"
        "🚨 Por que é golpe: banco NUNCA pede dados por link\n"
        "✅ Proteção: desconfie de QUALQUER link inesperado"
    )
    await tg_app.bot.send_message(chat_id=usuario_id, text=dica)


async def send_quiz_dia3(usuario_id: str):
    quiz = (
        "DESAFIO DE 10 SEGUNDOS:\n\nQual dessas é o REAL phishing?\n\n"
        "A) golpe-banco.com.br\nB) banco.com.br\nC) bancoo.com (com dois O)\n\n"
        "Responde aí 👆"
    )
    await tg_app.bot.send_message(chat_id=usuario_id, text=quiz)


async def send_dica_dia2(usuario_id: str):
    dica = (
        "NOVA ONDA DETECTADA esta semana: golpe de falso motoboy pedindo PIX "
        "de 'taxa de reentrega'.\n\n"
        "✅ Proteção: nenhuma transportadora cobra taxa por mensagem."
    )
    await tg_app.bot.send_message(chat_id=usuario_id, text=dica)
