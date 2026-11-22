#!/usr/bin/env python3
"""
Secure Backend Server for OWN Sense CURRENT Production Pipeline Dashboard.
Runs on localhost:8001. Restricts execution ONLY to the Current Pipeline.
"""

import os
import sys
import glob
import json
import time
import argparse
import threading
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import urllib.parse
from typing import Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "input_data")) if not os.path.exists("input_data") else os.path.abspath("input_data")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

from fatigue_pipeline import FatiguePipeline
from api_downloader import fetch_and_extract_rawdata, validate_user_id, validate_dates
import build_dashboard

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8001
ALLOWED_HOSTNAMES = {"localhost", "127.0.0.1", "[::1]"}

job_state = {
    "state": "idle",
    "phase": "idle",
    "percent": 0,
    "message": "Ready",
    "result": None,
    "error": None
}
job_lock = threading.Lock()


def run_job_thread(params: Dict[str, Any]):
    with job_lock:
        job_state["state"] = "running"
        job_state["percent"] = 5
        job_state["phase"] = "downloading"
        job_state["message"] = "Downloading raw telemetry from Cloud API..."
        job_state["error"] = None
        job_state["result"] = None

    try:
        user_id = params.get("user_id", "3mSa_i")
        start_date = params["start_date"]
        end_date = params["end_date"]

        def dl_cb(info):
            with job_lock:
                orig_pct = info.get("percent", 0)
                job_state["percent"] = min(50, int(orig_pct * 0.5))
                job_state["message"] = info.get("message", "Downloading telemetry...")

        extracted = fetch_and_extract_rawdata(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            output_dir=DATA_DIR,
            progress_callback=dl_cb
        )

        if not extracted:
            raise RuntimeError(f"No telemetry data found for user {user_id}.")

        os.makedirs(REPORTS_DIR, exist_ok=True)
        pipeline = FatiguePipeline(
            app="construction",
            resting_hr=65.0,
            window_sec=60.0,
            warmup_sec=180.0
        )

        num_files = len(extracted)
        for idx, fpath in enumerate(extracted):
            fname = os.path.basename(fpath)
            base_name = os.path.splitext(fname)[0]

            def cur_cb(p_info):
                with job_lock:
                    pct = p_info.get("percent", 0)
                    w = p_info.get("window", 0)
                    tot = p_info.get("total_windows", 0)
                    file_prog = 50 + int((idx / num_files) * 45) + int((pct / 100) * (45 / num_files))
                    job_state["percent"] = min(95, file_prog)
                    job_state["phase"] = "evaluating"
                    job_state["message"] = f"Current Pipeline: Window {w}/{tot} ({pct}%) on {fname}"

            report = pipeline.process_file(fpath, progress_callback=cur_cb)
            report["filename"] = fname
            out_p = os.path.join(REPORTS_DIR, base_name + ".json")
            with open(out_p, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)

        build_dashboard.update_dashboard()

        with job_lock:
            job_state["state"] = "completed"
            job_state["phase"] = "complete"
            job_state["percent"] = 100
            job_state["message"] = f"Successfully evaluated {len(extracted)} session(s) using Current Pipeline!"
            job_state["result"] = {
                "primary_file": os.path.basename(extracted[0]),
                "processed_count": len(extracted)
            }

    except Exception as e:
        with job_lock:
            job_state["state"] = "error"
            job_state["phase"] = "error"
            job_state["message"] = str(e)
            job_state["error"] = str(e)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send_security_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("X-Content-Type-Options", "nosniff")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_security_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            with job_lock:
                d = json.dumps(job_state)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_security_headers()
            self.end_headers()
            self.wfile.write(d.encode("utf-8"))
            return

        if path == "/api/data":
            reports = {}
            if os.path.exists(REPORTS_DIR):
                for p in sorted(glob.glob(os.path.join(REPORTS_DIR, "*.json"))):
                    try:
                        with open(p, "r", encoding="utf-8") as rf:
                            data = json.load(rf)
                            fn = data.get("filename", os.path.basename(p).replace(".json", ".txt"))
                            reports[fn] = data
                    except Exception:
                        pass
            payload = json.dumps({"files": list(reports.keys()), "reports": reports})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_security_headers()
            self.end_headers()
            self.wfile.write(payload.encode("utf-8"))
            return

        if path in ("/", "/index.html", "/dashboard.html"):
            dash_path = os.path.join(BASE_DIR, "dashboard.html")
            if not os.path.exists(dash_path):
                build_dashboard.update_dashboard()
            with open(dash_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_security_headers()
            self.end_headers()
            self.wfile.write(content)
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/run":
            with job_lock:
                if job_state["state"] == "running":
                    self.send_response(409)
                    self.send_header("Content-Type", "application/json")
                    self.send_security_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": "A pipeline task is already actively running."}).encode("utf-8"))
                    return

            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            params = json.loads(raw.decode("utf-8"))

            t = threading.Thread(target=run_job_thread, args=(params,), daemon=True)
            t.start()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_security_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"status": "started"}).encode("utf-8"))
            return


def start_server(host=DEFAULT_HOST, port=DEFAULT_PORT, open_browser=True):
    if not os.path.exists(os.path.join(BASE_DIR, "dashboard.html")):
        build_dashboard.update_dashboard()

    server = ThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}"
    print("=" * 72)
    print("   OWN SENSE - CURRENT PRODUCTION PIPELINE SERVER")
    print("=" * 72)
    print(f"[*] Dashboard URL: {url}")
    print(f"[*] Bound Host:    {host}:{port}")
    print("=" * 72)

    if open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Server stopped.")
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Current Pipeline Dashboard Server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port (default: 8001)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser")
    args = parser.parse_args()
    start_server(port=args.port, open_browser=not args.no_browser)

