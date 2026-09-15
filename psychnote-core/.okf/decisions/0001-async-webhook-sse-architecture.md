---
type: ADR
title: ADR 001 — Adoção de Arquitetura Assíncrona via HTTP 202, Webhook e Persistência no ChromaDB
description: Registro da decisão de arquitetura para desacoplar a inferência LLM síncrona através de Webhooks e Server-Sent Events.
timestamp: 2026-08-08T18:38:00-03:00
status: accepted
version: 1.0.0
owner: psychnote-core
---

# ADR 001 — Adoção de Arquitetura Assíncrona via HTTP 202, Webhook e Persistência no ChromaDB

## Contexto e Problema
Na versão síncrona da PoC, a chamada para `POST /api/v1/triage/` mantinha a conexão HTTP aberta por aproximadamente 20 a 40 segundos enquanto o LLM Ollama processava a inferência em CPU local. Isso gerava problemas de timeout no Gateway/BFF, experiência ruim no frontend MFE e falta de persistência dos resultados da triagem estruturada no banco de dados vetorial (as notas eram armazenadas brutas, sem a triagem agregada).

## Decisão
1. **Endpoint Assíncrono (`POST /api/v1/triage/async`):** Responder de forma imediata com HTTP `202 Accepted` contendo um `job_id`, delegando a execução do LangGraph para uma `BackgroundTask` assíncrona do FastAPI.
2. **Notificação por Webhook HTTP POST:** Ao término da inferência e da gravação no banco, o `psychnote-core` faz um callback HTTP POST para a URL fornecida pelo `psychnote-bff`.
3. **Persistência de Triagens nos Metadados do ChromaDB:** Salvar a nota clínica juntamente com os metadados da triagem (`risk_level`, `red_flags`, `audit_alerts`, `final_report`) no banco vetorial.
4. **Consulta Direta de Histórico (`GET /api/v1/patients/{id}/history`):** Permitir a leitura rápida de históricos pré-triados sem acionar novamente a inferência LLM.

## Consequências
- **Positivas:**
  - Elimina timeouts HTTP no BFF e MFE.
  - Reduz drasticamente a latência de leitura do histórico de pacientes (de 30s para < 50ms).
  - Garante reatividade em tempo real na interface React via Server-Sent Events (SSE).
- **Negativas / Riscos Mitigados:**
  - Requer tratamento de erros e retentativas na chamada do Webhook caso o BFF fique inatingível (mitigado com try/except e logs auditáveis no Core).
