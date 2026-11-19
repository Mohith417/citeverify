/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#23211C",
        paper: "#F3EFE6",
        violet: "#6B5B84",
        "violet-deep": "#4C3F5F",
        lavender: "#DCD3E3",
        "lavender-soft": "#EFEAF2",
        coral: "#C67B5C",
        "coral-soft": "#F0DCD0",
        slate: "#6E695E",
        line: "#DFD8C9",
        mint: "#CBD7C6",
        amber: "#D2AC6A",
        danger: "#AE5550",
      },
      fontFamily: {
        display: ['"Archivo Black"', "Arial Black", "sans-serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "monospace"],
      },
      boxShadow: {
        block: "6px 6px 0 0 #23211C",
        "block-sm": "4px 4px 0 0 #23211C",
        "block-xs": "2px 2px 0 0 #23211C",
        "block-violet": "6px 6px 0 0 #6B5B84",
        "block-coral": "6px 6px 0 0 #C67B5C",
        soft: "0 18px 40px -28px rgba(35,33,28,0.45)",
      },
      keyframes: {
        rise: {
          "0%": { opacity: "0", transform: "translateY(14px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0) rotate(var(--tw-rotate))" },
          "50%": { transform: "translateY(-10px) rotate(var(--tw-rotate))" },
        },
        marquee: {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
        pulseBar: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.45" },
        },
        drift: {
          "0%, 100%": { transform: "translate(0,0)" },
          "50%": { transform: "translate(6px,-8px)" },
        },
      },
      animation: {
        rise: "rise 0.55s cubic-bezier(0.22,1,0.36,1) both",
        float: "float 8s ease-in-out infinite",
        marquee: "marquee 26s linear infinite",
        pulseBar: "pulseBar 1.4s ease-in-out infinite",
        drift: "drift 12s ease-in-out infinite",
      },
      transitionTimingFunction: {
        smooth: "cubic-bezier(0.22,1,0.36,1)",
      },
    },
  },
  plugins: [],
};
