#!/usr/bin/env python3
"""
Interactive Terminal Runner for OWN Sense PREVIOUS KT-Doc Pipeline.
Executes ONLY the Previous KT-Doc Pipeline (15s Windows, 20s Baseline Warmup, Static 30/25/25/20 Weights).
"""

import os
import sys
import glob
import json
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "input_data")) if not os.path.exists("input_data") else os.path.abspath("input_data")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

from fatigue_pipeline import PreviousFatiguePipeline
from api_downloader import fetch_and_extract_rawdata
import build_dashboard


def run_pipeline_on_file(file_path: str, max_lines: int = None) -> dict:
    filename = os.path.basename(file_path)
    base_name = os.path.splitext(filename)[0]

    os.makedirs(REPORTS_DIR, exist_ok=True)
    pipeline = PreviousFatiguePipeline(
        app="construction",
        resting_hr=65.0,
        warmup_sec=20.0
    )

    def progress_cb(p_info):
        pct = p_info.get("percent", 0)
        w = p_info.get("window", 0)
        tot = p_info.get("total_windows", 0)
        print(f"\r  [Previous Pipeline] Window {w}/{tot} ({pct}%) ...", end="", flush=True)

    report = pipeline.process_file(file_path, max_lines=max_lines, progress_callback=progress_cb)
    print()
    report["filename"] = filename
    out_path = os.path.join(REPORTS_DIR, base_name + ".json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return {"filename": filename, "report_path": out_path, "summary": report.get("summary", {})}


def main():
    print("=" * 70)
    print("       OWN SENSE FATIGUE ANALYTICS - PREVIOUS KT-DOC PIPELINE")
    print("           [15s Windows | 20s Warmup | Static 30/25/25/20]")
    print("=" * 70)

    os.makedirs(DATA_DIR, exist_ok=True)
    files = sorted(glob.glob(os.path.join(DATA_DIR, "*.txt")) + glob.glob(os.path.join(DATA_DIR, "*.jsonl")))

    print("\nSelect an action / telemetry session:")
    print("-" * 70)
    print("  [0] 📥 Download new raw telemetry from API (Enter User ID, Start & End Date)")
    for idx, fpath in enumerate(files, start=1):
        fname = os.path.basename(fpath)
        size_mb = os.path.getsize(fpath) / (1024 * 1024)
        print(f"  [{idx}] {fname}  ({size_mb:.1f} MB)")
    print("-" * 70)

    choice = None
    prompt_max = len(files)
    while choice is None:
        try:
            user_input = input(f"\nEnter option (0-{prompt_max}) [Default: 1]: ").strip()
            if not user_input:
                choice = 1 if files else 0
            else:
                val = int(user_input)
                if 0 <= val <= prompt_max:
                    choice = val
                else:
                    print(f"Please enter a valid number between 0 and {prompt_max}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    if choice == 0:
        print("\n" + "=" * 70)
        print("         OWNWEARABLE CLOUD TELEMETRY API DOWNLOADER")
        print("=" * 70)
        user_id = input("\nEnter Worker / User ID (e.g. 3mSa_i) [Default: 3mSa_i]: ").strip() or "3mSa_i"
        start_date = input("Enter Start Date (YYYY-MM-DD) [Default: 2026-03-27]: ").strip() or "2026-03-27"
        end_date = input("Enter End Date (YYYY-MM-DD) [Default: 2026-03-27]: ").strip() or "2026-03-27"

        print(f"\n[*] Downloading telemetry for user '{user_id}' ({start_date} to {end_date})...")
        extracted = fetch_and_extract_rawdata(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            output_dir=DATA_DIR
        )
        if not extracted:
            print("[-] No raw telemetry files found.")
            return

        print(f"[✓] Downloaded {len(extracted)} file(s) into {DATA_DIR}")
        for fpath in extracted:
            print(f"\n[*] Processing Previous Pipeline on {os.path.basename(fpath)}...")
            run_pipeline_on_file(fpath)

    else:
        selected_file = files[choice - 1]
        print(f"\n[*] Processing Previous Pipeline on: {os.path.basename(selected_file)}")
        depth_in = input("Processing depth: [1] Quick (15k lines) [2] Full shift [Default: 2]: ").strip()
        max_lines = 15000 if depth_in == "1" else None
        res = run_pipeline_on_file(selected_file, max_lines=max_lines)

    # Rebuild dashboard
    print("\n[*] Rebuilding Previous Pipeline dashboard...")
    build_dashboard.update_dashboard()
    print("[✓] Dashboard updated successfully!")

    # Ask if user wants to open dashboard
    open_dash = input("\nDo you want to open the Previous Pipeline dashboard in your browser? (y/n) [Default: y]: ").strip().lower()
    if open_dash in ("", "y", "yes"):
        dash_path = os.path.join(BASE_DIR, "dashboard.html")
        print(f"[+] Opening: {dash_path}")
        webbrowser.open(f"file:///{dash_path}")

    print("\nDone! Previous Pipeline evaluation complete.")


if __name__ == "__main__":
    main()

