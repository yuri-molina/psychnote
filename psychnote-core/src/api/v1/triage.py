"""
Router FastAPI para o endpoint /api/v1/triage e histórico de pacientes.

Responsabilidade única: receber a nota clínica + ID do paciente,
delegar ao PsychiatricOrchestrator, persistir resultados no SQLite,
suportar processamento assíncrono via Webhook, servir histórico pré-computado
e expor o status de jobs em processamento.

Provedores de LLM suportados (parâmetro llm_provider):
  1 — Ollama local (padrão, LGPD-safe, Edge AI).
  2 — Google Gemini remoto (requer GOOGLE_API_KEY no .env; apenas dados sintéticos).
"""

from __future__ import annotations

import asyncio
import time
import httpx
from typing import List, Optional, Dict, Any
from functools import lru_cache

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field

from analytics.clinical_monitor import RiskLevelEnum
from config.engine import LLMProvider
from orchestrator.orchestrator_graph import PsychiatricOrchestrator
from database.patient_manager import PatientDataManager

router = APIRouter(prefix="/api/v1", tags=["Triagem Clínica & Histórico"])


# ---------------------------------------------------------------------------
# Registro in-memory de Jobs (ciclo de vida: processing → completed | error)
# Suficiente para a PoC: jobs sobrevivem ao ciclo de vida do processo.
# ---------------------------------------------------------------------------

# Estrutura: { job_id: { "patient_id", "status", "created_at", "risk_assessment", "audit_alerts", "error_message" } }
_JOB_REGISTRY: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Schemas de Contrato HTTP (desacoplados dos modelos internos)
# ---------------------------------------------------------------------------

class TriageRequest(BaseModel):
    """Payload de entrada para a triagem síncrona de risco de suicídio."""

    patient_id: str = Field(
        ...,
        description="Identificador único do paciente (ex: PAC-001).",
        examples=["PAC-001"],
    )
    current_note: str = Field(
        ...,
        min_length=10,
        description="Texto completo da nota clínica atual a ser avaliada.",
        examples=["Paciente relata sofrimento insuportável. Menciona carta escrita e data definida."],
    )
    llm_provider: int = Field(
        default=1,
        ge=1,
        le=2,
        description="Provedor de LLM: 1 = Ollama local (padrão, LGPD-safe), 2 = Google Gemini remoto.",
        examples=[1],
    )


class TriageAsyncRequest(BaseModel):
    """Payload de entrada para a triagem assíncrona de risco de suicídio."""

    job_id: str = Field(
        ...,
        description="Identificador único da requisição/job gerado pelo BFF (UUID).",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    patient_id: str = Field(
        ...,
        description="Identificador único do paciente.",
        examples=["PAC-001"],
    )
    current_note: str = Field(
        ...,
        min_length=10,
        description="Texto completo da nota clínica atual a ser avaliada.",
        examples=["Paciente relata sofrimento insuportável."],
    )
    callback_url: str = Field(
        ...,
        description="URL de Webhook do BFF para envio do resultado final.",
        examples=["http://psychnote-bff:3000/api/webhooks/triage-result"],
    )
    llm_provider: int = Field(
        default=1,
        ge=1,
        le=2,
        description="Provedor de LLM: 1 = Ollama local (padrão, LGPD-safe), 2 = Google Gemini remoto.",
        examples=[1],
    )


class TriageAsyncResponse(BaseModel):
    """Resposta imediata (HTTP 202) da triagem assíncrona."""

    job_id: str
    status: str = "processing"
    message: str = "Triagem enviada para processamento assíncrono."


class JobStatusResponse(BaseModel):
    """Resposta de status de um job de triagem assíncrono."""

    job_id: str
    patient_id: str
    status: str = Field(
        description="Status do job: 'processing', 'completed' ou 'error'.",
        examples=["processing"],
    )
    created_at: str
    risk_assessment: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Presente apenas quando status = 'completed'.",
    )
    audit_alerts: List[str] = Field(
        default_factory=list,
        description="Presente apenas quando status = 'completed'.",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Presente apenas quando status = 'error'.",
    )


class RiskAssessmentResponse(BaseModel):
    """Sub-schema com os dados estruturados extraídos pelo ClinicalMonitor."""

    risk_level: RiskLevelEnum
    passive_ideation: bool
    active_ideation: bool
    red_flags: List[str]
    protection_factors: List[str]
    clinical_justification: str


class TriageResponse(BaseModel):
    """Resposta completa do pipeline de triagem e auditoria."""

    patient_id: str
    risk_assessment: RiskAssessmentResponse
    audit_alerts: List[str] = Field(
        description="Lista de alertas de protocolo gerados pela árvore de decisão de auditoria."
    )
    final_report: str = Field(
        description="Parecer executivo consolidado gerado pelo Nó 4 do LangGraph."
    )


class PatientHistoryResponse(BaseModel):
    """Resposta contendo todo o histórico longitudinal com triagens salvas."""

    patient_id: str
    total_records: int
    history: List[Dict[str, Any]]


# ---------------------------------------------------------------------------
# Singletons (instâncias únicas por provedor para otimização de memória)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=2)
def _get_orchestrator(provider: int = 1) -> PsychiatricOrchestrator:
    """
    Retorna a instância cacheada do PsychiatricOrchestrator para o provedor informado.
    maxsize=2 — uma instância por provedor (Ollama + Gemini).
    """
    llm_provider = LLMProvider(provider)
    print(f"[*] Inicializando PsychiatricOrchestrator (provider={llm_provider.name})...")
    return PsychiatricOrchestrator(llm_provider=llm_provider)


@lru_cache(maxsize=1)
def _get_patient_manager() -> PatientDataManager:
    """Retorna a instância única do PatientDataManager."""
    return PatientDataManager()


# ---------------------------------------------------------------------------
# Helper Worker para Processamento Assíncrono + Webhook
# ---------------------------------------------------------------------------

async def _process_triage_background(
    job_id: str,
    patient_id: str,
    current_note: str,
    callback_url: str,
    llm_provider: int = 1,
) -> None:
    """
    Executa a inferência do LangGraph em background worker.
    Ao término:
      1. Atualiza o registro in-memory do job para 'completed' ou 'error'.
      2. Salva nota + triagem finalizada no SQLite (sobrescreve o registro 'processing').
      3. Dispara o Webhook Callback HTTP POST para o BFF.
    """
    print(f"[*] [Background Worker] Iniciando job_id={job_id} | patient_id={patient_id} | provider={llm_provider}")
    orchestrator = _get_orchestrator(provider=llm_provider)
    graph = orchestrator.build_graph()

    graph_input = {
        "patient_id": patient_id,
        "current_note": current_note,
        "risk_assessment": {},
        "patient_context": [],
        "audit_alerts": [],
        "final_response": "",
    }

    try:
        loop = asyncio.get_event_loop()
        final_state: dict = await loop.run_in_executor(
            None,
            graph.invoke,
            graph_input,
        )

        risk_data: dict = final_state.get("risk_assessment", {})
        audit_alerts: list = final_state.get("audit_alerts", [])
        final_report: str = final_state.get("final_response", "")

        # 1. Atualiza o registro in-memory para 'completed'
        if job_id in _JOB_REGISTRY:
            _JOB_REGISTRY[job_id]["status"] = "completed"
            _JOB_REGISTRY[job_id]["risk_assessment"] = risk_data
            _JOB_REGISTRY[job_id]["audit_alerts"] = audit_alerts

        # 2. Persiste nota + triagem finalizada no ChromaDB
        patient_mgr = _get_patient_manager()
        triage_metadata = {
            "job_id": job_id,
            "job_status": "completed",
            "has_triage": True,
            "risk_level": risk_data.get("risk_level", "Baixo"),
            "passive_ideation": risk_data.get("passive_ideation", False),
            "active_ideation": risk_data.get("active_ideation", False),
            "red_flags": risk_data.get("red_flags", []),
            "protection_factors": risk_data.get("protection_factors", []),
            "clinical_justification": risk_data.get("clinical_justification", ""),
            "audit_alerts": audit_alerts,
            "final_report": final_report,
        }
        patient_mgr.upsert_note(patient_id, current_note, metadata=triage_metadata)

        # 3. Notifica o BFF via Webhook Callback
        webhook_payload = {
            "job_id": job_id,
            "patient_id": patient_id,
            "status": "completed",
            "risk_assessment": risk_data,
            "audit_alerts": audit_alerts,
            "final_report": final_report,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(callback_url, json=webhook_payload)
            print(f"[+] [Webhook Push] Callback enviado para {callback_url} | HTTP {resp.status_code}")

    except Exception as exc:
        print(f"[!] [Background Worker ERROR] Falha no job_id={job_id}: {exc}")

        # Atualiza o registro in-memory para 'error'
        if job_id in _JOB_REGISTRY:
            _JOB_REGISTRY[job_id]["status"] = "error"
            _JOB_REGISTRY[job_id]["error_message"] = str(exc)

        # Tenta notificar o BFF sobre a falha se possível
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    callback_url,
                    json={"job_id": job_id, "patient_id": patient_id, "status": "error", "error": str(exc)},
                )
        except Exception as net_err:
            print(f"[!] Não foi possível notificar falha ao Webhook: {net_err}")


# ---------------------------------------------------------------------------
# Endpoints HTTP
# ---------------------------------------------------------------------------

@router.post(
    "/triage",
    response_model=TriageResponse,
    status_code=status.HTTP_200_OK,
    summary="Executar triagem síncrona de risco de suicídio",
)
@router.post(
    "/triage/",
    response_model=TriageResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def run_triage(payload: TriageRequest) -> TriageResponse:
    """Endpoint síncrono de triagem (mantido para compatibilidade). Persiste nota + triagem no SQLite ao concluir."""
    print(f"[*] Requisição síncrona de triagem recebida | patient_id={payload.patient_id} | provider={payload.llm_provider}")

    orchestrator = _get_orchestrator(provider=payload.llm_provider)
    graph = orchestrator.build_graph()

    graph_input = {
        "patient_id": payload.patient_id,
        "current_note": payload.current_note,
        "risk_assessment": {},
        "patient_context": [],
        "audit_alerts": [],
        "final_response": "",
    }

    try:
        loop = asyncio.get_event_loop()
        final_state: dict = await loop.run_in_executor(
            None,
            graph.invoke,
            graph_input,
        )
    except Exception as exc:
        print(f"[!] Falha na execução do grafo LangGraph: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno na execução do pipeline de triagem: {str(exc)}",
        ) from exc

    risk_data: dict = final_state.get("risk_assessment", {})
    if not risk_data or "risk_level" not in risk_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O pipeline retornou uma avaliação de risco vazia ou malformada.",
        )

    audit_alerts = final_state.get("audit_alerts", [])
    final_report = final_state.get("final_response", "")

    # Persiste no SQLite
    patient_mgr = _get_patient_manager()
    triage_metadata = {
        "has_triage": True,
        "job_status": "completed",
        "risk_level": risk_data.get("risk_level", "Baixo"),
        "passive_ideation": risk_data.get("passive_ideation", False),
        "active_ideation": risk_data.get("active_ideation", False),
        "red_flags": risk_data.get("red_flags", []),
        "protection_factors": risk_data.get("protection_factors", []),
        "clinical_justification": risk_data.get("clinical_justification", ""),
        "audit_alerts": audit_alerts,
        "final_report": final_report,
    }
    patient_mgr.upsert_note(payload.patient_id, payload.current_note, metadata=triage_metadata)

    return TriageResponse(
        patient_id=payload.patient_id,
        risk_assessment=RiskAssessmentResponse(**risk_data),
        audit_alerts=audit_alerts,
        final_report=final_report,
    )


@router.post(
    "/triage/async",
    response_model=TriageAsyncResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Executar triagem assíncrona com callback Webhook",
)
async def run_triage_async(
    payload: TriageAsyncRequest,
    background_tasks: BackgroundTasks,
) -> TriageAsyncResponse:
    """
    Endpoint assíncrono. Aceita o job imediatamente (202 Accepted):
      1. Registra o job no mapa in-memory com status 'processing'.
      2. Persiste a nota clínica no SQLite com has_triage=False e job_status='processing'
         para que o prontuário possa exibir a nota imediatamente com indicador de loading.
      3. Agenda o worker de background (LangGraph → SQLite → Webhook).
    """
    created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    print(f"[*] Requisição assíncrona recebida | job_id={payload.job_id} | patient_id={payload.patient_id} | provider={payload.llm_provider}")

    # 1. Registra o job no mapa in-memory
    _JOB_REGISTRY[payload.job_id] = {
        "patient_id": payload.patient_id,
        "status": "processing",
        "created_at": created_at,
        "risk_assessment": None,
        "audit_alerts": [],
        "error_message": None,
    }

    # 2. Persiste a nota imediatamente no SQLite com has_triage=False
    patient_mgr = _get_patient_manager()
    patient_mgr.upsert_note(
        patient_id=payload.patient_id,
        note_text=payload.current_note,
        metadata={
            "job_id": payload.job_id,
            "job_status": "processing",
            "has_triage": False,
        },
    )
    print(f"[+] Nota pré-registrada no SQLite com has_triage=False | job_id={payload.job_id}")

    # 3. Agenda o worker de background
    background_tasks.add_task(
        _process_triage_background,
        job_id=payload.job_id,
        patient_id=payload.patient_id,
        current_note=payload.current_note,
        callback_url=payload.callback_url,
        llm_provider=payload.llm_provider,
    )

    return TriageAsyncResponse(
        job_id=payload.job_id,
        status="processing",
        message="Triagem enviada para processamento assíncrono.",
    )


@router.get(
    "/triage/jobs/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar o status de um job de triagem assíncrono",
    description=(
        "Retorna o status atual do job: 'processing', 'completed' ou 'error'. "
        "Quando 'completed', inclui o risk_assessment e os audit_alerts completos. "
        "Permite ao BFF fazer polling de fallback caso a conexão SSE seja perdida."
    ),
)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Consulta o status de um job de triagem pelo job_id.
    Retorna 404 se o job_id não for reconhecido (expirou ou nunca existiu).
    """
    job = _JOB_REGISTRY.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' não encontrado. O job pode ter expirado ou o ID é inválido.",
        )

    return JobStatusResponse(
        job_id=job_id,
        patient_id=job["patient_id"],
        status=job["status"],
        created_at=job["created_at"],
        risk_assessment=job.get("risk_assessment"),
        audit_alerts=job.get("audit_alerts", []),
        error_message=job.get("error_message"),
    )


@router.get(
    "/patients/{patient_id}/history",
    response_model=PatientHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar histórico do paciente com triagens pré-computadas",
)
async def get_patient_history(patient_id: str) -> PatientHistoryResponse:
    """
    Recupera as notas e triagens salvas no ChromaDB em < 50ms,
    sem re-executar inferência LLM. Inclui registros com has_triage=False
    (nota recém-submetida aguardando processamento da IA).
    """
    patient_mgr = _get_patient_manager()
    records = patient_mgr.get_patient_history(patient_id)

    return PatientHistoryResponse(
        patient_id=patient_id,
        total_records=len(records),
        history=records,
    )
