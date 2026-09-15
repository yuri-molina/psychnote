---
type: Index
title: Base de Conhecimento — psychnote-bff
description: Catálogo principal e hub de navegação da base OKF do Backend for Frontend do PsicRE-AI.
timestamp: 2026-08-08T18:48:00-03:00
status: active
version: 1.1.0
owner: psychnote-bff
---

# Base de Conhecimento — psychnote-bff

O **psychnote-bff** é o Backend for Frontend da arquitetura MFE → BFF → Core do projeto PsicRE-AI. Atua como roteador seguro e gerenciador de eventos em tempo real (HTTP 202 Accepted + SSE Stream + Webhook Callback) entre o **psychnote-mfe** (porta 5001) e o **psychnote-core** (porta 8000), adicionando as camadas de segurança (CORS, Helmet), validação de contratos (Zod), gerenciamento de conexões ativas (`activeSseConnections`) e tratamento padronizado de falhas de upstream. O BFF não possui banco de dados próprio, não renderiza views HTML e não executa inferência de IA.

---

## Guia de Navegação para Agentes de IA

Use este índice como ponto de entrada para qualquer tarefa de leitura, geração ou modificação de código no repositório.

- **Entender o domínio clínico e os termos técnicos** → [`glossary.md`](./glossary.md)
- **Entender a arquitetura geral do serviço** → [`architecture/overview.md`](./architecture/overview.md)
- **Entender a estrutura de pastas e módulos** → [`architecture/folder-structure.md`](./architecture/folder-structure.md)
- **Entender por que o Fastify foi escolhido** → [`decisions/0001-fastify-framework.md`](./decisions/0001-fastify-framework.md)
- **Entender a estratégia de validação com Zod** → [`decisions/0002-zod-contract-validation.md`](./decisions/0002-zod-contract-validation.md)
- **Entender a estratégia de timeout e resiliência** → [`decisions/0003-timeout-and-resilience.md`](./decisions/0003-timeout-and-resilience.md)
- **Entender as políticas de CORS e Helmet** → [`decisions/0004-cors-and-helmet.md`](./decisions/0004-cors-and-helmet.md)
- **Entender a migração para a arquitetura assíncrona (HTTP 202 + Webhook + SSE)** → [`decisions/0005-async-webhook-sse-architecture.md`](./decisions/0005-async-webhook-sse-architecture.md)
- **Entender os contratos expostos pelo BFF ao MFE** → [`contracts/bff-api.md`](./contracts/bff-api.md)
- **Entender os contratos consumidos pelo BFF do Core** → [`contracts/core-api.md`](./contracts/core-api.md)
- **Entender o modelo de domínio de triagem clínica** → [`domain/clinical-triage.md`](./domain/clinical-triage.md)
- **Configurar o ambiente de desenvolvimento** → [`playbooks/project-setup.md`](./playbooks/project-setup.md)
- **Implementar ou revisar a rota POST /api/triage** → [`src/routes/triage/triage.spec.md`](../src/routes/triage/triage.spec.md)
- **Implementar ou revisar a rota SSE GET /api/triage/stream/:jobId** → [`src/routes/triage/stream.spec.md`](../src/routes/triage/stream.spec.md)
- **Implementar ou revisar o Webhook POST /api/webhooks/triage-result** → [`src/routes/webhooks/webhook.spec.md`](../src/routes/webhooks/webhook.spec.md)
- **Implementar ou revisar a rota GET /patients** → [`src/routes/patients/patients.spec.md`](../src/routes/patients/patients.spec.md)
- **Implementar ou revisar o cliente HTTP do Core** → [`src/plugins/core-client/CoreClient.spec.md`](../src/plugins/core-client/CoreClient.spec.md)
- **Implementar ou revisar o handler global de erros** → [`src/plugins/error-handler/ErrorHandler.spec.md`](../src/plugins/error-handler/ErrorHandler.spec.md)

---

## Catálogo OKF

### Raiz

| Artefato | Tipo | Descrição |
|---|---|---|
| [`glossary.md`](./glossary.md) | Glossary | Dicionário de termos do domínio clínico e técnico do psychnote-bff |

### Arquitetura

| Artefato | Tipo | Descrição |
|---|---|---|
| [`architecture/overview.md`](./architecture/overview.md) | Architecture | Visão geral da arquitetura MFE → BFF → Core, diagramas de 3 fases, mapa SSE e responsabilidades |
| [`architecture/folder-structure.md`](./architecture/folder-structure.md) | Architecture | Estrutura de pastas do repositório e convenções de módulos Fastify |

### Decisões Arquiteturais (ADRs)

| Artefato | Tipo | Descrição |
|---|---|---|
| [`decisions/0001-fastify-framework.md`](./decisions/0001-fastify-framework.md) | ADR | Justificativa para adoção do Fastify como framework HTTP |
| [`decisions/0002-zod-contract-validation.md`](./decisions/0002-zod-contract-validation.md) | ADR | Justificativa para uso do Zod via fastify-type-provider-zod na validação de contratos |
| [`decisions/0003-timeout-and-resilience.md`](./decisions/0003-timeout-and-resilience.md) | ADR | Estratégia de timeout com AbortController e tratamento de falhas do Core |
| [`decisions/0004-cors-and-helmet.md`](./decisions/0004-cors-and-helmet.md) | ADR | Política de CORS (@fastify/cors) e hardening de segurança (@fastify/helmet) |
| [`decisions/0005-async-webhook-sse-architecture.md`](./decisions/0005-async-webhook-sse-architecture.md) | ADR | Justificativa e arquitetura assíncrona orientada a eventos (HTTP 202 + Webhook Callback + SSE Stream) |

### Contratos de API

| Artefato | Tipo | Descrição |
|---|---|---|
| [`contracts/core-api.md`](./contracts/core-api.md) | Contract | Contratos dos endpoints do psychnote-core consumidos pelo BFF (assíncrono e webhook) |
| [`contracts/bff-api.md`](./contracts/bff-api.md) | Contract | Contratos dos endpoints do BFF expostos ao psychnote-mfe (HTTP 202, SSE Stream e Histórico) |

### Modelo de Domínio

| Artefato | Tipo | Descrição |
|---|---|---|
| [`domain/clinical-triage.md`](./domain/clinical-triage.md) | Domain | Modelo de domínio da triagem clínica de risco: entidades, fluxo e invariantes |

### Playbooks

| Artefato | Tipo | Descrição |
|---|---|---|
| [`playbooks/project-setup.md`](./playbooks/project-setup.md) | Playbook | Passo a passo para configuração do ambiente de desenvolvimento local |

---

## Catálogo de Specs SDD (co-localizadas em `src/`)

Specs de baixo nível co-localizadas com o código-fonte. Cada spec descreve a interface, o comportamento esperado e os critérios de aceitação de um módulo ou rota específica.

| Artefato | Tipo | Descrição |
|---|---|---|
| [`src/routes/triage/triage.spec.md`](../src/routes/triage/triage.spec.md) | RouteSpec | Especificação da rota `POST /api/triage`: geração de `job_id`, validação Zod e repasse HTTP 202 ao MFE |
| [`src/routes/triage/stream.spec.md`](../src/routes/triage/stream.spec.md) | RouteSpec | Especificação da rota SSE `GET /api/triage/stream/:jobId`: registro no `activeSseConnections`, Heartbeats e evento `triage_completed` |
| [`src/routes/webhooks/webhook.spec.md`](../src/routes/webhooks/webhook.spec.md) | RouteSpec | Especificação da rota Webhook `POST /api/webhooks/triage-result`: recepção do resultado do Core, push via SSE e cleanup |
| [`src/routes/patients/patients.spec.md`](../src/routes/patients/patients.spec.md) | RouteSpec | Especificação das rotas de pacientes `GET /patients` e `GET /patients/:id/record` |
| [`src/plugins/core-client/CoreClient.spec.md`](../src/plugins/core-client/CoreClient.spec.md) | ModuleSpec | Especificação do cliente HTTP para o Core em modo assíncrono (`POST /api/v1/triage/async`) |
| [`src/plugins/error-handler/ErrorHandler.spec.md`](../src/plugins/error-handler/ErrorHandler.spec.md) | ModuleSpec | Especificação do handler global de erros: payload padronizado, mapeamento de status HTTP e premissa crash-free |

