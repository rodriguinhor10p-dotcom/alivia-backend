# RUNBOOK — ALÍVIA™

## Checar se está no ar
```bash
curl https://SEU-BACKEND/health
```
Esperado: `{"status": "ok", "service": "ALÍVIA™"}`

## Reprocessar webhook do Telegram manualmente
Se o bot parar de responder, primeiro confirme se o webhook está registrado:
```bash
curl "https://api.telegram.org/bot$TELEGRAM_TOKEN/getWebhookInfo"
```
Se `url` estiver vazio ou errado, reconfigurar:
```bash
curl "https://api.telegram.org/bot$TELEGRAM_TOKEN/setWebhook?url=https://SEU-BACKEND/webhook/telegram"
```

## Usuário travado numa fase
Cada usuário tem `fase_atual` em `usuarios_alivia/{uid}` no Firestore. Pra
resetar manualmente: editar o documento e colocar `fase_atual: 1` (e limpar
campos de step tipo `checkup_step`, `investigacao_step`).

## Pagamento não confirmou
1. Conferir `pagamento_status` no doc do usuário (`pendente`/`aprovado`/`erro`).
2. Consultar direto no Mercado Pago pelo `pagamento_id` salvo no Firestore.
3. Se aprovado lá mas não no Firestore, o webhook falhou — reprocessar
   chamando manualmente `POST /webhook/mercadopago` com o payload do MP.

## Scheduler da Fase 3 não disparou
O job roda a cada 6h (`integracao/scheduler.py`). Confirmar que o processo do
backend não reiniciou perdendo o `BackgroundScheduler` (em produção, preferir
um scheduler externo/persistente em vez do in-process se o Cloud Run escalar
a zero).

## Logs
Ainda não há agregador configurado — usar os logs nativos do Railway/Cloud
Run. TODO: adicionar logging estruturado (ver seção "Próximos passos" no
README).
