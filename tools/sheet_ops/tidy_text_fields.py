"""Normalise text dirt in Lease Comps input fields.

Three unambiguous defects found by the 2026-09-06 consistency audit. None of these is a
judgement call — each is the same value written wrong, and each breaks an exact-match
grouping somewhere (tenant rollups, address de-duplication, the submarket tables).

  LC-0103  trailing spaces on Tenant / Address / Floor(s) — 'Moment ' does not group with
           'Moment', which is why the comp needed a Reference variant mapping it to itself.
  LC-0069  '18 west 18th Street' — same building as LC-0095 (Runway), different casing, so
           the two do not de-duplicate as one address.
  LC-0049  floor 'E2 -E 6' — stray spaces inside the floor range.

Idempotent: writes only what differs.
"""
from common import session, get_values, values_batch, changelog, qa_status, headers

FIXES = {
    'LC-0103': {'Tenant': 'Moment', 'Address': '325 Hudson Street', 'Floor(s)': 'E3 + E10'},
    'LC-0069': {'Address': '18 West 18th Street'},
    'LC-0049': {'Floor(s)': 'E2-E6'},
}

s = session()
H = headers(s, 'Lease Comps')
rows = get_values(s, "'Lease Comps'!A2:AS1206", render='FORMATTED_VALUE')


def col(r, letter):
    i = 0
    for ch in letter:
        i = i * 26 + ord(ch) - 64
    return str(r[i-1]) if i-1 < len(r) else ''


data, applied = [], []
for i, r in enumerate(rows, 2):
    cid = col(r, H['Comp ID'])
    for hdr, want in FIXES.get(cid, {}).items():
        cur = col(r, H[hdr])
        if cur != want:
            data.append({'range': f"'Lease Comps'!{H[hdr]}{i}", 'values': [[want]]})
            applied.append(f'{cid}  {hdr}: {cur!r} -> {want!r}')

if not data:
    print('nothing to tidy — all three already clean')
else:
    values_batch(s, data)
    print(f'{len(data)} cells written')
    for a in applied:
        print('  ' + a)
    changelog(s, 'TEXT TIDY',
              'Normalised three text defects found by the consistency audit: trailing spaces on '
              "LC-0103 (Moment), '18 west 18th Street' -> '18 West 18th Street' on LC-0069 so it "
              'de-duplicates against LC-0095 at the same building, and floor range "E2 -E 6" -> '
              '"E2-E6" on LC-0049. Values only — no economics touched.', len(applied))

summary, fails = qa_status(s)
print('\nQA:', summary, '| failing:', fails or 'none')
