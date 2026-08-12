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

- `Lease Comps` (input): signed leases. FK `company_id` → Companies. Funding columns (T–AA) hold *current/latest known* funding, refreshed over time — not frozen at signing.
- `Companies` (input): one row per real company; canonical name. Tenant name variants map via `Reference!VariantMap`.
- `Funding Rounds` (input): one row per round. FK `company_id` → Companies. Requires source + confidence (`HIGH`/`MEDIUM`/`LOW`/`REVIEW`).
- `Company Metrics` (computed): per-company rollup. Never edit.
- `Dashboard`, `QA`, `Changelog`, `_Schema`, `Start Here`: computed/meta. QA must show all checks PASS after any change.

## Record status semantics

Computed, never typed: `MISSING INPUTS` (missing any of comp ID, date, submarket, RSF, term, starting rent) → `NEEDS REVIEW` (seats or TI unknown) → `READY`.

## In this repo

- Keep `schema/schema.json` and `schema/reference.json` in sync with the workbook's `_Schema` and `Reference` tabs when they change; regenerate `docs/DATA_DICTIONARY.md` from the schema at the same time.
- Data snapshots, scripts, or an API layer added later must obey the contract above.
