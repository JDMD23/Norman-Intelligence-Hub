"""Undo the Harvey AI merge and set both deals' dates — JD, 2026-09-03.

Earlier in the session JD said the two Harvey rows "should be one comp" and LC-0052 absorbed
LC-0053. He has since clarified that Harvey signed TWO deals at 1 Madison Avenue: the initial
lease in October 2025 and an expansion in March 2026. So the merge is reversed.

LC-0053 is restored from its Changelog receipt rather than given a new ID: the comp always
existed and the deletion was mistaken, so restoring it under its own ID is an undo, not the
ID reuse the contract forbids.

Which is which, from JD's survey: the E4 / 92,663 SF row is the March 2026 Expansion; the
E6 / 92,000 SF row is the October 2025 initial New Lease.
"""
from common import session, get_values, values_batch, changelog, qa_status, headers

s = session()
H = headers(s, 'Lease Comps')
rows = get_values(s, "'Lease Comps'!A2:AS300", render='FORMATTED_VALUE')
ids = [r[0] for r in rows if r and r[0]]


def put(a1, value):
    values_batch(s, [{'range': "'Lease Comps'!" + a1, 'values': [[value]]}])


def note_for(comp_id, row, text):
    put(H['Notes'] + str(row), text)


NOTE_53 = ('Harvey AI initial lease at 1 Madison Avenue, October 2025. Restored from the Changelog '
           'after a merge into LC-0052 was reversed: JD confirms Harvey signed two deals here, the '
           'initial lease (this row) and a March 2026 expansion (LC-0052).')
NOTE_52 = ('Harvey AI expansion at 1 Madison Avenue, March 2026 (JD survey). Their second deal here; '
           'the October 2025 initial lease is LC-0053.')
NOTE_109 = ('From JD survey of comparable transactions >25,000 RSF. Submarket confirmed by JD: '
            '225 Park Avenue South sits in PAS / Mad. Square Park. Seats, building class and '
            'condition are not on the survey.')

if 'LC-0053' in ids:
    print('LC-0053 already present — nothing to un-merge')
else:
    restored = [['LC-0053', '2025-10-01', 'Harvey AI', 'CO-0041', '1 Madison Avenue',
                 'PAS / Mad. Square Park', 'Trophy', 'E6', 'Raw', 'New Lease', 'Custom TIA',
                 92000, '', 10.0, 108, 118, '', 16.0, 150]]
    row = 2 + len(ids)
    values_batch(s, [{'range': "'Lease Comps'!A%d:S%d" % (row, row), 'values': restored}])
    note_for('LC-0053', row, NOTE_53)
    print('LC-0053 restored at row %d — E6, 92,000 SF, Oct 2025, New Lease' % row)

for i, r in enumerate(rows, 2):
    if r and r[0] == 'LC-0052':
        for h, v in [('RSF', 92663), ('Floor(s)', 'E4'), ('Date Signed', '2026-03-01'),
                     ('Deal Type', 'Expansion')]:
            put(H[h] + str(i), v)
        note_for('LC-0052', i, NOTE_52)
        print('LC-0052 restored — E4, 92,663 SF, Mar 2026, Expansion')
        break

for i, r in enumerate(rows, 2):
    if r and r[0] == 'LC-0109':
        note_for('LC-0109', i, NOTE_109)
        print('LC-0109 Monday.com — submarket confirmed by JD, note updated')
        break

changelog(s, 'MERGE REVERSED', 'Un-merged Harvey AI per JD: they signed two deals at 1 Madison '
          'Avenue. LC-0052 is the March 2026 expansion (E4, 92,663 SF); LC-0053 is the October 2025 '
          'initial lease (E6, 92,000 SF), restored from its Changelog receipt under its own ID. '
          'Monday.com submarket confirmed as PAS / Mad. Square Park.', 2)
summary, fails = qa_status(s)
print('\nQA:', summary, '| failing:', fails or 'none')
