---
type: Index
title: Base de Conhecimento — psychnote-core
description: Catálogo principal e hub de navegação da base OKF do motor de IA local do PsicRE-AI.
timestamp: 2026-08-08T18:38:00-03:00
status: active
version: 1.1.0
owner: psychnote-core
---

# Base de Conhecimento — psychnote-core

O **psychnote-core** é o motor de inteligência artificial da plataforma PsicRE-AI. É responsável pela execução 100% local (Edge AI) de modelos LLM (`llama3:8b-instruct-q4_K_M` via Ollama), pela orquestração do pipeline de triagem e auditoria clínica com LangGraph, pela gestão do banco vetorial isolado ChromaDB com governança LGPD, e pela notificação assíncrona orientada a eventos (Webhook).

---

## Guia de Navegação para Agentes de IA

Use este índice como ponto de entrada para qualquer tarefa de leitura, geração ou modificação de código no repositório.

- **Entender a arquitetura assíncrona orientada a eventos** → [`architecture/overview.md`](./architecture/overview.md)
- **Entender a decisão da arquitetura Assíncrona + Webhook + SSE** → [`decisions/0001-async-webhook-sse-architecture.md`](./decisions/0001-async-webhook-sse-architecture.md)
- **Entender os contratos de API Assíncrona e Webhook** → [`contracts/triage-async-api.md`](./contracts/triage-async-api.md)

---

## Catálogo OKF

### Raiz e Arquitetura

| Artefato | Tipo | Descrição |
|---|---|---|
| [`architecture/overview.md`](./architecture/overview.md) | Architecture | Visão geral do pipeline LangGraph, execução assíncrona em background e persistência no ChromaDB |

### Decisões Arquiteturais (ADRs)

| Artefato | Tipo | Descrição |
|---|---|---|
| [`decisions/0001-async-webhook-sse-architecture.md`](./decisions/0001-async-webhook-sse-architecture.md) | ADR | Decisão de arquitetura para triagem assíncrona via HTTP 202, Webhook callback e persistência de metadados |

### Contratos de API

| Artefato | Tipo | Descrição |
|---|---|---|
| [`contracts/triage-async-api.md`](./contracts/triage-async-api.md) | Contract | Contratos dos endpoints `POST /api/v1/triage/async`, `GET /api/v1/patients/{id}/history` e do Webhook Callback |

### Pesquisa, Benchmarks e Estudo Comparativo (TCC)

| Artefato | Tipo | Descrição |
|---|---|---|
| [`../docs/TCC_MAPA_DOCUMENTACAO_E_CRONOLOGIA.md`](../docs/TCC_MAPA_DOCUMENTACAO_E_CRONOLOGIA.md) | Master Index | Mapa mestre de cronologia, linhagem e de-para entre capítulos do TCC e arquivos do repositório |
| [`../docs/TCC_BENCHMARK_RESULTS.md`](../docs/TCC_BENCHMARK_RESULTS.md) | Benchmark | Resultados da calibração de threads e ciclo iterativo de prompt v1→v4 (Ollama e Gemini) |
| [`../docs/TCC_ESTUDO_COMPARATIVO_EDGE_VS_CLOUD.md`](../docs/TCC_ESTUDO_COMPARATIVO_EDGE_VS_CLOUD.md) | Study | Relatório formal consolidado do estudo comparativo Edge AI vs. Cloud AI (EXP-01 a EXP-04) |
| [`../docs/TCC_SESSAO_HANDOFF.md`](../docs/TCC_SESSAO_HANDOFF.md) | Handoff | Roteiro de continuidade da escrita da dissertação de MBA |
