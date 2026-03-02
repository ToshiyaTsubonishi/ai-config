# Next.js AGI Project Structure Standard

## 1. Directory Tree
To ensure consistency across the SBI Ecosystem, all frontend projects must adhere to this Atomic-based structure:

```
src/ (or root if no-src)
├── app/
│   ├── layout.tsx        # Global Layout (Navbar, Footer, Context Providers)
│   ├── globals.css       # Tailwind v4 @import and @theme
│   └── (routes)/         # Page routes
├── components/
│   ├── ui/               # Atoms (Button, Input, Card) - Shadcn-like
│   ├── sections/         # Organisms (Hero, Features, Pricing)
│   └── layout/           # Global (Navbar, Footer, Sidebar)
├── lib/
│   ├── contexts/         # React Contexts (Language, Theme, Auth)
│   ├── utils.ts          # Helper functions (cn, formatters)
│   └── hooks/            # Custom Hooks
└── public/               # Static Assets
```

## 2. Component Guidelines
*   **Colocation:** Keep related assets (images specific to a component) near the component if possible, or strictly organized in `public`.
*   **Exports:** Use named exports (`export function Hero()`) instead of default exports for better tree-shaking and debugging.
*   ** "use client" Boundary:** Push the `"use client"` directive as far down the tree as possible (e.g., to the specific interactive button, not the whole page).
