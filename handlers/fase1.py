"""ALÍVIA™ — Fase 1: Captura e Descoberta (Dia 3-4)."""

from datetime import datetime
from firebase_admin import firestore
from core import log_conversa, update_usuario


async def handle_fase1(usuario_id: str, texto: str) -> str:
    if "sim" in texto.lower() or "recebi" in texto.lower():
        resposta = (
            "Ok, recebi. Deixa eu entender melhor pra poder ajudar.\n\n"
            "Qual era a mensagem EXATAMENTE? (Cole aqui ou descreva)"
        )
        nova_fase = 2
        intencao = "sim_recebeu"
    else:
        resposta = (
            "Que legal que sua segurança tá boa 👍\n\n"
            "Mas deixa eu compartilhar um alerta rápido: uma nova campanha de golpe "
            "está circulando agora. Quer aprender como identificar?"
        )
        nova_fase = 3
        intencao = "nao_recebeu"

    log_conversa(usuario_id, "usuario", texto, 1)

    dados = {
        "fase_atual": nova_fase,
        "data_ultima_conversa": firestore.SERVER_TIMESTAMP,
    }
    if nova_fase == 3:
        dados["data_entrada_fase3"] = datetime.now()

    update_usuario(usuario_id, dados)
    return resposta
