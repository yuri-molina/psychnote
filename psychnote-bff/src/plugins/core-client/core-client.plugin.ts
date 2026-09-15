import fp from 'fastify-plugin';
import type { FastifyPluginAsync } from 'fastify';

export class UpstreamTimeoutError extends Error {
  constructor() {
    super('O serviço de IA não respondeu dentro do tempo limite de 60 segundos.');
    this.name = 'UpstreamTimeoutError';
  }
}

export class UpstreamUnavailableError extends Error {
  constructor(cause?: unknown) {
    super('Não foi possível conectar ao serviço de IA. Verifique se o psychnote-core está rodando.');
    this.name = 'UpstreamUnavailableError';
    if (cause) this.cause = cause;
  }
}

export class UpstreamError extends Error {
  constructor(public statusCode: number) {
    super(`O serviço de IA retornou um erro inesperado (status ${statusCode}).`);
    this.name = 'UpstreamError';
  }
}

export interface CoreClient {
  postTriageAsync(
    payload: {
      job_id: string;
      patient_id: string;
      current_note: string;
      callback_url: string;
    },
    externalSignal?: AbortSignal
  ): Promise<unknown>;
  getPatientHistory(patientId: string): Promise<unknown>;
  getHealth(): Promise<{ status: string }>;
}

declare module 'fastify' {
  interface FastifyInstance {
    coreClient: CoreClient;
  }
}

export const coreClientPlugin: FastifyPluginAsync = fp(async (fastify) => {
  const coreUrl = (process.env.CORE_URL ?? 'http://localhost:8000').replace(/\/+$/, '');
  const timeoutMs = Number.parseInt(process.env.CORE_TIMEOUT_MS ?? '60000', 10);

  const client: CoreClient = {
    async postTriageAsync(
      payload: {
        job_id: string;
        patient_id: string;
        current_note: string;
        callback_url: string;
      },
      externalSignal?: AbortSignal
    ): Promise<unknown> {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

      let signal: AbortSignal = controller.signal;
      if (externalSignal) {
        signal = AbortSignal.any([controller.signal, externalSignal]);
      }

      try {
        const response = await fetch(`${coreUrl}/api/v1/triage/async`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
          signal,
        });

        if (!response.ok && response.status !== 202) {
          throw new UpstreamError(response.status);
        }

        return await response.json();
      } catch (err: unknown) {
        if (err instanceof UpstreamError) throw err;
        if (err instanceof Error && (err.name === 'AbortError' || controller.signal.aborted)) {
          throw new UpstreamTimeoutError();
        }
        throw new UpstreamUnavailableError(err);
      } finally {
        clearTimeout(timeoutId);
      }
    },

    async getPatientHistory(patientId: string): Promise<unknown> {
      try {
        const response = await fetch(`${coreUrl}/api/v1/patients/${patientId}/history`, {
          method: 'GET',
          headers: { Accept: 'application/json' },
          signal: AbortSignal.timeout(10000),
        });

        if (!response.ok) {
          throw new UpstreamError(response.status);
        }

        return await response.json();
      } catch (err: unknown) {
        if (err instanceof UpstreamError) throw err;
        throw new UpstreamUnavailableError(err);
      }
    },

    async getHealth(): Promise<{ status: string }> {
      try {
        const response = await fetch(`${coreUrl}/health`, {
          method: 'GET',
          headers: { Accept: 'application/json' },
          signal: AbortSignal.timeout(5000),
        });

        if (!response.ok) {
          throw new UpstreamError(response.status);
        }

        return (await response.json()) as { status: string };
      } catch (err: unknown) {
        if (err instanceof UpstreamError) throw err;
        throw new UpstreamUnavailableError(err);
      }
    },
  };

  fastify.decorate('coreClient', client);
});
