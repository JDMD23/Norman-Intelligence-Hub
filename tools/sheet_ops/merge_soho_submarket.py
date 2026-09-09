"""Merge the duplicate SoHo submarket labels into one.

The book carried both `SoHo` (13 comps) and `Soho/Noho` (9 comps) — one submarket entered
two ways, splitting 22 comps into two weaker rows on the Dashboard's submarket table with
near-identical economics ($101.54 / $102.89 starting rent). JD's canonical spelling is
`SoHo/NoHo`.

Rewrites Reference!Submarkets first (contract: vocabulary lives in Reference, add there
before using), then the comps, then narrows the named range and the Submarket dropdown to
the shorter list. The Dashboard submarket table ranks submarkets dynamically off
LeaseComps_Submarkets, so it re-forms on its own.

Idempotent: writes only what differs.
"""
from common import session, get_values, values_batch, batch_update, changelog, qa_status, \
    headers, sheet_ids, named_ranges, SID

CANON = 'SoHo/NoHo'
MERGE = {'SoHo', 'Soho/Noho', 'SoHo/NoHo'}

s = session()
H = headers(s, 'Lease Comps')
SUB = H['Submarket']

# --- 1. Reference vocabulary
ref = [r[0] if r else '' for r in get_values(s, 'Reference!A2:A40', render='FORMATTED_VALUE')]
kept = sorted({v for v in ref if v and v not in MERGE} | {CANON}, key=str.lower)
if [v for v in ref if v] != kept:
    pad = kept + [''] * (len(ref) - len(kept))
    values_batch(s, [{'range': f'Reference!A2:A{1 + len(pad)}', 'values': [[v] for v in pad]}])
    print(f'Reference!Submarkets: {len([v for v in ref if v])} -> {len(kept)} values')
else:
    print(f'Reference!Submarkets: already {len(kept)} values')
last = 1 + len(kept)

# --- 2. the comps
subs = get_values(s, f"'Lease Comps'!{SUB}2:{SUB}1206", render='FORMATTED_VALUE')
data, moved = [], []
for i, r in enumerate(subs, 2):
    v = r[0] if r else ''
    if v in MERGE and v != CANON:
        data.append({'range': f"'Lease Comps'!{SUB}{i}", 'values': [[CANON]]})
        moved.append(v)
if data:
    values_batch(s, data)
    print(f'Lease Comps: {len(data)} comps -> {CANON!r} '
          f'({moved.count("SoHo")} from "SoHo", {moved.count("Soho/Noho")} from "Soho/Noho")')
else:
    print('Lease Comps: already merged')

# --- 3. narrow the named range and the dropdown to the shorter list
reqs, lc = [], sheet_ids(s)['Lease Comps']
nr = named_ranges(s)['Submarkets']
if nr['range'].get('endRowIndex') != last:
    reqs.append({'updateNamedRange': {
        'namedRange': {'namedRangeId': nr['namedRangeId'], 'name': 'Submarkets',
                       'range': dict(nr['range'], endRowIndex=last)},
        'fields': 'range'}})
reqs.append({'setDataValidation': {
    'range': {'sheetId': lc, 'startRowIndex': 1, 'endRowIndex': 1206,
              'startColumnIndex': ord(SUB) - 65, 'endColumnIndex': ord(SUB) - 64},
    'rule': {'condition': {'type': 'ONE_OF_RANGE',
                           'values': [{'userEnteredValue': f'=Reference!$A$2:$A${last}'}]},
             'inputMessage': 'Pick from Reference!Submarkets (new values: add there first).',
             'strict': False, 'showCustomUi': True}}})
batch_update(s, reqs)
print(f'named range + dropdown narrowed to Reference!A2:A{last}')

if data:
    changelog(s, 'VOCAB MERGE',
              f'Submarket "SoHo" ({moved.count("SoHo")} comps) and "Soho/Noho" '
              f'({moved.count("Soho/Noho")} comps) merged into "{CANON}" per JD — one submarket '
              'entered two ways, splitting 22 comps across two Dashboard benchmark rows with '
              'near-identical economics. Reference narrowed to 15 submarkets; dropdown repointed.',
              len(data))

summary, fails = qa_status(s)
print('\nQA:', summary, '| failing:', fails or 'none')
