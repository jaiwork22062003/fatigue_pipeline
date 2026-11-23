import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Crosshair, Calendar as CalIcon } from 'lucide-react';
import { UserDatesCatalog } from '../../types';

interface LiveCalendarProps {
  catalog: UserDatesCatalog;
  selectedWorker: string;
  selectedDate: string;
  onSelectDate: (date: string) => void;
}

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

export const LiveCalendar: React.FC<LiveCalendarProps> = ({
  catalog,
  selectedWorker,
  selectedDate,
  onSelectDate
}) => {
  // Parse initial year and month from selectedDate or current date
  const initDate = selectedDate ? new Date(selectedDate) : new Date(2026, 2, 27);
  const [calYear, setCalYear] = useState<number>(initDate.getFullYear() || 2026);
  const [calMonth, setCalMonth] = useState<number>(initDate.getMonth() || 2); // 0-indexed

  const prevMonth = () => {
    if (calMonth === 0) {
      setCalMonth(11);
      setCalYear((y) => y - 1);
    } else {
      setCalMonth((m) => m - 1);
    }
  };

  const nextMonth = () => {
    if (calMonth === 11) {
      setCalMonth(0);
      setCalYear((y) => y + 1);
    } else {
      setCalMonth((m) => m + 1);
    }
  };

  // User dates lookup
  const userDates = catalog.user_dates?.[selectedWorker] || {};

  // Jump to latest available data date
  const jumpToLatestData = () => {
    const dates = Object.keys(userDates).sort();
    if (dates.length > 0) {
      const latest = dates[dates.length - 1];
      onSelectDate(latest);
      const [y, m] = latest.split('-').map(Number);
      setCalYear(y);
      setCalMonth(m - 1);
    }
  };

  // Calendar grid calculations
  const firstDayIndex = new Date(calYear, calMonth, 1).getDay(); // 0 is Sunday
  const totalDays = new Date(calYear, calMonth + 1, 0).getDate();
  const prevTotalDays = new Date(calYear, calMonth, 0).getDate();

  // Create day cell elements
  const cells: React.ReactNode[] = [];

  // 1. Previous month padding days
  for (let i = firstDayIndex - 1; i >= 0; i--) {
    const dNum = prevTotalDays - i;
    const prevM = calMonth === 0 ? 11 : calMonth - 1;
    const prevY = calMonth === 0 ? calYear - 1 : calYear;
    const dtStr = `${prevY}-${String(prevM + 1).padStart(2, '0')}-${String(dNum).padStart(2, '0')}`;
    const dateInfo = userDates[dtStr];
    cells.push(renderCell(dNum, dtStr, true, dateInfo));
  }

  // 2. Current month days
  for (let d = 1; d <= totalDays; d++) {
    const dtStr = `${calYear}-${String(calMonth + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    const dateInfo = userDates[dtStr];
    cells.push(renderCell(d, dtStr, false, dateInfo));
  }

  // 3. Trailing padding days
  const currentCellCount = firstDayIndex + totalDays;
  const targetCount = currentCellCount > 35 ? 42 : 35;
  const trailing = targetCount - currentCellCount;
  for (let t = 1; t <= trailing; t++) {
    const nextM = calMonth === 11 ? 0 : calMonth + 1;
    const nextY = calMonth === 11 ? calYear + 1 : calYear;
    const dtStr = `${nextY}-${String(nextM + 1).padStart(2, '0')}-${String(t).padStart(2, '0')}`;
    const dateInfo = userDates[dtStr];
    cells.push(renderCell(t, dtStr, true, dateInfo));
  }

  function renderCell(dayNum: number, dtStr: string, isDimmed: boolean, dateInfo?: any) {
    const isSelected = dtStr === selectedDate;
    const hasData = Boolean(dateInfo && (dateInfo.count > 0 || dateInfo.has_report));
    const hasReport = Boolean(dateInfo && dateInfo.has_report);

    let cellClass = 'relative flex flex-col items-center justify-between p-2 rounded-xl transition cursor-pointer select-none min-h-[58px] ';
    if (isSelected) {
      cellClass += 'bg-cyan-950/80 border-2 border-cyan-400 shadow-[0_0_14px_rgba(34,211,238,0.4)] ';
    } else if (isDimmed) {
      cellClass += 'bg-[#111827]/40 border border-gray-800/50 text-gray-600 hover:border-gray-700 ';
    } else {
      cellClass += 'bg-[#161f33] border border-gray-800 hover:border-cyan-500/60 hover:bg-[#1a253d] ';
    }

    return (
      <div
        key={dtStr}
        className={cellClass}
        onClick={() => onSelectDate(dtStr)}
      >
        <span className={`text-xs font-mono font-bold ${isSelected ? 'text-white' : (isDimmed ? 'text-gray-600' : 'text-gray-300')}`}>
          {dayNum}
        </span>

        {hasData ? (
          <div className="flex flex-col items-center gap-1 mt-1">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                hasReport
                  ? 'bg-emerald-400 shadow-[0_0_8px_#34d399] animate-pulse'
                  : 'bg-cyan-400 shadow-[0_0_8px_#22d3ee]'
              }`}
              title={hasReport ? `Report ready (${dateInfo.count} files)` : `Raw telemetry (${dateInfo.count} files)`}
            />
            <span className={`text-[9px] font-mono font-semibold uppercase ${hasReport ? 'text-emerald-300' : 'text-cyan-300'}`}>
              {hasReport ? 'Report' : `${dateInfo.count} files`}
            </span>
          </div>
        ) : (
          <span className="h-4" />
        )}
      </div>
    );
  }

  return (
    <div className="bg-[#0d1322] p-4 rounded-2xl border border-gray-800 space-y-3 shadow-md">
      {/* Calendar Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 px-1">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={prevMonth}
            className="p-1.5 px-3 rounded-lg bg-[#1e293b] hover:bg-gray-700 text-gray-200 text-xs font-bold transition border border-gray-700 flex items-center gap-1 cursor-pointer"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            <span>Prev</span>
          </button>

          <h3 className="text-sm font-bold text-white tracking-wide font-mono px-2 min-w-[170px] text-center">
            {MONTH_NAMES[calMonth]} {calYear}
          </h3>

          <button
            type="button"
            onClick={nextMonth}
            className="p-1.5 px-3 rounded-lg bg-[#1e293b] hover:bg-gray-700 text-gray-200 text-xs font-bold transition border border-gray-700 flex items-center gap-1 cursor-pointer"
          >
            <span>Next</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <button
          type="button"
          onClick={jumpToLatestData}
          className="text-xs px-3 py-1.5 rounded-lg bg-cyan-950/80 hover:bg-cyan-900 text-cyan-300 font-semibold border border-cyan-800 transition flex items-center gap-1.5 cursor-pointer shadow"
        >
          <Crosshair className="w-3.5 h-3.5 text-cyan-400" />
          <span>Jump to Available Telemetry Date</span>
        </button>
      </div>

      {/* Weekday headers */}
      <div className="grid grid-cols-7 gap-1 text-center text-[11px] font-bold text-gray-400 py-1.5 border-b border-gray-800 uppercase tracking-wider">
        <span className="text-rose-400">Sun</span>
        <span>Mon</span>
        <span>Tue</span>
        <span>Wed</span>
        <span>Thu</span>
        <span>Fri</span>
        <span className="text-cyan-400">Sat</span>
      </div>

      {/* Days grid */}
      <div className="grid grid-cols-7 gap-1.5 min-h-[220px]">
        {cells}
      </div>
    </div>
  );
};
