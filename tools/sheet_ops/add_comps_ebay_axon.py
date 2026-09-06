from common import session, get_values, values_batch, changelog, qa_status, headers

# JD, 2026-09-03. Rent given as "94/105" and "$100/5, $110/5" — years-at-rate, which maps onto
# the flat tranches: P1 months 1-60, P2 61-120. Seats from his approximate desk counts.
# eBay's TI is his own figure ($140), so it stands rather than the $150 turnkey benchmark.
COMPS = [
    dict(tenant='eBay', company='eBay', date='2026-06-01', addr='122 Fifth Avenue',
         sub='Flatiron', cls='Class A', floors='E2', cond='', deal='New Lease',
         delivery='LL Turnkey', rsf=27902, seats=140, term=7.0, p1=94, p2=105, p3='',
         free=7, ti=140,
         note='From JD. Turnkey at $140/SF — his figure, so it stands rather than the $150 '
              'turnkey benchmark. Seats approximate (~140 desks). Condition not stated. '
              'Deal type assumed New Lease — correct if it was a renewal or expansion.'),
    dict(tenant='Axon', company='Axon', date='2026-07-01', addr='225 Park Avenue South',
         sub='PAS / Mad. Square Park', cls='', floors='E3', cond='', deal='New Lease',
         delivery='Custom TIA', rsf=42855, seats=250, term=10.0, p1=100, p2=110, p3='',
         free=16, ti=150,
         note='From JD. Rent $100 (5yr) / $110 (5yr), $150/SF in TIA. Seats approximate '
              '(~250). Building class and condition not stated. Deal type assumed New Lease — '
              'correct if it was a renewal or expansion.'),
]

s = session()
H = headers(s, 'Lease Comps')
rows = get_values(s, "'Lease Comps'!A2:AS400", render='FORMATTED_VALUE')
existing = {(str(r[2]).strip().lower(), str(r[4]).strip().lower()) for r in rows if r and len(r) > 4}
todo = [x for x in COMPS if (x['tenant'].lower(), x['addr'].lower()) not in existing]
if not todo:
    print('both already present — nothing to add')
    raise SystemExit(0)

ids = [r[0] for r in rows if r and r[0]]
next_lc = max(int(x[3:]) for x in ids) + 1
co = get_values(s, 'Companies!A2:B300', render='FORMATTED_VALUE')
co_ids = [r[0] for r in co if r and r[0]]
by_name = {str(r[1]).strip().lower(): r[0] for r in co if r and len(r) > 1}
next_co = max(int(x[3:]) for x in co_ids) + 1
lc_row = 2 + len(ids)
co_row = 2 + len(co_ids)

new_co, comp_rows, added = [], [], []
for x in todo:
    key = x['company'].strip().lower()
    if key in by_name:
        cid = by_name[key]
    else:
        cid = 'CO-%04d' % next_co
        next_co += 1
        new_co.append([cid, x['company']])
        by_name[key] = cid
    comp_id = 'LC-%04d' % next_lc
    next_lc += 1
    comp_rows.append([comp_id, x['date'], x['tenant'], cid, x['addr'], x['sub'], x['cls'],
                      x['floors'], x['cond'], x['deal'], x['delivery'], x['rsf'], x['seats'],
                      x['term'], x['p1'], x['p2'], x['p3'], x['free'], x['ti']])
    added.append((comp_id, cid, x))

if new_co:
    values_batch(s, [{'range': 'Companies!A%d:B%d' % (co_row, co_row + len(new_co) - 1),
                      'values': new_co}])
    print('Companies added: ' + ', '.join('%s %s' % (r[0], r[1]) for r in new_co))

values_batch(s, [{'range': "'Lease Comps'!A%d:S%d" % (lc_row, lc_row + len(comp_rows) - 1),
                  'values': comp_rows}])
for i, (comp_id, cid, x) in enumerate(added):
    values_batch(s, [{'range': "'Lease Comps'!%s%d" % (H['Notes'], lc_row + i),
                      'values': [[x['note']]]}])
    print('  %s  %s  %-6s %s  %s SF  %syr  $%s/$%s  %smo free  TI $%s  %s seats'
          % (comp_id, cid, x['tenant'], x['addr'], format(x['rsf'], ','), x['term'],
             x['p1'], x['p2'], x['free'], x['ti'], x['seats']))

changelog(s, 'COMPS ADDED', 'Added %d comps from JD: %s. Rent entered as flat tranches from his '
          'years-at-rate notation; seats from his approximate desk counts. eBay keeps his own '
          '$140/SF turnkey figure rather than the $150 benchmark. Deal type assumed New Lease on '
          'both — not stated.' % (len(added), ', '.join(x['tenant'] for _, _, x in added)), len(added))
print('\nQA:', qa_status(s)[0])
