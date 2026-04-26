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

const INTEREST_OPTIONS = [
  { label: 'Building websites', emoji: '🌐' },
  { label: 'Working with data', emoji: '📊' },
  { label: 'Artificial Intelligence', emoji: '🤖' },
  { label: 'Mobile apps', emoji: '📱' },
  { label: 'Cybersecurity', emoji: '🔐' },
  { label: 'Cloud & infrastructure', emoji: '☁️' },
  { label: 'Design & creativity', emoji: '🎨' },
  { label: 'Startups & products', emoji: '💡' },
]

// ============================================================
// Skill Selector
// ============================================================

const buttonMotion = {
  whileHover: { scale: 1.03, y: -1 },
  whileTap: { scale: 0.97 },
  transition: { duration: 0.15, ease: 'easeOut' },
}

function SkillSelector({ selected, onToggle }) {
  const [expanded, setExpanded] = useState('Programming')
  return (
    <div className="space-y-3">
      {SKILL_OPTIONS.map(({ category, skills }) => (
        <div key={category} className="glass rounded-xl overflow-hidden">
          <motion.button {...buttonMotion} onClick={() => setExpanded(expanded === category ? null : category)}
            className="w-full flex items-center justify-between p-3 text-sm font-semibold text-[#d6d3d1] hover:text-white transition-colors">
            {category}
            <ChevronRight size={14} className={`transition-transform ${expanded === category ? 'rotate-90' : ''}`} />
          </motion.button>
          <AnimatePresence>
            {expanded === category && (
              <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }}
                className="overflow-hidden">
                <div className="flex flex-wrap gap-2 px-3 pb-3">
                  {skills.map(skill => (
                    <motion.button {...buttonMotion} key={skill} onClick={() => onToggle(skill)}
                      className={`text-xs px-3 py-1.5 rounded-full border transition-all
                        ${selected.includes(skill)
                          ? 'bg-rose-600/20 border-rose-500 text-rose-300'
                          : 'border-white/10 text-[#78716c] hover:border-white/30 hover:text-white'}`}>
                      {selected.includes(skill) && <span className="mr-1">✓</span>}
                      {skill}
                    </motion.button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      ))}
    </div>
  )
}

// ============================================================
// Role Card
// ============================================================

function RoleCard({ role, rank, delay }) {
  const [expanded, setExpanded] = useState(false)
  const matchColor = role.match_score >= 80 ? 'text-green-400' : role.match_score >= 60 ? 'text-rose-400' : 'text-red-400'
  const matchBg = role.match_score >= 80 ? 'bg-green-500/10 border-green-500/20' : role.match_score >= 60 ? 'bg-rose-600/10 border-rose-500/20' : 'bg-red-500/10 border-red-500/20'

  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay }}
      className="glass rounded-2xl overflow-hidden">

      {/* Header */}
      <div className="p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg font-black
              ${rank === 1 ? 'bg-rose-500/20 text-rose-400' : rank === 2 ? 'bg-[#44403c]/30 text-[#d6d3d1]' : 'bg-rose-600/20 text-rose-400'}`}>
              {rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : rank}
            </div>
            <div>
              <h3 className="text-white font-bold text-lg">{role.title}</h3>
              <p className="text-[#78716c] text-xs">{role.category}</p>
            </div>
          </div>
          <div className={`px-3 py-1.5 rounded-xl border text-center ${matchBg}`}>
            <p className={`text-xl font-black ${matchColor}`}>{role.match_score}%</p>
            <p className="text-xs text-[#78716c]">match</p>
          </div>
        </div>

        {/* Match bar */}
        <div className="mt-4 h-1.5 bg-white/5 rounded-full overflow-hidden">
          <motion.div className={`h-full rounded-full ${role.match_score >= 80 ? 'bg-green-500' : role.match_score >= 60 ? 'bg-rose-600' : 'bg-red-500'}`}
            initial={{ width: 0 }} animate={{ width: `${role.match_score}%` }}
            transition={{ duration: 1, delay: delay + 0.2 }} />
        </div>

        <p className="text-[#d6d3d1] text-sm mt-3 leading-relaxed">{role.description}</p>

        {/* Quick stats */}
        <div className="grid grid-cols-3 gap-3 mt-4">
          <div className="p-2 rounded-lg bg-white/5 text-center">
            <p className="text-xs text-[#78716c]">Avg Salary</p>
            <p className="text-xs font-semibold text-white mt-0.5">{role.avg_salary}</p>
          </div>
          <div className="p-2 rounded-lg bg-white/5 text-center">
            <p className="text-xs text-[#78716c]">Demand</p>
            <p className={`text-xs font-semibold mt-0.5 ${role.demand === 'Very High' ? 'text-green-400' : role.demand === 'High' ? 'text-rose-400' : 'text-rose-400'}`}>
              {role.demand}
            </p>
          </div>
          <div className="p-2 rounded-lg bg-white/5 text-center">
            <p className="text-xs text-[#78716c]">Time to Job</p>
            <p className="text-xs font-semibold text-white mt-0.5">{role.time_to_job}</p>
          </div>
        </div>

        <motion.button {...buttonMotion} onClick={() => setExpanded(!expanded)}
          className="mt-4 w-full text-xs text-rose-400 hover:text-rose-300 flex items-center justify-center gap-1 transition-colors">
          {expanded ? 'Show less' : 'See full roadmap & resources'}
          <ChevronRight size={12} className={`transition-transform ${expanded ? 'rotate-90' : ''}`} />
        </motion.button>
      </div>

      {/* Expanded details */}
      <AnimatePresence>
        {expanded && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden border-t border-white/5">
            <div className="p-5 space-y-5">

              {/* Skills you have vs need */}
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <p className="text-xs font-semibold text-green-400 mb-2 uppercase tracking-wide">✓ Skills You Already Have</p>
                  <div className="flex flex-wrap gap-1.5">
                    {role.matching_skills?.map((s, i) => (
                      <span key={i} className="text-xs px-2 py-1 rounded-full bg-green-500/10 text-green-300 border border-green-500/20">{s}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs font-semibold text-red-400 mb-2 uppercase tracking-wide">✗ Skills You Need to Learn</p>
                  <div className="flex flex-wrap gap-1.5">
                    {role.missing_skills?.map((s, i) => (
                      <span key={i} className="text-xs px-2 py-1 rounded-full bg-red-500/10 text-red-300 border border-red-500/20">{s}</span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Learning path */}
              {role.learning_path?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-[#78716c] mb-3 uppercase tracking-wide flex items-center gap-1">
                    <BookOpen size={12} /> Learning Path
                  </p>
                  <div className="space-y-2">
                    {role.learning_path.map((step, i) => (
                      <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-white/5">
                        <div className="w-5 h-5 rounded-full bg-rose-600/20 flex items-center justify-center text-xs text-rose-400 font-bold shrink-0 mt-0.5">
                          {i + 1}
                        </div>
                        <p className="text-sm text-[#d6d3d1]">{step}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Resources */}
              {role.resources?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-[#78716c] mb-3 uppercase tracking-wide">📚 Recommended Resources</p>
                  <div className="space-y-2">
                    {role.resources.map((r, i) => (
                      <a key={i} href={r.url} target="_blank" rel="noopener noreferrer"
                        className="flex items-center gap-3 p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 hover:border-rose-500/30 transition-all group">
                        <span className="text-base">{r.type === 'YouTube' ? '▶️' : r.type === 'Course' ? '🎓' : '🌐'}</span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-white group-hover:text-rose-300 transition-colors truncate">{r.name}</p>
                        </div>
                        <ExternalLink size={12} className="text-[#44403c] group-hover:text-rose-400 shrink-0" />
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* Job sites */}
              <div className="p-3 rounded-xl bg-rose-600/10 border border-rose-500/20">
                <p className="text-xs text-rose-300 font-semibold mb-1">🔍 Where to find {role.title} jobs</p>
                <p className="text-xs text-[#78716c]">{role.job_search_tip}</p>
              </div>

            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

// ============================================================
// Main Component
// ============================================================

export default function CareerRecommendations() {
  const [step, setStep] = useState(1)
  const [selectedSkills, setSelectedSkills] = useState([])
  const [experience, setExperience] = useState('')
  const [interests, setInterests] = useState([])
  const [result, setResult] = useState(null)
  const [githubContext, setGithubContext] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const toggleSkill = (skill) => {
    setSelectedSkills(prev =>
      prev.includes(skill) ? prev.filter(s => s !== skill) : [...prev, skill]
    )
  }

  const toggleInterest = (interest) => {
    setInterests(prev =>
      prev.includes(interest) ? prev.filter(i => i !== interest) : [...prev, interest]
    )
  }

  const handleGenerate = async () => {
    setLoading(true)
    setError('')
    const toastId = toast.loading('Generating career recommendations...')
    try {
      const res = await api.getCareerRecommendations({
        skills: selectedSkills,
        experience,
        interests,
      })
      setResult(res.recommendations)
      setGithubContext(res.github || null)
      toast.success('Recommendations ready!', { id: toastId })
    } catch (err) {
      const msg = err.message || 'Failed to generate recommendations.'
      setError(msg)
      toast.error(msg, { id: toastId })
    }
    setLoading(false)
  }

  const reset = () => {
    setResult(null)
    setStep(1)
    setSelectedSkills([])
    setExperience('')
    setInterests([])
    setGithubContext(null)
  }

  // ── Result Screen ────────────────────────────────────────
  if (result) return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
    <div className="max-w-3xl w-full mx-auto space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Sparkles size={26} className="text-rose-400" /> Your Career Matches
          </h1>
          <p className="text-[#78716c] mt-1">Brutally honest recommendations based primarily on your GitHub evidence</p>
        </div>
        <motion.button {...buttonMotion} onClick={reset} className="btn-ghost flex items-center gap-2 text-sm">
          <RefreshCw size={14} /> Retake
        </motion.button>
      </div>

      {(githubContext || result.github_profile_assessment) && (
        <div className="glass p-4 rounded-2xl border border-rose-500/20 bg-rose-600/10">
          <p className="text-rose-300 text-sm font-semibold mb-1">GitHub Evidence Used</p>
          <p className="text-[#d6d3d1] text-sm">
            @{githubContext?.username || 'unknown'} · {githubContext?.public_repos ?? result.github_profile_assessment?.public_repos ?? 0} repos · {githubContext?.total_stars ?? result.github_profile_assessment?.total_stars ?? 0} stars
          </p>
          {!!(githubContext?.top_languages?.length || result.github_profile_assessment?.top_languages?.length) && (
            <p className="text-[#78716c] text-xs mt-1">
              Top languages: {(githubContext?.top_languages || result.github_profile_assessment?.top_languages || []).join(', ')}
            </p>
          )}
        </div>
      )}

      {/* Summary */}
      {result.summary && (
        <div className="glass p-5 rounded-2xl border border-rose-500/20 bg-rose-500/5">
          <p className="text-[#d6d3d1] text-sm leading-relaxed">
            <span className="text-rose-400 font-semibold">💡 AI Summary: </span>
            {result.summary}
          </p>
        </div>
      )}
      {result.brutal_truth && (
        <div className="glass p-5 rounded-2xl border border-red-500/20 bg-red-500/10">
          <p className="text-red-300 text-sm leading-relaxed">
            <span className="font-semibold text-red-400">Brutal Truth: </span>
            {result.brutal_truth}
          </p>
        </div>
      )}

      {/* Role Cards */}
      <div className="space-y-4">
        {result.roles?.map((role, i) => (
          <RoleCard key={i} role={role} rank={i + 1} delay={i * 0.1} />
        ))}
      </div>

      {/* Next step CTA */}
      <div className="glass p-6 rounded-2xl border border-rose-500/20 bg-rose-600/5 text-center space-y-3">
        <p className="text-white font-bold text-lg">Ready to take action? 🚀</p>
        <p className="text-[#78716c] text-sm">Upload your resume to get a detailed analysis for your top matched role</p>
        <a href="/dashboard/resume" className="btn-primary inline-flex items-center gap-2 px-6 py-3">
          <Briefcase size={16} /> Analyze My Resume
        </a>
      </div>
    </div>
    </motion.div>
  )

  // ── Input Screen ─────────────────────────────────────────
  return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
    <div className="max-w-2xl w-full mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <Sparkles size={26} className="text-rose-400" /> Career Recommendations
        </h1>
        <p className="text-[#78716c] mt-1">
          GitHub-first matching in brutally honest mode. Your GitHub profile is treated as primary evidence.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">{error}</div>
      )}

      {/* Step indicator */}
      <div className="flex gap-2">
        {[1, 2, 3].map(i => (
          <div key={i} className={`h-1.5 flex-1 rounded-full transition-all ${i <= step ? 'bg-rose-600' : 'bg-white/10'}`} />
        ))}
      </div>

      <div className="glass p-6 rounded-2xl space-y-5">
        <AnimatePresence mode="wait">

          {/* Step 1 — Skills */}
          {step === 1 && (
            <motion.div key="s1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
              className="space-y-4">
              <div>
                <h2 className="text-xl font-bold text-white mb-1">What skills do you have?</h2>
                <p className="text-[#78716c] text-sm">Select all that apply — even basic knowledge counts</p>
              </div>
              {selectedSkills.length > 0 && (
                <div className="flex flex-wrap gap-1.5 p-3 rounded-xl bg-rose-600/10 border border-rose-500/20">
                  <span className="text-xs text-rose-400 w-full mb-1">Selected ({selectedSkills.length}):</span>
                  {selectedSkills.map(s => (
                    <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-rose-600/20 text-rose-300">{s}</span>
                  ))}
                </div>
              )}
              <SkillSelector selected={selectedSkills} onToggle={toggleSkill} />
              <motion.button {...buttonMotion} onClick={() => setStep(2)} disabled={selectedSkills.length === 0}
                className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50">
                Continue <ChevronRight size={16} />
              </motion.button>
            </motion.div>
          )}

          {/* Step 2 — Experience */}
          {step === 2 && (
            <motion.div key="s2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
              className="space-y-4">
              <div>
                <h2 className="text-xl font-bold text-white mb-1">What's your experience level?</h2>
                <p className="text-[#78716c] text-sm">Be honest — this helps us give accurate recommendations</p>
              </div>
              <div className="space-y-2">
                {EXPERIENCE_LEVELS.map(({ label, value, emoji }) => (
                  <motion.button {...buttonMotion} key={value} onClick={() => setExperience(value)}
                    className={`w-full p-4 rounded-xl border text-left flex items-center gap-3 transition-all
                      ${experience === value
                        ? 'border-rose-500 bg-rose-600/20 text-[#0a0a0a]'
                        : 'border-white/10 text-[#78716c] hover:border-white/30 hover:text-white'}`}>
                    <span className="text-xl">{emoji}</span>
                    <span className="font-medium text-sm">{label}</span>
                    {experience === value && <CheckCircle size={16} className="ml-auto text-rose-400" />}
                  </motion.button>
                ))}
              </div>
              <div className="flex gap-3">
                <motion.button {...buttonMotion} onClick={() => setStep(1)} className="btn-ghost flex-1">← Back</motion.button>
                <motion.button {...buttonMotion} onClick={() => setStep(3)} disabled={!experience}
                  className="btn-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-50">
                  Continue <ChevronRight size={16} />
                </motion.button>
              </div>
            </motion.div>
          )}

          {/* Step 3 — Interests */}
          {step === 3 && (
            <motion.div key="s3" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
              className="space-y-4">
              <div>
                <h2 className="text-xl font-bold text-white mb-1">What interests you most?</h2>
                <p className="text-[#78716c] text-sm">Pick up to 3 areas you enjoy or want to work in</p>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {INTEREST_OPTIONS.map(({ label, emoji }) => (
                  <motion.button {...buttonMotion} key={label} onClick={() => toggleInterest(label)}
                    className={`p-3 rounded-xl border text-left flex items-center gap-2 transition-all
                      ${interests.includes(label)
                        ? 'border-rose-500 bg-rose-600/20 text-[#0a0a0a]'
                        : 'border-white/10 text-[#78716c] hover:border-white/30 hover:text-white'}`}>
                    <span>{emoji}</span>
                    <span className="text-sm">{label}</span>
                  </motion.button>
                ))}
              </div>

              {/* Summary */}
              {interests.length > 0 && (
                <div className="p-4 rounded-xl bg-rose-600/10 border border-rose-500/20 text-sm space-y-1">
                  <p className="text-rose-300 font-semibold mb-2">📋 Your Profile</p>
                  <p className="text-[#d6d3d1]">🧠 Skills: <span className="text-white">{selectedSkills.slice(0, 4).join(', ')}{selectedSkills.length > 4 ? ` +${selectedSkills.length - 4} more` : ''}</span></p>
                  <p className="text-[#d6d3d1]">📈 Experience: <span className="text-white">{EXPERIENCE_LEVELS.find(e => e.value === experience)?.label}</span></p>
                  <p className="text-[#d6d3d1]">❤️ Interests: <span className="text-white">{interests.join(', ')}</span></p>
                </div>
              )}

              <div className="flex gap-3">
                <motion.button {...buttonMotion} onClick={() => setStep(2)} className="btn-ghost flex-1">← Back</motion.button>
                <motion.button {...buttonMotion} onClick={handleGenerate} disabled={interests.length === 0 || loading}
                  className="btn-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-50 py-4">
                  {loading
                    ? <><Loader2 size={16} className="animate-spin" /> Finding your matches...</>
                    : <><Sparkles size={16} /> Get My Recommendations</>}
                </motion.button>
              </div>
            </motion.div>
          )}

        </AnimatePresence>
      </div>
    </div>
    </motion.div>
  )
}






