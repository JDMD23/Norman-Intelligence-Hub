"""Lease Comps v4 structural migration (docs/LEASE_COMPS_DESIGN.md, owner-approved 2026-09-02).

Idempotence guard: refuses to run if the tab already has the v4 header set.
A full pre-migration copy exists in the visible tab LC_BACKUP_2026-09-02.
"""
from common import session, sheet_ids, named_ranges, batch_update, values_batch, get_values, changelog

s = session()
ids = sheet_ids(s)
lc, ref = ids['Lease Comps'], ids['Reference']

hdr = get_values(s, "'Lease Comps'!A1:AT1", render='FORMATTED_VALUE')[0]
if 'Comp Source' in hdr:
    raise SystemExit('Already migrated — v4 headers present. Aborting.')
assert hdr[19].startswith('Latest Round Date'), f'unexpected col T header: {hdr[19]}'

def cols(a, b):
    return {'sheetId': lc, 'dimension': 'COLUMNS', 'startIndex': a, 'endIndex': b}

# Stage 1: structure.
#  - insert 2 input cols before idx19 (new T=Comp Source, U=Verified Date)
#  - old funding block shifts to V..AC; convert V-Y in place to wired lookups,
#    Z (investors) -> canonical company wire, AA (cb url) -> HQ wire,
#    delete AB (founded) + AC (old hq) so notes/calcs return to original positions
#  - drop retired calc cols (right-to-left): tenure, nertc, y1/total-funding, l2lr, y6-rent
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
headers = {
    'O1': 'Rent P1 ($/RSF, mo 1-60)', 'P1': 'Rent P2 ($/RSF, mo 61-120)',
    'Q1': 'Rent P3 ($/RSF, mo 121+)', 'T1': 'Comp Source', 'U1': 'Verified Date',
    'V1': 'Latest Round Date', 'W1': 'Latest Round Type', 'X1': 'Latest Round Amt ($M)',
    'Y1': 'Total Tracked Funding ($M)', 'Z1': 'Company (canonical)', 'AA1': 'HQ City',
    'AF1': 'Projected Gross Rent (Term)',
}
data = [{'range': f"'Lease Comps'!{a}", 'values': [[v]]} for a, v in headers.items()]

F = {
    'V': '=IF($D{r}="","",IF(COUNTIF(FundingRounds_CompanyIds,$D{r})=0,"",'
         'MAXIFS(FundingRounds_Dates,FundingRounds_CompanyIds,$D{r})))',
    'W': '=IF(OR($D{r}="",$V{r}=""),"",IFERROR(INDEX(SORT(FILTER({FundingRounds_Dates,'
         'FundingRounds_Types},FundingRounds_CompanyIds=$D{r}),1,FALSE),1,2),""))',
    'X': '=IF(OR($D{r}="",$V{r}=""),"",IFERROR(LET(a,INDEX(SORT(FILTER({FundingRounds_Dates,'
         'FundingRounds_Amounts},FundingRounds_CompanyIds=$D{r}),1,FALSE),1,2),IF(a=0,"",a)),""))',
    'Y': '=IF($D{r}="","",IFERROR(LET(t,INDEX(\'Company Metrics\'!$M:$M,'
         'MATCH($D{r},\'Company Metrics\'!$A:$A,0)),IF(t="","",t)),""))',
    'Z': '=IF($D{r}="","",IFERROR(INDEX(Companies!$B:$B,'
         'MATCH($D{r},Companies!$A:$A,0)),"UNKNOWN ID"))',
    'AA': '=IF($D{r}="","",IFERROR(LET(h,INDEX(Companies!$G:$G,'
          'MATCH($D{r},Companies!$A:$A,0)),IF(h=0,"",h)),""))',
    'AF': '=IF(OR($L{r}="",$N{r}="",$O{r}=""),"",LET(nmo,ROUND($N{r}*12,0),rz,$O{r},'
          'rsix,IF($P{r}="",rz,$P{r}),relev,IF($Q{r}="",rsix,$Q{r}),mA,MIN(nmo,60),'
          'mB,MIN(MAX(nmo-60,0),60),mC,MAX(nmo-120,0),$L{r}*(rz*mA+rsix*mB+relev*mC)/12))',
    'AG': '=IF(OR($AF{r}="",$L{r}="",$N{r}=""),"",$AF{r}/$L{r}/$N{r})',
    'AK': '=IF(OR($AC{r}="",$X{r}=""),"",$AC{r}/($X{r}*1000000))',
    'AL': '=IF(OR($AF{r}="",$Y{r}=""),"",$AF{r}/($Y{r}*1000000))',
    'AM': '=IF(OR($Y{r}="",$AC{r}="",$AC{r}=0),"",($Y{r}*1000000)/($AC{r}/12))',
    'AN': '=IF($C{r}="","",IF(OR($A{r}="",$L{r}="",$N{r}="",$O{r}="",$B{r}="",$F{r}=""),'
          '"MISSING INPUTS",IF(OR($M{r}="",$S{r}=""),"NEEDS REVIEW",'
          'IF(AND($U{r}<>"",$U{r}<TODAY()-180),"STALE - REVERIFY","READY"))))',
    'AO': '=IF($C{r}="","",TEXTJOIN("; ",TRUE,IF($A{r}="","MISSING COMP ID",""),'
          'IF($L{r}="","MISSING RSF",""),IF($N{r}="","MISSING TERM",""),'
          'IF($O{r}="","MISSING STARTING RENT",""),IF($B{r}="","MISSING DATE",""),'
          'IF($F{r}="","MISSING SUBMARKET",""),IF($M{r}="","SEATS UNKNOWN",""),'
          'IF($S{r}="","TI UNKNOWN - NER BLANK",""),'
          'IF(AND($U{r}<>"",$U{r}<TODAY()-180),"VERIFIED >6 MO AGO","")))',
}
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
