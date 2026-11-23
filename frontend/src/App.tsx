import React from 'react';
import { Routes, Route, Navigate, Link } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { BlogPage } from './pages/BlogPage';
import { BlogPostPage } from './pages/BlogPostPage';
import { CreateBlogPage } from './pages/CreateBlogPage';
import { HeartHandshake, Shield, ExternalLink, Activity } from 'lucide-react';

export const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      <Navbar />

      <main className="flex-1">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/blog" element={<BlogPage />} />
          <Route path="/blog/new" element={<CreateBlogPage />} />
          <Route path="/blog/:slug" element={<BlogPostPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      {/* Modern Footer */}
      <footer className="border-t border-slate-900 bg-[#060911] text-xs text-slate-500 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <Activity className="w-4 h-4" />
            </div>
            <div>
              <span className="font-bold text-slate-300">OWN Sense Systems</span>
              <span className="text-slate-600 ml-2">Smart Footwear Fatigue & Ergonomics Platform</span>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <Link to="/" className="hover:text-cyan-400 transition-colors">
              Live Dashboard
            </Link>
            <Link to="/blog" className="hover:text-cyan-400 transition-colors">
              Research & Blog
            </Link>
            <Link to="/blog/new" className="hover:text-cyan-400 transition-colors">
              Publish Insight
            </Link>
          </div>

          <div className="text-[11px] text-slate-600">
            © {new Date().getFullYear()} OWN Sense. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
