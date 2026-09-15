"""Record the Notion 75 Varick amendment as one comp, plus the 9th-floor take.

JD supplied the negotiation term sheet (LL RFP Dec 2024 -> Notion proposal Sept 2025 -> Hines
final LOI Oct 2025 -> final amendment Dec 17 2025). It resolves a conflict the six broker decks
could not: they disagreed on Notion's rent, term, free rent and TI because the amendment covers
TWO premises with genuinely different economics, and each deck had picked up one half.

  Expansion Premises   7 years from RCD, $85 yrs 1-5 / $92 yrs 6-7, turnkey capped at $140/RSF,
                       10 months abated post landlord completion
  Existing Premises    coterminous through the Expansion LXD, $77 then $84 from year 6
                       (starting 2028), $55/RSF allowance, 8 months abated from existing LXD

Relevant_Completed_Transactions_06.29.26 reported the Expansion side ($140 TI, 10 months);
NYC_Relevant_Tech-Ai_Comps_05.19.26 reported the Existing side ($55 TI, 8 months). Neither deck
was wrong.

The size reconciles three independent ways, all within 113 SF:
  76,140 (deck total) less the 26,427 already on LC-0038  = 49,713 SF existing
  the signed $2.73M allowance at $55/RSF                  = 49,636 SF
  the landlord's opening $2.48M at $50/RSF                = 49,600 SF

Per JD this is ONE comp. LC-0038 becomes the whole 76,140 SF transaction at RSF-weighted
blended economics, and two Floor Detail rows carry the real per-premises terms so nothing is
lost — the tab's blend check then proves the blend reconciles to the typed figures.

Separately, Notion took 40,000 RSF on a partial 9th floor in July 2026. That space came through
the ROFO in this same amendment (the 9th floor is named there at a 30,000-70,000 RSF range).
Its economics are the amendment's expansion-option terms: $82 yrs 1-5 / $89 thereafter, 8 months
abated, landlord work on the same basis as the Expansion Premises capped at $140/RSF. Worth
noting the term sheet attaches that pricing block to the 7th-floor Initial Expansion Option, so
if the 9th floor was struck at different numbers these should be replaced.

NOT recorded: the 40,000 RSF 7th-floor growth right. Its deadline was June 30 2026 and nothing
was signed against it, so it is not a comp.
"""
from common import session, get_values, values_batch, changelog, qa_status, headers

TOTAL, EXPANSION = 76140, 26427
EXISTING = TOTAL - EXPANSION
bl = lambda a, b: round((EXPANSION * a + EXISTING * b) / TOTAL, 2)
P1, P2, TI, FREE = bl(85, 77), bl(92, 84), bl(140, 55), bl(10, 8)

AMEND = dict(rsf=TOTAL, date='2025-12-01', deal='Renewal + Expansion',
             floors='P8 (Expansion) + Existing Premises', p1=P1, p2=P2, ti=TI, free=FREE,
             note=('JD 9/14, from the signed term sheet: this is the 17 Dec 2025 amendment, one '
                   'transaction over two premises. Expansion Premises 26,427 SF at $85 yrs 1-5 / '
                   '$92 yrs 6-7, turnkey capped at $140/RSF, 10 months abated. Existing Premises '
                   f'{EXISTING:,} SF coterminous at $77 then $84 from year 6 (starting 2028), '
                   '$55/RSF allowance, 8 months abated. The figures on this row are RSF-weighted '
                   'blends of the two; the real per-premises terms are on the Floor Detail tab. '
                   'Size reconciles three ways within 113 SF: 76,140 less 26,427; $2.73M at $55; '
                   "$2.48M at $50. The decks disagreed because each reported one half."))

NINTH = dict(t='Notion', co='Notion', d='2026-07-01', a='75 Varick Street', sub='Hudson Square',
             cls='Class A', fl='P9', cond='Raw', deal='Expansion', dlv='LL Turnkey',
             rsf=40000, term=7.0, p1=82, p2=89, free=8, ti=140,
             note=('JD 9/14: 40,000 RSF on a partial 9th floor taken July 2026, through the ROFO '
                   'in the 17 Dec 2025 amendment, which names the 9th floor at a 30,000-70,000 '
                   'RSF range. Economics are that amendment\'s expansion-option terms: $82 yrs '
                   '1-5 / $89 thereafter, 8 months abated, landlord work on the same basis as the '
                   'Expansion Premises capped at $140/RSF. NOTE the term sheet attaches that '
                   'pricing block to the 7th-floor Initial Expansion Option, so replace these if '
                   'the 9th floor was struck at different numbers. Term shown as 7 years to match '
                   'the Expansion Premises; the option runs coterminous with its own rent clock '
                   'from each floor\'s RCD, which is not in the term sheet.'))

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


live = [r for r in rows if col(r, 'Comp ID')]
M = {'rsf': 'RSF', 'date': 'Date Signed', 'deal': 'Deal Type', 'floors': 'Floor(s)',
     'p1': 'Rent P1 ($/RSF, mo 1-60)', 'p2': 'Rent P2 ($/RSF, mo 61-120)',
     'ti': 'TI $/SF', 'free': 'Free Rent (months)'}
data, log = [], []
for i, r in enumerate(rows, 2):
    if col(r, 'Comp ID') != 'LC-0038':
        continue
    for k, hdr in M.items():
        if not same(col(r, hdr), AMEND[k]):
            data.append({'range': f"'Lease Comps'!{H[hdr]}{i}", 'values': [[AMEND[k]]]})
            log.append(f'   LC-0038 {hdr:28} {col(r, hdr)!r} -> {AMEND[k]!r}')
    ex = col(r, 'Notes').strip()
    if AMEND['note'] not in ex:
        data.append({'range': f"'Lease Comps'!{H['Notes']}{i}",
                     'values': [[(ex + ' ' if ex else '') + AMEND['note']]]})
if data:
    values_batch(s, data)
    print(f'LC-0038 rewritten as the whole amendment ({len(log)} fields):')
    for l in log:
        print(l)
else:
    print('LC-0038 already current')

# --- Floor Detail: the two premises
fd = get_values(s, "'Floor Detail'!A2:J200", render='FORMATTED_VALUE')
fd_live = [r for r in fd if r and r[0]]
have = {(r[1], r[3]) for r in fd_live if len(r) > 3}
want = [('P8 - Expansion Premises', EXPANSION, 85, 140, 10,
         'Expansion Premises: 7 years from RCD, $85 yrs 1-5 / $92 yrs 6-7, turnkey capped at '
         '$140/RSF, 10 months abated post landlord completion.'),
        ('Existing Premises', EXISTING, 77, 55, 8,
         f'Existing Premises, {EXISTING:,} SF: coterminous through the Expansion LXD, $77 then '
         '$84 from year 6 (starting 2028), $55/RSF ($2.73M) allowance, 8 months abated from the '
         'existing LXD. RSF derived as 76,140 less 26,427; the allowance implies 49,636.')]
todo = [w for w in want if ('LC-0038', w[0]) not in have]
if todo:
    nxt = max([int(r[0][3:]) for r in fd_live if r[0].startswith('FD-')] or [0]) + 1
    row = 2 + len(fd_live)
    vals = []
    for fl, rsf, rent, ti, free, note in todo:
        vals.append(['FD-%04d' % nxt, 'LC-0038', '', fl, rsf, rent, ti, free, '', note])
        nxt += 1
    values_batch(s, [{'range': f"'Floor Detail'!A{row}:J{row+len(vals)-1}", 'values': vals}])
    # column C and I are computed - clear the placeholders so their formulas fill back in
    print(f'\nFloor Detail rows added ({len(vals)}):')
    for v in vals:
        print(f'   {v[0]} {v[3]:26} {v[4]:>8,} SF  ${v[5]}  TI ${v[6]}  {v[7]}mo free')
else:
    print('\nFloor Detail already current')

# --- the 9th floor
if not any(col(r, 'Tenant').lower() == 'notion' and col(r, 'Floor(s)') == 'P9' for r in live):
    co = get_values(s, 'Companies!A2:B300', render='FORMATTED_VALUE')
    cid = next(r[0] for r in co if len(r) > 1 and str(r[1]).strip().lower() == 'notion')
    lc = 'LC-%04d' % (max(int(col(r, 'Comp ID')[3:]) for r in live) + 1)
    r0 = 2 + len(live)
    x = NINTH
    values_batch(s, [{'range': f"'Lease Comps'!A{r0}:S{r0}", 'values': [[
        lc, x['d'], x['t'], cid, x['a'], x['sub'], x['cls'], x['fl'], x['cond'], x['deal'],
        x['dlv'], x['rsf'], '', x['term'], x['p1'], x['p2'], '', x['free'], x['ti']]]},
        {'range': f"'Lease Comps'!{H['Notes']}{r0}", 'values': [[x['note']]]}])
    print(f"\n{lc} added: Notion P9, {x['rsf']:,} SF, July 2026, "
          f"${x['p1']}/${x['p2']}, {x['free']}mo free, ${x['ti']} TI, {x['deal']}")
else:
    print('\nNotion 9th floor already present')

changelog(s, 'NOTION AMENDMENT',
          'Recorded the 17 Dec 2025 Notion amendment at 75 Varick as one comp per JD. LC-0038 '
          f'becomes the whole {TOTAL:,} SF transaction at RSF-weighted blended economics '
          f'(${P1}/${P2}, ${TI} TI, {FREE} months), with two Floor Detail rows carrying the real '
          f'per-premises terms — Expansion {EXPANSION:,} SF at $85/$92 with $140 turnkey and 10 '
          f'months, Existing {EXISTING:,} SF at $77/$84 with $55 and 8 months. This explains why '
          'the broker decks disagreed on Notion: each reported one premises. Separately added the '
          '40,000 RSF partial 9th floor taken July 2026 through the ROFO in the same amendment. '
          'The unexercised 40,000 RSF 7th-floor growth right is deliberately not a comp.', 3)

summary, fails = qa_status(s)
print('\nQA:', summary, '| failing:', fails or 'none')
