#!/usr/bin/env python3
"""
Previous Pipeline (Knowledge Transfer Document Specification)
Implements the multi-modal fatigue evaluation engine exactly as documented
in the OWN Sense Knowledge Transfer specification (Section 11, Section 7, Section 17).

Formulas & Architecture (Doc Specification):
- Construction Fatigue Composite:
    fatigue_composite = 0.30 * hr_elevation + 0.25 * hrv_depression + 0.25 * cadence_decline + 0.20 * gait_degradation
- Capped at 95.
- Severity levels: none (<20), info (20-40), warning (40-65), urgent (65-80), critical (80-95).
- Quality gates:
    - hr_trustworthy: False when |median_ppg - median_bcg| > 20 bpm or unphysiological (<40 or >200 bpm).
    - hrv_trustworthy: False when RMSSD > 150 ms (RMSSD and SDNN are nulled when HRV is not trustworthy).
    - hr_quality_level: "ok" if both HR and HRV are trustworthy; otherwise "low".
- Warmup / baseline pending:
    - First ~20 seconds of a session are baseline_pending and return None.
- Exposed component keys:
    hr_elevation, hrv_depression, cadence_decline, gait_degradation, rms_drop, imu_fatigue_raw.
- Cumulative shift load:
    Summed per-window gait cum_load across shift.
"""

import os
import glob
import json
import argparse
import datetime
import numpy as np
from scipy import signal
from typing import Dict, Any, List, Optional, Tuple, Callable


class PreviousFatiguePipeline:
    def __init__(
        self,
        app: str = "construction",
        resting_hr: float = 65.0,
        age: int = 30,
        window_sec: float = 15.0,
        warmup_sec: float = 20.0,
    ):
        self.app = app.lower()
        self.resting_hr = resting_hr
        self.age = age
        self.window_sec = window_sec
        self.warmup_sec = warmup_sec
        self.tanaka_hrmax = 208.0 - 0.7 * self.age

        # State tracking
        self.baseline_established = False
        self.baseline_rmssd: Optional[float] = None
        self.baseline_cadence: Optional[float] = None
        self.baseline_rms: Optional[float] = None
        self.baseline_stride_cv: Optional[float] = None

        self.cum_load: float = 0.0

    def parse_records(self, file_path: str, max_lines: Optional[int] = None) -> Tuple[List[Tuple], List[Tuple]]:
        """
        Parses raw JSONL data into chronologically sorted PPG and IMU time-series chunks.
        Uses two-pass global timestamp normalization to ensure immunity to out-of-order initial packets.
        """
        raw_ppg: List[Tuple[float, float, float]] = []
        raw_imu: List[Tuple[float, float, float, float, float, float, float, str]] = []

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for idx, line in enumerate(f):
                if max_lines and idx >= max_lines:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except Exception:
                    continue

                topic = record.get("topic", "")
                content = record.get("content", {})
                if isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except Exception:
                        content = {}

                t_type = content.get("T", "")

                # Extract timestamp (handles ISO string or numeric epoch)
                ts_val = content.get("timestamp")
                if not ts_val and "Data" in content and isinstance(content["Data"], dict):
                    ts_val = content["Data"].get("timestamp")

                if not ts_val:
                    continue

                t_sec = None
                if isinstance(ts_val, (int, float)):
                    t_sec = float(ts_val) / 1000.0 if ts_val > 1e11 else float(ts_val)
                elif isinstance(ts_val, str):
                    try:
                        dt = datetime.datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
                        t_sec = dt.timestamp()
                    except Exception:
                        try:
                            f_val = float(ts_val)
                            t_sec = f_val / 1000.0 if f_val > 1e11 else f_val
                        except Exception:
                            continue

                if t_sec is None:
                    continue

                # Parse PPG
                if t_type == "PG" or (topic == "PPG" and "IR" in content):
                    ir_arr = content.get("IR", [])
                    rd_arr = content.get("RD", [])
                    n = min(len(ir_arr), len(rd_arr))
                    if n > 0:
                        packet_dt = 0.04  # 25 Hz nominal sample interval
                        for j in range(n):
                            try:
                                ir_v = float(ir_arr[j])
                                rd_v = float(rd_arr[j])
                                raw_ppg.append((t_sec + j * packet_dt, ir_v, rd_v))
                            except (ValueError, TypeError, IndexError):
                                continue

                # Parse Left Foot / Board IMU
                elif t_type == "BL" or (topic == "PPG" and "AC" in content):
                    ac = content.get("AC", [])
                    gy = content.get("GY", [])
                    n_triplets = min(len(ac) // 3, len(gy) // 3)
                    for j in range(n_triplets):
                        try:
                            t_sub = t_sec + j * 0.01
                            ax, ay, az = float(ac[j*3]), float(ac[j*3+1]), float(ac[j*3+2])
                            gx, gy_val, gz = float(gy[j*3]), float(gy[j*3+1]), float(gy[j*3+2])
                            raw_imu.append((t_sub, ax, ay, az, gx, gy_val, gz, "left"))
                        except (ValueError, TypeError, IndexError):
                            continue

                # Parse Right Foot IMU
                elif t_type == "BR" or topic == "BPST_RIGHT":
                    data = content.get("Data", {}) if isinstance(content.get("Data"), dict) else content
                    ac = data.get("AC", [])
                    gy = data.get("GY", [])
                    n_triplets = min(len(ac) // 3, len(gy) // 3)
                    for j in range(n_triplets):
                        try:
                            t_sub = t_sec + j * 0.01
                            ax, ay, az = float(ac[j*3]), float(ac[j*3+1]), float(ac[j*3+2])
                            gx, gy_val, gz = float(gy[j*3]), float(gy[j*3+1]), float(gy[j*3+2])
                            raw_imu.append((t_sub, ax, ay, az, gx, gy_val, gz, "right"))
                        except (ValueError, TypeError, IndexError):
                            continue

        if not raw_ppg and not raw_imu:
            return [], []

        # Find global minimum timestamp across all valid records to avoid out-of-order startup skew
        all_timestamps = [x[0] for x in raw_ppg] + [x[0] for x in raw_imu]
        min_start_time = min(all_timestamps)

        ppg_samples = [(max(0.0, x[0] - min_start_time), x[1], x[2]) for x in raw_ppg]
        imu_samples = [(max(0.0, x[0] - min_start_time), x[1], x[2], x[3], x[4], x[5], x[6], x[7]) for x in raw_imu]

        # Guarantee strict chronological sorting
        ppg_samples.sort(key=lambda x: x[0])
        imu_samples.sort(key=lambda x: x[0])

        return ppg_samples, imu_samples

    def extract_hr_hrv(self, ppg_window: List[Tuple[float, float, float]]) -> Dict[str, Any]:
        """
        Extracts Heart Rate (PPG/BCG) and Heart Rate Variability (RMSSD, SDNN)
        with quality gating as specified in KT Doc Section 7 & 17:
        - Tanaka HRmax: 208 - 0.7 * age
        - HR trustworthy: False when |median_ppg - median_bcg| > 20 bpm
        - HRV trustworthy: False when RMSSD > 150 ms
        - RMSSD and SDNN are nulled when HRV is not trustworthy
        - HR quality level: 'ok' when both HR and HRV trustworthy; otherwise 'low'
        """
        if len(ppg_window) < 50:
            return {
                "median_hr_ppg": None,
                "median_hr_bcg": None,
                "hr_trustworthy": False,
                "rmssd_ms": None,
                "sdnn_ms": None,
                "raw_rmssd": None,
                "hrv_trustworthy": False,
                "hr_quality_level": "low",
                "hr_quality_reasons": ["insufficient_samples"]
            }

        times = np.array([x[0] for x in ppg_window])
        ir = np.array([x[1] for x in ppg_window])
        rd = np.array([x[2] for x in ppg_window])

        # Interpolate onto uniform 50 Hz grid
        fs = 50.0
        t0, t1 = times[0], times[-1]
        if t1 - t0 < 1.0:
            return {
                "median_hr_ppg": None,
                "median_hr_bcg": None,
                "hr_trustworthy": False,
                "rmssd_ms": None,
                "sdnn_ms": None,
                "raw_rmssd": None,
                "hrv_trustworthy": False,
                "hr_quality_level": "low",
                "hr_quality_reasons": ["short_window"]
            }

        t_grid = np.arange(t0, t1, 1.0 / fs)
        ir_interp = np.interp(t_grid, times, ir)
        rd_interp = np.interp(t_grid, times, rd)

        # 2nd-order Butterworth bandpass (0.7 Hz to 3.5 Hz = 42 to 210 bpm)
        nyq = 0.5 * fs
        b, a = signal.butter(2, [0.7 / nyq, 3.5 / nyq], btype="bandpass")
        try:
            ir_filt = signal.filtfilt(b, a, ir_interp)
            rd_filt = signal.filtfilt(b, a, rd_interp)
        except Exception:
            return {
                "median_hr_ppg": None,
                "median_hr_bcg": None,
                "hr_trustworthy": False,
                "rmssd_ms": None,
                "sdnn_ms": None,
                "raw_rmssd": None,
                "hrv_trustworthy": False,
                "hr_quality_level": "low",
                "hr_quality_reasons": ["filter_failed"]
            }

        # Peak detection for PPG (IR)
        dist = int(fs * 0.35)  # min 0.35s refractory interval
        prom_ir = max(0.4 * np.std(ir_filt), 1e-4)
        peaks_ir, _ = signal.find_peaks(ir_filt, distance=dist, prominence=prom_ir)

        # Peak detection for BCG (Red)
        prom_rd = max(0.4 * np.std(rd_filt), 1e-4)
        peaks_rd, _ = signal.find_peaks(rd_filt, distance=dist, prominence=prom_rd)

        hr_ppg = None
        rmssd = None
        sdnn = None
        if len(peaks_ir) > 1:
            rr_intervals = np.diff(t_grid[peaks_ir])
            valid_rr = rr_intervals[(rr_intervals >= 0.28) & (rr_intervals <= 1.5)]  # 40-214 bpm
            if len(valid_rr) > 0:
                hr_ppg = float(np.median(60.0 / valid_rr))
                if len(valid_rr) > 1:
                    diff_rr = np.diff(valid_rr * 1000.0)  # in ms
                    rmssd = float(np.sqrt(np.mean(diff_rr ** 2)))
                    sdnn = float(np.std(valid_rr * 1000.0))

        hr_bcg = None
        if len(peaks_rd) > 1:
            rr_rd = np.diff(t_grid[peaks_rd])
            valid_rr_rd = rr_rd[(rr_rd >= 0.28) & (rr_rd <= 1.5)]
            if len(valid_rr_rd) > 0:
                hr_bcg = float(np.median(60.0 / valid_rr_rd))

        # Quality gating according to doc Section 7
        reasons = []
        hr_trustworthy = True
        if hr_ppg is None or hr_ppg < 40.0 or hr_ppg > 200.0:
            hr_trustworthy = False
            reasons.append("unphysiological_hr")

        if hr_ppg and hr_bcg and abs(hr_ppg - hr_bcg) > 20.0:
            hr_trustworthy = False
            reasons.append(f"ppg_bcg_divergence_{abs(hr_ppg - hr_bcg):.1f}bpm")

        hrv_trustworthy = True
        if rmssd is None or rmssd > 150.0 or rmssd < 5.0:
            hrv_trustworthy = False
            if rmssd and rmssd > 150.0:
                reasons.append("rmssd_ceiling_exceeded_150ms")
            # Doc requirement: RMSSD and SDNN are nulled when HRV is not trustworthy
            rmssd_gated = None
            sdnn_gated = None
        else:
            rmssd_gated = rmssd
            sdnn_gated = sdnn

        quality_level = "ok" if (hr_trustworthy and hrv_trustworthy) else "low"

        return {
            "median_hr_ppg": round(hr_ppg, 1) if hr_ppg else None,
            "median_hr_bcg": round(hr_bcg, 1) if hr_bcg else None,
            "hr_trustworthy": hr_trustworthy,
            "rmssd_ms": round(rmssd_gated, 1) if rmssd_gated else None,
            "sdnn_ms": round(sdnn_gated, 1) if sdnn_gated else None,
            "raw_rmssd": round(rmssd, 1) if rmssd else None,
            "hrv_trustworthy": hrv_trustworthy,
            "hr_quality_level": quality_level,
            "hr_quality_reasons": reasons
        }

    def extract_gait_motion(self, imu_window: List[Tuple]) -> Dict[str, Any]:
        """
        Extracts gait parameters: steps, cadence, Stride CV, RMS energy, and peak impact.
        Steps: Gyro-fused zero-crossing detector with accelerometer fallback (Doc Section 8).
        """
        if len(imu_window) < 50:
            return {
                "steps": 0,
                "cadence_spm": 0.0,
                "stride_cv": 0.0,
                "rms_acc": 0.0,
                "peak_impact_g": 0.0,
                "window_cum_load": 0.0
            }

        times = np.array([x[0] for x in imu_window])
        ax = np.array([x[1] for x in imu_window])
        ay = np.array([x[2] for x in imu_window])
        az = np.array([x[3] for x in imu_window])
        gx = np.array([x[4] for x in imu_window])
        gy = np.array([x[5] for x in imu_window])
        gz = np.array([x[6] for x in imu_window])

        acc_mag = np.sqrt(ax**2 + ay**2 + az**2)
        gyro_mag = np.sqrt(gx**2 + gy**2 + gz**2)

        duration = max(0.1, times[-1] - times[0])
        dt = np.median(np.diff(times))
        fs = 1.0 / dt if dt > 0 else 100.0

        # Gyro-fused step detector with accel peak fallback
        detrended_gyro = gyro_mag - np.mean(gyro_mag)
        detrended_acc = acc_mag - np.mean(acc_mag)

        min_step_dist = int(fs * 0.35)  # min ~0.35s between steps
        prom_gyro = max(0.5 * np.std(detrended_gyro), 10.0)
        peaks_gyro, _ = signal.find_peaks(detrended_gyro, distance=min_step_dist, prominence=prom_gyro)

        if len(peaks_gyro) > 1:
            step_peaks = peaks_gyro
        else:
            prom_acc = max(0.5 * np.std(detrended_acc), 0.1)
            peaks_acc, _ = signal.find_peaks(detrended_acc, distance=min_step_dist, prominence=prom_acc)
            step_peaks = peaks_acc

        steps = len(step_peaks)
        cadence_spm = (steps / duration) * 60.0

        # Stride CV (Coefficient of variation of stride intervals)
        if steps > 2:
            step_times = times[step_peaks]
            stride_intervals = np.diff(step_times)
            mean_si = np.mean(stride_intervals)
            stride_cv = float(np.std(stride_intervals) / mean_si) if mean_si > 0 else 0.0
        else:
            stride_cv = 0.0

        rms_acc = float(np.sqrt(np.mean(acc_mag**2)))
        peak_impact = float(np.max(acc_mag)) if len(acc_mag) > 0 else 0.0
        window_cum_load = float(rms_acc * duration * 0.1)

        return {
            "steps": steps,
            "cadence_spm": cadence_spm,
            "stride_cv": stride_cv,
            "rms_acc": rms_acc,
            "peak_impact_g": peak_impact,
            "window_cum_load": window_cum_load
        }

    def compute_fatigue_scores(
        self,
        cardio_metrics: Dict[str, Any],
        gait_metrics: Dict[str, Any],
        is_warmup: bool
    ) -> Dict[str, Any]:
        """
        Computes the fatigue composite and subcomponents based on OWN Sense Knowledge Transfer doc:
        - Construction:
            fatigue_composite = 0.30*hr_elevation + 0.25*hrv_depression + 0.25*cadence_decline + 0.20*gait_degradation
            Capped at 95.
        - First ~20 seconds of a session are baseline_pending and return None.
        - Construction exposes six keys:
            hr_elevation, hrv_depression, cadence_decline, gait_degradation, rms_drop, imu_fatigue_raw.
        - Severity buckets: none, info, warning, urgent, critical.
        """
        if is_warmup or not self.baseline_established:
            return {
                "fatigue_composite": None,
                "status": "baseline_pending",
                "severity": "none",
                "fatigue_components": None
            }

        # 1. HR Elevation: (median_hr - resting) / resting * 100 when resting baseline exists
        current_hr = cardio_metrics.get("median_hr_ppg")
        if current_hr and cardio_metrics.get("hr_trustworthy"):
            hr_elev = max(0.0, (current_hr - self.resting_hr) / self.resting_hr * 100.0)
        else:
            hr_elev = 0.0

        # 2. HRV Depression: uses RMSSD after quality gating
        current_rmssd = cardio_metrics.get("rmssd_ms")
        if current_rmssd and self.baseline_rmssd and self.baseline_rmssd > 0:
            hrv_dep = max(0.0, min(100.0, (self.baseline_rmssd - current_rmssd) / self.baseline_rmssd * 100.0))
        else:
            hrv_dep = 0.0

        # 3. Cadence Decline: relative decline from active baseline
        current_cadence = gait_metrics.get("cadence_spm", 0.0)
        if self.baseline_cadence and self.baseline_cadence > 20.0 and current_cadence > 10.0:
            cad_decline = max(0.0, min(100.0, (self.baseline_cadence - current_cadence) / self.baseline_cadence * 100.0))
        else:
            cad_decline = 0.0

        # 4. Gait Degradation: increase in Stride CV and RMS drop
        current_stride_cv = gait_metrics.get("stride_cv", 0.0)
        current_rms = gait_metrics.get("rms_acc", 0.0)

        # Baseline comparison
        if self.baseline_stride_cv is not None and self.baseline_stride_cv > 0:
            cv_increase = max(0.0, (current_stride_cv - self.baseline_stride_cv) / (self.baseline_stride_cv + 0.01) * 50.0)
        else:
            cv_increase = min(100.0, current_stride_cv * 150.0)

        if self.baseline_rms and self.baseline_rms > 0:
            rms_drop = max(0.0, min(100.0, (self.baseline_rms - current_rms) / self.baseline_rms * 100.0))
        else:
            rms_drop = 0.0

        gait_degradation = min(100.0, 0.50 * cv_increase + 0.50 * rms_drop)

        # IMU raw fatigue
        imu_fatigue_raw = min(100.0, 0.50 * cad_decline + 0.50 * gait_degradation)

        # Construction Fatigue Composite (Section 11)
        composite = (
            0.30 * hr_elev +
            0.25 * hrv_dep +
            0.25 * cad_decline +
            0.20 * gait_degradation
        )
        # Fatigue composite is capped at 95 (Section 11)
        composite = min(95.0, max(0.0, composite))

        # Construction exposes six keys (Section 11 & Section 17):
        components = {
            "hr_elevation": round(hr_elev, 2),
            "hrv_depression": round(hrv_dep, 2),
            "cadence_decline": round(cad_decline, 2),
            "gait_degradation": round(gait_degradation, 2),
            "rms_drop": round(rms_drop, 2),
            "imu_fatigue_raw": round(imu_fatigue_raw, 2)
        }

        # Severity buckets (Section 11): none, info, warning, urgent, critical
        if composite < 20.0:
            severity = "none"
        elif composite < 40.0:
            severity = "info"
        elif composite < 65.0:
            severity = "warning"
        elif composite < 80.0:
            severity = "urgent"
        else:
            severity = "critical"

        return {
            "fatigue_composite": round(composite, 2),
            "status": "active",
            "severity": severity,
            "fatigue_components": components
        }

    def process_file(
        self,
        file_path: str,
        max_lines: Optional[int] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Runs the full ingestion, windowing, feature extraction, and fatigue analysis pipeline.
        """
        print(f"[*] [Previous Pipeline] Ingesting raw sensor records from {file_path}...")
        ppg_samples, imu_samples = self.parse_records(file_path, max_lines=max_lines)

        print(f"[+] Loaded {len(ppg_samples)} PPG samples and {len(imu_samples)} IMU triplets.")

        if not ppg_samples and not imu_samples:
            return {"error": "No valid sensor records parsed"}

        max_t = 0.0
        if ppg_samples:
            max_t = max(max_t, ppg_samples[-1][0])
        if imu_samples:
            max_t = max(max_t, imu_samples[-1][0])

        total_windows = int(np.ceil(max_t / self.window_sec))
        print(f"[*] Stream duration: {max_t:.1f}s across {total_windows} evaluation windows (size: {self.window_sec}s).")

        window_results = []
        warmup_rmssd_list = []
        warmup_cadence_list = []
        warmup_rms_list = []
        warmup_cv_list = []

        ppg_idx = 0
        imu_idx = 0

        for w in range(total_windows):
            w_start = w * self.window_sec
            w_end = (w + 1) * self.window_sec

            # Slice window PPG
            w_ppg = []
            while ppg_idx < len(ppg_samples) and ppg_samples[ppg_idx][0] < w_end:
                if ppg_samples[ppg_idx][0] >= w_start:
                    w_ppg.append(ppg_samples[ppg_idx])
                ppg_idx += 1

            # Slice window IMU
            w_imu = []
            while imu_idx < len(imu_samples) and imu_samples[imu_idx][0] < w_end:
                if imu_samples[imu_idx][0] >= w_start:
                    w_imu.append(imu_samples[imu_idx])
                imu_idx += 1

            # Feature Extraction
            cardio = self.extract_hr_hrv(w_ppg)
            gait = self.extract_gait_motion(w_imu)

            self.cum_load += gait["window_cum_load"]

            is_warmup = (w_end <= self.warmup_sec)

            # Establish baseline during warmup
            if is_warmup:
                if cardio.get("raw_rmssd"):
                    warmup_rmssd_list.append(cardio["raw_rmssd"])
                if gait.get("cadence_spm", 0) > 15:
                    warmup_cadence_list.append(gait["cadence_spm"])
                if gait.get("rms_acc", 0) > 0.1:
                    warmup_rms_list.append(gait["rms_acc"])
                if gait.get("stride_cv", 0) > 0.01:
                    warmup_cv_list.append(gait["stride_cv"])
            else:
                if not self.baseline_established:
                    self.baseline_rmssd = float(np.median(warmup_rmssd_list)) if warmup_rmssd_list else 40.0
                    self.baseline_cadence = float(np.median(warmup_cadence_list)) if warmup_cadence_list else 80.0
                    self.baseline_rms = float(np.median(warmup_rms_list)) if warmup_rms_list else 1.0
                    self.baseline_stride_cv = float(np.median(warmup_cv_list)) if warmup_cv_list else 0.08
                    self.baseline_established = True

            # Compute Fatigue
            fatigue = self.compute_fatigue_scores(cardio, gait, is_warmup)

            if progress_callback and (w % 5 == 0 or w == total_windows - 1):
                progress_callback({
                    "window": w + 1,
                    "total_windows": total_windows,
                    "percent": int(((w + 1) / max(1, total_windows)) * 100)
                })

            # Derived Metrics from Section 9 & 10 of KT Doc:
            # 1. Calories (Section 9): Reconciled HR -> MET -> Step
            cur_hr = cardio.get("median_hr_ppg")
            weight_kg = 75.0
            hours_window = self.window_sec / 3600.0
            # Keytel formula: kcal/min = (-55.0969 + 0.6309*HR + 0.1988*weight + 0.2017*age) / 4.184
            if cur_hr and cardio.get("hr_trustworthy") and cur_hr >= 50.0:
                keytel_rate = (-55.0969 + 0.6309 * cur_hr + 0.1988 * weight_kg + 0.2017 * self.age) / 4.184
                cal_keytel = max(0.0, keytel_rate * (self.window_sec / 60.0))
            else:
                cal_keytel = None

            # Step mechanical: steps * stride_m(0.78) * 0.57 * weight_kg / 1000
            cal_step = gait["steps"] * 0.78 * 0.57 * weight_kg / 1000.0
            # MET estimate: walking ~3.5 MET, stationary ~1.3 MET
            met_val = 3.8 if gait["cadence_spm"] >= 20.0 else 1.3
            cal_met = met_val * weight_kg * hours_window
            cal_reconciled = int(round(cal_keytel if cal_keytel is not None else (cal_met if weight_kg else cal_step)))

            # 2. VO2 max (Section 10): 15.3 * (HRmax / HRrest)
            vo2_max = round(15.3 * (self.tanaka_hrmax / max(40.0, self.resting_hr)), 1)

            res = {
                "window": w + 1,
                "time_sec": round(w_end, 1),
                "is_warmup": is_warmup,
                "hr_bpm": cardio.get("median_hr_ppg"),
                "median_hr_bcg": cardio.get("median_hr_bcg"),
                "hr_trustworthy": cardio.get("hr_trustworthy"),
                "rmssd_ms": cardio.get("rmssd_ms"),
                "sdnn_ms": cardio.get("sdnn_ms"),
                "hrv_trustworthy": cardio.get("hrv_trustworthy"),
                "hr_quality_level": cardio.get("hr_quality_level"),
                "cadence_spm": round(gait["cadence_spm"], 1),
                "steps": gait["steps"],
                "stride_cv": round(gait["stride_cv"], 4),
                "rms_acc": round(gait["rms_acc"], 3),
                "peak_impact_g": round(gait["peak_impact_g"], 2),
                "fatigue_composite": fatigue.get("fatigue_composite"),
                "severity": fatigue.get("severity"),
                "components": fatigue.get("fatigue_components"),
                "cum_load": round(self.cum_load, 1),
                "calories": {
                    "keytel": round(cal_keytel, 2) if cal_keytel else None,
                    "step_mechanical": round(cal_step, 2),
                    "activity_met": round(cal_met, 2),
                    "value": cal_reconciled
                },
                "vo2_max": vo2_max
            }
            window_results.append(res)

        # Aggregate summary
        valid_scores = [w["fatigue_composite"] for w in window_results if w["fatigue_composite"] is not None]
        avg_fatigue = float(np.mean(valid_scores)) if valid_scores else 0.0
        max_fatigue = float(np.max(valid_scores)) if valid_scores else 0.0
        final_fatigue = valid_scores[-1] if valid_scores else 0.0

        if final_fatigue < 20:
            overall_severity = "none"
        elif final_fatigue < 40:
            overall_severity = "info"
        elif final_fatigue < 65:
            overall_severity = "warning"
        elif final_fatigue < 80:
            overall_severity = "urgent"
        else:
            overall_severity = "critical"

        return {
            "app": self.app,
            "pipeline_type": "previous_kt_doc",
            "pipeline_name": "Previous Pipeline (KT-Doc Spec Baseline)",
            "resting_hr_baseline": self.resting_hr,
            "total_windows": total_windows,
            "total_duration_sec": round(max_t, 1),
            "cum_load": round(self.cum_load, 1),
            "baseline_calibration": {
                "warmup_sec": self.warmup_sec,
                "baseline_rmssd": round(self.baseline_rmssd, 1) if self.baseline_rmssd else None,
                "baseline_cadence": round(self.baseline_cadence, 1) if self.baseline_cadence else None,
                "baseline_rms": round(self.baseline_rms, 3) if self.baseline_rms else None,
                "baseline_stride_cv": round(self.baseline_stride_cv, 4) if self.baseline_stride_cv else None
            },
            "summary": {
                "initial_warmup_sec": self.warmup_sec,
                "average_fatigue": round(avg_fatigue, 2),
                "peak_fatigue": round(max_fatigue, 2),
                "final_fatigue": round(final_fatigue, 2),
                "severity": overall_severity
            },
            "windows": window_results
        }


def process_all_to_directory(output_dir="previous_reports"):
    os.makedirs(output_dir, exist_ok=True)
    input_files = sorted(glob.glob("input_data/*.txt"))
    print(f"[*] Found {len(input_files)} raw telemetry files to evaluate.")
    
    for f in input_files:
        basename = os.path.basename(f)
        out_name = os.path.splitext(basename)[0] + ".json"
        out_path = os.path.join(output_dir, out_name)
        
        print(f"\n---> Processing {basename} -> {out_path} ...")
        pipeline = PreviousFatiguePipeline(app="construction", resting_hr=65.0, warmup_sec=20.0)
        report = pipeline.process_file(f)
        report["filename"] = basename
        
        with open(out_path, "w", encoding="utf-8") as out_fp:
            json.dump(report, out_fp, indent=2)
        print(f"[✓] Saved {out_path}")
        print(f"    Peak: {report['summary']['peak_fatigue']}, Avg: {report['summary']['average_fatigue']}, End: {report['summary']['final_fatigue']}, Severity: {report['summary']['severity']}")


def main():
    parser = argparse.ArgumentParser(description="OWN Sense Previous Pipeline (Doc Specification)")
    parser.add_argument("--input", "-i", type=str, default=None, help="Path to raw sensor JSONL data file")
    parser.add_argument("--all", action="store_true", help="Process all files in input_data/ into previous_reports/")
    parser.add_argument("--output", "-o", type=str, default="previous_fatigue_report.json", help="Path to save output JSON")
    parser.add_argument("--app", "-a", type=str, default="construction", choices=["construction", "rwf", "sports"])
    parser.add_argument("--resting-hr", type=float, default=65.0)
    parser.add_argument("--max-lines", "-m", type=int, default=None)
    args = parser.parse_args()

    if args.all or args.input is None:
        process_all_to_directory()
    else:
        pipeline = PreviousFatiguePipeline(app=args.app, resting_hr=args.resting_hr, warmup_sec=20.0)
        report = pipeline.process_file(args.input, max_lines=args.max_lines)
        report["filename"] = os.path.basename(args.input)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\n[+] Saved report to {args.output}")


if __name__ == "__main__":
    main()

