"""
tests/test_nodes.py — Testes Unitários dos Nós do LangGraph

Cobre o gap de cobertura identificado no GEMINI.md (Item 5):
os nós analyze_risk, retrieve_history e generate_report não possuíam
nenhum teste unitário.

Estratégia de mock:
  Toda a camada de infra (LLM, embeddings, ChromaDB) é interceptada via
  unittest.mock.patch no nível de importação do orchestrator.rag_logic,
  garantindo que NENHUMA dependência externa (Ollama, HuggingFace, disco)
  seja acionada. Os testes rodam off-line em qualquer ambiente.

Cobertura:
  TC-NODE-001  analyze_risk: estado com risk_assessment preenchido → early return {}
  TC-NODE-002  analyze_risk: estado vazio → invoca detect_risk e serializa output
  TC-NODE-003  retrieve_history: retriever retorna 2 documentos → patient_context correto
  TC-NODE-004  retrieve_history: retriever retorna lista vazia → patient_context vazio
  TC-NODE-005  generate_report: estado com alertas → final_response contém [!] e risco
  TC-NODE-006  generate_report: estado sem alertas → final_response contém mensagem padrão
"""

import pytest
from unittest.mock import patch, MagicMock

from langchain_core.documents import Document

from analytics.clinical_monitor import RiskLevelEnum, SuicideRiskAssessment
from orchestrator.orchestrator_graph import AgentState, PsychiatricOrchestrator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def orchestrator():
    """
    Instancia o PsychiatricOrchestrator com toda a infra de IA mockada.
    As dependências são interceptadas no módulo orchestrator.orchestrator_graph para
    evitar qualquer inicialização real de LLM, embeddings ou ChromaDB.
    """
    with (
        patch("orchestrator.orchestrator_graph.get_psychiatric_llm"),
        patch("orchestrator.orchestrator_graph.PatientDataManager"),
        patch("orchestrator.orchestrator_graph.ClinicalMonitor"),
    ):
        return PsychiatricOrchestrator()


def _base_state(**overrides) -> AgentState:
    """Fábrica de AgentState mínimo e válido para os testes dos nós."""
    state: AgentState = {
        "patient_id": "PA-TEST",
        "current_note": "Paciente relata ideação suicida ativa com plano estruturado.",
        "risk_assessment": {},
        "patient_context": [],
        "audit_alerts": [],
        "final_response": "",
    }
    state.update(overrides)
    return state


def _make_assessment(risk_level: str = "Alto/Iminente") -> SuicideRiskAssessment:
    """Constrói um SuicideRiskAssessment Pydantic controlado para injeção nos mocks."""
    return SuicideRiskAssessment(
        risk_level=RiskLevelEnum(risk_level),
        passive_ideation=False,
        active_ideation=True,
        red_flags=["plano estruturado", "corda adquirida"],
        protection_factors=[],
        clinical_justification=f"Classificação de teste: {risk_level}.",
    )


# ---------------------------------------------------------------------------
# TC-NODE-001 — analyze_risk: early return quando triagem já preenchida
# ---------------------------------------------------------------------------

def test_analyze_risk_reuses_existing_assessment(orchestrator: PsychiatricOrchestrator):
    """
    TC-NODE-001: Se risk_assessment já contém risk_level no estado inicial,
    o nó deve retornar {} imediatamente (reutilizando a triagem pré-computada)
    sem acionar o ClinicalMonitor.
    """
    state = _base_state(
        risk_assessment={
            "risk_level": "Alto/Iminente",
            "passive_ideation": False,
            "active_ideation": True,
            "red_flags": ["corda"],
            "protection_factors": [],
            "clinical_justification": "Pré-computado.",
        }
    )

    result = orchestrator.analyze_risk(state)

    # Nó deve retornar {} para não sobrescrever o estado existente
    assert result == {}, (
        "Esperado early return {} quando risk_assessment já está preenchido no estado."
    )
    # ClinicalMonitor.detect_risk NÃO deve ter sido chamado
    orchestrator.clinical_monitor.detect_risk.assert_not_called()


# ---------------------------------------------------------------------------
# TC-NODE-002 — analyze_risk: chama detect_risk e serializa output Pydantic
# ---------------------------------------------------------------------------

def test_analyze_risk_calls_detect_risk_and_serializes(orchestrator: PsychiatricOrchestrator):
    """
    TC-NODE-002: Com risk_assessment vazio, o nó deve invocar detect_risk,
    receber o objeto SuicideRiskAssessment Pydantic e retornar seu model_dump()
    no formato correto para o AgentState do LangGraph.
    """
    expected_assessment = _make_assessment("Alto/Iminente")
    orchestrator.clinical_monitor.detect_risk.return_value = expected_assessment

    state = _base_state()  # risk_assessment = {}

    result = orchestrator.analyze_risk(state)

    # detect_risk deve ter sido chamado com o texto da nota
    orchestrator.clinical_monitor.detect_risk.assert_called_once_with(state["current_note"])

    # O retorno deve conter a chave risk_assessment com o dict serializado
    assert "risk_assessment" in result
    ra = result["risk_assessment"]
    assert ra["risk_level"] == "Alto/Iminente"
    assert ra["active_ideation"] is True
    assert ra["passive_ideation"] is False
    assert "plano estruturado" in ra["red_flags"]
    assert isinstance(ra["clinical_justification"], str)


# ---------------------------------------------------------------------------
# TC-NODE-003 — retrieve_history: retorna patient_context com documentos
# ---------------------------------------------------------------------------

def test_retrieve_history_returns_patient_context(orchestrator: PsychiatricOrchestrator):
    """
    TC-NODE-003: O nó deve invocar o retriever do ChromaDB e popular
    patient_context com o page_content de cada documento retornado.
    """
    doc1 = Document(page_content="Tentativa prévia em 2022 por intoxicação.")
    doc2 = Document(page_content="Diagnóstico de Transtorno Bipolar tipo I, instável.")

    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = [doc1, doc2]
    orchestrator.patient_manager.get_patient_retriever.return_value = mock_retriever

    state = _base_state()
    result = orchestrator.retrieve_history(state)

    # Valida que o contexto foi corretamente extraído dos documentos
    assert "patient_context" in result
    context = result["patient_context"]
    assert len(context) == 2
    assert "Tentativa prévia em 2022 por intoxicação." in context
    assert "Diagnóstico de Transtorno Bipolar tipo I, instável." in context

    # Valida que o retriever foi chamado com o patient_id correto
    orchestrator.patient_manager.get_patient_retriever.assert_called_once_with("PA-TEST")


# ---------------------------------------------------------------------------
# TC-NODE-004 — retrieve_history: retorna patient_context vazio
# ---------------------------------------------------------------------------

def test_retrieve_history_returns_empty_context_when_no_docs(orchestrator: PsychiatricOrchestrator):
    """
    TC-NODE-004: Quando o ChromaDB não retorna documentos para o paciente
    (primeira triagem ou dados não ingeridos), patient_context deve ser [].
    """
    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = []
    orchestrator.patient_manager.get_patient_retriever.return_value = mock_retriever

    state = _base_state()
    result = orchestrator.retrieve_history(state)

    assert "patient_context" in result
    assert result["patient_context"] == []


# ---------------------------------------------------------------------------
# TC-NODE-005 — generate_report: relatório com alertas de auditoria
# ---------------------------------------------------------------------------

def test_generate_report_with_audit_alerts(orchestrator: PsychiatricOrchestrator):
    """
    TC-NODE-005: Quando audit_alerts está preenchido, o relatório final deve
    conter o nível de risco, os alertas formatados com [!] e o texto da nota.
    """
    state = _base_state(
        risk_assessment={
            "risk_level": "Alto/Iminente",
            "red_flags": ["carta de despedida", "raticida"],
            "protection_factors": [],
            "clinical_justification": "Comportamento preparatório confirmado.",
        },
        audit_alerts=[
            "[FALHA CRÍTICA]: Alta concedida para paciente de risco iminente.",
            "[ALERTA DE SEGURANÇA]: Sem registro de internação.",
        ],
    )

    result = orchestrator.generate_report(state)

    assert "final_response" in result
    report = result["final_response"]

    # Deve conter o nível de risco identificado
    assert "Alto/Iminente" in report
    # Deve formatar os alertas com prefixo [!]
    assert "[!]" in report
    assert "[FALHA CRÍTICA]" in report
    assert "[ALERTA DE SEGURANÇA]" in report
    # Deve incluir a nota clínica analisada
    assert state["current_note"] in report
    # Deve conter o cabeçalho do parecer executivo
    assert "PARECER EXECUTIVO" in report


# ---------------------------------------------------------------------------
# TC-NODE-006 — generate_report: relatório sem alertas (conduta adequada)
# ---------------------------------------------------------------------------

def test_generate_report_without_audit_alerts(orchestrator: PsychiatricOrchestrator):
    """
    TC-NODE-006: Quando audit_alerts está vazio (conduta médica adequada),
    o relatório deve conter a mensagem padrão de ausência de divergências.
    """
    state = _base_state(
        risk_assessment={
            "risk_level": "Alto/Iminente",
            "red_flags": ["ideação ativa"],
            "protection_factors": ["suporte familiar"],
            "clinical_justification": "Internação acionada corretamente.",
        },
        audit_alerts=[],  # Sem alertas — conduta adequada
    )

    result = orchestrator.generate_report(state)

    assert "final_response" in result
    report = result["final_response"]

    # Mensagem padrão de ausência de divergências graves
    assert "Nenhuma divergência grave" in report
    # Não deve conter prefixos de alerta
    assert "[FALHA CRÍTICA]" not in report
    assert "[ALERTA DE SEGURANÇA]" not in report
    # Fatores de proteção devem estar no relatório
    assert "suporte familiar" in report
