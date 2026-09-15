import fp from 'fastify-plugin';
import type { FastifyPluginAsync, FastifyReply } from 'fastify';

export interface SseManager {
  addConnection(jobId: string, reply: FastifyReply): void;
  getConnection(jobId: string): FastifyReply | undefined;
  removeConnection(jobId: string): void;
  sendEvent(jobId: string, eventName: string, data: unknown): boolean;
}

declare module 'fastify' {
  interface FastifyInstance {
    sseManager: SseManager;
  }
}

export const sseManagerPlugin: FastifyPluginAsync = fp(async (fastify) => {
  const activeSseConnections = new Map<string, FastifyReply>();

  const manager: SseManager = {
    addConnection(jobId: string, reply: FastifyReply): void {
      activeSseConnections.set(jobId, reply);
      fastify.log.info({ jobId, activeConnections: activeSseConnections.size }, 'SSE connection registered');
    },

    getConnection(jobId: string): FastifyReply | undefined {
      return activeSseConnections.get(jobId);
    },

    removeConnection(jobId: string): void {
      const existed = activeSseConnections.delete(jobId);
      if (existed) {
        fastify.log.info({ jobId, activeConnections: activeSseConnections.size }, 'SSE connection removed');
      }
    },

    sendEvent(jobId: string, eventName: string, data: unknown): boolean {
      const reply = activeSseConnections.get(jobId);
      if (!reply) {
        fastify.log.warn({ jobId }, 'Attempted to send SSE event to non-existent connection');
        return false;
      }

      try {
        const payloadStr = JSON.stringify(data);
        reply.raw.write(`event: ${eventName}\ndata: ${payloadStr}\n\n`);
        fastify.log.info({ jobId, eventName }, 'SSE event emitted successfully');
        return true;
      } catch (err) {
        fastify.log.error({ jobId, err }, 'Failed to write SSE event');
        activeSseConnections.delete(jobId);
        return false;
      }
    },
  };

  fastify.decorate('sseManager', manager);
});
