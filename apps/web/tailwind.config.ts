import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eff2ff",
          100: "#dfe7ff",
          300: "#a7b7ff",
          500: "#6c80ff",
          700: "#4f5fe6",
          900: "#2d3478"
        },
        slatex: "#0f172a"
      },
      boxShadow: {
        glow: "0 14px 40px rgba(108, 128, 255, 0.33)"
      }
    }
  },
  plugins: []
};

export default config;
