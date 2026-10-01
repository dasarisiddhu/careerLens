# CareerLens — Component Inventory & Transformation Map

## Overview
This document catalogs every component currently in the frontend, defining whether it is kept, restyled, replaced, or newly introduced for the Light 3D Glassmorphism rework.

---

### 1. Existing UI Primitives (`src/components/ui/`)

| Current Component | Current Status | Action | Target Transformation / New Name |
|---|---|---|---|
| `Button.jsx` | Dark cyberpunk styling (orange glow) | **Replaced & Standardized** | Pill buttons (primary solid black/blue, white glass secondary, ghost, destructive) matching REF-1 |
| `Card.jsx` | Dark glass card with orange border | **Replaced** | `GlassCard.jsx` with light 3D glass tokens (`--glass-bg`, `--glass-border`, `--glass-shadow`) |
| `Badge.jsx` | Dark orange badge | **Replaced** | `Badge.jsx` pill style with sparkle icon matching REF-1 |
| `Input.jsx` | Dark inputs with orange focus | **Restyled** | Clean white/glass input with 2px focus ring, micro-label support |
| `Modal.jsx` | Dark dialog overlay | **Restyled** | `Dialog.jsx` with light glass backdrop, smooth entrance, keyboard accessibility |
| `Tabs.jsx` | Underline tabs | **Restyled** | Pill switch tabs with animated shared layoutId indicator |
| `index.js` | Barrel export | **Updated** | Exports all primitives including new additions |

---

### 2. New Core Design System Primitives (`src/components/ui/`)

| Component | Responsibility | Visual Specification |
|---|---|---|
| `GlassCard.jsx` | Foundational surface container | Light glassmorphism, 20px radius, inner 1px border, soft shadow |
| `StatCard.jsx` | Metric display with icon tile | Tinted icon tile (blue, violet, coral), bold number, subtle label |
| `ScoreRing.jsx` | SVG donut progress score | Circular meter (e.g., 98/100, 92/100) with animated count-up |
| `FileDropzone.jsx` | Drag-and-drop resume upload | Clean dashed glass dropzone, file validation, upload states |
| `ScoreBadge.jsx` | Small score pill indicator | Donut chip or mini pill with status color |
| `EmptyState.jsx` | Zero-state placeholder | Mascot illustration + informative text + CTA |
| `ErrorState.jsx` | Data fetch / mutation failure | Mascot error expression + clear message + retry button |
| `Skeleton.jsx` | Shimmer loading placeholder | Neutral glass shimmer avoiding layout shift |

---

### 3. Layout Components (`src/components/layout/`)

| Component | Current Status | Target Transformation |
|---|---|---|
| `DashboardLayout.jsx` | Dark sidebar with orange accents | **Restyled to Light Glassmorphism**: Clean white-glass sidebar, primary "Resume Intelligence" & secondary "More Tools" groups, soft dividers, user status pill |
| `Navbar.jsx` (New) | Inlined in `Landing.jsx` | **Extracted & Standardized**: Sticky glass nav (72px, radius 20px, pill navigation indicator, login + Get Started CTA) |
| `Footer.jsx` (New) | Inlined in `Landing.jsx` | **Extracted & Standardized**: Clean footer with feature links, legal, branding |
| `PageShell.jsx` (New) | None (ad-hoc padding per page) | **Standardized Wrapper**: Consistent max-width, two-tone page title, breadcrumb |

---

### 4. Mascot & Assistant System (`src/mascot/` & `src/components/companion/`)

| Component | Current Status | Target Transformation |
|---|---|---|
| `Nova.jsx` | Heavy 860 kB Three.js 3D canvas | **Replaced**: Lightweight layered WebP/SVG mascot component (<= 180 kB) with 60fps Framer Motion transforms |
| `NovaFallback.jsx` | Static gradient fallback | **Integrated** into `Mascot.jsx` fallback |
| `CompanionWidget.jsx` | Fixed bottom-right launcher | **Restyled & Enhanced**: Mascot head launcher, REF-2 style speech bubble nudge, quick actions (linked to `/dashboard/optimizer`) |
| `Mascot.jsx` (New) | None | Canonical robot mascot ("Lens") matching REF-1 image: smiling eyes, podium glow, state machine |
| `useMascotState.js` (New) | None | State driver: `idle`, `thinking`, `success`, `error`, `pointing`, `wave` |

---

### 5. Pages (`src/pages/`)

| Page | Current Status | Action |
|---|---|---|
| `Landing.jsx` | Dark cyberpunk landing page | **Completely Reworked to REF-1**: Light 3D glass, hero with robot mascot on podium, 3 floating stat cards, complete career OS sections, confusion-to-clarity comparison, step-by-step strip |
| `Login.jsx`, `Signup.jsx`, `ForgotPassword.jsx` | Dark orange glass cards | **Restyled**: Clean centered light-glass card, subtle mascot peek, clear input validation |
| `Dashboard.jsx` | Dark dashboard | **Restyled**: Light glass cards, latest score rings, quota meters, quick actions |
| `ResumeOptimizer.jsx` | Dark System B UI | **Restyled Shell & Cards**: Preserves all 2,600+ lines of optimization logic, recruiter lens, bullet diffs, while wrapping in the light glassmorphic design system |
| `ResumeAnalysis.jsx` / `AnalysisResult.jsx` | Dark System A UI | **Restyled**: Light glass breakdown cards, score rings, safe data fallback |
| `JobMatch.jsx` / `JobMatchEngine.jsx` | Dark job match list | **Restyled**: Light cards, company logos, match percentage pills |
| `MockInterview.jsx` | Dark voice stage | **Restyled**: Light glass stage, pulsing mic ring, speech recognition indicators |
| `Chatbot.jsx` | Dark chat bubbles | **Restyled**: User bubbles (blue), assistant bubbles (glass), typing indicator with mascot |
| `TechNews.jsx` / `HiringNews.jsx` | Dark news list | **Restyled**: Clean card grid with image tiles |
| `CareerSwitch.jsx`, `ProgressTracker.jsx`, `CareerRecommendations.jsx`, `community.jsx`, `interviewpredictor.jsx`, `Portfolio.jsx`, `Upgrade.jsx` | Dark dashboard pages | **Restyled**: Preserves exact business logic with light glass theme |
