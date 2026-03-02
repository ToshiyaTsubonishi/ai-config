# SBI Group Skill Ecosystem Lifecycle Policy

## 1. Mission
To autonomously evolve the Gemini Agent's capabilities to drive SBI Group's "Financial Innovator" and "New Industry Creator" visions, ensuring strictly governed, high-performance operations.

## 2. Governance Standards (SQAG)
All skills must adhere to the following standards managed by `GEMINI-Skill-Quality-Governance`:

- **Naming Convention**: `CATEGORY-SubCategory-Focus` (e.g., `FIN-Crypto-Trading`).
- **Safety & Ethics**: No generation of illegal financial advice or PII mishandling.
- **Architecture**: Complex tasks must use **ReAct** or **Plan-and-Execute** patterns defined in ASEF.
- **Data Integrity**: Assets must use standardized CSV/JSON formats for interoperability.

## 3. KPI & Evaluation Metrics
The `GEMINI-Skill-Enhancement-Framework` will measure:

### Quantitative Metrics
1.  **Utilization Rate**: Frequency of skill activation per business request.
2.  **Success Rate**: % of tasks completed without user intervention/error.
3.  **Token Efficiency**: Output tokens per successful task (Goal: Minimize).
4.  **Coverage**: % of SBI business domains (Bank, Sec, Ins, Bio, Web3) covered by skills.

### Qualitative Metrics (Business Contribution)
1.  **Synergy Score**: How often the skill triggers/references other group skills.
2.  **Innovation Index**: Integration of new tech keywords (e.g., "DeFi", "GenAI").

## 4. Lifecycle Management
1.  **Incubation**: Created via `gemini-skill-creator`. Status: `Alpha`.
2.  **Active**: Passed SQAG audit. Status: `Stable`.
3.  **Refactoring**: Triggered by low KPI or new ASEF patterns. Status: `Updating`.
4.  **Deprecation**: Replaced by newer models or obsolete business logic. Status: `Archived`.

## 5. Continuous Improvement Cycle
- **Daily**: Automated Integrity Check (SQAG).
- **Weekly**: Performance Analysis & Gap Analysis (ASEF).
- **Monthly**: Strategic Skill Expansion (Creator).
