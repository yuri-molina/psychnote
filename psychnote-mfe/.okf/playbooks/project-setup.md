---
type: Playbook
title: Configuração e Execução Local — psychnote-mfe
description: Passo a passo para instalar dependências, configurar variáveis de ambiente e rodar o MFE em modo standalone.
timestamp: 2026-08-07T14:35:00-03:00
status: active
version: 1.0.0
related:
  - ./build-and-federation.md
  - ../../architecture/folder-structure.md
  - ../../decisions/0001-standalone-first.md
---

# Playbook: Configuração e Execução Local

## Pré-requisitos

| Ferramenta | Versão Mínima | Verificar com |
| :--- | :--- | :--- |
| Node.js | 20.x LTS | `node --version` |
| npm | 10.x | `npm --version` |
| psychnote-core rodando | qualquer | `curl http://localhost:8000/health` |
| psychnote-bff rodando | qualquer | `curl http://localhost:4000/health` |

O MFE pode ser executado em modo standalone sem o BFF ativo, mas todas as chamadas de dados retornarão erro. Para desenvolvimento isolado de componentes, usar Storybook.

## Passo 1: Instalar Dependências

```bash
npm install
```

## Passo 2: Configurar Variáveis de Ambiente

Criar o arquivo `.env.local` na raiz do projeto (não versionado):

```env
VITE_BFF_URL=http://localhost:4000
```

Sem esta variável, o HTTP client em `src/lib/api.ts` usará string vazia como baseURL e todas as chamadas falharão.

## Passo 3: Configurar shadcn/ui (primeira execução apenas)

O diretório `src/components/ui/` é gerenciado pelo CLI do shadcn/ui. Para adicionar um componente:

```bash
npx shadcn add button
npx shadcn add textarea
npx shadcn add card
npx shadcn add badge
npx shadcn add alert
```

O prefixo `psy-` já está configurado em `components.json`. Os componentes gerados usarão as classes Tailwind prefixadas automaticamente.

## Passo 4: Rodar em Modo Standalone (desenvolvimento cotidiano)

```bash
npm run dev
```

O MFE estará disponível em `http://localhost:5001`. O Module Federation NÃO está ativo neste modo. Este é o modo correto para desenvolvimento cotidiano de telas e componentes.

## Verificação do Ambiente

Após iniciar o servidor, verificar no browser:

- `http://localhost:5001` → tela de listagem de pacientes (pode exibir erro de fetch se BFF não estiver rodando)
- Console do browser não deve exibir erros de TypeScript ou Vite

## Modo Storybook (desenvolvimento de componentes isolados)

```bash
npm run storybook
```

Disponível em `http://localhost:6006`. Permite desenvolver e visualizar componentes sem depender do BFF ou do Core.
