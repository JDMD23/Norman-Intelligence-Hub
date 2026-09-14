"""Add the comps JD selected from the six broker decks, and correct two he ruled on.

Source decks, cited per comp in Notes:
  A  MTS_Comps_05.21.26.pptx
  B  MTS_Comps_Last_18_Months_10.29.25.pptx
  C  NYC_MTS_Comps_-_25000_Jan_2025_-_YTD_03.26.26.pptx
  D  NYC_Relevant_Tech-Ai_Comps_20000_RSF_12M_Direct_05.19.26.pptx
  E  Penn_1__Penn_2__Relevant_Transactions_10000_RSF_04.28.26.pptx
  F  Relevant_Completed_Transactions_06.29.26.pptx

JD's rulings, applied here:
  · follow the decks on RSF
  · Optiver is two deals — the Apr-25 single floor and the Mar-26 four-floor expansion
  · Sigma's Oct-25 28,286 SF is a second deal, an expansion
  · BILT is one lease: LC-0049 corrected to 58,434 SF across GRND, LL and E2-6
  · Ramp is one comp: LC-0019 rewritten as the whole 285,303 SF, dated March 2026
  · Coinbase stays on E5 and stays typed Expansion — the E24-25 deal is NOT added
  · Apple and OpenAI excluded (both entirely confidential in the decks anyway)
  · Adyen's 46,500 SF March record is the same deal as the 90,000 SF April one; only the
    April record, which carries full terms, is added
  · The Knot's 31,781 SF P5 row is the P5 portion of the 56,272 SF P5+P11 deal; one comp added

Assumptions I made rather than guess at you, all reversible and all in Notes:
  · Condition is blank on every row — no deck states it. The audit will report these.
  · Seats are blank — no deck carries density.
  · Submarket and building class follow precedent already in the book for that address;
    where the book had no precedent the choice is named in Notes.
  · Two comps carry different rents per floor (General Catalyst, Bridgewater). Floor RSF is
    not stated in any deck, so the comp-level rate is an equal-split weighted average and is
    flagged as an ESTIMATE. Replace via Floor Detail once floor RSF is known.

Idempotent: a comp already present at the same tenant and address is skipped.
"""
from common import session, get_values, values_batch, changelog, qa_status, headers

TK = 'LL Turnkey'; TIA = 'Custom TIA'; ASIS = 'As-Is'

COMPS = [
    dict(t='Veeva Systems', co='Veeva Systems', d='2026-06-01', a='2 Penn Plaza',
         sub='Hudson Yards / Penn Station', cls='Trophy', fl='E11', deal='New Lease', dlv=TIA,
         rsf=62223, term=10.0, p1=105, p2=115, free=12, ti=150, src='F'),
    dict(t='Adyen', co='Adyen', d='2026-04-01', a='111-115 Fifth Avenue',
         sub='Flatiron', cls='Class A', fl='E4-E5', deal='New Lease', dlv=TIA,
         rsf=90000, term=10.0, p1=83, p2=89, free=16, ti=135, src='F',
         note='Also reported in deck C as 46,500 SF at 881 Broadway (Mar-26) with all terms '
              'confidential — same building and same deal, so only this record is kept. '
              'Submarket Flatiron; no precedent for this address in the book.'),
    dict(t='Optiver', co='Optiver', d='2025-04-01', a='360 Park Avenue South',
         sub='PAS / Mad. Square Park', cls='Class A', fl='E12', deal='New Lease', dlv=ASIS,
         cond='New prebuilt', rsf=23038, term=5.0, p1=98, free=6, ti=0, src='A,B,C,D',
         note="Delivered pre-built with minor modifications, so As-Is with a confirmed $0 "
              "allowance. Optiver's first deal here; the Mar-26 four-floor expansion is separate."),
    dict(t='Optiver', co='Optiver', d='2026-03-01', a='360 Park Avenue South',
         sub='PAS / Mad. Square Park', cls='Class A', fl='E2-E5', deal='Expansion', dlv=TIA,
         rsf=92152, term=10.0, p1=93, p2=101, free=16, ti=165, src='A,C,D,F',
         note='Expansion of the Apr-25 E12 lease. 92,152 SF is exactly four 23,038 SF floor '
              'plates at this building.'),
    dict(t='Uber Technologies', co='Uber Technologies', d='2026-03-01', a='3 World Trade Center',
         sub='World Trade Center', cls='Trophy', fl='E36-E37', deal='Expansion', dlv=ASIS,
         rsf=86718, term=5.08, p1=96, free=6, ti=0, src='D',
         note='Term 5y 1m. Deck records a confirmed $0 allowance. Typed Expansion per the deck; '
              "Uber's earlier deal at this building is not in the book."),
    dict(t='Snowflake', co='Snowflake', d='2026-02-01', a='7 Times Square',
         sub='Midtown', cls='Class A', fl='E29-E31', deal='New Lease', dlv=TIA,
         rsf=82505, term=11.33, p1=79, p2=86, free=12, ti=180, src='D',
         note='Term 11y 4m. First comp in the Midtown submarket.'),
    dict(t='Media iQ Digital', co='Media iQ Digital', d='2026-02-01', a='261 Fifth Avenue',
         sub='NoMad', cls='Class B', fl='E20-E21', deal='New Lease', dlv=TIA,
         rsf=29425, term=10.0, p1=70, p2=75, free=8.5, ti=80, src='D',
         note='First comp in the NoMad submarket; 261 Fifth sits at 29th Street. Class B is a '
              'judgement call, no precedent for this address.'),
    dict(t='Marriott', co='Marriott', d='2026-02-01', a='360 Park Avenue South',
         sub='PAS / Mad. Square Park', cls='Class A', fl='E14', deal='New Lease', dlv=TIA,
         rsf=23038, term=10.0, p1=100, p2=108, free=14, ti=160, src='F'),
    dict(t='Elise AI', co='EliseAI', d='2026-01-01', a='401 Fifth Avenue',
         sub='Grand Central', cls='Class A', fl='E3', deal='Expansion', dlv=TIA,
         rsf=27371, term=10.0, p1=72, p2=75, free=12, ti=35, src='D,F',
         note='Expansion of LC-0043 (E4-6, Nov 2025) two months later. Deck D gives both rent '
              'tranches and types it an Expansion; deck F shows only a $72 start, 10 months free '
              'and calls it a relocation. Deck D used as the fuller record. Note both decks put '
              'the original LC-0043 deal at $72/$75 with $35 TI against the $72/$77 and $40 on '
              'file — not changed here.'),
    dict(t='Capgemini', co='Capgemini', d='2025-12-01', a='2 Penn Plaza',
         sub='Hudson Yards / Penn Station', cls='Trophy', fl='P22', deal='New Lease', dlv=TIA,
         rsf=43518, term=10.0, p1=116, p2=126, free=11, ti=155, src='A,D,F',
         note='Deck E prints 43,000 SF; the three other decks agree on 43,518.'),
    dict(t='Cadent', co='Cadent', d='2025-11-01', a='2 Park Avenue',
         sub='PAS / Mad. Square Park', cls='Class A', fl='E9', deal='New Lease', dlv=ASIS,
         rsf=50017, term=5.0, p1=83, free=5, ti=0, src='D,F',
         note='Decks show a second rate of $88 on a five-year term. The workbook models rent as '
              'flat tranches at months 1-60 / 61-120 / 121+, so a bump inside a 60-month term '
              'cannot be expressed; only the $83 starting rate is recorded and the $88 is noted '
              'here. NER is therefore marginally conservative.'),
    dict(t='Robinhood', co='Robinhood', d='2025-10-01', a='2 Penn Plaza',
         sub='Hudson Yards / Penn Station', cls='Trophy', fl='E25-E26', deal='New Lease', dlv=TIA,
         rsf=125392, term=10.0, p1=100, p2=110, free=14, ti=150, src='E'),
    dict(t='The Knot Worldwide', co='The Knot Worldwide', d='2025-10-01', a='295 Fifth Avenue',
         sub='PAS / Mad. Square Park', cls='Class A', fl='P5, P11', deal='New Lease', dlv=TIA,
         rsf=56272, term=10.0, p1=86, p2=93, free=7, ti=120, src='D',
         note='Decks A and F report the P5 portion alone as 31,781 SF with the same rent and free '
              'rent; that is part of this deal, not a second transaction, so one comp is recorded.'),
    dict(t='Sigma Computing', co='Sigma Computing', d='2025-10-01', a='1 Madison Avenue',
         sub='PAS / Mad. Square Park', cls='Trophy', fl='P3', deal='Expansion', dlv=TIA,
         rsf=28286, term=11.17, p1=105, p2=115, free=14, ti=175, src='B,C,D',
         note='Term 11y 2m. Expansion of LC-0093 at the same terms. Three decks type it an '
              'Expansion. Note those decks date the original LC-0093 deal to Jun/Jul 2025 against '
              'the January 2025 on file — not changed here.'),
    dict(t='Patreon', co='Patreon', d='2025-09-01', a='75 Varick Street',
         sub='Hudson Square', cls='Class A', fl='P4', deal='Sublease', dlv=ASIS,
         rsf=45294, term=1.0, p1=72, free=0, ti=0, src='B',
         note='Sublease from Oscar Health. One-year term, no free rent, no allowance — the short '
              'term makes its NER close to the face rent and not comparable to a direct deal.'),
    dict(t='Salesforce', co='Salesforce', d='2025-08-01', a='1095 Avenue of the Americas',
         sub='Midtown', cls='Trophy', fl='P0, E16-E20, E23', deal='New Lease', dlv=TIA,
         rsf=349515, term=15.0, p1=155, p2=165, p3=175, free=20, ti=160, src='D',
         note='Largest comp in the book. Floor list abbreviated from the deck.'),
    dict(t='Pinterest', co='Pinterest', d='2025-06-01', a='11 Madison Avenue',
         sub='PAS / Mad. Square Park', cls='Trophy', fl='E13', deal='New Lease', dlv=TIA,
         rsf=82812, term=10.0, p1=81, p2=86, free=18, ti=150, src='A,B,C,D'),
    dict(t='Palantir', co='Palantir', d='2025-05-01', a='620 Avenue of the Americas',
         sub='Chelsea', cls='Class A', fl='P3, P6', deal='Renewal', dlv=TIA,
         rsf=140345, term=11.0, p1=87, p2=92, free=12, ti=105, src='A',
         note='Submarket Chelsea; 620 Sixth Avenue sits on the Chelsea/Flatiron line and the book '
              'has no precedent for it.'),
    dict(t='Octus Intelligence', co='Octus Intelligence', d='2025-03-01', a='295 Fifth Avenue',
         sub='PAS / Mad. Square Park', cls='Class A', fl='E6', deal='New Lease', dlv=TIA,
         rsf=43588, term=10.0, p1=86, p2=92, free=16, ti=150, src='A,B,C,F'),
    dict(t='General Catalyst', co='General Catalyst', d='2025-03-01', a='148 Lafayette Street',
         sub='SoHo/NoHo', cls='Class A', fl='E10-E13', deal='New Lease', dlv=TIA,
         rsf=42535, term=12.0, p1=108.50, p2=118.50, free=16, ti=155, src='A',
         note='RENT IS AN ESTIMATE. The deck gives a different rate per floor — E10 $96/$106, '
              'E11 $98/$108, E12-13 (PH) $120/$130 — but no floor-level RSF. The comp-level rate '
              'here is an equal-split weighted average across the four floors. Replace with a '
              'Floor Detail breakdown once floor RSF is known.'),
    dict(t='Warby Parker', co='Warby Parker', d='2024-11-01', a='161 Avenue of the Americas',
         sub='Hudson Square', cls='Class A', fl='E6-E7', deal='Renewal', dlv=TIA,
         rsf=54668, term=11.58, p1=80, p2=86, free=19, ti=115, src='B',
         note='Term 11y 7m. Deck calls it an extension; recorded as Renewal, the nearest term in '
              'the workbook vocabulary.'),
    dict(t='Bridgewater Associates', co='Bridgewater Associates', d='2024-09-01',
         a='295 Fifth Avenue', sub='PAS / Mad. Square Park', cls='Class A', fl='E17-E19',
         deal='New Lease', dlv=TIA, rsf=63703, term=10.0, p1=133.35, p2=143.34, free=15, ti=150,
         src='B',
         note='RENT IS AN ESTIMATE. The deck gives E17 at $120/$130 and E18-19 at $140/$150 with '
              'no floor-level RSF. The comp-level rate here is an equal-split weighted average '
              'across the three floors. Replace with a Floor Detail breakdown once floor RSF is '
              "known. Deck notes this as Bridgewater's first NYC office."),
    dict(t='FanDuel', co='FanDuel', d='2024-04-01', a='1 Madison Avenue',
         sub='PAS / Mad. Square Park', cls='Trophy', fl='E23', deal='New Lease', dlv=TIA,
         rsf=35898, term=12.0, p1=160, p2=170, p3=180, free=16, ti=160, src='C',
         note='Deck shows the rent in four-year steps ($160/$170/$180 at 4 years each). The '
              'workbook models five-year tranches, so the bumps are recorded at months 61 and '
              '121 rather than 49 and 97 — NER is marginally conservative as a result.'),
]

# JD's rulings on comps already in the book
FIXES = {
    'LC-0019': dict(rsf=285303, date='2026-03-01', term=12.0, p1=93, p2=100, free=9, ti=150,
                    floors='E2-E7, PH', deal='Extension/Expansion', dlv=TK,
                    note='JD 9/14: recorded as the whole 285,303 SF Ramp premises dated March '
                         '2026, per deck C. Decks A, D and F print 153,000 SF on E2-6 + PH and '
                         'deck C prints 285,303 SF on E3, E5-E7; the previous 132,000 SF on E2+E4 '
                         'was the earlier partial record. Floors shown as the union of the deck '
                         'labels.'),
    'LC-0049': dict(rsf=58434, floors='GRND, LL, E2-E6',
                    note='JD 9/14: corrected to the full 58,434 SF premises per decks A and D, '
                         'which include the ground and lower levels. Decks B and C report only '
                         'the 39,591 SF office portion. All other terms already matched.'),
}
SRC = {'A': 'MTS_Comps_05.21.26', 'B': 'MTS_Comps_Last_18_Months_10.29.25',
       'C': 'NYC_MTS_Comps_25000_Jan2025-YTD_03.26.26',
       'D': 'NYC_Relevant_Tech-Ai_Comps_20000_RSF_12M_Direct_05.19.26',
       'E': 'Penn_1_Penn_2_Relevant_Transactions_10000_RSF_04.28.26',
       'F': 'Relevant_Completed_Transactions_06.29.26'}

s = session()
H = headers(s, 'Lease Comps')
rows = get_values(s, "'Lease Comps'!A2:AS1206", render='FORMATTED_VALUE')


def col(r, hdr):
    i = 0
    for ch in H[hdr]:
        i = i * 26 + ord(ch) - 64
    return str(r[i-1]) if i-1 < len(r) else ''


live = [r for r in rows if col(r, 'Comp ID')]
have = {(col(r, 'Tenant').lower(), col(r, 'Address').lower()) for r in live}
todo = [x for x in COMPS if (x['t'].lower(), x['a'].lower()) not in have]
print(f'{len(COMPS)} selected, {len(COMPS)-len(todo)} already present, {len(todo)} to add')

co = get_values(s, 'Companies!A2:B300', render='FORMATTED_VALUE')
co_ids = [r[0] for r in co if r and r[0]]
by_name = {str(r[1]).strip().lower(): r[0] for r in co if r and len(r) > 1 and r[1]}
next_co = max(int(x[3:]) for x in co_ids) + 1
next_lc = max(int(col(r, 'Comp ID')[3:]) for r in live) + 1
lc_row = 2 + len(live)
co_row = 2 + len(co_ids)

new_co, comp_rows, added = [], [], []
for x in todo:
    key = x['co'].strip().lower()
    if key in by_name:
        cid = by_name[key]
    else:
        cid = 'CO-%04d' % next_co; next_co += 1
        new_co.append([cid, x['co']]); by_name[key] = cid
    lc = 'LC-%04d' % next_lc; next_lc += 1
    bits = [f"From JD's broker decks ({', '.join(SRC[k] for k in x['src'].split(','))}).",
            x.get('note', ''), 'Seats and condition are not stated in any deck.']
    note = ' '.join(b.strip() for b in bits if b.strip())
    comp_rows.append([lc, x['d'], x['t'], cid, x['a'], x['sub'], x['cls'], x['fl'],
                      x.get('cond', ''), x['deal'], x['dlv'], x['rsf'], '', x['term'],
                      x['p1'], x.get('p2', ''), x.get('p3', ''), x['free'], x['ti']])
    added.append((lc, cid, x, note))

if new_co:
    values_batch(s, [{'range': f'Companies!A{co_row}:B{co_row+len(new_co)-1}', 'values': new_co}])
    print(f'\nCompanies added ({len(new_co)}): ' + ', '.join(f'{a} {b}' for a, b in new_co))

if comp_rows:
    values_batch(s, [{'range': f"'Lease Comps'!A{lc_row}:S{lc_row+len(comp_rows)-1}",
                      'values': comp_rows}])
    notes = [{'range': f"'Lease Comps'!{H['Notes']}{lc_row+i}", 'values': [[n]]}
             for i, (_, _, _, n) in enumerate(added)]
    values_batch(s, notes)
    print(f'\nLease Comps added ({len(comp_rows)}):')
    for lc, cid, x, _ in added:
        print(f"   {lc} {x['t'][:24]:24} {x['a'][:28]:28} {x['rsf']:>8,} SF {x['d']} {x['deal']}")

# --- JD's corrections to existing comps
fixdata, fixlog = [], []
for r_i, r in enumerate(rows, 2):
    cid = col(r, 'Comp ID')
    if cid not in FIXES:
        continue
    f = FIXES[cid]
    M = {'rsf': 'RSF', 'date': 'Date Signed', 'term': 'Term (Years)',
         'p1': 'Rent P1 ($/RSF, mo 1-60)', 'p2': 'Rent P2 ($/RSF, mo 61-120)',
         'free': 'Free Rent (months)', 'ti': 'TI $/SF', 'floors': 'Floor(s)',
         'deal': 'Deal Type', 'dlv': 'Delivery Condition'}
    for k, hdr in M.items():
        if k not in f:
            continue
        cur = col(r, hdr)
        want = f[k]
        same = (str(cur).replace('$', '').replace(',', '').strip() ==
                str(want).replace('$', '').replace(',', '').strip())
        if not same:
            fixdata.append({'range': f"'Lease Comps'!{H[hdr]}{r_i}", 'values': [[want]]})
            fixlog.append(f'   {cid} {hdr}: {cur!r} -> {want!r}')
    ex = col(r, 'Notes').strip()
    if f['note'] not in ex:
        fixdata.append({'range': f"'Lease Comps'!{H['Notes']}{r_i}",
                        'values': [[(ex + ' ' if ex else '') + f['note']]]})
if fixdata:
    values_batch(s, fixdata)
    print(f'\nCorrections ({len(fixlog)} fields):')
    for l in fixlog:
        print(l)

if comp_rows or fixdata:
    changelog(s, 'DECK COMPS',
              f'Added {len(comp_rows)} comps JD selected from six broker decks, each citing its '
              'source deck in Notes, and applied his two rulings on existing comps: LC-0019 (Ramp) '
              'rewritten as the whole 285,303 SF premises dated March 2026, and LC-0049 (BILT) '
              'corrected to 58,434 SF across GRND, LL and E2-6. Optiver and Sigma recorded as two '
              'deals each per his instruction; Coinbase left on E5 and typed Expansion, with the '
              'E24-25 deal deliberately not added; Apple and OpenAI excluded. Seats and condition '
              'are blank throughout — no deck carries either.',
              len(comp_rows) + len(fixlog))

summary, fails = qa_status(s)
print('\nQA:', summary, '| failing:', fails or 'none')
