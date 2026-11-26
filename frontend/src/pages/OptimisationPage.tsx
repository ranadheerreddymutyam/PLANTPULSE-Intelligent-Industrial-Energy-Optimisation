import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Decision, Equipment } from '../types';
import { ProvenanceBadge } from '../components/common/ProvenanceBadge';
import { CheckCircle2, XCircle, AlertCircle, HelpCircle, Shield, ArrowRight, Zap, RefreshCw } from 'lucide-react';

export const OptimisationPage: React.FC = () => {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [equipmentList, setEquipmentList] = useState<Equipment[]>([]);
  const [selectedEqId, setSelectedEqId] = useState<string>('eq_conveyor_motor');
  const [tradeoffs, setTradeoffs] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [decList, eqList, tradeRes] = await Promise.all([
        api.getLatestDecisions(),
        api.listEquipment(),
        api.getTradeoffs()
      ]);
      setDecisions(decList);
      setEquipmentList(eqList);
      setTradeoffs(tradeRes);
      if (eqList.length > 0 && !selectedEqId) {
        setSelectedEqId(eqList[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const selectedDecision = decisions.find(d => d.equipment_id === selectedEqId);
  const selectedEq = equipmentList.find(e => e.id === selectedEqId);

  return (
    <div className="space-y-6">
      {/* Page Header & Track Question 2 & 3 */}
      <div className="bg-emerald-50/60 border border-emerald-200 rounded-xl p-5 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-1.5">
            <Zap className="w-4 h-4 text-emerald-700" />
            8-Step Logical Flow & Engineering Recommendations
          </span>
          <ProvenanceBadge type="DERIVED" size="xs" />
        </div>
        <h2 className="text-lg font-bold text-slate-900 tracking-tight">
          Deterministic Decision Pipeline (Mirrors Challenge Logic)
        </h2>
        <p className="text-xs text-slate-600 leading-relaxed">
          Every evaluation window passes through a strictly non-AI, explainable state machine.
          Controlled shutdown is never automatic — it requires verified safety interlocks and authorized operator approval.
        </p>
      </div>

      {/* Asset Selector Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 border-b border-slate-200">
        {equipmentList.map(eq => {
          const isSelected = eq.id === selectedEqId;
          const dec = decisions.find(d => d.equipment_id === eq.id);
          const isApproved = dec?.outcome === 'APPROVED NON-CRITICAL';
          const isBlocked = dec?.outcome.startsWith('BLOCKED');
          const isSustained = dec?.outcome === 'SUSTAINED IDLE';

          let indicator = 'bg-slate-300';
          if (isApproved) indicator = 'bg-emerald-600';
          if (isSustained) indicator = 'bg-amber-500';
          if (isBlocked) indicator = 'bg-blue-500';

          return (
            <button
              key={eq.id}
              onClick={() => setSelectedEqId(eq.id)}
              className={`flex items-center gap-2 px-3 py-2 text-xs font-semibold rounded-lg shrink-0 transition ${
                isSelected
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${indicator}`} />
              <span>{eq.name}</span>
            </button>
          );
        })}
      </div>

      {/* 8-Step State Machine Visualizer */}
      {selectedDecision ? (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-slate-900 text-sm">
                  Decision Trace for {selectedEq?.name || selectedEqId}
                </h3>
                <ProvenanceBadge type={selectedDecision.provenance} size="xs" />
              </div>
              <p className="text-xs text-slate-500 font-mono mt-0.5">
                Outcome: <strong className="text-slate-900">{selectedDecision.outcome}</strong> · Reason: {selectedDecision.reason}
              </p>
            </div>

            <div className="text-right">
              <span className={`text-xs font-bold font-mono px-2.5 py-1 rounded-md ${
                selectedDecision.outcome === 'APPROVED NON-CRITICAL'
                  ? 'bg-emerald-100 text-emerald-800'
                  : selectedDecision.outcome === 'SUSTAINED IDLE'
                  ? 'bg-amber-100 text-amber-800'
                  : 'bg-slate-100 text-slate-700'
              }`}>
                Evaluation Stopped at Step {selectedDecision.evaluation_step} / 8
              </span>
            </div>
          </div>

          {/* Stepper Grid (Steps 1 through 8) */}
          <div className="space-y-2.5">
            {selectedDecision.decision_trace.map((step, idx) => {
              const isPassed = step.status === 'PASSED';
              const isFailed = step.status === 'FAILED';
              const isTerminated = step.status === 'TERMINATED';

              let borderCol = 'border-slate-200 bg-slate-50/50';
              let badgeCol = 'bg-slate-200 text-slate-700';
              let icon = <CheckCircle2 className="w-4 h-4 text-emerald-600" />;

              if (isPassed) {
                borderCol = 'border-emerald-200 bg-emerald-50/30';
                badgeCol = 'bg-emerald-100 text-emerald-800';
                icon = <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />;
              } else if (isFailed) {
                borderCol = 'border-red-200 bg-red-50/30';
                badgeCol = 'bg-red-100 text-red-800';
                icon = <XCircle className="w-4 h-4 text-red-600 shrink-0" />;
              } else if (isTerminated) {
                borderCol = 'border-blue-200 bg-blue-50/30';
                badgeCol = 'bg-blue-100 text-blue-800';
                icon = <AlertCircle className="w-4 h-4 text-blue-600 shrink-0" />;
              }

              return (
                <div key={step.step_number} className={`border rounded-lg p-3 ${borderCol} transition-colors`}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-2.5">
                      <div className="mt-0.5">{icon}</div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-slate-900">
                            Step {step.step_number}: {step.step_name}
                          </span>
                          <span className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded uppercase ${badgeCol}`}>
                            {step.status}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">
                          {step.evaluation}
                        </p>
                      </div>
                    </div>

                    {/* Step telemetry values snapshot */}
                    {Object.keys(step.values || {}).length > 0 && (
                      <div className="hidden sm:block text-right font-mono text-[11px] text-slate-500 shrink-0">
                        {Object.entries(step.values).slice(0, 2).map(([k, v]) => (
                          <div key={k}>{k}: <strong className="text-slate-800">{String(v)}</strong></div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Actionable Engineering Recommendation */}
          {selectedDecision.recommendation_text && (
            <div className="bg-slate-900 text-white rounded-lg p-4 space-y-1">
              <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold uppercase tracking-wider">
                <Zap className="w-4 h-4" />
                Actionable Recommendation
              </div>
              <p className="text-xs text-slate-200 leading-relaxed">
                {selectedDecision.recommendation_text}
              </p>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white p-8 rounded-xl border text-center text-slate-400 text-xs">
          Select an asset to view its step-by-step evaluation trace.
        </div>
      )}

      {/* Trade-off Checklist (Answers Challenge Question 3) */}
      {tradeoffs && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="border-b border-slate-100 pb-3">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-slate-900 text-sm">{tradeoffs.title}</h3>
              <ProvenanceBadge type={tradeoffs.provenance} size="xs" />
            </div>
            <p className="text-xs text-slate-500">{tradeoffs.subtitle}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {tradeoffs.tradeoffs.map((item: any, idx: number) => (
              <div key={idx} className="border border-slate-200 rounded-lg p-4 bg-slate-50/50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    {item.category}
                  </span>
                  <span className="text-[11px] font-mono text-slate-500 font-semibold">{item.status_check}</span>
                </div>
                <div className="font-bold text-slate-800 text-xs">{item.risk}</div>
                <p className="text-xs text-slate-600 leading-relaxed">{item.detail}</p>
                <div className="text-xs text-slate-700 bg-white p-2 rounded border border-slate-200 font-medium">
                  <strong className="text-slate-900">Engineering Mitigation:</strong> {item.mitigation}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
