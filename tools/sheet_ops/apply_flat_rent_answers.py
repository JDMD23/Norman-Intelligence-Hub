"""Apply JD's escalation answers for the 17 long-term comps recorded at flat rent.

A lease longer than five years with a blank Rent P2 asserts flat rent for the whole term.
Sometimes that is true; often it just meant nobody had entered the bump. Seventeen comps
were in that state, together 1.4M SF. JD answered each one in session.

Four carry a real escalation and get a Rent P2 (LC-0086 also corrects its P1). The other
thirteen are genuinely flat and get a note saying so, which is the point: an unanswered
blank and a confirmed-flat blank look identical in the sheet, and the note is what stops
this audit from re-raising them.

LC-0095 (Runway) also gets a building and RSF correction — the comp was recorded at
71 Fifth Avenue / 16,000 SF; the deal is 18 West 18th Street / 16,504 SF.

Idempotent: writes only cells that differ.
"""
from common import session, get_values, values_batch, changelog, qa_status, headers

# comp -> Rent P2 (years 6+), optional Rent P1 correction, note
ESCALATIONS = {
    'LC-0093': dict(p1=105, p2=115, note='JD: $105/SF years 1-5, $115/SF years 6+'),
    'LC-0086': dict(p1=79,  p2=84,  note='JD: $79/SF years 1-5, $84/SF years 6-7 (P1 corrected from $76)'),
    'LC-0004': dict(p2=85,          note='JD: bump to $85/SF for years 6-7'),
    'LC-0088': dict(p2=84,          note='JD: bump to $84/SF for years 6-7'),
}

# comps JD confirmed carry no escalation — blank P2 is the right answer, not a gap
FLAT = {
    'LC-0024': 'JD: confirmed flat for the full term',
    'LC-0012': 'JD: confirmed flat for the full term',
    'LC-0103': 'JD: confirmed flat for the full term',
    'LC-0072': 'JD: confirmed flat for the full term',
    'LC-0055': 'JD: confirmed flat for the full term',
    'LC-0032': 'JD: confirmed flat for the full term',
    'LC-0101': 'JD: confirmed flat, no bump in base rent',
    'LC-0039': 'JD: confirmed flat, no bump in base rent',
    'LC-0089': 'JD: confirmed flat, no bump in base rent',
    'LC-0045': 'JD: confirmed flat, no bump in base rent',
    'LC-0030': 'JD: confirmed flat, no bump in base rent',
    'LC-0042': 'JD: confirmed flat for the full term',
    'LC-0095': 'JD: confirmed flat for the full term',
}

# comp -> {header: value} straight corrections to input cells
CORRECTIONS = {
    'LC-0095': {'Address': '18 West 18th Street', 'RSF': 16504},
}
CORRECTION_NOTE = {'LC-0095': 'JD: building corrected to 18 West 18th Street; RSF 16,000 -> 16,504'}

s = session()
H = headers(s, 'Lease Comps')
IDC, P1, P2, NOTE = H['Comp ID'], H['Rent P1 ($/RSF, mo 1-60)'], H['Rent P2 ($/RSF, mo 61-120)'], H['Notes']
rows = get_values(s, "'Lease Comps'!A2:AS1207", render='FORMATTED_VALUE')


def col(r, letter):
    i = 0
    for ch in letter:
        i = i * 26 + ord(ch) - 64
    return r[i-1] if i-1 < len(r) else ''


def money(v):
    try:
        return float(str(v).replace('$', '').replace(',', ''))
    except (ValueError, TypeError):
        return None


data, applied, noted, fixed, skipped = [], [], [], [], []
for i, r in enumerate(rows, 2):
    cid = col(r, IDC)
    if not cid:
        continue
    bits, note = [], None

    if cid in ESCALATIONS:
        a = ESCALATIONS[cid]
        note = a['note']
        if 'p1' in a and money(col(r, P1)) != a['p1']:
            data.append({'range': f"'Lease Comps'!{P1}{i}", 'values': [[a['p1']]]})
            bits.append(f"P1 {col(r, P1)}->${a['p1']}")
        if money(col(r, P2)) != a['p2']:
            data.append({'range': f"'Lease Comps'!{P2}{i}", 'values': [[a['p2']]]})
            bits.append(f"P2 blank->${a['p2']}")
        if bits:
            applied.append((cid, '; '.join(bits)))
    elif cid in FLAT:
        note = FLAT[cid]

    for hdr, val in CORRECTIONS.get(cid, {}).items():
        cur = col(r, H[hdr])
        same = money(cur) == val if isinstance(val, (int, float)) else str(cur).strip() == val
        if not same:
            data.append({'range': f"'Lease Comps'!{H[hdr]}{i}", 'values': [[val]]})
            fixed.append(f'{cid} {hdr}: {cur!r} -> {val!r}')
    if cid in CORRECTION_NOTE:
        note = f'{note} | {CORRECTION_NOTE[cid]}' if note else CORRECTION_NOTE[cid]

    if note:
        existing = str(col(r, NOTE)).strip()
        add = [p for p in note.split(' | ') if p not in existing]
        if add:
            data.append({'range': f"'Lease Comps'!{NOTE}{i}",
                         'values': [[' | '.join(([existing] if existing else []) + add)]]})
            noted.append(cid)
        elif not bits:
            skipped.append(cid)

if not data:
    print('nothing to apply — every answer is already in the sheet')
else:
    values_batch(s, data)
    print(f'{len(data)} cells written')
    for cid, what in applied:
        print(f'  escalation  {cid}  {what}')
    for f in fixed:
        print(f'  correction  {f}')
    if noted:
        print(f'  notes written on {len(noted)} comps')
    if skipped:
        print(f'  ({len(skipped)} already current)')

    changelog(s, 'FLAT RENT ANSWERS',
              f'Resolved the 17 comps over five years that carried a blank Rent P2. '
              f'{len(ESCALATIONS)} carry a real escalation and now hold a Rent P2 per JD '
              '(LC-0086 also corrected its Rent P1 $76 -> $79); the other 13 he confirmed flat '
              'for the full term and now say so in Notes, so a blank P2 there reads as an answer '
              'rather than a gap.', len(ESCALATIONS) + len(FLAT))
    if fixed:
        changelog(s, 'COMP CORRECTION',
                  'LC-0095 (Runway) recorded at 71 Fifth Avenue / 16,000 SF; JD corrected it to '
                  '18 West 18th Street / 16,504 SF.', 1)

summary, fails = qa_status(s)
print('\nQA:', summary, '| failing:', fails or 'none')
