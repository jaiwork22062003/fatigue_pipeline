import React from 'react';
import { Calendar, Play, Download, BarChart3, CheckCircle2, AlertCircle } from 'lucide-react';
import { UserDatesCatalog } from '../../types';

interface DateActionStripProps {
  selectedWorker: string;
  selectedDate: string;
  catalog: UserDatesCatalog;
  onViewReport: () => void;
  onRunLocal: () => void;
  onDownloadAndRun: () => void;
  isLoading: boolean;
}

export const DateActionStrip: React.FC<DateActionStripProps> = ({
  selectedWorker,
  selectedDate,
  catalog,
  onViewReport,
  onRunLocal,
  onDownloadAndRun,
  isLoading
}) => {
  const userDates = catalog.user_dates?.[selectedWorker] || {};
  const dateInfo = selectedDate ? userDates[selectedDate] : undefined;
  const hasReport = Boolean(dateInfo && dateInfo.has_report);
  const hasRaw = Boolean(dateInfo && dateInfo.count > 0);

  return (
    <div className="bg-[#1e293b]/70 p-4 rounded-2xl border border-cyan-900/60 flex flex-col md:flex-row justify-between items-start md:items-center gap-3 shadow-md">
      {/* Date & status readout */}
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="text-gray-400 flex items-center gap-1">
          <Calendar className="w-3.5 h-3.5 text-cyan-400" />
          <span>Selected Date:</span>
        </span>
        <span className="font-bold text-white font-mono bg-gray-900/90 px-2.5 py-1 rounded border border-gray-700">
          {selectedDate || '--'}
        </span>

        <span className="text-gray-400 ml-2">Status:</span>
        {hasReport ? (
          <span className="text-emerald-400 font-bold flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Evaluated Report Ready ({dateInfo?.count || 1} telemetry files, ~{dateInfo?.total_size_mb || 0} MB)</span>
          </span>
        ) : hasRaw ? (
          <span className="text-cyan-400 font-bold flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-[0_0_8px_#22d3ee]" />
            <span>Raw Telemetry Available Locally ({dateInfo?.count} files, ~{dateInfo?.total_size_mb || 0} MB)</span>
          </span>
        ) : (
          <span className="text-gray-400 flex items-center gap-1.5">
            <AlertCircle className="w-4 h-4 text-gray-500" />
            <span>No Local Telemetry for {selectedWorker} on this date</span>
          </span>
        )}
      </div>

      {/* Action buttons */}
      <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
        {hasReport && (
          <button
            type="button"
            onClick={onViewReport}
            className="py-2 px-3.5 rounded-xl font-bold text-xs uppercase tracking-wide bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg transition flex items-center gap-1.5 border border-emerald-400/40 cursor-pointer"
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>View Report in Dashboard</span>
          </button>
        )}

        {hasReport ? (
          <button
            type="button"
            onClick={onRunLocal}
            disabled={isLoading}
            className="py-2 px-3 rounded-xl font-semibold text-xs text-gray-300 hover:text-white bg-gray-800 hover:bg-gray-700 transition border border-gray-700 flex items-center gap-1 cursor-pointer disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5" />
            <span>Re-run Pipeline</span>
          </button>
        ) : hasRaw ? (
          <button
            type="button"
            onClick={onRunLocal}
            disabled={isLoading}
            className="py-2 px-3.5 rounded-xl font-bold text-xs uppercase tracking-wide bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg transition flex items-center gap-1.5 border border-cyan-400/40 cursor-pointer disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5" />
            <span>Run Pipeline (Local Data)</span>
          </button>
        ) : (
          <button
            type="button"
            onClick={onDownloadAndRun}
            disabled={isLoading}
            className="py-2 px-3.5 rounded-xl font-bold text-xs uppercase tracking-wide bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg transition flex items-center gap-1.5 border border-cyan-400/40 cursor-pointer disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download & Run for {selectedWorker} (Florina API)</span>
          </button>
        )}
      </div>
    </div>
  );
};
