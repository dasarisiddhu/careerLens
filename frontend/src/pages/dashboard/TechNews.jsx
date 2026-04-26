// frontend/src/pages/dashboard/TechNews.jsx
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { pageTransition, staggerContainer, staggerItem } from '../../utils/animations'
import { api } from '../../services/api'
import toast from 'react-hot-toast'
import { Newspaper, ExternalLink, Loader2 } from 'lucide-react'

const stripHtml = (html) => {
  if (!html) return ''
  return html
    .replace(/<[^>]*>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .trim()
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
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
      <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white flex items-center gap-3"><Newspaper size={28} className="text-amber-400" /> Tech News</h1>
        <p className="text-[#78716c]">Latest in AI, programming, and startups</p>
      </div>
      {loading
        ? <div className="flex justify-center py-16"><Loader2 size={32} className="animate-spin text-amber-400" /></div>
        : <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}
          >
          {articles.map((a, i) => (
            <motion.a key={i} href={a.link} target="_blank" rel="noopener noreferrer"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              variants={staggerItem}
              whileHover={{
                y: -2,
                borderColor: 'rgba(245,158,11,0.32)',
                background: 'rgba(217,119,6,0.04)',
                boxShadow: '0 8px 32px rgba(0,0,0,0.4), 0 0 20px rgba(239,68,68,0.06)',
              }}
              style={{
                background: 'rgba(17,16,14,0.85)',
                border: '1px solid rgba(239,68,68,0.12)',
                borderRadius: '14px',
                padding: '20px 22px',
                cursor: 'pointer',
                transition: 'all 0.22s',
                position: 'relative',
                overflow: 'hidden',
              }}
              className="group block"
            >
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '3px',
                height: '100%',
                background: 'linear-gradient(180deg, rgba(239,68,68,0.6), transparent)',
                borderRadius: '14px 0 0 14px',
              }} />
              {a.image && (
                <img
                  src={a.image}
                  alt=""
                  className="w-full h-40 object-cover rounded-xl mb-4 opacity-80 group-hover:opacity-100 transition-opacity"
                  onError={e => e.target.style.display='none'}
                />
              )}
              <div className="flex items-center justify-between text-xs text-[#44403c]">
                <span style={{
                  fontSize: '11px',
                  color: 'rgba(120,113,108,0.8)',
                  background: 'rgba(255,255,255,0.04)',
                  padding: '2px 8px',
                  borderRadius: '6px',
                  border: '1px solid rgba(255,255,255,0.06)',
                }}>{a.source}</span>
                <ExternalLink size={12} />
              </div>
              <p style={{ fontSize: '15px', fontWeight: 600, color: '#fafaf9', lineHeight: 1.4, margin: '8px 0 6px' }}>
                {a.title}
              </p>
              <p style={{ fontSize: '13px', color: 'rgba(120,113,108,0.85)', lineHeight: 1.5 }}>
                {stripHtml(a.description || a.summary).slice(0, 120)}...
              </p>
            </motion.a>
          ))}
        </motion.div>
      }
      </div>
    </motion.div>
  )
}







