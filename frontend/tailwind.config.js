/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        base: {
          DEFAULT: '#F4F7FC',
          surface: '#FFFFFF',
        },
        ink: {
          900: '#0B0F19',
          800: '#111827',
          700: '#1E293B',
          600: '#475569',
          500: '#64748B',
          400: '#94A3B8',
          300: '#CBD5E1',
        },
        primary: {
          DEFAULT: '#2563EB',
          600: '#2563EB',
          500: '#3B82F6',
          400: '#60A5FA',
          100: '#DBEAFE',
          50: '#EFF6FF',
          dark: '#1D4ED8',
          light: '#3B82F6',
        },
        accent: {
          DEFAULT: '#3B82F6',
          light: '#60A5FA',
          dark: '#1D4ED8',
        },
        darkbtn: {
          DEFAULT: '#0B0F19',
          hover: '#1E293B',
        },
        success: {
          DEFAULT: '#16A34A',
          bg: '#DCFCE7',
        },
        warning: {
          DEFAULT: '#F59E0B',
          bg: '#FEF3C7',
        },
        danger: {
          DEFAULT: '#E11D48',
          bg: '#FFE4E6',
        },
      },
      fontFamily: {
        sans: [
          'Plus Jakarta Sans Variable',
          'Plus Jakarta Sans',
          'system-ui',
          '-apple-system',
          'Segoe UI',
          'Roboto',
          'sans-serif',
        ],
        display: [
          'Plus Jakarta Sans Variable',
          'Plus Jakarta Sans',
          'system-ui',
          '-apple-system',
          'sans-serif',
        ],
      },
      borderRadius: {
        pill: '9999px',
        card: '20px',
        inner: '14px',
        icon: '12px',
      },
      boxShadow: {
        glass: '0 20px 50px -15px rgba(37, 99, 235, 0.08), 0 4px 16px rgba(15, 23, 42, 0.04)',
        'glass-lg': '0 28px 64px -16px rgba(37, 99, 235, 0.12), 0 8px 24px rgba(15, 23, 42, 0.06)',
        subtle: '0 2px 8px rgba(15, 23, 42, 0.04)',
      },
    },
  },
  plugins: [],
}
