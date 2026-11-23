import { BlogPost, JobStatus, SessionReport, UserDatesCatalog } from '../types';
import { INITIAL_BLOGS } from '../data/initialBlogs';

const API_BASE = ''; // uses vite proxy or relative path when served by python server

const LOCAL_STORAGE_BLOGS_KEY = 'own_sense_blogs_v1';

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/status`, { method: 'GET', signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}

export async function fetchTelemetryData(): Promise<Record<string, SessionReport>> {
  try {
    const res = await fetch(`${API_BASE}/api/data`);
    if (!res.ok) throw new Error('Failed to load telemetry data');
    const data = await res.json();
    return data.reports || {};
  } catch (err) {
    console.warn('Backend unavailable, using empty telemetry dictionary:', err);
    return {};
  }
}

export async function fetchUserDates(): Promise<UserDatesCatalog> {
  try {
    const res = await fetch(`${API_BASE}/api/users-and-dates`);
    if (!res.ok) throw new Error('Failed to load users and dates');
    return await res.json();
  } catch (err) {
    console.warn('Backend unavailable, using fallback catalog:', err);
    return {
      users: ['3mSa_i'],
      user_dates: {
        '3mSa_i': {
          '2026-03-27': {
            files: ['3mSa_i_rawdata_2026-03-27_04-08.txt'],
            has_report: true,
            count: 1,
            total_size_mb: 27.1
          }
        }
      }
    };
  }
}

export async function triggerPipelineJob(payload: {
  user_id: string;
  start_date: string;
  end_date: string;
  force_download?: boolean;
}): Promise<void> {
  const res = await fetch(`${API_BASE}/api/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Execution request failed' }));
    throw new Error(err.message || 'Execution request failed');
  }
}

export async function fetchJobStatus(): Promise<JobStatus> {
  const res = await fetch(`${API_BASE}/api/status`);
  if (!res.ok) throw new Error('Failed to fetch job status');
  return await res.json();
}

// ==========================================
// BLOG API & PERSISTENCE
// ==========================================

export async function fetchBlogs(): Promise<BlogPost[]> {
  // 1. Try backend API first
  try {
    const res = await fetch(`${API_BASE}/api/blogs`, { signal: AbortSignal.timeout(3000) });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        // Cache to localStorage
        localStorage.setItem(LOCAL_STORAGE_BLOGS_KEY, JSON.stringify(data));
        return data;
      }
    }
  } catch {
    // Backend endpoint not ready or offline
  }

  // 2. Try localStorage
  try {
    const cached = localStorage.getItem(LOCAL_STORAGE_BLOGS_KEY);
    if (cached) {
      const parsed = JSON.parse(cached);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed;
      }
    }
  } catch {
    // Ignore parse error
  }

  // 3. Fallback to pre-configured clinical blog posts
  localStorage.setItem(LOCAL_STORAGE_BLOGS_KEY, JSON.stringify(INITIAL_BLOGS));
  return INITIAL_BLOGS;
}

export async function saveNewBlog(blog: Omit<BlogPost, 'id' | 'publishedAt'>): Promise<BlogPost> {
  const fullPost: BlogPost = {
    ...blog,
    id: `blog-${Date.now()}`,
    publishedAt: new Date().toISOString().split('T')[0]
  };

  // 1. Persist to local storage immediately
  const existing = await fetchBlogs();
  const updated = [fullPost, ...existing];
  localStorage.setItem(LOCAL_STORAGE_BLOGS_KEY, JSON.stringify(updated));

  // 2. Also attempt to post to backend server if available
  try {
    await fetch(`${API_BASE}/api/blogs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(fullPost)
    });
  } catch (e) {
    console.info('Backend blog sync skipped (persisted locally):', e);
  }

  return fullPost;
}

export async function getBlogBySlug(slug: string): Promise<BlogPost | undefined> {
  const blogs = await fetchBlogs();
  return blogs.find(b => b.slug === slug);
}
