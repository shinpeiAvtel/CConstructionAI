# PROJECT OVERVIEW

このシステムの目的と全体像

本システムは、実績工数データを収集し、統計解析を通じて標準歩掛（標準的な作業時間）を提案・管理するための社内向け見積・原価管理システムです。主な流れは以下の通りです。

Actual Work
↓
Statistical Analysis
↓
Standard Revision Candidate
↓
Human Review
↓
APPROVE / REJECT
↓
Labor Master Update
↓
Audit Log

重要: AIは標準歩掛を直接書き換えてはいけません。AIは候補生成と分析支援に留め、最終的な改定は人間の承認が必要です。

見積フロー（簡略）:

Material Master
+
Labor Master
+
Labor Cost Master
↓
Estimate Item
↓
Estimate
↓
Approval
↓
Issue
↓
Excel / PDF quotation
