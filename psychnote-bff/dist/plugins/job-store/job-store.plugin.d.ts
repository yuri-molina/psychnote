import type { FastifyPluginAsync } from 'fastify';
import type { RiskAssessment, JobStatus } from '../../schemas/index.js';
export interface JobEntry {
    job_id: string;
    patient_id: string;
    current_note: string;
    status: JobStatus;
    created_at: string;
    risk_assessment: RiskAssessment | null;
    audit_alerts: string[];
    final_report: string | null;
    error_message: string | null;
}
export interface JobStore {
    /** Register a new job immediately when POST /api/triage is received */
    createJob(job_id: string, patient_id: string, current_note: string): void;
    /** Get a job by its ID */
    getJob(job_id: string): JobEntry | undefined;
    /** Get the active (processing) job_id for a given patient */
    getActiveJobForPatient(patient_id: string): string | undefined;
    /** Mark a job as completed with its results */
    completeJob(job_id: string, result: {
        risk_assessment: RiskAssessment;
        audit_alerts: string[];
        final_report: string;
    }): void;
    /** Mark a job as errored */
    failJob(job_id: string, error_message: string): void;
}
declare module 'fastify' {
    interface FastifyInstance {
        jobStore: JobStore;
    }
}
export declare const jobStorePlugin: FastifyPluginAsync;
//# sourceMappingURL=job-store.plugin.d.ts.map