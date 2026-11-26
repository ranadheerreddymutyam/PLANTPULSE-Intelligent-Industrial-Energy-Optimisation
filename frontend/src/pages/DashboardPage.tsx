import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { DashboardOverview } from '../types';
import { MetricCard } from '../components/common/MetricCard';
import { TimeSeriesChart } from '../components/common/Charts';
import { ProvenanceBadge } from '../components/common/ProvenanceBadge';
import { Zap, Clock, ShieldCheck, AlertTriangle, TrendingDown, CheckCircle2, Activity } from 'lucide-react';

interface DashboardPageProps {
  onNavigate: (page: any) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigate }) => {
  const [data, setData] = useState<DashboardOverview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadOverview();
  }, []);

  const loadOverview = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getDashboardOverview();
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard overview');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500 text-sm">
        <Activity className="w-5 h-5 animate-spin mr-2 text-emerald-600" />
        Loading real-time engineering metrics...
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl text-sm">
        {error || 'No overview data received.'}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Headline Interpretation Sentence */}
      <div className="bg-emerald-50/70 border border-emerald-200/80 rounded-xl p-4 sm:p-5 flex flex-wrap items-center justify-between gap-3 shadow-xs">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse" />
            <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-800">Operational Headline</span>
            <ProvenanceBadge type="DERIVED" size="xs" />
          </div>
          <p className="text-sm sm:text-base font-bold text-slate-900 leading-snug">
            {data.headline_sentence}
          </p>
          {data.idle_equipment_names.length > 0 && (
            <p className="text-xs text-slate-600">
              Currently idle assets: <span className="font-semibold text-slate-800">{data.idle_equipment_names.join(', ')}</span>
            </p>
          )}
        </div>
        <button
          onClick={() => onNavigate('idle')}
          className="px-3.5 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold rounded-lg transition shadow-xs"
        >
          Inspect Idle Breakdown &rarr;
        </button>
      </div>

      {/* Primary Key Electrical & Energy Indicators */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Real-Time Electrical & Power Metrics (3-Phase 415 V Balanced Supply)
          </h2>
          <span className="text-[11px] font-mono text-slate-500">{data.site_name}</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            label="Total Active Power (P)"
            value={data.total_active_kw}
            unit="kW"
            provenance="DERIVED"
            customFormula="P_total = sum(sqrt(3) * V_LL * I * PF / 1000)"
            subtitle="Aggregated line active load"
            icon={<Zap className="w-4 h-4 text-emerald-600" />}
          />
          <MetricCard
            label="Cumulative Energy (E)"
            value={data.total_site_kwh}
            unit="kWh"
            provenance="DERIVED"
            customFormula="E = integral(P dt) via trapezoidal rule"
            subtitle="Integrated over active scenario shift"
            icon={<Activity className="w-4 h-4 text-blue-600" />}
          />
          <MetricCard
            label="Avoidable Idle Energy"
            value={data.avoidable_idle_energy_kwh}
            unit="kWh"
            provenance="ESTIMATED"
            customFormula="E_avoid = sum(P * dt) for t >= t_delay on eligible loads"
            subtitle="Potential saving opportunity"
            statusColor={data.avoidable_idle_energy_kwh > 0 ? 'warning' : 'normal'}
            icon={<Clock className="w-4 h-4 text-amber-600" />}
          />
          <MetricCard
            label="Idle Share of Consumption"
            value={`${data.idle_share_percent}`}
            unit="%"
            provenance="DERIVED"
            customFormula="Idle Share % = (E_idle / E_total) * 100"
            subtitle={`Total Idle: ${data.total_idle_energy_kwh} kWh`}
            icon={<TrendingDown className="w-4 h-4 text-purple-600" />}
          />
        </div>
      </div>

      {/* Secondary Electrical Health Indicators */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <MetricCard
          label="Average Supply Voltage"
          value={data.avg_voltage_v}
          unit="V"
          provenance="SIMULATED"
          subtitle="Nominal: 415.0 V LL RMS"
        />
        <MetricCard
          label="Total Feeder Current"
          value={data.total_current_a}
          unit="A"
          provenance="SIMULATED"
          subtitle="Line RMS summation"
        />
        <MetricCard
          label="Site Power Factor (PF)"
          value={data.avg_power_factor}
          unit=""
          provenance="DERIVED"
          customFormula="PF = P / S"
          subtitle="Reference threshold: >= 0.80"
          statusColor={data.avg_power_factor < 0.80 ? 'warning' : 'normal'}
        />
        <MetricCard
          label="Equipment In Service"
          value={`${data.equipment_by_state.RUNNING} Run / ${data.equipment_by_state.IDLE} Idle / ${data.equipment_by_state.STOPPED} Stop`}
          provenance="DERIVED"
          subtitle={`Total Assets: ${data.total_equipment_count}`}
        />
      </div>

      {/* Estimated Savings Potential Cards */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200/80 pb-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Estimated Opportunity from Simulated Dataset</h3>
            <p className="text-xs text-slate-500">
              Quantified under current engineering reference settings (Tariff: {data.savings.cost_savings.inputs?.tariff_per_kwh || 0.18} USD/kWh, Emission factor: {data.savings.emissions_reduction_kg_co2.inputs?.emission_factor_kg_co2_per_kwh || 0.42} kg CO2e/kWh)
            </p>
          </div>
          <button
            onClick={() => onNavigate('savings')}
            className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 underline"
          >
            Review Baseline Comparison &rarr;
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <MetricCard
            label="Estimated Energy Saving"
            value={data.savings.energy_savings_kwh.value}
            unit="kWh"
            provenance="ESTIMATED"
            calc={data.savings.energy_savings_kwh}
            statusColor="normal"
          />
          <MetricCard
            label="Estimated Cost Saving"
            value={data.savings.cost_savings.value}
            unit="USD"
            provenance="ESTIMATED"
            calc={data.savings.cost_savings}
            statusColor="normal"
          />
          <MetricCard
            label="Estimated Emissions Reduction"
            value={data.savings.emissions_reduction_kg_co2.value}
            unit="kg CO2e"
            provenance="ESTIMATED"
            calc={data.savings.emissions_reduction_kg_co2}
            statusColor="normal"
          />
        </div>
      </div>

      {/* Power Profile Sparkline Chart */}
      <TimeSeriesChart
        title="Aggregate Active Power vs. Idle Component (Recent Telemetry Window)"
        data={data.sparkline}
        series={[
          { key: 'total_kw', label: 'Total Active Load', color: '#0f172a', unit: 'kW' },
          { key: 'idle_kw', label: 'Avoidable Idle Power', color: '#eab308', unit: 'kW' }
        ]}
        height={240}
        provenance="SIMULATED"
      />

      {/* Action Banners for Pending Operator Tasks */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
        <div
          onClick={() => onNavigate('control')}
          className="cursor-pointer bg-white border border-amber-200 hover:border-amber-300 rounded-xl p-4 flex items-center justify-between gap-4 transition shadow-xs group"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center shrink-0">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-800">Pending Operator Approvals</div>
              <div className="text-xs text-slate-500">
                {data.pending_approvals_count} shutdown recommendations awaiting manual operator sign-off
              </div>
            </div>
          </div>
          <span className="text-xs font-bold text-amber-700 group-hover:underline">Review &rarr;</span>
        </div>

        <div
          onClick={() => onNavigate('events')}
          className="cursor-pointer bg-white border border-red-200 hover:border-red-300 rounded-xl p-4 flex items-center justify-between gap-4 transition shadow-xs group"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-red-50 text-red-700 flex items-center justify-center shrink-0">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-800">Active Alert Events</div>
              <div className="text-xs text-slate-500">
                {data.active_events_count} grouped parameter deviations under non-binding advisory
              </div>
            </div>
          </div>
          <span className="text-xs font-bold text-red-700 group-hover:underline">Inspect &rarr;</span>
        </div>
      </div>
    </div>
  );
};
