---
type: Playbook
title: Configuração e Execução Local — psychnote-bff
description: Passo a passo para instalar dependências, configurar variáveis de ambiente, rodar o BFF em modo de desenvolvimento e testar o fluxo assíncrono completo via cURL.
timestamp: 2026-08-08T18:50:00-03:00
status: active
version: 2.0.0
related:
  - ../architecture/overview.md
  - ../contracts/core-api.md
  - ../contracts/bff-api.md
---

# Configuração e Execução Local — psychnote-bff

## Pré-requisitos

Antes de iniciar, confirme que os seguintes componentes estão disponíveis:

| Ferramenta              | Versão Mínima | Como verificar                          |
|-------------------------|---------------|-----------------------------------------|
| Node.js                 | 20.x LTS      | `node --version`                        |
| npm                     | 10.x          | `npm --version`                         |
| psychnote-core rodando  | qualquer      | `curl http://localhost:8000/health`     |

---

## Passo 1: Instalar Dependências

Na raiz do repositório `psychnote-bff`, execute:

```bash
npm install
```

---

## Passo 2: Configurar Variáveis de Ambiente

Copie o arquivo de exemplo para criar o `.env` local:

```bash
cp .env.example .env
```

Conteúdo esperado do `.env`:

```env
PORT=4000
CORE_URL=http://localhost:8000
CORE_TIMEOUT_MS=60000
CORS_ORIGINS=http://localhost:5001
NODE_ENV=development
```

| Variável          | Descrição                                                             |
|-------------------|-----------------------------------------------------------------------|
| `PORT`            | Porta em que o BFF irá escutar                                        |
| `CORE_URL`        | URL base do psychnote-core                                            |
| `CORE_TIMEOUT_MS` | Timeout do cliente HTTP para o Core, em milissegundos (mínimo 60000) |
| `CORS_ORIGINS`    | Origem(ns) permitida(s) para o MFE                                    |
| `NODE_ENV`        | Modo de execução (`development` habilita logs detalhados)             |

---

## Passo 3: Rodar em Modo de Desenvolvimento

```bash
npm run dev
```

O BFF estará disponível em `http://localhost:4000`. O modo de desenvolvimento utiliza `tsx watch`, que monitora alterações nos arquivos TypeScript e reinicia o servidor automaticamente (hot-reload).

---

## Passo 4: Verificar Saúde do BFF

```bash
curl http://localhost:4000/health
# Esperado: {"status":"ok","service":"psychnote-bff","version":"1.0.0"}
```

---

## Passo 5: Testar o Fluxo Assíncrono Completo via cURL

O fluxo assíncrono envolve submissão (HTTP 202), escuta de eventos SSE pelo MFE e notificação via Webhook.

### 5.1. Submissão da Triagem (MFE → BFF)

Submeta a nota clínica para processamento assíncrono:

```bash
curl -X POST http://localhost:4000/api/triage \
  -H 'Content-Type: application/json' \
  -d '{
    "patient_id": "PAC-010",
    "current_note": "Paciente relata pensamentos de que seria melhor não estar aqui. Verbaliza sentimentos de inutilidade e desesperança persistentes há duas semanas."
  }'
```

**Resposta Esperada (202 Accepted):**
```json
{
  "job_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "status": "processing",
  "message": "Triagem aceita para processamento assíncrono."
}
```

Copie o `job_id` retornado para os passos seguintes.

---

### 5.2. Escuta do Canal SSE (MFE → BFF)

Em um terminal separado (ou background), abra a conexão SSE apontando para o `job_id`:

```bash
curl -N -H "Accept: text/event-stream" http://localhost:4000/api/triage/stream/a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d
```

O cURL permanecerá escutando. A cada 15 segundos você verá batimentos de coração (`: heartbeat`).

---

### 5.3. Simulação do Webhook de Conclusão (Core → BFF)

Em outro terminal, simule o callback de conclusão que o `psychnote-core` enviaria ao BFF após terminar a inferência do LLM e salvar no ChromaDB:

```bash
curl -X POST http://localhost:4000/api/webhooks/triage-result \
  -H 'Content-Type: application/json' \
  -d '{
    "job_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "patient_id": "PAC-010",
    "status": "completed",
    "risk_assessment": {
      "risk_level": "Alto/Iminente",
      "passive_ideation": true,
      "active_ideation": false,
      "red_flags": [
        "Verbalização de desejo de não existir",
        "Desesperança persistente há duas semanas"
      ],
      "protection_factors": [
        "Vínculo terapêutico estabelecido"
      ],
      "clinical_justification": "A presença de ideação passiva com desesperança persistente configura risco alto."
    },
    "audit_alerts": [
      "Ideação suicida verbalizada — registrar em prontuário"
    ],
    "final_report": "Paciente PAC-010 apresenta quadro de risco Alto/Iminente com base na nota clínica analisada."
  }'
```

**Resultado Esperado:**
1. A chamada ao Webhook retorna `200 OK`: `{"status":"success","message":"Webhook processed and SSE notification dispatched successfully"}`.
2. No terminal onde o SSE do cURL estava rodando (passo 5.2), o evento `triage_completed` será impresso e a conexão será encerrada:
   ```http
   event: triage_completed
   data: {"job_id":"a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d", ...}
   ```

---

### 5.4. Consulta de Histórico no ChromaDB

Para validar a consulta do histórico armazenado no Core/ChromaDB via BFF:

```bash
curl http://localhost:4000/api/patients/PAC-010/history
```

---

## Verificação do Ambiente e Diagnóstico

Caso algo não funcione como esperado, use a tabela abaixo para diagnóstico:

| Sintoma                      | Causa provável                                             | Ação                                                                 |
|------------------------------|------------------------------------------------------------|----------------------------------------------------------------------|
| BFF retorna `502`            | psychnote-core não está rodando em `localhost:8000`        | Iniciar o Core e verificar com `curl http://localhost:8000/health`   |
| SSE não recebe evento        | `job_id` no cURL SSE diverge do `job_id` do webhook         | Garantir uso do mesmo UUIDv4 na escuta e na simulação               |
| BFF não sobe (`EADDRINUSE`)   | Porta 4000 já está em uso por outro processo             | Identificar e encerrar o processo com `lsof -i :4000` ou mudar `PORT` |
| Webhook retorna `404`        | `job_id` não encontrado no mapa de conexões ativas        | Garantir que o passo 5.2 (conexão SSE) esteja ativo antes de chamar o webhook |
