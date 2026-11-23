import React from 'react';
import { User, Download, Sparkles } from 'lucide-react';
import { UserDatesCatalog } from '../../types';

interface WorkerSelectorProps {
  catalog: UserDatesCatalog;
  selectedWorker: string;
  customUid: string;
  onWorkerChange: (worker: string) => void;
  onCustomUidChange: (uid: string) => void;
  onFetchFromApi: () => void;
  isLoading: boolean;
}

export const WorkerSelector: React.FC<WorkerSelectorProps> = ({
  catalog,
  selectedWorker,
  customUid,
  onWorkerChange,
  onCustomUidChange,
  onFetchFromApi,
  isLoading
}) => {
  const users = catalog.users && catalog.users.length > 0 ? catalog.users : ['3mSa_i'];
  const effectiveUid = customUid.trim() || selectedWorker || '3mSa_i';

  return (
    <div className="bg-[#0d1322] p-4 rounded-2xl border border-gray-800 space-y-3 shadow-md">
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-3">
        {/* Worker selection & custom UID inputs */}
        <div className="flex flex-wrap items-center gap-2.5 w-full lg:w-auto">
          <span className="text-xs font-bold text-cyan-400 uppercase tracking-wide flex items-center gap-1.5">
            <User className="w-3.5 h-3.5" />
            <span>Worker UID:</span>
          </span>

          {/* Known local users dropdown */}
          <div className="relative min-w-[200px]">
            <select
              value={customUid.trim() ? '' : selectedWorker}
              onChange={(e) => {
                onCustomUidChange('');
                onWorkerChange(e.target.value);
              }}
              className="w-full bg-[#1e293b] text-white text-xs font-semibold rounded-xl px-3 py-2 border border-gray-700 focus:outline-none focus:border-cyan-400 cursor-pointer transition"
            >
              {customUid.trim() && <option value="">-- Custom UID Active --</option>}
              {users.map((u) => {
                const dates = catalog.user_dates?.[u] || {};
                const count = Object.keys(dates).length;
                return (
                  <option key={u} value={u}>
                    {u} ({count} telemetry date{count === 1 ? '' : 's'})
                  </option>
                );
              })}
            </select>
          </div>

          <span className="text-xs text-gray-500 font-medium">or custom UID:</span>

          {/* Direct Custom UID input field */}
          <div className="relative flex items-center">
            <input
              type="text"
              id="input-custom-uid"
              placeholder="Enter Custom UID (e.g. user_101)"
              value={customUid}
              onChange={(e) => onCustomUidChange(e.target.value)}
              className="bg-[#1e293b] text-white text-xs font-medium rounded-xl px-3 py-2 border border-cyan-500/60 focus:outline-none focus:border-cyan-400 min-w-[210px] transition"
            />
          </div>

          {/* Fetch from Florina Cloud API button */}
          <button
            type="button"
            onClick={onFetchFromApi}
            disabled={isLoading}
            className="py-2 px-3.5 rounded-xl font-bold text-xs uppercase tracking-wide bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-lg border border-cyan-400/50 cursor-pointer flex items-center gap-1.5 transition active:scale-95 disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            <span>{isLoading ? 'Connecting...' : 'Fetch from Florina API'}</span>
          </button>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs text-gray-400">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399] inline-block" />
            <span className="text-gray-300 font-medium">Evaluated Report Ready</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-[0_0_8px_#22d3ee] inline-block" />
            <span className="text-gray-300 font-medium">Raw Telemetry Available</span>
          </div>
        </div>
      </div>

      {/* Target status line */}
      <div className="flex flex-wrap items-center gap-2 text-[11px] text-gray-400 font-mono px-1 border-t border-gray-800/80 pt-2.5">
        <span>Active Target Worker UID:</span>
        <strong className="text-cyan-300 font-bold px-2 py-0.5 rounded bg-gray-900 border border-cyan-800">
          {effectiveUid}
        </strong>
        <span className="text-gray-500">
          • Type any worker UID above or choose from dropdown. Then select a date on the calendar below.
        </span>
      </div>
    </div>
  );
};
