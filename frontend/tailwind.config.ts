import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "var(--color-paper)",
        ink: "var(--color-ink)",
        amber: {
          DEFAULT: "var(--color-amber)",
          soft: "var(--color-amber-soft)",
        },
        green: "var(--color-green)",
        red: "var(--color-red)",
        "warm-gray": "var(--color-warm-gray)",
        surface: {
          base: "var(--surface-base)",
          raised: "var(--surface-raised)",
          sunken: "var(--surface-sunken)",
          overlay: "var(--surface-overlay)",
        },
      },
      fontFamily: {
        display: ["Instrument Serif", "ui-serif", "Georgia", "serif"],
        mono: ["DM Mono", "ui-monospace", "SFMono-Regular", "monospace"],
        sans: ["system-ui", "-apple-system", "Segoe UI", "Helvetica", "sans-serif"],
      },
      fontSize: {
        xs: "var(--text-xs)",
        sm: "var(--text-sm)",
        base: "var(--text-base)",
        md: "var(--text-md)",
        lg: "var(--text-lg)",
        xl: "var(--text-xl)",
        "2xl": "var(--text-2xl)",
        "3xl": "var(--text-3xl)",
        "4xl": "var(--text-4xl)",
      },
      spacing: {
        "1": "var(--space-1)",
        "2": "var(--space-2)",
        "3": "var(--space-3)",
        "4": "var(--space-4)",
        "5": "var(--space-5)",
        "6": "var(--space-6)",
        "7": "var(--space-7)",
        "8": "var(--space-8)",
        "9": "var(--space-9)",
        "10": "var(--space-10)",
      },
      borderRadius: {
        sm: "4px",
        DEFAULT: "8px",
        md: "10px",
        lg: "14px",
        xl: "20px",
        "2xl": "28px",
      },
      transitionTimingFunction: {
        "expo-out": "cubic-bezier(0.16, 1, 0.3, 1)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "clip-reveal": {
          "0%": { clipPath: "inset(0 100% 0 0)" },
          "100%": { clipPath: "inset(0 0 0 0)" },
        },
        "pulse-amber": {
          "0%, 100%": { boxShadow: "0 0 0 0 var(--color-amber-soft)" },
          "50%": { boxShadow: "0 0 0 6px transparent" },
        },
      },
      animation: {
        "fade-up": "fade-up 380ms cubic-bezier(0.16, 1, 0.3, 1) both",
        "clip-reveal": "clip-reveal 600ms cubic-bezier(0.16, 1, 0.3, 1) both",
        "pulse-amber": "pulse-amber 2.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
