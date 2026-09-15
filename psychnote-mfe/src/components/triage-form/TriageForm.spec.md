---
type: ComponentSpec
id: CS-TRIAGE-FORM
title: Especificação de Componente — TriageForm
description: Formulário de submissão de nota clínica para triagem de risco assíncrona. Gerencia validação local, submissão HTTP 202 e estado de streaming SSE da IA.
timestamp: 2026-08-08T19:00:00-03:00
status: approved
version: 2.0.0
owner: psychnote-mfe
tags: [component, form, triage, organism, sse, async]
related:
  - ../../.okf/contracts/bff-api.md
  - ../../.okf/contracts/core-api.md
  - ../../.okf/decisions/0005-async-sse-triage.md
  - ../../hooks/useTriage.spec.md
  - ./TriageResult.spec.md
---

# ComponentSpec: TriageForm

## 1. Visão Geral e Propósito

Captura a nota clínica atual redigida pelo profissional de saúde e dispara a triagem assíncrona via BFF. O componente coordena a validação local, o estado de submissão `HTTP 202` e a comunicação via `EventSource` (SSE stream `/api/triage/stream/:jobId`) durante o processamento da IA (~20-40s).

### Anti-patterns

- Não desabilitar o botão de submissão sem exibir um indicador claro de progresso da conexão SSE.
- Não limpar o campo de nota clínica automaticamente após a submissão.
- Não exibir o resultado da triagem dentro deste componente. O resultado é responsabilidade do `TriageResult`.
- Não criar a conexão SSE diretamente dentro deste componente. O gerenciamento de canal SSE é responsabilidade do hook `useTriage`.

## 2. Interface Pública (Props)

| Prop | Tipo | Obrigatório | Valor Padrão | Descrição |
| :--- | :--- | :---: | :---: | :--- |
| `patientId` | `string` | Sim | — | Identificador do paciente. Enviado no payload junto à nota. |
| `onSubmit` | `(note: string) => void` | Sim | — | Callback chamado com o texto da nota quando o formulário é submetido e validado. |
| `isSubmitting` | `boolean` | Sim | — | Quando `true`, desabilita o campo de texto e exibe o indicador de envio HTTP 202. |
| `isStreaming` | `boolean` | Não | `false` | Quando `true`, indica que o `EventSource` SSE está ativo escutando a inferência da IA. |
| `jobId` | `string \| null` | Não | `null` | Identificador único do job assíncrono exibido no indicador de progresso SSE. |
| `disabled` | `boolean` | Não | `false` | Desabilita o formulário por razão externa. |

## 3. Estados do Componente

| Estado | Condição | Comportamento |
| :--- | :--- | :--- |
| `idle` | `isSubmitting=false`, `isStreaming=false` | Campo de texto editável, botão habilitado |
| `submitting` | `isSubmitting=true` | Campo e botão desabilitados, spinner de envio HTTP 202 |
| `streaming` | `isStreaming=true` | Campo desabilitado, banner SSE exibindo: *"Conexão SSE ativa (Job [jobId]). Aguardando parecer da IA..."* |
| `validation-error` | Nota < 10 caracteres | Mensagem de erro inline abaixo do campo |

## 4. Requisitos de Acessibilidade (A11y)

- O campo de texto usa `<textarea>` com `id` único e `<label>` associado via `htmlFor`.
- Mensagens de erro usam `role="alert"`.
- O indicador de progresso SSE usa `aria-live="polite"` para anunciar atualizações de estado da IA.
