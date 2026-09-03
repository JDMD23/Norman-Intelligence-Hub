"""Finalize: rewrite the _Schema blocks for Lease Comps and Floor Detail from the live headers,
verify the Dashboard benchmark table, then gate on QA (exit non-zero unless every check PASSes).

Metadata is keyed by HEADER TEXT, not column letter, and formulas come from migrate_structure's
F_SPEC via each header's current position. So a column insert or move needs no edit here — the
recurring source of column-letter bugs in this repo.
"""
import sys

from common import (session, sheet_ids, batch_update, values_batch, get_values, changelog,
                    qa_status, headers, SID)
from migrate_structure import F_SPEC

LC_META = {
    'Comp ID': ('comp_id', 'id', 'input', 'yes', '',
        'AUTO-ASSIGNED by onEdit trigger when Tenant is entered. API writers must supply IDs. Immutable, never reused.'),
    'Date Signed': ('date', 'date', 'input', 'yes', '',
        'Lease execution date.'),
    'Tenant': ('tenant', 'text', 'input', 'yes', '',
        'Tenant display name as signed. Variants map via Reference!VariantMap.'),
    'Company ID': ('company_id', 'id', 'input', 'yes', 'CompanyIds',
        'FK to Companies. AUTO-ASSIGNED with Comp ID.'),
    'Address': ('address', 'text', 'input', 'yes', '',
        'Building street address.'),
    'Submarket': ('submarket', 'text', 'input', 'yes', 'Submarkets',
        'Canonical submarket.'),
    'Building Class': ('bclass', 'text', 'input', 'no', 'BuildingClasses',
        'Building class.'),
    'Floor(s)': ('floors', 'text', 'input', 'no', '',
        'Floor(s) leased.'),
    'Condition': ('condition', 'text', 'input', 'no', 'Conditions',
        'Space condition at signing.'),
    'Deal Type': ('deal_type', 'text', 'input', 'no', 'DealTypes',
        'Deal structure.'),
    'Delivery Condition': ('delivery', 'text', 'input', 'no', 'DeliveryConditions',
        'Landlord delivery condition.'),
    'RSF': ('rsf', 'int', 'input', 'yes', '',
        'Rentable square feet.'),
    'Seats': ('seats', 'int', 'input', 'no', '',
        'Seat count. Blank = unknown (never 0).'),
    'Term (Years)': ('term', 'num', 'input', 'yes', '',
        'Lease term in years. Fractional allowed.'),
    'Rent P1 ($/RSF, mo 1-60)': ('rent_p1', 'rent', 'input', 'yes', '',
        'Tranche-1 rent, flat through month 60 (or term end if shorter).'),
    'Rent P2 ($/RSF, mo 61-120)': ('rent_p2', 'rent', 'input', 'no', '',
        'Tranche-2 rent, months 61-120. BLANK = carries P1 flat (no assumed escalation).'),
    'Rent P3 ($/RSF, mo 121+)': ('rent_p3', 'rent', 'input', 'no', '',
        'Tranche-3 rent, months 121+. BLANK = carries P2 flat.'),
    'Free Rent (months)': ('free_mo', 'num', 'input', 'no', '',
        'Free rent concession in months.'),
    'TI $/SF': ('ti_psf', 'rent', 'input', 'no', '',
        'TI allowance per SF. Blank = unknown (NER stays blank). Confirmed-zero on as-is deals is a real 0.'),
    'Latest Round Date': ('lr_date', 'date', 'calc', 'no', '',
        'Most recent round date (wired lookup — never type here; source of truth lives in the referenced tab) -> Funding Rounds.'),
    'Latest Round Type': ('lr_type', 'text', 'calc', 'no', '',
        'Type of most recent round; same-day rounds resolve to the larger amount (wired lookup — never type here; source of truth lives in the referenced tab) -> Funding Rounds.'),
    'Latest Round Amt ($M)': ('lr_amt', 'num', 'calc', 'no', '',
        'Amount of most recent round (wired lookup — never type here; source of truth lives in the referenced tab) -> Funding Rounds.'),
    'Total Tracked Funding ($M)': ('total_fund', 'num', 'calc', 'no', '',
        'Sum of tracked rounds (wired lookup — never type here; source of truth lives in the referenced tab) -> Company Metrics. Blank (never 0) when tracked rounds have no amounts. Semantic: tracked receipts, not researched narrative totals.'),
    'Company (canonical)': ('company', 'text', 'calc', 'no', '',
        'Canonical company name (wired lookup — never type here; source of truth lives in the referenced tab) -> Companies.'),
    'HQ City': ('hq', 'text', 'calc', 'no', '',
        'HQ city (wired lookup — never type here; source of truth lives in the referenced tab) -> Companies.'),
    'Benchmark Cohort': ('cohort', 'text', 'calc', 'no', '',
        'Benchmark cohort used to group the Dashboard table (wired lookup — never type here; source of truth lives in the referenced tab) -> Reference CohortTypes/CohortLabels. Thin stages are grouped: Series D/E/F/G + Late Stage Venture -> "Late Stage (D+)", IPO + reverse merger -> "Public". Add new round types to the Reference map, never here.'),
    'Floors on File': ('floors_n', 'int', 'calc', 'no', '',
        'How many Floor Detail rows exist for this comp. Blank = none; the comp is single-floor or its floors share one economic deal.'),
    'Detail RSF': ('detail_rsf', 'int', 'calc', 'no', '',
        'Sum of RSF across this comp’s Floor Detail rows. Must equal the typed RSF.'),
    'Detail Rent (wtd)': ('detail_rent', 'rent', 'calc', 'no', '',
        'RSF-weighted starting rent across the floors on file. Weighted, never a simple average.'),
    'Detail TI (wtd)': ('detail_ti', 'rent', 'calc', 'no', '',
        'RSF-weighted TI across the floors on file, over floors that carry a TI. This is what catches a concession dropped during hand-blending.'),
    'Blend Check': ('blend_check', 'text', 'qa', 'no', '',
        'OK, or the mismatches between the typed RSF/rent/TI and the Floor Detail blend (tolerances 1 SF, $0.50/RSF, $1/SF). A typed 0 or blank TI against a positive detail blend reads TI MISSING. Feeds Record Status and QA Notes.'),
    'Notes': ('notes', 'text', 'input', 'no', '',
        'Free-form deal notes.'),
    'Year 1 Rent ($)': ('y1_rent', 'usd', 'calc', 'no', '',
        'RSF x P1 rent.'),
    'Free Rent $ Value': ('free_val', 'usd', 'calc', 'no', '',
        '(Free months / 12) x P1 rent x RSF.'),
    'TI Allowance Total ($)': ('ti_total', 'usd', 'calc', 'no', '',
        'TI $/SF x RSF.'),
    'Projected Gross Rent (Term)': ('pgr', 'usd', 'calc', 'no', '',
        'Nominal rent over the term on FLAT tranches (no assumed escalation).'),
    'Avg Rate ($/RSF/Yr)': ('avg_rate', 'rent', 'calc', 'no', '',
        'Projected Gross / RSF / Term.'),
    'NER Annuity ($/RSF/Yr) @ 6%': ('ner', 'rent', 'calc', 'no', '',
        'Baseline NER per docs/NER_MODEL.md: monthly 6%/12 discounting, beg-of-month, flat tranches, free rent + TI nominal upfront, levelized. Blank when TI unknown.'),
    'Cost/Seat (Year 1)': ('cost_seat', 'usd', 'calc', 'no', '',
        'Year 1 Rent / Seats.'),
    'RSF / Seat': ('rsf_seat', 'num1', 'calc', 'no', '',
        'Density: RSF / Seats.'),
    'Rent-to-Raise (Yr 1) %': ('rent_raise', 'pct', 'calc', 'no', '',
        'Year 1 Rent / wired latest round.'),
    'Lease-to-Total-Funding %': ('l2tf', 'pct', 'calc', 'no', '',
        'Projected Gross / wired total tracked funding.'),
    'Months of Rent Covered': ('mo_cover', 'num1', 'calc', 'no', '',
        'Total tracked funding / monthly Year-1 rent.'),
    'Record Status': ('status', 'text', 'qa', 'no', 'RecordStatuses',
        'READY / NEEDS REVIEW / MISSING INPUTS — computed, never typed. NEEDS REVIEW also when Blend Check is not OK.'),
    'QA Notes': ('qa', 'text', 'qa', 'no', '',
        'Auto list of missing fields, plus any Floor Detail blend mismatch.'),
}

FD_META = {
    'Detail ID': ('detail_id', 'id', 'input', 'yes', '',
        'FD-#### . One row per floor (or per premises component) of a comp. Assign the next ID; immutable, never reused.'),
    'Comp ID': ('comp_id', 'id', 'input', 'yes', 'LeaseComps_IDs',
        'FK to Lease Comps. Every floor row belongs to exactly one comp.'),
    'Tenant': ('tenant', 'text', 'calc', 'no', '',
        'Looked up from Lease Comps by Comp ID (wired — never type here).'),
    'Floor': ('floor', 'text', 'input', 'yes', '',
        'Floor or premises label as it appears on the lease, e.g. E3, P8, E7-8.'),
    'RSF': ('rsf', 'int', 'input', 'yes', '',
        'Rentable square feet for this floor. The floors must sum to the comp’s typed RSF.'),
    'Rent P1 ($/RSF)': ('rent_p1', 'rent', 'input', 'no', '',
        'Starting rent for this floor. Blank = unknown, never 0.'),
    'TI $/SF': ('ti_psf', 'rent', 'input', 'no', '',
        'TI allowance for this floor. Blank = unknown; a confirmed-zero on an as-is floor is a real 0.'),
    'Free Rent (months)': ('free_mo', 'num', 'input', 'no', '',
        'Free rent on this floor, in months.'),
    'Share of Comp RSF': ('share', 'pct', 'calc', 'no', '',
        'This floor’s share of the comp’s detailed RSF.'),
    'Notes': ('notes', 'text', 'input', 'no', '',
        'Why this floor’s economics differ — condition, buildout, floor premium.'),
}

W = '(wired lookup — never type here; source of truth lives in the referenced tab)'
s = session()
ids = sheet_ids(s)
schema_id = ids['_Schema']


def block(tab, meta, width='BZ'):
    """Rows for one tab's _Schema block, in the tab's live column order."""
    hd = headers(s, tab, width)
    out, missing = [], []
    for header, letter in sorted(hd.items(), key=lambda kv: (len(kv[1]), kv[1])):
        if header not in meta:
            missing.append(f'{letter} {header!r}')
            continue
        key, typ, role, req, enum, desc = meta[header]
        formula = F_SPEC[letter].format(r='{r}') if tab == 'Lease Comps' and letter in F_SPEC else ''
        out.append([tab, letter, header, key, typ, role, req, enum, formula, desc])
    assert not missing, f'{tab}: no metadata for {", ".join(missing)} — add it to this script'
    return out


def write_block(tab, rows):
    cur = get_values(s, '_Schema!A1:J400', render='FORMATTED_VALUE')
    idx = [i for i, r in enumerate(cur) if r and r[0] == tab]
    want = [[str(c) for c in r] for r in rows]
    if idx:
        start, end = idx[0], idx[-1] + 1
        have = [[str(c) for c in (cur[i] + [''] * 10)[:10]] for i in range(start, end)]
        if have == want:
            print(f'_Schema {tab}: already current ({len(rows)} entries)')
            return 0
        n_old = end - start
        # Make room BEFORE writing: a grown block must not write over the next tab's block.
        if n_old < len(rows):
            batch_update(s, [{'insertDimension': {'range': {
                'sheetId': schema_id, 'dimension': 'ROWS',
                'startIndex': end, 'endIndex': end + len(rows) - n_old},
                'inheritFromBefore': True}}])
        r = s.put(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/'
                  f'_Schema!A{start + 1}:J{start + len(rows)}?valueInputOption=RAW',
                  json={'values': rows})
        assert r.status_code == 200, r.json()
        if n_old > len(rows):
            batch_update(s, [{'deleteDimension': {'range': {
                'sheetId': schema_id, 'dimension': 'ROWS',
                'startIndex': start + len(rows), 'endIndex': start + n_old}}}])
        print(f'_Schema {tab}: rewritten, {len(rows)} entries (was {n_old})')
    else:
        last = max((i for i, r in enumerate(cur) if r and r[0]), default=0) + 1
        r = s.put(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/'
                  f'_Schema!A{last + 1}:J{last + len(rows)}?valueInputOption=RAW',
                  json={'values': rows})
        assert r.status_code == 200, r.json()
        print(f'_Schema {tab}: appended, {len(rows)} entries')
    return len(rows)


lc_rows = block('Lease Comps', LC_META)
fd_rows = block('Floor Detail', FD_META)
assert len(lc_rows) == 45, f'Lease Comps: {len(lc_rows)} entries, expected 45'
assert len(fd_rows) == 10, f'Floor Detail: {len(fd_rows)} entries, expected 10'
n = write_block('Lease Comps', lc_rows) + write_block('Floor Detail', fd_rows)
if n:
    changelog(s, 'SCHEMA UPDATE', 'Rewrote the _Schema blocks for Lease Comps (45 columns: '
              'identity / premises / deal terms / wired funding / wired floor detail / notes / '
              'economics / governance) and Floor Detail (10 columns).', n)

# --- Dashboard: the benchmark table is owned by cohorts.py — verify, do not manage.
hdr = get_values(s, "'Dashboard'!A13:H13", render='FORMATTED_VALUE')
hdr = hdr[0] if hdr else []
anchor = get_values(s, "'Dashboard'!A14", render='FORMULA')
anchor = anchor[0][0] if anchor and anchor[0] else ''
ok = any(h in hdr for h in ('Median RSF', 'Med RSF')) and 'CohortOrder' in str(anchor)
print('Dashboard benchmark table:', 'cohort-driven, headers current — OK' if ok else
      f'UNEXPECTED — run cohorts.py (headers={hdr!r})')
if not ok:
    sys.exit(1)

summary, fails = qa_status(s)
print('QA:', summary, '| failing:', fails or 'none')
if fails:
    print('QA NOT ALL PASS — not final')
    sys.exit(1)
