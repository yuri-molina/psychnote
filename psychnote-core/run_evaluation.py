import argparse
import json
import os
import time
from typing import Dict, List
from dotenv import load_dotenv

# Carrega variáveis de ambiente (.env)
load_dotenv()

from config.engine import LLMProvider
from database.patient_manager import PatientDataManager
from orchestrator.orchestrator_graph import PsychiatricOrchestrator


def load_synthetic_data(filepath: str = "synthetic_patients.json") -> List[Dict]:
    """Lê o dataset sintético de pacientes."""
    if not os.path.exists(filepath):
        print(f"[!] Erro Crítico: Ficheiro {filepath} não encontrado.")
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] Erro ao analisar o JSON: {e}")
        return []


def run_mass_evaluation(provider: LLMProvider = LLMProvider.OLLAMA):
    provider_name = "Gemini (gemini-3.8-flash)" if provider == LLMProvider.GEMINI else "Ollama (llama3:8b-instruct-q4_K_M)"
    print("=" * 65)
    print("=== INICIANDO AVALIAÇÃO EM LOTE (DATASET SINTÉTICO) ===")
    print("=== PLATAFORMA PSICRE-AI - AUDITORIA DE RISCO DE SUICÍDIO ===")
    print(f"=== PROVEDOR DE LLM: {provider_name} ===")
    print("=" * 65 + "\n")

    dataset = load_synthetic_data()
    if not dataset:
        return

    # Instância do banco SQLite local temporário/persistente
    p_manager = PatientDataManager(db_path="./eval_clinical.db")
    orchestrator = PsychiatricOrchestrator(llm_provider=provider)
    graph = orchestrator.build_graph()

    total_cases = len(dataset)
    acertos = 0

    matriz_desempenho = {
        "Alto/Iminente": {"acertos": 0, "erros": 0},
        "Moderado": {"acertos": 0, "erros": 0},
        "Baixo": {"acertos": 0, "erros": 0},
        "Falso_Positivo": {"acertos": 0, "erros": 0},
    }

    results_detail = []
    start_total_time = time.time()

    for idx, patient in enumerate(dataset, 1):
        patient_id = patient.get("patient_id", f"PAC-TEST-{idx}")
        true_risk = patient.get("true_risk_level", "")
        hist_notes = patient.get("historical_notes", [])
        curr_note = patient.get("current_note", "")

        print(f"\n[*] A processar Paciente {idx}/{total_cases}: {patient_id} (Risco Real: {true_risk})")

        # 1. Limpeza e Ingestão Isolada do Histórico (SQLite)
        p_manager.delete_patient_data(patient_id)
        for note in hist_notes:
            p_manager.upsert_note(patient_id, note)

        # 2. Orquestração do Grafo e Auditoria
        inputs = {
            "patient_id": patient_id,
            "current_note": curr_note,
            "risk_assessment": {},
            "patient_context": [],
            "audit_alerts": [],
            "final_response": "",
        }

        start_infer = time.time()
        try:
            result = graph.invoke(inputs)
        except Exception as err:
            print(f" -> [ERRO NA INFERÊNCIA]: {err}")
            continue
        end_infer = time.time()
        infer_latency = end_infer - start_infer

        # Extração da previsão feita pelo módulo Pydantic
        risk_assessment = result.get("risk_assessment", {})
        raw_risk = risk_assessment.get("risk_level", "Desconhecido")
        predicted_risk = str(raw_risk.value if hasattr(raw_risk, "value") else raw_risk)
        clinical_justification = risk_assessment.get("clinical_justification", "Nenhuma")

        # 3. Validação do Acerto
        is_correct = False
        if true_risk == "Falso_Positivo" and predicted_risk == "Baixo":
            is_correct = True
        elif true_risk == predicted_risk:
            is_correct = True

        time.sleep(1.0)

        # 4. Registo de Métricas
        if is_correct:
            acertos += 1
            if true_risk in matriz_desempenho:
                matriz_desempenho[true_risk]["acertos"] += 1
            print(f" -> [SUCESSO] Risco previsto corretamente: {predicted_risk} ({infer_latency:.2f}s)")
        else:
            if true_risk in matriz_desempenho:
                matriz_desempenho[true_risk]["erros"] += 1
            print(f" -> [FALHA] Risco previsto: {predicted_risk} | Esperado: {true_risk} ({infer_latency:.2f}s)")
            print(f"    Justificação da IA: {clinical_justification}")

        if result.get("audit_alerts"):
            print(f"    Alertas de Auditoria disparados: {len(result['audit_alerts'])}")

        results_detail.append({
            "patient_id": patient_id,
            "true_risk": true_risk,
            "predicted_risk": predicted_risk,
            "is_correct": is_correct,
            "latency_s": round(infer_latency, 2),
            "justification": clinical_justification,
            "audit_alerts": result.get("audit_alerts", []),
        })

    end_total_time = time.time()
    total_time = end_total_time - start_total_time

    # 5. Relatório Executivo
    accuracy = (acertos / total_cases) * 100 if total_cases > 0 else 0
    avg_latency = total_time / total_cases if total_cases > 0 else 0

    print("\n" + "=" * 65)
    print("=== RELATÓRIO DE VALIDAÇÃO CLÍNICA E DESEMPENHO (TCC) ===")
    print(f"=== PROVEDOR: {provider_name} ===")
    print("=" * 65)
    print(f"Total de Prontuários Sintéticos Processados: {total_cases}")
    print(f"Tempo Total do Lote: {total_time:.2f}s")
    print(f"Latência Média por Inferência: {avg_latency:.2f}s")
    print(f"Acurácia Global do Sistema Pydantic/LangGraph: {accuracy:.1f}%\n")

    print("=== MATRIZ DE DESEMPENHO POR COORTE CLÍNICA ===")
    for coorte, stats in matriz_desempenho.items():
        t = stats["acertos"] + stats["erros"]
        if t > 0:
            acc = (stats["acertos"] / t) * 100
            print(f"- Coorte {coorte.ljust(15)}: {stats['acertos']}/{t} acertos ({acc:.1f}%)")

    print("=" * 65)

    return {
        "provider": provider_name,
        "total_cases": total_cases,
        "total_time_s": round(total_time, 2),
        "avg_latency_s": round(avg_latency, 2),
        "accuracy_pct": round(accuracy, 1),
        "matriz_desempenho": matriz_desempenho,
        "details": results_detail,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executa avaliação em lote dos casos sintéticos.")
    parser.add_argument(
        "--provider",
        type=int,
        choices=[1, 2],
        default=1,
        help="Provedor de LLM: 1 = Ollama (llama3:8b), 2 = Gemini (gemini-3.8-flash)",
    )
    args = parser.parse_args()

    prov = LLMProvider.GEMINI if args.provider == 2 else LLMProvider.OLLAMA
    run_mass_evaluation(provider=prov)