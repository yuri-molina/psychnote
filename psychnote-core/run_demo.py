import time
from database.patient_manager import PatientDataManager
from orchestrator.orchestrator_graph import PsychiatricOrchestrator

def run_complete_demo():
    print("=== INICIANDO DEMO: PLATAFORMA PSICRE-AI (EDGE AI - NPU) ===")
    print("=== MÓDULO: TRIAGEM E AUDITORIA DE RISCO DE SUICÍDIO ===\n")
    
    # 1. Configuração do Banco de Dados Vetorial (Isolamento via Metadados LGPD)
    print("Step 1: Preparando ambiente e registrando Histórico do Paciente...")
    p_manager = PatientDataManager()
    patient_id = "MARIA-001"
    
    # Limpa dados de execuções anteriores para garantir um teste limpo
    p_manager.delete_patient_data(patient_id)
    
    # Ingestão de Nota Histórica (Simulando um Fator Estático: Tentativa prévia)
    p_manager.upsert_note(
        patient_id, 
        "2023-10-10: Paciente deu entrada no PS após tentativa de autoextermínio por ingestão medicamentosa. Diagnosticada com Transtorno Bipolar."
    )
    
    # 2. Orquestração da Inteligência Artificial (LangGraph)
    print("\nStep 2: Orquestração LangGraph (Triagem -> Busca Histórica -> Auditoria)...")
    orchestrator = PsychiatricOrchestrator()
    graph = orchestrator.build_graph()
    
    # Nota atual simulando Fatores Dinâmicos (Gatilhos) e uma CONDUTA MÉDICA INADEQUADA
    current_note = (
        "2024-05-20: Paciente relata perda de emprego recente e luto pela morte da mãe. "
        "Chora muito durante a consulta, diz que 'não aguenta mais e que a vida perdeu o sentido'. "
        "Afirma ter pesquisado na internet formas de acabar com o sofrimento e comprou uma corda. "
        "Conduta médica: Aumentei a dose da medicação e agendei retorno ambulatorial para daqui a 30 dias. Alta liberada."
    )
    
    inputs = {
        "patient_id": patient_id,
        "current_note": current_note,
        "risk_assessment": {},
        "patient_context": [],
        "audit_alerts": [],
        "final_response": ""
    }
    
    start_time = time.time()
    print("\n[*] Executando Inferência Local (Simulando NPU)...")
    
    # Inicia o pipeline determinístico do LangGraph
    result = graph.invoke(inputs)
    end_time = time.time()
    
    print("\n" + "="*70)
    print(f"=== PARECER EXECUTIVO DO AUDITOR (Tempo de Resposta: {end_time - start_time:.2f}s) ===")
    print("="*70)
    print(result["final_response"])
    print("="*70)

if __name__ == "__main__":
    try:
        run_complete_demo()
    except Exception as e:
        print(f"\n[!] Erro crítico durante o teste: {e}")
        print("Dica Arquitetural: Verifique se o backend do Ollama/OpenVINO está em execução e se as bibliotecas LangChain/Pydantic estão na versão correta.")