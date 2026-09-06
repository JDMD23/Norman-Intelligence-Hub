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
| 7 Governance | AN–AO | qa | Record Status (READY / NEEDS REVIEW / MISSING INPUTS + new `STALE — REVERIFY` when Verified Date > 6 months old), QA Notes |

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

Final column map (45 columns after the 2026-09-03 moves: Benchmark Cohort into the wired zone; Comp Source and Verified Date removed — the owner is the provenance and comps are final once entered, so STALE - REVERIFY retired with them; and the Floor Detail tab added with its four wired columns plus a blend check; Zones 1–3 unchanged so the onEdit auto-ID triggers keep working):

| Cols | Zone | Fields |
| --- | --- | --- |
| A–D | Identity (input) | Comp ID, Date Signed, Tenant, Company ID |
| E–K | Premises (input) | Address, Submarket, Building Class, Floor(s), Condition, Deal Type, Delivery Condition |
| L–S | Deal terms (input) | RSF, Seats, Term, Rent P1 / P2 / P3, Free Rent, TI $/SF |
| T–Z | Company wire (calc) | Latest Round Date, Latest Round Type, Latest Round Amt, Total Tracked Funding, Company (canonical), HQ City, Benchmark Cohort |
| AA–AD | Floor wire (calc) | Floors on File, Detail RSF, Detail Rent (wtd), Detail TI (wtd) — from the Floor Detail tab |
| AE | Blend check (qa) | Where the typed RSF / rent / TI disagrees with the floor detail |
| AF | Notes (input) | Free-form deal notes |
| AG–AN | Economics (calc) | Year 1 Rent, Free Rent $, TI Total, Projected Gross (flat tranches), Avg Rate, NER, Cost/Seat, RSF/Seat |
| AO–AQ | Ratios (calc) | Rent-to-Raise, Lease-to-Total-Funding, Months of Rent Covered |
| AR–AS | Governance (qa) | Record Status, QA Notes |

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

## Benchmark cohorts (added 2026-09-02)

Column **AP `Benchmark Cohort`** (calc) maps the wired round type through
`Reference!CohortTypes` → `CohortLabels`, and the Dashboard groups on it. Thin stages are
merged so each cohort has enough n to mean something:

| Cohort | Source round types | n |
| --- | --- | --- |
| Seed / Series A / Series B / Series C | themselves | 1 / 11 / 25 / 11 |
| **Late Stage (D+)** | Series D, E, F, G, Late Stage Venture, Private Equity | **40** |
| Public | IPO, Public Listing / Reverse Merger | 7 |
| Debt | Debt — a financing type, not a stage; deliberately not merged | 2 |
| Stage Unknown | Venture - Series Unknown, plus anything unmapped | 5 |
| No Funding Data | comps whose company has no tracked rounds | 1 |

Add new round types to the Reference map, never to the formula. Display order is
`Reference!CohortOrder`.

**The Dashboard shows median RSF next to average.** RSF is right-skewed in every cohort
(Series C averages 41,108 but medians 26,427), which is what made Series D read as a dip
below Series C. Rent and NER are per-SF rates and far less skewed, so mean is fine there.

## Multi-floor deals (2026-09-03)

**One comp is still one row.** Benchmarks count transactions, so the grain does not move for a
deal that happens to cover several floors.

When a deal's floors carry *different* economics, the per-floor numbers go on the **Floor Detail**
tab — one row per floor, linked by Comp ID, the same way Funding Rounds links to a company. The
comp row then carries four wired columns showing what the floors add up to (count, RSF, RSF-weighted
rent, RSF-weighted TI) and a **Blend Check** comparing them against what was typed. Tolerances are
1 SF, $0.50/RSF and $1/SF; a typed 0 or blank TI against a positive detail blend reads `TI MISSING`.
A mismatch flows into Record Status and QA Notes, so it reaches the Dashboard's needing-review
count, and QA-073 counts it.

Only deals whose floors differ need rows there. Single-floor comps — 79 of 103 — never touch it and
their check columns stay blank.

**Why the check is aimed at TI, not rent.** On LC-0103 (Moment, 325 Hudson, E3 + E10, 43,190 SF)
a simple average of two floors' rents lands within about 20 cents of the RSF-weighted answer:
immaterial. The TI, by contrast, was entered as $0 during hand-blending, which overstates that
comp's NER by roughly $15/SF — about 26%, or ~$4M of concession value over the term.

**Decision rule.** Same lease and same term across the floors: one comp, blend it, record the
floors. Genuinely different terms per floor: those are two deals and belong in two comps, because
differing terms cannot be blended honestly.

## TI conventions (JD, 2026-09-03)

**A TI figure JD supplies always wins.** Where he has the number, it goes in verbatim and his
wording goes in Notes.

**Where he does not have the number and the deal was a landlord turnkey, use $150/SF.** That is
the standing benchmark for turnkey installations. It is an estimate, not a sourced figure, so a
real number replaces it whenever one turns up — Rain AI is the cautionary case: it sat at $140,
was normalised to the $150 benchmark, and JD's survey then showed the real figure was $130.

**Building-level turnkey values beat the benchmark** where JD has set one. These are standing
rules, not one-off answers — apply them to any future comp that meets the condition, and do not
fall back to $150 in these buildings:

| Building | Turnkey value | Applies to | Source |
| --- | --- | --- | --- |
| 360 Park Avenue South | **$155/SF** | any **raw** space | the figure Rogo negotiated (LC-0099) |
| 60 Madison Avenue | **$110/SF** | turnkey deals | Pace (LC-0006), adopted for Tenex (LC-0003) |

Second-generation space at those buildings falls outside the rule — Rogo's own September 2025
deal (LC-0060) is Second Gen / As-Is at $0 and is untouched by the 360 PAS rule.

Note the open question at 60 Madison: Pace's $110 was a **Second Gen** installation while Tenex is
**Raw**, and a raw build normally costs more, not less. JD applied $110 to both. If a better Tenex
figure surfaces it should replace it.

**A $150 in the sheet is now one of two things**, and Notes say which: a figure JD confirmed as
real, or the benchmark estimate still standing in for an unknown. After the 2026-09-06 markup only
LC-0007 (Tempo Labs) is still the latter.

**$0 means a confirmed as-is deal**, not an unknown. Delivery condition and TI have to agree: a
Custom TIA or LL Turnkey deal cannot carry $0, and a new prebuilt is recorded as As-Is with $0
because the landlord built the space rather than passing an allowance. That contradiction is what
QA-072 and the 2026-09-03 markup pass were for — 26 comps carried $0 against a contributing
delivery condition, overstating their NER, on 48% of the book by RSF.

**Unknown is blank**, which blanks the NER rather than overstating it.
