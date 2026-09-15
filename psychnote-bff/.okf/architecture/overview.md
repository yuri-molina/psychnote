---
type: Architecture
title: Visão Geral da Arquitetura — psychnote-bff
description: Diagrama de containers C4, fluxo de sequência assíncrono em 3 fases (HTTP 202, SSE Stream, Webhook), stack tecnológica e responsabilidades do BFF.
timestamp: 2026-08-08T18:48:00-03:00
status: active
version: 1.1.0
related:
  - ./folder-structure.md
  - ../contracts/core-api.md
  - ../contracts/bff-api.md
  - ../decisions/0005-async-webhook-sse-architecture.md
  - ../domain/clinical-triage.md
---

# Visão Geral da Arquitetura — psychnote-bff

## 1. Diagrama de Containers (C4 Level 2)

```
Browser (localhost)
    |
    |  1. HTTP POST /api/triage (Aceite HTTP 202)
    |  2. SSE Stream GET /api/triage/stream/:jobId (EventSource)
    v
psychnote-mfe (React + Vite)       [consumidor]
    localhost:5001 (dev/preview)
    ^
    |  Server-Sent Events (triage_completed)
    |
psychnote-bff (Fastify + Node.js)  [este repositório]
    |                                 ^
    | 1. POST /api/v1/triage/async    | 2. POST /api/webhooks/triage-result
    v                                 |
psychnote-core (FastAPI + LangGraph) [backend de IA]
    |              |
    v              v
  Ollama        ChromaDB
  :11434        ./chroma_db
  llama3:8b     (local persistente)
```

O `psychnote-bff` atua como camada intermediária (Backend for Frontend) orientada a eventos. Suas funções incluem gerenciar o mapa de conexões SSE ativas (`activeSseConnections`), receber notificações via Webhook do `psychnote-core` e retransmitir em tempo real para o `psychnote-mfe`. O BFF não possui banco de dados próprio, não renderiza views HTML e não executa inferência de IA.

---

## 2. Responsabilidades do BFF

- Expor `POST /api/triage` para submissão assíncrona pelo MFE (retorna HTTP 202 com `job_id`).
- Expor `GET /api/triage/stream/:jobId` para abertura de conexão SSE pelo MFE (`EventSource`).
- Gerenciar em memória o mapa de conexões SSE ativas: `activeSseConnections` (`Map<jobId, FastifyReply>`).
- Enviar Heartbeats periódicos (a cada 15s) no canal SSE para impedir timeouts de conexão.
- Expor `POST /api/webhooks/triage-result` para recepção do resultado do `psychnote-core`.
- Repassar o resultado do Webhook para o canal SSE correspondente via evento `triage_completed`.
- Expor `GET /patients` e `GET /patients/:id/record` (histórico) para o MFE.
- Expor `GET /health` para verificação de saúde do serviço.
- Configurar CORS para aceitar origens permitidas (`http://localhost:5001`).
- Configurar HTTP Security Headers via `@fastify/helmet`.
- Validar contratos de entrada e saída com Zod (`fastify-type-provider-zod`).
- Interceptar falhas e garantir execução **crash-free**.
- **NÃO** possui banco de dados, **NÃO** renderiza views, **NÃO** executa inferência de IA.

---

## 3. Stack Tecnológica do BFF

| Camada | Tecnologia | Versão Alvo | Observação |
| :--- | :--- | :--- | :--- |
| Runtime | Node.js | ^20.x LTS | Suporte nativo a `Map`, `AbortController` e SSE |
| Framework HTTP | Fastify | ^5.x | Alta performance, suporte nativo a streaming |
| Validação de Schema | Zod + `fastify-type-provider-zod` | ^3.x / ^3.x | Validação de request, response e webhooks |
| HTTP Client | Undici / fetch nativo | nativo Node.js | Integração assíncrona com o Core |
| Event Streaming | Server-Sent Events (SSE) | HTTP/1.1 standard | Transferência unidirecional Servidor → Cliente |
| Segurança CORS | `@fastify/cors` | latest | Libera exclusivamente `localhost:5001` |
| Segurança HTTP Headers | `@fastify/helmet` | latest | HTTP Security Headers obrigatórios |
| Logging | Pino (nativo do Fastify) | nativo | JSON logging estruturado com `job_id` |

---

## 4. Diagrama de Sequência e Fluxo de Dados Assíncrono (3 Fases)

```mermaid
sequenceDiagram
    autonumber
    actor Medico as Médico (MFE)
    participant MFE as psychnote-mfe (Porta 5001)
    participant BFF as psychnote-bff (Porta 4000)
    participant CORE as psychnote-core (Porta 8000)
    participant DB as ChromaDB (Local)

    Note over Medico, DB: FASE 1: Submissão e Aceite Imediato (HTTP 202)
    Medico->>MFE: Clica em "Avaliar Risco com IA"
    MFE->>BFF: POST /api/triage { patient_id, current_note }
    BFF->>BFF: Gera job_id (UUIDv4)
    BFF->>CORE: POST /api/v1/triage/async { job_id, patient_id, current_note, callback_url }
    CORE-->>BFF: 202 Accepted { job_id, status: "processing" }
    BFF-->>MFE: 202 Accepted { job_id, status: "processing" }

    Note over Medico, DB: FASE 2: Conexão SSE de Baixo Consumo
    MFE->>MFE: Ativa Skeleton Loader ("Triagem em Andamento")
    MFE->>BFF: GET /api/triage/stream/:jobId (EventSource)
    BFF->>BFF: Registra em activeSseConnections.set(jobId, reply)
    BFF-->>MFE: 200 OK (Connection: keep-alive, Text/Event-Stream)
    loop Heartbeat a cada 15s
        BFF-->>MFE: : heartbeat\n\n
    end

    Note over Medico, DB: FASE 3: Conclusão, Persistência e Push
    CORE->>CORE: Executa LangGraph em Background (~20-40s)
    CORE->>DB: Salva Nota + Metadados de Triagem no ChromaDB
    CORE->>BFF: POST /api/webhooks/triage-result { job_id, patient_id, risk_assessment, audit_alerts, final_report }
    BFF-->>CORE: 200 OK
    BFF->>BFF: Busca reply em activeSseConnections.get(job_id)
    BFF->>MFE: Emite Evento SSE "triage_completed" { payload }
    BFF->>BFF: Limpa activeSseConnections.delete(job_id) e encerra streaming
    MFE->>MFE: Renderiza Badges e Auditoria na UI
    MFE->>BFF: Fecha Conexão SSE (EventSource.close())
```

---

## 5. Restrições e Premissas Inegociáveis

- **Comunicação Assíncrona:** Toda submissão de triagem deve responder HTTP 202 imediatamente. Nenhuma chamada de triagem deve segurar conexões síncronas de longa duração.
- **Gerenciamento Seguro do Mapa de Conexões:** O registro em `activeSseConnections` deve ser estritamente removido após o envio do evento final ou caso o cliente feche a conexão (evento `close` do socket), evitando memory leaks.
- **Separação de responsabilidades de IA:** O BFF não chama o Ollama ou ChromaDB diretamente. Toda a inteligência e persistência vetorial permanecem no Core.
- **Sem persistência de dados clínicos no BFF:** O BFF não persiste notas ou resultados em banco de dados. Os dados em trânsito são mantidos temporariamente apenas nos sockets ativos.
- **Resiliência e Crash-Free:** O processo Node.js do BFF nunca deve encerrar por exceções causadas por desconexões de SSE ou payloads malformados de Webhook.

