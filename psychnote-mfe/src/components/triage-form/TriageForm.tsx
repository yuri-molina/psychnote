import React, { useState } from 'react';
import { Loader2, Send, AlertCircle, Radio } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Props {
  patientId: string;
  onSubmit: (note: string) => void;
  isSubmitting: boolean;
  isStreaming?: boolean;
  jobId?: string | null;
  disabled?: boolean;
  className?: string;
}

export const TriageForm: React.FC<Props> = ({
  patientId,
  onSubmit,
  isSubmitting,
  isStreaming = false,
  jobId = null,
  disabled = false,
  className,
}) => {
  const [note, setNote] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  const isBusy = isSubmitting || isStreaming;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (disabled || isBusy) return;

    if (note.trim().length < 10) {
      setValidationError('A nota clínica deve conter no mínimo 10 caracteres.');
      return;
    }

    setValidationError(null);
    onSubmit(note.trim());
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setNote(e.target.value);
    if (validationError && e.target.value.trim().length >= 10) {
      setValidationError(null);
    }
  };

  return (
    <form onSubmit={handleSubmit} className={cn('psy-space-y-6', className)}>
      <div className="psy-space-y-2">
        <div className="psy-flex psy-items-center psy-justify-between">
          <label
            htmlFor="clinical-note-input"
            className="psy-text-sm psy-font-bold psy-uppercase psy-tracking-wider psy-text-slate-700"
          >
            Evolução
          </label>
          <span className="psy-text-xs psy-text-slate-500 psy-font-mono">
            {note.length} caracteres
          </span>
        </div>

        <textarea
          id="clinical-note-input"
          value={note}
          onChange={handleChange}
          disabled={disabled || isBusy}
          rows={7}
          placeholder="Descreva a apresentação clínica, comportamento, relatos de ideação ou sintomas do paciente..."
          aria-invalid={!!validationError}
          aria-describedby={validationError ? 'clinical-note-error' : undefined}
          className={cn(
            'psy-w-full psy-p-4 psy-rounded-xl psy-border psy-text-slate-900 psy-bg-white psy-text-sm psy-leading-relaxed focus:psy-outline-none focus:psy-ring-2 focus:psy-ring-primary psy-transition-all psy-resize-y',
            validationError
              ? 'psy-border-red-400 focus:psy-ring-red-500'
              : 'psy-border-slate-300 hover:psy-border-slate-400',
            (disabled || isBusy) && 'psy-bg-slate-50 psy-text-slate-500 psy-cursor-not-allowed'
          )}
        />

        {validationError && (
          <div
            id="clinical-note-error"
            role="alert"
            className="psy-flex psy-items-center psy-gap-1.5 psy-text-xs psy-font-medium psy-text-red-600 psy-mt-1"
          >
            <AlertCircle className="psy-w-4 psy-h-4 psy-shrink-0" />
            <span>{validationError}</span>
          </div>
        )}
      </div>

      {/* Indicador de Submissão HTTP 202 */}
      {isSubmitting && (
        <div
          aria-live="polite"
          className="psy-p-4 psy-rounded-xl psy-bg-blue-50 psy-border psy-border-blue-200 psy-text-blue-900 psy-flex psy-items-center psy-gap-3 psy-animate-pulse"
        >
          <Loader2 className="psy-w-5 psy-h-5 psy-animate-spin psy-text-primary psy-shrink-0" />
          <div className="psy-text-xs psy-font-medium">
            <p className="psy-font-semibold">Registrando triagem no servidor (HTTP 202)...</p>
            <p className="psy-text-blue-700">Enviando nota e solicitando identificador de processamento.</p>
          </div>
        </div>
      )}

      {/* Indicador de Conexão SSE Active Stream */}
      {isStreaming && (
        <div
          aria-live="polite"
          className="psy-p-4 psy-rounded-xl psy-bg-emerald-50 psy-border psy-border-emerald-200 psy-text-emerald-950 psy-flex psy-items-center psy-gap-3"
        >
          <Radio className="psy-w-5 psy-h-5 psy-animate-pulse psy-text-emerald-600 psy-shrink-0" />
          <div className="psy-text-xs psy-font-medium">
            <p className="psy-font-semibold psy-flex psy-items-center psy-gap-2">
              <span>Triagem psiquiátrica em andamento (SSE Stream)</span>
              {jobId && <span className="psy-font-mono psy-text-emerald-700 psy-bg-emerald-100 psy-px-1.5 psy-py-0.5 psy-rounded">Job: {jobId}</span>}
            </p>
            <p className="psy-text-emerald-700">
              O pipeline de IA (LangGraph) está analisando o risco. Você receberá o resultado em tempo real assim que concluído (~20-40s).
            </p>
          </div>
        </div>
      )}

      <div className="psy-flex psy-items-center psy-justify-end">
        <button
          type="submit"
          disabled={disabled || isBusy || !patientId}
          aria-label={isBusy ? 'Analisando nota clínica...' : 'Submeter nota para triagem de risco'}
          className={cn(
            'psy-inline-flex psy-items-center psy-gap-2 psy-px-6 psy-py-3 psy-rounded-xl psy-font-semibold psy-text-sm psy-text-white psy-bg-primary psy-shadow-sm hover:psy-bg-primary/90 focus:psy-outline-none focus:psy-ring-2 focus:psy-ring-primary focus:psy-ring-offset-2 psy-transition-all',
            (disabled || isBusy || !patientId) &&
              'psy-opacity-50 psy-cursor-not-allowed hover:psy-bg-primary'
          )}
        >
          {isBusy ? (
            <>
              <Loader2 className="psy-w-4 psy-h-4 psy-animate-spin" />
              <span>Processando IA...</span>
            </>
          ) : (
            <>
              <Send className="psy-w-4 psy-h-4" />
              <span>Salvar Evolução e Executar Triagem</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
};
