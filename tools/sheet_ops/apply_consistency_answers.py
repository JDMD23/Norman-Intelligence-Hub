"""Apply JD's answers from the 2026-09-06 consistency audit.

Three groups, all of them the same kind of defect: a value that was either inconsistent with
itself or simply absent.

1. Submarket contradictions and splits. A building cannot sit in two submarkets, and a
   submarket entered two ways splits its comps across two weaker Dashboard rows. JD ruled:
     · 1 Madison Avenue is PAS / Mad. Square Park — Sigma was the odd one out of four.
     · 675 Avenue of the Americas is Flatiron — a genuine border building, called for Flatiron.
     · 837 Washington Street is Meatpacking, which retires "Chelsea/Meatpacking" entirely.
     · The whole Penn cluster consolidates into "Hudson Yards / Penn Station", which retires
       "Penn Station" — 1245 Broadway and 1375 Broadway included, JD's call.
   Reference drops from 15 submarkets to 13 and the dropdown narrows with it.

2. Building class on the eight recent survey comps. Five are JD's answers; three are read
   straight off another comp in the same building and were never in question:
   295 Fifth (LC-0042), 2 Penn Plaza (LC-0051) and 11 Madison (LC-0020, LC-0064).

3. Condition on the four comps that lacked it. Monday.com is Second Gen — it is a renewal of
   space the tenant already occupied; the other three built from raw.

LC-0064 (Tempus) stays untouched: JD does not have the TIA, so TI stays blank and the comp
keeps computing no NER. That is the contract working, not a gap to paper over.

Idempotent: writes only what differs.
"""
import re
from common import session, get_values, values_batch, batch_update, changelog, qa_status, \
    headers, sheet_ids, named_ranges

SUBMARKET = {
    'LC-0093': ('PAS / Mad. Square Park', '1 Madison Avenue matches its three neighbours'),
    'LC-0012': ('Flatiron',               '675 Avenue of the Americas is Flatiron per JD'),
    'LC-0049': ('Meatpacking',            '837 Washington Street is Meatpacking per JD'),
    'LC-0059': ('Hudson Yards / Penn Station', 'Penn cluster consolidated per JD'),
    'LC-0067': ('Hudson Yards / Penn Station', 'Penn cluster consolidated per JD'),
    'LC-0089': ('Hudson Yards / Penn Station', 'Penn cluster consolidated per JD'),
}
RETIRE = {'Chelsea/Meatpacking', 'Penn Station'}

BUILDING_CLASS = {
    'LC-0104': ('Class A', 'matches LC-0042 at 295 Fifth Avenue'),
    'LC-0105': ('Class A', 'JD: 330 Hudson Street'),
    'LC-0106': ('Trophy',  'matches LC-0051 at 2 Penn Plaza'),
    'LC-0107': ('Class A', 'JD: 95 Morton Street'),
    'LC-0108': ('Class A', 'JD: 345 Hudson Street'),
    'LC-0109': ('Class A', 'JD: 225 Park Avenue South'),
    'LC-0110': ('Trophy',  'matches LC-0020 and LC-0064 at 11 Madison Avenue'),
    'LC-0112': ('Class A', 'JD: 225 Park Avenue South'),
}
CONDITION = {
    'LC-0107': ('Raw',         'JD'),
    'LC-0108': ('Raw',         'JD'),
    'LC-0109': ('Second Gen',  'JD: built already — the deal is a renewal'),
    'LC-0113': ('Raw',         'JD'),
}

# the survey notes said class/condition were unavailable; they are now answered
STALE = [
    (r'\s*Seats/class/condition not on the survey\.', ' Seats not on the survey.'),
    (r'\s*Seats, building class and condition are not on the survey\.', ' Seats not on the survey.'),
    (r'\s*Building class and condition not stated\.', ''),
]

s = session()
H = headers(s, 'Lease Comps')
SUB, CLS, CND, NOTE = H['Submarket'], H['Building Class'], H['Condition'], H['Notes']
rows = get_values(s, "'Lease Comps'!A2:AS1206", render='FORMATTED_VALUE')


def col(r, letter):
    i = 0
    for ch in letter:
        i = i * 26 + ord(ch) - 64
    return str(r[i-1]) if i-1 < len(r) else ''


# --- 1. Reference first: the new values must exist before the comps can hold them
ref = [r[0] if r else '' for r in get_values(s, 'Reference!A2:A40', render='FORMATTED_VALUE')]
kept = sorted({v for v in ref if v} - RETIRE, key=str.lower)
last = 1 + len(kept)
if [v for v in ref if v] != kept:
    pad = kept + [''] * (len(ref) - len(kept))
    values_batch(s, [{'range': f'Reference!A2:A{1 + len(pad)}', 'values': [[v] for v in pad]}])
    print(f'Reference!Submarkets: {len([v for v in ref if v])} -> {len(kept)} '
          f'(retired {", ".join(sorted(RETIRE))})')
else:
    print(f'Reference!Submarkets: already {len(kept)} values')

# --- 2. the comps
data, log = [], []
for i, r in enumerate(rows, 2):
    cid = col(r, H['Comp ID'])
    if not cid:
        continue
    note_bits = []
    for hdr, table in ((SUB, SUBMARKET), (CLS, BUILDING_CLASS), (CND, CONDITION)):
        if cid in table:
            want, why = table[cid]
            cur = col(r, hdr)
            if cur != want:
                data.append({'range': f"'Lease Comps'!{hdr}{i}", 'values': [[want]]})
                log.append(f'  {cid}  {cur!r} -> {want!r}   ({why})')
                note_bits.append(f'{want} ({why})')
    note = col(r, NOTE)
    fixed = note
    for pat, sub in STALE:
        fixed = re.sub(pat, sub, fixed)
    if note_bits:
        add = 'JD 9/6: ' + '; '.join(note_bits) + '.'
        if add not in fixed:
            fixed = (fixed.rstrip() + ' ' + add).strip()
    if fixed != note:
        data.append({'range': f"'Lease Comps'!{NOTE}{i}", 'values': [[re.sub(r'\s+', ' ', fixed).strip()]]})

if data:
    values_batch(s, data)
    print(f'\n{len(data)} cells written')
    for l in log:
        print(l)
else:
    print('\nnothing to apply — every answer is already in the sheet')

# --- 3. narrow the named range and the dropdown
lc = sheet_ids(s)['Lease Comps']
nr = named_ranges(s)['Submarkets']
reqs = []
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
print(f'named range + dropdown -> Reference!A2:A{last}')

if data:
    changelog(s, 'CONSISTENCY ANSWERS',
              'Applied JD\'s answers to the 2026-09-06 consistency audit. Submarkets: 1 Madison '
              'Avenue settled on PAS / Mad. Square Park (Sigma was the outlier of four), 675 Avenue '
              'of the Americas on Flatiron, 837 Washington Street on Meatpacking, and the whole Penn '
              'cluster consolidated into Hudson Yards / Penn Station. "Chelsea/Meatpacking" and '
              '"Penn Station" retired from Reference (15 -> 13 submarkets) and the dropdown narrowed '
              'so they cannot be picked again. Building class filled on 8 comps (5 from JD, 3 read '
              'off another comp in the same building) and condition on 4. LC-0064 (Tempus) left '
              'alone — JD does not have the TIA, so TI stays blank and the comp computes no NER.',
              len(log))

summary, fails = qa_status(s)
print('\nQA:', summary, '| failing:', fails or 'none')
