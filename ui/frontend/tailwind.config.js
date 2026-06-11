/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        autoliv: {
          blue:        "#003DA5",
          "blue-dark": "#002D7A",
          "blue-light":"#E8EEF9",
          "blue-mid":  "#1A52B8",
          white:       "#FFFFFF",
          grey:        "#4A4A4A",
          "grey-light":"#F5F6FA",
          border:      "#D8DEE9",
          charcoal:    "#1A1A1A",
        },
      },
      fontFamily: {
        sans: ["Segoe UI", "Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
}