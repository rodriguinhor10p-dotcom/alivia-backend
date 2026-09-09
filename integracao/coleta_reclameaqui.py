"""
ALÍVIA™ — Coleta Reclame Aqui via Apify (Categoria B)
Consulta o Actor memo23/reclameaqui-scraper pras empresas mais mencionadas
pelos usuários (ver integracao/empresas_monitoradas.py) e salva os
resultados em casos_publicos, alimentando o THREAT RADAR™.

⚠️ ATENÇÃO: os nomes dos campos da resposta (título, texto, data, etc.)
são uma estimativa baseada na descrição pública do Actor. Depois do
primeiro teste real, pode ser necessário ajustar o parsing conforme o
JSON que a Apify realmente devolver — igual ajustamos a URL do R7 no RSS.
"""

import os
import hashlib
import logging
import requests
from datetime import datetime

from core import db
from integracao.empresas_monitoradas import obter_empresas_prioritarias

logger = logging.getLogger(__name__)

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
ACTOR_ID = "memo23~reclameaqui-scraper"
APIFY_URL = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"


# ─────────────────────────────────────────────────────────
# CONSULTA AO ACTOR
# ─────────────────────────────────────────────────────────

async def consultar_reclameaqui(empresas: list[str]) -> list[dict]:
    """
    Roda o Actor da Apify pra uma lista de empresas e retorna as
    reclamações extraídas. Chamada síncrona (Apify processa e devolve
    o resultado pronto), por isso pode demorar alguns segundos/minutos.
    """
    if not empresas:
        return []

    if not APIFY_TOKEN:
        logger.error("❌ APIFY_TOKEN não configurado — pulando coleta Reclame Aqui")
        return []

    payload = {
        "compact": False,
        "companies": empresas,
        "detectUpdates": False,
        "emitExpired": False,
        "emitUnchanged": False,
        "enrichEmails": False,
        "excludeEmptyFields": False,
        "extractContacts": False,
        "flatten": True,
        "includeCompanyProfile": True,
        "includeInteractions": False,
        "incrementalMode": False,
        "notifyOnlyNew": True,
        "scrapeComplaints": True,
        "solvedOnly": False,
        "withReplyOnly": False,
    }

    try:
        response = requests.post(
            APIFY_URL,
            params={"token": APIFY_TOKEN},
            json=payload,
            timeout=180,  # Actor pode demorar a rodar
        )
        response.raise_for_status()
        itens = response.json()
        logger.info(f"✅ Apify Reclame Aqui: {len(itens)} itens retornados")
        return itens

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erro ao consultar Apify: {str(e)}")
        return []


# ─────────────────────────────────────────────────────────
# PARSING + SALVAMENTO NO FIRESTORE
# ─────────────────────────────────────────────────────────

def _extrair_campos(item: dict) -> dict:
    """
    Normaliza um item retornado pelo Actor pro formato da collection
    casos_publicos. Os nomes de campo abaixo são a melhor estimativa —
    ajustar depois de ver a resposta real (ver aviso no topo do arquivo).
    """
    titulo = item.get("title") or item.get("complaintTitle") or "Sem título"
    descricao = item.get("description") or item.get("complaintText") or ""
    url = item.get("url") or item.get("complaintUrl") or ""
    empresa = item.get("company") or item.get("companyName") or "Desconhecida"
    data_publicacao = item.get("date") or item.get("createdAt") or ""

    return {
        "titulo": titulo,
        "descricao": descricao[:500],  # limita tamanho
        "url_original": url,
        "fonte": f"Reclame Aqui — {empresa}",
        "tipo_golpe": "reclamacao_consumidor",
        "data_publicacao": data_publicacao,
        "timestamp_coleta": datetime.now().isoformat(),
        "processado": False,
        "enviado_threat_radar": False,
    }


async def salvar_reclamacoes_firestore(itens: list[dict]) -> int:
    """Salva reclamações em casos_publicos, com dedup por URL."""
    casos_ref = db.collection("casos_publicos")
    novos = 0

    for item_bruto in itens:
        try:
            caso = _extrair_campos(item_bruto)

            if not caso["url_original"]:
                continue  # sem URL não dá pra deduplicar com segurança

            existing = casos_ref.where("url_original", "==", caso["url_original"]).get()
            if existing:
                continue

            doc_id = hashlib.md5(caso["url_original"].encode()).hexdigest()[:16]
            casos_ref.document(doc_id).set(caso)
            novos += 1

        except Exception as e:
            logger.error(f"Erro ao salvar reclamação: {str(e)}")

    logger.info(f"📝 Firestore: {novos} reclamações novas salvas")
    return novos


def _marcar_verificadas(empresas: list[str]):
    """Atualiza o timestamp de última verificação de cada empresa consultada."""
    for nome in empresas:
        try:
            doc_id = nome.lower().replace(" ", "_").replace("ó", "o").replace("ú", "u")
            db.collection("empresas_monitoradas").document(doc_id).update({
                "ultima_verificacao_reclameaqui": datetime.now(),
            })
        except Exception as e:
            logger.error(f"Erro ao marcar {nome} como verificada: {str(e)}")


# ─────────────────────────────────────────────────────────
# ORQUESTRADOR
# ─────────────────────────────────────────────────────────

async def coleta_reclameaqui_completa(limite_empresas: int = 5) -> int:
    """
    Pega as empresas mais mencionadas (ver empresas_monitoradas.py),
    consulta o Reclame Aqui via Apify e salva os resultados novos.
    Retorna quantidade de reclamações novas salvas.
    """
    prioritarias = obter_empresas_prioritarias(limite=limite_empresas)
    nomes_empresas = [e["nome"] for e in prioritarias if "nome" in e]

    if not nomes_empresas:
        logger.info("ℹ️ Nenhuma empresa monitorada ainda — pulando coleta Reclame Aqui")
        return 0

    logger.info(f"🔄 Consultando Reclame Aqui: {', '.join(nomes_empresas)}")

    itens = await consultar_reclameaqui(nomes_empresas)
    novos = await salvar_reclamacoes_firestore(itens)
    _marcar_verificadas(nomes_empresas)

    return novos