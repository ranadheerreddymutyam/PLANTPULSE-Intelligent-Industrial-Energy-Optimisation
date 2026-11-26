import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Equipment, Telemetry } from '../types';
import { ProvenanceBadge } from '../components/common/ProvenanceBadge';
import { TimeSeriesChart } from '../components/common/Charts';
import { Lock, Unlock, Zap, Activity, Info, Sliders } from 'lucide-react';

export const EquipmentMonitoringPage: React.FC = () => {
  const [equipmentList, setEquipmentList] = useState<Equipment[]>([]);
  const [latestTelemetry, setLatestTelemetry] = useState<Telemetry[]>([]);
  const [selectedEqId, setSelectedEqId] = useState<string>('eq_conveyor_motor');
  const [historyTelemetry, setHistoryTelemetry] = useState<Telemetry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (selectedEqId) {
      loadHistory(selectedEqId);
    }
  }, [selectedEqId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [eqs, telems] = await Promise.all([
        api.listEquipment(),
        api.getLatestTelemetry()
      ]);
      setEquipmentList(eqs);
      setLatestTelemetry(telems);
      if (eqs.length > 0 && !selectedEqId) {
        setSelectedEqId(eqs[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async (eqId: string) => {
    try {
      const hist = await api.getTelemetryHistory(eqId, 60);
      setHistoryTelemetry(hist);
    } catch (err) {
      console.error(err);
    }
  };

  const selectedEq = equipmentList.find(e => e.id === selectedEqId) || equipmentList[0];
  const selectedLatest = latestTelemetry.find(t => t.equipment_id === selectedEqId);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900 tracking-tight">2. Equipment Electrical Monitoring</h2>
          <p className="text-xs text-slate-500">
            Real-time parameters, operating states, and 3-phase electrical signatures across all connected assets.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ProvenanceBadge type="SIMULATED" size="sm" />
          <span className="text-xs font-mono text-slate-500">415 V Balanced Feeder</span>
        </div>
      </div>

      {/* Equipment Inventory Summary Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="font-semibold text-slate-800 text-sm">Site Asset Registry & Electrical Baseline</h3>
          <span className="text-xs text-slate-500">Select any row to inspect historical load profile</span>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full text-xs text-left">
            <thead className="bg-slate-50 text-slate-700 font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="px-4 py-3">Asset Name & ID</th>
                <th className="px-3 py-3">Type</th>
                <th className="px-3 py-3">Rated Power</th>
                <th className="px-3 py-3">Active (kW)</th>
                <th className="px-3 py-3">Current (A)</th>
                <th className="px-3 py-3">Power Factor</th>
                <th className="px-3 py-3">State</th>
                <th className="px-3 py-3">P_idle Ref</th>
                <th className="px-3 py-3">Criticality</th>
                <th className="px-3 py-3">Control Eligibility</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {equipmentList.map(eq => {
                const tel = latestTelemetry.find(t => t.equipment_id === eq.id);
                const isSelected = eq.id === selectedEqId;
                const isCritical = eq.criticality === 'CRITICAL';

                let stateBadge = 'bg-slate-100 text-slate-700';
                if (tel?.operating_state === 'RUNNING') stateBadge = 'bg-emerald-100 text-emerald-800 font-bold';
                if (tel?.operating_state === 'IDLE') stateBadge = 'bg-amber-100 text-amber-800 font-bold animate-pulse';
                if (tel?.operating_state === 'STOPPED') stateBadge = 'bg-slate-100 text-slate-600';

                return (
                  <tr
                    key={eq.id}
                    onClick={() => setSelectedEqId(eq.id)}
                    className={`cursor-pointer transition-colors ${
                      isSelected ? 'bg-emerald-50/70 font-medium' : 'hover:bg-slate-50'
                    }`}
                  >
                    <td className="px-4 py-2.5">
                      <div className="font-semibold text-slate-900">{eq.name}</div>
                      <div className="text-[10px] font-mono text-slate-400">{eq.id}</div>
                    </td>
                    <td className="px-3 py-2.5 capitalize text-slate-600">{eq.equipment_type}</td>
                    <td className="px-3 py-2.5 font-mono text-slate-800">{eq.rated_power_kw} kW</td>
                    <td className="px-3 py-2.5 font-mono font-bold text-slate-900">
                      {tel ? `${tel.active_power_kw.toFixed(1)} kW` : '—'}
                    </td>
                    <td className="px-3 py-2.5 font-mono text-slate-800">
                      {tel ? `${tel.current_a.toFixed(1)} A` : '—'}
                    </td>
                    <td className="px-3 py-2.5 font-mono text-slate-800">
                      {tel ? tel.power_factor.toFixed(2) : '—'}
                    </td>
                    <td className="px-3 py-2.5">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase ${stateBadge}`}>
                        {tel?.operating_state || 'UNKNOWN'}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 font-mono text-slate-600">
                      &lt; {eq.p_idle_threshold_kw} kW ({eq.t_delay_seconds}s)
                    </td>
                    <td className="px-3 py-2.5">
                      <span
                        className={`inline-flex items-center gap-1 text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                          isCritical
                            ? 'bg-red-50 text-red-700 border border-red-200'
                            : 'bg-slate-100 text-slate-600'
                        }`}
                      >
                        {isCritical && <Lock className="w-3 h-3 text-red-600" />}
                        {eq.criticality}
                      </span>
                    </td>
                    <td className="px-3 py-2.5">
                      {isCritical ? (
                        <span className="text-[11px] font-medium text-red-600 flex items-center gap-1">
                          <Lock className="w-3 h-3" /> Locked Excluded
                        </span>
                      ) : eq.eligible_for_shutdown ? (
                        <span className="text-[11px] font-medium text-emerald-700 flex items-center gap-1">
                          <Unlock className="w-3 h-3" /> Eligible
                        </span>
                      ) : (
                        <span className="text-[11px] text-slate-400">Ineligible</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Selected Equipment Deep Dive */}
      {selectedEq && (
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-3">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-slate-900 text-base">{selectedEq.name}</h3>
                <ProvenanceBadge type={selectedEq.provenance} size="xs" />
                {selectedEq.criticality === 'CRITICAL' && (
                  <span className="bg-red-100 text-red-800 text-[10px] font-bold px-2 py-0.5 rounded flex items-center gap-1">
                    <Lock className="w-3 h-3" /> Critical Process Asset
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 font-mono">
                ID: {selectedEq.id} · Type: {selectedEq.equipment_type} · VFD: {selectedEq.vfd_capable ? 'Equipped' : 'DOL Direct-on-Line'}
              </p>
            </div>

            <div className="text-right text-xs">
              <span className="text-slate-500">Configured Idle Threshold: </span>
              <strong className="text-slate-800 font-mono">&lt; {selectedEq.p_idle_threshold_kw} kW</strong>
              <span className="text-slate-400 mx-1">|</span>
              <span className="text-slate-500">Delay: </span>
              <strong className="text-slate-800 font-mono">{selectedEq.t_delay_seconds} s</strong>
            </div>
          </div>

          {/* Quick Metrics for selected asset */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
            <div className="bg-white p-3 rounded-lg border border-slate-200">
              <div className="text-[10px] text-slate-500 font-sans">Active Power (P)</div>
              <div className="text-lg font-bold text-slate-900 mt-0.5">
                {selectedLatest ? `${selectedLatest.active_power_kw.toFixed(2)} kW` : '—'}
              </div>
            </div>
            <div className="bg-white p-3 rounded-lg border border-slate-200">
              <div className="text-[10px] text-slate-500 font-sans">Apparent Power (S)</div>
              <div className="text-lg font-bold text-slate-900 mt-0.5">
                {selectedLatest ? `${selectedLatest.apparent_power_kva.toFixed(2)} kVA` : '—'}
              </div>
            </div>
            <div className="bg-white p-3 rounded-lg border border-slate-200">
              <div className="text-[10px] text-slate-500 font-sans">Displacement PF</div>
              <div className="text-lg font-bold text-slate-900 mt-0.5">
                {selectedLatest ? selectedLatest.power_factor.toFixed(3) : '—'}
              </div>
            </div>
            <div className="bg-white p-3 rounded-lg border border-slate-200">
              <div className="text-[10px] text-slate-500 font-sans">Cumulative Shift Energy</div>
              <div className="text-lg font-bold text-emerald-800 mt-0.5">
                {selectedLatest ? `${selectedLatest.cumulative_energy_kwh.toFixed(2)} kWh` : '—'}
              </div>
            </div>
          </div>

          {/* Timeseries Load Chart */}
          <TimeSeriesChart
            title={`Active Power & Current Profile — ${selectedEq.name}`}
            data={historyTelemetry}
            series={[
              { key: 'active_power_kw', label: 'Active Power', color: '#16a34a', unit: 'kW' },
              { key: 'current_a', label: 'Line Current', color: '#0f172a', unit: 'A' }
            ]}
            height={240}
            provenance="SIMULATED"
          />
        </div>
      )}
    </div>
  );
};
