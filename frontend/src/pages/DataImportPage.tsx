import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { ProvenanceBadge } from '../components/common/ProvenanceBadge';
import { Upload, Download, FileText, CheckCircle2, AlertTriangle, AlertCircle, RefreshCw } from 'lucide-react';

export const DataImportPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<any>(null);
  const [importSummary, setImportSummary] = useState<any>(null);
  const [importRuns, setImportRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    loadImportRuns();
  }, []);

  const loadImportRuns = async () => {
    try {
      const runs = await api.listImportRuns();
      setImportRuns(runs);
    } catch (err) {
      console.error(err);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setErrorMsg(null);
      setImportSummary(null);

      try {
        setLoading(true);
        const prev = await api.previewFile(file);
        setPreviewData(prev);
      } catch (err: any) {
        setErrorMsg(err.message || 'Failed to parse file preview');
      } finally {
        setLoading(false);
      }
    }
  };

  const handleExecuteImport = async () => {
    if (!selectedFile) return;
    try {
      setLoading(true);
      setErrorMsg(null);
      const summary = await api.uploadFile(selectedFile);
      setImportSummary(summary);
      loadImportRuns();
    } catch (err: any) {
      setErrorMsg(err.message || 'Import execution failed');
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
            <Upload className="w-4 h-4 text-emerald-700" />
            Telemetry Data Ingestion Pipeline
          </span>
          <ProvenanceBadge type="IMPORTED" size="xs" />
        </div>
        <h2 className="text-lg font-bold text-slate-900 tracking-tight">
          9. External CSV / JSON Telemetry Import Boundary
        </h2>
        <p className="text-xs text-slate-600 leading-relaxed">
          Import electrical data from plant metering or third-party PQ loggers. All ingested rows receive provenance tag <strong className="text-emerald-800">[IMPORTED]</strong>.
          Mandatory fields: <code className="bg-emerald-100 text-emerald-900 px-1 rounded">timestamp, equipment_id, voltage, current</code>.
        </p>
      </div>

      {/* Upload & Sample Download Box */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="md:col-span-2 bg-white rounded-xl border border-dashed border-slate-300 p-8 text-center space-y-3 hover:border-emerald-500 transition-colors">
          <Upload className="w-10 h-10 text-slate-400 mx-auto" />
          <div>
            <label htmlFor="file-upload" className="cursor-pointer text-sm font-bold text-emerald-700 hover:text-emerald-800 underline">
              Choose CSV or JSON file
            </label>
            <input
              id="file-upload"
              type="file"
              accept=".csv,.json"
              onChange={handleFileSelect}
              className="hidden"
            />
            <p className="text-xs text-slate-500 mt-1">UTF-8 formatted CSV or JSON telemetry array</p>
          </div>

          {selectedFile && (
            <div className="text-xs font-mono bg-slate-50 border border-slate-200 p-2 rounded inline-block text-slate-800">
              Selected: <strong>{selectedFile.name}</strong> ({(selectedFile.size / 1024).toFixed(1)} KB)
            </div>
          )}
        </div>

        {/* Download Sample Card */}
        <div className="bg-slate-50 rounded-xl border border-slate-200 p-5 space-y-3 flex flex-col justify-between">
          <div className="space-y-1.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Official Specification</span>
            <h3 className="font-bold text-slate-900 text-sm">Download Valid Schema Sample</h3>
            <p className="text-xs text-slate-600">
              Download a pre-formatted sample CSV with matching equipment IDs and balanced 3-phase readings.
            </p>
          </div>

          <a
            href="/api/v1/import/sample-csv"
            download="plantpulse_telemetry_sample.csv"
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-white hover:bg-slate-100 text-slate-800 font-semibold text-xs rounded-lg border border-slate-300 shadow-xs transition"
          >
            <Download className="w-3.5 h-3.5" /> Download Sample CSV
          </a>
        </div>
      </div>

      {errorMsg && (
        <div className="bg-red-50 border border-red-300 text-red-700 p-4 rounded-xl text-xs space-y-1">
          <div className="font-bold flex items-center gap-1.5">
            <AlertCircle className="w-4 h-4 text-red-600" />
            Import Validation Failed
          </div>
          <div>{errorMsg}</div>
        </div>
      )}

      {/* Preview Section */}
      {previewData && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
            <div>
              <h3 className="font-bold text-slate-900 text-sm">Schema Validation & Preview (First 10 Rows)</h3>
              <p className="text-xs text-slate-500 font-mono">
                Detected Headers: {previewData.headers?.join(', ')}
              </p>
            </div>

            {previewData.is_valid_schema ? (
              <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded border border-emerald-200 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" /> Valid Schema
              </span>
            ) : (
              <span className="text-xs font-semibold text-red-700 bg-red-50 px-2.5 py-1 rounded border border-red-200 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5" /> Missing: {previewData.missing_required_fields?.join(', ')}
              </span>
            )}
          </div>

          <div className="overflow-x-auto border border-slate-200 rounded-lg max-h-60">
            <table className="min-w-full text-xs text-left">
              <thead className="bg-slate-50 text-slate-700 font-semibold uppercase border-b border-slate-200">
                <tr>
                  {previewData.headers?.map((h: string, idx: number) => (
                    <th key={idx} className="px-3 py-2">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                {previewData.preview_rows?.map((row: any[], rIdx: number) => (
                  <tr key={rIdx} className="hover:bg-slate-50">
                    {row.map((cell: any, cIdx: number) => (
                      <td key={cIdx} className="px-3 py-1.5 text-slate-700">{String(cell)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex justify-end pt-2">
            <button
              onClick={handleExecuteImport}
              disabled={loading || !previewData.is_valid_schema}
              className="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white font-bold text-xs rounded-lg shadow-xs flex items-center gap-2 transition"
            >
              {loading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              Execute Telemetry Import &rarr;
            </button>
          </div>
        </div>
      )}

      {/* Import Execution Result Summary */}
      {importSummary && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
          <div className="flex items-center gap-2 text-emerald-800 font-bold text-sm">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            Import Ingestion Completed
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
              <div className="text-slate-500 font-sans text-[10px]">Total Records in File</div>
              <div className="text-base font-bold text-slate-900 mt-0.5">{importSummary.total_records_in_file}</div>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
              <div className="text-slate-500 font-sans text-[10px]">Valid Imported</div>
              <div className="text-base font-bold text-emerald-700 mt-0.5">{importSummary.valid_imported_records}</div>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
              <div className="text-slate-500 font-sans text-[10px]">Warnings</div>
              <div className="text-base font-bold text-amber-700 mt-0.5">{importSummary.warning_count}</div>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
              <div className="text-slate-500 font-sans text-[10px]">Rejected Errors</div>
              <div className="text-base font-bold text-red-700 mt-0.5">{importSummary.error_count}</div>
            </div>
          </div>
        </div>
      )}

      {/* Ingestion History */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
        <h3 className="font-bold text-slate-900 text-sm border-b border-slate-100 pb-2">Import Ingestion History</h3>
        {importRuns.length === 0 ? (
          <div className="text-center py-6 text-slate-400 text-xs">No external import runs logged yet.</div>
        ) : (
          <div className="overflow-x-auto border border-slate-100 rounded-lg">
            <table className="min-w-full text-xs text-left">
              <thead className="bg-slate-50 text-slate-700 uppercase font-semibold border-b border-slate-200">
                <tr>
                  <th className="px-3 py-2">Timestamp</th>
                  <th className="px-3 py-2">Filename</th>
                  <th className="px-3 py-2">Type</th>
                  <th className="px-3 py-2">Imported</th>
                  <th className="px-3 py-2">Errors</th>
                  <th className="px-3 py-2">Provenance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                {importRuns.map(run => (
                  <tr key={run.id} className="hover:bg-slate-50">
                    <td className="px-3 py-1.5 text-slate-500">{run.imported_at.replace('T', ' ').substring(0, 19)}</td>
                    <td className="px-3 py-1.5 font-semibold text-slate-900">{run.filename}</td>
                    <td className="px-3 py-1.5 text-slate-600">{run.file_type}</td>
                    <td className="px-3 py-1.5 text-emerald-700 font-bold">{run.valid_count}</td>
                    <td className="px-3 py-1.5 text-red-600 font-bold">{run.error_count}</td>
                    <td className="px-3 py-1.5">
                      <ProvenanceBadge type={run.provenance} size="xs" />
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
