"""Split Clay (LC-0020) across its three floors, following the decks.

LC-0020 was held back from the 2026-09-03 TI pass precisely because its floors carry different
economics, and it is the comp the Floor Detail tab was built for. It never actually got split.

Two of the four decks that carry Clay give the full breakdown; the other two print only the
E14/E16 headline, which is what the book has been holding for all 163,095 SF:

  MTS_Comps_05.21.26            E14/E16: $84 / $90 / $96   P15: $75 / $81 / $87
                                free  E14: 14, P15/E16: 10/1/2027 Fixed RCD
                                TI    $145 + $10 Demolition Allowance + $12 Restroom Allowance
  Relevant_Completed_06.29.26   identical
  NYC_Relevant_Tech-Ai_05.19.26 $84 | $90 | $96, 14 months, $145      (headline only)
  NYC_MTS_Comps_25000_03.26.26  $84 (5) / $90 (5) / $96 (5), 14, $145 (headline only)

Two things change at comp level:

  Rent  P15 is $9/SF below the entire floors across all three tranches, so carrying $84/$90/$96
        over the whole premises overstates the comp. The blended rate replaces it.
  TI    $145 -> $167. The demolition and restroom allowances are landlord money delivered to the
        tenant and belong in the concession the same way TI does.

FLOOR RSF IS AN ESTIMATE. No deck breaks the 163,095 SF down, so this splits it in equal thirds
(54,365 each), the same treatment JD approved for General Catalyst and Bridgewater. It is
conservative in a knowable direction: P15 is a PARTIAL floor and is therefore almost certainly
smaller than the two entire floors, which means the true blend sits above $81 and closer to $84.
Replace the Floor Detail RSF as soon as the real split is known and the comp-level rate follows.

Free rent per floor is recorded only where the deck states a month count. E14 is 14 months;
P15 and E16 are expressed as a fixed rent commencement date of 1 Oct 2027, which cannot be
converted without the delivery date, so those stay blank rather than being guessed.
"""
from common import session, get_values, values_batch, changelog, qa_status, headers

RSF = 163095
THIRD = RSF // 3
SPLIT = [('E14 (entire)', THIRD, 84, 14,
          'Entire 14th floor. $84 / $90 / $96 with 14 months abated.'),
         ('P15 (partial)', THIRD, 75, None,
          'Partial 15th floor, $9/SF below the entire floors: $75 / $81 / $87. Free rent is '
          'stated as a fixed rent commencement date of 1 Oct 2027, not a month count, so it is '
          'left blank rather than guessed.'),
         ('E16 (entire)', RSF - 2 * THIRD, 84, None,
          'Entire 16th floor. $84 / $90 / $96. Free rent stated as a fixed RCD of 1 Oct 2027.')]
TI = 167   # $145 TI + $10 demolition + $12 restrooms
P1, P2, P3 = 81, 87, 93   # equal-thirds blend of (84, 75, 84) / (90, 81, 90) / (96, 87, 96)

NOTE = ('JD 9/15: split across its three floors per MTS_Comps_05.21.26 and '
        'Relevant_Completed_06.29.26, which both give E14/E16 at $84/$90/$96 and P15 at '
        '$75/$81/$87 — the book had been carrying the E14/E16 rate over all 163,095 SF. The '
        'comp-level rent is now the RSF-weighted blend; the real per-floor terms are on the '
        'Floor Detail tab. TI $145 -> $167, being the $145 allowance plus the $10 demolition and '
        '$12 restroom allowances those same decks record. FLOOR RSF IS AN ESTIMATE: no deck '
        'breaks out the 163,095 SF, so it is split in equal thirds. P15 is a partial floor and '
        'almost certainly smaller than the two entire floors, which means the true blend sits '
        'above $81 and nearer $84 — replace the Floor Detail RSF when the real split is known.')

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


WANT = {'Rent P1 ($/RSF, mo 1-60)': P1, 'Rent P2 ($/RSF, mo 61-120)': P2,
        'Rent P3 ($/RSF, mo 121+)': P3, 'TI $/SF': TI}
data, log = [], []
for i, r in enumerate(rows, 2):
    if col(r, 'Comp ID') != 'LC-0020':
        continue
    for hdr, v in WANT.items():
        if not same(col(r, hdr), v):
            data.append({'range': f"'Lease Comps'!{H[hdr]}{i}", 'values': [[v]]})
            log.append(f'   LC-0020 {hdr:28} {col(r, hdr)!r} -> {v!r}')
    ex = col(r, 'Notes').strip()
    if NOTE not in ex:
        data.append({'range': f"'Lease Comps'!{H['Notes']}{i}",
                     'values': [[(ex + ' ' if ex else '') + NOTE]]})
if data:
    values_batch(s, data)
    print(f'LC-0020 updated ({len(log)} fields):')
    for l in log:
        print(l)
else:
    print('LC-0020 already current')

fd = get_values(s, "'Floor Detail'!A2:J200", render='FORMATTED_VALUE')
fd_live = [r for r in fd if r and r[0]]
have = {(r[1], r[3]) for r in fd_live if len(r) > 3}
todo = [x for x in SPLIT if ('LC-0020', x[0]) not in have]
if todo:
    nxt = max([int(r[0][3:]) for r in fd_live if r[0].startswith('FD-')] or [0]) + 1
    row = 2 + len(fd_live)
    vals, fml = [], []
    for k, (fl, rsf, rent, free, note) in enumerate(todo):
        vals.append(['FD-%04d' % nxt, 'LC-0020', None, fl, rsf, rent, TI,
                     free if free is not None else '', None, note])
        r_ = row + k
        fml += [{'range': f"'Floor Detail'!C{r_}", 'values': [[
            f'=IF($B{r_}="","",IFERROR(INDEX(LeaseComps_Tenants,MATCH($B{r_},LeaseComps_IDs,0)),"UNKNOWN COMP"))']]},
            {'range': f"'Floor Detail'!I{r_}", 'values': [[
                f'=IF(OR($B{r_}="",$E{r_}=""),"",LET(t,SUMIF(FloorDetail_CompIds,$B{r_},FloorDetail_RSF),IF(t=0,"",$E{r_}/t)))']]}]
        nxt += 1
    # write the data columns only, then restore the two computed columns
    values_batch(s, [{'range': f"'Floor Detail'!A{row}:B{row+len(vals)-1}",
                      'values': [[v[0], v[1]] for v in vals]},
                     {'range': f"'Floor Detail'!D{row}:H{row+len(vals)-1}",
                      'values': [v[3:8] for v in vals]},
                     {'range': f"'Floor Detail'!J{row}:J{row+len(vals)-1}",
                      'values': [[v[9]] for v in vals]}])
    values_batch(s, fml)
    print(f'\nFloor Detail rows added ({len(vals)}):')
    for v in vals:
        print(f"   {v[0]} {v[3]:16} {v[4]:>8,} SF  ${v[5]}  TI ${v[6]}  free {v[7] or '(fixed RCD)'}")
else:
    print('\nFloor Detail already carries Clay')

changelog(s, 'CLAY FLOOR SPLIT',
          'Split LC-0020 (Clay, 11 Madison) across its three floors per MTS_Comps_05.21.26 and '
          'Relevant_Completed_06.29.26. The book had been carrying the E14/E16 rate of $84/$90/$96 '
          'over all 163,095 SF; P15 is $9/SF below that, so the comp-level rent becomes the '
          'RSF-weighted blend $81/$87/$93 and the real per-floor terms move to Floor Detail. TI '
          '$145 -> $167, adding the $10 demolition and $12 restroom allowances the same decks '
          'record. Floor RSF is an equal-thirds estimate — no deck breaks out the 163,095 SF — '
          'and since P15 is partial the true blend sits above $81. This is the comp the Floor '
          'Detail tab was built for on 2026-09-03 and it had never actually been split.', 3)

summary, fails = qa_status(s)
print('\nQA:', summary, '| failing:', fails or 'none')
