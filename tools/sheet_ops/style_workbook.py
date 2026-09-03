"""Visual system for the tabs no other pass owns (formatting only — never values/formulas):
Start Here, Companies, Funding Rounds, Company Metrics, QA Harness, Changelog, _Schema, Reference.
Lease Comps is styled by style.py + polish.py; the Dashboard by dashboard_style.py; tab order and
tiering by polish.py. Same palette and type as those passes so the workbook reads as one system.

One palette, one type scale, one header treatment, one rule for colour meaning:
  white  = type here        cyan #ECFEFF = wired from another tab
  green  #F0FDF4 = computed here   amber #FFFBEB = governance / QA
Title bands and section labels on the two narrative tabs (Start Here, Dashboard),
uniform column headers on every table tab, per-column number formats and widths,
frozen panes, status colouring, tab colours and tab order. Re-runnable: the rules
it owns are replaced, not duplicated, and a Changelog receipt is written each run.
"""
from common import session, sheet_ids, batch_update, changelog, qa_status, SID

s = session()
ids = sheet_ids(s)

# ---------- palette / type (theme.py) ----------
from theme import (hx, FONT, CBRE_GREEN, SAGE, FOREST, OLIVE, DARK_GREEN, INK, MUTED, RULE, PAPER,
                   WIRE, CALC, GOV, WHITE, LIGHT, OK_BG, OK_FG, WARN_BG, WARN_FG, BAD_BG, BAD_FG,
                   NEUTRAL_BG, NEUTRAL_FG, TAB_PRIMARY, TAB_INPUT, TAB_MACHINERY)
NAVY, SLATE, SLATE2 = CBRE_GREEN, CBRE_GREEN, SAGE
GREEN_BG, GREEN_FG = OK_BG, OK_FG
AMBER_BG, AMBER_FG = WARN_BG, WARN_FG
RED_BG, RED_FG = BAD_BG, BAD_FG
GRAY_BG, GRAY_FG = NEUTRAL_BG, NEUTRAL_FG


def ci(letter):
    n = 0
    for ch in letter:
        n = n * 26 + ord(ch) - 64
    return n - 1


def rng(sid, c1, c2, r1, r2):
    """0-based half-open grid range from column letters and 1-based inclusive rows."""
    return {'sheetId': sid, 'startRowIndex': r1 - 1, 'endRowIndex': r2,
            'startColumnIndex': ci(c1), 'endColumnIndex': ci(c2) + 1}


def fmt(r, **f):
    fields = []
    cell = {}
    if 'bg' in f:
        cell['backgroundColor'] = hx(f['bg']); fields.append('backgroundColor')
    tf = {}
    for k in ('bold', 'italic'):
        if k in f:
            tf[k] = f[k]
    if 'size' in f:
        tf['fontSize'] = f['size']
    if 'fg' in f:
        tf['foregroundColor'] = hx(f['fg'])
    if 'font' in f:
        tf['fontFamily'] = f['font']
    if tf:
        cell['textFormat'] = tf
        fields.append('textFormat(' + ','.join(
            {'bold': 'bold', 'italic': 'italic', 'fontSize': 'fontSize',
             'foregroundColor': 'foregroundColor', 'fontFamily': 'fontFamily'}[k] for k in tf) + ')')
    if 'h' in f:
        cell['horizontalAlignment'] = f['h']; fields.append('horizontalAlignment')
    if 'v' in f:
        cell['verticalAlignment'] = f['v']; fields.append('verticalAlignment')
    if 'wrap' in f:
        cell['wrapStrategy'] = f['wrap']; fields.append('wrapStrategy')
    if 'num' in f:
        t, p = f['num']
        cell['numberFormat'] = {'type': t, 'pattern': p}; fields.append('numberFormat')
    return {'repeatCell': {'range': r, 'cell': {'userEnteredFormat': cell},
                           'fields': 'userEnteredFormat(' + ','.join(fields) + ')'}}


def widths(sid, spec):
    return [{'updateDimensionProperties': {
        'range': {'sheetId': sid, 'dimension': 'COLUMNS', 'startIndex': ci(c), 'endIndex': ci(c) + 1},
        'properties': {'pixelSize': w}, 'fields': 'pixelSize'}} for c, w in spec.items()]


def row_height(sid, r1, r2, px):
    return {'updateDimensionProperties': {
        'range': {'sheetId': sid, 'dimension': 'ROWS', 'startIndex': r1 - 1, 'endIndex': r2},
        'properties': {'pixelSize': px}, 'fields': 'pixelSize'}}


def sheet_props(sid, frozen_rows=None, frozen_cols=None, tab=None, gridlines=True, hidden=None, index=None):
    props, fields = {'sheetId': sid, 'gridProperties': {}}, []
    if frozen_rows is not None:
        props['gridProperties']['frozenRowCount'] = frozen_rows; fields.append('gridProperties.frozenRowCount')
    if frozen_cols is not None:
        props['gridProperties']['frozenColumnCount'] = frozen_cols; fields.append('gridProperties.frozenColumnCount')
    props['gridProperties']['hideGridlines'] = not gridlines; fields.append('gridProperties.hideGridlines')
    if tab:
        props['tabColorStyle'] = {'rgbColor': hx(tab)}; fields.append('tabColorStyle')
    if hidden is not None:
        props['hidden'] = hidden; fields.append('hidden')
    if index is not None:
        props['index'] = index; fields.append('index')
    return {'updateSheetProperties': {'properties': props, 'fields': ','.join(fields)}}


def header(sid, c1, c2, bg=SLATE, height=40):
    return [fmt(rng(sid, c1, c2, 1, 1), bg=bg, fg='#FFFFFF', bold=True, size=9, font=FONT,
                h='CENTER', v='MIDDLE', wrap='WRAP'),
            row_height(sid, 1, 1, height),
            {'updateBorders': {'range': rng(sid, c1, c2, 1, 1),
                               'bottom': {'style': 'SOLID_THICK', 'color': hx(NAVY)}}}]


def body(sid, c1, c2, r2, bg=WHITE):
    return [fmt(rng(sid, c1, c2, 2, r2), bg=bg, fg=INK, bold=False, italic=False, size=10, font=FONT,
                v='MIDDLE', wrap='CLIP')]


def zone_rule(sid, cols, r2):
    return [{'updateBorders': {'range': rng(sid, c, c, 1, r2),
                               'right': {'style': 'SOLID_MEDIUM', 'color': hx('#94A3B8')}}} for c in cols]


def status_cf(sid, r, mapping):
    """Whole-cell text-equals colouring. mapping: {value: (bg, fg)}."""
    return [{'addConditionalFormatRule': {'index': 0, 'rule': {'ranges': [r], 'booleanRule': {
        'condition': {'type': 'TEXT_EQ', 'values': [{'userEnteredValue': val}]},
        'format': {'backgroundColor': hx(bg), 'textFormat': {'foregroundColor': hx(fg), 'bold': True}}}}}}
        for val, (bg, fg) in mapping.items()]


def contains_cf(sid, r, mapping):
    return [{'addConditionalFormatRule': {'index': 0, 'rule': {'ranges': [r], 'booleanRule': {
        'condition': {'type': 'TEXT_CONTAINS', 'values': [{'userEnteredValue': val}]},
        'format': {'backgroundColor': hx(bg), 'textFormat': {'foregroundColor': hx(fg), 'bold': True}}}}}}
        for val, (bg, fg) in mapping.items()]


DATE = ('DATE', 'yyyy-mm-dd')
INT = ('NUMBER', '#,##0')
NUM1 = ('NUMBER', '#,##0.0')
USD = ('CURRENCY', '$#,##0')
USD2 = ('CURRENCY', '$#,##0.00')
PCT = ('PERCENT', '0.00%')

# ---------- reset the layers this script owns (bands, our conditional formats, merges) ----------
meta = s.get(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}', params={
    'fields': 'sheets(properties(sheetId,title),bandedRanges.bandedRangeId,conditionalFormats,merges)'}).json()
OWNED = {'Companies', 'Funding Rounds', 'Company Metrics', 'QA Harness',
         'Changelog', 'Start Here', 'Reference', '_Schema'}
reset = []
for sh in meta['sheets']:
    title, sid = sh['properties']['title'], sh['properties']['sheetId']
    if title not in OWNED:
        continue
    for b in sh.get('bandedRanges', []):
        reset.append({'deleteBanding': {'bandedRangeId': b['bandedRangeId']}})
    for i in range(len(sh.get('conditionalFormats', [])) - 1, -1, -1):
        reset.append({'deleteConditionalFormatRule': {'sheetId': sid, 'index': i}})
    for m in sh.get('merges', []):
        reset.append({'unmergeCells': {'range': m}})
if reset:
    batch_update(s, reset)
print(f'reset {len(reset)} owned layers (bands / conditional formats / merges)')

R = []

# ---------- Start Here (narrative) ----------
sid = ids['Start Here']
R += [fmt(rng(sid, 'A', 'F', 1, 60), bg=WHITE, fg=INK, bold=False, size=10, font=FONT, v='MIDDLE', wrap='WRAP')]
R += [{'mergeCells': {'range': rng(sid, 'A', 'B', 1, 1), 'mergeType': 'MERGE_ALL'}},
      {'mergeCells': {'range': rng(sid, 'A', 'B', 2, 2), 'mergeType': 'MERGE_ALL'}},
      fmt(rng(sid, 'A', 'B', 1, 1), bg=NAVY, fg='#FFFFFF', bold=True, size=16, v='MIDDLE'),
      fmt(rng(sid, 'A', 'B', 2, 2), bg=DARK_GREEN, fg='#CFE3DC', bold=False, size=10, v='MIDDLE'),
      row_height(sid, 1, 1, 44), row_height(sid, 2, 2, 36),
      fmt(rng(sid, 'A', 'B', 4, 4), bg=SLATE2, fg='#FFFFFF', bold=True, size=9, v='MIDDLE'),
      fmt(rng(sid, 'A', 'A', 5, 12), bg=PAPER, fg=MUTED, bold=True, size=10),
      fmt(rng(sid, 'A', 'B', 14, 14), bg=SLATE2, fg='#FFFFFF', bold=True, size=9, v='MIDDLE'),
      fmt(rng(sid, 'A', 'A', 15, 22), bg=PAPER, fg=MUTED, bold=True, size=10),
      fmt(rng(sid, 'B', 'B', 15, 22), bold=True, size=11, fg=INK),
      {'updateBorders': {'range': rng(sid, 'A', 'B', 5, 12), 'innerHorizontal': {'style': 'SOLID', 'color': hx(RULE)},
                         'bottom': {'style': 'SOLID', 'color': hx(RULE)}}},
      {'updateBorders': {'range': rng(sid, 'A', 'B', 15, 22), 'innerHorizontal': {'style': 'SOLID', 'color': hx(RULE)},
                         'bottom': {'style': 'SOLID', 'color': hx(RULE)}}}]
R += widths(sid, {'A': 170, 'B': 720})
R += status_cf(sid, rng(sid, 'B', 'B', 15, 16), {'PASS': (GREEN_BG, GREEN_FG), 'REVIEW': (AMBER_BG, AMBER_FG), 'FAIL': (RED_BG, RED_FG)})
R += contains_cf(sid, rng(sid, 'B', 'B', 16, 16), {'/': (GREEN_BG, GREEN_FG)})
R += [sheet_props(sid, frozen_rows=0, tab=TAB_PRIMARY, gridlines=False)]

# ---------- Companies (input) ----------
sid = ids['Companies']
R += header(sid, 'A', 'N') + body(sid, 'A', 'N', 1200)
R += [fmt(rng(sid, 'M', 'N', 1, 1), bg=SAGE), fmt(rng(sid, 'M', 'N', 2, 1200), bg=WIRE),
      fmt(rng(sid, 'N', 'N', 2, 1200), num=NUM1),
      fmt(rng(sid, 'A', 'A', 2, 1200), fg=MUTED, bold=True),
      fmt(rng(sid, 'B', 'B', 2, 1200), bold=True),
      fmt(rng(sid, 'F', 'F', 2, 1200), num=('NUMBER', '0'), h='CENTER')]
R += zone_rule(sid, ['B', 'G', 'L'], 1200)
R += widths(sid, {'A': 88, 'B': 180, 'C': 230, 'D': 190, 'E': 230, 'F': 70, 'G': 110,
                  'H': 320, 'I': 260, 'J': 260, 'K': 260, 'L': 300, 'M': 170, 'N': 120})
R += [sheet_props(sid, frozen_rows=1, frozen_cols=2, tab=TAB_INPUT)]

# ---------- Funding Rounds (input; C + J wired/computed) ----------
sid = ids['Funding Rounds']
R += header(sid, 'A', 'N') + body(sid, 'A', 'N', 3000)
R += [fmt(rng(sid, 'A', 'A', 2, 3000), fg=MUTED, bold=True),
      fmt(rng(sid, 'C', 'C', 2, 3000), bg=WIRE),
      fmt(rng(sid, 'J', 'J', 2, 3000), bg=CALC, num=('NUMBER', '0'), h='CENTER'),
      fmt(rng(sid, 'D', 'D', 2, 3000), num=('NUMBER', '0'), h='CENTER'),
      fmt(rng(sid, 'F', 'F', 2, 3000), num=DATE, h='CENTER'),
      fmt(rng(sid, 'G', 'G', 2, 3000), num=NUM1),
      fmt(rng(sid, 'I', 'I', 2, 3000), num=NUM1),
      fmt(rng(sid, 'M', 'M', 2, 3000), h='CENTER', bold=True, size=9)]
R += zone_rule(sid, ['C', 'J', 'M'], 3000)
R += widths(sid, {'A': 84, 'B': 88, 'C': 170, 'D': 56, 'E': 150, 'F': 100, 'G': 100, 'H': 240,
                  'I': 110, 'J': 84, 'K': 220, 'L': 240, 'M': 88, 'N': 340})
R += status_cf(sid, rng(sid, 'M', 'M', 2, 3000), {'REVIEW': (AMBER_BG, AMBER_FG), 'LOW': (GRAY_BG, GRAY_FG)})
R += [sheet_props(sid, frozen_rows=1, frozen_cols=2, tab=TAB_INPUT)]

# ---------- Company Metrics (all computed) ----------
sid = ids['Company Metrics']
R += header(sid, 'A', 'O', bg=FOREST) + body(sid, 'A', 'O', 1200, bg=CALC)
R += [fmt(rng(sid, 'A', 'A', 2, 1200), fg=MUTED, bold=True),
      fmt(rng(sid, 'B', 'B', 2, 1200), bold=True),
      fmt(rng(sid, 'C', 'C', 2, 1200), num=INT, h='CENTER'),
      fmt(rng(sid, 'D', 'D', 2, 1200), num=DATE, h='CENTER'),
      fmt(rng(sid, 'E', 'E', 2, 1200), num=INT),
      fmt(rng(sid, 'F', 'G', 2, 1200), num=USD2),
      fmt(rng(sid, 'H', 'H', 2, 1200), num=USD),
      fmt(rng(sid, 'I', 'I', 2, 1200), num=('NUMBER', '0.0'), h='CENTER'),
      fmt(rng(sid, 'J', 'J', 2, 1200), num=('NUMBER', '0'), h='CENTER'),
      fmt(rng(sid, 'K', 'K', 2, 1200), num=DATE, h='CENTER'),
      fmt(rng(sid, 'M', 'M', 2, 1200), num=NUM1),
      fmt(rng(sid, 'N', 'N', 2, 1200), num=('NUMBER', '0.0'), h='CENTER')]
R += zone_rule(sid, ['B', 'I'], 1200)
R += widths(sid, {'A': 88, 'B': 180, 'C': 80, 'D': 110, 'E': 90, 'F': 100, 'G': 90, 'H': 100,
                  'I': 70, 'J': 80, 'K': 110, 'L': 150, 'M': 120, 'N': 100, 'O': 150})
R += [sheet_props(sid, frozen_rows=1, frozen_cols=2, tab=TAB_MACHINERY)]

# ---------- QA Harness (governance) ----------
sid = ids['QA Harness']
R += header(sid, 'A', 'F', bg=OLIVE) + body(sid, 'A', 'F', 40)
R += [fmt(rng(sid, 'A', 'A', 2, 40), fg=MUTED, bold=True),
      fmt(rng(sid, 'B', 'B', 2, 40), h='CENTER', size=9, bold=True),
      fmt(rng(sid, 'D', 'F', 2, 40), h='CENTER'),
      fmt(rng(sid, 'C', 'C', 2, 40), wrap='WRAP'),
      fmt(rng(sid, 'A', 'F', 24, 25), bg=PAPER, bold=True),
      {'updateBorders': {'range': rng(sid, 'A', 'F', 24, 24), 'top': {'style': 'SOLID_MEDIUM', 'color': hx(NAVY)}}}]
R += widths(sid, {'A': 84, 'B': 90, 'C': 420, 'D': 90, 'E': 90, 'F': 90})
R += status_cf(sid, rng(sid, 'F', 'F', 2, 40), {'PASS': (GREEN_BG, GREEN_FG), 'FAIL': (RED_BG, RED_FG),
                                                 'INFO': (GRAY_BG, GRAY_FG), 'REVIEW': (AMBER_BG, AMBER_FG)})
R += status_cf(sid, rng(sid, 'B', 'B', 2, 40), {'CRITICAL': (WHITE, RED_FG), 'HIGH': (WHITE, AMBER_FG), 'MEDIUM': (WHITE, MUTED)})
R += [sheet_props(sid, frozen_rows=1, tab=TAB_MACHINERY)]

# ---------- Changelog (append-only receipts) ----------
sid = ids['Changelog']
R += header(sid, 'A', 'E', bg=OLIVE) + body(sid, 'A', 'E', 1037)
R += [fmt(rng(sid, 'A', 'A', 2, 1037), fg=MUTED, size=9), fmt(rng(sid, 'C', 'C', 2, 1037), bold=True, size=9),
      fmt(rng(sid, 'E', 'E', 2, 1037), h='CENTER')]
R += widths(sid, {'A': 130, 'B': 190, 'C': 190, 'D': 720, 'E': 100})
R += [sheet_props(sid, frozen_rows=1, tab=TAB_MACHINERY)]

# ---------- _Schema (machine contract) ----------
sid = ids['_Schema']
R += header(sid, 'A', 'J', bg=SAGE) + body(sid, 'A', 'J', 971)
R += [fmt(rng(sid, 'A', 'A', 2, 971), bold=True, fg=MUTED), fmt(rng(sid, 'B', 'B', 2, 971), h='CENTER', bold=True),
      fmt(rng(sid, 'D', 'G', 2, 971), h='CENTER', size=9), fmt(rng(sid, 'I', 'I', 2, 971), size=9, fg=MUTED)]
R += widths(sid, {'A': 120, 'B': 56, 'C': 210, 'D': 110, 'E': 60, 'F': 60, 'G': 70, 'H': 190, 'I': 320, 'J': 460})
R += status_cf(sid, rng(sid, 'F', 'F', 2, 971), {'calc': (CALC, GREEN_FG), 'qa': (GOV, AMBER_FG), 'meta': (GRAY_BG, GRAY_FG)})
R += [sheet_props(sid, frozen_rows=1, tab=TAB_MACHINERY)]

# ---------- Reference (vocabularies) ----------
sid = ids['Reference']
R += header(sid, 'A', 'R', bg=SAGE) + body(sid, 'A', 'R', 1000)
R += [fmt(rng(sid, 'I', 'I', 1, 1), bg=WHITE), fmt(rng(sid, 'L', 'L', 1, 1), bg=WHITE)]
R += [fmt(rng(sid, c, c, 1, 1), bg=WHITE) for c in ('I', 'L', 'M', 'N', 'Q')]
R += widths(sid, {c: 170 for c in 'ABCDEFGHJKOPR'}) + widths(sid, {'I': 24, 'L': 24, 'M': 24, 'N': 24, 'Q': 24})
R += [sheet_props(sid, frozen_rows=1, tab=TAB_MACHINERY)]

# ---------- backup tab out of the way (tab order + tiering belong to polish.py) ----------
if 'LC_BACKUP_2026-09-02' in ids:
    R.append({'updateSheetProperties': {'properties': {'sheetId': ids['LC_BACKUP_2026-09-02'], 'hidden': True,
                                                        'tabColorStyle': {'rgbColor': hx(TAB_MACHINERY)}},
                                        'fields': 'hidden,tabColorStyle'}})

# batch in chunks (the API caps request payloads)
for i in range(0, len(R), 120):
    batch_update(s, R[i:i + 120])
print(f'applied {len(R)} formatting requests across {len(OWNED)} tabs')

summary, fails = qa_status(s)
print('QA:', summary, '| failing:', fails or 'none')
changelog(s, 'STYLE', 'Supporting-tab visual system (Start Here, Companies, Funding Rounds, Company Metrics, QA Harness, Changelog, _Schema, Reference): unified type (Roboto 10), header bands, colour-by-meaning '
          '(white input / cyan wired / green computed / amber governance), per-column number formats and widths, '
          'frozen panes, status colouring on QA/Funding Rounds/Start Here, tab colours; LC_BACKUP hidden.', '')
print('receipt appended')
