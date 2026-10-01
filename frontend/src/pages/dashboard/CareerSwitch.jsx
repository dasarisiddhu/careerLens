// ============================================================
// CareerLens – Career Switch Page (Complete Beginner Mode)
// File: frontend/src/pages/dashboard/CareerSwitch.jsx
// ============================================================

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { pageTransition } from '../../utils/animations'
import { api } from '../../services/api'
import {
  Loader2, Rocket, Clock, Target, BookOpen,
  ExternalLink, RefreshCw, CheckCircle, XCircle,
  ChevronRight, Star, AlertTriangle
} from 'lucide-react'
import { GlassCard, Badge } from '../../components/ui'

// ============================================================
// Constants
// ============================================================

const BACKGROUNDS = [
  { label: 'BIPC (Biology, Physics, Chemistry)', emoji: '🧬' },
  { label: 'Commerce / Business', emoji: '📊' },
  { label: 'Arts / Humanities', emoji: '🎨' },
  { label: 'MPC (Maths, Physics, Chemistry)', emoji: '🔢' },
  { label: 'Diploma', emoji: '📜' },
  { label: 'Other Non-Tech', emoji: '🎓' },
]

const TECH_FIELDS = [
  { label: 'Web Development', emoji: '🌐' },
  { label: 'Data Science', emoji: '📈' },
  { label: 'Artificial Intelligence / ML', emoji: '🤖' },
  { label: 'Mobile App Development', emoji: '📱' },
  { label: 'Cybersecurity', emoji: '🔐' },
  { label: 'Cloud Computing', emoji: '☁️' },
  { label: 'UI/UX Design', emoji: '🎨' },
  { label: 'DevOps', emoji: '⚙️' },
]

const TIMELINES = [
  { label: '3 months', emoji: '⚡', desc: 'Intensive pace' },
  { label: '6 months', emoji: '🎯', desc: 'Recommended' },
  { label: '1 year', emoji: '🌱', desc: 'Comfortable pace' },
]

const HOURS = [
  { label: '1-2 hours/day', emoji: '🌙', desc: 'After work/college' },
  { label: '3-4 hours/day', emoji: '☀️', desc: 'Part time' },
  { label: '5-6 hours/day', emoji: '💪', desc: 'Serious learner' },
  { label: '8+ hours/day', emoji: '🔥', desc: 'Full time' },
]

const GOALS = [
  { label: 'Get a job in a company', emoji: '🏢' },
  { label: 'Freelancing', emoji: '💻' },
  { label: 'Start my own startup', emoji: '🚀' },
  { label: 'Higher studies abroad', emoji: '✈️' },
  { label: 'Just learn for fun', emoji: '😊' },
]

const CAREER_SWITCH_STORAGE_KEY = 'careerlens.career-switch.state.v1'
const EMPTY_FORM = {
  background: '',
  target_field: '',
  hours_per_day: '',
  timeline: '',
  goal: '',
}

const REALITY_POINTS = [
  { text: 'CareerLens gives guidance — not a job guarantee', positive: false },
  { text: 'Consistency beats intensity — 1 hour daily beats 8 hours once a week', positive: true },
  { text: 'Build real projects — employers care about what you have built', positive: true },
  { text: 'Network actively — 70% of jobs are found through connections', positive: true },
  { text: "Don't skip fundamentals — shortcuts lead to weak foundations", positive: false },
  { text: 'Your non-tech background is an advantage in problem-solving and communication', positive: true },
]

// ============================================================
// State persistence
// ============================================================

function loadPersistedCareerSwitchState() {
  try {
    const raw = localStorage.getItem(CAREER_SWITCH_STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    return parsed && typeof parsed === 'object' ? parsed : null
  } catch {
    return null
  }
}

function savePersistedCareerSwitchState(state) {
  try {
    localStorage.setItem(CAREER_SWITCH_STORAGE_KEY, JSON.stringify(state))
  } catch {
    // Ignore storage quota/private mode errors.
  }
}

function clearPersistedCareerSwitchState() {
  try {
    localStorage.removeItem(CAREER_SWITCH_STORAGE_KEY)
  } catch {
    // Ignore storage errors.
  }
}

function StepIndicator({ current, total }) {
  return (
    <div className="flex gap-2 mb-6">
      {Array.from({ length: total }).map((_, i) => (
        <div
          key={i}
          className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${
            i < current ? 'bg-[#2563EB]' : 'bg-slate-200'
          }`}
        />
      ))}
    </div>
  )
}

// ============================================================
// Option Button
// ============================================================

const buttonMotion = {
  whileHover: { scale: 1.015, y: -1 },
  whileTap: { scale: 0.985 },
  transition: { duration: 0.15, ease: 'easeOut' },
}

function OptionBtn({ emoji, label, desc, selected, onClick }) {
  return (
    <motion.button
      {...buttonMotion}
      type="button"
      onClick={onClick}
      className={`p-3.5 rounded-xl border text-left transition-all flex items-center gap-3 w-full ${
        selected
          ? 'border-[#2563EB] bg-blue-50/80 text-[#0B0F19] font-bold shadow-[0_4px_16px_rgba(37,99,235,0.12)]'
          : 'border-slate-200 bg-white/70 text-[#475569] hover:border-blue-200 hover:bg-white hover:text-[#0B0F19]'
      }`}
    >
      <span className="text-xl shrink-0">{emoji}</span>
      <div className="flex-1 min-w-0">
        <p className="text-xs sm:text-sm font-semibold">{label}</p>
        {desc && <p className="text-[11px] text-[#64748B] mt-0.5">{desc}</p>}
      </div>
      {selected && <CheckCircle size={16} className="ml-auto text-[#2563EB] shrink-0" />}
    </motion.button>
  )
}

// ============================================================
// Resource Link Card
// ============================================================

function ResourceCard({ resource }) {
  const icon = resource.type === 'YouTube' ? '▶️' : resource.type === 'Course' ? '🎓' : '🌐'
  return (
    <a
      href={resource.url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-3 p-3 rounded-xl bg-white border border-slate-200/80 hover:border-blue-200 hover:bg-blue-50/30 transition-all group"
    >
      <span className="text-lg shrink-0">{icon}</span>
      <div className="flex-1 min-w-0">
        <p className="text-xs sm:text-sm font-semibold text-[#0B0F19] group-hover:text-[#2563EB] transition-colors truncate">
          {resource.name}
        </p>
        <p className="text-[11px] text-[#64748B] truncate">{resource.url}</p>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 text-[#475569] font-medium">
          {resource.type}
        </span>
        <ExternalLink size={12} className="text-[#94A3B8] group-hover:text-[#2563EB]" />
      </div>
    </a>
  )
}

// ============================================================
// Roadmap Result
// ============================================================

function RoadmapResult({ result, form, onReset }) {
  const backgroundLabel = String(form?.background || '').split('(')[0].trim() || 'Your Background'

  return (
    <div className="max-w-3xl mx-auto space-y-6 pb-16">
      {/* Header */}
      <GlassCard className="p-6 sm:p-8 border-white/95 shadow-glass-lg relative overflow-hidden">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <Rocket size={18} className="text-[#2563EB]" />
              <span className="text-xs font-bold text-[#2563EB] uppercase tracking-wider">
                Personalized Career Roadmap
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0B0F19] tracking-tight">
              {backgroundLabel} → {form.target_field || 'Target Role'}
            </h1>
            <p className="text-xs sm:text-sm text-[#64748B]">
              {form.timeline || 'Timeline pending'} · {form.hours_per_day || 'Study time pending'} · Goal: {form.goal || 'Goal pending'}
            </p>
          </div>
          <button
            type="button"
            onClick={onReset}
            className="flex items-center gap-1.5 text-xs font-semibold text-[#475569] hover:text-[#0B0F19] transition-colors px-3 py-1.5 rounded-full border border-slate-200 bg-white/80 shrink-0"
          >
            <RefreshCw size={13} /> Start Over
          </button>
        </div>
      </GlassCard>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Total Weeks', value: result.total_weeks, color: 'text-[#2563EB]', icon: '📅' },
          { label: 'Skills to Learn', value: result.total_skills, color: 'text-[#0B0F19]', icon: '🧠' },
          { label: 'Difficulty', value: result.difficulty, color: 'text-[#16A34A]', icon: '🎯' },
        ].map(({ label, value, color, icon }) => (
          <GlassCard key={label} className="p-4 sm:p-5 text-center border-white/90">
            <div className="text-2xl mb-1">{icon}</div>
            <p className={`text-xl sm:text-2xl font-black ${color}`}>{value}</p>
            <p className="text-xs text-[#64748B] mt-0.5">{label}</p>
          </GlassCard>
        ))}
      </div>

      {/* Summary */}
      {result.summary && (
        <GlassCard className="p-6 border-white/90 space-y-2">
          <h2 className="text-sm font-bold text-[#0B0F19] flex items-center gap-2">
            <BookOpen size={16} className="text-[#2563EB]" /> Overview
          </h2>
          <p className="text-xs sm:text-sm text-[#475569] leading-relaxed">{result.summary}</p>
        </GlassCard>
      )}

      {/* Phases */}
      <div className="space-y-4">
        <h2 className="text-base font-extrabold text-[#0B0F19] flex items-center gap-2">
          <Target size={18} className="text-[#2563EB]" /> Phase-by-Phase Plan
        </h2>
        {result.phases?.map((phase, i) => (
          <GlassCard key={i} className="p-5 sm:p-6 border-white/90 space-y-4">
            {/* Phase Header */}
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-blue-50 text-[#2563EB] border border-blue-200 flex items-center justify-center text-sm font-extrabold shrink-0">
                {i + 1}
              </div>
              <div>
                <p className="font-bold text-sm sm:text-base text-[#0B0F19]">{phase.title}</p>
                <p className="text-xs text-[#64748B]">
                  Week {phase.week_start} – Week {phase.week_end}
                </p>
              </div>
            </div>

            {/* Topics */}
            {phase.topics?.length > 0 && (
              <div>
                <p className="text-xs font-bold text-[#0B0F19] uppercase tracking-wider mb-2">What you'll learn</p>
                <ul className="space-y-1.5">
                  {phase.topics.map((t, j) => (
                    <li key={j} className="text-xs sm:text-sm text-[#475569] flex items-start gap-2">
                      <ChevronRight size={14} className="text-[#2563EB] mt-0.5 shrink-0" /> {t}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Resources with links */}
            {phase.free_resources?.length > 0 && (
              <div>
                <p className="text-xs font-bold text-[#0B0F19] uppercase tracking-wider mb-2">
                  📚 Recommended Free Resources
                </p>
                <div className="flex flex-col gap-2">
                  {phase.free_resources.map((r, j) => (
                    <ResourceCard key={j} resource={typeof r === 'string' ? { name: r, url: '#', type: 'Website' } : r} />
                  ))}
                </div>
              </div>
            )}
          </GlassCard>
        ))}
      </div>

      {/* Start Today */}
      {result.start_today?.length > 0 && (
        <GlassCard className="p-6 border-emerald-200/80 bg-emerald-50/30 space-y-3">
          <h2 className="text-sm sm:text-base font-bold text-[#0B0F19] flex items-center gap-2">
            <span className="text-lg">🟢</span> Start TODAY — Action Steps
          </h2>
          <div className="space-y-2.5">
            {result.start_today.map((s, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-white border border-emerald-200/60 shadow-xs">
                <div className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center text-[#16A34A] text-xs font-bold shrink-0 mt-0.5">
                  {i + 1}
                </div>
                <p className="text-xs sm:text-sm text-[#0B0F19] leading-relaxed">{s}</p>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* Reality Check */}
      <GlassCard className="p-6 border-amber-200/80 bg-amber-50/40 space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center shrink-0 text-amber-600">
            <AlertTriangle size={20} />
          </div>
          <div>
            <h2 className="text-sm sm:text-base font-bold text-[#0B0F19]">Honest Reality Check</h2>
            <p className="text-xs text-[#64748B]">Read this carefully before you start</p>
          </div>
        </div>

        {result.reality_check && (
          <p className="text-xs sm:text-sm text-[#475569] leading-relaxed p-3.5 rounded-xl bg-white border border-amber-200/60">
            {result.reality_check}
          </p>
        )}

        <div className="space-y-2">
          {REALITY_POINTS.map((point, i) => (
            <div
              key={i}
              className={`flex items-start gap-2.5 px-3 py-2 rounded-xl text-xs ${
                point.positive
                  ? 'bg-emerald-50 text-emerald-900 border border-emerald-200/60'
                  : 'bg-rose-50 text-rose-900 border border-rose-200/60'
              }`}
            >
              {point.positive ? (
                <CheckCircle size={14} className="shrink-0 mt-0.5 text-[#16A34A]" />
              ) : (
                <XCircle size={14} className="shrink-0 mt-0.5 text-[#E11D48]" />
              )}
              <span>{point.text}</span>
            </div>
          ))}
        </div>
      </GlassCard>

      {/* Bottom CTA */}
      <div className="flex gap-3 pt-2">
        <button
          type="button"
          onClick={onReset}
          className="w-full flex items-center justify-center gap-2 py-3.5 rounded-full border border-slate-200 bg-white text-[#0B0F19] font-bold text-sm hover:bg-slate-50 transition-all shadow-xs"
        >
          <RefreshCw size={15} /> Generate Another Roadmap
        </button>
      </div>
    </div>
  )
}

// ============================================================
// Main Component
// ============================================================

export default function CareerSwitch() {
  const TOTAL_STEPS = 4
  const [persistedState] = useState(() => loadPersistedCareerSwitchState())
  const [step, setStep] = useState(() => {
    const savedStep = persistedState?.step
    if (typeof savedStep !== 'number') return 1
    return Math.min(Math.max(savedStep, 1), TOTAL_STEPS)
  })
  const [form, setForm] = useState(() => {
    const savedForm = persistedState?.form
    if (!savedForm || typeof savedForm !== 'object') return EMPTY_FORM
    return { ...EMPTY_FORM, ...savedForm }
  })
  const [result, setResult] = useState(() => {
    const savedResult = persistedState?.result
    return savedResult && typeof savedResult === 'object' && !Array.isArray(savedResult) ? savedResult : null
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handle = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  useEffect(() => {
    savePersistedCareerSwitchState({ step, form, result })
  }, [step, form, result])

  const handleSubmit = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.generateBeginnerRoadmap(form)
      setResult(res.roadmap)
    } catch (err) {
      setError(err.message || 'Failed to generate roadmap.')
    }
    setLoading(false)
  }

  const handleStartOver = () => {
    clearPersistedCareerSwitchState()
    setResult(null)
    setStep(1)
    setForm(EMPTY_FORM)
    setError('')
  }

  const hasRoadmapResult = result && typeof result === 'object' && !Array.isArray(result)

  if (hasRoadmapResult) {
    return (
      <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
        <RoadmapResult result={result} form={form} onReset={handleStartOver} />
      </motion.div>
    )
  }

  return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
      <div className="max-w-2xl mx-auto space-y-6 pb-16">
        {/* Header */}
        <div className="text-center space-y-1.5">
          <Badge sparkle size="sm" className="mx-auto mb-1">
            Zero-to-Job Guide
          </Badge>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0B0F19] tracking-tight flex items-center justify-center gap-2.5">
            <Rocket size={24} className="text-[#2563EB]" />
            <span>Career Switch</span>
          </h1>
          <p className="text-xs sm:text-sm text-[#64748B]">
            Complete beginner? No problem. Get your tailored transition plan in 60 seconds.
          </p>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-[#E11D48] text-xs font-semibold">
            {error}
          </div>
        )}

        <GlassCard className="p-6 sm:p-8 border-white/95 shadow-glass-lg">
          <StepIndicator current={step} total={TOTAL_STEPS} />

          <AnimatePresence mode="wait">
            {/* Step 1 — Background */}
            {step === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 16 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -16 }}
                className="space-y-4"
              >
                <div>
                  <h2 className="text-base sm:text-lg font-bold text-[#0B0F19]">What's your current background?</h2>
                  <p className="text-xs text-[#64748B] mt-0.5">This helps us tailor advice specifically for your starting point.</p>
                </div>
                <div className="grid grid-cols-1 gap-2">
                  {BACKGROUNDS.map(({ label, emoji }) => (
                    <OptionBtn
                      key={label}
                      emoji={emoji}
                      label={label}
                      selected={form.background === label}
                      onClick={() => handle('background', label)}
                    />
                  ))}
                </div>
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  disabled={!form.background}
                  className="w-full flex items-center justify-center gap-2 py-3.5 rounded-full bg-[#0B0F19] text-white font-bold text-sm hover:bg-[#1E293B] transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed mt-2"
                >
                  Continue <ChevronRight size={16} />
                </button>
              </motion.div>
            )}

            {/* Step 2 — Tech Field */}
            {step === 2 && (
              <motion.div
                key="step2"
                initial={{ opacity: 0, x: 16 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -16 }}
                className="space-y-4"
              >
                <div>
                  <h2 className="text-base sm:text-lg font-bold text-[#0B0F19]">Which tech field interests you?</h2>
                  <p className="text-xs text-[#64748B] mt-0.5">Pick the role that aligns best with your target.</p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {TECH_FIELDS.map(({ label, emoji }) => (
                    <OptionBtn
                      key={label}
                      emoji={emoji}
                      label={label}
                      selected={form.target_field === label}
                      onClick={() => handle('target_field', label)}
                    />
                  ))}
                </div>
                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setStep(1)}
                    className="flex-1 py-3 rounded-full border border-slate-200 bg-white/80 text-[#0B0F19] font-bold text-sm hover:bg-white transition-all"
                  >
                    ← Back
                  </button>
                  <button
                    type="button"
                    onClick={() => setStep(3)}
                    disabled={!form.target_field}
                    className="flex-1 flex items-center justify-center gap-2 py-3 rounded-full bg-[#0B0F19] text-white font-bold text-sm hover:bg-[#1E293B] transition-all shadow-md disabled:opacity-50"
                  >
                    Continue <ChevronRight size={16} />
                  </button>
                </div>
              </motion.div>
            )}

            {/* Step 3 — Time & Timeline */}
            {step === 3 && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, x: 16 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -16 }}
                className="space-y-5"
              >
                <div>
                  <h2 className="text-base sm:text-lg font-bold text-[#0B0F19] flex items-center gap-2">
                    <Clock size={16} className="text-[#2563EB]" /> How many hours can you study daily?
                  </h2>
                  <p className="text-xs text-[#64748B] mt-0.5">Consistency matters more than intensity.</p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {HOURS.map(({ label, emoji, desc }) => (
                    <OptionBtn
                      key={label}
                      emoji={emoji}
                      label={label}
                      desc={desc}
                      selected={form.hours_per_day === label}
                      onClick={() => handle('hours_per_day', label)}
                    />
                  ))}
                </div>
                <div>
                  <h2 className="text-base sm:text-lg font-bold text-[#0B0F19] flex items-center gap-2">
                    <Star size={16} className="text-[#2563EB]" /> Target timeline
                  </h2>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-2">
                    {TIMELINES.map(({ label, emoji, desc }) => (
                      <OptionBtn
                        key={label}
                        emoji={emoji}
                        label={label}
                        desc={desc}
                        selected={form.timeline === label}
                        onClick={() => handle('timeline', label)}
                      />
                    ))}
                  </div>
                </div>
                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setStep(2)}
                    className="flex-1 py-3 rounded-full border border-slate-200 bg-white/80 text-[#0B0F19] font-bold text-sm hover:bg-white transition-all"
                  >
                    ← Back
                  </button>
                  <button
                    type="button"
                    onClick={() => setStep(4)}
                    disabled={!form.hours_per_day || !form.timeline}
                    className="flex-1 flex items-center justify-center gap-2 py-3 rounded-full bg-[#0B0F19] text-white font-bold text-sm hover:bg-[#1E293B] transition-all shadow-md disabled:opacity-50"
                  >
                    Continue <ChevronRight size={16} />
                  </button>
                </div>
              </motion.div>
            )}

            {/* Step 4 — Goal */}
            {step === 4 && (
              <motion.div
                key="step4"
                initial={{ opacity: 0, x: 16 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -16 }}
                className="space-y-4"
              >
                <div>
                  <h2 className="text-base sm:text-lg font-bold text-[#0B0F19] flex items-center gap-2">
                    <Target size={16} className="text-[#2563EB]" /> What's your end goal?
                  </h2>
                  <p className="text-xs text-[#64748B] mt-0.5">This shapes the depth of skills and projects we recommend.</p>
                </div>
                <div className="grid grid-cols-1 gap-2">
                  {GOALS.map(({ label, emoji }) => (
                    <OptionBtn
                      key={label}
                      emoji={emoji}
                      label={label}
                      selected={form.goal === label}
                      onClick={() => handle('goal', label)}
                    />
                  ))}
                </div>

                {/* Profile summary */}
                {form.goal && (
                  <div className="p-4 rounded-xl bg-blue-50/80 border border-blue-100 text-xs space-y-1">
                    <p className="text-[#2563EB] font-bold mb-1">Your Profile Summary</p>
                    <p className="text-[#475569]">🎓 Background: <strong className="text-[#0B0F19]">{form.background}</strong></p>
                    <p className="text-[#475569]">🎯 Target: <strong className="text-[#0B0F19]">{form.target_field}</strong></p>
                    <p className="text-[#475569]">⏰ Study time: <strong className="text-[#0B0F19]">{form.hours_per_day}</strong></p>
                    <p className="text-[#475569]">📅 Timeline: <strong className="text-[#0B0F19]">{form.timeline}</strong></p>
                    <p className="text-[#475569]">🏆 Goal: <strong className="text-[#0B0F19]">{form.goal}</strong></p>
                  </div>
                )}

                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setStep(3)}
                    className="flex-1 py-3.5 rounded-full border border-slate-200 bg-white/80 text-[#0B0F19] font-bold text-sm hover:bg-white transition-all"
                  >
                    ← Back
                  </button>
                  <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={!form.goal || loading}
                    className="flex-1 flex items-center justify-center gap-2 py-3.5 rounded-full bg-[#0B0F19] text-white font-bold text-sm hover:bg-[#1E293B] transition-all shadow-md disabled:opacity-50"
                  >
                    {loading ? (
                      <>
                        <Loader2 size={16} className="animate-spin" /> Generating roadmap...
                      </>
                    ) : (
                      <>
                        <Rocket size={16} /> Generate My Roadmap
                      </>
                    )}
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </GlassCard>
      </div>
    </motion.div>
  )
}
