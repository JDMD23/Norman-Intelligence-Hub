"""Finalize Lease Comps v4: rewrite the _Schema block to match the new layout, make sure
the Dashboard stage table has room for the wired round-type vocabulary, then gate on QA
(exit non-zero unless every check is PASS). Run after migrate_structure.py and verify_wire.py."""
import re
import sys

from common import (session, sheet_ids, batch_update, values_batch, get_values, changelog,
                    qa_status, SID, typed_rows)

s = session()
ids = sheet_ids(s)
schema_id, dash_id = ids['_Schema'], ids['Dashboard']

rows = get_values(s, '_Schema!A1:J200', render='FORMATTED_VALUE')
start = next(i for i, r in enumerate(rows) if r and r[0] == 'Lease Comps')
end = start
while end < len(rows) and rows[end] and rows[end][0] == 'Lease Comps':
    end += 1
old_n = end - start
print(f'_Schema Lease Comps block: rows {start+1}..{end} ({old_n} entries)')

W = '(wired lookup — never type here; source of truth lives in the referenced tab)'
SPEC = [
    ('A', 'Comp ID', 'comp_id', 'id', 'input', 'yes', '', '', 'AUTO-ASSIGNED by onEdit trigger when Tenant is entered. API writers must supply IDs. Immutable, never reused.'),
    ('B', 'Date Signed', 'date', 'date', 'input', 'yes', '', '', 'Lease execution date.'),
    ('C', 'Tenant', 'tenant', 'text', 'input', 'yes', '', '', 'Tenant display name as signed. Variants map via Reference!VariantMap.'),
    ('D', 'Company ID', 'company_id', 'id', 'input', 'yes', 'CompanyIds', '', 'FK to Companies. AUTO-ASSIGNED with Comp ID.'),
    ('E', 'Address', 'address', 'text', 'input', 'yes', '', '', 'Building street address.'),
    ('F', 'Submarket', 'submarket', 'text', 'input', 'yes', 'Submarkets', '', 'Canonical submarket.'),
    ('G', 'Building Class', 'bclass', 'text', 'input', 'no', 'BuildingClasses', '', 'Building class.'),
    ('H', 'Floor(s)', 'floors', 'text', 'input', 'no', '', '', 'Floor(s) leased.'),
    ('I', 'Condition', 'condition', 'text', 'input', 'no', 'Conditions', '', 'Space condition at signing.'),
    ('J', 'Deal Type', 'deal_type', 'text', 'input', 'no', 'DealTypes', '', 'Deal structure.'),
    ('K', 'Delivery Condition', 'delivery', 'text', 'input', 'no', 'DeliveryConditions', '', 'Landlord delivery condition.'),
    ('L', 'RSF', 'rsf', 'int', 'input', 'yes', '', '', 'Rentable square feet.'),
    ('M', 'Seats', 'seats', 'int', 'input', 'no', '', '', 'Seat count. Blank = unknown (never 0).'),
    ('N', 'Term (Years)', 'term', 'num', 'input', 'yes', '', '', 'Lease term in years. Fractional allowed.'),
    ('O', 'Rent P1 ($/RSF, mo 1-60)', 'rent_p1', 'rent', 'input', 'yes', '', '', 'Tranche-1 rent, flat through month 60 (or term end if shorter).'),
    ('P', 'Rent P2 ($/RSF, mo 61-120)', 'rent_p2', 'rent', 'input', 'no', '', '', 'Tranche-2 rent, months 61-120. BLANK = carries P1 flat (no assumed escalation).'),
    ('Q', 'Rent P3 ($/RSF, mo 121+)', 'rent_p3', 'rent', 'input', 'no', '', '', 'Tranche-3 rent, months 121+. BLANK = carries P2 flat.'),
    ('R', 'Free Rent (months)', 'free_mo', 'num', 'input', 'no', '', '', 'Free rent concession in months.'),
    ('S', 'TI $/SF', 'ti_psf', 'rent', 'input', 'no', '', '', 'TI allowance per SF. Blank = unknown (NER stays blank). Confirmed-zero on as-is deals is a real 0.'),
    ('T', 'Comp Source', 'source', 'text', 'input', 'no', 'CompSources', '', 'Where this comp came from.'),
    ('U', 'Verified Date', 'verified', 'date', 'input', 'no', '', '', 'When this comp was last verified. >6 months old flips status to STALE - REVERIFY.'),
    ('V', 'Latest Round Date', 'lr_date', 'date', 'calc', 'no', '', '=IF($D{r}="","",IF(COUNTIF(FundingRounds_CompanyIds,$D{r})=0,"",MAXIFS(FundingRounds_Dates,FundingRounds_CompanyIds,$D{r})))', f'Most recent round date {W} -> Funding Rounds.'),
    ('W', 'Latest Round Type', 'lr_type', 'text', 'calc', 'no', '', '=IF(OR($D{r}="",$V{r}=""),"",IFERROR(INDEX(SORT(FILTER({FundingRounds_Dates,FundingRounds_Types,FundingRounds_Amounts},FundingRounds_CompanyIds=$D{r}),1,FALSE,3,FALSE),1,2),""))', f'Type of most recent round; same-day rounds resolve to the larger amount {W} -> Funding Rounds.'),
    ('X', 'Latest Round Amt ($M)', 'lr_amt', 'num', 'calc', 'no', '', '=IF(OR($D{r}="",$V{r}=""),"",IFERROR(LET(a,INDEX(SORT(FILTER({FundingRounds_Dates,FundingRounds_Amounts},FundingRounds_CompanyIds=$D{r}),1,FALSE,2,FALSE),1,2),IF(a=0,"",a)),""))', f'Amount of most recent round {W} -> Funding Rounds.'),
    ('Y', 'Total Tracked Funding ($M)', 'total_fund', 'num', 'calc', 'no', '', "=IF($D{r}=\"\",\"\",IFERROR(LET(t,INDEX('Company Metrics'!$M:$M,MATCH($D{r},'Company Metrics'!$A:$A,0)),IF(OR(t=\"\",t=0),\"\",t)),\"\"))", f'Sum of tracked rounds {W} -> Company Metrics. Blank (never 0) when tracked rounds have no amounts. Semantic: tracked receipts, not researched narrative totals.'),
    ('Z', 'Company (canonical)', 'company', 'text', 'calc', 'no', '', '=IF($D{r}="","",IFERROR(INDEX(Companies!$B:$B,MATCH($D{r},Companies!$A:$A,0)),"UNKNOWN ID"))', f'Canonical company name {W} -> Companies.'),
    ('AA', 'HQ City', 'hq', 'text', 'calc', 'no', '', '=IF($D{r}="","",IFERROR(LET(h,INDEX(Companies!$G:$G,MATCH($D{r},Companies!$A:$A,0)),IF(h=0,"",h)),""))', f'HQ city {W} -> Companies.'),
    ('AB', 'Notes', 'notes', 'text', 'input', 'no', '', '', 'Free-form deal notes.'),
    ('AC', 'Year 1 Rent ($)', 'y1_rent', 'usd', 'calc', 'no', '', '=IF(OR(L{r}="",O{r}=""),"",L{r}*O{r})', 'RSF x P1 rent.'),
    ('AD', 'Free Rent $ Value', 'free_val', 'usd', 'calc', 'no', '', '=IF(OR(R{r}="",O{r}="",L{r}=""),"",R{r}/12*O{r}*L{r})', '(Free months / 12) x P1 rent x RSF.'),
    ('AE', 'TI Allowance Total ($)', 'ti_total', 'usd', 'calc', 'no', '', '=IF(OR(S{r}="",L{r}=""),"",S{r}*L{r})', 'TI $/SF x RSF.'),
    ('AF', 'Projected Gross Rent (Term)', 'pgr', 'usd', 'calc', 'no', '', '=IF(OR($L{r}="",$N{r}="",$O{r}=""),"",LET(nmo,ROUND($N{r}*12,0),rz,$O{r},rsix,IF($P{r}="",rz,$P{r}),relev,IF($Q{r}="",rsix,$Q{r}),mA,MIN(nmo,60),mB,MIN(MAX(nmo-60,0),60),mC,MAX(nmo-120,0),$L{r}*(rz*mA+rsix*mB+relev*mC)/12))', 'Nominal rent over the term on FLAT tranches (no assumed escalation).'),
    ('AG', 'Avg Rate ($/RSF/Yr)', 'avg_rate', 'rent', 'calc', 'no', '', '=IF(OR($AF{r}="",$L{r}="",$N{r}=""),"",$AF{r}/$L{r}/$N{r})', 'Projected Gross / RSF / Term.'),
    ('AH', 'NER Annuity ($/RSF/Yr) @ 6%', 'ner', 'rent', 'calc', 'no', '', '=IF(OR($N{r}="",$O{r}="",$S{r}=""),"",LET(nmo,ROUND($N{r}*12,0),im,0.06/12,rz,$O{r},rsix,IF($P{r}="",rz,$P{r}),relev,IF($Q{r}="",rsix,$Q{r}),mos,SEQUENCE(nmo),pvbeg,SUMPRODUCT(MAP(mos,LAMBDA(mm,IF(mm<=60,rz,IF(mm<=120,rsix,relev))/12*(1+im)^-(mm-1)))),afbeg,(1-(1+im)^-nmo)/im/12*(1+im),freemo,IF($R{r}="",0,$R{r}),ROUND(pvbeg/afbeg,2)-(freemo/12*rz+$S{r})/afbeg))', 'Baseline NER per docs/NER_MODEL.md: monthly 6%/12 discounting, beg-of-month, flat tranches, free rent + TI nominal upfront, levelized. Blank when TI unknown.'),
    ('AI', 'Cost/Seat (Year 1)', 'cost_seat', 'usd', 'calc', 'no', '', '=IF(OR(AC{r}="",M{r}="",M{r}=0),"",AC{r}/M{r})', 'Year 1 Rent / Seats.'),
    ('AJ', 'RSF / Seat', 'rsf_seat', 'num1', 'calc', 'no', '', '=IF(OR(L{r}="",M{r}="",M{r}=0),"",L{r}/M{r})', 'Density: RSF / Seats.'),
    ('AK', 'Rent-to-Raise (Yr 1) %', 'rent_raise', 'pct', 'calc', 'no', '', '=IF(OR($AC{r}="",$X{r}=""),"",$AC{r}/($X{r}*1000000))', 'Year 1 Rent / wired latest round.'),
    ('AL', 'Lease-to-Total-Funding %', 'l2tf', 'pct', 'calc', 'no', '', '=IF(OR($AF{r}="",$Y{r}="",$Y{r}=0),"",$AF{r}/($Y{r}*1000000))', 'Projected Gross / wired total tracked funding.'),
    ('AM', 'Months of Rent Covered', 'mo_cover', 'num1', 'calc', 'no', '', '=IF(OR($Y{r}="",$AC{r}="",$AC{r}=0),"",($Y{r}*1000000)/($AC{r}/12))', 'Total tracked funding / monthly Year-1 rent.'),
    ('AN', 'Record Status', 'status', 'text', 'qa', 'no', 'RecordStatuses', '=IF($C{r}="","",IF(OR($A{r}="",$L{r}="",$N{r}="",$O{r}="",$B{r}="",$F{r}=""),"MISSING INPUTS",IF(OR($M{r}="",$S{r}=""),"NEEDS REVIEW",IF(AND($U{r}<>"",$U{r}<TODAY()-180),"STALE - REVERIFY","READY"))))', 'READY / NEEDS REVIEW / MISSING INPUTS / STALE - REVERIFY (verified >6mo ago) — computed, never typed.'),
    ('AO', 'QA Notes', 'qa', 'text', 'qa', 'no', '', '(auto list incl. staleness)', 'Auto list of missing fields + staleness flag.'),
]
new_rows = [['Lease Comps'] + list(x) for x in SPEC]
assert len(new_rows) == 41

# overwrite block (only if it differs), then delete surplus rows
current = [[str(c) for c in r] + [''] * (10 - len(r)) for r in rows[start:end]]
if current == [[str(c) for c in r] for r in new_rows]:
    print('_Schema block already current — skipping')
else:
    r = s.put(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}'
              f'/values/_Schema!A{start+1}:J{start+len(new_rows)}'
              '?valueInputOption=RAW', json={'values': new_rows})
    assert r.status_code == 200, r.json()
    surplus = old_n - len(new_rows)
    if surplus > 0:
        batch_update(s, [{'deleteDimension': {'range': {
            'sheetId': schema_id, 'dimension': 'ROWS',
            'startIndex': start + len(new_rows), 'endIndex': start + old_n}}}])
    print(f'_Schema rewritten: {len(new_rows)} entries (removed {max(surplus,0)} surplus rows)')
    changelog(s, 'SCHEMA UPDATE', 'Rewrote _Schema Lease Comps block for v4 layout '
              '(41 columns: zones identity/premises/deal-terms/wired/economics/governance).', 41)

# --- Dashboard: the "benchmarks by last funding round" table. Column A spills one row per
#     distinct round type wired from Funding Rounds; columns B..G carry a per-row formula.
#     Keep STAGE_ROOM table rows (spill room) and make sure every row has the B..G formulas.
STAGE_ROOM = 30
d = [r[0] if r else '' for r in get_values(s, "'Dashboard'!A1:A300", render='FORMATTED_VALUE')]
hdr_row = d.index('Stage') + 1                                        # 1-based header row
anchor = hdr_row + 1                                                  # spill anchor row
typed_a = typed_rows(s, "'Dashboard'!A1:A300")                        # typed in column A only
nxt = min(r for r in typed_a if r > anchor)                           # next block (banner)
room = nxt - anchor
if room < STAGE_ROOM:
    batch_update(s, [{'insertDimension': {'range': {
        'sheetId': dash_id, 'dimension': 'ROWS', 'startIndex': nxt - 1,
        'endIndex': nxt - 1 + STAGE_ROOM - room}, 'inheritFromBefore': True}}])
    changelog(s, 'DASHBOARD LAYOUT', f'Inserted {STAGE_ROOM - room} rows under the stage '
              f'benchmark table (had {room}) so the wired round-type list can spill.', '')
    print(f'Dashboard: inserted {STAGE_ROOM - room} rows under the stage table')
    room = STAGE_ROOM
tmpl = get_values(s, f"'Dashboard'!B{anchor}:G{anchor}", render='FORMULA')[0]
assert len(tmpl) == 6 and all(str(t).startswith('=') for t in tmpl), tmpl
pat = re.compile(r'(\$?[A-G])' + str(anchor) + r'(?![0-9])')
want = [[pat.sub(lambda m: m.group(1) + str(r), t) for t in tmpl] for r in range(anchor, anchor + room)]
have = get_values(s, f"'Dashboard'!B{anchor}:G{anchor + room - 1}", render='FORMULA')
have = [list(r) + [''] * (6 - len(r)) for r in have] + [[''] * 6] * (room - len(have))
fix = [i for i in range(room) if have[i] != want[i]]
if fix:
    values_batch(s, [{'range': f"'Dashboard'!B{anchor + i}:G{anchor + i}", 'values': [want[i]]}
                     for i in fix])
    changelog(s, 'DASHBOARD LAYOUT', f'Filled stage-table row formulas (B..G) on {len(fix)} of '
              f'{room} table rows so every wired round type shows its benchmarks.', len(fix))
    print(f'Dashboard: stage table {room} rows; row formulas written on {len(fix)}')
else:
    print(f'Dashboard: stage table has {room} rows, all row formulas present — OK')

summary, fails = qa_status(s)
print('QA:', summary, '| failing:', fails or 'none')
if fails:
    print('QA NOT ALL PASS — migration not final')
    sys.exit(1)
