import os
import pytest
from database.patient_manager import PatientDataManager

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def manager(tmp_path):
    """Instância do PatientDataManager com banco SQLite temporário por teste."""
    db_file = str(tmp_path / "test_clinical.db")
    return PatientDataManager(db_path=db_file)


# ---------------------------------------------------------------------------
# TC-DB-001: Isolamento de dados entre pacientes distintos
# ---------------------------------------------------------------------------

def test_patient_data_isolation(manager):
    """Garante que os registros de pacientes distintos não vazam entre si."""
    patient_a = "PA-100"
    patient_b = "PB-200"

    manager.upsert_note(patient_a, "Paciente A relata tristeza profunda e ideação suicida passiva.")
    manager.upsert_note(patient_b, "Paciente B está clinicamente estável, nega ideação.")

    # Retriever do Paciente A deve conter apenas notas de A
    retriever_a = manager.get_patient_retriever(patient_a)
    docs_a = retriever_a.invoke("ideação suicida ou tristeza")

    assert len(docs_a) > 0
    for doc in docs_a:
        assert doc.metadata["patient_id"] == patient_a
        assert "Paciente A" in doc.page_content
        assert "Paciente B" not in doc.page_content

    # Retriever do Paciente B deve conter apenas notas de B
    retriever_b = manager.get_patient_retriever(patient_b)
    docs_b = retriever_b.invoke("ideação suicida ou tristeza")

    assert len(docs_b) > 0
    for doc in docs_b:
        assert doc.metadata["patient_id"] == patient_b
        assert "Paciente B" in doc.page_content
        assert "Paciente A" not in doc.page_content


# ---------------------------------------------------------------------------
# TC-DB-002: Exclusão lógica — Direito ao Esquecimento (LGPD)
# ---------------------------------------------------------------------------

def test_patient_data_deletion(manager):
    """Após delete_patient_data, nenhum registro deve ser recuperável."""
    patient_id = "PA-DEL-100"

    manager.upsert_note(patient_id, "Histórico clínico do paciente para exclusão.")

    retriever = manager.get_patient_retriever(patient_id)
    docs_before = retriever.invoke("Histórico")
    assert len(docs_before) > 0

    manager.delete_patient_data(patient_id)

    docs_after = retriever.invoke("Histórico")
    assert len(docs_after) == 0

    history_after = manager.get_patient_history(patient_id)
    assert history_after == []


# ---------------------------------------------------------------------------
# TC-DB-003: Histórico com metadados de triagem completos
# ---------------------------------------------------------------------------

def test_patient_history_with_triage_metadata(manager):
    """Valida serialização/desserialização de listas e estrutura completa do histórico."""
    patient_id = "PA-HIST-300"

    triage_meta = {
        "has_triage": True,
        "risk_level": "Moderado",
        "passive_ideation": True,
        "active_ideation": False,
        "red_flags": ["Diagnóstico psiquiátrico instável"],
        "protection_factors": ["Rede de apoio familiar"],
        "clinical_justification": "Ideação passiva com diagnóstico ativo.",
        "audit_alerts": ["[RECOMENDAÇÃO]: Contrato terapêutico"],
        "final_report": "PARECER TESTE",
    }

    manager.upsert_note(patient_id, "Nota de teste para histórico.", metadata=triage_meta)

    history = manager.get_patient_history(patient_id)
    assert len(history) == 1

    record = history[0]
    assert record["patient_id"] == patient_id
    assert record["has_triage"] is True
    assert record["risk_assessment"]["risk_level"] == "Moderado"
    assert record["risk_assessment"]["red_flags"] == ["Diagnóstico psiquiátrico instável"]
    assert record["risk_assessment"]["protection_factors"] == ["Rede de apoio familiar"]
    assert record["audit_alerts"] == ["[RECOMENDAÇÃO]: Contrato terapêutico"]
    assert record["final_report"] == "PARECER TESTE"


# ---------------------------------------------------------------------------
# TC-DB-004: Upsert por job_id — atualização do registro pré-registrado
# ---------------------------------------------------------------------------

def test_upsert_updates_existing_record_by_job_id(manager):
    """O segundo upsert com mesmo job_id deve ATUALIZAR, não duplicar."""
    patient_id = "PA-UPS-400"
    job_id = "aaaabbbb-cccc-dddd-eeee-ffffffffffff"

    # Pré-registro (has_triage=False)
    manager.upsert_note(patient_id, "Nota inicial.", metadata={
        "has_triage": False,
        "job_id": job_id,
        "job_status": "processing",
    })

    # Atualização após triagem (has_triage=True)
    manager.upsert_note(patient_id, "Nota com triagem completa.", metadata={
        "has_triage": True,
        "job_id": job_id,
        "job_status": "completed",
        "risk_level": "Alto/Iminente",
        "audit_alerts": ["[FALHA CRÍTICA]: conduta inadequada"],
    })

    history = manager.get_patient_history(patient_id)
    # Deve haver exatamente 1 registro (upsert, não insert duplicado)
    assert len(history) == 1
    record = history[0]
    assert record["has_triage"] is True
    assert record["risk_assessment"]["risk_level"] == "Alto/Iminente"
    assert len(record["audit_alerts"]) == 1
