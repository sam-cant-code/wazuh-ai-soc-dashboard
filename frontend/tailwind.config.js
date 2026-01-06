/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: "#0a0a0f",       // Deep void black
          card: "#13131f",     // Panel background
          border: "#2a2a35",   // Subtle borders
          primary: "#00ff9d",  // Neon Green (Healthy/Success)
          warning: "#ff9900",  // Neon Orange (Warning)
          danger: "#ff3333",   // Neon Red (Critical)
          text: "#e0e0e0",     // Main text
          muted: "#858595",    // Secondary text
        }
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'monospace'], // For logs/data
        display: ['"Share Tech Mono"', 'monospace'], // For headers/clock
      },
      boxShadow: {
        'glow-green': '0 0 15px rgba(0, 255, 157, 0.3)',
        'glow-red': '0 0 15px rgba(255, 51, 51, 0.3)',
        'panel': '0 4px 20px rgba(0, 0, 0, 0.5)',
      },
      animation: {
        'pulse-fast': 'pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}