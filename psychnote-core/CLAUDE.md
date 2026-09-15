# CLAUDE.md — psychnote-core

Guia de contexto e comandos rápidos para o assistente Claude Code ao atuar no repositório `psychnote-core`.

## Visão Geral
O **psychnote-core** é a engine de IA local do projeto PsicRE-AI (Plataforma Edge AI para Triagem Estruturada e Auditoria de Risco de Suicídio via Grafos de Estado Determinísticos).

## Comandos Principais
- **Testes Unitários:** `python3 -m pytest tests/`
- **Iniciar Servidor API:** `python3 main.py`
- **Verificar Ollama Local:** `curl -s http://localhost:11434/api/tags`

## Diretrizes de Código
1. **Tipagem Pydantic v2:** Todos os contratos da API e classificações do LLM utilizam esquemas Pydantic rígidos.
2. **LangGraph:** Modificações nos nós do grafo em `orchestrator/orchestrator_graph.py` (ou alias `orchestrator/rag_logic.py`) devem obrigatoriamente manter compatibilidade de chaves no `AgentState`.
3. **Persistência Vetorial LGPD:** A gravação e busca no ChromaDB (`database/patient_manager.py`) usam filtro estrito por `patient_id` nos metadados da coleção unificada `clinical_records`.
4. **Arquitetura Event-Driven Assíncrona:** A entrada principal de triagem opera de forma assíncrona (`POST /api/v1/triage/async`) respondendo `202 Accepted` e notificando o término via Webhook Callback ao BFF.
5. **Documentação OKF:** Leia sempre [`.okf/index.md`](./.okf/index.md) e [`docs/GUIA_ATUALIZACAO_BFF_MFE.md`](./docs/GUIA_ATUALIZACAO_BFF_MFE.md) antes de refatorar fluxos.
