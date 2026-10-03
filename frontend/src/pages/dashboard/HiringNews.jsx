import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { api } from '../../services/api'
import toast from 'react-hot-toast'
import { Briefcase, ExternalLink, Loader2 } from 'lucide-react'
import { GlassCard, Badge } from '../../components/ui'
import { CardsGridSkeleton } from '../../components/skeletons'

const cleanSnippet = (rawHtml) => {
  if (!rawHtml) return ''
  try {
    const doc = new DOMParser().parseFromString(rawHtml, 'text/html')
    doc.querySelectorAll('script, style').forEach((el) => el.remove())
    let text = doc.body.textContent || ''
    text = text.replace(/https?:\/\/[^\s)]+/g, '').replace(/[<>[\]]/g, '').trim()
    return text.replace(/\s+/g, ' ')
  } catch {
    return String(rawHtml).replace(/<[^>]*>/g, '').replace(/https?:\/\/[^\s)]+/g, '').trim()
  }
}

export default function HiringNews() {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getHiringNews()
      .then((r) => {
        setArticles(Array.isArray(r?.articles) ? r.articles : [])
        setLoading(false)
      })
      .catch((err) => {
        setLoading(false)
        toast.error(err?.message || 'Failed to load hiring news.')
      })
  }, [])

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6 pb-16">
      {/* Header */}
      <div>
        <Badge sparkle size="sm" className="mb-2">
          Market Movements
        </Badge>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0B0F19] tracking-tight flex items-center gap-2.5">
          <Briefcase size={24} className="text-[#2563EB]" />
          <span>Hiring News</span>
        </h1>
        <p className="text-xs sm:text-sm text-[#64748B] mt-1">
          Hiring rounds, startup funding, expansion signals, and talent shifts.
        </p>
      </div>

      {loading ? (
        <CardsGridSkeleton count={6} />
      ) : articles.length === 0 ? (
        <GlassCard className="p-12 text-center text-xs text-[#64748B]">
          No hiring news available at the moment. Check back soon.
        </GlassCard>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {articles.map((a, i) => {
            const snippet = cleanSnippet(a.description || a.summary)
            return (
              <motion.a
                key={i}
                href={a.link}
                target="_blank"
                rel="noopener noreferrer"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25, delay: i * 0.02 }}
                className="group block h-full"
              >
                <GlassCard hoverable className="p-5 h-full flex flex-col justify-between border-white/90 shadow-glass">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[11px] font-semibold text-[#2563EB] bg-blue-50 px-2.5 py-0.5 rounded-full border border-blue-100">
                        {a.source || 'Hiring'}
                      </span>
                      <ExternalLink size={13} className="text-[#94A3B8] group-hover:text-[#2563EB] transition-colors" />
                    </div>

                    <h2 className="text-sm font-bold text-[#0B0F19] group-hover:text-[#2563EB] transition-colors leading-snug">
                      {a.title}
                    </h2>

                    {snippet && (
                      <p className="text-xs text-[#64748B] leading-relaxed line-clamp-3">
                        {snippet}
                      </p>
                    )}
                  </div>

                  <div className="pt-3 mt-4 border-t border-slate-100 flex items-center text-[11px] font-bold text-[#2563EB]">
                    <span>Read Article</span>
                    <span className="ml-1 transition-transform group-hover:translate-x-1">→</span>
                  </div>
                </GlassCard>
              </motion.a>
            )
          })}
        </div>
      )}
    </div>
  )
}
