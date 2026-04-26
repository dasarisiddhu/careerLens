import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import {
  BarChart2,
  Brain,
  Building2,
  CheckCircle2,
  ChevronRight,
  Code2,
  Copy,
  Check,
  Loader2,
  MessageSquare,
  Mic,
  MicOff,
  Play,
  RefreshCw,
  Send,
  Sparkles,
  Star,
  Terminal,
  Trophy,
  Users,
  Volume2,
  Wrench,
  Zap,
} from 'lucide-react'
import { api } from '../../services/api'
import { pageTransition, staggerContainer, staggerItem, useAnimatedCircle } from '../../utils/animations'

// ─── Roles ────────────────────────────────────────────────────────────────────
const ROLES = [
  'Frontend Developer',
  'Backend Developer',
  'Full Stack Engineer',
  'Mobile Developer (iOS)',
  'Mobile Developer (Android)',
  'React Native Developer',
  'Data Scientist',
  'ML Engineer',
  'AI/LLM Engineer',
  'Data Analyst',
  'Data Engineer',
  'Business Intelligence Developer',
  'DevOps Engineer',
  'Cloud Engineer',
  'Site Reliability Engineer',
  'Platform Engineer',
  'Security Engineer',
  'Software Architect',
  'Engineering Manager',
  'Tech Lead',
  'Product Manager',
  'UI/UX Designer',
  'Product Designer',
  'Growth Product Manager',
  'QA Engineer',
  'Blockchain Developer',
  'Embedded Systems Engineer',
]

// ─── Companies ────────────────────────────────────────────────────────────────
// icon: Simple Icons slug (https://simpleicons.org) — renders as white SVG on brand color bg
// color: brand background color for the icon tile
const COMPANIES = [
  // ── General ──
  { value: 'general',     label: 'Any Company',   icon: null,             color: '#1e2030', tag: 'General prep' },
  // ── Big Tech ──
  { value: 'google',      label: 'Google',         icon: 'google',         color: '#4285F4', tag: 'Algorithms + System Design' },
  { value: 'amazon',      label: 'Amazon',         icon: 'amazon',         color: '#FF9900', tag: '16 Leadership Principles' },
  { value: 'microsoft',   label: 'Microsoft',      icon: 'microsoft',      color: '#00A4EF', tag: 'Growth Mindset + Collab' },
  { value: 'meta',        label: 'Meta',           icon: 'meta',           color: '#0081FB', tag: 'Product Sense + Impact' },
  { value: 'apple',       label: 'Apple',          icon: 'apple',          color: '#555555', tag: 'Deep Technical + Craft' },
  { value: 'netflix',     label: 'Netflix',        icon: 'netflix',        color: '#E50914', tag: 'Culture + Distributed Systems' },
  { value: 'uber',        label: 'Uber',           icon: 'uber',           color: '#276EF1', tag: 'Real-time + Geo Systems' },
  { value: 'stripe',      label: 'Stripe',         icon: 'stripe',         color: '#635BFF', tag: 'Payments + Correctness' },
  // ── AI Companies ──
  { value: 'openai',      label: 'OpenAI',         icon: 'openai',         color: '#412991', tag: 'LLMs + Safety + PyTorch' },
  { value: 'anthropic',   label: 'Anthropic',      icon: 'anthropic',      color: '#c96442', tag: 'AI Safety + Alignment' },
  { value: 'xai',         label: 'xAI',            icon: 'x',              color: '#000000', tag: 'First Principles + Frontier' },
  { value: 'deepmind',    label: 'DeepMind',       icon: 'googledeepmind', color: '#4285F4', tag: 'RL + Research Engineering' },
  { value: 'mistral',     label: 'Mistral AI',     icon: 'mistral',        color: '#FF7000', tag: 'Efficient LLMs + MoE' },
  { value: 'cohere',      label: 'Cohere',         icon: 'cohere',         color: '#39594D', tag: 'Enterprise RAG + Embeddings' },
  { value: 'huggingface', label: 'Hugging Face',   icon: 'huggingface',    color: '#FFD21E', tag: 'Open-Source ML Tooling' },
  // ── Indian Tech ──
  { value: 'flipkart',    label: 'Flipkart',       icon: 'flipkart',       color: '#2874F0', tag: 'E-Commerce at India Scale' },
  { value: 'swiggy',      label: 'Swiggy',         icon: 'swiggy',         color: '#FC8019', tag: 'Hyperlocal Delivery Tech' },
  { value: 'zomato',      label: 'Zomato',         icon: 'zomato',         color: '#E23744', tag: 'Food Tech + Ship Fast' },
  { value: 'infosys',     label: 'Infosys',        icon: 'infosys',        color: '#007CC3', tag: 'Core CS + Client Skills' },
  { value: 'tcs',         label: 'TCS',            icon: null,             color: '#0033A0', tag: 'Fundamentals + Communication' },
  // ── Other ──
  { value: 'startup',     label: 'Startup',        icon: null,             color: '#7c3aed', tag: 'Ownership + Full Stack' },
]

// ─── CompanyLogo component ─────────────────────────────────────────────────────
// White icon from Simple Icons CDN on a brand-colored rounded tile.
function CompanyLogo({ company, size = 32 }) {
  const [imgError, setImgError] = useState(false)

  const radius = Math.round(size * 0.28)
  const containerStyle = {
    width: size, height: size, minWidth: size,
    borderRadius: radius,
    background: company.color,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    overflow: 'hidden',
    boxShadow: `0 2px 10px ${company.color}66`,
    flexShrink: 0,
  }
  const iconSize = Math.round(size * 0.56)

  if (company.value === 'startup') {
    return <span style={containerStyle}><span style={{ fontSize: iconSize * 0.9, lineHeight: 1 }}>🚀</span></span>
  }
  if (company.value === 'general') {
    return <span style={containerStyle}><span style={{ fontSize: iconSize * 0.9, lineHeight: 1 }}>🌐</span></span>
  }
  if (company.value === 'tcs') {
    return (
      <span style={containerStyle}>
        <span style={{ color: '#fff', fontWeight: 900, fontSize: size * 0.32, lineHeight: 1, letterSpacing: '-0.5px' }}>TCS</span>
      </span>
    )
  }
  // Hugging Face icon is yellow on yellow — use dark icon variant instead
  const iconColor = company.value === 'huggingface' ? '111111' : 'ffffff'
  if (company.icon && !imgError) {
    return (
      <span style={containerStyle}>
        <img
          src={`https://cdn.simpleicons.org/${company.icon}/${iconColor}`}
          alt={company.label}
          width={iconSize}
          height={iconSize}
          onError={() => setImgError(true)}
          style={{ objectFit: 'contain', display: 'block', width: iconSize, height: iconSize }}
        />
      </span>
    )
  }
  // Final fallback: bold initial
  return (
    <span style={containerStyle}>
      <span style={{ color: '#fff', fontWeight: 800, fontSize: size * 0.44, lineHeight: 1 }}>
        {company.label[0]}
      </span>
    </span>
  )
}

// ─── CodeBlock component ───────────────────────────────────────────────────────
function CodeBlock({ code, language = 'python' }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  // Simple keyword highlight without external deps
  const highlighted = (code || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // strings
    .replace(/(["'`])(.*?)\1/g, '<span style="color:#a5f3fc">$1$2$1</span>')
    // comments
    .replace(/(#[^\n]*|\/\/[^\n]*)/g, '<span style="color:#6b7280;font-style:italic">$1</span>')
    // keywords
    .replace(
      /\b(def|return|if|else|elif|for|while|in|not|and|or|import|from|class|try|except|raise|with|as|pass|None|True|False|null|undefined|const|let|var|function|async|await|throw|catch|new|this|self|super|break|continue|yield)\b/g,
      '<span style="color:#f472b6">$1</span>',
    )
    // numbers
    .replace(/\b(\d+\.?\d*)\b/g, '<span style="color:#fb923c">$1</span>')
    // function names
    .replace(/\b([a-zA-Z_]\w*)\s*(?=\()/g, '<span style="color:#60a5fa">$1</span>')

  return (
    <div className="overflow-hidden rounded-[18px] border border-[rgba(255,255,255,0.08)] bg-[#0d0f14]">
      {/* Header bar */}
      <div className="flex items-center justify-between border-b border-[rgba(255,255,255,0.06)] px-4 py-2">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <span className="h-3 w-3 rounded-full bg-[#FF3B3B]" />
            <span className="h-3 w-3 rounded-full bg-[#fb923c]" />
            <span className="h-3 w-3 rounded-full bg-[#10b981]" />
          </div>
          <span className="text-[11px] font-medium text-[rgba(138,143,168,0.6)] uppercase tracking-widest ml-2">
            {language}
          </span>
        </div>
        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[11px] font-medium text-[rgba(138,143,168,0.7)] transition-all hover:bg-[rgba(255,255,255,0.06)] hover:text-white"
        >
          {copied ? <><Check size={12} className="text-[#10b981]" />Copied!</> : <><Copy size={12} />Copy</>}
        </button>
      </div>
      {/* Code */}
      <pre
        className="overflow-x-auto p-4 text-[13px] leading-6"
        style={{ fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace" }}
        // eslint-disable-next-line react/no-danger
        dangerouslySetInnerHTML={{ __html: highlighted }}
      />
    </div>
  )
}

// ─── Style helpers ─────────────────────────────────────────────────────────────
const DIFFICULTY_STYLES = {
  easy:   'badge badge-green',
  medium: 'badge badge-red',
  hard:   'badge badge-red',
}

const CATEGORY_META = {
  technical:      { icon: Code2,    label: 'Technical',       color: '#FF7070' },
  behavioral:     { icon: Users,    label: 'Behavioral',      color: '#60a5fa' },
  situational:    { icon: Brain,    label: 'Situational',     color: '#a78bfa' },
  code_fix:       { icon: Wrench,   label: 'Fix The Bug',     color: '#fb923c' },
  code_write:     { icon: Terminal, label: 'Write Code',      color: '#10b981' },
  debugging:      { icon: Terminal, label: 'Debug This',      color: '#fb923c' },
  error_handling: { icon: Zap,      label: 'Error Handling',  color: '#f59e0b' },
}

const CODING_CATEGORIES = new Set(['code_fix', 'code_write', 'debugging', 'error_handling'])

const SCORE_COLORS = {
  good: '#10b981',
  mid:  '#fb7185',
  low:  '#FF3B3B',
}

// ─── Utilities ─────────────────────────────────────────────────────────────────
const speak = (text) => {
  if (!window.speechSynthesis) return
  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.rate = 0.95
  utterance.pitch = 1
  window.speechSynthesis.speak(utterance)
}

function getScoreTone(score) {
  if (score >= 75) return SCORE_COLORS.good
  if (score >= 50) return SCORE_COLORS.mid
  return SCORE_COLORS.low
}

function getRecommendationMeta(recommendation) {
  const value = recommendation?.toLowerCase?.() || ''
  if (value.includes('strong yes'))  return { label: 'Strong Hire 🔥', className: 'badge badge-green' }
  if (value.includes('yes'))         return { label: 'Would Hire ✅',  className: 'badge badge-green' }
  if (value.includes('maybe'))       return { label: 'Borderline',     className: 'badge badge-red' }
  if (value.includes('strong no'))   return { label: 'Not Ready ❌',   className: 'badge badge-red' }
  return                                    { label: 'Not Yet',        className: 'badge badge-red' }
}

function getCompanyMeta(companyValue) {
  return COMPANIES.find((c) => c.value === companyValue) || COMPANIES[0]
}

// ─── Platform URL lookup (client-side fallback for resources without URLs) ─────
const PLATFORM_URLS = {
  'leetcode':                   'https://leetcode.com/',
  'neetcode':                   'https://neetcode.io/',
  'hackerrank':                 'https://www.hackerrank.com/',
  'codewars':                   'https://www.codewars.com/',
  'codecademy':                 'https://www.codecademy.com/',
  'freecodecamp':               'https://www.freecodecamp.org/',
  'udemy':                      'https://www.udemy.com/',
  'coursera':                   'https://www.coursera.org/',
  'edx':                        'https://www.edx.org/',
  'pluralsight':                'https://www.pluralsight.com/',
  'linkedin learning':          'https://www.linkedin.com/learning/',
  'udacity':                    'https://www.udacity.com/',
  'mit opencourseware':         'https://ocw.mit.edu/',
  'khan academy':               'https://www.khanacademy.org/',
  'system design primer':       'https://github.com/donnemartin/system-design-primer',
  'bytebytego':                 'https://bytebytego.com/',
  'cracking the coding':        'https://www.crackingthecodinginterview.com/',
  'fast.ai':                    'https://www.fast.ai/',
  'hugging face':               'https://huggingface.co/learn/',
  'roadmap.sh':                 'https://roadmap.sh/',
  'pramp':                      'https://www.pramp.com/',
  'interviewing.io':            'https://interviewing.io/',
  'visualgo':                   'https://visualgo.net/',
  'refactoring.guru':           'https://refactoring.guru/',
  'cs50':                       'https://cs50.harvard.edu/x/',
  'sqlzoo':                     'https://sqlzoo.net/',
  'karpathy':                   'https://karpathy.ai/zero-to-hero.html',
  'madewithml':                 'https://madewithml.com/',
  'exponent':                   'https://www.tryexponent.com/',
  'dev.to':                     'https://dev.to/',
  'github':                     'https://github.com/',
  'stackoverflow':              'https://stackoverflow.com/',
}

function resolveResourceUrl(resourceStr) {
  const s = String(resourceStr || '').trim()
  // 1. Try to find an embedded URL
  const urlMatch = s.match(/https?:\/\/[^\s"')]+/)
  if (urlMatch) {
    const url = urlMatch[0].replace(/[.,;)]+$/, '')
    const title = s.slice(0, s.indexOf(urlMatch[0])).replace(/[\s→\-–—]+$/, '').trim()
    return { title: title || url.replace(/^https?:\/\/(www\.)?/, '').split('/')[0], url }
  }
  // 2. Clean the string and look up by platform name
  const clean = s.replace(/[\-–—→]+/g, ' ').replace(/^[^:]+:\s*/, '').trim()
  const lower = clean.toLowerCase()
  for (const [platform, url] of Object.entries(PLATFORM_URLS)) {
    if (lower.includes(platform)) {
      return { title: clean || platform, url }
    }
  }
  // 3. No URL found
  return { title: clean || s, url: null }
}
function ScoreCircle({ score, label, size = 108, showScale = false, highlight = false }) {
  const strokeWidth = highlight ? 10 : 8
  const color = getScoreTone(score)
  const { radius, circumference, offset } = useAnimatedCircle(score, 100, size, strokeWidth)

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        <div
          className="absolute rounded-full"
          style={{
            width: size - 6,
            height: size - 6,
            border: `1px solid ${color}22`,
            boxShadow: `0 0 22px ${color}20`,
          }}
        />
        <div
          className="absolute rounded-full"
          style={{ width: size - 20, height: size - 20, border: `1px solid ${color}18` }}
        />
        <svg width={size} height={size} className="-rotate-90">
          <circle cx={size/2} cy={size/2} r={radius} stroke="rgba(255,255,255,0.08)" strokeWidth={strokeWidth} fill="none" />
          <circle
            cx={size/2} cy={size/2} r={radius}
            stroke={color} strokeWidth={strokeWidth} fill="none"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ filter: `drop-shadow(0 0 10px ${color}80)` }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className={`font-black leading-none ${highlight ? 'text-3xl' : 'text-xl'} ${
              score >= 75 && highlight ? 'gradient-text' : ''
            }`}
            style={score >= 75 && highlight ? undefined : { color }}
          >
            {score}
          </span>
          {showScale && <span className="mt-1 text-[11px] text-[rgba(138,143,168,0.7)]">/100</span>}
        </div>
      </div>
      <span className="text-xs uppercase tracking-[0.18em] text-[rgba(138,143,168,0.75)]">{label}</span>
    </div>
  )
}

// ─── SetupPhase ────────────────────────────────────────────────────────────────
function SetupPhase({ onStart }) {
  const [config, setConfig] = useState({
    job_role: 'Full Stack Engineer',
    company: 'general',
    mode: 'text',
  })
  const [loading, setLoading]   = useState(false)
  const voiceSupported =
    typeof window !== 'undefined' && !!(window.SpeechRecognition || window.webkitSpeechRecognition)

  const handleStart = async () => {
    setLoading(true)
    await onStart(config)
    setLoading(false)
  }

  const selectedCompany = getCompanyMeta(config.company)

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <div className="space-y-3">
        <span className="badge badge-red">Mock Interview</span>
        <h1 className="gradient-text text-4xl font-black tracking-tight">Interview like it counts.</h1>
        <p className="max-w-xl text-sm leading-7 text-[rgba(138,143,168,0.8)]">
          Pick a target company, choose your role, and get questions tailored to how that company
          actually interviews — powered by real interview culture profiles.
        </p>
      </div>

      <motion.div
        whileHover={{ y: -3 }}
        className="glass-glow overflow-hidden rounded-[28px] border-t-2 border-t-[rgba(255,59,59,0.4)] p-8"
        style={{ boxShadow: '0 25px 60px rgba(0,0,0,0.35), 0 0 40px rgba(255,59,59,0.06)' }}
      >
        <div className="absolute inset-x-0 top-0 h-24 bg-[radial-gradient(circle_at_top,rgba(255,59,59,0.12),transparent_70%)] pointer-events-none" />

        <div className="relative space-y-7">

          {/* ── Company selector ── */}
          <div>
            <label className="mb-3 block text-sm font-medium text-[rgba(245,245,247,0.92)]">
              Target Company
            </label>

            {/* Section: Big Tech */}
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-[rgba(138,143,168,0.5)]">Big Tech</p>
            <div className="grid grid-cols-5 gap-2 sm:grid-cols-5 mb-4">
              {COMPANIES.filter(c => ['general','google','amazon','microsoft','meta','apple','netflix','uber','stripe'].includes(c.value)).map((co) => {
                const isActive = config.company === co.value
                return (
                  <button
                    key={co.value}
                    type="button"
                    onClick={() => setConfig((c) => ({ ...c, company: co.value }))}
                    className={`flex flex-col items-center gap-2 rounded-2xl border px-2 py-3 text-center transition-all ${
                      isActive
                        ? 'border-[rgba(255,59,59,0.3)] bg-[rgba(255,59,59,0.1)] text-white shadow-[0_0_18px_rgba(255,59,59,0.12)]'
                        : 'border-[rgba(255,255,255,0.07)] bg-[rgba(255,255,255,0.02)] text-[rgba(138,143,168,0.85)] hover:border-[rgba(255,59,59,0.18)] hover:bg-[rgba(255,255,255,0.04)] hover:text-white'
                    }`}
                  >
                    <CompanyLogo company={co} size={34} />
                    <span className="text-[11px] font-medium leading-tight">{co.label}</span>
                  </button>
                )
              })}
            </div>

            {/* Section: AI Companies */}
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-[rgba(138,143,168,0.5)]">AI Labs</p>
            <div className="grid grid-cols-4 gap-2 sm:grid-cols-7 mb-4">
              {COMPANIES.filter(c => ['openai','anthropic','xai','deepmind','mistral','cohere','huggingface'].includes(c.value)).map((co) => {
                const isActive = config.company === co.value
                return (
                  <button
                    key={co.value}
                    type="button"
                    onClick={() => setConfig((c) => ({ ...c, company: co.value }))}
                    className={`flex flex-col items-center gap-2 rounded-2xl border px-2 py-3 text-center transition-all ${
                      isActive
                        ? 'border-[rgba(255,59,59,0.3)] bg-[rgba(255,59,59,0.1)] text-white shadow-[0_0_18px_rgba(255,59,59,0.12)]'
                        : 'border-[rgba(255,255,255,0.07)] bg-[rgba(255,255,255,0.02)] text-[rgba(138,143,168,0.85)] hover:border-[rgba(255,59,59,0.18)] hover:bg-[rgba(255,255,255,0.04)] hover:text-white'
                    }`}
                  >
                    <CompanyLogo company={co} size={34} />
                    <span className="text-[11px] font-medium leading-tight">{co.label}</span>
                  </button>
                )
              })}
            </div>

            {/* Section: Indian Tech + Other */}
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-[rgba(138,143,168,0.5)]">Indian Tech &amp; Other</p>
            <div className="grid grid-cols-5 gap-2 sm:grid-cols-5">
              {COMPANIES.filter(c => ['flipkart','swiggy','zomato','infosys','tcs','startup'].includes(c.value)).map((co) => {
                const isActive = config.company === co.value
                return (
                  <button
                    key={co.value}
                    type="button"
                    onClick={() => setConfig((c) => ({ ...c, company: co.value }))}
                    className={`flex flex-col items-center gap-2 rounded-2xl border px-2 py-3 text-center transition-all ${
                      isActive
                        ? 'border-[rgba(255,59,59,0.3)] bg-[rgba(255,59,59,0.1)] text-white shadow-[0_0_18px_rgba(255,59,59,0.12)]'
                        : 'border-[rgba(255,255,255,0.07)] bg-[rgba(255,255,255,0.02)] text-[rgba(138,143,168,0.85)] hover:border-[rgba(255,59,59,0.18)] hover:bg-[rgba(255,255,255,0.04)] hover:text-white'
                    }`}
                  >
                    <CompanyLogo company={co} size={34} />
                    <span className="text-[11px] font-medium leading-tight">{co.label}</span>
                  </button>
                )
              })}
            </div>

            {/* Company focus pill */}
            {selectedCompany.value !== 'general' && (
              <div className="mt-3 inline-flex items-center gap-2 rounded-full border border-[rgba(255,59,59,0.2)] bg-[rgba(255,59,59,0.08)] px-3 py-1.5">
                <Sparkles size={12} className="text-[#FF7070]" />
                <span className="text-xs text-[#FF7070]">
                  {selectedCompany.label} focuses on: <strong>{selectedCompany.tag}</strong>
                </span>
              </div>
            )}
          </div>

          <div className="grid gap-6 md:grid-cols-[1.25fr_0.75fr]">
            <div className="space-y-5">
              {/* ── Role selector ── */}
              <div>
                <label className="mb-2 block text-sm font-medium text-[rgba(245,245,247,0.92)]">
                  Job Role
                </label>
                <select
                  value={config.job_role}
                  onChange={(e) => setConfig((c) => ({ ...c, job_role: e.target.value }))}
                  className="input-field"
                  style={{ background: '#11131A', colorScheme: 'dark' }}
                >
                  {ROLES.map((role) => (
                    <option key={role} value={role}>{role}</option>
                  ))}
                </select>
              </div>

              {/* ── Mode selector ── */}
              <div>
                <label className="mb-3 block text-sm font-medium text-[rgba(245,245,247,0.92)]">
                  Interview Mode
                </label>
                <div className="grid gap-3 sm:grid-cols-2">
                  {[
                    { mode: 'text',  icon: Send, label: 'Text Mode',  description: 'Type your answers and move quickly through the session.' },
                    { mode: 'voice', icon: Mic,  label: 'Voice Mode', description: 'Practice speaking your answers out loud with live transcription.' },
                  ].map(({ mode, icon: Icon, label, description }) => {
                    const isActive  = config.mode === mode
                    const disabled  = mode === 'voice' && !voiceSupported
                    return (
                      <button
                        key={mode}
                        type="button"
                        onClick={() => setConfig((c) => ({ ...c, mode }))}
                        disabled={disabled}
                        className={`rounded-2xl border p-4 text-left transition-all ${
                          isActive
                            ? 'border-[rgba(255,59,59,0.24)] bg-[rgba(255,59,59,0.1)] text-white shadow-[inset_0_0_0_1px_rgba(255,59,59,0.08)]'
                            : 'border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.02)] text-[rgba(138,143,168,0.9)] hover:border-[rgba(255,59,59,0.18)] hover:bg-[rgba(255,255,255,0.04)] hover:text-white'
                        } ${disabled ? 'cursor-not-allowed opacity-50' : ''}`}
                      >
                        <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
                          <span
                            className="flex h-10 w-10 items-center justify-center rounded-xl border"
                            style={{
                              background:   isActive ? 'linear-gradient(135deg,#FF3B3B,#8B0000)' : 'rgba(255,255,255,0.04)',
                              borderColor:  isActive ? 'rgba(255,59,59,0.24)' : 'rgba(255,255,255,0.08)',
                              boxShadow:    isActive ? '0 0 18px rgba(255,59,59,0.22)' : 'none',
                            }}
                          >
                            <Icon size={18} />
                          </span>
                          {label}
                        </div>
                        <p className="text-xs leading-6 text-[rgba(138,143,168,0.78)]">{description}</p>
                      </button>
                    )
                  })}
                </div>
                {!voiceSupported && (
                  <p className="mt-3 text-xs text-[#fb7185]">
                    Voice input is not supported in this browser. Chrome over HTTPS or localhost works best.
                  </p>
                )}
              </div>
            </div>

            {/* ── What you get panel ── */}
            <div className="glass rounded-[24px] p-5">
              <div className="mb-4 flex items-center gap-3">
                <span
                  className="flex h-12 w-12 items-center justify-center rounded-2xl"
                  style={{
                    background: 'linear-gradient(135deg,#FF3B3B,#8B0000)',
                    boxShadow: '0 0 22px rgba(255,59,59,0.28)',
                  }}
                >
                  <Sparkles size={20} className="text-white" />
                </span>
                <div>
                  <p className="text-sm font-semibold text-white">What you will get</p>
                  <p className="text-xs text-[rgba(138,143,168,0.72)]">Eight tailored questions and a scored report.</p>
                </div>
              </div>
              <div className="space-y-3">
                {[
                  selectedCompany.value === 'general'
                    ? 'Role-specific technical and behavioral prompts'
                    : `Questions styled to ${selectedCompany.label}'s real interview culture`,
                  'Instant evaluation for overall, technical, confidence, and communication',
                  'Specific strengths, weak spots, and next-step prep tips',
                ].map((item) => (
                  <div key={item} className="flex items-start gap-3 rounded-2xl bg-[rgba(255,255,255,0.02)] p-3">
                    <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-[#10b981]" />
                    <p className="text-sm leading-6 text-[rgba(245,245,247,0.82)]">{item}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={handleStart}
            disabled={loading}
            className="btn-primary w-full justify-center py-4 text-base font-semibold"
          >
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                {selectedCompany.value === 'general'
                  ? 'Preparing your interview...'
                  : `Building your ${selectedCompany.label} interview...`}
              </>
            ) : (
              <>
                <Play size={18} />
                {selectedCompany.value === 'general'
                  ? 'Start Interview'
                  : `Start ${selectedCompany.label} Interview`}
              </>
            )}
          </button>
        </div>
      </motion.div>
    </div>
  )
}

// ─── CodingAnswerPanel ─────────────────────────────────────────────────────────
// Shows a two-tab panel for coding questions:
//   Tab 1 — Code Editor  : monospace textarea where candidate writes/fixes code
//   Tab 2 — Explanation  : plain textarea for describing their approach
// Both are merged into a single answer string on submit.
function CodingAnswerPanel({ answer, onChange, category, language = 'python' }) {
  const [activeTab, setActiveTab] = useState('code')

  // answer is stored as "CODE:\n...\n\nEXPLANATION:\n..."
  const parseAnswer = (raw) => {
    const codeMatch  = raw.match(/CODE:\n([\s\S]*?)(?:\n\nEXPLANATION:|$)/)
    const expMatch   = raw.match(/EXPLANATION:\n([\s\S]*)$/)
    return {
      code:        codeMatch  ? codeMatch[1]  : '',
      explanation: expMatch   ? expMatch[1]   : '',
    }
  }

  const buildAnswer = (code, explanation) => {
    const parts = []
    if (code.trim())        parts.push(`CODE:\n${code}`)
    if (explanation.trim()) parts.push(`EXPLANATION:\n${explanation}`)
    return parts.join('\n\n')
  }

  const { code, explanation } = parseAnswer(answer)

  const handleCodeChange = (val) => onChange(buildAnswer(val, explanation))
  const handleExpChange  = (val) => onChange(buildAnswer(code, val))

  const tabLabel = {
    code_fix:       'Your Fixed Code',
    code_write:     'Your Solution',
    debugging:      'Debugged Code',
    error_handling: 'Code With Error Handling',
  }

  return (
    <div className="space-y-3">
      {/* Tab switcher */}
      <div className="flex gap-2">
        {[
          { id: 'code',        icon: Terminal, label: tabLabel[category] || 'Your Code' },
          { id: 'explanation', icon: MessageSquare, label: 'Explanation' },
        ].map(({ id, icon: Icon, label }) => (
          <button
            key={id}
            type="button"
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition-all ${
              activeTab === id
                ? 'bg-[rgba(255,59,59,0.15)] border border-[rgba(255,59,59,0.3)] text-white'
                : 'border border-[rgba(255,255,255,0.07)] bg-[rgba(255,255,255,0.03)] text-[rgba(138,143,168,0.75)] hover:text-white hover:border-[rgba(255,59,59,0.2)]'
            }`}
          >
            <Icon size={13} />
            {label}
          </button>
        ))}
        <span className="ml-auto text-[11px] text-[rgba(138,143,168,0.5)] self-center">
          {language.toUpperCase()}
        </span>
      </div>

      {/* Code editor tab */}
      {activeTab === 'code' && (
        <div className="overflow-hidden rounded-[16px] border border-[rgba(255,255,255,0.08)] bg-[#0d0f14]">
          {/* Editor header */}
          <div className="flex items-center gap-2 border-b border-[rgba(255,255,255,0.06)] px-4 py-2">
            <div className="flex gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-[#FF3B3B]" />
              <span className="h-2.5 w-2.5 rounded-full bg-[#fb923c]" />
              <span className="h-2.5 w-2.5 rounded-full bg-[#10b981]" />
            </div>
            <span className="ml-2 text-[10px] font-medium uppercase tracking-widest text-[rgba(138,143,168,0.5)]">
              editor — {language}
            </span>
          </div>
          {/* Line-numbered editor */}
          <div className="relative flex">
            {/* Line numbers */}
            <div
              className="select-none border-r border-[rgba(255,255,255,0.05)] px-3 py-4 text-right text-[13px] leading-6"
              style={{
                fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                color: 'rgba(138,143,168,0.3)',
                minWidth: 44,
                userSelect: 'none',
              }}
              aria-hidden
            >
              {(code || '\n').split('\n').map((_, i) => (
                // eslint-disable-next-line react/no-array-index-key
                <div key={i}>{i + 1}</div>
              ))}
            </div>
            <textarea
              value={code}
              onChange={(e) => handleCodeChange(e.target.value)}
              rows={12}
              spellCheck={false}
              placeholder={`// Write your ${language} code here...\n// Use Tab for indentation`}
              className="flex-1 resize-none bg-transparent p-4 text-[13px] leading-6 text-[rgba(245,245,247,0.9)] outline-none placeholder:text-[rgba(138,143,168,0.3)]"
              style={{ fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace" }}
              onKeyDown={(e) => {
                // Tab key inserts spaces instead of moving focus
                if (e.key === 'Tab') {
                  e.preventDefault()
                  const { selectionStart, selectionEnd, value } = e.target
                  const newVal = `${value.slice(0, selectionStart)}    ${value.slice(selectionEnd)}`
                  handleCodeChange(newVal)
                  // restore cursor — setTimeout because state update is async
                  setTimeout(() => {
                    e.target.selectionStart = selectionStart + 4
                    e.target.selectionEnd   = selectionStart + 4
                  }, 0)
                }
              }}
            />
          </div>
        </div>
      )}

      {/* Explanation tab */}
      {activeTab === 'explanation' && (
        <div>
          <textarea
            value={explanation}
            onChange={(e) => handleExpChange(e.target.value)}
            rows={8}
            placeholder="Explain your approach: what was the bug, why it occurred, how your fix solves it, and any edge cases you considered..."
            className="input-field min-h-[180px] resize-none"
          />
          <p className="mt-2 text-[11px] text-[rgba(138,143,168,0.5)]">
            Tip — mention time/space complexity, trade-offs, and how you'd test this.
          </p>
        </div>
      )}
    </div>
  )
}

// ─── InterviewPhase ────────────────────────────────────────────────────────────
function InterviewPhase({ questions, sessionId, mode, jobRole, company, onComplete }) {
  const [currentQ, setCurrentQ]     = useState(0)
  const [answer, setAnswer]         = useState('')
  const [transcript, setTranscript] = useState([])
  const [listening, setListening]   = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [speechError, setSpeechError] = useState('')
  const recognitionRef  = useRef(null)
  const textareaRef     = useRef(null)
  const finalTranscriptRef = useRef('')
  const voiceSupported =
    typeof window !== 'undefined' && !!(window.SpeechRecognition || window.webkitSpeechRecognition)

  const companyMeta = getCompanyMeta(company)

  useEffect(() => {
    if (mode !== 'voice') return

    const SpeechRecognitionApi = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognitionApi) {
      setSpeechError('Voice input is not supported in this browser. Please use Chrome on HTTPS or localhost.')
      return
    }

    const recognition = new SpeechRecognitionApi()
    recognition.continuous       = true
    recognition.interimResults   = true
    recognition.lang             = 'en-US'
    recognition.maxAlternatives  = 1

    recognition.onstart  = () => { setListening(true); setSpeechError('') }
    recognition.onresult = (event) => {
      let finalText = '', interimText = ''
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const text = event.results[i]?.[0]?.transcript || ''
        if (event.results[i].isFinal) finalText += `${text} `
        else interimText += text
      }
      if (finalText.trim()) {
        finalTranscriptRef.current = `${finalTranscriptRef.current} ${finalText}`.trim()
      }
      setAnswer(`${finalTranscriptRef.current} ${interimText}`.trim())
    }
    recognition.onerror = (event) => {
      const code = event?.error || 'unknown'
      if (code === 'not-allowed' || code === 'service-not-allowed') {
        setSpeechError('Microphone permission denied. Allow microphone access in browser settings.')
      } else if (code === 'audio-capture') {
        setSpeechError('No microphone detected. Connect one and retry.')
      } else if (code === 'no-speech') {
        setSpeechError('No speech detected. Try speaking louder and closer to the microphone.')
      } else if (code === 'network') {
        setSpeechError('Speech service network error. Check your connection and retry.')
      } else if (code !== 'aborted') {
        setSpeechError('Voice input failed. Please retry.')
      }
    }
    recognition.onend = () => setListening(false)
    recognitionRef.current = recognition

    return () => {
      try { recognition.stop() } catch {}
      recognitionRef.current = null
    }
  }, [mode])

  useEffect(() => {
    if (mode === 'voice' && questions[currentQ]) {
      setTimeout(() => speak(questions[currentQ].question), 300)
    }
    finalTranscriptRef.current = ''
    setSpeechError('')
    textareaRef.current?.focus()
  }, [currentQ, mode, questions])

  const ensureMicPermission = async () => {
    if (!navigator.mediaDevices?.getUserMedia) return true
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach((track) => track.stop())
      return true
    } catch (error) {
      if (error?.name === 'NotAllowedError' || error?.name === 'SecurityError') {
        setSpeechError('Microphone permission denied. Allow microphone access in browser settings.')
      } else if (error?.name === 'NotFoundError') {
        setSpeechError('No microphone found on this device.')
      } else {
        setSpeechError('Unable to access microphone.')
      }
      return false
    }
  }

  const toggleListen = async () => {
    if (!voiceSupported || !recognitionRef.current) {
      setSpeechError('Voice input is not supported in this browser. Please use Chrome on HTTPS or localhost.')
      return
    }
    if (listening) {
      try { recognitionRef.current.stop() } catch {}
      return
    }
    const hasPermission = await ensureMicPermission()
    if (!hasPermission) return
    finalTranscriptRef.current = answer.trim()
    setSpeechError('')
    try {
      recognitionRef.current.start()
    } catch (error) {
      if (error?.name !== 'InvalidStateError') {
        setSpeechError('Could not start voice input. Check microphone permissions and retry.')
      }
    }
  }

  const submitAnswer = async () => {
    if (!answer.trim()) return
    setSubmitting(true)
    const questionAnswer = { question: questions[currentQ]?.question, answer }
    const newTranscript  = [...transcript, questionAnswer]
    setTranscript(newTranscript)
    setAnswer('')
    recognitionRef.current?.stop()
    setListening(false)
    if (currentQ + 1 < questions.length) {
      setCurrentQ((value) => value + 1)
      setSubmitting(false)
    } else {
      await onComplete(newTranscript)
      setSubmitting(false)
    }
  }

  const question     = questions[currentQ]
  const progress     = (currentQ / questions.length) * 100
  const isLast       = currentQ + 1 === questions.length
  const categoryMeta = CATEGORY_META[question?.category] || CATEGORY_META.technical
  const CategoryIcon = categoryMeta.icon
  const isCodingQ    = CODING_CATEGORIES.has(question?.category)

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="space-y-2">
          {/* Company badge */}
          {companyMeta.value !== 'general' && (
            <div className="inline-flex items-center gap-2 rounded-full border border-[rgba(255,59,59,0.2)] bg-[rgba(255,59,59,0.08)] px-3 py-1">
              <CompanyLogo company={companyMeta} size={16} />
              <span className="text-xs font-medium text-[#FF7070]">
                {companyMeta.label} Interview
              </span>
            </div>
          )}
          <span className="badge badge-red">Live Interview</span>
          <div>
            <h1 className="gradient-text text-3xl font-black tracking-tight">{jobRole}</h1>
            <p className="mt-1 text-sm capitalize text-[rgba(138,143,168,0.78)]">{mode} mode session</p>
          </div>
        </div>
        <div className="glass rounded-2xl px-4 py-3">
          <p className="text-xs uppercase tracking-[0.2em] text-[rgba(138,143,168,0.64)]">Session</p>
          <p className="mt-1 text-sm font-semibold text-white">
            Question {currentQ + 1} of {questions.length}
          </p>
          {sessionId && (
            <p className="mt-1 text-[11px] text-[rgba(138,143,168,0.58)]">ID: {sessionId}</p>
          )}
        </div>
      </div>

      {/* ── Progress bar ── */}
      <div className="overflow-hidden rounded-full bg-[rgba(255,255,255,0.04)]">
        <motion.div
          className="h-2 rounded-full bg-[linear-gradient(90deg,#FF3B3B,#e11d48,#fb7185)]"
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.45, ease: [0.4, 0, 0.2, 1] }}
        />
      </div>

      {/* ── Question card ── */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentQ}
          initial={{ opacity: 0, x: 24 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -24 }}
          transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
          className="glass-glow overflow-hidden rounded-[28px] p-7"
          style={{ borderLeft: '3px solid #FF3B3B' }}
        >
          <div className="absolute inset-x-0 top-0 h-px bg-[linear-gradient(90deg,transparent,rgba(255,59,59,0.45),transparent)]" />
          <div className="space-y-5">
            <div className="flex flex-wrap items-center gap-3">
              <span className="badge badge-red">Question {currentQ + 1}</span>
              <span className={DIFFICULTY_STYLES[question?.difficulty] || 'badge badge-red'}>
                {question?.difficulty || 'hard'}
              </span>
              <span
                className="inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-xs font-medium"
                style={{
                  background: `${categoryMeta.color}18`,
                  border: `1px solid ${categoryMeta.color}35`,
                  color: categoryMeta.color,
                }}
              >
                <CategoryIcon size={13} />
                {categoryMeta.label}
              </span>
              {/* Company-specific tag */}
              {companyMeta.value !== 'general' && (
                <span className="ml-auto inline-flex items-center gap-1.5 rounded-full border border-[rgba(255,59,59,0.18)] bg-[rgba(255,59,59,0.07)] px-2.5 py-0.5 text-[11px] text-[#FF7070]">
                  <CompanyLogo company={companyMeta} size={14} />
                  {companyMeta.label} style
                </span>
              )}
              {mode === 'voice' && (
                <button
                  type="button"
                  onClick={() => speak(question?.question)}
                  className="btn-ghost ml-auto px-4 py-2 text-xs"
                >
                  <Volume2 size={14} />
                  Replay
                </button>
              )}
            </div>

            {/* Coding context label */}
            {isCodingQ && (
              <div
                className="inline-flex items-center gap-2 rounded-xl px-3 py-1.5 text-xs font-semibold"
                style={{
                  background: `${categoryMeta.color}15`,
                  border: `1px solid ${categoryMeta.color}30`,
                  color: categoryMeta.color,
                }}
              >
                <CategoryIcon size={13} />
                {question?.category === 'code_fix'       && 'Find the bug and fix it'}
                {question?.category === 'code_write'     && 'Write a solution for this problem'}
                {question?.category === 'debugging'      && 'Debug this code — explain the error and the fix'}
                {question?.category === 'error_handling' && 'Add proper error handling to this code'}
              </div>
            )}

            <p className="text-xl font-semibold leading-8 text-white">{question?.question}</p>

            {/* Code snippet block */}
            {isCodingQ && question?.code_snippet && (
              <CodeBlock code={question.code_snippet} language={question.language || 'python'} />
            )}

            {question?.expected_points?.length > 0 && (
              <div className="rounded-[22px] border border-[rgba(255,59,59,0.15)] bg-[rgba(255,59,59,0.06)] p-4">
                <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-[#FF7070]">
                  Consider covering
                </p>
                <div className="flex flex-wrap gap-2">
                  {question.expected_points.map((point) => (
                    <span
                      key={point}
                      className="rounded-full border border-[rgba(255,59,59,0.2)] bg-[rgba(255,59,59,0.08)] px-3 py-1 text-xs text-[#FF7070]"
                    >
                      {point}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </AnimatePresence>

      {/* ── Answer box ── */}
      <div className="glass-glow rounded-[26px] p-6">

        {isCodingQ ? (
          /* ── Coding question: split code editor + explanation ── */
          <CodingAnswerPanel
            answer={answer}
            onChange={setAnswer}
            onSubmit={submitAnswer}
            category={question?.category}
            language={question?.language || 'python'}
          />
        ) : (
          /* ── Standard question: plain textarea ── */
          <>
            <label className="mb-3 block text-xs font-semibold uppercase tracking-[0.18em] text-[rgba(138,143,168,0.72)]">
              Your Answer
            </label>
            <textarea
              ref={textareaRef}
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && e.ctrlKey) submitAnswer() }}
              rows={6}
              placeholder={
                mode === 'voice'
                  ? 'Use the mic button below to speak, or type your answer here...'
                  : 'Type your answer here... Press Ctrl + Enter to submit.'
              }
              className="input-field min-h-[180px] resize-none"
            />
          </>
        )}

        <div className="mt-4 flex flex-col gap-3 sm:flex-row">
          {mode === 'voice' && !isCodingQ && (
            <button
              type="button"
              onClick={toggleListen}
              disabled={!voiceSupported}
              className={`inline-flex items-center justify-center gap-2 rounded-xl border px-5 py-3 text-sm font-medium transition-all ${
                listening
                  ? 'border-[rgba(255,59,59,0.32)] bg-[rgba(255,59,59,0.12)] text-white shadow-[0_0_20px_rgba(255,59,59,0.16)]'
                  : 'btn-ghost'
              } ${!voiceSupported ? 'cursor-not-allowed opacity-50' : ''}`}
            >
              {listening ? <><MicOff size={16} />Stop Recording</> : <><Mic size={16} />Speak Answer</>}
            </button>
          )}

          <button
            type="button"
            onClick={submitAnswer}
            disabled={!answer.trim() || submitting}
            className="btn-primary flex-1 justify-center py-3.5"
          >
            {submitting ? (
              <><Loader2 size={16} className="animate-spin" />{isLast ? 'Evaluating...' : 'Saving answer...'}</>
            ) : isLast ? (
              <><Trophy size={16} />Finish And Get Evaluation</>
            ) : (
              <>Next Question<ChevronRight size={16} /></>
            )}
          </button>
        </div>

        {!isCodingQ && (
          <p className="mt-3 text-center text-xs text-[rgba(138,143,168,0.62)]">Ctrl + Enter to submit</p>
        )}
        {mode === 'voice' && speechError && (
          <p className="mt-2 text-center text-xs text-[#fb7185]">{speechError}</p>
        )}
      </div>

      {/* ── Answered so far ── */}
      {transcript.length > 0 && (
        <div className="glass-glow rounded-[24px] p-5">
          <div className="mb-4 flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[rgba(138,143,168,0.72)]">
              Answered So Far
            </p>
            <span className="badge badge-red">{transcript.length}/{questions.length}</span>
          </div>
          <div className="space-y-3">
            {transcript.map((entry, index) => (
              <div
                key={`${entry.question}-${index}`}
                className="rounded-2xl border border-[rgba(255,255,255,0.06)] bg-[rgba(255,255,255,0.02)] p-3"
              >
                <p className="text-sm font-medium text-white">Q{index + 1}</p>
                <p className="mt-1 text-xs text-[rgba(138,143,168,0.7)] line-clamp-1">{entry.question}</p>
                <p className="mt-2 text-sm text-[rgba(245,245,247,0.78)] line-clamp-2">{entry.answer}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ─── ResultPhase ───────────────────────────────────────────────────────────────
function ResultPhase({ evaluation, jobRole, company, onRetry }) {
  const recommendation = getRecommendationMeta(evaluation.hire_recommendation)
  const companyMeta    = getCompanyMeta(company)

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <motion.div
        whileHover={{ y: -3 }}
        className="glass-glow overflow-hidden rounded-[30px] p-7"
        style={{ borderTop: '2px solid rgba(255,59,59,0.4)' }}
      >
        <div className="absolute inset-x-0 top-0 h-28 bg-[radial-gradient(circle_at_top,rgba(255,59,59,0.14),transparent_72%)] pointer-events-none" />
        <div className="relative flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className={recommendation.className}>{recommendation.label}</span>
              {companyMeta.value !== 'general' && (
                <span className="inline-flex items-center gap-1.5 rounded-full border border-[rgba(255,59,59,0.2)] bg-[rgba(255,59,59,0.08)] px-3 py-1 text-xs text-[#FF7070]">
                  <CompanyLogo company={companyMeta} size={14} />
                  {companyMeta.label} Interview
                </span>
              )}
            </div>
            <div>
              <h1 className="gradient-text text-3xl font-black tracking-tight">{jobRole} Evaluation</h1>
              <p className="mt-2 max-w-2xl text-sm leading-7 text-[rgba(138,143,168,0.82)]">
                Your interview was scored across technical depth, clarity, and confidence. Use the
                breakdown below to sharpen the next round.
              </p>
            </div>
          </div>

          <div className="glass rounded-[24px] p-5">
            <div className="flex items-center gap-4">
              <span
                className="flex h-14 w-14 items-center justify-center rounded-2xl"
                style={{
                  background: 'linear-gradient(135deg,#FF3B3B,#8B0000)',
                  boxShadow: '0 0 24px rgba(255,59,59,0.24)',
                }}
              >
                <Trophy size={24} className="text-white" />
              </span>
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-[rgba(138,143,168,0.68)]">Recommendation</p>
                <p className="mt-1 text-sm font-semibold capitalize text-white">{evaluation.hire_recommendation}</p>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]"
      >
        <motion.div variants={staggerItem} className="glass-glow rounded-[28px] p-6">
          <div className="mb-6 flex items-center gap-2 text-white">
            <BarChart2 size={18} className="text-[#FF3B3B]" />
            <h2 className="text-lg font-semibold">Performance Scores</h2>
          </div>
          <div className="grid gap-6 md:grid-cols-[1.1fr_0.9fr]">
            <div className="flex items-center justify-center rounded-[24px] border border-[rgba(255,255,255,0.06)] bg-[rgba(255,255,255,0.02)] p-6">
              <ScoreCircle score={evaluation.overall_score} label="Overall Score" size={164} showScale highlight />
            </div>
            <div className="grid gap-4 sm:grid-cols-3 md:grid-cols-1">
              <div className="glass rounded-[22px] p-4">
                <ScoreCircle score={evaluation.technical_score} label="Technical" />
              </div>
              <div className="glass rounded-[22px] p-4">
                <ScoreCircle score={evaluation.communication_score} label="Communication" />
              </div>
              <div className="glass rounded-[22px] p-4">
                <ScoreCircle score={evaluation.confidence_score} label="Confidence" />
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div variants={staggerItem} className="glass-glow rounded-[28px] p-6">
          <div className="mb-4 flex items-center gap-2 text-white">
            <MessageSquare size={18} className="text-[#FF3B3B]" />
            <h2 className="text-lg font-semibold">Summary</h2>
          </div>
          <p className="text-sm leading-7 text-[rgba(245,245,247,0.8)]">{evaluation.summary}</p>
        </motion.div>
      </motion.div>

      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid gap-4 lg:grid-cols-2"
      >
        <motion.div
          variants={staggerItem}
          whileHover={{ y: -3 }}
          className="rounded-[26px] border border-[rgba(16,185,129,0.2)] bg-[rgba(16,185,129,0.08)] p-6"
        >
          <div className="mb-4 flex items-center gap-2 text-white">
            <CheckCircle2 size={18} className="text-[#10b981]" />
            <h3 className="text-lg font-semibold">Strengths</h3>
          </div>
          <div className="space-y-3">
            {evaluation.strengths?.map((strength) => (
              <div key={strength} className="rounded-2xl bg-[rgba(255,255,255,0.03)] p-3 text-sm leading-6 text-white/85">
                {strength}
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div
          variants={staggerItem}
          whileHover={{ y: -3 }}
          className="rounded-[26px] border border-[rgba(255,59,59,0.2)] bg-[rgba(255,59,59,0.08)] p-6"
        >
          <div className="mb-4 flex items-center gap-2 text-white">
            <Zap size={18} className="text-[#FF3B3B]" />
            <h3 className="text-lg font-semibold">Areas To Improve</h3>
          </div>
          <div className="space-y-3">
            {evaluation.improvements?.map((item) => (
              <div key={item} className="rounded-2xl bg-[rgba(255,255,255,0.03)] p-3 text-sm leading-6 text-white/85">
                {item}
              </div>
            ))}
          </div>
        </motion.div>
      </motion.div>

      {evaluation.question_feedback?.length > 0 && (
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="glass-glow rounded-[28px] p-6"
        >
          <div className="mb-5 flex items-center gap-2 text-white">
            <Sparkles size={18} className="text-[#FF3B3B]" />
            <h2 className="text-lg font-semibold">Question By Question Feedback</h2>
          </div>
          <div className="space-y-4">
            {evaluation.question_feedback.map((item, index) => (
              <motion.div key={`${item.question}-${index}`} variants={staggerItem} className="glass-glow rounded-[22px] p-5">
                <div className="mb-3 flex items-start justify-between gap-4">
                  <div className="space-y-2">
                    <span className="badge badge-red">Question {index + 1}</span>
                    <p className="text-sm font-semibold leading-7 text-white">{item.question}</p>
                  </div>
                  <span
                    className={`text-sm font-bold ${
                      item.score >= 7 ? 'text-[#10b981]' : item.score >= 5 ? 'text-[#fb7185]' : 'text-[#FF3B3B]'
                    }`}
                  >
                    {item.score}/10
                  </span>
                </div>
                <p className="text-sm leading-7 text-[rgba(138,143,168,0.84)]">{item.feedback}</p>
                {item.ideal_answer_hint && (
                  <p className="mt-3 text-sm leading-7 text-[#FF7070]">{item.ideal_answer_hint}</p>
                )}
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {evaluation.recommended_resources?.length > 0 && (
        <motion.div whileHover={{ y: -3 }} className="glass-glow rounded-[28px] p-6">
          <div className="mb-2 flex items-center gap-2 text-white">
            <Star size={18} className="text-[#FF3B3B]" />
            <h2 className="text-lg font-semibold">Resources To Close Your Gaps</h2>
          </div>
          <p className="mb-4 text-xs text-[rgba(138,143,168,0.65)]">
            Curated specifically for the weak areas identified in your session. Click to open.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            {evaluation.recommended_resources.map((resource, idx) => {
              const { title, url } = resolveResourceUrl(resource)

              const handleOpen = () => {
                if (url) {
                  window.open(url, '_blank', 'noopener,noreferrer')
                }
              }

              return (
                <button
                  key={idx}
                  type="button"
                  onClick={handleOpen}
                  disabled={!url}
                  className="flex items-center gap-3 rounded-[20px] border border-[rgba(255,255,255,0.06)] bg-[rgba(255,255,255,0.02)] p-4 text-left transition-all hover:border-[rgba(255,59,59,0.25)] hover:bg-[rgba(255,59,59,0.07)] group disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <span
                    className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl"
                    style={{ background: 'linear-gradient(135deg,#FF3B3B,#8B0000)', boxShadow: '0 0 14px rgba(255,59,59,0.3)' }}
                  >
                    <Star size={14} className="text-white" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-white group-hover:text-[#FF7070] transition-colors">{title}</p>
                    {url && (
                      <p className="truncate text-[11px] text-[rgba(138,143,168,0.5)] mt-0.5">
                        {url.replace(/^https?:\/\/(www\.)?/, '').split('/')[0]}
                      </p>
                    )}
                    {!url && (
                      <p className="text-[11px] text-[rgba(138,143,168,0.4)] mt-0.5">No link available</p>
                    )}
                  </div>
                  <ChevronRight size={14} className="shrink-0 text-[rgba(138,143,168,0.4)] group-hover:text-[#FF7070] transition-colors" />
                </button>
              )
            })}
          </div>
        </motion.div>
      )}

      <div className="flex flex-col gap-3 sm:flex-row">
        <button type="button" onClick={onRetry} className="btn-ghost flex-1 justify-center py-3.5">
          <RefreshCw size={16} />
          Back To Setup
        </button>
        <button type="button" onClick={onRetry} className="btn-primary flex-1 justify-center py-3.5">
          <RefreshCw size={16} />
          Practice Again
        </button>
      </div>
    </div>
  )
}

// ─── Root export ───────────────────────────────────────────────────────────────
export default function MockInterview() {
  const [phase, setPhase]           = useState('setup')
  const [sessionId, setSessionId]   = useState(null)
  const [questions, setQuestions]   = useState([])
  const [evaluation, setEvaluation] = useState(null)
  const [jobRole, setJobRole]       = useState('')
  const [company, setCompany]       = useState('general')
  const [mode, setMode]             = useState('text')
  const [error, setError]           = useState('')

  const handleStart = async (config) => {
    setError('')
    try {
      const response = await api.startInterview({
        job_role: config.job_role,
        company:  config.company,
        mode:     config.mode,
      })
      setSessionId(response.session_id)
      setQuestions(response.questions)
      setJobRole(config.job_role)
      setCompany(config.company)
      setMode(config.mode)
      setPhase('interview')
    } catch (err) {
      setError(err.message)
    }
  }

  const handleComplete = async (transcript) => {
    setError('')
    try {
      const response = await api.evaluateInterview({
        session_id: sessionId,
        transcript,
      })
      setEvaluation(response.evaluation)
      setPhase('result')
    } catch (err) {
      setError(err.message)
    }
  }

  const handleRetry = () => {
    setPhase('setup')
    setSessionId(null)
    setQuestions([])
    setEvaluation(null)
    setError('')
  }

  return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
      {error && (
        <div className="mb-5 rounded-2xl border border-[rgba(255,59,59,0.2)] bg-[rgba(255,59,59,0.08)] px-4 py-3 text-sm text-[#FF7070]">
          {error}
        </div>
      )}

      <AnimatePresence mode="wait">
        {phase === 'setup' && (
          <motion.div key="setup" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <SetupPhase onStart={handleStart} />
          </motion.div>
        )}

        {phase === 'interview' && (
          <motion.div key="interview" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <InterviewPhase
              questions={questions}
              sessionId={sessionId}
              mode={mode}
              jobRole={jobRole}
              company={company}
              onComplete={handleComplete}
            />
          </motion.div>
        )}

        {phase === 'result' && evaluation && (
          <motion.div key="result" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <ResultPhase
              evaluation={evaluation}
              jobRole={jobRole}
              company={company}
              onRetry={handleRetry}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}