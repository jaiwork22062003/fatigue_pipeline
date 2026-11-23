import React, { useState, useEffect, useCallback } from 'react';
import { WorkerSelector } from '../components/Dashboard/WorkerSelector';
import { LiveCalendar } from '../components/Dashboard/LiveCalendar';
import { DateActionStrip } from '../components/Dashboard/DateActionStrip';
import { MetricCards } from '../components/Dashboard/MetricCards';
import { FatigueChart } from '../components/Dashboard/FatigueChart';
import { SessionLogTable } from '../components/Dashboard/SessionLogTable';
import {
  fetchUserDates,
  fetchTelemetryData,
  triggerPipelineJob,
  fetchJobStatus
} from '../services/api';
import { EvaluationWindow, SessionReport, UserDatesCatalog } from '../types';
import { Activity, Clock, ShieldCheck, Sparkles } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const [catalog, setCatalog] = useState<UserDatesCatalog>({ users: ['3mSa_i'], user_dates: {} });
  const [reports, setReports] = useState<Record<string, SessionReport>>({});
  const [selectedWorker, setSelectedWorker] = useState<string>('3mSa_i');
  const [customUid, setCustomUid] = useState<string>('');
  const [selectedDate, setSelectedDate] = useState<string>('2026-03-27');
  const [hoveredWindow, setHoveredWindow] = useState<EvaluationWindow | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Initial Load
  const loadInitialData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [catData, repData] = await Promise.all([
        fetchUserDates(),
        fetchTelemetryData()
      ]);
      setCatalog(catData);
      setReports(repData);

      // Auto-select first worker and date if available
      const workers = catData.users || [];
      if (workers.length > 0) {
        const worker = workers[0];
        setSelectedWorker(worker);
        const dates = Object.keys(catData.user_dates?.[worker] || {});
        if (dates.length > 0) {
          setSelectedDate(dates[dates.length - 1]);
        }
      }
    } catch (err) {
      console.error('Error loading dashboard data:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  const effectiveWorker = customUid.trim() || selectedWorker;

  // Find matching report for effectiveWorker and selectedDate
  // Report keys in server may be "report_{user}_{date}.json", "report_{date}.json", or direct filename
  const getActiveReport = (): SessionReport | null => {
    if (!reports) return null;

    // Check specific keys
    const matchKeys = [
      `report_${effectiveWorker}_${selectedDate}.json`,
      `report_${selectedDate}.json`,
      `fatigue_report_${selectedDate}.json`,
      `${effectiveWorker}_${selectedDate}`
    ];

    for (const key of matchKeys) {
      if (reports[key]) return reports[key];
    }

    // Try finding by filename or date match
    const foundKey = Object.keys(reports).find(
      k => k.includes(selectedDate) && (k.includes(effectiveWorker) || Object.keys(reports).length === 1)
    );
    if (foundKey) return reports[foundKey];

    // Fallback: first report available if user matches
    const firstKey = Object.keys(reports)[0];
    return firstKey ? reports[firstKey] : null;
  };

  const activeSession = getActiveReport();

  // Polling pipeline execution
  const pollPipelineStatus = async () => {
    try {
      const status = await fetchJobStatus();
      if (status.state === 'running') {
        setStatusMessage(`${status.phase || 'Processing'}: ${status.percent || 0}% - ${status.message || ''}`);
        setTimeout(pollPipelineStatus, 1500);
      } else {
        setIsLoading(false);
        setStatusMessage(null);
        // Refresh catalog & reports
        const [catData, repData] = await Promise.all([fetchUserDates(), fetchTelemetryData()]);
        setCatalog(catData);
        setReports(repData);
      }
    } catch {
      setIsLoading(false);
      setStatusMessage(null);
    }
  };

  // Handlers for Pipeline Actions
  const handleRunPipeline = async (forceDownload: boolean) => {
    if (!selectedDate) return;
    setIsLoading(true);
    setStatusMessage(forceDownload ? 'Downloading telemetry & running pipeline...' : 'Processing local session...');
    try {
      await triggerPipelineJob({
        user_id: effectiveWorker,
        start_date: selectedDate,
        end_date: selectedDate,
        force_download: forceDownload
      });
      setTimeout(pollPipelineStatus, 1000);
    } catch (err: any) {
      setIsLoading(false);
      setStatusMessage(null);
      alert(`Pipeline error: ${err.message || 'Execution failed'}`);
    }
  };

  const handleFetchFromApi = async () => {
    if (!effectiveWorker) return;
    setIsLoading(true);
    setStatusMessage(`Fetching worker catalog for UID: ${effectiveWorker}...`);
    try {
      await triggerPipelineJob({
        user_id: effectiveWorker,
        start_date: selectedDate || new Date().toISOString().split('T')[0],
        end_date: selectedDate || new Date().toISOString().split('T')[0],
        force_download: true
      });
      setTimeout(pollPipelineStatus, 1000);
    } catch (err: any) {
      setIsLoading(false);
      setStatusMessage(null);
      alert(`API fetch error: ${err.message || 'Could not fetch from Florina API'}`);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Status banner if job is running */}
      {statusMessage && (
        <div className="bg-cyan-500/10 border border-cyan-500/40 rounded-xl p-3 text-cyan-300 text-xs flex items-center justify-between animate-pulse">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 animate-spin" />
            <span>{statusMessage}</span>
          </div>
          <span className="font-mono text-[11px] text-cyan-400">PIPELINE ACTIVE</span>
        </div>
      )}

      {/* Top Controls: Worker Selector */}
      <WorkerSelector
        catalog={catalog}
        selectedWorker={selectedWorker}
        customUid={customUid}
        onWorkerChange={(w) => setSelectedWorker(w)}
        onCustomUidChange={(uid) => setCustomUid(uid)}
        onFetchFromApi={handleFetchFromApi}
        isLoading={isLoading}
      />

      {/* Calendar & Date Action Strip */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-5">
          <LiveCalendar
            catalog={catalog}
            selectedWorker={effectiveWorker}
            selectedDate={selectedDate}
            onSelectDate={(d) => setSelectedDate(d)}
          />
        </div>

        <div className="lg:col-span-7 space-y-4">
          <DateActionStrip
            selectedWorker={effectiveWorker}
            selectedDate={selectedDate}
            catalog={catalog}
            onViewReport={() => {}}
            onRunLocal={() => handleRunPipeline(false)}
            onDownloadAndRun={() => handleRunPipeline(true)}
            isLoading={isLoading}
          />

          {/* Session Metadata Banner */}
          {activeSession ? (
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div>
                <span className="text-slate-500 text-[11px] block">Clock Range</span>
                <span className="font-mono text-slate-200 font-semibold flex items-center gap-1 mt-0.5">
                  <Clock className="w-3.5 h-3.5 text-cyan-400" />
                  {activeSession.session_start_clock || '04:08:00'} - {activeSession.session_end_clock || '16:00:00'}
                </span>
              </div>
              <div>
                <span className="text-slate-500 text-[11px] block">Total Duration</span>
                <span className="font-mono text-slate-200 font-semibold mt-0.5 block">
                  {((activeSession.total_duration_sec || 0) / 3600).toFixed(1)} hrs ({activeSession.total_windows || 0} windows)
                </span>
              </div>
              <div>
                <span className="text-slate-500 text-[11px] block">Baseline Cadence / HR</span>
                <span className="font-mono text-slate-200 font-semibold mt-0.5 block">
                  {activeSession.walking_cadence_baseline?.toFixed(0) || 105} spm / {activeSession.resting_hr_baseline?.toFixed(0) || 68} bpm
                </span>
              </div>
              <div>
                <span className="text-slate-500 text-[11px] block">Overall Severity</span>
                <span className="font-bold text-cyan-400 mt-0.5 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  {(activeSession.summary?.severity || 'info').toUpperCase()}
                </span>
              </div>
            </div>
          ) : (
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 text-center text-xs text-slate-400">
              <Sparkles className="w-6 h-6 text-cyan-500/40 mx-auto mb-2" />
              <p>No evaluation report loaded for {selectedDate}. Click "Run Pipeline" above to process raw telemetry.</p>
            </div>
          )}
        </div>
      </div>

      {/* Real-time Metric Cards (Heart Rate, Cadence, Symmetry, Cumulative Load) */}
      {activeSession && (
        <MetricCards session={activeSession} hoveredWindow={hoveredWindow} />
      )}

      {/* Fatigue Chart */}
      {activeSession && (
        <FatigueChart
          session={activeSession}
          onHoverWindow={(win) => setHoveredWindow(win)}
        />
      )}

      {/* Detailed Evaluation Log Table */}
      {activeSession && activeSession.windows && (
        <SessionLogTable windows={activeSession.windows} />
      )}
    </div>
  );
};
