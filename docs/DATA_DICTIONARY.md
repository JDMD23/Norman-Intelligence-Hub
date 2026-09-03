# Data Dictionary

Generated from [`schema/schema.json`](../schema/schema.json), a mirror of the workbook's `_Schema` tab (V3.0.0). The live `_Schema` tab is authoritative.

**Workbook contract:** Unknown values stay BLANK, never 0. IDs are immutable and never reused. Input tabs hold no formulas in input columns; calc columns hold no typed values. All cross-tab references go through named ranges. Vocabulary lives in Reference; add new values there first. Every automation appends a Changelog row.

## Lease Comps

| Col | Header | Key | Type | Role | Req | Enum | Description |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | Comp ID | `comp_id` | id | input | yes |  | AUTO-ASSIGNED by onEdit trigger when Tenant is entered. API writers must supply IDs. Immutable, never reused. |
| B | Date Signed | `date` | date | input | yes |  | Lease execution date. |
| C | Tenant | `tenant` | text | input | yes |  | Tenant display name as signed. Variants map via Reference!VariantMap. |
| D | Company ID | `company_id` | id | input | yes | CompanyIds | FK to Companies. AUTO-ASSIGNED with Comp ID. |
| E | Address | `address` | text | input | yes |  | Building street address. |
| F | Submarket | `submarket` | text | input | yes | Submarkets | Canonical submarket. |
| G | Building Class | `bclass` | text | input |  | BuildingClasses | Building class. |
| H | Floor(s) | `floors` | text | input |  |  | Floor(s) leased. |
| I | Condition | `condition` | text | input |  | Conditions | Space condition at signing. |
| J | Deal Type | `deal_type` | text | input |  | DealTypes | Deal structure. |
| K | Delivery Condition | `delivery` | text | input |  | DeliveryConditions | Landlord delivery condition. |
| L | RSF | `rsf` | int | input | yes |  | Rentable square feet. |
| M | Seats | `seats` | int | input |  |  | Seat count. Blank = unknown (never 0). |
| N | Term (Years) | `term` | num | input | yes |  | Lease term in years. Fractional allowed. |
| O | Rent P1 ($/RSF, mo 1-60) | `rent_p1` | rent | input | yes |  | Tranche-1 rent, flat through month 60 (or term end if shorter). |
| P | Rent P2 ($/RSF, mo 61-120) | `rent_p2` | rent | input |  |  | Tranche-2 rent, months 61-120. BLANK = carries P1 flat (no assumed escalation). |
| Q | Rent P3 ($/RSF, mo 121+) | `rent_p3` | rent | input |  |  | Tranche-3 rent, months 121+. BLANK = carries P2 flat. |
| R | Free Rent (months) | `free_mo` | num | input |  |  | Free rent concession in months. |
| S | TI $/SF | `ti_psf` | rent | input |  |  | TI allowance per SF. Blank = unknown (NER stays blank). Confirmed-zero on as-is deals is a real 0. |
| T | Comp Source | `source` | text | input |  | CompSources | Where this comp came from. |
| U | Verified Date | `verified` | date | input |  |  | When this comp was last verified. >6 months old flips status to STALE - REVERIFY. |
| V | Latest Round Date | `lr_date` | date | calc |  |  | Most recent round date (wired lookup — never type here; source of truth lives in the referenced tab) -> Funding Rounds. |
| W | Latest Round Type | `lr_type` | text | calc |  |  | Type of most recent round; same-day rounds resolve to the larger amount (wired lookup — never type here; source of truth lives in the referenced tab) -> Funding Rounds. |
| X | Latest Round Amt ($M) | `lr_amt` | num | calc |  |  | Amount of most recent round (wired lookup — never type here; source of truth lives in the referenced tab) -> Funding Rounds. |
| Y | Total Tracked Funding ($M) | `total_fund` | num | calc |  |  | Sum of tracked rounds (wired lookup — never type here; source of truth lives in the referenced tab) -> Company Metrics. Blank (never 0) when tracked rounds have no amounts. Semantic: tracked receipts, not researched narrative totals. |
| Z | Company (canonical) | `company` | text | calc |  |  | Canonical company name (wired lookup — never type here; source of truth lives in the referenced tab) -> Companies. |
| AA | HQ City | `hq` | text | calc |  |  | HQ city (wired lookup — never type here; source of truth lives in the referenced tab) -> Companies. |
| AB | Benchmark Cohort | `cohort` | text | calc |  |  | Benchmark cohort used to group the Dashboard table (wired lookup — never type here; source of truth lives in the referenced tab) -> Reference CohortTypes/CohortLabels. Thin stages are grouped: Series D/E/F/G + Late Stage Venture -> "Late Stage (D+)", IPO + reverse merger -> "Public". Add new round types to the Reference map, never here. |
| AC | Notes | `notes` | text | input |  |  | Free-form deal notes. |
| AD | Year 1 Rent ($) | `y1_rent` | usd | calc |  |  | RSF x P1 rent. |
| AE | Free Rent $ Value | `free_val` | usd | calc |  |  | (Free months / 12) x P1 rent x RSF. |
| AF | TI Allowance Total ($) | `ti_total` | usd | calc |  |  | TI $/SF x RSF. |
| AG | Projected Gross Rent (Term) | `pgr` | usd | calc |  |  | Nominal rent over the term on FLAT tranches (no assumed escalation). |
| AH | Avg Rate ($/RSF/Yr) | `avg_rate` | rent | calc |  |  | Projected Gross / RSF / Term. |
| AI | NER Annuity ($/RSF/Yr) @ 6% | `ner` | rent | calc |  |  | Baseline NER per docs/NER_MODEL.md: monthly 6%/12 discounting, beg-of-month, flat tranches, free rent + TI nominal upfront, levelized. Blank when TI unknown. |
| AJ | Cost/Seat (Year 1) | `cost_seat` | usd | calc |  |  | Year 1 Rent / Seats. |
| AK | RSF / Seat | `rsf_seat` | num1 | calc |  |  | Density: RSF / Seats. |
| AL | Rent-to-Raise (Yr 1) % | `rent_raise` | pct | calc |  |  | Year 1 Rent / wired latest round. |
| AM | Lease-to-Total-Funding % | `l2tf` | pct | calc |  |  | Projected Gross / wired total tracked funding. |
| AN | Months of Rent Covered | `mo_cover` | num1 | calc |  |  | Total tracked funding / monthly Year-1 rent. |
| AO | Record Status | `status` | text | qa |  | RecordStatuses | READY / NEEDS REVIEW / MISSING INPUTS / STALE - REVERIFY (verified >6mo ago) — computed, never typed. |
| AP | QA Notes | `qa` | text | qa |  |  | Auto list of missing fields + staleness flag. |

## Companies

| Col | Header | Key | Type | Role | Req | Enum | Description |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B | Canonical Name | `name` | text | input | yes |  | One row per real company. Tenant-name variants map here via Reference!VariantMap. |
| C | Crunchbase URL | `cb_url` | text | input |  |  | Verified Crunchbase profile. |
| D | Website | `website` | text | input |  |  | Company website. |
| E | Industry | `industry` | text | input |  |  | Industry label. |
| F | Founded Year | `founded` | int | input |  |  | Founding year. |
| G | HQ City | `hq` | text | input |  |  | Headquarters city. |
| H | Funding History (text) | `fund_hist` | text | input |  |  | Narrative funding history (research output). |
| I | Funding Velocity Detail | `velocity` | text | input |  |  | Narrative velocity summary (research output). |
| J | Funding Accel/Decel Note | `accel` | text | input |  |  | Acceleration/deceleration read. |
| K | Sources | `sources` | text | input |  |  | Research source list. |
| L | Notes | `notes` | text | input |  |  | Identity caveats (e.g. Mirage<->Captions), review flags. |
| M | Latest Round | `latest_round` | text | calc |  |  | Latest tracked round type and month (wired lookup — never type here; source of truth lives in the referenced tab) -> Company Metrics. |
| N | Total Tracked Funding ($M) | `total_fund` | num | calc |  |  | Sum of tracked rounds, blank (never 0) when amounts are unknown (wired lookup — never type here; source of truth lives in the referenced tab) -> Company Metrics. |

## Funding Rounds

| Col | Header | Key | Type | Role | Req | Enum | Description |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | Round ID | `round_id` | id | input | yes |  | AUTO-ASSIGNED by onEdit trigger when row data is entered. API writers must supply IDs. Immutable, never reused. |
| B | Company ID | `company_id` | id | input | yes | CompanyIds | FK to Companies. |
| C | Company | `company` | text | calc |  |  | Looked up from Companies by ID. |
| D | Round Number | `round_no` | int | input |  |  | Sequence number within company. |
| E | Round Type | `round_type` | text | input | yes | RoundTypes | Round type. |
| F | Round Date | `date` | date | input | yes |  | Round announcement date. |
| G | Round Amount ($M) | `amount` | num | input |  |  | Round size in $M. |
| H | Lead Investors | `investors` | text | input |  |  | Lead investors. |
| I | Cumulative After Round ($M) | `cumulative` | num | input |  |  | Reported cumulative funding (may include undisclosed prior base). QA cross-checks vs running sum. |
| J | Months Since Prior Round | `mo_prior` | int | calc |  |  | Computed from previous round of same company. |
| K | Source | `source` | text | input | yes |  | Source name. |
| L | Source URL | `source_url` | text | input |  |  | Source link. |
| M | Confidence | `confidence` | text | input | yes | ConfidenceLevels | HIGH / MEDIUM / LOW / REVIEW. |
| N | Notes | `notes` | text | input |  |  | Disclosed prior-base notes, dedupe decisions, intentional-duplicate markers. |

## Company Metrics

| Col | Header | Key | Type | Role | Req | Enum | Description |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | Company ID | `company_id` | id | calc |  |  | Mirror of Companies!A. |
| B | Company | `name` | text | calc |  |  | Mirror of Companies!B. |
| C | Signed Lease Count | `comps` | int | calc |  |  | Count of lease comps for this company. |
| D | Latest Signed Lease | `latest_lease` | date | calc |  |  | Most recent signing date. |
| E | Avg RSF | `avg_rsf` | num1 | calc |  |  | Average comp RSF. |
| F | Avg Starting Rent | `avg_rent` | rent | calc |  |  | Average starting rent. |
| G | Avg NER | `avg_ner` | rent | calc |  |  | Average NER (blank-safe). |
| H | Avg Cost/Seat | `avg_seat` | usd | calc |  |  | Average Year-1 cost per seat. |
| I | Avg Term | `avg_term` | num1 | calc |  |  | Average lease term. |
| J | Funding Rounds Tracked | `rounds` | int | calc |  |  | Rows in Funding Rounds. |
| K | Last Round Date | `last_rd_date` | date | calc |  |  | Most recent tracked round. |
| L | Last Round Type | `last_rd_type` | text | calc |  |  | Type of most recent round. |
| M | Tracked Total Raised ($M) | `tracked_total` | num | calc |  |  | Sum of tracked round amounts. |
| N | Avg Months Between Rounds | `avg_cadence` | num1 | calc |  |  | Average of computed inter-round gaps. |
| O | Benchmark Band | `benchmark` | text | calc |  |  | Cohort label for benchmarking. |

## Reference vocabularies

- **Submarkets**: Chelsea, Chelsea/Meatpacking, Financial District, Flatiron, Grand Central, Hudson Square, Hudson Yards / Penn Station, Meatpacking, Midtown, NoMad, PAS / Mad. Square Park, Penn Station, SoHo, Soho/Noho, Union Square, World Trade Center
- **BuildingClasses**: Trophy, Glass & Steel, Class A, Class B, Commodity
- **DealTypes**: Expansion, Extension/Expansion, New Lease, Renewal, Renewal + Expansion, Sublease
- **Conditions**: Raw, New prebuilt, Second Gen
- **DeliveryConditions**: LL Turnkey, As-Is, Custom TIA
- **RoundTypes**: Debt, IPO, Late Stage Venture, Private Equity, Public Listing / Reverse Merger, Seed, Series A, Series B, Series C, Series D, Series E, Series F, Series G, Venture - Series Unknown
- **ConfidenceLevels**: HIGH, MEDIUM, LOW, REVIEW
- **RecordStatuses**: READY, NEEDS REVIEW, MISSING INPUTS, STALE - REVERIFY
- **CompSources**: CoStar, CBRE, Broker Intel, Press, Direct/Landlord
- **CohortTypes**: Seed, Series A, Series B, Series C, Series D, Series E, Series F, Series G, Late Stage Venture, Private Equity, IPO, Public Listing / Reverse Merger, Debt, Venture - Series Unknown
- **CohortLabels**: Seed, Series A, Series B, Series C, Late Stage (D+), Late Stage (D+), Late Stage (D+), Late Stage (D+), Late Stage (D+), Late Stage (D+), Public, Public, Debt, Stage Unknown
- **CohortOrder**: Seed, Series A, Series B, Series C, Late Stage (D+), Public, Debt, Stage Unknown, No Funding Data

### Tenant variant map

- `HARVEY AI (E6)` → `HARVEY AI`
