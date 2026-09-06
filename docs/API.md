# API — ALÍVIA™ Backend

## `POST /webhook/telegram`
Recebe updates do Telegram Bot API. Configurado via `setWebhook`. Não chamar
manualmente em produção — só pra debug local.

## `POST /webhook/mercadopago`
Recebe notificações de pagamento do Mercado Pago (IPN). Espera payload:
```json
{ "type": "payment", "data": { "id": "123456789" } }
```
Ao receber, consulta o pagamento na API do MP, confirma status `approved` e
ativa a assinatura do usuário (`assinante: true`, `fase_atual: 6`).

## `GET /health`
Health check simples. Retorna `{"status": "ok", "service": "ALÍVIA™"}`.

## Rotas planejadas (ainda não implementadas)
- `POST /admin/force-sync-threat-radar` — sincronizar THREAT RADAR™ manualmente
- `GET /metrics` — métricas de operação (conversão por fase, churn, etc)
