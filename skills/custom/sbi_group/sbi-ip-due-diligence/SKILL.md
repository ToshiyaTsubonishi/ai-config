---
name: sbi-ip-due-diligence
description: 投資対象企業やM&Aターゲットの知的財産（特許、商標、著作権）を精査し、リスクと価値を評価するIPデューデリジェンス・スキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-ip-due-diligence (IP Auditor)

## 1. Overview
技術系スタートアップの価値の源泉である「知財」を丸裸にするスキルです。
「その特許は本当に事業を守れるか？」「他社の特許を侵害していないか？（FTO調査）」を厳しくチェックし、投資判断を支援します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| OSSライセンス監査 | **OSS Compliance Scanner** | コードに含まれるOSSライセンスを特定し、法的リスク（GPL汚染等）を検出。 |
| 大学知財・権利関係調査 | **University IP Auditor** | 大学発ベンチャー特有の「職務発明」や「共同研究契約」の不備を調査。 |

## 3. Workflow
1. **Access**: VDR（仮想データルーム）やGitHubリポジトリへのアクセス権を取得。
2.  **Scan**: `OSS Compliance Scanner` がソースコードを全件スキャン。
3.  **Audit**: `University IP Auditor` が、特許の名義人や発明者の帰属を確認。
4.  **Report**: 発見されたリスク（レッドフラグ）と対策案をレポート化。

## 4. Operational Principles
*   **Freedom to Operate (FTO)**: 「他社の特許を踏まずに事業ができるか」を最重要視する。
*   **Asset Value**: 特許の数だけでなく、その「質（請求項の広さ）」を評価する。
