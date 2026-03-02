# 出向費用按分・較差補填金 管理表定義 (Schema)

## 1. 目的
出向元・先間での給与負担額および較差補填金の計算を自動化し、税務上の合理性を担保する。

## 2. カラム定義 (Excel/CSV)
| カラムID | 項目名 | データ型 | 計算ロジック・備考 |
| :--- | :--- | :--- | :--- |
| `EMP_ID` | 社員番号 | String | SBIグループ統一ID |
| `NAME` | 氏名 | String | |
| `DEST_CO` | 出向先会社名 | String | |
| `RATIO` | 出向比率 | Float | 例: 0.5 (50%) |
| `BASE_SAL_ORG`| 出向元基本給 | Integer | |
| `BASE_SAL_DEST`| 出向先基本給 | Integer | |
| `DIFF_PAY` | **較差補填金** | Integer | `MAX(0, BASE_SAL_ORG - BASE_SAL_DEST)` |
| `BURDEN_DEST` | 出向先負担額 | Integer | `BASE_SAL_DEST * RATIO` |
| `TAX_TYPE` | 消費税区分 | Enum | `不課税` (原則) |
| `HIRE_DATE_GRP`| **グループ入社日**| Date | 勤続年数・退職金計算用 |

## 3. AIエージェントへの指示 (Prompt Snippet)
- 「給与較差が発生している場合、出向契約書（`assets/contract_clause_library.md`）の規定に基づき、補填額が妥当か検証せよ。」
- 「按分比率に変更があった場合、過去3ヶ月の平均残業時間から実態と乖離がないかアラートを出せ。」
