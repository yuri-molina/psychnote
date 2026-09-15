---
type: RouteSpec
title: Spec — GET /api/triage/stream/:jobId
description: Especificação da rota SSE (Server-Sent Events) do BFF. Gerencia o canal de streaming para notificação em tempo real do resultado da triagem de risco clínico.
timestamp: 2026-08-08T18:38:00-03:00
status: active
version: 1.0.0
resource: ./stream.route.ts
related:
  - ./triage.spec.md
  - ../webhooks/webhook.spec.md
  - ../../../.okf/contracts/bff-api.md
  - ../../../.okf/decisions/0005-async-webhook-sse-architecture.md
---

# Spec — GET /api/triage/stream/:jobId

## Identidade da Rota

| Método | URL | Tag | Descrição |
| :--- | :--- | :--- | :--- |
| GET | /api/triage/stream/:jobId | Triagem Assíncrona / Streaming | Canal SSE (Server-Sent Events) para recebimento do resultado da triagem |

---

## Contrato de Entrada (Path Parameters)

| Campo | Tipo | Validação | Descrição |
| :--- | :--- | :--- | :--- |
| `jobId` | `string` | UUIDv4 | Identificador único da triagem gerado no `POST /api/triage` |

---

## Contrato de Saída (HTTP Headers & Event Stream)

### Headers HTTP Obrigatórios

```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
```

### Formato dos Eventos Emitidos

#### 1. Heartbeat (a cada 15 segundos)
```http
: heartbeat

```

#### 2. Conclusão da Triagem (`triage_completed`)
```http
event: triage_completed
data: {"job_id":"123e4567-e89b-12d3-a456-426614174000","patient_id":"PAC-001","status":"completed","risk_assessment":{"risk_level":"Alto/Iminente","passive_ideation":true,"active_ideation":true,"red_flags":["..."],"protection_factors":["..."],"clinical_justification":"..."},"audit_alerts":["..."],"final_report":"..."}

```

---

## Fluxo de Execução

1. O handler recebe `GET /api/triage/stream/:jobId`.
2. Valida se `jobId` é um UUIDv4 válido.
3. Configura os cabeçalhos de resposta HTTP (`Content-Type: text/event-stream`).
4. Armazena a referência de resposta no mapa global de conexões ativas: `activeSseConnections.set(jobId, reply)`.
5. Inicia um temporizador de heartbeat (envia `: heartbeat\n\n` a cada 15s para evitar desconexão de proxies).
6. Registra listeners de desconexão (`request.raw.on('close')`) para remover a conexão do mapa e limpar o interval do heartbeat em caso de desconexão prematura do cliente.

---

## Casos de Borda e Erros

| Cenário | Comportamento Esperado |
| :--- | :--- |
| `jobId` malformado | Retorna `400 Bad Request` instantaneamente |
| Cliente fecha a aba do navegador | O evento `close` remove a conexão do `activeSseConnections` e cancela o heartbeat |
| Webhook responde antes de o cliente conectar ao SSE | O webhook armazena o resultado temporariamente ou emite erro se a conexão não for estabelecida dentro do timeout máximo |
