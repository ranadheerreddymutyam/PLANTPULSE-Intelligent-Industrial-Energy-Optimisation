import React from 'react';
import { ProvenanceType } from '../../types';

interface ProvenanceBadgeProps {
  type: ProvenanceType | string;
  size?: 'xs' | 'sm';
}

export const ProvenanceBadge: React.FC<ProvenanceBadgeProps> = ({ type, size = 'xs' }) => {
  const norm = (type || 'SIMULATED').toUpperCase();
  
  let colorStyles = 'bg-slate-100 text-slate-700 border-slate-300';
  let label = norm;

  switch (norm) {
    case 'SIMULATED':
      colorStyles = 'bg-purple-50 text-purple-700 border-purple-200';
      label = 'SIMULATED';
      break;
    case 'DERIVED':
      colorStyles = 'bg-blue-50 text-blue-700 border-blue-200';
      label = 'DERIVED';
      break;
    case 'ESTIMATED':
      colorStyles = 'bg-amber-50 text-amber-700 border-amber-200';
      label = 'ESTIMATED';
      break;
    case 'CONFIGURED':
      colorStyles = 'bg-slate-50 text-slate-600 border-slate-200';
      label = 'CONFIGURED';
      break;
    case 'IMPORTED':
      colorStyles = 'bg-emerald-50 text-emerald-700 border-emerald-200';
      label = 'IMPORTED';
      break;
  }

  const sizeClasses = size === 'xs' ? 'text-[9px] px-1.5 py-0.5' : 'text-[11px] px-2 py-0.5';

  return (
    <span
      className={`inline-flex items-center font-mono font-semibold uppercase tracking-wider rounded border ${sizeClasses} ${colorStyles}`}
      title={`Data Provenance: ${label}`}
    >
      {label}
    </span>
  );
};
