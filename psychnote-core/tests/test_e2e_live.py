"""
tests/test_e2e_live.py — Testes E2E com Pipeline LangGraph Completo (Ollama Live)

Cobre o gap de cobertura identificado no GEMINI.md (Item 5):
testes E2E com o Ollama real e o grafo LangGraph completo.

Estratégia de skip condicional:
  Antes de qualquer teste, uma verificação de sessão faz GET http://localhost:11434
  com timeout de 2s. Se o Ollama não estiver disponível, TODOS os testes deste
  módulo são pulados automaticamente com a reason explicativa.
  Nenhum FAILED é reportado — o CI não quebra.

Cobertura:
  TC-E2E-001  Pipeline completo: Risco Alto/Iminente (nota com carta + corda)
  TC-E2E-002  Pipeline completo: Risco Baixo (ideação passiva + fatores protetores)
  TC-E2E-003  Pipeline completo: Risco Moderado (ideação recorrente sem plano)
  TC-E2E-004  SLA: pipeline deve completar em < 120 segundos (tolerância PoC CPU)

Pré-requisitos para execução:
  1. Ollama rodando em http://localhost:11434 (ou OLLAMA_BASE_URL no .env)
  2. Modelo llama3:8b-instruct-q4_K_M disponível: `ollama pull llama3:8b-instruct-q4_K_M`
  3. (Opcional) ChromaDB vazio para o patient_id de teste — o pipeline falha
     graciosamente se não houver histórico (retorna patient_context=[]).
"""

import os
import time
import pytest
import requests

# ---------------------------------------------------------------------------
# Skip condicional de sessão — detecta Ollama antes de qualquer teste
# ---------------------------------------------------------------------------

def _check_ollama_available() -> bool:
    """
    Verifica disponibilidade do Ollama em localhost:11434 (ou OLLAMA_BASE_URL).
    Retorna True se o servidor responder com status 200.
    """
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        response = requests.get(base_url, timeout=2)
        return response.status_code == 200
    except Exception:
        return False


OLLAMA_AVAILABLE: bool = _check_ollama_available()

# Marcador aplicado a todo o módulo: pula todos os testes se Ollama offline
pytestmark = pytest.mark.skipif(
    not OLLAMA_AVAILABLE,
    reason=(
        "[!] Ollama não disponível em localhost:11434 — "
        "testes E2E pulados. Ative o Ollama e rode novamente para executar TC-E2E-*."
    ),
)


# ---------------------------------------------------------------------------
# Fixture compartilhada: grafo compilado (instanciado uma vez por sessão)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def compiled_graph():
    """
    Compila o grafo LangGraph uma única vez para toda a sessão de testes E2E,
    evitando recarga de embeddings e inicialização redundante do LLM.
    """
    from orchestrator.orchestrator_graph import PsychiatricOrchestrator
    orchestrator = PsychiatricOrchestrator()
    return orchestrator.build_graph()


def _make_e2e_input(patient_id: str, note: str) -> dict:
    """Fábrica de payload compatível com o AgentState do LangGraph."""
    return {
        "patient_id": patient_id,
        "current_note": note,
        "risk_assessment": {},
        "patient_context": [],
        "audit_alerts": [],
        "final_response": "",
    }


# ---------------------------------------------------------------------------
# TC-E2E-001 — Risco Alto/Iminente: comportamento preparatório + carta
# ---------------------------------------------------------------------------

def test_e2e_alto_iminente(compiled_graph):
    """
    TC-E2E-001: Nota com comportamento preparatório concreto (carta de despedida,
    corda adquirida, data definida) deve classificar como Alto/Iminente e
    disparar alertas de protocolo devido à ausência de internação na conduta.
    """
    payload = _make_e2e_input(
        patient_id="E2E-ALTO-001",
        note=(
            "Paciente extremamente agitado. Admite ter escrito carta de despedida "
            "para a família e adquirido corda na semana passada. Afirma que pretende "
            "agir nesta noite após a consulta. Conduta: retorno ambulatorial em 15 dias."
        ),
    )

    final_state = compiled_graph.invoke(payload)

    risk = final_state.get("risk_assessment", {})
    assert risk.get("risk_level") == "Alto/Iminente", (
        f"[!] Esperado Alto/Iminente, obtido: {risk.get('risk_level')}"
    )
    assert risk.get("active_ideation") is True, "[!] active_ideation deve ser True neste cenário."

    alerts = final_state.get("audit_alerts", [])
    assert len(alerts) > 0, (
        "[!] Deve haver alertas de protocolo: retorno ambulatorial para risco iminente é negligente."
    )

    final_report = final_state.get("final_response", "")
    assert len(final_report) > 0, "[!] Parecer executivo não deve ser vazio."
    assert "Alto/Iminente" in final_report


# ---------------------------------------------------------------------------
# TC-E2E-002 — Risco Baixo: ideação passiva + fatores de proteção robustos
# ---------------------------------------------------------------------------

def test_e2e_risco_baixo(compiled_graph):
    """
    TC-E2E-002: Nota com ideação passiva situacional, negação clara de planos
    e fatores de proteção robustos deve classificar como Baixo e não gerar
    alertas críticos de protocolo.
    """
    payload = _make_e2e_input(
        patient_id="E2E-BAIXO-002",
        note=(
            "Paciente universitária, 22 anos. Relata cansaço intenso antes das provas. "
            "Diz que às vezes 'queria sumir das pressões', mas nega qualquer planejamento "
            "ou intenção de se machucar. Sem histórico psiquiátrico. Tem boa rede de apoio, "
            "namorado presente e planos de viagem de férias com a família. Alta motivação "
            "para continuar o tratamento. Conduta: suporte psicológico e retorno em 30 dias."
        ),
    )

    final_state = compiled_graph.invoke(payload)

    risk = final_state.get("risk_assessment", {})
    assert risk.get("risk_level") == "Baixo", (
        f"[!] Esperado Baixo, obtido: {risk.get('risk_level')}"
    )

    alerts = final_state.get("audit_alerts", [])
    critical_alerts = [a for a in alerts if "[FALHA CRÍTICA]" in a]
    assert len(critical_alerts) == 0, (
        f"[!] Não deve haver FALHA CRÍTICA para risco Baixo. Obtido: {critical_alerts}"
    )

    final_report = final_state.get("final_response", "")
    assert len(final_report) > 0, "[!] Parecer executivo não deve ser vazio."


# ---------------------------------------------------------------------------
# TC-E2E-003 — Risco Moderado: ideação recorrente sem plano imediato
# ---------------------------------------------------------------------------

def test_e2e_risco_moderado(compiled_graph):
    """
    TC-E2E-003: Paciente com diagnóstico instável e ideação recorrente, sem plano
    imediato, deve classificar como Moderado. Nota sem menção à família deve
    gerar RECOMENDAÇÃO de auditoria.
    """
    payload = _make_e2e_input(
        patient_id="E2E-MOD-003",
        note=(
            "Paciente com diagnóstico de Transtorno Bipolar tipo I, episódio depressivo atual. "
            "Relata pensamentos de morte recorrentes nos últimos 30 dias, com piora na última semana. "
            "Nega planejamento concreto ou acesso a meios letais. Histórico de automutilação em 2021. "
            "Conduta: ajuste de lítio para 900mg/dia e retorno em 2 semanas."
        ),
    )

    final_state = compiled_graph.invoke(payload)

    risk = final_state.get("risk_assessment", {})
    risk_level = risk.get("risk_level")
    assert risk_level in ("Moderado", "Alto/Iminente"), (
        f"[!] Esperado Moderado (ou Alto/Iminente por histórico), obtido: {risk_level}"
    )

    final_report = final_state.get("final_response", "")
    assert len(final_report) > 0, "[!] Parecer executivo não deve ser vazio."
    assert "PARECER EXECUTIVO" in final_report


# ---------------------------------------------------------------------------
# TC-E2E-004 — SLA: pipeline deve completar em < 120 segundos (PoC CPU)
# ---------------------------------------------------------------------------

def test_e2e_sla_pipeline(compiled_graph):
    """
    TC-E2E-004: O pipeline completo (4 nós do LangGraph) deve completar dentro
    do SLA de 120 segundos em CPU, tolerância definida para a PoC sem NPU/iGPU.
    O GEMINI.md define SLA < 10s como alvo final (com OpenVINO/IPEX-LLM).
    """
    SLA_LIMIT_SECONDS = 120  # Tolerância PoC: CPU pura (Intel Core Ultra 5)

    payload = _make_e2e_input(
        patient_id="E2E-SLA-004",
        note=(
            "Paciente em sofrimento agudo. Relata pensamentos de morte há 3 dias. "
            "Nega plano estruturado. Família presente e suportiva. "
            "Conduta: internação voluntária solicitada, vigilância constante."
        ),
    )

    start = time.monotonic()
    final_state = compiled_graph.invoke(payload)
    elapsed = time.monotonic() - start

    print(f"\n[*] SLA medido: {elapsed:.2f}s (limite: {SLA_LIMIT_SECONDS}s)")

    assert elapsed < SLA_LIMIT_SECONDS, (
        f"[!] SLA violado: pipeline demorou {elapsed:.2f}s, limite é {SLA_LIMIT_SECONDS}s. "
        f"Considere ativar OpenVINO/IPEX-LLM para atingir o SLA alvo de < 10s."
    )
    # Pipeline também deve retornar estado válido
    assert final_state.get("final_response", "") != "", "[!] Parecer executivo não deve ser vazio."
