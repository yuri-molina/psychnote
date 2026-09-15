---
type: Contract
title: Especificação dos Contratos de API Assíncrona, Webhook e Status de Jobs — psychnote-core
description: Contratos de requisição e resposta do endpoint assíncrono, consulta de status de job, histórico e callback Webhook.
timestamp: 2026-08-09T23:20:00-03:00
status: active
version: 1.2.0
owner: psychnote-core
---

# Contratos de API — psychnote-core

## 1. Endpoint Assíncrono de Triagem

### `POST /api/v1/triage/async`

Recebe a nota clínica, o identificador do paciente, o `job_id` gerado pelo BFF e a URL de callback.

#### Comportamento Imediato no Aceite:
1. Registra o job no registro in-memory com status `"processing"`.
2. Salva imediatamente a nota clínica no ChromaDB com `has_triage: false` e `job_status: "processing"`.
3. Dispara a execução do LangGraph em background worker.
4. Retorna HTTP `202 Accepted`.

#### Request Body (`application/json`)
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "patient_id": "PAC-001",
  "current_note": "Paciente relata sofrimento intenso e ideação passiva...",
  "callback_url": "http://psychnote-bff:3000/api/webhooks/triage-result"
}
```

#### Response (`202 Accepted`)
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "message": "Triagem enviada para processamento assíncrono."
}
```

---

## 2. Endpoint de Consulta de Status do Job de Triagem

### `GET /api/v1/triage/jobs/{job_id}`

Permite ao BFF ou MFE consultar o progresso de um job de triagem em processamento ou finalizado.

#### Response (`200 OK` — Em Processamento)
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "patient_id": "PAC-001",
  "status": "processing",
  "created_at": "2026-08-09T23:15:00Z",
  "risk_assessment": null,
  "audit_alerts": [],
  "error_message": null
}
```

#### Response (`200 OK` — Concluído)
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "patient_id": "PAC-001",
  "status": "completed",
  "created_at": "2026-08-09T23:15:00Z",
  "risk_assessment": {
    "risk_level": "Moderado",
    "passive_ideation": true,
    "active_ideation": false,
    "red_flags": ["Diagnóstico psiquiátrico instável ativo"],
    "protection_factors": ["Rede de apoio familiar forte"],
    "clinical_justification": "O paciente apresenta ideação suicida passiva..."
  },
  "audit_alerts": [
    "[RECOMENDAÇÃO]: Para Risco Moderado, as diretrizes exigem acionar a família..."
  ],
  "error_message": null
}
```

#### Response (`404 Not Found`)
```json
{
  "detail": "Job '123e4567-e89b-12d3-a456-426614174000' não encontrado. O job pode ter expirado ou o ID é inválido."
}
```

---

## 3. Callback HTTP (Webhook Disparado pelo Core ao BFF)

### `POST {callback_url}`

Payload enviado pelo `psychnote-core` para o `psychnote-bff` assim que a inferência do LLM e a gravação no ChromaDB forem finalizadas.

#### Request Body (`application/json`)
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
    "[RECOMENDAÇÃO]: Para Risco Moderado, as diretrizes exigem acionar a família..."
  ],
  "final_report": "=== PARECER EXECUTIVO DE AUDITORIA CLÍNICA ===\n..."
}
```

---

## 4. Endpoint de Consulta de Histórico com Triagens Pré-computadas

### `GET /api/v1/patients/{patient_id}/history`

Retorna todas as evoluções clínicas salvas no ChromaDB para o paciente especificado, contendo a triagem e pareceres pré-computados, sem acionar o LLM. Registros recém-criados em processamento aparecem com `has_triage: false`.

#### Response (`200 OK`)
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
