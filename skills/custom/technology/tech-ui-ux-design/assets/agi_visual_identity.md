# AGI Visual Identity System (The "SBI" Aesthetic)

## 1. Core Philosophy
The interface is not a screen; it is a **Portal to the Void**.
It represents the "Singularity" — where human intent meets infinite computational power.

## 2. Color Palette (CSS Variables)

```css
@theme {
  /* The Void (Backgrounds) */
  --color-agi-void: #050505;       /* Deepest Black */
  --color-agi-dark: #0A0A0A;       /* Surface Black */
  
  /* The Intelligence (Accents) */
  --color-agi-green: #00FF94;      /* Active AI / Growth */
  --color-agi-blue: #00A3FF;       /* Logic / Data */
  --color-agi-gold: #C6A87C;       /* Trust / Value */
  
  /* The Glass (Surfaces) */
  --color-glass-surface: rgba(255, 255, 255, 0.03);
  --color-glass-border: rgba(255, 255, 255, 0.08);
}
```

## 3. Typography
*   **Headings:** `Inter` (Tight tracking, bold weights). "Machine Precision".
*   **Data/Code:** `JetBrains Mono`. "Engineer Native".

## 4. Effects
*   **Glow:** Text and borders should emit a faint glow to simulate CRT or energy fields.
    ```css
    .text-glow { text-shadow: 0 0 20px rgba(0, 255, 148, 0.5); }
    ```
*   **Noise:** A subtle grain overlay to reduce "digital sterility" and add texture.
*   **Scanlines:** Optional micro-interaction for loading states.

## 5. Motion Principles
*   **Always Alive:** Elements should never be static. Use `animate-pulse-slow` or `animate-float`.
*   **Physics-Based:** Transitions should use spring physics (Framer Motion), not linear curves.
