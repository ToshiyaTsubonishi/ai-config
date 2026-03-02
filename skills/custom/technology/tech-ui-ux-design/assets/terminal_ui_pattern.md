# Terminal Interface Pattern (Pitch-to-Machine)

## 1. Overview
A UI pattern for high-trust, high-speed interaction with AGI systems.
It mimics a CLI (Command Line Interface) to signal "Direct Access" and "No Bureaucracy".

## 2. Component Specifications

### Visuals
*   **Background:** `#000000` or `#050505` (Void).
*   **Font:** `JetBrains Mono` or `Fira Code`.
*   **Cursor:** Block cursor (`\u2588`) with blinking animation.
*   **Syntax Highlighting:** Minimal coloring (Green for success, Yellow for processing, Red for error).

### Interactions
1.  **Typing Effect:** All system output should appear character-by-character (speed: 20-50ms).
2.  **Input Field:** A disguised `<input>` or `<textarea>` that looks like a command prompt line.
3.  **Process Visualization:**
    *   Instead of a spinner, show scrolling logs:
        ```
        > ANALYZING_REPOSITORY...
        > CHECKING_CYCLOMATIC_COMPLEXITY... [OK]
        > VERIFYING_TOKENOMICS... [OK]
        ```

### 3. Usage Pattern (The "Sourcing" Flow)
*   **Step 1:** User drags & drops a file (Codebase).
*   **Step 2:** Terminal "scans" the file (Visual logs).
*   **Step 3:** Terminal outputs a "Score" and a "Term Sheet" (Artifact).
