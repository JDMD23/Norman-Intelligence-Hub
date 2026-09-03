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

- **86 comps carry TI $/SF = 0** (QA-072, INFO). Per JD 7/28/2026 a confirmed zero on an as-is deal
  is a real zero, and unknown TI is left blank instead. Worth a spot check that all 86 are genuinely
  as-is rather than unknowns entered as 0 — a false zero inflates NER.
- **29 rounds flagged REVIEW** (QA-050, INFO). Verify, then downgrade the flag.
- **43 companies** show tracked funding below their researched narrative total, because early rounds
  are not tracked. This is expected and by design — Total Tracked Funding is a receipts number — but
  it means Lease-to-Total-Funding reads high for those companies.
