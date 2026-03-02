# Skill Design Standards (The Constitution)

## 1. Progressive Disclosure Principle
* **Level 1 (Root)**: Light-weight. Only routing logic. < 500 tokens.
* **Level 2 (Agents)**: Task-specific logic. Loaded on demand.
* **Level 3 (Resources)**: Heavy templates/docs. Loaded only when strictly needed.

## 2. Agent Independence
* Each agent must have a clear "Input" and "Output".
* Agents should not share global state explicitly; pass data via arguments.

## 3. Implementation over Intention
* Bad: "Help the user."
* Good: "If user asks X, execute script Y and return format Z."