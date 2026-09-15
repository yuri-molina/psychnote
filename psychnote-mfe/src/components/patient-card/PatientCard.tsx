import React from 'react';
import { User, Calendar, Eye, Stethoscope } from 'lucide-react';
import { Patient } from '@/lib/schemas';
import { ClinicalRiskBadge } from '@/components/clinical-risk-badge/ClinicalRiskBadge';
import { cn } from '@/lib/utils';

interface Props {
  patientId: string;
  patient?: Patient;
  onViewRecord: (patientId: string) => void;
  onStartTriage: (patientId: string) => void;
  isSelected?: boolean;
  className?: string;
}

export const PatientCard: React.FC<Props> = ({
  patientId,
  patient,
  onViewRecord,
  onStartTriage,
  isSelected = false,
  className,
}) => {
  const displayName = patient?.name || `Paciente ${patientId}`;

  return (
    <div
      aria-label={`Card do paciente ${displayName}`}
      className={cn(
        'psy-p-5 psy-rounded-xl psy-border psy-transition-all psy-bg-white psy-shadow-sm hover:psy-shadow-md psy-flex psy-flex-col psy-justify-between psy-gap-4',
        isSelected
          ? 'psy-border-primary psy-bg-primary/5 psy-ring-1 psy-ring-primary'
          : 'psy-border-slate-200 hover:psy-border-slate-300',
        className
      )}
    >
      <div>
        <div className="psy-flex psy-items-start psy-justify-between psy-gap-3">
          <div className="psy-flex psy-items-center psy-gap-3 psy-min-w-0">
            <div className="psy-w-10 psy-h-10 psy-rounded-full psy-bg-slate-100 psy-flex psy-items-center psy-justify-center psy-shrink-0">
              <User className="psy-w-5 psy-h-5 psy-text-slate-600" aria-hidden="true" />
            </div>
            <div className="psy-min-w-0">
              <h3 className="psy-text-base psy-font-semibold psy-text-slate-900 psy-truncate" title={displayName}>
                {displayName}
              </h3>
            </div>
          </div>

          {patient?.last_risk_level && (
            <ClinicalRiskBadge riskLevel={patient.last_risk_level} size="sm" showIcon={false} />
          )}
        </div>

        {patient?.last_triage_date && (
          <div className="psy-mt-3 psy-pt-2.5 psy-border-t psy-border-slate-100 psy-flex psy-items-center psy-gap-1.5 psy-text-xs psy-text-slate-500">
            <Calendar className="psy-w-3.5 psy-h-3.5" aria-hidden="true" />
            <span>Última evolução: {patient.last_triage_date}</span>
          </div>
        )}
      </div>

      {/* Botões de Ação Direta */}
      <div className="psy-pt-3 psy-border-t psy-border-slate-100 psy-grid psy-grid-cols-2 psy-gap-2">
        <button
          type="button"
          onClick={() => onViewRecord(patientId)}
          aria-label={`Ver prontuário do paciente ${displayName}`}
          className="psy-inline-flex psy-items-center psy-justify-center psy-gap-1.5 psy-px-3 psy-py-2 psy-rounded-lg psy-text-xs psy-font-semibold psy-text-slate-700 psy-bg-slate-100 hover:psy-bg-slate-200 focus:psy-outline-none focus:psy-ring-2 focus:psy-ring-primary psy-transition-all"
        >
          <Eye className="psy-w-3.5 psy-h-3.5 psy-text-slate-600" />
          <span>Ver Prontuário</span>
        </button>

        <button
          type="button"
          onClick={() => onStartTriage(patientId)}
          aria-label={`Iniciar nova evolução para o paciente ${displayName}`}
          className="psy-inline-flex psy-items-center psy-justify-center psy-gap-1.5 psy-px-3 psy-py-2 psy-rounded-lg psy-text-xs psy-font-semibold psy-text-white psy-bg-primary hover:psy-bg-primary/90 focus:psy-outline-none focus:psy-ring-2 focus:psy-ring-primary psy-transition-all"
        >
          <Stethoscope className="psy-w-3.5 psy-h-3.5" />
          <span>Nova Evolução</span>
        </button>
      </div>
    </div>
  );
};
