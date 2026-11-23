import React from 'react';
import { Heart, Activity, Scale, ShieldAlert } from 'lucide-react';
import { EvaluationWindow, SessionReport } from '../../types';

interface MetricCardsProps {
  session: SessionReport;
  hoveredWindow: EvaluationWindow | null;
}

export const MetricCards: React.FC<MetricCardsProps> = ({ session, hoveredWindow }) => {
  const wins = session.windows || [];
  const sum = session.summary || { average_fatigue: 0, peak_fatigue: 0, final_fatigue: 0, severity: 'none' };

  // Calculate active shift metrics
  const activeHrs = wins.filter((w) => w.hr_bpm && w.hr_trustworthy).map((w) => w.hr_bpm as number);
  const activeCads = wins.filter((w) => w.cadence_spm && w.cadence_spm > 0).map((w) => w.cadence_spm);
  const activeAsym = wins.filter((w) => w.temporal_asymmetry_pct !== undefined && w.temporal_asymmetry_pct > 0).map((w) => w.temporal_asymmetry_pct);
  const walkingWins = wins.filter((w) => (w.activity_state || '').includes('walking'));

  const isHover = Boolean(hoveredWindow);
  const currWin = hoveredWindow || (wins.length > 0 ? wins[wins.length - 1] : null);
  const comps = currWin?.components || {};

  const sqi = currWin?.ppg_sqi || 'poor';
  const act = currWin?.activity_state || 'stationary';
  const isWalking = act.includes('walking');

  // 1. Heart Rate (PPG) Display
  let hrBigDisplay = '';
  if (isHover) {
    hrBigDisplay = currWin?.hr_bpm
      ? `${currWin.hr_bpm.toFixed(1)} bpm`
      : 'Motion Protected';
  } else {
    const avgHrVal = sum.active_hr_avg !== undefined && sum.active_hr_avg !== null
      ? sum.active_hr_avg.toFixed(1)
      : (activeHrs.length > 0 ? (activeHrs.reduce((a, b) => a + b, 0) / activeHrs.length).toFixed(1) : '--');
    hrBigDisplay = avgHrVal !== '--' ? `${avgHrVal} bpm (Active Avg)` : '-- bpm';
  }

  // 2. Cadence Display
  let cadBigDisplay = '';
  if (isHover) {
    cadBigDisplay = (currWin?.cadence_spm ?? 0) > 0
      ? `${(currWin?.cadence_spm ?? 0).toFixed(1)} spm`
      : '0.0 spm (Resting)';
  } else {
    const avgCadVal = sum.active_cadence_avg !== undefined && sum.active_cadence_avg !== null && sum.active_cadence_avg > 0
      ? sum.active_cadence_avg.toFixed(1)
      : (activeCads.length > 0 ? (activeCads.reduce((a, b) => a + b, 0) / activeCads.length).toFixed(1) : '0.0');
    cadBigDisplay = avgCadVal !== '0.0' ? `${avgCadVal} spm (Walking Avg)` : '0.0 spm';
  }

  // 3. Bilateral Symmetry
  const asymVal = isHover
    ? (currWin?.temporal_asymmetry_pct ?? 0.0)
    : (activeAsym.length > 0 ? activeAsym.reduce((a, b) => a + b, 0) / activeAsym.length : 0.0);
  const symPct = Math.max(0.0, 100.0 - asymVal);

  // 4. Shift Load & Recovery
  const loadVal = session.cum_load !== undefined ? session.cum_load.toFixed(1) : (currWin?.cum_load ?? '--');
  const startClk = session.session_start_clock || '';
  const endClk = session.session_end_clock || '';

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Cardio & PPG SQI */}
      <div className={`bg-[#0d1322] p-4 rounded-2xl border border-gray-800 transition-all ${isHover ? 'ring-2 ring-cyan-400/60 shadow-[0_0_15px_rgba(34,211,238,0.2)]' : 'shadow-md'}`}>
        <div className="flex justify-between items-center">
          <span className="text-xs font-bold text-cyan-400 uppercase tracking-wide flex items-center gap-1.5">
            <Heart className="w-3.5 h-3.5 text-rose-400" />
            <span>1. Heart Rate (PPG)</span>
          </span>
          <span className="text-[10px] bg-rose-950 text-rose-300 px-1.5 py-0.5 rounded border border-rose-800 font-mono">Weight: 40%</span>
        </div>
        <div className="text-xl font-extrabold text-white mt-1.5 font-mono">
          {hrBigDisplay}
        </div>
        <div className="mt-2 text-[11px] text-gray-400 space-y-1 font-mono">
          <div>
            • PPG Signal Quality:{' '}
            <strong className={`uppercase ${sqi === 'good' ? 'text-emerald-400' : (sqi === 'fair' ? 'text-blue-400' : 'text-amber-400')}`}>
              {sqi}
            </strong>
          </div>
          <div>
            • Peak Active HR: <strong className="text-rose-300">{sum.peak_hr || (activeHrs.length > 0 ? Math.max(...activeHrs).toFixed(1) : '--')} bpm</strong>
          </div>
          <div>
            • Cardio Strain Penalty:{' '}
            <strong className="text-white">
              {comps.cardio_strain !== undefined ? `${comps.cardio_strain.toFixed(1)} pts` : '0.0 pts'}
            </strong>{' '}
            <span className="text-gray-500 font-normal">(0-100)</span>
          </div>
          <div>
            • %HRR / Cost:{' '}
            <strong className="text-white">
              {comps.pct_hrr !== undefined ? `${comps.pct_hrr.toFixed(1)}%` : '--'} / {comps.cardiac_cost !== undefined ? comps.cardiac_cost.toFixed(2) : '--'}
            </strong>
          </div>
        </div>
      </div>

      {/* 2. Cadence & Activity */}
      <div className={`bg-[#0d1322] p-4 rounded-2xl border border-gray-800 transition-all ${isHover ? 'ring-2 ring-cyan-400/60 shadow-[0_0_15px_rgba(34,211,238,0.2)]' : 'shadow-md'}`}>
        <div className="flex justify-between items-center">
          <span className="text-xs font-bold text-cyan-400 uppercase tracking-wide flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
            <span>2. Cadence (Dual IMU)</span>
          </span>
          <span className="text-[10px] bg-cyan-950 text-cyan-300 px-1.5 py-0.5 rounded border border-cyan-800 font-mono">
            {isWalking ? 'Active: 35%' : 'Gated: 0%'}
          </span>
        </div>
        <div className="text-xl font-extrabold text-cyan-300 mt-1.5 font-mono">
          {cadBigDisplay}
        </div>
        <div className="mt-2 text-[11px] text-gray-400 space-y-1 font-mono">
          <div>
            • Activity State:{' '}
            <strong className={`uppercase ${isWalking ? 'text-emerald-400' : (act === 'stationary' ? 'text-blue-400' : 'text-amber-400')}`}>
              {act.replace('_', ' ')}
            </strong>
          </div>
          <div>
            • Active Locomotion:{' '}
            <strong className="text-cyan-300">
              {walkingWins.length} windows ({((walkingWins.length / Math.max(1, wins.length)) * 100).toFixed(0)}% of shift)
            </strong>
          </div>
          <div>
            • Peak Cadence:{' '}
            <strong className="text-cyan-300">
              {sum.peak_cadence || (activeCads.length > 0 ? Math.max(...activeCads).toFixed(1) : '0.0')} spm
            </strong>
          </div>
          <div>
            • Cadence Decline Penalty:{' '}
            <strong className="text-white">
              {comps.cadence_decline !== undefined ? `${comps.cadence_decline.toFixed(1)} pts` : '0.0 pts'}
            </strong>{' '}
            <span className="text-gray-500 font-normal">
              {(comps.cadence_decline ?? 0) > 0 ? `${(comps.cadence_decline ?? 0).toFixed(1)}% decline` : 'healthy pace'}
            </span>
          </div>
        </div>
      </div>

      {/* 3. Gait & Bilateral Timing */}
      <div className={`bg-[#0d1322] p-4 rounded-2xl border border-gray-800 transition-all ${isHover ? 'ring-2 ring-cyan-400/60 shadow-[0_0_15px_rgba(34,211,238,0.2)]' : 'shadow-md'}`}>
        <div className="flex justify-between items-center">
          <span className="text-xs font-bold text-cyan-400 uppercase tracking-wide flex items-center gap-1.5">
            <Scale className="w-3.5 h-3.5 text-emerald-400" />
            <span>3. Gait Symmetry</span>
          </span>
          <span className="text-[10px] bg-cyan-950 text-cyan-300 px-1.5 py-0.5 rounded border border-cyan-800 font-mono">Weight: 25%</span>
        </div>
        <div className="text-xl font-extrabold text-emerald-400 mt-1.5 font-mono">
          {symPct.toFixed(1)}% <span className="text-xs text-emerald-300 font-normal">Symmetric</span>
        </div>
        <div className="mt-2 text-[11px] text-gray-400 space-y-1 font-mono">
          <div>
            • Temporal Asymmetry (ASI):{' '}
            <strong className={asymVal > 15 ? 'text-amber-400' : 'text-emerald-400'}>
              {asymVal.toFixed(1)}%
            </strong>
          </div>
          <div>
            • Stride Variability (CV):{' '}
            <strong className="text-white">
              {currWin?.stride_cv ? `${(currWin.stride_cv * 100).toFixed(1)}%` : '0.0%'}
            </strong>
          </div>
          <div>
            • Gait Deg Penalty:{' '}
            <strong className="text-white">
              {comps.gait_degradation !== undefined ? `${comps.gait_degradation.toFixed(1)} pts` : '0.0 pts'}
            </strong>{' '}
            <span className="text-gray-500 font-normal">(0-100)</span>
          </div>
          <div>
            • Timing Metric: <strong className="text-white">Stride Period (TL vs TR)</strong>
          </div>
        </div>
      </div>

      {/* 4. Shift Cumulative Load */}
      <div className={`bg-[#0d1322] p-4 rounded-2xl border border-emerald-800/80 transition-all ${isHover ? 'ring-2 ring-emerald-400/60 shadow-[0_0_15px_rgba(52,211,153,0.2)]' : 'shadow-md'}`}>
        <div className="flex justify-between items-center">
          <span className="text-xs font-bold text-emerald-400 uppercase tracking-wide flex items-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5 text-emerald-400" />
            <span>4. Shift Load & Recovery</span>
          </span>
          <span className="text-[10px] bg-emerald-950 text-emerald-300 px-1.5 py-0.5 rounded border border-emerald-800 font-mono">Physiological</span>
        </div>
        <div className="text-xl font-extrabold text-white mt-1.5 font-mono">
          {loadVal} <span className="text-xs text-emerald-400 font-normal">Load pts</span>
        </div>
        <div className="mt-2 text-[11px] text-gray-400 space-y-1 font-mono">
          <div>
            • Shift Clock Time:{' '}
            <strong className="text-white font-mono">
              {startClk && endClk ? `${startClk} - ${endClk}` : 'Active Shift'}
            </strong>
          </div>
          <div>
            • Motion-Gated Drift:{' '}
            <strong className="text-white">
              +{(Math.min(15.0, (session.cum_load || 0) * 0.012)).toFixed(2)} pts
            </strong>
          </div>
          <div>
            • Physiological Recovery:{' '}
            <strong className="text-white">
              {act === 'stationary' ? 'Resting (HRR-60 Gated)' : 'Locomotion Active'}
            </strong>
          </div>
          <div>
            • Tanaka HRmax Limit: <strong className="text-white">187 bpm (Age 30)</strong>
          </div>
        </div>
      </div>
    </div>
  );
};
