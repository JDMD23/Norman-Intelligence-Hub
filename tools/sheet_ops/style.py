"""Lease Comps v4 visual design.

Zone-colored header band, tinted data zones (white = type here, cyan = wired from
other tabs, green = computed here, amber = governance), zone-boundary rules,
per-column number formats, frozen header + identity columns, sized columns.
"""
from common import session, sheet_ids, batch_update, changelog, SID

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
ZONES = [('A', 'D', '#0F172A'), ('E', 'K', '#1E293B'), ('L', 'U', '#334155'),
         ('V', 'AA', '#155E75'), ('AB', 'AB', '#334155'), ('AC', 'AM', '#166534'),
         ('AN', 'AO', '#92400E')]
for c1, c2, color in ZONES:
    reqs.append({'repeatCell': {'range': rng(c1, c2, 0, 1), 'cell': {'userEnteredFormat': {
        'backgroundColor': hx(color),
        'textFormat': {'foregroundColor': hx('#FFFFFF'), 'bold': True, 'fontSize': 9},
        'wrapStrategy': 'WRAP', 'horizontalAlignment': 'CENTER', 'verticalAlignment': 'MIDDLE',
    }}, 'fields': 'userEnteredFormat(backgroundColor,textFormat,wrapStrategy,'
                  'horizontalAlignment,verticalAlignment)'}})

# --- data-zone tints (rows 2+): inputs white; wire cyan; calc green; governance amber
for c1, c2, color in [('A', 'U', '#FFFFFF'), ('AB', 'AB', '#FFFFFF'),
                      ('V', 'AA', '#ECFEFF'), ('AC', 'AM', '#F0FDF4'),
                      ('AN', 'AO', '#FFFBEB')]:
    reqs.append({'repeatCell': {'range': rng(c1, c2, 1), 'cell': {'userEnteredFormat': {
        'backgroundColor': hx(color)}}, 'fields': 'userEnteredFormat.backgroundColor'}})

# --- number formats
# Date Signed and Latest Round Date show as "July 2026": every Date Signed lands on
# the 1st (the day was always a placeholder) and ~half the wired round dates are
# month-level backfills, so month precision is what the data actually supports.
# Verified Date keeps day precision — it is an operational audit date you set.
FMT = {('B', 'B'): ('DATE', 'mmmm yyyy'), ('V', 'V'): ('DATE', 'mmmm yyyy'),
       ('U', 'U'): ('DATE', 'yyyy-mm-dd'),
       ('L', 'M'): ('NUMBER', '#,##0'), ('N', 'N'): ('NUMBER', '0.0'),
       ('O', 'Q'): ('CURRENCY', '$#,##0.00'), ('R', 'R'): ('NUMBER', '0.0'),
       ('S', 'S'): ('CURRENCY', '$#,##0'), ('X', 'Y'): ('NUMBER', '#,##0.0'),
       ('AC', 'AF'): ('CURRENCY', '$#,##0'), ('AG', 'AH'): ('CURRENCY', '$#,##0.00'),
       ('AI', 'AI'): ('CURRENCY', '$#,##0'), ('AJ', 'AJ'): ('NUMBER', '0.0'),
       ('AK', 'AL'): ('PERCENT', '0.00%'), ('AM', 'AM'): ('NUMBER', '#,##0')}
for (c1, c2), (t, p) in FMT.items():
    reqs.append({'repeatCell': {'range': rng(c1, c2, 1), 'cell': {'userEnteredFormat': {
        'numberFormat': {'type': t, 'pattern': p}}},
        'fields': 'userEnteredFormat.numberFormat'}})

# --- zone-boundary vertical rules + header underline
EDGE = {'style': 'SOLID_MEDIUM', 'color': hx('#94A3B8')}
for c in ['D', 'K', 'U', 'AA', 'AB', 'AM']:
    reqs.append({'updateBorders': {'range': rng(c, c), 'right': EDGE}})
reqs.append({'updateBorders': {'range': rng('A', 'AO', 0, 1),
                               'bottom': {'style': 'SOLID_THICK', 'color': hx('#0F172A')}}})

# --- freeze header + identity, header height, tab color
reqs.append({'updateSheetProperties': {'properties': {
    'sheetId': lc, 'tabColorStyle': {'rgbColor': hx('#0F172A')},
    'gridProperties': {'frozenRowCount': 1, 'frozenColumnCount': 3}},
    'fields': 'tabColorStyle,gridProperties.frozenRowCount,gridProperties.frozenColumnCount'}})
reqs.append({'updateDimensionProperties': {
    'range': {'sheetId': lc, 'dimension': 'ROWS', 'startIndex': 0, 'endIndex': 1},
    'properties': {'pixelSize': 48}, 'fields': 'pixelSize'}})

# --- column widths
WIDTHS = {'A': 88, 'B': 96, 'C': 168, 'D': 92, 'E': 200, 'F': 148, 'G': 104, 'H': 88,
          'I': 108, 'J': 128, 'K': 128, 'L': 78, 'M': 66, 'N': 72, 'O': 96, 'P': 96,
          'Q': 96, 'R': 64, 'S': 76, 'T': 108, 'U': 100, 'V': 108, 'W': 140, 'X': 96,
          'Y': 116, 'Z': 168, 'AA': 100, 'AB': 260, 'AC': 108, 'AD': 100, 'AE': 104,
          'AF': 128, 'AG': 100, 'AH': 112, 'AI': 100, 'AJ': 78, 'AK': 96, 'AL': 118,
          'AM': 104, 'AN': 128, 'AO': 240}
for c, w in WIDTHS.items():
    reqs.append({'updateDimensionProperties': {
        'range': {'sheetId': lc, 'dimension': 'COLUMNS', 'startIndex': ci(c), 'endIndex': ci(c) + 1},
        'properties': {'pixelSize': w}, 'fields': 'pixelSize'}})

# --- warning-only protection on wired + computed zones (edit inputs, not results);
#     the pre-v4 per-column "Calculated" warnings are superseded and removed.
LEGACY = 'Calculated -- edit the inputs, not this column'
added, removed = [], []
for c1, c2, desc in [('V', 'AA', 'Wired from Companies/Funding Rounds — edit those tabs instead'),
                     ('AC', 'AO', 'Computed — edit inputs, not results')]:
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
