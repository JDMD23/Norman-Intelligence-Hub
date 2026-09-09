"""Apply the owner's TI answers to Lease Comps (session of 2026-09-03).

87 of 103 comps carried TI $0. 26 of those contradicted their own delivery condition — a
Custom TIA or LL Turnkey deal cannot have a zero allowance — which overstated their NER and,
with those comps at 48% of the book by RSF, the Dashboard's headline Avg NER with it.

JD answered each comp in session. Values below are his, verbatim in the note. LC-0020 (Clay,
11 Madison, 163k SF over three floors) is deliberately absent: its floors carry different
economics and it goes through the Floor Detail tab instead.

Also normalises the turnkey benchmark: nine comps sat at $140/SF; JD set the benchmark at
$150/SF everywhere. Receipted separately from the answers. LC-0099 (Rogo, $155) is a specific
negotiated figure and is left alone.

Idempotent: writes only cells that differ.
"""
from common import session, get_values, values_batch, changelog, qa_status, headers

# comp -> (TI $/SF, note, condition or None, delivery or None)
ANSWERS = {
    'LC-0056': (35,  'JD: $35/SF in TIA', None, None),
    'LC-0077': (30,  'JD: $30/SF', None, None),
    'LC-0037': (20,  'JD: $20/SF', None, None),
    'LC-0063': (30,  'JD: $30/SF at 375 West Broadway (11 E 26th keeps $195/SF)', None, None),
    'LC-0065': (30,  'JD: $30/SF', None, None),
    'LC-0070': (0,   'JD: confirmed as-is, no allowance', None, 'As-Is'),
    'LC-0042': (0,   'JD: new prebuilt, no TIA in the deal', 'New prebuilt', 'As-Is'),
    'LC-0002': (0,   'JD: new prebuilt, no TIA; rent $118 yrs 1-5 / $128 yrs 6-7 confirmed',
                'New prebuilt', 'As-Is'),
    'LC-0032': (30,  'JD: $30/SF', None, None),
    'LC-0062': (150, 'JD: turnkey installation; $150/SF turnkey benchmark', None, 'LL Turnkey'),
    'LC-0019': (150, 'JD: Ramp was turnkey; $150/SF turnkey benchmark', None, 'LL Turnkey'),
    'LC-0047': (130, 'JD: $130/SF in TIA', None, None),
    'LC-0051': (150, 'JD: $150/SF in TIA', None, None),
    'LC-0052': (150, 'JD: $150/SF (both Harvey deals)', None, None),
    'LC-0053': (150, 'JD: $150/SF (both Harvey deals)', None, None),
    'LC-0079': (135, 'JD: $135/SF in TIA', None, None),
    'LC-0050': (150, 'JD: $150/SF', None, None),
    'LC-0049': (175, 'JD: $175/SF', None, None),
    'LC-0006': (110, 'JD: $110/SF TIA on the Pace deal', None, None),
    'LC-0093': (175, 'JD: $175/SF TIA', None, None),
    'LC-0082': (75,  'JD: $75/SF', None, None),
    'LC-0086': (85,  'JD: $85/SF', None, None),
    'LC-0089': (60,  'JD: $60/SF', None, None),
    'LC-0085': (0,   'JD: as-is, no allowance', None, 'As-Is'),
    'LC-0043': (40,  'JD: $40/SF', None, None),
}
TURNKEY_BENCHMARK = 150     # JD: normalise the $140 turnkey comps to the $150 benchmark
OLD_BENCHMARK = 140
RENAME = ('CO-0037', 'GlossGenius', 'Genius')   # JD: rename the company; keep the variant

s = session()
H = headers(s, 'Lease Comps')
TI, COND, DLV, NOTE, IDC = H['TI $/SF'], H['Condition'], H['Delivery Condition'], H['Notes'], H['Comp ID']
rows = get_values(s, "'Lease Comps'!A2:AS1207", render='FORMATTED_VALUE')


def col(r, letter):
    i = 0
    for ch in letter:
        i = i * 26 + ord(ch) - 64
    return r[i-1] if i-1 < len(r) else ''


def money(v):
    try:
        return float(str(v).replace('$', '').replace(',', ''))
    except ValueError:
        return None


data, applied, skipped = [], [], []
turnkey = []
for i, r in enumerate(rows, 2):
    cid = col(r, IDC)
    if not cid:
        continue
    cur_ti = money(col(r, TI))
    if cid in ANSWERS:
        ti, note, cond, dlv = ANSWERS[cid]
        bits = []
        if cur_ti != ti:
            data.append({'range': f"'Lease Comps'!{TI}{i}", 'values': [[ti]]}); bits.append(f'TI {cur_ti}->{ti}')
        if cond and col(r, COND) != cond:
            data.append({'range': f"'Lease Comps'!{COND}{i}", 'values': [[cond]]}); bits.append(f'cond->{cond}')
        if dlv and str(col(r, DLV)).strip() != dlv:
            data.append({'range': f"'Lease Comps'!{DLV}{i}", 'values': [[dlv]]}); bits.append(f'delivery->{dlv}')
        existing = str(col(r, NOTE)).strip()
        if note not in existing:
            data.append({'range': f"'Lease Comps'!{NOTE}{i}",
                         'values': [[(existing + ' | ' if existing else '') + note]]})
        (applied if bits else skipped).append((cid, '; '.join(bits) or 'already current'))
    elif cur_ti == OLD_BENCHMARK and str(col(r, DLV)).strip() == 'LL Turnkey':
        data.append({'range': f"'Lease Comps'!{TI}{i}", 'values': [[TURNKEY_BENCHMARK]]})
        turnkey.append(cid)

if not data:
    print('nothing to apply — every answer is already in the sheet')
else:
    values_batch(s, data)
    print(f'{len(data)} cells written')
    for cid, what in applied:
        print(f'  {cid}  {what}')
    if skipped:
        print(f'  ({len(skipped)} already current)')
    if turnkey:
        print(f'\n  turnkey benchmark ${OLD_BENCHMARK} -> ${TURNKEY_BENCHMARK}: {", ".join(turnkey)}')
    changelog(s, 'TI ANSWERS',
              f'Applied JD\'s per-comp TI answers to {len(applied)} comps that carried $0 against a '
              'Custom TIA / LL Turnkey / blank delivery condition, with his figure recorded in Notes. '
              'Condition and delivery corrected where he identified a prebuilt or a turnkey. '
              'LC-0020 (Clay) held back for Floor Detail — its floors differ.', len(applied))
    if turnkey:
        changelog(s, 'TURNKEY BENCHMARK',
                  f'Normalised the LL Turnkey TI benchmark from ${OLD_BENCHMARK} to '
                  f'${TURNKEY_BENCHMARK}/SF on {len(turnkey)} comps per JD ({", ".join(turnkey)}). '
                  'LC-0099 (Rogo, $155) left alone as a specific negotiated figure.', len(turnkey))

# --- company rename, keeping the as-signed name as a Reference variant
cid, old, new = RENAME
co = get_values(s, 'Companies!A2:B200', render='FORMATTED_VALUE')
for i, r in enumerate(co, 2):
    if r and r[0] == cid and r[1] != new:
        values_batch(s, [{'range': f'Companies!B{i}', 'values': [[new]]}])
        vm = get_values(s, 'Reference!J2:K20', render='FORMATTED_VALUE')
        have = {r[0] for r in vm if r}
        if old not in have:
            nxt = 2 + len([r for r in vm if r and r[0]])
            values_batch(s, [{'range': f'Reference!J{nxt}:K{nxt}', 'values': [[old, new]]}])
        changelog(s, 'COMPANY RENAME', f'{cid} canonical name "{old}" -> "{new}" per JD; "{old}" kept '
                  'in Reference!VariantMap so the as-signed tenant name still resolves.', 1)
        print(f'\nCompanies {cid}: "{old}" -> "{new}"; variant mapping added')
        break
else:
    print(f'\nCompanies {cid}: already "{new}"')

summary, fails = qa_status(s)
print('\nQA:', summary, '| failing:', fails or 'none')
