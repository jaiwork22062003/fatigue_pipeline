import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Clock, Calendar, User, Share2, Tag, Check, BookOpen, AlertCircle } from 'lucide-react';
import { BlogPost } from '../types';
import { getBlogBySlug } from '../services/api';

export const BlogPostPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const [post, setPost] = useState<BlogPost | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    async function load() {
      if (!slug) return;
      setLoading(true);
      try {
        const p = await getBlogBySlug(slug);
        setPost(p);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [slug]);

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-slate-400">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-cyan-400 border-r-transparent mr-3" />
        <span className="text-sm font-medium">Loading research paper...</span>
      </div>
    );
  }

  if (!post) {
    return (
      <div className="min-h-screen max-w-3xl mx-auto px-4 py-20 text-center">
        <AlertCircle className="w-12 h-12 text-rose-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">Article Not Found</h2>
        <p className="text-slate-400 text-sm mb-6">
          The requested publication could not be found or may have been relocated.
        </p>
        <Link
          to="/blog"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-500 text-slate-950 font-bold text-sm hover:bg-cyan-400"
        >
          <ArrowLeft className="w-4 h-4" /> Return to Research Hub
        </Link>
      </div>
    );
  }

  // Format markdown-like text to formatted HTML elements
  const renderFormattedContent = (content: string) => {
    const lines = content.split('\n');
    const elements: React.ReactNode[] = [];
    let inCodeBlock = false;
    let codeBuffer: string[] = [];

    lines.forEach((line, idx) => {
      // Code block handling
      if (line.startsWith('```')) {
        if (inCodeBlock) {
          elements.push(
            <pre key={`code-${idx}`} className="bg-slate-950 border border-slate-800 rounded-xl p-4 overflow-x-auto text-xs text-cyan-300 font-mono my-4">
              <code>{codeBuffer.join('\n')}</code>
            </pre>
          );
          codeBuffer = [];
          inCodeBlock = false;
        } else {
          inCodeBlock = true;
        }
        return;
      }

      if (inCodeBlock) {
        codeBuffer.push(line);
        return;
      }

      // Headers
      if (line.startsWith('# ')) {
        elements.push(
          <h1 key={idx} className="text-3xl font-extrabold text-white mt-10 mb-4 tracking-tight">
            {line.replace('# ', '')}
          </h1>
        );
      } else if (line.startsWith('## ')) {
        elements.push(
          <h2 key={idx} className="text-2xl font-bold text-cyan-300 mt-8 mb-3 border-b border-slate-800 pb-2">
            {line.replace('## ', '')}
          </h2>
        );
      } else if (line.startsWith('### ')) {
        elements.push(
          <h3 key={idx} className="text-lg font-semibold text-white mt-6 mb-2">
            {line.replace('### ', '')}
          </h3>
        );
      } else if (line.startsWith('> [!NOTE]') || line.startsWith('> [!IMPORTANT]') || line.startsWith('> [!WARNING]')) {
        elements.push(
          <div key={idx} className="my-4 p-4 rounded-xl bg-cyan-500/10 border-l-4 border-cyan-400 text-cyan-200 text-sm leading-relaxed">
            {line.replace(/^> \[[^\]]+\]\s*/, '')}
          </div>
        );
      } else if (line.startsWith('> ')) {
        elements.push(
          <blockquote key={idx} className="my-4 pl-4 border-l-2 border-slate-600 italic text-slate-300 text-sm">
            {line.replace('> ', '')}
          </blockquote>
        );
      } else if (line.startsWith('- ') || line.startsWith('* ')) {
        elements.push(
          <li key={idx} className="text-slate-300 text-sm leading-relaxed ml-4 list-disc my-1">
            {line.replace(/^[-*]\s+/, '')}
          </li>
        );
      } else if (line.trim() === '') {
        elements.push(<div key={idx} className="h-3" />);
      } else {
        elements.push(
          <p key={idx} className="text-slate-300 text-sm sm:text-base leading-relaxed my-2">
            {line}
          </p>
        );
      }
    });

    return elements;
  };

  return (
    <div className="min-h-screen pb-24">
      {/* Top Banner & Navigation */}
      <div className="border-b border-slate-800 bg-slate-900/60 sticky top-14 z-30 backdrop-blur-md">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <button
            onClick={() => navigate('/blog')}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-cyan-400 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Research Hub
          </button>

          <button
            onClick={handleCopyLink}
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition-colors border border-slate-700"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" /> Copied!
              </>
            ) : (
              <>
                <Share2 className="w-3.5 h-3.5 text-slate-400" /> Share
              </>
            )}
          </button>
        </div>
      </div>

      <article className="max-w-4xl mx-auto px-4 sm:px-6 pt-10">
        {/* Meta Header */}
        <div className="space-y-4 mb-8">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="px-3 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-semibold">
              {post.category}
            </span>
            <span className="flex items-center gap-1 text-slate-400">
              <Clock className="w-3.5 h-3.5" /> {post.readTimeMin} min read
            </span>
            <span className="text-slate-600">•</span>
            <span className="flex items-center gap-1 text-slate-400">
              <Calendar className="w-3.5 h-3.5" /> {post.publishedAt}
            </span>
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-white leading-tight tracking-tight">
            {post.title}
          </h1>

          <p className="text-base sm:text-lg text-slate-300 leading-relaxed font-normal border-l-2 border-cyan-500/50 pl-4 py-1">
            {post.excerpt}
          </p>

          {/* Author Card */}
          <div className="flex items-center gap-4 pt-4 border-t border-slate-800">
            {post.author.avatar ? (
              <img
                src={post.author.avatar}
                alt={post.author.name}
                className="w-11 h-11 rounded-full object-cover border border-cyan-500/30"
              />
            ) : (
              <div className="w-11 h-11 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-cyan-400">
                <User className="w-5 h-5" />
              </div>
            )}
            <div>
              <div className="text-sm font-bold text-white">{post.author.name}</div>
              <div className="text-xs text-slate-400">{post.author.role}</div>
            </div>
          </div>
        </div>

        {/* Hero Cover Image */}
        {post.coverImage && (
          <div className="mb-10 rounded-2xl overflow-hidden border border-slate-800 bg-slate-950 shadow-2xl">
            <img src={post.coverImage} alt={post.title} className="w-full h-80 object-cover" />
          </div>
        )}

        {/* Content Body */}
        <div className="prose prose-invert max-w-none text-slate-300">
          {renderFormattedContent(post.content)}
        </div>

        {/* Tags Footnote */}
        {post.tags && post.tags.length > 0 && (
          <div className="mt-12 pt-6 border-t border-slate-800">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-slate-400 font-semibold mr-1">Indexed Keywords:</span>
              {post.tags.map(t => (
                <span
                  key={t}
                  className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-300"
                >
                  <Tag className="w-3 h-3 text-cyan-400" /> {t}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Bottom CTA to Return */}
        <div className="mt-14 p-8 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900/90 to-cyan-950/30 border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <h4 className="text-base font-bold text-white mb-1">Explore Industrial Biometrics Live</h4>
            <p className="text-xs text-slate-400">Monitor live session telemetry, heart rate reserves, and cadence asymmetry in real time.</p>
          </div>
          <Link
            to="/"
            className="whitespace-nowrap px-4 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-colors shadow-lg shadow-cyan-500/20"
          >
            Go to Live Dashboard
          </Link>
        </div>
      </article>
    </div>
  );
};
