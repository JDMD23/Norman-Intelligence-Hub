"""Apply JD's seat-count answers from the 2026-09-06 density pass.

23 comps carried no seat count — 2,591,445 RSF, 55% of the book — which meant Cost/Seat,
RSF/Seat and the Dashboard's Avg cost/seat were all computed off the other 90. Seats cannot
be sourced from anywhere: they come from JD's own knowledge of how the space was laid out.

He was asked about all 23. Three have a number; the other twenty he has no insight into,
because they are custom build-outs where the tenant's real estate team set the layout. That
is a real answer, not a gap, and a guessed seat count on a 462,000 SF comp would move the
Dashboard's cost/seat more than any other single entry in the book. Blank is correct.

All three figures are approximate, in JD's words, and the note says so — Cost/Seat on these
comps is indicative, not a quoted number.

Idempotent: writes only what differs.
"""
from common import session, get_values, values_batch, changelog, qa_status, headers

# comp -> (seats, note)
SEATS = {
    'LC-0110': (600, 'JD: approx density ~600 seats'),
    'LC-0104': (620, 'JD: ~620 seats, approximate for now'),
    'LC-0087': (45,  'JD: ~45 seats'),
}

s = session()
H = headers(s, 'Lease Comps')
SEAT, NOTE, RSF = H['Seats'], H['Notes'], H['RSF']
rows = get_values(s, "'Lease Comps'!A2:AS1206", render='FORMATTED_VALUE')


def col(r, letter):
    i = 0
    for ch in letter:
        i = i * 26 + ord(ch) - 64
    return str(r[i-1]) if i-1 < len(r) else ''


def num(v):
    try:
        return float(str(v).replace('$', '').replace(',', ''))
    except ValueError:
        return None


data, applied = [], []
for i, r in enumerate(rows, 2):
    cid = col(r, H['Comp ID'])
    if cid not in SEATS:
        continue
    seats, note = SEATS[cid]
    if num(col(r, SEAT)) != seats:
        data.append({'range': f"'Lease Comps'!{SEAT}{i}", 'values': [[seats]]})
        rsf = num(col(r, RSF)) or 0
        applied.append(f'  {cid}  {col(r, H["Tenant"]):16} {rsf:>8,.0f} SF -> {seats} seats '
                       f'({rsf/seats:.0f} RSF/seat)')
    existing = col(r, NOTE).strip()
    if note not in existing:
        data.append({'range': f"'Lease Comps'!{NOTE}{i}",
                     'values': [[(existing + ' ' if existing else '') + note + '.']]})

if not data:
    print('nothing to apply — every seat count is already in the sheet')
else:
    values_batch(s, data)
    print(f'{len(data)} cells written')
    for a in applied:
        print(a)
    changelog(s, 'SEAT COUNTS',
              'JD was asked about all 23 comps carrying no seat count. Three have an approximate '
              'figure (LC-0110 Legora ~600, LC-0104 Suno AI ~620, LC-0087 Peregrine ~45) and are '
              'noted as approximate. The other twenty stay blank: they are custom build-outs whose '
              'layout JD has no insight into, and a guessed seat count on a comp that size would '
              'move the Dashboard cost/seat more than any real number in the book. Seat coverage '
              'goes from 90 to 93 of 113 comps.', len(applied))

summary, fails = qa_status(s)
print('\nQA:', summary, '| failing:', fails or 'none')
