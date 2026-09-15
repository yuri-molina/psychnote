---
type: Decision
title: "ADR-0003: Isolamento de CSS com Prefixo Tailwind psy- e Escopo de Variáveis"
description: Decisão de usar prefixo psy- em todas as classes Tailwind e escopar variáveis CSS na classe .psychnote-mfe-root para evitar colisão com o Shell App.
timestamp: 2026-08-07T12:00:00-03:00
status: active
version: 1.0.0
resource: ../../tailwind.config.js
related:
  - ../architecture/module-federation.md
---

# ADR-0003: Isolamento de CSS com Prefixo Tailwind psy-

## Contexto

Em uma arquitetura de Module Federation, o MFE (Remote) e o Shell App (Host) compartilham o mesmo documento HTML e DOM. Por padrão, o CSS de cada aplicação é injetado no `<head>` global. Se ambos usarem Tailwind CSS sem isolamento, classes como `flex`, `text-primary`, `bg-background` e variáveis CSS como `--primary`, `--background` do MFE irão sobrescrever as do Host ou vice-versa.

O projeto usa shadcn/ui, que gera componentes com classes Tailwind e variáveis CSS no `:root`. Sem isolamento, as variáveis de tema do MFE afetariam o tema inteiro do Shell App.

## Decisão

Toda a estilização do MFE segue três regras de isolamento:

1. **Prefixo `psy-` em todas as classes Tailwind** (configuração no `tailwind.config.js`).
2. **Variáveis CSS escopadas na classe `.psychnote-mfe-root`** em vez do seletor `:root` global (configuração no `src/index.css`).
3. **O componente raiz exportado (`PsychnoteMfe.tsx`) sempre envolve seu conteúdo em `<div className="psychnote-mfe-root">`**.

## Configuração

### tailwind.config.js
```javascript
module.exports = {
  prefix: 'psy-',
  content: ['./src/**/*.{ts,tsx}'],
  // ... restante da configuração
};
```

### components.json (shadcn/ui)
```json
{
  "tailwind": {
    "prefix": "psy-"
  }
}
```

### src/index.css
```css
.psychnote-mfe-root {
  --psy-background: /* valor */;
  --psy-foreground: /* valor */;
  --psy-primary: /* valor */;
  /* demais variáveis de tema */
}
```

## Consequências

- Todos os componentes gerados pelo `npx shadcn add` usarão automaticamente o prefixo `psy-` nas classes Tailwind.
- A função utilitária `cn()` do shadcn/ui funciona normalmente com o prefixo aplicado.
- O componente `PsychnoteMfe.tsx` deve sempre incluir `className="psychnote-mfe-root"` no elemento raiz exportado.
- Em modo standalone, a div `.psychnote-mfe-root` envolve toda a SPA, então o isolamento é transparente para o desenvolvimento cotidiano.
