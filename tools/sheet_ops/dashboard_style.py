"""Dashboard design pass — the workbook's front door.

Presentation only; no formula or value changes. Fixes the three things that make it
read as raw grid: truncated labels (column A far too narrow), gridlines on, and the
30-row stage table's empty tail showing as dead space (gridlines off makes it vanish).
"""
from common import session, sheet_ids, batch_update, changelog, SID

TITLE, SUB = '#0F172A', '#1E293B'
CARD_BG, CARD_EDGE = '#F8FAFC', '#CBD5E1'
HEAD = '#155E75'
NROWS = 45


def hx(h):
    h = h.lstrip('#')
    return {'red': int(h[0:2], 16) / 255, 'green': int(h[2:4], 16) / 255,
            'blue': int(h[4:6], 16) / 255}


def ci(letter):
    n = 0
    for ch in letter:
        n = n * 26 + ord(ch) - 64
    return n - 1


s = session()
meta = s.get(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}', params={
    'fields': 'sheets(properties(title,sheetId),bandedRanges(bandedRangeId),'
              'conditionalFormats(booleanRule(condition(type))))'}).json()
sh = next(x for x in meta['sheets'] if x['properties']['title'] == 'Dashboard')
d = sh['properties']['sheetId']


def rng(c1, c2, r1, r2):
    return {'sheetId': d, 'startRowIndex': r1, 'endRowIndex': r2,
            'startColumnIndex': ci(c1), 'endColumnIndex': ci(c2) + 1}


def fmt(c1, c2, r1, r2, cell, fields):
    return {'repeatCell': {'range': rng(c1, c2, r1, r2), 'cell': {'userEnteredFormat': cell},
                           'fields': fields}}


reqs = []

# gridlines off — the single biggest "this is a report, not a spreadsheet" change
reqs.append({'updateSheetProperties': {'properties': {
    'sheetId': d, 'gridProperties': {'hideGridlines': True}},
    'fields': 'gridProperties.hideGridlines'}})

# title + subtitle bands (text overflows across the band; no merges to keep it simple)
reqs.append(fmt('A', 'G', 0, 1, {
    'backgroundColor': hx(TITLE),
    'textFormat': {'foregroundColor': hx('#FFFFFF'), 'bold': True, 'fontSize': 14},
    'verticalAlignment': 'MIDDLE'},
    'userEnteredFormat(backgroundColor,textFormat,verticalAlignment)'))
reqs.append(fmt('A', 'G', 1, 2, {
    'backgroundColor': hx(SUB),
    'textFormat': {'foregroundColor': hx('#CBD5E1'), 'bold': False, 'fontSize': 9},
    'verticalAlignment': 'MIDDLE'},
    'userEnteredFormat(backgroundColor,textFormat,verticalAlignment)'))
for r1, r2, px in [(0, 1, 42), (1, 2, 22), (2, 3, 10)]:
    reqs.append({'updateDimensionProperties': {
        'range': {'sheetId': d, 'dimension': 'ROWS', 'startIndex': r1, 'endIndex': r2},
        'properties': {'pixelSize': px}, 'fields': 'pixelSize'}})

# KPI card (rows 4-10): tinted panel, labels left, numbers right and bold
reqs.append(fmt('A', 'B', 3, 10, {'backgroundColor': hx(CARD_BG)},
                'userEnteredFormat.backgroundColor'))
reqs.append(fmt('A', 'A', 3, 10, {
    'textFormat': {'foregroundColor': hx('#334155'), 'bold': True, 'fontSize': 10},
    'horizontalAlignment': 'LEFT'},
    'userEnteredFormat(textFormat,horizontalAlignment)'))
reqs.append(fmt('B', 'B', 3, 10, {
    'textFormat': {'foregroundColor': hx('#0F172A'), 'bold': True, 'fontSize': 12},
    'horizontalAlignment': 'RIGHT'},
    'userEnteredFormat(textFormat,horizontalAlignment)'))
reqs.append({'updateBorders': {'range': rng('A', 'B', 3, 10),
                               'top': {'style': 'SOLID', 'color': hx(CARD_EDGE)},
                               'bottom': {'style': 'SOLID', 'color': hx(CARD_EDGE)},
                               'left': {'style': 'SOLID', 'color': hx(CARD_EDGE)},
                               'right': {'style': 'SOLID', 'color': hx(CARD_EDGE)}}})
for c1, c2, r1, r2, pat in [('B', 'B', 3, 8, '#,##0'), ('B', 'B', 7, 9, '$#,##0.00'),
                            ('B', 'B', 9, 10, '#,##0')]:
    reqs.append(fmt(c1, c2, r1, r2, {'numberFormat': {
        'type': 'CURRENCY' if '$' in pat else 'NUMBER', 'pattern': pat}},
        'userEnteredFormat.numberFormat'))

# section heading + benchmark table header band
reqs.append(fmt('A', 'G', 11, 12, {
    'textFormat': {'foregroundColor': hx(TITLE), 'bold': True, 'fontSize': 11}},
    'userEnteredFormat.textFormat'))
reqs.append(fmt('A', 'G', 12, 13, {
    'backgroundColor': hx(HEAD),
    'textFormat': {'foregroundColor': hx('#FFFFFF'), 'bold': True, 'fontSize': 9},
    'horizontalAlignment': 'CENTER', 'verticalAlignment': 'MIDDLE'},
    'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)'))
reqs.append(fmt('A', 'A', 12, 13, {'horizontalAlignment': 'LEFT'},
                'userEnteredFormat.horizontalAlignment'))

# benchmark body: number formats + alignment
for c1, c2, typ, pat in [('B', 'C', 'NUMBER', '#,##0'), ('D', 'F', 'CURRENCY', '$#,##0')]:
    reqs.append(fmt(c1, c2, 13, 43, {'numberFormat': {'type': typ, 'pattern': pat}},
                    'userEnteredFormat.numberFormat'))
reqs.append(fmt('D', 'E', 13, 43, {'numberFormat': {'type': 'CURRENCY', 'pattern': '$#,##0.00'}},
                'userEnteredFormat.numberFormat'))
reqs.append(fmt('G', 'G', 13, 43, {
    'textFormat': {'foregroundColor': hx('#64748B'), 'fontSize': 9},
    'horizontalAlignment': 'LEFT'}, 'userEnteredFormat(textFormat,horizontalAlignment)'))

# banded rows over the populated + reserved table area (blank tail is invisible w/o gridlines)
for b in sh.get('bandedRanges', []):
    reqs.append({'deleteBanding': {'bandedRangeId': b['bandedRangeId']}})
reqs.append({'addBanding': {'bandedRange': {
    'range': rng('A', 'G', 13, 43),
    'rowProperties': {'firstBandColor': hx('#FFFFFF'), 'secondBandColor': hx('#F8FAFC')}}}})

# QA badge in A44: green when the workbook is client-safe, red when it is not
for i in reversed(range(len(sh.get('conditionalFormats', [])))):
    reqs.append({'deleteConditionalFormatRule': {'sheetId': d, 'index': i}})
reqs.append({'addConditionalFormatRule': {'index': 0, 'rule': {
    'ranges': [rng('A', 'A', 43, 44)],
    'booleanRule': {'condition': {'type': 'TEXT_STARTS_WITH',
                                  'values': [{'userEnteredValue': '[OK]'}]},
                    'format': {'backgroundColor': hx('#DCFCE7'),
                               'textFormat': {'foregroundColor': hx('#166534'), 'bold': True}}}}}})
reqs.append({'addConditionalFormatRule': {'index': 1, 'rule': {
    'ranges': [rng('A', 'A', 43, 44)],
    'booleanRule': {'condition': {'type': 'TEXT_NOT_CONTAINS',
                                  'values': [{'userEnteredValue': '[OK]'}]},
                    'format': {'backgroundColor': hx('#FEE2E2'),
                               'textFormat': {'foregroundColor': hx('#991B1B'), 'bold': True}}}}}})

# column widths — column A was truncating every label and stage name
for c, w in {'A': 236, 'B': 104, 'C': 104, 'D': 128, 'E': 104, 'F': 124, 'G': 196}.items():
    reqs.append({'updateDimensionProperties': {
        'range': {'sheetId': d, 'dimension': 'COLUMNS', 'startIndex': ci(c), 'endIndex': ci(c) + 1},
        'properties': {'pixelSize': w}, 'fields': 'pixelSize'}})

batch_update(s, reqs)
print(f'dashboard styled ({len(reqs)} requests)')
changelog(s, 'STYLE', 'Dashboard design pass (presentation only): gridlines off, title/subtitle '
          'bands, KPI stat card, benchmark header band + banded rows, number formats, QA badge '
          'colour, and column widths (column A was truncating every label and stage name).', '')
