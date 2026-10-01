import { z } from 'zod'

export const TechNewsSchema = z.object({
  articles: z.any().transform((val) => {
    if (!Array.isArray(val)) return []
    return val.map((a, idx) => ({
      id: a.id || `news-${idx}`,
      title: a.title || 'Tech Update',
      url: a.url || a.link || '#',
      source: a.source || 'Industry News',
      published_at: a.published_at || a.date || '',
      summary: a.summary || a.description || '',
      image_url: a.image_url || a.image || null,
    }))
  }),
})

export const HiringNewsSchema = z.object({
  trends: z.any().transform((val) => {
    const list = Array.isArray(val) ? val : Array.isArray(val?.trends) ? val.trends : []
    return list.map((t, idx) => ({
      id: t.id || `trend-${idx}`,
      company: t.company || 'Tech Company',
      role: t.role || 'Software Engineer',
      location: t.location || 'Remote',
      hiring_status: t.hiring_status || 'Actively Hiring',
      link: t.link || t.url || '#',
    }))
  }),
})

export function normalizeTechNews(raw) {
  if (!raw) return { articles: [] }
  const data = Array.isArray(raw) ? { articles: raw } : raw
  const parsed = TechNewsSchema.safeParse(data)
  return parsed.success ? parsed.data : { articles: [] }
}

export function normalizeHiringNews(raw) {
  if (!raw) return { trends: [] }
  const data = Array.isArray(raw) ? { trends: raw } : raw
  const parsed = HiringNewsSchema.safeParse(data)
  return parsed.success ? parsed.data : { trends: [] }
}
