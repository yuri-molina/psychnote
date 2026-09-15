import fp from 'fastify-plugin';
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
  completeJob(job_id: string, result: { risk_assessment: RiskAssessment; audit_alerts: string[]; final_report: string }): void;
  /** Mark a job as errored */
  failJob(job_id: string, error_message: string): void;
}

declare module 'fastify' {
  interface FastifyInstance {
    jobStore: JobStore;
  }
}

export const jobStorePlugin: FastifyPluginAsync = fp(async (fastify) => {
  // In-memory stores
  const jobs = new Map<string, JobEntry>();
  // Maps patient_id → active job_id (only jobs in "processing" state)
  const activeJobsByPatient = new Map<string, string>();

  const store: JobStore = {
    createJob(job_id: string, patient_id: string, current_note: string): void {
      const entry: JobEntry = {
        job_id,
        patient_id,
        current_note,
        status: 'processing',
        created_at: new Date().toISOString(),
        risk_assessment: null,
        audit_alerts: [],
        final_report: null,
        error_message: null,
      };
      jobs.set(job_id, entry);
      activeJobsByPatient.set(patient_id, job_id);
      fastify.log.info({ job_id, patient_id }, 'Job registered in store');
    },

    getJob(job_id: string): JobEntry | undefined {
      return jobs.get(job_id);
    },

    getActiveJobForPatient(patient_id: string): string | undefined {
      const activeJobId = activeJobsByPatient.get(patient_id);
      if (!activeJobId) return undefined;
      const job = jobs.get(activeJobId);
      // Only return if still processing
      if (job?.status === 'processing') return activeJobId;
      // Clean up stale mapping
      activeJobsByPatient.delete(patient_id);
      return undefined;
    },

    completeJob(job_id: string, result: { risk_assessment: RiskAssessment; audit_alerts: string[]; final_report: string }): void {
      const entry = jobs.get(job_id);
      if (!entry) {
        fastify.log.warn({ job_id }, 'Attempted to complete unknown job');
        return;
      }
      entry.status = 'completed';
      entry.risk_assessment = result.risk_assessment;
      entry.audit_alerts = result.audit_alerts;
      entry.final_report = result.final_report;
      // Remove from active mapping
      activeJobsByPatient.delete(entry.patient_id);
      fastify.log.info({ job_id, patient_id: entry.patient_id }, 'Job marked as completed in store');
    },

    failJob(job_id: string, error_message: string): void {
      const entry = jobs.get(job_id);
      if (!entry) return;
      entry.status = 'error';
      entry.error_message = error_message;
      activeJobsByPatient.delete(entry.patient_id);
      fastify.log.warn({ job_id, patient_id: entry.patient_id }, 'Job marked as error in store');
    },
  };

  fastify.decorate('jobStore', store);
});
