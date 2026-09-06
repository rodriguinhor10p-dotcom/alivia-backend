"""
ALÍVIA™ — Integração THREAT RADAR™
Placeholder até o endpoint real do THREAT RADAR estar disponível.
TODO: trocar por chamada HTTP real (ex: POST /internal/threat-radar/validar).
"""


async def validar_threat_radar(mensagem: str) -> int:
    """Retorna score de confiança 0-100 de que a mensagem é golpe.
    Hoje: fixo em 85 pra não travar o desenvolvimento das Fases 1-6.
    """
    return 85
