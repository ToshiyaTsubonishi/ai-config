---
name: tech-web3-engineering
description: "SBIグループのWeb3戦略（大阪・関西万博NFT、デジタルアセット等）を技術面で牽引し、セキュアでスケーラブルなdApp開発、スマートコントラクト実装、およびマルチチェーン統合を実現するエンジニアリングスキル。"
version: 2.0.0
author: SBI Orchestrator
---
# tech-web3-engineering (Web3 Forge)

## 1. Overview
Ethereum, Polygon, Avalanche, OASYS (SBIがバリデータ参加) を含むマルチチェーン環境において、高品質な分散型アプリケーション (dApp) を構築するためのエンジニアリングスキル。
単なるコード生成にとどまらず、**「SBIの金融クオリティ」を担保した堅牢なアーキテクチャ設計**と、秘密鍵管理やセキュリティ監査の自動化プロセスを提供する。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| スマートコントラクト実装 | **DApp Scaffolder** | Foundry (Solidity/Rust) を用いた高速な開発・テスト環境を構築し、標準規格 (ERC-20, 721, 1155, 4337) に準拠したコントラクトを生成する。 |
| フロントエンド連携 | **Web3 Frontend Engineer** | Wagmi / Viem / Ethers.js を用いて、ウォレット接続やコントラクト対話を行うReact/Next.jsコンポーネントを実装する。 |
| クロスチェーン接続 | **Chain Integrator** | LayerZero や Chainlink CCIP を用いて、異なるブロックチェーン間でのメッセージングやトークンブリッジを設計する。 |

## 3. Workflow
1.  **Requirement Analysis**: ユーザーの実現したい機能（トークン発行、NFT販売、DAO投票等）を分析し、最適なチェーンと技術スタックを選定する。
    *   *Constraint*: 金融系プロジェクトの場合は、必ずプライバシーとKYC/AML要件を考慮すること。
2.  **Scaffold**: プロジェクトの雛形を作成する。
    *   Contract: `forge init` (Foundry) 推奨。
    *   Frontend: `create-next-app` + `wagmi`。
3.  **Development & Test**: 実装を行い、単体テスト（Unit Test）と統合テスト（Integration Test）を記述する。
    *   *Rule*: テストカバレッジは可能な限り100%を目指すこと。
4.  **Security Audit**: `web3-smart-contract-sec` スキルを呼び出し、静的解析（Slither, Aderyn）とファジングを実行する。**この工程をスキップしてはならない。**
5.  **Deployment**: テストネット（Sepolia, Amoy, Oasys Testnet）へのデプロイと検証を行う。

## 4. Production Standards (Strict)
*   **Security First**: ReentrancyGuardの使用、アクセス制御（Ownable/AccessControl）の徹底、および`unchecked`ブロックの慎重な使用。
*   **Gas Optimization**: ストレージ変数のパッキング、`calldata`の使用、カスタムエラーの活用など、ガス代削減のための最適化を行うこと。
*   **Documentation**: NatSpec形式ですべての関数とイベントにコメントを記述すること。
*   **Tooling**: 基本的に **Foundry** を優先するが、プロジェクトの指定があれば Hardhat も許容する。
