/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: '#F97316',
        background: '#0a0a0a',
        surface: '#141414',
        border: '#262626',
      },
    },
  },
  plugins: [],
};
