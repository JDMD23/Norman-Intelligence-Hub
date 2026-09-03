"""Copy pass: the words a reader sees, written for people (presentation only).

Start Here becomes a human landing page (title, one-line purpose, plain-English principles,
live health). QA Harness descriptions lose the double-hyphen typewriter dashes. Tab names and
every formula stay as they are — the Apps Script auto-ID trigger addresses tabs by name.
"""
from common import session, get_values, values_batch, changelog

s = session()

START_HERE = [
    ('A1', 'Norman AI Intelligence Hub'),
    ('A2', 'The market-intelligence brain behind NormansHub: signed Manhattan office leases, the companies '
           'behind them and their funding, wired together and QA-checked on every change.'),
    ('A4', 'Principle'), ('B4', 'What it means'),
    ('A5', 'Source of truth'), ('B5', 'Lease Comps, Companies and Funding Rounds are the only tabs you type into. Everything else is computed from them.'),
    ('A6', 'Live math'), ('B6', 'Every economic figure is a live formula. Enter RSF, rent and concessions and Year 1 rent, projected gross, NER and cost per seat update instantly.'),
    ('A7', 'Unknown = blank'), ('B7', 'Never type 0 for an unknown value. Blank propagates correctly; 0 corrupts every average.'),
    ('A8', 'IDs'), ('B8', 'Assigned automatically the moment you type a tenant or company name. Leave the ID columns alone.'),
    ('A9', 'Vocabulary'), ('B9', 'Dropdown fields are fed from the Reference tab. New submarket, building class or round type? Add it there first.'),
    ('A10', 'Colour'), ('B10', 'White columns are inputs. Celadon columns are wired from another tab. Green columns are computed. Change inputs, never results.'),
    ('A11', 'Status'), ('B11', 'Every record status is computed: Ready, Needs review or Missing inputs. Nothing here claims to be ready as static text.'),
    ('A12', 'Receipts'), ('B12', 'Every automated change leaves a row in the Changelog: timestamp, actor, action, detail.'),
    ('A14', 'Live health'),
    ('A15', 'QA status'), ('A16', 'QA detail'), ('A17', 'Signed leases'), ('A18', 'Companies'),
    ('A19', 'Funding rounds'), ('A20', 'Next comp ID'), ('A21', 'Next company ID'), ('A22', 'Next round ID'),
]
data = [{'range': f"'Start Here'!{a}", 'values': [[v]]} for a, v in START_HERE]

# QA descriptions: " -- " -> " – " (typed text in column C only; formulas untouched)
qa = get_values(s, "'QA Harness'!C1:C40", render='FORMULA')
fixed = 0
for i, r in enumerate(qa, 1):
    if r and isinstance(r[0], str) and not r[0].startswith('=') and ' -- ' in r[0]:
        data.append({'range': f"'QA Harness'!C{i}", 'values': [[r[0].replace(' -- ', ' – ')]]})
        fixed += 1
values_batch(s, data)
print(f'copy pass: Start Here rewritten ({len(START_HERE)} cells); {fixed} QA descriptions re-punctuated')
changelog(s, 'COPY', 'Start Here rewritten for people (purpose line, plain-English principles, live health labels); '
          f'{fixed} QA descriptions switched from " -- " to an en dash. No tab renamed, no formula changed.', '')
