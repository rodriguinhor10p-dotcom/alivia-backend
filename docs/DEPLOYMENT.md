# DEPLOYMENT — ALÍVIA™

## Pré-requisitos
- Repositório no GitHub
- Conta Railway (ou Cloud Run) conectada
- `firebase-key.json` (service account) em mãos — NÃO commitar no git
- Token do Telegram (@BotFather)
- Credenciais do Mercado Pago (produção, não sandbox, pra ir ao ar de verdade)

## Passo a passo (Railway)

1. Criar novo projeto no Railway, conectar ao repositório `alivia-backend`.
2. Configurar variáveis de ambiente (mesmas do `.env.example`), incluindo:
   - `MP_WEBHOOK_URL` = `https://<seu-app>.up.railway.app/webhook/mercadopago`
   - `BACKEND_URL` = `https://<seu-app>.up.railway.app`
3. Subir `firebase-key.json` como arquivo de configuração/secret (não como
   variável de ambiente de texto — é um JSON grande).
4. Deploy via Dockerfile (Railway detecta automaticamente).
5. Após o deploy, registrar o webhook do Telegram:
   ```bash
   curl "https://api.telegram.org/bot$TELEGRAM_TOKEN/setWebhook?url=https://<seu-app>.up.railway.app/webhook/telegram"
   ```
6. Testar `/health` e mandar `/start` pro bot no Telegram.
7. Testar um pagamento PIX real de baixo valor antes de anunciar.

## Checklist de "tudo pronto" antes de anunciar (Regra de Ouro do projeto)
- [ ] `/health` responde 200
- [ ] Webhook do Telegram confirmado (`getWebhookInfo`)
- [ ] Webhook do Mercado Pago testado ponta-a-ponta (pagamento real pequeno)
- [ ] Firestore com as 5 collections criadas e populando
- [ ] Scheduler da Fase 3 disparando (checar logs após 6h)
- [ ] Monitoramento básico ativo (ver RUNBOOK.md)

Só sobe/publica quando TUDO estiver pronto — nunca antecipar publicação.
