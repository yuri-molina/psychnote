import { randomUUID } from 'node:crypto';
import type { FastifyPluginAsync } from 'fastify';
import type { ZodTypeProvider } from 'fastify-type-provider-zod';
import {
  TriageAsyncRequestSchema,
  TriageAsyncResponseSchema,
  ErrorResponseSchema,
} from '../../schemas/index.js';

export const triageRoute: FastifyPluginAsync = async (fastify) => {
  const app = fastify.withTypeProvider<ZodTypeProvider>();

  const bffCallbackUrl =
    process.env.BFF_CALLBACK_URL ?? 'http://localhost:4000/api/webhooks/triage-result';

  app.post(
    '/triage',
    {
      schema: {
        body: TriageAsyncRequestSchema,
        response: {
          202: TriageAsyncResponseSchema,
          400: ErrorResponseSchema,
          502: ErrorResponseSchema,
          504: ErrorResponseSchema,
        },
      },
    },
    async (request, reply) => {
      const { patient_id, current_note } = request.body;
      const jobId = randomUUID();

      // Register job in store immediately (before Core responds)
      // This allows /record endpoint to return active_job_id right away
      fastify.jobStore.createJob(jobId, patient_id, current_note);

      fastify.log.info({ jobId, patient_id }, 'Submitting async triage request to Core');

      // Forward to Core /api/v1/triage/async
      await fastify.coreClient.postTriageAsync({
        job_id: jobId,
        patient_id,
        current_note,
        callback_url: bffCallbackUrl,
      });

      return reply.code(202).send({
        job_id: jobId,
        patient_id,
        status: 'processing',
        message: 'Triagem enviada para processamento assíncrono.',
      });
    }
  );
};
