---
type: ComponentSpec
id: CS-CLINICAL-RISK-BADGE
title: Especificação de Componente — ClinicalRiskBadge
description: Badge de nível de risco clínico. Componente atômico de alta criticidade. Representa visualmente os três estados do RiskLevelEnum do psychnote-core com conformidade WCAG 2.1 AA.
timestamp: 2026-08-07T14:35:00-03:00
status: approved
version: 1.0.0
owner: psychnote-mfe
tags: [component, clinical, atomic, risk, a11y]
related:
  - ../../domain/clinical-triage.md
  - ../../contracts/core-api.md
  - ../states/triage-flow.md
---

# ComponentSpec: ClinicalRiskBadge

## 1. Visão Geral e Propósito

Exibe o nível de risco de suicídio classificado pelo pipeline de IA (psychnote-core) de forma visualmente inequívoca. Este componente é o elemento mais crítico da interface clínica: uma representação ambígua do risco pode levar a erros de protocolo médico com consequências graves ao paciente.

### Anti-patterns

- Não usar este componente para status genéricos de sistema não relacionados a risco clínico.
- Não sobrescrever as cores semânticas via `className` externo. As cores são definidas pela especificação clínica, não por preferência visual.
- Não renderizar o componente com `riskLevel` indefinido ou nulo. Tratar ausência de dados como estado de erro na camada da view.
- Não usar cor como único diferenciador visual (requisito WCAG 2.1 AA — critério 1.4.1).

## 2. Interface Pública (Props)

| Prop | Tipo | Obrigatório | Valor Padrão | Descrição |
| :--- | :--- | :---: | :---: | :--- |
| `riskLevel` | `"Baixo" \| "Moderado" \| "Alto/Iminente"` | Sim | — | Nível de risco retornado pelo campo `risk_assessment.risk_level` da Core API. |
| `size` | `"sm" \| "md" \| "lg"` | Não | `"md"` | Dimensão visual do badge. |
| `showIcon` | `boolean` | Não | `true` | Renderiza o ícone semântico associado ao nível de risco. |

## 3. Matriz de Variantes Visuais

| `riskLevel` | Token de Cor (Tailwind psy-) | Ícone Lucide | Texto Exibido | Comportamento Adicional |
| :--- | :--- | :--- | :--- | :--- |
| `"Baixo"` | `psy-bg-green-100 psy-text-green-800` | `CheckCircle2` | Risco Baixo | Sem destaque adicional |
| `"Moderado"` | `psy-bg-yellow-100 psy-text-yellow-800` | `AlertTriangle` | Risco Moderado | Borda visível, texto em negrito |
| `"Alto/Iminente"` | `psy-bg-red-100 psy-text-red-900` | `AlertOctagon` | Risco Alto / Iminente | Borda vermelha espessa, animação de pulso no ícone |

## 4. Requisitos de Acessibilidade (A11y)

- `role="status"` para anunciar mudanças dinâmicas em leitores de tela.
- `aria-label` explícito: `"Nível de risco de triagem: [texto do nível]"`.
- Contraste mínimo de 4.5:1 entre texto e fundo (WCAG AA, critério 1.4.3).
- O ícone deve ter `aria-hidden="true"`. A informação semântica é carregada pelo texto e pelo `aria-label`, não pelo ícone.
- Não exigir interação de teclado (componente de exibição, não interativo).

## 5. Casos de Borda e Tratamento de Erros

| Situação | Comportamento Esperado |
| :--- | :--- |
| `riskLevel` recebe valor fora do enum | Não deve ocorrer: o schema Zod valida o response antes de chegar ao componente. Se ocorrer, renderizar badge cinza com texto "Risco indeterminado" e registrar erro no console. |
| `showIcon=false` | Badge exibido apenas com texto e cor, sem ícone. O `aria-label` permanece completo. |
| `size="sm"` | Ícone reduzido ou omitido conforme espaço. Texto abreviado não permitido. |

## 6. Exemplo de Uso (Referência de Implementação)

```tsx
import { ClinicalRiskBadge } from '@/components/clinical-risk-badge/ClinicalRiskBadge';

// Uso dentro de TriageResult
<ClinicalRiskBadge
  riskLevel={triageData.risk_assessment.risk_level}
  size="lg"
  showIcon={true}
/>
```

## 7. Artefatos Derivados desta Spec

| Artefato | Caminho |
| :--- | :--- |
| Implementação | `src/components/clinical-risk-badge/ClinicalRiskBadge.tsx` |
| Story (Storybook CSF3) | `src/components/clinical-risk-badge/ClinicalRiskBadge.stories.tsx` |
| Schema de dados do campo | `src/lib/schemas.ts` — `RiskLevelSchema` |
