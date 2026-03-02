# Meta-Prompting Guide: How to Write High-Quality Agent Skills
This guide is for the `gemini-skill-creator` agent. Use these principles when populating `SKILL.md` files.

## 1. The "Skill Architect" Mindset
Don't just fill in blanks. Design a cognitive architecture for the agent.
*   **Role:** Who is this agent?
*   **Goal:** What is the specific outcome?
*   **Context:** What does the agent need to know?

## 2. Structure of a Great `SKILL.md`

### 2.1 Overview
*   **What:** 1-2 sentences summarizing the capability.
*   **When:** Bullet points of specific triggers

### 2.2 Capability Instructions (The Core)
Use the **ReAct (Reasoning + Acting)** pattern.
*   **Wrong:** "Run the script."
*   **Right:**
    1.  **Analyze:** Read the user's input to understand X.
    2.  **Plan:** Decide which tool to use.
    3.  **Execute:** Run `scripts/analyze.py` with arguments...
    4.  **Verify:** Check if the output contains Y. If not, retry.

### 2.3 Tool/Script Usage
*   Define parameters precisely.
*   Provide a concrete usage example.

### 2.4 Few-Shot Examples (Crucial)
Provide "User Input" -> "Agent Action" pairs.
*   Show, don't just tell.
*   Include edge cases (e.g., "User provides invalid input").

## 3. Best Practices checklist
- [ ] **YAML Frontmatter:** MUST be valid YAML. No XML.
- [ ] **Specific Steps:** Numbered lists are better than paragraphs.
- [ ] **Self-Correction:** Instruct the agent to check its own work.
- [ ] **Safety:** Explicitly forbid dangerous actions (e.g., `rm -rf`).
- [ ] **Tone:** Professional, objective, and concise.
