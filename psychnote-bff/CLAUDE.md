# CLAUDE.md — psychnote-bff

> **Para Claude Code:** Este arquivo é seu sistema de onboarding obrigatório. Leia-o **integralmente** antes de qualquer ação. É curto por design — cada linha conta.

---

## O que é este repositório

`psychnote-bff` é um **roteador e gerenciador de eventos em tempo real** (Backend for Frontend) na arquitetura `MFE → BFF → Core` do projeto PsicRE-AI. Ele **não** possui banco de dados, **não** renderiza views e **não** executa inferência de IA. Sua responsabilidade é intermediar o `psychnote-mfe` (porta 5001) e o `psychnote-core` (porta 8000) com segurança, validação de contrato via Zod, gerenciamento de conexões SSE em tempo real (`Map<jobId, FastifyReply>`) e recepção de Webhooks do Core.

**Stack obrigatório:** Node.js 20 LTS · Fastify 5 · Zod + fastify-type-provider-zod · Server-Sent Events (SSE) · @fastify/cors · @fastify/helmet · Undici/Node Fetch + AbortController · TypeScript strict · Pino logging

---

## Protocolo de Onboarding (execute ANTES de qualquer tarefa)

```
1. Leia .okf/index.md           → entenda o mapa completo de artefatos
2. Leia .okf/architecture/overview.md  → fluxo HTTP 202 + Webhook + SSE Stream e resiliência
3. Leia o .spec.md co-localizado       → spec SDD da rota/módulo que você vai tocar (stream.spec.md, webhook.spec.md, triage.spec.md, patients.spec.md)
4. Confirme o contrato de API          → .okf/contracts/ (bff-api.md e core-api.md) antes de qualquer integração
5. Consulte o ADR relevante            → .okf/decisions/ (incluindo 0005-async-webhook-sse-architecture.md)
```

> **Regra de ouro:** Se um artefato OKF ou SDD existir para o que você vai fazer, lê-lo **não é opcional**. A implementação deve ser fiel à spec.

---

## Comandos do Projeto

```bash
npm install          # instalar dependências
npm run dev          # desenvolvimento com hot-reload (tsx watch)
npm run build        # compilação TypeScript
npm run start        # executar build de produção
npm run type-check   # tsc --noEmit (obrigatório antes de considerar tarefa concluída)
npm run lint         # linter (obrigatório antes de considerar tarefa concluída)
npm run test         # testes automatizados
```

> Nunca invente comandos. Se o script não existir no `package.json`, informe antes de prosseguir.

---

## Como Pensar (Behaviorismo do Agente)

**Antes de escrever qualquer código, declare explicitamente:**
1. Qual spec SDD você leu e qual artefato OKF é relevante
2. Sua interpretação do que a tarefa pede
3. O que você vai alterar e o que vai deixar intocado
4. Qualquer ambiguidade que precise de esclarecimento

**Se a tarefa for ambígua — pare e pergunte.** Nunca assuma contratos de API, estrutura de payload ou comportamento de eventos. Uma suposição errada em domínio de saúde mental tem consequências reais.

**Modificações cirúrgicas:** toque apenas o código da tarefa. Não reformate, não renomeie, não reorganize imports fora do escopo.

**Verificação pós-tarefa (não negociável):**
```bash
npm run type-check && npm run lint
```

---

## Regras Inegociáveis

| Regra | Violação bloqueante |
| :--- | :--- |
| Validar payload do Webhook com `WebhookPayloadSchema.safeParse()` antes de emitir evento SSE | Sim |
| `POST /api/triage` deve responder imediatamente com HTTP `202 Accepted` contendo `job_id` | Sim |
| `GET /api/triage/stream/:jobId` deve abrir conexão SSE com `keep-alive` e heartbeat a cada 15s | Sim |
| `@fastify/cors` e `@fastify/helmet` registrados antes de qualquer rota | Sim |
| Nunca logar `current_note`, `final_report` ou `clinical_justification` | Sim — LGPD |
| Nunca usar `any` em TypeScript — use `unknown` com type guards | Sim |
| Nunca incluir stacktrace no payload HTTP de resposta ao MFE | Sim |
| Nunca chamar Ollama (11434) ou ChromaDB diretamente | Sim |
| Não instalar dependências sem aprovação explícita do usuário | Sim |

---

## Mapa de Specs SDD

Toda rota e plugin tem um `.spec.md` co-localizado. **Leia antes de implementar.**

| Spec | Cobre |
| :--- | :--- |
| `src/routes/triage/triage.spec.md` | `POST /api/triage` — geração de `job_id`, despacho assíncrono ao Core e retorno HTTP 202 |
| `src/routes/stream/stream.spec.md` | `GET /api/triage/stream/:jobId` — estabelecimento de SSE, mapa de sockets e heartbeat |
| `src/routes/webhook/webhook.spec.md` | `POST /api/webhooks/triage-result` — recebimento do resultado do Core, validação Zod e dispatch SSE `triage_completed` |
| `src/routes/patients/patients.spec.md` | `GET /patients` e `GET /patients/:id/history` — listagem e histórico de triagens |
| `src/plugins/core-client/CoreClient.spec.md` | Plugin HTTP do Core (`POST /api/v1/triage/async`), AbortController, erros customizados |
| `src/plugins/error-handler/ErrorHandler.spec.md` | Handler global crash-free, mapeamento de erros → HTTP |

---

## Navegação OKF Rápida

| Preciso entender... | Leia |
| :--- | :--- |
| Arquitetura geral e fluxo HTTP 202 + Webhook + SSE Stream | `.okf/architecture/overview.md` |
| Estrutura de diretórios e convenções | `.okf/architecture/folder-structure.md` |
| O que o Core expõe e notifica via Webhook | `.okf/contracts/core-api.md` |
| Endpoints HTTP 202, SSE e History expostos ao MFE | `.okf/contracts/bff-api.md` |
| Por que Fastify foi escolhido | `.okf/decisions/0001-fastify-framework.md` |
| Como funciona a validação Zod bidirecional | `.okf/decisions/0002-zod-contract-validation.md` |
| Como gerir timeouts e falhas do Core | `.okf/decisions/0003-timeout-and-resilience.md` |
| Como CORS e Helmet estão configurados | `.okf/decisions/0004-cors-and-helmet.md` |
| Decisão da arquitetura assíncrona HTTP 202 + Webhook + SSE | `.okf/decisions/0005-async-webhook-sse-architecture.md` |
| Como rodar o projeto | `.okf/playbooks/project-setup.md` |

---

## Antipadrões — Rejeitar Imediatamente

- `any` em TypeScript
- `console.log` em código de produção (use `fastify.log.info`)
- Retornar resposta síncrona bloqueante em `/api/triage` (esperando LangGraph terminar)
- Emitir dados no stream SSE sem validar o payload do Webhook com Zod
- Stacktrace no payload HTTP de resposta
- Log de `current_note`, `final_report` ou `clinical_justification`
- Lógica clínica de qualquer tipo dentro do BFF
- Dependências adicionadas ao `package.json` sem aprovação
- Chamar Ollama (porta 11434) ou ChromaDB diretamente

