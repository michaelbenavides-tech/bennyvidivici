import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        page: '#0a0c12',
        surface: '#0f1219',
        card: '#1a2030',
        border: '#2a3550',
        high: '#eef2ff',
        medium: '#c4cde8',
        low: '#8896c0',
        accent: '#38d4f5',
        warning: '#f5b838',
        danger: '#f55252',
        success: '#38f59a'
      }
    }
  },
  plugins: []
} satisfies Config
