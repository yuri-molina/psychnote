import { z } from 'zod';
export declare const RiskLevelSchema: z.ZodEnum<["Baixo", "Moderado", "Alto/Iminente"]>;
export declare const RiskAssessmentSchema: z.ZodObject<{
    risk_level: z.ZodEnum<["Baixo", "Moderado", "Alto/Iminente"]>;
    passive_ideation: z.ZodBoolean;
    active_ideation: z.ZodBoolean;
    red_flags: z.ZodArray<z.ZodString, "many">;
    protection_factors: z.ZodArray<z.ZodString, "many">;
    clinical_justification: z.ZodString;
}, "strip", z.ZodTypeAny, {
    risk_level: "Baixo" | "Moderado" | "Alto/Iminente";
    passive_ideation: boolean;
    active_ideation: boolean;
    red_flags: string[];
    protection_factors: string[];
    clinical_justification: string;
}, {
    risk_level: "Baixo" | "Moderado" | "Alto/Iminente";
    passive_ideation: boolean;
    active_ideation: boolean;
    red_flags: string[];
    protection_factors: string[];
    clinical_justification: string;
}>;
export declare const TriageResponseSchema: z.ZodObject<{
    patient_id: z.ZodString;
    risk_assessment: z.ZodObject<{
        risk_level: z.ZodEnum<["Baixo", "Moderado", "Alto/Iminente"]>;
        passive_ideation: z.ZodBoolean;
        active_ideation: z.ZodBoolean;
        red_flags: z.ZodArray<z.ZodString, "many">;
        protection_factors: z.ZodArray<z.ZodString, "many">;
        clinical_justification: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        risk_level: "Baixo" | "Moderado" | "Alto/Iminente";
        passive_ideation: boolean;
        active_ideation: boolean;
        red_flags: string[];
        protection_factors: string[];
        clinical_justification: string;
    }, {
        risk_level: "Baixo" | "Moderado" | "Alto/Iminente";
        passive_ideation: boolean;
        active_ideation: boolean;
        red_flags: string[];
        protection_factors: string[];
        clinical_justification: string;
    }>;
    audit_alerts: z.ZodArray<z.ZodString, "many">;
    final_report: z.ZodString;
}, "strip", z.ZodTypeAny, {
    patient_id: string;
    risk_assessment: {
        risk_level: "Baixo" | "Moderado" | "Alto/Iminente";
        passive_ideation: boolean;
        active_ideation: boolean;
        red_flags: string[];
        protection_factors: string[];
        clinical_justification: string;
    };
    audit_alerts: string[];
    final_report: string;
}, {
    patient_id: string;
    risk_assessment: {
        risk_level: "Baixo" | "Moderado" | "Alto/Iminente";
        passive_ideation: boolean;
        active_ideation: boolean;
        red_flags: string[];
        protection_factors: string[];
        clinical_justification: string;
    };
    audit_alerts: string[];
    final_report: string;
}>;
export declare const TriageAsyncRequestSchema: z.ZodObject<{
    patient_id: z.ZodString;
    current_note: z.ZodString;
}, "strip", z.ZodTypeAny, {
    patient_id: string;
    current_note: string;
}, {
    patient_id: string;
    current_note: string;
}>;
export declare const TriageAsyncResponseSchema: z.ZodObject<{
    job_id: z.ZodString;
    patient_id: z.ZodString;
    status: z.ZodLiteral<"processing">;
    message: z.ZodString;
}, "strip", z.ZodTypeAny, {
    status: "processing";
    message: string;
    patient_id: string;
    job_id: string;
}, {
    status: "processing";
    message: string;
    patient_id: string;
    job_id: string;
}>;
export declare const WebhookPayloadSchema: z.ZodObject<{
    job_id: z.ZodString;
    patient_id: z.ZodString;
    status: z.ZodLiteral<"completed">;
    risk_assessment: z.ZodObject<{
        risk_level: z.ZodEnum<["Baixo", "Moderado", "Alto/Iminente"]>;
        passive_ideation: z.ZodBoolean;
        active_ideation: z.ZodBoolean;
        red_flags: z.ZodArray<z.ZodString, "many">;
        protection_factors: z.ZodArray<z.ZodString, "many">;
        clinical_justification: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        risk_level: "Baixo" | "Moderado" | "Alto/Iminente";
        passive_ideation: boolean;
        active_ideation: boolean;
        red_flags: string[];
        protection_factors: string[];
        clinical_justification: string;
    }, {
        risk_level: "Baixo" | "Moderado" | "Alto/Iminente";
        passive_ideation: boolean;
        active_ideation: boolean;
        red_flags: string[];
        protection_factors: string[];
        clinical_justification: string;
    }>;
    audit_alerts: z.ZodArray<z.ZodString, "many">;
    final_report: z.ZodString;
}, "strip", z.ZodTypeAny, {
    status: "completed";
    patient_id: string;
    risk_assessment: {
        risk_level: "Baixo" | "Moderado" | "Alto/Iminente";
        passive_ideation: boolean;
        active_ideation: boolean;
        red_flags: string[];
        protection_factors: string[];
        clinical_justification: string;
    };
    audit_alerts: string[];
    final_report: string;
    job_id: string;
}, {
    status: "completed";
    patient_id: string;
    risk_assessment: {
        risk_level: "Baixo" | "Moderado" | "Alto/Iminente";
        passive_ideation: boolean;
        active_ideation: boolean;
        red_flags: string[];
        protection_factors: string[];
        clinical_justification: string;
    };
    audit_alerts: string[];
    final_report: string;
    job_id: string;
}>;
export declare const JobStatusSchema: z.ZodEnum<["processing", "completed", "error"]>;
export declare const JobStatusResponseSchema: z.ZodObject<{
    job_id: z.ZodString;
    patient_id: z.ZodString;
    status: z.ZodEnum<["processing", "completed", "error"]>;
    created_at: z.ZodString;
    risk_assessment: z.ZodNullable<z.ZodObject<{
        risk_level: z.ZodEnum<["Baixo", "Moderado", "Alto/Iminente"]>;
        passive_ideation: z.ZodBoolean;
        active_ideation: z.ZodBoolean;
        red_flags: z.ZodArray<z.ZodString, "many">;
        protection_factors: z.ZodArray<z.ZodString, "many">;
        clinical_justification: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        risk_level: "Baixo" | "Moderado" | "Alto/Iminente";
        passive_ideation: boolean;
        active_ideation: boolean;
        red_flags: string[];
        protection_factors: string[];
        clinical_justification: string;
    }, {
        risk_level: "Baixo" | "Moderado" | "Alto/Iminente";
        passive_ideation: boolean;
        active_ideation: boolean;
        red_flags: string[];
        protection_factors: string[];
        clinical_justification: string;
    }>>;
    audit_alerts: z.ZodArray<z.ZodString, "many">;
    error_message: z.ZodNullable<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    status: "error" | "processing" | "completed";
    patient_id: string;
    risk_assessment: {
        risk_level: "Baixo" | "Moderado" | "Alto/Iminente";
        passive_ideation: boolean;
        active_ideation: boolean;
        red_flags: string[];
        protection_factors: string[];
        clinical_justification: string;
    } | null;
    audit_alerts: string[];
    job_id: string;
    created_at: string;
    error_message: string | null;
}, {
    status: "error" | "processing" | "completed";
    patient_id: string;
    risk_assessment: {
        risk_level: "Baixo" | "Moderado" | "Alto/Iminente";
        passive_ideation: boolean;
        active_ideation: boolean;
        red_flags: string[];
        protection_factors: string[];
        clinical_justification: string;
    } | null;
    audit_alerts: string[];
    job_id: string;
    created_at: string;
    error_message: string | null;
}>;
export declare const TriageHistoryItemSchema: z.ZodObject<{
    id: z.ZodString;
    date: z.ZodString;
    current_note: z.ZodString;
    has_triage: z.ZodBoolean;
    risk_level: z.ZodOptional<z.ZodNullable<z.ZodEnum<["Baixo", "Moderado", "Alto/Iminente"]>>>;
    red_flags: z.ZodArray<z.ZodString, "many">;
    protection_factors: z.ZodArray<z.ZodString, "many">;
    clinical_justification: z.ZodOptional<z.ZodNullable<z.ZodString>>;
    audit_alerts: z.ZodArray<z.ZodString, "many">;
}, "strip", z.ZodTypeAny, {
    date: string;
    red_flags: string[];
    protection_factors: string[];
    audit_alerts: string[];
    current_note: string;
    id: string;
    has_triage: boolean;
    risk_level?: "Baixo" | "Moderado" | "Alto/Iminente" | null | undefined;
    clinical_justification?: string | null | undefined;
}, {
    date: string;
    red_flags: string[];
    protection_factors: string[];
    audit_alerts: string[];
    current_note: string;
    id: string;
    has_triage: boolean;
    risk_level?: "Baixo" | "Moderado" | "Alto/Iminente" | null | undefined;
    clinical_justification?: string | null | undefined;
}>;
export declare const PatientRecordSchema: z.ZodObject<{
    patient_id: z.ZodString;
    name: z.ZodOptional<z.ZodString>;
    last_triage_date: z.ZodOptional<z.ZodString>;
    active_job_id: z.ZodOptional<z.ZodNullable<z.ZodString>>;
    active_job_status: z.ZodOptional<z.ZodNullable<z.ZodEnum<["processing"]>>>;
    total_records: z.ZodOptional<z.ZodNumber>;
    history: z.ZodArray<z.ZodObject<{
        id: z.ZodString;
        date: z.ZodString;
        current_note: z.ZodString;
        has_triage: z.ZodBoolean;
        risk_level: z.ZodOptional<z.ZodNullable<z.ZodEnum<["Baixo", "Moderado", "Alto/Iminente"]>>>;
        red_flags: z.ZodArray<z.ZodString, "many">;
        protection_factors: z.ZodArray<z.ZodString, "many">;
        clinical_justification: z.ZodOptional<z.ZodNullable<z.ZodString>>;
        audit_alerts: z.ZodArray<z.ZodString, "many">;
    }, "strip", z.ZodTypeAny, {
        date: string;
        red_flags: string[];
        protection_factors: string[];
        audit_alerts: string[];
        current_note: string;
        id: string;
        has_triage: boolean;
        risk_level?: "Baixo" | "Moderado" | "Alto/Iminente" | null | undefined;
        clinical_justification?: string | null | undefined;
    }, {
        date: string;
        red_flags: string[];
        protection_factors: string[];
        audit_alerts: string[];
        current_note: string;
        id: string;
        has_triage: boolean;
        risk_level?: "Baixo" | "Moderado" | "Alto/Iminente" | null | undefined;
        clinical_justification?: string | null | undefined;
    }>, "many">;
}, "strip", z.ZodTypeAny, {
    patient_id: string;
    history: {
        date: string;
        red_flags: string[];
        protection_factors: string[];
        audit_alerts: string[];
        current_note: string;
        id: string;
        has_triage: boolean;
        risk_level?: "Baixo" | "Moderado" | "Alto/Iminente" | null | undefined;
        clinical_justification?: string | null | undefined;
    }[];
    name?: string | undefined;
    last_triage_date?: string | undefined;
    active_job_id?: string | null | undefined;
    active_job_status?: "processing" | null | undefined;
    total_records?: number | undefined;
}, {
    patient_id: string;
    history: {
        date: string;
        red_flags: string[];
        protection_factors: string[];
        audit_alerts: string[];
        current_note: string;
        id: string;
        has_triage: boolean;
        risk_level?: "Baixo" | "Moderado" | "Alto/Iminente" | null | undefined;
        clinical_justification?: string | null | undefined;
    }[];
    name?: string | undefined;
    last_triage_date?: string | undefined;
    active_job_id?: string | null | undefined;
    active_job_status?: "processing" | null | undefined;
    total_records?: number | undefined;
}>;
export declare const PatientHistoryItemSchema: z.ZodObject<{
    timestamp: z.ZodString;
    note_text: z.ZodString;
    has_triage: z.ZodBoolean;
    risk_level: z.ZodOptional<z.ZodEnum<["Baixo", "Moderado", "Alto/Iminente"]>>;
    passive_ideation: z.ZodOptional<z.ZodBoolean>;
    active_ideation: z.ZodOptional<z.ZodBoolean>;
    red_flags: z.ZodOptional<z.ZodArray<z.ZodString, "many">>;
    protection_factors: z.ZodOptional<z.ZodArray<z.ZodString, "many">>;
    clinical_justification: z.ZodOptional<z.ZodString>;
    audit_alerts: z.ZodOptional<z.ZodArray<z.ZodString, "many">>;
    final_report: z.ZodOptional<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    has_triage: boolean;
    timestamp: string;
    note_text: string;
    risk_level?: "Baixo" | "Moderado" | "Alto/Iminente" | undefined;
    passive_ideation?: boolean | undefined;
    active_ideation?: boolean | undefined;
    red_flags?: string[] | undefined;
    protection_factors?: string[] | undefined;
    clinical_justification?: string | undefined;
    audit_alerts?: string[] | undefined;
    final_report?: string | undefined;
}, {
    has_triage: boolean;
    timestamp: string;
    note_text: string;
    risk_level?: "Baixo" | "Moderado" | "Alto/Iminente" | undefined;
    passive_ideation?: boolean | undefined;
    active_ideation?: boolean | undefined;
    red_flags?: string[] | undefined;
    protection_factors?: string[] | undefined;
    clinical_justification?: string | undefined;
    audit_alerts?: string[] | undefined;
    final_report?: string | undefined;
}>;
export declare const PatientHistoryResponseSchema: z.ZodObject<{
    patient_id: z.ZodString;
    total_records: z.ZodNumber;
    history: z.ZodArray<z.ZodObject<{
        timestamp: z.ZodString;
        note_text: z.ZodString;
        has_triage: z.ZodBoolean;
        risk_level: z.ZodOptional<z.ZodEnum<["Baixo", "Moderado", "Alto/Iminente"]>>;
        passive_ideation: z.ZodOptional<z.ZodBoolean>;
        active_ideation: z.ZodOptional<z.ZodBoolean>;
        red_flags: z.ZodOptional<z.ZodArray<z.ZodString, "many">>;
        protection_factors: z.ZodOptional<z.ZodArray<z.ZodString, "many">>;
        clinical_justification: z.ZodOptional<z.ZodString>;
        audit_alerts: z.ZodOptional<z.ZodArray<z.ZodString, "many">>;
        final_report: z.ZodOptional<z.ZodString>;
    }, "strip", z.ZodTypeAny, {
        has_triage: boolean;
        timestamp: string;
        note_text: string;
        risk_level?: "Baixo" | "Moderado" | "Alto/Iminente" | undefined;
        passive_ideation?: boolean | undefined;
        active_ideation?: boolean | undefined;
        red_flags?: string[] | undefined;
        protection_factors?: string[] | undefined;
        clinical_justification?: string | undefined;
        audit_alerts?: string[] | undefined;
        final_report?: string | undefined;
    }, {
        has_triage: boolean;
        timestamp: string;
        note_text: string;
        risk_level?: "Baixo" | "Moderado" | "Alto/Iminente" | undefined;
        passive_ideation?: boolean | undefined;
        active_ideation?: boolean | undefined;
        red_flags?: string[] | undefined;
        protection_factors?: string[] | undefined;
        clinical_justification?: string | undefined;
        audit_alerts?: string[] | undefined;
        final_report?: string | undefined;
    }>, "many">;
}, "strip", z.ZodTypeAny, {
    patient_id: string;
    total_records: number;
    history: {
        has_triage: boolean;
        timestamp: string;
        note_text: string;
        risk_level?: "Baixo" | "Moderado" | "Alto/Iminente" | undefined;
        passive_ideation?: boolean | undefined;
        active_ideation?: boolean | undefined;
        red_flags?: string[] | undefined;
        protection_factors?: string[] | undefined;
        clinical_justification?: string | undefined;
        audit_alerts?: string[] | undefined;
        final_report?: string | undefined;
    }[];
}, {
    patient_id: string;
    total_records: number;
    history: {
        has_triage: boolean;
        timestamp: string;
        note_text: string;
        risk_level?: "Baixo" | "Moderado" | "Alto/Iminente" | undefined;
        passive_ideation?: boolean | undefined;
        active_ideation?: boolean | undefined;
        red_flags?: string[] | undefined;
        protection_factors?: string[] | undefined;
        clinical_justification?: string | undefined;
        audit_alerts?: string[] | undefined;
        final_report?: string | undefined;
    }[];
}>;
export declare const PatientSchema: z.ZodObject<{
    patient_id: z.ZodString;
    name: z.ZodOptional<z.ZodString>;
    last_triage_date: z.ZodOptional<z.ZodString>;
    last_risk_level: z.ZodOptional<z.ZodEnum<["Baixo", "Moderado", "Alto/Iminente"]>>;
}, "strip", z.ZodTypeAny, {
    patient_id: string;
    name?: string | undefined;
    last_triage_date?: string | undefined;
    last_risk_level?: "Baixo" | "Moderado" | "Alto/Iminente" | undefined;
}, {
    patient_id: string;
    name?: string | undefined;
    last_triage_date?: string | undefined;
    last_risk_level?: "Baixo" | "Moderado" | "Alto/Iminente" | undefined;
}>;
export declare const PatientsResponseSchema: z.ZodArray<z.ZodObject<{
    patient_id: z.ZodString;
    name: z.ZodOptional<z.ZodString>;
    last_triage_date: z.ZodOptional<z.ZodString>;
    last_risk_level: z.ZodOptional<z.ZodEnum<["Baixo", "Moderado", "Alto/Iminente"]>>;
}, "strip", z.ZodTypeAny, {
    patient_id: string;
    name?: string | undefined;
    last_triage_date?: string | undefined;
    last_risk_level?: "Baixo" | "Moderado" | "Alto/Iminente" | undefined;
}, {
    patient_id: string;
    name?: string | undefined;
    last_triage_date?: string | undefined;
    last_risk_level?: "Baixo" | "Moderado" | "Alto/Iminente" | undefined;
}>, "many">;
export declare const ErrorResponseSchema: z.ZodObject<{
    statusCode: z.ZodNumber;
    error: z.ZodString;
    message: z.ZodString;
    upstream: z.ZodOptional<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    error: string;
    statusCode: number;
    message: string;
    upstream?: string | undefined;
}, {
    error: string;
    statusCode: number;
    message: string;
    upstream?: string | undefined;
}>;
export type RiskLevel = z.infer<typeof RiskLevelSchema>;
export type RiskAssessment = z.infer<typeof RiskAssessmentSchema>;
export type TriageResponse = z.infer<typeof TriageResponseSchema>;
export type TriageAsyncRequest = z.infer<typeof TriageAsyncRequestSchema>;
export type TriageAsyncResponse = z.infer<typeof TriageAsyncResponseSchema>;
export type WebhookPayload = z.infer<typeof WebhookPayloadSchema>;
export type JobStatus = z.infer<typeof JobStatusSchema>;
export type JobStatusResponse = z.infer<typeof JobStatusResponseSchema>;
export type TriageHistoryItem = z.infer<typeof TriageHistoryItemSchema>;
export type PatientRecord = z.infer<typeof PatientRecordSchema>;
export type PatientHistoryItem = z.infer<typeof PatientHistoryItemSchema>;
export type PatientHistoryResponse = z.infer<typeof PatientHistoryResponseSchema>;
export type Patient = z.infer<typeof PatientSchema>;
export type PatientsResponse = z.infer<typeof PatientsResponseSchema>;
export type ErrorResponse = z.infer<typeof ErrorResponseSchema>;
//# sourceMappingURL=index.d.ts.map