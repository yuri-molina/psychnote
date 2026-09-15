---
type: Architecture
title: Estrutura de Diretórios — psychnote-bff
description: Layout canônico do repositório com responsabilidades e convenções de nomenclatura.
timestamp: 2026-08-07T16:55:00-03:00
status: active
version: 1.0.0
related:
  - ./overview.md
---

# Estrutura de Diretórios — psychnote-bff

## Layout Canônico do Repositório

```
psychnote-bff/
├── .okf/                          # Base de conhecimento OKF (specs, ADRs, contratos)
├── src/
│   ├── routes/
│   │   ├── health/
│   │   │   └── health.route.ts    # GET /health
│   │   ├── patients/
│   │   │   ├── patients.route.ts  # GET /patients
│   │   │   └── patients.spec.md   # RouteSpec SDD
│   │   └── triage/
│   │       ├── triage.route.ts    # POST /triage
│   │       └── triage.spec.md     # RouteSpec SDD
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

## Convenções de Nomenclatura

| Categoria | Convenção | Exemplo |
| :--- | :--- | :--- |
| Arquivos de rota | kebab-case + `.route.ts` | `triage.route.ts` |
| Arquivos de plugin | kebab-case + `.plugin.ts` | `core-client.plugin.ts` |
| Schemas Zod (constantes) | PascalCase com sufixo `Schema` | `TriageResponseSchema` |
| Tipos inferidos | PascalCase sem sufixo | `TriageResponse`, `TriageRequest` |
| Specs SDD | PascalCase (módulo) + `.spec.md` | `CoreClient.spec.md` |

---

## Regras de Co-localização

- Cada rota vive em seu próprio subdiretório dentro de `src/routes/`
- A spec SDD (`.spec.md`) fica co-localizada com o arquivo de implementação
- Todos os schemas Zod compartilhados vivem exclusivamente em `src/schemas/index.ts`
- Não deve existir lógica de negócio ou regras clínicas em nenhum arquivo do BFF
