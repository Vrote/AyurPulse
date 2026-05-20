/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ayur: {
          dark: '#064e3b',     // Deep emerald green
          medium: '#047857',   // Classic forest green
          light: '#a7f3d0',    // Soft mint green
          cream: '#fef3c7',    // Calming warm cream
          gold: '#d97706',     // Rich gold/amber highlight
          stone: '#78716c',    // Calm warm grey
        }
      }
    },
  },
  plugins: [],
}
