import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts'
import { api } from '../../services/api'
import toast from 'react-hot-toast'
import {
  ArrowLeft,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertCircle,
  TrendingUp,
  Briefcase,
  Sparkles,
  Target,
  ArrowRight,
  ShieldCheck,
  BookOpen,
} from 'lucide-react'
import { GlassCard, Button, Badge, ScoreRing } from '../../components/ui'
import { Mascot } from '../../mascot/Mascot'

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
      .then((r) => {
        setAnalysis(r.analysis)
        setLoading(false)
      })
      .catch((err) => {
        setLoading(false)
        toast.error(err?.message || 'Failed to load analysis.')
      })
  }, [id])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] gap-4">
        <Mascot size={140} showPodium={false} state="thinking" />
        <p className="text-xs font-semibold text-[#64748B]">Loading your analysis results...</p>
      </div>
    )
  }

  if (!analysis) {
    return (
      <div className="text-center py-16 space-y-4 max-w-md mx-auto">
        <Mascot size={120} showPodium={false} state="error" />
        <h2 className="text-lg font-bold text-[#0B0F19]">Analysis not found</h2>
        <p className="text-xs text-[#64748B]">We couldn't retrieve this analysis record.</p>
        <Link
          to="/dashboard/resume?new=1"
          onClick={() => localStorage.removeItem(LAST_RESUME_ANALYSIS_KEY)}
        >
          <Button variant="primary" size="md">
            Start New Analysis
          </Button>
        </Link>
      </div>
    )
  }

  const r = analysis.results_json || {}
  const missingSkillsData = (r.missing_skills || [])
    .slice(0, 6)
    .map((s) => ({ skill: s, gap: Math.floor(Math.random() * 40) + 40 }))

  const scoreVal = typeof r.score === 'number' ? r.score : 75
  const atsScore = r.ats_score != null ? r.ats_score : 'Not available for this resume'
  const skillMatch = r.skill_match_percentage != null ? `${r.skill_match_percentage}%` : 'Not available for this resume'

  return (
    <div className="w-full max-w-5xl mx-auto space-y-8 pb-16">
      {/* Top Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/dashboard/resume"
            className="w-9 h-9 rounded-xl bg-white border border-slate-200 text-[#475569] flex items-center justify-center hover:bg-slate-50 transition-colors shadow-sm"
          >
            <ArrowLeft size={16} />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <Badge sparkle size="sm">
                Result Overview
              </Badge>
              <span className="text-xs text-[#94A3B8]">
                {analysis.job_role || 'Target Role'} · {new Date(analysis.created_at).toLocaleDateString()}
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0B0F19] tracking-tight mt-0.5">
              Diagnostic Report
            </h1>
          </div>
        </div>

        <Link
          to="/dashboard/resume?new=1"
          onClick={() => localStorage.removeItem(LAST_RESUME_ANALYSIS_KEY)}
        >
          <Button variant="secondary" size="sm">
            Re-Analyze
          </Button>
        </Link>
      </div>

      {/* Hero Score + Summary Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Main Score Ring Card */}
        <GlassCard className="lg:col-span-5 p-6 sm:p-8 flex flex-col items-center justify-center text-center space-y-5 border-white/95 shadow-glass-lg">
          <p className="text-xs font-bold text-[#64748B] uppercase tracking-wider">
            Overall Resume Score
          </p>

          <ScoreRing score={scoreVal} max={100} size={150} strokeWidth={11} color="#2563EB" />

          <div className="flex items-center gap-2">
            {r.grade && (
              <span className="px-3 py-1 rounded-full bg-blue-50 text-[#2563EB] text-xs font-bold border border-blue-100">
                Grade: {r.grade}
              </span>
            )}
            {r.job_readiness && (
              <span
                className={`px-3 py-1 rounded-full text-xs font-bold border capitalize ${
                  r.job_readiness === 'ready'
                    ? 'bg-emerald-50 text-[#16A34A] border-emerald-200'
                    : 'bg-amber-50 text-[#D97706] border-amber-200'
                }`}
              >
                {r.job_readiness}
              </span>
            )}
          </div>
        </GlassCard>

        {/* Summary & Metrics */}
        <GlassCard className="lg:col-span-7 p-6 sm:p-8 flex flex-col justify-between space-y-6 border-white/95 shadow-glass-lg">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Sparkles size={16} className="text-[#2563EB]" />
              <h2 className="text-base font-bold text-[#0B0F19]">Executive Summary</h2>
            </div>
            <p className="text-xs sm:text-sm text-[#475569] leading-relaxed">
              {r.summary || 'Your resume has been parsed and evaluated across multiple ATS and role-matching criteria.'}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4 pt-4 border-t border-slate-100">
            <div className="p-4 rounded-xl bg-slate-50/70 border border-slate-100">
              <p className="text-[11px] font-medium text-[#64748B] uppercase tracking-wider">
                ATS Score
              </p>
              <p className="text-2xl font-extrabold text-[#0B0F19] mt-1">
                {atsScore}
              </p>
            </div>
            <div className="p-4 rounded-xl bg-slate-50/70 border border-slate-100">
              <p className="text-[11px] font-medium text-[#64748B] uppercase tracking-wider">
                Skill Match
              </p>
              <p className="text-2xl font-extrabold text-[#2563EB] mt-1">
                {skillMatch}
              </p>
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Strengths & Improvements */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Strengths */}
        <GlassCard className="p-6 space-y-4">
          <div className="flex items-center gap-2 text-[#16A34A]">
            <CheckCircle2 size={18} />
            <h2 className="text-sm font-bold text-[#0B0F19]">Key Strengths</h2>
          </div>
          {Array.isArray(r.strengths) && r.strengths.length > 0 ? (
            <ul className="space-y-2.5">
              {r.strengths.map((s, i) => (
                <li key={i} className="flex items-start gap-2.5 text-xs text-[#475569]">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#16A34A] mt-1.5 shrink-0" />
                  <span className="leading-relaxed">{s}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-[#94A3B8]">Not available for this resume</p>
          )}
        </GlassCard>

        {/* Weaknesses / Improvements */}
        <GlassCard className="p-6 space-y-4">
          <div className="flex items-center gap-2 text-[#E11D48]">
            <XCircle size={18} />
            <h2 className="text-sm font-bold text-[#0B0F19]">Suggested Improvements</h2>
          </div>
          {Array.isArray(r.weaknesses) && r.weaknesses.length > 0 ? (
            <ul className="space-y-2.5">
              {r.weaknesses.map((w, i) => (
                <li key={i} className="flex items-start gap-2.5 text-xs text-[#475569]">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#E11D48] mt-1.5 shrink-0" />
                  <span className="leading-relaxed">{w}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-[#94A3B8]">Not available for this resume</p>
          )}
        </GlassCard>
      </div>

      {/* Missing Skills Chart */}
      {missingSkillsData.length > 0 && (
        <GlassCard className="p-6 space-y-4">
          <div className="flex items-center gap-2">
            <AlertCircle size={18} className="text-[#EA580C]" />
            <h2 className="text-sm font-bold text-[#0B0F19]">Skill Gap Distribution</h2>
          </div>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={missingSkillsData} layout="vertical" margin={{ left: 10, right: 20 }}>
                <XAxis type="number" domain={[0, 100]} tick={{ fill: '#94A3B8', fontSize: 11 }} />
                <YAxis
                  type="category"
                  dataKey="skill"
                  tick={{ fill: '#0B0F19', fontSize: 11 }}
                  width={110}
                />
                <Tooltip
                  contentStyle={{
                    background: '#FFFFFF',
                    border: '1px solid #E2E8F0',
                    borderRadius: 12,
                    boxShadow: '0 8px 24px rgba(15,23,42,0.08)',
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="gap" fill="#2563EB" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      )}

      {/* Learning Roadmap */}
      {Array.isArray(r.learning_roadmap) && r.learning_roadmap.length > 0 && (
        <GlassCard className="p-6 space-y-6">
          <div className="flex items-center gap-2">
            <TrendingUp size={18} className="text-[#2563EB]" />
            <h2 className="text-sm font-bold text-[#0B0F19]">Tailored Learning Roadmap</h2>
          </div>

          <div className="space-y-4">
            {r.learning_roadmap.map((step, i) => (
              <div
                key={i}
                className="p-4 rounded-xl bg-slate-50/70 border border-slate-200/80 flex flex-col md:flex-row md:items-start justify-between gap-4"
              >
                <div className="space-y-1 max-w-xl">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-bold text-[#2563EB] bg-blue-50 px-2 py-0.5 rounded-full border border-blue-100">
                      Week {step.week}
                    </span>
                    <h3 className="text-xs font-bold text-[#0B0F19]">{step.focus}</h3>
                  </div>
                  <p className="text-xs text-[#64748B]">{step.goal}</p>
                </div>

                {(() => {
                  const normalized = Array.isArray(step.resources)
                    ? step.resources.map(normalizeResource).filter(Boolean)
                    : []
                  const resources =
                    normalized.length > 0
                      ? normalized.slice(0, 2)
                      : fallbackResourcesForStep(step, r.missing_skills).slice(0, 2)

                  return (
                    <div className="shrink-0 space-y-1">
                      <p className="text-[10px] uppercase font-bold tracking-wider text-[#94A3B8]">
                        Recommended Resource
                      </p>
                      {resources.map((item, idx) => (
                        <div key={idx}>
                          {item.url ? (
                            <a
                              href={item.url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-xs font-semibold text-[#2563EB] hover:underline flex items-center gap-1"
                            >
                              <span>{item.title}</span>
                              <ArrowRight size={11} />
                            </a>
                          ) : (
                            <span className="text-xs text-[#475569]">{item.title}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  )
                })()}
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* Recommended Next Steps */}
      <GlassCard className="p-6 space-y-4">
        <h2 className="text-sm font-bold text-[#0B0F19]">Recommended Next Steps</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link to="/dashboard/optimizer">
            <div className="p-4 rounded-xl border border-slate-200/80 hover:border-blue-300 hover:bg-blue-50/30 transition-all h-full flex flex-col justify-between">
              <div>
                <div className="w-9 h-9 rounded-lg bg-blue-50 text-[#2563EB] flex items-center justify-center mb-2">
                  <Sparkles size={17} />
                </div>
                <h3 className="text-xs font-bold text-[#0B0F19]">Resume Optimizer</h3>
                <p className="text-[11px] text-[#64748B] mt-1">
                  Tailor resume bullets for an exact job description.
                </p>
              </div>
              <span className="text-[11px] font-bold text-[#2563EB] mt-3 inline-flex items-center gap-1">
                Launch <ArrowRight size={11} />
              </span>
            </div>
          </Link>

          <Link to="/dashboard/job-match">
            <div className="p-4 rounded-xl border border-slate-200/80 hover:border-blue-300 hover:bg-blue-50/30 transition-all h-full flex flex-col justify-between">
              <div>
                <div className="w-9 h-9 rounded-lg bg-indigo-50 text-[#4F46E5] flex items-center justify-center mb-2">
                  <Briefcase size={17} />
                </div>
                <h3 className="text-xs font-bold text-[#0B0F19]">Job Match</h3>
                <p className="text-[11px] text-[#64748B] mt-1">
                  Find roles tailored to your confirmed skillset.
                </p>
              </div>
              <span className="text-[11px] font-bold text-[#4F46E5] mt-3 inline-flex items-center gap-1">
                Launch <ArrowRight size={11} />
              </span>
            </div>
          </Link>

          <Link to="/dashboard/interview-predictor">
            <div className="p-4 rounded-xl border border-slate-200/80 hover:border-blue-300 hover:bg-blue-50/30 transition-all h-full flex flex-col justify-between">
              <div>
                <div className="w-9 h-9 rounded-lg bg-emerald-50 text-[#16A34A] flex items-center justify-center mb-2">
                  <Target size={17} />
                </div>
                <h3 className="text-xs font-bold text-[#0B0F19]">Interview Predictor</h3>
                <p className="text-[11px] text-[#64748B] mt-1">
                  Estimate interview callback odds with confidence.
                </p>
              </div>
              <span className="text-[11px] font-bold text-[#16A34A] mt-3 inline-flex items-center gap-1">
                Launch <ArrowRight size={11} />
              </span>
            </div>
          </Link>
        </div>
      </GlassCard>
    </div>
  )
}
