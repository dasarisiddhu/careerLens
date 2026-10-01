// ============================================================
// CareerLens – Improvement Goal Tracker
// File: frontend/src/pages/dashboard/GoalTracker.jsx
// ============================================================

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { pageTransition } from '../../utils/animations'
import { CheckCircle, Circle, Target, TrendingUp, Plus, Trash2, Trophy } from 'lucide-react'
import { GlassCard } from '../../components/ui'

const DEFAULT_TASKS = () => [
  { id: 1, text: 'Add a complete GitHub project with README', done: false, points: 8 },
  { id: 2, text: 'Improve resume with quantified achievements (e.g. "Reduced latency by 40%")', done: false, points: 6 },
  { id: 3, text: 'Add missing keywords from job description to resume', done: false, points: 7 },
  { id: 4, text: 'Build one project using a required skill you are missing', done: false, points: 10 },
  { id: 5, text: 'Get at least 3 stars on a GitHub repo', done: false, points: 4 },
  { id: 6, text: 'Add a professional summary to your resume', done: false, points: 5 },
]

const STORAGE_KEY = 'careerlens_goal_tracker'

function CircleMeter({ value, size = 80, color }) {
  const r = (size - 10) / 2
  const circ = 2 * Math.PI * r
  const offset = circ - (value / 100) * circ
  return (
    <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#E2E8F0" strokeWidth={6} />
      <motion.circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={color}
        strokeWidth={6}
        strokeLinecap="round"
        strokeDasharray={circ}
        initial={{ strokeDashoffset: circ }}
        animate={{ strokeDashoffset: offset }}
        transition={{ duration: 1.2, ease: 'easeOut' }}
      />
    </svg>
  )
}

export default function GoalTracker({
  currentProbability = 0,
  targetProbability = 70,
  missingSkills = [],
  recommendedProjects = [],
}) {
  const [tasks, setTasks] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) || DEFAULT_TASKS()
    } catch {
      return DEFAULT_TASKS()
    }
  })
  const [newTask, setNewTask] = useState('')
  const [target, setTarget] = useState(targetProbability)

  useEffect(() => {
    const aiTasks = []
    missingSkills.slice(0, 3).forEach((skill, i) => {
      aiTasks.push({ id: Date.now() + i, text: `Learn ${skill}`, done: false, points: 8 })
    })
    recommendedProjects.slice(0, 2).forEach((p, i) => {
      aiTasks.push({ id: Date.now() + 100 + i, text: `Build: ${p.title || p}`, done: false, points: 10 })
    })
    if (aiTasks.length > 0) {
      setTasks((prev) => {
        const existingTexts = prev.map((t) => t.text)
        const newOnes = aiTasks.filter((t) => !existingTexts.includes(t.text))
        const merged = [...prev, ...newOnes]
        localStorage.setItem(STORAGE_KEY, JSON.stringify(merged))
        return merged
      })
    }
  }, [missingSkills, recommendedProjects])

  const toggle = (id) => {
    const updated = tasks.map((t) => (t.id === id ? { ...t, done: !t.done } : t))
    setTasks(updated)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
  }

  const addTask = () => {
    if (!newTask.trim()) return
    const updated = [...tasks, { id: Date.now(), text: newTask.trim(), done: false, points: 5 }]
    setTasks(updated)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
    setNewTask('')
  }

  const removeTask = (id) => {
    const updated = tasks.filter((t) => t.id !== id)
    setTasks(updated)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
  }

  const doneTasks = tasks.filter((t) => t.done)
  const totalPoints = tasks.reduce((a, t) => a + t.points, 0)
  const earnedPoints = doneTasks.reduce((a, t) => a + t.points, 0)
  const progress = totalPoints > 0 ? Math.round((earnedPoints / totalPoints) * 100) : 0
  const projectedIncrease = Math.round((earnedPoints / Math.max(totalPoints, 1)) * (target - currentProbability))
  const projectedScore = Math.min(currentProbability + projectedIncrease, target)

  const currentColor = currentProbability >= 70 ? '#16A34A' : currentProbability >= 50 ? '#2563EB' : '#E11D48'
  const projectedColor = projectedScore >= 70 ? '#16A34A' : projectedScore >= 50 ? '#2563EB' : '#E11D48'

  return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
      <GlassCard className="p-5 sm:p-6 border-white/95 shadow-glass space-y-6">
        {/* Header */}
        <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
          <Target size={18} className="text-[#2563EB]" />
          <h2 className="font-bold text-sm sm:text-base text-[#0B0F19]">Reach Your Target Interview Odds</h2>
        </div>

        <div className="space-y-6">
          {/* Score meters */}
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="space-y-1.5">
              <div className="relative w-20 mx-auto">
                <CircleMeter value={currentProbability} color={currentColor} />
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-sm font-black text-[#0B0F19]">{currentProbability}%</span>
                </div>
              </div>
              <p className="text-xs text-[#64748B]">Current</p>
            </div>
            <div className="flex flex-col items-center justify-center">
              <TrendingUp size={20} className="text-[#2563EB] mb-1" />
              <p className="text-[11px] text-[#64748B] font-semibold uppercase">Progress</p>
              <p className="text-sm font-bold text-[#2563EB]">{progress}%</p>
            </div>
            <div className="space-y-1.5">
              <div className="relative w-20 mx-auto">
                <CircleMeter value={target} color="#2563EB" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-sm font-black text-[#0B0F19]">{target}%</span>
                </div>
              </div>
              <p className="text-xs text-[#64748B]">Target</p>
            </div>
          </div>

          {/* Projected score */}
          {doneTasks.length > 0 && (
            <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-center">
              <p className="text-xs text-[#475569]">Projected score once completed</p>
              <p className="text-2xl font-black text-[#16A34A] mt-0.5">{projectedScore}%</p>
            </div>
          )}

          {/* Target input */}
          <div className="flex items-center gap-3">
            <label className="text-xs text-[#64748B] font-bold uppercase whitespace-nowrap">Target:</label>
            <input
              type="range"
              min={currentProbability + 5}
              max={95}
              value={target}
              onChange={(e) => setTarget(Number(e.target.value))}
              className="flex-1 accent-[#2563EB]"
            />
            <span className="text-sm font-bold text-[#2563EB] w-10 text-right">{target}%</span>
          </div>

          {/* Task list */}
          <div className="space-y-2">
            <p className="text-xs font-bold text-[#0B0F19] uppercase tracking-wider">
              Action Plan ({doneTasks.length}/{tasks.length} completed)
            </p>
            <div className="space-y-1.5 max-h-72 overflow-y-auto pr-1">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  className={`flex items-center gap-3 p-3 rounded-xl border transition-all ${
                    task.done
                      ? 'bg-slate-50/60 border-slate-200/60'
                      : 'bg-white border-slate-200/80 shadow-xs'
                  }`}
                >
                  <button type="button" onClick={() => toggle(task.id)} className="shrink-0 text-slate-400 hover:text-[#2563EB]">
                    {task.done ? (
                      <CheckCircle size={18} className="text-[#16A34A]" />
                    ) : (
                      <Circle size={18} />
                    )}
                  </button>
                  <span
                    className={`flex-1 text-xs sm:text-sm ${
                      task.done ? 'line-through text-[#94A3B8]' : 'text-[#0B0F19] font-medium'
                    }`}
                  >
                    {task.text}
                  </span>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-[#2563EB] font-bold">+{task.points}pts</span>
                    <button
                      type="button"
                      onClick={() => removeTask(task.id)}
                      className="text-slate-300 hover:text-rose-600 transition-colors"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Add task */}
          <div className="flex gap-2">
            <input
              value={newTask}
              onChange={(e) => setNewTask(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addTask()}
              placeholder="Add your own custom task..."
              className="flex-1 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs text-[#0B0F19] shadow-xs focus:border-[#2563EB] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/20"
            />
            <button
              type="button"
              onClick={addTask}
              disabled={!newTask.trim()}
              className="flex items-center justify-center rounded-xl bg-[#0B0F19] text-white px-3.5 py-2 text-xs font-bold hover:bg-[#1E293B] disabled:opacity-50 shadow-xs"
            >
              <Plus size={15} />
            </button>
          </div>

          {/* Completion celebration */}
          {progress >= 100 && (
            <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-center space-y-1">
              <Trophy size={24} className="text-[#16A34A] mx-auto" />
              <p className="text-sm font-bold text-emerald-900">All tasks completed! Re-run your prediction now.</p>
            </div>
          )}
        </div>
      </GlassCard>
    </motion.div>
  )
}
