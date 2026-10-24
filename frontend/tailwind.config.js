/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          900: "#07070b",
          800: "#0c0c14",
          700: "#11111c",
          600: "#16161f",
        },
        accent: {
          DEFAULT: "#7c5cff",
          soft: "#9d85ff",
          cyan: "#22d3ee",
          pink: "#ff5c9a",
        },
      },
      fontFamily: {
        display: ['"Space Grotesk"', "system-ui", "sans-serif"],
        sans: ['"Manrope"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(124,92,255,0.25), 0 12px 40px -12px rgba(124,92,255,0.45)",
        card: "0 20px 60px -30px rgba(0,0,0,0.9)",
      },
      backgroundImage: {
        "accent-gradient": "linear-gradient(135deg,#7c5cff 0%,#22d3ee 100%)",
        "accent-soft": "linear-gradient(135deg,#9d85ff 0%,#22d3ee 100%)",
      },
      keyframes: {
        "pulse-glow": {
          "0%,100%": { opacity: "0.55" },
          "50%": { opacity: "1" },
        },
        float: {
          "0%,100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-6px)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: {
        "pulse-glow": "pulse-glow 2.4s ease-in-out infinite",
        float: "float 6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
