/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        'pixel': ['"Press Start 2P"', 'monospace'],
        'press-start': ['"Press Start 2P"', 'monospace'],
        'minecraft-mono': ['"Courier New"', 'Courier', 'monospace'],
      },
      colors: {
        mc: {
          grass: '#7CB342',
          dirt: '#8D6E63',
          'dirt-dark': '#5D4037',
          stone: '#9E9E9E',
          wood: '#A1887F',
          sky: '#64B5F6',
          gold: '#FFD54F',
          obsidian: '#263238',
          dark: '#1E1E1E',
          sidebar: '#4E342E',
        }
      },
      borderWidth: {
        '3': '3px',
        '6': '6px',
      },
      keyframes: {
        'loading-bar': {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(400%)' },
        },
        'fade-in-up': {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'loading-bar': 'loading-bar 2s ease-in-out infinite',
        'fade-in-up': 'fade-in-up 0.5s ease-out',
      },
    },
  },
  plugins: [],
}
