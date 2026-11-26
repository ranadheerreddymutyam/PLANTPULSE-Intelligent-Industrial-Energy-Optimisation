import React from 'react';
import { ProvenanceType, EngineeringValue } from '../../types';
import { ProvenanceBadge } from './ProvenanceBadge';
import { CalculationPanel } from './CalculationPanel';

interface MetricCardProps {
  label: string;
  value: string | number | null | undefined;
  unit?: string;
  provenance: ProvenanceType | string;
  calc?: EngineeringValue;
  customFormula?: string;
  inputs?: Record<string, any>;
  icon?: React.ReactNode;
  subtitle?: string;
  statusColor?: 'normal' | 'warning' | 'attention' | 'neutral';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  unit,
  provenance,
  calc,
  customFormula,
  inputs,
  icon,
  subtitle,
  statusColor = 'neutral'
}) => {
  const displayVal = value !== null && value !== undefined ? value : '—';

  let statusRing = 'border-slate-200';
  if (statusColor === 'normal') statusRing = 'border-emerald-300 ring-1 ring-emerald-100';
  if (statusColor === 'warning') statusRing = 'border-amber-300 ring-1 ring-amber-100';
  if (statusColor === 'attention') statusRing = 'border-red-300 ring-1 ring-red-100';

  return (
    <div className={`bg-white rounded-xl border p-4 shadow-sm flex flex-col justify-between ${statusRing}`}>
      <div>
        <div className="flex items-start justify-between gap-2 mb-2">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{label}</span>
          <div className="flex items-center gap-1.5 shrink-0">
            <ProvenanceBadge type={provenance} size="xs" />
            {icon && <div className="text-slate-400">{icon}</div>}
          </div>
        </div>

        <div className="flex items-baseline gap-1.5">
          <span className="text-2xl font-bold tracking-tight text-slate-900 font-mono">
            {displayVal}
          </span>
          {unit && <span className="text-sm font-medium text-slate-500">{unit}</span>}
        </div>

        {subtitle && (
          <p className="mt-1 text-xs text-slate-500 font-medium">{subtitle}</p>
        )}
      </div>

      {(calc || customFormula) && (
        <CalculationPanel
          calc={calc}
          customFormula={customFormula}
          inputs={inputs}
          unit={unit}
          provenance={provenance}
        />
      )}
    </div>
  );
};
