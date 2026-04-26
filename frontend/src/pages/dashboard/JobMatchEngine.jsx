import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { api } from '../../services/api'
import {
  Loader2, Briefcase, ExternalLink, XCircle, Zap, ChevronRight,
  Upload, CheckCircle,
} from 'lucide-react'

function MatchBar({ score }) {
  const color = score >= 70 ? 'bg-green-500' : score >= 50 ? 'bg-[#FF8C42]' : score >= 35 ? 'bg-[#FF3B3B]' : 'bg-[#8B0000]'
  const text = score >= 70 ? 'text-green-400' : score >= 50 ? 'text-[#FF8C42]' : score >= 35 ? 'text-[#FF7070]' : 'text-[#8B0000]'

  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 1, ease: 'easeOut' }}
        />
      </div>
      <span className={`text-sm font-bold w-12 text-right ${text}`}>{score}%</span>
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
    const saved = localStorage.getItem('careerlens_resume_text')
    if (saved && saved.trim().length > 50) {
      setResumeText(saved.trim())
      localStorage.removeItem('careerlens_resume_text')
    }
  }, [])

  useEffect(() => {
    if (initialResumeText) setResumeText(initialResumeText)
  }, [initialResumeText])

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
          'Could not extract text automatically. ' +
          'Please paste your resume text below.'
        )
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
      setError('Upload your resume PDF or paste resume text first.')
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
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }} className="max-w-4xl w-full mx-auto space-y-6">
      <div className="max-w-2xl mx-auto text-center">
        <h1 className="gradient-text text-3xl font-bold flex items-center justify-center gap-2">
          <Briefcase size={22} className="text-[#FF3B3B]" /> Jobs You Can Realistically Get
        </h1>
        <p className="text-[#8A8FA8] text-sm mt-2">Matched against real roles based on your current skills</p>
      </div>

      <div className="glass-glow p-6 rounded-3xl space-y-5 max-w-3xl w-full mx-auto">
        <div>
          <label className="text-xs font-semibold text-[#8A8FA8] uppercase tracking-wide mb-2 block">Resume PDF</label>
          {!resumeFile ? (
            <div
              onDrop={(e) => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0]) }}
              onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              onClick={() => fileRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all
                ${dragging ? 'border-[#FF3B3B] bg-red-500/10 shadow-[0_0_30px_rgba(255,59,59,0.1)]' : 'border-white/10 bg-white/[0.02] hover:border-[rgba(255,59,59,0.28)] hover:bg-red-500/5'}`}
            >
              <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={(e) => handleFile(e.target.files[0])} />
              <Upload size={24} className="float text-[#FF7070] mx-auto mb-2" />
              <p className="text-[#F5F5F7] text-sm">Drop PDF or click to upload</p>
            </div>
          ) : (
            <div className="flex items-center gap-3 p-3 rounded-xl bg-green-500/10 border border-green-500/20">
              <CheckCircle size={16} className="text-green-400" />
              <span className="text-sm text-white flex-1 truncate">{resumeFile.name}</span>
              <button
                onClick={() => { setResumeFile(null); setResumeText(''); setError('') }}
                className="text-[#8A8FA8] hover:text-white text-xs"
              >
                Remove
              </button>
            </div>
          )}
          <p className="text-xs text-[#8A8FA8] mt-2">We extract text from the PDF and match it against realistic roles.</p>
          {extracting && (
            <div className="flex items-center gap-2 text-[#FF7070] text-sm mt-2">
              <Loader2 size={14} className="animate-spin" /> Extracting text from your PDF...
            </div>
          )}
        </div>

        <div>
          <label className="text-xs font-semibold text-[#8A8FA8] uppercase tracking-wide mb-2 block">
            RESUME TEXT{' '}
            <span className="text-[#8A8FA8]/70 font-normal">(auto-filled from PDF or paste manually)</span>
          </label>
          <textarea
            value={resumeText}
            onChange={e => setResumeText(e.target.value)}
            placeholder="Resume text will auto-fill from PDF upload, or paste manually here..."
            rows={6}
            className={`input-field resize-none w-full text-sm transition-all ${
              resumeText.length > 100 ? 'border-green-500/50 bg-green-500/5' : ''
            }`}
          />
          <div className="flex justify-between items-center mt-1">
            <span className={`text-xs ${resumeText.length > 100 ? 'text-green-400' : 'text-[#8A8FA8]/70'}`}>
              {resumeText.length > 100 ? `✓ ${resumeText.length} chars ready` : `${resumeText.length} chars`}
            </span>
            {resumeText.length > 0 && (
              <button onClick={() => setResumeText('')}
                className="text-xs text-[#8A8FA8]/70 hover:text-red-400 transition-colors">
                Clear
              </button>
            )}
          </div>
        </div>

        <button
          onClick={handleMatch}
          disabled={loading || resumeText.length < 50}
          className="btn-primary flex items-center justify-center gap-2 w-full disabled:opacity-50"
        >
          {loading
            ? <><Loader2 size={16} className="animate-spin" /> Matching roles...</>
            : <><Zap size={16} /> Find My Matches</>}
        </button>
      </div>

      {error && (
        <div className="max-w-3xl mx-auto p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}

      {hasMatchResult && (
        <div className="space-y-3 max-w-4xl mx-auto w-full">
          {bestFit && (
            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
              className={`p-4 rounded-2xl flex items-center gap-3 ${bestFit.realistic ? 'bg-green-500/10 border border-green-500/20' : 'bg-red-500/10 border border-red-500/20'}`}>
              <span className="text-2xl">🎯</span>
              <div className="flex-1">
                <p className={`font-bold text-sm ${bestFit.realistic ? 'text-green-300' : 'text-red-300'}`}>Best Match: {bestFit.job_title}</p>
                <p className="text-[#8A8FA8] text-xs">
                  {bestFit.assessment}
                </p>
              </div>
              <a href={bestFit.apply_link} target="_blank" rel="noopener noreferrer"
                className="btn-primary text-xs px-4 py-2 flex items-center gap-1.5">
                View Role <ExternalLink size={11} />
              </a>
            </motion.div>
          )}

          <div className="space-y-2">
            {jobMatches.map((job, i) => {
              const matchScore = Number(job?.match_score) || 0
              const missingSkills = Array.isArray(job?.missing_skills) ? job.missing_skills : []
              const assessment = String(job?.assessment || `${matchScore}% match`)

              return (
                <motion.div key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className={`glass-glow rounded-xl border transition-all cursor-pointer
                  ${expanded === i ? 'border-[rgba(255,59,59,0.3)]' : 'border-white/5 hover:border-[rgba(255,59,59,0.22)]'}`}
                  onClick={() => setExpanded(expanded === i ? null : i)}>
                  <div className="p-4">
                    <div className="flex items-center justify-between gap-3 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-white font-semibold text-sm">{job?.job_title || 'Job Match'}</span>
                        <span className={`px-2 py-0.5 rounded-full text-[10px] normal-case tracking-normal border ${
                          matchScore >= 85
                            ? 'bg-green-500/10 border-green-500/20 text-green-300'
                            : matchScore >= 70
                              ? 'bg-white/5 border-white/10 text-[#d6d3d1]'
                              : 'bg-red-500/10 border-red-500/20 text-red-300'
                        }`}>
                          {matchScore >= 85 ? 'Realistic' : matchScore >= 70 ? 'Close' : 'Underqualified'}
                        </span>
                      </div>
                      <ChevronRight size={14} className={`text-[#8A8FA8] transition-transform ${expanded === i ? 'rotate-90' : ''}`} />
                    </div>
                    <MatchBar score={matchScore} />
                    <p className="mt-2 text-xs text-[#8A8FA8]">{assessment}</p>
                  </div>

                  {expanded === i && (
                    <div className="px-4 pb-4 space-y-3 border-t border-white/5 pt-3">
                      {missingSkills.length > 0 && (
                        <div>
                          <p className="text-xs text-[#8A8FA8] mb-2 flex items-center gap-1">
                            <XCircle size={11} className="text-red-400" /> Skills you need:
                          </p>
                          <div className="flex flex-wrap gap-1.5">
                            {missingSkills.map((skill, index) => (
                              <span key={index} className="badge badge-red px-2 py-0.5 text-[10px] normal-case tracking-normal">
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      <a href={job?.apply_link} target="_blank" rel="noopener noreferrer"
                        className="btn-primary text-xs px-4 py-2 flex items-center gap-1.5 w-fit">
                        View Jobs <ExternalLink size={11} />
                      </a>
                    </div>
                  )}
                </motion.div>
              )
            })}
          </div>

          <button onClick={() => setResult(null)}
            className="text-xs text-[#8A8FA8] hover:text-white transition-colors mx-auto block">
            Refresh matches
          </button>
        </div>
      )}
    </motion.div>
  )
}
