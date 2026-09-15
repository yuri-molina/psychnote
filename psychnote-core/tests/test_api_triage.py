"""
tests/test_api_triage.py — Testes de Integração HTTP: POST /api/v1/triage

Estratégia de mock:
  O grafo LangGraph (PsychiatricOrchestrator.build_graph) e o ClinicalMonitor
  são mockados via unittest.mock.patch para evitar dependência do Ollama em CI.
  Testamos o contrato HTTP (status codes, schemas, validações) de forma isolada
  dos modelos de IA — conforme boas práticas de testes de integração de APIs.

Cobertura:
  TC-API-001  POST válido com nota de Risco Alto/Iminente
  TC-API-002  POST válido com nota de Risco Moderado
  TC-API-003  POST válido com nota de Risco Baixo
  TC-API-004  Validação: nota abaixo do mínimo de 10 caracteres
  TC-API-005  Validação: patient_id ausente no payload
  TC-API-006  Validação: current_note ausente no payload
  TC-API-007  Resposta contém audit_alerts quando conduta é negligente
  TC-API-008  Resposta sem audit_alerts quando conduta é adequada
  TC-API-009  GET /health retorna 200 e payload correto
  TC-API-010  Resposta com pipeline retornando risk_assessment vazio → 422
  TC-API-011  POST /api/v1/triage/async: aceite imediato (202 Accepted)
  TC-API-012  GET /api/v1/patients/{id}/history: consulta histórico pré-computado
  TC-API-013  GET /api/v1/triage/jobs/{job_id}: status processing durante execução
  TC-API-014  GET /api/v1/triage/jobs/{job_id}: job_id inexistente retorna 404
  TC-API-015  POST /api/v1/triage/async: pré-registro imediato com has_triage=False
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Garante imports absolutos do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# Factories de estado simulado do LangGraph
# ---------------------------------------------------------------------------

def _make_graph_state(
    risk_level: str = "Alto/Iminente",
    audit_alerts: list | None = None,
    red_flags: list | None = None,
    protection_factors: list | None = None,
) -> dict:
    """Constrói um AgentState final simulado compatível com TriageResponse."""
    return {
        "patient_id": "TEST-001",
        "current_note": "nota clínica de teste",
        "risk_assessment": {
            "risk_level": risk_level,
            "passive_ideation": risk_level in ("Moderado", "Baixo"),
            "active_ideation": risk_level == "Alto/Iminente",
            "red_flags": red_flags or ["raticida adquirido", "carta de despedida"],
            "protection_factors": protection_factors or [],
            "clinical_justification": f"Classificação automatizada: {risk_level}.",
        },
        "patient_context": ["Histórico: tentativa prévia em 2022."],
        "audit_alerts": audit_alerts or [],
        "final_response": f"=== PARECER EXECUTIVO ===\nRisco: {risk_level}\n",
    }


# ---------------------------------------------------------------------------
# Fixture: TestClient com mocks aplicados
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    """
    Retorna um TestClient com o grafo LangGraph mockado.
    O mock do _get_orchestrator garante que não há inicialização do Ollama.
    O mock do graph.invoke retorna um estado controlado por cada teste.
    """
    # Importa main apenas após configurar o path
    from main import app
    # Reseta o singleton entre testes para evitar vazamento de estado
    from src.api.v1.triage import _get_orchestrator
    _get_orchestrator.cache_clear()
    return TestClient(app)


@pytest.fixture()
def mock_graph_invoke():
    """Fixture que injeta mock no build_graph().invoke."""
    mock_graph = MagicMock()
    mock_orchestrator = MagicMock()
    mock_orchestrator.build_graph.return_value = mock_graph
    return mock_orchestrator, mock_graph


# ---------------------------------------------------------------------------
# TC-API-009: Health Check (não depende de LLM, testado primeiro)
# ---------------------------------------------------------------------------

def test_health_check(client):
    """TC-API-009: GET /health deve retornar 200 com status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "PsicRE-AI"
    assert "version" in body


# ---------------------------------------------------------------------------
# TC-API-001: POST válido — Risco Alto/Iminente
# ---------------------------------------------------------------------------

def test_triage_alto_iminente(client, mock_graph_invoke):
    """TC-API-001: Nota com Risco Alto/Iminente deve retornar 200 e risk_level correto."""
    mock_orchestrator, mock_graph = mock_graph_invoke
    mock_graph.invoke.return_value = _make_graph_state(
        risk_level="Alto/Iminente",
        audit_alerts=["[FALHA CRÍTICA]: Alta concedida para paciente de alto risco."],
    )

    with patch("src.api.v1.triage._get_orchestrator", return_value=mock_orchestrator):
        response = client.post(
            "/api/v1/triage/",
            json={
                "patient_id": "PAC-010",
                "current_note": (
                    "Paciente admite ter escrito carta de despedida e adquirido raticida "
                    "com intenção de uso esta noite. Conduta: alta ambulatorial."
                ),
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["risk_assessment"]["risk_level"] == "Alto/Iminente"
    assert body["risk_assessment"]["active_ideation"] is True
    assert len(body["audit_alerts"]) > 0
    assert any("FALHA CRÍTICA" in alert for alert in body["audit_alerts"])
    assert body["patient_id"] == "PAC-010"
    assert isinstance(body["final_report"], str)
    assert len(body["final_report"]) > 0


# ---------------------------------------------------------------------------
# TC-API-002: POST válido — Risco Moderado
# ---------------------------------------------------------------------------

def test_triage_moderado(client, mock_graph_invoke):
    """TC-API-002: Nota com Risco Moderado deve retornar 200 e campos consistentes."""
    mock_orchestrator, mock_graph = mock_graph_invoke
    mock_graph.invoke.return_value = _make_graph_state(
        risk_level="Moderado",
        audit_alerts=["[RECOMENDAÇÃO]: Acionar família e contrato terapêutico não documentados."],
        red_flags=["ideação recorrente", "diagnóstico bipolar instável"],
        protection_factors=["aliança terapêutica", "suporte familiar"],
    )

    with patch("src.api.v1.triage._get_orchestrator", return_value=mock_orchestrator):
        response = client.post(
            "/api/v1/triage/",
            json={
                "patient_id": "PAC-020",
                "current_note": (
                    "Paciente borderline relata pensamentos recorrentes de desaparecer. "
                    "Nega planejamento. Cita filho como fator protetor."
                ),
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["risk_assessment"]["risk_level"] == "Moderado"
    assert body["risk_assessment"]["passive_ideation"] is True
    assert body["risk_assessment"]["active_ideation"] is False
    assert len(body["risk_assessment"]["protection_factors"]) > 0


# ---------------------------------------------------------------------------
# TC-API-003: POST válido — Risco Baixo
# ---------------------------------------------------------------------------

def test_triage_baixo(client, mock_graph_invoke):
    """TC-API-003: Nota com Risco Baixo deve retornar 200 sem alertas críticos."""
    mock_orchestrator, mock_graph = mock_graph_invoke
    mock_graph.invoke.return_value = _make_graph_state(
        risk_level="Baixo",
        audit_alerts=[],
        red_flags=[],
        protection_factors=["planos de futuro", "rede de apoio sólida", "motivação para tratamento"],
    )

    with patch("src.api.v1.triage._get_orchestrator", return_value=mock_orchestrator):
        response = client.post(
            "/api/v1/triage/",
            json={
                "patient_id": "PAC-030",
                "current_note": (
                    "Paciente com cansaço situacional. Nega qualquer ideação ou planejamento. "
                    "Apresenta planos de futuro e motivação para retornar à terapia."
                ),
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["risk_assessment"]["risk_level"] == "Baixo"
    assert body["audit_alerts"] == []
    assert not any("FALHA CRÍTICA" in alert for alert in body["audit_alerts"])


# ---------------------------------------------------------------------------
# TC-API-004: Validação — current_note abaixo do mínimo
# ---------------------------------------------------------------------------

def test_triage_note_too_short(client):
    """TC-API-004: Nota com menos de 10 caracteres deve retornar 422."""
    response = client.post(
        "/api/v1/triage/",
        json={
            "patient_id": "PAC-000",
            "current_note": "curta",  # 5 chars < min_length=10
        },
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any("current_note" in str(err) or "min_length" in str(err) for err in detail)


# ---------------------------------------------------------------------------
# TC-API-005: Validação — patient_id ausente
# ---------------------------------------------------------------------------

def test_triage_missing_patient_id(client):
    """TC-API-005: Payload sem patient_id deve retornar 422."""
    response = client.post(
        "/api/v1/triage/",
        json={"current_note": "Nota clínica com conteúdo suficiente para passar na validação."},
    )
    assert response.status_code == 422
    fields = [err.get("loc", []) for err in response.json()["detail"]]
    assert any("patient_id" in loc for loc in fields)


# ---------------------------------------------------------------------------
# TC-API-006: Validação — current_note ausente
# ---------------------------------------------------------------------------

def test_triage_missing_current_note(client):
    """TC-API-006: Payload sem current_note deve retornar 422."""
    response = client.post(
        "/api/v1/triage/",
        json={"patient_id": "PAC-000"},
    )
    assert response.status_code == 422
    fields = [err.get("loc", []) for err in response.json()["detail"]]
    assert any("current_note" in loc for loc in fields)


# ---------------------------------------------------------------------------
# TC-API-007: audit_alerts presentes quando conduta é negligente
# ---------------------------------------------------------------------------

def test_triage_audit_alerts_present_on_negligent_conduct(client, mock_graph_invoke):
    """TC-API-007: Risco Alto + alta ambulatorial deve gerar audit_alerts."""
    mock_orchestrator, mock_graph = mock_graph_invoke
    mock_graph.invoke.return_value = _make_graph_state(
        risk_level="Alto/Iminente",
        audit_alerts=[
            "[FALHA CRÍTICA]: Alta concedida para paciente com risco iminente.",
            "[ALERTA DE SEGURANÇA]: Sem evidência de encaminhamento para internação.",
        ],
    )

    with patch("src.api.v1.triage._get_orchestrator", return_value=mock_orchestrator):
        response = client.post(
            "/api/v1/triage/",
            json={
                "patient_id": "PAC-012",
                "current_note": (
                    "Paciente com alucinações imperativas e plano detalhado. "
                    "Conduta: Aumento de risperidona e alta ambulatorial."
                ),
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert len(body["audit_alerts"]) == 2
    assert any("FALHA CRÍTICA" in a for a in body["audit_alerts"])
    assert any("ALERTA DE SEGURANÇA" in a for a in body["audit_alerts"])


# ---------------------------------------------------------------------------
# TC-API-008: audit_alerts ausentes quando conduta é adequada
# ---------------------------------------------------------------------------

def test_triage_no_alerts_on_adequate_conduct(client, mock_graph_invoke):
    """TC-API-008: Risco Alto com internação documentada não deve gerar alertas críticos."""
    mock_orchestrator, mock_graph = mock_graph_invoke
    mock_graph.invoke.return_value = _make_graph_state(
        risk_level="Alto/Iminente",
        audit_alerts=[],  # Conduta adequada: sem alertas
    )

    with patch("src.api.v1.triage._get_orchestrator", return_value=mock_orchestrator):
        response = client.post(
            "/api/v1/triage/",
            json={
                "patient_id": "PAC-011",
                "current_note": (
                    "Paciente com risco iminente. Encaminhado via SAMU para internação "
                    "psiquiátrica involuntária. Família acionada imediatamente."
                ),
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["audit_alerts"] == []


# ---------------------------------------------------------------------------
# TC-API-010: Pipeline retorna risk_assessment vazio → 422
# ---------------------------------------------------------------------------

def test_triage_empty_risk_assessment_returns_422(client, mock_graph_invoke):
    """TC-API-010: Quando o grafo retorna risk_assessment vazio, deve retornar 422."""
    mock_orchestrator, mock_graph = mock_graph_invoke
    # Simula falha silenciosa do nó de triagem
    mock_graph.invoke.return_value = {
        "patient_id": "PAC-ERR",
        "current_note": "nota qualquer",
        "risk_assessment": {},  # vazio — falha do nó analyze_risk
        "patient_context": [],
        "audit_alerts": [],
        "final_response": "",
    }

    with patch("src.api.v1.triage._get_orchestrator", return_value=mock_orchestrator):
        response = client.post(
            "/api/v1/triage/",
            json={
                "patient_id": "PAC-ERR",
                "current_note": "Nota de teste para cenário de falha silenciosa do pipeline.",
            },
        )

    assert response.status_code == 422
    assert "avaliação de risco vazia" in response.json()["detail"]


# ---------------------------------------------------------------------------
# TC-API-011: POST /api/v1/triage/async — Retorna 202 Accepted
# ---------------------------------------------------------------------------

def test_triage_async_accepts_202(client):
    """TC-API-011: Endpoint assíncrono aceita a requisição e retorna 202 com status processing."""
    with patch("src.api.v1.triage._process_triage_background") as mock_bg:
        response = client.post(
            "/api/v1/triage/async",
            json={
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "patient_id": "PAC-ASYNC-001",
                "current_note": "Nota clínica de teste para processamento assíncrono via Webhook.",
                "callback_url": "http://localhost:3000/api/webhooks/triage-result",
            },
        )

    assert response.status_code == 202
    body = response.json()
    assert body["job_id"] == "123e4567-e89b-12d3-a456-426614174000"
    assert body["status"] == "processing"


# ---------------------------------------------------------------------------
# TC-API-012: GET /api/v1/patients/{id}/history — Retorna 200 e histórico
# ---------------------------------------------------------------------------

def test_get_patient_history(client):
    """TC-API-012: Endpoint de histórico retorna lista de triagens pré-computadas."""
    mock_mgr = MagicMock()
    mock_mgr.get_patient_history.return_value = [
        {
            "patient_id": "PAC-HIST-001",
            "note_text": "Nota histórica de teste.",
            "created_at": "2026-08-08T18:00:00Z",
            "has_triage": True,
            "risk_assessment": {
                "risk_level": "Moderado",
                "passive_ideation": True,
                "active_ideation": False,
                "red_flags": ["Depressão recorrente"],
                "protection_factors": ["Apoio familiar"],
                "clinical_justification": "Justificativa teste",
            },
            "audit_alerts": [],
            "final_report": "PARECER HISTÓRICO",
        }
    ]

    with patch("src.api.v1.triage._get_patient_manager", return_value=mock_mgr):
        response = client.get("/api/v1/patients/PAC-HIST-001/history")

    assert response.status_code == 200
    body = response.json()
    assert body["patient_id"] == "PAC-HIST-001"
    assert body["total_records"] == 1
    assert body["history"][0]["risk_assessment"]["risk_level"] == "Moderado"


# ---------------------------------------------------------------------------
# TC-API-013: GET /api/v1/triage/jobs/{job_id} — Status processing
# ---------------------------------------------------------------------------

def test_get_job_status_processing(client):
    """TC-API-013: Após submeter triage/async, o job_id deve retornar status processing.

    Nota de implementação: o TestClient do FastAPI/Starlette executa BackgroundTasks de
    forma síncrona antes de retornar a resposta. Para isolar o comportamento do endpoint
    e garantir que o job permaneça em 'processing' no momento da asserção, o worker de
    background e o PatientDataManager são mockados.
    """
    job_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    mock_mgr = MagicMock()

    with patch("src.api.v1.triage._get_patient_manager", return_value=mock_mgr), \
         patch("src.api.v1.triage._process_triage_background"):
        # Submete o job assíncrono (202) — background worker mockado, status permanece 'processing'
        client.post(
            "/api/v1/triage/async",
            json={
                "job_id": job_id,
                "patient_id": "PAC-JOB-013",
                "current_note": "Nota clínica para teste de consulta de status do job.",
                "callback_url": "http://localhost:3000/api/webhooks/triage-result",
            },
        )

        # Consulta imediatamente o status: deve retornar 'processing'
        response = client.get(f"/api/v1/triage/jobs/{job_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == job_id
    assert body["patient_id"] == "PAC-JOB-013"
    assert body["status"] == "processing"
    assert body["risk_assessment"] is None
    assert body["error_message"] is None


# ---------------------------------------------------------------------------
# TC-API-014: GET /api/v1/triage/jobs/{job_id} — job_id inexistente → 404
# ---------------------------------------------------------------------------

def test_get_job_status_not_found(client):
    """TC-API-014: Consultar um job_id inexistente deve retornar 404."""
    response = client.get("/api/v1/triage/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert "não encontrado" in response.json()["detail"]


# ---------------------------------------------------------------------------
# TC-API-015: POST /api/v1/triage/async — Persiste nota imediatamente (has_triage=False)
# ---------------------------------------------------------------------------

def test_triage_async_pre_registers_note_in_db(client):
    """TC-API-015: Ao aceitar o job async, a nota deve ser pré-registrada no SQLite com has_triage=False.

    Nota de implementação: o worker de background é mockado para isolar a chamada de
    pré-registro (has_triage=False) no endpoint da chamada posterior do worker (has_triage=True),
    evitando que o assert_called_once() falhe por dupla chamada.
    """
    mock_mgr = MagicMock()
    job_id = "11111111-2222-3333-4444-555555555555"

    with patch("src.api.v1.triage._get_patient_manager", return_value=mock_mgr), \
         patch("src.api.v1.triage._process_triage_background"):
        response = client.post(
            "/api/v1/triage/async",
            json={
                "job_id": job_id,
                "patient_id": "PAC-PRE-015",
                "current_note": "Nota pré-registrada antes da triagem completar.",
                "callback_url": "http://localhost:3000/api/webhooks/triage-result",
            },
        )

    assert response.status_code == 202

    # Valida que upsert_note foi chamado EXATAMENTE UMA VEZ com has_triage=False e job_status='processing'
    # (o worker está mockado, portanto a segunda chamada com has_triage=True não ocorre)
    mock_mgr.upsert_note.assert_called_once()
    call_kwargs = mock_mgr.upsert_note.call_args
    metadata = call_kwargs.kwargs.get("metadata") or call_kwargs.args[2]
    assert metadata["has_triage"] is False
    assert metadata["job_status"] == "processing"
    assert metadata["job_id"] == job_id


