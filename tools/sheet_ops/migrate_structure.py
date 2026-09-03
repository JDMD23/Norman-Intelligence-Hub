"""Lease Comps v4 structural migration (docs/LEASE_COMPS_DESIGN.md, owner-approved 2026-09-02).

Re-runnable: on a pre-v4 tab it performs the column surgery, then headers/formulas/vocab;
on a half-migrated tab (surgery done, headers missing) it resumes at headers; on a migrated
tab it only re-syncs formula columns that drifted from F_SPEC (receipted as FORMULA PATCH).
A full pre-migration copy exists in the visible tab LC_BACKUP_2026-09-02.
"""
from common import session, sheet_ids, named_ranges, batch_update, values_batch, get_values, changelog

s = session()
ids = sheet_ids(s)
lc, ref = ids['Lease Comps'], ids['Reference']

hdr = get_values(s, "'Lease Comps'!A1:AT1", render='FORMATTED_VALUE')[0]
already_migrated = 'Comp Source' in hdr
# Resumable: if the column surgery already happened (41 cols, blank T/U, funding
# block starting at V) skip straight to headers/formulas.
structure_done = (len(hdr) == 41 and hdr[19] == '' and hdr[20] == ''
                  and hdr[21].startswith('Latest Round Date'))
if not already_migrated and not structure_done:
    assert len(hdr) == 46 and hdr[19].startswith('Latest Round Date'), \
        f'unexpected layout: {len(hdr)} cols, col T header: {hdr[19]!r}'

def cols(a, b):
    return {'sheetId': lc, 'dimension': 'COLUMNS', 'startIndex': a, 'endIndex': b}


F_SPEC = {
    'V': '=IF($D{r}="","",IF(COUNTIF(FundingRounds_CompanyIds,$D{r})=0,"",'
         'MAXIFS(FundingRounds_Dates,FundingRounds_CompanyIds,$D{r})))',
    # Sort: date desc, then amount desc — same-day rounds (e.g. a seed + Series A
    # disclosed together) surface the larger primary, matching the audit convention.
    'W': '=IF(OR($D{r}="",$V{r}=""),"",IFERROR(INDEX(SORT(FILTER({{FundingRounds_Dates,'
         'FundingRounds_Types,FundingRounds_Amounts}},FundingRounds_CompanyIds=$D{r}),'
         '1,FALSE,3,FALSE),1,2),""))',
    'X': '=IF(OR($D{r}="",$V{r}=""),"",IFERROR(LET(a,INDEX(SORT(FILTER({{FundingRounds_Dates,'
         'FundingRounds_Amounts}},FundingRounds_CompanyIds=$D{r}),1,FALSE,2,FALSE),1,2),'
         'IF(a=0,"",a)),""))',
    'Y': '=IF($D{r}="","",IFERROR(LET(t,INDEX(\'Company Metrics\'!$M:$M,'
         'MATCH($D{r},\'Company Metrics\'!$A:$A,0)),IF(OR(t="",t=0),"",t)),""))',
    'Z': '=IF($D{r}="","",IFERROR(INDEX(Companies!$B:$B,'
         'MATCH($D{r},Companies!$A:$A,0)),"UNKNOWN ID"))',
    'AA': '=IF($D{r}="","",IFERROR(LET(h,INDEX(Companies!$G:$G,'
          'MATCH($D{r},Companies!$A:$A,0)),IF(h=0,"",h)),""))',
    'AB': '=IF($C{r}="","",IF($W{r}="","No Funding Data",'
          'IFERROR(INDEX(CohortLabels,MATCH($W{r},CohortTypes,0)),"Stage Unknown")))',
    'AG': '=IF(OR($L{r}="",$N{r}="",$O{r}=""),"",LET(nmo,ROUND($N{r}*12,0),rz,$O{r},'
          'rsix,IF($P{r}="",rz,$P{r}),relev,IF($Q{r}="",rsix,$Q{r}),mA,MIN(nmo,60),'
          'mB,MIN(MAX(nmo-60,0),60),mC,MAX(nmo-120,0),$L{r}*(rz*mA+rsix*mB+relev*mC)/12))',
    'AH': '=IF(OR($AG{r}="",$L{r}="",$N{r}=""),"",$AG{r}/$L{r}/$N{r})',
    'AL': '=IF(OR($AD{r}="",$X{r}=""),"",$AD{r}/($X{r}*1000000))',
    'AM': '=IF(OR($AG{r}="",$Y{r}="",$Y{r}=0),"",$AG{r}/($Y{r}*1000000))',
    'AN': '=IF(OR($Y{r}="",$AD{r}="",$AD{r}=0),"",($Y{r}*1000000)/($AD{r}/12))',
    'AO': '=IF($C{r}="","",IF(OR($A{r}="",$L{r}="",$N{r}="",$O{r}="",$B{r}="",$F{r}=""),'
          '"MISSING INPUTS",IF(OR($M{r}="",$S{r}=""),"NEEDS REVIEW",'
          'IF(AND($U{r}<>"",$U{r}<TODAY()-180),"STALE - REVERIFY","READY"))))',
    'AP': '=IF($C{r}="","",TEXTJOIN("; ",TRUE,IF($A{r}="","MISSING COMP ID",""),'
          'IF($L{r}="","MISSING RSF",""),IF($N{r}="","MISSING TERM",""),'
          'IF($O{r}="","MISSING STARTING RENT",""),IF($B{r}="","MISSING DATE",""),'
          'IF($F{r}="","MISSING SUBMARKET",""),IF($M{r}="","SEATS UNKNOWN",""),'
          'IF($S{r}="","TI UNKNOWN - NER BLANK",""),'
          'IF(AND($U{r}<>"",$U{r}<TODAY()-180),"VERIFIED >6 MO AGO","")))',
}


# Stage 1: structure.
#  - insert 2 input cols before idx19 (new T=Comp Source, U=Verified Date)
#  - old funding block shifts to V..AC; convert V-Y in place to wired lookups,
#    Z (investors) -> canonical company wire, AA (cb url) -> HQ wire,
#    delete AB (founded) + AC (old hq) so notes/calcs return to original positions
#  - drop retired calc cols (right-to-left): tenure, nertc, y1/total-funding, l2lr, y6-rent
if already_migrated:
    print('already migrated — checking wired/computed formulas are current')
elif structure_done:
    print('structure already at v4 layout — skipping column surgery')
else:
    batch_update(s, [{'insertDimension': {'range': cols(19, 21), 'inheritFromBefore': False}}])
    print('inserted Comp Source / Verified Date')
    batch_update(s, [{'deleteDimension': {'range': cols(27, 29)}}])
    print('removed founded + old hq input columns (now wired from Companies)')
    batch_update(s, [
        {'deleteDimension': {'range': cols(43, 44)}},   # tenure
        {'deleteDimension': {'range': cols(42, 43)}},   # nertc
        {'deleteDimension': {'range': cols(40, 41)}},   # y1-to-total-funding
        {'deleteDimension': {'range': cols(38, 39)}},   # lease-to-latest-round
        {'deleteDimension': {'range': cols(29, 30)}},   # y6 rent $
    ])
    print('removed 5 retired calc columns')

# Stage 2: headers + formulas + Reference vocab
if already_migrated:
    # Re-run: rewrite only the formula columns whose row-2 formula drifted from spec
    # (formula fixes land here so the script stays the single source of truth).
    current = get_values(s, "'Lease Comps'!A2:AP2", render='FORMULA')[0]
    drift = []
    for c, tpl in F_SPEC.items():
        i = 0
        for ch in c:
            i = i * 26 + ord(ch) - 64
        if (current[i - 1] if i - 1 < len(current) else '') != tpl.format(r=2):
            drift.append(c)
    if drift:
        res = values_batch(s, [{'range': f"'Lease Comps'!{c}2:{c}1207",
                                'values': [[F_SPEC[c].format(r=row)] for row in range(2, 1208)]}
                               for c in drift])
        changelog(s, 'FORMULA PATCH', 'Lease Comps v4 wired/computed columns re-synced to '
                  f'migrate_structure.py spec: {", ".join(drift)}.', '1206')
        print('formula drift patched in columns', drift, '| cells:', res.get('totalUpdatedCells'))
    else:
        print('formulas current — nothing to do')
    raise SystemExit(0)

headers = {
    'O1': 'Rent P1 ($/RSF, mo 1-60)', 'P1': 'Rent P2 ($/RSF, mo 61-120)',
    'Q1': 'Rent P3 ($/RSF, mo 121+)', 'T1': 'Comp Source', 'U1': 'Verified Date',
    'V1': 'Latest Round Date', 'W1': 'Latest Round Type', 'X1': 'Latest Round Amt ($M)',
    'Y1': 'Total Tracked Funding ($M)', 'Z1': 'Company (canonical)', 'AA1': 'HQ City',
    'AF1': 'Projected Gross Rent (Term)',
}
data = [{'range': f"'Lease Comps'!{a}", 'values': [[v]]} for a, v in headers.items()]

F = F_SPEC
for col, tpl in F.items():
    data.append({'range': f"'Lease Comps'!{col}2:{col}1207",
                 'values': [[tpl.format(r=row)] for row in range(2, 1208)]})
data.append({'range': 'Reference!M1:M6', 'values': [
    ['CompSources'], ['CoStar'], ['CBRE'], ['Broker Intel'], ['Press'], ['Direct/Landlord']]})
data.append({'range': 'Reference!H5', 'values': [['STALE - REVERIFY']]})
res = values_batch(s, data)
print('headers + wired formulas + vocab written | cells:', res.get('totalUpdatedCells'))

# Stage 3: named ranges + input validation
nrs = named_ranges(s)
reqs = []
if 'CompSources' not in nrs:
    reqs.append({'addNamedRange': {'namedRange': {'name': 'CompSources', 'range': {
        'sheetId': ref, 'startRowIndex': 1, 'endRowIndex': 15,
        'startColumnIndex': 12, 'endColumnIndex': 13}}}})
rs = nrs.get('RecordStatuses')
if rs and rs['range'].get('endRowIndex', 0) < 5:
    reqs.append({'updateNamedRange': {'namedRange': {**rs, 'range': {
        **rs['range'], 'endRowIndex': 5}}, 'fields': 'range'}})
reqs.append({'setDataValidation': {
    'range': {'sheetId': lc, 'startRowIndex': 1, 'endRowIndex': 1207,
              'startColumnIndex': 19, 'endColumnIndex': 20},
    'rule': {'condition': {'type': 'ONE_OF_RANGE',
                           'values': [{'userEnteredValue': '=CompSources'}]},
             'strict': False, 'showCustomUi': True}}})
reqs.append({'setDataValidation': {
    'range': {'sheetId': lc, 'startRowIndex': 1, 'endRowIndex': 1207,
              'startColumnIndex': 20, 'endColumnIndex': 21},
    'rule': {'condition': {'type': 'DATE_IS_VALID'}, 'strict': False}}})
batch_update(s, reqs)
print('named ranges + validation set')

changelog(s, 'STRUCTURE MIGRATION',
          'Lease Comps v4 per docs/LEASE_COMPS_DESIGN.md: added Comp Source/Verified Date inputs; '
          'funding+HQ columns (V-AA) converted to wired lookups from Funding Rounds/Company Metrics/'
          'Companies; removed typed founded/hq/investors/cb-url and 5 retired calc columns; '
          'Projected Gross rebuilt on flat tranches; status adds STALE - REVERIFY. '
          'Backup: tab LC_BACKUP_2026-09-02.', '1206')
print('changelog receipt appended')
