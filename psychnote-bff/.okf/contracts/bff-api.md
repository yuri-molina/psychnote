---
type: Contract
title: Contrato da API psychnote-bff (Fastify) — Exposto ao MFE
description: Endpoints, schemas e comportamentos que o psychnote-bff expõe para consumo exclusivo do psychnote-mfe e para recebimento de webhooks do psychnote-core.
timestamp: 2026-08-08T18:50:00-03:00
status: active
version: 2.0.0
related:
  - ./core-api.md
  - ../decisions/0002-zod-contract-validation.md
  - ../decisions/0003-timeout-and-resilience.md
---

# Contrato da API psychnote-bff (Fastify) — Exposto ao MFE

## Visão Geral

- **Base URL:** `http://localhost:4000`
- **Framework:** Fastify (Node.js / TypeScript)
- **Validação de schema:** fastify-type-provider-zod
- **Comunicação em Tempo Real:** Server-Sent Events (SSE)

> **Regra de Ouro:** O MFE **nunca** chama o psychnote-core diretamente. Todos os requests originados pelo MFE apontam exclusivamente para o BFF. O BFF é a única fronteira de integração com o Core.

---

## Endpoints

### GET /health — Health Check

Verifica a disponibilidade do BFF. **Não aciona o Core.**

**Response 200:**

```json
{
  "status": "ok",
  "service": "psychnote-bff",
  "version": "1.0.0"
}
```

---

### GET /patients (e alias GET /api/patients) — Listagem de Pacientes

Retorna a lista de pacientes disponíveis para triagem na PoC.

**Response 200:** Array de objetos com estrutura mínima compatível com o MFE.

**Exemplo de Response 200:**

```json
[
  { "patient_id": "PAC-010", "name": "Paciente PAC-010", "last_triage_date": "2026-08-01", "last_risk_level": "Alto/Iminente" },
  { "patient_id": "PAC-011", "name": "Paciente PAC-011", "last_triage_date": "2026-08-02", "last_risk_level": "Alto/Iminente" },
  { "patient_id": "PAC-012", "name": "Paciente PAC-012", "last_triage_date": "2026-08-03", "last_risk_level": "Alto/Iminente" },
  { "patient_id": "PAC-020", "name": "Paciente PAC-020", "last_triage_date": "2026-08-04", "last_risk_level": "Moderado" },
  { "patient_id": "PAC-021", "name": "Paciente PAC-021", "last_triage_date": "2026-08-04", "last_risk_level": "Moderado" },
  { "patient_id": "PAC-022", "name": "Paciente PAC-022", "last_triage_date": "2026-08-05", "last_risk_level": "Moderado" },
  { "patient_id": "PAC-030", "name": "Paciente PAC-030", "last_triage_date": "2026-08-05", "last_risk_level": "Baixo" },
  { "patient_id": "PAC-031", "name": "Paciente PAC-031", "last_triage_date": "2026-08-06", "last_risk_level": "Baixo" },
  { "patient_id": "PAC-032", "name": "Paciente PAC-032", "last_triage_date": "2026-08-07", "last_risk_level": "Baixo" }
]
```

---

### GET /api/patients/:id/history — Histórico de Triagens do Paciente

Endpoint proxy que consulta o histórico de triagens do paciente persistido no **ChromaDB** através do `psychnote-core`.

- **Path Parameter:** `id` (string, ex: `"PAC-010"`)

#### Response 200 OK

```json
{
  "patient_id": "PAC-010",
  "total_records": 1,
  "history": [
    {
      "triage_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
      "patient_id": "PAC-010",
      "created_at": "2026-08-08T18:30:00Z",
      "current_note": "Paciente relata pensamentos de que seria melhor não estar aqui...",
      "risk_assessment": {
        "risk_level": "Alto/Iminente",
        "passive_ideation": true,
        "active_ideation": false,
        "red_flags": ["Verbalização de desejo de não existir"],
        "protection_factors": ["Vínculo terapêutico estabelecido"],
        "clinical_justification": "A presença de ideação passiva com desesperança persistente..."
      },
      "audit_alerts": [
        "Ideação suicida verbalizada — registrar em prontuário"
      ],
      "final_report": "Paciente PAC-010 apresenta quadro de risco Alto/Iminente..."
    }
  ]
}
```

---

### POST /api/triage — Solicitação de Triagem Assíncrona

Recebe a nota clínica do MFE, valida o payload via Zod, gera um `job_id` (UUIDv4), encaminha a solicitação assíncrona para o Core (`POST /api/v1/triage/async`) e responde imediatamente com status HTTP 202 Accepted.

- **Content-Type:** `application/json`

#### Request Body — `TriageAsyncRequestSchema`

Validado pelo BFF via Zod antes de ser encaminhado ao Core:

```json
{
  "patient_id": "PAC-010",
  "current_note": "Paciente relata sentimentos de inutilidade e desesperança persistentes há duas semanas."
}
```

| Campo          | Tipo   | Obrigatório | Restrições           |
|----------------|--------|-------------|----------------------|
| `patient_id`   | string | sim         | não-vazio            |
| `current_note` | string | sim         | mínimo 10 caracteres |

#### Response 202 Accepted — `TriageAsyncResponseSchema`

```json
{
  "job_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "status": "processing",
  "message": "Triagem aceita para processamento assíncrono."
}
```

---

### GET /api/triage/jobs/:jobId/status — Consulta de Status do Job de Triagem

Permite consultar via polling/revalidação o status e progresso de um job de triagem específico mantido em memória no `jobStore`.

- **Path Parameter:** `jobId` (UUIDv4)
- **Aliases:** `GET /api/triage/jobs/:jobId/status` e `GET /triage/jobs/:jobId/status`

#### Response 200 OK — `JobStatusResponseSchema`

**Job em Processamento:**
```json
{
  "job_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "patient_id": "PAC-010",
  "status": "processing",
  "created_at": "2026-08-09T23:00:00Z",
  "risk_assessment": null,
  "audit_alerts": [],
  "error_message": null
}
```

**Job Concluído:**
```json
{
  "job_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "patient_id": "PAC-010",
  "status": "completed",
  "created_at": "2026-08-09T23:00:00Z",
  "risk_assessment": {
    "risk_level": "Alto/Iminente",
    "passive_ideation": true,
    "active_ideation": false,
    "red_flags": ["Verbalização de desejo de não existir"],
    "protection_factors": ["Vínculo terapêutico"],
    "clinical_justification": "..."
  },
  "audit_alerts": ["..."],
  "error_message": null
}
```

---

### GET /api/triage/stream/:jobId — Canal SSE (Server-Sent Events)

Abre uma conexão de evento em tempo real baseada em Server-Sent Events (SSE) para que o MFE acompanhe o status da triagem associada ao `jobId`.

- **Headers de Resposta:**
  - `Content-Type: text/event-stream`
  - `Cache-Control: no-cache`
  - `Connection: keep-alive`

#### Funcionamento:
1. O BFF registra a conexão HTTP do MFE em um mapa em memória (`Map<jobId, FastifyReply>`).
2. O BFF envia heartbeats periódicos a cada 15 segundos (`: heartbeat\n\n`) para manter a conexão ativa.
3. Quando o webhook do Core notifica a conclusão (`POST /api/webhooks/triage-result`), o BFF emite o evento `triage_completed` contendo o resultado da triagem e encerra a conexão.

#### Eventos Emitidos:

**Evento `triage_completed`:**
```http
event: triage_completed
data: {"job_id":"a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d","patient_id":"PAC-010","status":"completed","risk_assessment":{"risk_level":"Alto/Iminente","passive_ideation":true,"active_ideation":false,"red_flags":["Verbalização de desejo de não existir"],"protection_factors":["Vínculo terapêutico"],"clinical_justification":"..."},"audit_alerts":["Ideação suicida verbalizada — registrar em prontuário"],"final_report":"..."}

```

---

### POST /api/webhooks/triage-result — Recebimento do Webhook do Core

Endpoint de callback invocado exclusivamente pelo `psychnote-core` para notificar a conclusão da triagem.

- **Content-Type:** `application/json`

#### Request Body — `WebhookPayloadSchema`

```json
{
  "job_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "patient_id": "PAC-010",
  "status": "completed",
  "risk_assessment": {
    "risk_level": "Alto/Iminente",
    "passive_ideation": true,
    "active_ideation": false,
    "red_flags": ["Verbalização de desejo de não existir"],
    "protection_factors": ["Vínculo terapêutico"],
    "clinical_justification": "A presença de ideação passiva..."
  },
  "audit_alerts": [
    "Ideação suicida verbalizada — registrar em prontuário"
  ],
  "final_report": "Paciente PAC-010 apresenta quadro de risco Alto/Iminente..."
}
```

#### Comportamento Interno do BFF:
1. Recebe o payload do webhook do Core.
2. Localiza a conexão SSE ativa no mapa pelo `job_id`.
3. Dispara a mensagem com evento `triage_completed` para o MFE via SSE.
4. Remove a conexão do mapa e encerra o stream SSE (`reply.raw.end()`).
5. Retorna `200 OK` ao Core: `{"status": "success", "message": "Webhook processed"}`.

---

## Respostas de Erro do BFF

| Código HTTP | Erro                  | Causa                                                                                           |
|-------------|-----------------------|-------------------------------------------------------------------------------------------------|
| `400`       | Bad Request           | Payload inválido: `patient_id` ausente ou `current_note` < 10 chars. Retornado via Zod.        |
| `404`       | Not Found             | Rota inexistente ou `jobId` não localizado na conexão SSE no momento do recebimento.            |
| `502`       | Bad Gateway           | BFF não conseguiu se comunicar com o Core ao disparar `POST /api/v1/triage/async`.               |
| `500`       | Internal Server Error | Erro interno inesperado no BFF.                                                                 |

**Estrutura do Payload de Erro:**

```json
{
  "statusCode": 400,
  "error": "Bad Request",
  "message": "current_note deve ter no mínimo 10 caracteres."
}
```

---

## Requisitos de CORS

O BFF libera o acesso ao MFE via cabeçalhos CORS.

| Configuração         | Valor                        |
|----------------------|------------------------------|
| Origens permitidas   | `http://localhost:5001`      |
| Métodos permitidos   | `GET`, `POST`, `OPTIONS`     |
| Headers permitidos   | `Content-Type`               |
