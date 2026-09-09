"""Normalise Funding Rounds confidence to the Reference vocabulary (HIGH / MEDIUM / LOW / REVIEW).

Title-case entries ("High", "Medium", "Low") are the same judgement in the wrong case; the
contract says enum columns hold Reference values only. Case-only change, receipted.
"""
from common import session, get_values, values_batch, changelog

s = session()
vocab = {r[0].upper(): r[0] for r in get_values(s, 'ConfidenceLevels', render='FORMATTED_VALUE') if r}
rows = get_values(s, "'Funding Rounds'!M2:M3000", render='FORMATTED_VALUE')
data = []
for i, r in enumerate(rows, 2):
    v = r[0] if r else ''
    if v and v not in vocab.values() and v.upper() in vocab:
        data.append({'range': f"'Funding Rounds'!M{i}", 'values': [[vocab[v.upper()]]]})
if data:
    values_batch(s, data)
    changelog(s, 'VOCAB TIDY', f'Funding Rounds confidence: {len(data)} title-case values normalised to the '
              'Reference vocabulary (case only).', len(data))
print(f'confidence normalised on {len(data)} rows')
