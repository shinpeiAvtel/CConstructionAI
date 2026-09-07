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

Mobile Query / WEB Fallback Evidence Enforcement:

When receiving short-format questions such as:
- Repo: CURRENT
- Q: ...

Do not answer directly from general knowledge. Always execute this workflow:

CURRENT Repository Context
-> Repository Search
-> Repository Evidence Evaluation
-> Insufficient?
	- YES: Official WEB Research
	- NO: Repository-based Answer
-> Evidence Comparison
-> Answer
-> Verification Status

Repository Search is mandatory before any technical conclusion. Search at least:
- README.md
- .github/copilot-instructions.md
- AGENTS.md
- repository context
- manufacturers/
- knowledge/
- field-cases/
- source-index/
- docs/

For LenelS2 OnGuard / Mercury / LNL / OSDP topics, prioritize repository evidence with those keywords first.

The answer must include this section and fields:

## Repository Search
Repository:
Search Result: FOUND / PARTIAL / NOT FOUND
Files Reviewed:
- actual/path/file1.md
- actual/path/file2.md
Relevant Evidence:
- ...
Missing Information:
- ...

Never fabricate file paths. If a file was not actually reviewed, do not list it.

Repository evidence decision rule:
- FOUND -> WEB Research: NOT REQUIRED
- PARTIAL -> WEB Research: REQUIRED
- NOT FOUND -> WEB Research: REQUIRED

If WEB Research is REQUIRED and web search capability is available, perform actual research.
If web search capability is unavailable, explicitly state:
- WEB Research: NOT AVAILABLE IN CURRENT ENVIRONMENT

Official source priority for WEB fallback:
1. LenelS2 official
2. Mercury Security official
3. HID or reader manufacturer official
4. Official installation guide
5. Official hardware guide
6. Official release notes
7. Official knowledge base
8. Authorized technical documentation
9. Reliable secondary engineering source

Do not present unverified technical claims as facts. For unsupported claims, use:
- NOT VERIFIED
or
- General troubleshooting hypothesis only

Ranking statements like "most common in the field" are prohibited unless evidence is provided.

When external sources are used, include all fields; unknown values must be NOT CONFIRMED:
- Source
- Publisher
- Document
- Version / Revision
- Publication Date
- Last Updated
- URL
- Access Date

Always separate evidence classes:
- ## Repository Evidence
- ## External WEB Evidence
- ## Engineering Hypothesis

Required final verification label:
- Verification Status: VERIFIED / PARTIALLY VERIFIED / NOT VERIFIED

Use this fixed answer order even for short-format mobile queries:

# Conclusion
# Reason
# Key Technical Data
# Repository Search
# Repository Evidence
# External WEB Evidence
# Engineering Hypothesis
# Recommended Troubleshooting Order
# Sources
# Verification Status
# Knowledge Update Recommendation

Conclusion must come before Reason, and Reason before Key Technical Data.
