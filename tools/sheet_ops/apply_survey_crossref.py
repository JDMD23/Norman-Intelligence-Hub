"""Reconcile the workbook against JD's >25,000 RSF survey (screenshot, 2026-09-03).

Five tenants appear both in the survey and the book, and every one differed. JD's calls:

  Rain AI (LC-0013)   same building, keep 130 Mercer Street; take the survey's TI of $130.
                      It had been $140 until the turnkey normalisation pushed it to $150 —
                      so at least one of those $140s was a real figure, not a placeholder.
  Legora              two separate deals. 836 Broadway (LC-0044) stays; add the 11 Madison one.
  Harvey AI           both floors are real but belong in ONE comp: LC-0052 absorbs LC-0053's
                      92,000 SF (floors 4 and 6, 184,663 SF total) and LC-0053 is removed.
                      Its full contents are in the Changelog receipt. LC-0053 is retired,
                      never reused, per the ID contract.
  Sierra (LC-0015)    trust the survey: 11-15 East 26th, 95,000 SF, 11y 4m, 16mo free, $190 TI,
                      and the company is Sierra Technologies (Sierra AI kept as a variant).
  Clay (LC-0020)      trust the survey: 15-year term and $145 TI. Its floors share one blended
                      schedule, so it needs no Floor Detail rows after all.

Idempotent: each edit is skipped when the sheet already holds the target value.
"""
from common import (session, get_values, values_batch, batch_update, changelog, qa_status,
                    headers, sheet_ids, SID)

s = session()
H = headers(s, 'Lease Comps')
lc_sheet = sheet_ids(s)['Lease Comps']


def col_of(header):
    return H[header]


def rows_now():
    return get_values(s, "'Lease Comps'!A2:AS300", render='FORMATTED_VALUE')


def find(comp_id):
    for i, r in enumerate(rows_now(), 2):
        if r and r[0] == comp_id:
            return i, r
    return None, None


def money(v):
    try:
        return float(str(v).replace('$', '').replace(',', ''))
    except (ValueError, AttributeError):
        return None


data, notes = [], []

# --- 1. Rain AI: survey TI
i, r = find('LC-0013')
if money(r[18]) != 130:
    data.append({'range': f"'Lease Comps'!{col_of('TI $/SF')}{i}", 'values': [[130]]})
    notes.append('LC-0013 Rain AI: TI -> $130 (JD survey; same building, address stays 130 Mercer Street)')

# --- 2. Sierra: survey figures + rename
i, r = find('LC-0015')
for header, val in [('Tenant', 'Sierra Technologies'), ('Address', '11-15 East 26th Street'),
                    ('RSF', 95000), ('Term (Years)', 11.33), ('Free Rent (months)', 16),
                    ('TI $/SF', 190)]:
    data.append({'range': f"'Lease Comps'!{col_of(header)}{i}", 'values': [[val]]})
notes.append('LC-0015 Sierra: 11-15 East 26th Street, 95,000 SF, 11y 4m, 16mo free, TI $190 (JD survey)')

# --- 3. Clay: survey term + TI
i, r = find('LC-0020')
data.append({'range': f"'Lease Comps'!{col_of('Term (Years)')}{i}", 'values': [[15.0]]})
data.append({'range': f"'Lease Comps'!{col_of('TI $/SF')}{i}", 'values': [[145]]})
notes.append('LC-0020 Clay: term -> 15 yrs, TI -> $145 (JD survey). One blended schedule across '
             'E14/P15/E16, so no Floor Detail rows needed.')

# --- 4. Harvey: merge LC-0053 into LC-0052
i52, r52 = find('LC-0052')
i53, r53 = find('LC-0053')
merged_note = ''
if r53 is not None:
    merged_note = ' | '.join(f'{h}={v}' for h, v in zip(
        ['id','date','tenant','company','address','submarket','class','floors','condition','deal',
         'delivery','rsf','seats','term','p1','p2','p3','free','ti'], r53[:19]))
    data.append({'range': f"'Lease Comps'!{col_of('RSF')}{i52}", 'values': [[184663]]})
    data.append({'range': f"'Lease Comps'!{col_of('Floor(s)')}{i52}", 'values': [['E4, E6']]})
    notes.append('LC-0052 Harvey AI: absorbed LC-0053 — floors E4 + E6, 184,663 SF (JD: both real, one comp)')

values_batch(s, data)
print(f'{len(data)} cells written')
for n in notes:
    print('  ' + n)

if r53 is not None:
    batch_update(s, [{'deleteDimension': {'range': {
        'sheetId': lc_sheet, 'dimension': 'ROWS', 'startIndex': i53 - 1, 'endIndex': i53}}}])
    print(f'  LC-0053 row deleted (row {i53})')
    changelog(s, 'COMP MERGED', 'LC-0053 merged into LC-0052 per JD — both Harvey AI floors at '
              '1 Madison Avenue are real but belong in one comp (E4 + E6, 184,663 SF). LC-0053 is '
              'retired and never reused. Deleted row contents: ' + merged_note, 1)

# --- 5. Companies: Sierra AI -> Sierra Technologies, keeping the variant
co = get_values(s, 'Companies!A2:B200', render='FORMATTED_VALUE')
for i, r in enumerate(co, 2):
    if r and r[0] == 'CO-0077' and r[1] != 'Sierra Technologies':
        values_batch(s, [{'range': f'Companies!B{i}', 'values': [['Sierra Technologies']]}])
        vm = get_values(s, 'Reference!J2:K20', render='FORMATTED_VALUE')
        if 'Sierra AI' not in {x[0] for x in vm if x}:
            nxt = 2 + len([x for x in vm if x and x[0]])
            values_batch(s, [{'range': f'Reference!J{nxt}:K{nxt}',
                              'values': [['Sierra AI', 'Sierra Technologies']]}])
        changelog(s, 'COMPANY RENAME', 'CO-0077 "Sierra AI" -> "Sierra Technologies" per JD survey; '
                  '"Sierra AI" kept in Reference!VariantMap so LC-0063 still resolves.', 1)
        print('  Companies CO-0077: "Sierra AI" -> "Sierra Technologies"; variant mapping added')
        break

changelog(s, 'SURVEY CROSS-REFERENCE', 'Reconciled the book against JD\'s >25,000 RSF survey. '
          + ' '.join(notes), len(notes))
summary, fails = qa_status(s)
print('\nQA:', summary, '| failing:', fails or 'none')
