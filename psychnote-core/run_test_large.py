"""
run_test_large.py — Teste de Alta Carga: Prontuário JS-2026

Executa o pipeline completo do LangGraph sobre um prontuário de alta
complexidade (Depressão Resistente F33.2), validando:
  1. Indexação de notas longas no ChromaDB (chunking por seções ##)
  2. Triagem estruturada (ClinicalMonitor / Pydantic)
  3. Orquestração do grafo LangGraph (triagem → histórico → auditoria → parecer)
  4. Geração de resumo narrativo longitudinal

NOTA: A ingestão PubMed (ScienceFetcher) foi REMOVIDA deste script
      por decisão arquitetural (GEMINI.md §6.4): o fluxo de pesquisa
      farmacológica deve rodar em grafo LangGraph separado, nunca
      acoplado ao fluxo de emergência suicida.
"""

import sys
import os
import time

# Garante imports absolutos independente do diretório de execução
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.patient_manager import PatientDataManager
from orchestrator.orchestrator_graph import PsychiatricOrchestrator
from analytics.clinical_monitor import ClinicalMonitor, SuicideRiskAssessment


def run_large_scale_test() -> None:
    print("=== INICIANDO TESTE DE ALTA CARGA: JS-2026 ===\n")

    # ------------------------------------------------------------------
    # 1. Carrega o prontuário extenso
    # ------------------------------------------------------------------
    prontuario_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PRONTUARIO_JS_2026.txt")
    with open(prontuario_path, "r", encoding="utf-8") as f:
        large_record = f.read()

    patient_id = "JS-2026"

    # ------------------------------------------------------------------
    # 2. Indexação do prontuário no ChromaDB
    #    Chunk por seção "##" para preservar granularidade de recuperação
    # ------------------------------------------------------------------
    print(f"[*] Step 1: Indexando prontuário de alta complexidade para ID {patient_id}...")
    db = PatientDataManager()
    sections = [s.strip() for s in large_record.split("##") if s.strip()]

    if not sections:
        print("[!] Prontuário sem seções delimitadas por '##'. Indexando como bloco único.")
        sections = [large_record]

    for i, section in enumerate(sections, start=1):
        db.upsert_note(patient_id, section)
        print(f"    [+] Seção {i}/{len(sections)} indexada ({len(section)} chars).")

    # ------------------------------------------------------------------
    # 3. Triagem Estruturada (ClinicalMonitor → SuicideRiskAssessment)
    # ------------------------------------------------------------------
    print("\n[*] Step 2: Monitoramento Clínico — Analisando Riscos Críticos...")
    monitor = ClinicalMonitor()

    try:
        risk_analysis: SuicideRiskAssessment = monitor.detect_risk(large_record)
    except Exception as exc:
        print(f"[!] Falha na triagem estruturada: {exc}")
        raise

    print(
        f"[+] Triagem concluída | Nível: {risk_analysis.risk_level.value} "
        f"| Justificativa: {risk_analysis.clinical_justification}"
    )

    # ------------------------------------------------------------------
    # 4. Orquestração LangGraph (RAG completo)
    #    O risk_assessment pré-computado é passado no estado inicial
    #    para economizar uma inferência no Nó 1 (reutilização de triagem).
    # ------------------------------------------------------------------
    print("\n[*] Step 3: Orquestrando Análise RAG Cruzada (LangGraph)...")
    orchestrator = PsychiatricOrchestrator()
    graph = orchestrator.build_graph()

    # Payload compatível com AgentState (TypedDict) definido em rag_logic.py
    graph_input = {
        "patient_id": patient_id,
        "current_note": large_record,
        "risk_assessment": risk_analysis.model_dump(),  # Pydantic v2 → dict
        "patient_context": [],
        "audit_alerts": [],
        "final_response": "",
    }

    start_time = time.time()
    try:
        result: dict = graph.invoke(graph_input)
    except Exception as exc:
        print(f"[!] Falha na execução do grafo LangGraph: {exc}")
        raise
    elapsed = time.time() - start_time

    print("\n" + "=" * 50)
    print("SAÍDA DO SISTEMA — PARECER EXECUTIVO")
    print("=" * 50)
    print(f"TEMPO DE RESPOSTA: {elapsed:.2f}s")
    print(f"\nALERTAS DE PROTOCOLO: {result.get('audit_alerts', [])}")
    print(f"\nPARECER DA IA:\n{result.get('final_response', '[sem resposta]')}")
    print("=" * 50)

    # ------------------------------------------------------------------
    # 5. Resumo Narrativo Longitudinal (Map-Reduce sobre ChromaDB)
    # ------------------------------------------------------------------
    print("\n[*] Step 4: Gerando Resumo Narrativo de Evolução (Map-Reduce)...")
    try:
        summary = monitor.generate_summary(patient_id)
        print(f"[+] EVOLUÇÃO CONSOLIDADA:\n{summary}")
    except Exception as exc:
        print(f"[!] Falha ao gerar resumo narrativo: {exc}")


if __name__ == "__main__":
    run_large_scale_test()
