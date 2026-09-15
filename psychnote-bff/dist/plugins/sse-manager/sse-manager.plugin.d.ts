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
export declare const sseManagerPlugin: FastifyPluginAsync;
//# sourceMappingURL=sse-manager.plugin.d.ts.map