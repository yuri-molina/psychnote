---
type: ModuleSpec
title: Spec — Plugin CoreClient
description: Especificação do plugin Fastify que encapsula a comunicação HTTP síncrona e assíncrona com o psychnote-core. Inclui suporte a submissão assíncrona de triagem e consulta de histórico no ChromaDB.
timestamp: 2026-08-08T18:48:00-03:00
status: active
version: 2.0.0
resource: ./core-client.plugin.ts
related:
  - ../../../.okf/decisions/0003-timeout-and-resilience.md
  - ../../../.okf/decisions/0005-async-webhook-sse-architecture.md
  - ../../../.okf/contracts/core-api.md
---

# Spec — Plugin CoreClient

## Responsabilidade Única

O plugin `CoreClient` encapsula **TODA** a comunicação HTTP com o `psychnote-core`. Nenhuma rota do BFF deve importar `fetch` ou bibliotecas de transporte HTTP diretamente — devem utilizar exclusivamente a instância `fastify.coreClient`.

Nesta versão, o `CoreClient` passa a suportar:
1. Submissão assíncrona de triagem (`postTriageAsync`).
2. Consulta de histórico de pacientes persistido no ChromaDB (`getPatientHistory`).
3. Manutenção de compatibilidade com chamadas legado e health check (`postTriage`, `getHealth`).

---

## Interface Pública (API do Plugin)

O plugin **DEVE** decorar a instância do Fastify com a propriedade `coreClient`, expondo a seguinte interface:

```typescript
export interface TriageAsyncCorePayload {
  job_id: string;
  patient_id: string;
  current_note: string;
  callback_url: string;
}

export interface CoreClient {
  postTriageAsync(payload: TriageAsyncCorePayload, signal?: AbortSignal): Promise<unknown>;
  getPatientHistory(patientId: string, signal?: AbortSignal): Promise<unknown>;
  postTriage(payload: TriageRequest, signal?: AbortSignal): Promise<unknown>;
  getHealth(): Promise<{ status: string }>;
}
```

| Método | Endpoint Core Consumido | Descrição |
| :--- | :--- | :--- |
| `postTriageAsync` | `POST /api/v1/triage/async` | Envia nota clínica, job_id e callback_url para aceite assíncrono (retorna 202 do Core) |
| `getPatientHistory` | `GET /api/v1/patients/:id/history` | Consulta histórico de triagens do paciente vetorizadas no ChromaDB pelo Core |
| `postTriage` | `POST /api/v1/triage/` | Envia triagem síncrona (legado / fallback) |
| `getHealth` | `GET /health` | Verifica a integridade e conectividade do Core |

---

## Implementação Esperada dos Novos Métodos

### 1. `postTriageAsync`

```
1. Montar a URL de destino: `${CORE_URL}/api/v1/triage/async`
2. Criar AbortSignal com timeout padrão (ex.: 5000ms se signal não fornecido)
3. Executar fetch HTTP POST com headers 'Content-Type: application/json' e body JSON.stringify(payload)
4. SE AbortError: lançar UpstreamTimeoutError('Timeout na confirmação assíncrona pelo Core')
5. SE Erro de Conexão (ECONNREFUSED / TypeError): lançar UpstreamUnavailableError('Core inacessível')
6. SE response.ok === false (status != 202 e status != 200):
   lançar UpstreamError com o statusCode e corpo retornado pelo Core
7. Retornar response.json() como unknown
```

### 2. `getPatientHistory`

```
1. Montar a URL de destino: `${CORE_URL}/api/v1/patients/${encodeURIComponent(patientId)}/history`
2. Criar AbortSignal com timeout (ex.: 10000ms se signal não fornecido)
3. Executar fetch HTTP GET
4. SE AbortError: lançar UpstreamTimeoutError('Timeout ao consultar histórico do paciente')
5. SE Erro de Conexão: lançar UpstreamUnavailableError('Core inacessível')
6. SE response.status === 404: lançar erro com status 404
7. SE response.ok === false: lançar UpstreamError com o statusCode correspondente
8. Retornar response.json() como unknown
```

---

## Configuração via Variáveis de Ambiente

| Variável | Descrição | Valor Padrão |
| :--- | :--- | :--- |
| `CORE_URL` | URL base do `psychnote-core`, sem barra final | `http://localhost:8000` |
| `CORE_TIMEOUT_MS` | Tempo máximo de espera padrão por resposta do Core (ms) | `60000` |
| `CORE_ASYNC_TIMEOUT_MS` | Tempo máximo de espera para confirmação de aceite (ms) | `5000` |

---

## Erros Customizados Lançados

| Classe de Erro | Condição de Disparo |
| :--- | :--- |
| `UpstreamTimeoutError` | O disparo do `AbortController` cancela a requisição por atingir o limite de tempo |
| `UpstreamUnavailableError` | Falha de resolução DNS, `ECONNREFUSED` ou falha de socket antes de receber resposta HTTP |
| `UpstreamError` | O Core respondeu com código de status HTTP fora da faixa de sucesso (`4xx` ou `5xx`) |

Estas exceções são tratadas pelo plugin `ErrorHandler` ou capturadas nos handlers de rota para conversão em respostas de erro formatadas.
