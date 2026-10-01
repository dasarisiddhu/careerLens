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
  TrendingUp, Minus, Trophy,
  FileText, Calendar, BarChart2,
  ArrowUp, ArrowDown, RefreshCw, Loader2
} from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, Legend
} from 'recharts'
import { GlassCard, Badge } from '../../components/ui'

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

// ── Delta badge ───────────────────────────────────────────────
const DeltaBadge = ({ delta }) => {
  if (delta === null) return <span className="text-[11px] text-[#94A3B8]">first entry</span>
  if (delta === 0) return (
    <span className="flex items-center gap-1 text-[11px] text-[#64748B]">
      <Minus size={11} /> no change
    </span>
  )
  const positive = delta > 0
  return (
    <span className={`flex items-center gap-0.5 text-[11px] font-bold ${positive ? 'text-[#16A34A]' : 'text-[#E11D48]'}`}>
      {positive ? <ArrowUp size={11} /> : <ArrowDown size={11} />}
      {positive ? '+' : ''}{delta} pts
    </span>
  )
}

// ── Score card ────────────────────────────────────────────────
const ScoreCard = ({ label, value, delta, color, icon }) => {
  const numeric = typeof value === 'number' ? value : parseInt(value, 10) || 0
  const count = useCountUp(numeric, 1200)
  return (
    <GlassCard className="p-5 space-y-2 border-white/90 shadow-glass">
      <div className="flex items-center justify-between">
        <span className="text-xs text-[#64748B] font-bold uppercase tracking-wider">{label}</span>
        <span className="text-xl">{icon}</span>
      </div>
      <p className={`text-3xl font-extrabold ${color}`}>{value == null ? '?' : count}</p>
      <DeltaBadge delta={delta} />
    </GlassCard>
  )
}

// ============================================================
// Custom Tooltip for chart
// ============================================================

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-xl border border-slate-200 bg-white/95 p-3 text-xs shadow-lg backdrop-blur-md min-w-[130px]">
      <p className="text-[#64748B] font-semibold mb-2">{label}</p>
      {payload.map((p, i) => (
        <div key={i} className="flex items-center justify-between gap-4">
          <span style={{ color: p.color }} className="font-medium">{p.name}</span>
          <span className="text-[#0B0F19] font-bold">{p.value}</span>
        </div>
      ))}
    </div>
  )
}

// ============================================================
// Empty State
// ============================================================

const EmptyState = () => (
  <GlassCard className="p-12 text-center space-y-4 max-w-lg mx-auto border-white/95 shadow-glass-lg">
    <div className="w-16 h-16 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center mx-auto text-[#2563EB]">
      <BarChart2 size={32} />
    </div>
    <h2 className="text-lg font-bold text-[#0B0F19]">No Progress Data Yet</h2>
    <p className="text-xs sm:text-sm text-[#64748B] leading-relaxed">
      Your progress will be tracked automatically every time you run a Resume Analysis.
      Submit an analysis to start seeing your improvement trends here.
    </p>
    <a
      href="/dashboard/resume"
      className="inline-flex items-center gap-2 py-3 px-6 rounded-full bg-[#0B0F19] text-white font-bold text-xs sm:text-sm hover:bg-[#1E293B] transition-all shadow-md"
    >
      <FileText size={15} /> Analyze My Resume
    </a>
  </GlassCard>
)

// ============================================================
// Main Component
// ============================================================

export default function ProgressTracker() {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

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
      setError(err.message || 'Failed to load progress history.')
      toast.error(err.message || 'Failed to load progress history.')
    }
    setLoading(false)
  }

  // ── Derived data ──────────────────────────────────────────
  const sorted = [...history].sort((a, b) => new Date(a.created_at) - new Date(b.created_at))

  const chartData = sorted.map((h, i) => ({
    date: formatDate(h.created_at),
    'Resume Score': h.resume_score,
    'ATS Score': h.ats_score,
    version: i + 1,
    job_role: h.job_role,
  }))

  const latest = sorted[sorted.length - 1]
  const prev = sorted[sorted.length - 2]
  const bestScore = sorted.length ? Math.max(...sorted.map((h) => h.resume_score ?? 0)) : 0
  const totalAnalyses = sorted.length
  const avgImprovement =
    sorted.length > 1
      ? Math.round((sorted[sorted.length - 1].resume_score - sorted[0].resume_score) / (sorted.length - 1))
      : 0

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 size={32} className="animate-spin text-[#2563EB]" />
      </div>
    )
  }

  return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
      <div className="max-w-4xl w-full mx-auto space-y-6 pb-16">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <Badge sparkle size="sm">Analytics</Badge>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0B0F19] tracking-tight flex items-center gap-2.5">
              <TrendingUp size={24} className="text-[#2563EB]" />
              <span>Progress Tracker</span>
            </h1>
            <p className="text-xs sm:text-sm text-[#64748B]">
              Track how your resume score and match capability improve with each iteration.
            </p>
          </div>
          <button
            type="button"
            onClick={fetchHistory}
            className="flex items-center gap-2 text-xs font-semibold text-[#475569] hover:text-[#0B0F19] transition-colors px-3.5 py-2 rounded-full border border-slate-200 bg-white/80 shadow-xs"
          >
            <RefreshCw size={13} /> Refresh
          </button>
        </div>

        {error && (
          <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-[#E11D48] text-xs font-semibold">
            {error}
          </div>
        )}

        {history.length === 0 ? (
          <EmptyState />
        ) : (
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
                color="text-[#2563EB]"
                icon="📊"
              />
              <ScoreCard
                label="Latest ATS"
                value={latest?.ats_score}
                delta={getDelta(latest?.ats_score, prev?.ats_score)}
                color="text-[#0284C7]"
                icon="🎯"
              />
              <ScoreCard
                label="Best Score"
                value={bestScore}
                delta={null}
                color="text-[#16A34A]"
                icon="🏆"
              />
              <ScoreCard
                label="Total Scans"
                value={totalAnalyses}
                delta={null}
                color="text-[#0B0F19]"
                icon="📈"
              />
            </motion.div>

            {/* Improvement banner */}
            {sorted.length > 1 && (
              <GlassCard className="p-4 sm:p-5 flex items-center gap-4 border-emerald-200/80 bg-emerald-50/40">
                <div className="text-3xl shrink-0">
                  {sorted[sorted.length - 1].resume_score > sorted[0].resume_score ? '🚀' : '💪'}
                </div>
                <div>
                  <p className="text-sm font-bold text-[#0B0F19]">
                    {sorted[sorted.length - 1].resume_score > sorted[0].resume_score
                      ? `Your score improved by ${sorted[sorted.length - 1].resume_score - sorted[0].resume_score} points since your first analysis!`
                      : 'Keep iterating — each targeted fix gets you closer to an interview!'}
                  </p>
                  <p className="text-xs text-[#64748B] mt-0.5">
                    Average delta per analysis: {avgImprovement > 0 ? '+' : ''}{avgImprovement} points
                  </p>
                </div>
              </GlassCard>
            )}

            {/* Chart */}
            <GlassCard className="p-6 border-white/95 shadow-glass-lg space-y-4">
              <h2 className="text-sm font-bold text-[#0B0F19] flex items-center gap-2">
                <BarChart2 size={16} className="text-[#2563EB]" /> Score Trend Over Time
              </h2>
              <div className="w-full h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                    <XAxis
                      dataKey="date"
                      tick={{ fill: '#64748B', fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      domain={[0, 100]}
                      tick={{ fill: '#64748B', fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend wrapperStyle={{ color: '#64748B', fontSize: '12px', paddingTop: '12px' }} />
                    <ReferenceLine
                      y={70}
                      stroke="#94A3B8"
                      strokeDasharray="4 4"
                      label={{ value: 'Good', fill: '#64748B', fontSize: 11 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="Resume Score"
                      stroke="#2563EB"
                      strokeWidth={2.5}
                      dot={{ fill: '#2563EB', strokeWidth: 0, r: 4 }}
                      activeDot={{ r: 6, fill: '#1D4ED8' }}
                    />
                    <Line
                      type="monotone"
                      dataKey="ATS Score"
                      stroke="#0284C7"
                      strokeWidth={2.5}
                      strokeDasharray="5 5"
                      dot={{ fill: '#0284C7', strokeWidth: 0, r: 4 }}
                      activeDot={{ r: 6, fill: '#0369A1' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </GlassCard>

            {/* History Table */}
            <GlassCard className="p-6 border-white/95 shadow-glass-lg space-y-4">
              <h2 className="text-sm font-bold text-[#0B0F19] flex items-center gap-2">
                <Calendar size={16} className="text-[#2563EB]" /> Analysis History
              </h2>
              <div className="space-y-2.5">
                {[...sorted].reverse().map((entry, i) => {
                  const idx = sorted.indexOf(entry)
                  const prevEntry = sorted[idx - 1]
                  const delta = prevEntry ? entry.resume_score - prevEntry.resume_score : null
                  return (
                    <div
                      key={entry.id || i}
                      className="flex items-center justify-between p-3.5 rounded-xl bg-white border border-slate-200/80 hover:border-blue-200 transition-colors shadow-xs"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center text-xs font-bold text-[#2563EB]">
                          v{idx + 1}
                        </div>
                        <div>
                          <p className="text-xs sm:text-sm font-bold text-[#0B0F19]">{entry.job_role || 'Resume Analysis'}</p>
                          <p className="text-[#64748B] text-[11px]">{formatDate(entry.created_at)}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 sm:gap-6">
                        <div className="text-right">
                          <p className="text-xs font-bold text-[#2563EB]">Score: {entry.resume_score}</p>
                          <DeltaBadge delta={delta} />
                        </div>
                        {entry.ats_score !== undefined && (
                          <div className="text-right hidden sm:block">
                            <p className="text-xs font-bold text-[#0284C7]">ATS: {entry.ats_score}</p>
                            <span className="text-[11px] text-[#64748B]">Keyword match</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </GlassCard>
          </>
        )}
      </div>
    </motion.div>
  )
}
