/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0a0f18',
        surface: '#121a24',
        accent: '#00d2ff',
        neonBlue: '#0bf',
        danger: '#ff2a2a',
        success: '#00e676',
      },
      fontFamily: {
        mono: ['"Fira Code"', 'monospace'],
        sans: ['"Inter"', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
