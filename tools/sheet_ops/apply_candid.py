"""Resolve the Candid Health / "Candid Group" question (JD, 2026-09-15).

NYC_MTS_Comps_-_25000_Jan_2025_-_YTD_03.26.26 carries a "Candid Group" row at 675 Avenue of
the Americas, P3, January 2026, seven years — the same building, floor and month as LC-0032,
but under a different name and with a seven-step rent from $55 against the book's flat $58.

JD: it is the same deal. The deck's rent is simply the annual escalation written out. That
reconciles exactly — the steps are 2.5% a year off $55:

    deck   $55.00 / $56.38 / $57.78 / $59.23 / $60.71 / $62.23 / $63.78
    2.5%   $55.00 / $56.37 / $57.78 / $59.23 / $60.71 / $62.23 / $63.78

The workbook models rent as flat tranches, so an annually escalating schedule is carried at a
single representative rate; JD's $58 stands (the schedule averages $59.30, midpoint $59.23).

His rulings on the remaining fields: take the deck on RSF and free rent, keep his own $30/SF
TI. The $30 was entered from direct knowledge on 2026-09-03 and is the same carve-out he
applied at 360 Park Avenue South — a figure he set personally beats the deck. Delivery
therefore stays Custom TIA, which is what a $30 allowance requires.

"Candid Group" is registered in Reference!VariantMap so the as-reported name resolves to the
canonical company rather than looking like a second tenant next time.
"""
from common import session, get_values, values_batch, changelog, qa_status, headers

FIX = dict(rsf=28687, free=6)
NOTE = ('JD 9/15: NYC_MTS_Comps_25000_03.26.26 reports this as "Candid Group" at 28,687 SF with '
        'a seven-step rent from $55 — the same deal, with the annual escalation written out '
        '(2.5%/yr: $55.00 / $56.38 / $57.78 / $59.23 / $60.71 / $62.23 / $63.78, averaging '
        '$59.30). The workbook models flat tranches, so it is carried at JD\'s single $58 rate. '
        'RSF and free rent follow the deck (28,687 SF, 6 months); the $30/SF TI is JD\'s own '
        'figure and stands against the deck\'s $0.')
VARIANT = ('Candid Group', 'Candid Health')

s = session()
H = headers(s, 'Lease Comps')
rows = get_values(s, "'Lease Comps'!A2:AS1206", render='FORMATTED_VALUE')


def col(r, hdr):
    i = 0
    for ch in H[hdr]:
        i = i * 26 + ord(ch) - 64
    return str(r[i-1]) if i-1 < len(r) else ''


def same(a, b):
    return (str(a).replace('$', '').replace(',', '').strip()
            == str(b).replace('$', '').replace(',', '').strip())


M = {'rsf': 'RSF', 'free': 'Free Rent (months)'}
data, log = [], []
for i, r in enumerate(rows, 2):
    if col(r, 'Comp ID') != 'LC-0032':
        continue
    for k, hdr in M.items():
        if not same(col(r, hdr), FIX[k]):
            data.append({'range': f"'Lease Comps'!{H[hdr]}{i}", 'values': [[FIX[k]]]})
            log.append(f'   LC-0032 {hdr:20} {col(r, hdr)!r} -> {FIX[k]!r}')
    ex = col(r, 'Notes').strip()
    if NOTE not in ex:
        data.append({'range': f"'Lease Comps'!{H['Notes']}{i}",
                     'values': [[(ex + ' ' if ex else '') + NOTE]]})
if data:
    values_batch(s, data)
    print(f'LC-0032 updated ({len(log)} fields):')
    for l in log:
        print(l)
    print('   TI stays $30 and delivery stays Custom TIA — JD\'s own figure')
else:
    print('LC-0032 already current')

# --- variant name so the deck's wording resolves next time
vm = get_values(s, 'Reference!J2:K40', render='FORMATTED_VALUE')
have = {r[0] for r in vm if r and r[0]}
if VARIANT[0] in have:
    print(f'\nReference!VariantMap already carries {VARIANT[0]!r}')
else:
    nxt = 2 + len([r for r in vm if r and r[0]])
    values_batch(s, [{'range': f'Reference!J{nxt}:K{nxt}', 'values': [list(VARIANT)]}])
    print(f'\nReference!VariantMap: {VARIANT[0]!r} -> {VARIANT[1]!r}')

changelog(s, 'CANDID RESOLVED',
          'The "Candid Group" row in NYC_MTS_Comps_25000_03.26.26 is the same deal as LC-0032 '
          '(Candid Health), not a second tenant — JD confirmed, and its seven-step rent is simply '
          "the annual escalation written out, reconciling to 2.5%/yr off $55. The book's flat $58 "
          'stands, as the workbook models rent in flat tranches. RSF 25,000 -> 28,687 and free '
          "rent 7 -> 6 months follow the deck per JD; the $30/SF TI is JD's own figure from "
          "2026-09-03 and beats the deck's $0, so delivery stays Custom TIA. \"Candid Group\" "
          'registered in Reference!VariantMap.', len(log) + 1)

summary, fails = qa_status(s)
print('\nQA:', summary, '| failing:', fails or 'none')
