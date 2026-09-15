import React, { useState, useId } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, UserPlus, User, AlertCircle, RefreshCw, XCircle } from 'lucide-react';
import { useTriage } from '@/hooks/useTriage';
import { TriageForm } from '@/components/triage-form/TriageForm';
import { registerPatient } from '@/lib/api';
import { cn } from '@/lib/utils';

export const NewPatientEvolutionView: React.FC = () => {
  const navigate = useNavigate();
  const [patientId] = useState(() => `PAC-${Math.floor(1000 + Math.random() * 9000)}`);
  const [patientName, setPatientName] = useState('');
  const [nameError, setNameError] = useState<string | null>(null);

  const queryClient = useQueryClient();
  const patientNameInputId = useId();

  const { status, jobId, errorMessage, submit, reset, retry } = useTriage();

  const handleFormSubmit = (note: string) => {
    if (!patientName.trim()) {
      setNameError('O nome do paciente é obrigatório para cadastrar uma nova evolução.');
      return;
    }
    setNameError(null);

    // Registra o novo paciente no repositório de pacientes com a evolução
    registerPatient(
      {
        patient_id: patientId,
        name: patientName.trim(),
        last_triage_date: new Date().toISOString().split('T')[0],
      },
      note
    );

    // Invalida a query do TanStack Query para atualizar a Listagem e o Prontuário
    queryClient.invalidateQueries({ queryKey: ['patients'] });
    queryClient.invalidateQueries({ queryKey: ['patientRecord', patientId] });

    // Dispara a triagem assíncrona
    submit(patientId, note);

    // Redireciona imediatamente para o prontuário do paciente cadastrado (/patients/:id/record)
    navigate(`/patients/${patientId}/record`);
  };

  const isSubmitting = status === 'submitting';
  const isStreaming = status === 'streaming';
  const isErrorApi = status === 'error:api';
  const isErrorContract = status === 'error:contract';

  return (
    <div className="psy-mx-auto psy-px-4 psy-py-8 psy-space-y-6 psy-max-w-3xl">
      {/* Slot: Navegação de Retorno Genérica (Histórico Anterior) */}
      <div>
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="psy-inline-flex psy-items-center psy-gap-2 psy-text-sm psy-font-medium psy-text-slate-600 hover:psy-text-primary psy-transition-colors focus:psy-outline-none focus:psy-ring-2 focus:psy-ring-primary psy-px-3 psy-py-1.5 psy-rounded-lg psy-bg-slate-100/80"
        >
          <ArrowLeft className="psy-w-4 psy-h-4" />
          <span>Voltar</span>
        </button>
      </div>

      {/* Slot: Cabeçalho Contextual */}
      <header className="psy-border-b psy-border-slate-200 psy-pb-4">
        <div className="psy-flex psy-items-center psy-gap-3">
          <div className="psy-w-10 psy-h-10 psy-rounded-xl psy-bg-primary/10 psy-text-primary psy-flex psy-items-center psy-justify-center psy-shrink-0">
            <UserPlus className="psy-w-5 psy-h-5" />
          </div>
          <div>
            <h1 className="psy-text-2xl psy-font-bold psy-text-slate-900">Novo Paciente</h1>
            <p className="psy-text-sm psy-text-slate-600 psy-mt-0.5">
              Cadastre um novo paciente e redija a evolução psiquiátrica para análise de risco por IA.
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
                  className="psy-inline-flex psy-items-center psy-gap-1.5 psy-px-3 psy-py-1.5 psy-rounded-lg psy-bg-red-600 psy-text-white psy-text-xs psy-font-semibold hover:psy-bg-red-700 focus:psy-outline-none"
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
      <main aria-label="Formulário de cadastro e evolução de novo paciente">
        <div className="psy-space-y-6">
          {/* Form de Identificação do Paciente */}
          <div className="psy-p-6 psy-rounded-2xl psy-bg-white psy-border psy-border-slate-200 psy-shadow-sm psy-space-y-4">
            <h2 className="psy-text-sm psy-font-bold psy-uppercase psy-tracking-wider psy-text-slate-700 psy-flex psy-items-center psy-gap-2">
              <User className="psy-w-4 psy-h-4 psy-text-primary" />
              <span>Identificação</span>
            </h2>

            <div>
              <div className="psy-space-y-1.5">
                <label htmlFor={patientNameInputId} className="psy-text-xs psy-font-semibold psy-text-slate-700 psy-flex psy-items-center psy-gap-1">
                  <User className="psy-w-3.5 psy-h-3.5 psy-text-slate-400" /> Nome Completo
                </label>
                <input
                  id={patientNameInputId}
                  type="text"
                  value={patientName}
                  onChange={(e) => {
                    setPatientName(e.target.value);
                    if (nameError) setNameError(null);
                  }}
                  disabled={isSubmitting || isStreaming}
                  placeholder="Ex: Carlos Eduardo de Oliveira"
                  className={cn(
                    'psy-w-full psy-px-3.5 psy-py-2.5 psy-rounded-xl psy-border psy-text-slate-900 psy-text-sm focus:psy-outline-none focus:psy-ring-2 focus:psy-ring-primary',
                    nameError ? 'psy-border-red-400 focus:psy-ring-red-500' : 'psy-border-slate-300'
                  )}
                />
              </div>
            </div>

            {nameError && (
              <div role="alert" className="psy-flex psy-items-center psy-gap-1.5 psy-text-xs psy-font-medium psy-text-red-600">
                <AlertCircle className="psy-w-4 psy-h-4 psy-shrink-0" />
                <span>{nameError}</span>
              </div>
            )}
          </div>

          {/* Form de Evolução Clínica */}
          <div className="psy-p-6 psy-rounded-2xl psy-bg-white psy-border psy-border-slate-200 psy-shadow-sm">
            <TriageForm
              patientId={patientId}
              onSubmit={handleFormSubmit}
              isSubmitting={isSubmitting}
              isStreaming={isStreaming}
              jobId={jobId}
            />
          </div>
        </div>
      </main>
    </div>
  );
};
