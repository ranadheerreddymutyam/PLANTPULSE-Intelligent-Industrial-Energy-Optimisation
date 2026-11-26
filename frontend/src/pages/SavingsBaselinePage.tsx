import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { ProvenanceBadge } from '../components/common/ProvenanceBadge';
import { MetricCard } from '../components/common/MetricCard';
import { CalculationPanel } from '../components/common/CalculationPanel';
import { TrendingDown, DollarSign, Leaf, Zap, HelpCircle, CheckCircle2, RefreshCw } from 'lucide-react';

export const SavingsBaselinePage: React.FC = () => {
  const [comparison, setComparison] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadComparison();
  }, []);

  const loadComparison = async () => {
    try {
      setLoading(true);
      const res = await api.getBaselineComparison();
      setComparison(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-emerald-50/60 border border-emerald-200 rounded-xl p-5 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-1.5">
            <TrendingDown className="w-4 h-4 text-emerald-700" />
            Quantified Opportunity & Baseline Comparison
          </span>
          <ProvenanceBadge type="ESTIMATED" size="xs" />
        </div>
        <h2 className="text-lg font-bold text-slate-900 tracking-tight">
          Controlled Before/After Evaluation Under Identical Schedule
        </h2>
        <p className="text-xs text-slate-600 leading-relaxed">
          Savings are computed strictly by comparing the unmitigated Baseline Run against the Optimised Run generated with identical random seeds, duty schedules, and operational parameters.
        </p>
      </div>

      {/* Comparison Cards */}
      {comparison && comparison.comparison_available ? (
        <div className="space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              label="Baseline Total Energy"
              value={comparison.baseline_total_kwh}
              unit="kWh"
              provenance="DERIVED"
              subtitle="Unmitigated shift run"
              icon={<Zap className="w-4 h-4 text-slate-600" />}
            />
            <MetricCard
              label="Optimised Shift Energy"
              value={comparison.optimised_total_kwh}
              unit="kWh"
              provenance="DERIVED"
              subtitle="Approved shutdowns applied"
              icon={<Zap className="w-4 h-4 text-emerald-600" />}
            />
            <MetricCard
              label="Avoidable Energy Saved"
              value={comparison.net_saved_kwh}
              unit="kWh"
              provenance="ESTIMATED"
              customFormula="E_save = max(0, E_avoid - E_restart_allowance)"
              subtitle={`Saving Ratio: ${comparison.saving_percentage}%`}
              statusColor="normal"
              icon={<TrendingDown className="w-4 h-4 text-emerald-600" />}
            />
            <MetricCard
              label="Estimated Cost Savings"
              value={comparison.cost_saved}
              unit={comparison.currency || 'USD'}
              provenance="ESTIMATED"
              customFormula="Cost = E_save * tariff"
              subtitle={`Tariff: ${comparison.assumptions?.tariff_per_kwh} USD/kWh`}
              statusColor="normal"
              icon={<DollarSign className="w-4 h-4 text-emerald-600" />}
            />
          </div>

          {/* Three-Bar Visual Comparison */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Shift Energy Comparison</h3>
                <p className="text-xs text-slate-500 font-mono">
                  Controlled seed: <strong>{comparison.seed}</strong> · Duration: 8 hours
                </p>
              </div>
              <ProvenanceBadge type={comparison.provenance} size="xs" />
            </div>

            <div className="space-y-4 pt-2">
              <div>
                <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
                  <span>Baseline Run (Unmitigated Idle)</span>
                  <span className="font-mono">{comparison.baseline_total_kwh} kWh (100%)</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-4 overflow-hidden">
                  <div className="bg-slate-700 h-full rounded-full" style={{ width: '100%' }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-semibold text-emerald-800 mb-1">
                  <span>Optimised Run (Operator-Approved Controlled Shutdown)</span>
                  <span className="font-mono">
                    {comparison.optimised_total_kwh} kWh ({((comparison.optimised_total_kwh / comparison.baseline_total_kwh) * 100).toFixed(1)}%)
                  </span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-4 overflow-hidden">
                  <div
                    className="bg-emerald-600 h-full rounded-full"
                    style={{ width: `${Math.min(100, (comparison.optimised_total_kwh / comparison.baseline_total_kwh) * 100)}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-semibold text-amber-800 mb-1">
                  <span>Avoidable Idle Energy Eliminated</span>
                  <span className="font-mono">{comparison.net_saved_kwh} kWh ({comparison.saving_percentage}%)</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-4 overflow-hidden">
                  <div
                    className="bg-amber-500 h-full rounded-full"
                    style={{ width: `${Math.min(100, comparison.saving_percentage)}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Assumptions Transparency Box */}
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-2 text-xs">
              <div className="font-bold text-slate-900 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                Fairness & Engineering Assumptions
              </div>
              <ul className="space-y-1 text-slate-600 list-disc list-inside">
                <li>
                  <strong>Fairness Guarantee:</strong> {comparison.assumptions?.fairness_guarantee}
                </li>
                <li>
                  <strong>Tariff Reference:</strong> Configured reference of {comparison.assumptions?.tariff_per_kwh} USD/kWh.
                </li>
                <li>
                  <strong>Grid Emission Factor:</strong> {comparison.assumptions?.emission_factor_kg_co2_per_kwh} kg CO2e/kWh (demonstration reference).
                </li>
                <li>
                  <strong>Restart Allowance:</strong> {comparison.assumptions?.restart_allowance_kwh} kWh per restart cycle.
                </li>
              </ul>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white p-8 rounded-xl border text-center text-slate-500 text-xs">
          Loading baseline data...
        </div>
      )}
    </div>
  );
};
