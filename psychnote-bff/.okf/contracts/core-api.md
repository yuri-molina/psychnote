---
type: Contract
title: Contrato da API psychnote-core (FastAPI) — Perspectiva do BFF
description: Endpoints, payloads, schemas e comportamentos da API do psychnote-core que o BFF consome, incluindo endpoints assíncronos e webhooks. Fonte de verdade para a camada de integração do BFF com o Core.
timestamp: 2026-08-08T18:50:00-03:00
status: active
version: 2.0.0
resource: ../../../psychnote-core/src/api/v1/triage.py
related:
  - ./bff-api.md
  - ../decisions/0002-zod-contract-validation.md
  - ../domain/clinical-triage.md
---

# Contrato da API psychnote-core (FastAPI) — Perspectiva do BFF

## Visão Geral

Este documento descreve a interface da API REST do **psychnote-core** da perspectiva do BFF. É a fonte de verdade para toda lógica de integração: URLs, schemas, comportamentos de erro, chamadas assíncronas (HTTP 202 + Webhook) e consulta de histórico persistido no ChromaDB.

- **Base URL:** `http://localhost:8000`
- **Documentação Swagger:** `http://localhost:8000/docs`
- **Framework:** FastAPI (Python)

---

## Endpoints

### GET /health — Health Check

Verifica a disponibilidade do serviço Core. **Não aciona o LLM.**

**Response 200:**

```json
{
  "status": "ok",
  "service": "PsicRE-AI",
  "version": "0.1.0-poc"
}
```

---

### POST /api/v1/triage/async — Triagem de Risco Assíncrona

Inicia o processamento assíncrono do pipeline de triagem clínica via LangGraph + Ollama. O Core aceita a requisição imediatamente (202 Accepted) e processa a análise em background, enviando o resultado final via Webhook para a `callback_url` informada.

- **Content-Type:** `application/json`

#### Request Body — `TriageAsyncRequest`

| Campo          | Tipo   | Obrigatório | Restrições                           | Exemplo                                        |
|----------------|--------|-------------|--------------------------------------|------------------------------------------------|
| `job_id`       | string | sim         | UUIDv4 válido                        | `"a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"`       |
| `patient_id`   | string | sim         | não-vazio                            | `"PAC-010"`                                    |
| `current_note` | string | sim         | mínimo 10 caracteres                 | `"Paciente relata..."`                         |
| `callback_url` | string | sim         | URL válida do webhook exposto no BFF | `"http://localhost:4000/api/webhooks/triage-result"` |

**Exemplo de Request:**

```json
{
  "job_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "patient_id": "PAC-010",
  "current_note": "Paciente relata pensamentos de que seria melhor não estar aqui. Verbaliza sentimentos de inutilidade e desesperança persistentes há duas semanas.",
  "callback_url": "http://localhost:4000/api/webhooks/triage-result"
}
```

#### Response Body 202 Accepted

| Campo     | Tipo   | Descrição                                         | Exemplo        |
|-----------|--------|---------------------------------------------------|----------------|
| `job_id`  | string | Identificador único do job de triagem (UUIDv4)    | `"a1b2c3d4..."`|
| `status`  | string | Status inicial da solicitação (`"processing"`)     | `"processing"` |
| `message` | string | Mensagem descritiva do recebimento para execução | `"Triage job accepted for asynchronous processing"` |

**Exemplo de Response 202:**

```json
{
  "job_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "status": "processing",
  "message": "Triage job accepted for asynchronous processing"
}
```

---

### POST /api/webhooks/triage-result — Callback de Resultado da Triagem (Notificação do Core ao BFF)

Endpoint HTTP exposto pelo BFF e invocado pelo `psychnote-core` após a conclusão da execução do LangGraph em background. Transmite o resultado final da triagem clínica e a confirmação da gravação vetorial no ChromaDB.

- **Sender:** `psychnote-core`
- **Receiver:** `psychnote-bff`
- **Content-Type:** `application/json`

#### Request Body (Payload enviado pelo Core)

| Campo             | Tipo     | Descrição                                                                      |
|-------------------|----------|--------------------------------------------------------------------------------|
| `job_id`          | string   | Identificador único do job (UUIDv4)                                           |
| `patient_id`      | string   | Identificador do paciente                                                      |
| `status`          | string   | Estado do processamento (`"completed"` ou `"failed"`)                          |
| `risk_assessment` | objeto   | Avaliação estruturada de risco clínico                                         |
| `audit_alerts`    | string[] | Alertas de auditoria de conduta clínica gerados                                |
| `final_report`    | string   | Parecer clínico completo sintetizado pelo LLM                                  |

**Estrutura de `risk_assessment`:**

| Campo                    | Tipo                                                  | Descrição                               |
|--------------------------|-------------------------------------------------------|-----------------------------------------|
| `risk_level`             | enum: `'Baixo'` \| `'Moderado'` \| `'Alto/Iminente'` | Nível de risco classificado pelo LLM    |
| `passive_ideation`       | boolean                                               | Presença de ideação passiva de suicídio |
| `active_ideation`        | boolean                                               | Presença de ideação ativa de suicídio   |
| `red_flags`              | string[]                                              | Fatores de risco identificados          |
| `protection_factors`     | string[]                                              | Fatores de proteção identificados       |
| `clinical_justification` | string                                                | Justificativa clínica da classificação  |

**Exemplo de Webhook Payload (Core → BFF):**

```json
{
  "job_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "patient_id": "PAC-010",
  "status": "completed",
  "risk_assessment": {
    "risk_level": "Alto/Iminente",
    "passive_ideation": true,
    "active_ideation": false,
    "red_flags": [
      "Verbalização de desejo de não existir",
      "Desesperança persistente há duas semanas",
      "Sentimentos de inutilidade"
    ],
    "protection_factors": [
      "Vínculo terapêutico estabelecido",
      "Ausência de plano ou meio identificado"
    ],
    "clinical_justification": "A presença de ideação passiva com desesperança persistente configura risco alto, exigindo avaliação presencial urgente."
  },
  "audit_alerts": [
    "Ideação suicida verbalizada — registrar em prontuário",
    "Considerar contato com familiar responsável conforme protocolo institucional"
  ],
  "final_report": "Paciente PAC-010 apresenta quadro de risco Alto/Iminente com base na nota clínica analisada."
}
```

#### Response Body 200 OK (Retornado pelo BFF ao Core)

```json
{
  "status": "success",
  "message": "Webhook processed and SSE notification dispatched successfully"
}
```

---

### GET /api/v1/patients/{patient_id}/history — Consulta de Histórico no ChromaDB

Recupera o histórico completo de notas clínicas e triagens prévias do paciente armazenadas no banco vetorial **ChromaDB** gerido pelo Core.

- **Query / Path Parameter:** `patient_id` (string, ex: `"PAC-010"`)

#### Response Body 200 OK

Array de registros de triagens históricas do paciente ordenados cronologicamente.

| Campo             | Tipo     | Descrição                                              |
|-------------------|----------|--------------------------------------------------------|
| `triage_id`       | string   | Identificador do registro de triagem                    |
| `patient_id`      | string   | Identificador do paciente                              |
| `created_at`      | string   | Data/hora ISO-8601 da realização da triagem            |
| `current_note`    | string   | Texto da nota clínica original submetida               |
| `risk_assessment` | objeto   | Objeto com `risk_level`, `red_flags`, `justification`  |
| `audit_alerts`    | string[] | Lista de alertas emitidos no momento da triagem        |
| `final_report`    | string   | Parecer gerado pelo modelo                             |

**Exemplo de Response 200:**

```json
{
  "patient_id": "PAC-010",
  "total_records": 1,
  "history": [
    {
      "triage_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
      "patient_id": "PAC-010",
      "created_at": "2026-08-08T18:30:00Z",
      "current_note": "Paciente relata pensamentos de que seria melhor não estar aqui...",
      "risk_assessment": {
        "risk_level": "Alto/Iminente",
        "passive_ideation": true,
        "active_ideation": false,
        "red_flags": ["Verbalização de desejo de não existir"],
        "protection_factors": ["Vínculo terapêutico estabelecido"],
        "clinical_justification": "A presença de ideação passiva com desesperança persistente..."
      },
      "audit_alerts": [
        "Ideação suicida verbalizada — registrar em prontuário"
      ],
      "final_report": "Paciente PAC-010 apresenta quadro de risco Alto/Iminente..."
    }
  ]
}
```

---

### POST /api/v1/triage/ — Triagem de Risco (Legado Síncrono)

> **Nota:** Mantido para retrocompatibilidade. Em novos fluxos, utilizar `POST /api/v1/triage/async`.

Executa o pipeline síncrono de triagem clínica via LangGraph + Ollama com latência estimada de 30-45s (Timeout de 60s).

---

## Respostas de Erro do Core

| Código HTTP | Causa                                                                 |
|-------------|-----------------------------------------------------------------------|
| `400`       | Body inválido ou ausência de parâmetros obrigatórios                  |
| `422`       | `current_note` com menos de 10 caracteres ou `patient_id` ausente     |
| `422`       | Pipeline retornou avaliação de risco vazia (falha de parsing do LLM)  |
| `500`       | Falha interna no pipeline LangGraph (ex: Ollama inacessível/ChromaDB) |

---

## Arquitetura Assíncrona e Performance

O Core utiliza processamento assíncrono em segundo plano para desonerar a conexão do cliente:

| Característica         | Valor                                                      |
|------------------------|------------------------------------------------------------|
| Modo de Aceite         | Assíncrono (HTTP 202 Accepted imediato)                    |
| Notificação            | Webhook POST para `callback_url` do BFF                    |
| Persistência           | Armazenamento automático de embeddings e parecer no ChromaDB|
| Tempo de Resposta 202  | < 50ms                                                     |
| Tempo de Grafo (LLM)   | 20-40 segundos em background                               |
