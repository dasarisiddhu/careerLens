// ============================================================
// CareerLens – AI Career Recommendations
// File: frontend/src/pages/dashboard/CareerRecommendations.jsx
// ============================================================

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { pageTransition } from '../../utils/animations'
import { api } from '../../services/api'
import toast from 'react-hot-toast'
import {
  Loader2, Sparkles, ChevronRight,
  BookOpen, Briefcase,
  CheckCircle, RefreshCw, ExternalLink
} from 'lucide-react'
import { GlassCard, Badge } from '../../components/ui'

// ============================================================
// Constants
// ============================================================

const SKILL_OPTIONS = [
  { category: 'Programming', skills: ['Python', 'JavaScript', 'Java', 'C++', 'TypeScript', 'Go', 'Rust'] },
  { category: 'Web', skills: ['React', 'Node.js', 'HTML/CSS', 'Vue.js', 'Django', 'FastAPI', 'Next.js'] },
  { category: 'Data & AI', skills: ['Machine Learning', 'Data Analysis', 'TensorFlow', 'SQL', 'Pandas', 'NLP'] },
  { category: 'Cloud & DevOps', skills: ['AWS', 'Docker', 'Kubernetes', 'CI/CD', 'Linux', 'Terraform'] },
  { category: 'Mobile', skills: ['React Native', 'Flutter', 'Android', 'iOS', 'Swift', 'Kotlin'] },
  { category: 'Design', skills: ['Figma', 'UI/UX', 'Prototyping', 'User Research', 'Adobe XD'] },
]

const EXPERIENCE_LEVELS = [
  { label: 'Complete Beginner', value: 'beginner', emoji: '🌱' },
  { label: 'Some Knowledge', value: 'some', emoji: '📚' },
  { label: 'Student / Intern', value: 'student', emoji: '🎓' },
  { label: '1-2 Years Experience', value: 'junior', emoji: '💼' },
  { label: '3+ Years Experience', value: 'mid', emoji: '🚀' },
]

const buttonMotion = {
  whileHover: { scale: 1.015, y: -1 },
  whileTap: { scale: 0.985 },
  transition: { duration: 0.15, ease: 'easeOut' },
}

function SkillSelector({ selected, onToggle }) {
  const [expanded, setExpanded] = useState('Programming')
  return (
    <div className="space-y-2.5">
      {SKILL_OPTIONS.map(({ category, skills }) => (
        <div key={category} className="rounded-xl border border-slate-200 bg-white/70 overflow-hidden">
          <button
            type="button"
            onClick={() => setExpanded(expanded === category ? null : category)}
            className="w-full flex items-center justify-between p-3 text-xs sm:text-sm font-bold text-[#0B0F19] hover:bg-slate-50 transition-colors"
          >
            <span>{category}</span>
            <ChevronRight size={14} className={`text-[#64748B] transition-transform ${expanded === category ? 'rotate-90' : ''}`} />
          </button>
          <AnimatePresence>
            {expanded === category && (
              <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }} className="overflow-hidden">
                <div className="flex flex-wrap gap-1.5 px-3 pb-3 pt-1 border-t border-slate-100">
                  {skills.map((skill) => {
                    const isSelected = selected.includes(skill)
                    return (
                      <button
                        type="button"
                        key={skill}
                        onClick={() => onToggle(skill)}
                        className={`text-xs px-3 py-1.5 rounded-full border transition-all ${
                          isSelected
                            ? 'bg-blue-50 border-[#2563EB] text-[#2563EB] font-bold shadow-xs'
                            : 'border-slate-200 bg-white text-[#475569] hover:border-slate-300 hover:text-[#0B0F19]'
                        }`}
                      >
                        {isSelected && <span className="mr-1">✓</span>}
                        {skill}
                      </button>
                    )
                  })}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      ))}
    </div>
  )
}

function RoleCard({ role, rank, delay }) {
  const [expanded, setExpanded] = useState(false)
  const isHighMatch = role.match_score >= 80

  return (
    <GlassCard className="p-5 sm:p-6 border-white/95 shadow-glass space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-lg font-black shrink-0">
            {rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : rank}
          </div>
          <div>
            <h3 className="text-base sm:text-lg font-bold text-[#0B0F19]">{role.title}</h3>
            <p className="text-xs text-[#64748B]">{role.category}</p>
          </div>
        </div>
        <div className={`px-3 py-1 rounded-xl border text-center ${isHighMatch ? 'bg-emerald-50 border-emerald-200' : 'bg-blue-50 border-blue-200'}`}>
          <p className={`text-base sm:text-lg font-black ${isHighMatch ? 'text-[#16A34A]' : 'text-[#2563EB]'}`}>
            {role.match_score}%
          </p>
          <p className="text-[10px] text-[#64748B] font-semibold uppercase">match</p>
        </div>
      </div>

      {/* Match bar */}
      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${isHighMatch ? 'bg-[#16A34A]' : 'bg-[#2563EB]'}`}
          initial={{ width: 0 }}
          animate={{ width: `${role.match_score}%` }}
          transition={{ duration: 0.8, delay: delay + 0.1 }}
        />
      </div>

      <p className="text-xs sm:text-sm text-[#475569] leading-relaxed">{role.description}</p>

      {/* Quick stats */}
      <div className="grid grid-cols-3 gap-2 pt-1">
        <div className="p-2.5 rounded-xl bg-white border border-slate-200/80 text-center">
          <p className="text-[10px] text-[#64748B] font-semibold uppercase">Avg Salary</p>
          <p className="text-xs font-bold text-[#0B0F19] mt-0.5">{role.avg_salary}</p>
        </div>
        <div className="p-2.5 rounded-xl bg-white border border-slate-200/80 text-center">
          <p className="text-[10px] text-[#64748B] font-semibold uppercase">Demand</p>
          <p className="text-xs font-bold text-[#2563EB] mt-0.5">{role.demand}</p>
        </div>
        <div className="p-2.5 rounded-xl bg-white border border-slate-200/80 text-center">
          <p className="text-[10px] text-[#64748B] font-semibold uppercase">Time to Job</p>
          <p className="text-xs font-bold text-[#0B0F19] mt-0.5">{role.time_to_job}</p>
        </div>
      </div>

      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full text-xs font-bold text-[#2563EB] hover:underline flex items-center justify-center gap-1 pt-1"
      >
        {expanded ? 'Show less' : 'See full roadmap & recommended resources'}
        <ChevronRight size={13} className={`transition-transform ${expanded ? 'rotate-90' : ''}`} />
      </button>

      {/* Expanded details */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden border-t border-slate-100 pt-4 space-y-4"
          >
            <div className="grid sm:grid-cols-2 gap-3">
              <div>
                <p className="text-xs font-bold text-[#16A34A] mb-2 uppercase tracking-wide">✓ Verified Skills</p>
                <div className="flex flex-wrap gap-1.5">
                  {role.matching_skills?.map((s, i) => (
                    <span key={i} className="text-xs px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200/60 font-medium">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-xs font-bold text-[#E11D48] mb-2 uppercase tracking-wide">✗ Skills to Learn</p>
                <div className="flex flex-wrap gap-1.5">
                  {role.missing_skills?.map((s, i) => (
                    <span key={i} className="text-xs px-2.5 py-1 rounded-full bg-rose-50 text-rose-800 border border-rose-200/60 font-medium">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Learning path */}
            {role.learning_path?.length > 0 && (
              <div>
                <p className="text-xs font-bold text-[#0B0F19] mb-2 uppercase tracking-wider flex items-center gap-1.5">
                  <BookOpen size={13} className="text-[#2563EB]" /> Learning Path
                </p>
                <div className="space-y-1.5">
                  {role.learning_path.map((step, i) => (
                    <div key={i} className="flex items-start gap-2.5 p-2.5 rounded-xl bg-white border border-slate-200/60">
                      <div className="w-5 h-5 rounded-full bg-blue-50 text-[#2563EB] flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
                        {i + 1}
                      </div>
                      <p className="text-xs sm:text-sm text-[#475569]">{step}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Resources */}
            {role.resources?.length > 0 && (
              <div>
                <p className="text-xs font-bold text-[#0B0F19] mb-2 uppercase tracking-wider">📚 Recommended Resources</p>
                <div className="space-y-1.5">
                  {role.resources.map((r, i) => (
                    <a
                      key={i}
                      href={r.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2.5 p-2.5 rounded-xl bg-white hover:bg-blue-50/40 border border-slate-200/80 transition-all group"
                    >
                      <span className="text-sm">{r.type === 'YouTube' ? '▶️' : r.type === 'Course' ? '🎓' : '🌐'}</span>
                      <p className="text-xs sm:text-sm font-semibold text-[#0B0F19] group-hover:text-[#2563EB] transition-colors flex-1 truncate">
                        {r.name}
                      </p>
                      <ExternalLink size={12} className="text-[#94A3B8] group-hover:text-[#2563EB]" />
                    </a>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </GlassCard>
  )
}

export default function CareerRecommendations() {
  const [step, setStep] = useState(1)
  const [selectedSkills, setSelectedSkills] = useState([])
  const [experience, setExperience] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [githubContext, setGithubContext] = useState(null)

  const toggleSkill = (skill) => {
    setSelectedSkills((prev) =>
      prev.includes(skill) ? prev.filter((s) => s !== skill) : [...prev, skill]
    )
  }

  const handleSubmit = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.getCareerRecommendations({
        skills: selectedSkills,
        experience_level: experience,
      })
      setResult(res)
      if (res.github_profile_assessment) {
        setGithubContext(res.github_profile_assessment)
      }
    } catch (err) {
      setError(err.message || 'Failed to generate recommendations.')
      toast.error(err.message || 'Failed to generate recommendations.')
    }
    setLoading(false)
  }

  const reset = () => {
    setResult(null)
    setStep(1)
    setSelectedSkills([])
    setExperience('')
    setGithubContext(null)
  }

  // ── Result Screen ────────────────────────────────────────
  if (result) {
    return (
      <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
        <div className="max-w-3xl w-full mx-auto space-y-6 pb-16">
          <div className="flex items-start justify-between gap-4">
            <div>
              <Badge sparkle size="sm" className="mb-1">Verified Matching</Badge>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0B0F19] tracking-tight flex items-center gap-2.5">
                <Sparkles size={24} className="text-[#2563EB]" />
                <span>Your Career Matches</span>
              </h1>
              <p className="text-xs sm:text-sm text-[#64748B] mt-1">
                Recommendations grounded in real skills and your technical footprint.
              </p>
            </div>
            <button
              type="button"
              onClick={reset}
              className="flex items-center gap-1.5 text-xs font-semibold text-[#475569] hover:text-[#0B0F19] px-3.5 py-2 rounded-full border border-slate-200 bg-white/80 shadow-xs"
            >
              <RefreshCw size={13} /> Retake
            </button>
          </div>

          {(githubContext || result.github_profile_assessment) && (
            <GlassCard className="p-4 border-blue-200 bg-blue-50/60">
              <p className="text-xs font-bold text-[#2563EB] uppercase tracking-wider mb-1">GitHub Evidence Used</p>
              <p className="text-xs sm:text-sm font-semibold text-[#0B0F19]">
                @{githubContext?.username || 'user'} · {githubContext?.public_repos ?? result.github_profile_assessment?.public_repos ?? 0} repos · {githubContext?.total_stars ?? result.github_profile_assessment?.total_stars ?? 0} stars
              </p>
              {!!(githubContext?.top_languages?.length || result.github_profile_assessment?.top_languages?.length) && (
                <p className="text-xs text-[#64748B] mt-1">
                  Top languages: {(githubContext?.top_languages || result.github_profile_assessment?.top_languages || []).join(', ')}
                </p>
              )}
            </GlassCard>
          )}

          {/* Summary */}
          {result.summary && (
            <GlassCard className="p-5 border-white/95 shadow-glass">
              <p className="text-xs sm:text-sm text-[#475569] leading-relaxed">
                <strong className="text-[#2563EB]">AI Summary: </strong>
                {result.summary}
              </p>
            </GlassCard>
          )}

          {result.brutal_truth && (
            <GlassCard className="p-5 border-rose-200 bg-rose-50/50">
              <p className="text-xs sm:text-sm text-rose-950 leading-relaxed">
                <strong className="text-[#E11D48]">Direct Assessment: </strong>
                {result.brutal_truth}
              </p>
            </GlassCard>
          )}

          {/* Role Cards */}
          <div className="space-y-4">
            {result.roles?.map((role, i) => (
              <RoleCard key={i} role={role} rank={i + 1} delay={i * 0.08} />
            ))}
          </div>

          {/* Next step CTA */}
          <GlassCard className="p-6 sm:p-8 text-center space-y-3 border-white/95 shadow-glass-lg">
            <h3 className="text-lg font-bold text-[#0B0F19]">Ready to target your best-fit role?</h3>
            <p className="text-xs sm:text-sm text-[#64748B] max-w-md mx-auto">
              Analyze and tune your resume specifically for your top recommendation.
            </p>
            <a
              href="/dashboard/resume"
              className="inline-flex items-center gap-2 py-3 px-6 rounded-full bg-[#0B0F19] text-white font-bold text-xs sm:text-sm hover:bg-[#1E293B] transition-all shadow-md"
            >
              <Briefcase size={15} /> Analyze My Resume
            </a>
          </GlassCard>
        </div>
      </motion.div>
    )
  }

  // ── Input Screen ─────────────────────────────────────────
  return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
      <div className="max-w-2xl w-full mx-auto space-y-6 pb-16">
        <div className="text-center space-y-1.5">
          <Badge sparkle size="sm" className="mx-auto mb-1">Career Intelligence</Badge>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0B0F19] tracking-tight flex items-center justify-center gap-2.5">
            <Sparkles size={24} className="text-[#2563EB]" />
            <span>Career Recommendations</span>
          </h1>
          <p className="text-xs sm:text-sm text-[#64748B]">
            Evidence-backed career path matching tailored to your skills and real code footprint.
          </p>
        </div>

        {error && (
          <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-[#E11D48] text-xs font-semibold">
            {error}
          </div>
        )}

        {/* Step indicator */}
        <div className="flex gap-2">
          {[1, 2].map((i) => (
            <div
              key={i}
              className={`h-1.5 flex-1 rounded-full transition-all ${
                i <= step ? 'bg-[#2563EB]' : 'bg-slate-200'
              }`}
            />
          ))}
        </div>

        <GlassCard className="p-6 sm:p-8 border-white/95 shadow-glass-lg space-y-5">
          <AnimatePresence mode="wait">
            {/* Step 1 — Skills */}
            {step === 1 && (
              <motion.div key="s1" initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -16 }} className="space-y-4">
                <div>
                  <h2 className="text-base sm:text-lg font-bold text-[#0B0F19]">What skills do you have?</h2>
                  <p className="text-xs text-[#64748B] mt-0.5">Select all that apply — even basic familiarity counts.</p>
                </div>
                {selectedSkills.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 p-3 rounded-xl bg-blue-50/80 border border-blue-100">
                    <span className="text-[11px] font-bold text-[#2563EB] w-full mb-0.5">
                      Selected ({selectedSkills.length}):
                    </span>
                    {selectedSkills.map((s) => (
                      <span key={s} className="text-xs px-2.5 py-0.5 rounded-full bg-white text-[#2563EB] border border-blue-200 font-semibold shadow-xs">
                        {s}
                      </span>
                    ))}
                  </div>
                )}
                <SkillSelector selected={selectedSkills} onToggle={toggleSkill} />
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  disabled={selectedSkills.length === 0}
                  className="w-full flex items-center justify-center gap-2 py-3.5 rounded-full bg-[#0B0F19] text-white font-bold text-sm hover:bg-[#1E293B] transition-all shadow-md disabled:opacity-50 mt-2"
                >
                  Continue <ChevronRight size={16} />
                </button>
              </motion.div>
            )}

            {/* Step 2 — Experience */}
            {step === 2 && (
              <motion.div key="s2" initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -16 }} className="space-y-4">
                <div>
                  <h2 className="text-base sm:text-lg font-bold text-[#0B0F19]">What's your experience level?</h2>
                  <p className="text-xs text-[#64748B] mt-0.5">Be honest — this ensures the recommended milestones fit your timeline.</p>
                </div>
                <div className="space-y-2">
                  {EXPERIENCE_LEVELS.map(({ label, value, emoji }) => {
                    const isSelected = experience === value
                    return (
                      <button
                        type="button"
                        key={value}
                        onClick={() => setExperience(value)}
                        className={`w-full p-3.5 rounded-xl border text-left flex items-center gap-3 transition-all ${
                          isSelected
                            ? 'border-[#2563EB] bg-blue-50/80 text-[#0B0F19] font-bold shadow-[0_4px_16px_rgba(37,99,235,0.12)]'
                            : 'border-slate-200 bg-white/70 text-[#475569] hover:border-blue-200 hover:bg-white hover:text-[#0B0F19]'
                        }`}
                      >
                        <span className="text-xl">{emoji}</span>
                        <span className="text-xs sm:text-sm font-semibold flex-1">{label}</span>
                        {isSelected && <CheckCircle size={16} className="text-[#2563EB]" />}
                      </button>
                    )
                  })}
                </div>
                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setStep(1)}
                    className="flex-1 py-3 rounded-full border border-slate-200 bg-white/80 text-[#0B0F19] font-bold text-sm hover:bg-white transition-all"
                  >
                    ← Back
                  </button>
                  <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={!experience || loading}
                    className="flex-1 flex items-center justify-center gap-2 py-3 rounded-full bg-[#0B0F19] text-white font-bold text-sm hover:bg-[#1E293B] transition-all shadow-md disabled:opacity-50"
                  >
                    {loading ? (
                      <>
                        <Loader2 size={16} className="animate-spin" /> Matching roles...
                      </>
                    ) : (
                      <>
                        <Sparkles size={16} /> Get Recommendations
                      </>
                    )}
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </GlassCard>
      </div>
    </motion.div>
  )
}
