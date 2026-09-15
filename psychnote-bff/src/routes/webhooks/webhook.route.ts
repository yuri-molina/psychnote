import type { FastifyPluginAsync } from 'fastify';
import type { ZodTypeProvider } from 'fastify-type-provider-zod';
import { WebhookPayloadSchema, ErrorResponseSchema } from '../../schemas/index.js';
import { z } from 'zod';

export const webhookRoute: FastifyPluginAsync = async (fastify) => {
  const app = fastify.withTypeProvider<ZodTypeProvider>();

  const webhookHandler = async (request: any, reply: any) => {
    const payload = request.body;
    const { job_id, patient_id, risk_assessment, audit_alerts, final_report } = payload;

    fastify.log.info({ job_id, patient_id }, 'Received webhook callback from Core');

    // Mark job as completed in the in-memory store
    fastify.jobStore.completeJob(job_id, { risk_assessment, audit_alerts, final_report });

    // Emit 'triage_completed' event over SSE (if client is still connected)
    const sent = fastify.sseManager.sendEvent(job_id, 'triage_completed', payload);

    if (sent) {
      const sseReply = fastify.sseManager.getConnection(job_id);
      if (sseReply && !sseReply.raw.destroyed) {
        sseReply.raw.end();
      }
      fastify.sseManager.removeConnection(job_id);
    } else {
      fastify.log.warn({ job_id }, 'Webhook received but no active SSE stream was open. Job state updated in store.');
    }

    return reply.code(200).send({
      status: 'ok',
      message: 'Callback do webhook processado com sucesso.',
    });
  };

  const routeSchema = {
    body: WebhookPayloadSchema,
    response: {
      200: z.object({
        status: z.string(),
        message: z.string(),
      }),
      400: ErrorResponseSchema,
    },
  };

  // Expose both /webhooks/triage-result and /api/webhooks/triage-result for compatibility
  app.post('/webhooks/triage-result', { schema: routeSchema }, webhookHandler);
  app.post('/api/webhooks/triage-result', { schema: routeSchema }, webhookHandler);
};
