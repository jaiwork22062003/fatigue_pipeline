/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          dark: '#070b14',
          card: '#0d1322',
          subcard: '#161f33',
          border: '#1f293d',
          cyan: '#22d3ee',
          emerald: '#34d399',
          rose: '#f43f5e',
          amber: '#fbbf24'
        }
      }
    },
  },
  plugins: [],
}
