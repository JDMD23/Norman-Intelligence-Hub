# Norman Intelligence Hub

The market-intelligence brain behind NormansHub — tracking NYC office lease comps for venture-backed companies, alongside the companies themselves and their funding rounds.

This repository is the code + contract home for the hub. The **live data lives in the Google Sheets workbook** (V3.0.0):

> [Norman AI Intelligence Hub — workbook](https://docs.google.com/spreadsheets/d/1qZlc8BUZRObyoeygAToWicor-UFFLmO_aCjk3axBhdE/edit)

## What the hub tracks

| Table | Purpose |
| --- | --- |
| **Lease Comps** | One row per signed NYC office lease: RSF, term, rents, concessions, plus computed economics (Year 1 Rent, Projected Gross, NER @ 6%, Cost/Seat, rent-to-funding ratios). |
| **Companies** | One row per real company (canonical name), with Crunchbase/website, industry, HQ, and narrative funding research. |
| **Funding Rounds** | One row per funding round, FK'd to Companies, with amount, lead investors, source, and confidence. |
| **Company Metrics** | Computed rollup per company: lease averages, tracked funding totals, round cadence, benchmark band. |
| **Dashboard** | Live market dashboard — benchmarks by last funding round, submarket, and class. Every number is a formula. |
| **QA** | Self-auditing health checks (formula errors, duplicate/orphan IDs, freshness, capacity). |
| **Changelog** | Append-only receipts for every automated change. |
| **_Schema** | The machine-readable contract for every tab, column, and formula. Mirrored in this repo at [`schema/schema.json`](schema/schema.json). |
| **Floor Detail** | Per-floor economics for multi-floor comps; the comp row checks its typed blend against it. |
| **Reference** | Controlled vocabularies (submarkets, building classes, deal types, round types, …) and the tenant-variant → canonical-company map. Mirrored at [`schema/reference.json`](schema/reference.json). |

## Repository layout

```
schema/
  schema.json      Machine-readable export of the workbook's _Schema tab
  reference.json   Controlled vocabularies + tenant variant map (Reference tab)
docs/
  DATA_DICTIONARY.md   Human-readable data dictionary (generated from schema.json)
  QA_CHECKS.md         Catalog of the workbook's QA health checks
  LEASE_COMPS_DESIGN.md  Lease Comps v4 tab design + as-built layout
  NER_MODEL.md         Baseline NER model (reference implementation in scripts/ner.py)
scripts/
  ner.py             Python reference for the workbook's NER formula
tools/sheet_ops/     Receipted, QA-gated workbook operations (Sheets API; needs GOOGLE_SA_KEY)
  run_all.py         Lease Comps v4 migration pipeline (re-runnable)
  theme.py           The CBRE-green palette every presentation pass imports
  migrate_cohort_column.py / remove_provenance_columns.py / migrate_floor_detail.py
                     Structural moves after v4 (idempotent, receipted)
  style.py / polish.py / dashboard_style.py / style_workbook.py / copy_pass.py
                     Presentation passes (Lease Comps zones, tab tiering, Dashboard v2, supporting tabs, copy)
  cohorts.py / companies_view.py / tidy_vocab.py
                     Benchmark cohorts, Companies reading view, vocabulary normalisation
  sync_schema.py     Pull _Schema + Reference into schema/ and regenerate the data dictionary
CLAUDE.md          Contract for AI agents working on the hub
```

## Core rules (the workbook contract)

1. **Source of truth** — Lease Comps, Companies, and Funding Rounds are the input tables. Everything else is computed. (Availabilities was retired 7/28/2026 — archived, rebuild pending.)
2. **Live math** — all calc columns are live formulas. Edit inputs, never results.
3. **Unknown = blank** — never type `0` for an unknown value. Blank propagates correctly; `0` corrupts averages. (A confirmed-zero TI on an as-is deal is the one legitimate `0`.)
4. **IDs are immutable** — `LC-####` / `CO-####` / `FR-####` are auto-assigned in the sheet by onEdit triggers and never reused. Agents writing via API must assign IDs themselves per `_Schema`.
5. **Controlled vocabulary** — dropdown fields are fed from the Reference tab. New submarket/class/type? Add it in Reference first.
6. **Computed status** — every record's status (`READY` / `NEEDS REVIEW` / `MISSING INPUTS`) is a formula, never static text.
7. **Receipts** — every automation appends a Changelog row: timestamp, actor, action, detail.

## For agents

Read [`CLAUDE.md`](CLAUDE.md) and [`schema/schema.json`](schema/schema.json) before touching anything. The `_Schema` tab in the workbook remains the authoritative live contract; the JSON here is a versioned mirror of it.
