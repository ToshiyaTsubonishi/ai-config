# Agent Design Patterns for Skills

Skills turn a generic LLM into a specialized agent. Use these patterns in your `SKILL.md` instructions.

## 1. ReAct (Reasoning + Acting)
Instead of just asking for an answer, instruct the agent to "Think" then "Act".

**Pattern:**
1.  **Thought:** Analyze the user's request. What is missing?
2.  **Action:** Call a tool (e.g., search, read_file).
3.  **Observation:** Read the tool output.
4.  **Repeat:** Until the answer is found.

## 2. Chain of Thought (CoT)
Encourage step-by-step logic, especially for complex tasks.

## 3. Plan-and-Solve
For multi-step goals, make a plan and then execute.