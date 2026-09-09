# System Design

## Overview

本システムは Excel を入力フロント、Power Query を統合エンジン、VBA を更新操作に使う軽量構成です。社員は個別テンプレートのみ更新し、管理者は `General_Resource_Management.xlsx` で全体稼働・進捗・過負荷を確認します。

## Directory Structure

- `/home/runner/work/CConstructionAI/CConstructionAI/resource-management/excel/General_Resource_Management.xlsx`
- `/home/runner/work/CConstructionAI/CConstructionAI/resource-management/excel/Employee_Template.xlsx`
- `/home/runner/work/CConstructionAI/CConstructionAI/resource-management/excel/Sample_Data.xlsx`
- `/home/runner/work/CConstructionAI/CConstructionAI/resource-management/powerquery/MergeSchedules.pq`
- `/home/runner/work/CConstructionAI/CConstructionAI/resource-management/powerquery/MergeProgress.pq`
- `/home/runner/work/CConstructionAI/CConstructionAI/resource-management/vba/RefreshAll.bas`
- `/home/runner/work/CConstructionAI/CConstructionAI/resource-management/docs/DataDictionary.md`
- `/home/runner/work/CConstructionAI/CConstructionAI/resource-management/docs/UserManual.md`

## Functional Design

### 1. Employee Input Layer
- 各社員は `Employee_Template.xlsx` をコピーして利用する
- `Personal_Schedule` で予定工数を入力する
- `Progress_Update` で案件進捗と実績工数を入力する
- 連携キーは `employee_id` と `project_id`

### 2. Consolidation Layer
- `MergeSchedules.pq` は社員テンプレート群から `tblPersonalSchedule` を抽出する
- `MergeProgress.pq` は社員テンプレート群から `tblProgressUpdate` を抽出する
- Power Query のロード先は `General_Resource_Management.xlsx` の `Resource_Input` と `Progress_Input`
- 取込元ファイル名と更新時刻を保持する

### 3. Resource Monitoring Layer
- `General_Resource` は読込済みデータから稼働率、過負荷、空き工数を算出する
- `progress_percent` と `progress_status` は案件単位で表示する
- 条件付き書式で過負荷、空き、遅延を強調表示する

### 4. Dashboard Layer
- 基準日入力で当日サマリーを切り替える
- 指標: 社員数、稼働案件数、総予定工数、平均稼働率、過負荷件数、空き工数、課題案件数
- グラフ: 稼働率、案件進捗、部門別配分

## Workbook Design

### General_Resource_Management.xlsx
1. `Employee_Master`: 社員定義
2. `Project_Master`: 案件定義
3. `Project_Schedule`: 工程計画
4. `Resource_Input`: Power Query スケジュール統合結果
5. `Progress_Input`: Power Query 進捗統合結果
6. `General_Resource`: 稼働監視表示
7. `Dashboard`: 管理者サマリー

### Employee_Template.xlsx
- `Instructions`: 入力ルール説明
- `Personal_Schedule`: 予定入力テーブル
- `Progress_Update`: 進捗入力テーブル

### Sample_Data.xlsx
- テンプレートと同一列構造
- 動作確認用サンプルレコードを格納

## Calculation Rules

- 稼働率 = 日別総予定工数 ÷ 日別標準稼働時間
- 過負荷判定 = 日別総予定工数 > 日別標準稼働時間
- 空き工数 = MAX(日別標準稼働時間 - 日別総予定工数, 0)
- 案件進捗表示 = `Progress_Input` の最新進捗率と進捗状態を参照

## Refresh Design

- `RefreshAll.bas` は `ThisWorkbook.RefreshAll` を実行する
- 更新ボタンはマクロ有効ブックへモジュールをインポート後に割り当てる
- 要求ファイル名が `.xlsx` のため、VBA は別ファイルで提供する

## Non-Destructive Design Choices

- マスタシートは手入力、統合シートは Power Query ロード専用として役割分離
- `General_Resource` は計算表示のみで原本を上書きしない
- サンプルデータは本番データを含めない

## Operational Assumptions Implemented

- 1 行は 1 社員・1 日・1 案件・1 作業の予定を表す
- 進捗は案件単位で管理する
- 管理帳票は最新 Power Query 取込結果を基準に表示する
