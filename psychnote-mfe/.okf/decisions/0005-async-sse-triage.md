---
type: Decision
title: "ADR-0005: Arquitetura Assíncrona de Triagem com EventSource (SSE Stream) no MFE"
description: Transição do modelo síncrono bloqueante para o modelo assíncrono baseado em HTTP 202 Accepted + conexão Server-Sent Events (SSE) via EventSource nativo.
timestamp: 2026-08-08T19:00:00-03:00
status: active
version: 1.0.0
resource: ../../src/hooks/useTriage.ts
related:
  - ../architecture/overview.md
  - ../contracts/bff-api.md
  - 0004-zod-runtime-validation.md
---

# ADR-0005: Arquitetura Assíncrona de Triagem com EventSource (SSE Stream) no MFE

## Contexto

A inferência dos modelos LLM no `psychnote-core` para triagem de risco e auditoria de conduta clínica possui latência variando entre 20 e 40 segundos. No modelo síncrono anterior (`POST /triage`), a conexão HTTP permanecia aberta aguardando a resposta, o que gerava riscos de timeout no browser/gateway, alto consumo de recursos e dependência de chamadas síncronas bloqueantes.

Para resolver este problema, a arquitetura do ecossistema evoluiu para um modelo assíncrono orientado a eventos:
1. O MFE envia `POST /api/triage` ao BFF e recebe imediatamente `202 Accepted` contendo um `job_id`.
2. O MFE estabelece uma conexão Server-Sent Events (`EventSource`) com a rota `/api/triage/stream/:jobId`.
3. O `psychnote-core` processa o LangGraph em background e notifica o BFF via Webhook.
4. O BFF dispara o evento SSE `triage_completed` com a resposta completa.
5. O MFE consome o evento, valida o payload via Zod e encerra o `EventSource`.

## Decisão

Adotar o uso do objeto nativo `EventSource` da Web API dentro do hook `useTriage` no React para gerenciar o streaming de atualizações em tempo real sem polling:

1. **Submissão Inicial (`POST /api/triage`)**:
   - Envia `{ patient_id, current_note }`.
   - Espera resposta rápida `202 Accepted` com `{ job_id, status: "processing" }`.
   - Valida o aceite com `TriageAsyncResponseSchema`.

2. **Conexão de Eventos (`EventSource`)**:
   - Instancia `new EventSource(`${BFF_URL}/api/triage/stream/${job_id}`)`.
   - Registra listener para o evento customizado `'triage_completed'`.
   - Ao receber o evento, efetua `TriageResponseSchema.parse(JSON.parse(event.data))`.
   - Fecha a conexão explicitamente (`eventSource.close()`).

3. **Gerenciamento de Erros e Cleanup**:
   - Tratamento do evento `onerror` no `EventSource` com timeout de segurança e encerramento do socket.
   - Encerramento obrigatório do `EventSource` no cleanup do `useEffect` ou cancelamento do hook para evitar vazamento de memória e conexões pendentes.

## Consequências

- **UX Aprimorada**: A UI responde instantaneamente ao clique do usuário exibindo estado de progresso com `job_id`, sem risco de timeout de requisição HTTP.
- **Eficiência de Rede**: Elimina conexões HTTP mantidas por 40s ou estratégias de polling contínuo.
- **Resiliência**: Falhas de conexão SSE são tratadas com encerramento limpo e mensagem informativa ao usuário com opção de retry.
