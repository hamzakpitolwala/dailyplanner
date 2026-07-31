/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#f8fafc',
        card: '#ffffff',
        border: '#e2e8f0',
        text: '#0f172a',
      }
    },
  },
  plugins: [],
}
