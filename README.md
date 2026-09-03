# CConstructionAI

**プロジェクト名:** CConstructionAI

## 目的
建設・セキュリティ施工業務向けの見積、材料原価、労務原価、実績工数、歩掛分析、標準歩掛改定、監査ログを統合管理する社内システム。

## 長期目標
- 実績施工データを蓄積
- 実績から標準歩掛を分析
- 人間の承認を経て標準歩掛を改定
- 材料費と労務費を組み合わせて見積作成
- Excel/PDF見積書出力
- 将来的にWeb UIを提供
- AIによる分析・提案
- 社内共同利用

## 技術
- Python
- FastAPI
- SQLModel
- SQLite（開発用）
- PostgreSQL（本番移行予定）
- openpyxl
- VS Code
- GitHub
- GitHub Copilot

## セットアップ
開発マシンでの最小手順例:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# FastAPI 開発サーバ起動（例）
# fastapi dev backend/main.py  <-- プロジェクトで使用している起動方法に合わせてください
```

Swagger:
http://127.0.0.1:8000/docs

OpenAPI確認:

```powershell
python -c "from backend.main import app; app.openapi(); print('OPENAPI OK')"
```

SQLite開発DB:
`data/estimator.db`

注意:
SQLiteは開発用です。本番ではPostgreSQLへ移行予定です。データベースの機密情報や実データをGitにコミットしないでください。
