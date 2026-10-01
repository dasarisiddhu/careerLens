import { z } from 'zod'

function clampScore(val, fallback = 70) {
  const num = Number(val)
  if (isNaN(num)) return fallback
  return Math.min(Math.max(Math.round(num), 0), 100)
}

export const InterviewStartSchema = z.object({
  session_id: z.string().optional().default(() => `session-${Date.now()}`),
  questions: z.any().optional().transform((val) => {
    if (!Array.isArray(val)) return []
    return val.map((q, idx) => ({
      id: typeof q === 'object' && q?.id ? q.id : `q-${idx}`,
      text: typeof q === 'string' ? q : q?.text || q?.question || 'Tell me about yourself.',
      category: typeof q === 'object' && q?.category ? q.category : 'General',
    }))
  }),
})

export const InterviewEvaluationSchema = z.object({
  overall_score: z.any().optional().transform((v) => clampScore(v, 70)),
  communication_score: z.any().optional().transform((v) => clampScore(v, 75)),
  technical_score: z.any().optional().transform((v) => clampScore(v, 70)),
  feedback: z.string().optional().default('Interview evaluation completed.'),
  question_reviews: z.any().optional().transform((val) => (Array.isArray(val) ? val : [])),
})

export function normalizeInterviewStart(raw) {
  if (!raw) return InterviewStartSchema.parse({})
  const parsed = InterviewStartSchema.safeParse(raw)
  return parsed.success ? parsed.data : InterviewStartSchema.parse({})
}

export function normalizeInterviewEvaluation(raw) {
  if (!raw) return InterviewEvaluationSchema.parse({})
  const parsed = InterviewEvaluationSchema.safeParse(raw)
  return parsed.success ? parsed.data : InterviewEvaluationSchema.parse({})
}
