---
type: ComponentSpec
id: CS-AUDIT-ALERTS
title: Especificação de Componente — AuditAlerts
description: Lista de alertas de auditoria de protocolo clínico com severidade diferenciada. Distingue visualmente alertas críticos de recomendações.
timestamp: 2026-08-07T14:35:00-03:00
status: approved
version: 1.0.0
owner: psychnote-mfe
tags: [component, alerts, audit, clinical, molecular]
related:
  - ../../domain/clinical-triage.md
  - ./triage-result.md
---

# ComponentSpec: AuditAlerts

## 1. Visão Geral e Propósito

Renderiza a lista de alertas gerados pelo Nó 3 (audit_conduct) do pipeline LangGraph. Os alertas indicam desvios de protocolo clínico em relação às diretrizes CFM/Botega/OMS. O componente deve distinguir visualmente entre alertas de alta severidade (`[FALHA CRITICA]`) e recomendações de protocolo (`[RECOMENDACAO]`, `[ALERTA DE SEGURANÇA]`).

### Anti-patterns

- Não tratar todos os alertas com o mesmo nível visual. Alertas `[FALHA CRITICA]` exigem máximo destaque.
- Não omitir a seção quando `alerts` estiver vazio. Exibir a mensagem de ausência de divergências.
- Não truncar o texto dos alertas. O profissional de saúde precisa da descrição completa para ação.

## 2. Interface Pública (Props)

| Prop | Tipo | Obrigatório | Valor Padrão | Descrição |
| :--- | :--- | :---: | :---: | :--- |
| `alerts` | `string[]` | Sim | — | Array de strings de alerta retornado em `audit_alerts` pela Core API. Pode ser array vazio. |

## 3. Regras de Classificação de Severidade

A severidade de cada alerta é determinada por análise de prefixo no texto da string:

| Prefixo no Texto do Alerta | Severidade | Tratamento Visual |
| :--- | :--- | :--- |
| `[FALHA CRITICA]` | Crítica | Fundo vermelho, borda vermelha espessa, ícone de alerta máximo |
| `[ALERTA DE SEGURANÇA]` | Alta | Fundo laranja, borda laranja, ícone de atenção |
| `[RECOMENDACAO]` | Informativa | Fundo amarelo, borda amarela, ícone informativo |
| Sem prefixo reconhecido | Padrão | Fundo cinza, borda cinza, ícone neutro |

## 4. Estado Vazio (alerts.length === 0)

Quando o array de alertas está vazio, o componente renderiza a mensagem:

> "Nenhuma divergência grave de protocolo identificada na documentação."

Essa mensagem usa estilo neutro (sem cor de alerta) e não deve ser ocultada. A ausência explícita de alertas é informação relevante para auditoria.

## 5. Requisitos de Acessibilidade (A11y)

- O elemento raiz usa `role="list"` quando há alertas, ou `role="status"` quando o array está vazio.
- Cada item de alerta usa `role="listitem"` com `aria-label` descrevendo a severidade: `"Alerta crítico: [texto]"`.
- Ícones têm `aria-hidden="true"`. A informação de severidade é transmitida pelo `aria-label` do item.
- Alertas de severidade crítica usam `aria-live="assertive"` para anuncio imediato em leitores de tela quando o componente monta.

## 6. Casos de Borda

| Situação | Comportamento Esperado |
| :--- | :--- |
| Alerta com texto muito longo (> 300 chars) | Texto completo exibido sem truncamento. Sem expansão/colapso nesta versão. |
| Múltiplos alertas `[FALHA CRITICA]` simultâneos | Todos exibidos com tratamento de máxima severidade. Ordem preservada do array. |
| Texto do alerta sem prefixo reconhecido | Renderizado com estilo padrão sem erro de runtime. |

## 7. Artefatos Derivados desta Spec

| Artefato | Caminho |
| :--- | :--- |
| Implementação | `src/components/audit-alerts/AuditAlerts.tsx` |
| Story (Storybook CSF3) | `src/components/audit-alerts/AuditAlerts.stories.tsx` |
