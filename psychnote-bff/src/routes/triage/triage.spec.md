---
type: RouteSpec
title: Spec — POST /api/triage
description: Especificação completa da rota assíncrona de submissão de triagem de risco clínico do BFF. Gera job_id (UUIDv4), encaminha para o Core (/api/v1/triage/async) e retorna HTTP 202 Accepted.
timestamp: 2026-08-08T18:48:00-03:00
status: active
version: 2.0.0
resource: ./triage.route.ts
related:
  - ../../schemas/index.ts
  - ../../../.okf/contracts/bff-api.md
  - ../../../.okf/contracts/core-api.md
  - ../../../.okf/decisions/0005-async-webhook-sse-architecture.md
  - ../plugins/core-client/CoreClient.spec.md
---

# Spec — POST /api/triage

## Identidade da Rota

| Método | URL | Tag | Descrição |
| :--- | :--- | :--- | :--- |
| POST | /api/triage | Triagem Clínica | Gera job_id, encaminha nota clínica ao Core assincronamente e retorna HTTP 202 Accepted |

---

## Contrato de Entrada (Request Body)

O schema de validação utilizado é o `TriageAsyncRequestSchema` (ou `TriageRequestSchema`) definido em `src/schemas/index.ts` e provisionado ao Fastify via `fastify-type-provider-zod`.

| Campo | Tipo | Validação | Descrição |
| :--- | :--- | :--- | :--- |
| `patient_id` | `string` | Mínimo 1 caractere | Identificador único do paciente |
| `current_note` | `string` | Mínimo 10 caracteres | Conteúdo textual da nota clínica a ser avaliada |

**Comportamento em payload inválido:** o `fastify-type-provider-zod` intercepta a validação do schema antes de o handler ser executado e retorna `400 Bad Request` automaticamente com os detalhes dos erros de validação.

---

## Contrato de Saída (Response)

### Resposta de Sucesso — 202 Accepted

Payload validado pelo schema `TriageAsyncResponseSchema`.

| Campo | Tipo | Valor | Descrição |
| :--- | :--- | :--- | :--- |
| `job_id` | `string` | UUIDv4 | Identificador único da tarefa assíncrona gerado pelo BFF |
| `status` | `string` | `'processing'` | Estado inicial do processamento da triagem |
| `message` | `string` | Ex.: `'Triagem iniciada com sucesso. Conecte ao canal SSE para receber os resultados.'` | Mensagem descritiva enviada ao cliente |

```json
{
  "job_id": "a3b8c9d0-1234-4567-89ab-cdef01234567",
  "status": "processing",
  "message": "Triagem iniciada com sucesso."
}
```

### Respostas de Erro

Todas as respostas de erro seguem o schema `ErrorResponseSchema` de `src/schemas/index.ts`.

| Código | Cenário | Campo `upstream` |
| :--- | :--- | :--- |
| 400 | Payload inválido (Zod validation failure) | ausente |
| 502 | Core inacessível / falha na chamada HTTP ao `/api/v1/triage/async` | `'psychnote-core'` |
| 504 | Timeout na requisição HTTP ao Core | `'psychnote-core'` |

---

## Fluxo de Execução

O arquivo `triage.route.ts` **DEVE** implementar o seguinte fluxo assíncrono:

```
1. Registrar rota POST /api/triage com schema de entrada TriageAsyncRequestSchema
2. Extrair { patient_id, current_note } do request.body
3. Gerar job_id via randomUUID() (crypto.randomUUID / UUIDv4)
4. Montar callback_url (ex.: `http://${BFF_HOST}:${BFF_PORT}/api/webhooks/triage-result`)
5. Criar AbortController com timeout curto para o aceite assíncrono (ex.: 5000ms)
6. Chamar coreClient.postTriageAsync({ job_id, patient_id, current_note, callback_url }, signal)
7. SE AbortError (timeout no aceite):
   - Retornar reply.code(504).send({
       statusCode: 504,
       error: 'Gateway Timeout',
       message: 'O serviço de IA não confirmou o recebimento da tarefa a tempo.',
       upstream: 'psychnote-core'
     })
8. SE FetchError / ECONNREFUSED / UpstreamError:
   - Retornar reply.code(502).send({
       statusCode: 502,
       error: 'Bad Gateway',
       message: 'Não foi possível registrar a triagem no serviço de IA.',
       upstream: 'psychnote-core'
     })
9. Retornar reply.code(202).send({
     job_id,
     status: 'processing',
     message: 'Triagem iniciada com sucesso.'
   })
```

---

## Logging Obrigatório

### O que DEVE ser logado

Os seguintes dados são seguros e obrigatórios para auditoria de execução:

- `job_id`, `patient_id` e timestamp de entrada da requisição
- Status de encaminhamento para o Core (`/api/v1/triage/async`)
- Código HTTP de resposta enviado ao MFE (`202 Accepted`)
- Em caso de falha: erro retornado ou causa de timeout sem stacktrace exposto ao cliente

### O que JAMAIS deve ser logado

Em estrita conformidade com a LGPD e políticas de privacidade de dados médicos:

- O texto contido em `current_note`
- Qualquer dado clínico sensível ou identificador direto do paciente fora do `patient_id` desidentificado

---

## Casos de Borda e Cenários de Teste

| Cenário | Input | Output Esperado |
| :--- | :--- | :--- |
| Submissão válida, Core aceita assincronamente | `patient_id` + `current_note` válidos | `202 Accepted` + `{ job_id, status: 'processing', message }` |
| `current_note` com menos de 10 caracteres | `current_note: 'curto'` | `400 Bad Request` |
| `patient_id` ausente ou vazio | `patient_id: ''` | `400 Bad Request` |
| Core indisponível no endpoint `/api/v1/triage/async` | `patient_id` + `current_note` válidos | `502 Bad Gateway` (upstream: 'psychnote-core') |
| Core demora > 5s para confirmar aceite HTTP 202 | `patient_id` + `current_note` válidos | `504 Gateway Timeout` (upstream: 'psychnote-core') |
