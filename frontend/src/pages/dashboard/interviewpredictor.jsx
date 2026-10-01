import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../../context/AuthContext'
import { api } from '../../services/api'
import {
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
  FileText,
  Target,
  Sparkles,
  Loader2,
  Lock,
  Upload,
  RefreshCw,
  Github,
  History,
  X,
  Code2,
} from 'lucide-react'
import { GlassCard, Badge } from '../../components/ui'

const GITHUB_LOCK_KEY = 'careerlens_saved_github'

const normalizeGithubUrl = (url) => {
  if (!url) return ''
  const trimmed = url.trim()
  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) return trimmed
  return `https://github.com/${trimmed.replace(/^@/, '')}`
}

function resolveGithubFromAuthUser(user) {
  if (!user) return ''
  const identities = Array.isArray(user.identities) ? user.identities : []
  const hasGithubIdentity = identities.some((identity) => identity?.provider === 'github')
  const userMeta = user.user_metadata || {}
  const appMeta = user.app_metadata || {}
  const providers = new Set([...(appMeta.providers || []), appMeta.provider].filter(Boolean))

  if (hasGithubIdentity || userMeta.user_name || userMeta.preferred_username) {
    const username = userMeta.user_name || userMeta.preferred_username || ''
    if (username) return `https://github.com/${username}`
  }

  return providers.has('github') ? normalizeGithubUrl(userMeta.profile || userMeta.url || '') : ''
}

function CircularMeter({ value }) {
  const [current, setCurrent] = useState(0)
  const size = 200
  const radius = 80
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (current / 100) * circumference
  const color = value >= 70 ? '#16A34A' : value >= 50 ? '#2563EB' : '#E11D48'
  const badgeClass =
    value >= 70
      ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
      : value >= 50
        ? 'bg-blue-50 text-blue-800 border-blue-200'
        : 'bg-rose-50 text-rose-800 border-rose-200'
  const badgeText = value >= 70 ? 'Strong Candidate' : value >= 50 ? 'Competitive' : 'Needs Optimization'

  useEffect(() => {
    let frame
    let start = 0
    const step = value / 60

    const animate = () => {
      start += step
      if (start >= value) {
        setCurrent(value)
        return
      }
      setCurrent(Math.floor(start))
      frame = requestAnimationFrame(animate)
    }

    frame = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(frame)
  }, [value])

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
          <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#E2E8F0" strokeWidth={12} />
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={12}
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.2, ease: 'easeOut' }}
          />
        </svg>

        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-black text-[#0B0F19]">{current}%</span>
          <span className="text-[10px] uppercase font-bold tracking-wider text-[#64748B] mt-1">Interview Odds</span>
        </div>
      </div>
      <div className={`px-3 py-1 rounded-full text-xs font-bold border ${badgeClass}`}>{badgeText}</div>
    </div>
  )
}

function ScoreCard({ label, value, icon: Icon, color, barColor = 'bg-[#2563EB]' }) {
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white/90 p-4 shadow-xs">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon size={16} style={{ color }} />
          <span className="text-xs font-bold text-[#0B0F19]">{label}</span>
        </div>
        <span className="text-xl font-black text-[#0B0F19]">{value}%</span>
      </div>
      <div className="relative h-2 overflow-hidden rounded-full bg-slate-100">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 1, ease: 'easeOut', delay: 0.2 }}
          className={`h-full rounded-full ${barColor}`}
        />
      </div>
    </div>
  )
}

function Section({ icon: Icon, title, iconColor, children }) {
  return (
    <GlassCard className="p-5 sm:p-6 border-white/95 shadow-glass space-y-3">
      <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
        <Icon size={16} style={{ color: iconColor }} />
        <h3 className="text-xs sm:text-sm font-bold text-[#0B0F19] uppercase tracking-wider">{title}</h3>
      </div>
      <div>{children}</div>
    </GlassCard>
  )
}

function HistoryModal({ onClose }) {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .getPredictionHistory()
      .then((response) => {
        setHistory(response.history || [])
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  const formatDate = (iso) => new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  const valueColor = (value) => (value >= 70 ? 'text-[#16A34A]' : value >= 50 ? 'text-[#2563EB]' : 'text-[#E11D48]')

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm"
      onClick={(event) => event.target === event.currentTarget && onClose()}
    >
      <GlassCard className="w-full max-w-xl p-6 border-white/95 shadow-glass-lg space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-base sm:text-lg font-bold text-[#0B0F19]">
            <History size={18} className="text-[#2563EB]" />
            Past Predictions
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-1.5 text-[#64748B] hover:bg-slate-100 hover:text-[#0B0F19] transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 size={24} className="animate-spin text-[#2563EB]" />
          </div>
        ) : history.length === 0 ? (
          <p className="py-10 text-center text-xs text-[#64748B]">No predictions logged yet.</p>
        ) : (
          <div className="max-h-96 space-y-2.5 overflow-y-auto pr-1">
            {history.map((item, index) => (
              <div key={index} className="rounded-xl border border-slate-200/80 bg-white p-3.5 shadow-xs">
                <div className="mb-1.5 flex items-center justify-between">
                  <span className={`text-xl font-black ${valueColor(item.interview_probability)}`}>
                    {item.interview_probability}%
                  </span>
                  <span className="text-[11px] text-[#64748B]">{formatDate(item.created_at)}</span>
                </div>
                <p className="line-clamp-2 text-xs text-[#475569]">{item.job_description}</p>
                <div className="mt-2.5 flex gap-3 text-[11px] font-semibold text-[#64748B]">
                  <span>Skill: {item.skill_match}%</span>
                  <span>ATS: {item.ats_score}%</span>
                  <span>Portfolio: {item.portfolio_score}%</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </GlassCard>
    </div>
  )
}

export default function InterviewPredictor() {
  const { user: authUser } = useAuth()
  const [form, setForm] = useState({ github_url: '', job_description: '' })
  const [githubLocked, setGithubLocked] = useState(false)
  const [resumeFile, setResumeFile] = useState(null)
  const [resumeText, setResumeText] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [showHistory, setShowHistory] = useState(false)
  const [dragging, setDragging] = useState(false)
  const fileRef = useRef(null)

  useEffect(() => {
    let active = true

    const load = async () => {
      try {
        const [meSettled, historySettled] = await Promise.allSettled([api.getMe(), api.getResumeHistory()])
        if (!active) return

        const meRes = meSettled.status === 'fulfilled' ? meSettled.value : null
        const historyRes = historySettled.status === 'fulfilled' ? historySettled.value : { analyses: [] }
        const githubFromOAuth = meRes?.user?.github_username ? `https://github.com/${meRes.user.github_username}` : ''
        const githubFromAuthSession = resolveGithubFromAuthUser(authUser)
        const historyGithub = Array.isArray(historyRes?.analyses)
          ? historyRes.analyses.find((analysis) => analysis?.github_url)?.github_url || ''
          : ''
        const storedGithub = localStorage.getItem(GITHUB_LOCK_KEY) || ''
        const savedGithub = normalizeGithubUrl(
          meRes?.user?.github_url || githubFromOAuth || githubFromAuthSession || historyGithub || storedGithub || '',
        )

        if (savedGithub) {
          setGithubLocked(true)
          setForm((current) => ({ ...current, github_url: savedGithub }))
          localStorage.setItem(GITHUB_LOCK_KEY, savedGithub)
          return
        }

        setGithubLocked(false)
      } catch {}
    }

    load()
    return () => {
      active = false
    }
  }, [authUser])

  const handle = (key, value) => setForm((current) => ({ ...current, [key]: value }))

  const handleFile = async (file) => {
    if (!file || (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf')) {
      setError('Please upload a PDF file.')
      return
    }
    setResumeFile(file)
    setError('')
    try {
      const buffer = await file.arrayBuffer()
      const uint8 = new Uint8Array(buffer)
      let binary = ''
      const chunk = 8192
      for (let i = 0; i < uint8.length; i += chunk) {
        binary += String.fromCharCode.apply(null, uint8.subarray(i, i + chunk))
      }
      const base64 = btoa(binary)
      const res = await api.extractResumeText({ pdf_base64: base64 })
      if (res && res.text) {
        setResumeText(res.text)
      }
    } catch {
      setError('Could not extract text from PDF. You can still proceed if the file is valid.')
    }
  }

  const handleDrop = (event) => {
    event.preventDefault()
    setDragging(false)
    if (event.dataTransfer.files?.[0]) {
      handleFile(event.dataTransfer.files[0])
    }
  }

  const handlePredict = async () => {
    if (!resumeFile && !resumeText.trim()) {
      setError('Upload your resume first.')
      return
    }
    if (!form.job_description.trim()) {
      setError('Paste a job description.')
      return
    }

    setLoading(true)
    setError('')
    try {
      const fd = new FormData()
      if (resumeFile) fd.append('resume', resumeFile)
      if (resumeText) fd.append('resume_text', resumeText)
      fd.append('github_url', form.github_url || '')
      fd.append('job_description', form.job_description.trim())

      const res = await api.predictInterview(fd)
      setResult(res)
    } catch (predictError) {
      setError(predictError.message || 'Failed to predict interview probability.')
    }
    setLoading(false)
  }

  const reset = () => {
    setResult(null)
    setForm((current) => ({
      ...current,
      job_description: '',
      github_url: githubLocked ? current.github_url : '',
    }))
  }

  if (result) {
    return (
      <div className="mx-auto max-w-4xl space-y-6 pb-16">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <Badge sparkle size="sm" className="mb-1">Prediction Report</Badge>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0B0F19] tracking-tight">
              Interview Readiness
            </h1>
            <p className="text-xs sm:text-sm text-[#64748B] mt-1">
              Data-backed estimate of your likelihood to pass initial screening.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setShowHistory(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-full border border-slate-200 bg-white/80 text-xs font-semibold text-[#475569] hover:text-[#0B0F19]"
            >
              <History size={13} /> History
            </button>
            <button
              type="button"
              onClick={reset}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-full border border-slate-200 bg-white/80 text-xs font-semibold text-[#475569] hover:text-[#0B0F19]"
            >
              <RefreshCw size={13} /> Re-analyze
            </button>
          </div>
        </div>

        <GlassCard className="p-6 sm:p-8 border-white/95 shadow-glass-lg space-y-6">
          <div className="flex justify-center">
            <CircularMeter value={result.interview_probability} />
          </div>

          {result.verdict && (
            <div className="rounded-xl border border-blue-200 bg-blue-50/80 p-4 text-center">
              <p className="text-xs sm:text-sm font-semibold italic text-[#0B0F19]">"{result.verdict}"</p>
            </div>
          )}

          <div className="grid gap-3 sm:grid-cols-3">
            <ScoreCard label="Skill Match" value={result.skill_match} icon={Target} color="#2563EB" barColor="bg-[#2563EB]" />
            <ScoreCard label="ATS Score" value={result.ats_score} icon={FileText} color="#0284C7" barColor="bg-[#0284C7]" />
            <ScoreCard label="Portfolio Score" value={result.portfolio_score} icon={Github} color="#16A34A" barColor="bg-[#16A34A]" />
          </div>
        </GlassCard>

        {result.biggest_weakness && (
          <GlassCard className="p-5 border-amber-200 bg-amber-50/60">
            <div className="flex items-start gap-3">
              <AlertTriangle size={18} className="mt-0.5 shrink-0 text-amber-600" />
              <div>
                <p className="text-xs font-bold text-amber-900 uppercase tracking-wider">Top Priority Weakness</p>
                <p className="mt-1 text-xs sm:text-sm text-[#0B0F19] leading-relaxed">{result.biggest_weakness}</p>
              </div>
            </div>
          </GlassCard>
        )}

        {result.green_flags?.length > 0 && (
          <GlassCard className="p-5 border-emerald-200 bg-emerald-50/50">
            <div className="flex items-start gap-3">
              <CheckCircle size={18} className="mt-0.5 shrink-0 text-[#16A34A]" />
              <div className="flex-1">
                <p className="text-xs font-bold text-emerald-900 uppercase tracking-wider">What's Working For You</p>
                <ul className="mt-2 space-y-1.5">
                  {result.green_flags.map((flag, index) => (
                    <li key={index} className="text-xs sm:text-sm text-[#0B0F19] flex items-start gap-2">
                      <span className="text-[#16A34A]">✓</span>
                      <span>{flag}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </GlassCard>
        )}

        {result.missing_skills?.length > 0 && (
          <Section icon={XCircle} title="Missing Skills" iconColor="#E11D48">
            <div className="flex flex-wrap gap-1.5">
              {result.missing_skills.map((skill, index) => (
                <span key={index} className="rounded-full border border-rose-200 bg-rose-50 px-3 py-1 text-xs font-semibold text-rose-800">
                  {skill}
                </span>
              ))}
            </div>
          </Section>
        )}

        {result.recommended_projects?.length > 0 && (
          <Section icon={Code2} title="Build These Projects" iconColor="#2563EB">
            <div className="grid gap-3 md:grid-cols-2">
              {result.recommended_projects.map((project, index) => (
                <div key={index} className="rounded-xl border border-slate-200/80 bg-white p-3.5 shadow-xs space-y-1.5">
                  <p className="text-xs sm:text-sm font-bold text-[#0B0F19]">{project.title}</p>
                  <p className="text-xs text-[#475569]">{project.description}</p>
                  {project.skills?.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1">
                      {project.skills.map((skill, sIdx) => (
                        <span key={sIdx} className="rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-[#475569]">
                          {skill}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Section>
        )}

        {showHistory && <HistoryModal onClose={() => setShowHistory(false)} />}
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 pb-16">
      <div className="text-center space-y-1.5">
        <Badge sparkle size="sm" className="mx-auto mb-1">Predictive AI</Badge>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0B0F19] tracking-tight flex items-center justify-center gap-2.5">
          <TrendingUp size={24} className="text-[#2563EB]" />
          <span>Interview Predictor</span>
        </h1>
        <p className="text-xs sm:text-sm text-[#64748B]">
          Find out exactly how likely you are to get an interview before you hit apply.
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs font-semibold text-[#E11D48]">
          {error}
        </div>
      )}

      <GlassCard className="p-6 sm:p-8 border-white/95 shadow-glass-lg space-y-5">
        <div
          onDrop={handleDrop}
          onDragOver={(event) => {
            event.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onClick={() => fileRef.current?.click()}
          className={`cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center transition-all ${
            dragging
              ? 'border-[#2563EB] bg-blue-50/50'
              : resumeFile
                ? 'border-emerald-300 bg-emerald-50/40'
                : 'border-slate-200 bg-white/50 hover:border-slate-300 hover:bg-white/80'
          }`}
        >
          <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={(event) => handleFile(event.target.files[0])} />
          {resumeFile ? (
            <div className="space-y-2">
              <CheckCircle size={30} className="mx-auto text-[#16A34A]" />
              <p className="text-sm font-bold text-[#0B0F19]">{resumeFile.name}</p>
              <p className="text-xs text-[#64748B]">{(resumeFile.size / 1024).toFixed(0)} KB - click to replace</p>
              {resumeText && <p className="text-xs text-[#16A34A] font-semibold">✓ Text ready</p>}
            </div>
          ) : (
            <div className="space-y-2">
              <div className="w-10 h-10 rounded-xl bg-blue-50 text-[#2563EB] flex items-center justify-center mx-auto mb-2 border border-blue-100">
                <Upload size={20} />
              </div>
              <p className="text-sm font-bold text-[#0B0F19]">Drop your resume PDF here</p>
              <p className="text-xs text-[#64748B]">or click to browse</p>
            </div>
          )}
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-[#0B0F19]">
            Target Job Description *
          </label>
          <textarea
            value={form.job_description}
            onChange={(event) => handle('job_description', event.target.value)}
            rows={5}
            placeholder="Paste the full job posting here..."
            className="w-full rounded-xl border border-slate-200 bg-white p-3.5 text-xs sm:text-sm text-[#0B0F19] shadow-xs focus:border-[#2563EB] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/20 resize-none"
          />
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-[#0B0F19]">
            GitHub Profile URL
          </label>
          <div className="relative">
            <input
              value={form.github_url}
              onChange={(event) => handle('github_url', event.target.value)}
              disabled={githubLocked}
              placeholder="https://github.com/your-username"
              className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-xs sm:text-sm text-[#0B0F19] shadow-xs focus:border-[#2563EB] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/20 disabled:bg-slate-50 disabled:text-[#64748B]"
            />
            {githubLocked && (
              <span className="absolute right-3 top-3 text-[#64748B]">
                <Lock size={14} />
              </span>
            )}
          </div>
        </div>

        <button
          type="button"
          onClick={handlePredict}
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 py-4 rounded-full bg-[#0B0F19] text-white font-bold text-sm hover:bg-[#1E293B] transition-all shadow-md disabled:opacity-50"
        >
          {loading ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              Calculating probability...
            </>
          ) : (
            <>
              <Sparkles size={18} />
              Predict Interview Odds
            </>
          )}
        </button>
      </GlassCard>

      {showHistory && <HistoryModal onClose={() => setShowHistory(false)} />}
    </div>
  )
}
