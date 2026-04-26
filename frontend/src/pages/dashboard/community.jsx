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
  Tag,
} from 'lucide-react'

const POST_TYPES = [
  { value: 'all', label: 'All Posts', icon: Globe, iconClass: 'text-[#8A8FA8]' },
  { value: 'project', label: 'Projects', icon: Code2, iconClass: 'text-[#FF7070]' },
  { value: 'job', label: 'Job Seeking', icon: Briefcase, iconClass: 'text-blue-300' },
  { value: 'funding', label: 'Funding', icon: DollarSign, iconClass: 'text-green-300' },
  { value: 'blog', label: 'Blog / Tips', icon: BookOpen, iconClass: 'text-amber-300' },
  { value: 'hiring', label: 'Hiring', icon: Users, iconClass: 'text-[#FF8C42]' },
]

const TYPE_STYLES = {
  project: { className: 'badge badge-red normal-case tracking-normal', icon: 'Project' },
  job: { className: 'badge badge-blue normal-case tracking-normal', icon: 'Job' },
  funding: { className: 'badge badge-green normal-case tracking-normal', icon: 'Funding' },
  blog: { className: 'badge badge-amber normal-case tracking-normal', icon: 'Blog' },
  hiring: { className: 'inline-flex items-center gap-1 rounded-full border border-[rgba(255,140,66,0.25)] bg-[rgba(255,140,66,0.12)] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#FF8C42]', icon: 'Hiring' },
}

const buttonMotion = {
  whileHover: { scale: 1.03, y: -1 },
  whileTap: { scale: 0.97 },
  transition: { duration: 0.15, ease: 'easeOut' },
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
  'linear-gradient(135deg,#FF3B3B,#8B0000)',
  'linear-gradient(135deg,#FF8C42,#FF3B3B)',
  'linear-gradient(135deg,#10b981,#0f9f6e)',
  'linear-gradient(135deg,#1a1f2b,#ef4444)',
  'linear-gradient(135deg,#FF3B3B,#CC1A1A)',
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
      setError(requestError.message)
    }
    setLoading(false)
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-[14px]"
      onClick={(event) => event.target === event.currentTarget && onClose()}
    >
      <motion.div
        initial={{ scale: 0.94, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.94, opacity: 0 }}
        className="glass-glow w-full max-w-xl rounded-3xl p-6"
        style={{ borderTop: '2px solid rgba(255,59,59,0.45)' }}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-white">Create Post</h2>
          <button onClick={onClose} className="rounded-xl p-2 text-[#8A8FA8] transition hover:bg-white/5 hover:text-white">
            <X size={20} />
          </button>
        </div>

        {error && <div className="mb-4 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-300">{error}</div>}

        <div className="mb-4">
          <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-[#8A8FA8]">Post Type</label>
          <div className="flex flex-wrap gap-2">
            {POST_TYPES.filter((type) => type.value !== 'all').map(({ value, label, icon: Icon, iconClass }) => (
              <motion.button
                key={value}
                {...buttonMotion}
                onClick={() => handle('post_type', value)}
                className={`flex items-center gap-1.5 rounded-xl border px-3 py-2 text-xs font-medium transition ${
                  form.post_type === value
                    ? 'border-red-500/25 bg-red-500/10 text-white'
                    : 'border-white/10 text-[#8A8FA8] hover:border-red-500/20 hover:bg-red-500/5 hover:text-white'
                }`}
              >
                <Icon size={12} className={form.post_type === value ? 'text-[#FF7070]' : iconClass} />
                {label}
              </motion.button>
            ))}
          </div>
        </div>

        <div className="mb-4">
          <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-[#8A8FA8]">Title *</label>
          <input
            value={form.title}
            onChange={(event) => handle('title', event.target.value)}
            placeholder="e.g. Built a full-stack AI resume analyzer..."
            className="input-field"
            maxLength={100}
          />
        </div>

        <div className="mb-4">
          <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-[#8A8FA8]">Content *</label>
          <textarea
            value={form.content}
            onChange={(event) => handle('content', event.target.value)}
            placeholder="Share your project, story, or opportunity..."
            rows={4}
            className="input-field resize-none"
            maxLength={1000}
          />
          <p className="mt-1 text-right text-xs text-[#8A8FA8]">{form.content.length}/1000</p>
        </div>

        <div className="mb-4 grid gap-3 sm:grid-cols-2">
          <div>
            <label className="mb-2 flex items-center gap-1 text-xs font-semibold uppercase tracking-[0.18em] text-[#8A8FA8]">
              <Globe size={10} />
              Demo URL
            </label>
            <input
              value={form.demo_url}
              onChange={(event) => handle('demo_url', event.target.value)}
              placeholder="https://yourapp.com (shows as Demo button)"
              className="input-field text-sm"
            />
            <p style={{ fontSize: 10, color: '#475569', marginTop: 3 }}>
              Will appear as a clickable "Demo" button on your post
            </p>
          </div>
          <div>
            <label className="mb-2 flex items-center gap-1 text-xs font-semibold uppercase tracking-[0.18em] text-[#8A8FA8]">
              <Github size={10} />
              GitHub URL
            </label>
            <input
              value={form.github_url}
              onChange={(event) => handle('github_url', event.target.value)}
              placeholder="https://github.com/..."
              className="input-field text-sm"
            />
          </div>
        </div>

        <div className="mb-5">
          <label className="mb-2 flex items-center gap-1 text-xs font-semibold uppercase tracking-[0.18em] text-[#8A8FA8]">
            <Tag size={10} />
            Tags
          </label>
          <input
            value={form.tags}
            onChange={(event) => handle('tags', event.target.value)}
            placeholder="React, AI, Open Source, Hiring..."
            className="input-field text-sm"
          />
        </div>

        <div className="flex gap-3">
          <button onClick={onClose} className="btn-ghost flex-1">
            Cancel
          </button>
          <button onClick={handleSubmit} disabled={loading} className="btn-primary flex-1">
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Posting...
              </>
            ) : (
              <>
                <Send size={16} />
                Post
              </>
            )}
          </button>
        </div>
      </motion.div>
    </motion.div>
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
      setComments((current) => [...current, response.comment])
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
    <div className="mt-4 space-y-3 border-t border-white/5 pt-4">
      {fetching ? (
        <div className="flex justify-center py-3">
          <Loader2 size={16} className="animate-spin text-[#8A8FA8]" />
        </div>
      ) : (
        <div className="max-h-64 space-y-3 overflow-y-auto pr-1">
          {comments.length === 0 && <p className="py-2 text-center text-xs text-[#8A8FA8]">No comments yet. Be the first.</p>}
          {comments.map((comment) => (
            <div key={comment.id} className="flex items-start gap-3">
              <div
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white"
                style={{ background: getAvatarColor(comment.author_name) }}
              >
                {getInitials(comment.author_name)}
              </div>
              <div className="glass flex-1 rounded-2xl px-3 py-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-white">{comment.author_name || 'Anonymous'}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-[#8A8FA8]">{formatTime(comment.created_at)}</span>
                    {comment.user_id === currentUser && (
                      <button onClick={() => handleDelete(comment.id)} className="text-[#8A8FA8] transition hover:text-red-400">
                        <Trash2 size={10} />
                      </button>
                    )}
                  </div>
                </div>
                <p className="mt-1 text-xs text-[#F5F5F7]">{comment.content}</p>
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
          className="input-field flex-1 py-2 text-sm"
        />
        <button onClick={handleComment} disabled={loading || !newComment.trim()} className="btn-primary px-3 py-2">
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
    <motion.div variants={staggerItem} whileHover={{ y: -2 }} className="glass-glow rounded-3xl p-6">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div
            className="flex h-11 w-11 items-center justify-center rounded-2xl text-sm font-bold text-white"
            style={{ background: getAvatarColor(post.author_name) }}
          >
            {getInitials(post.author_name)}
          </div>
          <div>
            <p className="text-sm font-semibold text-white">{post.author_name || 'Anonymous'}</p>
            <p className="text-xs text-[#8A8FA8]">{formatTime(post.created_at)}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className={typeStyle.className}>{typeStyle.icon}</span>
          {isOwner && (
            <button onClick={() => onDelete(post.id)} className="rounded-xl p-1 text-[#8A8FA8] transition hover:text-red-400">
              <Trash2 size={14} />
            </button>
          )}
        </div>
      </div>

      <div className="mb-4">
        <h3 className="mb-2 text-lg font-bold text-white">{post.title}</h3>
        <p className="whitespace-pre-wrap text-sm leading-7 text-[#F5F5F7]">{post.content}</p>
      </div>

      {(post.demo_url || post.github_url) && (
        <div className="mb-4">
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
            {post.demo_url && (
              <a
                href={post.demo_url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '7px 16px',
                  borderRadius: 10,
                  background: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  color: '#94a3b8',
                  fontSize: 12,
                  fontWeight: 600,
                  textDecoration: 'none',
                  transition: 'all 0.2s',
                  cursor: 'pointer',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.08)'
                  e.currentTarget.style.color = 'white'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.04)'
                  e.currentTarget.style.color = '#94a3b8'
                }}
              >
                <Globe size={13} />
                Demo
              </a>
            )}

            {false && post.demo_url && (
              <a
                href={post.demo_url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '7px 16px',
                  borderRadius: 10,
                  background: 'rgba(225, 29, 72, 0.1)',
                  border: '1px solid rgba(225, 29, 72, 0.25)',
                  color: '#fb7185',
                  fontSize: 12,
                  fontWeight: 600,
                  textDecoration: 'none',
                  transition: 'all 0.2s',
                  cursor: 'pointer',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(225,29,72,0.18)'
                  e.currentTarget.style.borderColor = 'rgba(225,29,72,0.4)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(225,29,72,0.1)'
                  e.currentTarget.style.borderColor = 'rgba(225,29,72,0.25)'
                }}
              >
                Demo
              </a>
            )}

            {post.github_url && (
              <a
                href={post.github_url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '7px 16px',
                  borderRadius: 10,
                  background: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  color: '#94a3b8',
                  fontSize: 12,
                  fontWeight: 600,
                  textDecoration: 'none',
                  transition: 'all 0.2s',
                  cursor: 'pointer',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.08)'
                  e.currentTarget.style.color = 'white'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.04)'
                  e.currentTarget.style.color = '#94a3b8'
                }}
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/>
                </svg>
                GitHub
              </a>
            )}
          </div>
        </div>
      )}

      {post.tags?.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {post.tags.map((tag, index) => (
            <span key={index} className="rounded-full border border-white/8 bg-white/5 px-2.5 py-1 text-xs text-[#8A8FA8]">
              #{tag}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center gap-4 border-t border-white/5 pt-3">
        <motion.button
          onClick={() => onLike(post.id)}
          animate={isLiked ? { scale: [1, 1.4, 1] } : { scale: 1 }}
          transition={{ type: 'spring', stiffness: 300, damping: 12 }}
          className={`flex items-center gap-1.5 text-sm transition ${
            isLiked ? 'text-[#FF3B3B]' : 'text-[#8A8FA8] hover:text-[#FF3B3B]'
          }`}
        >
          <Heart size={16} className={isLiked ? 'fill-[#FF3B3B]' : ''} />
          <span>{post.likes_count || 0}</span>
        </motion.button>

        <button onClick={() => setShowComments((current) => !current)} className="flex items-center gap-1.5 text-sm text-[#8A8FA8] transition hover:text-white">
          <MessageCircle size={16} />
          <span>{post.comments_count || 0}</span>
          {showComments ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        </button>
      </div>

      <AnimatePresence>
        {showComments && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
            <CommentSection postId={post.id} currentUser={currentUser} />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
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
    fetchLikes()
    getCurrentUser()
  }, [filter])

  const getCurrentUser = async () => {
    try {
      const response = await api.getMe()
      setCurrentUser(response.user?.user_id || response.user?.id)
    } catch {}
  }

  const fetchPosts = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await api.getPosts(filter)
      setPosts(Array.isArray(response?.posts) ? response.posts : [])
    } catch (requestError) {
      setError(requestError.message)
    }
    setLoading(false)
  }

  const fetchLikes = async () => {
    try {
      const response = await api.getUserLikes()
      setLikedPosts(Array.isArray(response?.liked_post_ids) ? response.liked_post_ids : [])
    } catch {}
  }

  const handleLike = async (postId) => {
    try {
      const response = await api.likePost(postId)
      setLikedPosts((current) => (response.liked ? [...current, postId] : current.filter((id) => id !== postId)))
      setPosts((current) =>
        current.map((post) =>
          post.id === postId ? { ...post, likes_count: (post.likes_count || 0) + (response.liked ? 1 : -1) } : post,
        ),
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
      <div className="mx-auto max-w-3xl space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="gradient-text flex items-center gap-3 text-3xl font-black">
              <Users size={28} className="text-[#FF3B3B]" />
              Community
            </h1>
            <p className="mt-2 text-sm text-[#8A8FA8]">Share projects, find jobs, seek funding, and post what you are building.</p>
          </div>
          <button onClick={() => setShowCreate(true)} className="btn-primary">
            <Plus size={16} />
            Create Post
          </button>
        </div>

        <div className="flex gap-2 overflow-x-auto pb-1">
          {POST_TYPES.map(({ value, label, icon: Icon, iconClass }) => (
            <button
              key={value}
              onClick={() => setFilter(value)}
              className={`flex shrink-0 items-center gap-1.5 rounded-xl border px-3 py-2 text-xs font-medium transition ${
                filter === value
                  ? 'border-red-500/25 bg-red-500/12 text-white'
                  : 'border-white/10 bg-white/[0.02] text-[#8A8FA8] hover:border-red-500/20 hover:bg-red-500/5 hover:text-white'
              }`}
            >
              <Icon size={12} className={filter === value ? 'text-[#FF7070]' : iconClass} />
              {label}
            </button>
          ))}
        </div>

        {error && <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300">{error}</div>}

        {loading ? (
          <div className="flex justify-center py-20">
            <Loader2 size={32} className="animate-spin text-[#FF7070]" />
          </div>
        ) : posts.length === 0 && filter === 'all' ? (
          <div className="flex flex-col items-center justify-center space-y-4 py-20 text-center">
            <div className="text-5xl">Seed</div>
            <h3 className="text-lg font-bold text-white">No posts yet</h3>
            <p className="text-sm text-[#8A8FA8]">Be the first to share your project or opportunity.</p>
            <button onClick={() => setShowCreate(true)} className="btn-primary">
              <Plus size={16} />
              Create First Post
            </button>
          </div>
        ) : (
          <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-4">
            {posts.map((post) => (
              <PostCard key={post.id} post={post} likedPosts={likedPosts} currentUser={currentUser} onLike={handleLike} onDelete={handleDelete} />
            ))}

            {posts.length === 0 && filter !== 'all' && (
              <div className="rounded-2xl border border-dashed border-red-500/20 p-10 text-center">
                <p className="text-base font-semibold text-white">No posts yet in this category</p>
                <p className="mt-2 text-sm text-[#8A8FA8]">Be the first to share something here.</p>
              </div>
            )}
          </motion.div>
        )}

        <AnimatePresence>{showCreate && <CreatePostModal onClose={() => setShowCreate(false)} onCreated={fetchPosts} />}</AnimatePresence>
      </div>
    </motion.div>
  )
}
