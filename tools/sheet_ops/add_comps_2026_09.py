"""Add six comparable transactions from JD's >25,000 RSF survey (screenshot, 2026-09-03).

Rent notation on the survey — "$92 (5) / $100 (5)" — is years-at-rate, which maps directly onto
the workbook's flat tranches: P1 months 1-60, P2 61-120, P3 121+.

Not on the survey and therefore left blank per the contract (blank = unknown, never 0): Seats,
Building Class, Condition. Delivery is set to Custom TIA because the survey states a TI allowance.
Submarkets follow the nearest precedent already in the book; the one judgement call is flagged in
Notes and in the report to JD.

Idempotent: skips any comp whose tenant + address is already present.
"""
from common import (session, get_values, values_batch, changelog, qa_status, headers, SID)

#  tenant, company, date, address, submarket, floors, rsf, term, p1, p2, p3, free, ti, deal, note
COMPS = [
 ('Suno AI', 'Suno AI', '2026-08-01', '295 Fifth Avenue', 'PAS / Mad. Square Park', 'E2-E3',
  87176, 11.25, 92, 100, None, 15, 150, 'New Lease',
  'From JD survey of comparable transactions >25,000 RSF. Term 11y 3m. Seats/class/condition not on the survey.'),
 ('Anthropic', 'Anthropic', '2026-07-01', '330 Hudson Street', 'Hudson Square', 'P1, E2-E16',
  462513, 13.67, 113, 123, 133, 17, 160, 'New Lease',
  'From JD survey. Term 13y 8m; rent $113 (5yr) / $123 (5yr) / $133 (2yr). Largest comp in the book.'),
 ('Altana AI', 'Altana AI', '2026-06-01', '2 Penn Plaza', 'Hudson Yards / Penn Station', 'E21',
  62309, 10.0, 120, 130, None, 8, 150, 'New Lease',
  'From JD survey.'),
 ('Fanatics', 'Fanatics', '2026-02-01', '95 Morton Street', 'Hudson Square', 'P1, E2-E8',
  210092, 10.0, 109, 119, None, 12, 125, 'Renewal + Expansion',
  'From JD survey. Submarket inferred from location (Hudson Square) — no 95 Morton precedent in the book.'),
 ('PayPal', 'PayPal', '2025-12-01', '345 Hudson Street', 'Hudson Square', 'E7-E9',
  261847, 11.58, 103, 113, None, 19, 165, 'New Lease',
  'From JD survey. Term 11y 7m; rent $103 (5yr) / $113 (6yr).'),
 ('Monday.com', 'Monday.com', '2025-11-01', '225 Park Avenue South', 'PAS / Mad. Square Park', 'E12-E16',
  138611, 10.0, 102, 112, None, 6, 60, 'Renewal',
  'From JD survey. SUBMARKET UNCONFIRMED: 215 PAS is recorded as Union Square and 257 PAS as '
  'PAS / Mad. Square Park; 225 sits between them. Confirm with JD.'),
]

s = session()
H = headers(s, 'Lease Comps')
rows = get_values(s, "'Lease Comps'!A2:AS1207", render='FORMATTED_VALUE')
existing = {(str(r[2]).strip().lower(), str(r[4]).strip().lower()) for r in rows if r and len(r) > 4}
todo = [c for c in COMPS if (c[0].lower(), c[3].lower()) not in existing]
if not todo:
    print('all six already present — nothing to add')
    raise SystemExit(0)

lc_ids = [r[0] for r in rows if r and r[0]]
next_lc = max(int(x[3:]) for x in lc_ids) + 1
co = get_values(s, 'Companies!A2:B200', render='FORMATTED_VALUE')
co_ids = [r[0] for r in co if r and r[0]]
by_name = {str(r[1]).strip().lower(): r[0] for r in co if r and len(r) > 1}
next_co = max(int(x[3:]) for x in co_ids) + 1
first_lc_row = 2 + len(lc_ids)
first_co_row = 2 + len(co_ids)

new_co, comp_rows, report = [], [], []
for i, (tenant, company, date, addr, sub, floors, rsf, term, p1, p2, p3, free, ti, deal, note) in enumerate(todo):
    key = company.strip().lower()
    if key in by_name:
        cid = by_name[key]
    else:
        cid = f'CO-{next_co:04d}'; next_co += 1
        new_co.append([cid, company])
        by_name[key] = cid
    comp_id = f'LC-{next_lc:04d}'; next_lc += 1
    # A..S: id, date, tenant, company, address, submarket, class, floors, condition, deal,
    #       delivery, rsf, seats, term, p1, p2, p3, free, ti
    comp_rows.append([comp_id, date, tenant, cid, addr, sub, '', floors, '', deal, 'Custom TIA',
                      rsf, '', term, p1, p2 if p2 else '', p3 if p3 else '', free, ti])
    report.append((comp_id, cid, tenant, rsf, term, ti, note))

if new_co:
    values_batch(s, [{'range': f'Companies!A{first_co_row}:B{first_co_row + len(new_co) - 1}',
                      'values': new_co}])
    print(f'Companies: {len(new_co)} added — ' + ', '.join(f'{c[0]} {c[1]}' for c in new_co))

values_batch(s, [{'range': f"'Lease Comps'!A{first_lc_row}:S{first_lc_row + len(comp_rows) - 1}",
                  'values': comp_rows}])
NOTE = H['Notes']
values_batch(s, [{'range': f"'Lease Comps'!{NOTE}{first_lc_row + i}", 'values': [[r[6]]]}
                 for i, r in enumerate(report)])
print(f"\nLease Comps: {len(comp_rows)} added at rows {first_lc_row}-{first_lc_row + len(comp_rows) - 1}")
for comp_id, cid, tenant, rsf, term, ti, _ in report:
    print(f'  {comp_id}  {cid}  {tenant:12} {rsf:>8,} SF  {term:>5.2f}yr  TI ${ti}')

changelog(s, 'COMPS ADDED', f'Added {len(comp_rows)} comparable transactions from JD\'s >25,000 RSF '
          'survey: ' + ', '.join(r[2] for r in report) + '. Rent entered as flat tranches per the '
          'survey\'s years-at-rate notation. Seats, building class and condition left blank — not on '
          'the survey. Monday.com submarket needs confirmation.', len(comp_rows))
summary, fails = qa_status(s)
print('\nQA:', summary, '| failing:', fails or 'none')
