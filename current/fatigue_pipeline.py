#!/usr/bin/env python3
"""
OWN Sense Current Production Fatigue Pipeline (Refined Expert Architecture)
Multi-modal fatigue evaluation engine for smart safety shoes (PPG and Dual IMU).

Key Upgrades & Clinical Refinements (Incorporating Expert Review):
1. Hardware Sampling Rate Separation:
   - IMU (Left & Right): 100 Hz (dt = 0.01s)
   - PPG (Left Insole): 25 Hz (dt = 0.04s nominal Florina hardware)
2. PPG Signal Quality Index (SQI) & Invalid HR State:
   - Rejects walking motion artifacts (overlap of foot impacts and heart pulse band).
   - Returns { hr: None, hr_valid: False, ppg_quality: "poor" } rather than blindly accepting 170+ BPM spikes.
3. Activity-State Classifier:
   - Classifies: 'stationary', 'walking_steady', 'walking_intermittent', 'running'.
   - Suppresses false Cadence Decline spikes when worker stops to inspect or stand still.
4. Temporal Bilateral Gait Asymmetry (ASI):
   - Replaces fragile step-count difference with true temporal stride/step time symmetry index.
   - Suppresses false limping alerts caused by RF packet loss.
5. Event-Driven Dynamic Baselines:
   - Replaces blind 180s time-based lock.
   - Establishes walking baseline only from verified steady walking, and resting baseline from verified stationary windows.
6. Grounded Physiological Recovery:
   - Replaces blind 0.92x multiplier on standing.
   - Verifies true HR drop (HRR-60) before applying recovery decay.
7. Motion-Gated Cumulative Shift Load:
   - Gated to genuine locomotion to prevent vehicle/generator vibration from accumulating fake fatigue load.
"""

import json
import argparse
import datetime
import numpy as np
from scipy import signal
from typing import Dict, Any, List, Optional, Tuple, Callable


class FatiguePipeline:
    def __init__(
        self,
        app: str = "construction",
        resting_hr: float = 65.0,
        age: int = 30,
        window_sec: float = 60.0,
        warmup_sec: float = 180.0,
    ):
        self.app = app.lower()
        self.resting_hr = resting_hr
        self.age = age
        self.window_sec = window_sec
        self.warmup_sec = warmup_sec
        self.tanaka_hrmax = 208.0 - 0.7 * self.age

        # State tracking: Event-driven baselines
        self.baseline_established = False
        self.walking_baseline_established = False
        self.resting_baseline_established = False

        self.baseline_cadence: Optional[float] = None
        self.baseline_stride_cv: Optional[float] = None
        self.baseline_rms: Optional[float] = None
        self.baseline_walking_hr: Optional[float] = None
        self.baseline_resting_hr: float = resting_hr
        self.baseline_resting_rmssd: Optional[float] = None

        # Warmup accumulation buffers
        self.warmup_cadence_list: List[float] = []
        self.warmup_cv_list: List[float] = []
        self.warmup_rms_list: List[float] = []
        self.warmup_walking_hr_list: List[float] = []
        self.warmup_resting_hr_list: List[float] = []
        self.warmup_resting_rmssd_list: List[float] = []

        # Shift cumulative load & state tracking
        self.cum_load: float = 0.0
        self.stationary_streak_sec: float = 0.0
        self.last_active_hr: Optional[float] = None
        self.last_fatigue_score: float = 0.0

    def parse_records(self, file_path: str, max_lines: Optional[int] = None) -> Tuple[List[Tuple], List[Tuple]]:
        """
        Parses raw JSONL footwear records into strictly sorted time-series streams.
        Separates IMU (100 Hz, dt = 0.01s) and PPG (25 Hz, dt = 0.04s) hardware sampling rates.
        """
        ppg_samples = []  # (rel_time_sec, ir_val, rd_val)
        imu_samples = []  # (rel_time_sec, ax, ay, az, gx, gy, gz, foot)

        start_time = None

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
                t_type = content.get("T", "")

                # Extract ISO timestamp
                ts_str = content.get("timestamp")
                if not ts_str and "Data" in content:
                    ts_str = content["Data"].get("timestamp")

                if not ts_str:
                    continue

                try:
                    dt = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    t_sec = dt.timestamp()
                except Exception:
                    continue

                if start_time is None:
                    start_time = t_sec

                rel_t = max(0.0, t_sec - start_time)

                # Parse PPG (Nominal Florina hardware sampling rate = 25 Hz -> dt = 0.04s)
                if t_type == "PG" or (topic == "PPG" and "IR" in content):
                    ir_arr = content.get("IR", [])
                    rd_arr = content.get("RD", [])
                    n = min(len(ir_arr), len(rd_arr))
                    if n > 0:
                        ppg_dt = 0.04  # 25 Hz sample interval
                        for j in range(n):
                            ppg_samples.append((rel_t + j * ppg_dt, float(ir_arr[j]), float(rd_arr[j])))

                # Parse Left Foot IMU (Nominal Florina hardware sampling rate = 100 Hz -> dt = 0.01s)
                elif t_type == "BL" or (topic == "PPG" and "AC" in content):
                    ac = content.get("AC", [])
                    gy = content.get("GY", [])
                    n_triplets = min(len(ac) // 3, len(gy) // 3)
                    for j in range(n_triplets):
                        t_sub = rel_t + j * 0.01  # 100 Hz sample interval
                        ax, ay, az = ac[j*3], ac[j*3+1], ac[j*3+2]
                        gx, gy_val, gz = gy[j*3], gy[j*3+1], gy[j*3+2]
                        imu_samples.append((t_sub, ax, ay, az, gx, gy_val, gz, "left"))

                # Parse Right Foot IMU (Nominal Florina hardware sampling rate = 100 Hz -> dt = 0.01s)
                elif t_type == "BR" or topic == "BPST_RIGHT":
                    data = content.get("Data", {})
                    ac = data.get("AC", [])
                    gy = data.get("GY", [])
                    n_triplets = min(len(ac) // 3, len(gy) // 3)
                    for j in range(n_triplets):
                        t_sub = rel_t + j * 0.01  # 100 Hz sample interval
                        ax, ay, az = ac[j*3], ac[j*3+1], ac[j*3+2]
                        gx, gy_val, gz = gy[j*3], gy[j*3+1], gy[j*3+2]
                        imu_samples.append((t_sub, ax, ay, az, gx, gy_val, gz, "right"))

        # Guarantee strict chronological monotonic ordering
        ppg_samples.sort(key=lambda x: x[0])
        imu_samples.sort(key=lambda x: x[0])

        return ppg_samples, imu_samples

    def extract_hr_sqi(
        self,
        ppg_window: List[Tuple[float, float, float]],
        left_foot_rms_acc: float = 0.0,
        left_foot_cadence: float = 0.0
    ) -> Dict[str, Any]:
        """
        Extracts Heart Rate with Signal Quality Assessment (SQI) & Motion Artifact Gating.
        Prevents heel-strike vibrations from being blindly accepted as 170+ BPM heartbeats.
        """
        fallback_invalid = {
            "median_hr_ppg": None,
            "median_hr_bcg": None,
            "hr_trustworthy": False,
            "ppg_sqi": "poor",
            "motion_artifact": True,
            "rmssd_ms": None,
            "sdnn_ms": None,
            "hrv_trustworthy": False,
            "hr_quality_level": "low"
        }

        if len(ppg_window) < 50:
            fallback_invalid["motion_artifact"] = False
            fallback_invalid["ppg_sqi"] = "insufficient_data"
            return fallback_invalid

        # Deduplicate and sort timestamps
        w_sorted = sorted(ppg_window, key=lambda x: x[0])
        raw_t = np.array([x[0] for x in w_sorted])
        raw_ir = np.array([x[1] for x in w_sorted])
        raw_rd = np.array([x[2] for x in w_sorted])

        keep = np.insert(np.diff(raw_t) > 0, 0, True)
        clean_t = raw_t[keep]
        clean_ir = raw_ir[keep]
        clean_rd = raw_rd[keep]

        duration = clean_t[-1] - clean_t[0]
        if len(clean_t) < 40 or duration < 5.0:
            fallback_invalid["ppg_sqi"] = "too_short"
            return fallback_invalid

        # 1. Optical SQI Check: Sensor Saturation, Flatline, or Dynamic Range
        ir_std = float(np.std(clean_ir))
        ir_ptp = float(np.ptp(clean_ir))
        if ir_std < 5.0 or ir_ptp < 15.0 or ir_ptp > 500000.0:
            fallback_invalid["ppg_sqi"] = "saturated_or_flatline"
            return fallback_invalid

        # 2. Resample on clean 50 Hz grid for stable bandpass filtering
        fs = 50.0
        uniform_t = np.arange(clean_t[0], clean_t[-1], 1.0 / fs)
        if len(uniform_t) < 50:
            fallback_invalid["ppg_sqi"] = "resampling_failure"
            return fallback_invalid

        uniform_ir = np.interp(uniform_t, clean_t, clean_ir)
        uniform_rd = np.interp(uniform_t, clean_t, clean_rd)

        # 3. Bandpass filter for PPG (0.7 Hz - 3.5 Hz ~ 42 - 210 bpm)
        nyq = 0.5 * fs
        low = max(0.01, 0.7 / nyq)
        high = min(0.99, 3.5 / nyq)

        try:
            b, a = signal.butter(2, [low, high], btype='band')
            filtered_ir = signal.filtfilt(b, a, uniform_ir)
            filtered_rd = signal.filtfilt(b, a, uniform_rd)
        except Exception:
            filtered_ir = uniform_ir - np.mean(uniform_ir)
            filtered_rd = uniform_rd - np.mean(uniform_rd)

        # 4. Pulse Peak Detection
        min_distance = int(fs * 0.35)  # Max HR ~170 bpm physiological refractory window
        prominence = max(5.0, np.std(filtered_ir) * 0.45)
        peaks_ir, _ = signal.find_peaks(filtered_ir, distance=min_distance, prominence=prominence)
        peaks_rd, _ = signal.find_peaks(filtered_rd, distance=min_distance, prominence=prominence)

        if len(peaks_ir) < 4:
            fallback_invalid["ppg_sqi"] = "insufficient_peaks"
            return fallback_invalid

        # 5. Inter-Beat Interval (IBI) Consistency & Physiological Range
        ibi_ir = np.diff(uniform_t[peaks_ir])
        ibi_valid = ibi_ir[(ibi_ir >= 0.28) & (ibi_ir <= 1.50)]  # 40 to 214 bpm

        if len(ibi_valid) < 3:
            fallback_invalid["ppg_sqi"] = "unphysiological_ibi"
            return fallback_invalid

        # IBI Coefficient of Variation (Sudden erratic jumps indicate motion noise)
        ibi_cv = float(np.std(ibi_valid) / np.mean(ibi_valid))
        hr_ppg = float(np.median(60.0 / ibi_valid))

        # 6. Motion-Artifact Collision Detection (Walking frequency vs Pulse frequency)
        # If left foot is vigorously moving (cadence > 40 or RMS > 0.4g) and IBI CV > 0.22,
        # foot impacts are corrupting the optical pulse signal.
        motion_artifact = False
        if left_foot_cadence >= 40.0 and ibi_cv > 0.20:
            motion_artifact = True
        if left_foot_rms_acc > 0.65 and ibi_cv > 0.18:
            motion_artifact = True

        # Check Red / IR channel agreement
        hr_rd = None
        if len(peaks_rd) >= 4:
            ibi_rd = np.diff(uniform_t[peaks_rd])
            ibi_rd_valid = ibi_rd[(ibi_rd >= 0.28) & (ibi_rd <= 1.50)]
            if len(ibi_rd_valid) >= 3:
                hr_rd = float(np.median(60.0 / ibi_rd_valid))

        channel_agreement = True
        if hr_rd and abs(hr_ppg - hr_rd) > 22.0:
            channel_agreement = False
            motion_artifact = True

        # Quality Gating Decision
        if motion_artifact or not channel_agreement or ibi_cv > 0.28:
            # Mark invalid rather than outputting corrupted 170+ BPM
            return {
                "median_hr_ppg": None,
                "median_hr_bcg": round(hr_rd, 1) if hr_rd else None,
                "hr_trustworthy": False,
                "ppg_sqi": "poor",
                "motion_artifact": True,
                "rmssd_ms": None,
                "sdnn_ms": None,
                "hrv_trustworthy": False,
                "hr_quality_level": "low"
            }

        # Valid HR Extraction
        # Note: Compute RMSSD only during high-quality stationary segments (expert review priority)
        rmssd, sdnn = None, None
        hrv_trustworthy = False
        if left_foot_cadence < 15.0 and ibi_cv < 0.15:
            rr_ms = ibi_valid * 1000.0
            raw_rmssd = float(np.sqrt(np.mean(np.diff(rr_ms) ** 2)))
            if 10.0 <= raw_rmssd <= 120.0:
                rmssd = round(raw_rmssd, 1)
                sdnn = round(float(np.std(rr_ms)), 1)
                hrv_trustworthy = True

        return {
            "median_hr_ppg": round(hr_ppg, 1),
            "median_hr_bcg": round(hr_rd, 1) if hr_rd else round(hr_ppg, 1),
            "hr_trustworthy": True,
            "ppg_sqi": "good" if ibi_cv < 0.12 else "fair",
            "motion_artifact": False,
            "rmssd_ms": rmssd,
            "sdnn_ms": sdnn,
            "hrv_trustworthy": hrv_trustworthy,
            "hr_quality_level": "ok"
        }

    def extract_gait_and_activity(self, imu_window: List[Tuple]) -> Dict[str, Any]:
        """
        Classifies activity state and extracts temporal bilateral gait metrics.
        Activity states: 'stationary', 'walking_steady', 'walking_intermittent', 'running'.
        Calculates true Temporal Gait Asymmetry (ASI %) instead of fragile step count difference.
        """
        if len(imu_window) < 30:
            return {
                "activity_state": "stationary",
                "steps": 0,
                "cadence_spm": 0.0,
                "stride_cv": 0.0,
                "rms_acc": 0.0,
                "peak_impact_g": 0.0,
                "temporal_asymmetry_pct": 0.0,
                "window_cum_load": 0.0,
                "left_active": False,
                "right_active": False
            }

        left_samples = [x for x in imu_window if x[7] == "left"]
        right_samples = [x for x in imu_window if x[7] == "right"]

        def analyze_foot_stream(samples: List[Tuple]) -> Tuple[bool, int, List[float], float, float]:
            if len(samples) < 15:
                return False, 0, [], 0.0, 0.0

            s_sorted = sorted(samples, key=lambda x: x[0])
            raw_times = np.array([x[0] for x in s_sorted])
            # Deduplicate interleaved or repeated network telemetry packets
            keep = np.insert(np.diff(raw_times) > 0.005, 0, True)
            if np.sum(keep) < 15:
                return False, 0, [], 0.0, 0.0

            times = raw_times[keep]
            ax = np.array([x[1] for x in s_sorted])[keep]
            ay = np.array([x[2] for x in s_sorted])[keep]
            az = np.array([x[3] for x in s_sorted])[keep]
            gx = np.array([x[4] for x in s_sorted])[keep]
            gy = np.array([x[5] for x in s_sorted])[keep]
            gz = np.array([x[6] for x in s_sorted])[keep]

            acc_mag = np.sqrt(ax**2 + ay**2 + az**2)
            gyro_mag = np.sqrt(gx**2 + gy**2 + gz**2)

            # Plausibility check: gravity must be >= 0.25g. Near-zero indicates sensor sleep/off.
            mean_acc = float(np.mean(acc_mag))
            if mean_acc < 0.25:
                return False, 0, [], 0.0, 0.0

            rms = float(np.sqrt(np.mean(acc_mag**2)))
            peak_imp = float(np.max(acc_mag))

            # Step detection on single foot (minimum single-foot step period ~0.45s)
            detrended_gyro = gyro_mag - np.mean(gyro_mag)
            diffs = np.diff(times)
            valid_diffs = diffs[diffs > 0]
            dt = float(np.median(valid_diffs)) if len(valid_diffs) > 0 else 0.01
            fs = 1.0 / dt if dt > 0 else 100.0

            min_dist = max(5, int(fs * 0.45))
            prominence = max(0.20, float(np.std(detrended_gyro) * 0.5))
            peaks, _ = signal.find_peaks(detrended_gyro, distance=min_dist, prominence=prominence)
            step_times = list(times[peaks]) if len(peaks) > 0 else []

            return True, len(peaks), step_times, rms, peak_imp

        l_active, l_steps, l_times, l_rms, l_peak = analyze_foot_stream(left_samples)
        r_active, r_steps, r_times, r_rms, r_peak = analyze_foot_stream(right_samples)

        # Bilateral Fusion
        if l_active and r_active:
            total_steps = l_steps + r_steps
            rms_acc = 0.5 * (l_rms + r_rms)
            peak_impact = max(l_peak, r_peak)
            active_stride_times = r_times if len(r_times) >= len(l_times) else l_times
        elif r_active:
            total_steps = r_steps * 2
            rms_acc = r_rms
            peak_impact = r_peak
            active_stride_times = r_times
        elif l_active:
            total_steps = l_steps * 2
            rms_acc = l_rms
            peak_impact = l_peak
            active_stride_times = l_times
        else:
            total_steps = 0
            rms_acc = 0.0
            peak_impact = 0.0
            active_stride_times = []

        all_times = [x[0] for x in imu_window]
        span = (max(all_times) - min(all_times)) if len(all_times) > 10 else self.window_sec
        duration = max(self.window_sec * 0.75, span)
        cadence_spm = min(180.0, (total_steps / duration) * 60.0)

        # Activity-State Classification
        if cadence_spm < 10.0 and rms_acc < 0.35:
            activity_state = "stationary"
        elif cadence_spm >= 130.0 and rms_acc > 1.8:
            activity_state = "running"
        elif cadence_spm >= 55.0:
            activity_state = "walking_steady"
        else:
            activity_state = "walking_intermittent"

        # Stride Time Variability (CV) on verified walking states only
        if len(active_stride_times) >= 4 and activity_state in ["walking_steady", "running"]:
            stride_intervals = np.diff(active_stride_times)
            mean_si = np.mean(stride_intervals)
            raw_cv = float(np.std(stride_intervals) / mean_si) if mean_si > 0 else 0.0
            stride_cv = min(0.35, raw_cv)
        else:
            stride_cv = 0.0

        # Temporal Gait Asymmetry Index (ASI %): Compares Left vs Right Step Duration
        # ASI = 100 * |T_L - T_R| / ((T_L + T_R) / 2)
        temporal_asi = 0.0
        if l_active and r_active and len(l_times) >= 3 and len(r_times) >= 3 and activity_state == "walking_steady":
            t_left_mean = float(np.mean(np.diff(l_times)))
            t_right_mean = float(np.mean(np.diff(r_times)))
            mean_both = (t_left_mean + t_right_mean) / 2.0
            if mean_both > 0:
                temporal_asi = round(abs(t_left_mean - t_right_mean) / mean_both * 100.0, 2)
                temporal_asi = min(50.0, temporal_asi)

        # Motion-Gated Cumulative Shift Load (Only accumulates during genuine physical locomotion)
        # Prevents vehicle vibration or standing near generators from creating fake cumulative load
        if activity_state in ["walking_steady", "walking_intermittent", "running"]:
            window_cum_load = float(rms_acc * duration * 0.1)
        else:
            window_cum_load = 0.0

        return {
            "activity_state": activity_state,
            "steps": total_steps,
            "cadence_spm": round(cadence_spm, 1),
            "stride_cv": round(stride_cv, 4),
            "rms_acc": round(rms_acc, 3),
            "peak_impact_g": round(peak_impact, 2),
            "temporal_asymmetry_pct": temporal_asi,
            "window_cum_load": round(window_cum_load, 2),
            "l_steps": l_steps,
            "r_steps": r_steps,
            "l_rms": round(l_rms, 3),
            "r_rms": round(r_rms, 3),
            "left_active": l_active,
            "right_active": r_active
        }

    def compute_fatigue_scores(
        self,
        cardio: Dict[str, Any],
        gait: Dict[str, Any],
        is_warmup: bool
    ) -> Dict[str, Any]:
        """
        Computes Fatigue Composite with:
        - Activity-aware Cadence Decline (suppressed when standing or inspecting).
        - Temporal Gait Deterioration (Stride CV + RMS Drop + Temporal Asymmetry).
        - Grounded Physiological Recovery (requires verified HR drop, no blind 0.92x).
        - Clean Separation of Cumulative Exposure from Instantaneous Strain.
        """
        if is_warmup or not self.baseline_established:
            return {
                "fatigue_composite": None,
                "status": "baseline_pending",
                "severity": "none",
                "activity_state": "warmup",
                "fatigue_components": None
            }

        act_state = gait.get("activity_state", "stationary")
        current_cadence = gait.get("cadence_spm", 0.0)
        current_hr = cardio.get("median_hr_ppg")
        hr_trustworthy = cardio.get("hr_trustworthy", False)
        temporal_asi = gait.get("temporal_asymmetry_pct", 0.0)
        current_stride_cv = gait.get("stride_cv", 0.0)
        current_rms = gait.get("rms_acc", 0.0)

        # 1. Cardiovascular Strain (0 - 100)
        pct_hrr = 0.0
        cardiac_cost_score = 0.0
        cardiac_cost_raw = 0.0

        if current_hr and hr_trustworthy:
            hr_capacity = max(20.0, self.tanaka_hrmax - self.baseline_resting_hr)
            pct_hrr = max(0.0, min(100.0, (current_hr - self.baseline_resting_hr) / hr_capacity * 100.0))

            # Cardiac Cost evaluated during locomotion
            if current_cadence >= 20.0:
                delta_hr = max(0.0, current_hr - self.baseline_resting_hr)
                cardiac_cost_raw = round(delta_hr / max(10.0, current_cadence), 3)
                # 0.20 ratio is normal/fresh; 0.70 indicates heavy cardio strain
                cardiac_cost_score = max(0.0, min(100.0, (cardiac_cost_raw - 0.20) / 0.50 * 100.0))

            cardio_strain = 0.60 * pct_hrr + 0.40 * cardiac_cost_score
            self.last_active_hr = current_hr
        else:
            cardio_strain = 0.0

        # 2. Cadence Deterioration (0 - 100)
        # CRITICAL EXPERT FIX: Cadence Decline is ONLY evaluated during steady walking!
        # When worker stands to inspect or perform stationary work, cadence decline is strictly ZERO!
        if act_state == "walking_steady" and self.baseline_cadence and self.baseline_cadence > 20.0:
            cad_decline = max(0.0, min(100.0, (self.baseline_cadence - current_cadence) / self.baseline_cadence * 100.0))
        else:
            cad_decline = 0.0

        # 3. Gait Deterioration (0 - 100)
        if self.baseline_stride_cv and self.baseline_stride_cv > 0 and act_state in ["walking_steady", "running"]:
            cv_increase = max(0.0, (current_stride_cv - self.baseline_stride_cv) / (self.baseline_stride_cv + 0.02) * 50.0)
        else:
            cv_increase = 0.0

        if self.baseline_rms and self.baseline_rms > 0.3 and act_state in ["walking_steady", "running"]:
            rms_drop = max(0.0, min(100.0, (self.baseline_rms - current_rms) / self.baseline_rms * 100.0))
        else:
            rms_drop = 0.0

        # Temporal Gait Asymmetry Score (15% temporal difference is marked fatigue/limping)
        asym_score = min(100.0, (temporal_asi / 15.0) * 100.0)
        gait_deg = min(100.0, 0.40 * cv_increase + 0.30 * rms_drop + 0.30 * asym_score)

        # 4. State-Driven Dynamic Model & Grounded Recovery
        weights = {}
        sub_scores = {}

        if act_state in ["walking_steady", "running", "walking_intermittent"]:
            self.stationary_streak_sec = 0.0

            if current_hr and hr_trustworthy:
                weights["cardio_strain"] = 0.40
                sub_scores["cardio_strain"] = round(cardio_strain, 2)

            if act_state == "walking_steady":
                weights["cadence_decline"] = 0.35
                sub_scores["cadence_decline"] = round(cad_decline, 2)
                weights["gait_degradation"] = 0.25
                sub_scores["gait_degradation"] = round(gait_deg, 2)
            else:
                # Intermittent walking / inspection: suppress cadence decline, focus on gait balance & cardio
                weights["gait_degradation"] = 0.40
                sub_scores["gait_degradation"] = round(gait_deg, 2)

            # Dynamic Weight Normalization
            tot_w = sum(weights.values())
            if tot_w > 0:
                active_composite = sum((weights[k] / tot_w) * sub_scores[k] for k in weights)
            else:
                active_composite = gait_deg

            # Cumulative Exposure Drift (Bounded at +15.0 points)
            cum_drift = min(15.0, self.cum_load * 0.012)
            composite = min(95.0, max(0.0, active_composite + cum_drift))
            self.last_fatigue_score = composite

        else:
            # Stationary State (No locomotion)
            self.stationary_streak_sec += self.window_sec

            # EXPERT FIX: Grounded Physiological Recovery (No blind 0.92x multiplier)
            # Recovery is verified by HR actually dropping towards resting baseline
            hrr_60 = None
            if self.last_active_hr and current_hr and hr_trustworthy:
                hrr_60 = round(self.last_active_hr - current_hr, 1)

            if self.stationary_streak_sec >= 60.0 and hrr_60 is not None and hrr_60 > 5.0:
                # Active cardiovascular recovery verified
                decay_rate = 0.94 if hrr_60 >= 20.0 else 0.97
            elif self.stationary_streak_sec >= 60.0:
                # Stationary but HR not dropping (e.g. standing while lifting heavy items) -> Gentle decay
                decay_rate = 0.985
            else:
                # Just stopped (< 60s)
                decay_rate = 0.995

            composite = max(0.0, self.last_fatigue_score * decay_rate)
            self.last_fatigue_score = composite

            sub_scores["cardio_strain"] = round(pct_hrr * 0.3, 2)
            sub_scores["cadence_decline"] = 0.0
            sub_scores["gait_degradation"] = 0.0

        # Sub-score reporting
        sub_scores["pct_hrr"] = round(pct_hrr, 2)
        sub_scores["cardiac_cost"] = cardiac_cost_raw
        sub_scores["temporal_asymmetry_pct"] = temporal_asi
        sub_scores["temporal_asymmetry_score"] = round(asym_score, 2)
        sub_scores["stride_cv_score"] = round(cv_increase, 2)
        sub_scores["rms_drop"] = round(rms_drop, 2)
        sub_scores["activity_state"] = act_state
        sub_scores["ppg_sqi"] = cardio.get("ppg_sqi", "poor")
        sub_scores["hr_trustworthy"] = hr_trustworthy

        # Severity Classification
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
            "activity_state": act_state,
            "fatigue_components": sub_scores
        }

    def process_file(
        self,
        file_path: str,
        max_lines: Optional[int] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Runs the full ingestion, windowing, feature extraction, and fatigue analysis pipeline.
        Features Event-Driven Baseline establishment and continuous motion tracking.
        """
        print(f"[*] Ingesting raw sensor records from {file_path}...")
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
        ppg_idx = 0
        imu_idx = 0

        for w in range(total_windows):
            w_start = w * self.window_sec
            w_end = (w + 1) * self.window_sec

            # Slice window PPG (chronologically ordered)
            w_ppg = []
            while ppg_idx < len(ppg_samples) and ppg_samples[ppg_idx][0] < w_end:
                if ppg_samples[ppg_idx][0] >= w_start:
                    w_ppg.append(ppg_samples[ppg_idx])
                ppg_idx += 1

            # Slice window IMU (chronologically ordered)
            w_imu = []
            while imu_idx < len(imu_samples) and imu_samples[imu_idx][0] < w_end:
                if imu_samples[imu_idx][0] >= w_start:
                    w_imu.append(imu_samples[imu_idx])
                imu_idx += 1

            # Step 1: Gait & Activity-State Classification
            gait = self.extract_gait_and_activity(w_imu)

            # Step 2: Cardio & PPG SQI Check with Left Foot Motion Awareness
            left_rms = gait.get("l_rms", 0.0)
            left_cad = gait.get("cadence_spm", 0.0)
            cardio = self.extract_hr_sqi(w_ppg, left_foot_rms_acc=left_rms, left_foot_cadence=left_cad)

            # Accumulate genuine locomotion load
            self.cum_load += gait["window_cum_load"]

            # Step 3: Event-Driven Dynamic Baseline Establishment
            is_warmup = (w_end <= self.warmup_sec) and (not self.baseline_established)

            if is_warmup:
                # Accumulate steady walking reference
                if gait.get("activity_state") == "walking_steady" and gait.get("cadence_spm", 0) >= 55.0:
                    self.warmup_cadence_list.append(gait["cadence_spm"])
                    self.warmup_rms_list.append(gait["rms_acc"])
                    if gait.get("stride_cv", 0) > 0.01:
                        self.warmup_cv_list.append(gait["stride_cv"])
                    if cardio.get("median_hr_ppg") and cardio.get("hr_trustworthy"):
                        self.warmup_walking_hr_list.append(cardio["median_hr_ppg"])

                # Accumulate resting reference
                if gait.get("activity_state") == "stationary":
                    if cardio.get("median_hr_ppg") and cardio.get("hr_trustworthy"):
                        self.warmup_resting_hr_list.append(cardio["median_hr_ppg"])
                    if cardio.get("rmssd_ms"):
                        self.warmup_resting_rmssd_list.append(cardio["rmssd_ms"])

            # Lock baseline when warmup expires or sufficient samples exist
            if not self.baseline_established:
                if w_end >= self.warmup_sec or (len(self.warmup_cadence_list) >= 2 and len(self.warmup_resting_hr_list) >= 1):
                    self.baseline_cadence = float(np.median(self.warmup_cadence_list)) if self.warmup_cadence_list else 85.0
                    self.baseline_rms = float(np.median(self.warmup_rms_list)) if self.warmup_rms_list else 0.85
                    self.baseline_stride_cv = float(np.median(self.warmup_cv_list)) if self.warmup_cv_list else 0.05
                    self.baseline_walking_hr = float(np.median(self.warmup_walking_hr_list)) if self.warmup_walking_hr_list else 95.0
                    self.baseline_resting_hr = float(np.median(self.warmup_resting_hr_list)) if self.warmup_resting_hr_list else self.resting_hr
                    self.baseline_established = True
                    is_warmup = False

            # Step 4: Compute Fatigue Composite
            fatigue = self.compute_fatigue_scores(cardio, gait, is_warmup)

            if progress_callback and (w % 5 == 0 or w == total_windows - 1):
                progress_callback({
                    "window": w + 1,
                    "total_windows": total_windows,
                    "percent": int(((w + 1) / max(1, total_windows)) * 100)
                })

            res = {
                "window": w + 1,
                "time_sec": round(w_end, 1),
                "is_warmup": is_warmup,
                "activity_state": fatigue.get("activity_state", gait.get("activity_state", "stationary")),
                "worker_state": fatigue.get("activity_state", gait.get("activity_state", "stationary")),
                "hr_bpm": cardio.get("median_hr_ppg"),
                "ppg_sqi": cardio.get("ppg_sqi", "poor"),
                "hr_trustworthy": cardio.get("hr_trustworthy", False),
                "pct_hrr": fatigue.get("fatigue_components", {}).get("pct_hrr") if fatigue.get("fatigue_components") else None,
                "cardiac_cost": fatigue.get("fatigue_components", {}).get("cardiac_cost") if fatigue.get("fatigue_components") else None,
                "cadence_spm": round(gait["cadence_spm"], 1),
                "stride_cv": round(gait["stride_cv"], 4),
                "temporal_asymmetry_pct": gait.get("temporal_asymmetry_pct", 0.0),
                "asymmetry_pct": gait.get("temporal_asymmetry_pct", 0.0),
                "fatigue_composite": fatigue.get("fatigue_composite"),
                "severity": fatigue.get("severity"),
                "components": fatigue.get("fatigue_components"),
                "cum_load": round(self.cum_load, 1)
            }
            window_results.append(res)

        # Aggregate summary statistics
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
            "resting_hr_baseline": self.baseline_resting_hr,
            "walking_cadence_baseline": self.baseline_cadence,
            "total_windows": total_windows,
            "total_duration_sec": round(max_t, 1),
            "cum_load": round(self.cum_load, 1),
            "summary": {
                "initial_warmup_sec": self.warmup_sec,
                "average_fatigue": round(avg_fatigue, 2),
                "peak_fatigue": round(max_fatigue, 2),
                "final_fatigue": round(final_fatigue, 2),
                "severity": overall_severity,
                "walking_windows": sum(1 for w in window_results if "walking" in w.get("activity_state", "")),
                "stationary_windows": sum(1 for w in window_results if w.get("activity_state") == "stationary")
            },
            "windows": window_results
        }


def main():
    parser = argparse.ArgumentParser(description="OWN Sense Raw Data to Fatigue Score Pipeline")
    parser.add_argument("--input", "-i", type=str, required=True, help="Path to raw sensor JSONL data file")
    parser.add_argument("--app", "-a", type=str, default="construction", choices=["construction", "rwf", "sports"], help="Application domain")
    parser.add_argument("--resting-hr", type=float, default=65.0, help="Resting HR baseline in bpm")
    parser.add_argument("--window", "-w", type=float, default=60.0, help="Evaluation window in seconds")
    parser.add_argument("--warmup", type=float, default=180.0, help="Warmup baseline time in seconds")
    parser.add_argument("--max-lines", "-m", type=int, default=10000, help="Max lines to read (for fast evaluation)")
    parser.add_argument("--output", "-o", type=str, default="fatigue_report.json", help="Path to save output JSON")
    args = parser.parse_args()

    pipeline = FatiguePipeline(
        app=args.app,
        resting_hr=args.resting_hr,
        window_sec=args.window,
        warmup_sec=args.warmup
    )

    report = pipeline.process_file(args.input, max_lines=args.max_lines)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "="*60)
    print("FATIGUE EVALUATION SUMMARY REPORT")
    print("="*60)
    print(f"Application Domain:     {report.get('app', '').upper()}")
    print(f"Resting HR Baseline:    {report.get('resting_hr_baseline')} bpm")
    print(f"Walking Cadence Baseline: {report.get('walking_cadence_baseline')} spm")
    print(f"Total Evaluated Time:   {report.get('total_duration_sec')} seconds")
    print(f"Cumulative Shift Load:  {report.get('cum_load')} a.u.")
    print("-" * 60)
    summary = report.get("summary", {})
    print(f"Average Fatigue Score:  {summary.get('average_fatigue')} / 95 (cap)")
    print(f"Peak Fatigue Score:     {summary.get('peak_fatigue')} / 95")
    print(f"Final Fatigue Score:    {summary.get('final_fatigue')} / 95")
    print(f"Final Severity Level:   {summary.get('severity', '').upper()}")
    print("="*60)
    print(f"[+] Detailed window progression saved to: {args.output}\n")


if __name__ == "__main__":
    main()
