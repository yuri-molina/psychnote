---
type: LayoutSpec
id: LS-NEW-PATIENT-EVOLUTION-LAYOUT
title: Especificação de Layout — NewPatientEvolutionView (Novo Paciente)
description: Composição estrutural da tela de cadastro de novo paciente e redação de evolução clínica com redirecionamento imediato para o prontuário.
timestamp: 2026-08-09T23:45:00-03:00
status: approved
version: 1.2.0
owner: psychnote-mfe
tags: [layout, evolution, new-patient, form, triage, view, redirect]
related:
  - ../views/LandingView.spec.md
  - ../views/PatientRecordView.spec.md
  - ../components/triage-form/TriageForm.spec.md
  - ../../.okf/contracts/bff-api.md
---

# LayoutSpec: NewPatientEvolutionView

## 1. Composição Estrutural

```
NewPatientEvolutionView
├── [Slot: Navegação de Retorno Dinâmica]
│   └── Botão "Voltar" → onClick={() => navigate(-1)} (retorna ao histórico de navegação anterior)
│
├── [Slot: Cabeçalho Contextual]
│   ├── Título: "Novo Paciente"
│   └── Subtítulo: "Cadastre um novo paciente e redija a evolução psiquiátrica para análise de risco por IA."
│
├── [Slot: Formulário de Identificação]
│   └── Campo: "Nome Completo" (input em largura total; o ID do paciente é gerado nos bastidores para LGPD/humanização)
│
└── [Slot: Formulário de Evolução Clínica]
    └── Componente TriageForm
        ├── Cabeçalho: "Evolução" (esquerda) | "{x} caracteres" (direita)
        └── Botão: "Salvar Evolução e Executar Triagem" → Ação: Registra paciente + Dispara Triagem + Redireciona para /patients/:patientId/record
```

## 2. Requisitos de UX/UI

- Redirecionamento Imediato: Ao clicar em "Salvar Evolução e Executar Triagem", a tela de resultado intermediário foi eliminada. O usuário é redirecionado instantaneamente para a página de prontuário do paciente (`/patients/:patientId/record`).
- Humanização e Minimização de Dados (LGPD): Nenhum identificador numérico de banco de dados (`PAC-001`) é exposto na UI do usuário.
- O botão de retorno `"Voltar"` utiliza navegação nativa do histórico da pilha do React Router (`navigate(-1)`).

## 3. Requisitos de Acessibilidade (A11y)

- Todos os campos de formulário possuem `<label>` associado via `htmlFor`.
- Mensagens de erro com `role="alert"`.
- O botão de retorno ao histórico anterior é o primeiro elemento focável da página.
