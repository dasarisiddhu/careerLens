import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { pageTransition } from '../../utils/animations'
import { api } from '../../services/api'
import toast from 'react-hot-toast'
import {
  Globe, Loader2, Sparkles, AlertTriangle,
  Download, Copy, RotateCcw, CheckCircle, Upload, FileText
} from 'lucide-react'
import { GlassCard, Badge } from '../../components/ui'

const FREE_PORTFOLIO_LIMIT = 4

function extractGithubUsername(url) {
  if (!url) return ''
  const cleaned = url.trim().replace(/\/+$/, '')
  const parts = cleaned.split('/')
  const maybeUser = parts[parts.length - 1] || ''
  if (!maybeUser || maybeUser.includes('.') || maybeUser.toLowerCase() === 'github.com') return ''
  return maybeUser
}

export default function Portfolio() {
  const STORAGE_KEY = 'careerlens:portfolio:last'
  const [profile, setProfile] = useState(null)
  const [form, setForm] = useState({ name: '', github_username: '' })
  const [resumeFile, setResumeFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [html, setHtml] = useState('')
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    api.getMe()
      .then((res) => {
        const user = res.user || {}
        setProfile(user)
        setForm((prev) => ({
          ...prev,
          name: user.name || '',
          github_username: extractGithubUsername(user.github_url || ''),
        }))
      })
      .catch(() => {})

    try {
      const cached = localStorage.getItem(STORAGE_KEY)
      if (cached) {
        const parsed = JSON.parse(cached)
        if (parsed?.html) {
          setHtml(parsed.html)
          setForm((prev) => ({
            ...prev,
            name: parsed.name || prev.name,
            github_username: parsed.github_username || prev.github_username,
          }))
        }
      }
    } catch {
      /* ignore cache errors */
    }
  }, [])

  const usedCount = Number(profile?.portfolio_gen_count || 0)
  const isFreePlan = profile?.plan_type !== 'premium'
  const remaining = isFreePlan ? Math.max(0, FREE_PORTFOLIO_LIMIT - usedCount) : null

  const canGenerate = useMemo(() => {
    return Boolean(resumeFile) && !loading
  }, [resumeFile, loading])

  const handle = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleFile = (file) => {
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
      setError('Please upload a PDF file only.')
      return
    }
    setError('')
    setResumeFile(file)
  }

  const handleGenerate = async () => {
    if (!canGenerate) return
    setLoading(true)
    setError('')
    const toastId = toast.loading('Generating your portfolio...')
    try {
      const fd = new FormData()
      fd.append('resume', resumeFile)
      fd.append('name', form.name || '')
      fd.append('github_username', form.github_username || '')

      const res = await api.generatePortfolio(fd)
      setHtml(res.html || '')
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          html: res.html || '',
          name: form.name,
          github_username: form.github_username,
          resume_name: resumeFile?.name || '',
        })
      )
      if (res.usage?.portfolio_gen_count !== undefined) {
        setProfile((prev) => ({ ...(prev || {}), portfolio_gen_count: res.usage.portfolio_gen_count }))
      } else {
        setProfile((prev) => ({ ...(prev || {}), portfolio_gen_count: usedCount + 1 }))
      }
      toast.success('Portfolio generated!', { id: toastId })
    } catch (err) {
      const msg = err.message || 'Failed to generate portfolio.'
      setError(msg)
      toast.error(msg, { id: toastId })
    }
    setLoading(false)
  }

  const handleDownload = () => {
    if (!html) return
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'portfolio.html'
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Portfolio downloaded!')
  }

  const handleCopy = async () => {
    if (!html) return
    try {
      await navigator.clipboard.writeText(html)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
      toast.success('Copied to clipboard!')
    } catch {
      setError('Could not copy HTML to clipboard.')
      toast.error('Copy failed.')
    }
  }

  return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
      <div className="max-w-4xl mx-auto space-y-6 pb-16">
        {/* Header */}
        <div className="text-center space-y-1.5">
          <Badge sparkle size="sm" className="mx-auto mb-1">
            Site Builder
          </Badge>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0B0F19] tracking-tight flex items-center justify-center gap-2.5">
            <Globe size={24} className="text-[#2563EB]" />
            <span>Portfolio Generator</span>
          </h1>
          <p className="text-xs sm:text-sm text-[#64748B]">
            Generate a complete personal portfolio website from your resume in one click.
          </p>
        </div>

        {isFreePlan && (
          <div
            className={`p-3.5 rounded-xl border text-xs sm:text-sm font-medium ${
              remaining === 0
                ? 'bg-rose-50 border-rose-200 text-[#E11D48]'
                : 'bg-blue-50/80 border-blue-200 text-[#1E293B]'
            }`}
          >
            Free tier usage: {usedCount}/{FREE_PORTFOLIO_LIMIT} portfolio generations used.
            {remaining !== null && ` (${remaining} remaining)`}
          </div>
        )}

        {error && (
          <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-[#E11D48] text-xs font-semibold flex items-center gap-2">
            <AlertTriangle size={15} /> {error}
          </div>
        )}

        {!html ? (
          <GlassCard className="p-6 sm:p-8 space-y-5 border-white/95 shadow-glass-lg">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-[#0B0F19] uppercase tracking-wider mb-1.5">Name</label>
                <input
                  type="text"
                  className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-xs sm:text-sm font-semibold text-[#0B0F19] shadow-xs focus:border-[#2563EB] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/20"
                  value={form.name}
                  onChange={handle('name')}
                  placeholder="Your full name"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-[#0B0F19] uppercase tracking-wider mb-1.5">GitHub Username (optional)</label>
                <input
                  type="text"
                  className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-xs sm:text-sm font-semibold text-[#0B0F19] shadow-xs focus:border-[#2563EB] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/20"
                  value={form.github_username}
                  onChange={handle('github_username')}
                  placeholder="e.g. octocat"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-[#0B0F19] uppercase tracking-wider mb-1.5">Resume PDF</label>
              <div
                className={`rounded-2xl border-2 border-dashed p-6 sm:p-8 text-center transition-all ${
                  resumeFile ? 'border-emerald-300 bg-emerald-50/40' : 'border-slate-200 bg-white/50 hover:border-slate-300 hover:bg-white/80'
                }`}
              >
                {resumeFile ? (
                  <div className="space-y-2">
                    <FileText size={32} className="mx-auto text-[#16A34A]" />
                    <p className="text-sm font-bold text-[#0B0F19]">{resumeFile.name}</p>
                    <p className="text-xs text-[#64748B]">{(resumeFile.size / 1024).toFixed(0)} KB</p>
                    <button
                      type="button"
                      onClick={() => setResumeFile(null)}
                      className="text-xs font-semibold text-rose-600 hover:underline"
                    >
                      Remove file
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="w-10 h-10 rounded-xl bg-blue-50 text-[#2563EB] flex items-center justify-center mx-auto mb-2 border border-blue-100">
                      <Upload size={20} />
                    </div>
                    <p className="text-sm font-bold text-[#0B0F19]">Upload your resume PDF</p>
                    <p className="text-xs text-[#64748B]">We use your experience to generate the site automatically</p>
                  </div>
                )}
                <input
                  type="file"
                  accept=".pdf,application/pdf"
                  className="mt-4 block w-full text-xs text-[#64748B] file:mr-3 file:rounded-full file:border-0 file:bg-[#0B0F19] file:px-4 file:py-2 file:text-xs file:font-semibold file:text-white hover:file:bg-[#1E293B] file:cursor-pointer"
                  onChange={(e) => handleFile(e.target.files?.[0])}
                />
              </div>
            </div>

            <button
              type="button"
              onClick={handleGenerate}
              disabled={!canGenerate || (isFreePlan && remaining === 0)}
              className="w-full flex items-center justify-center gap-2 py-4 rounded-full bg-[#0B0F19] text-white font-bold text-sm hover:bg-[#1E293B] transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader2 size={18} className="animate-spin" /> Generating portfolio website...
                </>
              ) : (
                <>
                  <Sparkles size={18} /> Generate Portfolio
                </>
              )}
            </button>
          </GlassCard>
        ) : (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={() => {
                  setHtml('')
                  localStorage.removeItem(STORAGE_KEY)
                }}
                className="flex items-center gap-2 py-2.5 px-5 rounded-full border border-slate-200 bg-white/80 text-[#0B0F19] font-bold text-xs sm:text-sm hover:bg-white transition-all shadow-xs"
              >
                <RotateCcw size={14} /> Generate Again
              </button>
              <button
                type="button"
                onClick={handleCopy}
                className="flex items-center gap-2 py-2.5 px-5 rounded-full border border-slate-200 bg-white/80 text-[#0B0F19] font-bold text-xs sm:text-sm hover:bg-white transition-all shadow-xs"
              >
                {copied ? <CheckCircle size={14} className="text-[#16A34A]" /> : <Copy size={14} />}
                {copied ? 'Copied' : 'Copy HTML'}
              </button>
              <button
                type="button"
                onClick={handleDownload}
                className="flex items-center gap-2 py-2.5 px-5 rounded-full bg-[#0B0F19] text-white font-bold text-xs sm:text-sm hover:bg-[#1E293B] transition-all shadow-sm"
              >
                <Download size={14} /> Download HTML
              </button>
            </div>

            <GlassCard className="rounded-2xl overflow-hidden p-0 border-white/95 shadow-glass-lg">
              <iframe title="Portfolio Preview" srcDoc={html} className="w-full h-[720px] bg-white border-0" />
            </GlassCard>
          </div>
        )}
      </div>
    </motion.div>
  )
}
