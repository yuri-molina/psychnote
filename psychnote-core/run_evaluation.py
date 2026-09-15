import json
import time
import os
from typing import List, Dict
from database.patient_manager import PatientDataManager
from orchestrator.orchestrator_graph import PsychiatricOrchestrator

def load_synthetic_data(filepath: str = "synthetic_patients.json") -> List[Dict]:
    """Lê o dataset sintético gerado pelo LLM."""
    if not os.path.exists(filepath):
        print(f"[!] Erro Crítico: Ficheiro {filepath} não encontrado.")
        print("Certifica-te de que guardaste os resultados do Gemini CLI neste diretório.")
        return []
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] Erro ao analisar o JSON: {e}")
        return []

def run_mass_evaluation():
    print("=== INICIANDO AVALIAÇÃO EM LOTE (DATASET SINTÉTICO) ===")
    print("=== PLATAFORMA PSICRE-AI - AUDITORIA DE RISCO DE SUICÍDIO ===\n")
    
    dataset = load_synthetic_data()
    if not dataset:
        return

    p_manager = PatientDataManager()
    orchestrator = PsychiatricOrchestrator()
    graph = orchestrator.build_graph()

    total_cases = len(dataset)
    acertos = 0
    
    # Dicionário para compor a Matriz de Confusão / Desempenho
    matriz_desempenho = {
        "Alto/Iminente": {"acertos": 0, "erros": 0},
        "Moderado": {"acertos": 0, "erros": 0},
        "Baixo": {"acertos": 0, "erros": 0},
        "Falso_Positivo": {"acertos": 0, "erros": 0}
    }

    start_total_time = time.time()

    for idx, patient in enumerate(dataset, 1):
        patient_id = patient.get("patient_id", f"PAC-TEST-{idx}")
        true_risk = patient.get("true_risk_level", "")
        hist_notes = patient.get("historical_notes", [])
        curr_note = patient.get("current_note", "")

        print(f"\n[*] A processar Paciente {idx}/{total_cases}: {patient_id} (Risco Real: {true_risk})")
        
        # 1. Limpeza e Ingestão Isolada do Histórico (Edge AI Vector DB)
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
            "final_response": ""
        }
        
        start_infer = time.time()
        result = graph.invoke(inputs)
        end_infer = time.time()
        
        # Extração da previsão feita pelo módulo Pydantic
        predicted_risk = result.get("risk_assessment", {}).get("risk_level", "Desconhecido")
        
        # 3. Validação do Acerto (Com lógica especial para Falsos Positivos)
        is_correct = False
        # Se o caso era um falso positivo estrutural, a IA acertou se classificou como Baixo Risco
        if true_risk == "Falso_Positivo" and predicted_risk == "Baixo":
            is_correct = True
        elif true_risk == predicted_risk:
            is_correct = True
            
        # 4. Registo de Métricas
        if is_correct:
            acertos += 1
            if true_risk in matriz_desempenho:
                matriz_desempenho[true_risk]["acertos"] += 1
            print(f" -> [SUCESSO] Risco previsto corretamente: {predicted_risk} ({end_infer - start_infer:.2f}s)")
        else:
            if true_risk in matriz_desempenho:
                matriz_desempenho[true_risk]["erros"] += 1
            print(f" -> [FALHA] Risco previsto: {predicted_risk} | Esperado: {true_risk} ({end_infer - start_infer:.2f}s)")
            print(f"    Justificação da IA: {result.get('risk_assessment', {}).get('clinical_justification', 'Nenhuma')}")
            
        # Opcional: imprimir alertas de auditoria detetados
        if result.get("audit_alerts"):
            print(f"    Alertas de Auditoria disparados: {len(result['audit_alerts'])}")

    end_total_time = time.time()
    
    # 5. Relatório Executivo (Para usar na secção de Resultados do TCC)
    accuracy = (acertos / total_cases) * 100 if total_cases > 0 else 0
    avg_latency = (end_total_time - start_total_time) / total_cases if total_cases > 0 else 0
    
    print("\n" + "="*60)
    print("=== RELATÓRIO DE VALIDAÇÃO CLÍNICA E DESEMPENHO (TCC) ===")
    print("="*60)
    print(f"Total de Prontuários Sintéticos Processados: {total_cases}")
    print(f"Tempo Total do Lote: {end_total_time - start_total_time:.2f}s")
    print(f"Latência Média por Inferência (SLA < 10s): {avg_latency:.2f}s")
    print(f"Acurácia Global do Sistema Pydantic/LangGraph: {accuracy:.1f}%\n")
    
    print("=== MATRIZ DE DESEMPENHO POR COORTE CLÍNICA ===")
    for coorte, stats in matriz_desempenho.items():
        t = stats["acertos"] + stats["erros"]
        if t > 0:
            acc = (stats["acertos"] / t) * 100
            print(f"- Coorte {coorte.ljust(15)}: {stats['acertos']}/{t} acertos ({acc:.1f}%)")
        else:
            print(f"- Coorte {coorte.ljust(15)}: Sem dados no dataset.")
    print("="*60)
    print("DICA PARA O TCC: Extraia a Acurácia Global e a Latência Média para provar a viabilidade clínica e o ROI do Edge AI.")

if __name__ == "__main__":
    run_mass_evaluation()