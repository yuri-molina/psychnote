import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import type { FastifyInstance } from 'fastify';
import { buildServer } from '../src/server.js';

describe('psychnote-bff API integration tests (Async Event-Driven Architecture)', () => {
  let app: FastifyInstance;

  beforeAll(async () => {
    process.env.CORE_TIMEOUT_MS = '1000';
    app = await buildServer();
    await app.ready();
  }, 30000);

  afterAll(async () => {
    await app.close();
  });

  describe('GET /health', () => {
    it('returns 200 OK with service status', async () => {
      const response = await app.inject({
        method: 'GET',
        url: '/health',
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.payload);
      expect(body).toEqual({
        status: 'ok',
        service: 'psychnote-bff',
        version: '1.0.0',
      });
    });
  });

  describe('GET /patients and GET /api/patients', () => {
    it('returns 200 OK with list of synthetic patients on /patients', async () => {
      const response = await app.inject({
        method: 'GET',
        url: '/patients',
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.payload);
      expect(Array.isArray(body)).toBe(true);
      expect(body.length).toBe(9);
      expect(body[0]).toHaveProperty('patient_id', 'PAC-010');
    });

    it('returns 200 OK with list of synthetic patients on /api/patients', async () => {
      const response = await app.inject({
        method: 'GET',
        url: '/api/patients',
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.payload);
      expect(Array.isArray(body)).toBe(true);
      expect(body.length).toBe(9);
      expect(body[0]).toHaveProperty('patient_id', 'PAC-010');
    });
  });

  describe('GET /patients/:patient_id/record', () => {
    it('returns 200 OK with patient record for existing patient PAC-012', async () => {
      const response = await app.inject({
        method: 'GET',
        url: '/patients/PAC-012/record',
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.payload);
      expect(body.patient_id).toBe('PAC-012');
      expect(body.name).toBe('Paciente PAC-012');
      expect(Array.isArray(body.history)).toBe(true);
      expect(body.history[0].risk_level).toBe('Alto/Iminente');
    });

    it('returns 404 Not Found when patient_id does not exist', async () => {
      const response = await app.inject({
        method: 'GET',
        url: '/patients/PAC-999/record',
      });

      expect(response.statusCode).toBe(404);
      const body = JSON.parse(response.payload);
      expect(body.statusCode).toBe(404);
      expect(body.error).toBe('Not Found');
    });
  });

  describe('POST /triage (HTTP 202 Async Submission)', () => {
    it('returns 400 Bad Request when patient_id is missing/empty', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/triage',
        payload: {
          patient_id: '',
          current_note: 'Paciente relata sofrimento intenso e angústia constante.',
        },
      });

      expect(response.statusCode).toBe(400);
      const body = JSON.parse(response.payload);
      expect(body.statusCode).toBe(400);
      expect(body.error).toBe('Bad Request');
    });

    it('returns 400 Bad Request when current_note is less than 10 chars', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/triage',
        payload: {
          patient_id: 'PAC-010',
          current_note: 'curta',
        },
      });

      expect(response.statusCode).toBe(400);
      const body = JSON.parse(response.payload);
      expect(body.statusCode).toBe(400);
      expect(body.error).toBe('Bad Request');
    });

    it('returns 502 Bad Gateway when Core service is offline during async submission', async () => {
      const prevUrl = process.env.CORE_URL;
      process.env.CORE_URL = 'http://127.0.0.1:59999';

      const offlineApp = await buildServer();
      await offlineApp.ready();

      const response = await offlineApp.inject({
        method: 'POST',
        url: '/triage',
        payload: {
          patient_id: 'PAC-010',
          current_note: 'Paciente relata ideação suicida persistente e desesperança grave.',
        },
      });

      expect(response.statusCode).toBe(502);
      const body = JSON.parse(response.payload);
      expect(body.statusCode).toBe(502);
      expect(body.error).toBe('Bad Gateway');
      expect(body.upstream).toBe('psychnote-core');

      await offlineApp.close();
      process.env.CORE_URL = prevUrl;
    });
  });

  describe('POST /api/webhooks/triage-result', () => {
    it('returns 200 OK when processing a valid webhook callback', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/webhooks/triage-result',
        payload: {
          job_id: '123e4567-e89b-12d3-a456-426614174000',
          patient_id: 'PAC-010',
          status: 'completed',
          risk_assessment: {
            risk_level: 'Alto/Iminente',
            passive_ideation: true,
            active_ideation: true,
            red_flags: ['Tentativa de autoextermínio previa'],
            protection_factors: ['Vínculo familiar'],
            clinical_justification: 'Paciente com ideação ativa estruturada.',
          },
          audit_alerts: ['[ALERTA CRÍTICO] Risco elevado iminente.'],
          final_report: '=== PARECER EXECUTIVO ===',
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.payload);
      expect(body.status).toBe('ok');
    });

    it('returns 400 Bad Request on invalid webhook payload schema', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/webhooks/triage-result',
        payload: {
          job_id: 'invalid-uuid',
          patient_id: 'PAC-010',
          status: 'completed',
        },
      });

      expect(response.statusCode).toBe(400);
    });
  });
});
