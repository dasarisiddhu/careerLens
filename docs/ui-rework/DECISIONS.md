# CareerLens — Architectural & Design Decisions Log

### Decision 001: Strict Palette Fidelity (No Purple Gradient)
- **Decision**: Use pure light glassmorphism palette derived directly from the provided reference photo (ice blue `--bg-wash-1: #EBF3FF`, light cyan/neutral `--bg-base: #F8FAFC`, dark charcoal text `#0F172A`, primary blue `#2563EB`, dark black buttons `#0B0F19`), completely omitting any heavy purple/violet gradients as instructed.
- **Alternative**: Default purple/lavender gradient bloom from general text prompt.
- **Reason**: User explicitly instructed: "don't add purple gradient make exactly like the photo".

### Decision 002: Mascot 2.5D Layered Asset Strategy over WebGL
- **Decision**: Build the robot mascot as a layered SVG/WebP component using GPU-composited CSS and Framer Motion transforms rather than a 860 kB Three.js bundle.
- **Alternative**: Three.js canvas (`Nova.jsx`).
- **Reason**: Meets the strict <= 180 kB mascot payload budget and prevents mobile LCP regressions while delivering 60fps animations.

### Decision 003: Response Adapter Boundary
- **Decision**: Introduce non-destructive adapter normalizers in `src/services/adapters/` that sanitize and validate API outputs without modifying the underlying HTTP service signatures or backend expectations.
- **Alternative**: Modify `services/api.js` directly or let UI handle undefined fields ad-hoc.
- **Reason**: Prevents crashes from malformed/partial LLM responses while strictly respecting the frozen backend constraint.
