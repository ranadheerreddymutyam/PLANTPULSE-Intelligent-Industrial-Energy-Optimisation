/**
 * Centralized Typed API Client for PlantPulse.
 * Note: Never duplicate or reimplement an engineering formula in the client.
 * The client only sends requests and renders data returned by the backend.
 */
import {
  DashboardOverview, Equipment, Telemetry, IdlePeriod, Decision,
  Approval, ControlCommand, EventItem, Scenario, SiteConfig, LossRankItem,
  AuthUser, AuthTokenResponse
} from '../types';

const API_BASE = '/api/v1';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {})
    },
    ...options
  });
  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errObj = await res.json();
      errorDetail = errObj.detail || errObj.message || errorDetail;
    } catch {
      // fallback
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  // Analytics / Dashboard
  getDashboardOverview: () => fetchJson<DashboardOverview>('/analytics/dashboard-overview'),

  // Equipment
  listEquipment: () => fetchJson<Equipment[]>('/equipment/'),
  getEquipment: (id: string) => fetchJson<Equipment>(`/equipment/${id}`),
  updateEquipment: (id: string, payload: Partial<Equipment>) =>
    fetchJson<Equipment>(`/equipment/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    }),

  // Telemetry
  getLatestTelemetry: () => fetchJson<Telemetry[]>('/telemetry/latest'),
  getTelemetryHistory: (equipmentId?: string, limit: number = 120) =>
    fetchJson<Telemetry[]>(`/telemetry/history?${equipmentId ? `equipment_id=${equipmentId}&` : ''}limit=${limit}`),

  // Idle Analysis
  getIdlePeriods: (equipmentId?: string) =>
    fetchJson<IdlePeriod[]>(`/idle/periods${equipmentId ? `?equipment_id=${equipmentId}` : ''}`),
  getLossRanking: () => fetchJson<{
    title: string;
    total_avoidable_idle_energy_kwh: number;
    ranking: LossRankItem[];
    provenance: string;
    note: string;
  }>('/idle/ranking'),
  getIdleSummary: () => fetchJson<any>('/idle/summary'),

  // Decisions & Optimisation
  getLatestDecisions: () => fetchJson<Decision[]>('/decisions/latest'),
  getTradeoffs: () => fetchJson<{
    title: string;
    subtitle: string;
    tradeoffs: Array<{
      category: string;
      risk: string;
      detail: string;
      mitigation: string;
      status_check: string;
    }>;
    provenance: string;
  }>('/decisions/tradeoffs'),

  // Control & Safety (Simulated)
  listApprovals: (status?: string) =>
    fetchJson<Approval[]>(`/control/approvals${status ? `?status_filter=${status}` : ''}`),
  reviewApproval: (approvalId: number, action: 'APPROVE' | 'REJECT', userId: string, userRole: string, comment?: string) =>
    fetchJson<Approval>(`/control/approvals/${approvalId}/action`, {
      method: 'POST',
      body: JSON.stringify({ action, user_id: userId, user_role: userRole, comment })
    }),
  issueSimulatedCommand: (equipmentId: string, commandType: string, userId: string, userRole: string, reason?: string) =>
    fetchJson<ControlCommand>('/control/simulated-command', {
      method: 'POST',
      body: JSON.stringify({ equipment_id: equipmentId, command_type: commandType, user_id: userId, user_role: userRole, reason })
    }),
  listCommands: () => fetchJson<ControlCommand[]>('/control/commands'),
  getInterlocks: () => fetchJson<{
    interlocks: Array<{
      equipment_id: string;
      equipment_name: string;
      criticality: string;
      eligible_for_shutdown: boolean;
      estop_active: boolean;
      overload_active: boolean;
      process_permissive: boolean;
      manual_override_active: boolean;
      can_shutdown: boolean;
    }>;
    notice: string;
    provenance: string;
  }>('/control/interlocks'),

  // Savings & Baseline
  getBaselineComparison: () => fetchJson<any>('/savings/baseline-comparison'),

  // Events & Alerts
  listEvents: (params?: { status?: string; severity?: string; parameter?: string; equipment_id?: string }) => {
    const q = new URLSearchParams();
    if (params?.status) q.append('status_filter', params.status);
    if (params?.severity) q.append('severity_filter', params.severity);
    if (params?.parameter) q.append('parameter_filter', params.parameter);
    if (params?.equipment_id) q.append('equipment_id', params.equipment_id);
    return fetchJson<EventItem[]>(`/events/?${q.toString()}`);
  },
  actOnEvent: (eventUid: string, action: 'ACKNOWLEDGE' | 'RESOLVE', userId: string) =>
    fetchJson<EventItem>(`/events/${eventUid}/action`, {
      method: 'POST',
      body: JSON.stringify({ action, user_id: userId })
    }),

  // Reports
  getLiveAssessment: () => fetchJson<any>('/reports/assessment'),
  saveReport: (title?: string) => fetchJson<any>(`/reports/save${title ? `?title=${encodeURIComponent(title)}` : ''}`, { method: 'POST' }),
  listReportsHistory: () => fetchJson<any[]>('/reports/history'),

  // Scenarios
  listScenarios: () => fetchJson<Scenario[]>('/scenarios/'),
  switchScenario: (scenarioId: string) =>
    fetchJson<any>('/scenarios/switch', {
      method: 'POST',
      body: JSON.stringify({ scenario_id: scenarioId })
    }),

  // Site Configuration & Settings
  getConfig: () => fetchJson<SiteConfig>('/config/'),
  updateConfig: (payload: Partial<SiteConfig>) =>
    fetchJson<SiteConfig>('/config/', {
      method: 'PUT',
      body: JSON.stringify(payload)
    }),

  // Auth / Users
  login: (username: string, password: string) =>
    fetchJson<AuthTokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    }),
  listUsers: () => fetchJson<AuthUser[]>('/auth/users'),

  // Import
  uploadFile: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/import/upload`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  previewFile: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/import/preview`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  listImportRuns: () => fetchJson<any[]>('/import/runs')
};
