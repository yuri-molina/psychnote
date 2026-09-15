import React, { useEffect, useRef } from 'react';
import { RefreshCw, AlertTriangle, ShieldCheck, FileCheck2, User, AlertOctagon } from 'lucide-react';
import { TriageResponse } from '@/lib/schemas';
import { ClinicalRiskBadge } from '@/components/clinical-risk-badge/ClinicalRiskBadge';
import { AuditAlerts } from '@/components/audit-alerts/AuditAlerts';
import { cn } from '@/lib/utils';

interface Props {
  data: TriageResponse;
  onNewTriage: () => void;
  className?: string;
}

export const TriageResult: React.FC<Props> = ({ data, onNewTriage, className }) => {
  const newTriageBtnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    // A11y: Foco no botão de nova triagem ao montar o resultado
    newTriageBtnRef.current?.focus();
  }, []);

  const { risk_assessment, audit_alerts, final_report, patient_id } = data;
  const isHighRisk = risk_assessment.risk_level === 'Alto/Iminente';

  return (
    <article
      aria-label={`Resultado da triagem clínica do paciente ${patient_id}`}
      className={cn('psy-space-y-8 psy-bg-white psy-p-6 md:psy-p-8 psy-rounded-2xl psy-border psy-border-slate-200 psy-shadow-sm', className)}
    >
      {/* Seção 1: Cabeçalho com Risco Clínico */}
      <section aria-labelledby="triage-header-title" className="psy-pb-6 psy-border-b psy-border-slate-200">
        <div className="psy-flex psy-flex-col sm:psy-flex-row sm:psy-items-center psy-justify-between psy-gap-4">
          <div>
            <span className="psy-text-xs psy-font-semibold psy-uppercase psy-tracking-wider psy-text-slate-500 psy-flex psy-items-center psy-gap-1.5">
              <User className="psy-w-3.5 psy-h-3.5" /> ID Paciente: {patient_id}
            </span>
            <h2 id="triage-header-title" className="psy-text-2xl psy-font-bold psy-text-slate-900 psy-mt-1">
              Parecer de Avaliação de Risco
            </h2>
          </div>
          <ClinicalRiskBadge riskLevel={risk_assessment.risk_level} size="lg" showIcon={true} />
        </div>
      </section>

      {/* Destaque para Alertas Críticos se Risco Alto */}
      {isHighRisk && (
        <section aria-labelledby="high-risk-alert-title" className="psy-p-4 psy-rounded-xl psy-bg-red-50 psy-border-2 psy-border-red-500 psy-text-red-950">
          <h3 id="high-risk-alert-title" className="psy-font-bold psy-text-base psy-flex psy-items-center psy-gap-2 psy-text-red-700">
            <AlertOctagon className="psy-w-5 psy-h-5 psy-animate-pulse" /> ALERTA DE PROTOCOLO DE EMERGÊNCIA
          </h3>
          <p className="psy-text-sm psy-mt-1 psy-text-red-900">
            Este paciente foi classificado em **Risco Alto/Iminente**. Acione imediatamente o protocolo de emergência psiquiátrica e não deixe o paciente desacompanhado.
          </p>
        </section>
      )}

      {/* Seção 2: Indicadores de Ideação */}
      <section aria-labelledby="ideation-section-title" className="psy-space-y-3">
        <h3 id="ideation-section-title" className="psy-text-sm psy-font-bold psy-uppercase psy-tracking-wider psy-text-slate-500">
          Indicadores de Ideação Suicida
        </h3>
        <div className="psy-grid psy-grid-cols-1 sm:psy-grid-cols-2 psy-gap-3">
          <div className="psy-p-4 psy-rounded-xl psy-bg-slate-50 psy-border psy-border-slate-200 psy-flex psy-items-center psy-justify-between">
            <span className="psy-text-sm psy-font-medium psy-text-slate-700">Ideação Passiva</span>
            <span
              className={cn(
                'psy-px-2.5 psy-py-1 psy-rounded-md psy-text-xs psy-font-bold',
                risk_assessment.passive_ideation
                  ? 'psy-bg-orange-100 psy-text-orange-800'
                  : 'psy-bg-slate-200 psy-text-slate-700'
              )}
            >
              {risk_assessment.passive_ideation ? 'Sim (Detectado)' : 'Não'}
            </span>
          </div>

          <div className="psy-p-4 psy-rounded-xl psy-bg-slate-50 psy-border psy-border-slate-200 psy-flex psy-items-center psy-justify-between">
            <span className="psy-text-sm psy-font-medium psy-text-slate-700">Ideação Ativa</span>
            <span
              className={cn(
                'psy-px-2.5 psy-py-1 psy-rounded-md psy-text-xs psy-font-bold',
                risk_assessment.active_ideation
                  ? 'psy-bg-red-100 psy-text-red-800'
                  : 'psy-bg-slate-200 psy-text-slate-700'
              )}
            >
              {risk_assessment.active_ideation ? 'Sim (Detectado)' : 'Não'}
            </span>
          </div>
        </div>
      </section>

      {/* Seção 3: Red Flags */}
      {risk_assessment.red_flags.length > 0 && (
        <section aria-labelledby="redflags-section-title" className="psy-space-y-3">
          <h3 id="redflags-section-title" className="psy-text-sm psy-font-bold psy-uppercase psy-tracking-wider psy-text-red-600 psy-flex psy-items-center psy-gap-1.5">
            <AlertTriangle className="psy-w-4 psy-h-4" /> Sinais de Alerta (Red Flags)
          </h3>
          <ul role="list" className="psy-space-y-2">
            {risk_assessment.red_flags.map((flag, idx) => (
              <li key={idx} className="psy-p-3 psy-rounded-lg psy-bg-red-50/60 psy-border psy-border-red-200 psy-text-xs psy-font-medium psy-text-red-900 psy-flex psy-items-start psy-gap-2">
                <span className="psy-text-red-500 psy-font-bold">•</span>
                <span>{flag}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Seção 4: Fatores de Proteção */}
      <section aria-labelledby="protection-section-title" className="psy-space-y-3">
        <h3 id="protection-section-title" className="psy-text-sm psy-font-bold psy-uppercase psy-tracking-wider psy-text-slate-500 psy-flex psy-items-center psy-gap-1.5">
          <ShieldCheck className="psy-w-4 psy-h-4 psy-text-green-600" /> Fatores de Proteção
        </h3>
        {risk_assessment.protection_factors.length > 0 ? (
          <ul role="list" className="psy-space-y-2">
            {risk_assessment.protection_factors.map((factor, idx) => (
              <li key={idx} className="psy-p-3 psy-rounded-lg psy-bg-green-50/60 psy-border psy-border-green-200 psy-text-xs psy-font-medium psy-text-green-900 psy-flex psy-items-start psy-gap-2">
                <span className="psy-text-green-600 psy-font-bold">✓</span>
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="psy-text-xs psy-italic psy-text-slate-500 psy-bg-slate-50 psy-p-3 psy-rounded-lg">
            Nenhum fator de proteção identificado na nota clínica.
          </p>
        )}
      </section>

      {/* Seção 5: Justificativa Clínica */}
      {risk_assessment.clinical_justification && (
        <section aria-labelledby="justification-section-title" className="psy-space-y-2">
          <h3 id="justification-section-title" className="psy-text-sm psy-font-bold psy-uppercase psy-tracking-wider psy-text-slate-500">
            Justificativa Clínica da IA
          </h3>
          <p className="psy-text-sm psy-text-slate-700 psy-leading-relaxed psy-p-4 psy-rounded-xl psy-bg-slate-50 psy-border psy-border-slate-200">
            {risk_assessment.clinical_justification}
          </p>
        </section>
      )}

      {/* Seção 6: Alertas de Auditoria de Protocolo */}
      <section aria-labelledby="audit-section-title" className="psy-space-y-3">
        <h3 id="audit-section-title" className="psy-text-sm psy-font-bold psy-uppercase psy-tracking-wider psy-text-slate-500">
          Auditoria de Protocolo Clínico (CFM / OMS)
        </h3>
        <AuditAlerts alerts={audit_alerts} />
      </section>

      {/* Seção 7: Relatório Executivo Final */}
      {final_report && (
        <section aria-labelledby="report-section-title" className="psy-space-y-2">
          <h3 id="report-section-title" className="psy-text-sm psy-font-bold psy-uppercase psy-tracking-wider psy-text-slate-500 psy-flex psy-items-center psy-gap-1.5">
            <FileCheck2 className="psy-w-4 psy-h-4 psy-text-primary" /> Relatório Síntese de Auditoria
          </h3>
          <div className="psy-p-4 psy-rounded-xl psy-bg-slate-900 psy-text-slate-100 psy-text-xs psy-font-mono psy-whitespace-pre-wrap psy-leading-relaxed psy-overflow-x-auto psy-max-h-96">
            {final_report}
          </div>
        </section>
      )}

      {/* Seção 8: Ação de Nova Triagem */}
      <div className="psy-pt-6 psy-border-t psy-border-slate-200 psy-flex psy-justify-end">
        <button
          ref={newTriageBtnRef}
          onClick={onNewTriage}
          className="psy-inline-flex psy-items-center psy-gap-2 psy-px-6 psy-py-3 psy-rounded-xl psy-font-semibold psy-text-sm psy-text-slate-700 psy-bg-slate-100 hover:psy-bg-slate-200 focus:psy-outline-none focus:psy-ring-2 focus:psy-ring-primary psy-transition-all"
        >
          <RefreshCw className="psy-w-4 psy-h-4" />
          <span>Realizar Nova Triagem</span>
        </button>
      </div>
    </article>
  );
};
