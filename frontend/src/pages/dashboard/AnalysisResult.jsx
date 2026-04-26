// frontend/src/pages/dashboard/AnalysisResult.jsx
import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAnimatedCircle, useCountUp, pageTransition } from '../../utils/animations'
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts'
import { api } from '../../services/api'
import toast from 'react-hot-toast'
import { ArrowLeft, Loader2, CheckCircle, XCircle, AlertCircle, TrendingUp, Briefcase, Sparkles, Target } from 'lucide-react'

const LAST_RESUME_ANALYSIS_KEY = 'careerlens:last_resume_analysis_id'

const FALLBACK_RESOURCES = {
  ml: [
    { title: 'Google ML Crash Course', url: 'https://developers.google.com/machine-learning/crash-course' },
    { title: 'Machine Learning Specialization', url: 'https://www.coursera.org/specializations/machine-learning-introduction/' },
  ],
  deep: [
    { title: 'TensorFlow Tutorials', url: 'https://www.tensorflow.org/tutorials' },
    { title: 'PyTorch Tutorials', url: 'https://docs.pytorch.org/tutorials/' },
  ],
  nlp: [
    { title: 'Hugging Face NLP Course', url: 'https://huggingface.co/learn/nlp-course' },
    { title: 'scikit-learn Text Tutorial', url: 'https://scikit-learn.org/1.3/tutorial/text_analytics/working_with_text_data.html' },
  ],
  deploy: [
    { title: 'Made With ML MLOps', url: 'https://madewithml.com/courses/mlops/' },
    { title: 'Full Stack Deep Learning', url: 'https://fullstackdeeplearning.com/course/' },
  ],
}

function AnimatedScoreCircle({ score, maxScore = 100, size = 140, color = '#f59e0b', label }) {
  const { radius, circumference, offset, strokeWidth } = useAnimatedCircle(score, maxScore, size, 8)
  const count = useCountUp(score, 1400)

  const strokeColor = score >= 70 ? '#10b981' : score >= 40 ? '#f59e0b' : '#ef4444'

  return (
    <div style={{ position: 'relative', width: size, height: size, flexShrink: 0 }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <defs>
          <filter id={`glow-${score}`}>
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>
        <circle
          cx={size/2} cy={size/2} r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size/2} cy={size/2} r={radius}
          fill="none"
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          filter={`url(#glow-${score})`}
          style={{ transition: 'stroke-dashoffset 1.4s cubic-bezier(0.22, 1, 0.36, 1)' }}
        />
      </svg>
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{
          fontSize: size > 100 ? '28px' : '20px',
          fontWeight: 800, color: '#fafaf9',
          letterSpacing: '-1px', lineHeight: 1,
        }}>
          {count}
        </span>
        {label && (
          <span style={{ fontSize: '10px', color: 'rgba(120,113,108,0.8)', marginTop: '2px' }}>
            {label}
          </span>
        )}
      </div>
    </div>
  )
}

function normalizeResource(resource) {
  if (!resource) return null

  if (typeof resource === 'string') {
    const match = resource.match(/https?:\/\/[^\s)>\],]+/)
    const url = match?.[0] || ''
    const title = url ? resource.replace(url, '').trim().replace(/^[-:]\s*/, '') : resource
    return { title: title || url || 'Learning Resource', url }
  }

  if (typeof resource === 'object') {
    const title = resource.title || resource.name || resource.resource || ''
    const url = resource.url || resource.link || ''
    return { title: title || url || 'Learning Resource', url: url || '' }
  }

  return null
}

function fallbackResourcesForStep(step, missingSkills = []) {
  const text = `${step?.focus || ''} ${(missingSkills || []).join(' ')}`.toLowerCase()
  if (/(nlp|natural language|llm|transformer|bert)/.test(text)) return FALLBACK_RESOURCES.nlp
  if (/(deep learning|neural|tensorflow|pytorch|keras|cnn|rnn)/.test(text)) return FALLBACK_RESOURCES.deep
  if (/(deploy|deployment|mlops|cloud|project|portfolio|production)/.test(text)) return FALLBACK_RESOURCES.deploy
  return FALLBACK_RESOURCES.ml
}

export default function AnalysisResult() {
  const { id } = useParams()
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (id) {
      localStorage.setItem(LAST_RESUME_ANALYSIS_KEY, id)
    }
    api.getAnalysis(id)
      .then(r => { setAnalysis(r.analysis); setLoading(false) })
      .catch((err) => {
        setLoading(false)
        toast.error(err?.message || 'Failed to load analysis.')
      })
  }, [id])

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <Loader2 size={32} className="animate-spin text-amber-400" />
    </div>
  )

  if (!analysis) return (
    <div className="text-center py-16">
      <p className="text-[#78716c]">Analysis not found.</p>
      <Link
        to="/dashboard/resume?new=1"
        onClick={() => localStorage.removeItem(LAST_RESUME_ANALYSIS_KEY)}
        className="btn-primary inline-block mt-4"
      >
        New Analysis
      </Link>
    </div>
  )

  const r = analysis.results_json || {}
  const missingSkillsData = (r.missing_skills || []).slice(0, 6).map(s => ({ skill: s, gap: Math.floor(Math.random() * 40) + 40 }))

  return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
      <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/dashboard/resume" className="text-[#78716c] hover:text-white">
          <ArrowLeft size={20} />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-white">Analysis Results</h1>
          <p className="text-[#78716c] text-sm">{analysis.job_role} · {new Date(analysis.created_at).toLocaleDateString()}</p>
        </div>
      </div>

      {/* Score + Summary */}
      <div className="grid md:grid-cols-2 gap-6">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}
          className="glass-glow p-6 rounded-2xl flex flex-col items-center gap-4 border-t-2 border-amber-500/40">
          <h2 className="text-lg font-bold text-white">Resume Score</h2>
          <AnimatedScoreCircle score={r.score || 0} size={160} />
          <div className="flex gap-3 text-sm">
            <span className="px-3 py-1 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">Grade: {r.grade}</span>
            <span className={`px-3 py-1 rounded-full border text-sm ${r.job_readiness === 'ready' ? 'bg-green-500/20 text-green-300 border-green-500/30' : 'bg-amber-500/20 text-amber-300 border-amber-500/30'}`}>
              {r.job_readiness}
            </span>
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
          className="glass-glow p-6 rounded-2xl border-t-2 border-amber-500/40">
          <h2 className="text-lg font-bold text-white mb-3">Summary</h2>
          <p className="text-[#d6d3d1] text-sm leading-relaxed">{r.summary}</p>
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="p-3 rounded-xl bg-white/5 border border-white/10">
              <p className="text-xs text-[#78716c]">ATS Score</p>
              <p className="text-2xl font-bold text-amber-400">{r.ats_score || 0}</p>
            </div>
            <div className="p-3 rounded-xl bg-white/5 border border-white/10">
              <p className="text-xs text-[#78716c]">Skill Match</p>
              <p className="text-2xl font-bold text-yellow-500">{r.skill_match_percentage || 0}%</p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Strengths & Weaknesses */}
      <div className="grid md:grid-cols-2 gap-6">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
          className="glass-glow p-6 rounded-2xl">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><CheckCircle size={18} className="text-green-400" /> Strengths</h2>
          <ul className="space-y-2">
            {(r.strengths || []).map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-[#d6d3d1]">
                <span className="text-green-400 mt-0.5 shrink-0">+</span> {s}
              </li>
            ))}
          </ul>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          className="glass-glow p-6 rounded-2xl">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><XCircle size={18} className="text-red-400" /> Weaknesses</h2>
          <ul className="space-y-2">
            {(r.weaknesses || []).map((w, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-[#d6d3d1]">
                <span className="text-red-400 mt-0.5 shrink-0">-</span> {w}
              </li>
            ))}
          </ul>
        </motion.div>
      </div>

      {/* Missing Skills Chart */}
      {missingSkillsData.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}
          className="glass-glow p-6 rounded-2xl">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><AlertCircle size={18} className="text-amber-400" /> Skill Gap Analysis</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={missingSkillsData} layout="vertical">
              <XAxis type="number" domain={[0, 100]} tick={{ fill: '#78716c', fontSize: 12 }} />
              <YAxis type="category" dataKey="skill" tick={{ fill: '#d6d3d1', fontSize: 12 }} width={120} />
              <Tooltip contentStyle={{ background: '#111010', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }} />
              <Bar dataKey="gap" fill="#f59e0b" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      )}

      {/* Learning Roadmap */}
      {r.learning_roadmap && (
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
          className="glass-glow p-6 rounded-2xl">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><TrendingUp size={18} className="text-amber-400" /> Learning Roadmap</h2>
          <div className="relative">
            <div className="absolute left-5 top-0 bottom-0 w-px bg-gradient-to-b from-red-500 to-transparent opacity-30" />
            <div className="space-y-4">
              {r.learning_roadmap.map((step, i) => (
                <div key={i} className="flex gap-4 pl-10 relative">
                  <div className="absolute left-3.5 top-2 w-3 h-3 rounded-full bg-red-500 border-2 border-[#0a0a0a]" />
                  <div className="glass-glow p-4 rounded-xl flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono text-amber-400">Week {step.week}</span>
                      <span className="text-xs text-[#44403c]">-</span>
                      <span className="text-sm font-semibold text-white">{step.focus}</span>
                    </div>
                    <p className="text-xs text-[#78716c]">{step.goal}</p>

                    {(() => {
                      const normalized = Array.isArray(step.resources)
                        ? step.resources.map(normalizeResource).filter(Boolean)
                        : []
                      const resources = normalized.length > 0
                        ? normalized.slice(0, 3)
                        : fallbackResourcesForStep(step, r.missing_skills).slice(0, 2)

                      return (
                        <div className="mt-3">
                          <p className="text-[11px] uppercase tracking-wide text-[#44403c] mb-1">Where to learn</p>
                          <ul className="space-y-1">
                            {resources.map((item, idx) => (
                              <li key={idx} className="text-xs text-[#d6d3d1]">
                                {item.url
                                  ? <a href={item.url} target="_blank" rel="noreferrer" className="text-amber-300 hover:text-amber-200 underline underline-offset-2">{item.title}</a>
                                  : <span>{item.title}</span>}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )
                    })()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {/* ATS Tips */}
      {r.ats_tips && (
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}
          className="glass-glow p-6 rounded-2xl">
          <h2 className="text-lg font-bold text-white mb-4">ATS Optimization Tips</h2>
          <ul className="space-y-2">
            {r.ats_tips.map((tip, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-[#d6d3d1]">
                <span className="text-amber-400 mt-0.5 shrink-0">?</span> {tip}
              </li>
            ))}
          </ul>
        </motion.div>
      )}

      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
        className="glass-glow p-6 rounded-2xl">
        <h2 className="text-lg font-bold text-white mb-4">Recommended Next Steps</h2>
        <div className="grid md:grid-cols-3 gap-3">
          {[
            {
              to: '/dashboard/resume-optimizer',
              title: 'Resume Optimizer',
              description: 'Rewrite your bullets for a target job description.',
              icon: Sparkles,
            },
            {
              to: '/dashboard/job-match',
              title: 'Job Match',
              description: 'See which roles are realistic with your current skills.',
              icon: Briefcase,
            },
            {
              to: '/dashboard/interview-predictor',
              title: 'Interview Predictor',
              description: 'Estimate your interview chances before you apply.',
              icon: Target,
            },
          ].map(({ to, title, description, icon: Icon }) => (
            <Link key={to} to={to} className="glass-glow p-4 rounded-2xl block hover:translate-y-[-2px] transition-transform">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mb-3 shadow-[0_0_12px_rgba(245,158,11,0.3)]">
                <Icon size={18} className="text-amber-400" />
              </div>
              <p className="text-white font-semibold">{title}</p>
              <p className="text-sm text-[#78716c] mt-1">{description}</p>
            </Link>
          ))}
        </div>
      </motion.div>

      <div className="pt-2">
        <Link
          to="/dashboard/resume?new=1"
          onClick={() => localStorage.removeItem(LAST_RESUME_ANALYSIS_KEY)}
          className="btn-primary inline-block"
        >
          New Analysis
        </Link>
      </div>
      </div>
    </motion.div>
  )
}









