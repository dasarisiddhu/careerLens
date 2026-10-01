import { z } from 'zod'

function clampScore(val, fallback = 70) {
  const num = Number(val)
  if (isNaN(num)) return fallback
  return Math.min(Math.max(Math.round(num), 0), 100)
}

function normalizeStringList(val) {
  if (Array.isArray(val)) {
    return val.map((item) =>
      typeof item === 'string'
        ? item
        : item.title || item.text || item.description || JSON.stringify(item)
    )
  }
  if (val && typeof val === 'object') {
    return Object.values(val).map(String)
  }
  if (typeof val === 'string' && val.trim()) return [val.trim()]
  return []
}

export const ResumeAnalysisSchema = z.object({
  id: z.any().optional().transform((v) => (v != null ? String(v) : `analysis-${Date.now()}`)),
  overall_score: z.any().optional().transform((v) => clampScore(v, 70)),
  ats_score: z.any().optional().transform((v) => clampScore(v, 70)),
  formatting_score: z.any().optional().transform((v) => clampScore(v, 75)),
  experience_score: z.any().optional().transform((v) => clampScore(v, 70)),
  skills_score: z.any().optional().transform((v) => clampScore(v, 70)),
  summary: z.string().optional().default('Analysis complete.'),
  strengths: z.any().optional().transform(normalizeStringList),
  weaknesses: z.any().optional().transform(normalizeStringList),
  suggestions: z.any().optional().transform(normalizeStringList),
  skill_gaps: z.any().optional().transform(normalizeStringList),
  github_analysis: z.any().optional().default(null),
})

export const ATSCheckSchema = z.object({
  ats_score: z.any().optional().transform((v) => clampScore(v, 70)),
  match_score: z.any().optional().transform((v) => clampScore(v, 70)),
  matching_keywords: z.any().optional().transform(normalizeStringList),
  missing_keywords: z.any().optional().transform(normalizeStringList),
  recommendations: z.any().optional().transform(normalizeStringList),
})

export function normalizeResumeAnalysis(raw) {
  if (!raw) return ResumeAnalysisSchema.parse({})
  const parsed = ResumeAnalysisSchema.safeParse(raw)
  if (!parsed.success) {
    console.warn('[resumeAdapter] analysis validation fallback:', parsed.error)
    return ResumeAnalysisSchema.parse({})
  }
  return parsed.data
}

export function normalizeATSCheck(raw) {
  if (!raw) return ATSCheckSchema.parse({})
  const parsed = ATSCheckSchema.safeParse(raw)
  if (!parsed.success) {
    console.warn('[resumeAdapter] ats check validation fallback:', parsed.error)
    return ATSCheckSchema.parse({})
  }
  return parsed.data
}
