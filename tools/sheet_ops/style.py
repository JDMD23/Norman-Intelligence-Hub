"""Lease Comps visual design: zone-coloured header band, tinted data zones, zone rules,
per-column number formats, frozen panes, sized columns, warning-only protection.

Columns are addressed by HEADER TEXT, so inserting or moving a column needs no edit here.
Colour carries meaning: white = type here, celadon = wired from another tab, green = computed
here, wheat = governance / QA.
"""
from common import session, sheet_ids, batch_update, changelog, headers, SID
from theme import (hx, FONT, CBRE_GREEN, SAGE, FOREST, OLIVE, WIRE, CALC, GOV, WHITE, LIGHT,
                   TAB_PRIMARY)

NROWS = 1207
s = session()
lc = sheet_ids(s)['Lease Comps']
H = headers(s, 'Lease Comps')


def ci(letter):
    n = 0
    for ch in letter:
        n = n * 26 + ord(ch) - 64
    return n - 1


def span(first, last=None):
    """(start, end) 0-based half-open column indices for a header range."""
    a = ci(H[first])
    b = ci(H[last if last else first])
    assert a <= b, f'{first} .. {last} is out of order in the live sheet'
    return a, b + 1


def rng(first, last=None, r1=0, r2=NROWS):
    a, b = span(first, last)
    return {'sheetId': lc, 'startRowIndex': r1, 'endRowIndex': r2,
            'startColumnIndex': a, 'endColumnIndex': b}


# (first header, last header, header-band colour, body tint)
ZONES = [
    ('Comp ID', 'Company ID', CBRE_GREEN, WHITE),                       # identity
    ('Address', 'Delivery Condition', CBRE_GREEN, WHITE),               # premises
    ('RSF', 'TI $/SF', CBRE_GREEN, WHITE),                              # deal terms
    ('Latest Round Date', 'Benchmark Cohort', SAGE, WIRE),              # wired: funding + company
    ('Floors on File', 'Detail TI (wtd)', SAGE, WIRE),                  # wired: floor detail
    ('Blend Check', 'Blend Check', OLIVE, GOV),                         # floor-detail check
    ('Notes', 'Notes', CBRE_GREEN, WHITE),                              # input
    ('Year 1 Rent ($)', 'Months of Rent Covered', FOREST, CALC),        # economics + ratios
    ('Record Status', 'QA Notes', OLIVE, GOV),                          # governance
]
# right-hand rule at each zone boundary
EDGES = ['Company ID', 'Delivery Condition', 'TI $/SF', 'Benchmark Cohort', 'Detail TI (wtd)',
         'Blend Check', 'Notes', 'Months of Rent Covered']

DATE_MY = ('DATE', 'mmmm yyyy')
INT = ('NUMBER', '#,##0')
NUM1 = ('NUMBER', '0.0')
NUM1C = ('NUMBER', '#,##0.0')
USD = ('CURRENCY', '$#,##0')
USD2 = ('CURRENCY', '$#,##0.00')
PCT = ('PERCENT', '0.00%')
# Date Signed and Latest Round Date show as "July 2026": every Date Signed lands on the 1st and
# about half the wired round dates are month-level backfills, so month precision is what the
# data actually supports.
FMT = {
    'Date Signed': DATE_MY, 'Latest Round Date': DATE_MY,
    'RSF': INT, 'Seats': INT, 'Term (Years)': NUM1,
    'Rent P1 ($/RSF, mo 1-60)': USD2, 'Rent P2 ($/RSF, mo 61-120)': USD2,
    'Rent P3 ($/RSF, mo 121+)': USD2, 'Free Rent (months)': NUM1, 'TI $/SF': USD,
    'Latest Round Amt ($M)': NUM1C, 'Total Tracked Funding ($M)': NUM1C,
    'Floors on File': ('NUMBER', '0'), 'Detail RSF': INT,
    'Detail Rent (wtd)': USD2, 'Detail TI (wtd)': USD,
    'Year 1 Rent ($)': USD, 'Free Rent $ Value': USD, 'TI Allowance Total ($)': USD,
    'Projected Gross Rent (Term)': USD, 'Avg Rate ($/RSF/Yr)': USD2,
    'NER Annuity ($/RSF/Yr) @ 6%': USD2, 'Cost/Seat (Year 1)': USD, 'RSF / Seat': NUM1,
    'Rent-to-Raise (Yr 1) %': PCT, 'Lease-to-Total-Funding %': PCT,
    'Months of Rent Covered': INT,
}
CENTER = {'Floors on File', 'Blend Check'}
WIDTHS = {
    'Comp ID': 88, 'Date Signed': 96, 'Tenant': 168, 'Company ID': 92, 'Address': 200,
    'Submarket': 148, 'Building Class': 104, 'Floor(s)': 88, 'Condition': 108, 'Deal Type': 128,
    'Delivery Condition': 128, 'RSF': 78, 'Seats': 66, 'Term (Years)': 72,
    'Rent P1 ($/RSF, mo 1-60)': 96, 'Rent P2 ($/RSF, mo 61-120)': 96,
    'Rent P3 ($/RSF, mo 121+)': 96, 'Free Rent (months)': 64, 'TI $/SF': 76,
    'Latest Round Date': 108, 'Latest Round Type': 140, 'Latest Round Amt ($M)': 96,
    'Total Tracked Funding ($M)': 116, 'Company (canonical)': 168, 'HQ City': 100,
    'Benchmark Cohort': 130, 'Floors on File': 74, 'Detail RSF': 90,
    'Detail Rent (wtd)': 104, 'Detail TI (wtd)': 96, 'Blend Check': 150, 'Notes': 260,
    'Year 1 Rent ($)': 108, 'Free Rent $ Value': 100, 'TI Allowance Total ($)': 104,
    'Projected Gross Rent (Term)': 128, 'Avg Rate ($/RSF/Yr)': 100,
    'NER Annuity ($/RSF/Yr) @ 6%': 112, 'Cost/Seat (Year 1)': 100, 'RSF / Seat': 78,
    'Rent-to-Raise (Yr 1) %': 96, 'Lease-to-Total-Funding %': 118,
    'Months of Rent Covered': 104, 'Record Status': 128, 'QA Notes': 240,
}

reqs = []
for first, last, band, tint in ZONES:
    reqs.append({'repeatCell': {'range': rng(first, last, 0, 1), 'cell': {'userEnteredFormat': {
        'backgroundColor': hx(band),
        'textFormat': {'foregroundColor': hx('#FFFFFF'), 'bold': True, 'fontSize': 9,
                       'fontFamily': FONT},
        'wrapStrategy': 'WRAP', 'horizontalAlignment': 'CENTER', 'verticalAlignment': 'MIDDLE'}},
        'fields': 'userEnteredFormat(backgroundColor,textFormat,wrapStrategy,'
                  'horizontalAlignment,verticalAlignment)'}})
    reqs.append({'repeatCell': {'range': rng(first, last, 1), 'cell': {'userEnteredFormat': {
        'backgroundColor': hx(tint)}}, 'fields': 'userEnteredFormat.backgroundColor'}})

for header, (t, p) in FMT.items():
    reqs.append({'repeatCell': {'range': rng(header, r1=1), 'cell': {'userEnteredFormat': {
        'numberFormat': {'type': t, 'pattern': p}}}, 'fields': 'userEnteredFormat.numberFormat'}})
for header in CENTER:
    reqs.append({'repeatCell': {'range': rng(header, r1=1), 'cell': {'userEnteredFormat': {
        'horizontalAlignment': 'CENTER'}}, 'fields': 'userEnteredFormat.horizontalAlignment'}})

EDGE = {'style': 'SOLID_MEDIUM', 'color': hx(LIGHT)}
for header in EDGES:
    reqs.append({'updateBorders': {'range': rng(header), 'right': EDGE}})
first_h, last_h = 'Comp ID', 'QA Notes'
reqs.append({'updateBorders': {'range': rng(first_h, last_h, 0, 1),
                               'bottom': {'style': 'SOLID_THICK', 'color': hx(CBRE_GREEN)}}})

reqs.append({'updateSheetProperties': {'properties': {
    'sheetId': lc, 'tabColorStyle': {'rgbColor': hx(TAB_PRIMARY)},
    'gridProperties': {'frozenRowCount': 1, 'frozenColumnCount': 3}},
    'fields': 'tabColorStyle,gridProperties.frozenRowCount,gridProperties.frozenColumnCount'}})
reqs.append({'updateDimensionProperties': {
    'range': {'sheetId': lc, 'dimension': 'ROWS', 'startIndex': 0, 'endIndex': 1},
    'properties': {'pixelSize': 48}, 'fields': 'pixelSize'}})
for header, w in WIDTHS.items():
    a, b = span(header)
    reqs.append({'updateDimensionProperties': {
        'range': {'sheetId': lc, 'dimension': 'COLUMNS', 'startIndex': a, 'endIndex': b},
        'properties': {'pixelSize': w}, 'fields': 'pixelSize'}})

# warning-only protection on the non-input zones; the pre-v4 per-column warnings are superseded
meta = s.get(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}',
             params={'fields': 'sheets(properties.sheetId,protectedRanges(protectedRangeId,'
                               'description,range))'}).json()
existing = next((sh.get('protectedRanges', []) for sh in meta['sheets']
                 if sh['properties']['sheetId'] == lc), [])
LEGACY = 'Calculated -- edit the inputs, not this column'
WANT = [('Latest Round Date', 'Blend Check',
         'Wired from Companies/Funding Rounds/Floor Detail — edit those tabs instead'),
        ('Year 1 Rent ($)', 'QA Notes', 'Computed — edit inputs, not results')]
have = {p['description']: p for p in existing}
added = removed = 0
for first, last, desc in WANT:
    want_range = rng(first, last, 1)
    p = have.get(desc)
    if p is None:
        reqs.append({'addProtectedRange': {'protectedRange': {
            'range': want_range, 'description': desc, 'warningOnly': True}}})
        added += 1
    elif (p['range'].get('startColumnIndex'), p['range'].get('endColumnIndex')) != \
         (want_range['startColumnIndex'], want_range['endColumnIndex']):
        reqs.append({'updateProtectedRange': {'protectedRange': {
            'protectedRangeId': p['protectedRangeId'], 'range': want_range}, 'fields': 'range'}})
for p in existing:
    if p['description'] in (LEGACY, 'Wired from Companies/Funding Rounds — edit those tabs instead'):
        reqs.append({'deleteProtectedRange': {'protectedRangeId': p['protectedRangeId']}})
        removed += 1

batch_update(s, reqs)
print(f'Lease Comps styled: {len(reqs)} requests across {len(ZONES)} zones '
      f'({len(H)} columns; protections +{added} -{removed})')
if added or removed:
    changelog(s, 'STYLE', 'Lease Comps visual design re-applied by header name: zone-coloured '
              'headers, input/wired/computed/governance tints, zone rules, number formats, frozen '
              f'panes, column sizing, warning-only protection ({added} added, {removed} legacy '
              'removed).', '')
