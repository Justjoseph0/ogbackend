/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#15171c",
        panel: "#ffffff",
        line: "#d8dde6",
        brand: "#0f766e",
        accent: "#b45309",
      },
      boxShadow: {
        soft: "0 14px 40px rgba(21, 23, 28, 0.08)",
      },
    },
  },
  plugins: [],
};
