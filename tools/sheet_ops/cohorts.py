"""Benchmark cohorts: group thin funding stages into cohorts with enough n to mean something.

Owner decision 2026-09-02: Series D/E/F/G and Late Stage Venture collapse into one
"Late Stage (D+)" cohort (40 comps, up from four buckets of 11/15/6/5), IPO and reverse
mergers become "Public", and Debt stays separate because it is a financing type rather
than a stage. Median RSF joins the table: RSF is right-skewed in every cohort (Series C
means 41,108 but medians 26,427), so the mean alone is what made Series D look like a
dip below Series C.

The map lives in Reference per the workbook contract; Lease Comps carries the cohort as
a calc column so the Dashboard can group on it cheaply.
"""
from common import (session, sheet_ids, named_ranges, batch_update, values_batch,
                    get_values, changelog, qa_status, SID)

MAP = [('Seed', 'Seed'), ('Series A', 'Series A'), ('Series B', 'Series B'),
       ('Series C', 'Series C'),
       ('Series D', 'Late Stage (D+)'), ('Series E', 'Late Stage (D+)'),
       ('Series F', 'Late Stage (D+)'), ('Series G', 'Late Stage (D+)'),
       ('Late Stage Venture', 'Late Stage (D+)'), ('Private Equity', 'Late Stage (D+)'),
       ('IPO', 'Public'), ('Public Listing / Reverse Merger', 'Public'),
       ('Debt', 'Debt'), ('Venture - Series Unknown', 'Stage Unknown')]
ORDER = ['Seed', 'Series A', 'Series B', 'Series C', 'Late Stage (D+)', 'Public',
         'Debt', 'Stage Unknown', 'No Funding Data']

s = session()
ids = sheet_ids(s)
lc, ref, dash = ids['Lease Comps'], ids['Reference'], ids['Dashboard']
nrs = named_ranges(s)
rows_end = nrs['LeaseComps_RSF']['range']['endRowIndex']   # match existing extent exactly
last = rows_end                                            # 1-based last row of the data ranges
print('data extent: rows 2..%d' % last)

# --- Reference: the map (O/P) and the display order (R)
values_batch(s, [
    {'range': 'Reference!O1:P%d' % (len(MAP) + 1),
     'values': [['CohortTypes', 'CohortLabels']] + [list(m) for m in MAP]},
    {'range': 'Reference!R1:R%d' % (len(ORDER) + 1),
     'values': [['CohortOrder']] + [[c] for c in ORDER]},
])
print('Reference: %d type->cohort mappings, %d ordered cohorts' % (len(MAP), len(ORDER)))

# --- Lease Comps: Benchmark Cohort wired column at Z (wired zone T-Z)
grid = s.get(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}', params={
    'fields': 'sheets(properties(title,gridProperties(columnCount)))'}).json()
ncols = next(x['properties']['gridProperties']['columnCount']
             for x in grid['sheets'] if x['properties']['title'] == 'Lease Comps')
assert ncols == 40, f'Lease Comps grid is {ncols} columns; expected 40'

COHORT_F = ('=IF($C{r}="","",IF($U{r}="","No Funding Data",'
            'IFERROR(INDEX(CohortLabels,MATCH($U{r},CohortTypes,0)),"Stage Unknown")))')
values_batch(s, [
    {'range': "'Lease Comps'!Z1", 'values': [['Benchmark Cohort']]},
    {'range': "'Lease Comps'!Z2:Z%d" % last,
     'values': [[COHORT_F.format(r=r)] for r in range(2, last + 1)]},
])
print('Lease Comps: Benchmark Cohort column (Z) written')

# --- named ranges
def add(name, sheet, c1, c2, r1, r2):
    if name in nrs:
        return {'updateNamedRange': {'namedRange': {
            'namedRangeId': nrs[name]['namedRangeId'], 'name': name,
            'range': {'sheetId': sheet, 'startRowIndex': r1, 'endRowIndex': r2,
                      'startColumnIndex': c1, 'endColumnIndex': c2}}, 'fields': 'range'}}
    return {'addNamedRange': {'namedRange': {'name': name, 'range': {
        'sheetId': sheet, 'startRowIndex': r1, 'endRowIndex': r2,
        'startColumnIndex': c1, 'endColumnIndex': c2}}}}

batch_update(s, [
    add('CohortTypes', ref, 14, 15, 1, len(MAP) + 1),
    add('CohortLabels', ref, 15, 16, 1, len(MAP) + 1),
    add('CohortOrder', ref, 17, 18, 1, len(ORDER) + 1),
    add('LeaseComps_Cohorts', lc, 25, 26, 1, rows_end),
])
print('named ranges: CohortTypes, CohortLabels, CohortOrder, LeaseComps_Cohorts')

# --- Dashboard: rebuild the benchmark table on cohorts, with median RSF added
# A cohort below MIN_N shows its comp count but no averages: two comps is not a benchmark,
# and a blank is honest where a number would be quoted back at you. Same rule on the
# submarket table in dashboard_style.py.
MIN_N = 3


def per_row(col_range, agg='AVERAGE'):
    return ('=IF(OR($A{r}="",$B{r}<' + str(MIN_N) + '),"",IFERROR(' + agg + '(FILTER(' + col_range +
            ',LeaseComps_Cohorts=$A{r},' + col_range + '<>"")),""))')

COLS = {
    'B': '=IF($A{r}="","",COUNTIF(LeaseComps_Cohorts,$A{r}))',
    'C': per_row('LeaseComps_RSF'),
    'D': per_row('LeaseComps_RSF', 'MEDIAN'),
    'E': per_row('LeaseComps_StartRent'),
    'F': per_row('LeaseComps_NER'),
    'G': per_row('LeaseComps_CostSeat'),
    'H': ('=IF($A{r}="","",IF($B{r}=0,"No comps",IF($B{r}<' + str(MIN_N) + ',"n too low",'
          'IF($B{r}<5,"Thin",IF($B{r}<8,"Directional","Reliable")))))'),
}
first, nrows = 14, len(ORDER)
data = [
    {'range': 'Dashboard!A12', 'values': [['Benchmarks by funding stage  ·  all signed leases']]},
    {'range': 'Dashboard!A13:H13', 'values': [['Stage', 'Comps', 'Avg RSF', 'Median RSF',
                                              'Avg start rent', 'Avg NER', 'Avg cost/seat',
                                              'Sample']]},
    {'range': 'Dashboard!A%d' % first, 'values': [['=IFERROR(FILTER(CohortOrder,CohortOrder<>""),"")']]},
]
for c, tpl in COLS.items():
    data.append({'range': 'Dashboard!%s%d:%s%d' % (c, first, c, first + nrows - 1),
                 'values': [[tpl.format(r=r)] for r in range(first, first + nrows)]})
values_batch(s, data)
# clear the old 30-row capacity tail (cohorts are a fixed list now)
s.post(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/'
       f'Dashboard!A{first + nrows}:H23:clear', json={})
print('Dashboard: benchmark table rebuilt on %d cohorts, median RSF added' % nrows)

# --- QA-006 scans the Dashboard for formula errors; widen it to the new column H
qa = get_values(s, 'QA Harness!A1:F25', render='FORMULA')
for i, r in enumerate(qa, 1):
    if len(r) > 3 and isinstance(r[3], str) and 'ISERROR(Dashboard!' in r[3]:
        fixed = r[3].replace('Dashboard!A4:G43', 'Dashboard!A4:H43')
        if fixed != r[3]:
            values_batch(s, [{'range': 'QA Harness!D%d' % i, 'values': [[fixed]]}])
            print('QA-006 range widened to Dashboard!A4:H43')

changelog(s, 'BENCHMARK COHORTS',
          'Grouped thin funding stages into benchmark cohorts (owner decision): Series D/E/F/G '
          '+ Late Stage Venture -> "Late Stage (D+)" (40 comps), IPO + reverse merger -> "Public", '
          'Debt kept separate as a financing type, unmapped -> "Stage Unknown", no tracked rounds '
          '-> "No Funding Data". Map in Reference (CohortTypes/CohortLabels/CohortOrder), cohort '
          'wired into Lease Comps col AP. Dashboard table rebuilt with MEDIAN RSF added: RSF is '
          'right-skewed in every cohort, which is what made Series D read below Series C.',
          len(MAP))
summary, fails = qa_status(s)
print('QA:', summary, '| failing:', fails or 'none')
