---
type: ModuleSpec
title: Spec — Plugin ErrorHandler
description: Especificação do plugin Fastify de tratamento global de erros. Garantia crash-free com suporte estendido para o fluxo assíncrono (HTTP 202), conexões SSE e Webhook Callbacks.
timestamp: 2026-08-08T18:48:00-03:00
status: active
version: 2.0.0
resource: ./error-handler.plugin.ts
related:
  - ../../../.okf/decisions/0003-timeout-and-resilience.md
  - ../../../.okf/decisions/0005-async-webhook-sse-architecture.md
  - ../core-client/CoreClient.spec.md
---

# Spec — Plugin ErrorHandler

## Responsabilidade Única

O plugin `ErrorHandler` registra o handler global `setErrorHandler` na instância do Fastify. Sua função primordial é capturar **qualquer** exceção não tratada na camada de rotas ou plugins e convertê-la em uma resposta HTTP estruturada, prevenindo o encerramento inesperado do processo Node.js (Garantia Crash-Free).

Com a arquitetura assíncrona, o `ErrorHandler` também provê tratamento resiliente para interrupções em conexões SSE e erros de payload em callbacks de webhook.

---

## Mapeamento Global de Erros

| Tipo de Erro | `statusCode` | `error` | `message` | Campo `upstream` |
| :--- | :--- | :--- | :--- | :--- |
| `UpstreamTimeoutError` | `504` | `'Gateway Timeout'` | `'O serviço de IA não respondeu dentro do tempo limite estipulado.'` | `'psychnote-core'` |
| `UpstreamUnavailableError` | `502` | `'Bad Gateway'` | `'Não foi possível conectar ao serviço de IA. Verifique se o psychnote-core está rodando.'` | `'psychnote-core'` |
| `UpstreamError` | `502` | `'Bad Gateway'` | `'O serviço de IA retornou uma resposta de erro inesperada.'` | `'psychnote-core'` |
| `ZodError` (Requisição do cliente) | `400` | `'Bad Request'` | Detalhes da falha de validação dos campos | ausente |
| `ZodError` (Payload do Webhook do Core) | `400` | `'Bad Request'` | `'Payload de webhook enviado pelo Core é inválido ou violou o contrato.'` | `'psychnote-core'` |
| `ZodError` (Validação de resposta do Core) | `502` | `'Bad Gateway'` | `'Resposta do serviço de IA violou o contrato esperado.'` | `'psychnote-core'` |
| `PrematureCloseError` (SSE) | N/A | Log local | Trata encerramento prematuro de conexão SSE sem lançar exceção não capturada | ausente |
| Qualquer outro erro não previsto | `500` | `'Internal Server Error'` | `'Erro interno inesperado no servidor.'` | ausente |

---

## Tratamento Específico para Conexões SSE e Webhooks

1. **Erros durante o Streaming SSE (`GET /api/triage/stream/:jobId`):**
   - Se ocorrer um erro enquanto a conexão SSE está aberta (ex.: erro de escrita no socket), o `ErrorHandler` deve garantir o fechamento amigável da conexão, cancelando o timer de heartbeat e removendo o `jobId` de `activeSseConnections`.
   - Evita exceções do tipo `ERR_STREAM_WRITE_AFTER_END` ou `ECONNRESET` subindo como unhandled rejections.

2. **Erros no Webhook Callback (`POST /api/webhooks/triage-result`):**
   - Se o payload recebido do Core falhar na validação do `WebhookPayloadSchema`, o handler responde `400 Bad Request` com `upstream: 'psychnote-core'`, sinalizando a quebra de contrato sem afetar o estado interno do BFF.

---

## Garantias de Resiliência e Segurança (Crash-Free & LGPD)

### Garantia Crash-Free:
- **Zero Unhandled Rejections:** Nenhuma `Promise` rejeitada em background ou handler de rota derruba o servidor.
- **Isolamento de Conexões SSE:** Uma falha em um socket SSE específico não compromete nem interfere nas demais streams ativas no mapa `activeSseConnections`.

### Diretrizes de Logging LGPD:
- **O que DEVE ser logado:** Código do erro (`error.name`), status HTTP, `job_id`, `patient_id` (se contextualizados) e mensagem genérica.
- **O que JAMAIS deve ser logado:** Conteúdo de notas clínicas (`current_note`), pareceres (`final_report`, `clinical_justification`), ou stacktraces expostas no corpo da resposta HTTP enviada aos clientes.
