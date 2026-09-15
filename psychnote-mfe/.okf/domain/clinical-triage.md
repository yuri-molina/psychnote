---
type: DomainModel
title: Modelo de Domínio Clínico — Triagem de Risco de Suicídio
description: Regras de negócio clínicas que o MFE deve representar visualmente. Extraído do psychnote-core (ClinicalMonitor, audit_conduct).
timestamp: 2026-08-07T12:00:00-03:00
status: active
version: 1.0.0
resource: ../../../psychnote-core/analytics/clinical_monitor.py
related:
  - ../glossary.md
  - ../contracts/core-api.md
---

# Modelo de Domínio Clínico — Triagem de Risco de Suicídio

Este documento descreve as regras de negócio clínicas extraídas do `psychnote-core`. O MFE não executa essas regras (isso é responsabilidade do Core), mas deve representá-las visualmente de forma precisa e inequívoca.

## Entidade Principal: RiskLevel (Nível de Risco)

Enum com três valores discretos, sem gradação intermediária:

| Valor | Descrição Clínica |
| :--- | :--- |
| `Baixo` | Ideação passiva pontual e situacional. Nega planejamento. Fatores de proteção robustos presentes. Sem histórico grave. |
| `Moderado` | Ideação recorrente ou persistente. Sem plano imediato estruturado. Diagnóstico instável ativo ou histórico de automutilação presente. |
| `Alto/Iminente` | Plano concreto (local, método, data). Atos preparatórios (cartas, testamento, meios letais). Alucinação imperativa com plano. Intenção de agir em horas ou dias. |

Hierarquia de precedência: qualquer critério de Alto/Iminente supera qualquer fator protetor. A presença de fator protetor nao reduz Alto/Iminente para Moderado.

## Entidade: SuicideRiskAssessment

Objeto retornado pelo Core no campo `risk_assessment` da resposta de triagem.

| Campo | Tipo | Significado |
| :--- | :--- | :--- |
| `risk_level` | RiskLevel | Classificacao discreta do risco |
| `passive_ideation` | boolean | Marcadores linguísticos de cansaço de vida sem intenção ativa |
| `active_ideation` | boolean | Planejamento tático com método, local ou data |
| `red_flags` | string[] | Fragmentos textuais de risco extraídos diretamente da nota |
| `protection_factors` | string[] | Fatores mitigadores identificados na nota |
| `clinical_justification` | string | Parecer técnico do modelo com base nos thresholds clínicos |

## Regras de Auditoria de Conduta (audit_conduct)

O Nó 3 do pipeline LangGraph compara o `risk_level` com a conduta narrada na nota e gera `audit_alerts`. O MFE deve exibir esses alertas com destaque proporcional à sua severidade.

### Alertas para risk_level = Alto/Iminente

- Se a nota contém palavras como "alta", "liberado" ou "retorno ambulatorial": gera alerta `[FALHA CRITICA]` de negligência de protocolo. O protocolo mandatório exige internação imediata, vigilância constante e quebra de sigilo com a família.
- Se a nota não contém palavras como "internação", "vigilância", "samu", "ambulância" ou "hospital": gera alerta `[ALERTA DE SEGURANÇA]` de ausência de encaminhamento documentado.

### Alertas para risk_level = Moderado

- Se a nota não contém palavras como "família", "contrato" ou "contato": gera alerta `[RECOMENDACAO]` de que as diretrizes exigem acionamento da família e negociação de contrato terapêutico.

### Ausência de Alertas

Se `audit_alerts` é um array vazio, significa que nenhuma divergência grave de protocolo foi identificada.

## Regras de Representação Visual no MFE

O MFE deve representar o `risk_level` de forma visualmente inequívoca, seguindo as regras abaixo. A cor nunca deve ser o único diferenciador (requisito de acessibilidade WCAG 2.1 AA).

| risk_level | Cor | Indicador Textual | Comportamento |
| :--- | :--- | :--- | :--- |
| `Baixo` | Verde (#22c55e) | "Risco Baixo" | Badge estático sem destaque adicional |
| `Moderado` | Ambar (#f59e0b) | "Risco Moderado" | Badge com borda, texto em negrito |
| `Alto/Iminente` | Vermelho (#ef4444) | "Risco Alto / Iminente" | Badge com destaque visual máximo; alertas de auditoria exibidos no topo |

Alertas com o prefixo `[FALHA CRITICA]` devem receber tratamento visual diferenciado dos alertas `[RECOMENDACAO]`.

## Premissa de Conformidade LGPD

Os dados do paciente (patient_id, current_note, resultados de triagem) existem apenas em memória durante a sessão. O MFE nao deve persistir nenhum dado clínico em mecanismos de armazenamento do navegador.
