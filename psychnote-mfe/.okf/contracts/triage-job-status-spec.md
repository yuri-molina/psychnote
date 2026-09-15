---
type: Contract
title: Especificação de Requisitos para BFF e Core — Status do Job de Triagem e Prontuário com Triagem em Andamento
description: Requisitos funcionais, schemas e justificativa técnica de desenvolvimento no psychnote-bff e psychnote-core para suportar a navegação imediata ao prontuário e indicador visual de triagem em andamento.
timestamp: 2026-08-09T23:05:00-03:00
status: active
version: 1.0.0
owner: psychnote-mfe
related:
  - ./bff-api.md
  - ./core-api.md
  - ../architecture/overview.md
---

# Especificação de Requisitos de Desenvolvimento (BFF & Core)

Este documento especifica os desenvolvimentos necessários nos serviços `psychnote-bff` e `psychnote-core` para atender à nova experiência de usuário do microfrontend (`psychnote-mfe`).

---

## 📋 Contexto e Justificativa da Necessidade

No fluxo atual:
1. Ao submeter uma nova evolução em `NewPatientEvolutionView`, o usuário permanece na mesma tela aguardando a conexão SSE finalizar.
2. Caso navegue para a Listagem de Pacientes ou acesse o Prontuário (`/patients/:patientId/record`), o prontuário não possui mecanismos no contrato de API para identificar que existe um **job de triagem por IA ativamente em processamento** para aquele paciente.

### Nova Experiência Desejada (UX/UI):
1. **Navegação Imediata ao Prontuário**: Ao cadastrar um paciente com sua evolução, o sistema deve abrir imediatamente o prontuário (`/patients/:patientId/record`), com o nome do paciente, a data e o texto da evolução recém-digitada já exibidos.
2. **Indicador de Triagem em Andamento**: Os campos derivados da IA (Nível de Risco, Justificativa Clínica, Red Flags e Alertas de Auditoria) não devem ser preenchidos até a conclusão, exibindo um componente de estado em processamento (*skeleton/spinner* com indicação explícita: *"Análise de Risco por IA em andamento..."*).
3. **Consistência via Listagem de Pacientes**: Sempre que qualquer usuário acessar o prontuário de um paciente pela Listagem de Pacientes, se houver uma triagem em processamento para ele, o prontuário deve carregar exibindo o mesmo indicador de triagem em andamento.

---

## 🛠️ Requisitos de Desenvolvimento no `psychnote-bff`

### 1. Novo Endpoint: Consulta de Status do Job de Triagem
**Endpoint**: `GET /api/triage/jobs/:jobId/status` (e alias `GET /triage/jobs/:jobId/status`)

**Objetivo**: Permitir que a UI consulte via polling/revalidação o progresso de um job específico caso a conexão SSE reconecte ou a página seja atualizada.

#### Resposta `200 OK`
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "patient_id": "PAC-001",
  "status": "processing", // "processing" | "completed" | "error"
  "created_at": "2026-08-09T23:00:00Z",
  "risk_assessment": null, // Presente apenas quando status = "completed"
  "audit_alerts": [],      // Presente apenas quando status = "completed"
  "error_message": null   // Presente apenas quando status = "error"
}
```

---

### 2. Atualização do Contrato de Prontuário: Inclusão de Job Ativo
**Endpoint**: `GET /api/patients/:patientId/record`

**Objetivo**: Informar ao MFE se o paciente possui um job de triagem em andamento ao carregar o prontuário diretamente.

#### Novos Campos no Schema de Resposta (`PatientRecordSchema`):
```json
{
  "patient_id": "PAC-001",
  "name": "Maria Silva",
  "last_triage_date": "2026-08-09",
  "active_job_id": "123e4567-e89b-12d3-a456-426614174000",
  "active_job_status": "processing", // "processing" | null
  "total_records": 1,
  "history": [
    {
      "id": "TR-001",
      "date": "2026-08-09T23:00:00Z",
      "current_note": "HMA: Paciente relata estresse ocupacional...",
      "has_triage": false, // false enquanto a triagem não for finalizada pela IA
      "risk_level": null,  // null enquanto em processamento
      "red_flags": [],
      "protection_factors": [],
      "clinical_justification": null,
      "audit_alerts": []
    }
  ]
}
```

---

### 3. Registro Imediato da Evolução na Submissão (`POST /api/triage`)
Quando o BFF receber o `POST /api/triage`, ele deve registrar a nota e a evolução do paciente no banco/memória **imediatamente** com `has_triage: false` e `active_job_status: "processing"`, antes mesmo de receber o callback final do `psychnote-core`.

---

## 🧠 Requisitos de Desenvolvimento no `psychnote-core`

### 1. Salvar Nota Imediatamente no Aceite (`POST /api/v1/triage/async`)
Ao receber a submissão assíncrona, a API FastAPI deve persistir no ChromaDB/PostgreSQL a nota clínica do paciente marcada com `has_triage: False` e `job_status: "processing"`.

### 2. Endpoint de Status no Core (`GET /api/v1/triage/jobs/{job_id}`)
Expor o status do job para consumo do BFF:
- `200 OK` com `status: "processing"` durante a execução dos nós do LangGraph no Ollama.
- `200 OK` com `status: "completed"` e o payload validado do `risk_assessment` após a conclusão.

---

## 🎯 Resumo da Integração MFE com BFF/Core

```
MFE                                BFF                              CORE
│                                   │                                │
├── POST /api/triage ──────────────>│                                │
│   (cria evolução com status       ├── POST /api/v1/triage/async ──>│ (Inicia LangGraph / Ollama)
│    processing e navega imediatamente)                              │
│                                   │                                │
├── GET /api/patients/:id/record ──>│                                │
│   <── active_job_status: processing ─── (Exibe Skeleton/Banner)    │
│                                   │                                │
├── GET /api/triage/jobs/:id/status>│                                │
│   <── status: processing ─────────┤                                │
│   ... (Polling/SSE)               │<── POST /webhooks ─────────────┤ (Finaliza inferência IA)
│   <── status: completed ──────────┤                                │
└── (Renderiza pareceer concluído)  │                                │
```
