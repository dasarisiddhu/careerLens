import React, { useState } from 'react'
import {
  Button,
  Badge,
  GlassCard,
  StatCard,
  ScoreRing,
  Input,
  Dialog,
  Tabs,
  Skeleton,
  FileDropzone,
  EmptyState,
  ErrorState,
} from '../../components/ui'
import { Navbar } from '../../components/layout/Navbar'
import { Footer } from '../../components/layout/Footer'
import { PageShell } from '../../components/layout/PageShell'
import {
  ArrowRight,
  Briefcase,
  Play,
  Mail,
  Lock,
  Layers,
  Sparkles,
  BarChart3,
  CheckCircle,
} from 'lucide-react'

export default function UIDevShowcase() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedFile, setSelectedFile] = useState(null)
  const [showPassword, setShowPassword] = useState(false)

  const showcaseTabs = [
    { id: 'overview', label: 'Overview', icon: Layers },
    { id: 'suggestions', label: 'Suggestions', icon: Sparkles },
    { id: 'skill-match', label: 'Skill Match', icon: BarChart3 },
    { id: 'ats-score', label: 'ATS Score', icon: CheckCircle },
  ]

  return (
    <div className="min-h-screen bg-base py-6">
      <Navbar />

      <PageShell
        title="Design System"
        titleAccent="Component Showcase (Gate 1)"
        subtitle="Verification suite for Light 3D Glassmorphism tokens, buttons, cards, inputs, and interactive primitives matching REF-1."
        badge={<Badge sparkle>Storybook Dev Route (/_dev/ui)</Badge>}
        actions={
          <Button variant="primary" size="sm" trailingIcon={ArrowRight} onClick={() => setDialogOpen(true)}>
            Test Dialog
          </Button>
        }
      >
        <div className="space-y-12 mt-6">
          {/* Section 1: Buttons */}
          <section className="space-y-4">
            <h2 className="text-lg font-bold text-[#0B0F19] border-b border-slate-200 pb-2">
              1. Buttons (Pill Shapes, Multiple Variants & States)
            </h2>
            <div className="flex flex-wrap items-center gap-4">
              <Button variant="primary" trailingIcon={ArrowRight}>
                Analyze My Resume
              </Button>
              <Button variant="blue" trailingIcon={ArrowRight}>
                Primary Blue Pill
              </Button>
              <Button variant="secondary" icon={Play}>
                Watch Demo
              </Button>
              <Button variant="ghost">Ghost Button</Button>
              <Button variant="destructive">Destructive</Button>
              <Button variant="primary" loading>
                Loading Button
              </Button>
              <Button variant="secondary" disabled>
                Disabled
              </Button>
            </div>
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <Button size="sm" variant="primary">Small (sm)</Button>
              <Button size="md" variant="primary">Medium (md)</Button>
              <Button size="lg" variant="primary">Large Hero (52px)</Button>
            </div>
          </section>

          {/* Section 2: Badges */}
          <section className="space-y-4">
            <h2 className="text-lg font-bold text-[#0B0F19] border-b border-slate-200 pb-2">
              2. Badges & Micro-Pills
            </h2>
            <div className="flex flex-wrap items-center gap-3">
              <Badge sparkle>AI Powered Career Guidance →</Badge>
              <Badge variant="neutral">Sample result</Badge>
              <Badge variant="success">98% Match</Badge>
              <Badge variant="warning">3 missing skills</Badge>
              <Badge variant="danger">High risk</Badge>
            </div>
          </section>

          {/* Section 3: StatCards & ScoreRings */}
          <section className="space-y-4">
            <h2 className="text-lg font-bold text-[#0B0F19] border-b border-slate-200 pb-2">
              3. Stat Cards & SVG Score Rings (REF-1 Hero Floating Elements)
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                icon={Briefcase}
                iconColor="violet"
                label="Matched Jobs"
                value="25+"
                tag="Sample result"
              />
              <StatCard
                icon={BarChart3}
                iconColor="blue"
                label="Skill Improvement"
                value="3 suggestions"
                tag="Sample result"
              />
              <GlassCard className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-[#64748B]">Resume Analysis</p>
                  <p className="text-xl font-bold text-[#0B0F19]">Great Score!</p>
                  <span className="text-[10px] font-semibold text-[#2563EB]">Sample result</span>
                </div>
                <ScoreRing score={98} max={100} size={58} />
              </GlassCard>
              <GlassCard className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-[#64748B]">Job Match</p>
                  <p className="text-xl font-bold text-[#0B0F19]">92%</p>
                  <span className="text-[10px] font-semibold text-emerald-600">High Match</span>
                </div>
                <ScoreRing score={92} max={100} size={58} color="#16A34A" />
              </GlassCard>
            </div>
          </section>

          {/* Section 4: Tabs & Inputs */}
          <section className="space-y-4">
            <h2 className="text-lg font-bold text-[#0B0F19] border-b border-slate-200 pb-2">
              4. Pill-Switch Tabs & Form Inputs
            </h2>
            <div className="space-y-4">
              <Tabs tabs={showcaseTabs} activeTab={activeTab} onChange={setActiveTab} />

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
                <Input
                  label="Email Address"
                  placeholder="name@example.com"
                  leadingIcon={Mail}
                />
                <Input
                  label="Password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  leadingIcon={Lock}
                  trailingIcon={showPassword ? Lock : Lock}
                  onTrailingIconClick={() => setShowPassword(!showPassword)}
                />
                <Input
                  label="With Error State"
                  value="invalid-email"
                  error="Please enter a valid email address."
                  leadingIcon={Mail}
                  readOnly
                />
              </div>
            </div>
          </section>

          {/* Section 5: Dropzone & Skeletons */}
          <section className="space-y-4">
            <h2 className="text-lg font-bold text-[#0B0F19] border-b border-slate-200 pb-2">
              5. File Dropzone & Shimmer Skeletons
            </h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <FileDropzone
                selectedFile={selectedFile}
                onFileSelect={(file) => setSelectedFile(file)}
              />
              <div className="space-y-3 p-6 glass rounded-[20px]">
                <p className="text-xs font-bold text-[#64748B] uppercase tracking-wider">
                  Loading Skeleton Shimmer
                </p>
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
                <div className="pt-2 flex gap-3">
                  <Skeleton className="h-10 w-28 rounded-pill" />
                  <Skeleton className="h-10 w-28 rounded-pill" />
                </div>
              </div>
            </div>
          </section>

          {/* Section 6: Empty & Error States */}
          <section className="space-y-4">
            <h2 className="text-lg font-bold text-[#0B0F19] border-b border-slate-200 pb-2">
              6. Empty & Error States
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <EmptyState
                title="No Resumes Analyzed"
                description="Upload your first PDF resume to get instant AI scoring, keyword matching and suggestions."
                actionLabel="Upload Resume"
                onAction={() => {}}
              />
              <ErrorState
                title="Analysis Failed"
                message="That didn't go through. Check your connection and try again."
                onRetry={() => {}}
              />
            </div>
          </section>
        </div>
      </PageShell>

      {/* Interactive Test Dialog */}
      <Dialog
        isOpen={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title="Interactive Dialog Preview"
        description="Verifying light glass modal backdrop, focus trap, and Escape key listener."
      >
        <p className="text-sm text-[#475569] leading-relaxed mb-6">
          This dialog matches the light 3D glassmorphism theme with 20px blur, smooth spring entrance, and accessible keyboard dismissal.
        </p>
        <div className="flex justify-end gap-3">
          <Button variant="secondary" size="sm" onClick={() => setDialogOpen(false)}>
            Close
          </Button>
          <Button variant="primary" size="sm" onClick={() => setDialogOpen(false)}>
            Confirm
          </Button>
        </div>
      </Dialog>

      <Footer />
    </div>
  )
}
