#!/usr/bin/env python3
"""
e2e_swagger_tests.py — Testes E2E via HTTP contra a API PsicRE-AI (requer Ollama ativo)

Executa os 8 cenários clínicos do backlog TC-SWAGGER-003 a TC-SWAGGER-010,
coletando resultados e imprimindo um relatório final de pass/fail.

Uso:
    python3 e2e_swagger_tests.py
"""

import sys
import json
import time
import httpx

BASE_URL = "http://localhost:8000"
TIMEOUT  = 300  # segundos (inferência CPU pode levar ~40-80s por request)

# ---------------------------------------------------------------------------
# Definição dos cenários
# ---------------------------------------------------------------------------

SCENARIOS = [
    {
        "id": "TC-SWAGGER-003",
        "desc": "PAC-011 — Alto/Iminente + Internação via SAMU (Conduta Adequada)",
        "payload": {
            "patient_id": "PAC-011",
            "current_note": (
                "HMA: Apresenta-se à consulta em sofrimento psíquico agudo e intolerável após "
                "término abrupto de relacionamento conjugal. Apresenta desesperança grave, anedonia "
                "global, apatia e insônia terminal. Durante exame do estado mental, relata plano "
                "definitivo de autoextermínio para o próximo fim de semana. Confessa ter acumulado "
                "e guardado doses letais de clonazepam e opioides adquiridos ilegalmente. "
                "Conduta: Paciente encaminhado em caráter de urgência para internação psiquiátrica "
                "involuntária em hospital terciário via SAMU. Acionada rede de apoio familiar."
            ),
        },
        "expect_risk": "Alto/Iminente",
        "expect_no_alert_prefix": "FALHA CRÍTICA",  # conduta adequada → sem falha crítica
    },
    {
        "id": "TC-SWAGGER-006",
        "desc": "PAC-010 — Alto/Iminente + Alta Ambulatorial (Conduta NEGLIGENTE)",
        "payload": {
            "patient_id": "PAC-010",
            "current_note": (
                "HMA: Paciente trazido por vizinho. Relata ter escrito cartas de despedida para "
                "os filhos e adquirido raticida com intenção de autolesão nesta noite. "
                "Conduta: Ajustado carbonato de lítio para 900mg/dia e agendado retorno ambulatorial "
                "para daqui a 15 dias. Liberado para casa sob cuidados de terceiros."
            ),
        },
        "expect_risk": "Alto/Iminente",
        "expect_alert_prefix": "FALHA CRÍTICA",  # conduta negligente → deve gerar falha crítica
    },
    {
        "id": "TC-SWAGGER-007",
        "desc": "PAC-020 — Moderado + Sem Família/Contrato (Recomendação Esperada)",
        "payload": {
            "patient_id": "PAC-020",
            "current_note": (
                "HMA: Paciente Borderline comparece queixando-se de aumento da labilidade emocional. "
                "Refere pensamentos recorrentes de que 'seria melhor desaparecer', contudo nega "
                "planejamento. Conduta: Realizado contato com a mãe e estabelecido contrato terapêutico."
            ),
        },
        "expect_risk": "Moderado",
    },
    {
        "id": "TC-SWAGGER-008",
        "desc": "PAC-012 — Alto/Iminente + Esquizofrenia + Plano Detalhado (active_ideation=True)",
        "payload": {
            "patient_id": "PAC-012",
            "current_note": (
                "HMA: Paciente relata que as vozes imperativas retornaram ordenando que ele se jogue "
                "da ponte do metrô. Traz consigo um diário detalhado com o mapa da estação e o "
                "horário de menor fluxo de pessoas para executar o plano. Sem crítica de realidade. "
                "Conduta: Aumento de Risperidona e alta ambulatorial acompanhado do irmão."
            ),
        },
        "expect_risk": "Alto/Iminente",
        "expect_active_ideation": True,
        "expect_alert_prefix": "FALHA CRÍTICA",
    },
    {
        "id": "TC-SWAGGER-009",
        "desc": "PAC-030 — Baixo Risco Situacional (Sem Alertas)",
        "payload": {
            "patient_id": "PAC-030",
            "current_note": (
                "HMA: Comparece referindo cansaço físico e sobrecarga acadêmica. Relata pensamento "
                "passivo de que 'seria bom dormir e só acordar quando as provas passassem'. "
                "Nega veementemente qualquer intenção de se machucar. Demonstra planos de futuro. "
                "Conduta: Escitalopram 10mg e encaminhamento para psicoterapia."
            ),
        },
        "expect_risk": "Baixo",
        "expect_no_alerts": True,
    },
    {
        "id": "TC-SWAGGER-010",
        "desc": "PAC-032 — Burnout sem Diagnóstico Grave (Falso Positivo Aceitável)",
        "payload": {
            "patient_id": "PAC-032",
            "current_note": (
                "HMA: Relata exaustão profunda após promoção com aumento de carga de trabalho. "
                "Pensa 'seria mais fácil se eu pudesse sumir por um tempo'. Nega desejo de morte "
                "ou planejamento. Conduta: Burnout. Atestado de 7 dias e encaminhamento para psicoterapia."
            ),
        },
        "expect_risk": "Baixo",  # v2-final pode classificar como Moderado (falso positivo aceitável)
        "acceptable_risks": ["Baixo", "Moderado"],
    },
]

# ---------------------------------------------------------------------------
# Executor
# ---------------------------------------------------------------------------

def run_scenario(client: httpx.Client, scenario: dict) -> dict:
    print(f"\n{'='*60}")
    print(f"[*] {scenario['id']}: {scenario['desc']}")
    t0 = time.time()

    try:
        resp = client.post(
            f"{BASE_URL}/api/v1/triage/",
            json=scenario["payload"],
            timeout=TIMEOUT,
        )
        elapsed = time.time() - t0
        body = resp.json()
    except Exception as exc:
        elapsed = time.time() - t0
        print(f"[!] ERRO de conexão após {elapsed:.1f}s: {exc}")
        return {"id": scenario["id"], "passed": False, "error": str(exc), "elapsed": elapsed}

    if resp.status_code != 200:
        print(f"[!] HTTP {resp.status_code} após {elapsed:.1f}s")
        print(f"    detail: {body.get('detail', body)}")
        return {"id": scenario["id"], "passed": False, "http_status": resp.status_code, "elapsed": elapsed}

    ra = body.get("risk_assessment", {})
    risk_level    = ra.get("risk_level", "N/A")
    active_idea   = ra.get("active_ideation", False)
    red_flags     = ra.get("red_flags", [])
    alerts        = body.get("audit_alerts", [])

    print(f"[+] Resposta recebida em {elapsed:.1f}s")
    print(f"    risk_level     : {risk_level}")
    print(f"    active_ideation: {active_idea}")
    print(f"    red_flags      : {red_flags[:3]}")
    print(f"    audit_alerts   : {len(alerts)} alerta(s)")
    for a in alerts:
        print(f"      → {a[:120]}")

    # Avaliação do resultado
    failures = []

    # Verifica risco esperado (ou lista de aceitáveis)
    acceptable = scenario.get("acceptable_risks") or [scenario.get("expect_risk")]
    if acceptable and risk_level not in acceptable:
        failures.append(f"risk_level={risk_level}, esperado em {acceptable}")

    # Verifica active_ideation se especificado
    if "expect_active_ideation" in scenario:
        if active_idea != scenario["expect_active_ideation"]:
            failures.append(f"active_ideation={active_idea}, esperado={scenario['expect_active_ideation']}")

    # Verifica presença de prefixo de alerta
    if "expect_alert_prefix" in scenario:
        if not any(scenario["expect_alert_prefix"] in a for a in alerts):
            failures.append(f"Esperado alerta com prefixo '{scenario['expect_alert_prefix']}' — não encontrado")

    # Verifica ausência de prefixo de alerta
    if "expect_no_alert_prefix" in scenario:
        if any(scenario["expect_no_alert_prefix"] in a for a in alerts):
            failures.append(f"Alerta '{scenario['expect_no_alert_prefix']}' não deveria estar presente")

    # Verifica ausência total de alertas
    if scenario.get("expect_no_alerts") and alerts:
        failures.append(f"Esperado 0 alertas, recebido {len(alerts)}")

    passed = len(failures) == 0
    if passed:
        print(f"[+] RESULTADO: PASS ✅")
    else:
        print(f"[!] RESULTADO: FAIL ❌ — {'; '.join(failures)}")

    return {
        "id": scenario["id"],
        "passed": passed,
        "risk_level": risk_level,
        "alerts": len(alerts),
        "elapsed": elapsed,
        "failures": failures,
    }


def main():
    print("=== PsicRE-AI — Testes E2E com Ollama (Swagger) ===")
    print(f"Base URL: {BASE_URL} | Timeout por request: {TIMEOUT}s\n")

    results = []
    with httpx.Client() as client:
        # Health check antes de começar
        try:
            hc = client.get(f"{BASE_URL}/health", timeout=5)
            print(f"[+] API health: {hc.json()}")
        except Exception as exc:
            print(f"[!] API não está acessível: {exc}")
            sys.exit(1)

        for scenario in SCENARIOS:
            result = run_scenario(client, scenario)
            results.append(result)

    # Relatório final
    passed  = [r for r in results if r["passed"]]
    failed  = [r for r in results if not r["passed"]]
    total_t = sum(r["elapsed"] for r in results)

    print(f"\n{'='*60}")
    print(f"RELATÓRIO FINAL — {len(passed)}/{len(results)} PASSED | Tempo total: {total_t:.0f}s")
    print(f"{'='*60}")
    for r in results:
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"  {status}  {r['id']}  ({r.get('elapsed', 0):.0f}s)  risk={r.get('risk_level','?')}")
        if not r["passed"] and r.get("failures"):
            for f in r["failures"]:
                print(f"          ↳ {f}")

    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
