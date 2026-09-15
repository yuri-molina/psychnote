---
type: Contract
title: Contrato do BFF — psychnote-bff (Consumido pelo MFE)
description: Endpoints, requisitos de CORS, mensagens de streaming SSE e schemas que o MFE consome do BFF na arquitetura assíncrona.
timestamp: 2026-08-09T01:55:00-03:00
status: active
version: 2.2.0
related:
  - ./core-api.md
  - ../decisions/0004-zod-runtime-validation.md
  - ../decisions/0005-async-sse-triage.md
---

# Contrato do BFF (Consumido pelo MFE)

Base URL (variável de ambiente): `VITE_BFF_URL=http://localhost:4000`

## Regra de Ouro

O MFE nunca chama o `psychnote-core` diretamente. Todos os requests HTTP e conexões SSE do MFE apontam para o BFF (`psychnote-bff`).

---

## 1. Listagem de Pacientes

```http
GET /api/patients
GET /patients
```

### Resposta `200 OK`
```json
[
  {
    "patient_id": "PAC-001",
    "name": "Maria Silva",
    "last_triage_date": "2026-08-05",
    "last_risk_level": "Moderado"
  }
]
```

---

## 2. Submissão Assíncrona de Triagem (HTTP 202 Accepted)

```http
POST /api/triage
POST /triage
Content-Type: application/json
```

### Request Payload (`TriageAsyncRequestSchema`)
```json
{
  "patient_id": "PAC-001",
  "current_note": "Paciente relata sofrimento intenso e ideação passiva..."
}
```

### Resposta `202 Accepted` (`TriageAsyncResponseSchema`)
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "message": "Triagem aceita para processamento assíncrono."
}
```

---

## 3. Conexão Server-Sent Events (SSE Stream)

```http
GET /api/triage/stream/:jobId
GET /triage/stream/:jobId
Headers:
  Accept: text/event-stream
  Cache-Control: no-cache
```

### Requisito Crítico de CORS em Respostas Brutas (Raw Stream)
Como a rota SSE escreve diretamente no fluxo bruto do Node (`reply.raw`), o BFF deve aplicar explicitamente os cabeçalhos de CORS na resposta bruta antes do handshake:
```http
Access-Control-Allow-Origin: http://localhost:5001 (ou Origin solicitante)
Access-Control-Allow-Credentials: true
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
```

### Evento Emitido: `triage_completed`
Quando o `psychnote-core` finaliza a inferência do LLM e a gravação no ChromaDB, o BFF dispara este evento no canal SSE do `jobId`:

```http
event: triage_completed
data: {
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "patient_id": "PAC-001",
  "status": "completed",
  "risk_assessment": {
    "risk_level": "Moderado",
    "passive_ideation": true,
    "active_ideation": false,
    "red_flags": ["Diagnóstico psiquiátrico instável ativo"],
    "protection_factors": ["Rede de apoio familiar forte"],
    "clinical_justification": "O paciente apresenta ideação suicida passiva..."
  },
  "audit_alerts": [
    "[RECOMENDAÇÃO]: Para Risco Moderado, as diretrizes exigem..."
  ],
  "final_report": "=== PARECER EXECUTIVO DE AUDITORIA CLÍNICA ===\n..."
}
```

---

## 4. Histórico Prontuário de Paciente

```http
GET /api/patients/:patientId/record
GET /api/patients/:patientId/history
```

### Resposta `200 OK` (`PatientRecordSchema`)
```json
{
  "patient_id": "PAC-001",
  "name": "Maria Silva",
  "total_records": 1,
  "history": [
    {
      "id": "TR-101",
      "date": "2026-08-08T18:30:00Z",
      "risk_level": "Moderado",
      "current_note": "Paciente relata sofrimento intenso...",
      "red_flags": ["Diagnóstico psiquiátrico instável ativo"],
      "protection_factors": ["Rede de apoio familiar forte"],
      "clinical_justification": "O paciente apresenta ideação suicida passiva...",
      "audit_alerts": ["[RECOMENDAÇÃO]: Para Risco Moderado..."],
      "final_report": "=== PARECER EXECUTIVO DE AUDITORIA CLÍNICA ==="
    }
  ]
}
```

---

## Respostas de Erro Esperadas

| Código | Condição |
| :--- | :--- |
| `400` | Payload inválido (patient_id ausente, current_note < 10 chars) |
| `404` | Job ID inexistente na rota SSE |
| `502` | BFF não conseguiu se comunicar com o Core para registrar o job |
| `500` | Erro interno de servidor |
