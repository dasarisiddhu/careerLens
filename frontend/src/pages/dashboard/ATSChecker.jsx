// frontend/src/pages/dashboard/ATSChecker.jsx
import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAnimatedCircle, useCountUp, pageTransition } from '../../utils/animations'
import { api } from '../../services/api'
import toast from 'react-hot-toast'
import {
  Loader2, CheckCircle, XCircle, Target, Zap,
  Upload, FileText, AlertTriangle, TrendingUp, TrendingDown
} from 'lucide-react'

function normalizePdfText(value = '') {
  return String(value)
    .replace(/\r/g, '')
    .replace(/[\u2013\u2014]/g, '-')
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201C\u201D]/g, '"')
    .replace(/\u2022/g, '*')
    .replace(/\u00A0/g, ' ')
    .replace(/[^\x20-\x7E\n]/g, ' ')
}

function escapePdfText(value = '') {
  return normalizePdfText(value)
    .replace(/\\/g, '\\\\')
    .replace(/\(/g, '\\(')
    .replace(/\)/g, '\\)')
}

function wrapPdfText(value, maxChars) {
  const paragraphs = normalizePdfText(value).split('\n')
  const lines = []
  for (const paragraph of paragraphs) {
    const words = paragraph.trim().split(/\s+/).filter(Boolean)
    if (!words.length) { lines.push(''); continue }
    let current = words[0]
    for (const word of words.slice(1)) {
      const candidate = `${current} ${word}`
      if (candidate.length <= maxChars) current = candidate
      else { lines.push(current); current = word }
    }
    lines.push(current)
  }
  return lines
}

function buildPdfFromText(text) {
  const pageWidth = 612, pageHeight = 792
  const marginX = 54, topY = 742, bottomY = 54
  const fontSize = 11, lineHeight = fontSize + 5
  const pages = []
  let commands = [], currentY = topY
  for (const line of wrapPdfText(text, 92)) {
    if (currentY - lineHeight < bottomY) {
      pages.push(commands.join('\n')); commands = []; currentY = topY
    }
    if (!line) { currentY -= lineHeight; continue }
    commands.push(`BT /F1 ${fontSize} Tf 0 g 1 0 0 1 ${marginX} ${currentY} Tm (${escapePdfText(line)}) Tj ET`)
    currentY -= lineHeight
  }
  if (!pages.length || commands.length) pages.push(commands.join('\n'))
  const objects = [null]
  objects[1] = '<< /Type /Catalog /Pages 2 0 R >>'
  objects[3] = '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>'
  const kids = []
  let objectIndex = 4
  for (const stream of pages) {
    const pageObject = objectIndex++, contentObject = objectIndex++
    kids.push(`${pageObject} 0 R`)
    objects[pageObject] = `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${pageWidth} ${pageHeight}] /Resources << /Font << /F1 3 0 R >> >> /Contents ${contentObject} 0 R >>`
    objects[contentObject] = `<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`
  }
  objects[2] = `<< /Type /Pages /Count ${pages.length} /Kids [${kids.join(' ')}] >>`
  let pdf = '%PDF-1.4\n'
  const offsets = [0]
  for (let i = 1; i < objects.length; i++) { offsets[i] = pdf.length; pdf += `${i} 0 obj\n${objects[i]}\nendobj\n` }
  const xrefOffset = pdf.length
  pdf += `xref\n0 ${objects.length}\n`
  pdf += '0000000000 65535 f \n'
  for (let i = 1; i < objects.length; i++) pdf += `${String(offsets[i]).padStart(10, '0')} 00000 n \n`
  pdf += `trailer\n<< /Size ${objects.length} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`
  return pdf
}

function buildPdfBase64FromText(text) {
  return btoa(buildPdfFromText(text || ''))
}

function AnimatedScoreCircle({ score, maxScore = 100, size = 140, label }) {
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

export default function ATSChecker() {
  const STORAGE_KEY = 'careerlens:ats:last_result'
  const [resumeFile,  setResumeFile]  = useState(null)
  const [resumeText,  setResumeText]  = useState('')
  const [jobDesc,     setJobDesc]     = useState('')
  const [result,      setResult]      = useState(null)
  const [loading,     setLoading]     = useState(false)
  const [extracting,  setExtracting]  = useState(false)
  const [error,       setError]       = useState('')
  const [dragging,    setDragging]    = useState(false)
  const fileRef = useRef(null)
  const buttonMotion = {
    whileHover: { scale: 1.03, y: -1 },
    whileTap: { scale: 0.97 },
    transition: { duration: 0.15, ease: 'easeOut' },
  }

  // ── Auto-fill from ResumeOptimizer via localStorage ──────
  useEffect(() => {
    const saved = localStorage.getItem('careerlens_resume_text')
    if (saved && saved.trim().length > 50) {
      setResumeText(saved.trim())
      localStorage.removeItem('careerlens_resume_text')
      return
    }
    try {
      const cached = localStorage.getItem(STORAGE_KEY)
      if (cached) {
        const parsed = JSON.parse(cached)
        if (parsed?.result) {
          setResult(parsed.result)
          setJobDesc(parsed.job_desc || '')
        }
      }
    } catch {}
  }, [])

  const handleFile = async (file) => {
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.pdf') &&
        file.type !== 'application/pdf') {
      setError('Please upload a PDF file.')
      return
    }
    setResumeFile(file)
    setResumeText('')
    setError('')
    setExtracting(true)
    try {
      const arrayBuffer = await file.arrayBuffer()
      const uint8Array = new Uint8Array(arrayBuffer)
      let binary = ''
      const chunkSize = 8192
      for (let i = 0; i < uint8Array.length; i += chunkSize) {
        binary += String.fromCharCode.apply(
          null, uint8Array.subarray(i, i + chunkSize)
        )
      }
      const base64 = btoa(binary)

      const res = await api.extractResumeText({ pdf_base64: base64 })

      if (res && res.text && res.text.trim().length > 20) {
        setResumeText(res.text.trim())
        setError('')
      } else {
        setError(
          'Could not extract text from this PDF. ' +
          'Please paste your resume text manually.'
        )
      }
    } catch (err) {
      const msg = err?.message || 'Extraction failed'
      setError(`${msg} — Please paste your resume text below.`)
    } finally {
      setExtracting(false)
    }
  }

  const handleDrop = (e) => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0]) }

  const handleCheck = async () => {
    if (resumeText.length < 50 || jobDesc.length < 50) return
    setLoading(true)
    setError('')
    const toastId = toast.loading('Analyzing ATS match...')
    try {
      const base64 = buildPdfBase64FromText(resumeText)
      const res = await api.checkATS({
        resume_pdf: base64,
        job_description: jobDesc
      })
      setResult(res.result)
      toast.success('ATS match calculated!', { id: toastId })
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        result: res.result,
        job_desc: jobDesc,
        resume_name: resumeFile?.name || '',
      }))
    } catch (err) {
      setError(err.message || 'ATS check failed. Please try again.')
      toast.error(err.message || 'ATS check failed. Please try again.', { id: toastId })
    }
    setLoading(false)
  }

  const getScoreSurface = (s) => s >= 85
    ? 'bg-[#141822] border-green-500/20'
    : s >= 70
      ? 'bg-[#141822] border-red-500/20'
      : s >= 50
        ? 'bg-[#141822] border-white/10'
        : 'bg-[#141822] border-red-500/20'
  // ── INPUT SCREEN ─────────────────────────────────────────
  const getPlainStatus = (s) => {
    if (s >= 85) return { text: 'Strong', color: 'text-green-400' }
    if (s >= 70) return { text: 'Good', color: 'text-white' }
    if (s >= 50) return { text: 'Average', color: 'text-[#d6d3d1]' }
    return { text: 'Weak', color: 'text-red-400' }
  }

  const hasScoreResult = result && typeof result === 'object' && !Array.isArray(result) && typeof result.ats_score === 'number'

  if (!hasScoreResult) return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
      <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="gradient-text text-3xl font-bold flex items-center gap-3">
          <Target size={28} className="text-[#FF3B3B]" /> ATS Checker
        </h1>
        <p className="text-[#78716c] mt-1">
          Upload your resume PDF + paste a job description → get a brutally honest ATS match score
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-2">
          <AlertTriangle size={16} /> {error}
        </div>
      )}

      {/* Auto-fill success notice */}
      {resumeText.length > 100 && !resumeFile && (
        <div className="p-3 rounded-xl bg-green-500/10 border border-green-500/20 text-green-300 text-sm flex items-center gap-2">
          <CheckCircle size={14} /> Optimized resume text loaded automatically — paste a job description and check your score!
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-5">

        {/* PDF Upload */}
        <div className="space-y-3">
          <label className="text-sm font-semibold text-[#d6d3d1] flex items-center gap-2">
            <FileText size={15} className="text-[#FF3B3B]" /> Your Resume (PDF)
          </label>
          <div
            onClick={() => fileRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            className={`relative flex flex-col items-center justify-center h-40 rounded-2xl border-2 border-dashed
              cursor-pointer transition-all duration-200
              ${dragging ? 'border-[#FF3B3B] bg-red-500/10 shadow-[0_0_30px_rgba(255,59,59,0.1)]' : resumeFile
                ? 'border-green-500/50 bg-green-500/5'
                : 'border-white/10 bg-white/[0.02] hover:border-[rgba(255,59,59,0.28)] hover:bg-red-500/5'}`}>
            {resumeFile ? (
              <div className="text-center px-4">
                <div className="w-12 h-12 rounded-2xl bg-green-500/20 flex items-center justify-center mx-auto mb-2">
                  <FileText size={22} className="text-green-400" />
                </div>
                <p className="text-white font-semibold text-sm">{resumeFile.name}</p>
                <p className="text-green-400 text-xs mt-1">✓ PDF uploaded successfully</p>
                <p className="text-[#44403c] text-xs">{(resumeFile.size / 1024).toFixed(0)} KB</p>
                <motion.button {...buttonMotion} onClick={(e) => { e.stopPropagation(); setResumeFile(null) }}
                  className="mt-2 text-xs text-red-400 hover:text-red-300 underline">Remove</motion.button>
              </div>
            ) : (
              <div className="text-center px-6">
                <Upload size={22} className="float text-[#FF7070] mx-auto mb-2" />
                <p className="text-white text-sm font-medium">Drop your resume PDF here</p>
                <p className="text-[#44403c] text-xs mt-1">or click to browse</p>
              </div>
            )}
            <input ref={fileRef} type="file" accept=".pdf" className="hidden"
              onChange={e => handleFile(e.target.files[0])} />
          </div>

          {extracting && (
            <div className="flex items-center gap-2 text-[#FF7070] text-sm">
              <Loader2 size={14} className="animate-spin" /> Extracting text from PDF...
            </div>
          )}

          {/* Resume text — always visible */}
          <div>
            <label className="text-xs font-semibold text-[#78716c] uppercase tracking-wide mb-2 block">
              RESUME TEXT{' '}
              <span className="text-[#44403c] font-normal">(auto-filled from PDF or paste manually)</span>
            </label>
            <textarea
              value={resumeText}
              onChange={e => setResumeText(e.target.value)}
              rows={6}
              placeholder="Resume text will auto-fill from PDF upload, or paste manually here..."
              className={`input-field resize-none w-full text-sm transition-all ${
                resumeText.length > 100 ? 'border-green-500/50 bg-green-500/5' : ''
              }`}
            />
            <div className="flex justify-between items-center mt-1">
              <span className={`text-xs ${resumeText.length > 100 ? 'text-green-400' : 'text-[#44403c]'}`}>
                {resumeText.length > 100 ? `✓ ${resumeText.length} chars ready` : `${resumeText.length} chars`}
              </span>
              {resumeText.length > 0 && (
                <motion.button {...buttonMotion} onClick={() => setResumeText('')}
                  className="text-xs text-[#44403c] hover:text-red-400 transition-colors">Clear</motion.button>
              )}
            </div>
          </div>
        </div>

        {/* Job Description */}
        <div className="space-y-3">
          <label className="text-sm font-semibold text-[#d6d3d1] flex items-center gap-2">
            💼 Job Description
          </label>
          <textarea
            value={jobDesc}
            onChange={e => setJobDesc(e.target.value)}
            rows={11}
            placeholder={`Paste the full job description here...\n\nInclude:\n• Job title and requirements\n• Required skills and technologies\n• Years of experience needed\n• Responsibilities`}
            className="input-field resize-none w-full h-64 text-sm leading-relaxed"
          />
        </div>
      </div>

      {/* Warning */}
      <div className="p-4 rounded-xl bg-red-500/6 border border-red-500/20 flex items-start gap-3">
        <AlertTriangle size={16} className="text-[#FF7070] shrink-0 mt-0.5" />
        <p className="text-[#FF7070] text-sm">
          <strong>Brutally honest mode ON.</strong> This tool will not sugarcoat results.
          If your resume is weak for this role, it will tell you exactly why.
        </p>
      </div>

      <motion.button {...buttonMotion}
        onClick={handleCheck}
        disabled={loading || resumeText.length < 50 || jobDesc.length < 50}
        className="btn-primary w-full py-4 flex items-center justify-center gap-2 text-base disabled:opacity-50 disabled:cursor-not-allowed">
        {loading
          ? <><Loader2 size={18} className="animate-spin" /> Analyzing your match...</>
          : <><Zap size={18} /> Check ATS Match</>}
      </motion.button>
    </div>
  </motion.div>
  )

  // ── RESULT SCREEN ─────────────────────────────────────────
  const verdict = getPlainStatus(result.ats_score)

  return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
      <div className="max-w-5xl mx-auto space-y-5">

      {/* Score Header */}
      <motion.div initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }}
        className={`relative overflow-hidden glass-glow rounded-2xl p-6 border ${getScoreSurface(result.ats_score)}`}>
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="flex flex-col sm:flex-row sm:items-center gap-6">
            <AnimatedScoreCircle score={result.ats_score} size={140} label="ATS Match" />
            <div>
              <div className="mb-2">
                <span className={`text-lg font-bold ${verdict.color}`}>{verdict.text}</span>
              </div>
              <p className="text-[#78716c] text-sm">ATS Match Score</p>
            </div>
          </div>
          <div className="space-y-3 text-right">
            <div className="glass px-4 py-3 rounded-xl">
              <p className="text-xs text-[#78716c] mb-0.5">Keywords Matched</p>
              <p className="text-2xl font-bold text-green-400">{result.matched_keywords?.length || 0}</p>
            </div>
            <div className="glass px-4 py-3 rounded-xl">
              <p className="text-xs text-[#78716c] mb-0.5">Keywords Missing</p>
              <p className="text-2xl font-bold text-red-400">{result.missing_keywords?.length || 0}</p>
            </div>
          </div>
        </div>
        {result.honest_verdict && (
          <div className="mt-4 p-3 rounded-xl bg-black/20 border border-white/5">
            <p className="text-sm text-[#d6d3d1] leading-relaxed">
              <span className="text-white font-semibold">Honest Assessment: </span>
              {result.honest_verdict}
            </p>
          </div>
        )}
      </motion.div>

      {/* Keywords Grid */}
      <div className="grid md:grid-cols-2 gap-4">
        <motion.div initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}
          className="glass-glow p-5 rounded-2xl">
          <h3 className="font-bold text-white mb-3 flex items-center gap-2">
            <CheckCircle size={16} className="text-green-400" /> Matched Keywords
          </h3>
          {result.matched_keywords?.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {result.matched_keywords.map((k, i) => (
                <span key={i} className="badge badge-green normal-case tracking-normal">
                  ✓ {k}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-[#44403c] text-sm">No keywords matched — this is a serious problem.</p>
          )}
        </motion.div>

        <motion.div initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15 }}
          className="glass-glow p-5 rounded-2xl">
          <h3 className="font-bold text-white mb-3 flex items-center gap-2">
            <XCircle size={16} className="text-red-400" /> Missing Keywords
          </h3>
          {result.missing_keywords?.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {result.missing_keywords.map((k, i) => (
                <span key={i} className="badge badge-red normal-case tracking-normal">
                  ✗ {k}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-green-400 text-sm">No critical keywords missing!</p>
          )}
        </motion.div>
      </div>

      {/* Skills Match */}
      <div className="grid md:grid-cols-2 gap-4">
        {result.matched_skills?.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
            className="glass-glow p-5 rounded-2xl">
            <h3 className="font-bold text-white mb-3 flex items-center gap-2">
              <TrendingUp size={16} className="text-green-400" /> Skills You Have
            </h3>
            <ul className="space-y-1.5">
              {result.matched_skills.map((s, i) => (
                <li key={i} className="text-sm text-[#d6d3d1] flex items-center gap-2">
                  <span className="text-green-400 shrink-0">✓</span> {s}
                </li>
              ))}
            </ul>
          </motion.div>
        )}
        {result.missing_skills?.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}
            className="glass-glow p-5 rounded-2xl">
            <h3 className="font-bold text-white mb-3 flex items-center gap-2">
              <TrendingDown size={16} className="text-red-400" /> Skills You're Missing
            </h3>
            <ul className="space-y-1.5">
              {result.missing_skills.map((s, i) => (
                <li key={i} className="text-sm text-[#d6d3d1] flex items-center gap-2">
                  <span className="text-red-400 shrink-0">✗</span> {s}
                </li>
              ))}
            </ul>
          </motion.div>
        )}
      </div>

      {/* Brutal Suggestions */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
        className="glass-glow p-6 rounded-2xl border border-red-500/20 bg-red-500/5">
        <h3 className="font-bold text-white mb-4 flex items-center gap-2">
          <AlertTriangle size={16} className="text-[#FF7070]" /> What You Must Fix (Brutally Honest)
        </h3>
        <ul className="space-y-3">
          {result.suggestions?.map((s, i) => (
            <li key={i} className="flex items-start gap-3 p-3 rounded-xl bg-black/20">
              <span className="text-[#FF3B3B] font-bold shrink-0 mt-0.5">{i + 1}.</span>
              <p className="text-sm text-[#e7e5e4]">{s}</p>
            </li>
          ))}
        </ul>
      </motion.div>

      {/* Bottom actions */}
      <div className="flex gap-3 pb-6">
        <motion.button {...buttonMotion} onClick={() => {
          setResult(null); setResumeFile(null); setJobDesc('')
          localStorage.removeItem(STORAGE_KEY)
        }} className="btn-ghost flex-1">
          Check Another Job
        </motion.button>
      </div>
    </div>
  </motion.div>
  )
}






