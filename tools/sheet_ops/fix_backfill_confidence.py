"""Downgrade the migration-backfilled rounds the company research does not support.

The v4 migration backfilled 39 latest rounds from the 2026-08/09 audit snapshot and stamped
every one HIGH. Reading each company's research narrative against the round it produced, four
are contradicted or unsupported. They are named here with the specific reason rather than
matched by keyword — a keyword scan flags companies whose narrative raises an unrelated
concern (identity mapping, tenant-name duplicates, "exclude public cos from velocity"), which
is not a reason to doubt the round.

Idempotent: rounds already at REVIEW are left alone.
"""
from common import session, get_values, values_batch, changelog, qa_status

# round id -> (company, why the narrative does not support this round)
UNSUPPORTED = {
    'FR-0279': ('Tempo Labs (CO-0082)',
                'Companies research states "pre-seed ... funding amount/date not confirmed in public '
                'source" and "insufficient disclosed funding amount/date history"; the $5.0M Seed is '
                'not corroborated.'),
    'FR-0282': ('Traversal (CO-0087)',
                'Companies research states "funding amount/total mismatch needs review" and "latest '
                'amount seems inconsistent with total funding" ($5M latest vs $53M total).'),
    'FR-0283': ('Verkada (CO-0089)',
                'Companies research describes Dec 2025 as a "$20M venture/unknown round" and calls the '
                'classification "needs review"; the backfilled row claims Series E $100M.'),
    'FR-0247': ('Actively AI (CO-0002)',
                'Companies research tracks funding only through Apr 2025 Series A ($17.5M, total '
                '$22.5M) and flags details as needing verification; the backfilled Apr 2026 Series B '
                '$45M is uncorroborated there.'),
}

s = session()
rows = get_values(s, "'Funding Rounds'!A2:N3000", render='FORMATTED_VALUE')
data, done = [], []
for i, r in enumerate(rows, 2):
    if not r or r[0] not in UNSUPPORTED:
        continue
    who, why = UNSUPPORTED[r[0]]
    conf = r[12] if len(r) > 12 else ''
    if conf == 'REVIEW':
        done.append(f'{r[0]} {who} — already REVIEW')
        continue
    note = r[13] if len(r) > 13 else ''
    data.append({'range': f"'Funding Rounds'!M{i}", 'values': [['REVIEW']]})
    data.append({'range': f"'Funding Rounds'!N{i}",
                 'values': [[(note + ' | ' if note else '') +
                             f'Confidence downgraded {conf} -> REVIEW: {why}']]})
    done.append(f'{r[0]} {who} — {conf} -> REVIEW')

for line in done:
    print('  ', line)
if not data:
    print('nothing to downgrade — all four already at REVIEW')
else:
    values_batch(s, data)
    changelog(s, 'CONFIDENCE DOWNGRADE',
              f'{len(data) // 2} migration-backfilled rounds moved HIGH -> REVIEW where the company '
              'research contradicts or does not corroborate the round (Tempo Labs, Traversal, Verkada, '
              'Actively AI). The backfill had stamped all 39 rounds HIGH regardless of source strength.',
              len(data) // 2)
    print(f'downgraded {len(data) // 2} rounds')
print('QA:', qa_status(s)[0])
