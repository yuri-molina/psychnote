import fp from 'fastify-plugin';
import { ZodError } from 'zod';
import { UpstreamTimeoutError, UpstreamUnavailableError, UpstreamError, } from '../core-client/core-client.plugin.js';
export const errorHandlerPlugin = fp(async (fastify) => {
    fastify.setErrorHandler((error, request, reply) => {
        // Extract patient_id safely from request body if present (for LGPD-compliant logging)
        let patientId;
        if (request.body && typeof request.body === 'object' && 'patient_id' in request.body) {
            patientId = String(request.body.patient_id);
        }
        // 1. Upstream Timeout (504)
        if (error instanceof UpstreamTimeoutError) {
            fastify.log.warn({ errName: error.name, statusCode: 504, patientId }, 'Core timeout occurred');
            const response = {
                statusCode: 504,
                error: 'Gateway Timeout',
                message: 'O serviço de IA não respondeu dentro do tempo limite de 60 segundos.',
                upstream: 'psychnote-core',
            };
            return reply.code(504).send(response);
        }
        // 2. Upstream Unavailable (502)
        if (error instanceof UpstreamUnavailableError) {
            fastify.log.error({ errName: error.name, statusCode: 502, patientId }, 'Core unavailable');
            const response = {
                statusCode: 502,
                error: 'Bad Gateway',
                message: 'Não foi possível conectar ao serviço de IA. Verifique se o psychnote-core está rodando.',
                upstream: 'psychnote-core',
            };
            return reply.code(502).send(response);
        }
        // 3. Upstream Error (502)
        if (error instanceof UpstreamError) {
            fastify.log.error({ errName: error.name, upstreamStatusCode: error.statusCode, statusCode: 502, patientId }, 'Core HTTP error');
            const response = {
                statusCode: 502,
                error: 'Bad Gateway',
                message: 'O serviço de IA retornou um erro inesperado.',
                upstream: 'psychnote-core',
            };
            return reply.code(502).send(response);
        }
        // 4. Zod Error on Upstream Validation (502)
        if (error instanceof ZodError) {
            fastify.log.error({ errName: 'ZodError', issues: error.issues, statusCode: 502, patientId }, 'Upstream contract violation');
            const response = {
                statusCode: 502,
                error: 'Bad Gateway',
                message: 'Resposta inválida recebida do serviço de IA. Contrato violado.',
                upstream: 'psychnote-core',
            };
            return reply.code(502).send(response);
        }
        // 5. Fastify Request Validation Error (400) from fastify-type-provider-zod or schema compilation
        if (typeof error === 'object' && error !== null && 'statusCode' in error && error.statusCode === 400) {
            fastify.log.info({ errName: error.name ?? 'Error', statusCode: 400, patientId }, 'Bad Request from client');
            const response = {
                statusCode: 400,
                error: 'Bad Request',
                message: error.message || 'Payload de requisição inválido.',
            };
            return reply.code(400).send(response);
        }
        // 6. Generic Internal Server Error (500)
        const errName = error?.name ?? 'Error';
        const errMessage = error?.message ?? String(error);
        fastify.log.error({ errName, errMessage, patientId }, 'Unhandled server error');
        const response = {
            statusCode: 500,
            error: 'Internal Server Error',
            message: 'Erro interno inesperado.',
        };
        return reply.code(500).send(response);
    });
});
//# sourceMappingURL=error-handler.plugin.js.map