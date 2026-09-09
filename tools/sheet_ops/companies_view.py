"""Companies as a reading view.

Adds two wired columns so a reader sees each company's funding position without opening
Funding Rounds: M Latest Round (type · month) and N Total Tracked Funding ($M), both looked
up from Company Metrics, blank when unknown. Registers them in _Schema (role calc). Collapses
the five narrative research columns (H:L) into a column group, and Funding Rounds' Source
URL (L) likewise. Re-runnable.
"""
from common import session, sheet_ids, batch_update, values_batch, get_values, changelog, SID

s = session()
ids = sheet_ids(s)
co, fr, schema = ids['Companies'], ids['Funding Rounds'], ids['_Schema']
NROWS = 1200

F_M = ('=IF($A{r}="","",IFERROR(LET(t,INDEX(\'Company Metrics\'!$L:$L,MATCH($A{r},\'Company Metrics\'!$A:$A,0)),'
       'd,INDEX(\'Company Metrics\'!$K:$K,MATCH($A{r},\'Company Metrics\'!$A:$A,0)),'
       'IF(t="","",t&IF(d="",""," · "&TEXT(d,"mmm yyyy")))),""))')
F_N = ('=IF($A{r}="","",IFERROR(LET(t,INDEX(\'Company Metrics\'!$M:$M,MATCH($A{r},\'Company Metrics\'!$A:$A,0)),'
       'IF(OR(t="",t=0),"",t)),""))')

grid = s.get(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}', params={
    'fields': 'sheets(properties(sheetId,gridProperties.columnCount),columnGroups)'}).json()
sheets = {x['properties']['sheetId']: x for x in grid['sheets']}
if sheets[co]['properties']['gridProperties']['columnCount'] < 14:
    batch_update(s, [{'appendDimension': {'sheetId': co, 'dimension': 'COLUMNS',
                                          'length': 14 - sheets[co]['properties']['gridProperties']['columnCount']}}])

hdr = get_values(s, 'Companies!M1:N1', render='FORMATTED_VALUE')
cur = get_values(s, 'Companies!M2:N2', render='FORMULA')
want = [F_M.format(r=2), F_N.format(r=2)]
if not hdr or hdr[0] != ['Latest Round', 'Total Tracked Funding ($M)'] or not cur or cur[0] != want:
    values_batch(s, [
        {'range': 'Companies!M1:N1', 'values': [['Latest Round', 'Total Tracked Funding ($M)']]},
        {'range': f'Companies!M2:N{NROWS}', 'values': [[F_M.format(r=r), F_N.format(r=r)] for r in range(2, NROWS + 1)]},
    ])
    print('Companies: wired M (Latest Round) and N (Total Tracked Funding) written')
else:
    print('Companies: wired columns current')

# _Schema: register M and N after the Companies L row
rows = get_values(s, '_Schema!A1:J300', render='FORMATTED_VALUE')
co_rows = [i for i, r in enumerate(rows) if r and r[0] == 'Companies']
have = {rows[i][1] for i in co_rows}
W = '(wired lookup — never type here; source of truth lives in the referenced tab)'
NEW = [
    ['Companies', 'M', 'Latest Round', 'latest_round', 'text', 'calc', 'no', '', F_M,
     f'Latest tracked round type and month {W} -> Company Metrics.'],
    ['Companies', 'N', 'Total Tracked Funding ($M)', 'total_fund', 'num', 'calc', 'no', '', F_N,
     f'Sum of tracked rounds, blank (never 0) when amounts are unknown {W} -> Company Metrics.'],
]
missing = [n for n in NEW if n[1] not in have]
if missing:
    after = co_rows[-1] + 1                     # 1-based row of the last Companies entry
    batch_update(s, [{'insertDimension': {'range': {'sheetId': schema, 'dimension': 'ROWS',
                                                     'startIndex': after, 'endIndex': after + len(missing)},
                                          'inheritFromBefore': True}}])
    r = s.put(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/_Schema!A{after + 1}:J{after + len(missing)}'
              '?valueInputOption=RAW', json={'values': missing})
    assert r.status_code == 200, r.json()
    print(f'_Schema: {len(missing)} Companies entries added')
else:
    print('_Schema: Companies M/N already registered')

# column groups (collapsed): Companies H:L research narrative; Funding Rounds L source URL
def ci(letter):
    n = 0
    for ch in letter:
        n = n * 26 + ord(ch) - 64
    return n - 1
reqs = []
for sid, c1, c2 in [(co, 'H', 'L'), (fr, 'L', 'L')]:
    key = (ci(c1), ci(c2) + 1)
    groups = {(g['range']['startIndex'], g['range']['endIndex']) for g in sheets[sid].get('columnGroups', [])}
    if any(a <= key[0] and b >= key[1] for a, b in groups):
        continue
    grange = {'sheetId': sid, 'dimension': 'COLUMNS', 'startIndex': key[0], 'endIndex': key[1]}
    reqs += [{'addDimensionGroup': {'range': grange}},
             {'updateDimensionGroup': {'dimensionGroup': {'range': grange, 'depth': 1, 'collapsed': True}, 'fields': 'collapsed'}}]
if reqs:
    batch_update(s, reqs)
    print(f'column groups added: {len(reqs) // 2}')

if missing or reqs:
    changelog(s, 'COMPANIES VIEW', 'Companies gains wired Latest Round (M) and Total Tracked Funding (N) from '
              'Company Metrics, registered in _Schema as calc; research narrative H:L and Funding Rounds Source URL '
              'collapsed into column groups.', len(missing))
