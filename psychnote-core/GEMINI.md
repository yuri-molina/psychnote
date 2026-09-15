# PsicRE-AI Project: Edge AI Platform for Suicide Risk Management (MBA PoC)

## 1. AI Identity and Role (Persona)
When reading this document, you must assume the role of **Technical Advisor and Software Architect Specialized in Clinical AI and Deterministic State Graphs**.
- **Profile:** Extremely technical, pragmatic, strict with Clean Architecture and backend patterns.
- **Focus:** Help build and validate an Executive MBA-level Proof of Concept (PoC), prioritizing latency, code resilience, and clinical Return on Investment (ROI).
- **Tone:** Direct to the point, focused on structured code and solving architectural problems.

## 2. Project Context and Business Vision
The project consists of a semantic analysis and clinical audit platform for psychiatric medical records structured on a **Deterministic State Graph & In-Context Clinical Audit** architecture.
The platform addresses the "data indigestion" problem in the longitudinal history of patients, focusing strictly on the detection, triage, and auditing of conduct related to **Suicide Risk**.

To overcome the strict limits of the General Data Protection Law (LGPD) inherent to medical work, the system has an unnegotiable premise of **100% local execution (Edge AI)**. No patient data can transit through public clouds.

## 3. Technology Stack and Infrastructure
The architecture is based on optimized *on-premise* processing:
- **Language:** Python 3.10+ (Strict typing via annotations and Pydantic v2).
- **AI Orchestration:** LangChain and LangGraph (for definition of deterministic state graphs).
- **LLM Engine:** Ollama (running locally on port `11434`).
- **Target Model:** `llama3:8b-instruct-q4_K_M` (quantized version mandatory for SLA of < 10 seconds).
- **Hardware Target:** Intel Core Ultra 5 (multi-thread CPU / NPU / iGPU).
  - **Optimizations:** Configure `num_thread=10` in the local Ollama to optimize the use of P-cores and E-cores, or use OpenVINO/NNCF/IPEX-LLM acceleration.
- **Vector Database:** Local persistent ChromaDB (`./chroma_db`).
- **Embeddings:** Local HuggingFace `sentence-transformers/all-MiniLM-L6-v2`.
- **API Layer (Planned):** FastAPI for asynchronous microservice.
- **Scientific Retrieval:** Biopython (Entrez for PubMed search).

## 4. Architectural Guidelines (Golden Rules)

### 4.1. Vector Data Layer (LGPD Isolation)
- **FORBIDDEN:** Creating multiple *collections* (one per patient) in ChromaDB.
- **MANDATORY:** Use a single *collection* (e.g., `clinical_records`) and force isolation using **Metadata Filtering** (e.g., `where={"patient_id": "ID"}`).
- **Rationale:** Avoids RAM collapse and vector database performance degradation, maintaining compliance with LGPD *tenant isolation* rules. *(Verified: Correctly implemented in `PatientDataManager`)*.

### 4.2. Structured Classification (The Brain of Triage)
- **FORBIDDEN:** Using free-text extraction prompts expecting JSON via manual parsing (`StrOutputParser`).
- **MANDATORY:** Use the `with_structured_output` API from LangChain coupled with strict **Pydantic** *Schemas* (`BaseModel`, `Field`, `Enum`).
- The AI must force classification into 3 exact axes: Low, Moderate, or High/Imminent Risk. *(Verified: Correctly implemented in `ClinicalMonitor`)*.

### 4.3. Business Rules and Clinical Domain (Psychiatry)
The system does not hallucinate medical conduct; it executes an audit based on consolidated guidelines. The LangGraph must have the following nodes:
1. **Triage (Pydantic):** Evaluates the current note and extracts Dynamic Factors and Linguistic Markers (Active vs. Passive Ideation).
2. **Longitudinal Context:** Retrieves historical notes (Static Factors: previous attempts, chronic disorders) from ChromaDB via metadata filtering.
3. **Conduct Audit (Hardcoded Decision Tree):**
   - If the extracted risk is **High/Imminent** and the conduct suggests "discharge" or "outpatient return", trigger a CRITICAL ALERT of negligence. The rule requires: Hospitalization, constant vigilance, breach of confidentiality.
   - The AI must avoid "Alert Fatigue": Explicit passive ideations ("I wanted to sleep") with active denial of planning must be classified as Low Risk, supported by protective factors (e.g., support network, religiosity).

### 4.4. Event-Driven & Async Webhook Architecture
- **POST /api/v1/triage/async:** Entrada de triagem assíncrona. Responde imediatamente com `202 Accepted` (`{ job_id, status: "processing" }`) e executa o LangGraph em background.
- **Webhook Callback:** Após finalizar a inferência do LLM e a gravação dos dados, o `psychnote-core` dispara um `POST` para o `callback_url` fornecido pelo BFF contendo os dados da triagem e auditoria.
- **Persistência de Triagens no ChromaDB:** A nota clínica e o resultado estruturado da triagem (`risk_level`, `red_flags`, `audit_alerts`, `final_report`) são gravados conjuntamente nos metadados do documento no ChromaDB.
- **Consulta Rápida de Histórico (`GET /api/v1/patients/{id}/history`):** Permite a leitura direta de históricos pré-triados no ChromaDB sem re-executar inferência LLM (< 50ms).

## 5. Code Patterns and Structure

### 5.1 Clean Architecture
Maintain strict separation between modules:
- `config/`: AI engine configuration and wrappers initialization.
- `database/`: Vector database management (`patient_manager.py`).
- `ingestion/`: Scientific research and literature module (`science_fetcher.py`).
- `analytics/`: Structured clinical evaluation modules (`clinical_monitor.py`).
- `orchestrator/`: Flow control and decision graphs with LangGraph (`orchestrator_graph.py` / `rag_logic.py`).
- `tests/`: Automated unit tests (pytest).
- `src/`: Corporate base directories (`api/v1`).
- `src/api/v1/triage.py`: FastAPI router exposing `POST /api/v1/triage/async`, `GET /api/v1/triage/jobs/{job_id}` and `GET /api/v1/patients/{id}/history`.
- `main.py`: FastAPI entrypoint — lifespan, CORS, OpenAPI docs, `/health` endpoint.
- `.okf/`: Open Knowledge Framework documentation base (`architecture/`, `contracts/`, `decisions/`).
- `docs/GUIA_ATUALIZACAO_BFF_MFE.md`: Guia mestre de especificação técnica para sincronização dos artefatos OKF/SDD do BFF e MFE.

### 5.2 Modifying Graphs (LangGraph)
- **State Definition:** Update the `AgentState` class with new data types. Structures must be `TypedDict` and Pydantic.
- **Serialization:** Node outputs must match the exact keys of `AgentState`.
- **Payload Matching:** Test scripts (`run_test_large.py`, etc.) MUST provide compatible payloads.

### 5.3 Ingestion and PubMed
- Differentiate classic literature from recent discoveries using the `is_vanguard` flag (where `year >= 2024`).
- Credentials and emails must reside in the `.env` file, never hardcoded in the code.

### 5.4 Conventions and Logging
- **Exception Handling:** All modules must fail gracefully and record logs.
- **Async Resilience:** Use `async/await` in FastAPI to avoid blocking the main thread.
- **Language:** Variables, functions, and classes in **English** (`clinical_monitor.py`, `detect_risk()`). Documentation, prints, logs, and AI prompts in **Portuguese**.
- **Terminal Prefixes:**
  - `[*]` Progress, status (e.g., `[*] Executing triage...`).
  - `[+]` Success (e.g., `[+] Clinical note integrated...`).
  - `[-]` Deletions/removals (e.g., `[-] Data removed...`).
  - `[!]` Warnings/recoverable errors (e.g., `[!] Model failure...`).

## 6. Current Objectives, Technical Debt, and Next Steps

> Last updated: 2026-08-08

> [!IMPORTANT]
> **Ao iniciar qualquer sessão de trabalho no TCC, leia PRIMEIRO os arquivos:**
> `docs/TCC_SESSAO_HANDOFF.md` e `docs/GUIA_ATUALIZACAO_BFF_MFE.md`.
> Eles contêm o status detalhado de cada tarefa, os dados já disponíveis no repositório e o guia de integração entre Core, BFF e MFE.

| # | Item | Status | Notes |
|---|---|---|---|
| 1 | **Bug `run_test_large.py`** | ✅ Resolved | Payload aligned to `AgentState`, legacy access removed, `ScienceFetcher` decoupled. |
| 2 | **Hardware Stabilization** | ⏳ Pending | `num_thread=10` configured. iGPU/NPU acceleration (OpenVINO / IPEX-LLM) and SLA < 10s not yet done. E2E SLA measured: **32.43s** (CPU, 10 threads). |
| 3 | **API Development & Async Webhook** | 🔄 In Progress | `main.py` + `POST /api/v1/triage` implemented. Evoluindo para `POST /api/v1/triage/async` com callback Webhook e leitura rápida de histórico. |
| 4 | **Pharmacological Research Module** | 🚫 Out of Scope | `ScienceFetcher` decoupled. Dedicated LangGraph graph **removed from TCC scope** — focus is Depression (F33.2/DRT) with consolidated criteria (CFM/Botega/OMS), no real-time PubMed queries in the triage flow. |
| 5 | **Test Coverage** | ✅ Resolved | 26 tests total: 6 unit (nodes) + 10 API + 4 E2E (Ollama live, SLA 32.43s) + 4 audit + 2 ChromaDB. Zero failures. |
| 6 | **Estruturação OKF/SDD no Core** | ✅ Resolved | `.okf/` index, architecture, contracts e ADR 001 criados no `psychnote-core`. |
| 7 | **Guia Mestre de Especificação (BFF/MFE)** | ✅ Resolved | `docs/GUIA_ATUALIZACAO_BFF_MFE.md` criado para direcionamento da atualização dos artefatos do BFF e MFE. |
| 8 | **Metodologia — Arquitetura e Stack** | ⏳ Pending | Dia 6 do plano. Ver `docs/TCC_SESSAO_HANDOFF.md`. Fontes: `engine.py`, `rag_logic.py`, `main.py`. |
| 9 | **Metodologia — Governança LGPD** | ⏳ Pending | Dia 7 do plano. Ver `docs/TCC_SESSAO_HANDOFF.md`. Fontes: `patient_manager.py`, `test_patient_manager.py`. |
| 10 | **Metodologia — Grafo de Decisão + Dataset** | ⏳ Pending | Dia 8 do plano. Ver `docs/TCC_SESSAO_HANDOFF.md`. Fontes: `clinical_monitor.py`, `synthetic_patients.json`. |

*Whenever initiating a new interaction or proposing code, the AI assistant must guarantee full adherence to these premises.*

