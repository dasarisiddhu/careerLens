// frontend/src/pages/dashboard/Chatbot.jsx
import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { pageTransition } from '../../utils/animations'
import { api } from '../../services/api'
import toast from 'react-hot-toast'
import { Send, Bot, User, Loader2, Sparkles } from 'lucide-react'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'

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
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      <div
        className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
          isUser
            ? 'bg-gradient-to-tr from-primary to-accent text-white shadow-[0_0_12px_rgba(255,107,0,0.4)]'
            : 'bg-primary/10 border border-primary/25'
        }`}
      >
        {isUser ? <User size={14} /> : <Bot size={14} className="text-primary-light" />}
      </div>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? 'bg-gradient-to-r from-primary to-primary-dark text-white rounded-tr-sm shadow-[0_4px_16px_rgba(255,107,0,0.25)]'
            : 'glass text-[#F5F5F7] rounded-tl-sm border-white/[0.08]'
        }`}
      >
        {msg.content}
      </div>
    </motion.div>
  )
}

export default function Chatbot() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        "I'm your Honest Career Coach. Ask me to evaluate your skills, roast your resume, or map out what you actually need to fix.",
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

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (text) => {
    const content = text || input.trim()
    if (!content || loading) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', content }])
    setLoading(true)
    try {
      const res = await api.sendMessage({ content, session_id: sessionId })
      setSessionId(res.session_id)
      setMessages((m) => [...m, { role: 'assistant', content: res.reply }])
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: `Sorry, I encountered an error: ${err.message}` },
      ])
      toast.error(err.message || 'Failed to send message.')
    }
    setLoading(false)
  }

  return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
      <div className="flex flex-col h-[calc(100vh-140px)] max-w-3xl mx-auto w-full">
        <div className="mb-4">
          <h1 className="text-2xl font-bold text-white flex items-center gap-2 font-display">
            <Bot size={22} className="text-primary" /> Honest Career Coach
          </h1>
          <p className="text-[#9499B3] text-sm">Powered by Google Gemini &amp; CareerLens AI</p>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto glass rounded-2xl p-4 space-y-4 mb-4 border border-white/[0.08]">
          {messages.length === 0 ? (
            <div
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '48px 24px',
                gap: '16px',
              }}
            >
              <div
                style={{
                  width: '72px',
                  height: '72px',
                  borderRadius: '20px',
                  background: 'rgba(255,107,0,0.12)',
                  border: '1px solid rgba(255,107,0,0.25)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '8px',
                  boxShadow: '0 0 40px rgba(255,107,0,0.15)',
                }}
              >
                <Bot size={32} className="text-primary-light" />
              </div>
              <h3 className="font-display" style={{ fontSize: '20px', fontWeight: 700, color: '#fafaf9', margin: 0, textAlign: 'center' }}>
                Honest Career Coach
              </h3>
              <p
                style={{
                  fontSize: '14px',
                  color: 'rgba(148,153,179,0.9)',
                  textAlign: 'center',
                  maxWidth: '360px',
                  lineHeight: 1.6,
                  margin: 0,
                }}
              >
                Ask anything about resumes, interviews, salary negotiation, or career transitions.
              </p>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3,1fr)',
                  gap: '10px',
                  width: '100%',
                  maxWidth: '640px',
                  marginTop: '16px',
                }}
              >
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
                      background: 'rgba(19,18,28,0.85)',
                      border: '1px solid rgba(255,255,255,0.08)',
                      color: 'rgba(245,245,247,0.85)',
                      fontSize: '12.5px',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      lineHeight: 1.4,
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = 'rgba(255,107,0,0.4)'
                      e.currentTarget.style.background = 'rgba(255,107,0,0.08)'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'
                      e.currentTarget.style.background = 'rgba(19,18,28,0.85)'
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
                {messages.map((msg, i) => (
                  <Message key={i} msg={msg} />
                ))}
              </AnimatePresence>
              {loading && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-xl bg-primary/10 border border-primary/25 flex items-center justify-center">
                    <Bot size={14} className="text-primary-light" />
                  </div>
                  <div className="glass px-4 py-3 rounded-2xl rounded-tl-sm border-white/[0.08]">
                    <Loader2 size={16} className="animate-spin text-primary" />
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
            <motion.button
              {...buttonMotion}
              key={i}
              onClick={() => send(p)}
              className="shrink-0 text-xs px-3 py-1.5 rounded-full bg-white/[0.04] border border-white/10 hover:border-primary/40 hover:text-primary-light hover:bg-primary/10 text-slate-300 transition-all"
            >
              <Sparkles size={10} className="inline mr-1 text-primary" />
              {p}
            </motion.button>
          ))}
        </div>

        {/* Input */}
        <div className="flex gap-3">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && send()}
            placeholder="Ask me to evaluate your skills, roast your resume, or give you a real roadmap."
            className="flex-1"
          />
          <Button
            variant="primary"
            onClick={() => send()}
            disabled={!input.trim() || loading}
            className="px-5 h-11 shrink-0"
          >
            <Send size={16} />
          </Button>
        </div>
      </div>
    </motion.div>
  )
}
