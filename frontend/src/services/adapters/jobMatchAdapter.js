import { z } from 'zod'

function clampPercent(v) {
  const num = Number(v)
  if (isNaN(num)) return 75
  return Math.min(Math.max(Math.round(num), 0), 100)
}

export const JobMatchSchema = z.object({
  matches: z.any().transform((val) => {
    if (!Array.isArray(val)) return []
    return val.map((job, idx) => ({
      id: job.id || `job-${idx}`,
      title: job.title || 'Role Title',
      company: job.company || 'Company',
      match_percentage: clampPercent(job.match_percentage || job.match_score),
      matching_skills: Array.isArray(job.matching_skills) ? job.matching_skills : [],
      missing_skills: Array.isArray(job.missing_skills) ? job.missing_skills : [],
      location: job.location || 'Remote',
      apply_url: job.apply_url || job.url || '#',
    }))
  }),
})

export function normalizeJobMatch(raw) {
  if (!raw) return { matches: [] }
  const data = Array.isArray(raw) ? { matches: raw } : raw
  const parsed = JobMatchSchema.safeParse(data)
  if (!parsed.success) {
    console.warn('[jobMatchAdapter] validation fallback:', parsed.error)
    return { matches: [] }
  }
  return parsed.data
}
