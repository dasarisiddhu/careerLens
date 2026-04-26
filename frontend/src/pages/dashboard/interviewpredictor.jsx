import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '../../services/api'
import { useAuth } from '../../context/AuthContext'
import {
  Loader2,
  Upload,
  Github,
  FileText,
  Target,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Zap,
  ChevronRight,
  Code2,
  BookOpen,
  RefreshCw,
  History,
  X,
} from 'lucide-react'

const GITHUB_LOCK_KEY = 'careerlens:locked_github_url'

const normalizeGithubUrl = (rawUrl = '') => {
  const url = String(rawUrl || '').trim()
  if (!url) return ''
  const match = url.match(/github\.com\/([^/?#]+)/i)
  return match ? `https://github.com/${match[1]}` : url
}

const resolveGithubFromAuthUser = (authUser) => {
  if (!authUser) return ''

  const providers = new Set()
  const identities = Array.isArray(authUser.identities) ? authUser.identities : []
  for (const identity of identities) {
    const provider = identity?.provider || identity?.identity_data?.provider
    if (provider) providers.add(String(provider).toLowerCase())
  }

  const metaProvider = authUser?.app_metadata?.provider
  if (metaProvider) providers.add(String(metaProvider).toLowerCase())
  const metaProviders = Array.isArray(authUser?.app_metadata?.providers) ? authUser.app_metadata.providers : []
  for (const provider of metaProviders) {
    if (provider) providers.add(String(provider).toLowerCase())
  }

  const userMeta = authUser?.user_metadata || {}
  const identityMeta = identities.find((identity) => (identity?.provider || '').toLowerCase() === 'github')?.identity_data || {}
  const githubUsername = (
    userMeta.user_name ||
    userMeta.preferred_username ||
    userMeta.username ||
    userMeta.login ||
    identityMeta.user_name ||
    identityMeta.preferred_username ||
    identityMeta.username ||
    identityMeta.login ||
    ''
  ).trim()

  if (githubUsername) return `https://github.com/${githubUsername}`
  return providers.has('github') ? normalizeGithubUrl(userMeta.profile || userMeta.url || '') : ''
}

function CircularMeter({ value }) {
  const [current, setCurrent] = useState(0)
  const size = 220
  const radius = 88
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (current / 100) * circumference
  const color = value >= 70 ? '#10b981' : value >= 50 ? '#fb7185' : '#FF3B3B'
  const badgeClass = value >= 70 ? 'badge badge-green' : value >= 50 ? 'badge badge-red' : 'badge badge-red'
  const badgeText = value >= 70 ? 'Strong Candidate' : value >= 50 ? 'Competitive' : 'Needs Work'

  useEffect(() => {
    let frame
    let start = 0
    const step = value / 80

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
        {[1, 2, 3].map((ring) => (
          <div
            key={ring}
            aria-hidden
            className="absolute rounded-full border"
            style={{
              inset: `${ring * 10}px`,
              borderColor: `${color}${ring === 1 ? '26' : ring === 2 ? '18' : '10'}`,
            }}
          />
        ))}
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
          <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={14} />
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={14}
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.6, ease: 'easeOut' }}
            style={{ filter: `drop-shadow(0 0 12px ${color}55)` }}
          />
        </svg>

        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-[54px] font-black leading-none text-white">{current}%</span>
          <span className="mt-2 text-xs uppercase tracking-[0.18em] text-[#8A8FA8]">Interview Probability</span>
        </div>
      </div>
      <div className={badgeClass}>{badgeText}</div>
    </div>
  )
}

function ScoreCard({ label, value, icon: Icon, color, barClass }) {
  return (
    <motion.div
      whileHover={{ y: -3, scale: 1.01 }}
      className="glass-glow rounded-3xl p-5"
      style={{ borderTop: `2px solid ${color}` }}
    >
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon size={16} style={{ color }} />
          <span className="text-sm font-semibold text-white">{label}</span>
        </div>
        <span className="text-2xl font-black text-white">{value}%</span>
      </div>
      <div className="relative h-2 overflow-hidden rounded-full bg-white/5">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 1.1, ease: 'easeOut', delay: 0.2 }}
          className={`h-full rounded-full ${barClass}`}
        />
        <div className="shimmer absolute inset-0 opacity-30" />
      </div>
    </motion.div>
  )
}

function Section({ icon: Icon, title, iconColor, children }) {
  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="glass-glow rounded-3xl overflow-hidden">
      <div className="flex items-center gap-2 border-b border-white/5 px-5 py-4">
        <Icon size={16} style={{ color: iconColor }} />
        <h3 className="text-sm font-bold text-white">{title}</h3>
      </div>
      <div className="p-5">{children}</div>
    </motion.div>
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
  const valueColor = (value) => (value >= 70 ? 'text-green-400' : value >= 50 ? 'text-rose-400' : 'text-[#FF7070]')

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-[14px]"
      onClick={(event) => event.target === event.currentTarget && onClose()}
    >
      <motion.div initial={{ scale: 0.96, y: 20 }} animate={{ scale: 1, y: 0 }} className="glass-glow w-full max-w-xl rounded-3xl p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-xl font-bold text-white">
            <History size={18} className="text-[#FF7070]" />
            Past Predictions
          </h2>
          <button onClick={onClose} className="rounded-xl p-2 text-[#8A8FA8] transition hover:bg-white/5 hover:text-white">
            <X size={17} />
          </button>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 size={24} className="animate-spin text-[#FF7070]" />
          </div>
        ) : history.length === 0 ? (
          <p className="py-10 text-center text-sm text-[#8A8FA8]">No predictions yet.</p>
        ) : (
          <div className="max-h-96 space-y-3 overflow-y-auto pr-1">
            {history.map((item, index) => (
              <div key={index} className="glass rounded-2xl p-4">
                <div className="mb-2 flex items-center justify-between">
                  <span className={`text-2xl font-black ${valueColor(item.interview_probability)}`}>{item.interview_probability}%</span>
                  <span className="text-xs text-[#8A8FA8]">{formatDate(item.created_at)}</span>
                </div>
                <p className="line-clamp-2 text-xs leading-6 text-[#8A8FA8]">{item.job_description}</p>
                <div className="mt-3 flex gap-3 text-xs text-[#8A8FA8]">
                  <span>Skill: {item.skill_match}%</span>
                  <span>ATS: {item.ats_score}%</span>
                  <span>Portfolio: {item.portfolio_score}%</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </motion.div>
    </motion.div>
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
    if (!file || file.type !== 'application/pdf') {
      setError('Please upload a PDF file.')
      return
    }
    setResumeFile(file)
    setError('')
    const reader = new FileReader()
    reader.onload = async (e) => {
      const base64 = e.target?.result?.split(',')[1]
      if (!base64) {
        setResumeText(`Resume: ${file.name}`)
        return
      }
      try {
        const res = await api.extractResumeText({ pdf_base64: base64 })
        setResumeText(res.text || '')
      } catch {
        setResumeText(`Resume: ${file.name}`)
      }
    }
    reader.readAsDataURL(file)
  }

  const handleDrop = (event) => {
    event.preventDefault()
    setDragging(false)
    const file = event.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  const handleAnalyze = async () => {
    if (!resumeText) {
      setError('Please upload your resume PDF.')
      return
    }
    if (!form.job_description.trim()) {
      setError('Please paste the job description.')
      return
    }
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const normalizedGithub = normalizeGithubUrl(form.github_url)
      const res = await api.predictInterviewProbability({
        resume_text: resumeText,
        github_url: normalizedGithub,
        linkedin_url: form.linkedin_url || '',
        job_description: form.job_description,
      })
      setResult(res)
      if (normalizedGithub) {
        localStorage.setItem(GITHUB_LOCK_KEY, normalizedGithub)
        setGithubLocked(true)
        setForm((current) => ({ ...current, github_url: normalizedGithub }))
      }
      try {
        const meResponse = await api.getMe()
        const githubFromOAuth = meResponse?.user?.github_username ? `https://github.com/${meResponse.user.github_username}` : ''
        const savedGithub = normalizeGithubUrl(meResponse?.user?.github_url || githubFromOAuth || '')
        if (savedGithub) {
          localStorage.setItem(GITHUB_LOCK_KEY, savedGithub)
          setGithubLocked(true)
          setForm((current) => ({ ...current, github_url: savedGithub }))
        }
      } catch {}
    } catch (requestError) {
      setError(requestError.message || 'Analysis failed. Please try again.')
    }
    setLoading(false)
  }

  const reset = () => {
    setResult(null)
    setResumeFile(null)
    setResumeText('')
    setForm((current) => ({
      github_url: githubLocked ? current.github_url : '',
      job_description: '',
    }))
  }

  if (result) {
    return (
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}>
        <div className="mx-auto max-w-4xl space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 className="gradient-text text-3xl font-black">Interview Readiness</h1>
              <p className="mt-2 text-sm text-[#8A8FA8]">Brutally honest analysis of your current interview odds.</p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => setShowHistory(true)} className="btn-ghost">
                <History size={14} />
                History
              </button>
              <button onClick={reset} className="btn-ghost">
                <RefreshCw size={14} />
                Re-analyze
              </button>
            </div>
          </div>

          <div className="glass-glow rounded-[30px] p-8">
            <div className="mb-8 flex justify-center">
              <CircularMeter value={result.interview_probability} />
            </div>

            {result.verdict && (
              <div className="glass-glow mb-6 rounded-2xl border-l-[3px] border-l-[#FF3B3B] p-4">
                <p className="text-sm font-medium italic leading-7 text-[#F5F5F7]">"{result.verdict}"</p>
              </div>
            )}

            <div className="grid gap-4 md:grid-cols-3">
              <ScoreCard label="Skill Match" value={result.skill_match} icon={Target} color="#FF3B3B" barClass="bg-[#FF3B3B]" />
              <ScoreCard label="ATS Score" value={result.ats_score} icon={FileText} color="#e11d48" barClass="bg-[#e11d48]" />
              <ScoreCard label="Portfolio Score" value={result.portfolio_score} icon={Github} color="#10b981" barClass="bg-[#10b981]" />
            </div>
          </div>

          {result.biggest_weakness && (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="rounded-2xl border border-red-500/20 bg-red-500/8 p-5">
              <div className="flex items-start gap-3">
                <AlertTriangle size={17} className="mt-0.5 shrink-0 text-[#FF7070]" />
                <div>
                  <p className="text-sm font-bold text-[#FF7070]">Biggest Weakness</p>
                  <p className="mt-1 text-sm leading-7 text-[#F5F5F7]">{result.biggest_weakness}</p>
                </div>
              </div>
            </motion.div>
          )}

          {result.green_flags?.length > 0 && (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="rounded-2xl border border-green-500/20 bg-green-500/8 p-5">
              <div className="flex items-start gap-3">
                <CheckCircle size={17} className="mt-0.5 shrink-0 text-green-400" />
                <div>
                  <p className="text-sm font-bold text-green-300">What&apos;s Working For You</p>
                  <ul className="mt-2 space-y-2">
                    {result.green_flags.map((flag, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm text-[#F5F5F7]">
                        <span className="mt-0.5 text-green-400">â€¢</span>
                        {flag}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </motion.div>
          )}

          {result.missing_skills?.length > 0 && (
            <Section icon={XCircle} title="Missing Skills" iconColor="#FF3B3B">
              <div className="flex flex-wrap gap-2">
                {result.missing_skills.map((skill, index) => (
                  <span key={index} className="badge badge-red">
                    {skill}
                  </span>
                ))}
              </div>
            </Section>
          )}

          {result.recommended_projects?.length > 0 && (
            <Section icon={Code2} title="Build These Projects" iconColor="#e11d48">
              <div className="space-y-3">
                {result.recommended_projects.map((project, index) => (
                  <div key={index} className="glass rounded-2xl p-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <p className="text-sm font-semibold text-white">{project.title}</p>
                      {project.estimated_time && (
                        <span className="badge badge-red">
                          <Clock size={11} />
                          {project.estimated_time}
                        </span>
                      )}
                    </div>
                    {project.why && <p className="mt-2 text-xs leading-6 text-[#8A8FA8]">{project.why}</p>}
                  </div>
                ))}
              </div>
            </Section>
          )}

          {result.resume_improvements?.length > 0 && (
            <Section icon={FileText} title="Resume Improvements" iconColor="#FF3B3B">
              <ul className="space-y-3">
                {result.resume_improvements.map((tip, index) => (
                  <li key={index} className="flex items-start gap-3 text-sm text-[#F5F5F7]">
                    <ChevronRight size={14} className="mt-0.5 shrink-0 text-[#FF7070]" />
                    {tip}
                  </li>
                ))}
              </ul>
            </Section>
          )}

          {result.interview_prep_tips?.length > 0 && (
            <Section icon={BookOpen} title="Interview Prep Tips" iconColor="#10b981">
              <ul className="space-y-3">
                {result.interview_prep_tips.map((tip, index) => (
                  <li key={index} className="flex items-start gap-3 text-sm text-[#F5F5F7]">
                    <ChevronRight size={14} className="mt-0.5 shrink-0 text-green-400" />
                    {tip}
                  </li>
                ))}
              </ul>
            </Section>
          )}

          {result.realistic_timeline && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-glow rounded-2xl border-l-[3px] border-l-[#FF3B3B] p-5"
            >
              <div className="flex items-center gap-4">
                <Clock size={22} className="shrink-0 text-[#FF7070]" />
                <div>
                  <p className="text-sm font-bold text-white">Realistic Timeline to Be Job-Ready</p>
                  <p className="mt-1 text-sm text-[#8A8FA8]">{result.realistic_timeline}</p>
                </div>
              </div>
            </motion.div>
          )}

          <AnimatePresence>{showHistory && <HistoryModal onClose={() => setShowHistory(false)} />}</AnimatePresence>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}>
      <div className="mx-auto max-w-3xl space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="gradient-text text-3xl font-black">Interview Predictor</h1>
            <p className="mt-2 text-sm text-[#8A8FA8]">Find out exactly how likely you are to get an interview.</p>
          </div>
          <button onClick={() => setShowHistory(true)} className="btn-ghost">
            <History size={14} />
            History
          </button>
        </div>

        {error && <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300">{error}</div>}

        <div className="glass-glow rounded-[30px] p-6">
          <div
            onDrop={handleDrop}
            onDragOver={(event) => {
              event.preventDefault()
              setDragging(true)
            }}
            onDragLeave={() => setDragging(false)}
            onClick={() => fileRef.current?.click()}
            className={`cursor-pointer rounded-[24px] border-2 border-dashed p-10 text-center transition ${
              dragging
                ? 'border-[#FF3B3B] bg-[rgba(255,59,59,0.06)] shadow-[0_0_30px_rgba(255,59,59,0.1)]'
                : resumeFile
                  ? 'border-green-500/40 bg-green-500/5'
                  : 'border-[rgba(255,255,255,0.1)] bg-[rgba(255,255,255,0.02)] hover:border-[rgba(255,59,59,0.25)] hover:bg-[rgba(255,59,59,0.04)]'
            }`}
          >
            <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={(event) => handleFile(event.target.files[0])} />
            {resumeFile ? (
              <div className="space-y-2">
                <CheckCircle size={30} className="mx-auto text-green-400" />
                <p className="text-sm font-semibold text-white">{resumeFile.name}</p>
                <p className="text-xs text-[#8A8FA8]">{(resumeFile.size / 1024).toFixed(0)} KB - click to replace</p>
                {resumeText && <p className="text-xs text-green-300">Text extracted</p>}
              </div>
            ) : (
              <div className="space-y-3">
                <Upload size={32} className="float mx-auto text-[#FF7070]" />
                <p className="text-base font-semibold text-white">Drop your resume PDF here</p>
                <p className="text-sm text-[#8A8FA8]">or click to browse</p>
              </div>
            )}
          </div>

          <div className="mt-5">
            <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-[#8A8FA8]">
              GitHub URL (optional but strongly recommended)
            </label>
            <input
              value={form.github_url}
              onChange={(event) => handle('github_url', event.target.value)}
              placeholder="https://github.com/yourname"
              disabled={githubLocked}
              className={`input-field ${githubLocked ? 'cursor-not-allowed opacity-70' : ''}`}
            />
            <p className="mt-2 text-xs text-[#8A8FA8]">
              {githubLocked ? 'GitHub URL is locked to your account profile for consistency.' : 'No GitHub means a weaker portfolio signal.'}
            </p>
          </div>

          <div className="mt-5">
            <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-[#8A8FA8]">Job Description</label>
            <textarea
              value={form.job_description}
              onChange={(event) => handle('job_description', event.target.value)}
              placeholder="Paste the complete job description here. The more detail, the more accurate the analysis."
              rows={7}
              className="input-field resize-none"
            />
            <p className="mt-2 text-right text-xs text-[#8A8FA8]">{form.job_description.length} chars</p>
          </div>

          <button onClick={handleAnalyze} disabled={loading || !resumeFile || !form.job_description.trim()} className="btn-primary mt-6 w-full py-4 text-base font-bold">
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Zap size={18} />
                Predict My Interview Chances
              </>
            )}
          </button>
          <p className="mt-3 text-center text-xs text-[#8A8FA8]">Real, honest score - not inflated to make you feel good.</p>
        </div>

        <AnimatePresence>{showHistory && <HistoryModal onClose={() => setShowHistory(false)} />}</AnimatePresence>
      </div>
    </motion.div>
  )
}
