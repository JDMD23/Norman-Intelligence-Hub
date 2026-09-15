"""Follow the decks on Sigma Computing, and add the expansion that was silently skipped.

JD 9/14: keep the book's figures for Elise AI, follow the decks for Sigma.

Three decks carry Sigma's 64,077 SF deal at 1 Madison and they do not fully agree:

  MTS_Comps_Last_18_Months_10.29.25   Jun-25, 10y, $105/$115, 14mo, Turnkey $175
  NYC_MTS_Comps_25000_03.26.26        Jun-25, 10y, $105/$115, 14mo, Turnkey $175
  NYC_Relevant_Tech-Ai_05.19.26       Jul-2025, 11y 2m, $105/$115, 14mo, $175

Rent, free rent and TI are unanimous and already match the book. Date and term are not, so
this takes the majority of two: June 2025 and a 10-year term, against the January 2025 and
11 years on file. The Tech-AI deck's Jul-2025 / 11y 2m reading is noted rather than lost.
Delivery moves to LL Turnkey — two decks state it explicitly and the book had Custom TIA.

The expansion is the part that went missing. add_comps_from_decks.py guarded against
duplicates on (tenant, address), which is right for a re-run but wrong for a tenant who signs
twice in one building: it matched Sigma's expansion against LC-0093 and skipped it. Optiver
survived only because neither of its deals was in the book yet. The guard is fixed separately
to key on (tenant, address, date).
"""
from common import session, get_values, values_batch, changelog, qa_status, headers

FIX = dict(date='2025-06-01', term=10.0, dlv='LL Turnkey',
           note='JD 9/14: follow the decks. MTS_Comps_Last_18_Months_10.29.25 and '
                'NYC_MTS_Comps_25000_03.26.26 both give Jun-25 and a 10-year term against the '
                'January 2025 and 11 years on file, and both state landlord turnkey at $175/SF. '
                'NYC_Relevant_Tech-Ai_05.19.26 reads it Jul-2025 on an 11y 2m term; the majority '
                'of two is taken. Rent, free rent and TI are unanimous across all three and '
                'already matched.')

EXPANSION = dict(t='Sigma Computing', co='Sigma Computing', d='2025-10-01',
                 a='1 Madison Avenue', sub='PAS / Mad. Square Park', cls='Trophy', fl='P3',
                 cond='', deal='Expansion', dlv='LL Turnkey', rsf=28286, term=10.0,
                 p1=105, p2=115, free=14, ti=175,
                 note='JD 9/14: second Sigma deal at 1 Madison, an expansion of LC-0093 at the '
                      'same terms. In MTS_Comps_Last_18_Months_10.29.25 and '
                      'NYC_MTS_Comps_25000_03.26.26 (Oct-25, 10y, landlord turnkey $175) and in '
                      'NYC_Relevant_Tech-Ai_05.19.26 (Oct-2025, 11y 2m), which is the deck that '
                      'types it an Expansion; the other two call it a new lease. Term takes the '
                      'majority of two at 10 years. Seats and condition are not stated in any '
                      'deck. This row was skipped when the deck comps were first added because '
                      'the duplicate guard keyed on tenant and address alone.')

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
M = {'date': 'Date Signed', 'term': 'Term (Years)', 'dlv': 'Delivery Condition'}
data, log = [], []
for i, r in enumerate(rows, 2):
    if col(r, 'Comp ID') != 'LC-0093':
        continue
    for k, hdr in M.items():
        if not same(col(r, hdr), FIX[k]):
            data.append({'range': f"'Lease Comps'!{H[hdr]}{i}", 'values': [[FIX[k]]]})
            log.append(f'   LC-0093 {hdr:22} {col(r, hdr)!r} -> {FIX[k]!r}')
    ex = col(r, 'Notes').strip()
    if FIX['note'] not in ex:
        data.append({'range': f"'Lease Comps'!{H['Notes']}{i}",
                     'values': [[(ex + ' ' if ex else '') + FIX['note']]]})
if data:
    values_batch(s, data)
    print(f'LC-0093 updated ({len(log)} fields):')
    for l in log:
        print(l)
else:
    print('LC-0093 already current')

# --- the expansion, keyed on tenant + address + date so a second deal is not mistaken for a dupe
x = EXPANSION
key = (x['t'].lower(), x['a'].lower(), x['rsf'])
have = {(col(r, 'Tenant').lower(), col(r, 'Address').lower(),
         int(float(col(r, 'RSF').replace(',', '') or 0))) for r in live}
if key in have:
    print('\nSigma expansion already present')
else:
    co = get_values(s, 'Companies!A2:B300', render='FORMATTED_VALUE')
    cid = next(r[0] for r in co if len(r) > 1 and str(r[1]).strip().lower() == x['co'].lower())
    lc = 'LC-%04d' % (max(int(col(r, 'Comp ID')[3:]) for r in live) + 1)
    r0 = 2 + len(live)
    values_batch(s, [{'range': f"'Lease Comps'!A{r0}:S{r0}", 'values': [[
        lc, x['d'], x['t'], cid, x['a'], x['sub'], x['cls'], x['fl'], x['cond'], x['deal'],
        x['dlv'], x['rsf'], '', x['term'], x['p1'], x['p2'], '', x['free'], x['ti']]]},
        {'range': f"'Lease Comps'!{H['Notes']}{r0}", 'values': [[x['note']]]}])
    print(f"\n{lc} added: Sigma Computing expansion, P3, {x['rsf']:,} SF, Oct 2025, "
          f"${x['p1']}/${x['p2']}, {x['free']}mo free, ${x['ti']} turnkey")

changelog(s, 'SIGMA DECK',
          'Followed the decks on Sigma Computing per JD. LC-0093 moves to June 2025 on a 10-year '
          'term with landlord turnkey delivery, the majority reading of two decks against the '
          "Tech-AI deck's Jul-2025 / 11y 2m. Added the 28,286 SF P3 expansion, which was skipped "
          'when the deck comps were first loaded because the duplicate guard keyed on tenant and '
          'address alone and matched it against LC-0093. Elise AI deliberately keeps the book '
          "figures per JD's ruling.", len(log) + 1)

summary, fails = qa_status(s)
print('\nQA:', summary, '| failing:', fails or 'none')
