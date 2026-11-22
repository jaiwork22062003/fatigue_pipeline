#!/usr/bin/env python3
"""
Dashboard Generator for OWN Sense PREVIOUS KT-Doc Pipeline.
Creates a clean, simple, non-verbose standalone dashboard.html in previous/.
"""

import os
import glob
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
OUTPUT_HTML = os.path.join(BASE_DIR, "dashboard.html")


def update_dashboard():
    reports = {}
    if os.path.exists(REPORTS_DIR):
        for p in sorted(glob.glob(os.path.join(REPORTS_DIR, "*.json"))):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    fn = d.get("filename", os.path.basename(p).replace(".json", ".txt"))
                    reports[fn] = d
            except Exception as e:
                print(f"[!] Error reading {p}: {e}")

    bundle_json = json.dumps(reports)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OWN Sense - Previous KT-Doc Pipeline Dashboard</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    body {{
      background-color: #0b0f19;
      color: #f3f4f6;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    }}
    .badge-none {{ background-color: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }}
    .badge-info {{ background-color: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); }}
    .badge-warning {{ background-color: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }}
    .badge-urgent {{ background-color: rgba(249, 115, 22, 0.2); color: #fb923c; border: 1px solid rgba(249, 115, 22, 0.4); }}
    .badge-critical {{ background-color: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }}
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: #0b0f19; }}
    ::-webkit-scrollbar-thumb {{ background: #1e293b; border-radius: 3px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: #334155; }}
  </style>
</head>
<body class="min-h-screen p-4 md:p-6 lg:p-8">
  <div class="max-w-7xl mx-auto space-y-6">

    <!-- Header -->
    <header class="flex flex-col sm:flex-row justify-between items-start sm:items-center bg-[#111827] p-5 rounded-2xl border border-gray-800 shadow-xl gap-4">
      <div>
        <div class="flex items-center gap-2">
          <span class="px-2.5 py-0.5 text-xs font-bold rounded-md bg-amber-900/40 text-amber-300 border border-amber-700/50 uppercase tracking-wider">
            Previous KT-Doc Pipeline
          </span>
          <span id="backend-status" class="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-gray-800 text-gray-400 border border-gray-700 flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full bg-gray-500"></span>Checking Backend...
          </span>
        </div>
        <h1 class="text-2xl font-extrabold mt-1 text-white tracking-tight">Worker Fatigue Analytics</h1>
        <p class="text-xs text-gray-400 mt-0.5">15-second evaluation windows | 20s baseline warmup | Static 30/25/25/20 weights | Knowledge Transfer specification</p>
      </div>
      <div class="bg-[#1e293b] px-4 py-2.5 rounded-xl border border-amber-900/60 text-right">
        <div class="text-[10px] text-gray-400 uppercase font-semibold">Active Engine</div>
        <div class="text-amber-400 font-bold text-xs">KT-Doc Baseline Specification</div>
      </div>
    </header>

    <!-- Calendar & Worker Timeframe Controls -->
    <div class="bg-[#111827] p-5 rounded-2xl border border-gray-800 shadow-md space-y-4">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 border-b border-gray-800 pb-3">
        <div>
          <h2 class="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <span>📅 Timeframe & Worker Telemetry Selection</span>
          </h2>
          <p class="text-xs text-gray-400 mt-0.5">Enter worker ID and dates to download raw telemetry from OwnWearable Cloud API and run the Previous pipeline.</p>
        </div>
        <button id="btn-toggle-fetch" onclick="toggleFetchDrawer()" class="text-xs text-amber-400 hover:underline">
          Hide Controls ▲
        </button>
      </div>

      <div id="fetch-drawer" class="space-y-4">
        <form onsubmit="event.preventDefault(); triggerPipelineFetch();" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-3 items-end">
          <div class="lg:col-span-3 space-y-1">
            <label class="text-xs font-semibold text-gray-300 uppercase tracking-wide">Worker / User ID</label>
            <input type="text" id="input-user-id" value="3mSa_i" placeholder="e.g. 3mSa_i" required
                   class="w-full bg-[#1e293b] text-white text-xs font-medium rounded-xl px-3 py-2.5 border border-gray-700 focus:outline-none focus:border-amber-500">
          </div>

          <div class="lg:col-span-3 space-y-1">
            <label class="text-xs font-semibold text-gray-300 uppercase tracking-wide">Start Date</label>
            <input type="date" id="input-start-date" value="2026-03-27" required
                   class="w-full bg-[#1e293b] text-white text-xs font-medium rounded-xl px-3 py-2.5 border border-gray-700 focus:outline-none focus:border-amber-500">
          </div>

          <div class="lg:col-span-3 space-y-1">
            <label class="text-xs font-semibold text-gray-300 uppercase tracking-wide">End Date</label>
            <input type="date" id="input-end-date" value="2026-03-27" required
                   class="w-full bg-[#1e293b] text-white text-xs font-medium rounded-xl px-3 py-2.5 border border-gray-700 focus:outline-none focus:border-amber-500">
          </div>

          <div class="lg:col-span-3">
            <button type="submit" id="btn-fetch"
                    class="w-full py-2.5 px-4 rounded-xl font-bold text-xs uppercase tracking-wide transition flex items-center justify-center gap-2 bg-amber-600 hover:bg-amber-500 text-white shadow-lg border border-amber-400/40">
              <span id="btn-fetch-icon">📥</span>
              <span id="btn-fetch-label">Download & Run Previous Pipeline</span>
            </button>
          </div>
        </form>

        <!-- Progress Box -->
        <div id="progress-container" class="hidden bg-[#0d1322] p-4 rounded-xl border border-gray-800 space-y-2">
          <div class="flex justify-between items-center text-xs">
            <div class="flex items-center gap-2">
              <span class="inline-block w-3 h-3 border-2 border-amber-400 border-t-transparent rounded-full animate-spin"></span>
              <span id="progress-phase" class="text-amber-300 font-semibold uppercase tracking-wider text-[11px]">Connecting...</span>
            </div>
            <span id="progress-pct" class="font-mono text-amber-400 font-bold">0%</span>
          </div>
          <div class="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
            <div id="progress-bar" class="bg-amber-500 h-full w-0 transition-all duration-300 rounded-full"></div>
          </div>
          <p id="progress-msg" class="text-xs text-gray-400 font-mono">Initializing...</p>
        </div>

        <!-- Alert Notification -->
        <div id="alert-box" class="hidden p-3 rounded-xl text-xs flex justify-between items-center">
          <span id="alert-msg"></span>
          <button onclick="document.getElementById('alert-box').classList.add('hidden')" class="text-gray-400 hover:text-white">&times;</button>
        </div>
      </div>
    </div>

    <!-- Telemetry Session Selector Bar -->
    <div class="bg-[#111827] p-5 rounded-2xl border border-gray-800 shadow-md">
      <div class="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
        <div class="md:col-span-7 space-y-1">
          <label class="text-xs font-semibold text-gray-300 uppercase tracking-wide">Select Worker Telemetry Session</label>
          <select id="select-session" onchange="onSessionChange()"
                  class="w-full bg-[#1e293b] text-gray-100 text-sm font-medium rounded-xl px-3.5 py-2.5 border border-gray-700 focus:outline-none focus:border-amber-500">
          </select>
        </div>

        <div class="md:col-span-5 space-y-1">
          <label class="text-xs font-semibold text-gray-300 uppercase tracking-wide">Session Summary</label>
          <div class="text-xs text-gray-300 bg-[#1e293b] px-3.5 py-2.5 rounded-xl border border-gray-700 flex justify-between items-center">
            <span>Duration: <strong id="lbl-duration" class="text-white">--</strong></span>
            <span>Total Windows: <strong id="lbl-windows" class="text-white">--</strong></span>
            <span>App: <strong class="text-amber-400 uppercase">Construction</strong></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div id="empty-state" class="hidden bg-[#111827] p-8 rounded-2xl border border-dashed border-gray-700 text-center space-y-3">
      <div class="text-3xl">📂</div>
      <h3 class="text-base font-bold text-white">No Telemetry Reports Found</h3>
      <p class="text-xs text-gray-400 max-w-md mx-auto">
        Please use the <strong>Timeframe & Worker Telemetry Selection</strong> above to download raw shoe telemetry from the API, or place raw telemetry files in <code class="text-gray-200">input_data/</code> and run <code class="text-gray-200">python run_pipeline.py</code>.
      </p>
    </div>

    <!-- Main Content -->
    <div id="dashboard-content" class="space-y-6">

      <!-- Fatigue Metric Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-[#111827] p-4 rounded-xl border border-gray-800 shadow">
          <div class="text-[11px] text-gray-400 uppercase font-semibold">Peak Fatigue Score</div>
          <div class="text-2xl font-extrabold text-amber-400 mt-1">
            <span id="val-peak-fatigue">--</span> <span class="text-xs text-gray-400 font-normal">/ 95</span>
          </div>
          <div class="mt-2" id="badge-severity">--</div>
        </div>

        <div class="bg-[#111827] p-4 rounded-xl border border-gray-800 shadow">
          <div class="text-[11px] text-gray-400 uppercase font-semibold">Average Shift Fatigue</div>
          <div class="text-2xl font-extrabold text-white mt-1">
            <span id="val-avg-fatigue">--</span> <span class="text-xs text-gray-400 font-normal">/ 95</span>
          </div>
          <div class="text-xs text-gray-400 mt-2">Across evaluated windows</div>
        </div>

        <div class="bg-[#111827] p-4 rounded-xl border border-gray-800 shadow">
          <div class="text-[11px] text-gray-400 uppercase font-semibold">End-of-Shift Fatigue</div>
          <div class="text-2xl font-extrabold text-white mt-1">
            <span id="val-final-fatigue">--</span> <span class="text-xs text-gray-400 font-normal">/ 95</span>
          </div>
          <div class="text-xs text-gray-400 mt-2">Terminal shift state</div>
        </div>

        <div class="bg-[#111827] p-4 rounded-xl border border-gray-800 shadow">
          <div class="text-[11px] text-gray-400 uppercase font-semibold">Shift Cumulative Load</div>
          <div class="text-2xl font-extrabold text-white mt-1">
            <span id="val-cum-load">--</span>
          </div>
          <div class="text-xs text-amber-400 mt-2">Summed per-window gait load</div>
        </div>
      </div>

      <!-- Fatigue Progression Chart -->
      <div class="bg-[#111827] p-6 rounded-2xl border border-gray-800 shadow-lg space-y-4">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
          <div>
            <h2 class="text-lg font-bold text-white flex items-center gap-2">
              <span>Fatigue Progression Curve</span>
              <span class="text-xs font-normal px-2 py-0.5 bg-gray-800 text-gray-300 rounded border border-gray-700">0 - 95 Scale</span>
            </h2>
            <p class="text-xs text-gray-400 mt-0.5">Continuous fatigue curve evaluated over 15-second windows</p>
          </div>
          <div class="flex items-center gap-2 text-xs font-semibold text-amber-300">
            <span class="w-3 h-3 rounded-full bg-amber-400 inline-block"></span>
            <span>Previous KT-Doc Pipeline</span>
          </div>
        </div>

        <div class="relative w-full h-80 bg-[#0d1322] rounded-xl p-3 border border-gray-800">
          <canvas id="chart-fatigue" class="w-full h-full"></canvas>
        </div>

        <!-- Legend -->
        <div class="flex flex-wrap justify-between items-center text-[11px] text-gray-400 px-1 border-t border-gray-800 pt-2 gap-2">
          <div class="flex flex-wrap gap-3">
            <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-emerald-500"></span> NONE (&lt;20)</span>
            <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-blue-500"></span> INFO (20-40)</span>
            <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-amber-500"></span> WARNING (40-65)</span>
            <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-orange-500"></span> URGENT (65-80)</span>
            <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-rose-500"></span> CRITICAL (80-95)</span>
          </div>
          <div class="font-mono text-[11px]">Timeline: Minutes Elapsed</div>
        </div>
      </div>

      <!-- Formula Metrics (Matrices used in calculation) -->
      <div class="bg-[#111827] p-6 rounded-2xl border border-gray-800 shadow-lg space-y-4">
        <div class="border-b border-gray-800 pb-3 flex flex-col md:flex-row justify-between items-start md:items-center gap-2">
          <div>
            <h2 class="text-base font-bold text-white">Fatigue Formula Components & Telemetry Metrics</h2>
            <p class="text-xs text-gray-400 mt-0.5">Exact component scores and physical sensors used in the KT-Doc formula</p>
          </div>
          <div class="bg-gray-900 px-3 py-1.5 rounded-lg border border-amber-800/60 font-mono text-xs text-amber-300">
            Fatigue = 0.30·HR_elev + 0.25·HRV_dep + 0.25·Cad_dec + 0.20·Gait_deg
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" id="formula-metrics-container">
          <!-- Populated via JS -->
        </div>
      </div>

      <!-- Telemetry Window Log Explorer (At Last Section) -->
      <div class="bg-[#111827] p-6 rounded-2xl border border-gray-800 shadow-lg space-y-4">
        <div class="flex justify-between items-center border-b border-gray-800 pb-3">
          <div>
            <h2 class="text-base font-bold text-white">Telemetry Window Log Explorer</h2>
            <p class="text-xs text-gray-400 mt-0.5">Sequential 15-second evaluation windows for the active session</p>
          </div>
          <span class="text-xs text-gray-400 font-mono" id="log-count-label">-- windows</span>
        </div>

        <div class="overflow-x-auto max-h-80">
          <table class="w-full text-left text-xs border-collapse">
            <thead class="sticky top-0 bg-[#1e293b] text-gray-300 text-[11px] uppercase">
              <tr>
                <th class="py-2.5 px-3">Window #</th>
                <th class="py-2.5 px-3">Time</th>
                <th class="py-2.5 px-3">Heart Rate</th>
                <th class="py-2.5 px-3">Cadence</th>
                <th class="py-2.5 px-3">Stride CV</th>
                <th class="py-2.5 px-3">RMS Acc</th>
                <th class="py-2.5 px-3">Fatigue Score</th>
                <th class="py-2.5 px-3">Severity</th>
              </tr>
            </thead>
            <tbody id="session-table-body" class="divide-y divide-gray-800/60 font-mono text-gray-300 text-[11px]">
              <!-- Populated via JS -->
            </tbody>
          </table>
        </div>
      </div>

    </div>

  </div>

  <script>
    let DATA = {bundle_json};
    let currentSession = '';
    let pollTimer = null;
    const API_BASE = (window.location.protocol.startsWith('http') ? window.location.origin : 'http://localhost:8002');

    async function checkBackend() {{
      const pill = document.getElementById('backend-status');
      try {{
        const r = await fetch(`${{API_BASE}}/api/status`, {{ signal: AbortSignal.timeout(1500) }});
        if (r.ok) {{
          pill.className = "text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-700/60 flex items-center gap-1";
          pill.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>Backend Online';
          return true;
        }}
      }} catch (e) {{}}
      pill.className = "text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-950/80 text-amber-300 border border-amber-700/60 flex items-center gap-1";
      pill.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span>Server Offline';
      return false;
    }}

    function toggleFetchDrawer() {{
      const d = document.getElementById('fetch-drawer');
      const b = document.getElementById('btn-toggle-fetch');
      if (d.classList.contains('hidden')) {{
        d.classList.remove('hidden');
        b.textContent = 'Hide Controls ▲';
      }} else {{
        d.classList.add('hidden');
        b.textContent = 'Show Controls ▼';
      }}
    }}

    function showAlert(msg, isError = false) {{
      const box = document.getElementById('alert-box');
      const msgEl = document.getElementById('alert-msg');
      box.className = isError
        ? "p-3 rounded-xl text-xs flex justify-between items-center bg-rose-950/70 border border-rose-800 text-rose-300"
        : "p-3 rounded-xl text-xs flex justify-between items-center bg-emerald-950/70 border border-emerald-800 text-emerald-300";
      msgEl.innerHTML = msg;
      box.classList.remove('hidden');
    }}

    async function triggerPipelineFetch() {{
      const userId = document.getElementById('input-user-id').value.trim();
      const startDate = document.getElementById('input-start-date').value.trim();
      const endDate = document.getElementById('input-end-date').value.trim();

      if (!userId) {{ showAlert('Please enter a Worker / User ID.', true); return; }}
      if (!startDate || !endDate) {{ showAlert('Please select Start Date and End Date.', true); return; }}
      if (endDate < startDate) {{ showAlert('End Date cannot be before Start Date.', true); return; }}

      const online = await checkBackend();
      if (!online) {{
        showAlert('Backend server is offline on <code>http://localhost:8002</code>.<br>Run <code>python server.py</code> in the <strong>previous/</strong> directory.', true);
        return;
      }}

      const pBox = document.getElementById('progress-container');
      const pBar = document.getElementById('progress-bar');
      const pPct = document.getElementById('progress-pct');
      const pPhase = document.getElementById('progress-phase');
      const pMsg = document.getElementById('progress-msg');
      const btn = document.getElementById('btn-fetch');

      pBox.classList.remove('hidden');
      document.getElementById('alert-box').classList.add('hidden');
      pBar.style.width = '5%';
      pPct.textContent = '5%';
      pPhase.textContent = 'STARTING';
      pMsg.textContent = `Downloading telemetry for user ${{userId}} (${{startDate}} to ${{endDate}})...`;

      btn.disabled = true;
      btn.classList.add('opacity-50', 'cursor-not-allowed');

      try {{
        const resp = await fetch(`${{API_BASE}}/api/run`, {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ user_id: userId, start_date: startDate, end_date: endDate }})
        }});
        if (!resp.ok) {{
          const err = await resp.json();
          throw new Error(err.message || 'Failed to start execution');
        }}
        if (pollTimer) clearInterval(pollTimer);
        pollTimer = setInterval(pollJob, 1000);
      }} catch (e) {{
        showAlert(`Error: ${{e.message}}`, true);
        resetFetchBtn();
      }}
    }}

    async function pollJob() {{
      try {{
        const r = await fetch(`${{API_BASE}}/api/status`);
        if (!r.ok) return;
        const d = await r.json();

        const pBar = document.getElementById('progress-bar');
        const pPct = document.getElementById('progress-pct');
        const pPhase = document.getElementById('progress-phase');
        const pMsg = document.getElementById('progress-msg');

        const pct = d.percent || 0;
        pBar.style.width = `${{pct}}%`;
        pPct.textContent = `${{pct}}%`;
        pPhase.textContent = (d.phase || d.state).toUpperCase();
        pMsg.textContent = d.message || '';

        if (d.state === 'completed') {{
          clearInterval(pollTimer);
          pollTimer = null;
          resetFetchBtn();
          pBar.style.width = '100%';
          pPct.textContent = '100%';
          pPhase.textContent = 'COMPLETE';
          await reloadTelemetryData(d.result);
        }} else if (d.state === 'error') {{
          clearInterval(pollTimer);
          pollTimer = null;
          resetFetchBtn();
          showAlert(`Failed: ${{d.error || d.message}}`, true);
        }}
      }} catch (e) {{}}
    }}

    function resetFetchBtn() {{
      const btn = document.getElementById('btn-fetch');
      btn.disabled = false;
      btn.classList.remove('opacity-50', 'cursor-not-allowed');
    }}

    async function reloadTelemetryData(resultInfo) {{
      try {{
        const r = await fetch(`${{API_BASE}}/api/data`);
        if (!r.ok) return;
        const fresh = await r.json();
        DATA = fresh.reports || {{}};

        populateSessionDropdown();
        if (resultInfo && resultInfo.primary_file && DATA[resultInfo.primary_file]) {{
          currentSession = resultInfo.primary_file;
          document.getElementById('select-session').value = currentSession;
        }}
        render();
        showAlert(`🎉 Telemetry downloaded and Previous Pipeline evaluated successfully!`);
      }} catch (e) {{}}
    }}

    function getBadge(sev) {{
      const s = (sev || 'none').toLowerCase();
      if (s === 'none') return '<span class="badge-none px-2 py-0.5 rounded text-[10px] font-bold uppercase">NONE</span>';
      if (s === 'info') return '<span class="badge-info px-2 py-0.5 rounded text-[10px] font-bold uppercase">INFO</span>';
      if (s === 'warning') return '<span class="badge-warning px-2 py-0.5 rounded text-[10px] font-bold uppercase">WARNING</span>';
      if (s === 'urgent') return '<span class="badge-urgent px-2 py-0.5 rounded text-[10px] font-bold uppercase">URGENT</span>';
      return '<span class="badge-critical px-2 py-0.5 rounded text-[10px] font-bold uppercase">CRITICAL</span>';
    }}

    function populateSessionDropdown() {{
      const sel = document.getElementById('select-session');
      sel.innerHTML = '';
      const files = Object.keys(DATA);
      if (files.length === 0) {{
        const opt = document.createElement('option');
        opt.value = '';
        opt.textContent = '-- No Sessions Available --';
        sel.appendChild(opt);
        currentSession = '';
        return;
      }}
      files.forEach(f => {{
        const opt = document.createElement('option');
        opt.value = f;
        opt.textContent = f;
        sel.appendChild(opt);
      }});
      if (!currentSession || !DATA[currentSession]) {{
        currentSession = files[0];
      }}
      sel.value = currentSession;
    }}

    function onSessionChange() {{
      currentSession = document.getElementById('select-session').value;
      render();
    }}

    function renderFormulaMetrics(sessionData) {{
      const container = document.getElementById('formula-metrics-container');
      const wins = sessionData.windows || [];
      const validWins = wins.filter(w => w.fatigue_composite !== null);
      const lastWin = validWins.length > 0 ? validWins[validWins.length - 1] : (wins.length > 0 ? wins[wins.length - 1] : null);
      const comps = lastWin ? (lastWin.components || {{}}) : {{}};

      container.innerHTML = `
        <div class="bg-[#0d1322] p-4 rounded-xl border border-gray-800">
          <div class="flex justify-between items-center">
            <span class="text-xs font-bold text-amber-400 uppercase">1. HR Elevation</span>
            <span class="text-[10px] bg-amber-950 text-amber-300 px-1.5 py-0.5 rounded border border-amber-800 font-mono">Weight: 30%</span>
          </div>
          <div class="text-xl font-extrabold text-white mt-1.5">
            ${{comps.hr_elevation !== undefined ? comps.hr_elevation.toFixed(1) : '--'}} <span class="text-xs text-gray-400 font-normal">/ 100</span>
          </div>
          <div class="mt-2 text-[11px] text-gray-400 space-y-1 font-mono">
            <div>• Median HR: <strong class="text-white">${{lastWin && lastWin.hr_bpm ? lastWin.hr_bpm.toFixed(1) : '--'}} bpm</strong></div>
            <div>• Baseline HR: <strong class="text-white">65.0 bpm</strong></div>
            <div>• Quality Level: <strong class="text-emerald-400">${{lastWin && lastWin.hr_trustworthy ? 'Trustworthy' : 'Low'}}</strong></div>
          </div>
        </div>

        <div class="bg-[#0d1322] p-4 rounded-xl border border-gray-800">
          <div class="flex justify-between items-center">
            <span class="text-xs font-bold text-amber-400 uppercase">2. HRV Depression</span>
            <span class="text-[10px] bg-amber-950 text-amber-300 px-1.5 py-0.5 rounded border border-amber-800 font-mono">Weight: 25%</span>
          </div>
          <div class="text-xl font-extrabold text-white mt-1.5">
            ${{comps.hrv_depression !== undefined ? comps.hrv_depression.toFixed(1) : '--'}} <span class="text-xs text-gray-400 font-normal">/ 100</span>
          </div>
          <div class="mt-2 text-[11px] text-gray-400 space-y-1 font-mono">
            <div>• Current RMSSD: <strong class="text-white">${{lastWin && lastWin.rmssd_ms ? lastWin.rmssd_ms.toFixed(1) + ' ms' : 'Nulled'}}</strong></div>
            <div>• Baseline RMSSD: <strong class="text-white">${{sessionData.baseline_calibration ? sessionData.baseline_calibration.baseline_rmssd.toFixed(1) + ' ms' : '--'}}</strong></div>
            <div>• Quality Gate: <strong class="text-white">RMSSD &lt; 150 ms</strong></div>
          </div>
        </div>

        <div class="bg-[#0d1322] p-4 rounded-xl border border-gray-800">
          <div class="flex justify-between items-center">
            <span class="text-xs font-bold text-amber-400 uppercase">3. Cadence Decline</span>
            <span class="text-[10px] bg-amber-950 text-amber-300 px-1.5 py-0.5 rounded border border-amber-800 font-mono">Weight: 25%</span>
          </div>
          <div class="text-xl font-extrabold text-white mt-1.5">
            ${{comps.cadence_decline !== undefined ? comps.cadence_decline.toFixed(1) : '--'}} <span class="text-xs text-gray-400 font-normal">/ 100</span>
          </div>
          <div class="mt-2 text-[11px] text-gray-400 space-y-1 font-mono">
            <div>• Cadence: <strong class="text-white">${{lastWin && lastWin.cadence_spm ? lastWin.cadence_spm.toFixed(1) : '--'}} spm</strong></div>
            <div>• Baseline Cadence: <strong class="text-white">${{sessionData.baseline_calibration ? sessionData.baseline_calibration.baseline_cadence.toFixed(1) + ' spm' : '--'}}</strong></div>
            <div>• Decline %: <strong class="text-white">${{comps.cadence_decline !== undefined ? comps.cadence_decline.toFixed(1) + '%' : '--'}}</strong></div>
          </div>
        </div>

        <div class="bg-[#0d1322] p-4 rounded-xl border border-gray-800">
          <div class="flex justify-between items-center">
            <span class="text-xs font-bold text-amber-400 uppercase">4. Gait Degradation</span>
            <span class="text-[10px] bg-amber-950 text-amber-300 px-1.5 py-0.5 rounded border border-amber-800 font-mono">Weight: 20%</span>
          </div>
          <div class="text-xl font-extrabold text-white mt-1.5">
            ${{comps.gait_degradation !== undefined ? comps.gait_degradation.toFixed(1) : '--'}} <span class="text-xs text-gray-400 font-normal">/ 100</span>
          </div>
          <div class="mt-2 text-[11px] text-gray-400 space-y-1 font-mono">
            <div>• Stride CV: <strong class="text-white">${{lastWin && lastWin.stride_cv ? (lastWin.stride_cv * 100).toFixed(1) + '%' : '--'}}</strong></div>
            <div>• RMS Drop: <strong class="text-white">${{comps.rms_drop !== undefined ? comps.rms_drop.toFixed(1) + '%' : '--'}}</strong></div>
            <div>• IMU Raw: <strong class="text-white">${{comps.imu_fatigue_raw !== undefined ? comps.imu_fatigue_raw.toFixed(1) : '--'}}</strong></div>
          </div>
        </div>
      `;
    }}

    function drawFatigueChart(canvasId, points) {{
      const canvas = document.getElementById(canvasId);
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;

      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);

      const w = rect.width, h = rect.height;
      const padL = 45, padR = 20, padT = 20, padB = 30;

      ctx.clearRect(0, 0, w, h);

      if (points.length === 0) {{
        ctx.fillStyle = '#64748b';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No evaluation points recorded for this session', w / 2, h / 2);
        return;
      }}

      let maxX = Math.max(...points.map(p => p.x));
      if (maxX <= 0) maxX = 1;
      const maxY = 100;

      const scaleX = val => padL + (val / maxX) * (w - padL - padR);
      const scaleY = val => (h - padB) - (val / maxY) * (h - padT - padB);

      // Grid
      ctx.strokeStyle = '#1e293b';
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let i = 0; i <= 5; i++) {{
        const yVal = (i / 5) * 100;
        const yPx = scaleY(yVal);
        ctx.moveTo(padL, yPx);
        ctx.lineTo(w - padR, yPx);
        ctx.fillStyle = '#64748b';
        ctx.font = '10px monospace';
        ctx.textAlign = 'right';
        ctx.fillText(yVal.toFixed(0), padL - 8, yPx + 3);
      }}
      ctx.stroke();

      // Thresholds
      const thresholds = [
        {{ val: 20, color: 'rgba(16, 185, 129, 0.4)', label: 'NONE (20)' }},
        {{ val: 40, color: 'rgba(59, 130, 246, 0.4)', label: 'INFO (40)' }},
        {{ val: 65, color: 'rgba(245, 158, 11, 0.4)', label: 'WARNING (65)' }},
        {{ val: 80, color: 'rgba(239, 68, 68, 0.5)', label: 'URGENT (80)' }}
      ];
      thresholds.forEach(th => {{
        const yPx = scaleY(th.val);
        ctx.strokeStyle = th.color;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(padL, yPx);
        ctx.lineTo(w - padR, yPx);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = th.color;
        ctx.font = '9px sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText(th.label, padL + 6, yPx - 4);
      }});

      // X Axis
      ctx.fillStyle = '#64748b';
      ctx.font = '10px monospace';
      ctx.textAlign = 'center';
      for (let i = 0; i <= 6; i++) {{
        const xVal = (i / 6) * maxX;
        ctx.fillText(xVal.toFixed(0) + 'm', scaleX(xVal), h - 10);
      }}

      // Fill
      const grad = ctx.createLinearGradient(0, padT, 0, h - padB);
      grad.addColorStop(0, 'rgba(245, 158, 11, 0.25)');
      grad.addColorStop(1, 'rgba(245, 158, 11, 0.0)');
      ctx.beginPath();
      let started = false;
      points.forEach(pt => {{
        const xPx = scaleX(pt.x);
        const yPx = scaleY(pt.y);
        if (!started) {{ ctx.moveTo(xPx, yPx); started = true; }}
        else {{ ctx.lineTo(xPx, yPx); }}
      }});
      if (started) {{
        ctx.lineTo(scaleX(points[points.length - 1].x), h - padB);
        ctx.lineTo(scaleX(points[0].x), h - padB);
        ctx.closePath();
        ctx.fillStyle = grad;
        ctx.fill();
      }}

      // Line
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      started = false;
      points.forEach(pt => {{
        const xPx = scaleX(pt.x);
        const yPx = scaleY(pt.y);
        if (!started) {{ ctx.moveTo(xPx, yPx); started = true; }}
        else {{ ctx.lineTo(xPx, yPx); }}
      }});
      ctx.stroke();
    }}

    function renderSessionLogTable(windows) {{
      const tbody = document.getElementById('session-table-body');
      tbody.innerHTML = '';
      const countLabel = document.getElementById('log-count-label');
      countLabel.textContent = `${{windows.length}} windows recorded`;

      windows.forEach(w => {{
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-800/40 transition';
        const hrStr = w.hr_bpm ? w.hr_bpm.toFixed(1) + ' bpm' : '--';
        const cadStr = w.cadence_spm ? w.cadence_spm.toFixed(1) + ' spm' : '0.0';
        const cvStr = w.stride_cv ? (w.stride_cv * 100).toFixed(1) + '%' : '--';
        const rmsStr = w.rms_acc ? w.rms_acc.toFixed(3) + 'g' : '--';
        const scoreStr = w.fatigue_composite !== null ? w.fatigue_composite.toFixed(1) : 'Pending';

        tr.innerHTML = `
          <td class="py-2.5 px-3 text-white font-bold">#${{w.window}}</td>
          <td class="py-2.5 px-3 text-gray-400">${{w.time_sec.toFixed(0)}}s (${{(w.time_sec / 60.0).toFixed(1)}}m)</td>
          <td class="py-2.5 px-3 text-rose-300 font-semibold">${{hrStr}}</td>
          <td class="py-2.5 px-3 text-amber-300">${{cadStr}}</td>
          <td class="py-2.5 px-3 text-gray-300">${{cvStr}}</td>
          <td class="py-2.5 px-3 text-gray-400 font-mono">${{rmsStr}}</td>
          <td class="py-2.5 px-3 font-bold text-white">${{scoreStr}}</td>
          <td class="py-2.5 px-3">${{getBadge(w.severity)}}</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    function render() {{
      const emptyState = document.getElementById('empty-state');
      const content = document.getElementById('dashboard-content');

      const files = Object.keys(DATA);
      if (files.length === 0 || !currentSession || !DATA[currentSession]) {{
        emptyState.classList.remove('hidden');
        content.classList.add('hidden');
        document.getElementById('lbl-duration').textContent = '--';
        document.getElementById('lbl-windows').textContent = '--';
        return;
      }}

      emptyState.classList.add('hidden');
      content.classList.remove('hidden');

      const d = DATA[currentSession];
      const sum = d.summary || {{}};

      const durSec = d.total_duration_sec || 0;
      const durHours = (durSec / 3600.0).toFixed(1);
      document.getElementById('lbl-duration').textContent = `${{durHours}} hrs (${{(durSec / 60.0).toFixed(0)}}m)`;
      document.getElementById('lbl-windows').textContent = d.total_windows || (d.windows ? d.windows.length : 0);

      document.getElementById('val-peak-fatigue').textContent = sum.peak_fatigue !== undefined ? sum.peak_fatigue.toFixed(1) : '--';
      document.getElementById('badge-severity').innerHTML = getBadge(sum.severity);
      document.getElementById('val-avg-fatigue').textContent = sum.average_fatigue !== undefined ? sum.average_fatigue.toFixed(1) : '--';
      document.getElementById('val-final-fatigue').textContent = sum.final_fatigue !== undefined ? sum.final_fatigue.toFixed(1) : '--';
      document.getElementById('val-cum-load').textContent = d.cum_load !== undefined ? d.cum_load.toFixed(1) : '--';

      const wins = d.windows || [];
      const pts = wins
        .filter(w => w.fatigue_composite !== null)
        .map(w => ({{ x: w.time_sec / 60.0, y: w.fatigue_composite }}));
      drawFatigueChart('chart-fatigue', pts);

      renderFormulaMetrics(d);
      renderSessionLogTable(wins);
    }}

    function init() {{
      populateSessionDropdown();
      render();
      checkBackend();
      setInterval(checkBackend, 5000);
    }}

    window.addEventListener('DOMContentLoaded', init);
    window.addEventListener('resize', () => {{
      if (currentSession && DATA[currentSession]) {{
        const wins = DATA[currentSession].windows || [];
        const pts = wins
          .filter(w => w.fatigue_composite !== null)
          .map(w => ({{ x: w.time_sec / 60.0, y: w.fatigue_composite }}));
        drawFatigueChart('chart-fatigue', pts);
      }}
    }});
  </script>
</body>
</html>"""

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[✓] Previous Dashboard built -> {OUTPUT_HTML} ({len(reports)} sessions)")


if __name__ == "__main__":
    update_dashboard()

