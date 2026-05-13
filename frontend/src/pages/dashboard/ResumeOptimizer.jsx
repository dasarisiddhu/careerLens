import { useRef, useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAnimatedCircle, useCountUp, pageTransition } from '../../utils/animations'
import { api } from '../../services/api'
import { supabase } from '../../services/supabase'
import { useAuth } from '../../context/AuthContext'
import toast from 'react-hot-toast'
import {
  Loader2, Zap, Download, CheckCircle,
  Tag, ChevronRight, RefreshCw, Badge, Plus,
  Upload, Sparkles, Copy, Check, CheckCircle2,
  Briefcase, Target,
} from 'lucide-react'

const GITHUB_LOCK_KEY = 'careerlens:locked_github_url'

function CopyBtn({ text }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <motion.button
      whileHover={{ scale: 1.03, y: -1 }}
      whileTap={{ scale: 0.97 }}
      transition={{ duration: 0.15, ease: 'easeOut' }}
      onClick={copy}
      className="text-[#8A8FA8] hover:text-[#FF7070] transition-colors p-1"
    >
      {copied ? <Check size={13} className="text-green-400" /> : <Copy size={13} />}
    </motion.button>
  )
}

function AnimatedScoreCircle({ score, maxScore = 100, size = 120, label, color }) {
  const { radius, circumference, offset, strokeWidth } = useAnimatedCircle(score, maxScore, size, 8)
  const count = useCountUp(score, 1400)
  const strokeColor = color || (score >= 70 ? '#10b981' : score >= 40 ? '#FF8C42' : '#FF3B3B')

  return (
    <div className="flex flex-col items-center gap-2">
      <div style={{ width: size, height: size, position: 'relative' }}>
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
          <defs>
            <filter id={`glow-${score}`}>
              <feGaussianBlur stdDeviation="3" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={strokeWidth} />
          <circle
            cx={size/2} cy={size/2} r={radius}
            fill="none" stroke={strokeColor} strokeWidth={strokeWidth} strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            filter={`url(#glow-${score})`}
            style={{ transition: 'stroke-dashoffset 1.4s cubic-bezier(0.22, 1, 0.36, 1)' }}
          />
        </svg>
        <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <span className="text-3xl font-black text-white">{count}</span>
        </div>
      </div>
      <span className="text-xs text-[#78716c] text-center">{label}</span>
    </div>
  )
}

function StatNumber({ value, prefix = '', suffix = '' }) {
  const numeric = typeof value === 'number' ? value : parseInt(value, 10) || 0
  const count = useCountUp(numeric, 1400)
  return <span>{prefix}{count}{suffix}</span>
}

function escapeRegex(value = '') {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function buildKeywordRegex(keywords = []) {
  const cleaned = keywords
    .map((k) => String(k || '').trim())
    .filter(Boolean)
    .sort((a, b) => b.length - a.length)
  if (!cleaned.length) return null
  const patterns = cleaned.map((k) => escapeRegex(k).replace(/\s+/g, '\\s+'))
  return new RegExp(`\\b(${patterns.join('|')})\\b`, 'gi')
}

function highlightKeywords(text = '', keywords = []) {
  const regex = buildKeywordRegex(keywords)
  if (!regex) return text
  const parts = String(text).split(regex)
  return parts.map((part, idx) => {
    if (idx % 2 === 1) {
      return (
        <span key={`kw-${idx}`} className="text-green-200 bg-green-500/10 px-1 rounded-sm shadow-[0_0_10px_rgba(34,197,94,0.2)]">
          {part}
        </span>
      )
    }
    return <span key={`kw-${idx}`}>{part}</span>
  })
}

function ProgressBar({ value, colorClass }) {
  const width = Math.max(0, Math.min(100, Number(value) || 0))
  return (
    <div className="h-2 rounded-full bg-white/5 overflow-hidden">
      <motion.div
        className={`h-full rounded-full ${colorClass}`}
        initial={{ width: 0 }}
        animate={{ width: `${width}%` }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
      />
    </div>
  )
}

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

function isHeadingLine(line = '') {
  const cleaned = line.trim()
  if (!cleaned) return false
  if (cleaned.length <= 40 && cleaned === cleaned.toUpperCase() && /[A-Z]/.test(cleaned)) return true
  if (cleaned.endsWith(':') && cleaned.length <= 40) return true
  return /^(summary|professional summary|experience|work experience|education|projects|skills|certifications|achievements|publications|volunteer|activities|objective|profile|awards|contact|details)\b/i.test(cleaned)
}

function extractResumeHeader(text = '') {
  const lines = normalizePdfText(text).split('\n').map((line) => line.trim())
  let i = 0
  while (i < lines.length && !lines[i]) i += 1
  const name = i < lines.length ? lines[i] : ''
  i += 1
  const contactLines = []
  while (i < lines.length && contactLines.length < 4) {
    const line = lines[i]
    if (!line) { i += 1; continue }
    if (isHeadingLine(line)) break
    contactLines.push(line)
    i += 1
  }
  const bodyText = lines.slice(i).join('\n').trim()
  return { name, contactLines, bodyText }
}

function extractContactInfo(text = '') {
  const normalized = normalizePdfText(text)
  const { name: headerName, contactLines } = extractResumeHeader(normalized)
  const emailMatch = normalized.match(/[\w.-]+@[\w.-]+\.\w+/)
  const phoneMatch = normalized.match(/[\+]?[\d][\d\s\-()]{8,}/)
  const email = emailMatch?.[0] || ''
  const phone = phoneMatch?.[0] || ''

  let name = headerName || ''
  if (!name) {
    const lines = normalized.split('\n').map((line) => line.trim()).filter(Boolean)
    name = lines.find((line) => !/@/.test(line) && !/\d{6,}/.test(line)) || ''
  }

  const contactLine = contactLines.length
    ? contactLines.join(' | ')
    : [email, phone].filter(Boolean).join(' | ')

  return { name, email, phone, contactLine }
}

function readStoredContact() {
  try {
    const raw = localStorage.getItem('careerlens:resume_contact')
    if (!raw) return {}
    const parsed = JSON.parse(raw)
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

function normalizeOptimizationResult(opt) {
  if (!opt || typeof opt !== 'object' || Array.isArray(opt)) return null

  return {
    ...opt,
    optimized_summary: opt.optimized_summary || opt.summary || '',
    optimized_skills: Array.isArray(opt.optimized_skills)
      ? opt.optimized_skills
      : Array.isArray(opt.skills_to_highlight)
        ? opt.skills_to_highlight
        : [],
    new_bullets: Array.isArray(opt.new_bullets) ? opt.new_bullets : [],
  }
}

function escapeHtml(value = '') {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function extractGithubUsername(value = '') {
  const raw = String(value || '').trim()
  if (!raw) return ''

  const match = raw.match(/github\.com\/([^/?#]+)/i)
  const candidate = (match ? match[1] : raw).replace(/^@/, '').trim()
  return /^[a-z\d](?:[a-z\d-]{0,38}[a-z\d])?$/i.test(candidate) ? candidate : ''
}

function resolveAuthGithubUsername(authUser) {
  if (!authUser) return ''

  const identities = Array.isArray(authUser.identities) ? authUser.identities : []
  const githubIdentity = identities.find((identity) => (identity?.provider || '').toLowerCase() === 'github')
  const identityMeta = githubIdentity?.identity_data || {}
  const userMeta = authUser?.user_metadata || {}

  return (
    userMeta.user_name
    || userMeta.preferred_username
    || userMeta.username
    || userMeta.login
    || identityMeta.user_name
    || identityMeta.preferred_username
    || identityMeta.username
    || identityMeta.login
    || extractGithubUsername(userMeta.profile || userMeta.url || '')
    || ''
  ).trim()
}

async function resolveGithubUsername(authUser) {
  const authUsername = resolveAuthGithubUsername(authUser)
  if (authUsername) return authUsername

  try {
    const storedUrl = localStorage.getItem(GITHUB_LOCK_KEY)
    const storedUsername = extractGithubUsername(storedUrl)
    if (storedUsername) return storedUsername
  } catch {
    // localStorage may be unavailable in restricted browser modes
  }

  try {
    const me = await api.getMe()
    return (
      String(me?.user?.github_username || '').trim()
      || extractGithubUsername(me?.user?.github_url || '')
    )
  } catch {
    return ''
  }
}

function countWords(value = '') {
  return String(value || '').trim().split(/\s+/).filter(Boolean).length
}

function takeWords(value = '', maxWords = 6) {
  return String(value || '').trim().split(/\s+/).filter(Boolean).slice(0, maxWords).join(' ')
}

function extractResumeHighlights(text = '', maxItems = 6) {
  return normalizePdfText(text)
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .filter((line) => !isHeadingLine(line))
    .map((line) => line.replace(/^[-*\u2022]\s+/, '').trim())
    .filter(Boolean)
    .slice(0, maxItems)
}

function extractSectionLines(text = '', patterns = [], maxItems = 4) {
  const lines = normalizePdfText(text).split('\n').map((line) => line.trim())
  const startIndex = lines.findIndex((line) => line && patterns.some((pattern) => pattern.test(line)))
  if (startIndex === -1) return []

  const collected = []
  for (let i = startIndex + 1; i < lines.length && collected.length < maxItems; i += 1) {
    const line = lines[i]
    if (!line) continue
    if (isHeadingLine(line)) break
    const cleaned = line.replace(/^[-*\u2022]\s+/, '').trim()
    if (cleaned) collected.push(cleaned)
  }
  return collected
}

function extractEducationLines(text = '', maxItems = 4) {
  return extractSectionLines(
    text,
    [/^education\b/i, /^academic\b/i, /^qualifications?\b/i, /^degree\b/i],
    maxItems,
  )
}

function formatEducationLine(value = '') {
  return String(value || '')
    .split('|')
    .map((part) => part.trim())
    .filter(Boolean)
    .join(' | ')
}

const EMAIL_PATTERN = /[\w.-]+@[\w.-]+\.\w+/
const PHONE_PATTERN = /(?:\+?\d[\d\s\-()]{8,}\d)/
const LOCATION_PATTERN = /\b[A-Za-z]+(?:\s+[A-Za-z]+)?,\s*(?:India|IN)\b/
function formatList(items = [], fallback = '') {
  const clean = items.map((item) => String(item || '').trim()).filter(Boolean)
  if (!clean.length) return fallback
  if (clean.length === 1) return clean[0]
  if (clean.length === 2) return `${clean[0]} and ${clean[1]}`
  return `${clean.slice(0, -1).join(', ')}, and ${clean[clean.length - 1]}`
}

function keywordKey(value = '') {
  const key = String(value || '').toLowerCase().replace(/[^a-z0-9+#.]+/g, ' ').trim()
  if (['ai', 'artificial intelligence'].includes(key)) return 'ai'
  if (['ml', 'machine learning'].includes(key)) return 'machine learning'
  if (['nodejs', 'node js', 'node.js'].includes(key)) return 'node.js'
  return key
}

function dedupeKeywords(items = []) {
  const seen = new Set()
  return items
    .map((item) => String(item || '').trim())
    .filter(Boolean)
    .filter((item) => {
      const key = keywordKey(item)
      if (!key || seen.has(key)) return false
      seen.add(key)
      return true
    })
}

function removeSummaryEllipses(value = '') {
  return String(value || '').replace(/\u2026/g, '.').replace(/\.{2,}/g, '.')
}

function cleanSummarySentence(value = '') {
  let text = removeSummaryEllipses(sanitizeProfessionalSummary(value))
    .replace(/\bwith experience in\b/gi, 'specializing in')
    .replace(/\b(has experience in|has knowledge of|is skilled in|worked on|proficient in|knowledge of)\b/gi, 'focused on')
    .replace(/[!?]+$/g, '.')
    .replace(/\s+/g, ' ')
    .replace(/\s+([,.])/g, '$1')
    .replace(/,\s*\./g, '.')
    .replace(/\s+-\s*$/g, '')
    .trim()

  if (!text) return ''
  text = text.charAt(0).toUpperCase() + text.slice(1)
  if (!text.endsWith('.')) text += '.'
  return text
}

function splitCompleteSummarySentences(value = '') {
  const text = removeSummaryEllipses(sanitizeProfessionalSummary(value))
    .replace(/[!?]/g, '.')
    .replace(/\s+/g, ' ')
    .trim()
  const matches = text.match(/[^.!?]+[.!?]/g) || []
  const sentences = []
  const seen = new Set()

  for (const match of matches) {
    const sentence = cleanSummarySentence(match)
    const key = sentence.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
    if (!key || seen.has(key)) continue
    seen.add(key)
    sentences.push(sentence)
  }

  return sentences
}

function isValidGeneratedSummary(value = '') {
  const sentences = splitCompleteSummarySentences(value)
  if (sentences.length !== 2) return false
  const summary = sentences.join(' ')
  if (/\.{2,}|\u2026/.test(summary)) return false
  if (/\b(with experience in|has experience in|has knowledge of|is skilled in|worked on|proficient in)\b/i.test(summary)) return false
  if (/\b(production-grade|applied engineering work|reliable deployment practices|practical, measurable|maintainable solutions|delivery quality|scalable infrastructure practices|workflow automation|user-centered product delivery|significantly improved|greatly enhanced|various improvements|multiple systems|improved system efficiency|improved throughput|enhanced performance|scaled systems|optimized workflows)\b/i.test(summary)) return false
  if (sentences.some((sentence) => /^(uses|has|i|my)\b/i.test(sentence))) return false
  if (!summaryMetricsValid(summary)) return false
  if (!/\b(backend systems|data pipelines|model deployment|production systems)\b/i.test(summary)) return false
  if (!/\b(accuracy|latency|uptime|processing|retrieval|deployment|processed|handled|supported)\b/i.test(summary)) return false
  const words = countWords(summary)
  return words <= 45 && sentences.every((sentence) => sentence.endsWith('.'))
}

function summaryMetricsValid(summary = '') {
  const lowered = String(summary || '').toLowerCase()
  const countUnit = '(?:users|records|requests|data points|transactions|patients|entries|patient records)'
  const countValue = `\\d+(?:\\.\\d+)?\\s*(?:k|m|b)?\\+?\\s*(?:daily\\s+|monthly\\s+)?${countUnit}`
  if (new RegExp(`\\b(accuracy|precision|recall|f1|auc|score|model quality)\\b[^.]*\\b${countValue}\\b`, 'i').test(lowered)) return false
  if (new RegExp(`\\b${countValue}\\b[^.]*\\b(accuracy|precision|recall|f1|auc|score|model quality)\\b`, 'i').test(lowered)) return false
  if (/\bimproved\s+by\s+\d+(?:\.\d+)?%/i.test(lowered)) return false
  if (/\b(improved|enhanced)\s+performance\b(?!\s+by\s+\d+(?:\.\d+)?%)/i.test(lowered)) return false
  if (lowered.includes('machine learning') && lowered.includes('artificial intelligence')) return false
  if (lowered.includes('python') && lowered.includes('coding')) return false
  if (lowered.includes('docker') && lowered.includes('containers')) return false
  return true
}

function composeSummary(sentences = []) {
  const clean = []
  const seen = new Set()

  for (const sentence of sentences.map(cleanSummarySentence).filter(Boolean)) {
    const key = sentence.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
    if (!key || seen.has(key)) continue
    clean.push(sentence)
    seen.add(key)
  }

  const summary = clean.join(' ')
  return isValidGeneratedSummary(summary) ? splitCompleteSummarySentences(summary).join(' ') : ''
}

function normalizeGeneratedSummary(value = '') {
  const sentences = splitCompleteSummarySentences(value)
  if (sentences.length < 2 || sentences.length > 3) return ''
  const summary = sentences.join(' ')
  return isValidGeneratedSummary(summary) ? summary : ''
}

function sanitizeProfessionalSummary(value = '') {
  const raw = String(value || '').trim()
  if (!raw) return ''

  const withoutContactFragments = removeSummaryEllipses(raw)
    .replace(new RegExp(EMAIL_PATTERN.source, 'g'), '')
    .replace(new RegExp(PHONE_PATTERN.source, 'g'), '')
    .replace(new RegExp(LOCATION_PATTERN.source, 'g'), '')
    .replace(/\b(?:email|phone|mobile|location|address)\s*[:|-]\s*/gi, '')

  const cleanedLines = withoutContactFragments
    .split(/\n+/)
    .map((line) => line.trim().replace(/^[-*\u2022]\s+/, ''))
    .filter(Boolean)
    .filter((line) => !EMAIL_PATTERN.test(line))
    .filter((line) => !PHONE_PATTERN.test(line))
    .filter((line) => !/^[|+\-\s\d().]+$/.test(line))
    .filter((line) => !/^(summary|professional summary|contact|details)\s*:?$/i.test(line))

  const sentences = cleanedLines
    .join(' ')
    .replace(/\s*([|•])\s*/g, ' ')
    .replace(/\s+/g, ' ')
    .split(/(?<=[.!?])\s+/)
    .map((sentence) => sentence.trim())
    .filter(Boolean)

  const unique = []
  const seen = new Set()
  for (const sentence of sentences.length ? sentences : [cleanedLines.join(' ')]) {
    const key = sentence.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
    if (!key || seen.has(key)) continue
    seen.add(key)
    unique.push(sentence)
  }

  return unique.join(' ').trim()
}

function extractSkillsFromSource(sourceText = '') {
  return extractSectionLines(
    sourceText,
    [/^skills\b/i, /^technical skills\b/i, /^core skills\b/i, /^technologies\b/i],
    6,
  )
    .flatMap((line) => line.split(/[,|;]+/))
    .map((skill) => skill.trim())
    .filter(Boolean)
}

function flattenSkillItems(value) {
  if (Array.isArray(value)) {
    return value.flatMap((item) => flattenSkillItems(item))
  }
  if (value && typeof value === 'object') {
    return Object.values(value).flatMap((item) => flattenSkillItems(item))
  }
  return String(value || '')
    .split(/[,|;/]+/)
    .map((skill) => skill.trim().replace(/^[A-Za-z &]+:\s*/, ''))
    .filter(Boolean)
}

function getTopSkills(result = {}, sourceText = '') {
  const candidates = [
    ...flattenSkillItems(result?.optimized_skills),
    ...flattenSkillItems(result?.skills_to_highlight),
    ...flattenSkillItems(result?.added_keywords),
    ...extractSkillsFromSource(sourceText),
  ]

  return dedupeKeywords(candidates)
    .map((skill) => String(skill || '').trim())
    .filter(Boolean)
    .filter((skill) => !EMAIL_PATTERN.test(skill) && !PHONE_PATTERN.test(skill) && !LOCATION_PATTERN.test(skill))
    .slice(0, 5)
}

function resolveTargetRole(result = {}, currentJobTitle = '') {
  const raw = String(
    currentJobTitle
    || result?.job_title
    || result?.target_role
    || result?.role
    || result?.role_description
    || 'Software Engineer',
  ).trim()

  const cleaned = (raw.split(/\n+/).find(Boolean) || raw)
    .replace(/^(target role|role|job title)\s*[:|-]\s*/i, '')
    .replace(EMAIL_PATTERN, '')
    .replace(PHONE_PATTERN, '')
    .replace(LOCATION_PATTERN, '')
    .replace(/[.]+$/, '')
    .trim()

  const lowered = cleaned.toLowerCase()
  if (/machine learning|(^|\s)ml(\s|$)|artificial intelligence|\bai\b/.test(lowered)) return 'Machine Learning Engineer'
  if (/data scientist/.test(lowered)) return 'Data Scientist'
  if (/data analyst|analytics/.test(lowered)) return 'Data Analyst'
  if (/frontend|front-end|react/.test(lowered)) return 'Frontend Engineer'
  if (/backend|back-end|api/.test(lowered)) return 'Backend Engineer'
  if (/full stack|full-stack/.test(lowered)) return 'Full Stack Engineer'
  if (/devops|cloud|site reliability|sre/.test(lowered)) return 'Cloud Engineer'
  if (/software/.test(lowered)) return 'Software Engineer'
  return takeWords(cleaned, 5) || 'Software Engineer'
}

function inferSpecialization(role = '', skills = []) {
  const text = `${role} ${skills.join(' ')}`.toLowerCase()
  if (/(machine learning|ml|ai|data science|model|pytorch|tensorflow|mlops)/.test(text)) return 'scalable AI systems'
  if (/(data|analytics|pipeline|sql|pandas|etl)/.test(text)) return 'data pipelines'
  if (/(frontend|react|ui|javascript|typescript)/.test(text)) return 'web applications'
  if (/(backend|api|fastapi|node|django|flask|database)/.test(text)) return 'backend APIs'
  if (/(cloud|devops|docker|kubernetes|aws|azure|gcp)/.test(text)) return 'cloud deployment'
  return 'software systems'
}

function buildFallbackSummary(role = '') {
  return 'Machine Learning Engineer specializing in scalable AI systems and data pipelines. Built scalable backend systems for high-volume workloads.'
}

function metricValue(metric = '') {
  const number = String(metric || '').match(/\d+(?:\.\d+)?/)
  if (!number) return 0
  const base = Number(number[0]) || 0
  const lowered = String(metric || '').toLowerCase()
  if (/\d+(?:\.\d+)?\s*b/.test(lowered)) return base * 1000000000
  if (/\d+(?:\.\d+)?\s*m/.test(lowered)) return base * 1000000
  if (/\d+(?:\.\d+)?\s*k/.test(lowered)) return base * 1000
  return base
}

function durationValueMs(metric = '') {
  const number = String(metric || '').match(/\d+(?:\.\d+)?/)
  if (!number) return 0
  const value = Number(number[0]) || 0
  return /\b(s|sec|secs|second|seconds)\b/i.test(metric) ? value * 1000 : value
}

function extractBestDurationPair(value = '') {
  const durations = String(value || '').replace(/\*\*/g, '').match(/\b\d+(?:\.\d+)?\s*(?:ms|milliseconds?|s|sec|secs|seconds?)\b/gi) || []
  if (durations.length < 2) return ['', '']
  const ordered = durations.sort((a, b) => durationValueMs(b) - durationValueMs(a))
  const start = ordered[0]
  const end = ordered[ordered.length - 1]
  return durationValueMs(start) > durationValueMs(end) ? [start, end] : ['', '']
}

function extractBestDuration(value = '') {
  const durations = String(value || '').replace(/\*\*/g, '').match(/\b\d+(?:\.\d+)?\s*(?:ms|milliseconds?|s|sec|secs|seconds?)\b/gi) || []
  return durations.sort((a, b) => durationValueMs(a) - durationValueMs(b))[0] || ''
}

function extractBestMetric(value = '') {
  const text = String(value || '').replace(/\*\*/g, '')
  const percentages = text.match(/\b\d+(?:\.\d+)?%\b/g) || []
  if (percentages.length) {
    return percentages.sort((a, b) => metricValue(b) - metricValue(a))[0]
  }

  const countMetrics = text.match(/\b\d+(?:\.\d+)?\s*(?:K|M|B)?\+?\s*(?:daily\s+|monthly\s+)?(?:users|requests|data points|transactions|patients|entries|patient records|records)\b/gi) || []
  return countMetrics
    .map((metric) => metric.trim())
    .filter((metric) => !/^(19|20)\d{2}$/.test(metric))
    .filter((metric) => metricValue(metric) >= 10000)
    .sort((a, b) => metricValue(b) - metricValue(a))[0] || ''
}

function extractBestPercent(value = '') {
  const percentages = String(value || '').replace(/\*\*/g, '').match(/\b\d+(?:\.\d+)?%\b/g) || []
  return percentages.sort((a, b) => metricValue(b) - metricValue(a))[0] || ''
}

function extractBestCount(value = '') {
  const counts = String(value || '').replace(/\*\*/g, '').match(/\b\d+(?:\.\d+)?\s*(?:K|M|B)?\+?\s*(?:daily\s+|monthly\s+)?(?:users|requests|data points|transactions|patients|entries|patient records|records)\b/gi) || []
  return counts
    .map((metric) => metric.trim())
    .filter((metric) => !/^(19|20)\d{2}$/.test(metric))
    .sort((a, b) => metricValue(b) - metricValue(a))[0] || ''
}

function largeCountMetric(metric = '') {
  return metricValue(metric) >= 10000 ? metric : ''
}

function summaryScaleSuffix(countMetric = '', context = '') {
  if (!countMetric) return ''
  if (largeCountMetric(countMetric)) return ` for ${countMetric}`
  if (/\b(data|records|patients|entries|pipeline|processing|dataset)\b/i.test(context)) {
    return ' for large-scale datasets'
  }
  return ' for high-volume workloads'
}

function buildAchievementDetails(value = '') {
  const text = sanitizeProfessionalSummary(value)
    .replace(/\*\*/g, '')
    .replace(/[.]+$/, '')
    .replace(/\b(I|we)\s+/gi, '')
    .trim()

  if (!text) return null
  const percent = extractBestPercent(text)
  const countMetric = extractBestCount(text)
  const [startDuration, endDuration] = extractBestDurationPair(text)
  const bestDuration = extractBestDuration(text)

  const lowered = text.toLowerCase()
  let method = 'optimizing backend systems'
  if (/pipeline|processing|automation|automated|etl/.test(lowered)) method = 'building scalable data pipelines'
  else if (/docker|kubernetes|deploy|production|cloud/.test(lowered)) method = 'deploying production systems'
  else if (/java|jdbc|database|sql|query/.test(lowered)) method = 'optimizing backend systems'
  else if (/html|css|webpage|interface|frontend|react/.test(lowered)) method = 'optimizing backend systems'
  else if (/model|training|machine learning|prediction|classifier/.test(lowered)) method = 'optimizing model deployment'
  else if (/api|backend|service/.test(lowered)) method = 'optimizing backend systems'

  const scale = summaryScaleSuffix(countMetric, text)
  if (/\b(accuracy|precision|recall|f1|auc|score)\b/.test(lowered)) {
    return percent ? {
      sentence: `Improved model accuracy to ${percent} by ${method}.`,
      metricPriority: 2,
      metricScore: metricValue(percent),
    } : null
  }
  if (/\b(uptime|availability)\b/.test(lowered) && percent) {
    return {
      sentence: countMetric
        ? `Improved uptime to ${percent} by optimizing backend systems${scale}.`
        : `Improved uptime to ${percent} by deploying production systems.`,
      metricPriority: 1.5,
      metricScore: metricValue(percent),
    }
  }
  if (percent && /\b(reduc|latency|processing time|query speed|load time|response time|speed|efficien|throughput)\b/.test(lowered)) {
    if (/\b(query|database|sql)\b/.test(lowered)) {
      return {
        sentence: `Reduced data retrieval time by ${percent}${scale} by optimizing backend systems.`,
        metricPriority: 3,
        metricScore: metricValue(percent),
      }
    }
    if (/\b(processing|pipeline|etl)\b/.test(lowered)) {
      return {
        sentence: `Reduced data processing time by ${percent}${scale} by building scalable data pipelines.`,
        metricPriority: 3,
        metricScore: metricValue(percent),
      }
    }
    if (/\b(load time|response time|latency)\b/.test(lowered)) {
      return {
        sentence: `Reduced latency by ${percent}${scale} by optimizing backend systems.`,
        metricPriority: 3,
        metricScore: metricValue(percent),
      }
    }
    return {
      sentence: `Reduced processing time by ${percent}${scale} by optimizing backend systems.`,
      metricPriority: 3,
      metricScore: metricValue(percent),
    }
  }
  if (percent) {
    if (/\b(query|database|sql|retrieval)\b/.test(lowered)) {
      return {
        sentence: `Reduced data retrieval time by ${percent}${scale} by optimizing backend systems.`,
        metricPriority: 3,
        metricScore: metricValue(percent),
      }
    }
    if (/\b(processing|pipeline|etl|data|records|dataset)\b/.test(lowered)) {
      return {
        sentence: `Reduced data processing time by ${percent}${scale} by building scalable data pipelines.`,
        metricPriority: 3,
        metricScore: metricValue(percent),
      }
    }
    if (/\b(model|deploy|prediction|classifier)\b/.test(lowered)) {
      return {
        sentence: `Reduced model deployment time by ${percent}${scale} by optimizing model deployment.`,
        metricPriority: 3,
        metricScore: metricValue(percent),
      }
    }
    return {
      sentence: `Reduced processing time by ${percent}${scale} by ${method}.`,
      metricPriority: 3,
      metricScore: metricValue(percent),
    }
  }
  if (startDuration && endDuration && /\b(latency|processing|query|retrieval|load time|response time|speed)\b/.test(lowered)) {
    if (/\b(query|database|sql|retrieval)\b/.test(lowered)) {
      return {
        sentence: `Reduced data retrieval time from ${startDuration} to ${endDuration} by optimizing backend systems.`,
        metricPriority: 2.5,
        metricScore: durationValueMs(startDuration) - durationValueMs(endDuration),
      }
    }
    if (/\b(processing|pipeline|etl)\b/.test(lowered)) {
      return {
        sentence: `Reduced data processing time from ${startDuration} to ${endDuration} by building scalable data pipelines.`,
        metricPriority: 2.5,
        metricScore: durationValueMs(startDuration) - durationValueMs(endDuration),
      }
    }
    return {
      sentence: `Reduced latency from ${startDuration} to ${endDuration} by optimizing backend systems.`,
      metricPriority: 2.5,
      metricScore: durationValueMs(startDuration) - durationValueMs(endDuration),
    }
  }
  if (bestDuration && /\b(latency|processing|query|retrieval|load time|response time|speed)\b/.test(lowered)) {
    if (/\b(query|database|sql|retrieval)\b/.test(lowered)) {
      return {
        sentence: `Reduced data retrieval time to ${bestDuration} by optimizing backend systems.`,
        metricPriority: 2.5,
        metricScore: durationValueMs(bestDuration),
      }
    }
    if (/\b(processing|pipeline|etl)\b/.test(lowered)) {
      return {
        sentence: `Reduced data processing time to ${bestDuration} by building scalable data pipelines.`,
        metricPriority: 2.5,
        metricScore: durationValueMs(bestDuration),
      }
    }
    return {
      sentence: `Reduced latency to ${bestDuration} by optimizing backend systems.`,
      metricPriority: 2.5,
      metricScore: durationValueMs(bestDuration),
    }
  }
  const strongCountMetric = largeCountMetric(countMetric)
  if (strongCountMetric) {
    if (/\b(records|data points|patients|entries|patient records|transactions)\b/i.test(strongCountMetric)) {
      return {
        sentence: `Processed ${strongCountMetric} by building scalable data pipelines for large-scale datasets.`,
        metricPriority: 1,
        metricScore: Math.min(metricValue(strongCountMetric), 1000000),
      }
    }
    if (/\brequests\b/i.test(strongCountMetric)) {
      return {
        sentence: `Handled ${strongCountMetric} by optimizing backend systems for high-volume workloads.`,
        metricPriority: 1,
        metricScore: Math.min(metricValue(strongCountMetric), 1000000),
      }
    }
    if (/\busers\b/i.test(strongCountMetric)) {
      return {
        sentence: `Supported ${strongCountMetric} by deploying production systems for high-volume workloads.`,
        metricPriority: 1,
        metricScore: Math.min(metricValue(strongCountMetric), 1000000),
      }
    }
  }
  return null
}

function scoreImpactCandidate(value = '') {
  const text = String(value || '').toLowerCase()
  const impact = buildAchievementDetails(text)
  if (!impact) return 0
  const metric = extractBestPercent(text) || extractBestCount(text)
  let score = ((impact.metricPriority || 0) * 1000000) + (impact.metricScore || metricValue(metric))
  if (/\b(improv|reduc|increas|optimiz|efficien|accuracy|performance|deploy|automated)\b/.test(text)) score += 4
  if (/\b(data|pipeline|model|training|processing|business|user|engagement|latency|query)\b/.test(text)) score += 2
  return score
}

function extractAchievementDetails(result = {}, sourceText = '') {
  const improved = Array.isArray(result?.improved_bullets)
    ? result.improved_bullets.map((bullet) => bullet?.improved || bullet?.text || bullet)
    : []
  const added = Array.isArray(result?.new_bullets)
    ? result.new_bullets.map((bullet) => bullet?.text || bullet)
    : []
  const highlights = extractResumeHighlights(sourceText, 12)
  const candidates = [...improved, ...added, ...highlights]
    .map((item) => String(item || '').trim())
    .map((item) => sanitizeProfessionalSummary(item))
    .filter(Boolean)

  const impactCandidate = candidates
    .filter((item) => buildAchievementDetails(item))
    .sort((a, b) => scoreImpactCandidate(b) - scoreImpactCandidate(a))[0]

  return impactCandidate ? buildAchievementDetails(impactCandidate) : null
}

function buildProfessionalSummary(result = {}, sourceText = '', currentJobTitle = '') {
  const role = resolveTargetRole(result, currentJobTitle)
  const skills = getTopSkills(result, sourceText)
  const specialization = inferSpecialization(role, skills)
  const achievement = extractAchievementDetails(result, sourceText)

  if (!achievement) {
    return buildFallbackSummary(role)
  }

  const secondaryDomain = specialization === 'data pipelines' ? 'model deployment' : 'data pipelines'
  const sentences = [
    `${role} specializing in ${specialization} and ${secondaryDomain}.`,
    achievement.sentence,
  ]
  const summary = composeSummary(sentences)
  if (summary) return summary

  return sentences.map(cleanSummarySentence).filter(Boolean).join(' ')
}

function buildOnePageResumeContent(result = {}, sourceText = '', currentJobTitle = '') {
  const summarySource = [
    result?.optimized_summary,
    result?.summary,
    extractResumeHighlights(sourceText, 1)[0] || '',
  ].find((value) => String(value || '').trim())

  const optimizedSkills = Array.isArray(result?.optimized_skills)
    ? result.optimized_skills
    : Array.isArray(result?.skills_to_highlight)
      ? result.skills_to_highlight
      : []

  const skills = [...new Set(
    optimizedSkills
      .map((skill) => String(skill || '').trim())
      .filter(Boolean),
  )].slice(0, 14)

  const improvedBulletsRaw = Array.isArray(result?.improved_bullets)
    ? result.improved_bullets
        .map((bullet) => String(bullet?.improved || '').trim())
        .filter(Boolean)
    : []

  const newBulletsRaw = Array.isArray(result?.new_bullets)
    ? result.new_bullets
        .map((bullet) => String(bullet?.text || bullet || '').trim())
        .filter(Boolean)
    : []

  const fallbackBullets = extractResumeHighlights(sourceText, 8)
  const improvedBullets = improvedBulletsRaw.length
    ? improvedBulletsRaw
    : fallbackBullets.slice(0, 6)
  const newBullets = newBulletsRaw
  const bullets = [...improvedBullets, ...newBullets].filter(Boolean)
  const educationLines = extractEducationLines(sourceText, 4)

  return {
    headline: String(currentJobTitle || result?.job_title || result?.role_description || '').trim(),
    summary: normalizeGeneratedSummary(summarySource)
      || buildProfessionalSummary({ ...result, optimized_summary: summarySource }, sourceText, currentJobTitle),
    skills,
    educationLines,
    improvedBullets,
    newBullets,
    githubProjects: Array.isArray(result?.githubProjects) ? result.githubProjects : [],
    bullets: bullets.length ? bullets : fallbackBullets.slice(0, 7),
  }
}

async function fetchUserRepos({ accessToken = '', username = '' } = {}) {
  const headers = {
    Accept: 'application/vnd.github+json',
  }

  let reposUrl = 'https://api.github.com/user/repos?sort=updated&per_page=50&type=owner'
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`
  } else {
    const publicUsername = extractGithubUsername(username)
    if (!publicUsername) {
      throw new Error('Add your GitHub profile URL in Profile to include public GitHub projects.')
    }
    reposUrl = `https://api.github.com/users/${encodeURIComponent(publicUsername)}/repos?sort=updated&per_page=50&type=owner`
  }

  const repoRes = await fetch(reposUrl, { headers })
  if (!repoRes.ok) {
    if (!accessToken && repoRes.status === 404) {
      throw new Error('GitHub username not found. Check the GitHub URL in your profile.')
    }
    if (!accessToken && repoRes.status === 403) {
      throw new Error('GitHub public API limit reached. Try again later or reconnect GitHub from Profile.')
    }
    throw new Error('Could not fetch GitHub repositories.')
  }

  const repos = await repoRes.json()
  const enriched = await Promise.all(
    (Array.isArray(repos) ? repos : []).map(async (repo) => {
      let topics = []
      try {
        const topicsRes = await fetch(
          `https://api.github.com/repos/${repo.owner?.login}/${repo.name}/topics`,
          {
            headers: {
              ...headers,
              Accept: 'application/vnd.github.mercy-preview+json',
            },
          },
        )
        if (topicsRes.ok) {
          const topicsJson = await topicsRes.json()
          topics = Array.isArray(topicsJson?.names) ? topicsJson.names : []
        }
      } catch {
        topics = []
      }

      return {
        name: repo.name || '',
        description: repo.description || null,
        language: repo.language || null,
        topics,
        stars: Number(repo.stargazers_count) || 0,
        forks: Number(repo.forks_count) || 0,
        html_url: repo.html_url || '',
        updated_at: repo.updated_at || '',
      }
    }),
  )

  return enriched.filter((repo) => {
    const hasUsefulContext = repo.description || repo.topics.length > 0
    const looksLikeScratchRepo = /test|practice|demo|hello|tutorial|fork/i.test(repo.name)
    return hasUsefulContext && !looksLikeScratchRepo
  })
}

function matchReposToJobDescription(repos, jobDescription, skills = []) {
  const stopwords = new Set([
    'the', 'a', 'an', 'and', 'or', 'for', 'to', 'in', 'of', 'with',
    'is', 'are', 'was', 'were', 'it', 'this', 'that', 'on', 'at', 'by',
  ])
  const normalize = (text = '') => String(text || '')
    .toLowerCase()
    .replace(/[^a-z0-9+#.\s-]/g, ' ')
    .split(/\s+/)
    .map((token) => token.trim())
    .filter((token) => token && !stopwords.has(token))

  const referenceText = String(jobDescription || '').trim() || (Array.isArray(skills) ? skills.join(' ') : '')
  if (!referenceText || !Array.isArray(repos) || !repos.length) return []

  const repoTexts = repos.map((repo) => [repo.name, repo.description, repo.language, ...(repo.topics || [])]
    .filter(Boolean)
    .join(' '))
  const docs = [referenceText, ...repoTexts]
  const tokenDocs = docs.map(normalize)
  const vocabulary = [...new Set(tokenDocs.flat())]
  const totalDocs = tokenDocs.length
  const docFrequency = new Map()

  vocabulary.forEach((term) => {
    const count = tokenDocs.reduce((total, tokens) => total + (tokens.includes(term) ? 1 : 0), 0)
    docFrequency.set(term, count)
  })

  const vectorize = (tokens) => {
    const counts = new Map()
    tokens.forEach((token) => counts.set(token, (counts.get(token) || 0) + 1))
    const length = tokens.length || 1
    return vocabulary.map((term) => {
      const tf = (counts.get(term) || 0) / length
      const idf = Math.log((totalDocs + 1) / ((docFrequency.get(term) || 0) + 1)) + 1
      return tf * idf
    })
  }

  const cosine = (a, b) => {
    const dot = a.reduce((total, value, index) => total + value * b[index], 0)
    const magA = Math.sqrt(a.reduce((total, value) => total + value * value, 0))
    const magB = Math.sqrt(b.reduce((total, value) => total + value * value, 0))
    return magA && magB ? dot / (magA * magB) : 0
  }

  const referenceVector = vectorize(tokenDocs[0])
  return repos
    .map((repo, index) => ({
      ...repo,
      score: cosine(referenceVector, vectorize(tokenDocs[index + 1] || [])),
    }))
    .filter((repo) => repo.score > 0.1)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3)
}

function generateRepoBullet(repo) {
  const techStack = [repo.language, ...(repo.topics || []).slice(0, 3)].filter(Boolean).join(', ')
  const metric = repo.stars > 10
    ? `with ${repo.stars} GitHub stars`
    : repo.forks > 0
      ? `adopted by ${repo.forks} developers`
      : 'as an independent project'
  const desc = repo.description
    ? repo.description.charAt(0).toUpperCase() + repo.description.slice(1)
    : `Built and deployed a ${repo.name.replace(/-/g, ' ')} system`

  return `${desc}${techStack ? ` using ${techStack}` : ''}, ${metric}.`
}

function GitHubProjectsSection({ projects = [] }) {
  if (!Array.isArray(projects) || !projects.length) return null
  return (
    <section className="mb-7 rounded-lg border-[1.5px] border-[#e0e9f5] bg-[#f8fbff] px-6 py-5">
      <div className="mb-4 flex items-center gap-2">
        <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true" className="text-[#1a2b4a]">
          <path fill="currentColor" d="M8 0C3.58 0 0 3.67 0 8.2c0 3.62 2.29 6.69 5.47 7.77.4.08.55-.18.55-.39 0-.19-.01-.84-.01-1.52-2.01.38-2.53-.5-2.69-.96-.09-.24-.48-.96-.82-1.15-.28-.16-.68-.55-.01-.56.63-.01 1.08.59 1.23.84.72 1.24 1.87.89 2.33.68.07-.53.28-.89.51-1.1-1.78-.21-3.64-.91-3.64-4.04 0-.89.31-1.62.82-2.19-.08-.21-.36-1.04.08-2.16 0 0 .67-.22 2.2.84A7.42 7.42 0 0 1 8 3.98c.68 0 1.36.09 2 .27 1.52-1.06 2.19-.84 2.19-.84.44 1.12.16 1.95.08 2.16.51.57.82 1.3.82 2.19 0 3.14-1.87 3.83-3.65 4.04.29.26.54.75.54 1.52 0 1.1-.01 1.98-.01 2.25 0 .21.15.47.55.39A8.1 8.1 0 0 0 16 8.2C16 3.67 12.42 0 8 0Z" />
        </svg>
        <h2 className="text-[11px] font-bold uppercase tracking-[2px] text-[#1a2b4a]">GitHub Projects</h2>
        <span className="rounded bg-[#4a90d9] px-2 py-0.5 text-[10px] font-semibold text-white">AI-Matched</span>
      </div>
      <div>
        {projects.map((project, index) => (
          <article key={`${project.name}-${index}`} className={`py-3 ${index < projects.length - 1 ? 'border-b border-[#edf2f7]' : ''}`}>
            <div className="flex items-center justify-between gap-3">
              <a href={project.html_url} target="_blank" rel="noopener noreferrer" className="text-[13px] font-bold text-[#1a2b4a] hover:text-[#4a90d9]">
                {project.name} <span className="text-[#4a90d9]">&#8599;</span>
              </a>
              <div className="flex items-center gap-2">
                {project.language && <span className="rounded bg-[#e3eaf5] px-[7px] py-0.5 text-[10px] text-[#1a2b4a]">{project.language}</span>}
                <span className="text-[11px] text-[#888]">&#11088; {project.stars}</span>
              </div>
            </div>
            <p className="mt-2 flex text-[13px] leading-[1.7] text-[#333]">
              <span className="mr-2 text-[#4a90d9]">&#8226;</span>
              <span>{project.bullet}</span>
            </p>
          </article>
        ))}
      </div>
      <p className="mt-3 text-right text-[10px] text-[#aaa]">Repositories auto-matched to your job description using AI</p>
    </section>
  )
}

function clampScore(value) {
  const score = Number(value)
  if (!Number.isFinite(score)) return 0
  return Math.max(0, Math.min(100, Math.round(score)))
}

function getMatchScoreEstimate(data, addedKeywords = [], missingKeywords = []) {
  const backendScore = data?.match_score_estimate ?? null
  if (backendScore !== null) return clampScore(backendScore)

  const total = (addedKeywords?.length ?? 0) + (missingKeywords?.length ?? 0)
  return total > 0 ? Math.round(((addedKeywords?.length ?? 0) / total) * 100) : 0
}

function getConfidence(score) {
  if (score >= 75) return { label: 'High Confidence', color: '#3aad6e' }
  if (score >= 50) return { label: 'Medium Confidence', color: '#e09a3a' }
  return { label: 'Low Confidence', color: '#e05c5c' }
}

function WhyThisIsBetterPanel({ items = [] }) {
  const bullets = Array.isArray(items) ? items : []

  return (
    <section className="rounded-[10px] border border-[#1e3a5f] bg-[#0f1a2e] px-6 py-5">
      <h3 className="text-[11px] font-bold uppercase tracking-[2px] text-[#4a90d9]">Why This Is Better</h3>

      {!bullets.length ? (
        <p className="mt-4 text-[13px] leading-[1.8] text-[#e0e0e0]">All your bullets are already strong &#10003;</p>
      ) : (
        <div className="mt-4 space-y-5">
          {bullets.map((item, idx) => {
            const verbFrom = item?.verb_upgrade?.from ?? ''
            const verbTo = item?.verb_upgrade?.to ?? ''
            const keywords = Array.isArray(item?.keywords_added) ? item.keywords_added : []
            const metric = item?.metric_added ?? ''
            const reason = item?.improvement_reason ?? ''

            return (
              <article key={`why-better-${idx}`} className="border-b border-[#1e3a5f]/70 pb-4 last:border-b-0 last:pb-0">
                {(verbFrom || verbTo) && (
                  <p className="text-[13px] leading-[1.8] text-[#e0e0e0]">
                    <span className="mr-2 text-[#4a90d9]">&#10022;</span>
                    <span className="font-semibold">Stronger wording:</span>{' '}
                    {verbFrom && <span>&quot;{verbFrom}&quot;</span>}
                    {verbFrom && verbTo && <span> &rarr; </span>}
                    {verbTo && <span>&quot;{verbTo}&quot;</span>}
                  </p>
                )}

                {keywords.length > 0 && (
                  <div className="flex flex-wrap items-center gap-2 text-[13px] leading-[1.8] text-[#e0e0e0]">
                    <span className="text-[#4a90d9]">&#10022;</span>
                    <span className="font-semibold">Recruiter keywords added:</span>
                    {keywords.map((keyword, keyIdx) => (
                      <span key={`${keyword}-${keyIdx}`} className="rounded bg-[#1a3a5c] px-2 py-0.5 text-[11px] text-[#7ab8f5]">
                        {keyword}
                      </span>
                    ))}
                  </div>
                )}

                {metric && (
                  <p className="text-[13px] leading-[1.8] text-[#e0e0e0]">
                    <span className="mr-2 text-[#4a90d9]">&#10022;</span>
                    <span className="font-semibold">Measurable impact added:</span> {metric}
                  </p>
                )}

                {reason && <p className="mt-2 text-xs leading-5 text-[#8A8FA8]">{reason}</p>}
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}

function ATSMatchBreakdownPanel({ data }) {
  const addedKeywords = Array.isArray(data?.added_keywords) ? data.added_keywords : []
  const missingKeywords = Array.isArray(data?.missing_keywords) ? data.missing_keywords : []
  const atsTips = Array.isArray(data?.ats_tips) ? data.ats_tips : []
  const score = getMatchScoreEstimate(data, addedKeywords, missingKeywords)
  const confidence = getConfidence(score)

  return (
    <section className="rounded-[10px] border border-[#1e3a5f] bg-[#0f1a2e] px-6 py-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-[11px] font-bold uppercase tracking-[2px] text-[#4a90d9]">ATS Match Score</h3>
        <div className="flex items-center gap-3">
          <span className="text-2xl font-black text-white">{score}%</span>
          <span
            className="rounded-full px-2 py-1 text-[10px] font-bold uppercase tracking-wide"
            style={{ backgroundColor: `${confidence.color}22`, color: confidence.color, border: `1px solid ${confidence.color}66` }}
          >
            {confidence.label}
          </span>
        </div>
      </div>

      <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${score}%`, backgroundColor: confidence.color }} />
      </div>

      <div className="mt-5">
        <h4 className="text-xs font-bold uppercase tracking-wide text-[#e0e0e0]">&#9989; Matched Keywords</h4>
        {addedKeywords.length > 0 ? (
          <div className="mt-3 flex flex-wrap gap-2">
            {addedKeywords.map((keyword, idx) => (
              <span key={`${keyword}-${idx}`} className="rounded border border-[#2d6b4a] bg-[#1a3d2b] px-2 py-1 text-xs text-[#4caf88]">
                {keyword}
              </span>
            ))}
          </div>
        ) : (
          <p className="mt-3 text-[13px] leading-[1.8] text-[#8A8FA8]">Run optimization to see keyword matches</p>
        )}
      </div>

      {missingKeywords.length > 0 ? (
        <div className="mt-5">
          <h4 className="text-xs font-bold uppercase tracking-wide text-[#e0e0e0]">&#10060; Still Missing</h4>
          <div className="mt-3 flex flex-wrap gap-2">
            {missingKeywords.map((keyword, idx) => (
              <span key={`${keyword}-${idx}`} className="rounded border border-[#6b2d2d] bg-[#3d1a1a] px-2 py-1 text-xs text-[#e07070]">
                {keyword}
              </span>
            ))}
          </div>
        </div>
      ) : (
        <p className="mt-5 text-[13px] leading-[1.8] text-[#4caf88]">&#10003; Your resume already covers all critical ATS keywords</p>
      )}

      {atsTips.length > 0 && (
        <div className="mt-5">
          <h4 className="text-xs font-bold uppercase tracking-wide text-[#e0e0e0]">&#128161; ATS Tips</h4>
          <ul className="mt-3 space-y-2">
            {atsTips.map((tip, idx) => (
              <li key={`ats-tip-${idx}`} className="flex gap-2 text-[13px] leading-[1.7] text-[#e0e0e0]">
                <span className="text-[#4a90d9]">&bull;</span>
                <span>{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}

function buildProfessionalResumePrintHtml({ name, email, phone, content }) {
  const safeName = escapeHtml(name || 'Your Name')
  const safeHeadline = escapeHtml(content?.headline || '')
  const contactLine = [email, phone]
    .map((item) => String(item || '').trim())
    .filter(Boolean)
    .map((item, idx) => `${idx ? '<span class="contact-separator">&#8226;</span>' : ''}<span>${escapeHtml(item)}</span>`)
    .join('')

  const skillsText = (content?.skills || [])
    .map((skill) => escapeHtml(skill))
    .join(', ')

  const educationMarkup = (content?.educationLines || [])
    .map((line) => formatEducationLine(line))
    .filter(Boolean)
    .map((line, idx) => idx === 0
      ? `<div class="entry-heading"><h3>${escapeHtml(line)}</h3><span class="entry-date"></span></div>`
      : `<p class="company-line">${escapeHtml(line)}</p>`)
    .join('')

  const improvedBulletItems = (content?.improvedBullets || [])
    .map((bullet) => `<li>${escapeHtml(bullet)}</li>`)
    .join('')

  const newBulletItems = (content?.newBullets || [])
    .map((bullet) => `<li>${escapeHtml(bullet)}</li>`)
    .join('')

  const fallbackBulletItems = (content?.bullets || [])
    .map((bullet) => `<li>${escapeHtml(bullet)}</li>`)
    .join('')

  const githubProjects = Array.isArray(content?.githubProjects) ? content.githubProjects : []
  const githubProjectItems = githubProjects
    .map((repo, index) => `
      <article class="github-entry${index === githubProjects.length - 1 ? ' is-last' : ''}">
        <div class="github-entry-header">
          <a href="${escapeHtml(repo.html_url || '#')}" target="_blank" rel="noopener noreferrer" class="github-name">
            ${escapeHtml(repo.name || 'GitHub Project')} <span class="external-icon">&#8599;</span>
          </a>
          <div class="github-meta">
            ${repo.language ? `<span class="language-pill">${escapeHtml(repo.language)}</span>` : ''}
            <span class="stars">&#11088; ${Number(repo.stars) || 0}</span>
          </div>
        </div>
        <p class="bullet-line"><span>&#8226;</span>${escapeHtml(repo.bullet || generateRepoBullet(repo))}</p>
      </article>`)
    .join('')

  const summary = escapeHtml(content?.summary || 'No summary generated.')

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>${safeName} - Professional Resume</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<style>
  body { font-family: 'Inter', 'Segoe UI', Arial, sans-serif; }
  .resume-shell { box-shadow: 0 4px 20px rgba(0,0,0,0.08); max-width: 794px; margin: 0 auto; padding: 40px 48px; background: #fff; }
  .resume-header { margin-bottom: 14px; }
  .resume-name { color: #111111; font-size: 28px; font-weight: 800; letter-spacing: -0.5px; line-height: 1.12; }
  .resume-title { margin-top: 4px; color: #4a90d9; font-size: 14px; font-weight: 600; line-height: 1.5; }
  .contact-row { display: flex; flex-wrap: wrap; align-items: center; gap: 0; margin-bottom: 28px; color: #555; font-size: 13px; line-height: 1.6; }
  .contact-separator { margin: 0 10px; color: #4a90d9; }
  .resume-section { margin-bottom: 28px; }
  .resume-section.last-section { padding-bottom: 40px; margin-bottom: 0; }
  .section-heading { display: inline-block; width: fit-content; min-width: 36px; padding-bottom: 6px; border-bottom: 1.5px solid #4a90d9; color: #1a2b4a; font-size: 11px; font-weight: 700; letter-spacing: 2px; line-height: 1.2; text-transform: uppercase; }
  .section-body { margin-top: 12px; color: #333; font-size: 13px; line-height: 1.7; }
  .skills-text { margin-top: 12px; color: #333; font-size: 13px; font-weight: 500; line-height: 1.7; }
  .resume-entry { margin-top: 14px; margin-bottom: 20px; }
  .entry-heading { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; }
  .entry-heading h3 { color: #1a2b4a; font-size: 14px; font-weight: 700; line-height: 1.5; }
  .entry-date { flex-shrink: 0; color: #666; font-size: 12px; font-style: italic; line-height: 1.5; white-space: nowrap; }
  .company-line { margin-top: 1px; color: #4a90d9; font-size: 13px; font-weight: 500; line-height: 1.6; }
  .resume-list { list-style: none; margin-top: 8px; padding-left: 0; }
  .resume-list li, .bullet-line { display: flex; gap: 8px; margin-bottom: 7px; color: #333; font-size: 13px; line-height: 1.7; }
  .resume-list li::before { content: "\\2022"; flex-shrink: 0; color: #4a90d9; }
  .github-box { margin-bottom: 28px; padding: 20px 24px; border: 1.5px solid #e0e9f5; border-radius: 8px; background: #f8fbff; }
  .github-heading-row { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
  .github-badge { margin-left: 0; border-radius: 4px; background: #4a90d9; padding: 2px 8px; color: #fff; font-size: 10px; line-height: 1.4; }
  .github-entry { padding: 12px 0; border-bottom: 1px solid #edf2f7; }
  .github-entry.is-last { border-bottom: 0; }
  .github-entry-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
  .github-name { color: #1a2b4a; font-size: 13px; font-weight: 700; text-decoration: none; }
  .external-icon { color: #4a90d9; }
  .github-meta { display: flex; align-items: center; gap: 8px; }
  .language-pill { border-radius: 3px; background: #e3eaf5; padding: 2px 7px; color: #1a2b4a; font-size: 10px; line-height: 1.4; }
  .stars { color: #888; font-size: 11px; line-height: 1.4; }
  .bullet-line span { flex-shrink: 0; color: #4a90d9; }
  .github-footer { margin-top: 12px; text-align: right; color: #aaa; font-size: 10px; }
  @media print {
    body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .resume-shell { box-shadow: none; }
    @page { margin: 0; size: A4; }
  }
</style>
</head>
<body class="bg-[#eef1f5] text-[#333] antialiased print:bg-white">
  <div class="fixed inset-x-0 top-0 z-50 flex h-14 items-center justify-between border-b border-gray-200 bg-white px-6 print:hidden">
    <div class="flex items-center gap-3 text-sm font-bold text-gray-900">
      <div class="flex h-7 w-7 items-center justify-center rounded bg-blue-600 text-xs font-bold text-white">CL</div>
      CareerLens
    </div>
    <div class="flex items-center gap-4">
      <span class="text-xs text-gray-500">Professional resume preview for ${safeName}</span>
      <button class="rounded-md bg-blue-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-blue-700" onclick="window.print()">Download PDF</button>
    </div>
  </div>

  <main class="resume-shell mt-20 print:m-0 print:min-h-[297mm] print:w-[210mm] print:max-w-none">
    <header class="resume-header">
      <h1 class="resume-name">${safeName}</h1>
      ${safeHeadline ? `<p class="resume-title">${safeHeadline}</p>` : ''}
    </header>

    ${contactLine ? `<section class="contact-row">${contactLine}</section>` : ''}

    <section class="resume-section">
      <h2 class="section-heading">Summary</h2>
      <p class="section-body">${summary}</p>
    </section>

    ${skillsText ? `
    <section class="resume-section">
      <h2 class="section-heading">Skills</h2>
      <p class="skills-text">${skillsText}</p>
    </section>` : ''}

    <section class="resume-section">
      <h2 class="section-heading">Experience</h2>
      <article class="resume-entry">
        <div class="entry-heading">
          <h3>Relevant Experience</h3>
          <span class="entry-date"></span>
        </div>
        ${safeHeadline ? `<p class="company-line">${safeHeadline}</p>` : ''}
        <ul class="resume-list">
          ${improvedBulletItems || fallbackBulletItems}
        </ul>
      </article>
    </section>

    ${newBulletItems ? `
    <section class="resume-section">
      <h2 class="section-heading">Projects</h2>
      <article class="resume-entry">
        <div class="entry-heading">
          <h3>Projects &amp; Additional Impact</h3>
          <span class="entry-date"></span>
        </div>
        ${safeHeadline ? `<p class="company-line">${safeHeadline}</p>` : ''}
        <ul class="resume-list">
          ${newBulletItems}
        </ul>
      </article>
    </section>` : ''}

    ${githubProjectItems ? `
    <section class="github-box">
      <div class="github-heading-row">
        <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true">
          <path fill="#1a2b4a" d="M8 0C3.58 0 0 3.67 0 8.2c0 3.62 2.29 6.69 5.47 7.77.4.08.55-.18.55-.39 0-.19-.01-.84-.01-1.52-2.01.38-2.53-.5-2.69-.96-.09-.24-.48-.96-.82-1.15-.28-.16-.68-.55-.01-.56.63-.01 1.08.59 1.23.84.72 1.24 1.87.89 2.33.68.07-.53.28-.89.51-1.1-1.78-.21-3.64-.91-3.64-4.04 0-.89.31-1.62.82-2.19-.08-.21-.36-1.04.08-2.16 0 0 .67-.22 2.2.84A7.42 7.42 0 0 1 8 3.98c.68 0 1.36.09 2 .27 1.52-1.06 2.19-.84 2.19-.84.44 1.12.16 1.95.08 2.16.51.57.82 1.3.82 2.19 0 3.14-1.87 3.83-3.65 4.04.29.26.54.75.54 1.52 0 1.1-.01 1.98-.01 2.25 0 .21.15.47.55.39A8.1 8.1 0 0 0 16 8.2C16 3.67 12.42 0 8 0Z" />
        </svg>
        <h2 class="section-heading">GitHub Projects</h2>
        <span class="github-badge">AI-Matched</span>
      </div>
      ${githubProjectItems}
      <p class="github-footer">Repositories auto-matched to your job description using AI</p>
    </section>` : ''}

    ${educationMarkup ? `
    <section class="resume-section last-section">
      <h2 class="section-heading">Education</h2>
      <article class="resume-entry">
        ${educationMarkup}
      </article>
    </section>` : ''}
  </main>
</body>
</html>`
}

function buildMergedOptimizedResume(originalResumeText = '', result = {}, currentJobTitle = '') {
  const original = String(originalResumeText || '').trim()
  const generatedSummary = buildProfessionalSummary(result, originalResumeText, currentJobTitle)
  const summary = normalizeGeneratedSummary(result?.optimized_summary || result?.summary || '') || generatedSummary
  const skills = Array.isArray(result?.optimized_skills) ? result.optimized_skills : []
  const improvedBullets = Array.isArray(result?.improved_bullets) ? result.improved_bullets : []
  const newBullets = Array.isArray(result?.new_bullets) ? result.new_bullets : []

  const sections = [
    original,
    summary ? `PROFESSIONAL SUMMARY\n${summary}` : '',
    skills.length ? `CORE SKILLS\n${skills.join(', ')}` : '',
    improvedBullets.length
      ? `OPTIMIZED BULLETS\n${improvedBullets.map((bullet) => `- ${bullet.improved}`).join('\n')}`
      : '',
    newBullets.length
      ? `NEW BULLETS\n${newBullets.map((bullet) => `- ${bullet.text || bullet}`).join('\n')}`
      : '',
  ]

  return sections.filter(Boolean).join('\n\n').trim()
}

function buildOptimizerToolText(result, summaryOverride = '', currentJobTitle = '') {
  const sourceText = result?.source_resume_text || ''
  const generatedSummary = buildProfessionalSummary(result, sourceText, currentJobTitle)
  const summary = normalizeGeneratedSummary(summaryOverride) || generatedSummary
  const merged = buildMergedOptimizedResume(result?.source_resume_text || '', {
    ...result,
    optimized_summary: summary,
  }, currentJobTitle)
  if (merged) return merged

  return [
    summary,
    (result?.optimized_skills || []).join(', '),
    ...(result?.improved_bullets || []).map((bullet) => bullet.improved),
    ...(result?.new_bullets || []).map((bullet) => bullet.text || bullet),
  ].filter(Boolean).join('\n\n')
}

async function blobToBase64(blob) {
  const arrayBuffer = await blob.arrayBuffer()
  const bytes = new Uint8Array(arrayBuffer)
  let binary = ''
  const chunkSize = 8192
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunkSize))
  }
  return btoa(binary)
}

async function buildResumePdfBase64FromText(text, jobTitle = '') {
  const items = []
  addWrapped(items, normalizePdfText(text), { size: 10, maxChars: 92 })
  const pdf = buildPdf(items)
  const blob = new Blob([pdf], { type: 'application/pdf' })
  return blobToBase64(blob)
}

function buildPdf(items) {
  const pageWidth = 612
  const pageHeight = 792
  const marginX = 54
  const topY = 742
  const bottomY = 54
  const pages = []
  let commands = []
  let currentY = topY

  for (const item of items) {
    const step = item.blank ? item.height : item.size + 5
    if (currentY - step < bottomY) {
      pages.push(commands.join('\n'))
      commands = []
      currentY = topY
    }
    if (item.blank) { currentY -= item.height; continue }
    const x = marginX + (item.indent || 0)
    commands.push(`BT /${item.font} ${item.size} Tf 0 g 1 0 0 1 ${x} ${currentY} Tm (${escapePdfText(item.text)}) Tj ET`)
    currentY -= item.size + 5
  }
  if (!pages.length || commands.length) pages.push(commands.join('\n'))

  const objects = [null]
  objects[1] = '<< /Type /Catalog /Pages 2 0 R >>'
  objects[3] = '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>'
  objects[4] = '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>'

  const kids = []
  let objectIndex = 5

  for (const stream of pages) {
    const pageObject = objectIndex++
    const contentObject = objectIndex++
    kids.push(`${pageObject} 0 R`)
    objects[pageObject] = `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${pageWidth} ${pageHeight}] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents ${contentObject} 0 R >>`
    objects[contentObject] = `<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`
  }

  objects[2] = `<< /Type /Pages /Count ${pages.length} /Kids [${kids.join(' ')}] >>`

  let pdf = '%PDF-1.4\n'
  const offsets = [0]
  for (let i = 1; i < objects.length; i += 1) {
    offsets[i] = pdf.length
    pdf += `${i} 0 obj\n${objects[i]}\nendobj\n`
  }
  const xrefOffset = pdf.length
  pdf += `xref\n0 ${objects.length}\n`
  pdf += '0000000000 65535 f \n'
  for (let i = 1; i < objects.length; i += 1) {
    pdf += `${String(offsets[i]).padStart(10, '0')} 00000 n \n`
  }
  pdf += `trailer\n<< /Size ${objects.length} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`
  return pdf
}

function buildSinglePagePdf(items) {
  const pageWidth = 612
  const pageHeight = 792
  const marginX = 42
  const topY = 754
  const bottomY = 42
  const commands = []
  let currentY = topY

  for (const item of items) {
    const step = item.blank ? item.height : item.size + 4
    if (currentY - step < bottomY) break
    if (item.blank) {
      currentY -= item.height
      continue
    }
    const x = marginX + (item.indent || 0)
    commands.push(`BT /${item.font} ${item.size} Tf 0 g 1 0 0 1 ${x} ${currentY} Tm (${escapePdfText(item.text)}) Tj ET`)
    currentY -= item.size + 4
  }

  const stream = commands.join('\n')
  const objects = [null]
  objects[1] = '<< /Type /Catalog /Pages 2 0 R >>'
  objects[2] = '<< /Type /Pages /Count 1 /Kids [5 0 R] >>'
  objects[3] = '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>'
  objects[4] = '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>'
  objects[5] = `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${pageWidth} ${pageHeight}] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents 6 0 R >>`
  objects[6] = `<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`

  let pdf = '%PDF-1.4\n'
  const offsets = [0]
  for (let i = 1; i < objects.length; i += 1) {
    offsets[i] = pdf.length
    pdf += `${i} 0 obj\n${objects[i]}\nendobj\n`
  }
  const xrefOffset = pdf.length
  pdf += `xref\n0 ${objects.length}\n`
  pdf += '0000000000 65535 f \n'
  for (let i = 1; i < objects.length; i += 1) {
    pdf += `${String(offsets[i]).padStart(10, '0')} 00000 n \n`
  }
  pdf += `trailer\n<< /Size ${objects.length} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`
  return pdf
}

function addWrapped(items, text, options = {}) {
  const { font = 'F1', size = 11, maxChars = 88, before = 0, after = 0, indent = 0 } = options
  if (before) items.push({ blank: true, height: before })
  for (const line of wrapPdfText(text, maxChars)) {
    if (!line) items.push({ blank: true, height: size })
    else items.push({ text: line, font, size, indent })
  }
  if (after) items.push({ blank: true, height: after })
}

function addFormattedResume(items, text) {
  const lines = normalizePdfText(text).split('\n')
  let previousWasHeading = false
  for (const rawLine of lines) {
    const line = rawLine.trim()
    if (!line) {
      items.push({ blank: true, height: previousWasHeading ? 8 : 6 })
      previousWasHeading = false
      continue
    }
    if (isHeadingLine(line)) {
      addWrapped(items, line.replace(/:$/, ''), { font: 'F2', size: 12, before: 8, after: 4 })
      previousWasHeading = true
      continue
    }
    const isBullet = /^[-*•]\s+/.test(line)
    const bulletText = isBullet ? line.replace(/^[-*•]\s+/, '') : line
    addWrapped(items, `${isBullet ? '- ' : ''}${bulletText}`, { size: 10, maxChars: 92, indent: isBullet ? 10 : 0 })
    previousWasHeading = false
  }
}

function buildOptimizedPdfBlob(opt, jobTitle, originalResumeText = '') {
  const items = []
  const sourceText = String(originalResumeText || opt?.source_resume_text || opt?.optimized_resume || '').trim()
  const headerSource = sourceText || opt?.optimized_resume || ''
  const headerInfo = extractResumeHeader(headerSource)
  const name = headerInfo.name
  const contactLines = headerInfo.contactLines
  const content = buildOnePageResumeContent(opt, sourceText, jobTitle)

  addWrapped(items, name || (content.headline ? `Optimized Resume - ${content.headline}` : 'Optimized Resume'), { font: 'F2', size: 18, maxChars: 48, after: 2 })
  if (contactLines.length) {
    addWrapped(items, contactLines.join(' | '), { size: 8.5, maxChars: 104, after: 2 })
  }
  if (content.headline) {
    addWrapped(items, content.headline, { size: 9, maxChars: 104, after: 6 })
  }
  addWrapped(items, 'PROFESSIONAL SUMMARY', { font: 'F2', size: 9.5, after: 2 })
  addWrapped(items, content.summary || 'No summary generated.', { size: 8.6, maxChars: 104, after: 5 })

  if (content.skills.length) {
    addWrapped(items, 'CORE SKILLS', { font: 'F2', size: 9.5, before: 2, after: 2 })
    addWrapped(items, content.skills.join(', '), { size: 8.4, maxChars: 108, after: 5 })
  }

  if (content.educationLines.length) {
    addWrapped(items, 'EDUCATION', { font: 'F2', size: 9.5, before: 2, after: 2 })
    content.educationLines.forEach((line) => {
      const educationLine = formatEducationLine(line)
      if (educationLine) addWrapped(items, educationLine, { size: 8.4, maxChars: 104, after: 1 })
    })
  }

  if (content.improvedBullets.length) {
    addWrapped(items, 'OPTIMIZED EXPERIENCE', { font: 'F2', size: 9.5, before: 2, after: 2 })
    content.improvedBullets.forEach((bullet) => {
      addWrapped(items, `- ${bullet}`, { size: 8.4, maxChars: 98, indent: 8, after: 1 })
    })
  }

  if (content.newBullets.length) {
    addWrapped(items, 'ROLE-SPECIFIC POINTS', { font: 'F2', size: 9.5, before: 2, after: 2 })
    content.newBullets.forEach((bullet) => {
      addWrapped(items, `- ${bullet}`, { size: 8.4, maxChars: 98, indent: 8, after: 1 })
    })
  } else if (!content.improvedBullets.length && content.bullets.length) {
    addWrapped(items, 'EXPERIENCE HIGHLIGHTS', { font: 'F2', size: 9.5, before: 2, after: 2 })
    content.bullets.forEach((bullet) => {
      addWrapped(items, `- ${bullet}`, { size: 8.4, maxChars: 98, indent: 8, after: 1 })
    })
  }

  const pdf = buildSinglePagePdf(items)
  const blob = new Blob([pdf], { type: 'application/pdf' })
  const safeTitle = (jobTitle || 'optimized-resume').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'optimized-resume'
  return { blob, filename: `${safeTitle}.pdf` }
}

function downloadOptimizedPdf(opt, jobTitle, originalResumeText = '') {
  const { blob, filename } = buildOptimizedPdfBlob(opt, jobTitle, originalResumeText)
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export default function ResumeOptimizer({ prefillResume = '', prefillJD = '', prefillJobTitle = '' }) {
  const { user: authUser } = useAuth()
  const STORAGE_KEY = 'careerlens:resume_optimizer:state'
  const [resumeText, setResumeText] = useState(prefillResume)
  const [resumeFile, setResumeFile] = useState(null)
  const [jobDesc, setJobDesc] = useState(prefillJD)
  const [jobTitle, setJobTitle] = useState(prefillJobTitle)
  const [result, setResult] = useState(null)
  const [editedSummary, setEditedSummary] = useState(result?.optimized_summary || result?.summary || '')
  const [comparisonView, setComparisonView] = useState('split')
  const [pdfUrl, setPdfUrl] = useState('')
  const [pdfLoading, setPdfLoading] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [pdfError, setPdfError] = useState('')
  const [pdfNotice, setPdfNotice] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [dragging, setDragging] = useState(false)
  const fileRef = useRef(null)
  const [checkedTips, setCheckedTips] = useState({})
  const [includeGitHubProjects, setIncludeGitHubProjects] = useState(false)
  const [githubProjects, setGithubProjects] = useState([])
  const [githubProjectsLoading, setGithubProjectsLoading] = useState(false)
  const [githubProjectsError, setGithubProjectsError] = useState('')
  const restoredSummaryRef = useRef(false)
  const buttonMotion = {
    whileHover: { scale: 1.03, y: -1 },
    whileTap: { scale: 0.97 },
    transition: { duration: 0.15, ease: 'easeOut' },
  }

  // ── Send optimized text to Job Match or ATS Checker ──────
  const sendToTool = (path) => {
    const text = buildOptimizerToolText(result, editedSummary, jobTitle)
    localStorage.setItem('careerlens_resume_text', text)
    window.location.href = path
  }

  useEffect(() => {
    const hasPrefill = Boolean(prefillResume || prefillJD || prefillJobTitle)
    if (hasPrefill) return
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (!raw) return
      const saved = JSON.parse(raw)
      if (typeof saved?.resumeText === 'string') setResumeText(saved.resumeText)
      if (typeof saved?.jobDesc === 'string') setJobDesc(saved.jobDesc)
      if (typeof saved?.jobTitle === 'string') setJobTitle(saved.jobTitle)
      if (saved?.result && typeof saved.result === 'object' && !Array.isArray(saved.result)) {
        setResult(normalizeOptimizationResult(saved.result))
      }
      if (typeof saved?.comparisonView === 'string') setComparisonView(saved.comparisonView)
      if (typeof saved?.editedSummary === 'string') {
        setEditedSummary(normalizeGeneratedSummary(saved.editedSummary))
        restoredSummaryRef.current = true
      }
      if (saved?.checkedTips && typeof saved.checkedTips === 'object') {
        setCheckedTips(saved.checkedTips)
      }
      if (typeof saved?.includeGitHubProjects === 'boolean') {
        setIncludeGitHubProjects(saved.includeGitHubProjects)
      }
      if (Array.isArray(saved?.githubProjects)) {
        setGithubProjects(saved.githubProjects)
      }
    } catch {
      // ignore invalid localStorage
    }
  }, [prefillResume, prefillJD, prefillJobTitle])

  useEffect(() => {
    if (!result) return
    const sourceText = resumeText || prefillResume || result?.source_resume_text || result?.optimized_resume || ''
    const generatedSummary = normalizeGeneratedSummary(result?.optimized_summary || result?.summary || '')
      || buildProfessionalSummary(result, sourceText, jobTitle)
    if (result && restoredSummaryRef.current) {
      restoredSummaryRef.current = false
      setEditedSummary((current) => normalizeGeneratedSummary(current) || generatedSummary)
      return
    }
    setEditedSummary(generatedSummary)
    setCheckedTips({})
  }, [result, resumeText, prefillResume, jobTitle])

  useEffect(() => {
    const payload = {
      resumeText,
      jobDesc,
      jobTitle,
      result,
      editedSummary,
      comparisonView,
      checkedTips,
      includeGitHubProjects,
      githubProjects,
    }
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
    } catch {
      // ignore storage quota errors
    }
  }, [resumeText, jobDesc, jobTitle, result, editedSummary, comparisonView, checkedTips, includeGitHubProjects, githubProjects])

  useEffect(() => {
    if (!resumeText || resumeText.trim().length < 3) return
    const contact = extractContactInfo(resumeText)
    if (contact.name || contact.email || contact.phone) {
      try { localStorage.setItem('careerlens:resume_contact', JSON.stringify(contact)) } catch {}
    }
  }, [resumeText])

  const generateStyledPDF = (resultData, meta = {}) => {
    const stored = readStoredContact()
    const fallbackSourceText = resumeText || prefillResume || resultData?.source_resume_text || resultData?.optimized_resume || ''
    const fallbackContact = extractContactInfo(resumeText || prefillResume || fallbackSourceText)
    const name  = meta.name  || fallbackContact.name || stored.name || 'Your Name'
    const email = meta.email || fallbackContact.email || stored.email || ''
    const phone = meta.phone || fallbackContact.phone || stored.phone || ''
    const summary = normalizeGeneratedSummary(meta.summary || editedSummary)
      || buildProfessionalSummary(resultData, fallbackSourceText, jobTitle)
    const onePageContent = buildOnePageResumeContent(
      {
        ...resultData,
        optimized_summary: summary,
        githubProjects: includeGitHubProjects ? githubProjects : [],
      },
      fallbackSourceText,
      jobTitle,
    )
    if (onePageContent) {
      const html = buildProfessionalResumePrintHtml({
        name,
        email,
        phone,
        content: onePageContent,
      })
      const win = window.open('', '_blank')
      if (win) {
        win.document.write(html)
        win.document.close()
        win.focus()
      }
      return
    }

  }

  const handleFile = async (file) => {
    if (!file || (file.type !== 'application/pdf' && !file.name?.toLowerCase().endsWith('.pdf'))) {
      setError('Upload a PDF.')
      return
    }
    setResumeFile(file)
    setError('')
    try {
      const arrayBuffer = await file.arrayBuffer()
      const uint8Array = new Uint8Array(arrayBuffer)
      let binary = ''
      const chunkSize = 8192
      for (let i = 0; i < uint8Array.length; i += chunkSize) {
        binary += String.fromCharCode.apply(null, uint8Array.subarray(i, i + chunkSize))
      }

      const res = await api.extractResumeText({ pdf_base64: btoa(binary) })
      const extracted = String(res?.text || '').trim()
      if (extracted && extracted.length > 20) {
        setResumeText(extracted)
        setError('')
      } else {
        setResumeText('')
        setError('Could not extract text from this PDF. Please paste your resume text manually.')
      }
    } catch (err) {
      const message = err?.message || 'Could not extract text from this PDF.'
      setResumeText('')
      setError(`${message} Please paste your resume text manually.`)
    }
  }

  const runGithubProjectMatch = async ({ refresh = false } = {}) => {
    if (githubProjectsLoading) return
    if (!refresh && githubProjects.length) return

    setGithubProjectsLoading(true)
    setGithubProjectsError('')
    try {
      let accessToken = authUser?.provider_token
        || authUser?.github_access_token
        || authUser?.user_metadata?.provider_token
        || authUser?.app_metadata?.provider_token

      if (!accessToken) {
        const { data } = await supabase.auth.getSession()
        accessToken = data?.session?.provider_token || data?.session?.user?.provider_token || ''
      }

      const githubUsername = await resolveGithubUsername(authUser)
      let repos = []

      try {
        repos = await fetchUserRepos({ accessToken, username: githubUsername })
      } catch (repoErr) {
        if (!accessToken || !githubUsername) throw repoErr
        repos = await fetchUserRepos({ username: githubUsername })
      }

      const currentSkills = Array.isArray(result?.optimized_skills) ? result.optimized_skills : []
      const matched = matchReposToJobDescription(repos, jobDesc, currentSkills)
        .map((repo) => ({ ...repo, bullet: generateRepoBullet(repo) }))

      setGithubProjects(matched)
      setResult((current) => current ? { ...current, githubProjects: matched } : current)
      if (!matched.length) {
        setGithubProjectsError('No GitHub repositories matched this job description strongly enough.')
      }
    } catch (err) {
      setGithubProjectsError(err.message || 'Could not fetch and match GitHub repositories.')
    } finally {
      setGithubProjectsLoading(false)
    }
  }

  const handleGitHubProjectsToggle = async (checked) => {
    setIncludeGitHubProjects(checked)
    if (checked && !githubProjects.length) {
      await runGithubProjectMatch()
    }
  }

  const handleRefreshGitHubProjects = async () => {
    setGithubProjects([])
    setResult((current) => current ? { ...current, githubProjects: [] } : current)
    await runGithubProjectMatch({ refresh: true })
  }

  const handleOptimize = async () => {
    if (!resumeText.trim()) {
      if (resumeFile) {
        setError('Could not extract text. Please paste your resume text manually.')
      } else {
        setError('Please upload or paste your resume.')
      }
      return
    }
    if (!jobDesc.trim()) {
      setError('Please paste the job description.')
      return
    }
    setLoading(true)
    setError('')
    setResult(null)
    if (pdfUrl) URL.revokeObjectURL(pdfUrl)
    setPdfUrl('')
    setShowPreview(false)
    setPdfError('')
    setPdfNotice('')
    setIncludeGitHubProjects(false)
    setGithubProjects([])
    setGithubProjectsError('')
    try {
      const res = await api.optimizeResume({
        resume_text: resumeText,
        job_description: jobDesc,
        job_title: jobTitle,
      })
      const normalized = normalizeOptimizationResult(res.optimization)
      if (normalized) {
        normalized.source_resume_text = resumeText
        normalized.optimized_summary = normalizeGeneratedSummary(normalized.optimized_summary)
          || buildProfessionalSummary(normalized, resumeText, jobTitle)
      }
      const optimizedText = buildMergedOptimizedResume(resumeText, normalized, jobTitle)

      if (normalized && optimizedText) {
        normalized.optimized_resume = optimizedText
      }

      try {
        const beforePdf = await buildResumePdfBase64FromText(resumeText, `${jobTitle || 'resume'}-before`)
        const afterPdf = await buildResumePdfBase64FromText(
          optimizedText || resumeText,
          `${jobTitle || 'resume'}-after`,
        )

        const [beforeRes, afterRes] = await Promise.all([
          api.checkATS({ resume_pdf: beforePdf, job_description: jobDesc }),
          api.checkATS({ resume_pdf: afterPdf, job_description: jobDesc }),
        ])

        const beforeScore = Number(beforeRes?.result?.ats_score)
        const afterScore = Number(afterRes?.result?.ats_score)

        if (!Number.isNaN(beforeScore)) normalized.ats_before = beforeScore
        if (!Number.isNaN(afterScore)) {
          normalized.ats_after = afterScore
          normalized.ats_score_estimate = afterScore
        }
      } catch {
        // Preserve optimization results even if ATS re-scoring fails.
      }

      setResult(normalized)
    } catch (err) {
      setError(err.message || 'Optimization failed. Please try again.')
    }
    setLoading(false)
  }

  const fetchPdf = async (resumeForPdf, opt) => {
    if (pdfLoading) return pdfUrl
    if (pdfUrl) return pdfUrl
    setPdfLoading(true); setPdfError(''); setPdfNotice('')
    try {
      const blob = await api.generateOptimizedPdf({ resume_text: resumeForPdf, job_title: jobTitle })
      const url = URL.createObjectURL(blob)
      if (pdfUrl) URL.revokeObjectURL(pdfUrl)
      setPdfUrl(url)
      return url
    } catch (err) {
      try {
        const local = buildOptimizedPdfBlob(opt || { optimized_resume: resumeForPdf }, jobTitle, resumeText)
        const url = URL.createObjectURL(local.blob)
        if (pdfUrl) URL.revokeObjectURL(pdfUrl)
        setPdfUrl(url)
        setPdfNotice('Using local PDF generator.')
        return url
      } catch (localErr) {
        setPdfError(err.message || localErr.message || 'PDF generation failed.')
        return ''
      }
    } finally { setPdfLoading(false) }
  }

  const handleDownloadPdf = async (resumeForPdf) => {
    const url = await fetchPdf(resumeForPdf, result)
    if (url) {
      const link = document.createElement('a')
      const safeTitle = (jobTitle || 'optimized-resume').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'optimized-resume'
      link.href = url; link.download = `${safeTitle}.pdf`; link.click()
      return
    }
    if (resumeForPdf) downloadOptimizedPdf(result, jobTitle, resumeText)
  }

  const contactMeta = extractContactInfo(resumeText)
  const pdfMeta = { name: contactMeta.name || '', email: contactMeta.email || '', phone: contactMeta.phone || '' }
  const hasOptimizationResult = result && typeof result === 'object' && !Array.isArray(result)

  // ── RESULT SCREEN ────────────────────────────────────────
  if (hasOptimizationResult) {
    const improvedBullets = Array.isArray(result?.improved_bullets) ? result.improved_bullets : []
    const newBullets      = Array.isArray(result?.new_bullets)      ? result.new_bullets      : []
    const addedKeywords   = Array.isArray(result?.added_keywords)   ? result.added_keywords   : []
    const optimizedSkills = Array.isArray(result?.optimized_skills) ? result.optimized_skills : []
    const atsTips         = Array.isArray(result?.ats_tips)         ? result.ats_tips         : []
    const atsBefore = typeof result?.ats_before === 'number' ? result.ats_before : 0
    const atsAfter  = typeof result?.ats_after  === 'number' ? result.ats_after  : atsBefore
    const atsGain   = atsAfter - atsBefore
    const gainPrefix = atsGain > 0 ? '+' : ''
    const displaySummary = normalizeGeneratedSummary(editedSummary)
      || buildProfessionalSummary(result, resumeText || result?.source_resume_text || '', jobTitle)

    const handleStyledDownload = () => {
      generateStyledPDF({ ...result, optimized_summary: displaySummary }, pdfMeta)
      toast.success('Professional resume preview opened.')
    }
    const toggleTip = (idx) => setCheckedTips((prev) => ({ ...prev, [idx]: !prev[idx] }))

    return (
      <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
      <div className="max-w-6xl w-full mx-auto space-y-8">

        {/* ── Hero impact card ─────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          style={{
            position: 'relative',
            background: 'rgba(24,27,37,0.72)',
            border: '1px solid rgba(255,59,59,0.2)',
            borderRadius: '20px',
            padding: '48px 40px',
            overflow: 'hidden',
            marginBottom: '24px',
          }}
          className="space-y-6"
        >
          <div style={{
            position: 'absolute', top: 0, left: '8%', right: '8%', height: '1px',
            background: 'linear-gradient(90deg, transparent, rgba(255,59,59,0.85), rgba(180,20,20,0.7), transparent)',
          }} />
          <div style={{
            position: 'absolute', top: '-60px', left: '50%', transform: 'translateX(-50%)',
            width: '500px', height: '300px', borderRadius: '50%',
            background: 'radial-gradient(ellipse, rgba(255,59,59,0.09) 0%, transparent 65%)',
            pointerEvents: 'none',
          }} />

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '48px', flexWrap: 'wrap' }}>
            <div style={{ textAlign: 'center' }}>
              <AnimatedScoreCircle score={atsBefore} size={120} label="Before" color="#FF8C42" />
            </div>
            <div style={{ textAlign: 'center' }}>
              <motion.div
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.4, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              >
                <div style={{
                  fontSize: 'clamp(52px, 8vw, 80px)', fontWeight: 900,
                  letterSpacing: '-3px', lineHeight: 1,
                  color: '#FF3B3B',
                }}>
                  <StatNumber value={atsGain} prefix={gainPrefix} />
                </div>
                <p style={{
                  fontSize: '11px', letterSpacing: '2px', textTransform: 'uppercase',
                  color: 'rgba(120,113,108,0.7)', marginTop: '4px',
                }}>
                  ATS Score Boost
                </p>
              </motion.div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <AnimatedScoreCircle score={atsAfter} size={120} label="After" color="#10b981" />
            </div>
          </div>

          {result.overall_improvement && (
            <p className="text-center text-[#d6d3d1] italic">"{result.overall_improvement}"</p>
          )}

          {/* ── Action buttons row ───────────────────────── */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 flex-wrap">
            <motion.button {...buttonMotion} onClick={handleStyledDownload} className="btn-primary flex items-center gap-2">
              <Download size={16} /> Download Professional Resume PDF
            </motion.button>
            <motion.button
              {...buttonMotion}
              onClick={() => sendToTool('/dashboard/job-match')}
              className="btn-primary flex items-center gap-2">
              <Briefcase size={15} /> Test Job Matches
            </motion.button>
            <motion.button
              {...buttonMotion}
              onClick={() => sendToTool('/dashboard/ats-checker')}
              className="btn-ghost flex items-center gap-2">
              <Target size={15} /> Check ATS Score
            </motion.button>
            <motion.button
              {...buttonMotion}
              onClick={() => {
                if (pdfUrl) URL.revokeObjectURL(pdfUrl)
                localStorage.removeItem(STORAGE_KEY)
                setResult(null); setPdfUrl(''); setShowPreview(false); setPdfError(''); setPdfNotice('')
                setIncludeGitHubProjects(false); setGithubProjects([]); setGithubProjectsError('')
              }}
              className="btn-ghost flex items-center gap-2"
            >
              <RefreshCw size={16} /> Optimize Again
            </motion.button>
          </div>

          <div className="mx-auto max-w-xl rounded-2xl border border-white/10 bg-white/[0.03] p-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <label className="flex items-center gap-3 text-sm font-semibold text-[#e7e5e4]">
                <input
                  type="checkbox"
                  checked={includeGitHubProjects}
                  onChange={(event) => handleGitHubProjectsToggle(event.target.checked)}
                  className="h-4 w-4 accent-[#4a90d9]"
                />
                Include GitHub Projects
              </label>
              <motion.button
                {...buttonMotion}
                type="button"
                onClick={handleRefreshGitHubProjects}
                disabled={!includeGitHubProjects || githubProjectsLoading}
                className="inline-flex items-center justify-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-xs font-semibold text-[#d6d3d1] transition hover:border-[#4a90d9]/50 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
              >
                {githubProjectsLoading ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
                Refresh
              </motion.button>
            </div>
            {githubProjectsLoading && (
              <p className="mt-3 flex items-center gap-2 text-xs text-[#8A8FA8]">
                <Loader2 size={13} className="animate-spin" /> Fetching and matching your repos...
              </p>
            )}
            {githubProjectsError && !githubProjectsLoading && (
              <p className="mt-3 text-xs text-red-300">{githubProjectsError}</p>
            )}
            {includeGitHubProjects && githubProjects.length > 0 && !githubProjectsLoading && (
              <p className="mt-3 text-xs text-[#8A8FA8]">{githubProjects.length} GitHub project{githubProjects.length === 1 ? '' : 's'} will be included in the exported resume.</p>
            )}
          </div>
        </motion.div>

        {/* ── Stat pills ───────────────────────────────────── */}
        <div className="grid gap-4 lg:grid-cols-2">
          <WhyThisIsBetterPanel items={improvedBullets} />
          <ATSMatchBreakdownPanel data={result} />
        </div>

        <div className="grid md:grid-cols-3 gap-3">
          <div className="rounded-full px-4 py-3 text-center text-sm font-semibold bg-green-500/10 border border-green-500/30 text-green-300">
            Keywords Injected: {addedKeywords.length}
          </div>
          <div className="rounded-full px-4 py-3 text-center text-sm font-semibold bg-red-500/10 border border-red-500/25 text-[#FF7070]">
            Bullets Rewritten: {improvedBullets.length}
          </div>
          <div className="rounded-full px-4 py-3 text-center text-sm font-semibold bg-[rgba(255,140,66,0.12)] border border-[rgba(255,140,66,0.25)] text-[#FF8C42]">
            New Bullets Added: {newBullets.length}
          </div>
        </div>

        {/* ── Keywords injected ────────────────────────────── */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-[#FF7070]">
            <Tag size={16} className="text-[#FF3B3B]" />
            <h3 className="text-sm font-semibold uppercase tracking-wide">Keywords Injected From Job Description</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {addedKeywords.length > 0 ? (
              addedKeywords.map((keyword, idx) => (
                <motion.span key={`${keyword}-${idx}`}
                  initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.04 }}
                  className="px-3 py-1 rounded-full text-xs bg-red-500/10 border border-red-500/20 text-[#FF7070]">
                  {keyword}
                </motion.span>
              ))
            ) : (
              <p className="text-[#78716c] text-sm">No keywords were injected.</p>
            )}
          </div>
        </div>

        {/* ── New bullets ──────────────────────────────────── */}
        {newBullets.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-[#FF7070]">
              <Plus size={16} className="text-[#FF3B3B]" />
              <h3 className="text-sm font-semibold uppercase tracking-wide">New Bullets Added to Fill JD Gaps</h3>
            </div>
            <div className="space-y-3">
              {newBullets.map((bullet, idx) => (
                <div key={idx} className="relative rounded-xl border border-red-500/20 border-l-4 border-l-[#FF3B3B] bg-red-500/5 p-4 pl-5">
                  <div className="absolute top-3 right-3 flex items-center gap-2">
                    <span className="rounded-full border border-red-500/25 bg-red-500/12 px-2 py-0.5 text-[10px] font-bold text-[#FF7070]">NEW</span>
                    <CopyBtn text={bullet.text || ''} />
                  </div>
                  <p className="text-[#fafaf9] text-sm leading-relaxed">{bullet.text}</p>
                  {bullet.reason && <p className="text-xs text-[#78716c] mt-2">{bullet.reason}</p>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Bullet rewrites ──────────────────────────────── */}
        {includeGitHubProjects && githubProjects.length > 0 && (
          <GitHubProjectsSection projects={githubProjects} />
        )}

        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 className="text-sm font-semibold text-[#e7e5e4] uppercase tracking-wide">
              Bullet Point Rewrites ({improvedBullets.length})
            </h3>
            <div className="flex items-center gap-1 rounded-xl bg-white/5 border border-white/10 p-1">
              <motion.button {...buttonMotion} onClick={() => setComparisonView('split')}
                className={`px-3 py-1.5 text-xs rounded-lg transition ${comparisonView === 'split' ? 'bg-red-500/20 text-[#FF7070]' : 'text-[#78716c] hover:text-[#e7e5e4]'}`}>
                Side by Side
              </motion.button>
              <motion.button {...buttonMotion} onClick={() => setComparisonView('single')}
                className={`px-3 py-1.5 text-xs rounded-lg transition ${comparisonView === 'single' ? 'bg-red-500/20 text-[#FF7070]' : 'text-[#78716c] hover:text-[#e7e5e4]'}`}>
                Single Column
              </motion.button>
            </div>
          </div>

          {improvedBullets.length > 0 ? (
            <div className="space-y-4">
              {improvedBullets.map((item, idx) => {
                const keywords = Array.isArray(item?.keywords_added) ? item.keywords_added : []
                return (
                  <motion.div key={idx} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.04 }}
                    className="rounded-xl overflow-hidden border border-white/10">
                    {comparisonView === 'single' ? (
                      <>
                        <div className="p-4 bg-red-500/5 border-b border-white/10">
                          <p className="text-xs font-semibold text-red-400 mb-2 uppercase tracking-wide">Original</p>
                          <p className="text-sm text-[#78716c] leading-relaxed">{item.original}</p>
                        </div>
                        <div className="p-4 bg-green-500/5 relative">
                          <p className="text-xs font-semibold text-green-400 mb-2 uppercase tracking-wide">Improved</p>
                          <p className="text-sm text-[#fafaf9] leading-relaxed">{item.improved}</p>
                          {keywords.length > 0 && (
                            <div className="flex flex-wrap gap-1.5 mt-3">
                              {keywords.map((kw, kidx) => (
                                <span key={kidx} className="px-2 py-0.5 rounded-full text-[10px] bg-red-500/10 border border-red-500/20 text-[#FF7070]">{kw}</span>
                              ))}
                            </div>
                          )}
                          <div className="absolute top-3 right-3"><CopyBtn text={item.improved || ''} /></div>
                        </div>
                      </>
                    ) : (
                      <div className="grid md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-white/10">
                        <div className="p-4 bg-red-500/5">
                          <p className="text-xs font-semibold text-red-400 mb-2 uppercase tracking-wide">Original</p>
                          <p className="text-sm text-[#78716c] leading-relaxed">{item.original}</p>
                        </div>
                        <div className="p-4 bg-green-500/5 relative">
                          <p className="text-xs font-semibold text-green-400 mb-2 uppercase tracking-wide">Improved</p>
                          <p className="text-sm text-[#fafaf9] leading-relaxed">{item.improved}</p>
                          {keywords.length > 0 && (
                            <div className="flex flex-wrap gap-1.5 mt-3">
                              {keywords.map((kw, kidx) => (
                                <span key={kidx} className="px-2 py-0.5 rounded-full text-[10px] bg-red-500/10 border border-red-500/20 text-[#FF7070]">{kw}</span>
                              ))}
                            </div>
                          )}
                          <div className="absolute top-3 right-3"><CopyBtn text={item.improved || ''} /></div>
                        </div>
                      </div>
                    )}
                  </motion.div>
                )
              })}
            </div>
          ) : (
            <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-[#78716c]">
              No bullet rewrites were returned.
            </div>
          )}
        </div>

        {/* ── Editable summary ─────────────────────────────── */}
        <div className="relative rounded-2xl border border-white/10 border-l-4 border-[#FF3B3B] bg-red-500/5 p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-[#FF7070] uppercase tracking-wide">Rewritten Professional Summary</h3>
            <CopyBtn text={displaySummary} />
          </div>
          <textarea value={displaySummary} onChange={(e) => setEditedSummary(sanitizeProfessionalSummary(e.target.value))} rows={4}
            className="input-field resize-none" />
        </div>

        {/* ── Updated skills ───────────────────────────────── */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-[#FF7070]">
            <Badge size={16} className="text-[#FF3B3B]" />
            <h3 className="text-sm font-semibold uppercase tracking-wide">Updated Skills Section</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {optimizedSkills.length > 0 ? (
              optimizedSkills.map((skill, idx) => (
                <motion.span key={`${skill}-${idx}`}
                  initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.04 }}
                  className="px-3 py-1 rounded-full text-xs bg-red-500/10 border border-red-500/20 text-[#FF7070]">
                  {skill}
                </motion.span>
              ))
            ) : <p className="text-[#78716c] text-sm">No skills returned.</p>}
          </div>
        </div>

        {/* ── ATS checklist ────────────────────────────────── */}
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-[#e7e5e4] uppercase tracking-wide">ATS Formatting Checklist</h3>
          <div className="space-y-2">
            {atsTips.length > 0 ? (
              atsTips.map((tip, idx) => {
                const checked = Boolean(checkedTips[idx])
                return (
                  <motion.button {...buttonMotion} key={idx} type="button" onClick={() => toggleTip(idx)}
                    className="w-full flex items-start gap-3 rounded-xl border border-white/5 bg-white/5 px-4 py-3 text-left">
                    <span className="mt-0.5">
                      {checked
                        ? <CheckCircle2 size={16} className="text-green-400" />
                        : <span className="block w-4 h-4 rounded border border-[#78716c]" />}
                    </span>
                    <span className={`text-sm ${checked ? 'text-[#78716c] line-through' : 'text-[#e7e5e4]'}`}>{tip}</span>
                  </motion.button>
                )
              })
            ) : <p className="text-[#78716c] text-sm">No ATS tips were returned.</p>}
          </div>
        </div>

        {/* ── Bottom download button ───────────────────────── */}
        <motion.button {...buttonMotion} onClick={handleStyledDownload}
          className="w-full flex items-center justify-center gap-2 rounded-2xl py-4 font-bold text-white bg-gradient-to-r from-[#FF3B3B] to-[#CC1A1A] shadow-[0_4px_20px_rgba(255,59,59,0.4)] transition">
          <Download size={16} /> Download Professional Resume PDF
        </motion.button>
      </div>
      </motion.div>
    )
  }

  // ── INPUT SCREEN ─────────────────────────────────────────
  return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
    <div className="max-w-4xl w-full mx-auto space-y-6">
      <div className="max-w-2xl mx-auto text-center">
        <h1 className="gradient-text text-3xl font-bold flex items-center justify-center gap-3">
          <Sparkles size={26} className="text-[#FF3B3B]" /> Resume Optimizer
        </h1>
        <p className="text-[#78716c] mt-2">Rewrite your resume bullets to match the exact job and export the optimized version as a PDF</p>
      </div>

      {error && <div className="max-w-3xl mx-auto p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">{error}</div>}

      <div className="glass-glow p-6 rounded-3xl space-y-5 max-w-3xl w-full mx-auto">
        <div>
          <label className="text-xs font-semibold text-[#78716c] uppercase tracking-wide mb-2 block">Resume *</label>
          {!resumeFile ? (
            <div
              onDrop={(e) => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0]) }}
              onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              onClick={() => fileRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all mb-2
                ${dragging ? 'border-[#FF3B3B] bg-red-500/10 shadow-[0_0_30px_rgba(255,59,59,0.1)]' : 'border-white/10 bg-white/[0.02] hover:border-[rgba(255,59,59,0.28)] hover:bg-red-500/5'}`}>
              <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={(e) => handleFile(e.target.files[0])} />
              <Upload size={24} className="float text-[#FF7070] mx-auto mb-2" />
              <p className="text-[#d6d3d1] text-sm">Drop PDF or click to upload</p>
            </div>
          ) : (
            <div className="flex items-center gap-3 p-3 rounded-xl bg-green-500/10 border border-green-500/20 mb-2">
              <CheckCircle size={16} className="text-green-400" />
              <span className="text-sm text-white flex-1">{resumeFile.name}</span>
              <motion.button {...buttonMotion} onClick={() => { setResumeFile(null); setResumeText(''); setError('') }}
                className="text-[#78716c] hover:text-white text-xs">Remove</motion.button>
            </div>
          )}
          <textarea value={resumeText} onChange={(e) => setResumeText(e.target.value)}
            placeholder="Or paste your resume text here..." rows={4}
            className="input-field resize-none w-full text-sm" />
        </div>

        <div>
          <label className="text-xs font-semibold text-[#78716c] uppercase tracking-wide mb-2 block">Job Title</label>
          <input value={jobTitle} onChange={(e) => setJobTitle(e.target.value)}
            placeholder="e.g. ML Engineer, Frontend Developer" className="input-field w-full" />
        </div>

        <div>
          <label className="text-xs font-semibold text-[#78716c] uppercase tracking-wide mb-2 block">Paste Job Description</label>
          <textarea value={jobDesc} onChange={(e) => setJobDesc(e.target.value)}
            placeholder="Paste the job description you are applying for..." rows={7}
            className="input-field resize-none w-full" />
        </div>

        <motion.button {...buttonMotion} onClick={handleOptimize} disabled={loading || !jobDesc.trim()}
          className="btn-primary w-full flex items-center justify-center gap-3 py-4 font-bold disabled:opacity-50">
          {loading
            ? <><Loader2 size={17} className="animate-spin" /> Optimizing...</>
            : <><Zap size={17} /> Optimize My Resume</>}
        </motion.button>
      </div>
    </div>
    </motion.div>
  )
}






