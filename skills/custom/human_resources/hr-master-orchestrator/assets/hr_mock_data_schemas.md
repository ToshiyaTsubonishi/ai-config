# HRエージェント・テスト用 JSON Mock Schema (2026年標準)

## 1. 従業員基本情報 (Master Data)
```json
{
  "employee_id": "SBI-99999",
  "name_kanji": "模擬 太郎",
  "name_kana": "モギ タロウ",
  "email": "mogi.taro@example.com",
  "department": "DX推進部",
  "position": "シニアマネージャー",
  "hire_date": "2025-04-01",
  "work_location": "Tokyo HQ",
  "status": "Active"
}
```

## 2. 休暇・休職ステータス (Leave Management)
```json
{
  "case_id": "LV-2026-001",
  "employee_id": "SBI-99999",
  "leave_type": "Childcare",
  "start_date": "2026-05-10",
  "end_date": "2027-05-09",
  "approval_status": "Approved",
  "bpo_sync": "Completed"
}
```

## 3. 採用KPIデータ (Recruitment)
```json
{
  "fiscal_year": 2026,
  "candidates": 1200,
  "offer_issued": 150,
  "offer_accepted": 105,
  "acceptance_rate": 0.7,
  "avg_hiring_cost_jpy": 450000
}
```

## 4. 運用上の注意
- 本データは、AIエージェントのロジックテスト（計算、マッピング、バリデーション）のみに使用すること。
- テスト完了後は、速やかにメモリ上の情報をクリアするよう指示に含めること。
