"""Move Benchmark Cohort from AP (after governance) into the wired zone at AB.

Result: V-AB wired, AC Notes, AD-AN economics, AO-AP governance. Zones 1-3 (A-U) are
untouched, so the Apps Script auto-ID trigger keeps working. Sheets shifts every formula,
named range, protection, band and column group on the insert; this script writes the
cohort formula at AB, re-points LeaseComps_Cohorts, widens the wired protection and
QA-001's scan, then removes the old column. Idempotent: no-op once AB is the cohort.
"""
import sys

from common import session, sheet_ids, named_ranges, batch_update, values_batch, get_values, changelog, qa_status, SID

s = session()
lc = sheet_ids(s)['Lease Comps']
hdr = get_values(s, "'Lease Comps'!A1:AQ1", render='FORMATTED_VALUE')[0]
hdr += [''] * (43 - len(hdr))
if hdr[27] == 'Benchmark Cohort' and hdr[28] == 'Notes':
    print('Benchmark Cohort already at AB — nothing to do')
    sys.exit(0)
assert hdr[27] == 'Notes' and hdr[41] == 'Benchmark Cohort', f'unexpected layout: AB={hdr[27]!r} AP={hdr[41]!r}'
last = named_ranges(s)['LeaseComps_RSF']['range']['endRowIndex']

COHORT_F = ('=IF($C{r}="","",IF($W{r}="","No Funding Data",'
            'IFERROR(INDEX(CohortLabels,MATCH($W{r},CohortTypes,0)),"Stage Unknown")))')

# 1. insert AB (old AP -> AQ), write the cohort column there
batch_update(s, [{'insertDimension': {'range': {'sheetId': lc, 'dimension': 'COLUMNS', 'startIndex': 27, 'endIndex': 28},
                                      'inheritFromBefore': True}}])
values_batch(s, [{'range': "'Lease Comps'!AB1", 'values': [['Benchmark Cohort']]},
                 {'range': f"'Lease Comps'!AB2:AB{last}", 'values': [[COHORT_F.format(r=r)] for r in range(2, last + 1)]}])
print('AB written (cohort wire)')

# 2. named range + wired protection + QA-001 scan, then drop the old column (now AQ, index 42)
nrs = named_ranges(s)
meta = s.get(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}', params={'fields': 'sheets(properties.sheetId,protectedRanges(protectedRangeId,description,range))'}).json()
prot = next(sh for sh in meta['sheets'] if sh['properties']['sheetId'] == lc).get('protectedRanges', [])
reqs = [{'updateNamedRange': {'namedRange': {'namedRangeId': nrs['LeaseComps_Cohorts']['namedRangeId'], 'name': 'LeaseComps_Cohorts',
                                            'range': {'sheetId': lc, 'startRowIndex': 1, 'endRowIndex': last, 'startColumnIndex': 27, 'endColumnIndex': 28}},
                              'fields': 'range'}}]
for p in prot:
    if p['description'].startswith('Wired from'):
        reqs.append({'updateProtectedRange': {'protectedRange': {'protectedRangeId': p['protectedRangeId'],
                                                                 'range': {**p['range'], 'startColumnIndex': 21, 'endColumnIndex': 28}},
                                              'fields': 'range'}})
reqs.append({'deleteDimension': {'range': {'sheetId': lc, 'dimension': 'COLUMNS', 'startIndex': 42, 'endIndex': 43}}})
batch_update(s, reqs)
qa = get_values(s, "'QA Harness'!A1:D30", render='FORMULA')
for i, r in enumerate(qa, 1):
    if len(r) > 3 and "'Lease Comps'!A:AO" in str(r[3]):
        values_batch(s, [{'range': f"'QA Harness'!D{i}", 'values': [[r[3].replace("'Lease Comps'!A:AO", "'Lease Comps'!A:AP")]]}])
        print(f'QA-001 scan widened to A:AP (row {i})')
print('named range re-pointed, wired protection V:AB, old cohort column removed')

changelog(s, 'STRUCTURE MIGRATION', 'Benchmark Cohort moved from AP into the wired zone at AB (V-AB wired, AC Notes, '
          'AD-AN economics, AO-AP governance). Formulas, named ranges, protections, bands and groups shifted with it; '
          'LeaseComps_Cohorts re-pointed; QA-001 scans A:AP.', last - 1)
summary, fails = qa_status(s)
print('QA:', summary, '| failing:', fails or 'none')
