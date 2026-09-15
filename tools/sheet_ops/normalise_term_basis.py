"""Make Term (Years) mean one thing: the stated, paying term.

JD 2026-09-15: free rent sits OUTSIDE the term unless the deal is a sublease. The NER formula
now derives the total lease length as Term + free months, so Term has to be the paying term
everywhere or the free months get counted twice.

Most of the book is already on that basis — 118 comps carry a whole-year term with free rent on
top, which is how a broker quotes a deal. Five do not: they were entered from surveys that
printed the TOTAL length, and each one nets to exactly ten or twelve years of paying rent once
the abatement comes out, which is what gives them away.

  LC-0104 Suno AI        135 mo - 15 free = 120   JD's own wording was "10 year, 15 month term"
  LC-0015 Sierra         136 mo - 16 free = 120   analysts model it as 76 + 60 = 136 total
  LC-0108 PayPal         139 mo - 19 free = 120   analysts model it as 79 + 60 = 139 total
  LC-0133 Warby Parker   139 mo - 19 free = 120   deck prints 11y 7m
  LC-0105 Anthropic      164 mo - 17 free = 147   analysts model it as 77 + 60 + 27 = 164 total

Deliberately NOT touched: LC-0119 (Snowflake, 136 mo with 12 free) nets to 124 months, which is
not a round paying term either way, so there is no evidence it holds a total rather than a
stated term. It stays as a paying term, the majority convention, and is flagged in the research
queue instead of being guessed at.

Subleases are untouched throughout — their abatement is carved out of the stated term.
"""
from common import session, get_values, values_batch, changelog, qa_status, headers

FIX = {
    'LC-0104': (10.0,   'JD: "10 year, 15 month term" — 120 months paying plus 15 abated'),
    'LC-0015': (10.0,   'analysts model 76 + 60 = 136 months total; 120 paying'),
    'LC-0108': (10.0,   'analysts model 79 + 60 = 139 months total; 120 paying'),
    'LC-0133': (10.0,   'deck prints 11y 7m = 139 months total; 120 paying'),
    'LC-0105': (12.25,  'analysts model 77 + 60 + 27 = 164 months total; 147 paying'),
}
NOTE = ('JD 9/15: Term (Years) restated as the PAYING term. Free rent sits outside the term, so '
        'the NER formula derives the total lease length as Term plus the abated months; this row '
        'previously held the total, which would have counted the abatement twice. {}. '
        'Total length is unchanged — only what the column means.')

s = session()
H = headers(s, 'Lease Comps')
rows = get_values(s, "'Lease Comps'!A2:AS1206", render='FORMATTED_VALUE')


def col(r, hdr):
    i = 0
    for ch in H[hdr]:
        i = i * 26 + ord(ch) - 64
    return str(r[i-1]) if i-1 < len(r) else ''


data, log = [], []
for i, r in enumerate(rows, 2):
    cid = col(r, 'Comp ID')
    if cid not in FIX:
        continue
    want, why = FIX[cid]
    cur = col(r, 'Term (Years)')
    free = float(col(r, 'Free Rent (months)') or 0)
    if abs(float(cur or 0) - want) > 1e-9:
        data.append({'range': f"'Lease Comps'!{H['Term (Years)']}{i}", 'values': [[want]]})
        log.append(f'   {cid} {col(r, "Tenant"):18} {cur}y -> {want}y  '
                   f'(total stays {round(want*12+free)} months)')
    note = NOTE.format(why)
    ex = col(r, 'Notes').strip()
    if 'Term (Years) restated as the PAYING term' not in ex:
        data.append({'range': f"'Lease Comps'!{H['Notes']}{i}",
                     'values': [[(ex + ' ' if ex else '') + note]]})

if not data:
    print('nothing to restate — all five already on the paying-term basis')
else:
    values_batch(s, data)
    print(f'{len(log)} terms restated:')
    for l in log:
        print(l)
    changelog(s, 'TERM BASIS',
              'Restated Term (Years) as the paying term on the five comps that held the total '
              'length, so the column means one thing everywhere now that free rent sits outside '
              'the term and the NER formula derives total = Term + abated months. Suno, Sierra, '
              'PayPal and Warby Parker each net to exactly 120 paying months; Anthropic to 147, '
              'matching the analysts\' 77 + 60 + 27. Total lease length is unchanged on all five. '
              'LC-0119 (Snowflake) deliberately left alone — it nets to 124 months, which is no '
              'rounder than its stated 136, so there is no evidence either way.', len(log))

summary, fails = qa_status(s)
print('\nQA:', summary, '| failing:', fails or 'none')
