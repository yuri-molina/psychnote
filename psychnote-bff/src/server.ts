import Fastify from 'fastify';
import cors from '@fastify/cors';
import helmet from '@fastify/helmet';
import {
  serializerCompiler,
  validatorCompiler,
  type ZodTypeProvider,
} from 'fastify-type-provider-zod';

import { coreClientPlugin } from './plugins/core-client/core-client.plugin.js';
import { errorHandlerPlugin } from './plugins/error-handler/error-handler.plugin.js';
import { sseManagerPlugin } from './plugins/sse-manager/sse-manager.plugin.js';
import { jobStorePlugin } from './plugins/job-store/job-store.plugin.js';
import { healthRoute } from './routes/health/health.route.js';
import { patientsRoute } from './routes/patients/patients.route.js';
import { streamRoute } from './routes/triage/stream.route.js';
import { triageRoute } from './routes/triage/triage.route.js';
import { jobStatusRoute } from './routes/triage/job-status.route.js';
import { webhookRoute } from './routes/webhooks/webhook.route.js';

const PORT = Number.parseInt(process.env.PORT ?? '4000', 10);

export async function buildServer() {
  const fastify = Fastify({
    logger: true,
  }).withTypeProvider<ZodTypeProvider>();

  // Set Zod compilers
  fastify.setValidatorCompiler(validatorCompiler);
  fastify.setSerializerCompiler(serializerCompiler);

  // Security plugins MUST be registered BEFORE routes
  // 1. Helmet
  await fastify.register(helmet, {
    contentSecurityPolicy: false,
  });

  // 2. CORS (Reflete a origin do cliente para permitir SSE e chamadas de MFE em qualquer porta)
  await fastify.register(cors, {
    origin: true,
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Accept', 'Authorization', 'X-Requested-With', 'Cache-Control'],
  });

  // Global plugins
  await fastify.register(errorHandlerPlugin);
  await fastify.register(sseManagerPlugin);
  await fastify.register(jobStorePlugin);
  await fastify.register(coreClientPlugin);

  // Routes
  await fastify.register(healthRoute);
  await fastify.register(patientsRoute);
  await fastify.register(triageRoute);
  await fastify.register(streamRoute);
  await fastify.register(jobStatusRoute);
  await fastify.register(webhookRoute);

  return fastify;
}

// Start server if executed directly
if (process.argv[1]?.endsWith('server.ts') || process.argv[1]?.endsWith('server.js')) {
  const server = await buildServer();
  try {
    await server.listen({ port: PORT, host: '0.0.0.0' });
    server.log.info(`psychnote-bff (Async Event-Driven Architecture) running on http://localhost:${PORT}`);
  } catch (err) {
    server.log.error(err);
    process.exit(1);
  }
}
