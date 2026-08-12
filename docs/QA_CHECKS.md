# QA Health Checks

Catalog of the self-auditing checks on the workbook's QA tab. The QA tab computes these live; after any change to the workbook, the summary must read all checks PASS. Snapshot below is from V3.0.0 as of 2026-08-12 (19 / 19 PASS).

| Check ID | Severity | Description | Expected |
| --- | --- | --- | --- |
| QA-001 | CRITICAL | Formula errors — Lease Comps | 0 |
| QA-003 | CRITICAL | Formula errors — Companies | 0 |
| QA-004 | CRITICAL | Formula errors — Funding Rounds | 0 |
| QA-005 | CRITICAL | Formula errors — Company Metrics | 0 |
| QA-006 | CRITICAL | Formula errors — Dashboard | 0 |
| QA-008 | CRITICAL | Formula errors — _Schema (machine contract) | 0 |
| QA-010 | CRITICAL | Duplicate comp IDs | 0 |
| QA-012 | CRITICAL | Duplicate company IDs | 0 |
| QA-013 | CRITICAL | Duplicate round IDs | 0 |
| QA-014 | CRITICAL | Next-ID collision — a Start Here next ID already exists in its table | 0 |
| QA-020 | CRITICAL | Comps with unknown company_id | 0 |
| QA-021 | CRITICAL | Rounds with unknown company_id | 0 |
| QA-022 | HIGH | Comps missing company_id | 0 |
| QA-031 | CRITICAL | Dashboard total comps vs source | 0 |
| QA-050 | HIGH | Rounds flagged REVIEW (verify then downgrade) | INFO |
| QA-051 | HIGH | Duplicate (company, type, date) rounds | 0 |
| QA-060 | MEDIUM | Extent: Lease Comps capacity used | <80% |
| QA-061 | MEDIUM | Extent: Funding Rounds capacity used | <80% |
| QA-070 | MEDIUM | Freshness: months since newest funding round | <13 |
| QA-071 | MEDIUM | Comps missing required inputs | 0 |
| QA-072 | MEDIUM | Comps with TI $/SF = 0 (confirmed zero = as-is deal, per JD 7/28/2026; unknown TI is never entered as 0 — the comp is skipped or noted instead) | INFO |

Severity semantics:

- **CRITICAL** — data integrity is broken (formula errors, duplicate or orphaned IDs, dashboard drift). Fix before anything else.
- **HIGH** — data quality debt that needs human verification (e.g. REVIEW-confidence rounds).
- **MEDIUM** — operational headroom and freshness signals.

`INFO` rows are informational counts, not pass/fail gates.
