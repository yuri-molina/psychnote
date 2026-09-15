---
type: DomainModel
title: Modelo de Domínio Clínico — Perspectiva do BFF
description: Regras de negócio clínicas que o BFF deve conhecer para rotear e transformar dados corretamente, sem executar nenhuma lógica de domínio própria.
timestamp: 2026-08-07T16:55:00-03:00
status: active
version: 1.0.0
resource: ../../../psychnote-core/analytics/clinical_monitor.py
related:
  - ../glossary.md
  - ../contracts/core-api.md
---

# Modelo de Domínio Clínico — Perspectiva do BFF

## Princípio de Responsabilidade

O BFF **não executa regras clínicas**. A responsabilidade de classificação de risco, auditoria de conduta e geração de parecer clínico é exclusiva do psychnote-core. O BFF deve conhecer o domínio **exclusivamente** para validar corretamente os schemas de entrada e saída e garantir que dados inválidos não trafeguem na fronteira de integração.

---

## Enum: RiskLevel

Os valores permitidos para `risk_level` são os seguintes, **exatamente como o Core retorna** (case-sensitive):

| Valor           | Significado clínico                                      |
|-----------------|----------------------------------------------------------|
| `Baixo`         | Sem indicadores significativos de risco imediato         |
| `Moderado`      | Presença de fatores de risco sem iminência identificada  |
| `Alto/Iminente` | Risco elevado com possível necessidade de intervenção    |

> A validação Zod no BFF deve usar esses três valores exatos. Qualquer valor fora desse conjunto indica falha no pipeline do Core e deve ser tratado como erro `502`.

---

## Entidade: TriageRequest

Entrada recebida do MFE e validada pelo BFF antes de encaminhar ao Core.

| Campo          | Tipo   | Restrição            | Motivo clínico                                                           |
|----------------|--------|----------------------|--------------------------------------------------------------------------|
| `patient_id`   | string | não-vazio            | Identifica o prontuário. Ausência impede rastreabilidade de auditoria.   |
| `current_note` | string | mínimo 10 caracteres | O pipeline LLM rejeita notas muito curtas por insuficiência de contexto clínico. |

---

## Entidade: TriageResponse

Retornada pelo Core e validada pelo BFF antes de repassar ao MFE. A validação garante que o MFE nunca receba um payload estruturalmente inválido.

```
TriageResponse
├── patient_id: string
├── risk_assessment: RiskAssessment
│   ├── risk_level: 'Baixo' | 'Moderado' | 'Alto/Iminente'
│   ├── passive_ideation: boolean
│   ├── active_ideation: boolean
│   ├── red_flags: string[]
│   ├── protection_factors: string[]
│   └── clinical_justification: string
├── audit_alerts: string[]
└── final_report: string
```

---

## Premissas de Conformidade LGPD

O BFF opera sobre dados de saúde classificados como **dados sensíveis** nos termos da Lei Geral de Proteção de Dados (LGPD, Art. 11). As seguintes restrições são obrigatórias na implementação do BFF:

### Proibição de Log de Dados Clínicos

O BFF **não deve logar** o conteúdo dos campos `current_note` e `final_report` em nenhum mecanismo de logging (console, arquivo, serviço externo).

Apenas **metadados não-clínicos** podem ser registrados:

| Metadado permitido | Exemplo de valor |
|--------------------|------------------|
| `patient_id`       | `"PAC-010"`      |
| Código HTTP        | `200`, `502`     |
| Latência (ms)      | `32430`          |
| Método e rota      | `POST /triage`   |

### Proibição de Cache de Resultados

O BFF **não deve armazenar em cache** nenhum resultado de triagem, independente da estratégia (in-memory, Redis, HTTP cache headers). Resultados de triagem têm validade clínica associada ao momento da avaliação e não podem ser reutilizados.

### Ciclo de Vida dos Dados Clínicos

Os dados clínicos têm **vida única no ciclo request/response**. Após o response ser enviado ao MFE, o BFF não deve reter qualquer referência ao conteúdo clínico. Nenhuma persistência, nenhum buffer de log assíncrono, nenhuma variável de módulo deve manter esses dados além do escopo da requisição.
