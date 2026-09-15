from enum import Enum
from typing import List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from database.patient_manager import PatientDataManager
from config.engine import get_psychiatric_llm, LLMProvider

# Esquema de Dados Clínicos baseados nas diretrizes (Botega, CFM, Manole)
class RiskLevelEnum(str, Enum):
    BAIXO = "Baixo"
    MODERADO = "Moderado"
    ALTO_IMINENTE = "Alto/Iminente"

class SuicideRiskAssessment(BaseModel):
    """Esquema rígido para garantir a integridade da triagem automatizada de risco de suicídio."""
    risk_level: RiskLevelEnum = Field(
        description="Classificação do risco: Baixo (ideação passageira, sem plano), Moderado (ideação frequente, histórico, sem plano imediato) ou Alto/Iminente (plano estruturado, acesso a meios ou urgência)."
    )
    passive_ideation: bool = Field(
        description="True se detectar marcadores linguísticos de cansaço da vida, desejo de dormir e não acordar ou frases de desamparo sem intenção ativa."
    )
    active_ideation: bool = Field(
        description="True se houver evidência de planejamento tático, bilhetes de despedida, organização de pendências ou busca/acesso a meios letais."
    )
    red_flags: List[str] = Field(
        description="Lista de frases, termos ou comportamentos de risco agudo extraídos textualmente da nota."
    )
    protection_factors: List[str] = Field(
        description="Fatores de proteção explícitos na nota que mitigam o risco (ex: boa rede de apoio, aliança terapêutica, religiosidade)."
    )
    clinical_justification: str = Field(
        description="Parecer técnico justificando a decisão do algoritmo com base nos limiares (thresholds) clínicos atingidos."
    )

class ClinicalMonitor:
    """
    Módulo analítico especializado na triagem estruturada de risco de autoextermínio.
    """

    def __init__(self, llm_provider: LLMProvider = LLMProvider.OLLAMA):
        self.llm = get_psychiatric_llm(provider=llm_provider)
        self.patient_manager = PatientDataManager()

    def detect_risk(self, note_text: str) -> SuicideRiskAssessment:
        """
        Executa a classificação zero-shot forçando uma saída estruturada via Pydantic.
        """
        print("[*] Executando análise estruturada de risco de suicídio...")
        
        prompt = ChatPromptTemplate.from_template("""
        Você é um sistema especialista em triagem psiquiátrica baseado nas diretrizes do CFM, Botega e OMS.
        Analise a nota clínica fornecida e classifique EXCLUSIVAMENTE o risco do paciente.

        ═══════════════════════════════════════════════════
        REGRA CRÍTICA DE SEPARAÇÃO DE CONTEXTO (MANDATÓRIA)
        ═══════════════════════════════════════════════════
        A "conduta médica" (ex: aumento de dose, internação agendada, retorno ambulatorial) descreve a AÇÃO DO MÉDICO,
        NÃO é um fator protetor do paciente. Ignore completamente a conduta médica ao classificar o risco.
        Avalie APENAS o estado clínico, comportamental e ideativo do paciente descrito na nota.

        ═════════════════════════════════════════════════════
        THRESHOLDS CLÍNICOS EXATOS (em ordem de precedência)
        ═════════════════════════════════════════════════════

        RISCO ALTO/IMINENTE — classifique aqui se QUALQUER um dos seguintes estiver presente:
          • Plano de suicídio concreto (local, método, data, horário definidos).
          • Atos preparatórios: cartas de despedida, testamento, guarda/aquisição de meios letais (cordas, veneno, armas, medicamentos acumulados).
          • Alucinações auditivas IMPERATIVAS ordenando suicídio com plano específico associado.
          • Paciente afirma intenção de agir dentro de horas ou dias ("nesta noite", "no próximo fim de semana").
          ⚠ ATENÇÃO: A presença de QUALQUER item acima configura ALTO/IMINENTE independente de qualquer negação verbal ou fator protetor.
          ⚠ ATENÇÃO: "Ideação ativa estruturada" com aquisição de meios letais e data definida NÃO é Moderado — é ALTO/IMINENTE.

        RISCO MODERADO — classifique aqui se TODOS os critérios abaixo estiverem presentes:
          • Ideação suicida ativa, recorrente ou persistente (pensamentos frequentes sobre morte, não apenas ocasionais).
          • SEM plano imediato estruturado ou aquisição de meios letais.
          • Pelo menos UM dos seguintes fatores de risco estáticos ou dinâmicos presentes:
            - Diagnóstico psiquiátrico instável ativo (Borderline, Bipolar, Esquizofrenia, Depressão Grave Recorrente).
            - Histórico prévio de automutilação ou tentativas anteriores de autoextermínio.
            - Luto recente, perda de emprego, ruptura conjugal, ou isolamento social agudo.
            - Ideação passiva crônica com piora progressiva no último mês.
          ⚠ ATENÇÃO: Paciente com diagnóstico instável ativo que nega planejamento NÃO é automaticamente Baixo Risco.
            A negação de planos em contexto de transtorno grave e ideação recorrente classifica como MODERADO.

        RISCO BAIXO — classifique aqui SOMENTE se TODOS os critérios abaixo estiverem presentes:
          • Ideação passiva pontual e situacional (ex: "queria descansar", "queria sumir das provas").
          • Nega de forma clara e consistente qualquer planejamento, intenção ou aquisição de meios.
          • Ausência de diagnóstico psiquiátrico grave ativo ou histórico de tentativas prévias.
          • Presença de fatores de proteção robustos (planos de futuro, rede de apoio sólida, motivação para tratamento).

        ═══════════════════════════════════════════════════════
        HIERARQUIA ANTI-SUBTRIAGE (aplicar em caso de conflito)
        ═══════════════════════════════════════════════════════
        1. Comportamento preparatório concreto (cartas, meios letais adquiridos) → ALTO/IMINENTE obrigatório.
        2. Alucinação imperativa com plano detalhado → ALTO/IMINENTE obrigatório.
        3. Diagnóstico instável grave + ideação recorrente + sem plano → MODERADO.
        4. Ideação passiva pontual + negação consistente + sem fatores de risco → BAIXO.

        NOTA CLÍNICA:
        {note}
        """)
        
        # Vincula o validador Pydantic ao LLM local (Ollama/OpenVINO)
        # Seed fixo e num_predict configurados no engine para máximo determinismo
        structured_llm = self.llm.with_structured_output(SuicideRiskAssessment)
        chain = prompt | structured_llm
        
        # Retorna uma instância direta da classe SuicideRiskAssessment
        return chain.invoke({"note": note_text})

    def generate_summary(self, patient_id: str) -> str:
        """
        Recupera as notas históricas e gera um resumo consolidado da evolução do paciente.
        """
        print(f"[*] Gerando resumo consolidado da evolução para o paciente {patient_id}...")
        retriever = self.patient_manager.get_patient_retriever(patient_id, search_kwargs={"k": 10})
        docs = retriever.invoke("evolução clínica queixas sintomas estado mental")
        
        if not docs:
            return "Nenhum histórico disponível para resumir."
            
        combined_text = "\n\n".join([d.page_content for d in docs])
        
        prompt = ChatPromptTemplate.from_template("""
        Você é um Psiquiatra sênior. Resuma de forma narrativa e consolidada a evolução clínica 
        longitudinal do paciente com base nas seguintes notas históricas:
        
        {notes}
        
        Resumo da Evolução:
        """)
        
        chain = prompt | self.llm
        response = chain.invoke({"notes": combined_text})
        return response.content

if __name__ == "__main__":
    monitor = ClinicalMonitor()
    
    # Simulação de um cenário agudo (Risco Alto/Iminente devido a comportamento preparatório)
    test_note = (
        "Paciente em consulta relata sofrimento existencial intolerável. "
        "Admite ter organizado todos os seus documentos nesta semana e deixado uma carta na gaveta "
        "para poupar a família. Refere que a esposa tem sido muito companheira e presente, "
        "mas que não consegue mais ser um fardo."
    )
    
    assessment = monitor.detect_risk(test_note)
    
    print("\n" + "="*40)
    print("RESULTADO DA TRIAGEM ESTRUTURADA")
    print("="*40)
    print(f"Nível de Risco: {assessment.risk_level.value}")
    print(f"Ideação Passiva: {assessment.passive_ideation}")
    print(f"Ideação Ativa: {assessment.active_ideation}")
    print(f"Red Flags: {assessment.red_flags}")
    print(f"Fatores de Proteção: {assessment.protection_factors}")
    print(f"Justificativa Clínica: {assessment.clinical_justification}")
    print("="*40)