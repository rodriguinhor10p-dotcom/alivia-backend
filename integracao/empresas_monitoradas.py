"""
ALÍVIA™ — Empresas Monitoradas (lista dinâmica pro Reclame Aqui)
Extrai nomes de empresas conhecidas mencionadas nos relatos de golpe dos
usuários (Fase 2) e mantém um ranking de menções no Firestore.
Esse ranking alimenta a coleta via Apify (Reclame Aqui) — Categoria B.
"""

import logging
from datetime import datetime
from firebase_admin import firestore
from core import db

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# LISTA DE EMPRESAS CONHECIDAS (curada manualmente)
# Chave: nome de exibição | Valor: variações de texto pra detectar
# ─────────────────────────────────────────────────────────

EMPRESAS_CONHECIDAS = {
    "Banco do Brasil": ["banco do brasil", "bb "],
    "Bradesco": ["bradesco"],
    "Itaú": ["itau", "itaú"],
    "Santander": ["santander"],
    "Caixa Econômica Federal": ["caixa econ", "caixa federal", " cef "],
    "Nubank": ["nubank", "nu bank"],
    "Banco Inter": ["banco inter", "inter "],
    "C6 Bank": ["c6 bank", "c6bank"],
    "PicPay": ["picpay", "pic pay"],
    "Mercado Pago": ["mercado pago", "mercadopago"],
    "Mercado Livre": ["mercado livre", "mercadolivre"],
    "OLX": ["olx"],
    "Shopee": ["shopee"],
    "Amazon": ["amazon"],
    "Magazine Luiza": ["magazine luiza", "magalu"],
    "Casas Bahia": ["casas bahia"],
    "iFood": ["ifood", "i-food"],
    "Uber": ["uber"],
    "99": ["99app", "99 app", "99táxi", "99 taxi"],
    "Correios": ["correios"],
    "Netflix": ["netflix"],
    "Enel": ["enel"],
    "INSS": ["inss"],
    "Receita Federal": ["receita federal"],
    "Serasa": ["serasa"],
    "SPC": ["spc brasil", " spc "],
    "WhatsApp": ["whatsapp", "whats app"],
}


# ─────────────────────────────────────────────────────────
# EXTRAÇÃO
# ─────────────────────────────────────────────────────────

def extrair_empresas_mencionadas(texto: str) -> list[str]:
    """
    Varre o texto (relato do golpe) procurando menções a empresas conhecidas.
    Retorna lista de nomes de exibição encontrados (sem duplicatas).
    """
    if not texto:
        return []

    texto_lower = f" {texto.lower()} "
    encontradas = []

    for nome_exibicao, variacoes in EMPRESAS_CONHECIDAS.items():
        for variacao in variacoes:
            if variacao in texto_lower:
                encontradas.append(nome_exibicao)
                break

    return encontradas


# ─────────────────────────────────────────────────────────
# UPSERT NO FIRESTORE
# ─────────────────────────────────────────────────────────

async def registrar_mencoes(texto: str) -> list[str]:
    """
    Extrai empresas do texto e incrementa o contador de menções de cada uma
    na collection 'empresas_monitoradas'. Retorna as empresas encontradas.
    """
    empresas = extrair_empresas_mencionadas(texto)

    for nome in empresas:
        try:
            doc_id = nome.lower().replace(" ", "_").replace("ó", "o").replace("ú", "u")
            ref = db.collection("empresas_monitoradas").document(doc_id)
            doc = ref.get()

            if doc.exists:
                ref.update({
                    "contagem_mencoes": firestore.Increment(1),
                    "ultima_mencao": datetime.now(),
                })
            else:
                ref.set({
                    "nome": nome,
                    "contagem_mencoes": 1,
                    "primeira_mencao": datetime.now(),
                    "ultima_mencao": datetime.now(),
                    "ultima_verificacao_reclameaqui": None,
                })

            logger.info(f"📌 Empresa mencionada: {nome}")

        except Exception as e:
            logger.error(f"Erro ao registrar menção de {nome}: {str(e)}")

    return empresas


def obter_empresas_prioritarias(limite: int = 5) -> list[dict]:
    """
    Retorna as empresas mais mencionadas que ainda não foram verificadas
    recentemente no Reclame Aqui (ou nunca foram verificadas).
    Usado pelo scheduler pra decidir quais consultar via Apify.
    """
    docs = (
        db.collection("empresas_monitoradas")
        .order_by("contagem_mencoes", direction=firestore.Query.DESCENDING)
        .limit(limite)
        .stream()
    )
    return [doc.to_dict() for doc in docs]