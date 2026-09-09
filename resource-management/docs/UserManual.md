# User Manual

## 1. Files

- 管理者用: `/home/runner/work/CConstructionAI/CConstructionAI/resource-management/excel/General_Resource_Management.xlsx`
- 社員配布用: `/home/runner/work/CConstructionAI/CConstructionAI/resource-management/excel/Employee_Template.xlsx`
- 動作確認用: `/home/runner/work/CConstructionAI/CConstructionAI/resource-management/excel/Sample_Data.xlsx`
- Power Query: `/home/runner/work/CConstructionAI/CConstructionAI/resource-management/powerquery/`
- VBA: `/home/runner/work/CConstructionAI/CConstructionAI/resource-management/vba/RefreshAll.bas`

## 2. Employee Operation

1. `Employee_Template.xlsx` を社員ごとにコピーします。
2. `Personal_Schedule` シートへ `employee_id`、`work_date`、`project_id`、`planned_hours` を入力します。
3. `Progress_Update` シートへ `project_id`、`progress_percent`、`progress_status` を入力します。
4. ファイルを共有フォルダに保存します。

## 3. Administrator Setup

1. `General_Resource_Management.xlsx` を開きます。
2. `Employee_Master` に社員情報を登録します。
3. `Project_Master` に案件情報を登録します。
4. `Project_Schedule` に工程計画を登録します。
5. Excel の Power Query に `MergeSchedules.pq` と `MergeProgress.pq` を貼り付けます。
6. 各クエリの `FolderPath` を社員ファイル格納フォルダへ変更します。
7. `MergeSchedules` の読込先を `Resource_Input`、`MergeProgress` の読込先を `Progress_Input` に設定します。

## 4. Refresh All Button

1. `General_Resource_Management.xlsx` をマクロ有効形式 `.xlsm` で保存し直します。
2. `RefreshAll.bas` を VBA エディタへインポートします。
3. 任意の図形またはボタンに `Refresh_All_Resource_Management` を割り当てます。
4. ボタン押下で Power Query と計算を一括更新します。

## 5. Sheet Usage

### Employee_Master
- `employee_id` を重複させない
- `daily_capacity_hours` は通常 8 時間基準

### Project_Master
- `project_id` を重複させない
- `status` は `DRAFT`、`APPROVED`、`ISSUED`、`Closed` のいずれかを使用

### Resource_Input / Progress_Input
- 直接編集しない
- Power Query ロード結果のみ保持する

### General_Resource
- 稼働率、過負荷、空き工数、案件進捗を確認する
- `overload_flag = OVER` は調整対象

### Dashboard
- `B2` の基準日を変更して日次サマリーを切り替える
- グラフと KPI を管理会議資料に利用する

## 6. Validation Rules

- `planned_hours` は 0〜24
- `actual_hours` は 0〜24
- `progress_percent` は 0〜100
- `employee_id` と `project_id` はマスタに合わせる

## 7. Recommended Operating Flow

1. 社員が個人予定表を更新
2. 管理者が `Refresh All` 実行
3. `General_Resource` で過負荷と空き工数を確認
4. `Dashboard` で全体進捗を確認
5. 必要に応じて `Project_Schedule` と社員予定を調整

## 8. Notes

- `.xlsx` 形式は VBA を保持できないため、更新ボタンは `.xlsm` 化後に利用します。
- サンプルデータは説明用であり、実顧客データは含みません。
