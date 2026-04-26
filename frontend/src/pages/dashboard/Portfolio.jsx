import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { pageTransition } from '../../utils/animations'
import { api } from '../../services/api'
import toast from 'react-hot-toast'
import { Globe, Loader2, Sparkles, AlertTriangle, Download, Copy, RotateCcw, CheckCircle, Upload, FileText } from 'lucide-react'

const FREE_PORTFOLIO_LIMIT = 4

const buttonMotion = {
  whileHover: { scale: 1.03, y: -1 },
  whileTap: { scale: 0.97 },
  transition: { duration: 0.15, ease: 'easeOut' },
}

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
    api.getMe().then((res) => {
      const user = res.user || {}
      setProfile(user)
      setForm((prev) => ({
        ...prev,
        name: user.name || '',
        github_username: extractGithubUsername(user.github_url || ''),
      }))
    }).catch(() => {})

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
    if (file.type !== 'application/pdf') {
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
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        html: res.html || '',
        name: form.name,
        github_username: form.github_username,
        resume_name: resumeFile?.name || '',
      }))
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
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <Globe size={28} className="text-amber-400" /> Portfolio Generator
        </h1>
        <p className="text-[#78716c] mt-1">Generate a complete personal portfolio website from your resume in one click.</p>
      </div>

      {isFreePlan && (
        <div className={`p-4 rounded-xl border text-sm ${remaining === 0 ? 'bg-red-500/10 border-red-500/30 text-red-300' : 'bg-amber-500/10 border-amber-500/20 text-amber-300'}`}>
          Free tier usage: {usedCount}/{FREE_PORTFOLIO_LIMIT} portfolio generations used.
          {remaining !== null && ` ${remaining} remaining.`}
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-2">
          <AlertTriangle size={16} /> {error}
        </div>
      )}

      {!html ? (
        <div className="glass p-6 rounded-2xl space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-[#d6d3d1] mb-1.5">Name</label>
              <input className="input-field" value={form.name} onChange={handle('name')} placeholder="Your name" />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#d6d3d1] mb-1.5">GitHub Username (optional)</label>
              <input className="input-field" value={form.github_username} onChange={handle('github_username')} placeholder="e.g. octocat" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-[#d6d3d1] mb-1.5">Resume PDF</label>
            <div
              className={`rounded-2xl border-2 border-dashed p-8 text-center transition-all ${
                resumeFile ? 'border-green-500/40 bg-green-500/5' : 'border-white/10 bg-white/5 hover:border-amber-500/40'
              }`}
            >
              {resumeFile ? (
                <div className="space-y-2">
                  <FileText size={30} className="mx-auto text-green-400" />
                  <p className="text-white font-semibold">{resumeFile.name}</p>
                  <p className="text-xs text-[#78716c]">{(resumeFile.size / 1024).toFixed(0)} KB</p>
                  <motion.button {...buttonMotion}
                    type="button"
                    onClick={() => setResumeFile(null)}
                    className="text-xs text-red-400 hover:text-red-300 underline"
                  >
                    Remove file
                  </motion.button>
                </div>
              ) : (
                <div className="space-y-2">
                  <Upload size={30} className="mx-auto text-[#78716c]" />
                  <p className="text-white font-medium">Upload your resume PDF</p>
                  <p className="text-xs text-[#44403c]">Only PDF files are accepted</p>
                </div>
              )}
              <input
                type="file"
                accept=".pdf,application/pdf"
                className="mt-4 block w-full text-sm text-[#d6d3d1] file:mr-3 file:rounded-lg file:border-0 file:bg-amber-600 file:px-3 file:py-2 file:text-[#0a0a0a] hover:file:bg-amber-500"
                onChange={(e) => handleFile(e.target.files?.[0])}
              />
            </div>
            <p className="text-xs text-[#44403c] mt-1">Tip: use a text-based PDF for best extraction quality.</p>
          </div>
          <motion.button {...buttonMotion} onClick={handleGenerate} disabled={!canGenerate || (isFreePlan && remaining === 0)}
            className="btn-primary w-full py-4 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
            {loading ? <><Loader2 size={18} className="animate-spin" /> Generating portfolio...</> : <><Sparkles size={18} /> Generate Portfolio</>}
          </motion.button>
        </div>
      ) : (
        <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <motion.button {...buttonMotion} onClick={() => { setHtml(''); localStorage.removeItem(STORAGE_KEY); }} className="btn-ghost flex items-center gap-2">
          <RotateCcw size={15} /> Generate Again
        </motion.button>
            <motion.button {...buttonMotion} onClick={handleCopy} className="btn-ghost flex items-center gap-2">
              {copied ? <CheckCircle size={15} className="text-green-400" /> : <Copy size={15} />}
              {copied ? 'Copied' : 'Copy HTML'}
            </motion.button>
            <motion.button {...buttonMotion} onClick={handleDownload} className="btn-primary flex items-center gap-2">
              <Download size={15} /> Download HTML
            </motion.button>
          </div>

          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass rounded-2xl overflow-hidden border border-white/10">
            <iframe title="Portfolio Preview" srcDoc={html} className="w-full h-[720px] bg-white" />
          </motion.div>
        </div>
      )}
    </div>
    </motion.div>
  )
}






