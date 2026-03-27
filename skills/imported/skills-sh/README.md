# imported skills (skills.sh)

`skills/imported/skills-sh` は `skills.sh` 由来の imported payload を保持します。

## Layout

- `sources/<source-key>/<skill-id>/...`
- `source-key` は exact `creator__repo`
- 各 imported skill directory には `.skills-sh-meta.json` を置く

## Legacy snapshots

過去の popularity snapshot はそのまま残します。

- `manifest.top20.json`
- `summary.top20.json`
- `import-state.top20.json`
- `manifest.top500.json`
- `summary.top500.json`
- `import-state.top500.json`

これらは historical artifact であり、この directory 全体の current source of truth ではありません。

## Official coverage workflow

`skills.sh/official` の official repo coverage は frozen manifest `config/skills_sh_official.yaml` を正本にします。

- CLI: `ai-config-official-skills`
- status: official manifest に対する exact coverage を集計する
- sync: missing exact pair だけを `sources/<creator>__<repo>/...` に import する
- state file: `import-state.official.json`

coverage 判定は exact `creator/repo` match のみです。alias repo や別 owner の mirror は official coverage として数えません。
