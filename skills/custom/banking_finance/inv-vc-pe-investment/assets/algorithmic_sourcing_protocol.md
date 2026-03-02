# Algorithmic Sourcing Protocol Specification

## 1. Overview
Traditional VC sourcing relies on pitch decks and warm intros. The "AGI Capital Engine" replaces this with a code-first, trustless protocol.

## 2. User Flow
1.  **Code Injection:** Founder uploads GitHub URL or Smart Contract Address.
2.  **Strategic-Auditor Analysis (0.4s):**
    *   **Technical Debt Check:** Cyclomatic complexity, test coverage.
    *   **Security Scan:** Slither/Mythril for smart contracts, SonarQube for Web2.
    *   **Market Fit:** Sentiment analysis of README vs. Twitter/Discord trends.
3.  **Trustless Funding:**
    *   Score > 95: Instant Term Sheet (Standardized SAFE/SAFT).
    *   Score > 80: Human Associate Alerted.
    *   Score < 80: Automated Feedback Report sent.

## 3. UI Implementation Guide
*   **Terminal Interface:** Use a CLI-like aesthetic (Monospace font, blinking cursor).
*   **Real-time Feedback:** Show the "scanning" process visually (lines of code scrolling, security checks passing).
*   **Drag & Drop:** Allow dropping repo zip files for stealth mode startups.

## 4. Key Metrics
*   **Time-to-Term-Sheet:** Target < 24 hours.
*   **Bias Reduction:** Zero visibility of founder gender/race during initial score.
