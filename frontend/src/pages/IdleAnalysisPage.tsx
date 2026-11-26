import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { IdlePeriod, LossRankItem } from '../types';
import { ProvenanceBadge } from '../components/common/ProvenanceBadge';
import { CalculationPanel } from '../components/common/CalculationPanel';
import { Clock, TrendingDown, HelpCircle, CheckCircle2, Lock } from 'lucide-react';

export const IdleAnalysisPage: React.FC = () => {
  const [rankingData, setRankingData] = useState<{
    title: string;
    total_avoidable_idle_energy_kwh: number;
    ranking: LossRankItem[];
    provenance: string;
    note: string;
  } | null>(null);
  const [periods, setPeriods] = useState<IdlePeriod[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadIdleData();
  }, []);

  const loadIdleData = async () => {
    try {
      setLoading(true);
      const [rankRes, periodsRes] = await Promise.all([
        api.getLossRanking(),
        api.getIdlePeriods()
      ]);
      setRankingData(rankRes);
      setPeriods(periodsRes);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const maxAvoidable = rankingData?.ranking.length
    ? Math.max(...rankingData.ranking.map(r => r.avoidable_idle_energy_kwh)) || 1
    : 1;

  return (
    <div className="space-y-6">
      {/* Page Title & Track Question 1 */}
      <div className="bg-emerald-50/60 border border-emerald-200 rounded-xl p-5 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-1.5">
            <HelpCircle className="w-4 h-4 text-emerald-700" />
            L'Oréal Challenge Consideration Question 1
          </span>
          <ProvenanceBadge type="ESTIMATED" size="xs" />
        </div>
        <h2 className="text-lg font-bold text-slate-900 tracking-tight">
          Where does the loss occur?
        </h2>
        <p className="text-xs text-slate-600 leading-relaxed">
          Idle electricity is isolated through continuous active-power signature monitoring (P &lt; P_idle) sustained beyond configured time delays (t &ge; t_delay).
          Losses occur predominantly on auxiliary equipment running during meal breaks, shift handovers, and line standby.
        </p>
      </div>

      {/* Avoidable Energy Loss Ranking (Chart & Table) */}
      {rankingData && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
            <div>
              <h3 className="font-bold text-slate-900 text-sm">{rankingData.title}</h3>
              <p className="text-xs text-slate-500 font-mono">
                Total avoidable idle energy identified: <strong>{rankingData.total_avoidable_idle_energy_kwh} kWh</strong>
              </p>
            </div>
            <ProvenanceBadge type={rankingData.provenance} size="xs" />
          </div>

          {/* Visual Ranked Bar Chart */}
          <div className="space-y-3 pt-1">
            {rankingData.ranking.map(item => {
              const widthPct = Math.max(3, (item.avoidable_idle_energy_kwh / maxAvoidable) * 100);
              const isCritical = item.criticality === 'CRITICAL';

              return (
                <div key={item.equipment_id} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-800 flex items-center gap-1.5">
                      {item.equipment_name}
                      {isCritical && (
                        <span className="text-[10px] font-mono text-red-600 bg-red-50 border border-red-200 px-1.5 py-0.2 rounded flex items-center gap-1">
                          <Lock className="w-2.5 h-2.5" /> Critical (0 kWh avoidable)
                        </span>
                      )}
                    </span>
                    <span className="font-mono text-xs text-slate-700">
                      <strong>{item.avoidable_idle_energy_kwh.toFixed(2)} kWh</strong>
                      <span className="text-slate-400 text-[11px] ml-1.5">({item.share_of_avoidable_percent}%)</span>
                    </span>
                  </div>

                  <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isCritical ? 'bg-slate-300' : 'bg-emerald-600'
                      }`}
                      style={{ width: `${widthPct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Calculation Panel */}
          <CalculationPanel
            title="Formula: Avoidable Idle Energy Integration"
            customFormula="E_avoid = integral(P dt) for t in [t_start + t_delay, t_end] if eligible else 0"
            inputs={{
              formula_basis: "Portion strictly after t_delay has elapsed",
              critical_asset_rule: "Zero for all equipment with Criticality=CRITICAL"
            }}
            unit="kWh"
            provenance="ESTIMATED"
            note="Restart allowance not subtracted at individual equipment level; deducted at site summary."
          />
        </div>
      )}

      {/* Qualifying Idle Periods Log */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="font-bold text-slate-900 text-sm">Qualifying Idle Periods Log</h3>
            <p className="text-xs text-slate-500">Continuous idle segments satisfying duration requirement (t &ge; t_delay)</p>
          </div>
          <span className="text-xs font-mono text-slate-500">{periods.length} qualifying periods detected</span>
        </div>

        {periods.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-xs">
            No qualifying idle periods detected under current threshold settings.
          </div>
        ) : (
          <div className="overflow-x-auto border border-slate-100 rounded-lg max-h-80">
            <table className="min-w-full text-xs text-left">
              <thead className="bg-slate-50 text-slate-700 uppercase font-semibold border-b border-slate-200 sticky top-0">
                <tr>
                  <th className="px-3 py-2">ID</th>
                  <th className="px-3 py-2">Asset ID</th>
                  <th className="px-3 py-2">Start Time</th>
                  <th className="px-3 py-2">End Time</th>
                  <th className="px-3 py-2">Duration</th>
                  <th className="px-3 py-2">Threshold</th>
                  <th className="px-3 py-2">Total Idle kWh</th>
                  <th className="px-3 py-2">Avoidable kWh</th>
                  <th className="px-3 py-2">Eligibility</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                {periods.map(p => (
                  <tr key={p.id} className="hover:bg-slate-50">
                    <td className="px-3 py-1.5 text-slate-400">#{p.id}</td>
                    <td className="px-3 py-1.5 font-semibold text-slate-800">{p.equipment_id}</td>
                    <td className="px-3 py-1.5 text-slate-600">{p.start_time.replace('T', ' ').substring(0, 19)}</td>
                    <td className="px-3 py-1.5 text-slate-600">{p.end_time.replace('T', ' ').substring(0, 19)}</td>
                    <td className="px-3 py-1.5 text-slate-800">{(p.duration_seconds / 60).toFixed(1)} min</td>
                    <td className="px-3 py-1.5 text-slate-500">&lt; {p.p_idle_threshold_kw} kW</td>
                    <td className="px-3 py-1.5 text-slate-900 font-medium">{p.total_idle_energy_kwh.toFixed(3)}</td>
                    <td className="px-3 py-1.5 font-bold text-emerald-700">
                      {p.avoidable_energy_kwh.toFixed(3)}
                    </td>
                    <td className="px-3 py-1.5">
                      {p.eligible ? (
                        <span className="text-[10px] text-emerald-700 font-semibold bg-emerald-50 px-1.5 py-0.5 rounded">Eligible</span>
                      ) : (
                        <span className="text-[10px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">Excluded</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
