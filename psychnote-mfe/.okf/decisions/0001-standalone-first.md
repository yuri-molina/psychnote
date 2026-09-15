---
type: Decision
title: "ADR-0001: Estratégia Standalone-First para o MFE"
description: Decisão de desenvolver o MFE como SPA autônoma com Module Federation pré-configurado para integração futura com Shell App.
timestamp: 2026-08-07T12:00:00-03:00
status: active
version: 1.0.0
related:
  - ./0002-vite-plugin-federation.md
  - ../architecture/module-federation.md
---

# ADR-0001: Estratégia Standalone-First para o MFE

## Contexto

O psychnote-mfe é o único MFE do projeto PsicRE-AI. O Shell App (Host de Module Federation) não existe e não será criado no escopo atual da PoC acadêmica. O BFF também está sendo desenvolvido em paralelo por um agente separado, criando dependências externas que poderiam bloquear o desenvolvimento da interface.

A adoção de Module Federation desde o início impõe um requisito: o Remote precisa de um Host funcional para ser testado em contexto integrado, e o `remoteEntry.js` não é gerado em modo `vite dev`.

## Decisão

O MFE será desenvolvido com estratégia **standalone-first**:

1. O arquivo `src/main.tsx` monta o MFE como SPA completa e autônoma na porta 5001.
2. O arquivo `src/PsychnoteMfe.tsx` é o componente exportado via `exposes` no `vite.config.ts`.
3. Todo o desenvolvimento cotidiano ocorre com `npm run dev` (modo standalone, sem Module Federation ativo).
4. O `@originjs/vite-plugin-federation` é configurado desde o início mas só é exercitado na build (`npm run build`).

## Alternativas Consideradas

**Alternativa A: Sem Module Federation por enquanto.**
Risco: ao introduzir Module Federation no futuro, as telas precisariam ser refatoradas para encapsulamento no componente `PsychnoteMfe.tsx`, gerando retrabalho.

**Alternativa B: Forçar Module Federation em dev com mock de Host.**
Risco: complexidade operacional desnecessária para uma PoC. Requer um segundo projeto (shell) funcional ou scripts de mock sofisticados.

**Alternativa C: Standalone-first (escolhida).**
Desenvolvimento ágil e desacoplado no dia a dia. Module Federation pré-configurado sem custo operacional atual. Integração com Shell App futura requer apenas adicionar a URL do `remoteEntry.js` no Host, sem alterar código das telas.

## Consequências

- O componente `src/PsychnoteMfe.tsx` deve ser mantido como wrapper limpo que encapsula toda a aplicação e gerencia Providers de forma resiliente.
- Ao criar o Shell App, o único trabalho necessário é registrar o Remote no `vite.config.ts` do Host e declarar os tipos em `src/remotes.d.ts`.
- Testes de integração com Module Federation devem usar `npm run dev:mfe` no Remote e `vite dev` no Host.
