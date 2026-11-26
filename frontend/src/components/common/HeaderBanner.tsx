import React, { useEffect, useState } from 'react';
import { Sliders, Shield, RefreshCw, CheckCircle2, LogOut, User } from 'lucide-react';
import { api } from '../../api/client';
import { Scenario, UserRole, AuthUser } from '../../types';

interface HeaderBannerProps {
  currentRole: UserRole;
  onRoleChange: (role: UserRole) => void;
  onScenarioSwitched: () => void;
  authenticatedUser?: AuthUser | null;
  onLogout?: () => void;
}

export const HeaderBanner: React.FC<HeaderBannerProps> = ({
  currentRole,
  onRoleChange,
  onScenarioSwitched,
  authenticatedUser,
  onLogout
}) => {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [activeScenarioId, setActiveScenarioId] = useState<string>('scenario_heavy_idle');
  const [isSwitching, setIsSwitching] = useState<boolean>(false);
  const [switchMessage, setSwitchMessage] = useState<string>('');

  useEffect(() => {
    loadScenarios();
  }, []);

  const loadScenarios = async () => {
    try {
      const list = await api.listScenarios();
      setScenarios(list);
      const active = list.find(s => s.is_active);
      if (active) setActiveScenarioId(active.id);
    } catch (e) {
      console.error('Failed to load scenarios', e);
    }
  };

  const handleScenarioChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newId = e.target.value;
    setIsSwitching(true);
    setSwitchMessage('Regenerating deterministic telemetry & recalculating...');
    try {
      await api.switchScenario(newId);
      setActiveScenarioId(newId);
      setSwitchMessage('Scenario active. Calculations updated.');
      onScenarioSwitched();
      setTimeout(() => setSwitchMessage(''), 3500);
    } catch (err: any) {
      alert(`Scenario switch failed: ${err.message}`);
      setSwitchMessage('');
    } finally {
      setIsSwitching(false);
    }
  };

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
      {/* Main Navbar controls */}
      <div className="px-4 sm:px-6 py-2.5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-700 flex items-center justify-center text-white shadow-xs font-bold text-sm tracking-wider">
            PP
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-slate-900 tracking-tight">PLANTPULSE</h1>
              <span className="text-[10px] bg-emerald-100 text-emerald-800 font-mono font-semibold px-1.5 py-0.5 rounded">
                v1.0-PROTOTYPE
              </span>
            </div>
            <p className="text-[11px] text-slate-500 hidden sm:block">
              Intelligent Industrial Energy Optimisation for Sustainable Manufacturing
            </p>
          </div>
        </div>

        {/* Global Controls: Scenario Switcher & Role Selector */}
        <div className="flex items-center gap-3">
          {switchMessage && (
            <span className="flex items-center gap-1 text-xs text-emerald-700 font-medium bg-emerald-50 px-2 py-1 rounded border border-emerald-200 animate-pulse">
              <CheckCircle2 className="w-3.5 h-3.5" />
              {switchMessage}
            </span>
          )}

          {/* Scenario Selector */}
          <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1">
            <Sliders className="w-3.5 h-3.5 text-slate-500" />
            <label htmlFor="scenario-select" className="text-xs font-medium text-slate-600 hidden md:inline">
              Scenario:
            </label>
            <select
              id="scenario-select"
              value={activeScenarioId}
              onChange={handleScenarioChange}
              disabled={isSwitching}
              className="text-xs font-semibold text-slate-800 bg-transparent border-none focus:outline-none cursor-pointer pr-1"
            >
              {scenarios.map(sc => (
                <option key={sc.id} value={sc.id}>
                  {sc.name}
                </option>
              ))}
            </select>
            {isSwitching && <RefreshCw className="w-3.5 h-3.5 text-emerald-600 animate-spin" />}
          </div>

          {/* Role Switcher (L7 Governance) */}
          <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1">
            <Shield className="w-3.5 h-3.5 text-slate-500" />
            <label htmlFor="role-select" className="text-xs font-medium text-slate-600 hidden md:inline">
              Role:
            </label>
            <select
              id="role-select"
              value={currentRole}
              onChange={e => onRoleChange(e.target.value as UserRole)}
              className="text-xs font-semibold text-emerald-800 bg-transparent border-none focus:outline-none cursor-pointer"
            >
              <option value="OPERATOR">Operator (Approvals)</option>
              <option value="ENERGY_MANAGER">Energy Manager (Reports)</option>
              <option value="MAINTENANCE">Maintenance (Interlocks)</option>
              <option value="ADMIN">Admin (Settings)</option>
            </select>
          </div>

          {authenticatedUser && onLogout && (
            <div className="flex items-center gap-2">
              <span
                title={authenticatedUser.full_name}
                className="hidden sm:flex items-center gap-1.5 text-xs font-medium text-slate-700 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1"
              >
                <User className="w-3.5 h-3.5 text-emerald-700" aria-hidden="true" />
                <span>{authenticatedUser.username}</span>
              </span>
              <button
                type="button"
                onClick={onLogout}
                className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 hover:text-red-700 bg-slate-50 hover:bg-red-50 border border-slate-200 hover:border-red-200 rounded-lg px-2.5 py-1 transition-colors cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" aria-hidden="true" />
                <span>Logout</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
