# AGENTS.md — psychnote-bff

Arquivo de instruções mandatórias para agentes de IA que operam neste repositório.
Leia este arquivo integralmente antes de executar qualquer tarefa.

> **Agentes especializados:** Se você é Claude Code, leia também [`CLAUDE.md`](./CLAUDE.md) — contém protocolo de onboarding otimizado e regras comportamentais específicas para Claude. Se você é Gemini / Antigravity, leia [`GEMINI.md`](./GEMINI.md). Esses arquivos complementam — não substituem — este AGENTS.md.

---

## 1. Comandos do Projeto

```bash
# Instalar dependências
npm install

# Desenvolvimento com hot-reload
npm run dev

# Build de produção
npm run build

# Executar build de produção
npm run start

# Verificação de tipos TypeScript
npm run type-check

# Linter
npm run lint

# Testes
npm run test
```

> **Nota:** Nunca invente comandos. Se um script não existir no `package.json`, informe ao usuário antes de prosseguir.

---

## 2. Regras de Comportamento do Agente

1. **Pergunte antes de assumir** — se a tarefa for ambígua (especialmente contratos de API e fluxos assíncronos), pause e solicite esclarecimento.
2. **Modificações cirúrgicas** — altere apenas o código diretamente relacionado à tarefa. Não refatore código fora do escopo solicitado.
3. **Verificação obrigatória pós-tarefa** — ao concluir qualquer alteração de código, execute: `npm run type-check && npm run lint`.
4. **Não instale dependências sem permissão** — proponha a dependência ao usuário e aguarde aprovação explícita.
5. **Não desative testes para fazer o build passar** — corrija a causa raiz ou informe ao usuário sobre o conflito.
6. **Consulte as specs antes de implementar** — cada rota (`stream.spec.md`, `webhook.spec.md`, `triage.spec.md`, `patients.spec.md`) e plugin tem um `.spec.md` co-localizado. Leia-o antes de qualquer implementação.
7. **Consulte o OKF antes de regras de negócio** — leia `.okf/index.md` para localizar o artefato relevante ao contexto da tarefa.
8. **NUNCA implemente lógica clínica no BFF** — o BFF é um gerenciador de rotas, eventos SSE (`Map<jobId, FastifyReply>`) e webhooks; toda inteligência clínica é responsabilidade do Core.
9. **NUNCA chame o Ollama ou ChromaDB diretamente** — todo acesso ao Core é via HTTP (aceite 202 em `/api/v1/triage/async`) usando o plugin `coreClient`.

---

## 3. Stack Tecnológica

| Camada | Tecnologia | Observação |
| :--- | :--- | :--- |
| Runtime | Node.js 20+ LTS | Obrigatório: AbortController nativo |
| Framework HTTP | Fastify 5.x | Alta performance, suporte a SSE Stream e tipo-seguro com Zod |
| Validação | Zod + fastify-type-provider-zod | Validação bidirecional obrigatória |
| HTTP Client | Undici / Node Fetch nativo | AbortController para timeout |
| Comunicação Realtime | SSE (Server-Sent Events) | Gerenciamento de conexões ativas (`Map<jobId, FastifyReply>`) |
| Segurança | @fastify/cors + @fastify/helmet | Obrigatórios, registrados antes das rotas |
| Logging | Pino (nativo do Fastify) | JSON estruturado, sem dados clínicos |
| Linguagem | TypeScript strict | `strict: true` no tsconfig |

---

## 4. Convenções de Código

### TypeScript

- `strict: true` ativo. O tipo `any` é **proibido**. Use `unknown` com type guards se necessário.
- Tipos de API são inferidos dos schemas Zod (`TriageAsyncRequestSchema`, `TriageAsyncResponseSchema`, `WebhookPayloadSchema`). Não declare tipos em paralelo.

### Rotas Fastify

- Toda rota deve declarar schemas de request e response usando `fastify-type-provider-zod`.
- A rota `POST /api/triage` responde com HTTP `202 Accepted` contendo `job_id` e status `processing`.
- A rota `GET /api/triage/stream/:jobId` estabelece streaming SSE (`text/event-stream`, `keep-alive`, heartbeat a cada 15s) e registra a conexão no mapa global.
- A rota `POST /api/webhooks/triage-result` recebe o callback do Core, valida via Zod, emite o evento SSE `triage_completed` para o cliente conectado e encerra a conexão SSE.

### Tratamento de Erros

- Nunca use `throw new Error()` diretamente nas rotas sem capturar. Use os tipos de erro definidos no plugin `ErrorHandler`.
- O plugin `ErrorHandler` é o único responsável por converter exceções em respostas HTTP.
- **JAMAIS** inclua stacktraces no payload de resposta HTTP.

### LGPD

- **PROIBIDO** logar `current_note`, `final_report` ou `clinical_justification`.
- Apenas metadados não-clínicos podem ser logados: `job_id`, `patient_id`, código HTTP, latência em ms.

---

## 5. Mapa de Diretórios

```
psychnote-bff/
├── .okf/                          # Base de conhecimento OKF (specs, ADRs, contratos)
├── src/
│   ├── routes/
│   │   ├── health/
│   │   │   └── health.route.ts    # GET /health
│   │   ├── patients/
│   │   │   ├── patients.route.ts  # GET /patients, GET /patients/:id/history
│   │   │   └── patients.spec.md   # RouteSpec SDD
│   │   ├── stream/
│   │   │   ├── stream.route.ts    # GET /api/triage/stream/:jobId (SSE)
│   │   │   └── stream.spec.md     # RouteSpec SDD
│   │   ├── triage/
│   │   │   ├── triage.route.ts    # POST /api/triage (HTTP 202 Accepted)
│   │   │   └── triage.spec.md     # RouteSpec SDD
│   │   └── webhook/
│   │       ├── webhook.route.ts   # POST /api/webhooks/triage-result
│   │       └── webhook.spec.md    # RouteSpec SDD
│   ├── plugins/
│   │   ├── core-client/
│   │   │   ├── core-client.plugin.ts  # Plugin de HTTP client para o Core
│   │   │   └── CoreClient.spec.md     # ModuleSpec SDD
│   │   └── error-handler/
│   │       ├── error-handler.plugin.ts # Plugin de tratamento global de erros
│   │       └── ErrorHandler.spec.md   # ModuleSpec SDD
│   ├── schemas/
│   │   └── index.ts               # Schemas Zod — fonte única de verdade dos tipos
│   └── server.ts                  # Entrypoint Fastify: registra plugins e rotas
├── .env.example                   # Modelo de variáveis de ambiente (versionado)
├── .env                           # Variáveis locais (não versionado)
├── package.json
├── tsconfig.json
└── AGENTS.md
```

---

## 6. Base de Conhecimento OKF

| Necessidade | Artefato OKF |
| :--- | :--- |
| Arquitetura geral e fluxo assíncrono (HTTP 202 + Webhook + SSE) | `.okf/architecture/overview.md` |
| Estrutura de diretórios e convenções | `.okf/architecture/folder-structure.md` |
| Contrato da Core API (o que o BFF consome e recebe via Webhook) | `.okf/contracts/core-api.md` |
| Contrato da BFF API (endpoints HTTP 202, SSE e History expostos ao MFE) | `.okf/contracts/bff-api.md` |
| Por que Fastify foi escolhido | `.okf/decisions/0001-fastify-framework.md` |
| Como a validação Zod funciona | `.okf/decisions/0002-zod-contract-validation.md` |
| Como gerenciar timeouts e falhas | `.okf/decisions/0003-timeout-and-resilience.md` |
| Como CORS e Helmet estão configurados | `.okf/decisions/0004-cors-and-helmet.md` |
| Decisão da Arquitetura Assíncrona Webhook + SSE Stream | `.okf/decisions/0005-async-webhook-sse-architecture.md` |
| Como rodar o projeto | `.okf/playbooks/project-setup.md` |

---

## 7. Regras de Domínio Clínico (Invioláveis)

- **O BFF é um roteador e gerenciador de eventos em tempo real.** Não executa nenhuma lógica clínica.
- **Nenhum dado clínico deve ser persistido ou logado no BFF.** LGPD.
- **Toda triagem iniciada via `POST /api/triage` gera um `job_id` (UUIDv4) e responde imediatamente com 202 Accepted.**
- **Sempre valide o payload recebido do Core no webhook (`POST /api/webhooks/triage-result`) com Zod antes de emitir o evento SSE `triage_completed`.**
- **Em caso de falha, retorne payload estruturado de erro.** Nunca crashe silenciosamente.

---

## 8. Antipadrões Proibidos

- Chamar Ollama (porta 11434) ou ChromaDB diretamente.
- Implementar lógica de classificação de risco ou auditoria de conduta no BFF.
- Usar `any` em qualquer contexto TypeScript.
- Fazer requisições ao Core sem tratar falha ou timeout.
- Repassar ao cliente SSE um payload do Core sem validar com Zod via schema do Webhook.
- Incluir stacktraces no payload HTTP de resposta.
- Logar conteúdo de notas clínicas ou pareceres (`current_note`, `final_report`).
- Adicionar dependências sem aprovação do usuário.
- Usar `console.log` em código de produção (use o logger do Fastify: `fastify.log.info`).

