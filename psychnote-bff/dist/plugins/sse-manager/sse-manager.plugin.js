import fp from 'fastify-plugin';
export const sseManagerPlugin = fp(async (fastify) => {
    const activeSseConnections = new Map();
    const manager = {
        addConnection(jobId, reply) {
            activeSseConnections.set(jobId, reply);
            fastify.log.info({ jobId, activeConnections: activeSseConnections.size }, 'SSE connection registered');
        },
        getConnection(jobId) {
            return activeSseConnections.get(jobId);
        },
        removeConnection(jobId) {
            const existed = activeSseConnections.delete(jobId);
            if (existed) {
                fastify.log.info({ jobId, activeConnections: activeSseConnections.size }, 'SSE connection removed');
            }
        },
        sendEvent(jobId, eventName, data) {
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
            }
            catch (err) {
                fastify.log.error({ jobId, err }, 'Failed to write SSE event');
                activeSseConnections.delete(jobId);
                return false;
            }
        },
    };
    fastify.decorate('sseManager', manager);
});
//# sourceMappingURL=sse-manager.plugin.js.map