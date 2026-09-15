---
type: Architecture
title: Visão Geral da Arquitetura — psychnote-core
description: Descrição da arquitetura de triagem assíncrona, orquestração LangGraph via grafo de estados determinístico, registro in-memory de jobs, persistência vetorial e notificações Webhook.
timestamp: 2026-09-08T00:15:00-03:00
status: active
version: 1.3.0
owner: psychnote-core
---

# Visão Geral da Arquitetura — psychnote-core

## 1. Responsabilidade
O **psychnote-core** é o serviço backend de inteligência artificial da plataforma PsicRE-AI. Suas atribuições primárias são:
1. **Triagem Estruturada (Pydantic Zero-Shot):** Classificação do risco de suicídio em 3 eixos (`Baixo`, `Moderado`, `Alto/Iminente`) com extração de *red flags*, fatores de proteção e justificativa sobre a nota aguda.
2. **Contexto Longitudinal (ChromaDB Metadata Filtering):** Recuperação isolada por metadados de histórico (`patient_id`) sem vazamento LGPD, desacoplada da triagem aguda para evitar contaminação atencional do modelo.
3. **Auditoria de Conduta Médica (Árvore de Decisão Determinística):** Verificação determinística baseada em regras clínicas de segurança (CFM/Botega/OMS).
4. **Execução Assíncrona Não-Bloqueante:** Processamento do pipeline LLM em background task via FastAPI, respondendo imediatamente HTTP `202 Accepted` ao BFF e notificando a conclusão através de **Webhook HTTP POST**.
5. **Registro de Status do Job (`_JOB_REGISTRY`):** Rastreamento in-memory do status do job (`processing`, `completed`, `error`) acessível via `GET /api/v1/triage/jobs/{job_id}`.
6. **Pré-Registro Imediato de Evoluções:** Gravação imediata da nota no ChromaDB no momento do aceite (`has_triage: false`, `job_status: "processing"`), permitindo que a UI exiba a evolução imediatamente no prontuário com indicador de triagem em andamento.
7. **Persistência Integrada de Metadados:** Atualização dos resultados de triagem no ChromaDB ao concluir a inferência, permitindo leitura histórica rápida (< 50ms) sem custo de LLM.

---

## 2. Fluxo de Dados e Ciclo de Vida do Job

```
[BFF] ---> POST /api/v1/triage/async ---> [FastAPI Router]
                                                  |
                                                  +---> (1) Registra em _JOB_REGISTRY (status: processing)
                                                  +---> (2) Salva nota no ChromaDB (has_triage: false)
                                                  +---> Retorna 202 Accepted {job_id}
                                                  |
                                                  v
                                      [BackgroundWorker Thread]
                                                  |
                                                  +---> (3) LangGraph Pipeline (LLM Ollama)
                                                  +---> (4) Atualiza _JOB_REGISTRY (status: completed)
                                                  +---> (5) Sobrescreve ChromaDB (has_triage: true + metadados)
                                                  +---> (6) Dispara POST (Webhook) para callback_url
```

---

## 3. Componentes Principais

| Componente | Módulo | Função |
|---|---|---|
| **API Router & Registry** | `src/api/v1/triage.py` | Recebe requisições HTTP, gerencia `_JOB_REGISTRY`, executa tasks assíncronas e expõe rotas de histórico e status do job |
| **Orquestrador de Grafo** | `orchestrator/orchestrator_graph.py` | Grafo determinístico de 4 nós (`analyze_risk`, `retrieve_history`, `audit_conduct`, `generate_report`) |
| **Monitor Clínico** | `analytics/clinical_monitor.py` | Interface Pydantic rígida com Ollama `llama3:8b-instruct-q4_K_M` |
| **Banco Vetorial & Metadados** | `database/patient_manager.py` | Persistência ChromaDB com metadados de triagem e filtro LGPD por paciente |
