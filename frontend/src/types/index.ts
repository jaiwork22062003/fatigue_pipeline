export interface EvaluationWindow {
  window: number;
  time_sec: number;
  clock_time?: string;
  is_warmup: boolean;
  activity_state: string;
  worker_state?: string;
  hr_bpm: number | null;
  ppg_sqi: string;
  hr_trustworthy: boolean;
  pct_hrr: number | null;
  cardiac_cost: number | null;
  cadence_spm: number;
  stride_cv: number;
  temporal_asymmetry_pct: number;
  asymmetry_pct?: number;
  fatigue_composite: number | null;
  severity: 'none' | 'info' | 'warning' | 'urgent' | 'critical';
  components?: {
    cardio_strain?: number;
    cadence_decline?: number;
    gait_degradation?: number;
    pct_hrr?: number;
    cardiac_cost?: number;
    temporal_asymmetry_pct?: number;
    temporal_asymmetry_score?: number;
    stride_cv_score?: number;
    rms_drop?: number;
    activity_state?: string;
    ppg_sqi?: string;
    hr_trustworthy?: boolean;
  } | null;
  cum_load: number;
}

export interface SessionSummary {
  initial_warmup_sec?: number;
  average_fatigue: number;
  peak_fatigue: number;
  final_fatigue: number;
  severity: 'none' | 'info' | 'warning' | 'urgent' | 'critical';
  walking_windows?: number;
  stationary_windows?: number;
  idle_windows?: number;
  active_cadence_avg?: number;
  active_hr_avg?: number | null;
  peak_cadence?: number;
  peak_hr?: number | null;
}

export interface SessionReport {
  app: string;
  filename?: string;
  session_start_iso?: string | null;
  session_end_iso?: string | null;
  session_start_clock?: string | null;
  session_end_clock?: string | null;
  resting_hr_baseline: number;
  walking_cadence_baseline: number;
  total_windows: number;
  total_duration_sec: number;
  cum_load: number;
  summary: SessionSummary;
  windows: EvaluationWindow[];
}

export interface UserDatesCatalog {
  users: string[];
  user_dates: Record<string, Record<string, {
    files: string[];
    has_report: boolean;
    count: number;
    total_size_mb: number;
  }>>;
}

export interface JobStatus {
  state: 'idle' | 'running' | 'completed' | 'error';
  phase: string;
  percent: number;
  message: string;
  result?: any;
  error?: string | null;
}

export interface BlogPost {
  id: string;
  title: string;
  slug: string;
  excerpt: string;
  content: string;
  author: {
    name: string;
    role: string;
    avatar?: string;
  };
  publishedAt: string;
  readTimeMin: number;
  category: 'Fatigue Science' | 'Sensor Biomechanics' | 'Clinical Research' | 'Safety Standards' | 'Engineering';
  tags: string[];
  coverImage?: string;
  featured?: boolean;
}
