# BUSINESS RULES

## 標準歩掛（Definitions）

actual_person_days =
workers * work_minutes / minutes_per_person_day

actual_labor_per_unit =
actual_person_days / quantity


## 標準歩掛の改定
AIや実績データから直接 `LaborMaster` を書き換えてはいけません。必須フロー:

Actual Work
→ Analysis
→ Revision Candidate
→ Human Review
→ APPROVE / REJECT
→ Labor Master
→ Audit Log


## 見積計算ルール

material_cost =
material_unit_price * quantity

standard_labor_per_unit =
standard_minutes / minutes_per_person_day

labor_person_days =
standard_labor_per_unit
* quantity
* correction_factor

labor_cost =
labor_person_days
* labor_unit_price

direct_cost =
material_cost
+ labor_cost

overhead_amount =
direct_cost * overhead_rate / 100

subtotal =
direct_cost + overhead_amount

profit_amount =
subtotal * profit_rate / 100

estimate_total =
subtotal + profit_amount


## 見積ステータスとルール

ステータス遷移: DRAFT → APPROVED → ISSUED

ルール:
- `DRAFT` のみ編集可能
- `APPROVED` は明細編集禁止
- `ISSUED` は明細編集禁止
- `DRAFT` から直接 `ISSUED` へ遷移禁止
- `APPROVED` から `DRAFT` へ戻さない
- `ISSUED` から戻さない

EstimateItem は snapshot として扱う。マスターが後から変更されても、過去見積の単価・歩掛・原価が勝手に変わってはいけない。
