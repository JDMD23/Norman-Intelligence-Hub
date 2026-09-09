"""Apply JD's turnkey TI answers (2026-09-06).

Ten LL Turnkey comps carried the $150/SF benchmark rather than a real figure. The benchmark
is an estimate, and TI is the single largest source of NER error in the book — $25/SF of TI
moves NER $3.31/SF/yr on a ten-year term and $4.36 on a seven. JD marked up all ten.

Five are confirmed at $150: it was the right number, and the value of the answer is that the
comp is no longer an estimate. Four move, three of them off precedent JD set in this pass:

  · 360 Park Avenue South — JD's standing rule is $155/SF for any RAW space in the building,
    which is the figure Rogo actually negotiated (LC-0099). It reaches Vercel and Grammarly.
    Rogo's own September 2025 deal (LC-0060) is Second Gen / As-Is and stays outside the rule.
  · Tenex at 60 Madison takes $110/SF, the figure from Pace (LC-0006) in the same building.
  · Notion at 75 Varick takes $140/SF.

Tempo Labs stays on the estimate at JD's direction — it already carries an unverified Seed
round, and guessing its TI would compound one open question with another.

Notes record which of the two a $150 is: a confirmed figure or the benchmark.

Idempotent: writes only what differs.
"""
from common import session, get_values, values_batch, changelog, qa_status, headers

CONFIRMED = {          # right number, now recorded as confirmed rather than estimated
    'LC-0019': 'Ramp',
    'LC-0029': 'Whatnot',
    'LC-0067': 'Fireblocks',
    'LC-0014': 'Charlie Health',
    'LC-0068': 'Imprint',
}
CHANGED = {            # comp -> (TI, note)
    'LC-0023': (155, 'JD: $155/SF — standing rule, any raw space at 360 Park Avenue South '
                     'takes the turnkey value Rogo negotiated (LC-0099)'),
    'LC-0062': (155, 'JD: $155/SF — standing rule, any raw space at 360 Park Avenue South '
                     'takes the turnkey value Rogo negotiated (LC-0099)'),
    'LC-0003': (110, 'JD: $110/SF, matching Pace at 60 Madison Avenue (LC-0006)'),
    'LC-0038': (140, 'JD: $140/SF'),
}
CONFIRM_NOTE = 'JD 9/6: ${} /SF turnkey confirmed — a real figure, not the benchmark estimate.'

s = session()
H = headers(s, 'Lease Comps')
TI, NOTE = H['TI $/SF'], H['Notes']
rows = get_values(s, "'Lease Comps'!A2:AS1206", render='FORMATTED_VALUE')


def col(r, letter):
    i = 0
    for ch in letter:
        i = i * 26 + ord(ch) - 64
    return str(r[i-1]) if i-1 < len(r) else ''


def money(v):
    try:
        return float(str(v).replace('$', '').replace(',', ''))
    except ValueError:
        return None


data, moved, held = [], [], []
for i, r in enumerate(rows, 2):
    cid = col(r, H['Comp ID'])
    if not cid:
        continue
    note = None
    if cid in CHANGED:
        ti, note = CHANGED[cid]
        cur = money(col(r, TI))
        if cur != ti:
            data.append({'range': f"'Lease Comps'!{TI}{i}", 'values': [[ti]]})
            moved.append(f'  {cid}  {col(r, H["Tenant"]):12} TI ${cur:.0f} -> ${ti}')
    elif cid in CONFIRMED:
        note = CONFIRM_NOTE.format(int(money(col(r, TI)) or 150)).replace('$ ', '$')
        held.append(f'  {cid}  {col(r, H["Tenant"]):12} ${money(col(r, TI)):.0f} confirmed')
    if note:
        existing = col(r, NOTE).strip()
        if note not in existing:
            data.append({'range': f"'Lease Comps'!{NOTE}{i}",
                         'values': [[(existing + ' ' if existing else '') + note
                                     + ('' if note.endswith('.') else '.')]]})

if not data:
    print('nothing to apply — every answer is already in the sheet')
else:
    values_batch(s, data)
    print(f'{len(data)} cells written\n\nmoved:')
    for x in moved:
        print(x)
    print('\nconfirmed at the existing figure:')
    for x in held:
        print(x)
    changelog(s, 'TURNKEY TI ANSWERS',
              'JD marked up all ten LL Turnkey comps that carried the $150/SF benchmark rather than '
              'a real figure. Five confirmed at $150 (Ramp, Whatnot, Fireblocks, Charlie Health, '
              'Imprint) and are no longer estimates. Four moved: Vercel and Grammarly to $155 under '
              "JD's standing rule that any raw space at 360 Park Avenue South takes the turnkey "
              'value Rogo negotiated; Tenex to $110 matching Pace at 60 Madison Avenue; Notion to '
              '$140. Tempo Labs stays on the estimate at his direction — it already carries an '
              'unverified Seed round. Notes now distinguish a confirmed $150 from the benchmark.',
              len(moved) + len(held))

summary, fails = qa_status(s)
print('\nQA:', summary, '| failing:', fails or 'none')
