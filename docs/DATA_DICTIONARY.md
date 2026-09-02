# Data Dictionary

Generated from [`schema/schema.json`](../schema/schema.json), a mirror of the workbook's `_Schema` tab (V3.0.0). The live `_Schema` tab is authoritative.

**Workbook contract:** Unknown values stay BLANK, never 0. IDs are immutable and never reused. Input tabs hold no formulas in input columns; calc columns hold no typed values. All cross-tab references go through named ranges. Vocabulary lives in Reference; add new values there first. Every automation appends a Changelog row.

## Lease Comps

| Col | Header | Key | Type | Role | Req | Enum | Description |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | Comp ID | `comp_id` | id | input | yes |  | AUTO-ASSIGNED by onEdit trigger when Tenant is entered (company auto-created if unknown). API writers must supply IDs themselves. Immutable, never reused. |
| B | Date Signed | `date` | date | input | yes |  | Lease execution date. |
| C | Tenant | `tenant` | text | input | yes |  | Tenant display name as signed. Variants map to a company in Reference!VariantMap. |
| D | Company ID | `company_id` | id | input | yes | CompanyIds | AUTO-ASSIGNED by onEdit trigger when Tenant is entered (company auto-created if unknown). API writers must supply IDs themselves. Immutable, never reused. |
| E | Address | `address` | text | input | yes |  | Building street address. |
| F | Submarket | `submarket` | text | input | yes | Submarkets | Canonical submarket. |
| G | Building Class | `bclass` | text | input |  | BuildingClasses | Building class. |
| H | Floor(s) | `floors` | text | input |  |  | Floor(s) leased. |
| I | Condition | `condition` | text | input |  | Conditions | Space condition at signing. |
| J | Deal Type | `deal_type` | text | input |  | DealTypes | Deal structure. |
| K | Delivery Condition | `delivery` | text | input |  | DeliveryConditions | Landlord delivery condition. |
| L | RSF | `rsf` | int | input | yes |  | Rentable square feet. |
| M | Seats | `seats` | int | input |  |  | Seat count / density input. Blank = unknown (never 0). |
| N | Term (Years) | `term` | num | input | yes |  | Lease term in years. Fractional allowed. |
| O | Starting Rent ($/RSF) | `start_rent` | rent | input | yes |  | Year-1 base rent per RSF. |
| P | Escalated Rent Yr 6 ($/RSF) | `rent_y6` | rent | input |  |  | Explicit year-6 step rent. Blank = continuous 3% escalation assumed. |
| Q | Escalated Rent Yr 11 ($/RSF) | `rent_y11` | rent | input |  |  | Explicit year-11 step rent. Blank = continuous 3% escalation assumed. |
| R | Free Rent (months) | `free_mo` | num | input |  |  | Free rent concession in months. |
| S | TI $/SF | `ti_psf` | rent | input |  |  | Tenant improvement allowance per SF. Blank = unknown (NER stays blank). |
| T | Latest Round Date | `lr_date` | date | input |  |  | Latest known funding round date. Policy (JD 7/28/2026): these funding columns hold CURRENT/latest known funding, refreshed over time -- not frozen at signing. |
| U | Last Funding Round | `lr_type` | text | input |  | RoundTypes | Latest known round type. |
| V | Latest Round Amt ($M) | `lr_amt` | num | input |  |  | Latest known round size in $M. Blank for public cos. |
| W | Total Funding ($M) | `total_fund` | num | input |  |  | Latest known cumulative funding in $M. |
| X | Top 5 Investors | `investors` | text | input |  |  | Top investors, comma-separated. |
| Y | Crunchbase URL | `cb_url` | text | input |  |  | Crunchbase profile URL. |
| Z | Founded Year | `founded` | int | input |  |  | Company founding year. |
| AA | HQ City | `hq` | text | input |  |  | Headquarters city. |
| AB | Notes | `notes` | text | input |  |  | Free-form deal notes. |
| AC | Year 1 Rent ($) | `y1_rent` | usd | calc |  |  | RSF x Starting Rent. |
| AD | Year 6 Rent ($) | `y6_rent` | usd | calc |  |  | RSF x explicit Yr-6 rent; blank when no explicit step. |
| AE | Free Rent $ Value | `free_val` | usd | calc |  |  | (Free months / 12) x Starting Rent x RSF. |
| AF | TI Allowance Total ($) | `ti_total` | usd | calc |  |  | TI $/SF x RSF. |
| AG | Projected Gross Rent (Term) | `pgr` | usd | calc |  |  | Three-tranche rent total with 3% annual escalation inside each tranche. Tranche rates: Starting / Yr-6 / Yr-11 (blank steps fall back to continuous 3%). |
| AH | Avg Rate ($/RSF/Yr) | `avg_rate` | rent | calc |  |  | Projected Gross Rent / RSF / Term. |
| AI | NER Annuity ($/RSF/Yr) @ 6% | `ner` | rent | calc |  |  | Baseline NER (per NER.xls model, owner-approved 2026-09-02): flat rent tranches (start rent to mo 60, Yr-6 rate to mo 120, Yr-11 rate after; blank bump carries prior rate), monthly discounting at 6%/12, beginning-of-month annuity, free rent at starting rate + TI charged nominal upfront, levelized to $/RSF/yr. No commissions/downtime. Blank when TI unknown. |
| AJ | Cost/Seat (Year 1) | `cost_seat` | usd | calc |  |  | Year 1 Rent / Seats. Blank until Seats entered. |
| AK | RSF / Seat | `rsf_seat` | num1 | calc |  |  | Density: RSF / Seats. Blank until Seats entered. |
| AL | Rent-to-Raise (Yr 1) % | `rent_raise` | pct | calc |  |  | Year 1 Rent / latest round ($M->$). |
| AM | Lease-to-Latest-Round % | `l2lr` | pct | calc |  |  | Projected Gross Rent / latest round. |
| AN | Lease-to-Total-Funding % | `l2tf` | pct | calc |  |  | Projected Gross Rent / total funding. |
| AO | Year 1 Rent / Total Funding % | `y12tf` | pct | calc |  |  | Year 1 Rent / total funding. |
| AP | Months of Rent Covered | `mo_cover` | num1 | calc |  |  | Total funding / monthly Year-1 rent. |
| AQ | NER Term Cost / Latest Round % | `nertc` | pct | calc |  |  | NER x RSF x Term / latest round. |
| AR | Tenant Tenure at Signing | `tenure` | int | calc |  |  | YEAR(signed) - founded year. |
| AS | Record Status | `status` | text | qa |  |  | READY / NEEDS REVIEW / MISSING INPUTS -- computed, never typed. |
| AT | QA Notes | `qa` | text | qa |  |  | Auto list of missing fields. |

## Companies

| Col | Header | Key | Type | Role | Req | Enum | Description |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | Company ID | `company_id` | id | input | yes |  | AUTO-ASSIGNED by onEdit trigger when Canonical Name is entered. Immutable, never reused. FK target for Lease Comps + Funding Rounds. |
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
- **RecordStatuses**: READY, NEEDS REVIEW, MISSING INPUTS

### Tenant variant map

- `HARVEY AI (E6)` → `HARVEY AI`
