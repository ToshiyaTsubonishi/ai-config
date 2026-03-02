# AI Agent Compliance & Ethics Guidelines

## 1. Safety & Privacy
- Skills must NOT instruct the agent to handle PII (Personally Identifiable Information) without explicit user consent and local handling instructions.
- Skills must NOT bypass system-level safety guardrails.

## 2. Transparency
- Skills should encourage the agent to disclose its nature as an AI when interacting in simulated external environments (if applicable).
- Skills generating critical outputs (legal/financial) must include a disclaimer to verify with a human expert.

## 3. Security
- No hardcoded API keys or credentials in `SKILL.md` or scripts. Use environment variables.
- Scripts must be validated for safe execution paths (no `rm -rf /` equivalents).
