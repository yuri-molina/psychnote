---
type: Architecture
title: Visão Geral da Arquitetura — psychnote-mfe
description: Diagrama de containers C4, mapa de navegação e fluxo assíncrono MFE -> BFF -> Core com EventSource (SSE) do Psych Note.
timestamp: 2026-08-09T01:00:00-03:00
status: active
version: 2.1.0
related:
  - ./module-federation.md
  - ../contracts/core-api.md
  - ../contracts/bff-api.md
  - ../decisions/0005-async-sse-triage.md
---

# Visão Geral da Arquitetura

## Diagrama de Containers (C4 Level 2)

```
Browser (localhost)
    |
    |  HTTP REST / SSE Stream (EventSource)
    v
psychnote-mfe (React + Vite)       [este repositório]
    localhost:5001 (dev/preview)
    ├── LandingView (/)            [Menu Inicial: Evoluir Novo Paciente | Listar Pacientes]
    ├── PatientListView (/patients) [Listagem de Pacientes Cadastrados]
    ├── NewPatientEvolutionView    [Cadastro de Novo Paciente + Evolução]
    ├── PatientRecordView          [Prontuário e Histórico de Evoluções]
    └── TriageLayout               [Evolução de Paciente Existente]
    |
    |  HTTP REST (202) + SSE Stream  ->  localhost:4000
    v
psychnote-bff                      [BFF Fastify com mapa SSE]
    |                                 ^
    |  POST /api/v1/triage/async      | Webhook Callback
    v                                 | POST /api/webhooks/triage-result
psychnote-core (FastAPI + LangGraph) -+
    |              |
    v              v
  Ollama        ChromaDB
  :11434        ./chroma_db
  llama3:8b     (local persistente)
```

## Mapa de Rotas e Fluxo do Usuário

```
[ LandingView (/) ]
   ├── CTA "Evoluir Novo Paciente"  ──>  [ NewPatientEvolutionView (/patients/new-evolution) ]
   └── CTA "Listar Pacientes"        ──>  [ PatientListView (/patients) ]
                                              ├── Botão "Ver Prontuário"  ──>  [ PatientRecordView (/patients/:id/record) ]
                                              └── Botão "Nova Evolução"   ──>  [ TriageLayout (/patients/:id/triage) ]
```

## Responsabilidades por Camada

### MFE (psychnote-mfe)
- Renderizar o Menu Inicial (`LandingView`) com ações de destaque para evoluir novo paciente ou consultar listagem.
- Coletar cadastro do novo paciente e nota clínica na tela `NewPatientEvolutionView`.
- Renderizar a interface de listagem de pacientes (`PatientListView`), prontuário histórico (`PatientRecordView`) e formulário de evolução (`TriageLayout`).
- Submeter notas clínicas para triagem assíncrona (`POST /api/triage`) e receber `202 Accepted` com `job_id`.
- Abrir conexão SSE (`EventSource`) em `/api/triage/stream/:jobId` para consumir a resposta via evento `triage_completed`.
- Validar contratos de API em runtime com Zod.
- Funcionar de forma autônoma (standalone) e como Remote de Module Federation.
