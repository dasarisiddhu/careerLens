import React, { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '../../services/api'
import {
  Loader2,
  Briefcase,
  ExternalLink,
  XCircle,
  Zap,
  ChevronRight,
  Upload,
  CheckCircle2,
  AlertCircle,
  Sparkles,
} from 'lucide-react'
import { GlassCard, Button, Badge } from '../../components/ui'

function MatchBar({ score }) {
  const color =
    score >= 75 ? 'bg-[#16A34A]' : score >= 50 ? 'bg-[#2563EB]' : 'bg-[#D97706]'
  const textColor =
    score >= 75 ? 'text-[#16A34A]' : score >= 50 ? 'text-[#2563EB]' : 'text-[#D97706]'

  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        />
      </div>
      <span className={`text-xs font-bold w-12 text-right ${textColor}`}>{score}%</span>
    </div>
  )
}

export default function JobMatchEngine({ resumeText: initialResumeText = '' }) {
  const [resumeText, setResumeText] = useState(initialResumeText)
  const [resumeFile, setResumeFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [extracting, setExtracting] = useState(false)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState(null)
  const fileRef = useRef(null)

  const hasMatchResult = result && typeof result === 'object' && !Array.isArray(result)
  const bestFit = hasMatchResult && result.best_fit && typeof result.best_fit === 'object' ? result.best_fit : null
  const jobMatches = hasMatchResult && Array.isArray(result.job_matches) ? result.job_matches : []

  useEffect(() => {
    const saved = sessionStorage.getItem('careerlens_resume_text') || localStorage.getItem('careerlens_resume_text')
    if (saved && saved.trim().length > 50) {
      setResumeText(saved.trim())
      sessionStorage.removeItem('careerlens_resume_text')
      localStorage.removeItem('careerlens_resume_text')
    }
  }, [])

  useEffect(() => {
    if (initialResumeText) setResumeText(initialResumeText)
  }, [initialResumeText])

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
        setError('Could not extract text automatically. Please paste your resume text below.')
      }
    } catch (err) {
      const msg = err?.message || 'Extraction failed'
      setError(`${msg} — Please paste your resume text below.`)
    } finally {
      setExtracting(false)
    }
  }

  const handleMatch = async () => {
    if (resumeText.trim().length <= 50) {
      setError('Upload your resume PDF or paste resume text first (min 50 characters).')
      return
    }

    setLoading(true)
    setError('')
    try {
      const res = await api.matchJobs({ resume_text: resumeText.trim() })
      setResult(res)
    } catch (err) {
      setError(err.message || 'Job matching failed. Please try again.')
    }
    setLoading(false)
  }

  return (
    <div className="max-w-4xl w-full mx-auto space-y-6 pb-16">
      {/* Header */}
      <div className="max-w-2xl mx-auto text-center space-y-2">
        <Badge sparkle size="sm" className="mx-auto">
          Opportunity Matcher
        </Badge>
        <h1 className="text-3xl font-extrabold text-[#0B0F19] tracking-tight flex items-center justify-center gap-2.5">
          <Briefcase size={26} className="text-[#2563EB]" />
          <span>Jobs You Can Realistically Get</span>
        </h1>
        <p className="text-xs sm:text-sm text-[#64748B]">
          Matched against live market roles based on your verified skills and level.
        </p>
      </div>

      {/* Main Upload & Text Glass Card */}
      <GlassCard className="p-6 sm:p-8 space-y-5 max-w-3xl w-full mx-auto border-white/95 shadow-glass-lg">
        <div>
          <label className="text-xs font-bold text-[#0B0F19] uppercase tracking-wider mb-2 block">
            Resume PDF
          </label>

          {!resumeFile ? (
            <div
              onDrop={(e) => {
                e.preventDefault()
                setDragging(false)
                handleFile(e.dataTransfer.files[0])
              }}
              onDragOver={(e) => {
                e.preventDefault()
                setDragging(true)
              }}
              onDragLeave={() => setDragging(false)}
              onClick={() => fileRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-6 sm:p-8 text-center cursor-pointer transition-all ${
                dragging
                  ? 'border-[#2563EB] bg-blue-50/50'
                  : 'border-slate-200 bg-white/50 hover:border-slate-300 hover:bg-white/80'
              }`}
            >
              <input
                ref={fileRef}
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={(e) => handleFile(e.target.files[0])}
              />
              <div className="w-10 h-10 rounded-xl bg-blue-50 text-[#2563EB] flex items-center justify-center mx-auto mb-2 border border-blue-100">
                <Upload size={20} />
              </div>
              <p className="text-sm font-bold text-[#0B0F19]">Drop PDF or click to browse</p>
              <p className="text-xs text-[#64748B] mt-1">We extract text from the PDF automatically.</p>
            </div>
          ) : (
            <div className="flex items-center gap-3 p-3.5 rounded-xl bg-emerald-50 border border-emerald-200">
              <CheckCircle2 size={18} className="text-[#16A34A]" />
              <span className="text-xs sm:text-sm font-semibold text-[#0B0F19] flex-1 truncate">
                {resumeFile.name}
              </span>
              <button
                type="button"
                onClick={() => {
                  setResumeFile(null)
                  setResumeText('')
                  setError('')
                }}
                className="text-xs font-semibold text-rose-600 hover:underline px-2"
              >
                Remove
              </button>
            </div>
          )}

          {extracting && (
            <div className="flex items-center gap-2 text-[#2563EB] text-xs font-semibold mt-2.5">
              <Loader2 size={14} className="animate-spin" />
              <span>Extracting text from your PDF...</span>
            </div>
          )}
        </div>

        <div>
          <label className="text-xs font-bold text-[#0B0F19] uppercase tracking-wider mb-2 block">
            Resume Text{' '}
            <span className="text-[#64748B] font-normal lowercase">(auto-filled or paste manually)</span>
          </label>
          <textarea
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
            placeholder="Resume text will auto-fill from PDF upload, or paste manually here..."
            rows={5}
            className="w-full p-3.5 rounded-xl bg-white border border-slate-200 text-xs sm:text-sm text-[#0B0F19] placeholder:text-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] resize-none shadow-xs"
          />
          <div className="flex justify-between items-center mt-1.5">
            <span className={`text-[11px] font-semibold ${resumeText.length > 50 ? 'text-[#16A34A]' : 'text-[#64748B]'}`}>
              {resumeText.length > 50 ? `✓ ${resumeText.length} characters ready` : `${resumeText.length} chars`}
            </span>
            {resumeText.length > 0 && (
              <button
                type="button"
                onClick={() => setResumeText('')}
                className="text-[11px] font-semibold text-slate-400 hover:text-rose-600 transition-colors"
              >
                Clear text
              </button>
            )}
          </div>
        </div>

        <Button
          type="button"
          variant="primary"
          size="lg"
          onClick={handleMatch}
          disabled={loading || resumeText.length < 50}
          loading={loading}
          icon={Zap}
          className="w-full"
        >
          {loading ? 'Matching Roles...' : 'Find My Matches'}
        </Button>
      </GlassCard>

      {/* Error Notice */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            className="max-w-3xl mx-auto p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-xs text-[#E11D48] flex items-center gap-2"
          >
            <AlertCircle size={15} className="shrink-0" />
            <span>{error}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results Section */}
      {hasMatchResult && (
        <div className="space-y-4 max-w-3xl mx-auto w-full pt-2">
          {bestFit && (
            <GlassCard className="p-5 border-emerald-200/90 bg-emerald-50/40 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-glass">
              <div className="space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#16A34A] bg-emerald-100/80 px-2 py-0.5 rounded-full border border-emerald-200">
                  Best Match
                </span>
                <h2 className="text-base font-bold text-[#0B0F19] mt-1">
                  {bestFit.job_title}
                </h2>
                <p className="text-xs text-[#475569] leading-relaxed max-w-lg">
                  {bestFit.assessment}
                </p>
              </div>

              {bestFit.apply_link && (
                <a
                  href={bestFit.apply_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="shrink-0"
                >
                  <Button variant="primary" size="sm" trailingIcon={ExternalLink}>
                    View Role
                  </Button>
                </a>
              )}
            </GlassCard>
          )}

          {/* List of Matched Roles */}
          <div className="space-y-3">
            {jobMatches.map((job, i) => {
              const matchScore = Number(job?.match_score) || 0
              const missingSkills = Array.isArray(job?.missing_skills) ? job.missing_skills : []
              const assessment = String(job?.assessment || `${matchScore}% match`)
              const isExpanded = expanded === i

              return (
                <GlassCard
                  key={i}
                  hoverable
                  className="p-4 sm:p-5 cursor-pointer border-white/90 shadow-glass"
                  onClick={() => setExpanded(isExpanded ? null : i)}
                >
                  <div className="flex items-center justify-between gap-3 mb-2.5">
                    <div className="flex items-center gap-2.5">
                      <span className="text-sm font-bold text-[#0B0F19]">
                        {job?.job_title || 'Target Role'}
                      </span>
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                          matchScore >= 75
                            ? 'bg-emerald-50 text-[#16A34A] border-emerald-200'
                            : matchScore >= 50
                            ? 'bg-blue-50 text-[#2563EB] border-blue-200'
                            : 'bg-amber-50 text-[#D97706] border-amber-200'
                        }`}
                      >
                        {matchScore >= 75 ? 'Realistic' : matchScore >= 50 ? 'Close' : 'Target'}
                      </span>
                    </div>

                    <ChevronRight
                      size={15}
                      className={`text-[#94A3B8] transition-transform duration-200 ${
                        isExpanded ? 'rotate-90' : ''
                      }`}
                    />
                  </div>

                  <MatchBar score={matchScore} />
                  <p className="mt-2 text-xs text-[#64748B] leading-relaxed">{assessment}</p>

                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t border-slate-100 space-y-3">
                      {missingSkills.length > 0 && (
                        <div>
                          <p className="text-[11px] font-bold text-[#64748B] uppercase tracking-wider mb-2">
                            Skills to Strengthen
                          </p>
                          <div className="flex flex-wrap gap-1.5">
                            {missingSkills.map((skill, index) => (
                              <span
                                key={index}
                                className="px-2.5 py-0.5 rounded-full bg-slate-100 text-xs font-semibold text-[#0B0F19] border border-slate-200"
                              >
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {job?.apply_link && (
                        <div className="pt-1">
                          <a
                            href={job?.apply_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="inline-flex"
                          >
                            <Button variant="secondary" size="sm" trailingIcon={ExternalLink}>
                              Search Open Roles
                            </Button>
                          </a>
                        </div>
                      )}
                    </div>
                  )}
                </GlassCard>
              )
            })}
          </div>

          <div className="text-center pt-2">
            <button
              type="button"
              onClick={() => setResult(null)}
              className="text-xs font-semibold text-[#2563EB] hover:underline"
            >
              Start New Job Match
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
