---
type: Contract
title: Contrato da API psychnote-core (FastAPI Assíncrono + ChromaDB)
description: Endpoints, payloads, schemas e comportamentos da API do psychnote-core na arquitetura assíncrona.
timestamp: 2026-08-08T19:00:00-03:00
status: active
version: 2.0.0
resource: ../../../psychnote-core/main.py
related:
  - ./bff-api.md
  - ../domain/clinical-triage.md
  - ../decisions/0005-async-sse-triage.md
---

# Contrato da API psychnote-core

Base URL: `http://localhost:8000`

## Regra Fundamental

O MFE nunca chama o `psychnote-core` diretamente. O `psychnote-bff` encapsula as chamadas assíncronas do Core e disponibiliza conexões SSE e APIs REST limpas para a UI React.

---

## 1. Endpoint Assíncrono de Triagem

```http
POST /api/v1/triage/async
Content-Type: application/json
```

### Request Body
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "patient_id": "PAC-001",
  "current_note": "Paciente relata sofrimento intenso e ideação passiva...",
  "callback_url": "http://psychnote-bff:4000/api/webhooks/triage-result"
}
```

### Response `202 Accepted`
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "message": "Triagem enviada para processamento assíncrono."
}
```

---

## 2. Callback Webhook (Core → BFF)

### `POST {callback_url}`
Disparado pelo Core após concluir o pipeline LangGraph e salvar a nota + triagem no ChromaDB:

```json
{
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

## 3. Consulta de Histórico Prontuário (ChromaDB)

```http
GET /api/v1/patients/{patient_id}/history
```

### Response `200 OK`
```json
{
  "patient_id": "PAC-001",
  "total_records": 1,
  "history": [
    {
      "timestamp": "2026-08-08T18:30:00Z",
      "note_text": "Paciente relata sofrimento intenso...",
      "has_triage": true,
      "risk_level": "Moderado",
      "passive_ideation": true,
      "active_ideation": false,
      "red_flags": ["Diagnóstico psiquiátrico instável ativo"],
      "protection_factors": ["Rede de apoio familiar forte"],
      "clinical_justification": "O paciente apresenta ideação suicida passiva...",
      "audit_alerts": ["[RECOMENDAÇÃO]: Para Risco Moderado..."],
      "final_report": "=== PARECER EXECUTIVO DE AUDITORIA CLÍNICA ===\n..."
    }
  ]
}
```
