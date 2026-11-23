import React from 'react';
import { Link } from 'react-router-dom';
import { Clock, Calendar, ArrowRight, User, Tag } from 'lucide-react';
import { BlogPost } from '../../types';

interface BlogCardProps {
  post: BlogPost;
  featured?: boolean;
}

const CATEGORY_COLORS: Record<string, string> = {
  'Fatigue Science': 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
  'Sensor Biomechanics': 'bg-purple-500/10 text-purple-400 border-purple-500/30',
  'Clinical Research': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  'Safety Standards': 'bg-amber-500/10 text-amber-400 border-amber-500/30',
  'Engineering': 'bg-blue-500/10 text-blue-400 border-blue-500/30',
};

export const BlogCard: React.FC<BlogCardProps> = ({ post, featured = false }) => {
  const categoryClass = CATEGORY_COLORS[post.category] || 'bg-slate-800 text-slate-300 border-slate-700';

  if (featured) {
    return (
      <div className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900/90 to-slate-950 border border-cyan-500/30 hover:border-cyan-400/60 transition-all duration-300 shadow-xl shadow-cyan-950/20">
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 via-blue-500/5 to-transparent pointer-events-none" />
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 p-6 sm:p-8">
          {post.coverImage && (
            <div className="lg:col-span-5 relative overflow-hidden rounded-xl h-64 lg:h-auto min-h-[220px]">
              <img
                src={post.coverImage}
                alt={post.title}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent" />
              <div className="absolute top-3 left-3">
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-400/40 backdrop-blur-md">
                  ★ Featured Insight
                </span>
              </div>
            </div>
          )}

          <div className={`${post.coverImage ? 'lg:col-span-7' : 'lg:col-span-12'} flex flex-col justify-between`}>
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-3 text-xs">
                <span className={`px-2.5 py-0.5 rounded-full border font-medium ${categoryClass}`}>
                  {post.category}
                </span>
                <span className="flex items-center text-slate-400 gap-1">
                  <Clock className="w-3.5 h-3.5" /> {post.readTimeMin} min read
                </span>
                <span className="text-slate-600">•</span>
                <span className="flex items-center text-slate-400 gap-1">
                  <Calendar className="w-3.5 h-3.5" /> {post.publishedAt}
                </span>
              </div>

              <Link to={`/blog/${post.slug}`}>
                <h2 className="text-2xl sm:text-3xl font-bold text-white group-hover:text-cyan-400 transition-colors leading-snug mb-3">
                  {post.title}
                </h2>
              </Link>

              <p className="text-slate-300/90 text-sm sm:text-base leading-relaxed line-clamp-3 mb-4">
                {post.excerpt}
              </p>

              {post.tags && post.tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-5">
                  {post.tags.slice(0, 4).map(t => (
                    <span key={t} className="inline-flex items-center gap-1 text-[11px] text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded-md border border-slate-700/60">
                      <Tag className="w-2.5 h-2.5 text-cyan-400" /> {t}
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-slate-800">
              <div className="flex items-center gap-3">
                {post.author.avatar ? (
                  <img src={post.author.avatar} alt={post.author.name} className="w-9 h-9 rounded-full object-cover border border-cyan-500/30" />
                ) : (
                  <div className="w-9 h-9 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-cyan-400">
                    <User className="w-4 h-4" />
                  </div>
                )}
                <div>
                  <div className="text-xs font-semibold text-slate-200">{post.author.name}</div>
                  <div className="text-[11px] text-slate-400">{post.author.role}</div>
                </div>
              </div>

              <Link
                to={`/blog/${post.slug}`}
                className="inline-flex items-center gap-1.5 text-xs font-medium text-cyan-400 hover:text-cyan-300 transition-colors group-hover:translate-x-1 duration-200"
              >
                Read Deep-Dive <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="group flex flex-col justify-between rounded-xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 hover:bg-slate-900 transition-all duration-200 overflow-hidden shadow-lg hover:shadow-cyan-950/10">
      {post.coverImage && (
        <div className="relative h-48 overflow-hidden bg-slate-950">
          <img
            src={post.coverImage}
            alt={post.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-transparent to-transparent" />
          <div className="absolute top-3 left-3">
            <span className={`px-2.5 py-0.5 rounded-full border text-xs font-medium backdrop-blur-md ${categoryClass}`}>
              {post.category}
            </span>
          </div>
        </div>
      )}

      <div className="p-5 flex-1 flex flex-col justify-between">
        <div>
          {!post.coverImage && (
            <div className="flex items-center gap-2 mb-3">
              <span className={`px-2 py-0.5 rounded-full border text-[11px] font-medium ${categoryClass}`}>
                {post.category}
              </span>
            </div>
          )}

          <div className="flex items-center gap-2 text-[11px] text-slate-400 mb-2">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" /> {post.readTimeMin}m
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" /> {post.publishedAt}
            </span>
          </div>

          <Link to={`/blog/${post.slug}`}>
            <h3 className="text-base font-semibold text-slate-100 group-hover:text-cyan-400 transition-colors line-clamp-2 mb-2 leading-snug">
              {post.title}
            </h3>
          </Link>

          <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed mb-4">
            {post.excerpt}
          </p>
        </div>

        <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            {post.author.avatar ? (
              <img src={post.author.avatar} alt={post.author.name} className="w-6 h-6 rounded-full object-cover border border-slate-700" />
            ) : (
              <div className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center text-slate-400">
                <User className="w-3 h-3" />
              </div>
            )}
            <span className="text-[11px] text-slate-300 font-medium truncate max-w-[110px]">{post.author.name}</span>
          </div>

          <Link
            to={`/blog/${post.slug}`}
            className="text-cyan-400 hover:text-cyan-300 font-medium inline-flex items-center gap-1 text-[11px]"
          >
            Read <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </div>
      </div>
    </div>
  );
};
