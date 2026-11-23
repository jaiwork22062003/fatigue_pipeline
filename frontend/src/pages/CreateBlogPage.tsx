import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Save, Eye, Edit3, Image, Sparkles, Tag, Check, AlertCircle } from 'lucide-react';
import { BlogPost } from '../types';
import { saveNewBlog } from '../services/api';

const DEFAULT_COVER_SUGGESTIONS = [
  'https://images.unsplash.com/photo-1576091160550-2173dba999ef?auto=format&fit=crop&w=1200&q=80',
  'https://images.unsplash.com/photo-1507668077129-56e32842fceb?auto=format&fit=crop&w=1200&q=80',
  'https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=1200&q=80',
  'https://images.unsplash.com/photo-1516549655169-df83a0774514?auto=format&fit=crop&w=1200&q=80'
];

export const CreateBlogPage: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'write' | 'preview'>('write');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form Fields
  const [title, setTitle] = useState('');
  const [slug, setSlug] = useState('');
  const [category, setCategory] = useState<BlogPost['category']>('Fatigue Science');
  const [excerpt, setExcerpt] = useState('');
  const [content, setContent] = useState('');
  const [authorName, setAuthorName] = useState('Dr. Jatin Thakur');
  const [authorRole, setAuthorRole] = useState('Principal Biomechanics Architect');
  const [coverImage, setCoverImage] = useState(DEFAULT_COVER_SUGGESTIONS[0]);
  const [tagsInput, setTagsInput] = useState('fatigue, sensors, dual-imu, clinical');
  const [readTimeMin, setReadTimeMin] = useState(6);

  // Auto slug generator
  const handleTitleChange = (val: string) => {
    setTitle(val);
    const autoSlug = val
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/(^-|-$)+/g, '');
    setSlug(autoSlug);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!title.trim()) {
      setError('Title is required.');
      return;
    }
    if (!excerpt.trim()) {
      setError('Excerpt summary is required.');
      return;
    }
    if (!content.trim()) {
      setError('Content body is required.');
      return;
    }

    const finalSlug = slug.trim() || title.toLowerCase().replace(/[^a-z0-9]+/g, '-');
    const tags = tagsInput.split(',').map(t => t.trim()).filter(Boolean);

    const newPost: BlogPost = {
      id: `post-${Date.now()}`,
      title: title.trim(),
      slug: finalSlug,
      excerpt: excerpt.trim(),
      content: content.trim(),
      publishedAt: new Date().toISOString().split('T')[0],
      readTimeMin: Number(readTimeMin) || 5,
      category,
      coverImage: coverImage.trim() || undefined,
      author: {
        name: authorName.trim() || 'OWN Sense Team',
        role: authorRole.trim() || 'Biomechanics Research',
      },
      tags
    };

    setSubmitting(true);
    try {
      await saveNewBlog(newPost);
      navigate(`/blog/${newPost.slug}`);
    } catch (err: any) {
      setError(err?.message || 'Failed to publish blog post.');
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen pb-24">
      {/* Top Bar */}
      <div className="border-b border-slate-800 bg-slate-900/60 sticky top-14 z-30 backdrop-blur-md">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link
            to="/blog"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-cyan-400 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Blog
          </Link>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setActiveTab('write')}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                activeTab === 'write'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              <Edit3 className="w-3.5 h-3.5" /> Write Form
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('preview')}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                activeTab === 'preview'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              <Eye className="w-3.5 h-3.5" /> Live Preview
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 pt-8">
        <div className="mb-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 mb-2">
            <Sparkles className="w-3.5 h-3.5" /> Research Publication Creator
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Upload New Research Post</h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Publish clinical studies, sensor firmware updates, or ergonomics whitepapers to the OWN Sense Hub.
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {activeTab === 'write' ? (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-5">
              {/* Title & Slug */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Article Title <span className="text-rose-400">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={title}
                    onChange={e => handleTitleChange(e.target.value)}
                    placeholder="e.g. Ground Reaction Forces and Bilateral Gait Asymmetry"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/60"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    URL Slug
                  </label>
                  <input
                    type="text"
                    value={slug}
                    onChange={e => setSlug(e.target.value)}
                    placeholder="ground-reaction-forces"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-cyan-300 font-mono placeholder-slate-500 focus:outline-none focus:border-cyan-500/60"
                  />
                </div>
              </div>

              {/* Category & Read Time */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Category <span className="text-rose-400">*</span>
                  </label>
                  <select
                    value={category}
                    onChange={e => setCategory(e.target.value as any)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-cyan-500/60"
                  >
                    <option value="Fatigue Science">Fatigue Science</option>
                    <option value="Sensor Biomechanics">Sensor Biomechanics</option>
                    <option value="Clinical Research">Clinical Research</option>
                    <option value="Safety Standards">Safety Standards</option>
                    <option value="Engineering">Engineering</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Estimated Read Time (minutes)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="60"
                    value={readTimeMin}
                    onChange={e => setReadTimeMin(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-cyan-500/60"
                  />
                </div>
              </div>

              {/* Excerpt */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Executive Summary / Excerpt <span className="text-rose-400">*</span>
                </label>
                <textarea
                  rows={2}
                  required
                  value={excerpt}
                  onChange={e => setExcerpt(e.target.value)}
                  placeholder="Provide a concise 1-2 sentence overview of the research findings or technical architecture..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/60 leading-relaxed"
                />
              </div>

              {/* Cover Image URL */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1 flex items-center gap-1.5">
                  <Image className="w-3.5 h-3.5 text-cyan-400" /> Cover Image URL
                </label>
                <input
                  type="url"
                  value={coverImage}
                  onChange={e => setCoverImage(e.target.value)}
                  placeholder="https://..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-300 placeholder-slate-500 focus:outline-none focus:border-cyan-500/60 font-mono"
                />
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-[11px] text-slate-500">Preset previews:</span>
                  {DEFAULT_COVER_SUGGESTIONS.map((img, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => setCoverImage(img)}
                      className={`w-6 h-6 rounded-md overflow-hidden border ${
                        coverImage === img ? 'border-cyan-400' : 'border-slate-800 opacity-60'
                      }`}
                    >
                      <img src={img} alt="Preset" className="w-full h-full object-cover" />
                    </button>
                  ))}
                </div>
              </div>

              {/* Author Details */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-800">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Author Name
                  </label>
                  <input
                    type="text"
                    value={authorName}
                    onChange={e => setAuthorName(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-cyan-500/60"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Author Role / Affiliation
                  </label>
                  <input
                    type="text"
                    value={authorRole}
                    onChange={e => setAuthorRole(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-cyan-500/60"
                  />
                </div>
              </div>

              {/* Tags */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1 flex items-center gap-1.5">
                  <Tag className="w-3.5 h-3.5 text-cyan-400" /> Tags (comma-separated)
                </label>
                <input
                  type="text"
                  value={tagsInput}
                  onChange={e => setTagsInput(e.target.value)}
                  placeholder="biomechanics, dual-imu, fatigue, gait"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-300 focus:outline-none focus:border-cyan-500/60"
                />
              </div>

              {/* Content Body */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-medium text-slate-300">
                    Publication Body (Markdown Supported) <span className="text-rose-400">*</span>
                  </label>
                  <span className="text-[11px] text-slate-500">Supports # H1, ## H2, - lists, `code`, & blockquotes</span>
                </div>
                <textarea
                  rows={14}
                  required
                  value={content}
                  onChange={e => setContent(e.target.value)}
                  placeholder={`# Executive Summary\n\nWrite your findings here...\n\n## Methodology & Data Acquisition\n\nExplain how dual insole IMUs or PPG were collected...`}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs font-mono text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500/60 leading-relaxed"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end gap-3">
              <Link
                to="/blog"
                className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors"
              >
                Cancel
              </Link>
              <button
                type="submit"
                disabled={submitting}
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 transition-all duration-200 disabled:opacity-50"
              >
                {submitting ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                    Publishing...
                  </>
                ) : (
                  <>
                    <Save className="w-3.5 h-3.5" />
                    Publish Article to Blog
                  </>
                )}
              </button>
            </div>
          </form>
        ) : (
          /* Live Preview Mode */
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 sm:p-10">
            <div className="mb-4 text-xs text-cyan-400 font-semibold uppercase tracking-wider">
              {category} • {readTimeMin} MIN READ
            </div>
            <h1 className="text-3xl font-bold text-white mb-3">{title || 'Untitled Article'}</h1>
            <p className="text-slate-300 text-sm italic mb-6 border-l-2 border-cyan-400 pl-3">
              {excerpt || 'No excerpt provided.'}
            </p>

            {coverImage && (
              <div className="mb-6 rounded-xl overflow-hidden max-h-72">
                <img src={coverImage} alt="Cover Preview" className="w-full object-cover" />
              </div>
            )}

            <div className="whitespace-pre-wrap text-sm text-slate-300 leading-relaxed font-sans">
              {content || 'Start typing in the "Write Form" tab to see live preview here...'}
            </div>

            <div className="mt-8 pt-4 border-t border-slate-800 flex justify-between items-center text-xs text-slate-400">
              <div>By {authorName} ({authorRole})</div>
              <button
                onClick={() => setActiveTab('write')}
                className="text-cyan-400 hover:underline"
              >
                Return to Editor
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
