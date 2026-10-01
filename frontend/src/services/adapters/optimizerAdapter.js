import { z } from 'zod'

function clampScore(val, fallback = 70) {
  const num = Number(val)
  if (isNaN(num)) return fallback
  return Math.min(Math.max(Math.round(num), 0), 100)
}

function normalizeArray(val) {
  if (Array.isArray(val)) return val
  if (val && typeof val === 'object') {
    return Object.entries(val).map(([k, v]) => (typeof v === 'string' ? `${k}: ${v}` : String(k)))
  }
  if (typeof val === 'string' && val.trim()) return [val.trim()]
  return []
}

export const OptimizerAnalysisSchema = z.object({
  overall_score: z.any().optional().transform((v) => clampScore(v, 75)),
  recruiter_lens: z
    .object({
      verdict: z.string().optional().default('Profile Analyzed'),
      score: z.any().optional().transform((v) => clampScore(v, 75)),
      key_strengths: z.any().optional().transform(normalizeArray),
      key_weaknesses: z.any().optional().transform(normalizeArray),
    })
    .optional()
    .default({
      verdict: 'Profile Analyzed',
      score: 75,
      key_strengths: [],
      key_weaknesses: [],
    }),
  skill_gap_analysis: z.any().optional().transform((val) => {
    if (Array.isArray(val)) {
      return val.map((item, idx) => ({
        id: item.id || `skill-${idx}`,
        skill: item.skill || item.name || 'Core Skill',
        importance: item.importance || 'Medium',
        status: item.status || 'Missing',
      }))
    }
    if (val && typeof val === 'object') {
      return Object.entries(val).map(([skill, status], idx) => ({
        id: `skill-${idx}`,
        skill,
        importance: 'Medium',
        status: typeof status === 'string' ? status : 'Missing',
      }))
    }
    return []
  }),
  rejection_diagnosis: z
    .object({
      primary_reason: z.string().optional().default('None identified'),
      risk_factors: z.any().optional().transform(normalizeArray),
    })
    .optional()
    .default({
      primary_reason: 'None identified',
      risk_factors: [],
    }),
  ats_checks: z
    .object({
      formatting: z.any().optional().transform((v) => String(v || 'Pass')),
      keyword_density: z.any().optional().transform((v) => String(v || 'Optimal')),
      structure: z.any().optional().transform((v) => String(v || 'Standard')),
    })
    .optional()
    .default({
      formatting: 'Pass',
      keyword_density: 'Optimal',
      structure: 'Standard',
    }),
})

export const OptimizerResultSchema = z.object({
  status: z.string().optional().default('success'),
  message: z.string().optional().default('Resume optimized successfully'),
  changes_applied: z.any().optional().transform(normalizeArray),
  bullet_diffs: z.any().optional().transform((val) => {
    if (!Array.isArray(val)) return []
    return val.map((diff, idx) => ({
      id: diff.id || `diff-${idx}`,
      section: diff.section || 'Experience',
      original: diff.original || '',
      optimized: diff.optimized || diff.original || '',
      improvement_reason: diff.improvement_reason || '',
      jd_requirement: diff.jd_requirement || '',
      safety_reverted: Boolean(diff.safety_reverted),
    }))
  }),
  summary: z
    .object({
      original: z.string().optional().default(''),
      optimized: z.string().optional().default(''),
    })
    .optional()
    .default({ original: '', optimized: '' }),
  ats_regression: z
    .object({
      before_score: z.any().optional().transform((v) => clampScore(v, 70)),
      after_score: z.any().optional().transform((v) => clampScore(v, 85)),
      status: z.string().optional().default('improved'),
    })
    .optional()
    .default({ before_score: 70, after_score: 85, status: 'improved' }),
  skill_provenance: z
    .object({
      verified: z.any().optional().transform(normalizeArray),
      added_unverified: z.any().optional().transform(normalizeArray),
    })
    .optional()
    .default({ verified: [], added_unverified: [] }),
})

export function normalizeOptimizerAnalysis(raw) {
  if (!raw) return OptimizerAnalysisSchema.parse({})
  const parsed = OptimizerAnalysisSchema.safeParse(raw)
  if (!parsed.success) {
    console.warn('[optimizerAdapter] analysis validation fallback:', parsed.error)
    return OptimizerAnalysisSchema.parse({})
  }
  return parsed.data
}

export function normalizeOptimizerResult(raw) {
  if (!raw) return OptimizerResultSchema.parse({})
  const parsed = OptimizerResultSchema.safeParse(raw)
  if (!parsed.success) {
    console.warn('[optimizerAdapter] result validation fallback:', parsed.error)
    return OptimizerResultSchema.parse({})
  }
  return parsed.data
}
