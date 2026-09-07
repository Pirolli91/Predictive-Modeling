import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ocean: {
          50: "#eefbff",
          100: "#d6f3ff",
          200: "#b3e9ff",
          300: "#7ddbff",
          400: "#3fc4ff",
          500: "#12a6f5",
          600: "#0685d1",
          700: "#0669a9",
          800: "#0b598c",
          900: "#0f4a74",
          950: "#0a2f4d",
        },
        sand: {
          50: "#fdfaf3",
          100: "#faf1dd",
          200: "#f3e0b3",
          300: "#eaca80",
          400: "#e0ae4f",
          500: "#d6952f",
        },
      },
    },
  },
  plugins: [],
};

export default config;
