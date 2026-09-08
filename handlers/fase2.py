"""ALÍVIA™ — Fase 2: Investigação (Dia 5-6)."""

from datetime import datetime
from firebase_admin import firestore
from core import update_usuario
from integracao.threat_radar import validar_threat_radar
from integracao.empresas_monitoradas import registrar_mencoes

PERGUNTAS = [
    "1. Você conhecia a pessoa que mandou?",
    "2. Você clicou em algum link?",
    "3. Você compartilhou dados pessoais?",
    "4. Quanto tempo faz que recebeu?",
]
CAMPOS = ["conhecia_pessoa", "clicou_link", "compartilhou_dados", "tempo_recebeu"]


async def handle_fase2(usuario_id: str, texto: str, usuario_doc) -> str:
    dados = usuario_doc.to_dict() or {}
    step = dados.get("investigacao_step") or 0

    if step == 0:
        update_usuario(usuario_id, {"investigacao_step": 1, "mensagem_descrita": texto})
        return PERGUNTAS[0]

    if step <= len(CAMPOS):
        campo = CAMPOS[step - 1]
        update_usuario(usuario_id, {campo: texto})

        if step < len(PERGUNTAS):
            update_usuario(usuario_id, {"investigacao_step": step + 1})
            return PERGUNTAS[step]

        # última pergunta respondida → validar com THREAT RADAR™
        mensagem = dados.get("mensagem_descrita", "")
        score = await validar_threat_radar(mensagem)

        # extrai empresas mencionadas no relato pra alimentar a coleta
        # dinâmica do Reclame Aqui (Categoria B)
        await registrar_mencoes(mensagem)

        update_usuario(usuario_id, {
            "investigacao_step": firestore.DELETE_FIELD,
            "fase_atual": 3,
            "data_entrada_fase3": datetime.now(),
        })

        if score > 80:
            return (
                "🔴 ISSO É UM GOLPE CONFIRMADO\n\n"
                "AÇÃO IMEDIATA:\n✅ Não clique em mais links\n"
                "✅ Mude sua senha agora\n✅ Contate seu banco"
            )
        return (
            "Padrão SUSPEITO, mas não posso confirmar 100%.\n\n"
            "Melhor prevenir: não clique, não compartilhe, bloqueie."
        )