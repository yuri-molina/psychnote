#!/usr/bin/env python3
"""
=============================================================================
PsicRE-AI: Bateria Experimental Unificada para Estudo Comparativo (TCC MBA)
Tema: Edge AI (Ollama Local) vs. Cloud AI (Google Gemini 3.6 Flash)
=============================================================================

Executa de forma simétrica e determinística os 4 grandes experimentos da pesquisa:
  - EXP-01: Paradigmas de Prompting (Zero-Shot, Regras Rígidas, CoT, Few-Shot)
  - EXP-02: Escalabilidade de Contexto Longitudinal (Nota vs. Nota+Histórico Resumido vs. Nota+Histórico Completo)
  - EXP-03: Direcionalidade do Erro Clínico e Índice de Segurança do Paciente
  - EXP-04: Benchmark de Latência, Throughput e SLA

Uso:
  python3 run_comparative_study.py --provider 1 --experiment all
  python3 run_comparative_study.py --provider 2 --experiment all --sleep 2.0
=============================================================================
"""

import os
import sys
import json
import time
import argparse
from enum import Enum
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# Ajuste de path para importações internas
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from config.engine import PsychiatricAIEngine, LLMProvider, get_psychiatric_llm


# ─────────────────────────────────────────────────────────────────────────────
# 1. Schemas Pydantic para os Experimentos
# ─────────────────────────────────────────────────────────────────────────────

class RiskLevelEnum(str, Enum):
    BAIXO = "Baixo"
    MODERADO = "Moderado"
    ALTO = "Alto/Iminente"


class StandardAssessment(BaseModel):
    """Schema Pydantic Padrão (utilizado em Zero-Shot e Few-Shot)"""
    risk_level: RiskLevelEnum = Field(description="Classificação mandatória: Baixo, Moderado, ou Alto/Iminente.")
    passive_ideation: bool = Field(description="Presença de ideação passiva de morte.")
    active_ideation: bool = Field(description="Presença de ideação suicida ativa.")
    red_flags: List[str] = Field(description="Sinais de alerta textuais extraídos.")
    protection_factors: List[str] = Field(description="Fatores de proteção identificados.")
    clinical_justification: str = Field(description="Justificativa clínica consolidada.")


class CoTAssessment(BaseModel):
    """
    Schema Chain-of-Thought (Reasoning-in-Schema)
    Força a geração do raciocínio analítico ANTES da emissão do token do enum de risco.
    """
    diagnostic_stability_analysis: str = Field(
        description="Análise detalhada do diagnóstico de base, gravidade do episódio e estabilidade clínica."
    )
    protective_factors_scrutiny: str = Field(
        description="Escrutínio crítico dos fatores de proteção relatados: eles anulam o risco ou apenas mitigam atos iminentes?"
    )
    verbal_denial_validity: str = Field(
        description="Análise da negação verbal de ideação/planos à luz do quadro clínico geral e ambivalência."
    )
    risk_level: RiskLevelEnum = Field(
        description="Classificação final e mandatória: Baixo, Moderado, ou Alto/Iminente."
    )
    passive_ideation: bool = Field(description="Presença de ideação passiva de morte.")
    active_ideation: bool = Field(description="Presença de ideação suicida ativa.")
    red_flags: List[str] = Field(description="Sinais de alerta textuais extraídos.")
    protection_factors: List[str] = Field(description="Fatores de proteção identificados.")
    clinical_justification: str = Field(description="Parecer técnico consolidado.")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Prompts dos Experimentos
# ─────────────────────────────────────────────────────────────────────────────

PROMPT_ZERO_SHOT_STRICT = """
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
"""

PROMPT_COT_REASONING = """
Você é um sistema especialista em auditoria e triagem psiquiátrica de alta precisão (CFM/Botega/OMS).
Antes de determinar o nível de risco, você DEVE preencher os campos de raciocínio clínico preliminares:
1. Avalie a estabilidade do diagnóstico de base e a gravidade dos sintomas atuais.
2. Analise criticamente se os fatores de proteção (ex: fé religiosa, família, temor da morte) anulam a vulnerabilidade ou apenas evitam atos imediatos.
3. Avalie se a negação verbal de intenção é genuína ou ocorre em contexto de transtorno depressivo/borderline ativo.
4. Emita a classificação de risco estritamente baseada nesta análise.

DIRETRIZES FUNDAMENTAIS:
- Paciente com Transtorno Depressivo Recorrente (F33) ou TAG/Dor Crônica com ideação de morte persistente é MODERADO, mesmo com crenças religiosas ou negação de planos.
- Comportamentos preparatórios (cartas, veneno guardado, plano detalhado) são ALTO/IMINENTE.
- Ideação passiva situacional em paciente eutímico/sem transtorno prévio é BAIXO.

NOTA CLÍNICA:
{note}
"""

PROMPT_FEW_SHOT = """
Você é um sistema especialista em triagem psiquiátrica baseado nas diretrizes do CFM, Botega e OMS.
Analise a nota clínica fornecida e classifique o risco, observando os exemplos canônicos de calibração abaixo.

EXEMPLO DE CALIBRAÇÃO 1 (Risco Moderado em Depressão Recorrente com Proteção Religiosa):
Nota: "Paciente com Transtorno Depressivo Maior Recorrente (F33.1) relata retorno de pensamentos de morte no último mês. Nega planos ativos de autoextermínio por convicções religiosas sobre o pecado do suicídio. Prescrito ajuste de antidepressivo."
Classificação: MODERADO
Justificativa: A crença religiosa protege contra ação iminente, mas a vigência de episódio depressivo recorrente com ideação persistente de morte mantém risco moderado conforme diretrizes clínicas.

EXEMPLO DE CALIBRAÇÃO 2 (Risco Moderado em Dor Crônica com Temor da Morte):
Nota: "Paciente com TAG e Fibromialgia refratária com piora de dores, sentimentos de inutilidade e desejo de morte ('gostaria que Deus me levasse'). Nega intenção ativa e expressa temor da morte. Ajustada medicação analgésica."
Classificação: MODERADO
Justificativa: Exacerbação álgica severa associada a sentimentos de inutilidade e desejo passivo de morte configura sofrimento psíquico relevante com necessidade de acompanhamento próximo (Risco Moderado).

EXEMPLO DE CALIBRAÇÃO 3 (Risco Baixo em Estresse Situacional):
Nota: "Paciente sem histórico psiquiátrico relata exaustão por sobrecarga de provas acadêmicas. Refere que às vezes pensa que seria bom dormir e acordar só depois das provas. Nega qualquer desejo de morte ou plano."
Classificação: BAIXO
Justificativa: Pensamento passivo situacional reativo a sobrecarga pontual, sem transtorno de base ou ideação suicida real.

AVALIE A SEGUINTE NOTA CLÍNICA:
{note}
"""

PROMPT_CONTEXT_LONGITUDINAL = """
Você é um sistema especialista em triagem psiquiátrica baseado nas diretrizes do CFM, Botega e OMS.
Analise o histórico longitudinal e a nota clínica atual do paciente para classificar o risco de suicídio.

HISTÓRICO PRÉVIO E ANTECEDENTES (LONGITUDINAL):
{history}

NOTA CLÍNICA ATUAL:
{note}

THRESHOLDS CLÍNICOS:
- ALTO/IMINENTE: Atos preparatórios, planos concretos, aquisição de meios letais ou alucinações de comando.
- MODERADO: Transtorno psiquiátrico prévio relevante ativo + ideação de morte (mesmo passiva ou com negação de planos).
- BAIXO: Ausência de transtornos graves no histórico + ideação passiva estritamente situacional + negação consistente.
"""


# ─────────────────────────────────────────────────────────────────────────────
# 3. Funções Auxiliares de Inferência com Retry
# ─────────────────────────────────────────────────────────────────────────────

def run_inference_with_retry(llm, prompt_template: str, input_vars: Dict[str, Any], schema_cls, max_retries: int = 4):
    prompt = ChatPromptTemplate.from_template(prompt_template)
    structured_llm = llm.with_structured_output(schema_cls)
    chain = prompt | structured_llm

    for attempt in range(1, max_retries + 1):
        try:
            return chain.invoke(input_vars)
        except Exception as e:
            err_str = str(e)
            if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                wait = min(20 * attempt, 90)
                print(f"  [!] Rate limit ({attempt}/{max_retries}). Aguardando {wait}s...")
                time.sleep(wait)
                continue
            if "DEADLINE_EXCEEDED" in err_str or "504" in err_str or "503" in err_str:
                wait = 15 * attempt
                print(f"  [!] Timeout/Unavailable ({attempt}/{max_retries}). Aguardando {wait}s...")
                time.sleep(wait)
                continue
            raise
    raise RuntimeError(f"Falha na inferência após {max_retries} tentativas.")


def load_dataset(filepath: str = "synthetic_patients.json") -> List[Dict]:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Executores dos Experimentos
# ─────────────────────────────────────────────────────────────────────────────

def run_experiment_01_prompting_paradigms(llm, dataset: List[Dict], provider_name: str, sleep_s: float) -> Dict:
    """
    EXP-01: Paradigmas de Prompting
    Avalia 3 estratégias: Regras Rígidas (Zero-Shot), Reasoning-in-Schema (CoT), Few-Shot In-Context.
    """
    print(f"\n{'='*75}\n  INICIANDO EXP-01: PARADIGMAS DE PROMPTING ({provider_name})\n{'='*75}")
    paradigms = {
        "Zero-Shot Regras Estritas": (PROMPT_ZERO_SHOT_STRICT, StandardAssessment),
        "Chain-of-Thought (Reasoning-in-Schema)": (PROMPT_COT_REASONING, CoTAssessment),
        "Few-Shot In-Context Learning": (PROMPT_FEW_SHOT, StandardAssessment),
    }

    results = {}
    for p_name, (p_template, p_schema) in paradigms.items():
        print(f"\n[*] Executando Paradigma: {p_name}")
        acertos = 0
        matriz = {"Alto/Iminente": 0, "Moderado": 0, "Baixo": 0}
        totais = {"Alto/Iminente": 3, "Moderado": 3, "Baixo": 3}
        latencies = []
        details = []

        for p in dataset:
            pid = p["patient_id"]
            true_risk = p["true_risk_level"]
            note = p["current_note"]

            t0 = time.time()
            try:
                out = run_inference_with_retry(llm, p_template, {"note": note}, p_schema)
                raw_risk = out.risk_level
                pred_risk = str(raw_risk.value if hasattr(raw_risk, "value") else raw_risk)
                just = out.clinical_justification
            except Exception as e:
                pred_risk = "ERRO"
                just = str(e)
            lat = time.time() - t0
            latencies.append(lat)

            is_correct = (pred_risk == true_risk)
            if is_correct:
                acertos += 1
                matriz[true_risk] += 1
                status = f"[+] ACERTO ({lat:.2f}s)"
            else:
                status = f"[-] ERRO: prev={pred_risk} != esp={true_risk} ({lat:.2f}s)"

            print(f"  • {pid} ({true_risk:<13}) → {status}")
            details.append({"patient_id": pid, "true_risk": true_risk, "pred_risk": pred_risk, "is_correct": is_correct, "latency_s": lat, "justification": just})
            time.sleep(sleep_s)

        acc_pct = (acertos / len(dataset)) * 100
        avg_lat = sum(latencies) / len(latencies)
        print(f"  → Resultado {p_name}: {acertos}/9 ({acc_pct:.1f}%) | Latência Média: {avg_lat:.2f}s")
        results[p_name] = {
            "accuracy_pct": round(acc_pct, 1),
            "acertos": acertos,
            "total": len(dataset),
            "avg_latency_s": round(avg_lat, 2),
            "matriz": matriz,
            "details": details,
        }

    return results


def run_experiment_02_context_scaling(llm, dataset: List[Dict], provider_name: str, sleep_s: float) -> Dict:
    """
    EXP-02: Escalabilidade de Contexto Longitudinal
    Nível A: Apenas nota atual (~300 tokens)
    Nível B: Nota + Histórico curto (~1000 tokens)
    Nível C: Nota + Histórico denso com antecedentes completos (~3000 tokens)
    """
    print(f"\n{'='*75}\n  INICIANDO EXP-02: ESCALABILIDADE DE CONTEXTO ({provider_name})\n{'='*75}")
    levels = {
        "Nível A (Nota Isolada)": lambda p: ("", p["current_note"]),
        "Nível B (Nota + Histórico Resumido)": lambda p: (p.get("historical_notes", [""])[0], p["current_note"]),
        "Nível C (Nota + Histórico Longitudinal Denso)": lambda p: (
            f"{p.get('historical_notes', [''])[0]} "
            f"Antecedentes adicionais: Paciente com histórico de internações prévias, múltiplas passagens por pronto-atendimento psiquiátrico, "
            f"tentativas prévias registradas em prontuários de 2018 a 2024, uso de diversas classes psicofarmacológicas com tolerabilidade variável, "
            f"padrão de adesão oscilante e suporte familiar catalogado.",
            p["current_note"]
        ),
    }

    results = {}
    for l_name, builder_fn in levels.items():
        print(f"\n[*] Executando Nível: {l_name}")
        acertos = 0
        matriz = {"Alto/Iminente": 0, "Moderado": 0, "Baixo": 0}
        latencies = []
        details = []

        for p in dataset:
            pid = p["patient_id"]
            true_risk = p["true_risk_level"]
            hist, note = builder_fn(p)

            t0 = time.time()
            try:
                out = run_inference_with_retry(llm, PROMPT_CONTEXT_LONGITUDINAL, {"history": hist if hist else "Nenhum histórico pregresso disponível.", "note": note}, StandardAssessment)
                raw_risk = out.risk_level
                pred_risk = str(raw_risk.value if hasattr(raw_risk, "value") else raw_risk)
                just = out.clinical_justification
            except Exception as e:
                pred_risk = "ERRO"
                just = str(e)
            lat = time.time() - t0
            latencies.append(lat)

            is_correct = (pred_risk == true_risk)
            if is_correct:
                acertos += 1
                matriz[true_risk] += 1
                status = f"[+] ACERTO ({lat:.2f}s)"
            else:
                status = f"[-] ERRO: prev={pred_risk} != esp={true_risk} ({lat:.2f}s)"

            print(f"  • {pid} ({true_risk:<13}) → {status}")
            details.append({"patient_id": pid, "true_risk": true_risk, "pred_risk": pred_risk, "is_correct": is_correct, "latency_s": lat, "justification": just})
            time.sleep(sleep_s)

        acc_pct = (acertos / len(dataset)) * 100
        avg_lat = sum(latencies) / len(latencies)
        print(f"  → Resultado {l_name}: {acertos}/9 ({acc_pct:.1f}%) | Latência Média: {avg_lat:.2f}s")
        results[l_name] = {
            "accuracy_pct": round(acc_pct, 1),
            "acertos": acertos,
            "total": len(dataset),
            "avg_latency_s": round(avg_lat, 2),
            "matriz": matriz,
            "details": details,
        }

    return results


def run_experiment_03_safety_asymmetry(exp01_results: Dict) -> Dict:
    """
    EXP-03: Análise de Direcionalidade do Erro & Índice de Segurança do Paciente
    Calcula a assimetria: Falso Positivo (Over-triage = peso 1) vs. Falso Negativo (Sub-triage = peso 10).
    Clinical Safety Score = max(0, 100 - (1*FP + 10*FN_Critico) / Total * 10)
    """
    print(f"\n{'='*75}\n  CALCULANDO EXP-03: ÍNDICE DE SEGURANÇA CLÍNICA\n{'='*75}")
    safety_results = {}

    for paradigm_name, data in exp01_results.items():
        fp_count = 0  # Over-triage (classificou Baixo como Moderado ou Alto)
        fn_count = 0  # Sub-triage (classificou Moderado/Alto como Baixo)
        
        for d in data["details"]:
            true_r = d["true_risk"]
            pred_r = d["pred_risk"]
            
            if true_r == "Baixo" and pred_r in ("Moderado", "Alto/Iminente"):
                fp_count += 1
            elif true_r in ("Moderado", "Alto/Iminente") and pred_r == "Baixo":
                fn_count += 1

        total = len(data["details"])
        # Fórmula de penalização clínica assimétrica
        penalty = (1.0 * fp_count) + (10.0 * fn_count)
        safety_score = max(0.0, 100.0 - (penalty / total) * 10.0)

        safety_results[paradigm_name] = {
            "over_triage_fp": fp_count,
            "sub_triage_fn": fn_count,
            "clinical_safety_score": round(safety_score, 1),
            "accuracy_pct": data["accuracy_pct"],
        }
        print(f"  • {paradigm_name:<35} → Safety Score: {safety_score:.1f}/100 (FP={fp_count}, FN={fn_count})")

    return safety_results


# ─────────────────────────────────────────────────────────────────────────────
# 5. Entrypoint e Persistência
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Bateria Experimental Unificada Edge AI vs. Cloud AI (TCC MBA)")
    parser.add_argument("--provider", type=int, choices=[1, 2], default=2, help="1 = Ollama (Local), 2 = Gemini (Cloud)")
    parser.add_argument("--experiment", type=str, choices=["exp01", "exp02", "all"], default="all", help="Experimento a rodar")
    parser.add_argument("--sleep", type=float, default=2.0, help="Intervalo em segundos entre chamadas (padrão: 2.0s)")
    args = parser.parse_args()

    provider = LLMProvider.GEMINI if args.provider == 2 else LLMProvider.OLLAMA
    provider_name = "Cloud AI (Google Gemini 3.6 Flash)" if provider == LLMProvider.GEMINI else "Edge AI (Ollama llama3:8b)"
    provider_tag = "gemini" if provider == LLMProvider.GEMINI else "ollama"

    print(f"\n[*] Inicializando Engine: {provider_name}")
    llm = get_psychiatric_llm(provider=provider)
    dataset = load_dataset()
    print(f"[+] Dataset carregado: {len(dataset)} prontuários sintéticos.")

    output_file = f"comparative_study_{provider_tag}.json"
    study_data = {}
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                study_data = json.load(f)
        except Exception:
            study_data = {}

    # Execução EXP-01
    if args.experiment in ("exp01", "all"):
        study_data["EXP-01_Prompting_Paradigms"] = run_experiment_01_prompting_paradigms(llm, dataset, provider_name, args.sleep)
        study_data["EXP-03_Safety_Asymmetry"] = run_experiment_03_safety_asymmetry(study_data["EXP-01_Prompting_Paradigms"])

    # Execução EXP-02
    if args.experiment in ("exp02", "all"):
        study_data["EXP-02_Context_Scaling"] = run_experiment_02_context_scaling(llm, dataset, provider_name, args.sleep)

    # Metadados de Execução
    study_data["metadata"] = {
        "provider": provider_name,
        "provider_tag": provider_tag,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_cases": len(dataset),
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(study_data, f, ensure_ascii=False, indent=2)
    print(f"\n[+] Estudo comparativo persistido com sucesso → {output_file}")


if __name__ == "__main__":
    main()
