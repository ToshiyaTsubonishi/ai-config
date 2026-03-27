# imported skills (skills.sh)

`skills/imported/skills-sh` は `skills.sh` 由来の imported payload を保持します。

## Layout

- `sources/<source-key>/<skill-id>/...`
- `source-key` は exact `creator__repo`
- 一部の imported skill directory には `.skills-sh-meta.json` を置く

## Legacy snapshots

過去の popularity snapshot はそのまま残します。

- `manifest.top20.json`
- `summary.top20.json`
- `import-state.top20.json`
- `manifest.top500.json`
- `summary.top500.json`
- `import-state.top500.json`

これらは historical artifact であり、この directory 全体の current source of truth ではありません。

## Official snapshot artifacts

`skills.sh/official` 由来の source of truth は `skills/official` layer です。

- manifest: `config/skills_sh_official.yaml`
- refresh: `ai-config-vendor-skills --repo-root . refresh-skills-sh-official-manifest`
- sync: `ai-config-vendor-skills --repo-root . sync-skills-sh-official`
- target: `skills/official/<creator>__<repo>/...`
- historical imported artifacts が残っている場合、それらは legacy record として扱います。
