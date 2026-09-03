# API REFERENCE

以下は `backend/main.py` に実装されているFastAPIエンドポイントの一覧です。存在しないエンドポイントを推測で追加していません。

## Labor Master

| Method | Path | Purpose |
|---|---|---|
| POST | /labor-master | Create `LaborMaster` |
| GET  | /labor-master | List `LaborMaster` records |

## Company Settings

| Method | Path | Purpose |
|---|---|---|
| POST | /company-settings | Create `CompanySetting` |
| GET  | /company-settings | List `CompanySetting` records |

## Labor Cost Master

| Method | Path | Purpose |
|---|---|---|
| POST | /labor-cost-master | Create `LaborCostMaster` |
| GET  | /labor-cost-master | List `LaborCostMaster` records |

## Projects

| Method | Path | Purpose |
|---|---|---|
| POST | /projects | Create `Project` |
| GET  | /projects | List `Project` records |

## Actual Work

| Method | Path | Purpose |
|---|---|---|
| POST | /actual-work | Create `ActualWorkRecord` (validates project, labor, and company setting) |
| GET  | /actual-work | List `ActualWorkRecord` with filters (project_code, labor_code, date range, site_condition) |
| PUT  | /actual-work/{record_id} | Update an actual work record |
| DELETE | /actual-work/{record_id} | Delete an actual work record |

## Statistical Analysis / Labor Analysis

| Method | Path | Purpose |
|---|---|---|
| GET | /analysis/labor/{labor_code} | Analyze actual work for a labor code (outlier detection, weighted/median, sample quality) |

## Standard Revision Candidates

| Method | Path | Purpose |
|---|---|---|
| GET  | /standard-revision-candidates | List candidates (filterable by labor_code, status) |
| POST | /standard-revision-candidates/{labor_code} | Create a revision candidate for a labor code (eligibility checks) |
| POST | /standard-revision-candidates/{candidate_id}/approve | Approve a pending candidate (updates `LaborMaster`, creates audit log) |
| POST | /standard-revision-candidates/{candidate_id}/reject | Reject a pending candidate (creates audit log) |

## Audit Logs

| Method | Path | Purpose |
|---|---|---|
| GET | /audit-logs | List audit logs (filterable by labor_code, action, actor) |

## Labor Estimation Engine

| Method | Path | Purpose |
|---|---|---|
| POST | /estimate/labor | Calculate labor estimate using labor master and labor cost master |

## Material Master

| Method | Path | Purpose |
|---|---|---|
| POST | /material-master | Create `MaterialMaster` |
| GET  | /material-master | List `MaterialMaster` (filters: category, manufacturer, active) |

## Combined Estimate

| Method | Path | Purpose |
|---|---|---|
| POST | /estimate/combined | Calculate combined material+labor estimate for given codes and quantity |

## Estimates and Estimate Items

| Method | Path | Purpose |
|---|---|---|
| POST | /estimates | Create an `Estimate` (initially DRAFT) |
| GET  | /estimates | List estimates (filterable by status, project_code) |
| POST | /estimates/{estimate_id}/items | Create an `EstimateItem` (DRAFT only; snapshots master values) |
| GET  | /estimates/{estimate_id}/items | List items for an estimate |
| DELETE | /estimates/{estimate_id}/items/{item_id} | Delete an item (DRAFT only) |
| PUT | /estimates/{estimate_id}/items/{item_id} | Update an item (DRAFT only) |
| PUT | /estimates/{estimate_id}/status | Update estimate status (DRAFT→APPROVED→ISSUED allowed transitions) |

## Excel Export

| Method | Path | Purpose |
|---|---|---|
| GET | /estimates/{estimate_id}/export/excel | Export estimate to Excel (`.xlsx`) using `openpyxl` |

