import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { api } from '../../services/api'
import toast from 'react-hot-toast'
import { Newspaper, ExternalLink, Loader2 } from 'lucide-react'
import { GlassCard, Badge } from '../../components/ui'
import { CardsGridSkeleton } from '../../components/skeletons'

const cleanSnippet = (rawHtml) => {
  if (!rawHtml) return ''
  try {
    const doc = new DOMParser().parseFromString(rawHtml, 'text/html')
    // Remove scripts and styles
    doc.querySelectorAll('script, style').forEach((el) => el.remove())
    let text = doc.body.textContent || ''
    // Strip dangling image URLs or markdown artifacts
    text = text.replace(/https?:\/\/[^\s)]+/g, '').replace(/[<>[\]]/g, '').trim()
    return text.replace(/\s+/g, ' ')
  } catch {
    return String(rawHtml).replace(/<[^>]*>/g, '').replace(/https?:\/\/[^\s)]+/g, '').trim()
  }
}

export default function TechNews() {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getTechNews()
      .then((r) => {
        setArticles(Array.isArray(r?.articles) ? r.articles : [])
        setLoading(false)
      })
      .catch((err) => {
        setLoading(false)
        toast.error(err?.message || 'Failed to load tech news.')
      })
  }, [])

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6 pb-16">
      {/* Header */}
      <div>
        <Badge sparkle size="sm" className="mb-2">
          Industry Signals
        </Badge>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0B0F19] tracking-tight flex items-center gap-2.5">
          <Newspaper size={24} className="text-[#2563EB]" />
          <span>Tech News</span>
        </h1>
        <p className="text-xs sm:text-sm text-[#64748B] mt-1">
          Curated real-time updates across AI, engineering, and tech ecosystems.
        </p>
      </div>

      {loading ? (
        <CardsGridSkeleton count={6} />
      ) : articles.length === 0 ? (
        <GlassCard className="p-12 text-center text-xs text-[#64748B]">
          No news articles available at the moment. Check back soon.
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
                    {a.image && (
                      <div className="w-full h-36 rounded-xl overflow-hidden bg-slate-100">
                        <img
                          src={a.image}
                          alt=""
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                          onError={(e) => {
                            e.currentTarget.parentElement.style.display = 'none'
                          }}
                        />
                      </div>
                    )}

                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[11px] font-semibold text-[#2563EB] bg-blue-50 px-2.5 py-0.5 rounded-full border border-blue-100">
                        {a.source || 'Tech'}
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
