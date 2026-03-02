# Tailwind CSS v4 Migration & Configuration Guide

## 1. The Core Shift: CSS-First
Tailwind v4 moves configuration from JavaScript (`tailwind.config.ts`) to CSS (`@theme`).
When initializing a new Next.js project that includes Tailwind v4, **YOU MUST DELETE** the legacy configuration files to avoid conflicts.

### ❌ Legacy (Do Not Use with v4)
- `tailwind.config.ts` (Delete this file)
- `tailwind.config.js` (Delete this file)
- `@apply` with arbitrary utility classes if not properly defined.

### ✅ Modern (v4 Standard)
- Define everything in `app/globals.css`.
- Use the `@theme` block for custom variables.

## 2. Implementation Steps

### Step 1: Clean Up
```bash
del tailwind.config.ts
```

### Step 2: Configure `app/globals.css`
Replace the entire content with:

```css
@import "tailwindcss";

@theme {
  /* Define your project's Design Tokens here */
  
  /* Colors */
  --color-brand-primary: #00FF94;
  --color-brand-dark: #050505;

  /* Fonts */
  --font-sans: var(--font-inter), sans-serif;
  
  /* Animations */
  --animate-float: float 6s ease-in-out infinite;

  @keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-20px); }
  }
}

/* Custom Utilities (If absolutely necessary) */
@layer utilities {
  .glass-panel {
    background-color: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(12px);
  }
}
```

## 3. Troubleshooting
*   **Styles not applying?** -> Check if `tailwind.config.ts` still exists. It overrides the CSS config.
*   **Unknown class error?** -> Ensure you are not using `@apply` with a class that relies on a plugin not yet imported.
