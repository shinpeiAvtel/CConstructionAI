# COPILOT / AI 開発者向けルール

開発者向けの必須ルール:

- 既存の正常動作を壊さない
- FastAPI route の重複を作らない
- API追加後は OpenAPI チェックを実行する
- DB更新後は `commit` / `refresh` を適切に行う
- `EstimateItem` の snapshot を維持する
- `APPROVED` / `ISSUED` 見積は編集してはいけない
- 標準歩掛を AI が直接更新してはいけない
- 標準改定は人間承認が必須
- Audit Log を保持する
- 現段階では SQLite を開発 DB として使う
- 本番 DB 変更時は Alembic マイグレーションを使用する
- `create_all` のみで本番スキーマ変更を行わない
- 本番移行前に認証・認可を追加する
- テストデータと実データを区別する
- 顧客情報や原価情報を Git へ commit しない
