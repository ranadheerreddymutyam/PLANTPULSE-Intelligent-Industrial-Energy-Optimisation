export type ProvenanceType = "SIMULATED" | "IMPORTED" | "DERIVED" | "ESTIMATED" | "CONFIGURED";

export type UserRole = "OPERATOR" | "ENERGY_MANAGER" | "MAINTENANCE" | "ADMIN";

export type EquipmentCriticality = "CRITICAL" | "NON_CRITICAL";

export type OperatingState = "RUNNING" | "IDLE" | "STOPPED" | "FAULT";

export type EventSeverity = "NORMAL" | "MONITOR" | "WARNING" | "ATTENTION";

export interface EngineeringValue {
  value: number | null;
  unit: string;
  formula: string;
  inputs: Record<string, any>;
  provenance: ProvenanceType;
  timestamp: string;
  model_version: string;
  label?: string;
  note?: string;
}

export interface SiteConfig {
  id: string;
  site_name: string;
  description?: string;
  nominal_voltage_v: number;
  nominal_frequency_hz: number;
  voltage_min_v: number;
  voltage_max_v: number;
  frequency_min_hz: number;
  frequency_max_hz: number;
  power_factor_min: number;
  tariff_per_kwh: number;
  currency: string;
  emission_factor_kg_co2_per_kwh: number;
  restart_allowance_kwh: number;
  alert_debounce_count: number;
  alert_hysteresis_seconds: number;
  config_version: string;
  provenance: ProvenanceType;
  updated_at?: string;
}

export interface Equipment {
  id: string;
  site_id: string;
  name: string;
  equipment_type: string;
  rated_power_kw: number;
  rated_current_a: number;
  p_idle_threshold_kw: number;
  t_delay_seconds: number;
  criticality: EquipmentCriticality;
  eligible_for_shutdown: boolean;
  vfd_capable: boolean;
  min_off_time_seconds: number;
  restart_delay_seconds: number;
  max_restarts_per_hour: number;
  provenance: ProvenanceType;
  config_version: string;
}

export interface Telemetry {
  id: number;
  equipment_id: string;
  scenario_id?: string;
  timestamp: string;
  timestamp_epoch_s: number;
  voltage_v: number;
  current_a: number;
  power_factor: number;
  frequency_hz: number;
  active_power_kw: number;
  apparent_power_kva: number;
  reactive_power_kvar: number;
  cumulative_energy_kwh: number;
  operating_state: OperatingState;
  interlock_estop: boolean;
  interlock_overload: boolean;
  interlock_process_permissive: boolean;
  interlock_manual_override: boolean;
  provenance: ProvenanceType;
}

export interface IdlePeriod {
  id: number;
  equipment_id: string;
  scenario_id?: string;
  start_time: string;
  end_time: string;
  duration_seconds: number;
  p_idle_threshold_kw: number;
  t_delay_seconds: number;
  total_idle_energy_kwh: number;
  avoidable_energy_kwh: number;
  eligible: boolean;
  provenance: ProvenanceType;
}

export interface DecisionTraceStep {
  step_number: number;
  step_name: string;
  status: "PASSED" | "FAILED" | "TERMINATED" | "SKIPPED";
  evaluation: string;
  values: Record<string, any>;
}

export interface Decision {
  id: number;
  equipment_id: string;
  scenario_id?: string;
  timestamp: string;
  evaluation_step: number;
  outcome: string;
  reason: string;
  decision_trace: DecisionTraceStep[];
  recommendation_text?: string;
  approval_required: boolean;
  approval_id?: number;
  provenance: ProvenanceType;
}

export interface Approval {
  id: number;
  equipment_id: string;
  scenario_id?: string;
  action_type: string;
  status: "PENDING" | "APPROVED" | "REJECTED";
  requested_at: string;
  reviewed_at?: string;
  reviewed_by?: string;
  user_role?: UserRole;
  comment?: string;
  estimated_kwh_saving: number;
  provenance: ProvenanceType;
}

export interface ControlCommand {
  id: number;
  equipment_id: string;
  command_type: string;
  target_interface: string;
  simulated_command_label: string;
  status: string;
  issued_by: string;
  issued_at: string;
  completed_at: string;
  details?: Record<string, any>;
  provenance: ProvenanceType;
}

export interface EventItem {
  id: number;
  event_uid: string;
  equipment_id: string;
  severity: EventSeverity;
  event_code: string;
  parameter: string;
  observed_value?: number;
  threshold_reference?: number;
  deviation?: number;
  unit: string;
  engineering_explanation: string;
  recommended_consideration: string;
  status: "ACTIVE" | "ACKNOWLEDGED" | "RESOLVED";
  occurrence_count: number;
  started_at: string;
  last_detected_at: string;
  resolved_at?: string;
  acknowledged_by?: string;
  provenance: ProvenanceType;
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
  seed: number;
  duration_hours: number;
  is_active: boolean;
  provenance: ProvenanceType;
}

export interface DashboardOverview {
  project_status: string;
  data_provenance: string;
  headline_sentence: string;
  site_id: string;
  site_name: string;
  total_active_kw: number;
  total_apparent_kva: number;
  total_site_kwh: number;
  total_current_a: number;
  avg_voltage_v: number;
  avg_power_factor: number;
  equipment_by_state: {
    RUNNING: number;
    IDLE: number;
    STOPPED: number;
  };
  idle_equipment_count: number;
  idle_equipment_names: string[];
  total_equipment_count: number;
  total_idle_energy_kwh: number;
  avoidable_idle_energy_kwh: number;
  idle_share_percent: number;
  savings: {
    energy_savings_kwh: EngineeringValue;
    cost_savings: EngineeringValue;
    emissions_reduction_kg_co2: EngineeringValue;
  };
  pending_approvals_count: number;
  active_events_count: number;
  sparkline: Array<{
    timestamp: string;
    total_kw: number;
    idle_kw: number;
  }>;
  provenance: ProvenanceType;
}

export interface LossRankItem {
  equipment_id: string;
  equipment_name: string;
  equipment_type: string;
  criticality: EquipmentCriticality;
  eligible_for_shutdown: boolean;
  p_idle_threshold_kw: number;
  t_delay_seconds: number;
  qualifying_periods_count: number;
  total_idle_duration_minutes: number;
  idle_energy_kwh: number;
  avoidable_idle_energy_kwh: number;
  share_of_avoidable_percent?: number;
  provenance: ProvenanceType;
}

export interface AuthUser {
  id: string;
  username: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}
