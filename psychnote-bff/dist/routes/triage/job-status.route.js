import { z } from 'zod';
import { JobStatusResponseSchema, ErrorResponseSchema } from '../../schemas/index.js';
export const jobStatusRoute = async (fastify) => {
    const app = fastify.withTypeProvider();
    const jobStatusHandler = async (request, reply) => {
        const { jobId } = request.params;
        const job = fastify.jobStore.getJob(jobId);
        if (!job) {
            return reply.code(404).send({
                statusCode: 404,
                error: 'Not Found',
                message: `Job de triagem ${jobId} não encontrado.`,
            });
        }
        return reply.code(200).send({
            job_id: job.job_id,
            patient_id: job.patient_id,
            status: job.status,
            created_at: job.created_at,
            risk_assessment: job.risk_assessment,
            audit_alerts: job.audit_alerts,
            error_message: job.error_message,
        });
    };
    const schema = {
        params: z.object({ jobId: z.string().uuid() }),
        response: {
            200: JobStatusResponseSchema,
            404: ErrorResponseSchema,
        },
    };
    // Both prefixed and non-prefixed for compatibility
    app.get('/triage/jobs/:jobId/status', { schema }, jobStatusHandler);
    app.get('/api/triage/jobs/:jobId/status', { schema }, jobStatusHandler);
};
//# sourceMappingURL=job-status.route.js.map