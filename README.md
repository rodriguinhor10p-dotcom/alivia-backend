# ALÍVIA™ — Backend

Guardiã digital do Brasil. Bot no Telegram que educa, investiga, faz checkup
de segurança digital e converte em assinatura (PIX/Cartão via Mercado Pago).

## Estrutura

```
alivia-backend/
├─ main.py                 # entrypoint FastAPI + dispatcher de mensagens
├─ core.py                 # Firebase, Telegram Bot, helpers Firestore compartilhados
├─ requirements.txt
├─ .env.example             # copiar pra .env e preencher
├─ firebase-key.json        # NÃO versionar (baixar do Firebase Console)
├─ config/
│  └─ checkup_questions.json   # as 15 perguntas do Checkup Digital (5 áreas)
├─ handlers/
│  ├─ comandos.py           # /start, /help
│  ├─ fase1.py               # Captura
│  ├─ fase2.py               # Investigação (+ THREAT RADAR)
│  ├─ fase3.py               # Educação (dicas/quiz enviados pelo scheduler)
│  ├─ fase4.py               # Checkup Digital
│  └─ fase5.py               # Conversão (oferta + Mercado Pago)
├─ integracao/
│  ├─ threat_radar.py       # cliente THREAT RADAR™ (placeholder)
│  └─ scheduler.py          # job da Fase 3, roda a cada 6h
├─ webhooks/
│  ├─ telegram_webhook.py
│  └─ mercadopago_webhook.py
├─ tests/
│  └─ test_health.py
├─ docs/
│  ├─ RUNBOOK.md
│  ├─ API.md
│  └─ DEPLOYMENT.md
└─ Dockerfile
```

## Rodando localmente

```bash
pip install -r requirements.txt
cp .env.example .env   # preencher com valores reais
# colocar firebase-key.json na raiz (baixar do Firebase Console)
uvicorn main:app --reload
```

Local só serve pra testar Fases 1-4 (Telegram webhook precisa de HTTPS
público — usar `ngrok` pra testar webhook do Telegram em dev). Mercado Pago
(Fase 5) exige `MP_WEBHOOK_URL` público, então só funciona ponta-a-ponta após
deploy.

## Status das fases

| Fase | Nome | Status |
|------|------|--------|
| 1 | Captura | ✅ Funcional |
| 2 | Investigação | ✅ Funcional (THREAT RADAR ainda é placeholder) |
| 3 | Educação | ✅ Funcional (scheduler a cada 6h) |
| 4 | Checkup Digital | ✅ Funcional (score é MVP simplificado) |
| 5 | Conversão | ✅ Funcional (testar com sandbox do Mercado Pago) |
| 6 | Retenção + Afiliados | ⏳ Não iniciada |

## Próximos passos

- [ ] Plugar THREAT RADAR™ real em `integracao/threat_radar.py`
- [ ] Revisar pesos do score do Checkup com Vera/Marco
- [ ] Construir `handlers/fase6.py` (retenção + churn prevention + afiliados)
- [ ] Deploy em Railway/Cloud Run + configurar webhooks públicos
- [ ] Ver `docs/DEPLOYMENT.md` para o passo a passo
