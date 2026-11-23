#!/usr/bin/env python3
"""
Dashboard Generator for OWN Sense CURRENT Production Pipeline.
Creates a clean, simple, non-verbose standalone dashboard.html in current/.
Includes:
- Worker / User Dropdown
- Interactive Live Month Calendar with data-dot indicators
- 1-Click Report Viewer & Evaluation Runner
"""

import os
import glob
import json
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "input_data")) if not os.path.exists("input_data") else os.path.abspath("input_data")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
OUTPUT_HTML = os.path.join(BASE_DIR, "dashboard.html")


def get_user_dates_catalog():
    """
    Scans input_data/ and reports/ to extract all known users and their available dates.
    Returns list of users and a dictionary of available dates per user.
    """
    user_dates = {}
    known_users = set(["3mSa_i"])
    pattern = re.compile(r'^([A-Za-z0-9_]+)_rawdata_(\d{4}-\d{2}-\d{2})')

    # 1. Scan input_data/
    if os.path.exists(DATA_DIR):
        for fname in sorted(os.listdir(DATA_DIR)):
            fpath = os.path.join(DATA_DIR, fname)
            if not os.path.isfile(fpath):
                continue
            m = pattern.match(fname)
            if m:
                uid, dt = m.group(1), m.group(2)
                known_users.add(uid)
                if uid not in user_dates:
                    user_dates[uid] = {}
                if dt not in user_dates[uid]:
                    user_dates[uid][dt] = {"files": [], "has_report": False, "count": 0, "total_size_mb": 0.0}
                user_dates[uid][dt]["files"].append(fname)
                user_dates[uid][dt]["count"] += 1
                try:
                    user_dates[uid][dt]["total_size_mb"] = round(user_dates[uid][dt]["total_size_mb"] + os.path.getsize(fpath) / (1024 * 1024), 2)
                except Exception:
                    pass

    # 2. Scan REPORTS_DIR
    if os.path.exists(REPORTS_DIR):
        for rname in sorted(os.listdir(REPORTS_DIR)):
            if not rname.endswith(".json"):
                continue
            rpath = os.path.join(REPORTS_DIR, rname)
            m = pattern.match(rname)
            if m:
                uid, dt = m.group(1), m.group(2)
                known_users.add(uid)
                if uid not in user_dates:
                    user_dates[uid] = {}
                if dt not in user_dates[uid]:
                    user_dates[uid][dt] = {"files": [], "has_report": True, "count": 1, "total_size_mb": 0.0}
                else:
                    user_dates[uid][dt]["has_report"] = True

    for u in known_users:
        if u not in user_dates:
            user_dates[u] = {}

    return {
        "users": sorted(list(known_users)),
        "user_dates": user_dates
    }


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

    bundle_json = json.dumps(reports).replace("</script>", "<\\/script>").replace("<!--", "<\\!--")
    catalog = get_user_dates_catalog()
    bundle_catalog_json = json.dumps(catalog).replace("</script>", "<\\/script>").replace("<!--", "<\\!--")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OWN Sense - Current Production Pipeline Dashboard</title>
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
          <span class="px-2.5 py-0.5 text-xs font-bold rounded-md bg-cyan-900/40 text-cyan-300 border border-cyan-700/50 uppercase tracking-wider">
            Current Production Pipeline
          </span>
          <span id="backend-status" class="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-gray-800 text-gray-400 border border-gray-700 flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full bg-gray-500"></span>Checking Backend...
          </span>
        </div>
        <h1 class="text-2xl font-extrabold mt-1 text-white tracking-tight">Worker Fatigue Analytics</h1>
        <p class="text-xs text-gray-400 mt-0.5">60s Windows | Activity-Gated Locomotion | PPG Signal Quality Index (SQI) | Temporal Bilateral Asymmetry (ASI) | Physiological HRR Recovery</p>
      </div>
      <div class="bg-[#1e293b] px-4 py-2.5 rounded-xl border border-cyan-900/60 text-right">
        <div class="text-[10px] text-gray-400 uppercase font-semibold">Active Engine</div>
        <div class="text-cyan-400 font-bold text-xs">Current Production Model</div>
      </div>
    </header>

    <!-- Calendar & Worker Timeframe Controls -->
    <div class="bg-[#111827] p-5 rounded-2xl border border-gray-800 shadow-md space-y-4">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 border-b border-gray-800 pb-3">
        <div>
          <h2 class="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <span>📅 Worker Dropdown & Interactive Live Calendar</span>
          </h2>
          <p class="text-xs text-gray-400 mt-0.5">User select karein aur calendar me date chunein. Jin dates pe telemetry data hai waha green/cyan dot dikhega.</p>
        </div>
        <div class="flex items-center gap-3">
          <button id="btn-toggle-fetch" onclick="toggleFetchDrawer()" class="text-xs text-cyan-400 hover:underline">
            Hide Controls ▲
          </button>
        </div>
      </div>

      <div id="fetch-drawer" class="space-y-4">
        <!-- Worker Dropdown & Custom UID Bar -->
        <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-3 bg-[#0d1322] p-3.5 rounded-xl border border-gray-800">
          <div class="flex flex-wrap items-center gap-2.5 w-full lg:w-auto">
            <span class="text-xs font-bold text-cyan-400 uppercase tracking-wide flex items-center gap-1.5">
              <span>👤 Worker UID:</span>
            </span>
            <div class="relative min-w-[190px]">
              <select id="select-worker" onchange="onWorkerSelected(this.value)"
                      class="w-full bg-[#1e293b] text-white text-xs font-semibold rounded-xl px-3 py-2 border border-gray-700 focus:outline-none focus:border-cyan-400 cursor-pointer">
              </select>
            </div>

            <span class="text-xs text-gray-500 font-medium">or custom UID:</span>
            <div class="relative flex items-center">
              <input type="text" id="input-custom-uid" placeholder="Enter Custom UID (e.g. user_101)"
                     class="bg-[#1e293b] text-white text-xs font-medium rounded-xl px-3 py-2 border border-cyan-500/60 focus:outline-none focus:border-cyan-400 min-w-[200px]"
                     oninput="onCustomUidInput(this.value)">
            </div>

            <button type="button" onclick="triggerDirectApiDownload()"
                    class="py-2 px-3.5 rounded-xl font-bold text-xs uppercase tracking-wide bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-lg border border-cyan-400/50 cursor-pointer flex items-center gap-1.5 transition active:scale-95">
              <span>📥 Fetch from Florina API</span>
            </button>
          </div>

          <div class="flex items-center gap-4 text-xs text-gray-400">
            <div class="flex items-center gap-1.5">
              <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399] inline-block"></span>
              <span class="text-gray-300 font-medium">Evaluated Report Ready</span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-[0_0_8px_#22d3ee] inline-block"></span>
              <span class="text-gray-300 font-medium">Raw Telemetry Available</span>
            </div>
          </div>
        </div>

        <!-- Active Worker Status Line -->
        <div class="flex flex-wrap items-center gap-2 text-[11px] text-gray-400 font-mono px-1">
          <span>Active Worker UID:</span>
          <strong id="lbl-active-uid" class="text-cyan-300 font-bold px-2 py-0.5 rounded bg-gray-900 border border-cyan-800">3mSa_i</strong>
          <span class="text-gray-500">• Type any custom UID above or choose from dropdown. Then select a date on the calendar and click "Fetch from Florina API".</span>
        </div>

        <!-- Interactive Month Calendar -->
        <div class="bg-[#0d1322] p-4 rounded-xl border border-gray-800 space-y-3">
          <!-- Calendar Header Navigation -->
          <div class="flex justify-between items-center px-1">
            <div class="flex items-center gap-2">
              <button type="button" onclick="calPrevMonth()"
                      class="p-1.5 px-3 rounded-lg bg-[#1e293b] hover:bg-gray-700 text-gray-200 text-xs font-bold transition border border-gray-700 flex items-center gap-1">
                ◀ <span>Prev</span>
              </button>
              <h3 id="cal-month-year-label" class="text-sm font-bold text-white tracking-wide font-mono px-2 min-w-[150px] text-center">
                Loading...
              </h3>
              <button type="button" onclick="calNextMonth()"
                      class="p-1.5 px-3 rounded-lg bg-[#1e293b] hover:bg-gray-700 text-gray-200 text-xs font-bold transition border border-gray-700 flex items-center gap-1">
                <span>Next</span> ▶
              </button>
            </div>

            <div class="flex items-center gap-2">
              <button type="button" onclick="jumpToWorkerData(true)"
                      class="text-xs px-2.5 py-1.5 rounded-lg bg-cyan-950/80 hover:bg-cyan-900/80 text-cyan-300 font-semibold border border-cyan-800 transition flex items-center gap-1">
                <span>🎯 Jump to Available Data Date</span>
              </button>
            </div>
          </div>

          <!-- Weekday Headers -->
          <div class="grid grid-cols-7 gap-1 text-center text-[11px] font-bold text-gray-400 py-1 border-b border-gray-800 uppercase tracking-wider">
            <span class="text-rose-400">Sun</span>
            <span>Mon</span>
            <span>Tue</span>
            <span>Wed</span>
            <span>Thu</span>
            <span>Fri</span>
            <span class="text-cyan-400">Sat</span>
          </div>

          <!-- Calendar Days Grid -->
          <div id="cal-days-grid" class="grid grid-cols-7 gap-1.5 min-h-[220px]">
            <!-- Day cells rendered dynamically by JS -->
          </div>
        </div>

        <!-- Selected Date Action Strip -->
        <div id="cal-action-strip" class="bg-[#1e293b]/70 p-3.5 rounded-xl border border-cyan-900/60 flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
          <div class="flex flex-wrap items-center gap-2 text-xs">
            <span class="text-gray-400">Selected Date:</span>
            <span id="lbl-selected-date" class="font-bold text-white font-mono bg-gray-900/80 px-2 py-1 rounded border border-gray-700">--</span>
            <span class="text-gray-400 ml-2">Status:</span>
            <span id="lbl-date-status" class="font-semibold text-gray-300">Checking...</span>
          </div>

          <div id="cal-action-buttons" class="flex flex-wrap items-center gap-2 w-full md:w-auto">
            <!-- Buttons dynamically populated depending on date status -->
          </div>
        </div>

        <!-- Collapsible Advanced Range Drawer -->
        <details class="text-xs text-gray-400">
          <summary class="cursor-pointer hover:text-cyan-300 font-semibold transition select-none">
            ⚙ Advanced Custom Date Range (Optional)
          </summary>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 items-end pt-3">
            <div class="space-y-1">
              <label class="text-[11px] font-semibold text-gray-300 uppercase">Worker ID</label>
              <input type="text" id="input-user-id" value="3mSa_i" required
                     class="w-full bg-[#1e293b] text-white text-xs font-medium rounded-xl px-3 py-2 border border-gray-700 focus:outline-none focus:border-cyan-500">
            </div>
            <div class="space-y-1">
              <label class="text-[11px] font-semibold text-gray-300 uppercase">Start Date</label>
              <input type="date" id="input-start-date" value="2026-03-27" required
                     class="w-full bg-[#1e293b] text-white text-xs font-medium rounded-xl px-3 py-2 border border-gray-700 focus:outline-none focus:border-cyan-500">
            </div>
            <div class="space-y-1">
              <label class="text-[11px] font-semibold text-gray-300 uppercase">End Date</label>
              <input type="date" id="input-end-date" value="2026-03-27" required
                     class="w-full bg-[#1e293b] text-white text-xs font-medium rounded-xl px-3 py-2 border border-gray-700 focus:outline-none focus:border-cyan-500">
            </div>
          </div>
        </details>

        <!-- Progress Box -->
        <div id="progress-container" class="hidden bg-[#0d1322] p-4 rounded-xl border border-gray-800 space-y-2">
          <div class="flex justify-between items-center text-xs">
            <div class="flex items-center gap-2">
              <span class="inline-block w-3 h-3 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></span>
              <span id="progress-phase" class="text-cyan-300 font-semibold uppercase tracking-wider text-[11px]">Connecting...</span>
            </div>
            <span id="progress-pct" class="font-mono text-cyan-400 font-bold">0%</span>
          </div>
          <div class="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
            <div id="progress-bar" class="bg-cyan-500 h-full w-0 transition-all duration-300 rounded-full"></div>
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
                  class="w-full bg-[#1e293b] text-gray-100 text-sm font-medium rounded-xl px-3.5 py-2.5 border border-gray-700 focus:outline-none focus:border-cyan-500 cursor-pointer">
          </select>
        </div>

        <div class="md:col-span-5 space-y-1">
          <label class="text-xs font-semibold text-gray-300 uppercase tracking-wide">Session Summary</label>
          <div class="text-xs text-gray-300 bg-[#1e293b] px-3.5 py-2.5 rounded-xl border border-gray-700 flex justify-between items-center">
            <span>Duration: <strong id="lbl-duration" class="text-white">--</strong></span>
            <span>Total Windows: <strong id="lbl-windows" class="text-white">--</strong></span>
            <span>App: <strong class="text-cyan-400 uppercase">Construction</strong></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div id="empty-state" class="hidden bg-[#111827] p-8 rounded-2xl border border-dashed border-gray-700 text-center space-y-3">
      <div class="text-3xl">📂</div>
      <h3 class="text-base font-bold text-white">No Telemetry Reports Found</h3>
      <p class="text-xs text-gray-400 max-w-md mx-auto">
        Please use the <strong>Worker Dropdown & Calendar</strong> above to download raw telemetry or evaluate existing files in <code class="text-gray-200">input_data/</code>.
      </p>
    </div>

    <!-- Main Content -->
    <div id="dashboard-content" class="space-y-6">

      <!-- Fatigue Metric Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-[#111827] p-4 rounded-xl border border-gray-800 shadow">
          <div class="text-[11px] text-gray-400 uppercase font-semibold">Peak Fatigue Score</div>
          <div class="text-2xl font-extrabold text-cyan-400 mt-1">
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
          <div class="text-[11px] text-gray-400 uppercase font-semibold">Cumulative Shift Load</div>
          <div class="text-2xl font-extrabold text-white mt-1">
            <span id="val-cum-load">--</span>
          </div>
          <div class="text-xs text-emerald-400 mt-2">Gait load accumulation</div>
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
            <p class="text-xs text-gray-400 mt-0.5">Continuous fatigue curve evaluated over 60-second windows</p>
          </div>
          <div class="flex items-center gap-2 text-xs font-semibold text-cyan-300">
            <span class="w-3 h-3 rounded-full bg-cyan-400 inline-block"></span>
            <span>Current Production Pipeline</span>
          </div>
        </div>

        <div class="relative w-full h-80 bg-[#0d1322] rounded-xl p-3 border border-gray-800">
          <canvas id="chart-fatigue" class="w-full h-full cursor-crosshair"></canvas>
          <div id="chart-tooltip" class="hidden absolute pointer-events-none bg-gray-900/95 border border-cyan-500/70 text-white rounded-lg p-2.5 text-xs shadow-2xl backdrop-blur-md z-10 font-mono space-y-1"></div>
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
            <p class="text-xs text-gray-400 mt-0.5">Exact component scores and physical sensors used in the Current formula</p>
          </div>
          <div class="text-xs font-mono text-cyan-300 bg-cyan-950/60 px-2.5 py-1 rounded-lg border border-cyan-800">
            Fatigue = 0.40·Cardio + 0.35·Cadence + 0.25·Gait + Load - Recov
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4" id="formula-metrics-container">
          <!-- Populated by JS -->
        </div>
      </div>

      <!-- Evaluated 60s Windows Table -->
      <div class="bg-[#111827] p-6 rounded-2xl border border-gray-800 shadow-lg space-y-4">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-gray-800 pb-3">
          <div>
            <h2 class="text-base font-bold text-white">Continuous Window Timeline</h2>
            <p class="text-xs text-gray-400 mt-0.5">Every 60-second window evaluated with SQI, bilateral asymmetry, and composite score</p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <span class="text-xs text-gray-400 mr-1">Filter:</span>
            <div class="flex bg-[#1e293b] p-0.5 rounded-lg border border-gray-700">
              <button onclick="setTableFilter('all')" id="btn-filt-all" class="px-2.5 py-1 text-[11px] font-semibold rounded-md bg-cyan-600 text-white">All</button>
              <button onclick="setTableFilter('steady')" id="btn-filt-steady" class="px-2.5 py-1 text-[11px] font-semibold rounded-md text-gray-400 hover:text-white">Steady Walk</button>
              <button onclick="setTableFilter('intermittent')" id="btn-filt-intermittent" class="px-2.5 py-1 text-[11px] font-semibold rounded-md text-gray-400 hover:text-white">Intermittent</button>
              <button onclick="setTableFilter('stationary')" id="btn-filt-stationary" class="px-2.5 py-1 text-[11px] font-semibold rounded-md text-gray-400 hover:text-white">Stationary</button>
              <button onclick="setTableFilter('elevated')" id="btn-filt-elevated" class="px-2.5 py-1 text-[11px] font-semibold rounded-md text-gray-400 hover:text-white">Fatigue &gt; 40</button>
            </div>
            <span id="log-count-label" class="text-xs text-gray-400 font-mono ml-2">-- windows</span>
          </div>
        </div>

        <div class="overflow-x-auto max-h-96">
          <table class="w-full text-left text-xs text-gray-300">
            <thead class="text-[11px] uppercase bg-[#1e293b] text-gray-400 sticky top-0 border-b border-gray-700">
              <tr>
                <th class="py-2.5 px-3">Win #</th>
                <th class="py-2.5 px-3">Time</th>
                <th class="py-2.5 px-3">State</th>
                <th class="py-2.5 px-3">Heart Rate (PPG)</th>
                <th class="py-2.5 px-3">Cadence</th>
                <th class="py-2.5 px-3">Asymmetry (ASI)</th>
                <th class="py-2.5 px-3">Stride CV</th>
                <th class="py-2.5 px-3">Fatigue</th>
                <th class="py-2.5 px-3">Severity</th>
              </tr>
            </thead>
            <tbody id="session-table-body" class="divide-y divide-gray-800/60 font-mono">
              <!-- Populated by JS -->
            </tbody>
          </table>
        </div>
      </div>

    </div>

  </div>

  <script>
    let DATA = {bundle_json};
    let userDatesCatalog = {bundle_catalog_json};
    let selectedWorker = '3mSa_i';
    let selectedDate = '2026-03-27';
    let calYear = 2026;
    let calMonth = 2; // 0-indexed: 2 is March
    let currentSession = '';
    let pollTimer = null;
    let tableFilter = 'all';
    let currentChartPoints = [];
    const API_BASE = (window.location.protocol.startsWith('http') ? window.location.origin : 'http://localhost:8001');

    const MONTH_NAMES = [
      "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"
    ];

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

    /* =========================================================================
       WORKER DROPDOWN, CUSTOM UID & LIVE CALENDAR LOGIC
       ========================================================================= */

    function getEffectiveUid() {{
      const customEl = document.getElementById('input-custom-uid');
      if (customEl && customEl.value.trim()) {{
        return customEl.value.trim();
      }}
      return selectedWorker || (document.getElementById('input-user-id') ? document.getElementById('input-user-id').value.trim() : '3mSa_i');
    }}

    function onCustomUidInput(val) {{
      const uid = val.trim();
      const activeLbl = document.getElementById('lbl-active-uid');
      const advInput = document.getElementById('input-user-id');
      if (uid) {{
        selectedWorker = uid;
        if (activeLbl) activeLbl.textContent = uid;
        if (advInput) advInput.value = uid;
      }} else {{
        const sel = document.getElementById('select-worker');
        selectedWorker = sel ? sel.value : '3mSa_i';
        if (activeLbl) activeLbl.textContent = selectedWorker;
        if (advInput) advInput.value = selectedWorker;
      }}
      renderCalendar();
      updateDateActionStrip();
    }}

    function triggerDirectApiDownload() {{
      const uid = getEffectiveUid();
      if (!uid) {{
        showAlert('Please enter or select a Worker / User UID first.', true);
        return;
      }}
      if (!selectedDate) {{
        selectedDate = document.getElementById('input-start-date').value || '2026-03-27';
      }}
      showAlert(`Initiating Florina Cloud API download for UID: <strong>${{uid}}</strong>, Date: <strong>${{selectedDate}}</strong>...`);
      triggerPipelineFetch(true);
    }}

    function populateWorkerDropdown() {{
      const sel = document.getElementById('select-worker');
      if (!sel) return;
      sel.innerHTML = '';

      const users = (userDatesCatalog && userDatesCatalog.users && userDatesCatalog.users.length > 0)
        ? userDatesCatalog.users
        : ['3mSa_i'];

      users.forEach(u => {{
        const opt = document.createElement('option');
        opt.value = u;
        const uDates = (userDatesCatalog && userDatesCatalog.user_dates && userDatesCatalog.user_dates[u]) ? userDatesCatalog.user_dates[u] : {{}};
        const dCount = Object.keys(uDates).length;
        opt.textContent = `${{u}} (${{dCount}} telemetry date${{dCount === 1 ? '' : 's'}})`;
        sel.appendChild(opt);
      }});

      const customEl = document.getElementById('input-custom-uid');
      const hasCustom = customEl && customEl.value.trim();

      if (!hasCustom) {{
        if (users.includes(selectedWorker)) {{
          sel.value = selectedWorker;
        }} else if (users.length > 0) {{
          selectedWorker = users[0];
          sel.value = selectedWorker;
        }}
      }}

      const activeLbl = document.getElementById('lbl-active-uid');
      if (activeLbl) activeLbl.textContent = getEffectiveUid();
      document.getElementById('input-user-id').value = getEffectiveUid();
    }}

    function onWorkerSelected(wId) {{
      const customEl = document.getElementById('input-custom-uid');
      if (customEl) customEl.value = '';
      selectedWorker = wId;
      const activeLbl = document.getElementById('lbl-active-uid');
      if (activeLbl) activeLbl.textContent = wId;
      document.getElementById('input-user-id').value = wId;
      jumpToWorkerData(false);
      renderCalendar();
      updateDateActionStrip();
    }}

    function jumpToWorkerData(notify = true) {{
      const uDates = (userDatesCatalog && userDatesCatalog.user_dates && userDatesCatalog.user_dates[selectedWorker]) ? userDatesCatalog.user_dates[selectedWorker] : {{}};
      const dates = Object.keys(uDates).sort();
      if (dates.length > 0) {{
        const latest = dates[dates.length - 1]; // e.g. "2026-03-27"
        selectedDate = latest;
        const parts = latest.split('-');
        calYear = parseInt(parts[0], 10);
        calMonth = parseInt(parts[1], 10) - 1;
        document.getElementById('input-start-date').value = selectedDate;
        document.getElementById('input-end-date').value = selectedDate;
        if (notify) {{
          showAlert(`Jumped to available telemetry date: <strong>${{selectedDate}}</strong> for worker <strong>${{selectedWorker}}</strong>`);
        }}
      }}
      renderCalendar();
      updateDateActionStrip();
    }}

    function calPrevMonth() {{
      calMonth--;
      if (calMonth < 0) {{
        calMonth = 11;
        calYear--;
      }}
      renderCalendar();
    }}

    function calNextMonth() {{
      calMonth++;
      if (calMonth > 11) {{
        calMonth = 0;
        calYear++;
      }}
      renderCalendar();
    }}

    function selectDate(dtStr) {{
      selectedDate = dtStr;
      document.getElementById('input-start-date').value = dtStr;
      document.getElementById('input-end-date').value = dtStr;
      renderCalendar();
      updateDateActionStrip();
    }}

    function renderCalendar() {{
      const label = document.getElementById('cal-month-year-label');
      label.textContent = `${{MONTH_NAMES[calMonth]}} ${{calYear}}`;

      const grid = document.getElementById('cal-days-grid');
      grid.innerHTML = '';

      const firstDayIndex = new Date(calYear, calMonth, 1).getDay(); // 0 is Sunday
      const totalDays = new Date(calYear, calMonth + 1, 0).getDate();
      const prevTotalDays = new Date(calYear, calMonth, 0).getDate();

      const uDates = (userDatesCatalog && userDatesCatalog.user_dates && userDatesCatalog.user_dates[selectedWorker]) ? userDatesCatalog.user_dates[selectedWorker] : {{}};

      // Leading padding days from previous month
      for (let i = firstDayIndex - 1; i >= 0; i--) {{
        const dNum = prevTotalDays - i;
        const prevM = calMonth === 0 ? 11 : calMonth - 1;
        const prevY = calMonth === 0 ? calYear - 1 : calYear;
        const dtStr = `${{prevY}}-${{String(prevM + 1).padStart(2, '0')}}-${{String(dNum).padStart(2, '0')}}`;
        const cell = createDayCell(dNum, dtStr, true, uDates[dtStr]);
        grid.appendChild(cell);
      }}

      // Current month days
      for (let d = 1; d <= totalDays; d++) {{
        const dtStr = `${{calYear}}-${{String(calMonth + 1).padStart(2, '0')}}-${{String(d).padStart(2, '0')}}`;
        const cell = createDayCell(d, dtStr, false, uDates[dtStr]);
        grid.appendChild(cell);
      }}

      // Trailing padding days to fill 35 or 42 cells
      const currentCellCount = firstDayIndex + totalDays;
      const targetCellCount = currentCellCount > 35 ? 42 : 35;
      const trailing = targetCellCount - currentCellCount;
      for (let t = 1; t <= trailing; t++) {{
        const nextM = calMonth === 11 ? 0 : calMonth + 1;
        const nextY = calMonth === 11 ? calYear + 1 : calYear;
        const dtStr = `${{nextY}}-${{String(nextM + 1).padStart(2, '0')}}-${{String(t).padStart(2, '0')}}`;
        const cell = createDayCell(t, dtStr, true, uDates[dtStr]);
        grid.appendChild(cell);
      }}
    }}

    function createDayCell(dayNum, dtStr, isDimmed, dateInfo) {{
      const cell = document.createElement('div');
      const isSelected = (dtStr === selectedDate);
      const hasData = Boolean(dateInfo && (dateInfo.count > 0 || dateInfo.has_report));
      const hasReport = Boolean(dateInfo && dateInfo.has_report);

      let baseClasses = "relative flex flex-col items-center justify-between p-2 rounded-xl transition cursor-pointer select-none min-h-[58px] ";

      if (isSelected) {{
        baseClasses += "bg-cyan-950/80 border-2 border-cyan-400 shadow-[0_0_14px_rgba(34,211,238,0.4)] ";
      }} else if (isDimmed) {{
        baseClasses += "bg-[#111827]/40 border border-gray-800/50 text-gray-600 hover:border-gray-700 ";
      }} else {{
        baseClasses += "bg-[#161f33] border border-gray-800 hover:border-cyan-500/60 hover:bg-[#1a253d] ";
      }}

      cell.className = baseClasses;
      cell.onclick = () => selectDate(dtStr);

      // Day number
      const numSpan = document.createElement('span');
      numSpan.className = `text-xs font-mono font-bold ${{isSelected ? 'text-white' : (isDimmed ? 'text-gray-600' : 'text-gray-300')}}`;
      numSpan.textContent = dayNum;
      cell.appendChild(numSpan);

      // Visual DOT indicator for dates with data
      if (hasData) {{
        const dotContainer = document.createElement('div');
        dotContainer.className = "flex items-center justify-center gap-1 mt-1";

        const dot = document.createElement('span');
        if (hasReport) {{
          dot.className = "w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399] animate-pulse";
          dot.title = `Evaluated Report Ready (${{dateInfo.count || 1}} files)`;
        }} else {{
          dot.className = "w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-[0_0_8px_#22d3ee]";
          dot.title = `Raw Telemetry Available (${{dateInfo.count}} files)`;
        }}
        dotContainer.appendChild(dot);
        cell.appendChild(dotContainer);

        const badge = document.createElement('span');
        badge.className = `text-[9px] font-mono font-semibold uppercase ${{hasReport ? 'text-emerald-300' : 'text-cyan-300'}}`;
        badge.textContent = hasReport ? "Report" : `${{dateInfo.count}} files`;
        cell.appendChild(badge);
      }} else {{
        const empty = document.createElement('span');
        empty.className = "h-4";
        cell.appendChild(empty);
      }}

      return cell;
    }}

    function updateDateActionStrip() {{
      const lblDate = document.getElementById('lbl-selected-date');
      const lblStatus = document.getElementById('lbl-date-status');
      const btnContainer = document.getElementById('cal-action-buttons');

      lblDate.textContent = selectedDate || '--';

      const activeUid = getEffectiveUid();
      const uDates = (userDatesCatalog && userDatesCatalog.user_dates && userDatesCatalog.user_dates[activeUid]) ? userDatesCatalog.user_dates[activeUid] : {{}};
      const dateInfo = uDates[selectedDate];

      btnContainer.innerHTML = '';

      if (dateInfo && dateInfo.has_report) {{
        lblStatus.innerHTML = `<span class="text-emerald-400 font-bold flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-emerald-400"></span>Evaluated Report Ready (${{dateInfo.count || 1}} telemetry files, ~${{dateInfo.total_size_mb || 0}} MB)</span>`;

        // View Report button
        const btnView = document.createElement('button');
        btnView.type = 'button';
        btnView.className = 'py-2 px-3.5 rounded-xl font-bold text-xs uppercase tracking-wide bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg transition flex items-center gap-1.5 border border-emerald-400/40 cursor-pointer';
        btnView.innerHTML = `<span>📊 View Report for ${{activeUid}}</span>`;
        btnView.onclick = () => loadSessionForDate(activeUid, selectedDate);
        btnContainer.appendChild(btnView);

        // Re-run pipeline button
        const btnRerun = document.createElement('button');
        btnRerun.type = 'button';
        btnRerun.className = 'py-2 px-3 rounded-xl font-semibold text-xs text-gray-300 hover:text-white bg-gray-800 hover:bg-gray-700 transition border border-gray-700 flex items-center gap-1 cursor-pointer';
        btnRerun.innerHTML = '<span>⚡ Re-run Pipeline</span>';
        btnRerun.onclick = () => triggerPipelineFetch(false);
        btnContainer.appendChild(btnRerun);

      }} else if (dateInfo && dateInfo.count > 0) {{
        lblStatus.innerHTML = `<span class="text-cyan-400 font-bold flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-cyan-400"></span>Raw Telemetry Ready Locally (${{dateInfo.count}} files, ~${{dateInfo.total_size_mb || 0}} MB)</span>`;

        const btnRunLocal = document.createElement('button');
        btnRunLocal.type = 'button';
        btnRunLocal.className = 'py-2 px-3.5 rounded-xl font-bold text-xs uppercase tracking-wide bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg transition flex items-center gap-1.5 border border-cyan-400/40 cursor-pointer';
        btnRunLocal.innerHTML = `<span>⚡ Run Current Pipeline (${{activeUid}})</span>`;
        btnRunLocal.onclick = () => triggerPipelineFetch(false);
        btnContainer.appendChild(btnRunLocal);

      }} else {{
        lblStatus.innerHTML = `<span class="text-gray-400 flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-gray-600"></span>No Local Telemetry for ${{activeUid}} on this date</span>`;

        const btnDl = document.createElement('button');
        btnDl.type = 'button';
        btnDl.className = 'py-2 px-3.5 rounded-xl font-bold text-xs uppercase tracking-wide bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg transition flex items-center gap-1.5 border border-cyan-400/40 cursor-pointer';
        btnDl.innerHTML = `<span>📥 Download & Run for ${{activeUid}} (Florina API)</span>`;
        btnDl.onclick = () => triggerPipelineFetch(true);
        btnContainer.appendChild(btnDl);
      }}
    }}

    function loadSessionForDate(worker, dtStr) {{
      const prefix = `${{worker}}_rawdata_${{dtStr}}`;
      const sessions = Object.keys(DATA);
      let match = sessions.find(s => s.startsWith(prefix));
      if (!match) {{
        match = sessions.find(s => s.includes(dtStr) && s.includes(worker));
      }}
      if (match) {{
        currentSession = match;
        const sel = document.getElementById('select-session');
        if (sel) sel.value = currentSession;
        render();
        showAlert(`Loaded evaluated session: <strong>${{match}}</strong>`);
        window.scrollTo({{ top: document.getElementById('select-session').offsetTop - 30, behavior: 'smooth' }});
      }} else {{
        showAlert(`No evaluated report found yet for ${{worker}} on ${{dtStr}}. Click <strong>⚡ Run Current Pipeline</strong> to process it.`, true);
      }}
    }}

    async function fetchUserDatesFromBackend() {{
      try {{
        const r = await fetch(`${{API_BASE}}/api/users-and-dates`);
        if (r.ok) {{
          const fresh = await r.json();
          userDatesCatalog = fresh;
          populateWorkerDropdown();
          renderCalendar();
          updateDateActionStrip();
        }}
      }} catch (e) {{}}
    }}

    /* =========================================================================
       PIPELINE EXECUTION & DATA REFRESH
       ========================================================================= */

    async function triggerPipelineFetch(forceDownload = false) {{
      const userId = getEffectiveUid();
      const startDate = selectedDate || document.getElementById('input-start-date').value.trim();
      const endDate = selectedDate || document.getElementById('input-end-date').value.trim();

      if (!userId) {{ showAlert('Please select or enter a Worker / User ID.', true); return; }}
      if (!startDate || !endDate) {{ showAlert('Please select a date from the calendar.', true); return; }}
      if (endDate < startDate) {{ showAlert('End Date cannot be before Start Date.', true); return; }}

      const online = await checkBackend();
      if (!online) {{
        showAlert('Backend server is offline on <code>http://localhost:8001</code>.<br>Run <code>python server.py</code> in the <strong>current/</strong> directory.', true);
        return;
      }}

      const pBox = document.getElementById('progress-container');
      const pBar = document.getElementById('progress-bar');
      const pPct = document.getElementById('progress-pct');
      const pPhase = document.getElementById('progress-phase');
      const pMsg = document.getElementById('progress-msg');

      pBox.classList.remove('hidden');
      document.getElementById('alert-box').classList.add('hidden');
      pBar.style.width = '5%';
      pPct.textContent = '5%';
      pPhase.textContent = 'STARTING';
      pMsg.textContent = `Preparing telemetry for user ${{userId}} (${{startDate}})...`;

      try {{
        const resp = await fetch(`${{API_BASE}}/api/run`, {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ user_id: userId, start_date: startDate, end_date: endDate, force_download: forceDownload }})
        }});
        if (!resp.ok) {{
          const err = await resp.json();
          throw new Error(err.message || 'Failed to start execution');
        }}
        if (pollTimer) clearInterval(pollTimer);
        pollTimer = setInterval(pollJob, 1000);
      }} catch (e) {{
        showAlert(`Error: ${{e.message}}`, true);
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
          pBar.style.width = '100%';
          pPct.textContent = '100%';
          pPhase.textContent = 'COMPLETE';
          await reloadTelemetryData(d.result);
        }} else if (d.state === 'error') {{
          clearInterval(pollTimer);
          pollTimer = null;
          showAlert(`Failed: ${{d.error || d.message}}`, true);
        }}
      }} catch (e) {{}}
    }}

    async function reloadTelemetryData(resultInfo) {{
      try {{
        const r = await fetch(`${{API_BASE}}/api/data`);
        if (!r.ok) return;
        const fresh = await r.json();
        DATA = fresh.reports || {{}};

        await fetchUserDatesFromBackend();
        populateSessionDropdown();

        if (resultInfo && resultInfo.primary_file && DATA[resultInfo.primary_file]) {{
          currentSession = resultInfo.primary_file;
          document.getElementById('select-session').value = currentSession;
        }} else {{
          loadSessionForDate(selectedWorker, selectedDate);
        }}
        render();
        showAlert(`🎉 Current Pipeline evaluated successfully for ${{selectedWorker}} on ${{selectedDate}}!`);
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
        const d = DATA[f];
        let label = f;
        if (d) {{
          const startClk = d.session_start_clock || '';
          const endClk = d.session_end_clock || '';
          const durHrs = d.total_duration_sec ? (d.total_duration_sec / 3600.0).toFixed(1) : '';
          const winsCount = d.total_windows || (d.windows ? d.windows.length : 0);
          if (startClk && endClk) {{
            label = `${{f.replace('.txt', '')}} [Shift: ${{startClk}} - ${{endClk}} (${{durHrs}}h, ${{winsCount}}w)]`;
          }} else if (durHrs) {{
            label = `${{f.replace('.txt', '')}} [${{durHrs}}h, ${{winsCount}}w]`;
          }}
        }}
        opt.textContent = label;
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

    function renderFormulaMetrics(sessionData, targetWindow = null) {{
      const container = document.getElementById('formula-metrics-container');
      const wins = sessionData.windows || [];
      const sum = sessionData.summary || {{}};

      // Active shift references
      const activeHrs = wins.filter(w => w.hr_bpm && w.hr_trustworthy).map(w => w.hr_bpm);
      const activeCads = wins.filter(w => w.cadence_spm && w.cadence_spm > 0).map(w => w.cadence_spm);
      const activeAsym = wins.filter(w => w.temporal_asymmetry_pct !== undefined && w.temporal_asymmetry_pct > 0).map(w => w.temporal_asymmetry_pct);
      const walkingWins = wins.filter(w => (w.activity_state || '').includes('walking'));

      const isHover = Boolean(targetWindow);
      const currWin = targetWindow || (wins.length > 0 ? wins[wins.length - 1] : null);
      const comps = currWin ? (currWin.components || {{}}) : {{}};

      const sqi = (currWin && currWin.ppg_sqi) ? currWin.ppg_sqi : 'poor';
      const act = (currWin && currWin.activity_state) ? currWin.activity_state : 'stationary';
      const isWalking = act.includes('walking');
      const hrValid = (currWin && currWin.hr_trustworthy);

      // Card 1: Heart Rate (PPG)
      let hrBigDisplay = '';
      if (isHover) {{
        hrBigDisplay = (currWin && currWin.hr_bpm)
          ? `${{currWin.hr_bpm.toFixed(1)}} <span class="text-xs text-rose-300 font-normal">bpm</span>`
          : '<span class="text-gray-400 text-base font-normal">Motion Protected</span>';
      }} else {{
        const avgHrVal = (sum.active_hr_avg !== undefined && sum.active_hr_avg !== null)
          ? sum.active_hr_avg.toFixed(1)
          : (activeHrs.length > 0 ? (activeHrs.reduce((a,b)=>a+b,0)/activeHrs.length).toFixed(1) : '--');
        hrBigDisplay = (avgHrVal !== '--')
          ? `${{avgHrVal}} <span class="text-xs text-rose-300 font-normal">bpm (Active Avg)</span>`
          : '-- <span class="text-xs text-gray-400 font-normal">bpm</span>';
      }}

      // Card 2: Cadence (Dual IMU)
      let cadBigDisplay = '';
      if (isHover) {{
        cadBigDisplay = (currWin && currWin.cadence_spm > 0)
          ? `${{currWin.cadence_spm.toFixed(1)}} <span class="text-xs text-cyan-300 font-normal">spm</span>`
          : '<span class="text-gray-400 text-base font-normal">0.0 spm (Resting)</span>';
      }} else {{
        const avgCadVal = (sum.active_cadence_avg !== undefined && sum.active_cadence_avg !== null && sum.active_cadence_avg > 0)
          ? sum.active_cadence_avg.toFixed(1)
          : (activeCads.length > 0 ? (activeCads.reduce((a,b)=>a+b,0)/activeCads.length).toFixed(1) : '0.0');
        cadBigDisplay = (avgCadVal !== '0.0')
          ? `${{avgCadVal}} <span class="text-xs text-cyan-300 font-normal">spm (Walking Avg)</span>`
          : '0.0 <span class="text-xs text-gray-400 font-normal">spm</span>';
      }}

      // Card 3: Gait & Bilateral Timing
      const asymVal = isHover
        ? ((currWin && currWin.temporal_asymmetry_pct !== undefined) ? currWin.temporal_asymmetry_pct : 0.0)
        : (activeAsym.length > 0 ? (activeAsym.reduce((a,b)=>a+b,0)/activeAsym.length) : 0.0);
      const symPct = Math.max(0.0, 100.0 - asymVal);

      // Card 4: Load & Recovery
      const loadVal = sessionData.cum_load !== undefined ? sessionData.cum_load.toFixed(1) : (currWin ? currWin.cum_load : '--');
      const startClk = sessionData.session_start_clock || '';
      const endClk = sessionData.session_end_clock || '';

      container.innerHTML = `
        <div class="bg-[#0d1322] p-4 rounded-xl border border-gray-800 ${{isHover ? 'ring-1 ring-cyan-500/50' : ''}}">
          <div class="flex justify-between items-center">
            <span class="text-xs font-bold text-cyan-400 uppercase">1. Heart Rate (PPG)</span>
            <span class="text-[10px] bg-rose-950 text-rose-300 px-1.5 py-0.5 rounded border border-rose-800 font-mono">Weight: 40%</span>
          </div>
          <div class="text-xl font-extrabold text-white mt-1.5">
            ${{hrBigDisplay}}
          </div>
          <div class="mt-2 text-[11px] text-gray-400 space-y-1 font-mono">
            <div>• PPG Signal Quality: <strong class="${{sqi === 'good' ? 'text-emerald-400' : (sqi === 'fair' ? 'text-blue-400' : 'text-amber-400')}} uppercase">${{sqi}}</strong></div>
            <div>• Peak Active HR: <strong class="text-rose-300">${{sum.peak_hr || (activeHrs.length > 0 ? Math.max(...activeHrs).toFixed(1) : '--')}} bpm</strong></div>
            <div>• Cardio Strain Penalty: <strong class="text-white">${{comps.cardio_strain !== undefined ? comps.cardio_strain.toFixed(1) + ' pts' : '0.0 pts'}}</strong> <span class="text-gray-500 font-normal">(0-100)</span></div>
            <div>• %HRR / Cost: <strong class="text-white">${{comps.pct_hrr !== undefined ? comps.pct_hrr.toFixed(1) + '%' : '--'}} / ${{comps.cardiac_cost !== undefined ? comps.cardiac_cost.toFixed(2) : '--'}}</strong></div>
          </div>
        </div>

        <div class="bg-[#0d1322] p-4 rounded-xl border border-gray-800 ${{isHover ? 'ring-1 ring-cyan-500/50' : ''}}">
          <div class="flex justify-between items-center">
            <span class="text-xs font-bold text-cyan-400 uppercase">2. Cadence (Dual IMU)</span>
            <span class="text-[10px] bg-cyan-950 text-cyan-300 px-1.5 py-0.5 rounded border border-cyan-800 font-mono">${{isWalking ? 'Active: 35%' : 'Gated: 0%'}}</span>
          </div>
          <div class="text-xl font-extrabold text-white mt-1.5">
            ${{cadBigDisplay}}
          </div>
          <div class="mt-2 text-[11px] text-gray-400 space-y-1 font-mono">
            <div>• Activity State: <strong class="${{isWalking ? 'text-emerald-400' : (act === 'stationary' ? 'text-blue-400' : 'text-amber-400')}} uppercase">${{act.replace('_', ' ')}}</strong></div>
            <div>• Active Locomotion: <strong class="text-cyan-300">${{walkingWins.length}} windows (${{((walkingWins.length / Math.max(1, wins.length)) * 100).toFixed(0)}}% of shift)</strong></div>
            <div>• Peak Cadence: <strong class="text-cyan-300">${{sum.peak_cadence || (activeCads.length > 0 ? Math.max(...activeCads).toFixed(1) : '0.0')}} spm</strong></div>
            <div>• Cadence Decline Penalty: <strong class="text-white">${{comps.cadence_decline !== undefined ? comps.cadence_decline.toFixed(1) + ' pts' : '0.0 pts'}}</strong> <span class="text-gray-500 font-normal">(${{comps.cadence_decline > 0 ? comps.cadence_decline.toFixed(1) + '% decline' : 'healthy pace'}})</span></div>
          </div>
        </div>

        <div class="bg-[#0d1322] p-4 rounded-xl border border-gray-800 ${{isHover ? 'ring-1 ring-cyan-500/50' : ''}}">
          <div class="flex justify-between items-center">
            <span class="text-xs font-bold text-cyan-400 uppercase">3. Gait & Bilateral Timing</span>
            <span class="text-[10px] bg-cyan-950 text-cyan-300 px-1.5 py-0.5 rounded border border-cyan-800 font-mono">Weight: 25%</span>
          </div>
          <div class="text-xl font-extrabold text-white mt-1.5">
            ${{symPct.toFixed(1)}}% <span class="text-xs text-emerald-400 font-normal">Symmetric</span>
          </div>
          <div class="mt-2 text-[11px] text-gray-400 space-y-1 font-mono">
            <div>• Temporal Asymmetry (ASI): <strong class="${{asymVal > 15 ? 'text-amber-400' : 'text-emerald-400'}}">${{asymVal.toFixed(1)}}%</strong></div>
            <div>• Stride Variability (CV): <strong class="text-white">${{currWin && currWin.stride_cv ? (currWin.stride_cv * 100).toFixed(1) + '%' : '0.0%'}}</strong></div>
            <div>• Gait Deg Penalty: <strong class="text-white">${{comps.gait_degradation !== undefined ? comps.gait_degradation.toFixed(1) + ' pts' : '0.0 pts'}}</strong> <span class="text-gray-500 font-normal">(0-100)</span></div>
            <div>• Timing Metric: <strong class="text-white">Stride Period (TL vs TR)</strong></div>
          </div>
        </div>

        <div class="bg-[#0d1322] p-4 rounded-xl border border-emerald-800/80 ${{isHover ? 'ring-1 ring-emerald-500/50' : ''}}">
          <div class="flex justify-between items-center">
            <span class="text-xs font-bold text-emerald-400 uppercase">4. Shift Load & Recovery</span>
            <span class="text-[10px] bg-emerald-950 text-emerald-300 px-1.5 py-0.5 rounded border border-emerald-800 font-mono">Physiological</span>
          </div>
          <div class="text-xl font-extrabold text-white mt-1.5">
            ${{loadVal}} <span class="text-xs text-emerald-400 font-normal">Cum Load pts</span>
          </div>
          <div class="mt-2 text-[11px] text-gray-400 space-y-1 font-mono">
            <div>• Shift Clock Time: <strong class="text-white font-mono">${{startClk && endClk ? `${{startClk}} - ${{endClk}}` : 'Active Shift'}}</strong></div>
            <div>• Motion-Gated Drift: <strong class="text-white">+${{(Math.min(15.0, (sessionData.cum_load || 0) * 0.012)).toFixed(2)}} pts</strong></div>
            <div>• Physiological Recovery: <strong class="text-white">${{act === 'stationary' ? 'Resting (HRR-60 Gated)' : 'Locomotion Active'}}</strong></div>
            <div>• Tanaka HRmax Limit: <strong class="text-white">187 bpm (Age 30)</strong></div>
          </div>
        </div>
      `;
    }}

    function setTableFilter(filt) {{
      tableFilter = filt;
      ['all', 'steady', 'intermittent', 'stationary', 'elevated'].forEach(id => {{
        const btn = document.getElementById('btn-filt-' + id);
        if (!btn) return;
        if (id === filt) {{
          btn.className = 'px-2.5 py-1 text-[11px] font-semibold rounded-md bg-cyan-600 text-white';
        }} else {{
          btn.className = 'px-2.5 py-1 text-[11px] font-semibold rounded-md text-gray-400 hover:text-white';
        }}
      }});
      if (currentSession && DATA[currentSession]) {{
        renderSessionLogTable(DATA[currentSession].windows || []);
      }}
    }}

    function drawFatigueChart(canvasId, points, highlightIndex = -1) {{
      const canvas = document.getElementById(canvasId);
      if (!canvas) return;
      currentChartPoints = points || [];
      const ctx = canvas.getContext('2d');
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;

      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);

      const w = rect.width;
      const h = rect.height;

      ctx.clearRect(0, 0, w, h);

      const pad = {{ top: 20, right: 30, bottom: 35, left: 45 }};
      const plotW = w - pad.left - pad.right;
      const plotH = h - pad.top - pad.bottom;

      if (!points || points.length === 0) {{
        ctx.fillStyle = '#6b7280';
        ctx.font = '12px system-ui';
        ctx.textAlign = 'center';
        ctx.fillText('No evaluated fatigue data points available in this session.', w / 2, h / 2);
        return;
      }}

      const xs = points.map(p => p.x);
      const minX = 0;
      const maxX = Math.max(1, Math.max(...xs));
      const minY = 0;
      const maxY = 95;

      const toX = x => pad.left + ((x - minX) / (maxX - minX)) * plotW;
      const toY = y => pad.top + plotH - ((y - minY) / (maxY - minY)) * plotH;

      // Severity Bands
      const bands = [
        {{ y0: 0, y1: 20, color: 'rgba(16, 185, 129, 0.05)' }},
        {{ y0: 20, y1: 40, color: 'rgba(59, 130, 246, 0.05)' }},
        {{ y0: 40, y1: 65, color: 'rgba(245, 158, 11, 0.05)' }},
        {{ y0: 65, y1: 80, color: 'rgba(249, 115, 22, 0.05)' }},
        {{ y0: 80, y1: 95, color: 'rgba(239, 68, 68, 0.08)' }}
      ];
      bands.forEach(b => {{
        const bTop = toY(b.y1);
        const bBottom = toY(b.y0);
        ctx.fillStyle = b.color;
        ctx.fillRect(pad.left, bTop, plotW, bBottom - bTop);
      }});

      // Threshold reference lines
      [20, 40, 65, 80].forEach(val => {{
        ctx.beginPath();
        ctx.setLineDash([4, 4]);
        ctx.strokeStyle = '#1e293b';
        ctx.lineWidth = 1;
        ctx.moveTo(pad.left, toY(val));
        ctx.lineTo(w - pad.right, toY(val));
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.fillStyle = '#64748b';
        ctx.font = '10px monospace';
        ctx.textAlign = 'right';
        ctx.fillText(val, pad.left - 8, toY(val) + 3);
      }});

      // Fatigue Area gradient
      const grad = ctx.createLinearGradient(0, pad.top, 0, pad.top + plotH);
      grad.addColorStop(0, 'rgba(6, 182, 212, 0.35)');
      grad.addColorStop(1, 'rgba(6, 182, 212, 0.00)');

      ctx.beginPath();
      ctx.moveTo(toX(points[0].x), toY(points[0].y));
      for (let i = 1; i < points.length; i++) {{
        ctx.lineTo(toX(points[i].x), toY(points[i].y));
      }}
      ctx.lineTo(toX(points[points.length - 1].x), pad.top + plotH);
      ctx.lineTo(toX(points[0].x), pad.top + plotH);
      ctx.closePath();
      ctx.fillStyle = grad;
      ctx.fill();

      // Fatigue Curve line
      ctx.beginPath();
      ctx.moveTo(toX(points[0].x), toY(points[0].y));
      for (let i = 1; i < points.length; i++) {{
        ctx.lineTo(toX(points[i].x), toY(points[i].y));
      }}
      ctx.strokeStyle = '#22d3ee';
      ctx.lineWidth = 2.5;
      ctx.stroke();

      // Highlight point if hovered
      if (highlightIndex >= 0 && highlightIndex < points.length) {{
        const hp = points[highlightIndex];
        const hx = toX(hp.x);
        const hy = toY(hp.y);

        ctx.beginPath();
        ctx.strokeStyle = 'rgba(34, 211, 238, 0.5)';
        ctx.setLineDash([2, 2]);
        ctx.moveTo(hx, pad.top);
        ctx.lineTo(hx, pad.top + plotH);
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.beginPath();
        ctx.arc(hx, hy, 5, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = '#06b6d4';
        ctx.stroke();
      }}

      // X-axis ticks (minutes)
      const xTickCount = Math.min(8, Math.max(3, Math.floor(plotW / 80)));
      ctx.fillStyle = '#64748b';
      ctx.font = '10px monospace';
      ctx.textAlign = 'center';
      for (let i = 0; i <= xTickCount; i++) {{
        const xVal = minX + (i / xTickCount) * (maxX - minX);
        const px = toX(xVal);
        ctx.fillText(`${{xVal.toFixed(0)}}m`, px, pad.top + plotH + 16);
      }}
    }}

    function setupChartInteraction() {{
      const canvas = document.getElementById('chart-fatigue');
      const tooltip = document.getElementById('chart-tooltip');

      canvas.addEventListener('mousemove', e => {{
        if (!currentChartPoints || currentChartPoints.length === 0) return;
        const rect = canvas.getBoundingClientRect();
        const pad = {{ top: 20, right: 30, bottom: 35, left: 45 }};
        const plotW = rect.width - pad.left - pad.right;
        const mouseX = e.clientX - rect.left;

        if (mouseX < pad.left || mouseX > rect.width - pad.right) {{
          tooltip.classList.add('hidden');
          drawFatigueChart('chart-fatigue', currentChartPoints, -1);
          return;
        }}

        const maxX = Math.max(...currentChartPoints.map(p => p.x));
        const relX = (mouseX - pad.left) / plotW;
        const targetX = relX * maxX;

        let closestIdx = 0;
        let minDist = Math.abs(currentChartPoints[0].x - targetX);
        for (let i = 1; i < currentChartPoints.length; i++) {{
          const d = Math.abs(currentChartPoints[i].x - targetX);
          if (d < minDist) {{
            minDist = d;
            closestIdx = i;
          }}
        }}

        const pt = currentChartPoints[closestIdx];
        drawFatigueChart('chart-fatigue', currentChartPoints, closestIdx);

        const wObj = (currentSession && DATA[currentSession] && DATA[currentSession].windows) ? DATA[currentSession].windows[closestIdx] : null;
        const clkStr = (wObj && wObj.clock_time) ? ` (${{wObj.clock_time}})` : '';
        const actStr = (wObj && wObj.activity_state) ? wObj.activity_state.replace('_', ' ').toUpperCase() : '';

        tooltip.innerHTML = `
          <div class="text-[11px] text-cyan-300 font-bold border-b border-gray-700 pb-1">Time: ${{pt.x.toFixed(1)}} min${{clkStr}}</div>
          <div class="text-sm font-extrabold text-white mt-1">Fatigue: ${{pt.y.toFixed(1)}} <span class="text-[10px] text-gray-400 font-normal">/ 95</span></div>
          <div class="text-[10px] text-gray-400">Window #${{closestIdx + 1}} • <strong class="text-cyan-400">${{actStr}}</strong></div>
        `;
        tooltip.classList.remove('hidden');

        if (currentSession && DATA[currentSession] && wObj) {{
          renderFormulaMetrics(DATA[currentSession], wObj);
        }}

        let tipLeft = mouseX + 15;
        if (tipLeft + 160 > rect.width) tipLeft = mouseX - 170;
        tooltip.style.left = `${{tipLeft}}px`;
        tooltip.style.top = `${{Math.max(10, e.clientY - rect.top - 40)}}px`;
      }});

      canvas.addEventListener('mouseleave', () => {{
        tooltip.classList.add('hidden');
        drawFatigueChart('chart-fatigue', currentChartPoints, -1);
        if (currentSession && DATA[currentSession]) {{
          renderFormulaMetrics(DATA[currentSession], null);
        }}
      }});
    }}

    function renderSessionLogTable(windows) {{
      const tbody = document.getElementById('session-table-body');
      tbody.innerHTML = '';

      let filtered = windows;
      if (tableFilter === 'steady') {{
        filtered = windows.filter(w => (w.activity_state || w.worker_state) === 'walking_steady');
      }} else if (tableFilter === 'intermittent') {{
        filtered = windows.filter(w => (w.activity_state || w.worker_state) === 'walking_intermittent');
      }} else if (tableFilter === 'stationary') {{
        filtered = windows.filter(w => (w.activity_state || w.worker_state) === 'stationary');
      }} else if (tableFilter === 'elevated') {{
        filtered = windows.filter(w => (w.fatigue_composite !== null && w.fatigue_composite >= 40.0));
      }}

      const countLabel = document.getElementById('log-count-label');
      countLabel.textContent = `${{filtered.length}} of ${{windows.length}} windows`;

      if (filtered.length === 0) {{
        const tr = document.createElement('tr');
        tr.innerHTML = '<td colspan="9" class="py-6 text-center text-gray-500 italic">No windows matching the current filter criteria.</td>';
        tbody.appendChild(tr);
        return;
      }}

      filtered.forEach(w => {{
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-800/40 transition';
        const state = (w.activity_state || w.worker_state || 'stationary').toLowerCase();
        let stateBadge = '';
        if (state === 'walking_steady') {{
          stateBadge = '<span class="px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-700/60 text-[10px] font-bold">STEADY WALK</span>';
        }} else if (state === 'walking_intermittent') {{
          stateBadge = '<span class="px-2 py-0.5 rounded bg-blue-950/80 text-blue-300 border border-blue-700/60 text-[10px] font-bold">INTERMITTENT</span>';
        }} else if (state === 'running') {{
          stateBadge = '<span class="px-2 py-0.5 rounded bg-purple-950/80 text-purple-300 border border-purple-700/60 text-[10px] font-bold">RUNNING</span>';
        }} else if (state === 'stationary') {{
          stateBadge = '<span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[10px] font-bold">STATIONARY</span>';
        }} else if (state === 'idle' || state === 'disconnected') {{
          stateBadge = '<span class="px-2 py-0.5 rounded bg-gray-900 text-gray-400 border border-gray-800 text-[10px] font-bold">IDLE / OFF</span>';
        }} else {{
          stateBadge = '<span class="px-2 py-0.5 rounded bg-gray-800 text-gray-400 text-[10px] font-bold">WARMUP</span>';
        }}

        let hrHtml = '';
        if (w.hr_bpm && w.hr_trustworthy) {{
          hrHtml = `<span class="text-rose-300 font-bold">${{w.hr_bpm.toFixed(1)}} bpm</span> <span class="text-[9px] text-emerald-400 bg-emerald-950/60 px-1 py-0.2 rounded border border-emerald-800 uppercase font-sans">${{w.ppg_sqi || 'GOOD'}}</span>`;
        }} else if (w.hr_bpm) {{
          hrHtml = `<span class="text-amber-400 font-mono">${{w.hr_bpm.toFixed(1)}} bpm</span> <span class="text-[9px] text-amber-300 bg-amber-950/60 px-1 py-0.2 rounded border border-amber-800 uppercase font-sans">${{w.ppg_sqi || 'POOR'}}</span>`;
        }} else {{
          hrHtml = `<span class="text-gray-500 italic">Suppressed (Motion)</span>`;
        }}

        const cadStr = (w.cadence_spm !== undefined && w.cadence_spm !== null && w.cadence_spm > 0)
          ? `<span class="text-cyan-300 font-bold">${{w.cadence_spm.toFixed(1)}} spm</span>`
          : '<span class="text-gray-400 font-mono">0.0 spm</span>';
        const asymStr = (w.temporal_asymmetry_pct !== undefined && w.temporal_asymmetry_pct !== null) ? `${{w.temporal_asymmetry_pct.toFixed(1)}}%` : '0.0%';
        const cvStr = w.stride_cv ? `${{(w.stride_cv * 100).toFixed(1)}}%` : '0.0%';
        const scoreStr = (w.fatigue_composite !== null && w.fatigue_composite !== undefined) ? w.fatigue_composite.toFixed(1) : 'Warmup';

        tr.innerHTML = `
          <td class="py-2.5 px-3 text-white font-bold">#${{w.window}}</td>
          <td class="py-2.5 px-3 text-gray-300 font-mono">
            ${{w.clock_time ? `<div class="text-white font-bold text-xs">${{w.clock_time}}</div>` : ''}}
            <div class="text-[10px] text-gray-500">${{w.time_sec.toFixed(0)}}s (${{(w.time_sec / 60.0).toFixed(1)}}m)</div>
          </td>
          <td class="py-2.5 px-3 font-semibold">${{stateBadge}}</td>
          <td class="py-2.5 px-3">${{hrHtml}}</td>
          <td class="py-2.5 px-3 text-cyan-300 font-mono">${{cadStr}}</td>
          <td class="py-2.5 px-3 text-gray-300 font-mono">${{asymStr}}</td>
          <td class="py-2.5 px-3 text-gray-300 font-mono">${{cvStr}}</td>
          <td class="py-2.5 px-3 font-bold text-white font-mono">${{scoreStr}}</td>
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
      const startClk = d.session_start_clock || '';
      const endClk = d.session_end_clock || '';
      const timeSpanStr = (startClk && endClk) ? ` | Clock: ${{startClk}} - ${{endClk}}` : '';
      document.getElementById('lbl-duration').textContent = `${{durHours}} hrs (${{(durSec / 60.0).toFixed(0)}}m)${{timeSpanStr}}`;
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
      populateWorkerDropdown();
      jumpToWorkerData(false);
      renderCalendar();
      updateDateActionStrip();

      populateSessionDropdown();
      render();
      setupChartInteraction();
      checkBackend();
      fetchUserDatesFromBackend();
      setInterval(checkBackend, 5000);
      setInterval(fetchUserDatesFromBackend, 10000);
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

    print(f"[✓] Current Dashboard built -> {OUTPUT_HTML} ({len(reports)} sessions)")


if __name__ == "__main__":
    update_dashboard()
