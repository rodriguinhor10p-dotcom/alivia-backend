# integracao/coleta_rss.py
"""
ALÍVIA™ — Coleta RSS de 17 Portais (Categoria A)
Parseia 11 feeds RSS, dedup, salva em Firestore, enriquece com Gemini NLP.
"""

import feedparser
import logging
import hashlib
import asyncio
from datetime import datetime
from typing import List, Dict
from firebase_admin import firestore

logger = logging.getLogger(__name__)

db = firestore.client()

# ─────────────────────────────────────────────────────────
# CONFIGURAÇÃO DOS 11 PORTAIS RSS
# ─────────────────────────────────────────────────────────

PORTAIS_RSS = {
    "g1": {
        "nome": "G1 Globo",
        "url": "https://g1.globo.com/rss/feeds/busca/noticia/golpe/",
        "intervalo_horas": 2,
    },
    "r7": {
        "nome": "R7",
        "url": "https://www.r7.com/rss/cidades/",  # Placeholder — ajustar real
        "intervalo_horas": 3,
    },
    "uol": {
        "nome": "UOL",
        "url": "https://noticias.uol.com.br/rss/",
        "intervalo_horas": 3,
    },
    "folha": {
        "nome": "Folha de S.Paulo",
        "url": "https://www1.folha.uol.com.br/rss/",
        "intervalo_horas": 4,
    },
    "estadao": {
        "nome": "O Estado de S.Paulo",
        "url": "https://rss.estadao.com.br/",
        "intervalo_horas": 4,
    },
    "correio": {
        "nome": "Correio Braziliense",
        "url": "https://www.correiobraziliense.com.br/rss/",
        "intervalo_horas": 6,
    },
    "oglobo": {
        "nome": "O Globo",
        "url": "https://oglobo.globo.com/rss/",
        "intervalo_horas": 6,
    },
    "cnn": {
        "nome": "CNN Brasil",
        "url": "https://www.cnnbrasil.com.br/feed/",
        "intervalo_horas": 3,
    },
    "terra": {
        "nome": "Terra",
        "url": "https://www.terra.com.br/rss/",
        "intervalo_horas": 4,
    },
    "certbr": {
        "nome": "CERT.br",
        "url": "https://www.cert.br/rss/alertas/",
        "intervalo_horas": 6,
    },
    "febraban": {
        "nome": "FEBRABAN",
        "url": "https://www.febraban.org.br/rss/",
        "intervalo_horas": 24,
    },
}


# ─────────────────────────────────────────────────────────
# FUNÇÕES DE COLETA RSS
# ─────────────────────────────────────────────────────────

async def coletar_portal_rss(portal_key: str) -> List[Dict]:
    """
    Faz parse de um feed RSS específico.
    Retorna lista de dicts com: título, descrição, URL, fonte, data.
    """
    config = PORTAIS_RSS[portal_key]
    url = config["url"]
    nome_portal = config["nome"]

    try:
        feed = feedparser.parse(url)

        if not feed.entries:
            logger.warning(f"Nenhum artigo em {nome_portal}")
            return []

        artigos = []
        for entry in feed.entries[:10]:  # Top 10 mais recentes
            artigo = {
                "titulo": entry.get("title", "Sem título"),
                "descricao": entry.get("summary", ""),
                "url_original": entry.get("link", ""),
                "fonte": nome_portal,
                "data_publicacao": entry.get("published", ""),
                "timestamp_coleta": datetime.now().isoformat(),
                "processado": False,
                "enviado_threat_radar": False,
            }
            artigos.append(artigo)

        logger.info(f"✅ {nome_portal}: {len(artigos)} artigos coletados")
        return artigos

    except Exception as e:
        logger.error(f"❌ Erro ao coletar {nome_portal}: {str(e)}")
        return []


async def salvar_casos_firestore(artigos: List[Dict]) -> int:
    """
    Salva artigos em Firestore, faz dedup por URL.
    Retorna quantidade de novos artigos inseridos.
    """
    casos_ref = db.collection("casos_publicos")
    novos = 0

    for artigo in artigos:
        try:
            # Dedup: procura se URL já existe
            existing = casos_ref.where("url_original", "==", artigo["url_original"]).get()

            if existing:
                logger.debug(f"Dedup: {artigo['url_original']} já existe")
                continue

            # Cria novo documento com ID baseado na URL (hash curto)
            doc_id = hashlib.md5(artigo["url_original"].encode()).hexdigest()[:16]
            casos_ref.document(doc_id).set(artigo)
            novos += 1

        except Exception as e:
            logger.error(f"Erro ao salvar artigo: {str(e)}")

    logger.info(f"📝 Firestore: {novos} artigos novos salvos")
    return novos


async def coleta_rss_completa() -> int:
    """
    Orquestra coleta de TODOS os 11 portais RSS em paralelo.
    Retorna total de artigos coletados.
    """
    logger.info("🔄 Iniciando coleta RSS de 11 portais...")

    # Coleta em paralelo
    tasks = [coletar_portal_rss(portal_key) for portal_key in PORTAIS_RSS.keys()]
    resultados = await asyncio.gather(*tasks)

    # Agrupa resultados
    todos_artigos = []
    for resultado in resultados:
        todos_artigos.extend(resultado)

    logger.info(f"📊 Total coletado: {len(todos_artigos)} artigos")

    # Salva no Firestore (com dedup)
    novos = await salvar_casos_firestore(todos_artigos)

    return novos