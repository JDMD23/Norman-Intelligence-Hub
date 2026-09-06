from common import session, get_values, values_batch, changelog, qa_status, headers

# JD, 2026-09-03. Rent "$72/SF for 5 and $79/5" is years-at-rate -> P1 months 1-60, P2 61-120;
# on an 11-year term the blank P3 carries P2 through months 121-132, which is the model's
# intent. Density not available, so Seats stays blank (unknown, never 0), which also blanks
# Cost/Seat and RSF/Seat. Signed August 2026.
X = dict(tenant='David Protein', company='David Protein', date='2026-08-01', addr='395 Hudson Street',
         sub='Hudson Square', cls='Class B', floors='P4', cond='', deal='New Lease',
         delivery='Custom TIA', rsf=57000, seats='', term=11.0, p1=72, p2=79, p3='',
         free=22, ti=155)
NOTE = ('From JD. Partial 4th floor, $72 (5yr) / $79 (5yr) on an 11-year term, $155/SF in TIA, '
        '22 months free, signed August 2026. Density not available, so Seats is blank and '
        'Cost/Seat and RSF/Seat stay blank with it. Building class follows the other 395 Hudson '
        'comp (LC-0045). Deal type assumed New Lease.')

s = session()
H = headers(s, 'Lease Comps')
rows = get_values(s, "'Lease Comps'!A2:AS400", render='FORMATTED_VALUE')
if any(r and len(r) > 4 and str(r[2]).strip().lower() == X['tenant'].lower()
       and str(r[4]).strip().lower() == X['addr'].lower() for r in rows):
    print('David Protein at 395 Hudson already present — nothing to add')
    raise SystemExit(0)

ids = [r[0] for r in rows if r and r[0]]
co = get_values(s, 'Companies!A2:B300', render='FORMATTED_VALUE')
co_ids = [r[0] for r in co if r and r[0]]
by_name = {str(r[1]).strip().lower(): r[0] for r in co if r and len(r) > 1}
cid = by_name.get(X['company'].lower())
if not cid:
    cid = 'CO-%04d' % (max(int(x[3:]) for x in co_ids) + 1)
    values_batch(s, [{'range': 'Companies!A%d:B%d' % (2 + len(co_ids), 2 + len(co_ids)),
                      'values': [[cid, X['company']]]}])
    print('Companies: %s %s added' % (cid, X['company']))

comp_id = 'LC-%04d' % (max(int(x[3:]) for x in ids) + 1)
row = 2 + len(ids)
values_batch(s, [{'range': "'Lease Comps'!A%d:S%d" % (row, row), 'values': [[
    comp_id, X['date'], X['tenant'], cid, X['addr'], X['sub'], X['cls'], X['floors'], X['cond'],
    X['deal'], X['delivery'], X['rsf'], X['seats'], X['term'], X['p1'], X['p2'], X['p3'],
    X['free'], X['ti']]]}])
values_batch(s, [{'range': "'Lease Comps'!%s%d" % (H['Notes'], row), 'values': [[NOTE]]}])
print('%s added at row %d: David Protein, 395 Hudson Street, P4, 57,000 SF, 11yr, $72/$79, '
      '22mo free, TI $155' % (comp_id, row))
changelog(s, 'COMP ADDED', '%s David Protein at 395 Hudson Street (57,000 SF, partial 4th floor, '
          '11yr, $72/$79, 22mo free, TI $155, Aug 2026) from JD. Density not available, so Seats is blank.' % comp_id, 1)
print('QA:', qa_status(s)[0])
