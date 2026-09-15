import type { FastifyPluginAsync } from 'fastify';
export declare class UpstreamTimeoutError extends Error {
    constructor();
}
export declare class UpstreamUnavailableError extends Error {
    constructor(cause?: unknown);
}
export declare class UpstreamError extends Error {
    statusCode: number;
    constructor(statusCode: number);
}
export interface CoreClient {
    postTriageAsync(payload: {
        job_id: string;
        patient_id: string;
        current_note: string;
        callback_url: string;
    }, externalSignal?: AbortSignal): Promise<unknown>;
    getPatientHistory(patientId: string): Promise<unknown>;
    getHealth(): Promise<{
        status: string;
    }>;
}
declare module 'fastify' {
    interface FastifyInstance {
        coreClient: CoreClient;
    }
}
export declare const coreClientPlugin: FastifyPluginAsync;
//# sourceMappingURL=core-client.plugin.d.ts.map