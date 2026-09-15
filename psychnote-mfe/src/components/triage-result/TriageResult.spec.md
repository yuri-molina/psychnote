---
type: ComponentSpec
id: CS-TRIAGE-RESULT
title: Especificação de Componente — TriageResult
description: Organismo que compõe e exibe o resultado completo de uma triagem clínica. Coordena ClinicalRiskBadge, AuditAlerts e as seções textuais do parecer.
timestamp: 2026-08-07T14:35:00-03:00
status: approved
version: 1.0.0
owner: psychnote-mfe
tags: [component, triage, result, organism]
related:
  - ./clinical-risk-badge.md
  - ./audit-alerts.md
  - ../../contracts/core-api.md
  - ../../domain/clinical-triage.md
---

# ComponentSpec: TriageResult

## 1. Visão Geral e Propósito

Exibe o resultado completo retornado pelo pipeline de triagem do psychnote-core. É um componente de leitura pura — não contém ações de edição nem lógica de fetch. Compõe `ClinicalRiskBadge` e `AuditAlerts` junto às seções textuais do parecer clínico.

### Anti-patterns

- Não renderizar este componente com dados parcialmente validados. O schema Zod `TriageResponseSchema` deve ter sido aplicado antes de passar os dados via props.
- Não truncar o `final_report` ou a `clinical_justification`. O profissional de saúde precisa do texto completo para auditoria.
- Não ocultar `audit_alerts` quando o array estiver vazio — exibir a mensagem de ausência de divergências.

## 2. Interface Pública (Props)

| Prop | Tipo | Obrigatório | Valor Padrão | Descrição |
| :--- | :--- | :---: | :---: | :--- |
| `data` | `TriageResponse` | Sim | — | Objeto completo validado pelo `TriageResponseSchema` (Zod). |
| `onNewTriage` | `() => void` | Sim | — | Callback para iniciar nova triagem do mesmo paciente. Controla a navegação de volta ao formulário. |

O tipo `TriageResponse` é inferido de `TriageResponseSchema` em `src/lib/schemas.ts`.

## 3. Seções do Componente e Ordem de Renderização

```
TriageResult
├── [Seção 1] Cabeçalho
│   ├── patient_id (texto identificador)
│   └── ClinicalRiskBadge (risk_level) — size="lg"
│
├── [Seção 2] Indicadores de Ideação
│   ├── passive_ideation (boolean — exibido como linha sim/não)
│   └── active_ideation  (boolean — exibido como linha sim/não)
│
├── [Seção 3] Red Flags
│   └── Lista de strings (red_flags[]) — sem texto padrão se vazio
│
├── [Seção 4] Fatores de Proteção
│   └── Lista de strings (protection_factors[]) — "Nenhum identificado" se vazio
│
├── [Seção 5] Justificativa Clínica
│   └── clinical_justification (texto completo, sem truncar)
│
├── [Seção 6] Alertas de Protocolo
│   └── AuditAlerts (audit_alerts[])
│
├── [Seção 7] Parecer Executivo
│   └── final_report (texto pré-formatado, preservar quebras de linha)
│
└── [Seção 8] Ação
    └── Botão "Nova Triagem" → onNewTriage()
```

## 4. Regras de Exibição por Campo

| Campo | Exibição quando vazio | Exibição quando preenchido |
| :--- | :--- | :--- |
| `red_flags` | Seção omitida | Lista com marcadores |
| `protection_factors` | "Nenhum fator de proteção identificado na nota." | Lista com marcadores |
| `audit_alerts` | Mensagem: "Nenhuma divergência grave de protocolo identificada." | Delegado ao componente `AuditAlerts` |
| `clinical_justification` | Seção omitida | Parágrafo de texto completo |
| `final_report` | Seção omitida | Bloco pré-formatado (`<pre>` ou `whitespace-pre-wrap`) |

## 5. Requisitos de Acessibilidade (A11y)

- A estrutura usa `<article>` como elemento semântico raiz do resultado.
- Cada seção usa `<section>` com `aria-labelledby` apontando para o `<h2>` correspondente.
- A hierarquia de headings dentro do componente deve ser H2 (seções) e H3 (subseções).
- O botão "Nova Triagem" é o único elemento interativo e deve receber foco ao montar o componente.

## 6. Casos de Borda

| Situação | Comportamento Esperado |
| :--- | :--- |
| `risk_assessment.risk_level = "Alto/Iminente"` | `ClinicalRiskBadge` renderizado com destaque máximo. Seção de alertas exibida no topo, antes das outras seções. |
| `audit_alerts` contém string com prefixo `[FALHA CRITICA]` | Delegado ao `AuditAlerts`, que aplica tratamento visual de máxima severidade. |
| `final_report` muito longo | Área de texto com scroll interno. Sem truncamento. |

## 7. Artefatos Derivados desta Spec

| Artefato | Caminho |
| :--- | :--- |
| Implementação | `src/components/triage-result/TriageResult.tsx` |
| Story (Storybook CSF3) | `src/components/triage-result/TriageResult.stories.tsx` |
| Schema de dados | `src/lib/schemas.ts` — `TriageResponseSchema` |
