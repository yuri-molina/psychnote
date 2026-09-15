/** @type {import('tailwindcss').Config} */
export default {
  prefix: 'psy-',
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{ts,tsx,js,jsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        '2xl': '1400px',
      },
    },
    extend: {
      colors: {
        border: 'hsl(var(--psy-border))',
        input: 'hsl(var(--psy-input))',
        ring: 'hsl(var(--psy-ring))',
        background: 'hsl(var(--psy-background))',
        foreground: 'hsl(var(--psy-foreground))',
        primary: {
          DEFAULT: 'hsl(var(--psy-primary))',
          foreground: 'hsl(var(--psy-primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--psy-secondary))',
          foreground: 'hsl(var(--psy-secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--psy-destructive))',
          foreground: 'hsl(var(--psy-destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--psy-muted))',
          foreground: 'hsl(var(--psy-muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--psy-accent))',
          foreground: 'hsl(var(--psy-accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--psy-popover))',
          foreground: 'hsl(var(--psy-popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--psy-card))',
          foreground: 'hsl(var(--psy-card-foreground))',
        },
      },
      borderRadius: {
        lg: 'var(--psy-radius)',
        md: 'calc(var(--psy-radius) - 2px)',
        sm: 'calc(var(--psy-radius) - 4px)',
      },
    },
  },
  plugins: [],
};
