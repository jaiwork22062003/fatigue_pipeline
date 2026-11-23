import React, { useState } from 'react';
import { EvaluationWindow } from '../../types';

interface SessionLogTableProps {
  windows: EvaluationWindow[];
}

export const SessionLogTable: React.FC<SessionLogTableProps> = ({ windows }) => {
  const [filter, setFilter] = useState<'all' | 'steady' | 'intermittent' | 'stationary' | 'elevated'>('all');

  const filtered = windows.filter((w) => {
    const st = (w.activity_state || w.worker_state || 'stationary').toLowerCase();
    if (filter === 'steady') return st === 'walking_steady';
    if (filter === 'intermittent') return st === 'walking_intermittent';
    if (filter === 'stationary') return st === 'stationary';
    if (filter === 'elevated') return (w.fatigue_composite ?? 0) >= 40.0;
    return true;
  });

  const getBadge = (sev: string) => {
    const s = (sev || 'none').toLowerCase();
    if (s === 'none') return <span className="badge-none px-2 py-0.5 rounded text-[10px] font-bold uppercase">NONE</span>;
    if (s === 'info') return <span className="badge-info px-2 py-0.5 rounded text-[10px] font-bold uppercase">INFO</span>;
    if (s === 'warning') return <span className="badge-warning px-2 py-0.5 rounded text-[10px] font-bold uppercase">WARNING</span>;
    if (s === 'urgent') return <span className="badge-urgent px-2 py-0.5 rounded text-[10px] font-bold uppercase">URGENT</span>;
    return <span className="badge-critical px-2 py-0.5 rounded text-[10px] font-bold uppercase">CRITICAL</span>;
  };

  const getStateBadge = (stRaw: string) => {
    const state = stRaw.toLowerCase();
    if (state === 'walking_steady') {
      return <span className="px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-700/60 text-[10px] font-bold">STEADY WALK</span>;
    }
    if (state === 'walking_intermittent') {
      return <span className="px-2 py-0.5 rounded bg-blue-950/80 text-blue-300 border border-blue-700/60 text-[10px] font-bold">INTERMITTENT</span>;
    }
    if (state === 'running') {
      return <span className="px-2 py-0.5 rounded bg-purple-950/80 text-purple-300 border border-purple-700/60 text-[10px] font-bold">RUNNING</span>;
    }
    if (state === 'stationary') {
      return <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[10px] font-bold">STATIONARY</span>;
    }
    if (state === 'idle' || state === 'disconnected') {
      return <span className="px-2 py-0.5 rounded bg-gray-900 text-gray-400 border border-gray-800 text-[10px] font-bold">IDLE / OFF</span>;
    }
    return <span className="px-2 py-0.5 rounded bg-gray-800 text-gray-400 text-[10px] font-bold">WARMUP</span>;
  };

  return (
    <div className="bg-[#0d1322] p-5 rounded-2xl border border-gray-800 shadow-md space-y-4">
      {/* Table Header & Filters */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div>
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <span>📋 Window-by-Window Physiological Telemetry Log</span>
          </h3>
          <p className="text-xs text-gray-400 mt-0.5">
            Sequential 60-second evaluation intervals with exact wall-clock time and multi-modal gait breakdown.
          </p>
        </div>

        {/* Filter buttons */}
        <div className="flex flex-wrap items-center gap-1.5 bg-[#090d19] p-1 rounded-xl border border-gray-800 text-xs">
          {(['all', 'steady', 'intermittent', 'stationary', 'elevated'] as const).map((id) => (
            <button
              key={id}
              onClick={() => setFilter(id)}
              className={`px-2.5 py-1 text-[11px] font-semibold rounded-lg transition capitalize ${
                filter === id
                  ? 'bg-cyan-600 text-white shadow-sm'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/60'
              }`}
            >
              {id === 'steady' ? 'Steady Walk' : (id === 'elevated' ? 'Fatigue ≥ 40' : id)}
            </button>
          ))}
          <span className="text-[11px] text-gray-500 font-mono px-2 border-l border-gray-800">
            {filtered.length} of {windows.length}
          </span>
        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto max-h-[460px] overflow-y-auto rounded-xl border border-gray-800/80">
        <table className="w-full text-left border-collapse text-xs">
          <thead className="bg-[#111827] text-gray-400 uppercase tracking-wider font-mono text-[10px] sticky top-0 z-10 border-b border-gray-800">
            <tr>
              <th className="py-2.5 px-3">Window</th>
              <th className="py-2.5 px-3">Clock Time / Duration</th>
              <th className="py-2.5 px-3">Activity State</th>
              <th className="py-2.5 px-3">Heart Rate (PPG)</th>
              <th className="py-2.5 px-3">Cadence</th>
              <th className="py-2.5 px-3">Temporal ASI</th>
              <th className="py-2.5 px-3">Stride CV</th>
              <th className="py-2.5 px-3">Fatigue Score</th>
              <th className="py-2.5 px-3">Severity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800/60 font-mono text-gray-300 text-[11px]">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={9} className="py-8 text-center text-gray-500 italic">
                  No telemetry windows matching current filter criteria.
                </td>
              </tr>
            ) : (
              filtered.map((w) => {
                const hrValid = w.hr_bpm && w.hr_trustworthy;
                return (
                  <tr key={w.window} className="hover:bg-gray-800/40 transition">
                    <td className="py-2.5 px-3 text-white font-bold">#{w.window}</td>
                    <td className="py-2.5 px-3 text-gray-300">
                      {w.clock_time && <div className="text-white font-bold text-xs">{w.clock_time}</div>}
                      <div className="text-[10px] text-gray-500">
                        {w.time_sec.toFixed(0)}s ({(w.time_sec / 60.0).toFixed(1)}m)
                      </div>
                    </td>
                    <td className="py-2.5 px-3">{getStateBadge(w.activity_state || w.worker_state || 'stationary')}</td>
                    <td className="py-2.5 px-3">
                      {hrValid ? (
                        <div className="flex items-center gap-1.5">
                          <span className="text-rose-300 font-bold">{w.hr_bpm?.toFixed(1)} bpm</span>
                          <span className="text-[9px] text-emerald-400 bg-emerald-950/60 px-1 py-0.2 rounded border border-emerald-800 uppercase font-sans">
                            {w.ppg_sqi || 'GOOD'}
                          </span>
                        </div>
                      ) : w.hr_bpm ? (
                        <div className="flex items-center gap-1.5">
                          <span className="text-amber-400 font-mono">{w.hr_bpm.toFixed(1)} bpm</span>
                          <span className="text-[9px] text-amber-300 bg-amber-950/60 px-1 py-0.2 rounded border border-amber-800 uppercase font-sans">
                            {w.ppg_sqi || 'POOR'}
                          </span>
                        </div>
                      ) : (
                        <span className="text-gray-500 italic">Suppressed (Motion)</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-cyan-300">
                      {w.cadence_spm > 0 ? (
                        <strong className="font-bold">{w.cadence_spm.toFixed(1)} spm</strong>
                      ) : (
                        <span className="text-gray-500">0.0 spm</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-gray-300">
                      {w.temporal_asymmetry_pct !== undefined ? `${w.temporal_asymmetry_pct.toFixed(1)}%` : '0.0%'}
                    </td>
                    <td className="py-2.5 px-3 text-gray-300">
                      {w.stride_cv ? `${(w.stride_cv * 100).toFixed(1)}%` : '0.0%'}
                    </td>
                    <td className="py-2.5 px-3 font-bold text-white">
                      {w.fatigue_composite !== null ? w.fatigue_composite.toFixed(1) : 'Warmup'}
                    </td>
                    <td className="py-2.5 px-3">{getBadge(w.severity)}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
