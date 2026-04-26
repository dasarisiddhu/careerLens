// frontend/src/pages/dashboard/Chatbot.jsx
import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { pageTransition } from '../../utils/animations'
import { api } from '../../services/api'
import toast from 'react-hot-toast'
import { Send, Bot, User, Loader2, Sparkles } from 'lucide-react'

const QUICK_PROMPTS = [
  'How do I improve my resume ATS score?',
  'What skills should I learn for backend development?',
  'How to negotiate salary as a junior developer?',
  'Best way to prepare for technical interviews?',
  'How to build a strong GitHub profile?',
]

function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${isUser ? 'bg-red-600' : 'bg-red-500/10 border border-red-500/20'}`}>
        {isUser ? <User size={14} /> : <Bot size={14} className="text-[#FF7070]" />}
      </div>
      <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed
        ${isUser ? 'bg-red-600 text-white rounded-tr-sm' : 'glass text-[#e7e5e4] rounded-tl-sm'}`}>
        {msg.content}
      </div>
    </motion.div>
  )
}

export default function Chatbot() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "I'm your Honest Career Coach. Ask me to evaluate your skills, roast your resume, or map out what you actually need to fix.",
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const bottomRef = useRef(null)
  const buttonMotion = {
    whileHover: { scale: 1.03, y: -1 },
    whileTap: { scale: 0.97 },
    transition: { duration: 0.15, ease: 'easeOut' },
  }

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const send = async (text) => {
    const content = text || input.trim()
    if (!content || loading) return
    setInput('')
    setMessages(m => [...m, { role: 'user', content }])
    setLoading(true)
    try {
      const res = await api.sendMessage({ content, session_id: sessionId })
      setSessionId(res.session_id)
      setMessages(m => [...m, { role: 'assistant', content: res.reply }])
    } catch (err) {
      setMessages(m => [...m, { role: 'assistant', content: `Sorry, I encountered an error: ${err.message}` }])
      toast.error(err.message || 'Failed to send message.')
    }
    setLoading(false)
  }

  return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
    <div className="flex flex-col h-[calc(100vh-120px)] max-w-3xl mx-auto w-full">
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2"><Bot size={22} className="text-[#FF7070]" /> Honest Career Coach</h1>
        <p className="text-[#78716c] text-sm">Powered by Google Gemini</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto glass rounded-2xl p-4 space-y-4 mb-4">
        {messages.length === 0 ? (
          <div style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '48px 24px',
            gap: '16px',
          }}>
            <div style={{
              width: '72px',
              height: '72px',
              borderRadius: '20px',
              background: 'rgba(239,68,68,0.1)',
              border: '1px solid rgba(239,68,68,0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '8px',
              boxShadow: '0 0 40px rgba(239,68,68,0.08)',
            }}>
              <Bot size={32} className="text-[#FF7070]" />
            </div>
            <h3 style={{ fontSize: '20px', fontWeight: 700, color: '#fafaf9', margin: 0, textAlign: 'center' }}>
              Honest Career Coach
            </h3>
            <p style={{
              fontSize: '14px',
              color: 'rgba(120,113,108,0.9)',
              textAlign: 'center',
              maxWidth: '360px',
              lineHeight: 1.6,
              margin: 0,
            }}>
              Ask anything about resumes, interviews, salary negotiation, or career transitions. I'm here 24/7.
            </p>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3,1fr)',
              gap: '10px',
              width: '100%',
              maxWidth: '640px',
              marginTop: '16px',
            }}>
              {[
                'How do I improve my ATS score?',
                'What skills are in demand for 2025?',
                'Help me prepare for interviews',
              ].map((prompt) => (
                <motion.button
                  {...buttonMotion}
                  key={prompt}
                  onClick={() => setInput(prompt)}
                  style={{
                    padding: '12px 14px',
                    borderRadius: '12px',
                    textAlign: 'left',
                    background: 'rgba(17,16,14,0.8)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    color: 'rgba(214,211,209,0.85)',
                    fontSize: '12.5px',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    lineHeight: 1.4,
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = 'rgba(239,68,68,0.35)'
                    e.currentTarget.style.background = 'rgba(239,68,68,0.06)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'
                    e.currentTarget.style.background = 'rgba(17,16,14,0.8)'
                  }}
                >
                  {prompt}
                </motion.button>
              ))}
            </div>
          </div>
        ) : (
          <>
            <AnimatePresence>
              {messages.map((msg, i) => <Message key={i} msg={msg} />)}
            </AnimatePresence>
            {loading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
                  <Bot size={14} className="text-[#FF7070]" />
                </div>
                <div className="glass px-4 py-3 rounded-2xl rounded-tl-sm">
                  <Loader2 size={16} className="animate-spin text-[#FF7070]" />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </>
        )}
      </div>

      {/* Quick prompts */}
      <div className="flex gap-2 mb-3 overflow-x-auto pb-1">
        {QUICK_PROMPTS.map((p, i) => (
          <motion.button {...buttonMotion} key={i} onClick={() => send(p)}
            className="shrink-0 text-xs px-3 py-1.5 rounded-full bg-white/5 border border-white/10 hover:border-red-500/40 hover:text-[#FF7070] text-[#78716c] transition-all">
            <Sparkles size={10} className="inline mr-1" />{p}
          </motion.button>
        ))}
      </div>

      {/* Input */}
      <div className="flex gap-3">
        <input value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
          placeholder="Ask me to evaluate your skills, roast your resume, or give you a real roadmap."
          className="input-field flex-1" />
        <motion.button {...buttonMotion} onClick={() => send()} disabled={!input.trim() || loading}
          className="btn-primary px-4 py-3 disabled:opacity-50 disabled:cursor-not-allowed">
          <Send size={16} />
        </motion.button>
      </div>
    </div>
    </motion.div>
  )
}









