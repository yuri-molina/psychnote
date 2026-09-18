"""
run_prompt_version_eval.py
==========================
Avalia as versões iterativas de prompt (v1, v2, v3, v4, v2-final) em todos os
prontuários sintéticos usando o provider LLM especificado (Ollama ou Gemini).

Estratégia para free tier Gemini (20 req/dia):
  - Execute UMA versão por dia: --provider 2 --version v1
  - Os resultados são acumulados em prompt_version_results_gemini.json entre sessões.
  - O script para graciosamente ao detectar quota diária esgotada.

Uso:
    python3 run_prompt_version_eval.py --provider 2 --version v1   # Dia 1
    python3 run_prompt_version_eval.py --provider 2 --version v2   # Dia 2
    python3 run_prompt_version_eval.py --provider 2 --version v3   # Dia 3
    python3 run_prompt_version_eval.py --provider 2 --version v4   # Dia 4
    python3 run_prompt_version_eval.py --provider 2 --version v2-final  # Dia 5
    python3 run_prompt_version_eval.py --provider 1 --version all  # Ollama (sem limite)
"""

import argparse
import json
import os
import time
from typing import Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from enum import Enum

from config.engine import LLMProvider, get_psychiatric_llm
from database.patient_manager import PatientDataManager


# ─────────────────────────────────────────────────────────────────────────────
# Esquema Pydantic (idêntico ao de produção)
# ─────────────────────────────────────────────────────────────────────────────

class RiskLevelEnum(str, Enum):
    BAIXO = "Baixo"
    MODERADO = "Moderado"
    ALTO_IMINENTE = "Alto/Iminente"


class SuicideRiskAssessment(BaseModel):
    """Esquema rígido para garantir a integridade da triagem automatizada."""
    risk_level: RiskLevelEnum = Field(
        description="Classificação do risco: Baixo, Moderado ou Alto/Iminente."
    )
    passive_ideation: bool = Field(
        description="True se detectar marcadores linguísticos de cansaço da vida, desejo de dormir e não acordar."
    )
    active_ideation: bool = Field(
        description="True se houver evidência de planejamento tático ou busca/acesso a meios letais."
    )
    red_flags: List[str] = Field(
        description="Lista de frases ou comportamentos de risco extraídos textualmente da nota."
    )
    protection_factors: List[str] = Field(
        description="Fatores de proteção explícitos na nota que mitigam o risco."
    )
    clinical_justification: str = Field(
        description="Parecer técnico justificando a classificação com base nos critérios atingidos."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Definição das versões de prompt (reconstruídas a partir do TCC_BENCHMARK_RESULTS.md)
# ─────────────────────────────────────────────────────────────────────────────

PROMPT_VERSIONS: Dict[str, str] = {

    # ── v1: Linha de base — regra mandatória "nega = Baixo" (causa over-reliance em negação verbal)
    "v1": """
Você é um sistema especialista em triagem psiquiátrica baseado nas diretrizes do CFM, Botega e OMS.
Analise a nota clínica fornecida e classifique EXCLUSIVAMENTE o risco do paciente.

CRITÉRIOS DE CLASSIFICAÇÃO:

- RISCO BAIXO: Ideação passiva (ex: "queria sumir", "queria dormir"), MAS nega intenções,
  planos ou tentativas. Não há histórico grave recente.

- RISCO MODERADO: Ideação persistente, foco na morte, histórico de tentativas,
  SEM plano imediato estruturado.

- RISCO ALTO/IMINENTE: Plano definido, busca por métodos letais, atos preparatórios
  (cartas de despedida, aquisição de meios).

REGRA MANDATÓRIA: Se a nota afirmar que o paciente "nega" (nega intenção, nega
planejamento), e não houver comportamento preparatório contraditório, o risco DEVE
ser classificado como BAIXO.

NOTA CLÍNICA:
{note}
""",

    # ── v2: Corrige viés "nega = Baixo" + separação de conduta médica + precedência Alto/Iminente
    "v2": """
Você é um sistema especialista em triagem psiquiátrica baseado nas diretrizes do CFM, Botega e OMS.
Analise a nota clínica fornecida e classifique EXCLUSIVAMENTE o risco do paciente.

═══════════════════════════════════════════════════
REGRA CRÍTICA DE SEPARAÇÃO DE CONTEXTO (MANDATÓRIA)
═══════════════════════════════════════════════════
A "conduta médica" (ex: aumento de dose, internação agendada, retorno ambulatorial) descreve a AÇÃO DO MÉDICO,
NÃO é um fator protetor do paciente. Ignore a conduta médica ao classificar o risco.
Avalie APENAS o estado clínico e ideativo do paciente.

═════════════════════════════════════════════════════
THRESHOLDS CLÍNICOS EXATOS (em ordem de precedência)
═════════════════════════════════════════════════════

RISCO ALTO/IMINENTE — classifique aqui se QUALQUER um dos seguintes estiver presente:
  • Plano concreto (local, método, data, horário definidos).
  • Atos preparatórios: cartas de despedida, aquisição de meios letais.
  • Alucinações auditivas IMPERATIVAS ordenando suicídio com plano específico.
  • Intenção de agir dentro de horas ou dias ("nesta noite", "próximo fim de semana").
⚠ A presença de QUALQUER item acima configura ALTO/IMINENTE mesmo que o paciente
  verbalize algum fator protetor.

RISCO MODERADO — classifique aqui se TODOS abaixo estiverem presentes:
  • Ideação ativa, recorrente ou persistente.
  • SEM plano estruturado ou aquisição de meios letais.
  • Pelo menos UM: diagnóstico instável ativo (Borderline, Bipolar, Esquizofrenia,
    Depressão Grave Recorrente), histórico de tentativas, luto recente ou perda de
    emprego, ideação passiva crônica com piora no último mês.
⚠ Diagnóstico instável + negação de planos = MODERADO, não BAIXO.

RISCO BAIXO — classifique aqui SOMENTE se TODOS abaixo estiverem presentes:
  • Ideação passiva pontual e situacional.
  • Nega de forma clara e consistente qualquer planejamento ou aquisição de meios.
  • Ausência de diagnóstico psiquiátrico grave ativo ou histórico de tentativas prévias.
  • Presença de fatores de proteção robustos.

NOTA CLÍNICA:
{note}
""",

    # ── v3: Enumera CIDs que qualificam/não qualificam como "instável" (causa lost-in-the-middle)
    "v3": """
Você é um sistema especialista em triagem psiquiátrica baseado nas diretrizes do CFM, Botega e OMS.
Analise a nota clínica fornecida e classifique EXCLUSIVAMENTE o risco do paciente.

═══════════════════════════════════════════════════
REGRA CRÍTICA DE SEPARAÇÃO DE CONTEXTO (MANDATÓRIA)
═══════════════════════════════════════════════════
A "conduta médica" (ex: aumento de dose, internação agendada, retorno ambulatorial) descreve a AÇÃO DO MÉDICO,
NÃO é um fator protetor do paciente. Ignore a conduta médica ao classificar o risco.
Avalie APENAS o estado clínico e ideativo do paciente.

═════════════════════════════════════════════════════
THRESHOLDS CLÍNICOS EXATOS (em ordem de precedência)
═════════════════════════════════════════════════════

RISCO ALTO/IMINENTE — classifique aqui se QUALQUER um dos seguintes estiver presente:
  • Plano concreto (local, método, data, horário definidos).
  • Atos preparatórios: cartas de despedida, aquisição de meios letais.
  • Alucinações auditivas IMPERATIVAS ordenando suicídio com plano específico.
  • Intenção de agir dentro de horas ou dias ("nesta noite", "próximo fim de semana").
⚠ A presença de QUALQUER item acima configura ALTO/IMINENTE mesmo que o paciente
  verbalize algum fator protetor.

RISCO MODERADO — classifique aqui se TODOS abaixo estiverem presentes:
  • Ideação ativa, recorrente ou persistente.
  • SEM plano estruturado ou aquisição de meios letais.
  • Pelo menos UM diagnóstico psiquiátrico GRAVE e INSTÁVEL ativo.
    Qualificam APENAS: Borderline (F60.3), Bipolar (F31), Esquizofrenia (F20),
    Depressão Grave Recorrente (F33.2) em episódio atual agudo.
    NÃO qualificam: Distimia estável (F34.1), TAG (F41.1), Depressão Leve em
    remissão, Burnout (Z73), ansiedade situacional.
  • Ou histórico de tentativas, luto recente, isolamento agudo.
⚠ Diagnóstico instável + negação de planos = MODERADO, não BAIXO.

RISCO BAIXO — classifique aqui SOMENTE se TODOS abaixo estiverem presentes:
  • Ideação passiva pontual e situacional.
  • Nega de forma clara e consistente qualquer planejamento ou aquisição de meios.
  • Ausência de diagnóstico psiquiátrico grave ativo ou histórico de tentativas prévias.
  • Presença de fatores de proteção robustos.

NOTA CLÍNICA:
{note}
""",

    # ── v4: Remove enumeração CID do v3, adiciona bloco FALSO POSITIVO ESTRUTURAL no final
    "v4": """
Você é um sistema especialista em triagem psiquiátrica baseado nas diretrizes do CFM, Botega e OMS.
Analise a nota clínica fornecida e classifique EXCLUSIVAMENTE o risco do paciente.

═══════════════════════════════════════════════════
REGRA CRÍTICA DE SEPARAÇÃO DE CONTEXTO (MANDATÓRIA)
═══════════════════════════════════════════════════
A "conduta médica" (ex: aumento de dose, internação agendada, retorno ambulatorial) descreve a AÇÃO DO MÉDICO,
NÃO é um fator protetor do paciente. Ignore a conduta médica ao classificar o risco.
Avalie APENAS o estado clínico e ideativo do paciente.

═════════════════════════════════════════════════════
THRESHOLDS CLÍNICOS EXATOS (em ordem de precedência)
═════════════════════════════════════════════════════

RISCO ALTO/IMINENTE — classifique aqui se QUALQUER um dos seguintes estiver presente:
  • Plano concreto (local, método, data, horário definidos).
  • Atos preparatórios: cartas de despedida, aquisição de meios letais.
  • Alucinações auditivas IMPERATIVAS ordenando suicídio com plano específico.
  • Intenção de agir dentro de horas ou dias ("nesta noite", "próximo fim de semana").
⚠ A presença de QUALQUER item acima configura ALTO/IMINENTE mesmo que o paciente
  verbalize algum fator protetor.

RISCO MODERADO — classifique aqui se TODOS abaixo estiverem presentes:
  • Ideação ativa, recorrente ou persistente.
  • SEM plano estruturado ou aquisição de meios letais.
  • Pelo menos UM: diagnóstico instável ativo (Borderline, Bipolar, Esquizofrenia,
    Depressão Grave Recorrente), histórico de tentativas, luto recente ou perda de
    emprego, ideação passiva crônica com piora no último mês.
⚠ Diagnóstico instável + negação de planos = MODERADO, não BAIXO.

RISCO BAIXO — classifique aqui SOMENTE se TODOS abaixo estiverem presentes:
  • Ideação passiva pontual e situacional.
  • Nega de forma clara e consistente qualquer planejamento ou aquisição de meios.
  • Ausência de diagnóstico psiquiátrico grave ativo ou histórico de tentativas prévias.
  • Presença de fatores de proteção robustos.

══════════════════════════════════════════════════════
FALSO POSITIVO ESTRUTURAL — ATENÇÃO ESPECIAL AO CLASSIFICAR
══════════════════════════════════════════════════════
As seguintes condições NÃO configuram diagnóstico psiquiátrico grave instável:
  - Distimia estável de longa data (F34.1) em acompanhamento regular.
  - Síndrome de Burnout (Z73) ou esgotamento profissional.
  - Fibromialgia, dor crônica ou fadiga física sem componente suicida estruturado.

Frases como "cansa viver sentindo dor", "queria sumir por um tempo" ditas por
paciente SEM diagnóstico grave, SEM histórico de tentativas e COM negação
consistente → RISCO BAIXO.

NOTA CLÍNICA:
{note}
""",

    # ── v2-final: Versão de produção — v2 + 2 linhas de override literal para PAC-010
    "v2-final": """
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
""",
}


# ─────────────────────────────────────────────────────────────────────────────
# Motor de inferência por versão de prompt (sem alterar produção)
# ─────────────────────────────────────────────────────────────────────────────

# Sentinel de quota diária esgotada
class DailyQuotaExhausted(Exception):
    pass


def run_single_note_with_retry(
    llm,
    prompt_template: str,
    note_text: str,
    max_retries: int = 4,
) -> SuicideRiskAssessment:
    """
    Executa a triagem com retry/backoff em 429 por rate limit de minuto.
    Lança DailyQuotaExhausted quando a quota diária (GenerateRequestsPerDay) é atingida.
    """
    prompt = ChatPromptTemplate.from_template(prompt_template)
    structured_llm = llm.with_structured_output(SuicideRiskAssessment)
    chain = prompt | structured_llm

    for attempt in range(1, max_retries + 1):
        try:
            return chain.invoke({"note": note_text})
        except Exception as e:
            err_str = str(e)
            # Quota diária — não há retry que resolva, encerrar sessão
            if "GenerateRequestsPerDayPerProjectPerModel" in err_str or (
                "RESOURCE_EXHAUSTED" in err_str and "PerDay" in err_str
            ):
                raise DailyQuotaExhausted(
                    f"Quota diária do Gemini esgotada. Execute novamente amanhã.\n"
                    f"Detalhe: {err_str[:300]}"
                )
            # Rate limit por minuto — aguarda e tenta novamente
            if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                wait = min(30 * attempt, 120)
                print(f"  [!] Rate limit (tentativa {attempt}/{max_retries}). Aguardando {wait}s...")
                time.sleep(wait)
                continue
            # Timeout transitório
            if "DEADLINE_EXCEEDED" in err_str or "504" in err_str:
                wait = 15 * attempt
                print(f"  [!] Timeout (tentativa {attempt}/{max_retries}). Aguardando {wait}s...")
                time.sleep(wait)
                continue
            # Erro permanente — propaga
            raise

    raise RuntimeError(f"Falha após {max_retries} tentativas.")


def evaluate_version(
    version_name: str,
    prompt_template: str,
    dataset: List[Dict],
    llm,
    provider_name: str,
    sleep_between: float = 3.0,
) -> Dict:
    """
    Avalia todos os prontuários com uma versão de prompt.
    Para graciosamente se a quota diária for atingida, salvando parciais.
    """
    print(f"\n{'═'*65}")
    print(f"  VERSÃO: {version_name.upper()} | PROVEDOR: {provider_name}")
    print(f"{'═'*65}")

    total = len(dataset)
    acertos = 0
    quota_exhausted = False
    matriz = {
        "Alto/Iminente": {"acertos": 0, "erros": 0, "casos_errados": []},
        "Moderado":      {"acertos": 0, "erros": 0, "casos_errados": []},
        "Baixo":         {"acertos": 0, "erros": 0, "casos_errados": []},
        "Falso_Positivo":{"acertos": 0, "erros": 0, "casos_errados": []},
    }
    details = []
    start = time.time()

    for idx, patient in enumerate(dataset, 1):
        patient_id = patient.get("patient_id", f"PAC-{idx}")
        true_risk = patient.get("true_risk_level", "")
        curr_note = patient.get("current_note", "")

        print(f"\n[*] {idx}/{total} — {patient_id} | Esperado: {true_risk}")

        t0 = time.time()
        predicted_risk = "ERRO"
        justification = ""
        try:
            assessment = run_single_note_with_retry(llm, prompt_template, curr_note)
            raw_risk = assessment.risk_level
            predicted_risk = str(raw_risk.value if hasattr(raw_risk, "value") else raw_risk)
            justification = assessment.clinical_justification
        except DailyQuotaExhausted as dqe:
            print(f"\n  [!] QUOTA DIÁRIA ESGOTADA — interrompendo sessão.")
            print(f"      Execute amanhã: python3 run_prompt_version_eval.py --provider 2 --version {version_name}")
            quota_exhausted = True
            details.append({
                "patient_id": patient_id,
                "true_risk": true_risk,
                "predicted_risk": "QUOTA_ESGOTADA",
                "is_correct": False,
                "latency_s": round(time.time() - t0, 2),
                "justification": str(dqe)[:300],
            })
            break
        except Exception as e:
            print(f"  [!] ERRO NA INFERÊNCIA: {e}")
            justification = str(e)

        latency = time.time() - t0
        is_correct = (
            (true_risk == "Falso_Positivo" and predicted_risk == "Baixo")
            or (true_risk == predicted_risk)
        )

        if is_correct:
            acertos += 1
            if true_risk in matriz:
                matriz[true_risk]["acertos"] += 1
            print(f"  [+] ACERTO → {predicted_risk} ({latency:.2f}s)")
        else:
            if true_risk in matriz:
                matriz[true_risk]["erros"] += 1
                if predicted_risk not in ("ERRO", "QUOTA_ESGOTADA"):
                    matriz[true_risk]["casos_errados"].append(f"{patient_id} → {predicted_risk}")
            print(f"  [-] ERRO   → previsto={predicted_risk} | esperado={true_risk} ({latency:.2f}s)")
            if justification:
                print(f"      Justificativa: {justification[:200]}...")

        details.append({
            "patient_id": patient_id,
            "true_risk": true_risk,
            "predicted_risk": predicted_risk,
            "is_correct": is_correct,
            "latency_s": round(latency, 2),
            "justification": justification,
        })

        if idx < total and not quota_exhausted:
            time.sleep(sleep_between)

    total_time = time.time() - start
    processed = len([d for d in details if d["predicted_risk"] not in ("ERRO", "QUOTA_ESGOTADA")])
    accuracy = (acertos / total) * 100 if total > 0 else 0.0
    avg_latency = (total_time / processed) if processed > 0 else 0.0

    print(f"\n{'─'*65}")
    tag = " [PARCIAL — quota esgotada]" if quota_exhausted else ""
    print(f"  RESULTADO {version_name.upper()}{tag}: {acertos}/{total} — Acurácia: {accuracy:.1f}%")
    print(f"  Latência média: {avg_latency:.2f}s | Tempo total: {total_time:.2f}s")
    for coorte, stats in matriz.items():
        t = stats["acertos"] + stats["erros"]
        if t > 0:
            acc = (stats["acertos"] / t) * 100
            casos_errados = ", ".join(stats["casos_errados"]) if stats["casos_errados"] else "—"
            print(f"  {coorte:<16}: {stats['acertos']}/{t} ({acc:.0f}%) | Erros: {casos_errados}")
    print(f"{'─'*65}")

    return {
        "version": version_name,
        "provider": provider_name,
        "accuracy_pct": round(accuracy, 1),
        "avg_latency_s": round(avg_latency, 2),
        "total_time_s": round(total_time, 2),
        "acertos": acertos,
        "total": total,
        "quota_exhausted": quota_exhausted,
        "matriz": matriz,
        "details": details,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────────────────────────────────────

def load_dataset(filepath: str = "synthetic_patients.json") -> List[Dict]:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset não encontrado: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Avalia versões iterativas de prompt (v1/v2/v3/v4/v2-final) com Ollama ou Gemini."
    )
    parser.add_argument(
        "--provider",
        type=int,
        choices=[1, 2],
        default=2,
        help="1 = Ollama (llama3:8b), 2 = Gemini (gemini-3.6-flash)",
    )
    parser.add_argument(
        "--version",
        type=str,
        choices=list(PROMPT_VERSIONS.keys()) + ["all"],
        default="all",
        help="Versão a avaliar. 'all' executa todas em sequência.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=3.0,
        help="Intervalo (s) entre inferências para respeitar rate limits (padrão: 3.0).",
    )
    args = parser.parse_args()

    provider = LLMProvider.GEMINI if args.provider == 2 else LLMProvider.OLLAMA
    provider_name = (
        "Gemini (gemini-3.6-flash)" if provider == LLMProvider.GEMINI
        else "Ollama (llama3:8b-instruct-q4_K_M)"
    )

    safe_provider = "gemini" if provider == LLMProvider.GEMINI else "ollama"
    output_file = f"prompt_version_results_{safe_provider}.json"

    # ── Carrega resultados acumulados de sessões anteriores ───────────────────
    accumulated: List[Dict] = []
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                accumulated = json.load(f)
            existing_versions = [r["version"] for r in accumulated]
            print(f"[*] Resultados anteriores carregados ({output_file}): versões já avaliadas: {existing_versions}")
        except Exception:
            accumulated = []

    print(f"\n[*] Carregando LLM: {provider_name}")
    llm = get_psychiatric_llm(provider=provider)

    print(f"[*] Carregando dataset sintético...")
    dataset = load_dataset()
    print(f"[+] {len(dataset)} prontuários carregados.\n")

    versions_to_run = (
        list(PROMPT_VERSIONS.keys()) if args.version == "all" else [args.version]
    )

    new_results: List[Dict] = []
    for version_name in versions_to_run:
        result = evaluate_version(
            version_name=version_name,
            prompt_template=PROMPT_VERSIONS[version_name],
            dataset=dataset,
            llm=llm,
            provider_name=provider_name,
            sleep_between=args.sleep,
        )
        new_results.append(result)
        # Interrompe o loop se a quota diária foi esgotada
        if result.get("quota_exhausted"):
            print(f"\n[!] Interrompendo sequência — quota esgotada na versão {version_name}.")
            break

    # ── Mescla: substitui versões re-executadas, adiciona novas ──────────────
    acc_by_version = {r["version"]: r for r in accumulated}
    for r in new_results:
        acc_by_version[r["version"]] = r
    # Preserva a ordem canônica das versões
    ordered_versions = ["v1", "v2", "v3", "v4", "v2-final"]
    merged = [acc_by_version[v] for v in ordered_versions if v in acc_by_version]

    # ── Salva JSON acumulado ──────────────────────────────────────────────────
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n[+] Resultados salvos/acumulados → {output_file}")

    # ── Tabela comparativa com tudo que foi acumulado ─────────────────────────
    complete = [r for r in merged if not r.get("quota_exhausted")]
    if len(complete) >= 2:
        print(f"\n\n{'═'*78}")
        print(f"  TABELA COMPARATIVA ACUMULADA — {provider_name}")
        print(f"{'═'*78}")
        header = f"{'Versão':<12} {'Alto/Im.':<14} {'Moderado':<14} {'Baixo':<14} {'Acurácia':<12} Lat.Média"
        print(header)
        print("─" * 78)
        for r in complete:
            m = r["matriz"]
            def pct(coorte: str) -> str:
                t = m[coorte]["acertos"] + m[coorte]["erros"]
                return f"{m[coorte]['acertos']}/{t} ({(m[coorte]['acertos']/t*100):.0f}%)" if t > 0 else "—"
            tag = " ⚠" if r.get("quota_exhausted") else ""
            print(
                f"{r['version']:<12} {pct('Alto/Iminente'):<14} {pct('Moderado'):<14} "
                f"{pct('Baixo'):<14} {r['accuracy_pct']:.1f}%{tag:<8}  {r['avg_latency_s']:.2f}s"
            )
        print("═" * 78)

    pending = [v for v in ordered_versions if v not in acc_by_version]
    if pending:
        print(f"\n[*] Versões pendentes para próximas sessões: {pending}")
        print(f"    Exemplo: python3 run_prompt_version_eval.py --provider 2 --version {pending[0]}")


if __name__ == "__main__":
    main()
