---
type: Architecture
title: Estrutura de Diretórios — psychnote-mfe
description: Layout canônico do diretório src/ com responsabilidades e convenções de nomenclatura de arquivos.
timestamp: 2026-08-07T14:35:00-03:00
status: active
version: 1.0.0
related:
  - ./component-tree.md
  - ../specs/components/
  - ../decisions/0001-standalone-first.md
---

# Estrutura de Diretórios — psychnote-mfe

## Layout do Repositório

```
psychnote-mfe/
├── .okf/                          # Base de conhecimento OKF (specs, ADRs, contratos)
├── public/                        # Assets estáticos servidos sem processamento
├── src/
│   ├── components/
│   │   ├── ui/                    # Componentes shadcn/ui gerados pelo CLI (não editar manualmente)
│   │   ├── clinical-risk-badge/
│   │   │   ├── ClinicalRiskBadge.tsx
│   │   │   └── ClinicalRiskBadge.stories.tsx
│   │   ├── triage-form/
│   │   │   ├── TriageForm.tsx
│   │   │   └── TriageForm.stories.tsx
│   │   ├── triage-result/
│   │   │   ├── TriageResult.tsx
│   │   │   └── TriageResult.stories.tsx
│   │   ├── audit-alerts/
│   │   │   ├── AuditAlerts.tsx
│   │   │   └── AuditAlerts.stories.tsx
│   │   └── patient-card/
│   │       ├── PatientCard.tsx
│   │       └── PatientCard.stories.tsx
│   ├── views/
│   │   ├── PatientListView.tsx    # Tela 1: listagem de pacientes
│   │   ├── PatientDetailView.tsx  # Tela 2: formulário de triagem
│   │   └── TriageResultView.tsx   # Tela 3: resultado da triagem
│   ├── hooks/
│   │   ├── usePatients.ts         # TanStack Query: GET /patients
│   │   └── useTriage.ts           # TanStack Query mutation: POST /triage
│   ├── lib/
│   │   ├── api.ts                 # Configuração do HTTP client (baseURL via VITE_BFF_URL)
│   │   ├── schemas.ts             # Schemas Zod — fonte única de verdade dos tipos de API
│   │   └── utils.ts               # cn() e utilitários gerais
│   ├── App.tsx                    # Router + layout raiz
│   ├── main.tsx                   # Ponto de entrada standalone (dev)
│   ├── PsychnoteMfe.tsx           # Ponto de entrada Module Federation (exposto via federation)
│   └── index.css                  # Tailwind base + variáveis CSS escopadas em .psychnote-mfe-root
├── components.json                # Configuração shadcn/ui (prefix: psy-)
├── tailwind.config.js             # Tailwind (prefix: psy-)
├── tsconfig.json                  # TypeScript strict mode
├── vite.config.ts                 # Vite + @originjs/vite-plugin-federation
├── .env.local                     # Variáveis de ambiente locais (não versionadas)
└── package.json
```

## Convenções de Nomenclatura

| Categoria | Convenção | Exemplo |
| :--- | :--- | :--- |
| Componentes React | PascalCase por arquivo, diretório em kebab-case | `components/clinical-risk-badge/ClinicalRiskBadge.tsx` |
| Hooks customizados | camelCase com prefixo `use` | `hooks/useTriage.ts` |
| Views (telas) | PascalCase com sufixo `View` | `views/PatientListView.tsx` |
| Schemas Zod | camelCase com sufixo `Schema` | `TriageResponseSchema` |
| Tipos inferidos | PascalCase sem sufixo | `TriageResponse`, `RiskLevel` |
| Arquivos de stories | Mesmo nome do componente + `.stories.tsx` | `ClinicalRiskBadge.stories.tsx` |

## Regras de Colocação (Co-location)

- Cada componente vive em seu próprio subdiretório dentro de `src/components/`.
- O arquivo de story (`.stories.tsx`) fica no mesmo diretório do componente.
- Hooks que chamam a API vivem em `src/hooks/` e são importados pelas views.
- Nenhuma lógica de fetch ou mutação deve existir diretamente em componentes — apenas em hooks.
- O diretório `src/components/ui/` é gerenciado exclusivamente pelo CLI do shadcn/ui.
