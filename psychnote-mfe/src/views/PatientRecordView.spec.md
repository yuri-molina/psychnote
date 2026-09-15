---
type: LayoutSpec
id: LS-PATIENT-RECORD-LAYOUT
title: Especificação de Layout — PatientRecordView (Prontuário Psiquiátrico)
description: Composição estrutural da tela de prontuário e histórico de evoluções, suportando estados de triagem concluída e triagem em andamento por IA.
timestamp: 2026-08-09T23:45:00-03:00
status: approved
version: 1.1.0
owner: psychnote-mfe
tags: [layout, record, history, patient, triage, pending-state]
related:
  - ../views/NewPatientEvolutionView.spec.md
  - ../views/PatientListView.spec.md
  - ../components/clinical-risk-badge/ClinicalRiskBadge.spec.md
---

# LayoutSpec: PatientRecordView

## 1. Composição Estrutural

```
PatientRecordView
├── [Slot: Navegação de Retorno]
│   └── Botão "Voltar para a Listagem de Pacientes" → NavLink para /patients
│
├── [Slot: Cabeçalho do Prontuário]
│   ├── Avatar + Ícone de Usuário
│   ├── Rótulo: "Prontuário Psiquiátrico"
│   ├── Título: Nome Completo do Paciente (Humanizado / Sem exposição de ID)
│   └── Botão: "+ Iniciar Nova Evolução" → NavLink para /patients/:patientId/triage
│
└── [Slot: Histórico de Evoluções e Triagens]
    ├── [Estado Vazio] → "Nenhuma evolução registrada anteriormente para este paciente." + Botão "Realizar Primeira Evolução"
    │
    └── [Lista de Registros de Evolução]
        └── Cada Item de Evolução (`article`):
            ├── Cabeçalho do Item: Data da Avaliação + Badge de Risco (ou Badge "Análise de Risco em Andamento...")
            ├── Bloco da Evolução: Texto completo da evolução registrada
            │
            ├── [Triagem em Andamento (`has_triage === false`)]
            │   └── Card de Estado em Processamento:
            │       ├── Spinner animado + "Aguardando conclusão da triagem automatizada de risco por IA"
            │       └── Mensagem informativa: "A evolução foi salva no prontuário. O nível de risco, Red Flags, Fatores de Proteção e Alertas de Auditoria serão atualizados automaticamente."
            │
            └── [Triagem Concluída (`has_triage === true`)]
                ├── Grid de Red Flags Detectadas e Fatores de Proteção
                ├── Justificativa Clínica da síntese psiquiátrica
                └── Alertas de Auditoria Médica
```

## 2. Requisitos de UX/UI

- **Experiência de Triagem em Andamento**: Quando uma evolução é recém-cadastrada ou acessada via Listagem enquanto o job de IA processa no backend, o prontuário exibe imediatamente o texto da evolução e um indicador elegante de "Análise de Risco em Andamento...".
- **Humanização (LGPD)**: O nome completo é a referência principal no cabeçalho. Nenhum identificador numérico de banco de dados (`PAC-001`) é exposto na UI do usuário.

## 3. Requisitos de Acessibilidade (A11y)

- Elementos estruturais semânticos: `<header>`, `<main>`, `<section>`, `<article>`.
- O spinner animado possui texto descritivo correspondente para leitores de tela.
