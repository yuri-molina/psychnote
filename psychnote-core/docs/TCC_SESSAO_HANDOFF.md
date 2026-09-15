# TCC PsicRE-AI — Documento de Continuidade de Sessão

> **Última atualização:** 31/07/2026 — 00:15h  
> **Status geral:** Semana 1 (Engenharia) ✅ Concluída | Semana 2 (Escrita) ⚠️ Atrasada  
> **Próxima ação imediata:** Iniciar escrita da **Metodologia** (Dias 6–8 do plano)

---

## 🔴 Contexto Crítico para Toda Sessão

> [!IMPORTANT]
> **Foco do TCC:** O sistema analisa prontuários com foco em **Depressão** (especialmente Depressão Resistente ao Tratamento — DRT, CID F33.2) e risco de suicídio associado. O paciente de referência é **João Silva (JS-2026)**: 10 anos de depressão recorrente, falha em 3 classes de antidepressivos.
>
> **O `ScienceFetcher` (PubMed) NÃO faz parte do fluxo de triagem.** O `ClinicalMonitor` usa critérios consolidados hardcoded no prompt (CFM, Botega, OMS) — não consulta artigos em tempo real. O Módulo Farmacológico está fora do escopo do TCC.

---

## ✅ O que já está Pronto (Semana 1 — Engenharia)

| Entregável | Arquivo | Dado-chave para o TCC |
|-----------|---------|----------------------|
| LLM local otimizado | [`config/engine.py`](file:///mnt/c/Repos/Local/MBA/config/engine.py) | `num_thread=10`, `num_ctx=4096`, modelo `llama3:8b-instruct-q4_K_M` |
| Prompt v2-final (triagem) | [`analytics/clinical_monitor.py`](file:///mnt/c/Repos/Local/MBA/analytics/clinical_monitor.py) | Thresholds CFM/Botega/OMS, 3 eixos (Baixo/Moderado/Alto-Iminente) |
| Avaliação em lote | [`docs/TCC_BENCHMARK_RESULTS.md`](file:///mnt/c/Repos/Local/MBA/docs/TCC_BENCHMARK_RESULTS.md) | Acurácia 77.8%, sensibilidade 100% nas coortes críticas |
| Benchmark de threads | [`run_thread_benchmark.py`](file:///mnt/c/Repos/Local/MBA/run_thread_benchmark.py) | SLA ~40s CPU / 32.43s medido nos testes E2E |
| API FastAPI | [`main.py`](file:///mnt/c/Repos/Local/MBA/main.py) + [`src/api/v1/triage.py`](file:///mnt/c/Repos/Local/MBA/src/api/v1/triage.py) | `POST /api/v1/triage`, schemas Pydantic, Swagger em `/docs` |
| Grafo LangGraph | [`orchestrator/rag_logic.py`](file:///mnt/c/Repos/Local/MBA/orchestrator/rag_logic.py) | 4 nós: `analyze_risk → retrieve_history → audit_conduct → generate_report` |
| ChromaDB + isolamento | [`database/patient_manager.py`](file:///mnt/c/Repos/Local/MBA/database/patient_manager.py) | Coleção única `clinical_records` + metadata filtering por `patient_id` |
| Dataset sintético | [`synthetic_patients.json`](file:///mnt/c/Repos/Local/MBA/synthetic_patients.json) | 9 pacientes: 3 Alto/Iminente, 3 Moderado, 3 Baixo |
| Suíte de testes | [`tests/`](file:///mnt/c/Repos/Local/MBA/tests/) | 26 testes (22 unit + 4 E2E), 0 falhas |

---

## 📋 Tarefas Pendentes — Escrita do TCC

### DIA 6 — Metodologia: Arquitetura do Sistema e Stack

**Seção a escrever:** `3. Metodologia > 3.1 Arquitetura do Sistema`

**O que cobrir:**
- Premissa central de **Edge AI / 100% local**: justificativa LGPD (sem dados em nuvem pública)
- Diagrama de fluxo do pipeline: `Nota Clínica → ClinicalMonitor (Pydantic) → ChromaDB (RAG) → Árvore de Decisão → Parecer`
- Stack tecnológico e justificativas de escolha:

| Componente | Tecnologia | Justificativa |
|-----------|------------|--------------|
| LLM Engine | `llama3:8b-instruct-q4_K_M` via Ollama | Quantização q4 = menor footprint RAM sem perda crítica de precisão |
| Orquestração | LangGraph (StateGraph determinístico) | Grafo com estado tipado evita outputs não-estruturados |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Modelo leve, offline, adequado para portugês clínico |
| Banco vetorial | ChromaDB persistente (`./chroma_db`) | Persistência local, zero latência de rede |
| API | FastAPI + Pydantic v2 | Validação de schema nativa, Swagger automático |
| Hardware-alvo | Intel Core Ultra 5 235U | Arquitetura híbrida P-core/E-core, `num_thread=10` |

**Dados do repositório a usar:**
- Diagrama do grafo → código em [`orchestrator/rag_logic.py`](file:///mnt/c/Repos/Local/MBA/orchestrator/rag_logic.py) L114–131
- Config de hardware → [`config/engine.py`](file:///mnt/c/Repos/Local/MBA/config/engine.py) L61–67
- Justificativa LGPD → [`database/patient_manager.py`](file:///mnt/c/Repos/Local/MBA/database/patient_manager.py) L10–14

---

### DIA 7 — Metodologia: Governança de Dados e Conformidade LGPD

**Seção a escrever:** `3. Metodologia > 3.2 Governança de Dados e Isolamento LGPD`

**O que cobrir:**
- O problema: sistemas multi-tenant com dados sensíveis psiquiátricos
- A decisão arquitetural: **uma única collection ChromaDB** com Metadata Filtering (`where={"patient_id": "PAC-XXX"}`) em vez de múltiplas collections por paciente
- Justificativa técnica: evita "RAM collapse" e degradação de performance em ChromaDB com muitas collections
- Conformidade LGPD: `delete_patient_data()` implementa o **Direito ao Esquecimento** (Art. 18, LGPD)
- Evidência empírica: `tests/test_patient_manager.py` valida o isolamento cross-patient

**Dados do repositório a usar:**
- Implementação do isolamento → [`database/patient_manager.py`](file:///mnt/c/Repos/Local/MBA/database/patient_manager.py) L46–72
- Teste de isolamento → [`tests/test_patient_manager.py`](file:///mnt/c/Repos/Local/MBA/tests/test_patient_manager.py) L27–55
- Regra arquitetural → [`GEMINI.md`](file:///mnt/c/Repos/Local/MBA/GEMINI.md) seção 4.1

**Trecho de código a citar no TCC:**
```python
# Isolamento mandatório: nenhuma query retorna dados de outro paciente
kwargs["filter"] = {"patient_id": patient_id}
vectorstore.as_retriever(search_kwargs=kwargs)
```

---

### DIA 8 — Metodologia: Grafo de Decisão Clínica e Dataset Sintético

**Seção a escrever:** `3. Metodologia > 3.3 Grafo de Decisão Clínica` + `3.4 Dataset de Validação`

**Subseção 3.3 — Grafo LangGraph:**

Os 4 nós e sua lógica:

| Nó | Função | Tecnologia |
|----|--------|-----------|
| `analyze_risk` | Triagem estruturada Pydantic zero-shot | LLM + `with_structured_output(SuicideRiskAssessment)` |
| `retrieve_history` | RAG longitudinal (fatores estáticos) | ChromaDB retriever com filtro `patient_id` |
| `audit_conduct` | Auditoria de conduta médica | Árvore de decisão hardcoded (regras CFM) |
| `generate_report` | Parecer executivo | Template determinístico |

Schema Pydantic de saída (citar no TCC):
- `risk_level`: Enum 3 valores (Baixo / Moderado / Alto-Iminente)
- `passive_ideation` / `active_ideation`: bool (marcadores linguísticos)
- `red_flags`: List[str] (extraídas textualmente)
- `protection_factors`: List[str]
- `clinical_justification`: str

**Subseção 3.4 — Dataset Sintético:**
- 9 prontuários criados manualmente por especialista (Flávia)
- Distribuição balanceada: 3 por coorte de risco
- CIDs presentes: F31 (Bipolar), F32/F33 (Depressão), F34 (Distimia), F41 (TAG), F60 (Borderline), F20 (Esquizofrenia), Z73 (Burnout)
- Critério de verdade-base (*ground truth*): atribuído antes da inferência do modelo

**Dados do repositório a usar:**
- Schema Pydantic → [`analytics/clinical_monitor.py`](file:///mnt/c/Repos/Local/MBA/analytics/clinical_monitor.py) L14–33
- Topologia do grafo → [`orchestrator/rag_logic.py`](file:///mnt/c/Repos/Local/MBA/orchestrator/rag_logic.py) L114–131
- Dataset → [`synthetic_patients.json`](file:///mnt/c/Repos/Local/MBA/synthetic_patients.json)

---

### DIA 9 — Resultados: Latência da Inferência Local

**Seção a escrever:** `4. Resultados > 4.1 Performance de Hardware e SLA`

**Tabela pronta para uso (copiar do TCC_BENCHMARK_RESULTS.md):**

| Threads | Decode (t/s) | Tempo Total (s) | Diagnóstico |
|:---:|:---:|:---:|:---|
| 2 | 4.81 | 72.87 | Apenas P-cores físicos |
| 10 | **9.20** | **43.00** | **Ideal: 2 P-cores + 8 E-cores** |
| 14 | 0.44 | 128.03 | Gargalo LP E-cores |

**SLA E2E medido (31/07/2026):** `32.43s` para o pipeline completo de 4 nós.

**Fonte:** [`docs/TCC_BENCHMARK_RESULTS.md`](file:///mnt/c/Repos/Local/MBA/docs/TCC_BENCHMARK_RESULTS.md) — seção 2.

---

### DIA 10 — Resultados: Matriz de Desempenho Clínico

**Seção a escrever:** `4. Resultados > 4.2 Acurácia Clínica e Prompt Engineering`

**Tabela comparativa das versões de prompt (pronta):**

| Versão | Alto/Im. | Moderado | Baixo | Acurácia |
|:---:|:---:|:---:|:---:|:---:|
| v1 (baseline) | 33% | 0% | 100% | 44.4% |
| v2 | 100% | 100% | 33% | 77.8% |
| v3 | 67% | 100% | 33% | 66.7% |
| v4 | 67% | 33% | 100% | 66.7% |
| **v2-final** | **100%** | **100%** | 33% | **77.8%** |

**Argumento central para a discussão:**
> Sensibilidade 100% nas coortes críticas (Alto/Iminente e Moderado) com zero falsos negativos. Os 2 falsos positivos no Risco Baixo (PAC-031, PAC-032) são clinicamente aceitáveis: custo = consulta adicional desnecessária vs. custo de falso negativo = risco de vida.

**Fonte:** [`docs/TCC_BENCHMARK_RESULTS.md`](file:///mnt/c/Repos/Local/MBA/docs/TCC_BENCHMARK_RESULTS.md) — seção 3.

---

### DIAS 11–12 — Discussão, Conclusão e Referencial

*Não bloqueiam os dias anteriores. Conteúdo a definir na sessão correspondente.*

---

## 🚀 Como Iniciar a Próxima Sessão

Cole no chat ao iniciar:

```
Retomando o TCC PsicRE-AI. Consulte o documento de continuidade em:
/home/yurimolina/.gemini/antigravity-cli/brain/d6ac903b-6065-44fc-bdee-90c1bfe5cecc/sessao_handoff.md

Próxima tarefa: [INFORME O DIA AQUI, ex: "Dia 6 — Metodologia: Arquitetura"]
```

---

## 📁 Mapa de Arquivos Essenciais

```
MBA/
├── analytics/clinical_monitor.py     ← Prompt v2-final + schema Pydantic
├── orchestrator/rag_logic.py         ← Grafo LangGraph (4 nós)
├── database/patient_manager.py       ← Isolamento LGPD / ChromaDB
├── config/engine.py                  ← LLM + threads otimizados
├── src/api/v1/triage.py              ← Endpoint POST /api/v1/triage
├── main.py                           ← FastAPI entrypoint
├── synthetic_patients.json           ← Dataset 9 pacientes (ground truth)
├── PRONTUARIO_JS_2026.txt            ← Caso-base: depressão resistente (F33.2)
├── docs/TCC_BENCHMARK_RESULTS.md     ← Dados de performance + acurácia
└── tests/                            ← 26 testes (evidência de robustez)
```
