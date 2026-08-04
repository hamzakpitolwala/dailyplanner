/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: 'var(--background)',
        card: 'var(--card)',
        border: 'var(--border)',
        text: 'var(--text)',
        'sidebar-bg': 'var(--sidebar-bg)',
        'sidebar-hover': 'var(--sidebar-hover)',
        primary: 'var(--primary)',
        'primary-hover': 'var(--primary-hover)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
