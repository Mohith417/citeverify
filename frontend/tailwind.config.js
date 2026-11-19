/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#14122B",
        paper: "#F6F4FC",
        violet: "#4B36F5",
        "violet-deep": "#2C1DB8",
        lavender: "#D9D2FF",
        "lavender-soft": "#EDE9FF",
        coral: "#FF6B45",
        "coral-soft": "#FFE3D9",
        slate: "#6B6880",
        line: "#DAD4F2",
        mint: "#C7F2DD",
        amber: "#F6C453",
        danger: "#E5484D",
      },
      fontFamily: {
        display: ['"Archivo Black"', "Arial Black", "sans-serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "monospace"],
      },
      boxShadow: {
        block: "6px 6px 0 0 #14122B",
        "block-sm": "4px 4px 0 0 #14122B",
        "block-violet": "6px 6px 0 0 #4B36F5",
        soft: "0 18px 40px -28px rgba(20,18,43,0.45)",
      },
      keyframes: {
        rise: {
          "0%": { opacity: "0", transform: "translateY(14px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseBar: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.45" },
        },
      },
      animation: {
        rise: "rise 0.5s ease-out both",
        pulseBar: "pulseBar 1.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
