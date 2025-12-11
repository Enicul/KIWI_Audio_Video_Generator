import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // KIWI-Video 黑白灰配色系统
        kiwi: {
          black: "#0a0a0a",
          dark: "#1a1a1a",
          gray: {
            900: "#171717",
            800: "#262626",
            700: "#404040",
            600: "#525252",
            500: "#737373",
            400: "#a3a3a3",
            300: "#d4d4d4",
            200: "#e5e5e5",
            100: "#f5f5f5",
          },
          white: "#fafafa",
        },
      },
      boxShadow: {
        // 浮动卡片阴影效果
        "card": "0 8px 32px rgba(0, 0, 0, 0.4), 0 2px 8px rgba(0, 0, 0, 0.3)",
        "card-hover": "0 12px 48px rgba(0, 0, 0, 0.5), 0 4px 12px rgba(0, 0, 0, 0.4)",
        "subtle": "0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24)",
      },
      fontFamily: {
        sans: ["SF Pro Display", "Inter", "system-ui", "sans-serif"],
        mono: ["SF Mono", "Fira Code", "monospace"],
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out",
        "slide-up": "slideUp 0.5s ease-out",
        "float": "float 6s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;

