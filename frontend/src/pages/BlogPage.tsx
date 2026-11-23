import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, Search, PlusCircle, Sparkles, Filter, RefreshCw } from 'lucide-react';
import { BlogPost } from '../types';
import { fetchBlogs } from '../services/api';
import { BlogCard } from '../components/Blog/BlogCard';

const CATEGORIES = [
  'All',
  'Fatigue Science',
  'Sensor Biomechanics',
  'Clinical Research',
  'Safety Standards',
  'Engineering'
] as const;

export const BlogPage: React.FC = () => {
  const [blogs, setBlogs] = useState<BlogPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  const loadBlogs = async () => {
    setLoading(true);
    try {
      const posts = await fetchBlogs();
      setBlogs(posts);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBlogs();
  }, []);

  const filtered = blogs.filter(post => {
    const matchesCat = selectedCategory === 'All' || post.category === selectedCategory;
    const query = search.toLowerCase().trim();
    const matchesSearch =
      !query ||
      post.title.toLowerCase().includes(query) ||
      post.excerpt.toLowerCase().includes(query) ||
      post.tags?.some(t => t.toLowerCase().includes(query)) ||
      post.author.name.toLowerCase().includes(query);
    return matchesCat && matchesSearch;
  });

  const featuredPost = filtered.length > 0 ? filtered[0] : null;
  const remainingPosts = filtered.length > 1 ? filtered.slice(1) : [];

  return (
    <div className="min-h-screen pb-20">
      {/* Hero Header */}
      <div className="relative overflow-hidden border-b border-slate-800 bg-gradient-to-b from-slate-900/90 via-slate-950 to-slate-950 py-16 px-4 sm:px-6 lg:px-8">
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-1/2 left-1/3 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-7xl mx-auto relative z-10">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 mb-4">
                <Sparkles className="w-3.5 h-3.5" /> Biometrics & Ergonomics Journal
              </div>
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white tracking-tight leading-tight">
                OWN Sense <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">Research & Blog</span>
              </h1>
              <p className="mt-3 text-base sm:text-lg text-slate-300 max-w-2xl">
                Explore peer-reviewed methodologies, insole sensor fusion engineering, dual-IMU biomechanics, and proactive worker safety research.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Link
                to="/blog/new"
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-sm shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/30 transition-all duration-200"
              >
                <PlusCircle className="w-4 h-4" />
                Upload New Blog
              </Link>
            </div>
          </div>

          {/* Search & Categories Bar */}
          <div className="mt-10 flex flex-col sm:flex-row gap-4 items-center justify-between">
            {/* Search Input */}
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search research, authors, tags..."
                className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/50 transition-all"
              />
            </div>

            {/* Category Filter Pills */}
            <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto pb-1 scrollbar-none">
              <Filter className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
              {CATEGORIES.map(cat => {
                const active = selectedCategory === cat;
                return (
                  <button
                    key={cat}
                    onClick={() => setSelectedCategory(cat)}
                    className={`whitespace-nowrap px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                      active
                        ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                        : 'bg-slate-900 text-slate-400 border border-slate-800 hover:border-slate-700 hover:text-slate-200'
                    }`}
                  >
                    {cat}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-10">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400">
            <RefreshCw className="w-8 h-8 animate-spin text-cyan-400 mb-3" />
            <p className="text-sm font-medium">Loading research publications...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-12 text-center max-w-md mx-auto">
            <BookOpen className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <h3 className="text-lg font-bold text-slate-200 mb-1">No articles found</h3>
            <p className="text-xs text-slate-400 mb-6">
              No blogs match your filter criteria. Try adjusting your search or upload a new article.
            </p>
            <div className="flex justify-center gap-3">
              <button
                onClick={() => { setSelectedCategory('All'); setSearch(''); }}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700"
              >
                Clear Filters
              </button>
              <Link
                to="/blog/new"
                className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-cyan-500 text-slate-950 hover:bg-cyan-400"
              >
                Create Blog
              </Link>
            </div>
          </div>
        ) : (
          <div className="space-y-12">
            {/* Featured Hero Article */}
            {featuredPost && (
              <div>
                <BlogCard post={featuredPost} featured={true} />
              </div>
            )}

            {/* Remaining Grid */}
            {remainingPosts.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-cyan-400" /> Latest Publications
                  </h2>
                  <span className="text-xs text-slate-400">{remainingPosts.length} more articles</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {remainingPosts.map(post => (
                    <BlogCard key={post.id} post={post} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
