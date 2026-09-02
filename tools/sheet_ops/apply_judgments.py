"""Apply the owner-reviewed resolutions to the three judgment items the v4
migration surfaced (see Changelog receipts and docs/LEASE_COMPS_DESIGN.md).

1. Synthesia (CO-0080): the Series E $200M round was formally announced
   2026-01-26 (GV-led; the 2025-10 date reflected 'in talks' press). The audit
   dual-source-confirmed this. Fix the Funding Rounds date.
2. Abridge (CO-0001): 2019 disclosure was '$15M across seed + Series A'
   combined; the per-round split is not public. Don't guess — flag both early
   rows confidence REVIEW with an explanatory note.
3. Round-type vocabulary: normalize the four out-of-vocabulary types in
   Funding Rounds to Reference's canonical RoundTypes, preserving the original
   label in Notes. Keeps Dashboard stage benchmarks cohorted instead of
   fragmenting into near-empty stages.
"""
from common import session, get_values, changelog, qa_status, SID

TYPE_MAP = {
    'Growth': 'Late Stage Venture',
    'Direct Listing': 'Public Listing / Reverse Merger',
    'Common Stock Financing': 'Late Stage Venture',
    'Series B / Strategic': 'Series B',
}

s = session()
rows = get_values(s, "'Funding Rounds'!A2:N3000", render='FORMATTED_VALUE')
data = []
receipts = []

for i, r in enumerate(rows):
    rownum = i + 2
    if not r or not str(r[0]).startswith('FR-'):
        continue
    pad = r + [''] * (14 - len(r))
    frid, cid, rtype, rdate, note = pad[0], pad[1], pad[4], pad[5], pad[13]

    # 1. Synthesia date correction
    if cid == 'CO-0080' and rtype == 'Series E' and str(rdate).startswith('2025-10'):
        data.append({'range': f"'Funding Rounds'!F{rownum}", 'values': [['2026-01-26']]})
        data.append({'range': f"'Funding Rounds'!N{rownum}", 'values': [[
            (note + ' | ' if note else '') + 'Date corrected 2025-10 -> 2026-01-26: round formally '
            'announced 2026-01-26 (GV-led); earlier date reflected in-talks press (2026-08 audit).']]})
        receipts.append(f'{frid} Synthesia Series E date -> 2026-01-26')

    # 2. Abridge early-round split flagged REVIEW
    if cid == 'CO-0001' and str(rdate).startswith('2019') and rtype in ('Seed', 'Series A'):
        data.append({'range': f"'Funding Rounds'!M{rownum}", 'values': [['REVIEW']]})
        data.append({'range': f"'Funding Rounds'!N{rownum}", 'values': [[
            (note + ' | ' if note else '') + '2019 disclosure was $15M combined across seed + '
            'Series A; per-round split not public. Verify split before treating amounts as exact.']]})
        receipts.append(f'{frid} Abridge {rtype} -> confidence REVIEW (undisclosed split)')

    # 3. Vocabulary normalization
    if rtype in TYPE_MAP:
        data.append({'range': f"'Funding Rounds'!E{rownum}", 'values': [[TYPE_MAP[rtype]]]})
        data.append({'range': f"'Funding Rounds'!N{rownum}", 'values': [[
            (note + ' | ' if note else '') + f'Round type normalized to Reference vocabulary '
            f'(original label: "{rtype}").']]})
        receipts.append(f'{frid} type "{rtype}" -> "{TYPE_MAP[rtype]}"')

if not data:
    print('nothing to apply — judgments already recorded')
    raise SystemExit(0)

r = s.post(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}/values:batchUpdate',
           json={'valueInputOption': 'USER_ENTERED', 'data': data})
assert r.status_code == 200, r.json()
print(f'applied {len(receipts)} resolutions:')
for x in receipts:
    print('  ', x)
changelog(s, 'JUDGMENT RESOLUTIONS',
          'Owner-approved resolutions to v4 migration review items: Synthesia Series E date '
          '-> 2026-01-26 (audit-confirmed announcement date); Abridge 2019 seed/A rows flagged '
          'REVIEW (combined $15M disclosure, split unverified); 4 out-of-vocabulary round types '
          'normalized to Reference RoundTypes with originals preserved in Notes.', len(receipts))
summary, fails = qa_status(s)
print('QA:', summary, '| failing:', fails or 'none')
