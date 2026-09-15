export const healthRoute = async (fastify) => {
    fastify.get('/health', async (_request, reply) => {
        return reply.code(200).send({
            status: 'ok',
            service: 'psychnote-bff',
            version: '1.0.0',
        });
    });
};
//# sourceMappingURL=health.route.js.map