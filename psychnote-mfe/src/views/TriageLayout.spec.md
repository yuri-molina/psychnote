---
type: LayoutSpec
id: LS-TRIAGE-LAYOUT
title: Especificação de Layout — Telas de Triagem (Form e Resultado)
description: Composição estrutural compartilhada pelas views de formulário e resultado de triagem assíncrona. Define navegação contextual, transição de estados via SSE e atualização de estado/cache de paciente.
timestamp: 2026-08-09T22:45:00-03:00
status: approved
version: 2.1.0
owner: psychnote-mfe
tags: [layout, triage, detail, result, view, sse, persistence]
related:
  - ../components/triage-form/TriageForm.spec.md
  - ../components/triage-result/TriageResult.spec.md
  - ../hooks/useTriage.spec.md
---

# LayoutSpec: Telas de Triagem

## 1. Layout Compartilhado (TriageForm e TriageResult)

Ambas as views compartilham o mesmo esqueleto de layout. O slot de conteúdo principal alterna entre `TriageForm` (nos estados FSM `idle`, `submitting`, `streaming` e `error`) e `TriageResult` (no estado `success`).

```
[Slot: Navegação de Retorno]
  Botão "Voltar para a Listagem de Pacientes"  →  NavLink para PatientListView (/patients)

[Slot: Cabeçalho Contextual]
  Título: "Evolução"
  Subtítulo: "Paciente em Atendimento: [displayName]" (Humanização: exibe Nome Completo)

[Slot: Conteúdo Principal]
  ├── [FSM: idle | submitting | streaming | error]  →  TriageForm (com indicador SSE / banner de erro)
  └── [FSM: success]                               →  TriageResult
```

## 2. Transição entre Conteúdo Principal e Atualização de Prontuário

A alternância entre `TriageForm` e `TriageResult` ocorre na rota `/patients/:patientId/triage`, controlada pela FSM do `useTriage`.

| Estado FSM | Slot de Conteúdo Principal | Ação de Estado / Cache |
| :--- | :--- | :--- |
| `idle` | `TriageForm` habilitado | — |
| `submitting` | `TriageForm` desabilitado enviando `POST /triage` | Registra rascunho de evolução e invalida queries `['patients']` e `['patientRecord', patientId]` |
| `streaming` | `TriageForm` desabilitado com indicador SSE ativo | Conexão `EventSource` escutando evento `triage_completed` |
| `error:api` ou `error:contract` | `TriageForm` com banner de erro acima | Opções de Retry/Reset |
| `success` | `TriageResult` com dados completos recebidos da IA | Atualiza `last_risk_level` e `last_triage_date` no repositório do paciente e invalida caches |

## 3. Navegação de Retorno e Cleanup

- O botão "Voltar para a Listagem de Pacientes" direciona para `/patients`.
- Ao submeter uma evolução, a atualização do repositório garante que a nova evolução permaneça visível na linha do tempo do prontuário e na listagem de pacientes.
- Caso o usuário navegue para outra rota durante o estado `streaming`, o `useEffect` do `useTriage` fecha a conexão `EventSource` automaticamente, evitando vazamento de socket SSE.
