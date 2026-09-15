---
type: RouteSpec
title: Spec — POST /api/webhooks/triage-result
description: Especificação da rota de Webhook callback do BFF. Recebe o resultado do processamento assíncrono do Core e o dispara via SSE para o MFE.
timestamp: 2026-08-08T18:38:00-03:00
status: active
version: 1.0.0
resource: ./webhook.route.ts
related:
  - ../triage/stream.spec.md
  - ../../../.okf/contracts/core-api.md
  - ../../../.okf/contracts/bff-api.md
---

# Spec — POST /api/webhooks/triage-result

## Identidade da Rota

| Método | URL | Tag | Descrição |
| :--- | :--- | :--- | :--- |
| POST | /api/webhooks/triage-result | Webhook Callback | Recebe o resultado do pipeline LangGraph + ChromaDB enviado pelo Core |

---

## Contrato de Entrada (Request Body)

Validado via `WebhookPayloadSchema` com Zod:

```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "patient_id": "PAC-001",
  "status": "completed",
  "risk_assessment": {
    "risk_level": "Alto/Iminente",
    "passive_ideation": true,
    "active_ideation": true,
    "red_flags": ["Histórico prévio de tentativa de suicídio"],
    "protection_factors": ["Suporte de familiares"],
    "clinical_justification": "Justificativa clínica detalhada..."
  },
  "audit_alerts": ["[ALERTA CRÍTICO] Risco elevado..."],
  "final_report": "=== PARECER EXECUTIVO DE AUDITORIA CLÍNICA ==="
}
```

---

## Fluxo de Execução

1. O handler recebe `POST /api/webhooks/triage-result`.
2. Valida o payload de entrada com `WebhookPayloadSchema`.
3. Extrai `job_id` do body.
4. Busca a conexão SSE ativa no mapa global: `reply = activeSseConnections.get(job_id)`.
5. **Se a conexão for encontrada:**
   - Formata a mensagem SSE: `event: triage_completed\ndata: ${JSON.stringify(payload)}\n\n`.
   - Envia a mensagem no socket cru (`reply.raw.write(...)`).
   - Remove a conexão do mapa (`activeSseConnections.delete(job_id)`).
   - Encerra o fluxo SSE (`reply.raw.end()`).
6. Retorna `200 OK` `{ status: "ok", message: "Result delivered to client via SSE" }` ao Core.

---

## Casos de Borda e Erros

| Cenário | Comportamento Esperado |
| :--- | :--- |
| Payload inválido enviado pelo Core | Retorna `400 Bad Request` |
| `job_id` não encontrado em `activeSseConnections` | Retorna `200 OK` `{ status: "ok", message: "Result stored, client connection expired or missing" }` sem crashar |
