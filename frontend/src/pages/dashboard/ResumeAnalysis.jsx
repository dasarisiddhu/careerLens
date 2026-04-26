import { useState, useCallback, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { motion } from 'framer-motion'
import { pageTransition } from '../../utils/animations'
import { api } from '../../services/api'
import { useAuth } from '../../context/AuthContext'
import toast from 'react-hot-toast'
import { Upload, Github, Briefcase, Loader2, FileText, CheckCircle, History, ArrowRight } from 'lucide-react'

const LAST_RESUME_ANALYSIS_KEY = 'careerlens:last_resume_analysis_id'
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

export default function ResumeAnalysis() {
  const { user: authUser } = useAuth()
  const [file, setFile] = useState(null)
  const [form, setForm] = useState({ github_url: '', job_role: '' })
  const [githubLocked, setGithubLocked] = useState(false)
  const [loading, setLoading] = useState(false)
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

  const onDrop = useCallback((accepted) => {
    if (accepted[0]) setFile(accepted[0])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
  })

  const handle = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }))

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

  const dropzoneClass = file
    ? 'border-[rgba(255,59,59,0.4)] bg-[rgba(255,59,59,0.05)]'
    : isDragActive
      ? 'border-[#FF3B3B] bg-[rgba(255,59,59,0.06)] shadow-[0_0_30px_rgba(255,59,59,0.1)]'
      : 'border-[rgba(255,255,255,0.1)] bg-[rgba(255,255,255,0.02)] hover:border-[rgba(255,59,59,0.28)] hover:bg-[rgba(255,59,59,0.04)]'

  return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
      <div className="mx-auto max-w-3xl space-y-6">
        <div>
          <h1 className="gradient-text mb-2 text-3xl font-black">Resume Analysis</h1>
          <p className="text-[#8A8FA8]">Get AI-powered insight on your resume, GitHub profile, and target role fit.</p>
        </div>

        {error && <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div
            {...getRootProps()}
            className={`glass-glow cursor-pointer rounded-[24px] border-2 border-dashed p-10 text-center transition-all ${dropzoneClass}`}
          >
            <input {...getInputProps()} />
            {file ? (
              <div className="flex flex-col items-center gap-3">
                <motion.div initial={{ scale: 0.7, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: 'spring', stiffness: 220, damping: 16 }}>
                  <CheckCircle size={36} className="text-green-400" />
                </motion.div>
                <p className="text-base font-semibold text-white">{file.name}</p>
                <p className="text-sm text-[#8A8FA8]">{(file.size / 1024).toFixed(0)} KB - click to replace</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <Upload size={34} className="float text-[#FF7070]" />
                <p className="text-base font-semibold text-white">Drop your resume PDF here</p>
                <p className="text-sm text-[#8A8FA8]">or click to browse · Max 5MB</p>
              </div>
            )}
          </div>

          {loading && (
            <div className="h-2 overflow-hidden rounded-full bg-white/10">
              <div className="shimmer h-full bg-[rgba(255,59,59,0.45)]" />
            </div>
          )}

          {[
            { key: 'github_url', label: 'GitHub Profile URL', icon: Github, placeholder: 'https://github.com/username', type: 'url' },
            { key: 'job_role', label: 'Desired Job Role', icon: Briefcase, placeholder: 'e.g. Full Stack Engineer, ML Engineer', type: 'text' },
          ].map(({ key, label, icon: Icon, placeholder, type }) => (
            <div key={key} className="glass-glow p-4">
              <label className="mb-2 flex items-center gap-2 text-sm font-semibold text-white">
                <Icon size={14} className="text-[#FF7070]" />
                {label}
              </label>
              <input
                type={type}
                required
                value={form[key]}
                onChange={handle(key)}
                placeholder={placeholder}
                disabled={key === 'github_url' && githubLocked}
                className={`input-field ${key === 'github_url' && githubLocked ? 'cursor-not-allowed opacity-70' : ''}`}
              />
              {key === 'github_url' && githubLocked && (
                <p className="mt-2 text-xs text-[#8A8FA8]">GitHub URL is locked to your linked profile for this account.</p>
              )}
            </div>
          ))}

          <button type="submit" disabled={loading} className="btn-primary w-full py-4 text-base font-bold">
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Analyzing with AI... this may take 30s
              </>
            ) : (
              <>
                <FileText size={18} />
                Analyze My Resume
              </>
            )}
          </button>
        </form>

        <button onClick={() => navigate('/dashboard/resume/history')} className="btn-ghost w-full">
          <History size={16} />
          View Past Analyses
          <ArrowRight size={14} />
        </button>
      </div>
    </motion.div>
  )
}
