# Data Dictionary

## Purpose

このデータ定義は `/home/runner/work/CConstructionAI/CConstructionAI/resource-management/` 配下で作成する Excel ベースのリソース統合管理システム用です。ここに記載した列のみを実装対象とし、社員ID・案件ID連携、Power Query 統合、稼働率計算、進捗表示、過負荷判定、空き工数表示を成立させます。

## Workbook Scope

### General_Resource_Management.xlsx
- `Employee_Master`
- `Project_Master`
- `Project_Schedule`
- `Resource_Input`
- `Progress_Input`
- `General_Resource`
- `Dashboard`

### Employee_Template.xlsx / Sample_Data.xlsx
- `Instructions`
- `Personal_Schedule`
- `Progress_Update`

## Common Keys

| Key | Type | Required | Description |
| --- | --- | --- | --- |
| employee_id | Text | Yes | 社員一意キー。社員予定表と統合管理表を連携する主キー。 |
| project_id | Text | Yes | 案件一意キー。案件マスタ、予定、進捗を連携する主キー。 |
| work_date | Date | Yes | 稼働対象日。日別リソース集計単位。 |

## Sheet Definitions

### 1. Employee_Master

| Column | Type | Required | Example | Description |
| --- | --- | --- | --- | --- |
| employee_id | Text | Yes | EMP-001 | 社員ID |
| employee_name | Text | Yes | 山田 太郎 | 社員名 |
| department | Text | Yes | Construction | 部門 |
| role_name | Text | Yes | Site Lead | 役割 |
| daily_capacity_hours | Number | Yes | 8 | 1日標準稼働時間 |
| skill_group | Text | No | Security | スキル分類 |
| active_flag | Text | Yes | Y | 利用対象社員フラグ |

### 2. Project_Master

| Column | Type | Required | Example | Description |
| --- | --- | --- | --- | --- |
| project_id | Text | Yes | PRJ-001 | 案件ID |
| project_name | Text | Yes | 本社入退室工事 | 案件名 |
| customer_name | Text | No | Alpha Co. | 顧客名 |
| project_manager_id | Text | Yes | EMP-001 | 案件責任者社員ID |
| start_date | Date | Yes | 2026-09-01 | 開始日 |
| end_date | Date | Yes | 2026-09-30 | 終了日 |
| status | Text | Yes | DRAFT | 案件状態 |
| priority | Text | No | High | 優先度 |
| planned_total_hours | Number | No | 120 | 総予定工数 |

### 3. Project_Schedule

| Column | Type | Required | Example | Description |
| --- | --- | --- | --- | --- |
| schedule_id | Text | Yes | SCH-001 | 予定行ID |
| project_id | Text | Yes | PRJ-001 | 案件ID |
| task_name | Text | Yes | 機器取付 | 工程名 |
| responsible_employee_id | Text | Yes | EMP-002 | 担当社員ID |
| schedule_date | Date | Yes | 2026-09-10 | 工程日 |
| planned_hours | Number | Yes | 6 | 予定工数 |
| schedule_status | Text | Yes | Planned | 工程状態 |
| progress_percent | Number | No | 35 | 工程進捗率 |

### 4. Resource_Input

Power Query `MergeSchedules.pq` のロード先です。

| Column | Type | Required | Example | Description |
| --- | --- | --- | --- | --- |
| entry_id | Text | Yes | EMP-001-2026-09-10-01 | 予定行ID |
| employee_id | Text | Yes | EMP-001 | 社員ID |
| work_date | Date | Yes | 2026-09-10 | 作業日 |
| project_id | Text | Yes | PRJ-001 | 案件ID |
| task_name | Text | Yes | 現地調査 | 作業名 |
| planned_hours | Number | Yes | 4 | 予定工数 |
| availability_status | Text | Yes | Assigned | 稼働区分 |
| remarks | Text | No | 午前対応 | 備考 |
| source_file | Text | Yes | EMP-001.xlsx | 取込元ファイル |
| last_refresh_at | DateTime | Yes | 2026-09-09 09:00 | 最終更新日時 |

### 5. Progress_Input

Power Query `MergeProgress.pq` のロード先です。

| Column | Type | Required | Example | Description |
| --- | --- | --- | --- | --- |
| progress_entry_id | Text | Yes | PRG-001 | 進捗行ID |
| employee_id | Text | Yes | EMP-001 | 更新者社員ID |
| project_id | Text | Yes | PRJ-001 | 案件ID |
| progress_date | Date | Yes | 2026-09-10 | 更新日 |
| progress_percent | Number | Yes | 40 | 案件進捗率 |
| actual_hours | Number | No | 3.5 | 実績工数 |
| progress_status | Text | Yes | In Progress | 進捗状態 |
| issue_flag | Text | No | N | 課題有無 |
| update_comment | Text | No | 配線完了 | コメント |
| source_file | Text | Yes | EMP-001.xlsx | 取込元ファイル |
| last_refresh_at | DateTime | Yes | 2026-09-09 09:00 | 最終更新日時 |

### 6. General_Resource

統合監視用の表示シートです。原本入力は行わず、Power Query 読込済み `Resource_Input` と `Progress_Input`、およびマスタを参照します。

| Column | Type | Required | Formula / Source | Description |
| --- | --- | --- | --- | --- |
| resource_row_id | Text | Yes | `=Resource_Input[@entry_id]` | 統合表示行ID |
| employee_id | Text | Yes | `=Resource_Input[@employee_id]` | 社員ID |
| employee_name | Text | Yes | `XLOOKUP(employee_id, Employee_Master[employee_id], Employee_Master[employee_name], "")` | 社員名 |
| department | Text | Yes | `XLOOKUP(employee_id, Employee_Master[employee_id], Employee_Master[department], "")` | 部門 |
| work_date | Date | Yes | `=Resource_Input[@work_date]` | 作業日 |
| project_id | Text | Yes | `=Resource_Input[@project_id]` | 案件ID |
| project_name | Text | Yes | `XLOOKUP(project_id, Project_Master[project_id], Project_Master[project_name], "")` | 案件名 |
| task_name | Text | Yes | `=Resource_Input[@task_name]` | 作業名 |
| planned_hours | Number | Yes | `=Resource_Input[@planned_hours]` | 当該行予定工数 |
| daily_capacity_hours | Number | Yes | `XLOOKUP(employee_id, Employee_Master[employee_id], Employee_Master[daily_capacity_hours], 0)` | 標準稼働時間 |
| total_daily_hours | Number | Yes | `SUMIFS(Resource_Input[planned_hours], Resource_Input[employee_id], employee_id, Resource_Input[work_date], work_date)` | 日別総予定工数 |
| utilization_rate | Percent | Yes | `IFERROR(total_daily_hours / daily_capacity_hours, 0)` | 稼働率 |
| overload_flag | Text | Yes | `IF(total_daily_hours > daily_capacity_hours, "OVER", "OK")` | 過負荷判定 |
| available_hours | Number | Yes | `MAX(daily_capacity_hours - total_daily_hours, 0)` | 空き工数 |
| progress_percent | Number | No | `MAXIFS(Progress_Input[progress_percent], Progress_Input[project_id], project_id)` | 案件進捗率 |
| progress_status | Text | No | `XLOOKUP(project_id, Progress_Input[project_id], Progress_Input[progress_status], "Not Started", 0, -1)` | 最新進捗状態 |
| issue_flag | Text | No | `XLOOKUP(project_id, Progress_Input[project_id], Progress_Input[issue_flag], "", 0, -1)` | 課題有無 |

### 7. Dashboard

ダッシュボードはサマリー専用です。

| Metric | Type | Formula / Source | Description |
| --- | --- | --- | --- |
| total_employees | Number | `COUNTA(Employee_Master[employee_id])` | 登録社員数 |
| active_projects | Number | `COUNTIF(Project_Master[status], "<>Closed")` | 稼働案件数 |
| today_assigned_hours | Number | `SUMIFS(Resource_Input[planned_hours], Resource_Input[work_date], Dashboard!B2)` | 基準日の総予定工数 |
| today_average_utilization | Percent | `AVERAGEIFS(General_Resource[utilization_rate], General_Resource[work_date], Dashboard!B2)` | 平均稼働率 |
| overloaded_rows | Number | `COUNTIF(General_Resource[overload_flag], "OVER")` | 過負荷件数 |
| available_hours_total | Number | `SUMIFS(General_Resource[available_hours], General_Resource[work_date], Dashboard!B2)` | 空き工数合計 |
| delayed_projects | Number | `COUNTIF(Progress_Input[issue_flag], "Y")` | 課題案件数 |

## Template Table Definitions

### Personal_Schedule (`tblPersonalSchedule`)

| Column | Type | Required | Description |
| --- | --- | --- | --- |
| entry_id | Text | Yes | 予定行ID |
| employee_id | Text | Yes | 社員ID |
| work_date | Date | Yes | 作業日 |
| project_id | Text | Yes | 案件ID |
| task_name | Text | Yes | 作業名 |
| planned_hours | Number | Yes | 予定工数 |
| availability_status | Text | Yes | `Assigned` / `Leave` / `Training` / `Available` |
| remarks | Text | No | 備考 |

### Progress_Update (`tblProgressUpdate`)

| Column | Type | Required | Description |
| --- | --- | --- | --- |
| progress_entry_id | Text | Yes | 進捗行ID |
| employee_id | Text | Yes | 更新者社員ID |
| project_id | Text | Yes | 案件ID |
| progress_date | Date | Yes | 更新日 |
| progress_percent | Number | Yes | 進捗率 |
| actual_hours | Number | No | 実績工数 |
| progress_status | Text | Yes | `Not Started` / `In Progress` / `Delayed` / `Done` |
| issue_flag | Text | No | `Y` / `N` |
| update_comment | Text | No | コメント |

## Validation Rules

| Target | Rule |
| --- | --- |
| employee_id | 空欄不可、社員マスタと一致させる |
| project_id | 空欄不可、案件マスタと一致させる |
| planned_hours | 0 以上 24 以下 |
| actual_hours | 0 以上 24 以下 |
| progress_percent | 0 以上 100 以下 |
| daily_capacity_hours | 0 より大きい |
| status values | ドキュメント記載の候補値のみ |

## Refresh Flow

1. 各社員は `Employee_Template.xlsx` をコピーして個人予定表を入力する。
2. Power Query `MergeSchedules.pq` が各社員ファイルの `tblPersonalSchedule` を結合する。
3. Power Query `MergeProgress.pq` が各社員ファイルの `tblProgressUpdate` を結合する。
4. `Resource_Input` と `Progress_Input` を更新後、`General_Resource` と `Dashboard` の式・書式が反映される。
