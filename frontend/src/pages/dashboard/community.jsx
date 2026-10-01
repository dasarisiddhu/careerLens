import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { pageTransition, staggerContainer, staggerItem } from '../../utils/animations'
import { api } from '../../services/api'
import {
  Heart,
  MessageCircle,
  Github,
  Plus,
  X,
  Send,
  Loader2,
  Trash2,
  Globe,
  Briefcase,
  DollarSign,
  BookOpen,
  Users,
  Code2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { GlassCard, Badge } from '../../components/ui'

const POST_TYPES = [
  { value: 'all', label: 'All Posts', icon: Globe, iconClass: 'text-[#64748B]' },
  { value: 'project', label: 'Projects', icon: Code2, iconClass: 'text-[#2563EB]' },
  { value: 'job', label: 'Job Seeking', icon: Briefcase, iconClass: 'text-[#0284C7]' },
  { value: 'funding', label: 'Funding', icon: DollarSign, iconClass: 'text-[#16A34A]' },
  { value: 'blog', label: 'Blog / Tips', icon: BookOpen, iconClass: 'text-[#D97706]' },
  { value: 'hiring', label: 'Hiring', icon: Users, iconClass: 'text-[#2563EB]' },
]

const TYPE_STYLES = {
  project: { className: 'text-[11px] font-bold text-[#2563EB] bg-blue-50 px-2.5 py-0.5 rounded-full border border-blue-100', label: 'Project' },
  job: { className: 'text-[11px] font-bold text-[#0284C7] bg-sky-50 px-2.5 py-0.5 rounded-full border border-sky-100', label: 'Job Seeking' },
  funding: { className: 'text-[11px] font-bold text-[#16A34A] bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-100', label: 'Funding' },
  blog: { className: 'text-[11px] font-bold text-[#D97706] bg-amber-50 px-2.5 py-0.5 rounded-full border border-amber-100', label: 'Blog' },
  hiring: { className: 'text-[11px] font-bold text-[#2563EB] bg-blue-50 px-2.5 py-0.5 rounded-full border border-blue-100', label: 'Hiring' },
}

const formatTime = (iso) => {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  if (hours < 24) return `${hours}h ago`
  return `${days}d ago`
}

const getInitials = (name) => {
  if (!name) return '?'
  return name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

const avatarPalette = [
  'linear-gradient(135deg,#2563EB,#1D4ED8)',
  'linear-gradient(135deg,#0284C7,#0369A1)',
  'linear-gradient(135deg,#10B981,#047857)',
  'linear-gradient(135deg,#0F172A,#334155)',
  'linear-gradient(135deg,#0D9488,#0F766E)',
]

const getAvatarColor = (name) => avatarPalette[(name?.charCodeAt(0) || 0) % avatarPalette.length]

function CreatePostModal({ onClose, onCreated }) {
  const [form, setForm] = useState({
    post_type: 'project',
    title: '',
    content: '',
    demo_url: '',
    github_url: '',
    tags: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handle = (key, value) => setForm((current) => ({ ...current, [key]: value }))

  const handleSubmit = async () => {
    if (!form.title.trim() || !form.content.trim()) {
      setError('Title and content are required.')
      return
    }

    setLoading(true)
    setError('')
    try {
      const tags = form.tags.split(',').map((tag) => tag.trim()).filter(Boolean)
      await api.createPost({ ...form, tags })
      onCreated()
      onClose()
    } catch (requestError) {
      setError(requestError.message || 'Failed to publish post.')
    }
    setLoading(false)
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm"
      onClick={(event) => event.target === event.currentTarget && onClose()}
    >
      <GlassCard className="w-full max-w-xl p-6 sm:p-8 space-y-4 border-white/95 shadow-glass-lg relative">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-[#0B0F19]">Create Community Post</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-1.5 text-[#64748B] hover:bg-slate-100 hover:text-[#0B0F19] transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs font-semibold text-[#E11D48]">
            {error}
          </div>
        )}

        <div>
          <label className="mb-2 block text-xs font-bold uppercase tracking-wider text-[#0B0F19]">Category</label>
          <div className="flex flex-wrap gap-2">
            {POST_TYPES.filter((type) => type.value !== 'all').map(({ value, label, icon: Icon, iconClass }) => {
              const isSelected = form.post_type === value
              return (
                <button
                  type="button"
                  key={value}
                  onClick={() => handle('post_type', value)}
                  className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold transition-all ${
                    isSelected
                      ? 'border-[#2563EB] bg-blue-50 text-[#2563EB]'
                      : 'border-slate-200 bg-white text-[#475569] hover:bg-slate-50 hover:text-[#0B0F19]'
                  }`}
                >
                  <Icon size={13} className={isSelected ? 'text-[#2563EB]' : iconClass} />
                  <span>{label}</span>
                </button>
              )
            })}
          </div>
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-[#0B0F19]">Title *</label>
          <input
            value={form.title}
            onChange={(e) => handle('title', e.target.value)}
            placeholder="What are you building or sharing?"
            className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-xs sm:text-sm font-semibold text-[#0B0F19] shadow-xs focus:border-[#2563EB] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/20"
          />
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-[#0B0F19]">Content *</label>
          <textarea
            value={form.content}
            onChange={(e) => handle('content', e.target.value)}
            rows={4}
            placeholder="Share details, context, questions, or opportunities..."
            className="w-full rounded-xl border border-slate-200 bg-white p-3.5 text-xs sm:text-sm text-[#0B0F19] shadow-xs focus:border-[#2563EB] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/20 resize-none"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-[#0B0F19]">Live URL (optional)</label>
            <input
              value={form.demo_url}
              onChange={(e) => handle('demo_url', e.target.value)}
              placeholder="https://..."
              className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs text-[#0B0F19] shadow-xs focus:border-[#2563EB] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/20"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-[#0B0F19]">GitHub URL (optional)</label>
            <input
              value={form.github_url}
              onChange={(e) => handle('github_url', e.target.value)}
              placeholder="https://github.com/..."
              className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs text-[#0B0F19] shadow-xs focus:border-[#2563EB] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/20"
            />
          </div>
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-[#0B0F19]">Tags (comma separated)</label>
          <input
            value={form.tags}
            onChange={(e) => handle('tags', e.target.value)}
            placeholder="react, python, fast-api, ai"
            className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs text-[#0B0F19] shadow-xs focus:border-[#2563EB] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/20"
          />
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="py-2.5 px-5 rounded-full border border-slate-200 bg-white text-xs font-bold text-[#475569] hover:bg-slate-50 transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={loading}
            className="flex items-center gap-2 py-2.5 px-6 rounded-full bg-[#0B0F19] text-white font-bold text-xs hover:bg-[#1E293B] transition-all shadow-md disabled:opacity-50"
          >
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
            <span>Publish Post</span>
          </button>
        </div>
      </GlassCard>
    </div>
  )
}

function CommentSection({ postId, currentUser }) {
  const [comments, setComments] = useState([])
  const [newComment, setNewComment] = useState('')
  const [loading, setLoading] = useState(false)
  const [fetching, setFetching] = useState(true)

  useEffect(() => {
    fetchComments()
  }, [postId])

  const fetchComments = async () => {
    setFetching(true)
    try {
      const response = await api.getComments(postId)
      setComments(Array.isArray(response?.comments) ? response.comments : [])
    } catch {}
    setFetching(false)
  }

  const handleComment = async () => {
    if (!newComment.trim()) return
    setLoading(true)
    try {
      const response = await api.addComment({ post_id: postId, content: newComment })
      if (response?.comment) {
        setComments((current) => [...current, response.comment])
      }
      setNewComment('')
    } catch {}
    setLoading(false)
  }

  const handleDelete = async (commentId) => {
    try {
      await api.deleteComment(commentId)
      setComments((current) => current.filter((comment) => comment.id !== commentId))
    } catch {}
  }

  return (
    <div className="mt-4 space-y-3 border-t border-slate-100 pt-4">
      {fetching ? (
        <div className="flex justify-center py-3">
          <Loader2 size={16} className="animate-spin text-[#2563EB]" />
        </div>
      ) : (
        <div className="max-h-64 space-y-2.5 overflow-y-auto pr-1">
          {comments.length === 0 && (
            <p className="py-2 text-center text-xs text-[#64748B]">No comments yet. Start the conversation.</p>
          )}
          {comments.map((comment) => (
            <div key={comment.id} className="flex items-start gap-2.5">
              <div
                className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white mt-0.5"
                style={{ background: getAvatarColor(comment.author_name) }}
              >
                {getInitials(comment.author_name)}
              </div>
              <div className="flex-1 rounded-xl bg-slate-50/80 border border-slate-200/60 px-3 py-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-bold text-[#0B0F19]">{comment.author_name || 'Anonymous'}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-[#64748B]">{formatTime(comment.created_at)}</span>
                    {comment.user_id === currentUser && (
                      <button
                        type="button"
                        onClick={() => handleDelete(comment.id)}
                        className="text-[#94A3B8] transition hover:text-rose-600"
                      >
                        <Trash2 size={11} />
                      </button>
                    )}
                  </div>
                </div>
                <p className="mt-1 text-xs text-[#334155] leading-relaxed">{comment.content}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <input
          value={newComment}
          onChange={(event) => setNewComment(event.target.value)}
          onKeyDown={(event) => event.key === 'Enter' && handleComment()}
          placeholder="Write a comment..."
          className="flex-1 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs text-[#0B0F19] shadow-xs focus:border-[#2563EB] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/20"
        />
        <button
          type="button"
          onClick={handleComment}
          disabled={loading || !newComment.trim()}
          className="flex items-center justify-center rounded-xl bg-[#0B0F19] text-white px-3 py-2 text-xs font-bold hover:bg-[#1E293B] disabled:opacity-50 shadow-xs"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
        </button>
      </div>
    </div>
  )
}

function PostCard({ post, likedPosts, currentUser, onLike, onDelete }) {
  const [showComments, setShowComments] = useState(false)
  const typeStyle = TYPE_STYLES[post.post_type] || TYPE_STYLES.project
  const isLiked = likedPosts.includes(post.id)
  const isOwner = post.user_id === currentUser

  return (
    <GlassCard className="p-5 sm:p-6 border-white/95 shadow-glass space-y-3.5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div
            className="flex h-10 w-10 items-center justify-center rounded-xl text-xs font-bold text-white shadow-xs"
            style={{ background: getAvatarColor(post.author_name) }}
          >
            {getInitials(post.author_name)}
          </div>
          <div>
            <p className="text-xs sm:text-sm font-bold text-[#0B0F19]">{post.author_name || 'Anonymous'}</p>
            <p className="text-[11px] text-[#64748B]">{formatTime(post.created_at)}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className={typeStyle.className}>{typeStyle.label}</span>
          {isOwner && (
            <button
              type="button"
              onClick={() => onDelete(post.id)}
              className="rounded-lg p-1 text-[#94A3B8] transition hover:text-rose-600"
            >
              <Trash2 size={13} />
            </button>
          )}
        </div>
      </div>

      <div className="space-y-1">
        <h3 className="text-sm sm:text-base font-bold text-[#0B0F19] leading-snug">{post.title}</h3>
        <p className="whitespace-pre-wrap text-xs sm:text-sm leading-relaxed text-[#475569]">{post.content}</p>
      </div>

      {(post.demo_url || post.github_url) && (
        <div className="flex flex-wrap gap-2 pt-1">
          {post.demo_url && (
            <a
              href={post.demo_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-[#0B0F19] hover:border-blue-200 hover:text-[#2563EB] transition-colors shadow-xs"
            >
              <Globe size={12} />
              <span>Live Preview</span>
            </a>
          )}
          {post.github_url && (
            <a
              href={post.github_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-[#0B0F19] hover:border-blue-200 hover:text-[#2563EB] transition-colors shadow-xs"
            >
              <Github size={12} />
              <span>Source Code</span>
            </a>
          )}
        </div>
      )}

      {Array.isArray(post.tags) && post.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-0.5">
          {post.tags.map((tag, idx) => (
            <span key={idx} className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-[#475569]">
              #{tag}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between border-t border-slate-100 pt-3 text-xs text-[#64748B]">
        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={() => onLike(post.id)}
            className={`flex items-center gap-1.5 font-semibold transition-colors ${
              isLiked ? 'text-[#E11D48]' : 'hover:text-[#0B0F19]'
            }`}
          >
            <Heart size={14} className={isLiked ? 'fill-[#E11D48]' : ''} />
            <span>{post.likes_count || 0}</span>
          </button>
          <button
            type="button"
            onClick={() => setShowComments(!showComments)}
            className="flex items-center gap-1.5 font-semibold hover:text-[#0B0F19] transition-colors"
          >
            <MessageCircle size={14} />
            <span>{post.comments_count || 0} Comments</span>
          </button>
        </div>

        <button
          type="button"
          onClick={() => setShowComments(!showComments)}
          className="flex items-center gap-1 font-semibold text-[#2563EB] hover:underline"
        >
          <span>{showComments ? 'Hide' : 'View'}</span>
          {showComments ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
        </button>
      </div>

      {showComments && <CommentSection postId={post.id} currentUser={currentUser} />}
    </GlassCard>
  )
}

export default function Community() {
  const [posts, setPosts] = useState([])
  const [likedPosts, setLikedPosts] = useState([])
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [currentUser, setCurrentUser] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchPosts()
    api.getMe()
      .then((res) => {
        if (res?.user?.id) setCurrentUser(res.user.id)
      })
      .catch(() => {})
  }, [filter])

  const fetchPosts = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await api.getPosts(filter === 'all' ? undefined : filter)
      setPosts(Array.isArray(response?.posts) ? response.posts : [])
      if (Array.isArray(response?.liked_post_ids)) {
        setLikedPosts(response.liked_post_ids)
      }
    } catch (fetchError) {
      setError(fetchError.message || 'Failed to load community feed.')
    }
    setLoading(false)
  }

  const handleLike = async (postId) => {
    try {
      const response = await api.likePost(postId)
      setLikedPosts((current) =>
        response.liked ? [...current, postId] : current.filter((id) => id !== postId)
      )
      setPosts((current) =>
        current.map((post) =>
          post.id === postId
            ? { ...post, likes_count: (post.likes_count || 0) + (response.liked ? 1 : -1) }
            : post
        )
      )
    } catch {}
  }

  const handleDelete = async (postId) => {
    if (!window.confirm('Delete this post?')) return
    try {
      await api.deletePost(postId)
      setPosts((current) => current.filter((post) => post.id !== postId))
    } catch {}
  }

  return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
      <div className="mx-auto max-w-3xl space-y-6 pb-16">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <Badge sparkle size="sm" className="mb-1">Builder Network</Badge>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0B0F19] tracking-tight flex items-center gap-2.5">
              <Users size={24} className="text-[#2563EB]" />
              <span>Community</span>
            </h1>
            <p className="text-xs sm:text-sm text-[#64748B] mt-1">
              Share projects, job opportunities, tech writing, and connect with peers.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 py-3 px-5 rounded-full bg-[#0B0F19] text-white font-bold text-xs sm:text-sm hover:bg-[#1E293B] transition-all shadow-md"
          >
            <Plus size={16} />
            <span>Create Post</span>
          </button>
        </div>

        {/* Category Filter Pills */}
        <div className="flex gap-2 overflow-x-auto pb-1">
          {POST_TYPES.map(({ value, label, icon: Icon, iconClass }) => {
            const isSelected = filter === value
            return (
              <button
                type="button"
                key={value}
                onClick={() => setFilter(value)}
                className={`flex shrink-0 items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-xs font-semibold transition-all ${
                  isSelected
                    ? 'border-[#2563EB] bg-blue-50 text-[#2563EB] shadow-xs'
                    : 'border-slate-200 bg-white/80 text-[#64748B] hover:border-slate-300 hover:text-[#0B0F19]'
                }`}
              >
                <Icon size={12} className={isSelected ? 'text-[#2563EB]' : iconClass} />
                <span>{label}</span>
              </button>
            )
          })}
        </div>

        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs font-semibold text-[#E11D48]">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-20">
            <Loader2 size={30} className="animate-spin text-[#2563EB]" />
          </div>
        ) : posts.length === 0 && filter === 'all' ? (
          <GlassCard className="p-12 text-center space-y-3 border-white/95 shadow-glass-lg">
            <div className="w-12 h-12 rounded-2xl bg-blue-50 text-[#2563EB] flex items-center justify-center mx-auto">
              <Users size={24} />
            </div>
            <h3 className="text-base font-bold text-[#0B0F19]">No community posts yet</h3>
            <p className="text-xs text-[#64748B] max-w-sm mx-auto">
              Be the first to share your project, portfolio, or career updates.
            </p>
            <button
              type="button"
              onClick={() => setShowCreate(true)}
              className="inline-flex items-center gap-2 py-2.5 px-5 rounded-full bg-[#0B0F19] text-white font-bold text-xs hover:bg-[#1E293B] shadow-md mt-2"
            >
              <Plus size={14} /> Create First Post
            </button>
          </GlassCard>
        ) : (
          <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-4">
            {posts.map((post) => (
              <PostCard
                key={post.id}
                post={post}
                likedPosts={likedPosts}
                currentUser={currentUser}
                onLike={handleLike}
                onDelete={handleDelete}
              />
            ))}

            {posts.length === 0 && filter !== 'all' && (
              <GlassCard className="p-10 text-center border-white/95">
                <p className="text-sm font-bold text-[#0B0F19]">No posts yet in this category</p>
                <p className="mt-1 text-xs text-[#64748B]">Be the first to share an update here.</p>
              </GlassCard>
            )}
          </motion.div>
        )}

        {showCreate && <CreatePostModal onClose={() => setShowCreate(false)} onCreated={fetchPosts} />}
      </div>
    </motion.div>
  )
}
