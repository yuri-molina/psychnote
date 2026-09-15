---
type: Log
title: Registro de Alterações da Base OKF — psychnote-bff
description: Diário cronológico append-only de adições, atualizações e depreciações dos artefatos de conhecimento.
timestamp: 2026-08-07T16:55:00-03:00
status: active
---

# Registro de Alterações da Base OKF — psychnote-bff

> Este arquivo é **append-only**. Nunca edite ou remova entradas existentes. Adicione novas entradas sempre no topo, dentro da seção de data correspondente.

## 2026-08-08

- **[ADDED]** `.okf/decisions/0005-async-webhook-sse-architecture.md` — ADR registrando a decisão de substituir o modelo síncrono/long-polling por submissão assíncrona HTTP 202 Accepted, recebimento de Webhook do Core e streaming SSE ao MFE. | autor: psychnote-bff agent

- **[UPDATED]** `.okf/index.md` — Atualização do catálogo OKF com referências ao ADR-0005, novos contratos e specs SDD do fluxo assíncrono (stream e webhook). | autor: psychnote-bff agent

- **[UPDATED]** `.okf/glossary.md` — Inclusão de novos termos técnicos da arquitetura assíncrona (HTTP 202 Accepted, Job ID UUIDv4, SSE, EventSource, Webhook Callback, Active Connection Map, Heartbeat). | autor: psychnote-bff agent

- **[UPDATED]** `.okf/architecture/overview.md` — Atualização do diagrama C4, diagramas de sequência de 3 fases e adição da gestão do mapa de conexões SSE (`activeSseConnections`) e recepção do Webhook do Core às responsabilidades do BFF. | autor: psychnote-bff agent

---

## 2026-08-07

- **[ADDED]** `.okf/index.md` — Catálogo principal e hub de navegação da base OKF. Inclui guia de navegação para agentes de IA, catálogo de artefatos por categoria e catálogo de specs SDD co-localizadas. | autor: psychnote-bff agent

- **[ADDED]** `.okf/glossary.md` — Dicionário de termos do domínio clínico (Triagem de Risco, Nota Clínica, Nível de Risco, Red Flags, Fatores de Proteção, Ideação Passiva, Ideação Ativa, Auditoria de Conduta, Parecer Executivo, LGPD) e do domínio técnico (BFF, MFE, Core, Fastify, fastify-type-provider-zod, @fastify/cors, @fastify/helmet, AbortController, Long-polling, 502, 504, Payload Amigável de Erro, Crash-free, Out-of-Scope). | autor: psychnote-bff agent

- **[ADDED]** `.okf/log.md` — Registro de alterações append-only da base OKF. | autor: psychnote-bff agent

- **[ADDED]** `.okf/architecture/overview.md` — *(planejado)* Visão geral da arquitetura MFE → BFF → Core. | autor: psychnote-bff agent

- **[ADDED]** `.okf/architecture/folder-structure.md` — *(planejado)* Estrutura de pastas e convenções de módulos Fastify. | autor: psychnote-bff agent

- **[ADDED]** `.okf/decisions/0001-fastify-framework.md` — *(planejado)* ADR: Adoção do Fastify como framework HTTP. | autor: psychnote-bff agent

- **[ADDED]** `.okf/decisions/0002-zod-contract-validation.md` — *(planejado)* ADR: Validação de contratos com Zod via fastify-type-provider-zod. | autor: psychnote-bff agent

- **[ADDED]** `.okf/decisions/0003-timeout-and-resilience.md` — *(planejado)* ADR: Estratégia de timeout com AbortController e resiliência contra falhas do Core. | autor: psychnote-bff agent

- **[ADDED]** `.okf/decisions/0004-cors-and-helmet.md` — *(planejado)* ADR: Política de CORS e hardening de segurança com Helmet. | autor: psychnote-bff agent

- **[ADDED]** `.okf/contracts/core-api.md` — *(planejado)* Contratos dos endpoints do Core consumidos pelo BFF. | autor: psychnote-bff agent

- **[ADDED]** `.okf/contracts/bff-api.md` — *(planejado)* Contratos dos endpoints do BFF expostos ao MFE. | autor: psychnote-bff agent

- **[ADDED]** `.okf/domain/clinical-triage.md` — *(planejado)* Modelo de domínio da triagem clínica de risco. | autor: psychnote-bff agent

- **[ADDED]** `.okf/playbooks/project-setup.md` — *(planejado)* Playbook de configuração do ambiente de desenvolvimento local. | autor: psychnote-bff agent

- **[ADDED]** `src/routes/triage/triage.spec.md` — *(planejado)* RouteSpec da rota `POST /triage`. | autor: psychnote-bff agent

- **[ADDED]** `src/routes/patients/patients.spec.md` — *(planejado)* RouteSpec da rota `GET /patients`. | autor: psychnote-bff agent

- **[ADDED]** `src/plugins/core-client/CoreClient.spec.md` — *(planejado)* ModuleSpec do cliente HTTP para o Core. | autor: psychnote-bff agent

- **[ADDED]** `src/plugins/error-handler/ErrorHandler.spec.md` — *(planejado)* ModuleSpec do handler global de erros. | autor: psychnote-bff agent
