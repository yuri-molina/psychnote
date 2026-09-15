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
  job_id: z.string().optional(),
  patient_id: z.string(),
  status: z.string().optional(),
  risk_assessment: RiskAssessmentSchema,
  audit_alerts: z.array(z.string()),
  final_report: z.string(),
});

export const TriageRequestSchema = z.object({
  patient_id: z.string().min(1, 'ID do paciente é obrigatório'),
  current_note: z.string().min(10, 'A nota clínica deve ter no mínimo 10 caracteres'),
});

export const NewPatientEvolutionSchema = z.object({
  patient_id: z.string().min(3, 'O ID do paciente deve conter no mínimo 3 caracteres'),
  name: z.string().min(2, 'O nome do paciente deve conter no mínimo 2 caracteres'),
  current_note: z.string().min(10, 'A evolução clínica deve conter no mínimo 10 caracteres'),
});

export const TriageAsyncResponseSchema = z.object({
  job_id: z.string(),
  status: z.string(),
  message: z.string().optional(),
});

export const PatientSchema = z.object({
  patient_id: z.string(),
  name: z.string().optional(),
  last_triage_date: z.string().optional(),
  last_risk_level: RiskLevelSchema.optional(),
});

export const PatientsResponseSchema = z.array(PatientSchema);

export const TriageHistoryItemSchema = z.object({
  id: z.string().optional(),
  date: z.string().optional(),
  timestamp: z.string().optional(),
  current_note: z.string().optional(),
  note_text: z.string().optional(),
  has_triage: z.boolean().optional(),
  risk_level: RiskLevelSchema.optional(),
  passive_ideation: z.boolean().optional(),
  active_ideation: z.boolean().optional(),
  red_flags: z.array(z.string()).default([]),
  protection_factors: z.array(z.string()).default([]),
  clinical_justification: z.string().optional(),
  audit_alerts: z.array(z.string()).default([]),
  final_report: z.string().optional(),
});

export const PatientRecordSchema = z.object({
  patient_id: z.string(),
  name: z.string().optional(),
  last_triage_date: z.string().optional(),
  active_job_id: z.string().nullable().optional(),
  active_job_status: z.string().nullable().optional(),
  total_records: z.number().optional(),
  history: z.array(TriageHistoryItemSchema),
});

export type RiskLevel = z.infer<typeof RiskLevelSchema>;
export type RiskAssessment = z.infer<typeof RiskAssessmentSchema>;
export type TriageResponse = z.infer<typeof TriageResponseSchema>;
export type TriageRequest = z.infer<typeof TriageRequestSchema>;
export type NewPatientEvolution = z.infer<typeof NewPatientEvolutionSchema>;
export type TriageAsyncResponse = z.infer<typeof TriageAsyncResponseSchema>;
export type Patient = z.infer<typeof PatientSchema>;
export type TriageHistoryItem = z.infer<typeof TriageHistoryItemSchema>;
export type PatientRecord = z.infer<typeof PatientRecordSchema>;
