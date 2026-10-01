/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#FF6B00',
          dark:    '#CC4E00',
          light:   '#FF8533',
        },
        accent: {
          DEFAULT: '#FFA726',
          dark:    '#F57C00',
          light:   '#FFB74D',
        },
        surface: {
          DEFAULT: '#0B0A10',
          dark:    '#07060A',
          card:    '#13121C',
          elevated:'#1A1826',
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
          'linear-gradient(135deg, #07060A 0%, #1A0D06 50%, #07060A 100%)',
      },
      boxShadow: {
        'glow':        '0 0 25px rgba(255, 107, 0, 0.4)',
        'glow-lg':     '0 0 50px rgba(255, 107, 0, 0.55)',
        'glow-amber':  '0 0 30px rgba(255, 167, 38, 0.45)',
        'glow-red':    '0 0 25px rgba(255, 107, 0, 0.4)',
        'glow-red-lg': '0 0 50px rgba(255, 107, 0, 0.55)',
        'card':        '0 4px 24px rgba(0, 0, 0, 0.5)',
      },
    },
  },
  plugins: [],
}
