---
type: Architecture
title: Estratégia de Module Federation — psychnote-mfe
description: Configuração standalone-first com @originjs/vite-plugin-federation. Estrutura de pontos de entrada, scripts npm e limitações de dev server.
timestamp: 2026-08-07T12:00:00-03:00
status: active
version: 1.0.0
resource: ../../vite.config.ts
related:
  - ./overview.md
  - ../decisions/0001-standalone-first.md
  - ../decisions/0002-vite-plugin-federation.md
---

# Estratégia de Module Federation

## Papéis na Arquitetura de Module Federation

O `psychnote-mfe` assume o papel de **Remote**. Expõe o componente `PsychnoteMfe` via `remoteEntry.js` para consumo por um Shell App (Host) futuro.

O Host não existe no escopo atual. A estratégia standalone-first resolve essa dependência. Ver [decisions/0001-standalone-first.md](../decisions/0001-standalone-first.md).

## Configuração do vite.config.ts

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import federation from '@originjs/vite-plugin-federation';
import path from 'path';

export default defineConfig({
  plugins: [
    react(),
    federation({
      name: 'psychnote_mfe',
      filename: 'remoteEntry.js',
      exposes: {
        './PsychnoteApp': './src/PsychnoteMfe.tsx',
      },
      shared: {
        react: { singleton: true, requiredVersion: '^19.0.0' },
        'react-dom': { singleton: true, requiredVersion: '^19.0.0' },
        '@tanstack/react-query': { singleton: true, requiredVersion: '^5.0.0' },
      },
    }),
  ],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  build: {
    target: 'esnext',
    modulePreload: false,
    cssCodeSplit: false,
  },
  server: { port: 5001, strictPort: true },
  preview: { port: 5001, strictPort: true },
});
```

## Pontos de Entrada Duplos (Standalone-First)

O MFE possui dois pontos de entrada com propósitos distintos:

| Arquivo | Propósito | Quando usado |
| :--- | :--- | :--- |
| `src/main.tsx` | Entrada da SPA standalone | `npm run dev` — desenvolvimento cotidiano |
| `src/PsychnoteMfe.tsx` | Componente exposto via Module Federation | `npm run build` — integração com Shell App futuro |

### src/main.tsx
Monta o MFE como SPA autônoma no elemento `#root`. Inicializa todos os Providers necessários (QueryClientProvider, BrowserRouter).

### src/PsychnoteMfe.tsx
Componente exportado para o Host. Implementa lógica de resiliência: verifica se um `QueryClientProvider` já existe no contexto do React (injetado pelo Shell App) antes de criar um local, evitando múltiplas instâncias de cache.

## Scripts npm

| Script | Comando | Propósito |
| :--- | :--- | :--- |
| `dev` | `vite` | SPA standalone para desenvolvimento cotidiano |
| `build` | `vite build` | Gera bundle de produção + remoteEntry.js |
| `build:watch` | `vite build --watch` | Rebuild contínuo ao salvar arquivos |
| `serve:remote` | `vite preview --port 5001` | Serve o build localmente (necessário para Module Federation em dev) |
| `dev:mfe` | `concurrently "build:watch" "serve:remote"` | Remote servindo remoteEntry.js para testes de integração com Host |

## Limitação Crítica do Dev Server

O `@originjs/vite-plugin-federation` não suporta HMR nativo em `vite dev`. O `remoteEntry.js` é gerado apenas pelo pipeline Rollup (build de produção), não pelo servidor de desenvolvimento.

Consequência prática:
- Para desenvolvimento isolado do MFE: usar `npm run dev` (standalone, sem Module Federation ativo).
- Para testar a integração com um Shell App: usar `npm run dev:mfe` no Remote e `vite dev` no Host.

## Configuração do Host (Referência para o Shell App Futuro)

Quando o Shell App for criado, a configuração de `remotes` será:

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

E o import no código do Host será:

```typescript
import PsychnoteApp from 'psychnoteMfe/PsychnoteApp';
```

A tipagem do componente remoto deve ser declarada em `src/remotes.d.ts` no repositório do Host.

## Dependências Compartilhadas (shared)

| Dependência | Razão do singleton |
| :--- | :--- |
| `react` | Uma única instância de React é obrigatória; múltiplas causam erros de hooks. |
| `react-dom` | Idem ao React. |
| `@tanstack/react-query` | Múltiplas instâncias de QueryClient criam caches independentes e duplicados. |
