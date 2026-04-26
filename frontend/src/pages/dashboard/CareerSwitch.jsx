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
// Step Indicator
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
        <div key={i} className={`h-1.5 flex-1 rounded-full transition-all duration-500
          ${i < current ? 'bg-amber-500' : i === current - 1 ? 'bg-amber-400' : 'bg-white/10'}`} />
      ))}
    </div>
  )
}

// ============================================================
// Option Button
// ============================================================

const buttonMotion = {
  whileHover: { scale: 1.03, y: -1 },
  whileTap: { scale: 0.97 },
  transition: { duration: 0.15, ease: 'easeOut' },
}

function OptionBtn({ emoji, label, desc, selected, onClick }) {
  return (
    <motion.button {...buttonMotion} onClick={onClick}
      className={`p-3 rounded-xl border text-left transition-all duration-200 flex items-center gap-3
        ${selected
          ? 'border-amber-500 bg-amber-500/20 text-[#0a0a0a] shadow-lg shadow-amber-500/10'
          : 'border-white/10 text-[#78716c] hover:border-white/30 hover:text-white hover:bg-white/5'}`}>
      <span className="text-xl shrink-0">{emoji}</span>
      <div>
        <p className="text-sm font-medium">{label}</p>
        {desc && <p className="text-xs text-[#44403c]">{desc}</p>}
      </div>
      {selected && <CheckCircle size={16} className="ml-auto text-amber-400 shrink-0" />}
    </motion.button>
  )
}

// ============================================================
// Resource Link Card
// ============================================================

function ResourceCard({ resource }) {
  const icon = resource.type === 'YouTube' ? '▶️' : resource.type === 'Course' ? '🎓' : '🌐'
  return (
    <a href={resource.url} target="_blank" rel="noopener noreferrer"
      className="flex items-center gap-3 p-3 rounded-xl bg-white/5 hover:bg-white/10
                 border border-white/5 hover:border-amber-500/30 transition-all group">
      <span className="text-lg shrink-0">{icon}</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white group-hover:text-amber-300 transition-colors truncate">
          {resource.name}
        </p>
        <p className="text-xs text-[#44403c] truncate">{resource.url}</p>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-[#78716c]">{resource.type}</span>
        <ExternalLink size={12} className="text-[#44403c] group-hover:text-amber-400" />
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
    <div className="max-w-3xl mx-auto space-y-6">

      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden glass rounded-2xl p-6">
        <div className="absolute inset-0 bg-red-500/5" />
        <div className="relative flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Rocket size={20} className="text-amber-400" />
              <span className="text-sm text-amber-400 font-medium">Your Personal Roadmap</span>
            </div>
            <h1 className="text-2xl font-bold text-white mb-1">
              {backgroundLabel} → {form.target_field || 'Target Role'}
            </h1>
            <p className="text-[#78716c] text-sm">
              {form.timeline || 'Timeline pending'} · {form.hours_per_day || 'Study time pending'} · Goal: {form.goal || 'Goal pending'}
            </p>
          </div>
          <motion.button {...buttonMotion} onClick={onReset}
            className="flex items-center gap-1 text-xs text-[#78716c] hover:text-white transition-colors px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10">
            <RefreshCw size={12} /> Start Over
          </motion.button>
        </div>
      </motion.div>

      {/* Stats */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
        className="grid grid-cols-3 gap-4">
        {[
          { label: 'Total Weeks', value: result.total_weeks, color: 'text-amber-400', icon: '📅' },
          { label: 'Skills to Learn', value: result.total_skills, color: 'text-yellow-500', icon: '🧠' },
          { label: 'Level', value: result.difficulty, color: 'text-green-400', icon: '🎯' },
        ].map(({ label, value, color, icon }) => (
          <div key={label} className="glass p-4 rounded-xl text-center">
            <div className="text-2xl mb-1">{icon}</div>
            <p className={`text-xl font-bold ${color}`}>{value}</p>
            <p className="text-xs text-[#78716c]">{label}</p>
          </div>
        ))}
      </motion.div>

      {/* Summary */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
        className="glass p-6 rounded-2xl">
        <h2 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
          <BookOpen size={18} className="text-amber-400" /> Overview
        </h2>
        <p className="text-[#d6d3d1] text-sm leading-relaxed">{result.summary}</p>
      </motion.div>

      {/* Phases */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <Target size={18} className="text-yellow-500" /> Phase-by-Phase Plan
        </h2>
        {result.phases?.map((phase, i) => (
          <motion.div key={i}
            initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
            className="glass p-5 rounded-2xl">

            {/* Phase Header */}
            <div className="flex items-center gap-3 mb-4">
              <div className="w-9 h-9 rounded-xl border border-red-500/20 bg-[#151924]
                              flex items-center justify-center text-sm font-bold text-white shrink-0">
                {i + 1}
              </div>
              <div>
                <p className="font-bold text-white">{phase.title}</p>
                <p className="text-xs text-[#78716c]">
                  Week {phase.week_start} – Week {phase.week_end}
                </p>
              </div>
            </div>

            {/* Topics */}
            <div className="mb-4">
              <p className="text-xs font-semibold text-[#78716c] uppercase tracking-wide mb-2">What you'll learn</p>
              <ul className="space-y-1.5">
                {phase.topics?.map((t, j) => (
                  <li key={j} className="text-sm text-[#d6d3d1] flex items-start gap-2">
                    <ChevronRight size={14} className="text-amber-400 mt-0.5 shrink-0" /> {t}
                  </li>
                ))}
              </ul>
            </div>

            {/* Resources with links */}
            {phase.free_resources?.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-[#78716c] uppercase tracking-wide mb-2">
                  📚 Free Resources & Links
                </p>
                <div className="flex flex-col gap-2">
                  {phase.free_resources.map((r, j) => (
                    <ResourceCard key={j} resource={typeof r === 'string' ? { name: r, url: '#', type: 'Website' } : r} />
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        ))}
      </div>

      {/* Start Today */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
        className="glass p-6 rounded-2xl border border-green-500/20 bg-green-500/5">
        <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <span className="text-2xl">🟢</span> Start TODAY — Right Now
        </h2>
        <div className="space-y-3">
          {result.start_today?.map((s, i) => (
            <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-green-500/10 border border-green-500/10">
              <div className="w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center
                              text-green-400 text-xs font-bold shrink-0 mt-0.5">
                {i + 1}
              </div>
              <p className="text-sm text-[#e7e5e4]">{s}</p>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Useful Links */}
      {result.useful_links?.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
          className="glass p-6 rounded-2xl">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <span className="text-xl">🔗</span> Essential Websites to Bookmark
          </h2>
          <div className="grid md:grid-cols-2 gap-3">
            {result.useful_links.map((link, i) => (
              <a key={i} href={link.url} target="_blank" rel="noopener noreferrer"
                className="flex items-start gap-3 p-4 rounded-xl bg-white/5 hover:bg-white/10
                           border border-white/5 hover:border-amber-500/30 transition-all group">
                <span className="text-2xl shrink-0">🌐</span>
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-white group-hover:text-amber-300 transition-colors">
                    {link.name}
                  </p>
                  <p className="text-xs text-[#78716c] mt-0.5">{link.description}</p>
                  <p className="text-xs text-[#44403c] truncate mt-1">{link.url}</p>
                </div>
                <ExternalLink size={14} className="text-[#44403c] group-hover:text-amber-400 shrink-0 mt-1" />
              </a>
            ))}
          </div>
        </motion.div>
      )}

      {/* Reality Check */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
        className="glass p-6 rounded-2xl border border-amber-500/20 bg-amber-500/5">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center shrink-0">
            <AlertTriangle size={20} className="text-amber-400" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Honest Reality Check</h2>
            <p className="text-xs text-amber-400">Read this carefully before you start</p>
          </div>
        </div>

        {/* AI generated reality check */}
        <p className="text-[#d6d3d1] text-sm leading-relaxed mb-5 p-4 rounded-xl bg-white/5 border border-white/5">
          {result.reality_check}
        </p>

        {/* Universal truth points */}
        <div className="space-y-2">
          {REALITY_POINTS.map((point, i) => (
            <div key={i} className={`flex items-start gap-3 px-3 py-2.5 rounded-xl text-sm
              ${point.positive
                ? 'bg-green-500/10 border border-green-500/10 text-green-300'
                : 'bg-red-500/10 border border-red-500/10 text-red-300'}`}>
              {point.positive
                ? <CheckCircle size={15} className="shrink-0 mt-0.5 text-green-400" />
                : <XCircle size={15} className="shrink-0 mt-0.5 text-red-400" />}
              {point.text}
            </div>
          ))}
        </div>

        {/* Disclaimer */}
        <div className="mt-4 p-3 rounded-xl bg-white/5 border border-white/5">
          <p className="text-xs text-[#78716c] text-center">
            ⚡ CareerLens provides <strong className="text-white">guidance</strong>, not guarantees.
            Your success depends on your consistency, effort, and dedication.
            We are committed to giving you the most accurate and up-to-date roadmap possible.
          </p>
        </div>
      </motion.div>

      {/* Bottom CTA */}
      <div className="flex gap-3 pb-6">
        <motion.button {...buttonMotion} onClick={onReset} className="btn-ghost flex-1 flex items-center justify-center gap-2">
          <RefreshCw size={16} /> Generate New Roadmap
        </motion.button>
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

  const handle = (k, v) => setForm(f => ({ ...f, [k]: v }))

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
      setError(err.message)
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

  if (hasRoadmapResult) return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
      <RoadmapResult result={result} form={form} onReset={handleStartOver} />
    </motion.div>
  )

  return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
    <div className="max-w-2xl mx-auto space-y-6">

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <Rocket size={28} className="text-amber-400" /> Career Switch
        </h1>
        <p className="text-[#78716c] mt-1">
          Complete beginner? No problem. Get your personalized zero-to-job roadmap in 60 seconds.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}

      <div className="glass p-6 rounded-2xl">
        <StepIndicator current={step} total={TOTAL_STEPS} />

        <AnimatePresence mode="wait">

          {/* Step 1 — Background */}
          {step === 1 && (
            <motion.div key="step1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
              className="space-y-4">
              <div>
                <h2 className="text-xl font-bold text-white mb-1">What's your current background?</h2>
                <p className="text-[#78716c] text-sm">This helps us tailor advice specifically for you</p>
              </div>
              <div className="grid grid-cols-1 gap-2">
                {BACKGROUNDS.map(({ label, emoji }) => (
                  <OptionBtn key={label} emoji={emoji} label={label}
                    selected={form.background === label}
                    onClick={() => handle('background', label)} />
                ))}
              </div>
              <motion.button {...buttonMotion} onClick={() => setStep(2)} disabled={!form.background}
                className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
                Continue <ChevronRight size={16} />
              </motion.button>
            </motion.div>
          )}

          {/* Step 2 — Tech Field */}
          {step === 2 && (
            <motion.div key="step2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
              className="space-y-4">
              <div>
                <h2 className="text-xl font-bold text-white mb-1">Which tech field interests you?</h2>
                <p className="text-[#78716c] text-sm">Pick the one that excites you the most</p>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {TECH_FIELDS.map(({ label, emoji }) => (
                  <OptionBtn key={label} emoji={emoji} label={label}
                    selected={form.target_field === label}
                    onClick={() => handle('target_field', label)} />
                ))}
              </div>
              <div className="flex gap-3">
                <motion.button {...buttonMotion} onClick={() => setStep(1)} className="btn-ghost flex-1">← Back</motion.button>
                <motion.button {...buttonMotion} onClick={() => setStep(3)} disabled={!form.target_field}
                  className="btn-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-50">
                  Continue <ChevronRight size={16} />
                </motion.button>
              </div>
            </motion.div>
          )}

          {/* Step 3 — Time & Timeline */}
          {step === 3 && (
            <motion.div key="step3" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
              className="space-y-5">
              <div>
                <h2 className="text-xl font-bold text-white mb-1 flex items-center gap-2">
                  <Clock size={18} className="text-amber-400" /> How many hours can you study daily?
                </h2>
                <p className="text-[#78716c] text-sm">Be realistic — consistency matters more than intensity</p>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {HOURS.map(({ label, emoji, desc }) => (
                  <OptionBtn key={label} emoji={emoji} label={label} desc={desc}
                    selected={form.hours_per_day === label}
                    onClick={() => handle('hours_per_day', label)} />
                ))}
              </div>
              <div>
                <h2 className="text-xl font-bold text-white mb-1 flex items-center gap-2">
                  <Star size={18} className="text-yellow-500" /> Target timeline
                </h2>
                <div className="grid grid-cols-3 gap-2">
                  {TIMELINES.map(({ label, emoji, desc }) => (
                    <OptionBtn key={label} emoji={emoji} label={label} desc={desc}
                      selected={form.timeline === label}
                      onClick={() => handle('timeline', label)} />
                  ))}
                </div>
              </div>
              <div className="flex gap-3">
                <motion.button {...buttonMotion} onClick={() => setStep(2)} className="btn-ghost flex-1">← Back</motion.button>
                <motion.button {...buttonMotion} onClick={() => setStep(4)} disabled={!form.hours_per_day || !form.timeline}
                  className="btn-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-50">
                  Continue <ChevronRight size={16} />
                </motion.button>
              </div>
            </motion.div>
          )}

          {/* Step 4 — Goal */}
          {step === 4 && (
            <motion.div key="step4" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
              className="space-y-4">
              <div>
                <h2 className="text-xl font-bold text-white mb-1 flex items-center gap-2">
                  <Target size={18} className="text-amber-400" /> What's your end goal?
                </h2>
                <p className="text-[#78716c] text-sm">This shapes the type of skills and projects we recommend</p>
              </div>
              <div className="grid grid-cols-1 gap-2">
                {GOALS.map(({ label, emoji }) => (
                  <OptionBtn key={label} emoji={emoji} label={label}
                    selected={form.goal === label}
                    onClick={() => handle('goal', label)} />
                ))}
              </div>

              {/* Summary before submit */}
              {form.goal && (
                <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                  className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-sm space-y-1">
                  <p className="text-amber-300 font-semibold mb-2">📋 Your Profile Summary</p>
                  <p className="text-[#d6d3d1]">🎓 Background: <span className="text-white">{form.background}</span></p>
                  <p className="text-[#d6d3d1]">🎯 Target: <span className="text-white">{form.target_field}</span></p>
                  <p className="text-[#d6d3d1]">⏰ Study time: <span className="text-white">{form.hours_per_day}</span></p>
                  <p className="text-[#d6d3d1]">📅 Timeline: <span className="text-white">{form.timeline}</span></p>
                  <p className="text-[#d6d3d1]">🏆 Goal: <span className="text-white">{form.goal}</span></p>
                </motion.div>
              )}

              <div className="flex gap-3">
                <motion.button {...buttonMotion} onClick={() => setStep(3)} className="btn-ghost flex-1">← Back</motion.button>
                <motion.button {...buttonMotion} onClick={handleSubmit} disabled={!form.goal || loading}
                  className="btn-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-50 py-4">
                  {loading
                    ? <><Loader2 size={16} className="animate-spin" /> Generating roadmap...</>
                    : <><Rocket size={16} /> Generate My Roadmap</>}
                </motion.button>
              </div>
            </motion.div>
          )}

        </AnimatePresence>
      </div>
    </div>
    </motion.div>
  )
}







