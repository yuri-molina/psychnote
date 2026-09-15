---
type: LayoutSpec
id: LS-LANDING-LAYOUT
title: Especificação de Layout — LandingView (Menu Inicial)
description: Composição estrutural da página inicial do Psych Note. Apresenta ações primárias para evolução de novos pacientes e listagem de prontuários.
timestamp: 2026-08-09T01:00:00-03:00
status: approved
version: 1.0.0
owner: psychnote-mfe
tags: [layout, landing, home, dashboard, view]
related:
  - ../views/NewPatientEvolutionView.spec.md
  - ../views/PatientListView.spec.md
  - ../../.okf/architecture/overview.md
---

# LayoutSpec: LandingView (Menu Inicial)

## 1. Composição Estrutural

```
LandingView
├── [Região: Hero Header]
│   ├── Logo + Título: "Psych Note"
│   ├── Subtítulo: "Assistente Psiquiátrico de Inteligência Artificial para Triagem de Risco e Prontuário Eletrônico"
│   └── Badge de Versão / Status do Sistema
│
├── [Região: Cards de Ação Principal (Grid 2 Colunas)]
│   ├── [Card 1: Evoluir Novo Paciente]
│   │   ├── Ícone: Stethoscope / UserPlus
│   │   ├── Título: "Evoluir Novo Paciente"
│   │   ├── Descrição: "Cadastre um novo paciente e redija a evolução psiquiátrica para triagem automatizada com IA"
│   │   └── Botão CTA: "Iniciar Evolução" → NavLink /patients/new-evolution
│   │
│   └── [Card 2: Listar Pacientes]
│       ├── Ícone: Users / FolderSearch
│       ├── Título: "Listar Pacientes"
│       ├── Descrição: "Consulte a lista de pacientes cadastrados, prontuários clínicos e histórico de evoluções"
│       └── Botão CTA: "Ver Lista de Pacientes" → NavLink /patients
│
└── [Região: Destaques de Recursos / Footer]
    └── Indicadores de conformidade LGPD, WCAG 2.1 AA e suporte a Module Federation
```

## 2. Requisitos de UX/UI

- Design moderno, de alto impacto visual com cartões elevados, sombras suaves, gradientes primários e suporte a hover dinâmico.
- Botão "Evoluir Novo Paciente" com destaque visual de ação primária (fundo primário, maior peso visual).
- Botão "Listar Pacientes" com estilo neutro/secundário elevado para rápida identificação funcional.
- Responsividade total: 1 coluna em dispositivos móveis (`< 640px`) e 2 colunas em telas médias/grandes (`>= 640px`).

## 3. Requisitos de Acessibilidade (A11y)

- `<main role="main">` engloba o conteúdo da Landing View.
- Cada card de ação possui `role="region"` ou é um elemento focável com `aria-label` descritivo.
- Navegação direta por teclado com foco bem visível (`focus:psy-ring-2`).
