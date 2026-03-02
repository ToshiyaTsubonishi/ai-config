# 証明書発行 依頼Forms設計・マッピング定義

## 1. 依頼Forms (入力項目案)
申請者がFormsで入力すべき必須項目。

| 項目名 | 選択肢・形式 | 備考 |
| :--- | :--- | :--- |
| 証明書の種類 | 在籍、年収、就労(認可外保育園用)、その他 | 複数選択可 |
| 使用目的 | 住宅ローン、賃貸契約、ビザ申請、保育園、その他 | |
| 言語 | 日本語、英語、日本語・英語併記 | |
| 氏名 (漢字/ローマ字) | テキスト | 英語の場合はパスポート表記 |
| 住所 (和文/英文) | テキスト | |
| 提出先 | 銀行、大使館、市区町村、その他 | |
| 記載希望の有無 | 給与額、職務内容、期間、住所 | 項目により個別対応 |
| 受取方法 | PDF(メール)、郵送、手渡し | |

## 2. システムデータ・テンプレート マッピング表
人事システム（COMPANY）から抽出する項目とWordテンプレート上のブックマーク名の対応。

| 抽出項目 (COMPANY) | テンプレート項目 | 英語表記 (Reference用) |
| :--- | :--- | :--- |
| 氏名 | `FullName` | Full Name |
| 生年月日 | `DateOfBirth` | Date of Birth |
| 入社年月日 | `HireDate` | Date of Employment |
| 退職年月日 | `ResignationDate` | Date of Resignation |
| 役職 | `Position` | Position / Job Title |
| 会社名 | `CompanyName` | Company Name |
| 代表者名 | `CEO_Name` | Representative Name |
| 昨年度年収 | `AnnualIncome_LY` | Annual Compensation (Last Year) |
| 住所 | `Address` | Address |
