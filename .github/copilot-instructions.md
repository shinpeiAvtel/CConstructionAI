Project: CConstructionAI

Purpose:
Construction estimating, cost management, actual work data collection,
labor productivity analysis, standard revision, audit logging.

Core rules:

1. Do not duplicate FastAPI routes.
2. Do not directly overwrite approved labor standards.
3. Labor standard changes require revision candidate and human approval.
4. Maintain audit logs.
5. Estimate items are immutable snapshots of master values at creation/update.
6. Only DRAFT estimates may be edited.
7. APPROVED and ISSUED estimates are locked.
8. Preserve calculation consistency.
9. Run OpenAPI validation after API changes.
10. Do not expose secrets, customer data, database files, or real cost data.
11. SQLite is development-only.
12. PostgreSQL and Alembic are planned for production.

Before modifying code:
- inspect existing models and routes
- reuse existing patterns
- avoid creating duplicate functions
- explain potentially destructive schema changes before applying them
