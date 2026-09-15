from typing import List, Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from config.engine import get_psychiatric_llm, LLMProvider
from database.patient_manager import PatientDataManager
from analytics.clinical_monitor import ClinicalMonitor

# Definição do Estado do Grafo (Adaptado para Gestão de Risco de Suicídio)
class AgentState(TypedDict):
    patient_id: str
    current_note: str  # Nota clínica atual a ser avaliada
    risk_assessment: Dict[str, Any]  # Output estruturado do Pydantic
    patient_context: List[str]  # Histórico longitudinal do paciente
    audit_alerts: List[str]  # Alertas da árvore de decisão de conduta
    final_response: str  # Parecer executivo consolidado

class PsychiatricOrchestrator:
    """
    Orquestrador LangGraph para Triagem Estruturada e Auditoria Clínica de Risco de Suicídio.
    Topologia Sequencial:
      1. analyze_risk: Classificação estruturada zero-shot (Pydantic) da nota atual.
      2. retrieve_history: Recuperação do histórico longitudinal do paciente via SQLite.
      3. audit_conduct: Auditoria determinística de conduta vs. diretrizes (CFM/Botega/OMS).
      4. generate_report: Consolidação do parecer executivo de auditoria.
    """
    
    def __init__(self, llm_provider: LLMProvider = LLMProvider.OLLAMA):
        self.llm = get_psychiatric_llm(provider=llm_provider)
        self.patient_manager = PatientDataManager()
        self.clinical_monitor = ClinicalMonitor(llm_provider=llm_provider)

    def analyze_risk(self, state: AgentState) -> Dict[str, Any]:
        """Nó 1: Executa a classificação estruturada (Pydantic) sobre a nota atual."""
        # Se a triagem já foi executada e passada no estado inicial, reutiliza para economizar inferência (Speedup)
        if state.get('risk_assessment') and state['risk_assessment'].get('risk_level'):
            print(f"[+] Nó 1 (LangGraph): Reutilizando triagem estruturada existente no estado...")
            return {}
            
        print(f"[*] Nó 1 (LangGraph): Classificando o risco estruturado da nota atual...")
        assessment = self.clinical_monitor.detect_risk(state['current_note'])
        
        # Converte o objeto Pydantic (v2) para dicionário para serialização no LangGraph
        return {"risk_assessment": assessment.model_dump()}

    def retrieve_history(self, state: AgentState) -> Dict[str, Any]:
        """Nó 2: Recupera o histórico do paciente para validar fatores estáticos."""
        print(f"[*] Nó 2 (LangGraph): Recuperando contexto longitudinal do paciente {state['patient_id']}...")
        retriever = self.patient_manager.get_patient_retriever(state['patient_id'])
        
        # Busca por preditores históricos no banco vetorial
        docs = retriever.invoke("histórico de tentativa de suicídio ideação depressão fatores estáticos")
        return {"patient_context": [doc.page_content for doc in docs]}

    def audit_conduct(self, state: AgentState) -> Dict[str, Any]:
        """
        Nó 3 (Árvore de Decisão): Compara o Nível de Risco com a conduta narrada na nota.
        Injeta as regras de negócio clínicas extraídas das diretrizes de prevenção.
        """
        print("[*] Nó 3 (LangGraph): Auditando Conduta Médica vs Diretrizes Clínicas...")
        alerts = []
        risk_level = state['risk_assessment'].get('risk_level', 'Baixo')
        note_lower = state['current_note'].lower()
        
        # Lógica de Auditoria Baseada em Regras (NotebookLM)
        if risk_level == "Alto/Iminente":
            if "alta" in note_lower or "liberado" in note_lower or "retorno ambulatorial" in note_lower:
                alerts.append(
                    "[FALHA CRÍTICA]: O sistema detectou Risco Alto/Iminente, mas a nota sugere alta ou liberação. "
                    "O protocolo mandatório exige vigilância constante, internação imediata e quebra de sigilo com a família."
                )
            if not any(word in note_lower for word in ["internação", "vigilância", "samu", "ambulância", "hospital"]):
                alerts.append(
                    "[ALERTA DE SEGURANÇA]: Não há evidência documentada de encaminhamento para internação psiquiátrica "
                    "ou remoção de pertences de risco, ações prioritárias para Risco Alto."
                )
                
        elif risk_level == "Moderado":
            if not any(word in note_lower for word in ["família", "contrato", "contato"]):
                alerts.append(
                    "[RECOMENDAÇÃO]: Para Risco Moderado, as diretrizes exigem acionar a família para restringir acesso "
                    "a meios letais em casa e a negociação de um contrato terapêutico. Estas ações não estão claras na nota."
                )
                
        return {"audit_alerts": alerts}

    def generate_report(self, state: AgentState) -> Dict[str, Any]:
        """Nó 4: Gera a síntese final atuando como Auditor de Qualidade."""
        print("[*] Nó 4 (LangGraph): Gerando Parecer Executivo de Auditoria...")
        
        risk_data = state['risk_assessment']
        risk_level = risk_data.get('risk_level', 'Desconhecido')
        red_flags = ", ".join(risk_data.get('red_flags', [])) if risk_data.get('red_flags') else "Nenhuma"
        protection = ", ".join(risk_data.get('protection_factors', [])) if risk_data.get('protection_factors') else "Nenhum mapeado"
        justification = risk_data.get('clinical_justification', '')
        
        alerts_list = state['audit_alerts']
        if alerts_list:
            alerts_text = "\n".join([f"  [!] {alert}" for alert in alerts_list])
        else:
            alerts_text = "  -> Nenhuma divergência grave de protocolo identificada na documentação."

        report = f"""=== PARECER EXECUTIVO DE AUDITORIA CLÍNICA ===
NOTA CLÍNICA AVALIADA:
"{state['current_note']}"

AVALIAÇÃO ESTRUTURADA DA IA:
- Risco Identificado: {risk_level}
- Red Flags Ativas: {red_flags}
- Fatores de Proteção: {protection}
- Parecer Base: {justification}

ALERTAS DE PROTOCOLO (AUDITORIA RIGOROSA):
{alerts_text}
"""
        return {"final_response": report}

    def build_graph(self):
        """Constrói a topologia sequencial determinística do LangGraph."""
        workflow = StateGraph(AgentState)
        
        # Adiciona Nós
        workflow.add_node("analyze_risk", self.analyze_risk)
        workflow.add_node("retrieve_history", self.retrieve_history)
        workflow.add_node("audit_conduct", self.audit_conduct)
        workflow.add_node("generate_report", self.generate_report)
        
        # Define Arestas Sequenciais
        workflow.set_entry_point("analyze_risk")
        workflow.add_edge("analyze_risk", "retrieve_history")
        workflow.add_edge("retrieve_history", "audit_conduct")
        workflow.add_edge("audit_conduct", "generate_report")
        workflow.add_edge("generate_report", END)
        
        return workflow.compile()

if __name__ == "__main__":
    orchestrator = PsychiatricOrchestrator()
    app = orchestrator.build_graph()
    
    # Exemplo de payload para execução do grafo
    inputs = {
        "patient_id": "PA-TESTE",
        "current_note": "Paciente extremamente deprimido, trouxe corda na mochila e diz que amanhã não estará mais aqui. Médico agendou retorno ambulatorial para daqui a 15 dias.",
        "risk_assessment": {},
        "patient_context": [],
        "audit_alerts": [],
        "final_response": ""
    }
    
    print("[+] Grafo de orquestração compilado com sucesso. Pronto para rodar o pipeline completo.")
