---
type: Decision
title: "ADR-0004: Validação de Contratos de API em Runtime com Zod"
description: Decisão de validar todos os responses do BFF com schemas Zod antes de renderizar dados clínicos, evitando falhas silenciosas em domínio de alta criticidade.
timestamp: 2026-08-07T12:00:00-03:00
status: active
version: 1.0.0
resource: ../../src/lib/schemas.ts
related:
  - ../contracts/core-api.md
  - ../contracts/bff-api.md
  - ../domain/clinical-triage.md
---

# ADR-0004: Validação de Contratos de API em Runtime com Zod

## Contexto

O campo `risk_level` retornado pelo pipeline de triagem determina a classificação visual de risco exibida ao profissional de saúde. Um valor ausente, nulo ou malformado renderizado silenciosamente como "Baixo" (fallback padrão) configuraria uma falha de segurança clínica: um paciente em risco Alto/Iminente poderia ser apresentado com indicador de risco baixo.

Adicionalmente, o BFF está sendo desenvolvido em paralelo por um agente separado. Desvios de contrato entre BFF e Core podem ocorrer durante o desenvolvimento e não seriam detectados apenas pela tipagem estática do TypeScript, pois os tipos TypeScript são apagados em runtime.

## Decisão

Todos os responses do BFF são validados com `schema.parse()` do Zod antes de serem passados para qualquer componente React. A validação ocorre dentro do hook TanStack Query (`queryFn` / `mutationFn`), garantindo que dados inválidos nunca cheguem à camada de renderização.

## Schemas Definidos (src/lib/schemas.ts)

```typescript
import { z } from 'zod';

export const RiskLevelSchema = z.enum(['Baixo', 'Moderado', 'Alto/Iminente']);

export const RiskAssessmentSchema = z.object({
  risk_level: RiskLevelSchema,
  passive_ideation: z.boolean(),
  active_ideation: z.boolean(),
  red_flags: z.array(z.string()),
  protection_factors: z.array(z.string()),
  clinical_justification: z.string(),
});

export const TriageResponseSchema = z.object({
  patient_id: z.string(),
  risk_assessment: RiskAssessmentSchema,
  audit_alerts: z.array(z.string()),
  final_report: z.string(),
});

export const TriageRequestSchema = z.object({
  patient_id: z.string().min(1),
  current_note: z.string().min(10),
});

export type RiskLevel = z.infer<typeof RiskLevelSchema>;
export type TriageResponse = z.infer<typeof TriageResponseSchema>;
export type TriageRequest = z.infer<typeof TriageRequestSchema>;
```

## Comportamento em Caso de Falha de Validação

Um `ZodError` lançado na `mutationFn` do TanStack Query é capturado pelo estado de erro da mutation (`isError: true`, `error: ZodError`). O componente de resultado deve exibir um estado de erro claro e informativo ao profissional, nunca silenciar o erro nem renderizar dados parciais.

## Consequências

- O contrato do BFF deve ser compatível com `TriageResponseSchema`. Incompatibilidades são detectadas explicitamente em desenvolvimento.
- Os schemas Zod são a fonte única de verdade dos tipos de dados de API no MFE. Os tipos TypeScript são inferidos a partir dos schemas (`z.infer<>`), não declarados manualmente em paralelo.
- Atualizações no contrato do Core ou do BFF devem ser refletidas primeiro nos schemas Zod em `src/lib/schemas.ts`.
