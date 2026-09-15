# GEMINI.md — psychnote-bff

> **Para Gemini / Antigravity CLI:** Este arquivo é seu sistema de onboarding obrigatório. Leia-o **integralmente** antes de qualquer ação. Cada seção é um filtro de decisão, não uma sugestão.

---

## Identidade do Repositório

`psychnote-bff` é um **roteador e gerenciador de eventos em tempo real** (Backend for Frontend) na arquitetura `MFE → BFF → Core` do projeto PsicRE-AI — uma plataforma Edge AI de triagem de risco de suicídio em prontuários psiquiátricos, operando 100% localmente (LGPD).

O BFF **não** possui banco de dados, **não** renderiza views e **não** executa inferência de IA. É um intermediário entre o `psychnote-mfe` (React, porta 5001) e o `psychnote-core` (FastAPI + LangGraph, porta 8000). Suas funções principais são:
1. Receber requisições do MFE em `POST /api/triage`, gerar um `job_id` (UUIDv4) e responder imediatamente com HTTP `202 Accepted`.
2. Repassar a requisição assíncrona ao Core (`POST /api/v1/triage/async`) fornecendo a URL do Webhook.
3. Manter conexões SSE abertas em `GET /api/triage/stream/:jobId` (`Map<jobId, FastifyReply>`).
4. Receber callbacks de conclusão do Core via `POST /api/webhooks/triage-result`, validar com Zod e notificar o MFE via SSE.

**Stack obrigatório:**
- Runtime: Node.js 20 LTS
- Framework HTTP: Fastify 5 + `fastify-type-provider-zod`
- Validação: Zod (bidirecional — entrada do MFE, resposta 202 e callback Webhook)
- Realtime: Server-Sent Events (SSE) com heartbeat a cada 15s
- Segurança: `@fastify/cors` + `@fastify/helmet` (obrigatórios, antes das rotas)
- HTTP Client: Undici / Node Fetch nativo com `AbortController`
- Logging: Pino (nativo do Fastify) — JSON estruturado, sem dados clínicos
- TypeScript: `strict: true` — `any` é proibido

---

## Protocolo de Onboarding Obrigatório

> Execute este protocolo **antes de escrever qualquer código**. Não é opcional.

### Passo 1 — Oriente-se na base de conhecimento
```
Leia: .okf/index.md
```
Este arquivo é o mapa. Ele lista todos os artefatos OKF (arquitetura, contratos, decisões, domínio) e as specs SDD co-localizadas em `src/`. Localize aqui o artefato relevante para a sua tarefa.

### Passo 2 — Entenda a arquitetura
```
Leia: .okf/architecture/overview.md
```
Contém o diagrama de sequência do fluxo assíncrono (HTTP 202 + SSE + Webhook), as responsabilidades do BFF, o gerenciamento de sockets SSE e os caminhos de resiliência.

### Passo 3 — Leia a spec SDD da rota/módulo que você vai tocar

| Se você vai implementar... | Leia esta spec |
| :--- | :--- |
| `POST /api/triage` | `src/routes/triage/triage.spec.md` |
| `GET /api/triage/stream/:jobId` | `src/routes/stream/stream.spec.md` |
| `POST /api/webhooks/triage-result` | `src/routes/webhook/webhook.spec.md` |
| `GET /patients` e `GET /patients/:id/history` | `src/routes/patients/patients.spec.md` |
| Plugin de HTTP client para o Core | `src/plugins/core-client/CoreClient.spec.md` |
| Plugin de tratamento de erros | `src/plugins/error-handler/ErrorHandler.spec.md` |

### Passo 4 — Confirme o contrato de API
```
Leia: .okf/contracts/bff-api.md   (endpoints HTTP 202, SSE e History expostos ao MFE)
Leia: .okf/contracts/core-api.md  (POST /api/v1/triage/async e Webhook /api/webhooks/triage-result)
```

### Passo 5 — Consulte o ADR relevante antes de decisões de design

```
.okf/decisions/0001-fastify-framework.md               → Fastify vs Express vs Hono
.okf/decisions/0002-zod-contract-validation.md         → Validação bidirecional com Zod
.okf/decisions/0003-timeout-and-resilience.md          → AbortController, crash-free, 502/504
.okf/decisions/0004-cors-and-helmet.md                 → CORS restrito a localhost:5001, Helmet
.okf/decisions/0005-async-webhook-sse-architecture.md  → Submissão assíncrona 202 + Webhook + SSE
```

---

## Como Pensar Antes de Agir

**1. Declare suas premissas antes de codificar.**
Antes de escrever qualquer linha de código, escreva em texto:
- Qual spec SDD você leu
- Qual ADR é relevante
- O que você vai alterar (e o que vai deixar intocado)
- Se há alguma ambiguidade — e se há, pare e pergunte

**2. Simplicidade cirúrgica.**
Implemente o mínimo necessário para satisfazer a spec. Não adicione abstrações, generalizações ou "melhorias" fora do escopo da tarefa. Não reformate código não relacionado.

**3. Se for ambíguo — pergunte.**
Contratos de API e comportamento dos canais de eventos nunca devem ser assumidos. Um payload corrompido ou erro não tratado no streaming tem impacto direto na UI do médico.

**4. Defina critérios de conclusão antes de começar.**
A tarefa está concluída quando:
- O código satisfaz a spec SDD
- `npm run type-check` passa sem erros
- `npm run lint` passa sem erros
- Nenhuma regra inegociável foi violada

---

## Comandos do Projeto

```bash
npm install          # instalar dependências
npm run dev          # desenvolvimento com hot-reload (tsx watch) — porta 4000
npm run build        # compilação TypeScript de produção
npm run start        # executar build de produção
npm run type-check   # verificação de tipos (obrigatório pós-tarefa)
npm run lint         # linter (obrigatório pós-tarefa)
npm run test         # testes automatizados
```

> Nunca invente comandos. Se o script não existir no `package.json`, informe ao usuário antes de prosseguir.

---

## Regras Inegociáveis (Violação = Bloqueante)

### Segurança e Contrato
- `@fastify/helmet` e `@fastify/cors` registrados **antes** de qualquer rota
- Responder `202 Accepted` imediatamente em `POST /api/triage` com `job_id` (UUIDv4)
- Todo payload do Webhook (`POST /api/webhooks/triage-result`) validado com Zod (`WebhookPayloadSchema.safeParse()`) antes de disparar no SSE
- Manter streaming SSE em `GET /api/triage/stream/:jobId` com headers corretos (`text/event-stream`, `no-cache`, `keep-alive`) e heartbeat a cada 15s

### LGPD — Dados Clínicos
- **PROIBIDO** logar `current_note`, `final_report` ou `clinical_justification`
- Logar apenas: `job_id`, `patient_id`, código HTTP, latência em ms
- Dados clínicos trafegam em memória no ciclo de eventos — sem cache ou persistência em disco no BFF

### TypeScript
- `any` é proibido — use `unknown` com type guards
- Tipos inferidos de schemas Zod (`z.infer<typeof Schema>`) — não declarar em paralelo
- `strict: true` no `tsconfig.json` deve permanecer ativo

### Processo
- Nunca incluir stacktrace no payload HTTP de resposta ao MFE
- Nunca chamar Ollama (porta 11434) ou ChromaDB diretamente
- Nunca implementar lógica clínica no BFF
- Não instalar dependências sem aprovação explícita do usuário
- Não usar `console.log` — use `fastify.log.info` / `fastify.log.error`

---

## Mapa de Diretórios

```
psychnote-bff/
├── .okf/                              ← BASE DE CONHECIMENTO — leia antes de qualquer tarefa
│   ├── index.md                       ← PONTO DE ENTRADA do OKF
│   ├── architecture/
│   │   ├── overview.md                ← Visão Geral HTTP 202 + Webhook + SSE
│   │   └── folder-structure.md        ← Convenções de nomenclatura
│   ├── decisions/                     ← ADRs (0001 a 0005)
│   ├── contracts/                     ← Contratos de API (bff-api.md e core-api.md)
│   ├── domain/                        ← Regras clínicas que o BFF deve conhecer
│   └── playbooks/                     ← Como rodar o projeto
├── src/
│   ├── routes/
│   │   ├── health/health.route.ts
│   │   ├── patients/
│   │   │   ├── patients.route.ts
│   │   │   └── patients.spec.md       ← LEIA ANTES DE IMPLEMENTAR
│   │   ├── stream/
│   │   │   ├── stream.route.ts
│   │   │   └── stream.spec.md         ← LEIA ANTES DE IMPLEMENTAR
│   │   ├── triage/
│   │   │   ├── triage.route.ts
│   │   │   └── triage.spec.md         ← LEIA ANTES DE IMPLEMENTAR
│   │   └── webhook/
│   │       ├── webhook.route.ts
│   │       └── webhook.spec.md        ← LEIA ANTES DE IMPLEMENTAR
│   ├── plugins/
│   │   ├── core-client/
│   │   │   ├── core-client.plugin.ts
│   │   │   └── CoreClient.spec.md     ← LEIA ANTES DE IMPLEMENTAR
│   │   └── error-handler/
│   │       ├── error-handler.plugin.ts
│   │       └── ErrorHandler.spec.md   ← LEIA ANTES DE IMPLEMENTAR
│   ├── schemas/
│   │   └── index.ts                   ← FONTE ÚNICA DE VERDADE dos tipos Zod
│   └── server.ts                      ← Entrypoint: registra plugins e rotas
├── .env.example                       ← PORT, CORE_URL, CORE_TIMEOUT_MS, CORS_ORIGINS
├── AGENTS.md                          ← Instruções para todos os agentes
├── CLAUDE.md                          ← Otimizado para Claude Code
└── GEMINI.md                          ← Este arquivo — otimizado para Gemini/Antigravity
```

---

## Antipadrões — Rejeitar Imediatamente

```
✗ any em TypeScript
✗ console.log em produção           → use fastify.log.info
✗ Chamada síncrona bloqueante aguardando LangGraph em /api/triage
✗ Enviar mensagem SSE sem validação Zod no payload do Webhook
✗ Stacktrace no payload HTTP de resposta
✗ Log de current_note, final_report ou clinical_justification
✗ Lógica clínica de qualquer tipo no BFF
✗ Chamar Ollama (11434) ou ChromaDB diretamente
✗ Adicionar dependência ao package.json sem aprovação
✗ throw new Error() em rota sem capturar — use o plugin ErrorHandler
✗ Implementar comportamento não previsto na spec SDD sem esclarecimento prévio
```

