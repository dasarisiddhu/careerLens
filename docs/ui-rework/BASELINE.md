# CareerLens — Performance Baseline Audit

## Build Measurement Baseline (Vite 5.4.21 Production Build)

### Chunk Distribution & Transfer Sizes
| Chunk Name | Description | Raw Size | Gzip Size |
|---|---|---|---|
| `dist/assets/Nova-BOmFO4NP.js` | 3D Assistant (Three.js, Drei, Postprocessing) | 860.58 kB | 230.28 kB |
| `dist/assets/vendor-charts-DJZIi8fE.js` | Charts library (Recharts, D3 sub-modules) | 383.26 kB | 105.33 kB |
| `dist/assets/index-B2iDSPxc.js` | Main app entry & Landing page bundle | 278.92 kB | 77.17 kB |
| `dist/assets/vendor-react-DMEzE_sp.js` | React 18, React-DOM, React-Router-DOM 6 | 163.66 kB | 53.36 kB |
| `dist/assets/vendor-motion-CcbiJmR-.js` | Framer Motion runtime | 115.84 kB | 38.46 kB |
| `dist/assets/index-CV89EIhz.css` | Global Tailwind CSS stylesheet | 82.43 kB | 13.82 kB |
| `dist/assets/ResumeOptimizer-Df6vKVME.js` | Resume Optimizer view & analysis logic | 68.47 kB | 20.32 kB |
| `dist/assets/ResumeAnalysis-9nqcuGgM.js` | GitHub Analysis view | 66.24 kB | 19.06 kB |
| `dist/assets/MockInterview-Bb9RkzTs.js` | Voice interview stage | 40.62 kB | 11.50 kB |
| `dist/assets/vendor-icons-Bq_M2Uzl.js` | Lucide icon subset | 30.51 kB | 6.03 kB |
| `dist/assets/Upgrade-DcEXkdf7.js` | Stripe upgrade billing modal/view | 19.01 kB | 6.89 kB |
| `dist/assets/CareerSwitch-e1GBD4ep.js` | Career Switch roadmaps | 18.40 kB | 5.09 kB |
| `dist/assets/interviewpredictor-DPPvS3S_.js`| Interview Predictor | 16.48 kB | 5.13 kB |
| `dist/assets/community-B5egpy3q.js` | Community feed | 16.40 kB | 5.07 kB |
| `dist/assets/ATSChecker-B2guGeIH.js` | ATS Checker view | 15.53 kB | 5.25 kB |
| `dist/assets/Dashboard-C6GdTyLA.js` | Dashboard core view | 14.46 kB | 4.58 kB |
| `dist/index.html` | Entry HTML document | 3.34 kB | 1.10 kB |

### Top 10 Heaviest Modules
1. **Three.js & Drei (Nova.js)**: ~860 kB (3D canvas renders in assistant widget; blocks lightweight mobile LCP if mounted)
2. **Recharts & D3**: ~383 kB
3. **App + Landing Core (index.js)**: ~279 kB
4. **React & React-Router**: ~164 kB
5. **Framer Motion**: ~116 kB
6. **ResumeOptimizer**: ~68 kB
7. **ResumeAnalysis**: ~66 kB
8. **MockInterview**: ~41 kB
9. **Lucide Icons**: ~31 kB
10. **Tailwind Global CSS**: ~82 kB

### Lighthouse Target Comparison
| Metric | Current Estimate (Mobile Slow 4G) | Rework Budget | Strategy to Achieve Budget |
|---|---|---|---|
| **LCP (Landing)** | ~3.8s - 4.5s | **<= 2.0s** | Replace heavy 3D canvas with lightweight layered SVG/WebP mascot + high-priority preload; eliminate Three.js on landing |
| **CLS** | ~0.08 - 0.12 | **<= 0.02** | Fixed aspect-ratio containers, no layout-shifting dynamic font loads, clamp-based typography |
| **INP** | ~220ms | **<= 150ms** | Passive listeners, IntersectionObserver instead of scroll handlers, GPU-only transforms |
| **TBT** | ~450ms | **<= 150ms** | Strip Three.js from initial load, chunk Framer Motion with `domAnimation` |
| **Initial JS (gzip)** | ~175 kB + Nova (230 kB) | **<= 150 kB** | Lazy-load all dashboard routes, exclude Three.js from landing, manual chunk tuning |
| **Initial CSS (gzip)** | 13.82 kB | **<= 25 kB** | Currently under budget (13.82 kB <= 25 kB); maintain tight Tailwind purge |
| **Mascot Payload** | N/A (3D canvas ~860 kB) | **<= 180 kB** | High-efficiency WebP/SVG layered assets |
