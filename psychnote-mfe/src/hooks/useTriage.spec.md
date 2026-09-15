---
type: StateSpec
id: SS-TRIAGE-FLOW
title: Especificação de Máquina de Estado — TriageFlow (Assíncrona com EventSource SSE)
description: Máquina de estados finitos (FSM) para o fluxo de triagem clínica assíncrona orientada a eventos (HTTP 202 Accepted + EventSource SSE).
timestamp: 2026-08-08T19:00:00-03:00
status: approved
version: 2.0.0
owner: psychnote-mfe
tags: [state-machine, fsm, triage, flow, sse, async]
related:
  - ../components/triage-form/TriageForm.spec.md
  - ../components/triage-result/TriageResult.spec.md
  - ../../.okf/contracts/bff-api.md
  - ../../.okf/decisions/0005-async-sse-triage.md
---

# StateSpec: TriageFlow (Assíncrona com SSE Stream)

## 1. Visão Geral

Define os estados possíveis do fluxo de triagem individual do paciente: do envio da nota clínica (`POST /api/triage`), recebimento do `job_id` (HTTP 202 Accepted), abertura da conexão `EventSource` (SSE stream `/api/triage/stream/:jobId`), até a recepção do evento `triage_completed` e exibição do parecer ou tratamento de erros.

## 2. Diagrama de Estados Finitos

```
[idle]
  |
  | SUBMIT (nota válida, min 10 chars)
  v
[submitting]  (POST /api/triage -> HTTP 202 Accepted { job_id })
  |
  | JOB_ACCEPTED
  v
[streaming]   (new EventSource /api/triage/stream/:jobId) <--- RETRY ---+
  |                                                                        |
  | SSE_EVENT: triage_completed (Zod parse ok)                             |
  v                                                                        |
[success]                                                                  |
  |                                                                        |
  | NEW_TRIAGE                                                             |
  v                                                                        |
[idle]                                                                     |
                                                                           |
[submitting] / [streaming]                                                 |
  |                                                                        |
  | API_ERROR (HTTP 4xx/5xx ou SSE connection error)                       |
  v                                                                        |
[error:api] ---------------------- RETRY ----------------------------------+
  |
  | RESET
  v
[idle]

[streaming]
  |
  | VALIDATION_ERROR (ZodError no payload do evento SSE)
  v
[error:contract] ----> RESET
  |
  v
[idle]
```

## 3. Definição de Estados

| Estado | Descrição | UI esperada |
| :--- | :--- | :--- |
| `idle` | Formulário disponível para entrada de dados | `TriageForm` habilitado, sem resultado visível |
| `submitting` | Requisição `POST /api/triage` enviando a nota | `TriageForm` desabilitado com spinner de submissão rápida |
| `streaming` | `202 Accepted` recebido, `EventSource` ativo em `/stream/:jobId` | Indicator de progresso da IA: "Processando triagem com IA (Job [jobId])..." |
| `success` | Evento `triage_completed` recebido e validado pelo Zod | `TriageResult` renderizado, `EventSource` fechado, formulário oculto |
| `error:api` | Falha no HTTP 202 ou erro de comunicação SSE | Mensagem de erro de comunicação, `EventSource` fechado, opção de retry |
| `error:contract` | `ZodError` no JSON do evento `triage_completed` | Mensagem de erro de contrato, `EventSource` fechado, opção de reset |

## 4. Eventos e Transições

| De | Evento | Para | Ação |
| :--- | :--- | :--- | :--- |
| `idle` | `SUBMIT` (nota >= 10 chars) | `submitting` | `POST /api/triage { patient_id, current_note }` |
| `submitting` | `JOB_ACCEPTED` (202 Accepted) | `streaming` | Iniciar `new EventSource('/api/triage/stream/' + job_id)` |
| `streaming` | `SSE: triage_completed` + Zod ok | `success` | Fechar `EventSource`, armazenar `TriageResponse` |
| `streaming` | `SSE: onerror` | `error:api` | Fechar `EventSource`, registrar mensagem de erro de conexão |
| `streaming` | `VALIDATION_ERROR` (ZodError) | `error:contract` | Fechar `EventSource`, registrar erro de schema |
| `success` | `NEW_TRIAGE` | `idle` | Limpar resultado, reexibir formulário |
| `error:api` | `RETRY` | `submitting` | Re-executar a submissão com os mesmos dados |
| `error:api` / `error:contract` | `RESET` | `idle` | Limpar estado de erro |

## 5. Estados Impossíveis (Prevenidos pela FSM)

- `streaming=true` E `success=true` simultaneamente.
- Conexão `EventSource` aberta após transição para `success` ou `error`.
- Renderizar `TriageResult` com dados parciais não parseados pelo Zod.
