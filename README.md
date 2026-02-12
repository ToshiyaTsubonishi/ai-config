# ai-config

MCP と Skills 設定を GitHub で一元管理するためのテンプレートです。

## 含まれるもの

- `mcp/codex.config.toml.tmpl`: Codex 用 MCP テンプレート
- `mcp/antigravity.mcp_config.json.tmpl`: Antigravity 用 MCP テンプレート
- `scripts/apply-mcp.ps1`: テンプレートを実ファイルへ反映
- `skills/`: 共通 Skill を置くディレクトリ（必要に応じてシンボリックリンク/Junction 運用）
- `.env.example`: 必要な環境変数のサンプル

## 使い方

1. `.env.example` を `.env` にコピーして値を設定
2. 以下を実行

```powershell
cd $HOME/ai-config
./scripts/apply-mcp.ps1
```

## 反映先

- Codex: `~/.codex/config.toml`
- Antigravity: `~/.gemini/antigravity/mcp_config.json`

## 補足

- 既存ファイルはデフォルトで `*.bak.<timestamp>` にバックアップされます。
- `.env` は `.gitignore` で除外済みです。
