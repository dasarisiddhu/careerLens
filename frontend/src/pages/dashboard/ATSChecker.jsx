// frontend/src/pages/dashboard/ATSChecker.jsx
import React, { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAnimatedCircle, useCountUp, pageTransition } from '../../utils/animations'
import { api } from '../../services/api'
import toast from 'react-hot-toast'
import {
  Loader2, CheckCircle2, XCircle, Target, Zap,
  Upload, FileText, AlertTriangle, TrendingUp, TrendingDown,
  ArrowRight,
} from 'lucide-react'
import { GlassCard, Button, Badge } from '../../components/ui'

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
  const { radius, circumference, offset, strokeWidth } = useAnimatedCircle(score, maxScore, size, 9)
  const count = useCountUp(score, 1400)
  const strokeColor = score >= 75 ? '#16A34A' : score >= 50 ? '#2563EB' : '#E11D48'

  return (
    <div style={{ position: 'relative', width: size, height: size, flexShrink: 0 }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle
          cx={size/2} cy={size/2} r={radius}
          fill="none"
          stroke="#E2E8F0"
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
          style={{ transition: 'stroke-dashoffset 1.4s cubic-bezier(0.22, 1, 0.36, 1)' }}
        />
      </svg>
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{
          fontSize: size > 100 ? '30px' : '22px',
          fontWeight: 800, color: '#0B0F19',
          letterSpacing: '-1px', lineHeight: 1,
        }}>
          {count}
        </span>
        {label && (
          <span style={{ fontSize: '11px', fontWeight: 600, color: '#64748B', marginTop: '3px' }}>
            {label}
          </span>
        )}
      </div>
    </div>
  )
}

const STORAGE_KEY = 'careerlens_ats_cache'

export default function ATSChecker() {
  const [resumeText,  setResumeText]  = useState('')
  const [resumeFile,  setResumeFile]  = useState(null)
  const [jobDesc,     setJobDesc]     = useState('')
  const [result,      setResult]      = useState(null)
  const [loading,     setLoading]     = useState(false)
  const [extracting,  setExtracting]  = useState(false)
  const [error,       setError]       = useState('')
  const [dragging,    setDragging]    = useState(false)
  const fileRef = useRef(null)

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
    if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
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
        binary += String.fromCharCode.apply(null, uint8Array.subarray(i, i + chunkSize))
      }
      const base64 = btoa(binary)
      const res = await api.extractResumeText({ pdf_base64: base64 })
      if (res && res.text && res.text.trim().length > 20) {
        setResumeText(res.text.trim())
        setError('')
      } else {
        setError('Could not extract text from this PDF. Please paste your resume text manually.')
      }
    } catch (err) {
      const msg = err?.message || 'Extraction failed'
      setError(`${msg} — Please paste your resume text below.`)
    } finally {
      setExtracting(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }

  const handleCheck = async () => {
    if (resumeText.length < 50 || jobDesc.length < 50) return
    setLoading(true)
    setError('')
    const toastId = toast.loading('Analyzing ATS match...')
    try {
      const base64 = buildPdfBase64FromText(resumeText)
      const res = await api.checkATS({
        resume_pdf: base64,
        job_description: jobDesc,
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

  const getScoreSurface = (s) =>
    s >= 85
      ? 'border-emerald-200/90 bg-emerald-50/40 shadow-glass'
      : s >= 70
      ? 'border-blue-200/90 bg-blue-50/40 shadow-glass'
      : s >= 50
      ? 'border-amber-200/90 bg-amber-50/40 shadow-glass'
      : 'border-rose-200/90 bg-rose-50/40 shadow-glass'

  const getPlainStatus = (s) => {
    if (s >= 85) return { text: 'Strong Match', color: 'text-[#16A34A]' }
    if (s >= 70) return { text: 'Good Match', color: 'text-[#2563EB]' }
    if (s >= 50) return { text: 'Average Match', color: 'text-[#D97706]' }
    return { text: 'Weak Match', color: 'text-[#E11D48]' }
  }

  const hasScoreResult = result && typeof result === 'object' && !Array.isArray(result) && typeof result.ats_score === 'number'

  if (!hasScoreResult) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 pb-16">
        <div>
          <Badge sparkle size="sm" className="mb-2">
            ATS Diagnostic
          </Badge>
          <h1 className="text-3xl font-extrabold text-[#0B0F19] tracking-tight">
            ATS Checker
          </h1>
          <p className="text-xs sm:text-sm text-[#64748B] mt-1">
            Upload your resume PDF + paste a job description → get an honest ATS keyword and structure match.
          </p>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-[#E11D48] text-xs flex items-center gap-2">
            <AlertTriangle size={16} className="shrink-0" /> <span>{error}</span>
          </div>
        )}

        {resumeText.length > 100 && !resumeFile && (
          <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-[#16A34A] text-xs flex items-center gap-2">
            <CheckCircle2 size={15} /> <span>Optimized resume text loaded automatically — paste a job description and check your score!</span>
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-5">
          {/* PDF Upload */}
          <div className="space-y-3">
            <label className="text-xs font-bold text-[#0B0F19] uppercase tracking-wider flex items-center gap-2">
              <FileText size={14} className="text-[#2563EB]" /> Your Resume (PDF)
            </label>
            <div
              onClick={() => fileRef.current?.click()}
              onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              className={`relative flex flex-col items-center justify-center h-44 rounded-2xl border-2 border-dashed cursor-pointer transition-all p-4 ${
                dragging ? 'border-[#2563EB] bg-blue-50/60' : resumeFile
                  ? 'border-emerald-300 bg-emerald-50/40'
                  : 'border-slate-200 bg-white/70 hover:border-slate-300 hover:bg-white'
              }`}
            >
              {resumeFile ? (
                <div className="text-center px-4">
                  <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center mx-auto mb-2 text-[#16A34A]">
                    <CheckCircle2 size={20} />
                  </div>
                  <p className="text-[#0B0F19] font-bold text-sm truncate max-w-xs">{resumeFile.name}</p>
                  <p className="text-[#16A34A] text-xs font-semibold mt-0.5">✓ PDF uploaded successfully</p>
                  <p className="text-[#94A3B8] text-[11px]">{(resumeFile.size / 1024).toFixed(0)} KB</p>
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); setResumeFile(null) }}
                    className="mt-2 text-xs font-semibold text-rose-600 hover:underline"
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <div className="text-center px-6">
                  <div className="w-10 h-10 rounded-xl bg-blue-50 text-[#2563EB] flex items-center justify-center mx-auto mb-2 border border-blue-100">
                    <Upload size={18} />
                  </div>
                  <p className="text-[#0B0F19] text-sm font-bold">Drop your resume PDF here</p>
                  <p className="text-[#64748B] text-xs mt-0.5">or click to browse</p>
                </div>
              )}
              <input ref={fileRef} type="file" accept=".pdf" className="hidden"
                onChange={e => handleFile(e.target.files[0])} />
            </div>

            {extracting && (
              <div className="flex items-center gap-2 text-[#2563EB] text-xs font-semibold">
                <Loader2 size={14} className="animate-spin" /> <span>Extracting text from PDF...</span>
              </div>
            )}

            <div>
              <label className="text-xs font-bold text-[#0B0F19] uppercase tracking-wider mb-2 block">
                RESUME TEXT{' '}
                <span className="text-[#64748B] font-normal lowercase">(auto-filled or paste manually)</span>
              </label>
              <textarea
                value={resumeText}
                onChange={e => setResumeText(e.target.value)}
                rows={6}
                placeholder="Resume text will auto-fill from PDF upload, or paste manually here..."
                className="w-full rounded-xl border border-slate-200 bg-white p-3 text-xs text-[#0B0F19] placeholder:text-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] resize-none shadow-xs"
              />
              <div className="flex justify-between items-center mt-1">
                <span className={`text-[11px] font-semibold ${resumeText.length > 50 ? 'text-[#16A34A]' : 'text-[#64748B]'}`}>
                  {resumeText.length > 50 ? `✓ ${resumeText.length} chars ready` : `${resumeText.length} chars`}
                </span>
                {resumeText.length > 0 && (
                  <button
                    type="button"
                    onClick={() => setResumeText('')}
                    className="text-[11px] font-semibold text-slate-400 hover:text-rose-600 transition-colors"
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Job Description */}
          <div className="space-y-3">
            <label className="text-xs font-bold text-[#0B0F19] uppercase tracking-wider flex items-center gap-2">
              💼 Job Description
            </label>
            <textarea
              value={jobDesc}
              onChange={e => setJobDesc(e.target.value)}
              rows={11}
              placeholder={`Paste the full job description here...\n\nInclude:\n• Job title and requirements\n• Required skills and technologies\n• Years of experience needed\n• Responsibilities`}
              className="w-full h-80 rounded-xl border border-slate-200 bg-white p-3 text-xs leading-relaxed text-[#0B0F19] placeholder:text-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] resize-none shadow-xs"
            />
          </div>
        </div>

        <button
          type="button"
          onClick={handleCheck}
          disabled={loading || resumeText.length < 50 || jobDesc.length < 50}
          className="w-full py-4 rounded-full bg-[#0B0F19] text-white font-bold text-sm hover:bg-[#1E293B] transition-all shadow-md flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {loading
            ? <><Loader2 size={18} className="animate-spin" /> Analyzing your match...</>
            : <><Zap size={18} /> Check ATS Match</>}
        </button>
      </div>
    )
  }

  // ── RESULT SCREEN ─────────────────────────────────────────
  const verdict = getPlainStatus(result.ats_score)

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-16">
      {/* Score Header */}
      <div className={`relative overflow-hidden rounded-[24px] p-6 sm:p-8 border ${getScoreSurface(result.ats_score)}`}>
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="flex flex-col sm:flex-row sm:items-center gap-6">
            <AnimatedScoreCircle score={result.ats_score} size={130} label="ATS Match" />
            <div>
              <div className="mb-1">
                <span className={`text-xl font-extrabold ${verdict.color}`}>{verdict.text}</span>
              </div>
              <p className="text-xs text-[#64748B]">ATS Match Score out of 100</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="bg-white/90 border border-slate-200/90 px-4 py-3 rounded-xl shadow-xs">
              <p className="text-[11px] font-bold uppercase tracking-wider text-[#64748B] mb-0.5">Matched</p>
              <p className="text-2xl font-black text-[#16A34A]">{result.matched_keywords?.length || 0}</p>
            </div>
            <div className="bg-white/90 border border-slate-200/90 px-4 py-3 rounded-xl shadow-xs">
              <p className="text-[11px] font-bold uppercase tracking-wider text-[#64748B] mb-0.5">Missing</p>
              <p className="text-2xl font-black text-[#E11D48]">{result.missing_keywords?.length || 0}</p>
            </div>
          </div>
        </div>
        {result.honest_verdict && (
          <div className="mt-4 p-3.5 rounded-xl bg-white/80 border border-slate-200/70">
            <p className="text-xs text-[#475569] leading-relaxed">
              <span className="font-bold text-[#0B0F19]">Assessment: </span>
              {result.honest_verdict}
            </p>
          </div>
        )}
      </div>

      {/* Keywords Grid */}
      <div className="grid md:grid-cols-2 gap-4">
        <GlassCard className="p-5 shadow-glass">
          <h2 className="font-bold text-sm text-[#0B0F19] mb-3 flex items-center gap-2">
            <CheckCircle2 size={16} className="text-[#16A34A]" /> Matched Keywords
          </h2>
          {result.matched_keywords?.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {result.matched_keywords.map((k, i) => (
                <span key={i} className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-[#16A34A] border border-emerald-200">
                  ✓ {k}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-[#94A3B8] text-xs">No keywords matched.</p>
          )}
        </GlassCard>

        <GlassCard className="p-5 shadow-glass">
          <h2 className="font-bold text-sm text-[#0B0F19] mb-3 flex items-center gap-2">
            <XCircle size={16} className="text-[#E11D48]" /> Missing Keywords
          </h2>
          {result.missing_keywords?.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {result.missing_keywords.map((k, i) => (
                <span key={i} className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-[#E11D48] border border-rose-200">
                  ✗ {k}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-[#16A34A] text-xs font-semibold">No critical keywords missing!</p>
          )}
        </GlassCard>
      </div>

      {/* Skills Match */}
      <div className="grid md:grid-cols-2 gap-4">
        {result.matched_skills?.length > 0 && (
          <GlassCard className="p-5 shadow-glass">
            <h2 className="font-bold text-sm text-[#0B0F19] mb-3 flex items-center gap-2">
              <TrendingUp size={16} className="text-[#16A34A]" /> Skills You Have
            </h2>
            <ul className="space-y-1.5">
              {result.matched_skills.map((s, i) => (
                <li key={i} className="text-xs text-[#475569] flex items-center gap-2">
                  <span className="text-[#16A34A] font-bold">✓</span> {s}
                </li>
              ))}
            </ul>
          </GlassCard>
        )}
        {result.missing_skills?.length > 0 && (
          <GlassCard className="p-5 shadow-glass">
            <h2 className="font-bold text-sm text-[#0B0F19] mb-3 flex items-center gap-2">
              <TrendingDown size={16} className="text-[#E11D48]" /> Skills You're Missing
            </h2>
            <ul className="space-y-1.5">
              {result.missing_skills.map((s, i) => (
                <li key={i} className="text-xs text-[#475569] flex items-center gap-2">
                  <span className="text-[#E11D48] font-bold">✗</span> {s}
                </li>
              ))}
            </ul>
          </GlassCard>
        )}
      </div>

      {/* Suggestions */}
      {result.suggestions?.length > 0 && (
        <GlassCard className="p-6 border-blue-200/80 bg-blue-50/40 shadow-glass">
          <h2 className="font-bold text-sm text-[#0B0F19] mb-4 flex items-center gap-2">
            <Zap size={16} className="text-[#2563EB]" /> Actionable Fixes
          </h2>
          <ul className="space-y-2.5">
            {result.suggestions.map((s, i) => (
              <li key={i} className="flex items-start gap-2.5 p-3 rounded-xl bg-white border border-slate-200/70 text-xs text-[#475569]">
                <span className="text-[#2563EB] font-bold shrink-0 mt-0.5">{i + 1}.</span>
                <p className="leading-relaxed">{s}</p>
              </li>
            ))}
          </ul>
        </GlassCard>
      )}

      {/* Bottom actions */}
      <div className="flex gap-3 pb-6">
        <button
          type="button"
          onClick={() => {
            setResult(null)
            setResumeFile(null)
            setJobDesc('')
            localStorage.removeItem(STORAGE_KEY)
          }}
          className="flex-1 py-3.5 rounded-full border border-slate-200 bg-white text-[#0B0F19] font-bold text-xs hover:bg-slate-50 transition-all shadow-xs"
        >
          Check Another Job
        </button>
      </div>
    </div>
  )
}
