import React, { useState, useCallback, useEffect } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '../../services/api'
import { useAuth } from '../../context/AuthContext'
import toast from 'react-hot-toast'
import {
  Upload,
  Github,
  Briefcase,
  Loader2,
  FileText,
  CheckCircle2,
  History,
  ArrowRight,
  AlertCircle,
  Sparkles,
} from 'lucide-react'
import { GlassCard, Button, Input, Badge } from '../../components/ui'

const LAST_RESUME_ANALYSIS_KEY = 'careerlens:last_resume_analysis_id'
const GITHUB_LOCK_KEY = 'careerlens:locked_github_url'

const STATUS_ROTATION = [
  'Reading your resume...',
  'Checking keywords and structure...',
  'Analyzing GitHub repositories & commits...',
  'Evaluating job role alignment...',
  'Preparing your personalized feedback...',
]

const normalizeGithubUrl = (rawUrl = '') => {
  const url = String(rawUrl || '').trim()
  if (!url) return ''
  const match = url.match(/github\.com\/([^/?#]+)/i)
  return match ? `https://github.com/${match[1]}` : url
}

const resolveGithubFromAuthUser = (authUser) => {
  if (!authUser) return ''
  const identities = Array.isArray(authUser.identities) ? authUser.identities : []
  const userMeta = authUser?.user_metadata || {}
  const identityMeta =
    identities.find((identity) => (identity?.provider || '').toLowerCase() === 'github')?.identity_data || {}
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
  return ''
}

export default function ResumeAnalysis() {
  const { user: authUser } = useAuth()
  const [file, setFile] = useState(null)
  const [form, setForm] = useState({ github_url: '', job_role: '' })
  const [githubLocked, setGithubLocked] = useState(false)
  const [loading, setLoading] = useState(false)
  const [statusIdx, setStatusIdx] = useState(0)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    const params = new URLSearchParams(location.search)
    if (params.get('new') === '1') {
      localStorage.removeItem(LAST_RESUME_ANALYSIS_KEY)
      return
    }

    const lastAnalysisId = localStorage.getItem(LAST_RESUME_ANALYSIS_KEY)
    if (lastAnalysisId) {
      navigate(`/dashboard/resume/${lastAnalysisId}`, { replace: true })
    }
  }, [location.search, navigate])

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

  // Rotate status message while analyzing
  useEffect(() => {
    if (!loading) return
    const interval = setInterval(() => {
      setStatusIdx((prev) => (prev + 1) % STATUS_ROTATION.length)
    }, 2800)
    return () => clearInterval(interval)
  }, [loading])

  const onDrop = useCallback((accepted) => {
    if (accepted[0]) setFile(accepted[0])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
  })

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!file) {
      setError('Please upload your resume PDF.')
      toast.error('Please upload your resume PDF.')
      return
    }

    setLoading(true)
    setError('')
    const toastId = toast.loading('Analyzing your resume...')

    try {
      const formData = new FormData()
      const normalizedGithub = normalizeGithubUrl(form.github_url)
      formData.append('resume', file)
      formData.append('github_url', normalizedGithub)
      formData.append('job_role', form.job_role)
      const response = await api.analyzeResume(formData)
      if (normalizedGithub) {
        localStorage.setItem(GITHUB_LOCK_KEY, normalizedGithub)
        setGithubLocked(true)
        setForm((current) => ({ ...current, github_url: normalizedGithub }))
      }
      localStorage.setItem(LAST_RESUME_ANALYSIS_KEY, response.analysis_id)
      toast.success('Resume analyzed successfully!', { id: toastId })
      navigate(`/dashboard/resume/${response.analysis_id}`)
    } catch (submitError) {
      const message = submitError.message || 'Upload failed. Please try again.'
      setError(message)
      toast.error(message, { id: toastId })
      setLoading(false)
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Badge sparkle size="sm" className="mb-2">
            AI Diagnosis
          </Badge>
          <h1 className="text-3xl font-extrabold text-[#0B0F19] tracking-tight">
            Resume Analysis
          </h1>
          <p className="text-xs text-[#64748B] mt-1 max-w-xl">
            Upload your resume PDF and optionally connect your GitHub profile to receive actionable diagnosis and role alignment.
          </p>
        </div>

        <Link to="/dashboard/optimizer">
          <Button variant="secondary" size="sm" trailingIcon={ArrowRight}>
            Try Resume Optimizer
          </Button>
        </Link>
      </div>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-xs text-[#E11D48] flex items-center gap-2.5"
          >
            <AlertCircle size={16} className="shrink-0" />
            <span>{error}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Upload Card */}
      <GlassCard className="p-8 sm:p-10 border-white/95 shadow-glass-lg">
        {loading ? (
          /* Analyzing State */
          <div className="py-12 flex flex-col items-center justify-center text-center space-y-6">
            <div className="w-16 h-16 rounded-full border-4 border-blue-100 border-t-[#2563EB] animate-spin mb-2" />

            <div className="space-y-2 max-w-md">
              <h3 className="text-lg font-bold text-[#0B0F19]">
                Analyzing your profile...
              </h3>
              <p
                role="status"
                aria-live="polite"
                className="text-xs font-semibold text-[#2563EB] h-5 transition-all"
              >
                {STATUS_ROTATION[statusIdx]}
              </p>
              <p className="text-[11px] text-[#94A3B8]">
                This thorough scan takes ~20–30 seconds.
              </p>
            </div>

            {/* Indeterminate Shimmer Progress Bar */}
            <div className="w-full max-w-xs h-2 rounded-full bg-slate-100 overflow-hidden relative">
              <motion.div
                animate={{ x: ['-100%', '200%'] }}
                transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
                className="w-1/2 h-full bg-[#2563EB] rounded-full"
              />
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* File Dropzone */}
            <div
              {...getRootProps()}
              className={`cursor-pointer rounded-2xl border-2 border-dashed p-8 sm:p-10 text-center transition-all ${
                file
                  ? 'border-[#2563EB] bg-blue-50/40'
                  : isDragActive
                  ? 'border-[#2563EB] bg-blue-50/60 scale-[1.01]'
                  : 'border-slate-200 bg-white/50 hover:border-slate-300 hover:bg-white/80'
              }`}
            >
              <input {...getInputProps()} />

              {file ? (
                <div className="flex flex-col items-center gap-2.5">
                  <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-[#16A34A] flex items-center justify-center border border-emerald-100">
                    <CheckCircle2 size={24} />
                  </div>
                  <p className="text-sm font-bold text-[#0B0F19]">{file.name}</p>
                  <p className="text-xs text-[#64748B]">
                    {(file.size / 1024).toFixed(0)} KB · Click or drag to replace
                  </p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2.5">
                  <div className="w-12 h-12 rounded-2xl bg-blue-50 text-[#2563EB] flex items-center justify-center border border-blue-100">
                    <Upload size={22} />
                  </div>
                  <p className="text-sm font-bold text-[#0B0F19]">
                    Drop your resume PDF here
                  </p>
                  <p className="text-xs text-[#64748B]">
                    Supported format: PDF · Max size: 5MB
                  </p>
                </div>
              )}
            </div>

            {/* Inputs Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="GitHub Profile URL (Optional)"
                type="url"
                value={form.github_url}
                onChange={(e) => setForm((c) => ({ ...c, github_url: e.target.value }))}
                placeholder="https://github.com/username"
                leadingIcon={Github}
                disabled={githubLocked}
                hint={githubLocked ? 'Locked to linked GitHub profile' : 'Used for repository analysis'}
              />

              <Input
                label="Desired Job Role"
                type="text"
                required
                value={form.job_role}
                onChange={(e) => setForm((c) => ({ ...c, job_role: e.target.value }))}
                placeholder="e.g. Frontend Engineer, ML Engineer"
                leadingIcon={Briefcase}
              />
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              variant="primary"
              size="lg"
              trailingIcon={FileText}
              className="w-full"
            >
              Analyze My Resume
            </Button>
          </form>
        )}
      </GlassCard>

      {/* History CTA */}
      <div className="text-center pt-2">
        <Link
          to="/dashboard/resume/history"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#64748B] hover:text-[#0B0F19] transition-colors"
        >
          <History size={14} />
          <span>View Past Analyses History</span>
        </Link>
      </div>
    </div>
  )
}
