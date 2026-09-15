---
type: Decision
title: "ADR-0001: Fastify como Framework HTTP do BFF"
description: Decisão de usar Fastify (em vez de Express ou Hono) como framework HTTP principal do psychnote-bff, priorizando performance, ecossistema de plugins e integração nativa com Zod.
timestamp: 2026-08-07T16:55:00-03:00
status: active
version: 1.0.0
related:
  - ./0002-zod-contract-validation.md
  - ../architecture/overview.md
---

## Contexto

O psychnote-bff é um roteador leve sem banco de dados ou lógica de domínio. Sua função é receber requisições do MFE, encaminhá-las ao Core e retornar respostas validadas. O framework escolhido deve:

- **(a)** ter baixo overhead de CPU/memória para não adicionar latência ao já lento pipeline de IA (~40s);
- **(b)** suportar validação de schemas de forma nativa;
- **(c)** ter ecossistema de plugins robusto para CORS e Helmet sem configuração manual.

## Decisão

O BFF usará **Fastify v5** como framework HTTP. O plugin `fastify-type-provider-zod` será instalado para integrar Zod como provider de tipagem e validação de schemas, habilitando validação automática de request body, response e query params diretamente nas definições de rota.

## Alternativas Consideradas

**Express.js:** Ecossistema maduro, mas arquitetura de callback e overhead de middleware são desnecessariamente complexos para um BFF simples. Integração com Zod requer biblioteca de terceiros sem integração profunda.

**Hono:** Excelente para edge runtimes (Cloudflare Workers). Overhead mínimo, mas ecossistema de plugins menos maduro para Node.js on-premise comparado ao Fastify.

**Fastify (escolhido):** Benchmark consistente — ~30–40% mais rápido que Express em requests/s em Node.js puro. O plugin `fastify-type-provider-zod` oferece integração de primeira classe com Zod. Os plugins oficiais `@fastify/cors` e `@fastify/helmet` eliminam configuração manual de segurança. O Pino (logger nativo) oferece JSON logging estruturado sem dependência adicional.

## Consequências

- Todo o registro de rotas deve usar o método tipado do Fastify com `serializerCompiler` e `validatorCompiler` do `fastify-type-provider-zod`.
- Plugins de segurança (`@fastify/cors`, `@fastify/helmet`) devem ser registrados antes de qualquer rota.
- O `server.ts` é o entrypoint que orquestra o registro de plugins e rotas na ordem correta.
