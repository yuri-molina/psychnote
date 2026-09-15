---
type: Decision
title: "ADR-0004: Segurança via @fastify/cors e @fastify/helmet"
description: Decisão de usar os plugins oficiais do Fastify para configuração de CORS e HTTP Security Headers, garantindo que apenas o MFE possa consumir o BFF e que as respostas incluam headers de segurança.
timestamp: 2026-08-07T16:55:00-03:00
status: active
version: 1.0.0
related:
  - ./0001-fastify-framework.md
  - ../architecture/overview.md
---

## Contexto

O BFF é um serviço HTTP local sem autenticação. Sem CORS configurado, qualquer origem poderia enviar requisições ao BFF — incluindo scripts maliciosos rodando no browser do usuário. Sem HTTP Security Headers (Helmet), as respostas carecem de proteções contra ataques comuns (XSS, clickjacking, MIME sniffing).

## Decisão

**CORS (`@fastify/cors`):** Configurado para aceitar requisições exclusivamente de `http://localhost:5001` (porta do MFE em dev). Métodos permitidos: `GET`, `POST`. Headers permitidos: `Content-Type`.

Configuração de referência:

```typescript
await fastify.register(cors, {
  origin: ['http://localhost:5001'],
  methods: ['GET', 'POST'],
  allowedHeaders: ['Content-Type'],
});
```

**Helmet (`@fastify/helmet`):** Registrado com configuração padrão. Headers de segurança ativados por padrão incluem: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`, entre outros.

**Ordem de registro obrigatória:**

1. `@fastify/helmet` (primeiro)
2. `@fastify/cors` (segundo)
3. Plugins de rota (por último)

## Consequências

- Em ambiente de produção futuro, a lista de origens CORS deverá ser configurada via variável de ambiente (`CORS_ORIGINS`), não hardcoded.
- O Core (`localhost:8000`) não precisa de ajuste de CORS para receber requisições do BFF: CORS é uma proteção do browser, não de servidor-para-servidor.
- A PoC não implementa autenticação. Em contexto de produção, adicionar `@fastify/jwt` ou `@fastify/oauth2` seria o próximo passo.
