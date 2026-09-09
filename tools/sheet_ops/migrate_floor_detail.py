"""Add the Floor Detail tab and the blend-check columns on Lease Comps.

Why: a multi-floor deal whose floors carry different economics was being hand-blended into
one row, and concessions were getting lost — LC-0103 Moment (325 Hudson, E3 + E10) reads
TI $0, which overstates its NER by roughly $15/SF. Rent blending is off by pennies; a
dropped TI is worth $10-20/SF, so the sheet now stores the per-floor detail and checks the
typed blend against it.

Model: one comp is still one row (benchmarks count transactions, so the grain does not move).
Floors live on their own tab and link back by Comp ID, exactly as Funding Rounds links to a
company. Only deals whose floors differ need rows there; single-floor comps are untouched and
their check columns stay blank.

Layout after this runs (45 columns): A-S inputs, T-Z wired funding/company,
AA-AD wired floor detail, AE blend check, AF Notes, AG-AQ economics, AR-AS governance.

Idempotent: no-op once 'Floors on File' is present.
"""
import sys

from common import (session, sheet_ids, named_ranges, batch_update, values_batch, get_values,
                    changelog, qa_status, SID)

FD_ROWS = 600          # detail rows 2..600; keeps the weighted-average SUMPRODUCTs cheap
LC_ROWS = 1207

s = session()
ids = sheet_ids(s)
lc = ids['Lease Comps']
hdr = get_values(s, "'Lease Comps'!A1:AZ1", render='FORMATTED_VALUE')[0]
if 'Floors on File' in hdr:
    print('Floor Detail columns already present — nothing to do')
    sys.exit(0)
assert len(hdr) == 40 and hdr[25] == 'Benchmark Cohort' and hdr[26] == 'Notes', \
    f'unexpected layout ({len(hdr)} cols): Z={hdr[25]!r} AA={hdr[26]!r}'

# ---------------------------------------------------------------- 1. the Floor Detail tab
FD_HEADERS = ['Detail ID', 'Comp ID', 'Tenant', 'Floor', 'RSF', 'Rent P1 ($/RSF)', 'TI $/SF',
              'Free Rent (months)', 'Share of Comp RSF', 'Notes']
FD_TENANT = ('=IF($B{r}="","",IFERROR(INDEX(LeaseComps_Tenants,MATCH($B{r},LeaseComps_IDs,0)),'
             '"UNKNOWN COMP"))')
FD_SHARE = ('=IF(OR($B{r}="",$E{r}=""),"",LET(t,SUMIF(FloorDetail_CompIds,$B{r},FloorDetail_RSF),'
            'IF(t=0,"",$E{r}/t)))')

if 'Floor Detail' not in ids:
    batch_update(s, [{'addSheet': {'properties': {
        'title': 'Floor Detail', 'index': 5,
        'gridProperties': {'rowCount': FD_ROWS + 20, 'columnCount': 10, 'frozenRowCount': 1,
                              'frozenColumnCount': 3}}}}])
    ids = sheet_ids(s)
    print('created tab "Floor Detail"')
fd = ids['Floor Detail']
values_batch(s, [
    {'range': "'Floor Detail'!A1:J1", 'values': [FD_HEADERS]},
    {'range': f"'Floor Detail'!C2:C{FD_ROWS}", 'values': [[FD_TENANT.format(r=r)] for r in range(2, FD_ROWS + 1)]},
    {'range': f"'Floor Detail'!I2:I{FD_ROWS}", 'values': [[FD_SHARE.format(r=r)] for r in range(2, FD_ROWS + 1)]},
])
print(f'Floor Detail: headers + wired Tenant + Share of Comp RSF through row {FD_ROWS}')

# ---------------------------------------------------------------- 2. named ranges on Floor Detail
nrs = named_ranges(s)


def nr(name, sheet, col, r1=1, r2=None):
    rng = {'sheetId': sheet, 'startRowIndex': r1, 'endRowIndex': r2 or FD_ROWS,
           'startColumnIndex': col, 'endColumnIndex': col + 1}
    if name in nrs:
        return {'updateNamedRange': {'namedRange': {'namedRangeId': nrs[name]['namedRangeId'],
                                                    'name': name, 'range': rng}, 'fields': 'range'}}
    return {'addNamedRange': {'namedRange': {'name': name, 'range': rng}}}


batch_update(s, [nr('FloorDetail_IDs', fd, 0), nr('FloorDetail_CompIds', fd, 1),
                 nr('FloorDetail_RSF', fd, 4), nr('FloorDetail_Rents', fd, 5),
                 nr('FloorDetail_TIs', fd, 6)])
print('named ranges: FloorDetail_IDs / CompIds / RSF / Rents / TIs')

# ---------------------------------------------------------------- 3. five columns on Lease Comps
batch_update(s, [{'insertDimension': {'range': {'sheetId': lc, 'dimension': 'COLUMNS',
                                                'startIndex': 26, 'endIndex': 31},
                                      'inheritFromBefore': False}}])
print('inserted AA:AE (everything from Notes shifted right by five)')

F = {
    'AA': '=IF($A{r}="","",LET(n,COUNTIF(FloorDetail_CompIds,$A{r}),IF(n=0,"",n)))',
    'AB': '=IF(OR($A{r}="",$AA{r}=""),"",SUMIF(FloorDetail_CompIds,$A{r},FloorDetail_RSF))',
    'AC': '=IF(OR($A{r}="",$AA{r}=""),"",LET(m,(FloorDetail_CompIds=$A{r})*(FloorDetail_Rents<>""),'
          'd,SUMPRODUCT(m*N(FloorDetail_RSF)),IF(d=0,"",'
          'SUMPRODUCT(m*N(FloorDetail_RSF)*N(FloorDetail_Rents))/d)))',
    'AD': '=IF(OR($A{r}="",$AA{r}=""),"",LET(m,(FloorDetail_CompIds=$A{r})*(FloorDetail_TIs<>""),'
          'd,SUMPRODUCT(m*N(FloorDetail_RSF)),IF(d=0,"",'
          'SUMPRODUCT(m*N(FloorDetail_RSF)*N(FloorDetail_TIs))/d)))',
    'AE': '=IF(OR($A{r}="",$AA{r}=""),"",LET(t,TEXTJOIN("; ",TRUE,'
          'IF(AND($AB{r}<>"",$L{r}<>"",ABS($L{r}-$AB{r})>1),"RSF MISMATCH",""),'
          'IF(AND($AC{r}<>"",$O{r}<>"",ABS($O{r}-$AC{r})>0.5),"RENT MISMATCH",""),'
          'IF(AND($AD{r}<>"",$AD{r}>0,OR($S{r}="",$S{r}=0)),"TI MISSING",'
          'IF(AND($AD{r}<>"",$S{r}<>"",ABS($S{r}-$AD{r})>1),"TI MISMATCH",""))),'
          'IF(t="","OK",t)))',
    # governance rewritten so a blend problem reaches Record Status and QA Notes
    'AR': '=IF($C{r}="","",IF(OR($A{r}="",$L{r}="",$N{r}="",$O{r}="",$B{r}="",$F{r}=""),'
          '"MISSING INPUTS",IF(OR($M{r}="",$S{r}="",AND($AE{r}<>"",$AE{r}<>"OK")),'
          '"NEEDS REVIEW","READY")))',
    'AS': '=IF($C{r}="","",TEXTJOIN("; ",TRUE,IF($A{r}="","MISSING COMP ID",""),'
          'IF($L{r}="","MISSING RSF",""),IF($N{r}="","MISSING TERM",""),'
          'IF($O{r}="","MISSING STARTING RENT",""),IF($B{r}="","MISSING DATE",""),'
          'IF($F{r}="","MISSING SUBMARKET",""),IF($M{r}="","SEATS UNKNOWN",""),'
          'IF($S{r}="","TI UNKNOWN - NER BLANK",""),'
          'IF(AND($AE{r}<>"",$AE{r}<>"OK"),"FLOOR DETAIL: "&$AE{r},"")))',
}
HEADERS = {'AA1': 'Floors on File', 'AB1': 'Detail RSF', 'AC1': 'Detail Rent (wtd)',
           'AD1': 'Detail TI (wtd)', 'AE1': 'Blend Check'}
data = [{'range': f"'Lease Comps'!{a}", 'values': [[v]]} for a, v in HEADERS.items()]
for col, tpl in F.items():
    data.append({'range': f"'Lease Comps'!{col}2:{col}{LC_ROWS}",
                 'values': [[tpl.format(r=r)] for r in range(2, LC_ROWS + 1)]})
res = values_batch(s, data)
print('AA:AE headers + formulas, governance rewritten | cells:', res.get('totalUpdatedCells'))

# ---------------------------------------------------------------- 4. named range + validation
nrs = named_ranges(s)
reqs = [nr('LeaseComps_BlendCheck', lc, 30, 1, LC_ROWS)]
for name, col in [('LeaseComps_Status', 43), ('LeaseComps_Cohorts', 25)]:
    if name in nrs:                          # Sheets shifts these itself; assert rather than move
        got = nrs[name]['range']['startColumnIndex']
        assert got == col, f'{name} at column {got}, expected {col}'
reqs.append({'setDataValidation': {
    'range': {'sheetId': fd, 'startRowIndex': 1, 'endRowIndex': FD_ROWS,
              'startColumnIndex': 1, 'endColumnIndex': 2},
    'rule': {'condition': {'type': 'ONE_OF_RANGE',
                           'values': [{'userEnteredValue': '=LeaseComps_IDs'}]},
             'strict': False, 'showCustomUi': True}}})
batch_update(s, reqs)
print('named range LeaseComps_BlendCheck; Comp ID dropdown on Floor Detail')

# ---------------------------------------------------------------- 5. QA checks
qa = get_values(s, "'QA Harness'!A1:F30", render='FORMULA')
last = max(i for i, r in enumerate(qa, 1) if r and str(r[0]).startswith('QA-'))
NEW = [
    ['QA-009', 'CRITICAL', 'Formula errors – Floor Detail',
     f"=SUMPRODUCT(--ISERROR('Floor Detail'!A2:J{FD_ROWS}))", '0', '=IF(N(D{r})=0,"PASS","FAIL")'],
    ['QA-023', 'CRITICAL', 'Floor Detail rows with unknown comp_id',
     '=SUMPRODUCT((FloorDetail_CompIds<>"")*ISNA(MATCH(FloorDetail_CompIds,LeaseComps_IDs,0)))',
     '0', '=IF(N(D{r})=0,"PASS","FAIL")'],
    ['QA-073', 'HIGH', 'Comps whose typed blend disagrees with Floor Detail',
     '=SUMPRODUCT((LeaseComps_BlendCheck<>"")*(LeaseComps_BlendCheck<>"OK"))',
     '0', '=IF(N(D{r})=0,"PASS","FAIL")'],
]
batch_update(s, [{'insertDimension': {'range': {
    'sheetId': ids['QA Harness'], 'dimension': 'ROWS',
    'startIndex': last, 'endIndex': last + len(NEW)}, 'inheritFromBefore': True}}])
rows = [[c.format(r=last + 1 + i) if isinstance(c, str) else c for c in spec]
        for i, spec in enumerate(NEW)]
values_batch(s, [{'range': f"'QA Harness'!A{last + 1}:F{last + len(NEW)}", 'values': rows}])
new_last = last + len(NEW)
sm = new_last + 2                                   # blank row, then SUMMARY
values_batch(s, [
    {'range': f"'QA Harness'!D{sm}", 'values': [[
        f'=COUNTIF(F2:F{new_last},"PASS")&" / "&(COUNTA(F2:F{new_last})'
        f'-COUNTIF(F2:F{new_last},"INFO"))&" PASS"']]},
    {'range': f"'QA Harness'!F{sm}", 'values': [[
        f'=IF(COUNTIF(F2:F{new_last},"FAIL")+COUNTIF(F2:F{new_last},"UNKNOWN")=0,"PASS","REVIEW")']]},
    {'range': f"'QA Harness'!D{sm + 1}", 'values': [[f'=COUNTIF(F2:F{new_last},"FAIL")']]},
])
print(f'QA: added QA-009 / QA-023 / QA-073 at rows {last + 1}-{new_last}; summary now spans F2:F{new_last}')

# QA-001 scans the whole Lease Comps row; QA-072's typed-TI count keeps its column (S)
for i, r in enumerate(qa, 1):
    if len(r) > 3 and "'Lease Comps'!A:AN" in str(r[3]):
        values_batch(s, [{'range': f"'QA Harness'!D{i}",
                          'values': [[r[3].replace("'Lease Comps'!A:AN", "'Lease Comps'!A:AS")]]}])
        print(f'QA-001 scan widened to A:AS (row {i})')

changelog(s, 'STRUCTURE MIGRATION',
          'Added the Floor Detail tab (one row per floor, FK Comp ID) and five columns on Lease '
          'Comps: Floors on File, Detail RSF, Detail Rent (wtd), Detail TI (wtd), Blend Check. '
          'A comp is still one row; per-floor economics are stored instead of hand-blended, and '
          'the typed RSF/rent/TI are checked against the RSF-weighted detail (tolerances 1 SF, '
          '$0.50, $1). A mismatch reaches Record Status and QA Notes. New checks QA-009 / QA-023 '
          '/ QA-073. Layout now 45 columns: A-S inputs, T-Z wired, AA-AD floor detail, AE check, '
          'AF Notes, AG-AQ economics, AR-AS governance.', LC_ROWS - 1)
summary, fails = qa_status(s)
print('QA:', summary, '| failing:', fails or 'none')
