# Lease Comps v4 — tab design

Owner brief (2026-09-02): most organized, structured, precise; everything wired, everything with a home;
never creates confusion or questions; not overdone.

## Principles

1. **One fact, one home.** A comp row contains only lease facts. Company facts live in Companies; funding
   facts in Funding Rounds. Cross-domain data appears here only as formulas — it cannot go stale
   independently (the failure mode behind 45 of the 2026-08-12 audit corrections).
2. **Left-to-right = input-to-derived.** Inputs (Zones 1–3) → wired lookups (Zone 4) → computed economics
   (Zones 5–6) → governance (Zone 7).
3. **No hidden assumptions.** Rent is an explicit flat-tranche schedule (per docs/NER_MODEL.md); the 3%
   escalation assumption is removed everywhere, including Projected Gross.
4. **Every opinion is an enum.** Reference-constrained wherever a vocabulary exists.
5. **Provenance is data.** Each comp records its source and last-verified date; status logic enforces freshness.

## Zones

| Zone | Cols | Role | Fields |
| --- | --- | --- | --- |
| 1 Identity | A–D | input | Comp ID (auto), Date Signed, Tenant (as-signed), Company ID (auto FK). CB URL / HQ / Founded / Investors REMOVED (live in Companies / Funding Rounds). |
| 2 Premises | E–K | input | Address, Submarket*, Building Class*, Floors, Condition*, Deal Type*, Delivery Condition*  (* = Reference enum) |
| 3 Deal terms | L–U | input | RSF, Seats, Term (yrs); Rent P1 (mo 1–60), Rent P2 (61–120, blank = carry P1), Rent P3 (121+, blank = carry P2); Free Rent (mos), TI ($/RSF); NEW: Comp Source*, Verified Date |
| 4 Company wire | V–AA | calc | Canonical Company, HQ, Last Round Type, Last Round Date, Last Round Amt ($M), Total Tracked Funding ($M) — INDEX/MATCH via named ranges from Companies + Company Metrics |
| 5 Economics | AB–AI | calc | Year-1 Rent $, Free Rent Value, TI Total, Projected Gross (flat tranches), Avg Rate, NER (baseline, docs/NER_MODEL.md), Cost/Seat, RSF/Seat |
| 6 Ratios | AJ–AL | calc | Rent-to-Raise (Yr 1), Lease-to-Total-Funding, Months of Rent Covered. (Trimmed from 6: lease-to-latest-round, Yr1-to-total-funding, NER-term-cost/latest-round dropped as unread permutations.) |
| 7 Governance | AM–AN | qa | Record Status (READY / NEEDS REVIEW / MISSING INPUTS + new `STALE — REVERIFY` when Verified Date > 6 months old), QA Notes |

~41 columns (from 46): 10 typed columns removed (8 funding + CB URL + HQ), 2 added (Comp Source, Verified Date).

## Semantics locked in

- Blank = unknown, never 0 (confirmed-zero TI on as-is deals excepted).
- Rent tranches hold FLAT within their window; blank tranche carries the prior rate. Matches deal reality
  (3–5 yr deals flat; 7–10+ bump at yr 6 / yr 11) and the approved NER baseline.
- Zone 4 is protected calc: never typed. Funding updates happen in Funding Rounds only.
- Total Tracked Funding wire respects disclosure-artifact flags (excluded companies show a flag, not a number).

## Migration plan (staged, receipted, QA-gated)

1. Add Comp Source / Verified Date columns + `CompSources` vocabulary to Reference.
2. Build Zone-4 lookup formulas alongside existing typed funding columns; verify they reproduce the
   corrected values on all 103 comps.
3. Cut over: delete typed funding + identity columns, shift calc zones into place.
4. Rebuild Projected Gross on flat tranches; re-point Avg Rate and ratios.
5. Update _Schema, named ranges, QA checks (add freshness check), Dashboard references.
6. Changelog receipts per stage; QA must be all-PASS after each.

Constraint: onEdit auto-ID triggers (Apps Script, not reachable from this environment) reference Zones 1–3
column positions — those zones keep today's column order exactly; only columns T+ restructure.

## As built (2026-09-02)

Executed by `tools/sheet_ops/run_all.py`; receipts in Changelog (STRUCTURE MIGRATION, FORMULA PATCH,
FUNDING ROUNDS BACKFILL, MIGRATION VERIFIED, STYLE, SCHEMA UPDATE, DASHBOARD LAYOUT). QA 19/19 PASS.
Pre-migration copy: tab `LC_BACKUP_2026-09-02` (delete once the v4 tab has been used in anger).

Final column map (41 columns; Zones 1–3 unchanged so the onEdit auto-ID triggers keep working):

| Cols | Zone | Fields |
| --- | --- | --- |
| A–D | Identity (input) | Comp ID, Date Signed, Tenant, Company ID |
| E–K | Premises (input) | Address, Submarket, Building Class, Floor(s), Condition, Deal Type, Delivery Condition |
| L–U | Deal terms (input) | RSF, Seats, Term, Rent P1 / P2 / P3, Free Rent, TI $/SF, Comp Source, Verified Date |
| V–AA | Company wire (calc) | Latest Round Date, Latest Round Type, Latest Round Amt, Total Tracked Funding, Company (canonical), HQ City |
| AB | Notes (input) | Free-form deal notes |
| AC–AJ | Economics (calc) | Year 1 Rent, Free Rent $, TI Total, Projected Gross (flat tranches), Avg Rate, NER, Cost/Seat, RSF/Seat |
| AK–AM | Ratios (calc) | Rent-to-Raise, Lease-to-Total-Funding, Months of Rent Covered |
| AN–AO | Governance (qa) | Record Status, QA Notes |

Wire semantics: Latest Round = most recent row in Funding Rounds for the company; Total Tracked Funding =
Company Metrics tracked sum, blank (never 0) when tracked rounds carry no amounts. Total Tracked is a
*receipts* number, not the researched narrative total that used to be typed — expect it to be lower
wherever early rounds are not yet tracked (41 companies at cut-over).

Backfill: 39 audited latest rounds that Funding Rounds lacked were added as FR-0246..FR-0284 with
month-level dates (day recorded as the 1st, flagged in Notes) so the wire reproduces the audit.

Open REVIEW items for the owner (not auto-fixed):

- LC-0001 (Confido, CO-0023 — earlier drafts of this note wrongly said CO-0001/Abridge): Funding Rounds holds
  both a Seed $5M and a Series A $15M dated 2025-08-11. The wire's latest-round lookup tie-breaks same-day
  rounds by row order and surfaces the Seed; the audit recorded the Series A. Fix belongs in the W/X wire
  formulas (secondary sort on amount, descending), not in the Funding Rounds data.
- LC-0012 / LC-0083 (CO-0080): RESOLVED 2026-09-02 via apply_judgments.py (date -> 2026-01-26).
- Off-vocabulary round types: "Growth", "Direct Listing", "Series B / Strategic", "Common Stock Financing"
  RESOLVED 2026-09-02 via apply_judgments.py (normalised to Reference RoundTypes, originals kept in Notes).
  Still off-vocabulary: "Series E-2", "Debt / Venture Unknown".
