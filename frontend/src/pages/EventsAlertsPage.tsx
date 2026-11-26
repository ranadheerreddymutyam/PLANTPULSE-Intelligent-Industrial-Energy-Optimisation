import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { EventItem, UserRole } from '../types';
import { ProvenanceBadge } from '../components/common/ProvenanceBadge';
import { AlertTriangle, ShieldAlert, CheckCircle, Info, Filter, RefreshCw } from 'lucide-react';

interface EventsAlertsPageProps {
  currentRole: UserRole;
}

export const EventsAlertsPage: React.FC<EventsAlertsPageProps> = ({ currentRole }) => {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [actionNotice, setActionNotice] = useState<string>('');

  useEffect(() => {
    loadEvents();
  }, [statusFilter, severityFilter]);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const res = await api.listEvents({
        status: statusFilter || undefined,
        severity: severityFilter || undefined
      });
      setEvents(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (eventUid: string, action: 'ACKNOWLEDGE' | 'RESOLVE') => {
    try {
      await api.actOnEvent(eventUid, action, `User_${currentRole.toLowerCase()}`);
      setActionNotice(`Event ${eventUid} marked as ${action}D.`);
      loadEvents();
      setTimeout(() => setActionNotice(''), 3500);
    } catch (err: any) {
      alert(`Action failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-amber-50/60 border border-amber-200 rounded-xl p-5 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold uppercase tracking-wider text-amber-800 flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4 text-amber-700" />
            Grouped Alert Engine with Flood Prevention
          </span>
          <ProvenanceBadge type="DERIVED" size="xs" />
        </div>
        <h2 className="text-lg font-bold text-slate-900 tracking-tight">
          7. Event History & Parameter Deviations
        </h2>
        <p className="text-xs text-slate-700 leading-relaxed">
          Alerts require 3 consecutive qualifying samples to open and 5-minute hysteresis before resolving, preventing operator alert flooding.
          <strong className="text-slate-900 ml-1">Notice: All statements are non-binding engineering advisories for plant maintenance teams.</strong>
        </p>
      </div>

      {actionNotice && (
        <div className="bg-emerald-50 border border-emerald-300 text-emerald-800 p-3 rounded-lg text-xs font-semibold flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-emerald-600" />
          {actionNotice}
        </div>
      )}

      {/* Filters Toolbar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <span className="font-semibold text-slate-600 flex items-center gap-1">
            <Filter className="w-3.5 h-3.5" /> Filters:
          </span>

          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-700 bg-white"
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="ACKNOWLEDGED">Acknowledged</option>
            <option value="RESOLVED">Resolved</option>
          </select>

          <select
            value={severityFilter}
            onChange={e => setSeverityFilter(e.target.value)}
            className="border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-700 bg-white"
          >
            <option value="">All Severities</option>
            <option value="ATTENTION">Attention (Red)</option>
            <option value="WARNING">Warning (Amber)</option>
            <option value="MONITOR">Monitor (Blue)</option>
            <option value="NORMAL">Normal (Green)</option>
          </select>
        </div>

        <button
          onClick={loadEvents}
          className="px-3 py-1.5 text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg flex items-center gap-1.5 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Log
        </button>
      </div>

      {/* Grouped Events Table */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 className="font-bold text-slate-900 text-sm">Grouped Advisory Events Log</h3>
          <span className="text-xs font-mono text-slate-500">{events.length} records matching filter</span>
        </div>

        {events.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-xs">
            No events found matching selected criteria.
          </div>
        ) : (
          <div className="overflow-x-auto border border-slate-100 rounded-lg">
            <table className="min-w-full text-xs text-left">
              <thead className="bg-slate-50 text-slate-700 uppercase font-semibold border-b border-slate-200">
                <tr>
                  <th className="px-3 py-2.5">Severity</th>
                  <th className="px-3 py-2.5">Event UID & Asset</th>
                  <th className="px-3 py-2.5">Parameter</th>
                  <th className="px-3 py-2.5">Observed vs Threshold</th>
                  <th className="px-3 py-2.5">Engineering Explanation</th>
                  <th className="px-3 py-2.5">Recommended Consideration</th>
                  <th className="px-3 py-2.5">Status</th>
                  <th className="px-3 py-2.5">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-sans">
                {events.map(ev => {
                  let sevBadge = 'bg-slate-100 text-slate-700';
                  if (ev.severity === 'ATTENTION') sevBadge = 'bg-red-100 text-red-800 font-bold';
                  if (ev.severity === 'WARNING') sevBadge = 'bg-amber-100 text-amber-800 font-bold';
                  if (ev.severity === 'MONITOR') sevBadge = 'bg-blue-100 text-blue-800';

                  const isResolved = ev.status === 'RESOLVED';
                  const isAck = ev.status === 'ACKNOWLEDGED';

                  return (
                    <tr key={ev.event_uid} className="hover:bg-slate-50/80">
                      <td className="px-3 py-3">
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${sevBadge}`}>
                          {ev.severity}
                        </span>
                      </td>
                      <td className="px-3 py-3">
                        <div className="font-mono text-slate-900 font-bold">{ev.equipment_id}</div>
                        <div className="text-[10px] font-mono text-slate-400">{ev.event_uid}</div>
                      </td>
                      <td className="px-3 py-3 font-semibold text-slate-800">{ev.parameter}</td>
                      <td className="px-3 py-3 font-mono text-slate-700">
                        <div>Obs: {ev.observed_value} {ev.unit}</div>
                        <div className="text-slate-400 text-[10px]">Ref: {ev.threshold_reference} {ev.unit}</div>
                      </td>
                      <td className="px-3 py-3 text-slate-600 max-w-xs">{ev.engineering_explanation}</td>
                      <td className="px-3 py-3 text-emerald-800 font-medium max-w-xs bg-emerald-50/40 p-2 rounded">
                        {ev.recommended_consideration}
                      </td>
                      <td className="px-3 py-3 font-mono">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          isResolved ? 'bg-slate-100 text-slate-500' : isAck ? 'bg-blue-50 text-blue-700' : 'bg-red-50 text-red-700'
                        }`}>
                          {ev.status}
                        </span>
                        <div className="text-[10px] text-slate-400 mt-0.5">{ev.occurrence_count}x detected</div>
                      </td>
                      <td className="px-3 py-3">
                        {!isResolved && (
                          <div className="flex items-center gap-1.5">
                            {!isAck && (
                              <button
                                onClick={() => handleAction(ev.event_uid, 'ACKNOWLEDGE')}
                                className="px-2 py-1 text-[10px] font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 rounded border border-blue-200"
                              >
                                Ack
                              </button>
                            )}
                            <button
                              onClick={() => handleAction(ev.event_uid, 'RESOLVE')}
                              className="px-2 py-1 text-[10px] font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 rounded border border-emerald-200"
                            >
                              Resolve
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
