import React from 'react';
import { CheckCircle2, AlertTriangle, AlertOctagon, HelpCircle } from 'lucide-react';
import { RiskLevel } from '@/lib/schemas';
import { cn } from '@/lib/utils';

interface Props {
  riskLevel: RiskLevel;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  className?: string;
}

export const ClinicalRiskBadge: React.FC<Props> = ({
  riskLevel,
  size = 'md',
  showIcon = true,
  className,
}) => {
  const getBadgeStyle = (level: RiskLevel) => {
    switch (level) {
      case 'Baixo':
        return {
          container: 'psy-bg-green-100 psy-text-green-800 psy-border-green-300',
          icon: CheckCircle2,
          iconClass: 'psy-text-green-600',
          text: 'Risco Baixo',
        };
      case 'Moderado':
        return {
          container: 'psy-bg-yellow-100 psy-text-yellow-800 psy-border-yellow-400 psy-font-bold psy-border',
          icon: AlertTriangle,
          iconClass: 'psy-text-yellow-600',
          text: 'Risco Moderado',
        };
      case 'Alto/Iminente':
        return {
          container: 'psy-bg-red-100 psy-text-red-900 psy-border-red-500 psy-border-2 psy-font-bold',
          icon: AlertOctagon,
          iconClass: 'psy-text-red-600 psy-animate-pulse',
          text: 'Risco Alto / Iminente',
        };
      default:
        return {
          container: 'psy-bg-gray-100 psy-text-gray-800 psy-border-gray-300',
          icon: HelpCircle,
          iconClass: 'psy-text-gray-500',
          text: 'Risco indeterminado',
        };
    }
  };

  const getSizeStyle = (sz: 'sm' | 'md' | 'lg') => {
    switch (sz) {
      case 'sm':
        return {
          padding: 'psy-px-2 psy-py-0.5 psy-text-xs',
          iconSize: 14,
        };
      case 'lg':
        return {
          padding: 'psy-px-4 psy-py-2 psy-text-base',
          iconSize: 22,
        };
      case 'md':
      default:
        return {
          padding: 'psy-px-3 psy-py-1 psy-text-sm',
          iconSize: 18,
        };
    }
  };

  const style = getBadgeStyle(riskLevel);
  const sizeStyle = getSizeStyle(size);
  const IconComponent = style.icon;

  return (
    <span
      role="status"
      aria-label={`Nível de risco de triagem: ${style.text}`}
      className={cn(
        'psy-inline-flex psy-items-center psy-gap-1.5 psy-rounded-full psy-font-medium psy-transition-all',
        style.container,
        sizeStyle.padding,
        className
      )}
    >
      {showIcon && (
        <IconComponent
          size={sizeStyle.iconSize}
          className={cn('psy-shrink-0', style.iconClass)}
          aria-hidden="true"
        />
      )}
      <span>{style.text}</span>
    </span>
  );
};
