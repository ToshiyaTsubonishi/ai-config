# Next.js App Router Best Practices (AGI Native)

## 1. Server Components by Default
In the AGI era, we prioritize "Zero-Bundle-Size".
*   **Rule:** All components are Server Components (`.tsx`) unless they explicitly require interactivity.
*   **When to use "use client":**
    *   `useState`, `useEffect`, `useContext`
    *   Event listeners (`onClick`, `onChange`)
    *   Browser-only APIs (`window`, `localStorage`)

## 2. Layouts & Metadata
*   **Metadata:** Define `generateMetadata` in `page.tsx` or `layout.tsx` for dynamic SEO.
*   **Root Layout:** Must contain `<html>` and `<body>`.
*   **Fonts:** Use `next/font` (e.g., `Inter`, `JetBrains Mono`) to prevent Layout Shift (CLS).

## 3. Data Fetching
*   **No `useEffect` for data:** Do not fetch data in `useEffect` (Client).
*   **Async Components:** Fetch data directly in Server Components using `async/await`.
    ```tsx
    export default async function Dashboard() {
      const data = await getAGIScore(); // Direct DB/API call
      return <ScoreDisplay value={data} />;
    }
    ```

## 4. Architecture Pattern
*   `app/`: Routing layer (Pages, Layouts, API Routes).
*   `components/`: UI building blocks.
    *   `ui/`: Atomic components (Button, Input).
    *   `sections/`: Page sections (Hero, Features).
    *   `layout/`: Global structure (Navbar, Footer).
*   `lib/`: Logic layer.
    *   `utils.ts`: Helper functions (`cn`).
    *   `actions.ts`: Server Actions.
