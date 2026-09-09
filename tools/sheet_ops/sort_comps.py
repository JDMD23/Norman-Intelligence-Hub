"""Keep Lease Comps in date order, newest first.

The tab's convention is reverse chronological — the most recent signing at the top. Appending a
comp at the bottom breaks that, so this runs after any add.

Only INPUT cells move. The calc columns are per-row formulas that reference their own row, so
they are left exactly where they are and simply recompute against whatever inputs land in their
row. Input columns are read from _Schema by role, not hard-coded, and must be contiguous plus
the separate Notes column.

The sort is stable: comps sharing a signing date keep their existing relative order, so a run
moves as few rows as possible. A comp with no signing date yet is parked at the bottom and
named in the output rather than blocking the run — it will show MISSING INPUTS until the date
is filled in.

Idempotent: writes nothing when the tab is already ordered.
"""
import sys

from common import session, get_values, values_batch, changelog, qa_status, headers, SID

s = session()
H = headers(s, 'Lease Comps')

# input columns, from the schema contract rather than hard-coded letters
schema = get_values(s, '_Schema!A1:J400', render='FORMATTED_VALUE')
inputs = [r[1] for r in schema if r and r[0] == 'Lease Comps' and len(r) > 5 and r[5] == 'input']
assert inputs, 'no input columns found in _Schema for Lease Comps'


def ci(letter):
    n = 0
    for ch in letter:
        n = n * 26 + ord(ch) - 64
    return n - 1


block = [c for c in inputs if ci(c) <= ci(H['TI $/SF'])]      # the contiguous A..S run
extra = [c for c in inputs if c not in block]                  # Notes, which sits among the calcs
first, last = min(block, key=ci), max(block, key=ci)
assert [ci(c) for c in sorted(block, key=ci)] == list(range(ci(first), ci(last) + 1)), \
    'input block is not contiguous — this script assumes A..%s' % last

# real date serials: common.get_values formats dates, so fetch this one directly
r = s.get('https://sheets.googleapis.com/v4/spreadsheets/%s/values/%s' % (SID, "'Lease Comps'!A2:AS400"),
          params={'valueRenderOption': 'UNFORMATTED_VALUE',
                  'dateTimeRenderOption': 'SERIAL_NUMBER'}).json().get('values', [])
rows = [x for x in r if x and x[0]]
n = len(rows)
width = ci(last) + 1
grid = [(x + [''] * width)[:width] for x in rows]
notes = [(x + [''] * (ci(extra[0]) + 1))[ci(extra[0])] if extra else '' for x in rows]

date_i = ci(H['Date Signed'])
undated = [g[0] for g in grid if not isinstance(g[date_i], (int, float))]
if undated:
    print('%d comp(s) have no signing date and are parked at the bottom: %s'
          % (len(undated), ', '.join(undated)))

# Dated comps first, newest at the top; undated ones fall to the bottom in their existing order.
# Stable, so comps sharing a date keep their relative positions and a run moves as few rows as
# it can.
def key(i):
    d = grid[i][date_i]
    return (0, -d) if isinstance(d, (int, float)) else (1, 0)


order = sorted(range(n), key=key)
if order == list(range(n)):
    print('Lease Comps already in date order (newest first) — %d comps, nothing to do' % n)
    sys.exit(0)

moved = sum(1 for i, j in enumerate(order) if i != j)
values_batch(s, [
    {'range': "'Lease Comps'!%s2:%s%d" % (first, last, n + 1), 'values': [grid[i] for i in order]},
] + ([{'range': "'Lease Comps'!%s2:%s%d" % (extra[0], extra[0], n + 1),
       'values': [[notes[i]] for i in order]}] if extra else []))

top = [(grid[i][0], grid[i][2]) for i in order[:3]]
bottom = [(grid[i][0], grid[i][2]) for i in order[-3:]]
print('sorted %d comps by Date Signed, newest first — %d rows moved' % (n, moved))
print('  now first: %s' % ', '.join('%s %s' % t for t in top))
print('  now last:  %s' % ', '.join('%s %s' % t for t in bottom))
changelog(s, 'SORT', 'Re-sorted Lease Comps by Date Signed, newest first (%d of %d rows moved). '
          'Only input cells were rewritten; the per-row calc formulas stayed in place and '
          'recomputed against their new row.' % (moved, n), moved)
summary, fails = qa_status(s)
print('\nQA:', summary, '| failing:', fails or 'none')
