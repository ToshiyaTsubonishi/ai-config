# AI Agent Design Patterns for Skills

## 1. ReAct (Reason + Act)
**Best for**: Complex, multi-step problem solving where the path isn't linear.
**Implementation**: Instruct the agent to "Think" (reason about the current state) before "Acting" (calling a tool).

## 2. Sequential Pipeline
**Best for**: Standard Operating Procedures (SOPs) like payroll or monthly closing.
**Implementation**: Define a strict ordered list of steps. "Do A, then B, then C."

## 3. Manager/Worker (Hierarchical)
**Best for**: Broad domains (e.g., "HR Management").
**Implementation**: The main skill acts as a router/manager, identifying the sub-domain (Recruitment vs. Labor) and calling specific sub-routines or reading specific references.

## 4. Reflection/Critique
**Best for**: Content generation or code writing.
**Implementation**: Explicitly instruct the agent to generate a draft, then critique it against a set of constraints, then revise.
