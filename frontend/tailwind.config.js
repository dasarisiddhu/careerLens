/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#e11d48',
          dark:    '#be123c',
          light:   '#fb7185',
        },
        accent:  '#f97316',
        surface: {
          DEFAULT: '#14141c',
          dark:    '#0f0f14',
          card:    '#1a1a24',
          elevated:'#1e1e2a',
        },
      },
      fontFamily: {
        display: [
          'Clash Display',
          'SF Pro Display',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'sans-serif',
        ],
        sans: [
          'Cabinet Grotesk',
          'SF Pro Text',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'sans-serif',
        ],
        mono: [
          'JetBrains Mono',
          'Cascadia Code',
          'Fira Code',
          'Consolas',
          'monospace',
        ],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'hero-gradient':
          'linear-gradient(135deg, #0a0a0f 0%, #1a0710 50%, #0a0a0f 100%)',
      },
      boxShadow: {
        'glow-red':    '0 0 20px rgba(225, 29, 72, 0.3)',
        'glow-red-lg': '0 0 40px rgba(225, 29, 72, 0.45)',
        'card':        '0 4px 24px rgba(0, 0, 0, 0.4)',
      },
    },
  },
  plugins: [],
}
