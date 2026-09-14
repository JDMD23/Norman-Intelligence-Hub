"""Apply JD's rulings on the deck-vs-book conflicts (2026-09-14).

His instruction was "just use what you see" in the decks, with two carve-outs:

  · 360 Park Avenue South keeps $155/SF. Grammarly and Vercel therefore stay where they are,
    and the standing raw-space rule for that building survives the decks disagreeing with it
    (deck C says $120 for Grammarly, deck F says $160 for Vercel).
  · Bluefish AI and Legora at 836 Broadway were new prebuilts, so no allowance passed to the
    tenant. Both are already recorded as New prebuilt / As-Is / $0, which is what he confirmed,
    so neither is touched here.

What that leaves:

  LC-0029 Whatnot     follow the deck outright — 56,250 SF on P11 and E12 at $87/$95, against
                      75,430 SF on E11-12 at $85/$92 on file. A 19,180 SF difference.
  LC-0067 Fireblocks  TI $150 -> $130. The $150 was the turnkey benchmark he confirmed on 9/6
                      in the absence of a real number; the deck supplies one.
  LC-0085 Faire       TI $0 -> $100. Recorded as a confirmed as-is zero; the deck shows a real
                      allowance, so the delivery condition moves to Custom TIA to agree with it.
  LC-0082 Figma       TI $75 -> $70.

Elise AI and Sigma are deliberately untouched — JD kept the book's figures on both.

Idempotent: writes only what differs.
"""
from common import session, get_values, values_batch, changelog, qa_status, headers

FIX = {
    'LC-0029': dict(rsf=56250, floors='P11, E12', p1=87, p2=95,
                    note='JD 9/14: follow the deck. NYC_MTS_Comps_25000_Jan2025-YTD_03.26.26 '
                         'gives 56,250 SF on P11 and E12 at $87/$95; the book had 75,430 SF on '
                         'E11-12 at $85/$92.'),
    'LC-0067': dict(ti=130,
                    note='JD 9/14: TI $150 -> $130 per NYC_Relevant_Tech-Ai_Comps_05.19.26, which '
                         'records it as a $130/SF prebuilt. The $150 was the turnkey benchmark '
                         'standing in for an unknown; this is a real figure, so the comp is no '
                         'longer an estimate.'),
    'LC-0085': dict(ti=100, dlv='Custom TIA',
                    note='JD 9/14: TI $0 -> $100 per MTS_Comps_Last_18_Months_10.29.25. Delivery '
                         'moves from As-Is to Custom TIA so the two agree — an as-is deal cannot '
                         'carry a $100/SF allowance.'),
    'LC-0082': dict(ti=70,
                    note='JD 9/14: TI $75 -> $70 per MTS_Comps_Last_18_Months_10.29.25.'),
}
M = {'rsf': 'RSF', 'floors': 'Floor(s)', 'p1': 'Rent P1 ($/RSF, mo 1-60)',
     'p2': 'Rent P2 ($/RSF, mo 61-120)', 'ti': 'TI $/SF', 'dlv': 'Delivery Condition'}

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


data, log = [], []
for i, r in enumerate(rows, 2):
    cid = col(r, 'Comp ID')
    if cid not in FIX:
        continue
    f = FIX[cid]
    for k, hdr in M.items():
        if k not in f:
            continue
        cur = col(r, hdr)
        if not same(cur, f[k]):
            data.append({'range': f"'Lease Comps'!{H[hdr]}{i}", 'values': [[f[k]]]})
            log.append(f'   {cid} {col(r, "Tenant"):12} {hdr:28} {cur!r} -> {f[k]!r}')
    ex = col(r, 'Notes').strip()
    if f['note'] not in ex:
        data.append({'range': f"'Lease Comps'!{H['Notes']}{i}",
                     'values': [[(ex + ' ' if ex else '') + f['note']]]})

if not data:
    print('nothing to apply — every ruling is already in the sheet')
else:
    values_batch(s, data)
    print(f'{len(data)} cells written\n')
    for l in log:
        print(l)
    changelog(s, 'DECK CONFLICTS',
              "Applied JD's rulings on the deck-vs-book conflicts. Whatnot follows the deck "
              'outright (56,250 SF on P11/E12 at $87/$95). Fireblocks TI $150 -> $130, replacing '
              'the turnkey benchmark with a real figure. Faire $0 -> $100 with delivery moved to '
              'Custom TIA to agree. Figma $75 -> $70. Deliberately unchanged: 360 Park Avenue '
              'South keeps $155 (Grammarly and Vercel), Bluefish and Legora stay at $0 as new '
              'prebuilts, and Elise AI and Sigma keep the book figures.',
              len(log))

summary, fails = qa_status(s)
print('\nQA:', summary, '| failing:', fails or 'none')
