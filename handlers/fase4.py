"""ALÍVIA™ — Fase 4: Checkup Digital (Dia 9-10)."""

import json
from pathlib import Path
from firebase_admin import firestore
from core import db, update_usuario
from handlers.fase5 import apresentar_oferta

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "checkup_questions.json"
CHECKUP_AREAS = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
AREAS_ORDEM = list(CHECKUP_AREAS.keys())


def calcular_checkup_score(respostas: list) -> int:
    """MVP: conta respostas 'seguras' e tira %.
    TODO (Vera/Marco): pesos por pergunta em vez de contagem simples."""
    respostas_seguras = sum(
        1 for r in respostas
        if r.strip().lower() in ("não", "nao", "sim, uso", "sim")
    )
    return round((respostas_seguras / max(len(respostas), 1)) * 100)


async def handle_fase4(usuario_id: str, texto: str, usuario_doc, bot) -> str | None:
    step = usuario_doc.get("checkup_step") or 0

    if step == 0:
        update_usuario(usuario_id, {"checkup_step": 1})
        return (
            "Você aprende bem. Que tal um CHECKUP DIGITAL rápido?\n"
            "Vamos revisar sua segurança em 5 áreas. Topa? (Sim/Não)"
        )

    if step == 1:
        if "sim" not in texto.lower():
            update_usuario(usuario_id, {"checkup_step": firestore.DELETE_FIELD})
            return "Sem problema, seguimos com as dicas por enquanto 🙂"

        update_usuario(usuario_id, {
            "checkup_step": 2,
            "checkup_respostas": [],
            "checkup_area": AREAS_ORDEM[0],
            "checkup_pergunta": 0,
        })
        return CHECKUP_AREAS[AREAS_ORDEM[0]][0]

    if step == "aguardando_decisao":
        if "sim" in texto.lower():
            score = usuario_doc.get("checkup_score", 0)
            await apresentar_oferta(usuario_id, score, bot)
            update_usuario(usuario_id, {"checkup_step": firestore.DELETE_FIELD})
            return None  # apresentar_oferta já envia a mensagem
        update_usuario(usuario_id, {
            "checkup_step": firestore.DELETE_FIELD,
            "fase_atual": 3,
        })
        return "Tudo bem! Continuo te mandando dicas por aqui."

    # steps 2+ : coletando as 15 respostas
    respostas = usuario_doc.get("checkup_respostas", [])
    respostas.append(texto)

    area = usuario_doc.get("checkup_area")
    pergunta_idx = usuario_doc.get("checkup_pergunta", 0)

    if pergunta_idx < 2:
        pergunta_idx += 1
        update_usuario(usuario_id, {
            "checkup_step": step + 1,
            "checkup_respostas": respostas,
            "checkup_pergunta": pergunta_idx,
        })
        return CHECKUP_AREAS[area][pergunta_idx]

    area_idx = AREAS_ORDEM.index(area)
    if area_idx < len(AREAS_ORDEM) - 1:
        nova_area = AREAS_ORDEM[area_idx + 1]
        update_usuario(usuario_id, {
            "checkup_step": step + 1,
            "checkup_respostas": respostas,
            "checkup_area": nova_area,
            "checkup_pergunta": 0,
        })
        return CHECKUP_AREAS[nova_area][0]

    # CHECKUP COMPLETO
    score = calcular_checkup_score(respostas)

    db.collection("checkup_digital_alivia").add({
        "usuario_id": usuario_id,
        "score_final": score,
        "respostas": respostas,
        "timestamp": firestore.SERVER_TIMESTAMP,
    })

    update_usuario(usuario_id, {
        "checkup_step": "aguardando_decisao",
        "checkup_score": score,
    })

    return (
        f"SEU CHECKUP DIGITAL\n\n{score}% de segurança\n\n"
        f"RECOMENDAÇÕES:\n1. Ativar 2FA\n2. Mudar senhas\n3. Instalar gerenciador\n\n"
        f"Quer proteção completa? (Sim/Não)"
    )
