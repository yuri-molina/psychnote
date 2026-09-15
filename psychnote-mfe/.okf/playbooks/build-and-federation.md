---
type: Playbook
title: Build de Produção e Module Federation — psychnote-mfe
description: Como gerar o bundle de produção, validar o remoteEntry.js e preparar o MFE para integração com o Shell App (Host).
timestamp: 2026-08-07T14:35:00-03:00
status: active
version: 1.0.0
related:
  - ./project-setup.md
  - ../../architecture/module-federation.md
  - ../../decisions/0001-standalone-first.md
  - ../../decisions/0002-vite-plugin-federation.md
---

# Playbook: Build de Produção e Module Federation

## Build de Produção

```bash
npm run build
```

Gera os artefatos em `dist/`. O arquivo crítico para Module Federation é:

```
dist/
└── assets/
    └── remoteEntry.js    ← manifesto do Remote, consumido pelo Shell App
```

## Validar o remoteEntry.js

Após o build, verificar se o `remoteEntry.js` está sendo servido corretamente:

```bash
npm run serve:remote
```

Isso executa `vite preview` na porta 5001. Verificar no browser:

```
http://localhost:5001/assets/remoteEntry.js
```

O arquivo deve retornar JavaScript válido (não um 404). Se retornar 404, o `build.target: 'esnext'` pode estar ausente no `vite.config.ts`.

## Modo de Desenvolvimento Integrado (Remote + Host simultâneos)

Este modo é necessário apenas ao testar a integração com o Shell App. Não é o fluxo de desenvolvimento cotidiano.

### Terminal 1 — Remote (psychnote-mfe):

```bash
npm run dev:mfe
```

Isso executa `vite build --watch` em paralelo com `vite preview --port 5001`. O `remoteEntry.js` é reconstruído a cada alteração de arquivo. O HMR não está disponível neste modo.

### Terminal 2 — Host (Shell App):

```bash
# No repositório do Shell App
npm run dev
```

O Host (porta 3000) carrega o Remote via `http://localhost:5001/assets/remoteEntry.js`.

## Configuração no Shell App (Referência)

Ao criar o Shell App, registrar o psychnote-mfe como Remote no `vite.config.ts` do Host:

```typescript
federation({
  name: 'shell_app',
  remotes: {
    psychnoteMfe: 'http://localhost:5001/assets/remoteEntry.js',
  },
  shared: {
    react: { singleton: true },
    'react-dom': { singleton: true },
    '@tanstack/react-query': { singleton: true },
  },
})
```

Declarar os tipos do Remote em `src/remotes.d.ts` no Shell App:

```typescript
declare module 'psychnoteMfe/PsychnoteApp' {
  import React from 'react';
  const PsychnoteApp: React.ComponentType;
  export default PsychnoteApp;
}
```

Importar e usar o Remote no Shell App:

```tsx
import React, { Suspense } from 'react';
const PsychnoteApp = React.lazy(() => import('psychnoteMfe/PsychnoteApp'));

function App() {
  return (
    <Suspense fallback={<div>Carregando módulo clínico...</div>}>
      <PsychnoteApp />
    </Suspense>
  );
}
```

## Problemas Comuns

| Problema | Causa Provável | Solução |
| :--- | :--- | :--- |
| `remoteEntry.js` retorna 404 | `build.target` não é `esnext` ou path incorreto | Verificar `vite.config.ts`: `build.target: 'esnext'` |
| Erro "Top-level await is not available" | Target de build incompatível | Garantir `target: 'esnext'` no `vite.config.ts` do Remote e do Host |
| Múltiplas instâncias de React no Host | `shared.react.singleton` ausente | Adicionar `singleton: true` em ambos os configs |
| ZodError ao carregar no Host | Contrato do BFF mudou após o build do Remote | Rebuild do Remote e atualizar `TriageResponseSchema` |
