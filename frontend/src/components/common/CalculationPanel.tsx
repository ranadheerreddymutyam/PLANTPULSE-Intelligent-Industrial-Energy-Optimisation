import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Calculator, Info } from 'lucide-react';
import { EngineeringValue } from '../../types';
import { ProvenanceBadge } from './ProvenanceBadge';

interface CalculationPanelProps {
  title?: string;
  calc?: EngineeringValue;
  customFormula?: string;
  inputs?: Record<string, any>;
  unit?: string;
  provenance?: string;
  note?: string;
}

export const CalculationPanel: React.FC<CalculationPanelProps> = ({
  title = 'View Engineering Calculation',
  calc,
  customFormula,
  inputs,
  unit,
  provenance,
  note
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const formula = calc?.formula || customFormula || 'Derived standard formula';
  const displayInputs = calc?.inputs || inputs || {};
  const displayUnit = calc?.unit || unit || '';
  const displayProv = calc?.provenance || provenance || 'DERIVED';
  const displayNote = calc?.note || note;

  return (
    <div className="mt-2 border border-slate-200 rounded-lg bg-slate-50/60 overflow-hidden text-xs">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3 py-2 text-left font-medium text-slate-700 hover:bg-slate-100 transition-colors focus:outline-none focus:ring-1 focus:ring-emerald-500"
      >
        <span className="flex items-center gap-1.5 font-medium">
          <Calculator className="w-3.5 h-3.5 text-emerald-600" />
          <span>{title}</span>
        </span>
        <span className="flex items-center gap-2">
          <ProvenanceBadge type={displayProv} size="xs" />
          {isOpen ? <ChevronDown className="w-3.5 h-3.5 text-slate-500" /> : <ChevronRight className="w-3.5 h-3.5 text-slate-500" />}
        </span>
      </button>

      {isOpen && (
        <div className="px-3 pb-3 pt-1 border-t border-slate-200 space-y-2 bg-white">
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-0.5">Formula</div>
            <code className="block bg-slate-900 text-emerald-300 font-mono text-[11px] px-2.5 py-1.5 rounded border border-slate-800">
              {formula}
            </code>
          </div>

          {Object.keys(displayInputs).length > 0 && (
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-0.5">Parameters & Inputs</div>
              <div className="grid grid-cols-2 gap-1.5 bg-slate-50 p-2 rounded border border-slate-100 font-mono text-[11px]">
                {Object.entries(displayInputs).map(([k, v]) => (
                  <div key={k} className="flex justify-between border-b border-slate-200/50 pb-0.5">
                    <span className="text-slate-500">{k}:</span>
                    <span className="font-semibold text-slate-800">{String(v)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex items-center justify-between text-[11px] pt-1">
            <span className="text-slate-500">Output Unit: <strong className="text-slate-800">{displayUnit || 'none'}</strong></span>
            <span className="text-slate-500">Model: <code className="text-slate-700">{calc?.model_version || '1.0.0-prototype'}</code></span>
          </div>

          {displayNote && (
            <div className="flex items-start gap-1.5 text-[11px] text-slate-600 bg-amber-50/60 border border-amber-200/60 p-2 rounded">
              <Info className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
              <span>{displayNote}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
