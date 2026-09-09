"""Remove Comp Source (T) and Verified Date (U) — owner decision 2026-09-03.

"Once I add a comp it's final and it always comes from me": provenance is the owner, so
the two columns carry no information, and the STALE - REVERIFY status they fed retires
with them. Columns from V shift left by two (wired T-Z, Notes AA, economics AB-AL,
governance AM-AN; 40 columns). Zones 1-3 up to S are untouched, so the Apps Script
auto-ID trigger keeps working. Idempotent: no-op once T is Latest Round Date.
"""
import sys

from common import session, sheet_ids, named_ranges, batch_update, values_batch, get_values, changelog, qa_status, SID

s = session()
ids = sheet_ids(s)
lc, ref = ids['Lease Comps'], ids['Reference']
hdr = get_values(s, "'Lease Comps'!A1:AP1", render='FORMATTED_VALUE')[0]
if hdr[19].startswith('Latest Round Date'):
    print('Comp Source / Verified Date already removed — nothing to do')
    sys.exit(0)
assert hdr[19] == 'Comp Source' and hdr[20] == 'Verified Date', f'unexpected T/U: {hdr[19]!r} {hdr[20]!r}'
last = named_ranges(s)['LeaseComps_RSF']['range']['endRowIndex']

# 1. drop the two columns (everything to the right shifts left by two)
batch_update(s, [{'deleteDimension': {'range': {'sheetId': lc, 'dimension': 'COLUMNS', 'startIndex': 19, 'endIndex': 21}}}])
print('columns T:U removed')

# 2. status + QA notes without the staleness branch (they referenced $U and would be #REF!)
STATUS = ('=IF($C{r}="","",IF(OR($A{r}="",$L{r}="",$N{r}="",$O{r}="",$B{r}="",$F{r}=""),'
          '"MISSING INPUTS",IF(OR($M{r}="",$S{r}=""),"NEEDS REVIEW","READY")))')
NOTES = ('=IF($C{r}="","",TEXTJOIN("; ",TRUE,IF($A{r}="","MISSING COMP ID",""),'
         'IF($L{r}="","MISSING RSF",""),IF($N{r}="","MISSING TERM",""),'
         'IF($O{r}="","MISSING STARTING RENT",""),IF($B{r}="","MISSING DATE",""),'
         'IF($F{r}="","MISSING SUBMARKET",""),IF($M{r}="","SEATS UNKNOWN",""),'
         'IF($S{r}="","TI UNKNOWN - NER BLANK","")))')
values_batch(s, [{'range': f"'Lease Comps'!AM2:AN{last}",
                  'values': [[STATUS.format(r=r), NOTES.format(r=r)] for r in range(2, last + 1)]}])
print('Record Status / QA Notes rewritten without staleness (AM:AN)')

# 3. Reference: retire CompSources and the STALE - REVERIFY status
nrs = named_ranges(s)
reqs = []
if 'CompSources' in nrs:
    reqs.append({'deleteNamedRange': {'namedRangeId': nrs['CompSources']['namedRangeId']}})
rs = nrs['RecordStatuses']
reqs.append({'updateNamedRange': {'namedRange': {'namedRangeId': rs['namedRangeId'], 'name': 'RecordStatuses',
                                                 'range': {**rs['range'], 'endRowIndex': 4}}, 'fields': 'range'}})
batch_update(s, reqs)
s.post(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/Reference!M1:M6:clear', json={})
s.post(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/Reference!H5:clear', json={})
print('Reference: CompSources removed, RecordStatuses = READY / NEEDS REVIEW / MISSING INPUTS')

# 4. QA-001 scan follows the last column
qa = get_values(s, "'QA Harness'!A1:D30", render='FORMULA')
for i, r in enumerate(qa, 1):
    if len(r) > 3 and "'Lease Comps'!A:AP" in str(r[3]):
        values_batch(s, [{'range': f"'QA Harness'!D{i}", 'values': [[r[3].replace("'Lease Comps'!A:AP", "'Lease Comps'!A:AN")]]}])
        print(f'QA-001 scan narrowed to A:AN (row {i})')

changelog(s, 'STRUCTURE MIGRATION', 'Removed Comp Source (T) and Verified Date (U) per owner decision (comps are final '
          'and owner-sourced); STALE - REVERIFY status retired; CompSources vocabulary removed. Columns from V shifted '
          'left by two: wired T-Z, Notes AA, economics AB-AL, governance AM-AN (40 columns).', last - 1)
summary, fails = qa_status(s)
print('QA:', summary, '| failing:', fails or 'none')
