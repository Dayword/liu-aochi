/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // 游戏化主题色
        primary: {
          DEFAULT: '#6366f1',
          dark: '#4f46e5',
          light: '#818cf8',
        },
        adventure: {
          bg: '#f6f7fb',
          panel: '#ffffff',
          gold: '#d97706',
          exp: '#7c3aed',
          hp: '#e11d48',
          coin: '#d97706',
        },
      },
      fontFamily: {
        game: ['"Segoe UI"', 'PingFang SC', 'Microsoft YaHei', 'sans-serif'],
      },
      animation: {
        float: 'float 3s ease-in-out infinite',
        pulseSlow: 'pulse 2.5s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-8px)' },
        },
      },
    },
  },
  plugins: [],
}
