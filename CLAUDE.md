# CLAUDE.md — Agent contract for the Norman Intelligence Hub

This repo is the code + contract home for the Norman AI Intelligence Hub (V3.0.0). The live data is the Google Sheets workbook:
https://docs.google.com/spreadsheets/d/1qZlc8BUZRObyoeygAToWicor-UFFLmO_aCjk3axBhdE/edit

## Read this first

- `schema/schema.json` — the machine-readable contract for every tab, column, and formula. It mirrors the workbook's `_Schema` tab, which is authoritative.
- `schema/reference.json` — controlled vocabularies and the tenant-variant → canonical-company map.

## The workbook contract (non-negotiable)

- **Unknown values stay BLANK, never 0.** A `0` corrupts averages; blank propagates correctly. Exception: a confirmed-zero TI on an as-is deal is a real zero (per JD, 7/28/2026).
- **IDs are immutable and never reused.** Formats: `LC-####` (Lease Comps), `CO-####` (Companies), `FR-####` (Funding Rounds). In-sheet edits get IDs auto-assigned by onEdit triggers; API writers must assign the next ID themselves following `_Schema`.
- **Input tabs hold no formulas in input columns; calc columns hold no typed values.** Columns with role `calc` or `qa` in the schema are computed — never write into them.
- **All cross-tab references go through named ranges.**
- **Vocabulary lives in Reference.** Enum-constrained columns (see `enum_named_range` in the schema) only accept values from Reference. Add new values to Reference first, then use them.
- **Every automation appends a Changelog row**: timestamp, actor, action, detail, rows affected.

## Data model

- `Lease Comps` (input): signed leases. FK `company_id` → Companies. Since v4 (2026-09-02) the funding/company columns (T–Z, including Benchmark Cohort) are **wired lookups** from Funding Rounds, Company Metrics and Companies — never typed; update those tabs instead. Rent is a flat three-tranche schedule (P1 months 1–60, P2 61–120, P3 121+; blank carries the prior tranche). See `docs/LEASE_COMPS_DESIGN.md`.
- `Companies` (input): one row per real company; canonical name. Tenant name variants map via `Reference!VariantMap`.
- `Funding Rounds` (input): one row per round. FK `company_id` → Companies. Requires source + confidence (`HIGH`/`MEDIUM`/`LOW`/`REVIEW`).
- `Floor Detail` (input): one row per floor of a multi-floor comp whose floors carry different economics. FK `comp_id` → Lease Comps. Only needed when floors differ; the comp row's wired AA–AD columns and `Blend Check` (AE) compare the RSF-weighted detail against the typed RSF/rent/TI. See `docs/LEASE_COMPS_DESIGN.md`.
- `Company Metrics` (computed): per-company rollup. Never edit.
- `Dashboard`, `QA`, `Changelog`, `_Schema`, `Start Here`: computed/meta. QA must show all checks PASS after any change.

## Record status semantics

Computed, never typed: `MISSING INPUTS` (missing any of comp ID, date, submarket, RSF, term, starting rent) → `NEEDS REVIEW` (seats or TI unknown, or `Blend Check` not OK) → `READY`.

## In this repo

- Keep `schema/schema.json` and `schema/reference.json` in sync with the workbook's `_Schema` and `Reference` tabs when they change; regenerate `docs/DATA_DICTIONARY.md` from the schema at the same time.
- Scripts address Lease Comps columns **by header text** (`common.headers`), never by hard-coded letter — three column moves in one day proved letters are not a stable key.
- Workbook operations live in `tools/sheet_ops/` (Sheets API via the `GOOGLE_SA_KEY` service account). Every script is re-runnable, appends Changelog receipts, and gates on QA. Run `python3 tools/sheet_ops/sync_schema.py` after any `_Schema` or Reference change to refresh the mirrors and the data dictionary.
- Data snapshots, scripts, or an API layer added later must obey the contract above.
