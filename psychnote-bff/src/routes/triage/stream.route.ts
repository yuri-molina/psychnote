import type { FastifyPluginAsync } from 'fastify';
import type { ZodTypeProvider } from 'fastify-type-provider-zod';
import { z } from 'zod';
import { ErrorResponseSchema } from '../../schemas/index.js';

export const streamRoute: FastifyPluginAsync = async (fastify) => {
  const app = fastify.withTypeProvider<ZodTypeProvider>();

  const streamHandler = async (
    request: { params: { jobId: string }; raw: import('node:http').IncomingMessage; headers: Record<string, string | undefined> },
    reply: import('fastify').FastifyReply
  ) => {
    // Hijack raw response to prevent Fastify from auto-closing the connection on async handler resolution
    reply.hijack();

    const { jobId } = request.params;
    const reqOrigin = request.headers.origin;
    const allowedOrigin = reqOrigin && reqOrigin !== 'null' ? reqOrigin : '*';

    // Configure SSE & CORS headers on raw response stream
    reply.raw.setHeader('Access-Control-Allow-Origin', allowedOrigin);
    if (allowedOrigin !== '*') {
      reply.raw.setHeader('Access-Control-Allow-Credentials', 'true');
    }
    reply.raw.setHeader('Access-Control-Allow-Headers', 'Content-Type, Accept, Authorization, X-Requested-With');
    reply.raw.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    reply.raw.setHeader('Content-Type', 'text/event-stream');
    reply.raw.setHeader('Cache-Control', 'no-cache, no-transform');
    reply.raw.setHeader('Connection', 'keep-alive');
    reply.raw.setHeader('X-Accel-Buffering', 'no');
    reply.raw.statusCode = 200;

    // Register active SSE connection in manager
    fastify.sseManager.addConnection(jobId, reply);

    // Initial SSE connection handshake comment
    reply.raw.write(`: sse connected\n\n`);

    // Setup 15s heartbeat interval
    const heartbeatTimer = setInterval(() => {
      if (!reply.raw.destroyed && !reply.raw.closed) {
        reply.raw.write(`: heartbeat\n\n`);
      }
    }, 15000);

    // Cleanup on client disconnect
    request.raw.on('close', () => {
      clearInterval(heartbeatTimer);
      fastify.sseManager.removeConnection(jobId);
    });
  };

  const optionsHandler = async (
    request: { headers: Record<string, string | undefined> },
    reply: import('fastify').FastifyReply
  ) => {
    const reqOrigin = request.headers.origin;
    const allowedOrigin = reqOrigin && reqOrigin !== 'null' ? reqOrigin : '*';
    if (allowedOrigin !== '*') {
      reply.header('Access-Control-Allow-Credentials', 'true');
    }
    return reply
      .header('Access-Control-Allow-Origin', allowedOrigin)
      .header('Access-Control-Allow-Headers', 'Content-Type, Accept, Authorization, X-Requested-With')
      .header('Access-Control-Allow-Methods', 'GET, OPTIONS')
      .status(204)
      .send();
  };

  const routeSchema = {
    params: z.object({
      jobId: z.string().min(1),
    }),
    response: {
      400: ErrorResponseSchema,
    },
  };

  // Preflight OPTIONS routes for CORS
  app.options('/triage/stream/:jobId', optionsHandler as any);
  app.options('/api/triage/stream/:jobId', optionsHandler as any);

  // Expose both /triage/stream/:jobId and /api/triage/stream/:jobId for compatibility
  app.get('/triage/stream/:jobId', { schema: routeSchema }, streamHandler as any);
  app.get('/api/triage/stream/:jobId', { schema: routeSchema }, streamHandler as any);
};
