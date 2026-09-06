# Data research queue

Open data questions in the Norman Intelligence Hub that need a human with sources, not a script.
Compiled 2026-09-03 from the workbook's own flags. Work top to bottom: the first section distorts
what the Dashboard shows today.

The workbook stages every comp by its **latest tracked funding round**. That is only as good as
Funding Rounds is complete. When a company's recent rounds are not tracked, its comps sit in an
earlier cohort and pull that cohort's averages toward a larger, later-stage deal.

---

## 1. Rounds the company research does not support

These four were backfilled from the 2026-08/09 audit during the v4 migration and are now flagged
`REVIEW` in Funding Rounds (see the CONFIDENCE DOWNGRADE Changelog receipt). Each needs a primary
source, then either a corrected row or an upgrade back to `HIGH`.

| Round | Company | What the row claims | What the research says |
| --- | --- | --- | --- |
| FR-0279 | Tempo Labs (CO-0082) | Seed, Oct 2025, $5.0M | "pre-seed … funding amount/date **not confirmed** in public source"; "insufficient disclosed funding amount/date history" |
| FR-0283 | Verkada (CO-0089) | Series E, Dec 2025, $100M | Dec 2025 was a "**$20M** venture/unknown round"; classification "needs review" |
| FR-0282 | Traversal (CO-0087) | Venture – Series Unknown, Mar 2026, no amount | "$5M latest vs $53M total — amount/total **mismatch needs review**" |
| FR-0247 | Actively AI (CO-0002) | Series B, Apr 2026, $45M | research tracks only through Apr 2025 Series A ($17.5M, total $22.5M) |

**Tempo Labs is the urgent one.** It is the *entire* Seed cohort (n=1), and its lease economics
contradict a seed stage outright:

- 15,271 RSF · 90 seats · **10-year term** · $120.00/RSF · signed May 2026
- Year 1 rent **$1,832,520** — **37%** of all capital the company is recorded as having raised
- Projected gross **$19.1M** — **382%** of total tracked funding
- Total tracked funding covers **33 months** of rent

Either Tempo Labs raised substantially more before signing and those rounds are untracked, or the
comp's lease terms need re-checking. Until it is resolved the Seed row shows a count with no
averages.

---

## 2. Companies whose recent funding is probably untracked

15 comps were signed 12+ months after the company's last tracked round. For the five public
companies this is expected and harmless — once public they stay in the `Public` cohort. The rest
are likely mis-staged. Ordered by how much they distort a cohort:

| Comp | Tenant | Sits in | Last tracked round | Gap | Why it matters |
| --- | --- | --- | --- | --- | --- |
| LC-0038 | Notion | Series C | Series C, Oct 2021 | 51 mo | 26,427 RSF at $85 anchored in Series C; Notion is far later stage |
| LC-0008 | Meow | Series A | Series A, Jul 2022 | 46 mo | small deal, but Series A n=11 so it carries weight |
| LC-0088 | Radar Labs | Series C | Series C, Feb 2022 | 37 mo | 20,000 RSF at $79 |
| LC-0021 | Pelago | Series C | Series C, Mar 2024 | 24 mo | 13,600 RSF at $67 |
| LC-0100 | One Pay | Stage Unknown | Venture – Series Unknown, Dec 2024 | 18 mo | 14,563 RSF at $117 — unmapped stage |
| LC-0014 | Charlie Health | Debt | Debt, Jun 2020 | 70 mo | Debt cohort is n=2; a stale debt facility is its whole story |
| LC-0062 | Grammarly | Late Stage (D+) | Late Stage Venture, Nov 2021 | 45 mo | already in the top bucket — low distortion |
| LC-0067 | Fireblocks | Late Stage (D+) | Series E, Jan 2022 | 42 mo | as above |
| LC-0065 | The Farmer's Dog | Late Stage (D+) | Series E, Jun 2022 | 38 mo | as above |
| LC-0054 | Scale AI | Late Stage (D+) | Series F, May 2024 | 17 mo | as above |

Expected and fine (public companies): LC-0072 Cloudflare, LC-0050 Coinbase, LC-0004 NextDoor,
LC-0089 Affirm, LC-0064 Tempus.

**Fix path:** add the missing rounds to Funding Rounds. The comp's stage columns and the Dashboard
cohort tables re-compute on their own — never type into the Lease Comps funding columns.

---

## 3. Company identity and naming

| Company | Issue |
| --- | --- |
| Mirage (CO-0050) | Crunchbase URL points to **Captions**. "Verify Mirage/Captions identity before company-level aggregation." Two names for one company, or two companies? |
| Paradigm Health (CO-0061) | "Verify whether duplicate/variant tenant naming is intended" — potential duplicate with another Paradigm row. |

Both affect Company Metrics rollups, which feed the wired columns on every comp for those companies.

---

## 4. Standing data-quality notes

- **Rent escalations: resolved 2026-09-06.** 17 comps longer than five years carried a blank
  Rent P2, which asserts flat rent for the whole term. JD answered all 17: four carry a real
  escalation and now hold a Rent P2 (LC-0093 Sigma, LC-0086 Plaid — whose P1 was also corrected
  $76 → $79 — LC-0004 NextDoor, LC-0088 Radar Labs); the other 13 he confirmed genuinely flat and
  now say so in Notes. **A blank Rent P2 on those 13 is an answer, not a gap** — do not re-raise
  them. Any *new* long comp with a blank P2 is still an open question.
- **Submarket vocabulary: settled 2026-09-06.** "SoHo"/"Soho/Noho" merged into `SoHo/NoHo` (22
  comps), `Chelsea/Meatpacking` and `Penn Station` retired, and Reference narrowed 16 -> 13 with the
  dropdown repointed so none of the retired spellings can be picked again. Building-level rulings on
  record: 1 Madison Avenue is PAS / Mad. Square Park, 675 Avenue of the Americas is Flatiron, 837
  Washington Street is Meatpacking, and the whole Penn cluster (2/5/21 Penn Plaza, 330 W 34th, 1245
  and 1375 Broadway) is Hudson Yards / Penn Station. `Midtown` and `NoMad` remain in Reference with
  no comps — kept deliberately for future deals.
- **Seat counts: closed 2026-09-06, and mostly closed as "unknowable."** JD was asked about all 23
  comps that had none. Three now carry an approximate figure — LC-0110 Legora ~600, LC-0104 Suno AI
  ~620, LC-0087 Peregrine ~45, all noted as approximate. The other **20 stay permanently blank**:
  they are custom build-outs whose layout the tenant's own real estate team set, and JD has no
  visibility into it. **Do not re-raise these and do not estimate them** — a guessed seat count on a
  462,000 SF comp would move the Dashboard's cost/seat more than any real number in the book.
  Coverage is 93 of 113 comps (2,396,344 RSF still seatless), and the Dashboard methodology note now
  states that count live so nobody reads Avg cost/seat as full-book. The 20: Anthropic, PayPal,
  Fanatics, Clay, Monday.com, Ramp, Rippling, Figma, Harvey AI ×2, Coinbase, Chime, EliseAI, Sigma,
  Altana AI, Current Bank, David Protein, BILT Rewards, Tempus, Notion.
- **65 comps carry TI $/SF = 0** (QA-072, INFO), all of them now on an `As-Is` delivery condition,
  so each is a confirmed zero rather than an unknown entered as 0 (down from 87 before the
  2026-09-03 TI pass). Per JD 7/28/2026 a confirmed zero on an as-is deal is a real zero; unknown
  TI is left blank.
- **LC-0064 (Tempus, 11 Madison) has no TI figure**, so it computes no NER and sits out of every
  average — the only comp in that state. JD does not have the TIA. Blank is correct per the
  contract; the comp becomes complete the moment a real number surfaces.
- **Turnkey TI: closed 2026-09-06.** Ten comps sat on the $150/SF benchmark rather than a real
  figure (the earlier count of eight was wrong — it missed Ramp and Grammarly). JD marked up all
  ten. Five confirmed at $150 and are no longer estimates; four moved — Vercel and Grammarly to
  $155, Tenex to $110, Notion to $140. Two standing building-level rules came out of it and are
  recorded in `docs/LEASE_COMPS_DESIGN.md`: any **raw** space at 360 Park Avenue South takes
  **$155/SF**, and 60 Madison Avenue takes **$110/SF**. **Only LC-0007 (Tempo Labs) is still on the
  benchmark**, held there deliberately — see section 1, it already carries an unverified Seed round
  and guessing its TI would compound one open question with another.
- **92% of funding rounds have no source URL.** Confidence is asserted, not evidenced. This is why
  section 1 exists.
- **29 rounds flagged REVIEW** (QA-050, INFO). Verify, then downgrade the flag.
- **43 companies** show tracked funding below their researched narrative total, because early rounds
  are not tracked. This is expected and by design — Total Tracked Funding is a receipts number — but
  it means Lease-to-Total-Funding reads high for those companies.
