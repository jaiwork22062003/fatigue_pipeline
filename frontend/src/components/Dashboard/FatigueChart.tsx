import React, { useRef, useEffect, useState } from 'react';
import { EvaluationWindow, SessionReport } from '../../types';

interface FatigueChartProps {
  session: SessionReport;
  onHoverWindow: (win: EvaluationWindow | null) => void;
}

export const FatigueChart: React.FC<FatigueChartProps> = ({ session, onHoverWindow }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [tooltip, setTooltip] = useState<{
    visible: boolean;
    x: number;
    y: number;
    minute: number;
    clockTime?: string;
    fatigue: number;
    windowNum: number;
    activity: string;
  } | null>(null);

  const wins = session.windows || [];
  const points = wins
    .filter((w) => w.fatigue_composite !== null && w.fatigue_composite !== undefined)
    .map((w, idx) => ({
      x: w.time_sec / 60.0,
      y: w.fatigue_composite as number,
      win: w,
      idx
    }));

  const [highlightIdx, setHighlightIdx] = useState<number>(-1);

  // Draw chart
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;

    ctx.clearRect(0, 0, w, h);

    const pad = { top: 20, right: 30, bottom: 35, left: 45 };
    const plotW = w - pad.left - pad.right;
    const plotH = h - pad.top - pad.bottom;

    if (points.length === 0) {
      ctx.fillStyle = '#6b7280';
      ctx.font = '12px system-ui';
      ctx.textAlign = 'center';
      ctx.fillText('No evaluated fatigue data points available in this session.', w / 2, h / 2);
      return;
    }

    const xs = points.map((p) => p.x);
    const minX = 0;
    const maxX = Math.max(1, Math.max(...xs));
    const minY = 0;
    const maxY = 95;

    const toX = (x: number) => pad.left + ((x - minX) / (maxX - minX)) * plotW;
    const toY = (y: number) => pad.top + plotH - ((y - minY) / (maxY - minY)) * plotH;

    // Severity bands
    const bands = [
      { y0: 0, y1: 20, color: 'rgba(16, 185, 129, 0.05)' },
      { y0: 20, y1: 40, color: 'rgba(59, 130, 246, 0.05)' },
      { y0: 40, y1: 65, color: 'rgba(245, 158, 11, 0.05)' },
      { y0: 65, y1: 80, color: 'rgba(249, 115, 22, 0.05)' },
      { y0: 80, y1: 95, color: 'rgba(239, 68, 68, 0.08)' }
    ];
    bands.forEach((b) => {
      const bTop = toY(b.y1);
      const bBottom = toY(b.y0);
      ctx.fillStyle = b.color;
      ctx.fillRect(pad.left, bTop, plotW, bBottom - bTop);
    });

    // Grid lines & Y-axis labels
    ctx.strokeStyle = 'rgba(75, 85, 99, 0.2)';
    ctx.lineWidth = 1;
    ctx.fillStyle = '#64748b';
    ctx.font = '10px monospace';
    ctx.textAlign = 'right';

    [0, 20, 40, 65, 80, 95].forEach((yVal) => {
      const py = toY(yVal);
      ctx.beginPath();
      ctx.moveTo(pad.left, py);
      ctx.lineTo(pad.left + plotW, py);
      ctx.stroke();
      ctx.fillText(String(yVal), pad.left - 8, py + 3);
    });

    // Area fill gradient under curve
    const areaGrad = ctx.createLinearGradient(0, pad.top, 0, pad.top + plotH);
    areaGrad.addColorStop(0, 'rgba(34, 211, 238, 0.25)');
    areaGrad.addColorStop(1, 'rgba(34, 211, 238, 0.0)');

    ctx.beginPath();
    ctx.moveTo(toX(points[0].x), toY(points[0].y));
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(toX(points[i].x), toY(points[i].y));
    }
    ctx.lineTo(toX(points[points.length - 1].x), pad.top + plotH);
    ctx.lineTo(toX(points[0].x), pad.top + plotH);
    ctx.closePath();
    ctx.fillStyle = areaGrad;
    ctx.fill();

    // Fatigue curve line
    ctx.beginPath();
    ctx.moveTo(toX(points[0].x), toY(points[0].y));
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(toX(points[i].x), toY(points[i].y));
    }
    ctx.strokeStyle = '#22d3ee';
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // Hover highlight crosshair
    if (highlightIdx >= 0 && highlightIdx < points.length) {
      const hp = points[highlightIdx];
      const hx = toX(hp.x);
      const hy = toY(hp.y);

      ctx.beginPath();
      ctx.strokeStyle = 'rgba(34, 211, 238, 0.6)';
      ctx.setLineDash([3, 3]);
      ctx.moveTo(hx, pad.top);
      ctx.lineTo(hx, pad.top + plotH);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.beginPath();
      ctx.arc(hx, hy, 5.5, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.fill();
      ctx.lineWidth = 2.5;
      ctx.strokeStyle = '#06b6d4';
      ctx.stroke();
    }

    // X-axis ticks (minutes)
    const xTickCount = Math.min(8, Math.max(3, Math.floor(plotW / 80)));
    ctx.fillStyle = '#64748b';
    ctx.font = '10px monospace';
    ctx.textAlign = 'center';
    for (let i = 0; i <= xTickCount; i++) {
      const xVal = minX + (i / xTickCount) * (maxX - minX);
      const px = toX(xVal);
      ctx.fillText(`${xVal.toFixed(0)}m`, px, pad.top + plotH + 16);
    }
  }, [points, highlightIdx]);

  // Handle mouse move
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas || points.length === 0) return;
    const rect = canvas.getBoundingClientRect();
    const pad = { top: 20, right: 30, bottom: 35, left: 45 };
    const plotW = rect.width - pad.left - pad.right;
    const mouseX = e.clientX - rect.left;

    if (mouseX < pad.left || mouseX > rect.width - pad.right) {
      setTooltip(null);
      setHighlightIdx(-1);
      onHoverWindow(null);
      return;
    }

    const maxX = Math.max(...points.map((p) => p.x));
    const relX = (mouseX - pad.left) / plotW;
    const targetX = relX * maxX;

    let closestIdx = 0;
    let minDist = Math.abs(points[0].x - targetX);
    for (let i = 1; i < points.length; i++) {
      const d = Math.abs(points[i].x - targetX);
      if (d < minDist) {
        minDist = d;
        closestIdx = i;
      }
    }

    setHighlightIdx(closestIdx);
    const pt = points[closestIdx];
    const win = pt.win;
    onHoverWindow(win);

    let tipLeft = mouseX + 15;
    if (tipLeft + 170 > rect.width) tipLeft = mouseX - 180;

    setTooltip({
      visible: true,
      x: tipLeft,
      y: Math.max(10, e.clientY - rect.top - 40),
      minute: pt.x,
      clockTime: win.clock_time,
      fatigue: pt.y,
      windowNum: closestIdx + 1,
      activity: win.activity_state || 'stationary'
    });
  };

  const handleMouseLeave = () => {
    setTooltip(null);
    setHighlightIdx(-1);
    onHoverWindow(null);
  };

  return (
    <div className="bg-[#0d1322] p-5 rounded-2xl border border-gray-800 shadow-md space-y-4">
      {/* Chart Title & Severity Zone Legend */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div>
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <span>📈 Multi-Modal Fatigue Progression (0 - 95 Scale)</span>
          </h3>
          <p className="text-xs text-gray-400 mt-0.5">
            Real-time composite curve evaluated across 60s windows with activity-gated dynamic weighting.
          </p>
        </div>

        {/* Severity scale legend */}
        <div className="flex flex-wrap items-center gap-2 text-[10px] font-mono">
          <span className="px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800">
            0-20 None
          </span>
          <span className="px-2 py-0.5 rounded bg-blue-950/60 text-blue-400 border border-blue-800">
            20-40 Info
          </span>
          <span className="px-2 py-0.5 rounded bg-amber-950/60 text-amber-400 border border-amber-800">
            40-65 Warning
          </span>
          <span className="px-2 py-0.5 rounded bg-orange-950/60 text-orange-400 border border-orange-800">
            65-80 Urgent
          </span>
          <span className="px-2 py-0.5 rounded bg-rose-950/60 text-rose-400 border border-rose-800">
            80-95 Critical
          </span>
        </div>
      </div>

      {/* Canvas chart container */}
      <div ref={containerRef} className="relative w-full h-[260px] select-none">
        <canvas
          ref={canvasRef}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          className="w-full h-full cursor-crosshair rounded-xl bg-[#090d19]/60 border border-gray-800/80"
        />

        {/* Dynamic Tooltip */}
        {tooltip && tooltip.visible && (
          <div
            className="absolute z-20 pointer-events-none bg-[#090d19]/95 text-white p-2.5 rounded-xl border border-cyan-500/60 shadow-xl backdrop-blur-md text-xs font-mono min-w-[155px]"
            style={{ left: `${tooltip.x}px`, top: `${tooltip.y}px` }}
          >
            <div className="text-[11px] text-cyan-300 font-bold border-b border-gray-700/80 pb-1">
              Time: {tooltip.minute.toFixed(1)}m {tooltip.clockTime ? `(${tooltip.clockTime})` : ''}
            </div>
            <div className="text-sm font-extrabold text-white mt-1">
              Fatigue: {tooltip.fatigue.toFixed(1)}{' '}
              <span className="text-[10px] text-gray-400 font-normal">/ 95</span>
            </div>
            <div className="text-[10px] text-gray-400 mt-0.5">
              Window #{tooltip.windowNum} • <strong className="text-cyan-400 uppercase">{tooltip.activity.replace('_', ' ')}</strong>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
