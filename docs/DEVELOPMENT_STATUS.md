# DEVELOPMENT STATUS

進捗（概略）

Phase 1  Labor Master                 COMPLETE
Phase 2  Estimate Engine              COMPLETE
Phase 3  Project DB                   COMPLETE
Phase 4  Actual Work DB               COMPLETE
Phase 5  Statistical Analysis         COMPLETE
Phase 6  Standard Revision Workflow   COMPLETE
Phase 7  Audit Log                    COMPLETE
Phase 8  Material Master              COMPLETE
Phase 9  Combined Estimate            COMPLETE
Phase 10 Estimate Header              COMPLETE
Phase 11 Estimate Item Snapshot       COMPLETE
Phase 12 Estimate Item CRUD           COMPLETE
Phase 13 Duplicate Route Cleanup      COMPLETE
Phase 14 Estimate Status Workflow     COMPLETE
Phase 15 Excel Export                 IN PROGRESS


## 現在検証済みのテスト値（例）

Estimate:
EST-2026-0001

Material:
MAT-TEST-001
Unit Price: 45,000 JPY

Labor:
TEST-001
Standard Minutes: 30.72
Labor Unit Price: 35,000 JPY/person-day

Quantity:
25

Correction Factor:
1.2

計算例:
Material Cost:
1,125,000

Labor Person Days:
1.92

Labor Cost:
67,200

Direct Cost:
1,192,200

Overhead:
10%
119,220

Profit:
15%
196,713

Estimate Total:
1,508,133 JPY

Status workflow:
DRAFT → APPROVED → ISSUED

APPROVED estimate modification protection:
VERIFIED

OpenAPI:
OK

Duplicate FastAPI routes:
NONE

次の予定:
- Excel出力レイアウト改善
- 社内原価計算書と顧客提出用見積書の分離
- PDF出力
- 見積承認監査ログ
- Web UI
- PostgreSQL移行
