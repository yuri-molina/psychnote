---
type: Decision
title: "ADR-0005: Arquitetura Assíncrona Orientada a Eventos (HTTP 202 + Webhook Callback + SSE Stream)"
description: Decisão de migrar a comunicação de triagem de long-polling síncrono (60s) para o padrão HTTP 202 Accepted + Webhook Callback + Server-Sent Events (SSE), eliminando requisições pendentes e habilitando atualização em tempo real sem polling.
timestamp: 2026-08-08T18:38:00-03:00
status: active
version: 1.0.0
related:
  - ./0001-fastify-framework.md
  - ./0002-zod-contract-validation.md
  - ./0003-timeout-and-resilience.md
  - ../contracts/bff-api.md
  - ../contracts/core-api.md
---

# ADR-0005: Arquitetura Assíncrona Orientada a Eventos (HTTP 202 + Webhook Callback + SSE Stream)

## Contexto

A inferência do modelo LLM no `psychnote-core` (LangGraph + Ollama em CPU) possui latência média de 20 a 40 segundos por requisição. Na arquitetura inicial, o `psychnote-bff` mantinha uma conexão HTTP síncrona bloqueante aberta durante todo esse período (long-polling com timeout de 60s).

Essa abordagem síncrona apresentou limitações estruturais:
1. **Consumo Ineficiente de Recursos:** Handles TCP, sockets e conexões mantidas pendentes por até 60 segundos esgotam recursos do servidor sob requisições concorrentes.
2. **Sensibilidade a Timeouts do Browser/Proxy:** Redes locais, proxies reversos e browsers podem encerrar conexões HTTP de longa duração arbitrariamente (timeout de 30s por padrão em muitos proxies).
3. **Experiência do Usuário (UX):** A UI do frontend ficava aguardando uma única resposta HTTP síncrona sem visibilidade detalhada sobre o progresso ou a capacidade de desconectar e reconectar com resiliência.

## Decisão

Migrar a integração do `psychnote-bff` com o `psychnote-core` e o `psychnote-mfe` para uma **Arquitetura Assíncrona Orientada a Eventos em 3 Fases**:

```
FASE 1: Submissão e Aceite Imediato (HTTP 202)
MFE → BFF: POST /api/triage { patient_id, current_note }
BFF: Gera job_id (UUIDv4)
BFF → CORE: POST /api/v1/triage/async { job_id, patient_id, current_note, callback_url }
CORE → BFF: 202 Accepted { job_id, status: "processing" }
BFF → MFE: 202 Accepted { job_id, status: "processing" }

FASE 2: Conexão SSE de Baixo Consumo
MFE → BFF: GET /api/triage/stream/:jobId (EventSource)
BFF: Armazena a conexão no mapa activeSseConnections.set(jobId, reply)
BFF → MFE: HTTP 200 (text/event-stream, keep-alive, heartbeat 15s)

FASE 3: Conclusão, Persistência no ChromaDB e Push via Webhook
CORE: Executa pipeline LangGraph + persiste nota e triagem no ChromaDB
CORE → BFF: POST /api/webhooks/triage-result { job_id, patient_id, risk_assessment, audit_alerts, final_report }
BFF → CORE: 200 OK
BFF → MFE: Emite evento SSE "triage_completed" com payload completo
BFF: Encerra stream e remove do mapa
```

### Componentes Principais

1. **Geração de UUIDv4 (`job_id`):** O BFF gera um identificador único para cada requisição de triagem antes de encaminhar ao Core.
2. **Mapa de Conexões Ativas (`activeSseConnections`):** Mapa em memória (`Map<string, FastifyReply>`) mantido pelo BFF para vincular o `job_id` à resposta SSE do cliente.
3. **Endpoint de Webhook (`POST /api/webhooks/triage-result`):** Endpoint exposto pelo BFF para receber o callback assíncrono do Core quando a inferência e gravação no ChromaDB forem concluídas.
4. **SSE Stream (`GET /api/triage/stream/:jobId`):** Endpoint que expõe canal unidirecional HTTP streaming (`text/event-stream`) ao MFE com evento `triage_completed` e heartbeat a cada 15 segundos (`: heartbeat\n\n`).

## Alternativas Consideradas

* **Polling Curto (Short Polling):** MFE consultando `GET /api/triage/status/:jobId` a cada 3 segundos. Rejeitado por gerar sobrecarga desnecessária de requisições HTTP e tráfego de rede desnecessário.
* **WebSockets (`@fastify/websocket`):** Protocolo bidirecional full-duplex. Rejeitado por adicionar complexidade de handshake e gerenciamento de estado bidirecional desnecessário, uma vez que o fluxo de resultado de triagem é puramente unidirecional (servidor → cliente).
* **SSE Stream + Webhook (Escolha Final):** Padrão nativo do protocolo HTTP (`EventSource`), leve, compatível com proxies padrão e sem overhead de conexão bidirecional.

## Consequências

- O endpoint `POST /api/triage` responde em **menos de 10ms** com status `202 Accepted`.
- Nenhuma chamada HTTP fica bloqueada aguardando os 20-40s do pipeline do LLM.
- O BFF passa a expor o webhook `/api/webhooks/triage-result` e o endpoint SSE `/api/triage/stream/:jobId`.
- O histórico de triagens e prontuário sintético passa a ser consultado diretamente via `GET /api/patients/:id/history` (proxy para o Core/ChromaDB).
