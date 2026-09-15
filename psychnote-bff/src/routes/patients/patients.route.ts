import type { FastifyPluginAsync } from 'fastify';
import {
  PatientsResponseSchema,
  PatientRecordSchema,
  ErrorResponseSchema,
  type PatientRecord,
  type Patient,
  type TriageHistoryItem,
} from '../../schemas/index.js';
import type { ZodTypeProvider } from 'fastify-type-provider-zod';
import { z } from 'zod';

const SYNTHETIC_PATIENTS: Patient[] = [
  { patient_id: 'PAC-010', name: 'Paciente PAC-010', last_triage_date: '2026-08-01', last_risk_level: 'Alto/Iminente' },
  { patient_id: 'PAC-011', name: 'Paciente PAC-011', last_triage_date: '2026-08-02', last_risk_level: 'Alto/Iminente' },
  { patient_id: 'PAC-012', name: 'Paciente PAC-012', last_triage_date: '2026-08-03', last_risk_level: 'Alto/Iminente' },
  { patient_id: 'PAC-020', name: 'Paciente PAC-020', last_triage_date: '2026-08-04', last_risk_level: 'Moderado' },
  { patient_id: 'PAC-021', name: 'Paciente PAC-021', last_triage_date: '2026-08-04', last_risk_level: 'Moderado' },
  { patient_id: 'PAC-022', name: 'Paciente PAC-022', last_triage_date: '2026-08-05', last_risk_level: 'Moderado' },
  { patient_id: 'PAC-030', name: 'Paciente PAC-030', last_triage_date: '2026-08-05', last_risk_level: 'Baixo' },
  { patient_id: 'PAC-031', name: 'Paciente PAC-031', last_triage_date: '2026-08-06', last_risk_level: 'Baixo' },
  { patient_id: 'PAC-032', name: 'Paciente PAC-032', last_triage_date: '2026-08-07', last_risk_level: 'Baixo' },
];

const SYNTHETIC_RECORDS: Record<string, PatientRecord> = {
  'PAC-010': {
    patient_id: 'PAC-010',
    name: 'Paciente PAC-010',
    last_triage_date: '2026-08-01',
    history: [
      {
        has_triage: true,
        id: 'TR-010',
        date: '2026-08-01T10:00:00Z',
        risk_level: 'Alto/Iminente',
        current_note:
          'HMA: Paciente trazido por vizinho devido a isolamento social e choro copioso há 3 dias. Refere luto recente (morte inesperada da irmã há duas semanas) associado a demissão sumária do emprego.',
        red_flags: [
          'Histórico de duas tentativas prévias graves (UTI/enforcamento)',
          'Ideação ativa estruturada com plano e aquisição de raticida',
          'Cartas de despedida escritas para os filhos',
        ],
        protection_factors: ['Vínculo com os filhos'],
        clinical_justification:
          'Paciente com ideação suicida ativa estruturada, meio letal disponível e plano imediato após estressores agudos graves.',
        audit_alerts: [
          '[ALERTA CRÍTICO] Risco elevado iminente de autoextermínio.',
          '[RECOMENDACAO] Encaminhamento imediato para internação ou vigilância contínua.',
        ],
      },
    ],
  },
  'PAC-011': {
    patient_id: 'PAC-011',
    name: 'Paciente PAC-011',
    last_triage_date: '2026-08-02',
    history: [
      {
        has_triage: true,
        id: 'TR-011',
        date: '2026-08-02T11:30:00Z',
        risk_level: 'Alto/Iminente',
        current_note:
          'HMA: Apresenta-se à consulta em sofrimento psíquico agudo e intolerável após término abrupto de relacionamento conjugal. Apresenta desesperança grave, anedonia global, apatia e insônia terminal.',
        red_flags: [
          'Tentativa prévia grave por precipitação de altura',
          'Plano definitivo e estocado medicação letal (clonazepam e opioides)',
          'Histórico de abuso de substâncias',
        ],
        protection_factors: ['Suporte de familiares próximos'],
        clinical_justification:
          'Quadro de sofrimento agudo com acúmulo clandestino de fármacos letais e planejamento explícito para o próximo fim de semana.',
        audit_alerts: [
          '[ALERTA CRÍTICO] Encaminhamento involuntário/emergencial indicado via SAMU.',
        ],
      },
    ],
  },
  'PAC-012': {
    patient_id: 'PAC-012',
    name: 'Paciente PAC-012',
    last_triage_date: '2026-08-03',
    history: [
      {
        has_triage: true,
        id: 'TR-012',
        date: '2026-08-03T15:20:00Z',
        risk_level: 'Alto/Iminente',
        current_note:
          'HMA: Paciente relata que as vozes imperativas retornaram com extrema intensidade há uma semana, ordenando que ele se jogue da ponte do metrô para purificar seus pecados.',
        red_flags: [
          'Alucinações auditivas imperativas de comando de morte',
          'Diário detalhado com mapa e horários da estação de metrô',
          'Ausência de crítica sobre o estado alucinatório',
        ],
        protection_factors: ['Presença e suporte do irmão'],
        clinical_justification:
          'Esquizofrenia paranoide descompensada com alucinações imperativas e plano logístico mapeado.',
        audit_alerts: [
          '[ALERTA CRÍTICO] Risco imperativo derivado de sintomatologia psicótica ativa.',
        ],
      },
    ],
  },
  'PAC-020': {
    patient_id: 'PAC-020',
    name: 'Paciente PAC-020',
    last_triage_date: '2026-08-04',
    history: [
      {
        has_triage: true,
        id: 'TR-020',
        date: '2026-08-04T09:15:00Z',
        risk_level: 'Moderado',
        current_note:
          'HMA: Paciente comparece à consulta queixando-se de aumento da labilidade emocional após conflito interpessoal recente no ambiente de trabalho. Refere pensamentos recorrentes de que seria melhor desaparecer.',
        red_flags: [
          'Ideação passiva recorrente',
          'Labilidade emocional e impulsividade prévia',
        ],
        protection_factors: ['Amor pelo filho de 2 anos', 'Suporte da mãe'],
        clinical_justification:
          'Ideação passiva flutuante sem planejamento ativo, amparada por fortes fatores de proteção interpessoal.',
        audit_alerts: [
          '[RECOMENDACAO] Orientar familiares e pactuar contrato terapêutico.',
        ],
      },
    ],
  },
  'PAC-021': {
    patient_id: 'PAC-021',
    name: 'Paciente PAC-021',
    last_triage_date: '2026-08-04',
    history: [
      {
        has_triage: true,
        id: 'TR-021',
        date: '2026-08-04T14:00:00Z',
        risk_level: 'Moderado',
        current_note:
          'HMA: Relata ressurgimento de pensamentos passivos de morte associados a insônia inicial de rebote e cansaço no último mês.',
        red_flags: ['Exacerbação de sintomas depressivos e insônia'],
        protection_factors: ['Crenças religiosas e morais contra o suicídio', 'Suporte conjugal'],
        clinical_justification:
          'Depressão recorrente com ideação passiva sem intenção ou plano ativo.',
        audit_alerts: [
          '[RECOMENDACAO] Otimização medicamentosa e retorno ambulatorial curto.',
        ],
      },
    ],
  },
  'PAC-022': {
    patient_id: 'PAC-022',
    name: 'Paciente PAC-022',
    last_triage_date: '2026-08-05',
    history: [
      {
        has_triage: true,
        id: 'TR-022',
        date: '2026-08-05T16:45:00Z',
        risk_level: 'Moderado',
        current_note:
          'HMA: Relata piora dos sintomas álgicos na última quinzena, acompanhada de sentimentos de inutilidade e pensamentos de morte passivos.',
        red_flags: ['Dor crônica refratária e exaustão física'],
        protection_factors: ['Boa aliança terapêutica com psicologia', 'Presença das irmãs'],
        clinical_justification:
          'Ideação passiva associada a estresse álgico crônico, com forte preservação da aliança terapêutica.',
        audit_alerts: [],
      },
    ],
  },
  'PAC-030': {
    patient_id: 'PAC-030',
    name: 'Paciente PAC-030',
    last_triage_date: '2026-08-05',
    history: [
      {
        has_triage: true,
        id: 'TR-030',
        date: '2026-08-05T11:00:00Z',
        risk_level: 'Baixo',
        current_note:
          'HMA: Comparece ao consultório referindo cansaço físico persistente, letargia e dificuldades de concentração nas últimas duas semanas.',
        red_flags: ['Fadiga física e estresse acadêmico'],
        protection_factors: ['Projetos futuros estabelecidos', 'Motivação para psicoterapia'],
        clinical_justification:
          'Sintomas depressivos leves situacionais, sem ideação ativa ou planejamento.',
        audit_alerts: [],
      },
    ],
  },
  'PAC-031': {
    patient_id: 'PAC-031',
    name: 'Paciente PAC-031',
    last_triage_date: '2026-08-06',
    history: [
      {
        has_triage: true,
        id: 'TR-031',
        date: '2026-08-06T10:15:00Z',
        risk_level: 'Baixo',
        current_note:
          'HMA: Queixa-se de intensificação discreta da desmotivação e fadiga crônica, acompanhada de sintomas somáticos como dores musculares difusas.',
        red_flags: ['Sentimento pontual de utilidade reduzida'],
        protection_factors: ['Expectativa pelo nascimento da neta', 'Reside com a filha'],
        clinical_justification:
          'Quadro distímico crônico compensado, sem qualquer intenção ou plano suicida.',
        audit_alerts: [],
      },
    ],
  },
  'PAC-032': {
    patient_id: 'PAC-032',
    name: 'Paciente PAC-032',
    last_triage_date: '2026-08-07',
    history: [
      {
        has_triage: true,
        id: 'TR-032',
        date: '2026-08-07T13:30:00Z',
        risk_level: 'Baixo',
        current_note:
          'HMA: Relata quadro de exaustão profunda, insônia de conciliação e dor física difusa após recente promoção e aumento da carga de trabalho corporativo.',
        red_flags: ['Sobrecarga ocupacional severa'],
        protection_factors: ['Crítica preservada', 'Ausência total de ideação autolesiva'],
        clinical_justification:
          'Síndrome de esgotamento profissional (Burnout) sem risco suicida identificável.',
        audit_alerts: [],
      },
    ],
  },
};

export const patientsRoute: FastifyPluginAsync = async (fastify) => {
  const app = fastify.withTypeProvider<ZodTypeProvider>();

  // GET /patients and GET /api/patients
  const patientsHandler = async (_request: any, reply: any) => {
    return reply.code(200).send(SYNTHETIC_PATIENTS);
  };

  const patientsSchema = {
    response: {
      200: PatientsResponseSchema,
    },
  };

  app.get('/patients', { schema: patientsSchema }, patientsHandler);
  app.get('/api/patients', { schema: patientsSchema }, patientsHandler);

  // GET /patients/:patient_id/record and /api/patients/:patient_id/record
  const recordHandler = async (request: any, reply: any) => {
    const { patient_id } = request.params;
    const baseRecord = SYNTHETIC_RECORDS[patient_id];

    // Check if there is an active processing job for this patient
    const activeJobId = fastify.jobStore.getActiveJobForPatient(patient_id);
    const activeJob = activeJobId ? fastify.jobStore.getJob(activeJobId) : undefined;

    if (!baseRecord && !activeJob) {
      fastify.log.warn({ patient_id }, 'Patient record not found');
      return reply.code(404).send({
        statusCode: 404,
        error: 'Not Found',
        message: `Prontuário do paciente ${patient_id} não foi encontrado.`,
      });
    }

    // Build history: start with existing records
    const historicalItems: TriageHistoryItem[] = baseRecord?.history ?? [];

    // Prepend in-progress entry from active job (newest first)
    const historyWithJob: TriageHistoryItem[] = activeJob
      ? [
          {
            id: activeJob.job_id,
            date: activeJob.created_at,
            current_note: activeJob.current_note,
            has_triage: false,
            risk_level: undefined,
            red_flags: [],
            protection_factors: [],
            clinical_justification: undefined,
            audit_alerts: [],
          },
          ...historicalItems,
        ]
      : historicalItems;

    const response = {
      patient_id,
      name: baseRecord?.name ?? `Paciente ${patient_id}`,
      last_triage_date: baseRecord?.last_triage_date,
      active_job_id: activeJobId ?? null,
      active_job_status: activeJobId ? ('processing' as const) : null,
      total_records: historyWithJob.length,
      history: historyWithJob,
    };

    return reply.code(200).send(response);
  };

  const recordSchema = {
    params: z.object({
      patient_id: z.string(),
    }),
    response: {
      200: PatientRecordSchema,
      404: ErrorResponseSchema,
    },
  };

  app.get('/patients/:patient_id/record', { schema: recordSchema }, recordHandler);
  app.get('/api/patients/:patient_id/record', { schema: recordSchema }, recordHandler);

  // GET /api/patients/:patient_id/history (query history from Core/ChromaDB)
  const historyHandler = async (request: any, reply: any) => {
    const { patient_id } = request.params;

    try {
      const coreHistory = await fastify.coreClient.getPatientHistory(patient_id);
      return reply.code(200).send(coreHistory);
    } catch (err) {
      fastify.log.warn({ patient_id, err }, 'Failed to fetch history from Core, using synthetic record');
      const fallbackRecord = SYNTHETIC_RECORDS[patient_id];
      if (!fallbackRecord) {
        return reply.code(404).send({
          statusCode: 404,
          error: 'Not Found',
          message: `Histórico do paciente ${patient_id} não encontrado.`,
        });
      }
      return reply.code(200).send({
        patient_id,
        total_records: fallbackRecord.history.length,
        history: fallbackRecord.history.map((h: TriageHistoryItem) => ({
          timestamp: h.date,
          note_text: h.current_note,
          has_triage: true,
          risk_level: h.risk_level,
          red_flags: h.red_flags,
          protection_factors: h.protection_factors,
          clinical_justification: h.clinical_justification,
          audit_alerts: h.audit_alerts,
        })),
      });
    }
  };

  const historySchema = {
    params: z.object({
      patient_id: z.string(),
    }),
    response: {
      200: z.unknown(),
      404: ErrorResponseSchema,
      502: ErrorResponseSchema,
    },
  };

  app.get('/patients/:patient_id/history', { schema: historySchema }, historyHandler);
  app.get('/api/patients/:patient_id/history', { schema: historySchema }, historyHandler);
};
