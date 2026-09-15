import React from 'react';
import { AlertTriangle, AlertCircle, Info, ShieldAlert } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Props {
  alerts: string[];
  className?: string;
}

export const AuditAlerts: React.FC<Props> = ({ alerts, className }) => {
  if (!alerts || alerts.length === 0) {
    return (
      <div
        role="status"
        aria-live="polite"
        className={cn(
          'psy-p-4 psy-rounded-lg psy-bg-slate-50 psy-border psy-border-slate-200 psy-text-slate-600 psy-text-sm psy-flex psy-items-center psy-gap-2',
          className
        )}
      >
        <Info className="psy-w-4 psy-h-4 psy-text-slate-400 psy-shrink-0" aria-hidden="true" />
        <span>Nenhuma divergência grave de protocolo identificada na documentação.</span>
      </div>
    );
  }

  const getAlertStyle = (text: string) => {
    if (text.startsWith('[FALHA CRITICA]')) {
      return {
        container: 'psy-bg-red-50 psy-border-red-500 psy-text-red-950 psy-border-l-4',
        icon: AlertTriangle,
        iconClass: 'psy-text-red-600',
        severityLabel: 'Alerta crítico',
        isCritical: true,
      };
    }
    if (text.startsWith('[ALERTA DE SEGURANÇA]')) {
      return {
        container: 'psy-bg-orange-50 psy-border-orange-400 psy-text-orange-950 psy-border-l-4',
        icon: ShieldAlert,
        iconClass: 'psy-text-orange-600',
        severityLabel: 'Alerta de segurança',
        isCritical: false,
      };
    }
    if (text.startsWith('[RECOMENDACAO]')) {
      return {
        container: 'psy-bg-yellow-50 psy-border-yellow-400 psy-text-yellow-950 psy-border-l-4',
        icon: Info,
        iconClass: 'psy-text-yellow-600',
        severityLabel: 'Recomendação de protocolo',
        isCritical: false,
      };
    }
    return {
      container: 'psy-bg-slate-50 psy-border-slate-300 psy-text-slate-900 psy-border-l-4',
      icon: AlertCircle,
      iconClass: 'psy-text-slate-500',
      severityLabel: 'Alerta de auditoria',
      isCritical: false,
    };
  };

  return (
    <ul role="list" aria-label="Lista de alertas de auditoria" className={cn('psy-space-y-3', className)}>
      {alerts.map((alertText, index) => {
        const style = getAlertStyle(alertText);
        const Icon = style.icon;

        return (
          <li
            key={index}
            role="listitem"
            aria-label={`${style.severityLabel}: ${alertText}`}
            aria-live={style.isCritical ? 'assertive' : undefined}
            className={cn('psy-p-4 psy-rounded-r-lg psy-shadow-sm psy-flex psy-items-start psy-gap-3', style.container)}
          >
            <Icon className={cn('psy-w-5 psy-h-5 psy-mt-0.5 psy-shrink-0', style.iconClass)} aria-hidden="true" />
            <div className="psy-text-sm psy-leading-relaxed psy-font-normal">{alertText}</div>
          </li>
        );
      })}
    </ul>
  );
};
