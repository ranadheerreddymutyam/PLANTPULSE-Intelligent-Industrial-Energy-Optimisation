import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { SiteConfig, Equipment } from '../types';
import { ProvenanceBadge } from '../components/common/ProvenanceBadge';
import { Settings, Save, Lock, Cpu, Sliders, Shield, Info, CheckCircle2 } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [config, setConfig] = useState<SiteConfig | null>(null);
  const [equipmentList, setEquipmentList] = useState<Equipment[]>([]);
  const [saveSuccess, setSaveSuccess] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const [cfg, eqs] = await Promise.all([
        api.getConfig(),
        api.listEquipment()
      ]);
      setConfig(cfg);
      setEquipmentList(eqs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleConfigChange = (field: keyof SiteConfig, val: any) => {
    if (!config) return;
    setConfig({ ...config, [field]: val });
  };

  const handleSaveConfig = async () => {
    if (!config) return;
    try {
      await api.updateConfig({
        tariff_per_kwh: Number(config.tariff_per_kwh),
        emission_factor_kg_co2_per_kwh: Number(config.emission_factor_kg_co2_per_kwh),
        restart_allowance_kwh: Number(config.restart_allowance_kwh),
        nominal_voltage_v: Number(config.nominal_voltage_v),
        voltage_min_v: Number(config.voltage_min_v),
        voltage_max_v: Number(config.voltage_max_v),
        alert_debounce_count: Number(config.alert_debounce_count),
        alert_hysteresis_seconds: Number(config.alert_hysteresis_seconds)
      });
      setSaveSuccess('Engineering reference settings updated successfully.');
      setTimeout(() => setSaveSuccess(''), 3500);
    } catch (err: any) {
      alert(`Save failed: ${err.message}`);
    }
  };

  if (loading && !config) {
    return <div className="p-8 text-center text-slate-500 text-sm">Loading engineering settings...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-emerald-50/60 border border-emerald-200 rounded-xl p-5 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-1.5">
            <Settings className="w-4 h-4 text-emerald-700" />
            Engineering References & L7 Governance
          </span>
          <ProvenanceBadge type="CONFIGURED" size="xs" />
        </div>
        <h2 className="text-lg font-bold text-slate-900 tracking-tight">
          10. Site Settings, Thresholds & Proposed Architecture
        </h2>
        <p className="text-xs text-slate-600 leading-relaxed">
          All baseline values are configured engineering reference limits editable by authorized plant engineers.
          Critical loads are permanently locked against automated shutdown.
        </p>
      </div>

      {saveSuccess && (
        <div className="bg-emerald-50 border border-emerald-300 text-emerald-800 p-3 rounded-lg text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          {saveSuccess}
        </div>
      )}

      {/* Site Electrical & Economic Configuration */}
      {config && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="font-bold text-slate-900 text-sm">Feeder Parameters & Economic Reference Rates</h3>
            <button
              onClick={handleSaveConfig}
              className="px-3.5 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white font-semibold text-xs rounded-lg shadow-xs flex items-center gap-1.5 transition"
            >
              <Save className="w-3.5 h-3.5" /> Save Configuration
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
            <div>
              <label className="block text-slate-600 font-medium mb-1">Electricity Tariff Rate (USD/kWh)</label>
              <input
                type="number"
                step="0.01"
                value={config.tariff_per_kwh}
                onChange={e => handleConfigChange('tariff_per_kwh', e.target.value)}
                className="w-full border border-slate-200 rounded-lg p-2 font-mono"
              />
            </div>
            <div>
              <label className="block text-slate-600 font-medium mb-1">Grid Emission Factor (kg CO2e/kWh)</label>
              <input
                type="number"
                step="0.01"
                value={config.emission_factor_kg_co2_per_kwh}
                onChange={e => handleConfigChange('emission_factor_kg_co2_per_kwh', e.target.value)}
                className="w-full border border-slate-200 rounded-lg p-2 font-mono"
              />
            </div>
            <div>
              <label className="block text-slate-600 font-medium mb-1">Restart Allowance Deduction (kWh)</label>
              <input
                type="number"
                step="0.1"
                value={config.restart_allowance_kwh}
                onChange={e => handleConfigChange('restart_allowance_kwh', e.target.value)}
                className="w-full border border-slate-200 rounded-lg p-2 font-mono"
              />
            </div>
            <div>
              <label className="block text-slate-600 font-medium mb-1">Nominal Line-to-Line Voltage (V RMS)</label>
              <input
                type="number"
                value={config.nominal_voltage_v}
                onChange={e => handleConfigChange('nominal_voltage_v', e.target.value)}
                className="w-full border border-slate-200 rounded-lg p-2 font-mono"
              />
            </div>
            <div>
              <label className="block text-slate-600 font-medium mb-1">Voltage Min Acceptable (V RMS)</label>
              <input
                type="number"
                value={config.voltage_min_v}
                onChange={e => handleConfigChange('voltage_min_v', e.target.value)}
                className="w-full border border-slate-200 rounded-lg p-2 font-mono"
              />
            </div>
            <div>
              <label className="block text-slate-600 font-medium mb-1">Voltage Max Acceptable (V RMS)</label>
              <input
                type="number"
                value={config.voltage_max_v}
                onChange={e => handleConfigChange('voltage_max_v', e.target.value)}
                className="w-full border border-slate-200 rounded-lg p-2 font-mono"
              />
            </div>
            <div>
              <label className="block text-slate-600 font-medium mb-1">Alert Debounce Count (samples)</label>
              <input
                type="number"
                value={config.alert_debounce_count}
                onChange={e => handleConfigChange('alert_debounce_count', e.target.value)}
                className="w-full border border-slate-200 rounded-lg p-2 font-mono"
              />
            </div>
            <div>
              <label className="block text-slate-600 font-medium mb-1">Alert Hysteresis Window (seconds)</label>
              <input
                type="number"
                value={config.alert_hysteresis_seconds}
                onChange={e => handleConfigChange('alert_hysteresis_seconds', e.target.value)}
                className="w-full border border-slate-200 rounded-lg p-2 font-mono"
              />
            </div>
          </div>
        </div>
      )}

      {/* Critical Load Exclusion Enforcement List */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="font-bold text-slate-900 text-sm">Critical Load Lock & Exclusion Enforcement</h3>
            <p className="text-xs text-slate-500">Critical process and life-safety loads are locked at database & logic levels</p>
          </div>
          <span className="text-[10px] font-bold uppercase bg-red-100 text-red-800 px-2 py-0.5 rounded flex items-center gap-1">
            <Lock className="w-3 h-3" /> Hard Boundary
          </span>
        </div>

        <div className="overflow-x-auto border border-slate-100 rounded-lg">
          <table className="min-w-full text-xs text-left">
            <thead className="bg-slate-50 text-slate-700 uppercase font-semibold border-b border-slate-200">
              <tr>
                <th className="px-3 py-2">Asset Name</th>
                <th className="px-3 py-2">Type</th>
                <th className="px-3 py-2">Criticality Classification</th>
                <th className="px-3 py-2">Controlled Shutdown Eligibility</th>
                <th className="px-3 py-2">Safe-Restart Limit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {equipmentList.map(eq => {
                const isCrit = eq.criticality === 'CRITICAL';
                return (
                  <tr key={eq.id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 font-bold text-slate-900">{eq.name}</td>
                    <td className="px-3 py-2 text-slate-600 capitalize">{eq.equipment_type}</td>
                    <td className="px-3 py-2">
                      <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                        isCrit ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-slate-100 text-slate-600'
                      }`}>
                        {eq.criticality}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      {isCrit ? (
                        <span className="text-red-700 font-semibold flex items-center gap-1">
                          <Lock className="w-3 h-3" /> Permanently Locked (Ineligible)
                        </span>
                      ) : (
                        <span className="text-emerald-700 font-medium">Eligible (Operator Controlled)</span>
                      )}
                    </td>
                    <td className="px-3 py-2 font-mono text-slate-600">
                      Max {eq.max_restarts_per_hour} restarts/hr · {eq.min_off_time_seconds}s min off
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Proposed Hardware Architecture Section (Purely Informational / Pending) */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
          <div>
            <span className="text-[10px] font-bold font-mono uppercase tracking-wider text-amber-800 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded">
              PROPOSED HARDWARE ARCHITECTURE — IMPLEMENTATION PENDING
            </span>
            <h3 className="font-bold text-slate-900 text-sm mt-1">
              Industrial Retrofit Metering & Interlock Topology
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">Conceptual Physical Block Diagram</span>
        </div>

        <p className="text-xs text-slate-600 leading-relaxed">
          The proposed physical hardware layer complements existing motor control centers (MCC), direct-on-line (DOL) contactors, and variable frequency drives (VFDs).
          No physical hardware is connected in this prototype software release.
        </p>

        {/* Visual Architecture Diagram */}
        <div className="p-4 bg-slate-900 text-slate-200 rounded-xl font-mono text-xs overflow-x-auto space-y-4 border border-slate-800">
          <div className="text-emerald-400 font-bold border-b border-slate-800 pb-1">
            FEEDER BUS: 3-Phase 415 V (Line-to-Line), 50 Hz, Balanced AC Supply
          </div>
          <pre className="text-[11px] leading-relaxed text-slate-300">
{`+-----------------------------------------------------------------------------------+
|  FEEDER PANEL (415 V LL, 50 Hz)                                                  |
|     |                                                                             |
|     +--> [Potential Transformers (PT/VT) 415V/110V]                              |
|     +--> [Current Transformers (CT) 100:5A Class 0.5S]                            |
|             |                                                                     |
|             v                                                                     |
|     +-----------------------------------------+                                   |
|     | DEDICATED METERING IC (ADE9000 / ATM90E) |                                  |
|     | - 24-bit Sigma-Delta ADCs               |                                   |
|     | - True RMS V, I, Active P, Reactive Q   |                                   |
|     +-----------------------------------------+                                   |
|             | Isolated SPI / Modbus-RTU                                           |
|             v                                                                     |
|     +-----------------------------------------+                                   |
|     | INDUSTRIAL CONTROLLER / EDGE GATEWAY    |                                   |
|     | - Hardware Watchdog & Safety Loop       |                                   |
|     | - Telemetry Sampling (1 s - 60 s)       |                                   |
|     +-----------------------------------------+                                   |
|             |                                 |                                   |
|             v (Simulated Telemetry Pipeline)  v (Simulated Relay / VFD Adapter)   |
|     +-----------------------+         +-------------------------------+           |
|     | PLANTPULSE PLATFORM   |         | INTERLOCK CHECK & TRIP COIL   |           |
|     | - 8-Step State Engine |         | - E-Stop Circuit              |           |
|     | - Operator Approval   | ------> | - Motor Overload Relay (95/96)|           |
|     | - Avoidable kWh Audit |         | - Process Permissive Relay    |           |
|     +-----------------------+         +-------------------------------+           |
+-----------------------------------------------------------------------------------+`}
          </pre>
          <div className="text-[10px] text-slate-400 italic">
            * Hardware implementation remains pending. Software prototype simulates this exact physical behavior deterministically.
          </div>
        </div>
      </div>
    </div>
  );
};
