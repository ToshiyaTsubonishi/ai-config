# Rename Evaluation

## Decision

2026-03-26 時点の結論:

- **`ai-config` は今は rename しない**
- 将来 rename を再検討する場合でも、**先に repo / display name だけを変える**
- `ai_config` package 名、`ai-config-*` CLI 名、`AI_CONFIG_*` env 名、`ai-config.*` contract kind は現フェーズでは変えない

理由は単純です。  
Phase 1-3 でようやく `dispatch` 分離、GCP production-safe resolution、cross-repo compatibility automation が安定したばかりで、現時点の rename は architecture value より compatibility cost の方が大きいです。

## Preconditions

この評価は次が揃った前提で行っています。

- `ai-config-dispatch` への runtime cutover が完了
- GCP / Cloud Run production-safe command resolution が完了
- 両 repo の cross-repo compatibility automation が入った

## Naming Surface Inventory

2026-03-26 時点の概算露出量:

| Surface | Count | Notes |
|---|---:|---|
| `ai-config` 文字列 | 481 | docs, scripts, workflows, URLs, package metadata |
| `ai_config` 文字列 | 294 | import path, package path, module execution |
| `ai-config-*` CLI 名 | 166 | `pyproject.toml`, setup scripts, docs, tests |
| `AI_CONFIG_*` env 名 | 97 | runtime resolution, agent adapters, docs, tests |
| `ai-config-dispatch` / `ai_config_dispatch` | 201 | external runtime repo, CI, docs |

特に rename cost を押し上げる箇所:

1. `pyproject.toml` の package 名と console scripts
2. `src/ai_config/**` import path
3. stable contract identity
   - `ai-config.approved-plan`
   - `ai-config.approved-plan-execution-request`
   - `ai-config.approved-plan-execution-result`
4. `AI_CONFIG_*` env 契約
5. sibling checkout 前提
   - `../ai-config`
   - `../ai-config-dispatch`
6. cross-repo GitHub Actions
7. README / operations docs / setup scripts / doctor

補足:

- release tag はまだ無く、両 repo とも実運用上は `main` 基準が強い
- `ai-config-dispatch` は現在 `ai-config` package に shared contracts / executor / runtime env helper を依存している

## Option Matrix

| Option | Scope | Pros | Cons | Decision |
|---|---|---|---|---|
| A. No rename | 変更なし | compatibility risk 最小、Phase 1-3 の安定を維持 | 名前の一般性は残る | **採用** |
| B. Repo / display rename only | GitHub repo 名、docs 表現、clone 例 | architecture messaging を改善しやすい | CI URL、sibling path、docs、scripts の追従が必要 | 将来の第一候補 |
| C. Repo + CLI rename | B + `ai-config-*` CLI alias 再設計 | UX 上の一貫性が出る | setup / docs / users / wrapper script への影響が大きい | 今は不採用 |
| D. Full rename | B + C + package/import/env/contract kind | 名前と実態を完全一致させられる | protocol, package, env, cross-repo boundary の breaking change が大きすぎる | 不採用 |

## Candidate Directions

rename を再開するなら、候補は 2 系統です。

### Candidate 1: `ai-capability-platform`

向いている理由:

- selector / planner / registry / serving の control-plane 性を説明しやすい
- `dispatch runtime` を中核から外した今の architecture と整合する
- capability broker という将来像も包含しやすい

### Candidate 2: `ai-capability-broker`

向いている理由:

- 各 agent が共通利用する capability broker という将来像に近い

弱い点:

- 現在の repo は broker だけでなく vendor provenance / index build / serving も担う
- 現時点では platform の方がスコープを誤解しにくい

現時点の優先順位:

1. `ai-capability-platform`
2. `ai-capability-broker`

## Recommendation

### 1. 今は rename しない

現時点では `ai-config` の説明は docs 上でかなり改善されており、architecture misunderstanding の主因は repo 名より責務の曖昧さでした。  
その責務整理は Phase 1-3 で解消済みです。

rename を今やらない理由:

- `ai-config.*` contract identity を動かしたくない
- `ai_config` import path は external dispatch repo の shared dependency 面でも効いている
- `AI_CONFIG_*` env 名は runtime / test / CI に広く浸透している
- GitHub Actions が 2 repo checkout を前提にし始めた直後で、name churn を入れるとノイズが大きい
- release tag がまだ無く、rename の compatibility window を設計しづらい

### 2. rename をやるなら repo / display rename から始める

順序の推奨:

1. GitHub repo 名と docs headline だけを変更
2. Python package / CLI / env / contract kind は維持
3. 互換 automation と install docs が安定したあとで alias 追加の要否を判断

この順序なら:

- architecture messaging は改善できる
- Python import / CLI / env / contract の breaking change を避けられる
- `ai-config-dispatch` 側 dependency もすぐには壊れない

### 3. contract kind は rebrand しない

`ai-config.approved-plan*` 系の contract kind は protocol identity です。  
repo rename をしたとしても、protocol name まで同時に rebrand しない方が安全です。

どうしても変えるなら:

- major protocol revision
- dual-accept window
- result / request / plan 全 contract の並行互換

が必要です。Phase 4 の範囲ではありません。

## Recommended Future Plan

rename を再開する条件:

1. `ai-config-dispatch` 依存が今より安定し、shared dependency 面が整理されている
2. release tag / stable channel ができている
3. in-repo compatibility shim をさらに薄くするか削除している
4. external docs / install path / CI path が固まっている

その時点での推奨プラン:

### Step 1

repo / display rename proposal を別 memo にする  
候補は `ai-capability-platform`

### Step 2

GitHub repo rename を実施する  
更新対象:

- clone URL
- CI checkout URL
- sibling path docs
- cross-repo scripts

### Step 3

package / CLI / env は当面維持する  
必要なら docs 上で:

- product name
- repo name
- Python package name
- CLI family

を明示的に分ける

### Step 4

package / CLI alias を追加するかどうかを別判断にする  
full rename は major release planning と同時でなければやらない

## Impact Summary By Surface

### Repo name only

変更対象:

- GitHub URLs
- CI clone commands
- local sibling path docs / scripts
- README / operations examples

互換性:

- GitHub redirect が効く範囲では比較的安全
- local sibling path の既定値は調整が必要

### CLI rename

変更対象:

- `pyproject.toml`
- setup wrappers
- docs command examples
- user muscle memory

互換性:

- alias 期間が必要
- Windows wrapper も含めて 2 系統管理が必要

### Package/import rename

変更対象:

- `src/ai_config/**`
- tests
- external dispatch dependency
- `python -m ai_config...` invocation

互換性:

- もっとも高コスト
- import alias package を長期間維持する前提でないと危険

### Env rename

変更対象:

- `AI_CONFIG_*` 全般
- runtime mode / command override / adapter settings
- docs / CI / local shell profiles

互換性:

- dual-read window が必要
- operational mistakes を誘発しやすい

## Final Position

Phase 4 の結論は **rename deferred** です。  
いま進めるべきなのは rename 実装ではなく、必要なら将来の **repo / display rename only** proposal を別トラックで起こすことです。
