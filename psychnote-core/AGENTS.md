# AGENTS.md — psychnote-core

Arquivo de instruções mandatórias para todos os agentes de IA que operam neste repositório.
Leia este arquivo integralmente antes de executar qualquer tarefa.

> **Regra de Precedência:** As diretrizes contidas neste arquivo e no [`GEMINI.md`](./GEMINI.md) / [`CLAUDE.md`](./CLAUDE.md) são soberanas e devem ser seguidas sem exceções.

---

## 1. Comandos do Projeto

```bash
# Executar testes automatizados (Pytest)
python3 -m pytest tests/

# Rodar a API FastAPI em ambiente de desenvolvimento
python3 main.py
# ou via Uvicorn direto:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Executar benchmark de performance e SLA
python3 run_thread_benchmark.py

# Executar teste de carga da API
python3 run_test_large.py
```

---

## 2. Regras de Comportamento do Agente

1. **Clean Architecture e Tipagem Estrita:** Toda alteração em código Python deve usar tipagem explícita (`typing`) e modelos Pydantic v2.
2. **Execução 100% Local (Edge AI & LGPD):** NENHUM dado de paciente pode ser enviado para APIs de nuvem pública. Toda inferência roda via Ollama local (`localhost:11434`) com o modelo `llama3:8b-instruct-q4_K_M`.
3. **Isolamento de Dados no ChromaDB:** PROIBIDO criar coleções separadas por paciente no ChromaDB. Usar a coleção única `clinical_records` com **Metadata Filtering** estrito (`where={"patient_id": "ID"}`).
4. **Verificação Obrigatória Pós-Tarefa:** Ao concluir qualquer alteração de código, execute a suíte de testes unitários: `python3 -m pytest tests/`.
5. **Grafo LangGraph Determinístico:** Nós do grafo devem receber e retornar dados totalmente compatíveis com a estrutura `AgentState` (`TypedDict`).
6. **Arquitetura Assíncrona (Event-Driven):**
   - O endpoint de entrada `POST /api/v1/triage/async` responde de forma não-bloqueante com `202 Accepted`.
   - A inferência e a gravação de metadados no ChromaDB ocorrem em background.
   - A notificação final ao BFF é feita via Webhook HTTP POST para a `callback_url` informada.
7. **Consulta de Histórico sem Custo de LLM:** O endpoint `GET /api/v1/patients/{id}/history` lê os resultados de triagens pré-computados diretamente do ChromaDB em < 50ms.

---

## 3. Mapa de Arquivos e Documentação Mestre

- **Base de Conhecimento OKF:** Consulte [`.okf/index.md`](./.okf/index.md).
- **Visão Geral de Arquitetura:** Consulte [`.okf/architecture/overview.md`](./.okf/architecture/overview.md).
- **Contratos de API e Webhook:** Consulte [`.okf/contracts/triage-async-api.md`](./.okf/contracts/triage-async-api.md).
- **Guia Mestre de Integração BFF/MFE:** Consulte [`docs/GUIA_ATUALIZACAO_BFF_MFE.md`](./docs/GUIA_ATUALIZACAO_BFF_MFE.md).
