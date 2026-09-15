---
type: LayoutSpec
id: LS-PATIENT-LIST-LAYOUT
title: Especificação de Layout — PatientListView
description: Composição estrutural da tela de listagem de pacientes. Define regiões, slots, estados de loading e empty state.
timestamp: 2026-08-07T14:35:00-03:00
status: approved
version: 1.0.0
owner: psychnote-mfe
tags: [layout, patient-list, view]
related:
  - ../components/patient-card.md
  - ../../architecture/component-tree.md
  - ../../contracts/bff-api.md
---

# LayoutSpec: PatientListView

## 1. Composição Estrutural

```
PatientListView
├── [Região: Header]
│   ├── Título: "Pacientes"
│   └── Subtítulo: "Selecione um paciente para iniciar a triagem"
│
├── [Região: Content]
│   ├── [Estado: loading]    → grade de skeleton cards (placeholder)
│   ├── [Estado: error]      → mensagem de erro + botão de retry
│   ├── [Estado: empty]      → mensagem de lista vazia
│   └── [Estado: success]    → grade de PatientCard[]
│
└── [Região: Footer] (opcional)
    └── Contagem de pacientes: "X pacientes encontrados"
```

## 2. Contrato de Layout

| Região | Elemento HTML | Responsabilidade |
| :--- | :--- | :--- |
| Header | `<header>` com `role="banner"` | Título e instrução de uso |
| Content | `<main>` com `role="main"` | Área de renderização dos cards |
| Footer | `<footer>` | Metadado de contagem (opcional) |

## 3. Layout da Grade de Cards

- Desktop (>= 1024px): 3 colunas, gap de 16px.
- Tablet (640px - 1023px): 2 colunas, gap de 12px.
- Mobile (< 640px): 1 coluna.

## 4. Estados da Camada de Dados

| Estado (`usePatients`) | O que renderizar |
| :--- | :--- |
| `isLoading=true` | Grade de 6 skeleton cards com animação de pulso |
| `isError=true` | Mensagem: "Não foi possível carregar a lista de pacientes." + botão "Tentar novamente" |
| `data.length === 0` | Mensagem: "Nenhum paciente encontrado no sistema." |
| `data.length > 0` | Grade de `PatientCard` para cada item |

## 5. Navegação

Ao acionar `onSelect` em um `PatientCard`, a view navega para `PatientDetailView` passando o `patientId` via parâmetro de rota: `/patients/:patientId/triage`.

## 6. Requisitos de Acessibilidade

- A grade de cards usa `<ul role="list">` com cada `PatientCard` dentro de `<li role="listitem">`.
- O estado de loading anuncia "Carregando lista de pacientes..." via `aria-live="polite"`.
- O estado de erro anuncia a mensagem via `role="alert"`.
