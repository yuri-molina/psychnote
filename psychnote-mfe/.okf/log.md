---
type: Log
title: Registro de Alterações da Base OKF — psychnote-mfe
description: Diário cronológico append-only de adições, atualizações e depreciações dos artefatos de conhecimento.
timestamp: 2026-08-09T22:45:00-03:00
status: active
---

# Log de Alterações de Conhecimento

Registros ordenados do mais recente para o mais antigo. Tags válidas: [ADDED], [UPDATED], [DEPRECATED], [REMOVED].

## 2026-08-09 (Redirecionamento ao Prontuário e Estado de Triagem em Andamento no MFE)

- **[UPDATED]** `src/views/NewPatientEvolutionView.spec.md`
  - Descrição: Atualizada especificação SDD para a versão 1.2.0 documentando o redirecionamento imediato ao prontuário (`/patients/:patientId/record`) após a submissão, eliminando a tela de resultado intermediário na rota de cadastro.
  - Autor: psychnote-mfe agent

- **[ADDED]** `src/views/PatientRecordView.spec.md`
  - Descrição: Criada especificação SDD v1.1.0 documentando a estrutura do prontuário, a exibição de evoluções recém-salvas e o indicador visual de triagem em andamento ("Análise de Risco em Andamento...").
  - Autor: psychnote-mfe agent

- **[ADDED]** [`contracts/triage-job-status-spec.md`](./contracts/triage-job-status-spec.md)
  - Descrição: Documento de especificação de requisitos de contratos para desenvolvimento no `psychnote-bff` e `psychnote-core` (Endpoints de status de job `GET /api/triage/jobs/:jobId/status`, status de job ativo no prontuário `active_job_status` e persistência imediata da evolução).
  - Autor: psychnote-mfe agent

- **[UPDATED]** `src/views/TriageLayout.spec.md`
  - Descrição: Atualizada especificação para a versão 2.1.0 documentando a persistência automática de evoluções para pacientes pré-existentes, atualização do nível de risco e invalidação de cache via TanStack Query.
  - Autor: psychnote-mfe agent

- **[UPDATED]** [`contracts/bff-api.md`](./contracts/bff-api.md)
  - Descrição: Atualizado para o contrato versão 2.2.0, documentando o aliasing de rotas (`POST /api/triage` e `POST /triage`) e a obrigatoriedade de injeção manual de cabeçalhos de CORS (`Access-Control-Allow-Origin`, `Access-Control-Allow-Credentials`) nas respostas brutas de streaming SSE (`GET /api/triage/stream/:jobId`).
  - Autor: psychnote-mfe agent

- **[UPDATED]** `src/views/NewPatientEvolutionView.spec.md`
  - Descrição: Atualizada especificação SDD para a versão 1.1.0 documentando o cabeçalho dinâmico em estado de sucesso (`<Nome Completo>` / `Análise de risco por IA.`), a navegação dinâmica do botão `"Voltar"` (`navigate(-1)`) e os novos rótulos de identificação.
  - Autor: psychnote-mfe agent

- **[ADDED]** `src/views/LandingView.spec.md`
  - Descrição: LayoutSpec da nova tela inicial LandingView com CTAs de alta conversão para "Evoluir Novo Paciente" e "Listar Pacientes".
  - Autor: psychnote-mfe agent

- **[UPDATED]** [`architecture/overview.md`](./architecture/overview.md)
  - Descrição: Atualizado mapa de rotas (`/`, `/patients`, `/patients/new-evolution`, `/patients/:id/record`, `/patients/:id/triage`).
  - Autor: psychnote-mfe agent

- **[UPDATED]** [`architecture/component-tree.md`](./architecture/component-tree.md)
  - Descrição: Atualizada a hierarquia de componentes e tabela de responsabilidades com LandingView e NewPatientEvolutionView.
  - Autor: psychnote-mfe agent

- **[UPDATED]** [`index.md`](./index.md)
  - Descrição: Atualizada versão para 3.2.0.
  - Autor: psychnote-mfe agent

## 2026-08-08 (Arquitetura Assíncrona + SSE Stream)

- **[ADDED]** [`decisions/0005-async-sse-triage.md`](./decisions/0005-async-sse-triage.md)
  - Descrição: ADR documentando a decisão de substituir o modelo síncrono bloqueante pelo modelo assíncrono com HTTP 202 Accepted + conexões EventSource (SSE stream) via `/api/triage/stream/:jobId`.
  - Autor: psychnote-mfe agent

- **[UPDATED]** [`contracts/bff-api.md`](./contracts/bff-api.md)
  - Descrição: Atualizado para o contrato versão 2.0.0, incluindo `POST /api/triage` (202 Accepted), `GET /api/triage/stream/:jobId` (evento `triage_completed`) e `GET /api/patients/:id/history`.
  - Autor: psychnote-mfe agent

- **[UPDATED]** [`contracts/core-api.md`](./contracts/core-api.md)
  - Descrição: Atualizado para o contrato versão 2.0.0 do `psychnote-core` com suporte a `POST /api/v1/triage/async`, callback Webhook e consulta ao ChromaDB.
  - Autor: psychnote-mfe agent

- **[UPDATED]** [`architecture/overview.md`](./architecture/overview.md)
  - Descrição: Atualizada a visão geral e diagrama de sequência Mermaid para refletir o fluxo de 3 fases (HTTP 202 -> EventSource Stream -> Webhook Callback -> Push `triage_completed`).
  - Autor: psychnote-mfe agent

- **[UPDATED]** [`index.md`](./index.md)
  - Descrição: Atualizado para versão 3.1.0 com catálogo revisado de ADRs e contratos assíncronos.
  - Autor: psychnote-mfe agent
