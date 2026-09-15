import pytest
from orchestrator.orchestrator_graph import PsychiatricOrchestrator

def test_audit_conduct_high_risk_discharge_alert():
    orchestrator = PsychiatricOrchestrator()
    
    # Risco Alto mas nota sugere alta do paciente
    state = {
        "patient_id": "PA-100",
        "current_note": "Paciente com ideação suicida ativa e planos concretos. Conduta: Alta concedida e liberado.",
        "risk_assessment": {"risk_level": "Alto/Iminente"},
        "patient_context": [],
        "audit_alerts": [],
        "final_response": ""
    }
    
    result = orchestrator.audit_conduct(state)
    alerts = result.get("audit_alerts", [])
    
    assert len(alerts) > 0
    assert any("[FALHA CRÍTICA]" in alert for alert in alerts)
    assert any("alta ou liberação" in alert for alert in alerts)

def test_audit_conduct_high_risk_missing_hospitalization_alert():
    orchestrator = PsychiatricOrchestrator()
    
    # Risco Alto mas sem menção a hospitalização ou vigilância
    state = {
        "patient_id": "PA-100",
        "current_note": "Paciente refere plano de se atirar de altura. Aumentei a dose do antidepressivo.",
        "risk_assessment": {"risk_level": "Alto/Iminente"},
        "patient_context": [],
        "audit_alerts": [],
        "final_response": ""
    }
    
    result = orchestrator.audit_conduct(state)
    alerts = result.get("audit_alerts", [])
    
    assert len(alerts) > 0
    assert any("[ALERTA DE SEGURANÇA]" in alert for alert in alerts)
    assert any("internação psiquiátrica" in alert for alert in alerts)

def test_audit_conduct_moderate_risk_missing_family_recommendation():
    orchestrator = PsychiatricOrchestrator()
    
    # Risco Moderado sem mencionar a família ou contrato terapêutico
    state = {
        "patient_id": "PA-100",
        "current_note": "Paciente com ideação recorrente. Ajustei a medicação e marquei retorno.",
        "risk_assessment": {"risk_level": "Moderado"},
        "patient_context": [],
        "audit_alerts": [],
        "final_response": ""
    }
    
    result = orchestrator.audit_conduct(state)
    alerts = result.get("audit_alerts", [])
    
    assert len(alerts) > 0
    assert any("[RECOMENDAÇÃO]" in alert for alert in alerts)
    assert any("acionar a família" in alert for alert in alerts)

def test_audit_conduct_no_alerts_when_conduct_adequate():
    orchestrator = PsychiatricOrchestrator()
    
    # Risco Alto e conduta adequada
    state = {
        "patient_id": "PA-100",
        "current_note": "Paciente com risco de autoextermínio. Acionamos o SAMU e encaminhamos para internação de urgência.",
        "risk_assessment": {"risk_level": "Alto/Iminente"},
        "patient_context": [],
        "audit_alerts": [],
        "final_response": ""
    }
    
    result = orchestrator.audit_conduct(state)
    alerts = result.get("audit_alerts", [])
    
    # Não deve disparar alertas críticos de negligência
    assert not any("[FALHA CRÍTICA]" in alert for alert in alerts)
