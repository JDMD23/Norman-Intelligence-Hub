"""Lease Comps v4 visual design.

Zone-colored header band, tinted data zones (white = type here, cyan = wired from
other tabs, green = computed here, amber = governance), zone-boundary rules,
per-column number formats, frozen header + identity columns, sized columns.
"""
from common import session, sheet_ids, batch_update, changelog, SID
from theme import (CBRE_GREEN, SAGE, FOREST, OLIVE, WIRE, CALC, GOV, WHITE, LIGHT, FONT,
                   TAB_PRIMARY)

s = session()
lc = sheet_ids(s)['Lease Comps']
NROWS = 1207
meta = s.get(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}',
             params={'fields': 'sheets(properties.sheetId,protectedRanges(protectedRangeId,'
                               'description))'}).json()
existing = next((sh.get('protectedRanges', []) for sh in meta['sheets']
                 if sh['properties']['sheetId'] == lc), [])
have = {p['description'] for p in existing}


def hx(h):
    h = h.lstrip('#')
    return {'red': int(h[0:2], 16) / 255, 'green': int(h[2:4], 16) / 255,
            'blue': int(h[4:6], 16) / 255}


def ci(letter):
    n = 0
    for ch in letter:
        n = n * 26 + ord(ch) - 64
    return n - 1


def rng(c1, c2, r1=0, r2=NROWS):
    return {'sheetId': lc, 'startRowIndex': r1, 'endRowIndex': r2,
            'startColumnIndex': ci(c1), 'endColumnIndex': ci(c2) + 1}


reqs = []

# --- header band by zone (row 1): white bold, wrapped, centered
ZONES = [('A', 'D', CBRE_GREEN), ('E', 'K', CBRE_GREEN), ('L', 'S', CBRE_GREEN),
         ('T', 'Z', SAGE), ('AA', 'AA', CBRE_GREEN), ('AB', 'AL', FOREST),
         ('AM', 'AN', OLIVE)]
for c1, c2, color in ZONES:
    reqs.append({'repeatCell': {'range': rng(c1, c2, 0, 1), 'cell': {'userEnteredFormat': {
        'backgroundColor': hx(color),
        'textFormat': {'foregroundColor': hx('#FFFFFF'), 'bold': True, 'fontSize': 9, 'fontFamily': FONT},
        'wrapStrategy': 'WRAP', 'horizontalAlignment': 'CENTER', 'verticalAlignment': 'MIDDLE',
    }}, 'fields': 'userEnteredFormat(backgroundColor,textFormat,wrapStrategy,'
                  'horizontalAlignment,verticalAlignment)'}})

# --- data-zone tints (rows 2+): inputs white; wire cyan; calc green; governance amber
for c1, c2, color in [('A', 'S', WHITE), ('AA', 'AA', WHITE),
                      ('T', 'Z', WIRE), ('AB', 'AL', CALC),
                      ('AM', 'AN', GOV)]:
    reqs.append({'repeatCell': {'range': rng(c1, c2, 1), 'cell': {'userEnteredFormat': {
        'backgroundColor': hx(color)}}, 'fields': 'userEnteredFormat.backgroundColor'}})

# --- number formats
# Date Signed and Latest Round Date show as "July 2026": every Date Signed lands on
# the 1st (the day was always a placeholder) and ~half the wired round dates are
# month-level backfills, so month precision is what the data actually supports.
FMT = {('B', 'B'): ('DATE', 'mmmm yyyy'), ('T', 'T'): ('DATE', 'mmmm yyyy'),
       ('L', 'M'): ('NUMBER', '#,##0'), ('N', 'N'): ('NUMBER', '0.0'),
       ('O', 'Q'): ('CURRENCY', '$#,##0.00'), ('R', 'R'): ('NUMBER', '0.0'),
       ('S', 'S'): ('CURRENCY', '$#,##0'), ('V', 'W'): ('NUMBER', '#,##0.0'),
       ('AB', 'AE'): ('CURRENCY', '$#,##0'), ('AF', 'AG'): ('CURRENCY', '$#,##0.00'),
       ('AH', 'AH'): ('CURRENCY', '$#,##0'), ('AI', 'AI'): ('NUMBER', '0.0'),
       ('AJ', 'AK'): ('PERCENT', '0.00%'), ('AL', 'AL'): ('NUMBER', '#,##0')}
for (c1, c2), (t, p) in FMT.items():
    reqs.append({'repeatCell': {'range': rng(c1, c2, 1), 'cell': {'userEnteredFormat': {
        'numberFormat': {'type': t, 'pattern': p}}},
        'fields': 'userEnteredFormat.numberFormat'}})

# --- zone-boundary vertical rules + header underline
EDGE = {'style': 'SOLID_MEDIUM', 'color': hx(LIGHT)}
for c in ['D', 'K', 'S', 'Z', 'AA', 'AL']:
    reqs.append({'updateBorders': {'range': rng(c, c), 'right': EDGE}})
reqs.append({'updateBorders': {'range': rng('A', 'AN', 0, 1),
                               'bottom': {'style': 'SOLID_THICK', 'color': hx(CBRE_GREEN)}}})

# --- freeze header + identity, header height, tab color
reqs.append({'updateSheetProperties': {'properties': {
    'sheetId': lc, 'tabColorStyle': {'rgbColor': hx(TAB_PRIMARY)},
    'gridProperties': {'frozenRowCount': 1, 'frozenColumnCount': 3}},
    'fields': 'tabColorStyle,gridProperties.frozenRowCount,gridProperties.frozenColumnCount'}})
reqs.append({'updateDimensionProperties': {
    'range': {'sheetId': lc, 'dimension': 'ROWS', 'startIndex': 0, 'endIndex': 1},
    'properties': {'pixelSize': 48}, 'fields': 'pixelSize'}})

# --- column widths
WIDTHS = {'A': 88, 'B': 96, 'C': 168, 'D': 92, 'E': 200, 'F': 148, 'G': 104, 'H': 88,
          'I': 108, 'J': 128, 'K': 128, 'L': 78, 'M': 66, 'N': 72, 'O': 96, 'P': 96,
          'Q': 96, 'R': 64, 'S': 76, 'T': 108, 'U': 140, 'V': 96,
          'W': 116, 'X': 168, 'Y': 100, 'Z': 130, 'AA': 260, 'AB': 108, 'AC': 100, 'AD': 104,
          'AE': 128, 'AF': 100, 'AG': 112, 'AH': 100, 'AI': 78, 'AJ': 96, 'AK': 118,
          'AL': 104, 'AM': 128, 'AN': 240}
for c, w in WIDTHS.items():
    reqs.append({'updateDimensionProperties': {
        'range': {'sheetId': lc, 'dimension': 'COLUMNS', 'startIndex': ci(c), 'endIndex': ci(c) + 1},
        'properties': {'pixelSize': w}, 'fields': 'pixelSize'}})

# --- warning-only protection on wired + computed zones (edit inputs, not results);
#     the pre-v4 per-column "Calculated" warnings are superseded and removed.
LEGACY = 'Calculated -- edit the inputs, not this column'
added, removed = [], []
for c1, c2, desc in [('T', 'Z', 'Wired from Companies/Funding Rounds — edit those tabs instead'),
                     ('AB', 'AN', 'Computed — edit inputs, not results')]:
    if desc not in have:
        reqs.append({'addProtectedRange': {'protectedRange': {
            'range': rng(c1, c2, 1), 'description': desc, 'warningOnly': True}}})
        added.append(desc)
for p in existing:
    if p['description'] == LEGACY:
        reqs.append({'deleteProtectedRange': {'protectedRangeId': p['protectedRangeId']}})
        removed.append(p['protectedRangeId'])

batch_update(s, reqs)
print(f'styling applied ({len(reqs)} requests; protections added {len(added)}, '
      f'legacy removed {len(removed)})')
if added or removed:
    changelog(s, 'STYLE', 'Lease Comps v4 visual design: zone-colored headers, input/wired/'
              'computed/governance tints, zone rules, number formats, frozen panes, '
              f'column sizing, warning-only protection on non-input zones ({len(added)} zone '
              f'protections added, {len(removed)} legacy per-column warnings removed).', '')
else:
    print('protections already in place — no receipt needed (formatting re-applied only)')
