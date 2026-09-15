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
// HTTP 202 Async Triage Request/Response
export const TriageAsyncRequestSchema = z.object({
    patient_id: z.string().min(1, 'patient_id é obrigatório'),
    current_note: z.string().min(10, 'Nota clínica deve ter no mínimo 10 caracteres'),
});
export const TriageAsyncResponseSchema = z.object({
    job_id: z.string().uuid(),
    patient_id: z.string(),
    status: z.literal('processing'),
    message: z.string(),
});
// Webhook payload received from Core
export const WebhookPayloadSchema = z.object({
    job_id: z.string().uuid(),
    patient_id: z.string(),
    status: z.literal('completed'),
    risk_assessment: RiskAssessmentSchema,
    audit_alerts: z.array(z.string()),
    final_report: z.string(),
});
// Job Status (in-memory store)
export const JobStatusSchema = z.enum(['processing', 'completed', 'error']);
export const JobStatusResponseSchema = z.object({
    job_id: z.string().uuid(),
    patient_id: z.string(),
    status: JobStatusSchema,
    created_at: z.string(),
    risk_assessment: RiskAssessmentSchema.nullable(),
    audit_alerts: z.array(z.string()),
    error_message: z.string().nullable(),
});
// Patient Record Schemas (MFE record view)
// has_triage: false when still processing, true when AI completed
export const TriageHistoryItemSchema = z.object({
    id: z.string(),
    date: z.string(),
    current_note: z.string(),
    has_triage: z.boolean(),
    risk_level: RiskLevelSchema.nullable().optional(),
    red_flags: z.array(z.string()),
    protection_factors: z.array(z.string()),
    clinical_justification: z.string().nullable().optional(),
    audit_alerts: z.array(z.string()),
});
export const PatientRecordSchema = z.object({
    patient_id: z.string(),
    name: z.string().optional(),
    last_triage_date: z.string().optional(),
    active_job_id: z.string().uuid().nullable().optional(),
    active_job_status: z.enum(['processing']).nullable().optional(),
    total_records: z.number().optional(),
    history: z.array(TriageHistoryItemSchema),
});
// Patient History Schemas (Core ChromaDB history)
export const PatientHistoryItemSchema = z.object({
    timestamp: z.string(),
    note_text: z.string(),
    has_triage: z.boolean(),
    risk_level: RiskLevelSchema.optional(),
    passive_ideation: z.boolean().optional(),
    active_ideation: z.boolean().optional(),
    red_flags: z.array(z.string()).optional(),
    protection_factors: z.array(z.string()).optional(),
    clinical_justification: z.string().optional(),
    audit_alerts: z.array(z.string()).optional(),
    final_report: z.string().optional(),
});
export const PatientHistoryResponseSchema = z.object({
    patient_id: z.string(),
    total_records: z.number(),
    history: z.array(PatientHistoryItemSchema),
});
export const PatientSchema = z.object({
    patient_id: z.string(),
    name: z.string().optional(),
    last_triage_date: z.string().optional(),
    last_risk_level: RiskLevelSchema.optional(),
});
export const PatientsResponseSchema = z.array(PatientSchema);
export const ErrorResponseSchema = z.object({
    statusCode: z.number(),
    error: z.string(),
    message: z.string(),
    upstream: z.string().optional(),
});
//# sourceMappingURL=index.js.map