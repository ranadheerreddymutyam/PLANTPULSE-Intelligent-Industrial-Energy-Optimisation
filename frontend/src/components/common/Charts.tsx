import React, { useState } from 'react';
import { Table, Eye, EyeOff } from 'lucide-react';

interface SparklineProps {
  data: number[];
  color?: string;
  height?: number;
  width?: number;
}

export const Sparkline: React.FC<SparklineProps> = ({
  data,
  color = '#16a34a',
  height = 36,
  width = 120
}) => {
  if (!data || data.length < 2) {
    return <div className="text-xs text-slate-400">No data</div>;
  }

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const points = data.map((val, idx) => {
    const x = (idx / (data.length - 1)) * width;
    const y = height - ((val - min) / range) * (height - 6) - 3;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
};

interface TimeSeriesChartProps {
  title: string;
  data: Array<{
    timestamp: string;
    [key: string]: any;
  }>;
  series: Array<{
    key: string;
    label: string;
    color: string;
    unit?: string;
  }>;
  height?: number;
  provenance?: string;
}

export const TimeSeriesChart: React.FC<TimeSeriesChartProps> = ({
  title,
  data,
  series,
  height = 260,
  provenance = 'SIMULATED'
}) => {
  const [showTable, setShowTable] = useState(false);

  if (!data || data.length === 0) {
    return (
      <div className="bg-white p-6 rounded-xl border border-slate-200 text-center text-slate-500 text-sm">
        No telemetry records available for chart rendering.
      </div>
    );
  }

  // Calculate scales
  let allValues: number[] = [];
  series.forEach(s => {
    data.forEach(d => {
      const v = Number(d[s.key]);
      if (!isNaN(v)) allValues.push(v);
    });
  });

  const minVal = Math.min(0, ...allValues);
  const maxVal = Math.max(10, ...allValues);
  const valRange = maxVal - minVal || 1;

  const chartW = 700;
  const chartH = height;
  const padLeft = 55;
  const padRight = 20;
  const padTop = 20;
  const padBottom = 35;
  const plotW = chartW - padLeft - padRight;
  const plotH = chartH - padTop - padBottom;

  return (
    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <h3 className="font-semibold text-slate-900 text-sm">{title}</h3>
          <span className="text-[11px] text-slate-500 font-mono">Continuous 3-Phase Telemetry Profile</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-3 text-xs">
            {series.map(s => (
              <span key={s.key} className="flex items-center gap-1.5 font-medium text-slate-600">
                <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ backgroundColor: s.color }} />
                {s.label} {s.unit ? `(${s.unit})` : ''}
              </span>
            ))}
          </div>
          <button
            type="button"
            onClick={() => setShowTable(!showTable)}
            className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-md transition"
            aria-label="Toggle accessible data table"
          >
            <Table className="w-3.5 h-3.5 text-slate-500" />
            {showTable ? 'Hide Table' : 'View Table'}
          </button>
        </div>
      </div>

      {!showTable ? (
        <div className="w-full overflow-x-auto">
          <svg
            viewBox={`0 0 ${chartW} ${chartH}`}
            className="w-full min-w-[550px] select-none font-mono text-[10px]"
          >
            {/* Horizontal Grid lines */}
            {[0, 0.25, 0.5, 0.75, 1].map(frac => {
              const y = padTop + plotH * (1 - frac);
              const gridVal = (minVal + frac * valRange).toFixed(1);
              return (
                <g key={frac}>
                  <line
                    x1={padLeft}
                    y1={y}
                    x2={chartW - padRight}
                    y2={y}
                    stroke="#e2e8f0"
                    strokeDasharray="4 4"
                  />
                  <text x={padLeft - 8} y={y + 3} textAnchor="end" fill="#64748b">
                    {gridVal}
                  </text>
                </g>
              );
            })}

            {/* Series Paths */}
            {series.map(s => {
              const points = data.map((d, i) => {
                const x = padLeft + (i / (data.length - 1)) * plotW;
                const v = Number(d[s.key]) || 0;
                const y = padTop + plotH * (1 - (v - minVal) / valRange);
                return `${x},${y}`;
              }).join(' ');

              return (
                <polyline
                  key={s.key}
                  fill="none"
                  stroke={s.color}
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  points={points}
                />
              );
            })}

            {/* Time labels on X axis */}
            {data.filter((_, i) => i % Math.max(1, Math.floor(data.length / 5)) === 0).map((d, idx, arr) => {
              const originalIndex = data.indexOf(d);
              const x = padLeft + (originalIndex / (data.length - 1)) * plotW;
              const timeLabel = d.timestamp.split('T')[1]?.substring(0, 5) || d.timestamp.substring(11, 16);
              return (
                <text key={idx} x={x} y={chartH - 10} textAnchor="middle" fill="#64748b">
                  {timeLabel}
                </text>
              );
            })}
          </svg>
        </div>
      ) : (
        /* Accessible Table Alternative */
        <div className="overflow-x-auto border border-slate-200 rounded-lg max-h-72">
          <table className="min-w-full text-xs text-left">
            <thead className="bg-slate-50 text-slate-700 uppercase font-semibold border-b border-slate-200 sticky top-0">
              <tr>
                <th className="px-3 py-2">Timestamp</th>
                {series.map(s => (
                  <th key={s.key} className="px-3 py-2">{s.label} ({s.unit})</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {data.slice(-30).map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-50">
                  <td className="px-3 py-1.5 text-slate-600">{row.timestamp}</td>
                  {series.map(s => (
                    <td key={s.key} className="px-3 py-1.5 text-slate-900 font-medium">
                      {row[s.key] !== undefined ? Number(row[s.key]).toFixed(2) : '—'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
