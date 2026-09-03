# ARCHITECTURE

現在のアーキテクチャ

- FastAPI API layer（現状: `backend/main.py` に主要なエンドポイントが集中）
- SQLModel ORM
- SQLite（開発用）
- Models（マスター、実績、見積、監査ログなど）
- Master data（Material Master, Labor Master, Labor Cost Master）
- Actual work records（実績）
- Analysis（歩掛分析、外れ値検出）
- Standard revision（改定候補の生成と承認フロー）
- Audit log（監査記録の保持）
- Estimate engine（見積計算）
- Excel export（openpyxl）

今後の改善予定

- PostgreSQL への本番移行
- Alembic によるマイグレーション管理
- Authentication／Authorization の追加
- Web フロントエンドの実装
- バックアップと運用設計
- API テストの整備
- CI/CD パイプライン

リファクタ方針（将来）:

現在は `backend/main.py` にAPIが集中しているため、以下のように分離する予定です。

backend/
  routers/
  services/
  models/
  schemas/
  repositories/

各責務を分割し、テスト性と保守性を向上させます。
