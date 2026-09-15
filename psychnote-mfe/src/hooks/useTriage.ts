import { useState, useEffect, useRef, useCallback } from 'react';
import { ZodError } from 'zod';
import { submitTriageAsync, subscribeTriageStream } from '@/lib/api';
import { TriageResponse } from '@/lib/schemas';

export type TriageFSMStatus = 'idle' | 'submitting' | 'streaming' | 'success' | 'error:api' | 'error:contract';

export interface UseTriageReturn {
  status: TriageFSMStatus;
  jobId: string | null;
  data: TriageResponse | null;
  errorMessage: string | null;
  submit: (patientId: string, currentNote: string) => void;
  reset: () => void;
  retry: () => void;
}

export function useTriage(): UseTriageReturn {
  const [status, setStatus] = useState<TriageFSMStatus>('idle');
  const [jobId, setJobId] = useState<string | null>(null);
  const [data, setData] = useState<TriageResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const lastSubmittedRef = useRef<{ patientId: string; note: string } | null>(null);
  const sseUnsubscribeRef = useRef<(() => void) | null>(null);

  const cleanupSse = useCallback(() => {
    if (sseUnsubscribeRef.current) {
      sseUnsubscribeRef.current();
      sseUnsubscribeRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => {
      cleanupSse();
    };
  }, [cleanupSse]);

  const submit = async (patientId: string, currentNote: string) => {
    cleanupSse();
    setStatus('submitting');
    setErrorMessage(null);
    setData(null);
    lastSubmittedRef.current = { patientId, note: currentNote };

    try {
      const asyncRes = await submitTriageAsync({
        patient_id: patientId,
        current_note: currentNote,
      });

      const currentJobId = asyncRes.job_id;
      setJobId(currentJobId);
      setStatus('streaming');

      // Conecta ao canal SSE
      const unsubscribe = subscribeTriageStream(
        currentJobId,
        patientId,
        (completedData) => {
          setData(completedData);
          setStatus('success');
          cleanupSse();
        },
        (err) => {
          cleanupSse();
          if (err instanceof ZodError) {
            setStatus('error:contract');
            setErrorMessage('A resposta recebida do evento SSE não está no formato esperado (falha no contrato do BFF).');
          } else {
            setStatus('error:api');
            setErrorMessage(err.message || 'Falha na conexão SSE de streaming com a IA.');
          }
        }
      );

      sseUnsubscribeRef.current = unsubscribe;
    } catch (err) {
      setStatus('error:api');
      setErrorMessage(err instanceof Error ? err.message : 'Ocorreu um erro ao enviar a triagem.');
    }
  };

  const reset = () => {
    cleanupSse();
    setStatus('idle');
    setJobId(null);
    setData(null);
    setErrorMessage(null);
  };

  const retry = () => {
    if (lastSubmittedRef.current) {
      submit(lastSubmittedRef.current.patientId, lastSubmittedRef.current.note);
    }
  };

  return {
    status,
    jobId,
    data,
    errorMessage,
    submit,
    reset,
    retry,
  };
}
