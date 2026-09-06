/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        t: {
          bg:     "#000a0a",
          card:   "#050f0c",
          border: "#0e2921",
          accent: "#00d4aa",
          dim:    "#009980",
          text:   "#c8f5ec",
          muted:  "#4a9985",
        },
      },
    },
  },
  plugins: [],
};
