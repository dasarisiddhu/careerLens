import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '../../services/api'
import toast from 'react-hot-toast'
import { Send, Bot, User, Sparkles, AlertCircle, Loader2 } from 'lucide-react'
import { GlassCard, Button, Badge } from '../../components/ui'

const QUICK_PROMPTS = [
  'How do I improve my resume ATS score?',
  'What skills should I learn for backend development?',
  'How to negotiate salary as a junior developer?',
  'Best way to prepare for technical interviews?',
  'How to build a standout GitHub profile?',
]

function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-3 items-end ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
      role={isUser ? 'none' : 'status'}
      aria-live={isUser ? 'off' : 'polite'}
    >
      {/* Avatar */}
      <div className="shrink-0 mb-1">
        {isUser ? (
          <div className="w-8 h-8 rounded-full bg-[#0B0F19] text-white flex items-center justify-center font-bold text-xs shadow-sm">
            <User size={15} />
          </div>
        ) : (
          <div className="w-8 h-8 rounded-full bg-blue-50 border border-blue-200 flex items-center justify-center text-[#2563EB] shadow-sm">
            <Sparkles size={16} />
          </div>
        )}
      </div>

      {/* Bubble */}
      <div
        className={`max-w-[80%] rounded-[20px] px-4 py-3 text-xs sm:text-sm leading-relaxed shadow-sm ${
          isUser
            ? 'bg-[#2563EB] text-white rounded-br-xs font-medium'
            : 'bg-white/95 border border-slate-200/90 text-[#0B0F19] rounded-bl-xs backdrop-blur-md'
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
        "Hi! 👋 I'm your Honest Career Coach. Ask me anything about your resume, interview strategy, skill gaps, or career direction!",
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

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
        { role: 'assistant', content: `That didn't go through. Check your connection and try again.` },
      ])
      toast.error(err.message || 'Failed to send message.')
    }
    setLoading(false)
  }

  return (
    <div className="w-full max-w-4xl mx-auto flex flex-col h-[calc(100vh-140px)] space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-1">
        <div>
          <Badge sparkle size="sm" className="mb-1.5">
            AI Assistant
          </Badge>
          <h1 className="text-2xl font-extrabold text-[#0B0F19] tracking-tight">
            Honest Career Coach
          </h1>
          <p className="text-xs text-[#64748B]">
            Strategic guidance on resumes, negotiations, and technical interviews.
          </p>
        </div>
      </div>

      {/* Messages Stream Container */}
      <GlassCard className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 border-white/95 shadow-glass-lg rounded-[24px]">
        <AnimatePresence>
          {messages.map((msg, i) => (
            <Message key={i} msg={msg} />
          ))}
        </AnimatePresence>

        {/* Loading / Typing Indicator with Bouncing Dots */}
        {loading && (
          <div className="flex gap-3 items-end">
            <div className="w-8 h-8 rounded-full bg-blue-50 border border-blue-200 flex items-center justify-center shrink-0 shadow-sm mb-1 text-[#2563EB]">
              <Loader2 size={16} className="animate-spin" />
            </div>
            <div className="bg-white/95 border border-slate-200/90 rounded-[20px] rounded-bl-xs px-4 py-3 shadow-sm flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#2563EB] animate-bounce [animation-delay:-0.3s]" />
              <span className="w-2 h-2 rounded-full bg-[#2563EB] animate-bounce [animation-delay:-0.15s]" />
              <span className="w-2 h-2 rounded-full bg-[#2563EB] animate-bounce" />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </GlassCard>

      {/* Quick Prompts Strip */}
      <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar">
        {QUICK_PROMPTS.map((p, i) => (
          <button
            key={i}
            type="button"
            onClick={() => send(p)}
            className="shrink-0 text-xs px-3.5 py-1.5 rounded-full bg-white/80 border border-slate-200/80 hover:border-blue-300 hover:bg-blue-50/50 text-[#475569] font-medium transition-all shadow-xs"
          >
            <Sparkles size={11} className="inline mr-1.5 text-[#2563EB]" />
            {p}
          </button>
        ))}
      </div>

      {/* Input Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault()
          send()
        }}
        className="flex gap-3"
      >
        <div className="relative flex-1">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me anything about your resume, career, or interviews..."
            className="w-full h-12 px-4 rounded-xl bg-white/95 border border-slate-200/90 text-xs sm:text-sm text-[#0B0F19] placeholder:text-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] shadow-sm"
          />
        </div>

        <Button
          type="submit"
          variant="primary"
          size="md"
          disabled={!input.trim() || loading}
          className="h-12 px-5"
        >
          <Send size={15} />
        </Button>
      </form>
    </div>
  )
}
