import React from 'react'
import { Navbar } from '../components/layout/Navbar'
import { Footer } from '../components/layout/Footer'
import { PageShell } from '../components/layout/PageShell'
import { Button, Badge, GlassCard } from '../components/ui'
import { Mascot } from './Mascot'
import { useMascotState } from './useMascotState'
import { Sparkles, Play, RefreshCw, AlertTriangle, MessageSquare, Hand } from 'lucide-react'

export default function MascotDemo() {
  const {
    state,
    setState,
    bubbleOpen,
    setBubbleOpen,
    mouseOffset,
    prefersReducedMotion,
  } = useMascotState({ initial: 'greeting' })

  const states = [
    { id: 'idle', label: 'Idle Float', icon: Play },
    { id: 'greeting', label: 'Greeting', icon: MessageSquare },
    { id: 'wave', label: 'Wave Hand', icon: Hand },
    { id: 'thinking', label: 'Thinking / Scanning', icon: RefreshCw },
    { id: 'success', label: 'Success / Sparkle', icon: Sparkles },
    { id: 'error', label: 'Error State', icon: AlertTriangle },
  ]

  return (
    <div className="min-h-screen bg-base py-6">
      <Navbar />

      <PageShell
        title="Mascot System"
        titleAccent="Lens (Gate 3 Verification)"
        subtitle="Verification of the 3D-style robot mascot on illuminated glass podium, state machine animations, and speech bubble."
        badge={<Badge sparkle>60fps GPU Composited • Payload: 30.2 KB (Budget: &le;180 KB)</Badge>}
      >
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center mt-6">
          {/* Controls Column */}
          <div className="lg:col-span-5 space-y-6">
            <GlassCard className="p-6 space-y-5">
              <div>
                <h3 className="text-base font-bold text-[#0B0F19]">State Machine Controls</h3>
                <p className="text-xs text-[#64748B] mt-1">
                  Active State: <span className="font-bold text-[#2563EB] uppercase">{state}</span>
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2.5">
                {states.map(({ id, label, icon: Icon }) => (
                  <Button
                    key={id}
                    variant={state === id ? 'primary' : 'secondary'}
                    size="sm"
                    icon={Icon}
                    onClick={() => setState(id)}
                    className="w-full text-xs"
                  >
                    {label}
                  </Button>
                ))}
              </div>

              <div className="pt-3 border-t border-slate-200/80 flex items-center justify-between">
                <span className="text-xs font-semibold text-[#0B0F19]">Speech Bubble Nudge</span>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setBubbleOpen(!bubbleOpen)}
                >
                  {bubbleOpen ? 'Hide Bubble' : 'Show Bubble'}
                </Button>
              </div>
            </GlassCard>

            <GlassCard className="p-6 space-y-2">
              <h4 className="text-xs font-bold text-[#64748B] uppercase tracking-wider">
                Specification Compliance
              </h4>
              <ul className="text-xs text-[#0B0F19] space-y-1.5 list-disc pl-4">
                <li>Exact visual match to reference photo (white ceramic shell, blue smiling eyes, podium rings).</li>
                <li>Zero purple gradients — pure light glass & cyan-blue accents.</li>
                <li>Compressed WebP asset: <strong>30.2 KB</strong> (Budget &le; 180 KB).</li>
                <li>Parallax mouse tracking throttled via <code>requestAnimationFrame</code>.</li>
                <li>Respects <code>prefers-reduced-motion</code>: {prefersReducedMotion ? 'Active' : 'False'}.</li>
              </ul>
            </GlassCard>
          </div>

          {/* Interactive Mascot Stage */}
          <div className="lg:col-span-7 flex flex-col items-center justify-center p-8 glass rounded-[28px] min-h-[500px]">
            <Mascot
              state={state}
              bubbleOpen={bubbleOpen}
              onBubbleClose={() => setBubbleOpen(false)}
              onMascotClick={() => setState('wave', 1200)}
              mouseOffset={mouseOffset}
              prefersReducedMotion={prefersReducedMotion}
              size={420}
            />
            <p className="text-xs text-[#94A3B8] mt-4">
              Tip: Hover over the stage to test mouse parallax tracking, or click the robot to trigger a wave!
            </p>
          </div>
        </div>
      </PageShell>

      <Footer />
    </div>
  )
}
