---
type: Architecture
title: Árvore de Componentes — psychnote-mfe
description: Hierarquia de componentes, responsabilidades por nível e regras de composição. Fonte de verdade para relações pai-filho entre componentes.
timestamp: 2026-08-09T01:00:00-03:00
status: active
version: 2.1.0
related:
  - ./folder-structure.md
  - ../../src/components/clinical-risk-badge/ClinicalRiskBadge.spec.md
  - ../../src/components/triage-form/TriageForm.spec.md
  - ../../src/components/triage-result/TriageResult.spec.md
  - ../../src/components/audit-alerts/AuditAlerts.spec.md
  - ../../src/components/patient-card/PatientCard.spec.md
  - ../../src/views/LandingView.spec.md
  - ../../src/views/NewPatientEvolutionView.spec.md
  - ../../src/views/PatientListView.spec.md
  - ../../src/views/PatientRecordView.spec.md
  - ../../src/views/TriageLayout.spec.md
---

# Árvore de Componentes — psychnote-mfe

## Hierarquia por View

```
App (Router)
├── LandingView (/)
│   └── CTAs: "Evoluir Novo Paciente" (/patients/new-evolution) | "Listar Pacientes" (/patients)
│
├── PatientListView (/patients)
│   └── PatientCard[]               (um por paciente, botões Ver Prontuário | Nova Evolução)
│
├── NewPatientEvolutionView (/patients/new-evolution)
│   ├── Form: Cadastro de Novo Paciente (patient_id + name)
│   ├── TriageForm                  (Evolução clínica)
│   └── TriageResult                (Parecer após stream SSE)
│
├── PatientRecordView (/patients/:patientId/record)
│   ├── Prontuário do Paciente (Header)
│   ├── Timeline de Histórico de Evoluções
│   ├── ClinicalRiskBadge
│   └── AuditAlerts
│
└── TriageLayout (/patients/:patientId/triage)
    ├── TriageForm                  (Evolução clínica para paciente existente)
    └── TriageResult                (Resultado do parecer)
```

## Tabela de Responsabilidades por View

| View | Rota | Responsabilidade Principal |
| :--- | :--- | :--- |
| `LandingView` | `/` | Menu inicial com CTAs de destaque para Evoluir Novo Paciente ou Listar Pacientes |
| `PatientListView` | `/patients` | Listagem de pacientes cadastrados com ações diretas |
| `NewPatientEvolutionView` | `/patients/new-evolution` | Cadastro de novo paciente + redação de evolução clínica + triagem SSE |
| `PatientRecordView` | `/patients/:patientId/record` | Exibição do prontuário histórico do paciente no ChromaDB |
| `TriageLayout` | `/patients/:patientId/triage` | Redação de evolução para paciente existente |
