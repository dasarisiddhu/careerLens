// ============================================================
// CareerLens – Improvement Goal Tracker
// File: frontend/src/components/dashboard/GoalTracker.jsx
// ============================================================

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { pageTransition } from '../../utils/animations'
import { CheckCircle, Circle, Target, TrendingUp, Plus, Trash2, Trophy } from 'lucide-react'

const DEFAULT_TASKS = (currentScore, targetScore) => [
  { id: 1, text: 'Add a complete GitHub project with README', done: false, points: 8 },
  { id: 2, text: 'Improve resume with quantified achievements (e.g. "Reduced load time by 40%")', done: false, points: 6 },
  { id: 3, text: 'Add missing keywords from job description to resume', done: false, points: 7 },
  { id: 4, text: 'Build one project using a required skill you are missing', done: false, points: 10 },
  { id: 5, text: 'Get at least 3 stars on a GitHub repo', done: false, points: 4 },
  { id: 6, text: 'Add a professional summary to your resume', done: false, points: 5 },
]

const STORAGE_KEY = 'careerlens_goal_tracker'

const buttonMotion = {
  whileHover: { scale: 1.03, y: -1 },
  whileTap: { scale: 0.97 },
  transition: { duration: 0.15, ease: 'easeOut' },
}

function CircleMeter({ value, size = 80, color }) {
  const r = (size - 10) / 2
  const circ = 2 * Math.PI * r
  const offset = circ - (value / 100) * circ
  return (
    <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth={7} />
      <motion.circle cx={size/2} cy={size/2} r={r} fill="none"
        stroke={color} strokeWidth={7} strokeLinecap="round"
        strokeDasharray={circ}
        initial={{ strokeDashoffset: circ }}
        animate={{ strokeDashoffset: offset }}
        transition={{ duration: 1.2, ease: 'easeOut' }}
      />
    </svg>
  )
}

export default function GoalTracker({ currentProbability = 0, targetProbability = 70, missingSkills = [], recommendedProjects = [] }) {
  const [tasks,    setTasks]    = useState(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || DEFAULT_TASKS(currentProbability, targetProbability) }
    catch { return DEFAULT_TASKS(currentProbability, targetProbability) }
  })
  const [newTask,  setNewTask]  = useState('')
  const [target,   setTarget]   = useState(targetProbability)

  // Inject AI-suggested tasks from interview predictor
  useEffect(() => {
    const aiTasks = []
    missingSkills.slice(0, 3).forEach((skill, i) => {
      aiTasks.push({ id: Date.now() + i, text: `Learn ${skill}`, done: false, points: 8 })
    })
    recommendedProjects.slice(0, 2).forEach((p, i) => {
      aiTasks.push({ id: Date.now() + 100 + i, text: `Build: ${p.title || p}`, done: false, points: 10 })
    })
    if (aiTasks.length > 0) {
      setTasks(prev => {
        const existingTexts = prev.map(t => t.text)
        const newOnes = aiTasks.filter(t => !existingTexts.includes(t.text))
        const merged = [...prev, ...newOnes]
        localStorage.setItem(STORAGE_KEY, JSON.stringify(merged))
        return merged
      })
    }
  }, [missingSkills, recommendedProjects])

  const toggle = (id) => {
    const updated = tasks.map(t => t.id === id ? { ...t, done: !t.done } : t)
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
    const updated = tasks.filter(t => t.id !== id)
    setTasks(updated)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
  }

  const doneTasks    = tasks.filter(t => t.done)
  const totalPoints  = tasks.reduce((a, t) => a + t.points, 0)
  const earnedPoints = doneTasks.reduce((a, t) => a + t.points, 0)
  const progress     = totalPoints > 0 ? Math.round((earnedPoints / totalPoints) * 100) : 0
  const projectedIncrease = Math.round((earnedPoints / Math.max(totalPoints, 1)) * (target - currentProbability))
  const projectedScore    = Math.min(currentProbability + projectedIncrease, target)

  const currentColor   = currentProbability >= 70 ? '#22c55e' : currentProbability >= 50 ? '#f59e0b' : '#ef4444'
  const projectedColor = projectedScore >= 70 ? '#22c55e' : projectedScore >= 50 ? '#f59e0b' : '#f97316'

  return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
    <div className="glass rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-white/5 flex items-center gap-2">
        <Target size={18} className="text-amber-400" />
        <h2 className="font-bold text-white">Reach Your Target Interview Probability</h2>
      </div>

      <div className="p-5 space-y-6">
        {/* Score meters */}
        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="space-y-2">
            <div className="relative w-20 mx-auto">
              <CircleMeter value={currentProbability} color={currentColor} />
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-sm font-black text-white">{currentProbability}%</span>
              </div>
            </div>
            <p className="text-xs text-[#78716c]">Current</p>
          </div>
          <div className="flex flex-col items-center justify-center">
            <TrendingUp size={20} className="text-amber-400 mb-1" />
            <p className="text-xs text-[#44403c]">Progress</p>
            <p className="text-sm font-bold text-amber-400">{progress}%</p>
          </div>
          <div className="space-y-2">
            <div className="relative w-20 mx-auto">
              <CircleMeter value={target} color="#f59e0b" />
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-sm font-black text-white">{target}%</span>
              </div>
            </div>
            <p className="text-xs text-[#78716c]">Target</p>
          </div>
        </div>

        {/* Projected score */}
        {doneTasks.length > 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="p-3 rounded-xl bg-green-500/10 border border-green-500/20 text-center">
            <p className="text-xs text-[#78716c]">Projected score if you complete remaining tasks</p>
            <p className="text-2xl font-black text-green-400 mt-1">{projectedScore}%</p>
          </motion.div>
        )}

        {/* Target input */}
        <div className="flex items-center gap-3">
          <label className="text-xs text-[#78716c] whitespace-nowrap">Set target:</label>
          <input type="range" min={currentProbability + 5} max={90} value={target}
            onChange={e => setTarget(Number(e.target.value))}
            className="flex-1 accent-amber-500" />
          <span className="text-sm font-bold text-amber-400 w-10 text-right">{target}%</span>
        </div>

        {/* Task list */}
        <div className="space-y-2">
          <p className="text-xs font-semibold text-[#78716c] uppercase tracking-wide">
            Tasks ({doneTasks.length}/{tasks.length} done)
          </p>
          <div className="space-y-1.5 max-h-72 overflow-y-auto pr-1">
            {tasks.map((task) => (
              <motion.div key={task.id} layout
                className={`flex items-center gap-3 p-3 rounded-xl border transition-all
                  ${task.done ? 'bg-green-500/5 border-green-500/10' : 'bg-white/3 border-white/5 hover:border-white/10'}`}>
                <motion.button {...buttonMotion} onClick={() => toggle(task.id)} className="shrink-0">
                  {task.done
                    ? <CheckCircle size={18} className="text-green-400" />
                    : <Circle size={18} className="text-[#44403c] hover:text-amber-400 transition-colors" />}
                </motion.button>
                <span className={`flex-1 text-sm ${task.done ? 'line-through text-[#44403c]' : 'text-[#d6d3d1]'}`}>
                  {task.text}
                </span>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-xs text-amber-400 font-semibold">+{task.points}pts</span>
                  <motion.button {...buttonMotion} onClick={() => removeTask(task.id)} className="text-[#292524] hover:text-red-400 transition-colors">
                    <Trash2 size={12} />
                  </motion.button>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Add task */}
        <div className="flex gap-2">
          <input value={newTask} onChange={e => setNewTask(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && addTask()}
            placeholder="Add your own task..."
            className="input-field flex-1 text-sm py-2" />
          <motion.button {...buttonMotion} onClick={addTask} disabled={!newTask.trim()}
            className="btn-primary px-3 py-2 disabled:opacity-40">
            <Plus size={15} />
          </motion.button>
        </div>

        {/* Completion celebration */}
        {progress >= 100 && (
          <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            className="p-4 rounded-2xl bg-yellow-500/10 border border-yellow-500/20 text-center space-y-2">
            <Trophy size={28} className="text-yellow-400 mx-auto" />
            <p className="text-yellow-300 font-bold">All tasks complete! Re-run the Interview Predictor now.</p>
          </motion.div>
        )}
      </div>
    </div>
    </motion.div>
  )
}






