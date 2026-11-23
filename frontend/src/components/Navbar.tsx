import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Activity, BookOpen, PenSquare, Radio, Sparkles } from 'lucide-react';
import { checkBackendHealth } from '../services/api';

export const Navbar: React.FC = () => {
  const [isBackendOnline, setIsBackendOnline] = useState<boolean>(true);

  useEffect(() => {
    let mounted = true;
    const check = async () => {
      const ok = await checkBackendHealth();
      if (mounted) setIsBackendOnline(ok);
    };
    check();
    const interval = setInterval(check, 6000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="sticky top-0 z-50 bg-[#070b14]/90 backdrop-blur-md border-b border-gray-800/80 px-4 sm:px-6 lg:px-8 py-3.5 transition-all">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-3">
        {/* Brand identity */}
        <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-start">
          <NavLink to="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-500 p-0.5 shadow-lg shadow-cyan-500/20 group-hover:shadow-cyan-500/40 transition">
              <div className="w-full h-full bg-[#0d1322] rounded-[10px] flex items-center justify-center">
                <Activity className="w-5 h-5 text-cyan-400 group-hover:scale-110 transition-transform" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-base font-extrabold tracking-tight text-white font-mono">OWN<span className="text-cyan-400">Sense</span></span>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 uppercase tracking-wider font-mono">v2.0</span>
              </div>
              <p className="text-[10px] text-gray-400 font-medium">Multi-Modal Footwear Fatigue & Science Portal</p>
            </div>
          </NavLink>

          {/* Mobile Backend Status indicator */}
          <div className="sm:hidden flex items-center gap-1.5 text-[11px] font-mono px-2 py-0.5 rounded-full bg-gray-900 border border-gray-800">
            <span className={`w-2 h-2 rounded-full ${isBackendOnline ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]' : 'bg-rose-500'}`} />
            <span className="text-gray-300">{isBackendOnline ? 'Backend 8001' : 'Offline'}</span>
          </div>
        </div>

        {/* Navigation Tabs with clean URL Routing */}
        <nav className="flex items-center gap-1 sm:gap-2 w-full sm:w-auto justify-center">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition ${
                isActive
                  ? 'bg-cyan-950/80 text-cyan-300 border border-cyan-500/60 shadow-[0_0_12px_rgba(34,211,238,0.2)]'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/60'
              }`
            }
          >
            <Radio className="w-3.5 h-3.5 text-cyan-400" />
            <span>Telemetry Dashboard</span>
          </NavLink>

          <NavLink
            to="/blog"
            className={({ isActive }) =>
              `flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition ${
                isActive
                  ? 'bg-cyan-950/80 text-cyan-300 border border-cyan-500/60 shadow-[0_0_12px_rgba(34,211,238,0.2)]'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/60'
              }`
            }
          >
            <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
            <span>Science & Tech Blog</span>
            <span className="text-[9px] bg-cyan-900/60 text-cyan-300 px-1 rounded font-mono font-bold">New</span>
          </NavLink>

          <NavLink
            to="/blog/new"
            className={({ isActive }) =>
              `flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition ml-1 ${
                isActive
                  ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg'
                  : 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-md hover:shadow-cyan-500/20'
              }`
            }
          >
            <PenSquare className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Write Blog</span>
            <span className="sm:hidden">Write</span>
          </NavLink>
        </nav>

        {/* Desktop backend status */}
        <div className="hidden sm:flex items-center gap-2 text-xs font-mono">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gray-900 border border-gray-800">
            <span className={`w-2 h-2 rounded-full ${isBackendOnline ? 'bg-emerald-400 shadow-[0_0_8px_#34d399] animate-pulse' : 'bg-rose-500'}`} />
            <span className="text-gray-300 text-[11px]">{isBackendOnline ? 'API Connected (8001)' : 'Offline / Standalone'}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
