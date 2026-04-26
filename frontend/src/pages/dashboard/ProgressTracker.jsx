// ============================================================
// CareerLens – Resume Progress Tracker
// File: frontend/src/pages/dashboard/ProgressTracker.jsx
// ============================================================

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useCountUp, staggerContainer, staggerItem, pageTransition } from '../../utils/animations'
import { api } from '../../services/api'
import toast from 'react-hot-toast'
import {
  TrendingUp, TrendingDown, Minus, Trophy,
  FileText, Calendar, Target, Zap, BarChart2,
  ArrowUp, ArrowDown, RefreshCw, Loader2
} from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, Legend
} from 'recharts'

// ============================================================
// Helpers
// ============================================================

const formatDate = (iso) => {
  const d = new Date(iso)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

const getDelta = (current, previous) => {
  if (previous == null) return null
  return current - previous
}

const buttonMotion = {
  whileHover: { scale: 1.03, y: -1 },
  whileTap:   { scale: 0.97 },
  transition: { duration: 0.15, ease: 'easeOut' },
}

// ── Delta badge ───────────────────────────────────────────────
const DeltaBadge = ({ delta }) => {
  if (delta === null) return <span className="text-xs text-[#44403c]">first entry</span>
  if (delta === 0) return (
    <span className="flex items-center gap-1 text-xs text-[#78716c]">
      <Minus size={12} /> no change
    </span>
  )
  const positive = delta > 0
  return (
    <span className={`flex items-center gap-1 text-xs font-semibold ${positive ? 'text-green-400' : 'text-red-400'}`}>
      {positive ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
      {positive ? '+' : ''}{delta} pts
    </span>
  )
}

// ── Score card ────────────────────────────────────────────────
const ScoreCard = ({ label, value, delta, color, icon }) => {
  const numeric = typeof value === 'number' ? value : parseInt(value, 10) || 0
  const count = useCountUp(numeric, 1200)
  return (
    <motion.div
      variants={staggerItem}
      whileHover={{
        y: -4, scale: 1.015,
        boxShadow: '0 16px 48px rgba(0,0,0,0.5), 0 0 32px rgba(225,29,72,0.1)',
        borderColor: 'rgba(225,29,72,0.35)',
        transition: { duration: 0.22, ease: 'easeOut' },
      }}
      whileTap={{ scale: 0.985 }}
      className="glass p-5 rounded-2xl space-y-2"
      style={{ cursor: 'pointer', transition: 'border-color 0.2s' }}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs text-[#78716c] font-medium uppercase tracking-wide">{label}</span>
        <span className="text-xl">{icon}</span>
      </div>
      <p className={`text-4xl font-black ${color}`}>{value == null ? '?' : count}</p>
      <DeltaBadge delta={delta} />
    </motion.div>
  )
}

// ============================================================
// Custom Tooltip for chart
// BUG FIX: removed stray </motion.div> that was after the return
// ============================================================

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background:   '#111010',
      border:       '1px solid rgba(225,29,72,0.25)',
      borderRadius: '10px',
      color:        '#fafaf9',
      padding:      '12px',
      fontSize:     '12px',
      minWidth:     '128px',
    }}>
      <p className="text-[#78716c] mb-2">{label}</p>
      {payload.map((p, i) => (
        <div key={i} className="flex items-center justify-between gap-4">
          <span style={{ color: p.color }}>{p.name}</span>
          <span className="text-white font-bold">{p.value}</span>
        </div>
      ))}
    </div>
  )
}

// ============================================================
// Empty State
// ============================================================

const EmptyState = () => (
  <div className="flex flex-col items-center justify-center py-20 text-center space-y-4">
    <div className="w-20 h-20 rounded-2xl bg-rose-600/10 flex items-center justify-center">
      <BarChart2 size={36} className="text-rose-400" />
    </div>
    <h2 className="text-xl font-bold text-white">No Progress Data Yet</h2>
    <p className="text-[#78716c] max-w-sm text-sm leading-relaxed">
      Your progress will be tracked automatically every time you run a Resume Analysis.
      Submit at least one analysis to start seeing your improvement trends here.
    </p>
    <a href="/dashboard/resume" className="btn-primary px-6 py-3 flex items-center gap-2">
      <FileText size={16} /> Analyze My Resume
    </a>
  </div>
)

// ============================================================
// Main Component
// ============================================================

export default function ProgressTracker() {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState('')

  useEffect(() => {
    fetchHistory()
  }, [])

  const fetchHistory = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.getProgressHistory()
      setHistory(Array.isArray(res?.history) ? res.history : [])
    } catch (err) {
      setError(err.message)
      toast.error(err.message || 'Failed to load progress history.')
    }
    setLoading(false)
  }

  // ── Derived data ──────────────────────────────────────────

  const sorted = [...history].sort((a, b) => new Date(a.created_at) - new Date(b.created_at))

  const chartData = sorted.map((h, i) => ({
    date:           formatDate(h.created_at),
    'Resume Score': h.resume_score,
    'ATS Score':    h.ats_score,
    version:        i + 1,
    job_role:       h.job_role,
  }))

  const latest  = sorted[sorted.length - 1]
  const prev    = sorted[sorted.length - 2]
  const bestScore     = Math.max(...sorted.map(h => h.resume_score ?? 0))
  const totalAnalyses = sorted.length
  const avgImprovement = sorted.length > 1
    ? Math.round(
        (sorted[sorted.length - 1].resume_score - sorted[0].resume_score) /
        (sorted.length - 1)
      )
    : 0

  // ── Loading state ─────────────────────────────────────────

  if (loading) return (
    <div className="flex items-center justify-center py-32">
      <Loader2 size={32} className="animate-spin text-rose-400" />
    </div>
  )

  // ── Render ────────────────────────────────────────────────

  return (
    // BUG FIX: added missing closing </motion.div> at bottom
    <motion.div
      variants={pageTransition}
      initial="hidden"
      animate="visible"
      exit="exit"
      style={{ width: '100%' }}
    >
      <div className="max-w-4xl w-full mx-auto space-y-6">

        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <TrendingUp size={28} className="text-green-400" /> Progress Tracker
            </h1>
            <p className="text-[#78716c] mt-1">
              Track how your resume score improves with every update
            </p>
          </div>
          <motion.button
            {...buttonMotion}
            onClick={fetchHistory}
            className="btn-ghost flex items-center gap-2 text-sm"
          >
            <RefreshCw size={14} /> Refresh
          </motion.button>
        </div>

        {/* Error */}
        {error && (
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {error}
          </div>
        )}

        {history.length === 0 ? <EmptyState /> : (
          <>
            {/* Stats Row */}
            <motion.div
              variants={staggerContainer}
              initial="hidden"
              animate="visible"
              className="grid grid-cols-2 md:grid-cols-4 gap-4"
            >
              <ScoreCard
                label="Latest Score"
                value={latest?.resume_score}
                delta={getDelta(latest?.resume_score, prev?.resume_score)}
                color="text-rose-400"
                icon="📊"
              />
              <ScoreCard
                label="Latest ATS"
                value={latest?.ats_score}
                delta={getDelta(latest?.ats_score, prev?.ats_score)}
                color="text-rose-400"
                icon="🎯"
              />
              <ScoreCard
                label="Best Score"
                value={bestScore}
                delta={null}
                color="text-rose-400"
                icon="🏆"
              />
              <ScoreCard
                label="Analyses Done"
                value={totalAnalyses}
                delta={null}
                color="text-rose-500"
                icon="📈"
              />
            </motion.div>

            {/* Improvement banner */}
            {sorted.length > 1 && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className={`p-4 rounded-2xl border flex items-center gap-4
                  ${sorted[sorted.length - 1].resume_score > sorted[0].resume_score
                    ? 'bg-green-500/5 border-green-500/20'
                    : 'bg-rose-600/5 border-rose-500/20'}`}
              >
                <div className="text-3xl">
                  {sorted[sorted.length - 1].resume_score > sorted[0].resume_score ? '🚀' : '💪'}
                </div>
                <div>
                  <p className="text-white font-semibold">
                    {sorted[sorted.length - 1].resume_score > sorted[0].resume_score
                      ? `Your resume score improved by ${sorted[sorted.length - 1].resume_score - sorted[0].resume_score} points since your first analysis!`
                      : 'Keep improving — every update gets you closer to your goal!'}
                  </p>
                  <p className="text-[#78716c] text-sm">
                    Average change per analysis: {avgImprovement > 0 ? '+' : ''}{avgImprovement} points
                  </p>
                </div>
              </motion.div>
            )}

            {/* Chart */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="glass p-6 rounded-2xl"
            >
              <h2 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
                <BarChart2 size={18} className="text-rose-400" /> Score Trend Over Time
              </h2>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(225,29,72,0.08)" />
                  <XAxis
                    dataKey="date"
                    tick={{ fill: '#78716c', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    domain={[0, 100]}
                    tick={{ fill: '#78716c', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend
                    wrapperStyle={{ color: '#78716c', fontSize: '12px', paddingTop: '16px' }}
                  />
                  <ReferenceLine
                    y={70}
                    stroke="rgba(225,29,72,0.35)"
                    strokeDasharray="4 4"
                    label={{ value: 'Good', fill: '#be123c', fontSize: 11 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="Resume Score"
                    stroke="#e11d48"
                    strokeWidth={2.5}
                    dot={{ fill: '#e11d48', strokeWidth: 0, r: 4 }}
                    activeDot={{ r: 6, fill: '#fb7185' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="ATS Score"
                    stroke="#be123c"
                    strokeWidth={2.5}
                    strokeDasharray="5 5"
                    dot={{ fill: '#be123c', strokeWidth: 0, r: 4 }}
                    activeDot={{ r: 6, fill: '#e11d48' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </motion.div>

            {/* History Table */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="glass p-6 rounded-2xl"
            >
              <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <Calendar size={18} className="text-rose-500" /> Analysis History
              </h2>
              <div className="space-y-3">
                {[...sorted].reverse().map((entry, i) => {
                  const idx       = sorted.indexOf(entry)
                  const prevEntry = sorted[idx - 1]
                  const delta     = prevEntry ? entry.resume_score - prevEntry.resume_score : null
                  return (
                    <div
                      key={entry.id || i}
                      className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5 hover:bg-white/8 transition-colors"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-9 h-9 rounded-lg bg-rose-600/20 flex items-center justify-center text-sm font-bold text-rose-300">
                          v{idx + 1}
                        </div>
                        <div>
                          <p className="text-white text-sm font-medium">{entry.job_role || 'Resume Analysis'}</p>
                          <p className="text-[#44403c] text-xs">{formatDate(entry.created_at)}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-6">
                        <div className="text-right hidden md:block">
                          <p className="text-xs text-[#78716c]">ATS Score</p>
                          <p className="text-rose-400 font-bold">{entry.ats_score ?? '—'}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-[#78716c]">Resume Score</p>
                          <p className={`font-bold text-lg ${
                            entry.resume_score >= 70 ? 'text-green-400'
                            : entry.resume_score >= 50 ? 'text-rose-400'
                            : 'text-red-400'
                          }`}>
                            {entry.resume_score ?? '—'}
                          </p>
                        </div>
                        <div className="w-20 text-right">
                          <DeltaBadge delta={delta} />
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </motion.div>

            {/* Tips */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="glass p-6 rounded-2xl border border-rose-500/20 bg-rose-600/5"
            >
              <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <Zap size={18} className="text-rose-400" /> How to Improve Your Score
              </h2>
              <div className="grid md:grid-cols-2 gap-3">
                {[
                  { tip: 'Add quantified achievements (e.g. "Reduced load time by 40%")',     icon: '📊' },
                  { tip: 'Include keywords from the job description you are targeting',        icon: '🔑' },
                  { tip: 'Build and deploy at least 2-3 real projects with GitHub links',      icon: '🛠️' },
                  { tip: 'Add internship or freelance work experience',                        icon: '💼' },
                  { tip: 'Keep GitHub active — commit regularly to show consistency',          icon: '💻' },
                  { tip: 'Get certifications relevant to your target role',                    icon: '🎓' },
                ].map((item, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-white/5">
                    <span className="text-lg shrink-0">{item.icon}</span>
                    <p className="text-sm text-[#d6d3d1]">{item.tip}</p>
                  </div>
                ))}
              </div>
            </motion.div>

          </>
        )}

      </div>
    </motion.div>
  )
}
