---
type: Decision
title: "ADR-0003: Gestão de Timeout e Resiliência a Falhas do Core"
description: Decisão de implementar timeout de 60 segundos via AbortController e tratamento crash-free de falhas do Core, retornando payloads de erro estruturados ao MFE.
timestamp: 2026-08-07T16:55:00-03:00
status: active
version: 1.0.0
related:
  - ./0002-zod-contract-validation.md
  - ../architecture/overview.md
---

## Contexto

O pipeline de IA do Core (LangGraph + Ollama) tem latência medida de ~32–45 segundos em CPU. Em condições de carga elevada ou falha de hardware, o Core pode não responder. Sem tratamento explícito, três categorias de falha podem derrubar o BFF:

1. **Timeout:** O Core não responde dentro do tempo esperado. A conexão TCP fica pendente indefinidamente.
2. **Falha de rede:** O Core está inacessível (`ECONNREFUSED`, `ENOTFOUND`, etc.).
3. **JSON malformado:** O Core responde com HTTP 200 mas o body não é um JSON válido, ou o JSON não respeita o schema esperado.

Em todos esses casos, uma exceção não capturada em uma Promise rejeitada pode crashar o processo Node.js.

## Decisão

**Timeout (60 segundos):** Toda chamada HTTP ao Core será criada com `AbortController` e `AbortSignal.timeout(60_000)`. Se o Core não responder em 60s, a conexão é abortada e o BFF retorna `504 Gateway Timeout`.

**Falha de rede / ECONNREFUSED:** Capturada por `try/catch` no handler de rota ou no plugin `core-client`. Retorna `502 Bad Gateway` com mensagem descritiva.

**JSON malformado / Zod falhou:** Capturado pela validação `safeParse` do Zod após `response.json()`. Se `success === false`, retorna `502 Bad Gateway` com `message: 'Contrato violado pelo Core'`.

**Payload de Erro Padronizado:**

```typescript
// Retornado em todos os cenários de falha de upstream
{
  statusCode: 502 | 504,
  error: 'Bad Gateway' | 'Gateway Timeout',
  message: string,  // Descrição human-readable do erro
  upstream: 'psychnote-core'
}
```

**Crash-free:** O plugin `error-handler` deve registrar um hook `setErrorHandler` no Fastify que captura qualquer exceção não tratada nas rotas e a converte em resposta HTTP estruturada. O processo Node.js não deve nunca terminar por erro de runtime oriundo de falhas do Core.

## Alternativas Consideradas

**Sem timeout:** Requisições ao Core pendentes consumiriam handles TCP indefinidamente. Em carga concorrente, esgotaria os recursos do processo.

**Axios com timeout global:** Axios adiciona ~45 KB ao bundle e tem API de cancelamento mais verbosa que `AbortController` nativo. Undici ou `fetch` nativo do Node.js são preferíveis para um BFF lean.

## Consequências

- O valor de 60 segundos é fixo no código. A latência máxima medida do Core é ~43s; 60s oferece margem de segurança sem penalizar a experiência do usuário com esperas excessivas.
- O MFE deve implementar timeout próprio (recomendado: 70s) para exibir mensagem de erro antes que o BFF atinja seu limite.
- Não há retry automático no BFF. Em caso de falha, o MFE deve permitir que o usuário re-submeta a requisição.
