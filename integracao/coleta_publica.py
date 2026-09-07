# integracao/coleta_publica.py
"""
ALÍVIA™ — Orquestrador de Coleta Pública (17 Portais)
Coordena RSS + API + Scraping, alimenta THREAT RADAR.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict
from firebase_admin import firestore

from integracao.coleta_rss import coleta_rss_completa

logger = logging.getLogger(__name__)
db = firestore.client()


# ─────────────────────────────────────────────────────────
# ORQUESTRADOR PRINCIPAL
# ─────────────────────────────────────────────────────────

async def executar_coleta_completa() -> Dict:
    """
    Executa coleta de TODAS as 17 fontes (RSS + API + Scraping).
    Retorna resumo de artigos coletados por categoria.
    """
    logger.info("=" * 60)
    logger.info("🚀 INICIANDO COLETA COMPLETA - 17 PORTAIS")
    logger.info("=" * 60)

    resumo = {
        "timestamp": datetime.now().isoformat(),
        "rss": 0,
        "api": 0,
        "scraping": 0,
        "total": 0,
    }

    try:
        # CATEGORIA A: RSS (11 portais)
        logger.info("\n📡 CATEGORIA A: RSS (11 portais)")
        resumo["rss"] = await coleta_rss_completa()

        # CATEGORIA B: API (2 portais) — virá depois
        logger.info("\n🔌 CATEGORIA B: API (2 portais)")
        # resumo["api"] = await coleta_api_completa()

        # CATEGORIA C: Scraping (4 portais) — virá depois
        logger.info("\n🌐 CATEGORIA C: Scraping (4 portais)")
        # resumo["scraping"] = await coleta_scraping_completa()

        resumo["total"] = resumo["rss"] + resumo["api"] + resumo["scraping"]

        logger.info("\n" + "=" * 60)
        logger.info(f"✅ COLETA COMPLETA FINALIZADA")
        logger.info(f"   RSS: {resumo['rss']} | API: {resumo['api']} | Scraping: {resumo['scraping']}")
        logger.info(f"   TOTAL: {resumo['total']} artigos novos")
        logger.info("=" * 60)

        return resumo

    except Exception as e:
        logger.error(f"❌ Erro na coleta completa: {str(e)}")
        return resumo


async def atualizar_mapa_risco():
    """
    Agrupa casos_publicos por região e atualiza Mapa de Risco.
    Chamado a cada 6h após a coleta.
    """
    logger.info("📍 Atualizando Mapa de Risco...")

    try:
        casos = db.collection("casos_publicos").get()

        # Agrupa por região (vai ser simples por enquanto, será aperfeiçoado com Gemini)
        mapa = {}
        for caso in casos:
            # Placeholder: todos "Brasil" por enquanto
            regiao = "Brasil"
            tipo = caso.get("tipo_golpe", "Outro")

            if regiao not in mapa:
                mapa[regiao] = {"golpes_detectados": 0, "tipos": {}}

            mapa[regiao]["golpes_detectados"] += 1
            mapa[regiao]["tipos"][tipo] = mapa[regiao]["tipos"].get(tipo, 0) + 1

        # Salva no Firestore
        for regiao, dados in mapa.items():
            dados["data_atualizacao"] = datetime.now().isoformat()
            db.collection("mapa_risco").document(regiao).set(dados)

        logger.info(f"✅ Mapa de Risco atualizado: {len(mapa)} regiões")

    except Exception as e:
        logger.error(f"❌ Erro ao atualizar Mapa de Risco: {str(e)}")


async def gerar_boletim_diario():
    """
    Gera Boletim Diário com top 10 alertas do dia.
    Chamado uma vez por dia (6 AM).
    """
    logger.info("📰 Gerando Boletim Diário...")

    try:
        # Top 10 casos mais recentes
        casos = db.collection("casos_publicos").order_by("timestamp_coleta", direction=firestore.Query.DESCENDING).limit(10).get()

        alertas = []
        for caso in casos:
            alertas.append({
                "titulo": caso.get("titulo"),
                "tipo": caso.get("tipo_golpe", "Outro"),
                "regiao": caso.get("regiao", "Brasil"),
                "confianca": caso.get("confianca", 0),
                "fonte": caso.get("fonte"),
            })

        # Salva boletim
        hoje = datetime.now().strftime("%Y-%m-%d")
        boletim = {
            "principais_alertas": alertas,
            "total_alertas": len(alertas),
            "timestamp_geracao": datetime.now().isoformat(),
        }
        db.collection("boletins").document(hoje).set(boletim)

        logger.info(f"✅ Boletim Diário gerado: {len(alertas)} alertas")

    except Exception as e:
        logger.error(f"❌ Erro ao gerar Boletim: {str(e)}")