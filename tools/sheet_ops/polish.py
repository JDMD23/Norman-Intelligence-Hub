"""Workbook polish pass: make the daily-use surface crisp and put the machinery away.

Everything here is presentation only — no values, formulas, or structure change, so it
is safe to re-run and easy to reverse (notes below each section say how).

  1. Tab tiering      hide the four pure-machinery tabs; order the rest front-to-back.
  2. Hide Company ID  column D is a join key, not something a human reads.
  3. Column groups    collapse funding detail, concession restatements, ratios, QA notes.
  4. Status colors    READY / NEEDS REVIEW / STALE / MISSING INPUTS read as color.
  5. Banded rows      per zone, so row-scanning and the zone tint scheme coexist.
"""
from common import session, batch_update, changelog, SID

# Machinery: load-bearing (Company Metrics alone feeds 199 wired cells) but never browsed.
HIDE_TABS = ['Company Metrics', 'QA Harness', 'Changelog', '_Schema']
# Front-to-back order for whatever stays visible.
ORDER = ['Dashboard', 'Lease Comps', 'Companies', 'Funding Rounds', 'Start Here']

# Collapsed column groups: (first, last, why)
GROUPS = [('V', 'Y', 'funding round detail'),
          ('AD', 'AE', 'concession $ restatements'),
          ('AK', 'AM', 'funding ratios'),
          ('AO', 'AO', 'QA notes')]

# Status pills: value -> (background, text)
STATUS = [('READY', '#DCFCE7', '#166534'),
          ('NEEDS REVIEW', '#FEF3C7', '#92400E'),
          ('STALE - REVERIFY', '#FEE2E2', '#991B1B'),
          ('MISSING INPUTS', '#E2E8F0', '#334155')]

# Zone banding: (first, last, base color, alternate) — alternate is a touch deeper so
# the eye can track a row across 30+ columns without losing the zone colour coding.
BANDS = [('A', 'U', '#FFFFFF', '#F8FAFC'), ('V', 'AA', '#ECFEFF', '#DDF5F9'),
         ('AB', 'AB', '#FFFFFF', '#F8FAFC'), ('AC', 'AM', '#F0FDF4', '#E2F7E9'),
         ('AN', 'AO', '#FFFBEB', '#FCF2D9')]

NROWS = 1207


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
meta = s.get(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}', params={'fields':
             'sheets(properties(sheetId,title,index,hidden),columnGroups,bandedRanges,'
             'conditionalFormats)'}).json()
tabs = {sh['properties']['title']: sh for sh in meta['sheets']}
lc_sheet = tabs['Lease Comps']
lc = lc_sheet['properties']['sheetId']


def rng(c1, c2, r1=0, r2=NROWS):
    return {'sheetId': lc, 'startRowIndex': r1, 'endRowIndex': r2,
            'startColumnIndex': ci(c1), 'endColumnIndex': ci(c2) + 1}


reqs, notes = [], []

# --- 1. tab tiering (reverse with: unhide from the sheet tab bar's "All sheets" menu)
for title in HIDE_TABS:
    sh = tabs.get(title)
    if sh and not sh['properties'].get('hidden'):
        reqs.append({'updateSheetProperties': {'properties': {
            'sheetId': sh['properties']['sheetId'], 'hidden': True}, 'fields': 'hidden'}})
        notes.append(f'hid tab "{title}"')
for i, title in enumerate(ORDER):
    sh = tabs.get(title)
    if sh and sh['properties']['index'] != i:
        reqs.append({'updateSheetProperties': {'properties': {
            'sheetId': sh['properties']['sheetId'], 'index': i}, 'fields': 'index'}})
# the pre-migration backup should not be the first thing the workbook opens on
bk = tabs.get('LC_BACKUP_2026-09-02')
if bk and bk['properties']['index'] < len(meta['sheets']) - 1:
    reqs.append({'updateSheetProperties': {'properties': {
        'sheetId': bk['properties']['sheetId'], 'index': len(meta['sheets']) - 1},
        'fields': 'index'}})
    notes.append('moved LC_BACKUP to the end')

# --- 2. hide Company ID (reverse: select C:E, right-click, unhide)
reqs.append({'updateDimensionProperties': {
    'range': {'sheetId': lc, 'dimension': 'COLUMNS', 'startIndex': ci('D'), 'endIndex': ci('D') + 1},
    'properties': {'hiddenByUser': True}, 'fields': 'hiddenByUser'}})
notes.append('hid Company ID (col D) — join key, still wired to everything')

# --- 3. collapsed column groups (reverse: click the +/- bar above the columns)
have_groups = {(g['range']['startIndex'], g['range']['endIndex'])   # DimensionRange keys
               for g in lc_sheet.get('columnGroups', [])}
for c1, c2, why in GROUPS:
    key = (ci(c1), ci(c2) + 1)
    # already grouped if any existing group covers the span (a later column insert can
    # widen a group, e.g. AO -> AO:AP once the cohort column landed)
    if any(a <= key[0] and b >= key[1] for a, b in have_groups):
        continue
    grange = {'sheetId': lc, 'dimension': 'COLUMNS', 'startIndex': key[0], 'endIndex': key[1]}
    reqs.append({'addDimensionGroup': {'range': grange}})
    reqs.append({'updateDimensionGroup': {'dimensionGroup': {
        'range': grange, 'depth': 1, 'collapsed': True}, 'fields': 'collapsed'}})
    notes.append(f'grouped {c1}:{c2} ({why}), collapsed')

# --- 4. status colors (replace any prior rules on the status column)
for i, cf in reversed(list(enumerate(lc_sheet.get('conditionalFormats', [])))):
    if any(r.get('startColumnIndex') == ci('AN') for r in cf.get('ranges', [])):
        reqs.append({'deleteConditionalFormatRule': {'sheetId': lc, 'index': i}})
for i, (val, bg, fg) in enumerate(STATUS):
    reqs.append({'addConditionalFormatRule': {'index': i, 'rule': {
        'ranges': [rng('AN', 'AN', 1)],
        'booleanRule': {
            'condition': {'type': 'TEXT_EQ', 'values': [{'userEnteredValue': val}]},
            'format': {'backgroundColor': hx(bg),
                       'textFormat': {'foregroundColor': hx(fg), 'bold': True}}}}}})
notes.append(f'{len(STATUS)} status colour rules')

# --- 5. per-zone banded rows (reverse: Format > Alternating colours > Remove)
for b in lc_sheet.get('bandedRanges', []):
    reqs.append({'deleteBanding': {'bandedRangeId': b['bandedRangeId']}})
for c1, c2, first, second in BANDS:
    reqs.append({'addBanding': {'bandedRange': {
        'range': rng(c1, c2, 1),
        'rowProperties': {'firstBandColor': hx(first), 'secondBandColor': hx(second)}}}})
notes.append(f'{len(BANDS)} zone-aware banded ranges')

batch_update(s, reqs)
print(f'polish applied ({len(reqs)} requests)')
for n in notes:
    print('  ', n)
changelog(s, 'POLISH',
          'Presentation pass (no data/formula change): machinery tabs hidden (Company Metrics, '
          'QA Harness, Changelog, _Schema) and visible tabs ordered Dashboard > Lease Comps > '
          'Companies > Funding Rounds; Company ID column hidden; funding detail, concession '
          'restatements, ratios and QA notes put in collapsed column groups; Record Status shown '
          'as colour; per-zone banded rows. Date Signed and Latest Round Date now display as '
          '"July 2026" (day was always a placeholder).', '')
