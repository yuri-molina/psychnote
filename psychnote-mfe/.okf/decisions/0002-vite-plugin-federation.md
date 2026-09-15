---
type: Decision
title: "ADR-0002: Uso do @originjs/vite-plugin-federation"
description: Decisão de usar @originjs/vite-plugin-federation v1.3.9 como mecanismo de Module Federation, em detrimento do @module-federation/vite.
timestamp: 2026-08-07T12:00:00-03:00
status: active
version: 1.0.0
related:
  - ./0001-standalone-first.md
  - ../architecture/module-federation.md
---

# ADR-0002: Uso do @originjs/vite-plugin-federation

## Contexto

Para implementar Module Federation com Vite, existem dois pacotes principais disponíveis em 2026:

1. `@originjs/vite-plugin-federation` (OriginJS) — versão estável: `1.3.9`.
2. `@module-federation/vite` (Module Federation v2 / ByteDance) — ativo e mantido, com HMR nativo.

## Decisão

Usar `@originjs/vite-plugin-federation@^1.3.9`.

## Alternativas Consideradas

**@module-federation/vite (Module Federation v2)**
Vantagens: HMR nativo em dev server (sem necessidade de `vite build --watch`), suporte a Vite 5/6+, tipagem automática com `@module-federation/typescript`, manutenção ativa.
Desvantagens: API e configuração mais complexa. Overhead de setup desnecessário para o escopo de uma PoC acadêmica standalone-first.

**@originjs/vite-plugin-federation (escolhido)**
Vantagens: API simples e bem documentada, funcional para os requisitos da PoC, não requer HMR em dev (estratégia standalone-first elimina essa necessidade).
Desvantagens: Repositório com manutenção reduzida desde 2024/2025. Sem HMR nativo (contornado pela estratégia standalone-first). Exige `build.target: 'esnext'` obrigatoriamente.

## Consequências

- O arquivo `vite.config.ts` deve incluir `build.target: 'esnext'` para suportar Top-Level Await gerado pelo plugin.
- O desenvolvimento cotidiano usa `npm run dev` (SPA standalone) e não depende do Module Federation ativo.
- Se o projeto evoluir para produção ou para um ambiente com múltiplos MFEs e Shell App ativo, a migração para `@module-federation/vite` deve ser avaliada.

## Requisitos de Configuração

```typescript
build: {
  target: 'esnext',    // obrigatório para Top-Level Await
  modulePreload: false,
  cssCodeSplit: false,
}
```
