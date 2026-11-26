import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { ProvenanceBadge } from '../components/common/ProvenanceBadge';
import { FileText, Download, Printer, CheckCircle2, Clock, Shield, AlertCircle, RefreshCw } from 'lucide-react';

export const ReportsPage: React.FC = () => {
  const [assessment, setAssessment] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [savedSuccess, setSavedSuccess] = useState<string>('');

  useEffect(() => {
    loadLiveAssessment();
  }, []);

  const loadLiveAssessment = async () => {
    try {
      setLoading(true);
      const res = await api.getLiveAssessment();
      setAssessment(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSnapshot = async () => {
    try {
      await api.saveReport();
      setSavedSuccess('Report snapshot persisted to database.');
      setTimeout(() => setSavedSuccess(''), 4000);
    } catch (err: any) {
      alert(`Save failed: ${err.message}`);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleExportJson = () => {
    if (!assessment) return;
    const blob = new Blob([JSON.stringify(assessment, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${assessment.report_id}_energy_assessment.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading && !assessment) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500 text-sm">
        <RefreshCw className="w-5 h-5 animate-spin mr-2 text-emerald-600" />
        Generating live engineering assessment from database...
      </div>
    );
  }

  if (!assessment) {
    return <div className="text-sm text-red-600">Failed to load report data.</div>;
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Top Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-4 rounded-xl border border-slate-200 shadow-xs print:hidden">
        <div>
          <h2 className="text-base font-bold text-slate-900">Official Prototype Engineering Assessment</h2>
          <p className="text-xs text-slate-500 font-mono">
            Report ID: {assessment.report_id} · Generated: {assessment.generated_at.replace('T', ' ').substring(0, 19)} UTC
          </p>
        </div>

        <div className="flex items-center gap-2">
          {savedSuccess && (
            <span className="text-xs text-emerald-700 font-medium bg-emerald-50 px-2.5 py-1 rounded border border-emerald-200">
              {savedSuccess}
            </span>
          )}
          <button
            onClick={handleSaveSnapshot}
            className="px-3 py-1.5 text-xs font-semibold bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg shadow-xs transition"
          >
            Save Snapshot
          </button>
          <button
            onClick={handleExportJson}
            className="px-3 py-1.5 text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg border border-slate-200 flex items-center gap-1.5 transition"
          >
            <Download className="w-3.5 h-3.5" /> Export JSON
          </button>
          <button
            onClick={handlePrint}
            className="px-3 py-1.5 text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg border border-slate-200 flex items-center gap-1.5 transition"
          >
            <Printer className="w-3.5 h-3.5" /> Print / PDF
          </button>
        </div>
      </div>

      {/* Main Printable Document Sheet (Always White Background) */}
      <div className="bg-white border border-slate-300 rounded-2xl p-8 sm:p-10 shadow-sm space-y-8 text-slate-800 font-sans print:border-none print:p-0">
        {/* Assessment Header */}
        <div className="border-b-2 border-slate-900 pb-6 space-y-2">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-xs font-mono font-bold tracking-widest text-emerald-800 uppercase">
              PLANTPULSE ENGINEERING DECISION SUPPORT
            </span>
            <span className="bg-amber-100 border border-amber-300 text-amber-900 text-[10px] font-mono font-bold px-2 py-0.5 rounded">
              {assessment.header_banner}
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-950 tracking-tight">
            {assessment.title}
          </h1>
          <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-slate-600 pt-1">
            <span>Site: <strong>{assessment.site.site_name}</strong></span>
            <span>·</span>
            <span>Nominal: <strong>{assessment.site.nominal_voltage_v} V, {assessment.site.nominal_frequency_hz} Hz</strong></span>
            <span>·</span>
            <span>Status: <strong className="text-amber-800">{assessment.project_status}</strong></span>
          </div>
        </div>

        {/* Deliverable 4: Measures Block */}
        <section className="space-y-3">
          <div className="flex items-center justify-between border-b border-slate-200 pb-1.5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
              Deliverable 4: Key Measures & Quantified Opportunities
            </h3>
            <ProvenanceBadge type="ESTIMATED" size="xs" />
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono">
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
              <div className="text-[10px] text-slate-500 font-sans">Total Idle Energy</div>
              <div className="text-lg font-bold text-slate-900 mt-0.5">{assessment.measures.total_idle_energy_kwh} kWh</div>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
              <div className="text-[10px] text-slate-500 font-sans">Avoidable Idle Energy</div>
              <div className="text-lg font-bold text-amber-700 mt-0.5">{assessment.measures.avoidable_idle_energy_kwh} kWh</div>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
              <div className="text-[10px] text-slate-500 font-sans">Estimated Cost Savings</div>
              <div className="text-lg font-bold text-emerald-800 mt-0.5">{assessment.measures.estimated_cost_savings} {assessment.site.currency}</div>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
              <div className="text-[10px] text-slate-500 font-sans">Estimated CO2 Reduction</div>
              <div className="text-lg font-bold text-emerald-800 mt-0.5">{assessment.measures.estimated_emissions_reduction_kg_co2} kg</div>
            </div>
          </div>

          {/* Out of Scope Disclosure */}
          <div className="bg-slate-100 text-slate-700 text-xs p-3 rounded-lg border border-slate-200 font-medium">
            <strong>Scope Boundary:</strong> {assessment.measures.out_of_scope_notice}
          </div>
        </section>

        {/* Deliverable 1: Baseline Data Needed */}
        <section className="space-y-3">
          <div className="border-b border-slate-200 pb-1.5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
              Deliverable 1: Electrical Baseline Data Needed
            </h3>
          </div>
          <div className="overflow-x-auto border border-slate-200 rounded-lg">
            <table className="min-w-full text-xs text-left">
              <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
                <tr>
                  <th className="px-3 py-2">Parameter</th>
                  <th className="px-3 py-2">Engineering Purpose & Role in Decision Pipeline</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-sans">
                {assessment.baseline_data_needed.map((item: any, idx: number) => (
                  <tr key={idx}>
                    <td className="px-3 py-2 font-mono font-bold text-slate-900">{item.parameter}</td>
                    <td className="px-3 py-2 text-slate-600">{item.purpose}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Track Consideration Questions */}
        <section className="space-y-4">
          <div className="border-b border-slate-200 pb-1.5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
              Track Consideration Questions (Answered from System Data)
            </h3>
          </div>

          {/* Q1 */}
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-2">
            <div className="font-bold text-slate-900 text-xs flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-slate-900 text-white flex items-center justify-center text-[10px]">1</span>
              {assessment.consideration_questions.q1_where_loss_occurs.question}
            </div>
            <p className="text-xs text-slate-700">
              {assessment.consideration_questions.q1_where_loss_occurs.answer}
            </p>
            {/* Top ranked equipment */}
            <div className="pt-2">
              <div className="text-[11px] font-semibold text-slate-800 mb-1">Ranked Equipment Losses:</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
                {assessment.consideration_questions.q1_where_loss_occurs.ranked_equipment.slice(0, 4).map((eq: any) => (
                  <div key={eq.equipment_id} className="bg-white p-2 rounded border border-slate-200 flex justify-between">
                    <span>{eq.equipment_name}:</span>
                    <strong className="text-emerald-800">{eq.avoidable_energy_kwh} kWh avoidable</strong>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Q2 */}
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-2">
            <div className="font-bold text-slate-900 text-xs flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-slate-900 text-white flex items-center justify-center text-[10px]">2</span>
              {assessment.consideration_questions.q2_can_practices_reduce.question}
            </div>
            <p className="text-xs text-slate-700 leading-relaxed">
              {assessment.consideration_questions.q2_can_practices_reduce.answer}
            </p>
          </div>

          {/* Q3 */}
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-2">
            <div className="font-bold text-slate-900 text-xs flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-slate-900 text-white flex items-center justify-center text-[10px]">3</span>
              {assessment.consideration_questions.q3_tradeoffs_to_check.question}
            </div>
            <div className="space-y-1.5 pt-1">
              {assessment.consideration_questions.q3_tradeoffs_to_check.tradeoffs.map((t: any, idx: number) => (
                <div key={idx} className="bg-white p-2 rounded border border-slate-200 text-xs">
                  <strong className="text-slate-900">{t.tradeoff}:</strong> <span className="text-slate-600">{t.detail}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Deliverable 3: Pilot Plan & Roadmap */}
        <section className="space-y-4">
          <div className="border-b border-slate-200 pb-1.5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
              Deliverable 3: Comprehensive Pilot Plan & Deployment Roadmap
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {assessment.pilot_plan.methodology_steps.map((s: any) => (
              <div key={s.step} className="border border-slate-200 rounded-lg p-3 bg-slate-50/60 space-y-1 text-xs">
                <div className="font-bold text-slate-900 flex items-center gap-1.5">
                  <span className="w-4 h-4 rounded-full bg-emerald-700 text-white flex items-center justify-center text-[10px]">
                    {s.step}
                  </span>
                  {s.title}
                </div>
                <p className="text-slate-600 text-[11px] leading-relaxed">{s.description}</p>
              </div>
            ))}
          </div>

          {/* Roadmap Stage Gates with Honest Status */}
          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <div className="bg-slate-50 p-2.5 font-bold text-slate-800 text-xs border-b border-slate-200">
              Implementation Roadmap Stage Gates
            </div>
            <div className="divide-y divide-slate-100 text-xs">
              {assessment.pilot_plan.roadmap_stages.map((stage: any) => (
                <div key={stage.stage} className="p-2.5 flex items-center justify-between font-mono">
                  <span className="font-medium text-slate-800">
                    Stage {stage.stage}: {stage.name}
                  </span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      stage.status === 'IN PROGRESS'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-slate-100 text-slate-500'
                    }`}
                  >
                    {stage.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};
