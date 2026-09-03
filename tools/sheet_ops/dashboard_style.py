"""Dashboard v2 — the workbook's front door, built to be presented.

Owns the Dashboard tab's layout and presentation (formulas here are display formulas
over named ranges; no source data is touched). The cohort benchmark table (rows 12-22)
is written by cohorts.py and only styled here.

  rows 1-2    title band; live subtitle (as-of date, counts) + health badge in H2
  rows 4-8    eight KPI tiles, four across
  rows 12-22  benchmarks by funding stage (cohorts.py)
  rows 24-35  benchmarks by submarket, top 10 by comp count
  row 37      methodology footnote
  J4 / J21    embedded charts: Avg NER by stage, comps by submarket
QA-031 reads the comps-tracked tile (A5); QA-006 scans A4:H40 for errors.
"""
from common import session, sheet_ids, batch_update, values_batch, get_values, changelog, SID
from theme import (hx, FONT, CBRE_GREEN, ACCENT, DARK_GREEN, SAGE, INK, MUTED, RULE, PAPER, WHITE,
                   OK_FG, BAD_FG, WARN_FG, TAB_PRIMARY)

s = session()
ids = sheet_ids(s)
d = ids['Dashboard']


def ci(letter):
    n = 0
    for ch in letter:
        n = n * 26 + ord(ch) - 64
    return n - 1


def rng(c1, c2, r1, r2):
    """1-based inclusive rows / column letters -> grid range."""
    return {'sheetId': d, 'startRowIndex': r1 - 1, 'endRowIndex': r2,
            'startColumnIndex': ci(c1), 'endColumnIndex': ci(c2) + 1}


def fmt(c1, c2, r1, r2, **f):
    cell, fields = {}, []
    if 'bg' in f:
        cell['backgroundColor'] = hx(f['bg']); fields.append('backgroundColor')
    # only touch the text-format sub-fields that were asked for (a numberFormat-only call
    # must not reset size / weight / colour set by an earlier request)
    tf, sub = {}, []
    for key, api in (('fg', 'foregroundColor'), ('bold', 'bold'), ('italic', 'italic'), ('size', 'fontSize')):
        if key in f:
            tf[api] = hx(f[key]) if key == 'fg' else f[key]; sub.append(api)
    if tf:
        tf['fontFamily'] = FONT; sub.append('fontFamily')
        cell['textFormat'] = tf; fields.append('textFormat(' + ','.join(sub) + ')')
    if 'h' in f: cell['horizontalAlignment'] = f['h']; fields.append('horizontalAlignment')
    if 'v' in f: cell['verticalAlignment'] = f['v']; fields.append('verticalAlignment')
    if 'wrap' in f: cell['wrapStrategy'] = f['wrap']; fields.append('wrapStrategy')
    if 'num' in f:
        cell['numberFormat'] = {'type': f['num'][0], 'pattern': f['num'][1]}; fields.append('numberFormat')
    return {'repeatCell': {'range': rng(c1, c2, r1, r2), 'cell': {'userEnteredFormat': cell},
                           'fields': 'userEnteredFormat(' + ','.join(fields) + ')'}}


def rows_px(r1, r2, px):
    return {'updateDimensionProperties': {'range': {'sheetId': d, 'dimension': 'ROWS', 'startIndex': r1 - 1, 'endIndex': r2},
                                          'properties': {'pixelSize': px}, 'fields': 'pixelSize'}}


def merge(c1, c2, r1, r2):
    return {'mergeCells': {'range': rng(c1, c2, r1, r2), 'mergeType': 'MERGE_ALL'}}


def src_range(c1, c2, r1, r2):
    return {'sheetId': d, 'startRowIndex': r1 - 1, 'endRowIndex': r2,
            'startColumnIndex': ci(c1), 'endColumnIndex': ci(c2) + 1}


# ---------------------------------------------------------------- reset owned layers
meta = s.get(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}', params={
    'fields': 'sheets(properties(sheetId,title),merges,bandedRanges.bandedRangeId,'
              'conditionalFormats.ranges,charts.chartId)'}).json()
sh = next(x for x in meta['sheets'] if x['properties']['sheetId'] == d)
reset = [{'unmergeCells': {'range': m}} for m in sh.get('merges', [])]
reset += [{'deleteBanding': {'bandedRangeId': b['bandedRangeId']}} for b in sh.get('bandedRanges', [])]
reset += [{'deleteConditionalFormatRule': {'sheetId': d, 'index': i}}
          for i in range(len(sh.get('conditionalFormats', [])) - 1, -1, -1)]
reset += [{'deleteEmbeddedObject': {'objectId': c['chartId']}} for c in sh.get('charts', [])]
none = {'style': 'NONE'}
reset.append({'updateBorders': {'range': rng('A', 'H', 1, 60), 'top': none, 'bottom': none, 'left': none,
                                'right': none, 'innerHorizontal': none, 'innerVertical': none}})
reset.append(fmt('A', 'H', 1, 60, bg=WHITE, fg=INK, bold=False, italic=False, size=10, h='LEFT', v='MIDDLE',
                 wrap='OVERFLOW_CELL', num=('TEXT', '')))
reset.append(rows_px(1, 60, 21))
batch_update(s, reset)

# ---------------------------------------------------------------- content (display formulas)
s.post(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/Dashboard!A1:H11:clear', json={})
s.post(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/Dashboard!A23:H60:clear', json={})

TILES = [  # (label, formula, number format)
    ('Comps tracked', '=COUNTA(LeaseComps_IDs)', ('NUMBER', '#,##0')),
    ('Total RSF signed', '=SUMPRODUCT((LeaseComps_IDs<>"")*N(LeaseComps_RSF))', ('NUMBER', '#,##0')),
    ('Avg starting rent ($/RSF)', '=IFERROR(AVERAGE(FILTER(LeaseComps_StartRent,LeaseComps_IDs<>"")),"")', ('CURRENCY', '$#,##0.00')),
    ('Avg NER ($/RSF, 6%)', '=IFERROR(AVERAGE(FILTER(LeaseComps_NER,LeaseComps_NER<>"")),"")', ('CURRENCY', '$#,##0.00')),
    ('Companies tracked', '=COUNTA(CompanyIds)', ('NUMBER', '#,##0')),
    ('Funding rounds tracked', '=COUNTA(FundingRounds_IDs)', ('NUMBER', '#,##0')),
    ('Comps ready', '=COUNTIF(LeaseComps_Status,"READY")', ('NUMBER', '#,##0')),
    ('Comps needing review', '=COUNTIF(LeaseComps_Status,"NEEDS REVIEW")+COUNTIF(LeaseComps_Status,"MISSING INPUTS")', ('NUMBER', '#,##0')),
]
TILE_COLS = [('A', 'B'), ('C', 'D'), ('E', 'F'), ('G', 'H')]
TILE_ROWS = [(4, 5), (7, 8)]          # (label row, value row)

SUB_FIRST, SUB_N = 26, 10             # submarket table body rows
def per_row(col_range, agg='AVERAGE'):
    return ('=IF($A{r}="","",IFERROR(' + agg + '(FILTER(' + col_range +
            ',LeaseComps_Submarkets=$A{r},' + col_range + '<>"")),""))')
SUB_COLS = {
    'B': '=IF($A{r}="","",COUNTIF(LeaseComps_Submarkets,$A{r}))',
    'C': per_row('LeaseComps_RSF'), 'D': per_row('LeaseComps_RSF', 'MEDIAN'),
    'E': per_row('LeaseComps_StartRent'), 'F': per_row('LeaseComps_NER'),
    'G': per_row('LeaseComps_CostSeat'),
    'H': '=IF($A{r}="","",IF($B{r}<5,"Thin",IF($B{r}<8,"Directional","Reliable")))',
}

data = [
    {'range': 'Dashboard!A1', 'values': [['Norman AI Intelligence Hub']]},
    {'range': 'Dashboard!A2', 'values': [['="Manhattan office market intelligence  ·  As of "&TEXT(TODAY(),"mmmm d, yyyy")'
                                          '&"  ·  "&COUNTA(LeaseComps_IDs)&" signed leases  ·  "&COUNTA(CompanyIds)&" companies"']]},
    {'range': 'Dashboard!H2', 'values': [['=IF(QA_FailCount=0,"●  "&QA_Summary,"▲  "&QA_FailCount&" QA check(s) failing")']]},
    {'range': 'Dashboard!A24', 'values': [['Benchmarks by submarket  ·  top 10 by comp count']]},
    {'range': 'Dashboard!A25:H25', 'values': [['Submarket', 'Comps', 'Avg RSF', 'Median RSF', 'Avg start rent',
                                               'Avg NER', 'Avg cost/seat', 'Sample']]},
    {'range': f'Dashboard!A{SUB_FIRST}', 'values': [[
        '=LET(u,UNIQUE(FILTER(LeaseComps_Submarkets,LeaseComps_Submarkets<>"")),'
        f'ARRAY_CONSTRAIN(SORT(u,COUNTIF(LeaseComps_Submarkets,u),FALSE),{SUB_N},1))']]},
    {'range': 'Dashboard!A37', 'values': [[
        'Methodology: NER is a 6% annuity on flat rent tranches with free rent and TI taken upfront (docs/NER_MODEL.md). '
        'Blank means unknown, never zero. Sample: Reliable n ≥ 8, Directional 5–7, Thin < 5. '
        'Funding figures are tracked receipts in Funding Rounds, not narrative totals.']]},
]
for (lr, vr), row_tiles in zip(TILE_ROWS, (TILES[:4], TILES[4:])):
    for (c1, _), (label, formula, _) in zip(TILE_COLS, row_tiles):
        data.append({'range': f'Dashboard!{c1}{lr}', 'values': [[label]]})
        data.append({'range': f'Dashboard!{c1}{vr}', 'values': [[formula]]})
for c, tpl in SUB_COLS.items():
    data.append({'range': f'Dashboard!{c}{SUB_FIRST}:{c}{SUB_FIRST + SUB_N - 1}',
                 'values': [[tpl.format(r=r)] for r in range(SUB_FIRST, SUB_FIRST + SUB_N)]})
values_batch(s, data)

# QA hooks: total-comps tile moved to A5; error scan covers the whole board
qa = get_values(s, "'QA Harness'!A1:D30", render='FORMULA')
fixes = []
for i, r in enumerate(qa, 1):
    if len(r) > 3 and isinstance(r[3], str):
        f = r[3].replace('Dashboard!B4-', 'Dashboard!A5-')
        f = f.replace('Dashboard!A4:G43', 'Dashboard!A4:H40').replace('Dashboard!A4:H43', 'Dashboard!A4:H40')
        if f != r[3]:
            fixes.append({'range': f"'QA Harness'!D{i}", 'values': [[f]]})
if fixes:
    values_batch(s, fixes)

# ---------------------------------------------------------------- presentation
R = []
R.append({'updateSheetProperties': {'properties': {
    'sheetId': d, 'gridProperties': {'hideGridlines': True, 'frozenRowCount': 0},
    'tabColorStyle': {'rgbColor': hx(TAB_PRIMARY)}},
    'fields': 'gridProperties.hideGridlines,gridProperties.frozenRowCount,tabColorStyle'}})
for c, w in {'A': 232, 'B': 118, 'C': 112, 'D': 112, 'E': 128, 'F': 112, 'G': 124, 'H': 190, 'I': 28}.items():
    R.append({'updateDimensionProperties': {'range': {'sheetId': d, 'dimension': 'COLUMNS', 'startIndex': ci(c), 'endIndex': ci(c) + 1},
                                            'properties': {'pixelSize': w}, 'fields': 'pixelSize'}})

# title + subtitle band
R += [merge('A', 'H', 1, 1), merge('A', 'G', 2, 2),
      fmt('A', 'H', 1, 1, bg=CBRE_GREEN, fg=WHITE, bold=True, size=18, v='MIDDLE'),
      fmt('A', 'G', 2, 2, bg=DARK_GREEN, fg='#CFE3DC', size=10, v='MIDDLE'),
      fmt('H', 'H', 2, 2, bg=DARK_GREEN, fg=ACCENT, bold=True, size=10, h='RIGHT', v='MIDDLE'),
      rows_px(1, 1, 52), rows_px(2, 2, 30), rows_px(3, 3, 14)]
# KPI tiles
for lr, vr in TILE_ROWS:
    for c1, c2 in TILE_COLS:
        R += [merge(c1, c2, lr, lr), merge(c1, c2, vr, vr),
              fmt(c1, c2, lr, lr, bg=PAPER, fg=MUTED, bold=True, size=9, v='BOTTOM'),
              fmt(c1, c2, vr, vr, bg=PAPER, fg=CBRE_GREEN, bold=True, size=20, v='TOP'),
              {'updateBorders': {'range': rng(c1, c2, lr, vr),
                                 'left': {'style': 'SOLID_THICK', 'color': hx(ACCENT)}}}]
    R += [rows_px(lr, lr, 22), rows_px(vr, vr, 38)]
for (c1, _), (_, _, num) in zip(TILE_COLS, TILES[:4]):
    R.append(fmt(c1, c1, 5, 5, num=num))
for (c1, _), (_, _, num) in zip(TILE_COLS, TILES[4:]):
    R.append(fmt(c1, c1, 8, 8, num=num))
R += [rows_px(6, 6, 8), rows_px(9, 9, 8), rows_px(10, 11, 10)]

# the two tables: section title, header band, body, sample column
NUMFMT = {'B': ('NUMBER', '#,##0'), 'C': ('NUMBER', '#,##0'), 'D': ('NUMBER', '#,##0'),
          'E': ('CURRENCY', '$#,##0.00'), 'F': ('CURRENCY', '$#,##0.00'), 'G': ('CURRENCY', '$#,##0')}
for title_r, hdr_r, r1, r2 in [(12, 13, 14, 22), (24, 25, SUB_FIRST, SUB_FIRST + SUB_N - 1)]:
    R += [merge('A', 'H', title_r, title_r),
          fmt('A', 'H', title_r, title_r, fg=CBRE_GREEN, bold=True, size=12, v='BOTTOM'),
          rows_px(title_r, title_r, 34),
          fmt('A', 'H', hdr_r, hdr_r, bg=CBRE_GREEN, fg=WHITE, bold=True, size=9, h='RIGHT', v='MIDDLE'),
          fmt('A', 'A', hdr_r, hdr_r, h='LEFT'), fmt('H', 'H', hdr_r, hdr_r, h='CENTER'),
          rows_px(hdr_r, hdr_r, 28), rows_px(r1, r2, 24),
          fmt('A', 'A', r1, r2, bold=True, fg=INK),
          fmt('H', 'H', r1, r2, size=9, h='CENTER'),
          {'updateBorders': {'range': rng('A', 'H', r1, r2), 'innerHorizontal': {'style': 'SOLID', 'color': hx(RULE)},
                             'bottom': {'style': 'SOLID', 'color': hx(RULE)}}}]
    for c, num in NUMFMT.items():
        R.append(fmt(c, c, r1, r2, num=num, h='RIGHT'))
    R.append({'addBanding': {'bandedRange': {'range': rng('A', 'H', hdr_r, r2), 'rowProperties': {
        'headerColor': hx(CBRE_GREEN), 'firstBandColor': hx(WHITE), 'secondBandColor': hx(PAPER)}}}})
    for val, fg in (('Reliable', OK_FG), ('Directional', WARN_FG), ('Thin', BAD_FG), ('No comps', MUTED)):
        R.append({'addConditionalFormatRule': {'index': 0, 'rule': {'ranges': [rng('H', 'H', r1, r2)], 'booleanRule': {
            'condition': {'type': 'TEXT_EQ', 'values': [{'userEnteredValue': val}]},
            'format': {'textFormat': {'foregroundColor': hx(fg), 'bold': True}}}}}})
R += [rows_px(23, 23, 14), rows_px(36, 36, 10), merge('A', 'H', 37, 37),
      fmt('A', 'H', 37, 37, fg=MUTED, italic=True, size=9, wrap='WRAP', v='TOP'), rows_px(37, 37, 44)]
# health badge colour
for prefix, fg in (('●', ACCENT), ('▲', '#FFB4A2')):
    R.append({'addConditionalFormatRule': {'index': 0, 'rule': {'ranges': [rng('H', 'H', 2, 2)], 'booleanRule': {
        'condition': {'type': 'TEXT_STARTS_WITH', 'values': [{'userEnteredValue': prefix}]},
        'format': {'textFormat': {'foregroundColor': hx(fg), 'bold': True}}}}}})

# charts
def chart(title, subtitle, dom, ser, anchor_row, color, axis_title):
    return {'addChart': {'chart': {
        'spec': {'title': title, 'subtitle': subtitle, 'fontName': FONT,
                 'titleTextFormat': {'fontFamily': FONT, 'fontSize': 12, 'bold': True, 'foregroundColor': hx(CBRE_GREEN)},
                 'subtitleTextFormat': {'fontFamily': FONT, 'fontSize': 9, 'foregroundColor': hx(MUTED)},
                 'backgroundColor': hx(WHITE),
                 'basicChart': {
                     'chartType': 'COLUMN', 'legendPosition': 'NO_LEGEND', 'headerCount': 0,
                     'axis': [{'position': 'BOTTOM_AXIS', 'title': '', 'format': {'fontFamily': FONT, 'fontSize': 9}},
                              {'position': 'LEFT_AXIS', 'title': axis_title, 'format': {'fontFamily': FONT, 'fontSize': 9}}],
                     'domains': [{'domain': {'sourceRange': {'sources': [dom]}}}],
                     'series': [{'series': {'sourceRange': {'sources': [ser]}}, 'targetAxis': 'LEFT_AXIS',
                                 'colorStyle': {'rgbColor': hx(color)}}]}},
        'position': {'overlayPosition': {'anchorCell': {'sheetId': d, 'rowIndex': anchor_row - 1, 'columnIndex': ci('J')},
                                         'offsetXPixels': 0, 'offsetYPixels': 0, 'widthPixels': 560, 'heightPixels': 320}}}}}
R.append(chart('Average NER by funding stage', '$/RSF/yr, 6% annuity, flat tranches',
               src_range('A', 'A', 14, 22), src_range('F', 'F', 14, 22), 4, CBRE_GREEN, '$/RSF/yr'))
R.append(chart('Signed leases by submarket', 'top 10 submarkets by comp count',
               src_range('A', 'A', SUB_FIRST, SUB_FIRST + SUB_N - 1), src_range('B', 'B', SUB_FIRST, SUB_FIRST + SUB_N - 1),
               21, SAGE, 'comps'))

batch_update(s, R)
print(f'dashboard v2: {len(R)} presentation requests, {len(data)} content writes, {len(fixes)} QA hooks repointed')
changelog(s, 'DASHBOARD', 'Dashboard v2 (CBRE green): title band with live as-of subtitle and health badge; eight KPI '
          'tiles; benchmarks by funding stage (cohorts) and by submarket (top 10); Avg NER by stage and leases by '
          'submarket charts; methodology footnote. QA-031 now reads the comps tile (A5); QA-006 scans A4:H40.', '')
