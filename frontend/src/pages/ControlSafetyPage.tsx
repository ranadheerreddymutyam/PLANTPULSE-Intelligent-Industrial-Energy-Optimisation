import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Approval, ControlCommand, UserRole } from '../types';
import { ProvenanceBadge } from '../components/common/ProvenanceBadge';
import { ShieldCheck, ShieldAlert, CheckCircle, XCircle, Terminal, AlertTriangle, RefreshCw } from 'lucide-react';

interface ControlSafetyPageProps {
  currentRole: UserRole;
}

export const ControlSafetyPage: React.FC<ControlSafetyPageProps> = ({ currentRole }) => {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [commands, setCommands] = useState<ControlCommand[]>([]);
  const [interlocks, setInterlocks] = useState<any[]>([]);
  const [actionComment, setActionComment] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [actionSuccess, setActionSuccess] = useState<string>('');

  useEffect(() => {
    loadControlData();
  }, []);

  const loadControlData = async () => {
    try {
      setLoading(true);
      const [appRes, cmdRes, intRes] = await Promise.all([
        api.listApprovals(),
        api.listCommands(),
        api.getInterlocks()
      ]);
      setApprovals(appRes);
      setCommands(cmdRes);
      setInterlocks(intRes.interlocks || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprovalAction = async (approvalId: number, action: 'APPROVE' | 'REJECT') => {
    if (currentRole !== 'OPERATOR' && currentRole !== 'ADMIN') {
      alert(`Role '${currentRole}' is not authorized to sign off controlled shutdowns. Switch role to OPERATOR in the top banner.`);
      return;
    }

    try {
      await api.reviewApproval(
        approvalId,
        action,
        `User_${currentRole.toLowerCase()}`,
        currentRole,
        actionComment || `Operator ${action.toLowerCase()} sign-off`
      );
      setActionSuccess(`Recommendation #${approvalId} ${action}D successfully.`);
      setActionComment('');
      loadControlData();
      setTimeout(() => setActionSuccess(''), 4000);
    } catch (err: any) {
      alert(`Action failed: ${err.message}`);
    }
  };

  const handleDirectSimulatedRestart = async (equipmentId: string) => {
    try {
      await api.issueSimulatedCommand(
        equipmentId,
        'SIMULATED_RESTART',
        `User_${currentRole.toLowerCase()}`,
        currentRole,
        'Direct operator test restart'
      );
      setActionSuccess(`SIMULATED RESTART command sent to ${equipmentId}`);
      loadControlData();
      setTimeout(() => setActionSuccess(''), 4000);
    } catch (err: any) {
      alert(`Command failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Strict Simulated Command Notice Banner */}
      <div className="bg-amber-50 border border-amber-300 rounded-xl p-4 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
        <div className="space-y-1 text-xs text-amber-900">
          <div className="font-bold flex items-center gap-2">
            <span>SIMULATED CONTROL BOUNDARY — NO REAL EQUIPMENT CONTROLLED</span>
            <ProvenanceBadge type="SIMULATED" size="xs" />
          </div>
          <p className="leading-relaxed">
            All commands dispatch strictly through a software-emulated contactor/VFD adapter. No physical GPIO, serial, Modbus, or MQTT signals are ever transmitted.
            Critical process loads are permanently locked and cannot be actuated under any circumstance.
          </p>
        </div>
      </div>

      {actionSuccess && (
        <div className="bg-emerald-50 border border-emerald-300 text-emerald-800 p-3 rounded-lg text-xs font-semibold flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-emerald-600" />
          {actionSuccess}
        </div>
      )}

      {/* Operator Approvals Queue */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
          <div>
            <h3 className="font-bold text-slate-900 text-sm">Operator Controlled-Shutdown Approvals Queue</h3>
            <p className="text-xs text-slate-500">
              Authorized sign-off required before simulated de-energisation of sustained idle equipment
            </p>
          </div>
          <span className="text-xs font-mono font-bold bg-amber-100 text-amber-900 px-2 py-0.5 rounded">
            {approvals.filter(a => a.status === 'PENDING').length} Pending Approval
          </span>
        </div>

        {approvals.length === 0 ? (
          <div className="text-center py-6 text-slate-400 text-xs">
            No approval requests in queue. Equipment operating normally or not in sustained idle.
          </div>
        ) : (
          <div className="space-y-3">
            {approvals.map(app => {
              const isPending = app.status === 'PENDING';
              return (
                <div
                  key={app.id}
                  className={`border rounded-lg p-4 flex flex-wrap items-center justify-between gap-4 transition ${
                    isPending ? 'border-amber-200 bg-amber-50/30' : 'border-slate-200 bg-slate-50/50'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-900 text-xs">{app.equipment_id}</span>
                      <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                        isPending ? 'bg-amber-100 text-amber-800' : app.status === 'APPROVED' ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {app.status}
                      </span>
                      <ProvenanceBadge type={app.provenance} size="xs" />
                    </div>
                    <div className="text-xs text-slate-600">
                      Estimated Saving Opportunity: <strong className="text-slate-900 font-mono">{app.estimated_kwh_saving.toFixed(2)} kWh</strong>
                    </div>
                    {app.reviewed_by && (
                      <div className="text-[11px] text-slate-500">
                        Reviewed by: <strong className="text-slate-700">{app.reviewed_by}</strong> ({app.user_role}) on {app.reviewed_at?.replace('T', ' ').substring(0, 19)}
                        {app.comment && <span> · Note: "{app.comment}"</span>}
                      </div>
                    )}
                  </div>

                  {isPending && (
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => handleApprovalAction(app.id, 'APPROVE')}
                        className="px-3 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white font-semibold text-xs rounded-lg shadow-xs flex items-center gap-1.5 transition"
                      >
                        <CheckCircle className="w-3.5 h-3.5" /> Approve Shutdown
                      </button>
                      <button
                        onClick={() => handleApprovalAction(app.id, 'REJECT')}
                        className="px-3 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 font-semibold text-xs rounded-lg shadow-xs flex items-center gap-1.5 transition"
                      >
                        <XCircle className="w-3.5 h-3.5" /> Reject
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Safety Interlocks Real-Time Status Panel */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
        <div className="border-b border-slate-100 pb-3">
          <h3 className="font-bold text-slate-900 text-sm">Simulated Safety Interlocks Status Panel</h3>
          <p className="text-xs text-slate-500">
            Monitoring E-Stop, thermal overload, upstream process permissive, and local maintenance override
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {interlocks.map(item => {
            const isCrit = item.criticality === 'CRITICAL';
            return (
              <div key={item.equipment_id} className="border border-slate-200 rounded-lg p-3 bg-slate-50 text-xs space-y-2">
                <div className="flex items-center justify-between font-bold text-slate-800">
                  <span className="truncate pr-1">{item.equipment_name}</span>
                  <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${isCrit ? 'bg-red-100 text-red-800' : 'bg-slate-200 text-slate-700'}`}>
                    {item.criticality}
                  </span>
                </div>

                <div className="space-y-1 font-mono text-[11px] text-slate-600">
                  <div className="flex justify-between">
                    <span>E-Stop:</span>
                    <strong className={item.estop_active ? 'text-red-600 font-bold' : 'text-emerald-700'}>
                      {item.estop_active ? 'TRIPPED' : 'CLEAR'}
                    </strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Overload:</span>
                    <strong className={item.overload_active ? 'text-red-600 font-bold' : 'text-emerald-700'}>
                      {item.overload_active ? 'TRIPPED' : 'NORMAL'}
                    </strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Permissive:</span>
                    <strong className={item.process_permissive ? 'text-emerald-700' : 'text-amber-600 font-bold'}>
                      {item.process_permissive ? 'GRANTED' : 'INHIBITED'}
                    </strong>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-200 flex justify-between items-center">
                  <span className="text-[10px] text-slate-500">Shutdown Status:</span>
                  <span className={`text-[10px] font-bold font-mono px-1.5 py-0.5 rounded ${
                    isCrit ? 'text-red-700 bg-red-50' : item.can_shutdown ? 'text-emerald-700 bg-emerald-50' : 'text-slate-500 bg-slate-200'
                  }`}>
                    {isCrit ? 'LOCKED EXCLUDED' : item.can_shutdown ? 'ALLOWED' : 'BLOCKED'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Simulated Contactor/VFD Command Log */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-slate-700" />
            <h3 className="font-bold text-slate-900 text-sm">Simulated Contactor / VFD Command Audit Log</h3>
          </div>
          <span className="text-xs font-mono text-slate-500">{commands.length} commands logged</span>
        </div>

        {commands.length === 0 ? (
          <div className="text-center py-6 text-slate-400 text-xs">
            No simulated commands executed yet.
          </div>
        ) : (
          <div className="overflow-x-auto border border-slate-100 rounded-lg max-h-64">
            <table className="min-w-full text-xs text-left">
              <thead className="bg-slate-50 text-slate-700 uppercase font-semibold border-b border-slate-200 sticky top-0">
                <tr>
                  <th className="px-3 py-2">Timestamp</th>
                  <th className="px-3 py-2">Equipment ID</th>
                  <th className="px-3 py-2">Command Type</th>
                  <th className="px-3 py-2">Interface</th>
                  <th className="px-3 py-2">Executed By</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Simulated Label</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                {commands.map(cmd => (
                  <tr key={cmd.id} className="hover:bg-slate-50">
                    <td className="px-3 py-1.5 text-slate-500">{cmd.issued_at.replace('T', ' ').substring(0, 19)}</td>
                    <td className="px-3 py-1.5 font-bold text-slate-900">{cmd.equipment_id}</td>
                    <td className="px-3 py-1.5 font-semibold text-emerald-800">{cmd.command_type}</td>
                    <td className="px-3 py-1.5 text-slate-600">{cmd.target_interface}</td>
                    <td className="px-3 py-1.5 text-slate-700">{cmd.issued_by}</td>
                    <td className="px-3 py-1.5">
                      <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded">
                        {cmd.status}
                      </span>
                    </td>
                    <td className="px-3 py-1.5">
                      <span className="text-[10px] font-bold text-amber-800 bg-amber-50 border border-amber-200 px-1.5 py-0.5 rounded">
                        {cmd.simulated_command_label}
                      </span>
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
