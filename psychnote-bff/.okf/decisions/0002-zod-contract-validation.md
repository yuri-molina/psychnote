---
type: Decision
title: "ADR-0002: Validação de Contrato em Runtime com Zod (Bidirecional)"
description: Decisão de usar Zod para validar tanto os payloads de entrada do MFE quanto os responses do Core, garantindo que nenhum JSON inválido transite através do BFF sem detecção.
timestamp: 2026-08-07T16:55:00-03:00
status: active
version: 1.0.0
related:
  - ./0001-fastify-framework.md
  - ./0003-timeout-and-resilience.md
  - ../contracts/core-api.md
  - ../contracts/bff-api.md
---

## Contexto

O BFF situa-se entre dois sistemas heterogêneos: um frontend TypeScript (MFE) e um backend Python (Core). Desvios de contrato podem ocorrer de duas direções:

1. **MFE → BFF:** O MFE pode enviar payloads malformados (campo ausente, tipo incorreto).
2. **Core → BFF:** O Core pode retornar JSON inválido, parcial ou com campos renomeados após uma atualização.

Sem validação de contrato bidirecional, o BFF poderia repassar dados inválidos ao MFE silenciosamente, resultando em erro de renderização no cliente ou, pior, exibindo dados clínicos errôneos ao profissional de saúde.

## Decisão

Zod será usado para validação bidirecional:

**Direção MFE → BFF (validação de entrada):**
O `fastify-type-provider-zod` valida automaticamente o `request.body` de acordo com o schema Zod declarado na definição da rota. Payloads inválidos resultam em `400 Bad Request` automático sem código adicional.

**Direção Core → BFF (validação de upstream):**
Após receber o response do Core, o BFF executa `TriageResponseSchema.safeParse(data)`. Se a validação falhar, o BFF retorna `502 Bad Gateway` com payload de erro estruturado. O response inválido nunca é repassado ao MFE.

## Schemas Zod Centralizados (`src/schemas/index.ts`)

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
  patient_id: z.string().min(1, 'patient_id é obrigatório'),
  current_note: z.string().min(10, 'Nota clínica deve ter no mínimo 10 caracteres'),
});

export const PatientSchema = z.object({
  patient_id: z.string(),
});

export const PatientsResponseSchema = z.array(PatientSchema);

export const ErrorResponseSchema = z.object({
  statusCode: z.number(),
  error: z.string(),
  message: z.string(),
  upstream: z.string().optional(),
});

export type TriageResponse = z.infer<typeof TriageResponseSchema>;
export type TriageRequest = z.infer<typeof TriageRequestSchema>;
export type ErrorResponse = z.infer<typeof ErrorResponseSchema>;
```

## Consequências

- `src/schemas/index.ts` é a fonte única de verdade dos tipos de contrato no BFF. Tipos TypeScript são inferidos com `z.infer<>`, não declarados manualmente em paralelo.
- Qualquer alteração no contrato do Core deve ser refletida primeiro nos schemas deste arquivo.
- O MFE e o BFF devem manter schemas compatíveis (mesmos campos e tipos). Incompatibilidades serão detectadas explicitamente em desenvolvimento via `ZodError`.
