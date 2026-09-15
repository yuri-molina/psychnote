import {
  TriageRequest,
  TriageResponse,
  TriageResponseSchema,
  TriageAsyncResponse,
  TriageAsyncResponseSchema,
  Patient,
  PatientsResponseSchema,
  PatientRecord,
  PatientRecordSchema,
} from './schemas';

const BFF_URL = import.meta.env.VITE_BFF_URL || 'http://localhost:4000';

// Armazenamento dinâmico em memória para pacientes criados na sessão ativa
const DYNAMIC_PATIENTS_STORE: Patient[] = [];

// Armazenamento dinâmico em memória para prontuários criados na sessão ativa
const SYNTHETIC_RECORDS_MOCK: Record<string, PatientRecord> = {};

export function registerPatient(
  patient: Patient,
  noteText?: string,
  triageResult?: TriageResponse,
  jobId?: string
) {
  const existingIndex = DYNAMIC_PATIENTS_STORE.findIndex(
    (p) => p.patient_id === patient.patient_id || (patient.name && p.name === patient.name)
  );

  const hasCompletedTriage = !!triageResult;

  const updatedPatient: Patient = {
    patient_id: patient.patient_id,
    name: patient.name || patient.patient_id,
    last_triage_date: patient.last_triage_date || new Date().toISOString().split('T')[0],
    last_risk_level: triageResult?.risk_assessment.risk_level || patient.last_risk_level || undefined,
  };

  if (existingIndex >= 0) {
    DYNAMIC_PATIENTS_STORE[existingIndex] = {
      ...DYNAMIC_PATIENTS_STORE[existingIndex],
      ...updatedPatient,
    };
  } else {
    DYNAMIC_PATIENTS_STORE.unshift(updatedPatient);
  }

  const existingRecord = SYNTHETIC_RECORDS_MOCK[patient.patient_id];

  if (hasCompletedTriage && existingRecord && existingRecord.history.length > 0) {
    // Se o resultado final da IA chegou, atualiza o item pendente correspondente na história do prontuário
    const pendingItem = existingRecord.history.find(
      (h) => (jobId && h.id === jobId) || h.has_triage === false || !h.risk_level
    );
    if (pendingItem) {
      pendingItem.has_triage = true;
      pendingItem.risk_level = triageResult.risk_assessment.risk_level;
      pendingItem.red_flags = triageResult.risk_assessment.red_flags;
      pendingItem.protection_factors = triageResult.risk_assessment.protection_factors;
      pendingItem.clinical_justification = triageResult.risk_assessment.clinical_justification;
      pendingItem.audit_alerts = triageResult.audit_alerts;
      pendingItem.final_report = triageResult.final_report;
      existingRecord.last_triage_date = updatedPatient.last_triage_date;
      existingRecord.active_job_id = null;
      existingRecord.active_job_status = null;
      return;
    }
  }

  // Evita duplicar item pendente com a mesma nota no repositório local
  if (!hasCompletedTriage && existingRecord && noteText) {
    const existingSameNote = existingRecord.history.find(
      (h) => h.current_note?.trim() === noteText.trim()
    );
    if (existingSameNote) {
      if (jobId) existingSameNote.id = jobId;
      return;
    }
  }

  const newHistoryItem = {
    id: jobId || `TR-${Math.floor(1000 + Math.random() * 9000)}`,
    date: new Date().toISOString(),
    has_triage: hasCompletedTriage,
    risk_level: triageResult?.risk_assessment.risk_level || undefined,
    current_note: noteText || 'Evolução psiquiátrica registrada.',
    red_flags: triageResult?.risk_assessment.red_flags || [],
    protection_factors: triageResult?.risk_assessment.protection_factors || [],
    clinical_justification: triageResult?.risk_assessment.clinical_justification || undefined,
    audit_alerts: triageResult?.audit_alerts || [],
    final_report: triageResult?.final_report || undefined,
  };

  if (existingRecord) {
    existingRecord.last_triage_date = updatedPatient.last_triage_date;
    existingRecord.name = updatedPatient.name;
    existingRecord.active_job_id = hasCompletedTriage ? null : jobId || existingRecord.active_job_id;
    existingRecord.active_job_status = hasCompletedTriage ? null : 'processing';
    existingRecord.history.unshift(newHistoryItem);
    existingRecord.total_records = existingRecord.history.length;
  } else {
    SYNTHETIC_RECORDS_MOCK[patient.patient_id] = {
      patient_id: patient.patient_id,
      name: updatedPatient.name,
      last_triage_date: updatedPatient.last_triage_date,
      active_job_id: hasCompletedTriage ? null : jobId || null,
      active_job_status: hasCompletedTriage ? null : 'processing',
      total_records: 1,
      history: [newHistoryItem],
    };
  }
}

export async function fetchPatients(): Promise<Patient[]> {
  const res = await fetch(`${BFF_URL}/api/patients`);
  if (!res.ok) {
    throw new Error(`Erro na API BFF (${res.status}): ${res.statusText}`);
  }
  const data = await res.json();
  const parsedPatients = PatientsResponseSchema.parse(data);

  // Funde e atualiza pacientes criados na sessão ativa
  DYNAMIC_PATIENTS_STORE.forEach((localP) => {
    const idx = parsedPatients.findIndex((p) => p.patient_id === localP.patient_id);
    if (idx >= 0) {
      parsedPatients[idx] = { ...parsedPatients[idx], ...localP };
    } else {
      parsedPatients.unshift(localP);
    }
  });

  return parsedPatients;
}

export async function fetchPatientRecord(patientId: string): Promise<PatientRecord> {
  let record: PatientRecord | null = null;
  let lastError: Error | null = null;

  try {
    const res = await fetch(`${BFF_URL}/api/patients/${patientId}/record`);
    if (res.ok) {
      const data = await res.json();
      record = PatientRecordSchema.parse(data);
    } else {
      lastError = new Error(`Erro na API BFF (${res.status}): ${res.statusText}`);
    }
  } catch (e: any) {
    lastError = e;
  }

  if (!record) {
    try {
      const res = await fetch(`${BFF_URL}/api/patients/${patientId}/history`);
      if (res.ok) {
        const data = await res.json();
        record = PatientRecordSchema.parse(data);
      } else {
        lastError = new Error(`Erro na API BFF (${res.status}): ${res.statusText}`);
      }
    } catch (e: any) {
      lastError = e;
    }
  }

  const localRecord = SYNTHETIC_RECORDS_MOCK[patientId];

  if (!record && localRecord) {
    record = JSON.parse(JSON.stringify(localRecord));
  }

  if (record) {
    // Mescla itens do repositório local no registro retornado pelo BFF
    if (localRecord && localRecord.history.length > 0) {
      localRecord.history.forEach((localItem) => {
        const existingIdx = record!.history.findIndex(
          (h) =>
            (h.id && localItem.id && h.id === localItem.id) ||
            (h.current_note && localItem.current_note && h.current_note.trim() === localItem.current_note.trim())
        );

        if (existingIdx >= 0) {
          const bffItem = record!.history[existingIdx];
          const hasTriage = Boolean(bffItem.has_triage || localItem.has_triage);
          record!.history[existingIdx] = {
            ...bffItem,
            ...localItem,
            has_triage: hasTriage,
            risk_level: localItem.risk_level || bffItem.risk_level,
            red_flags: localItem.red_flags?.length ? localItem.red_flags : bffItem.red_flags,
            protection_factors: localItem.protection_factors?.length ? localItem.protection_factors : bffItem.protection_factors,
            clinical_justification: localItem.clinical_justification || bffItem.clinical_justification,
            audit_alerts: localItem.audit_alerts?.length ? localItem.audit_alerts : bffItem.audit_alerts,
            final_report: localItem.final_report || bffItem.final_report,
          };
        } else {
          record!.history.unshift(localItem);
        }
      });
      if (localRecord.last_triage_date) record.last_triage_date = localRecord.last_triage_date;
      if (localRecord.name) record.name = localRecord.name;
    }

    // Passagem de Deduplicação rigorosa final no array history para garantir entrada única por nota/id
    const uniqueHistory: typeof record.history = [];
    record.history.forEach((item) => {
      const idx = uniqueHistory.findIndex(
        (u) =>
          (u.id && item.id && u.id === item.id) ||
          (u.current_note && item.current_note && u.current_note.trim() === item.current_note.trim())
      );

      if (idx >= 0) {
        const existing = uniqueHistory[idx];
        const hasTriage = Boolean(existing.has_triage || item.has_triage);
        uniqueHistory[idx] = {
          ...existing,
          ...item,
          has_triage: hasTriage,
          risk_level: item.risk_level || existing.risk_level,
          red_flags: item.red_flags?.length ? item.red_flags : existing.red_flags,
          protection_factors: item.protection_factors?.length ? item.protection_factors : existing.protection_factors,
          clinical_justification: item.clinical_justification || existing.clinical_justification,
          audit_alerts: item.audit_alerts?.length ? item.audit_alerts : existing.audit_alerts,
          final_report: item.final_report || existing.final_report,
        };
      } else {
        uniqueHistory.push(item);
      }
    });

    record.history = uniqueHistory;
    record.total_records = uniqueHistory.length;

    // Se nenhuma entrada da história possui triagem pendente, limpa os campos de active_job
    const hasAnyPending = record.history.some((h) => h.has_triage === false || !h.risk_level);
    if (!hasAnyPending) {
      record.active_job_id = null;
      record.active_job_status = null;
    }

    return record;
  }

  throw lastError || new Error(`Não foi possível conectar ao BFF para obter o prontuário do paciente ${patientId}.`);
}

/**
 * Envia a nota clínica para triagem assíncrona (HTTP 202 Accepted) e retorna o job_id.
 */
export async function submitTriageAsync(payload: TriageRequest): Promise<TriageAsyncResponse> {
  let res: Response;
  try {
    res = await fetch(`${BFF_URL}/api/triage`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (res.status === 404) {
      res = await fetch(`${BFF_URL}/triage`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
    }
  } catch (err: any) {
    throw new Error(`Falha de conexão com o BFF (${BFF_URL}). Verifique se o serviço está em execução.`);
  }

  if (res.status !== 202 && res.status !== 200) {
    const errorBody = await res.text().catch(() => '');
    throw new Error(
      `Resposta inesperada do BFF (${res.status} ${res.statusText}): ${errorBody || 'Sem detalhes do servidor'}`
    );
  }

  const data = await res.json();

  try {
    return TriageAsyncResponseSchema.parse(data);
  } catch (zodErr) {
    console.error('Erro de validação no schema do HTTP 202 do BFF:', zodErr);
    throw zodErr;
  }
}

/**
 * Conecta via SSE EventSource ao BFF (/triage/stream/:jobId) e escuta eventos de triagem.
 */
export function subscribeTriageStream(
  jobId: string,
  patientId: string,
  onMessage: (data: TriageResponse) => void,
  onError: (err: Error) => void
): () => void {
  const streamUrl = `${BFF_URL}/api/triage/stream/${jobId}?patient_id=${encodeURIComponent(patientId)}`;
  const eventSource = new EventSource(streamUrl, { withCredentials: true });

  const handleTriageCompleted = (event: MessageEvent) => {
    try {
      const parsedData = JSON.parse(event.data);
      const validatedData = TriageResponseSchema.parse(parsedData);
      onMessage(validatedData);
    } catch (err: any) {
      console.error('Falha de validação no contrato do evento SSE:', err);
      onError(err);
    }
  };

  const handleGeneralMessage = (event: MessageEvent) => {
    try {
      const parsedData = JSON.parse(event.data);
      if (parsedData.risk_assessment) {
        const validatedData = TriageResponseSchema.parse(parsedData);
        onMessage(validatedData);
      }
    } catch (err: any) {
      // Ignora eventos que não se referem ao resultado final
    }
  };

  const handleError = () => {
    onError(new Error('Conexão SSE de triagem encerrada inesperadamente. Verifique a execução do BFF.'));
    eventSource.close();
  };

  eventSource.addEventListener('triage_completed', handleTriageCompleted);
  eventSource.onmessage = handleGeneralMessage;
  eventSource.onerror = handleError;

  return () => {
    eventSource.removeEventListener('triage_completed', handleTriageCompleted);
    eventSource.close();
  };
}
