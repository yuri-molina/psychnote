import fp from 'fastify-plugin';
export const jobStorePlugin = fp(async (fastify) => {
    // In-memory stores
    const jobs = new Map();
    // Maps patient_id → active job_id (only jobs in "processing" state)
    const activeJobsByPatient = new Map();
    const store = {
        createJob(job_id, patient_id, current_note) {
            const entry = {
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
        getJob(job_id) {
            return jobs.get(job_id);
        },
        getActiveJobForPatient(patient_id) {
            const activeJobId = activeJobsByPatient.get(patient_id);
            if (!activeJobId)
                return undefined;
            const job = jobs.get(activeJobId);
            // Only return if still processing
            if (job?.status === 'processing')
                return activeJobId;
            // Clean up stale mapping
            activeJobsByPatient.delete(patient_id);
            return undefined;
        },
        completeJob(job_id, result) {
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
        failJob(job_id, error_message) {
            const entry = jobs.get(job_id);
            if (!entry)
                return;
            entry.status = 'error';
            entry.error_message = error_message;
            activeJobsByPatient.delete(entry.patient_id);
            fastify.log.warn({ job_id, patient_id: entry.patient_id }, 'Job marked as error in store');
        },
    };
    fastify.decorate('jobStore', store);
});
//# sourceMappingURL=job-store.plugin.js.map