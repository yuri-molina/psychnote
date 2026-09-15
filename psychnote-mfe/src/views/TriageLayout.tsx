import React, { useEffect } from 'react';
import { useParams, NavLink } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, AlertCircle, RefreshCw, XCircle } from 'lucide-react';
import { useTriage } from '@/hooks/useTriage';
import { usePatientRecord } from '@/hooks/usePatientRecord';
import { TriageForm } from '@/components/triage-form/TriageForm';
import { TriageResult } from '@/components/triage-result/TriageResult';
import { registerPatient } from '@/lib/api';
import { cn } from '@/lib/utils';

export const TriageLayout: React.FC = () => {
  const { patientId = 'PAC-UNKNOWN' } = useParams<{ patientId: string }>();
  const { record } = usePatientRecord(patientId);
  const { status, jobId, data, errorMessage, submit, reset, retry } = useTriage();
  const queryClient = useQueryClient();

  const displayName = record?.name || `Paciente ${patientId}`;

  const handleFormSubmit = (note: string) => {
    registerPatient(
      {
        patient_id: patientId,
        name: displayName,
        last_triage_date: new Date().toISOString().split('T')[0],
      },
      note
    );
    queryClient.invalidateQueries({ queryKey: ['patients'] });
    queryClient.invalidateQueries({ queryKey: ['patientRecord', patientId] });
    submit(patientId, note);
  };

  useEffect(() => {
    if (status === 'success' && data) {
      registerPatient(
        {
          patient_id: patientId,
          name: displayName,
          last_triage_date: new Date().toISOString().split('T')[0],
          last_risk_level: data.risk_assessment.risk_level,
        },
        undefined,
        data
      );
      queryClient.invalidateQueries({ queryKey: ['patients'] });
      queryClient.invalidateQueries({ queryKey: ['patientRecord', patientId] });
    }
  }, [status, data, patientId, displayName, queryClient]);

  const isSuccess = status === 'success' && data !== null;
  const isSubmitting = status === 'submitting';
  const isStreaming = status === 'streaming';
  const isErrorApi = status === 'error:api';
  const isErrorContract = status === 'error:contract';

  return (
    <div
      className={cn(
        'psy-mx-auto psy-px-4 psy-py-8 psy-space-y-6 psy-transition-all',
        isSuccess ? 'psy-max-w-4xl' : 'psy-max-w-3xl'
      )}
    >
      {/* Slot: Navegação de Retorno */}
      <div>
        <NavLink
          to="/patients"
          className="psy-inline-flex psy-items-center psy-gap-2 psy-text-sm psy-font-medium psy-text-slate-600 hover:psy-text-primary psy-transition-colors focus:psy-outline-none focus:psy-ring-2 focus:psy-ring-primary psy-px-3 psy-py-1.5 psy-rounded-lg psy-bg-slate-100/80"
        >
          <ArrowLeft className="psy-w-4 psy-h-4" />
          <span>Voltar para a Listagem de Pacientes</span>
        </NavLink>
      </div>

      {/* Slot: Cabeçalho Contextual */}
      <header className="psy-border-b psy-border-slate-200 psy-pb-4">
        <div className="psy-flex psy-items-center psy-justify-between">
          <div>
            <h1 className="psy-text-2xl psy-font-bold psy-text-slate-900">Evolução</h1>
            <p className="psy-text-sm psy-text-slate-600 psy-mt-0.5">
              Paciente em Atendimento: <span className="psy-font-semibold psy-text-primary">{displayName}</span>
            </p>
          </div>
        </div>
      </header>

      {/* Error Banner: error:api ou error:contract */}
      {(isErrorApi || isErrorContract) && (
        <div
          role="alert"
          className="psy-p-4 psy-rounded-xl psy-bg-red-50 psy-border psy-border-red-200 psy-text-red-950 psy-flex psy-items-start psy-gap-3 psy-shadow-sm"
        >
          <AlertCircle className="psy-w-5 psy-h-5 psy-text-red-600 psy-mt-0.5 psy-shrink-0" />
          <div className="psy-flex-1 psy-space-y-2">
            <h2 className="psy-font-bold psy-text-sm">
              {isErrorContract ? 'Falha de Contrato da API' : 'Erro na Comunicação com a IA'}
            </h2>
            <p className="psy-text-xs psy-leading-relaxed psy-text-red-800">{errorMessage}</p>
            <div className="psy-flex psy-items-center psy-gap-3 psy-pt-1">
              {isErrorApi && (
                <button
                  onClick={retry}
                  className="psy-inline-flex psy-items-center psy-gap-1.5 psy-px-3 psy-py-1.5 psy-rounded-lg psy-bg-red-600 psy-text-white psy-text-xs psy-font-semibold hover:psy-bg-red-700 focus:psy-outline-none focus:psy-ring-2 focus:psy-ring-red-500"
                >
                  <RefreshCw className="psy-w-3.5 psy-h-3.5" />
                  <span>Tentar Novamente</span>
                </button>
              )}
              <button
                onClick={reset}
                className="psy-inline-flex psy-items-center psy-gap-1.5 psy-px-3 psy-py-1.5 psy-rounded-lg psy-bg-white psy-border psy-border-slate-300 psy-text-slate-700 psy-text-xs psy-font-semibold hover:psy-bg-slate-50 focus:psy-outline-none"
              >
                <XCircle className="psy-w-3.5 psy-h-3.5" />
                <span>Fechar Erro</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Slot: Conteúdo Principal */}
      <main aria-label={`Triagem clínica do paciente ${patientId}`}>
        {isSuccess ? (
          <TriageResult data={data} onNewTriage={reset} />
        ) : (
          <TriageForm
            patientId={patientId}
            onSubmit={handleFormSubmit}
            isSubmitting={isSubmitting}
            isStreaming={isStreaming}
            jobId={jobId}
          />
        )}
      </main>
    </div>
  );
};
