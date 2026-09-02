"""Post-migration gate: the wired funding columns must reproduce the audited values.

Compares wire (V/W/X latest round) per company against the pre-migration snapshot
(the 2026-08/09 audited values), backfills missing rounds into Funding Rounds so the
wire becomes correct at its source, then re-verifies. Also validates computed
economics (Y1, flat-tranche PGR, NER) against the verified Python reference.
"""
import json
import os
import re
import sys

from common import session, get_values, changelog, qa_status, SID

HERE = os.path.dirname(os.path.abspath(__file__))
snap = json.load(open(os.path.join(HERE, 'data/pre_migration_funding.json')))

s = session()
rows = get_values(s, "'Lease Comps'!A2:AO105")
hdr_check = get_values(s, "'Lease Comps'!T1:V1", render='FORMATTED_VALUE')[0]
assert hdr_check[0] == 'Comp Source', 'v4 layout not present — run migrate_structure.py first'


def col(row, letter):
    idx = 0
    for ch in letter:
        idx = idx * 26 + ord(ch) - 64
    idx -= 1
    return row[idx] if idx < len(row) and row[idx] != '' else None


def datekey(v):
    m = re.match(r'(\d{4})-(\d{2})', str(v or ''))
    return m.group(0) if m else None


# ---- pass 1: find companies whose wired latest round is older than the audited one
fr_rows = get_values(s, "'Funding Rounds'!A2:N3000")
max_fr = max((int(r[0][3:]) for r in fr_rows if r and str(r[0]).startswith('FR-')), default=0)
by_company_needed = {}
for row in rows:
    comp_id = col(row, 'A')
    if not comp_id:
        continue
    want = snap.get(comp_id)
    if not want or not want.get('lr_date'):
        continue
    cid = col(row, 'D')
    wire_date = datekey(col(row, 'V'))
    want_date = datekey(want['lr_date'])
    if want_date and wire_date != want_date and cid not in by_company_needed:
        if not wire_date or wire_date < want_date:
            by_company_needed[cid] = want

appended = []
if by_company_needed:
    values = []
    n = max_fr
    for cid, w in sorted(by_company_needed.items()):
        n += 1
        amt = w.get('lr_amt') if isinstance(w.get('lr_amt'), (int, float)) else ''
        values.append([f'FR-{n:04d}', cid, '', '', w.get('lr_type') or '', w.get('lr_date') or '',
                       amt, '', '', '', '2026-08/09 audit (dual-sourced press verification)', '',
                       'HIGH', 'Backfilled during Lease Comps v4 migration so wired latest-round '
                       'lookups reproduce the audited values.'])
        appended.append((f'FR-{n:04d}', cid, w.get('lr_type'), w.get('lr_date'), amt))
    r = s.post(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/'
               "'Funding Rounds'!A:N:append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS",
               json={'values': values})
    if r.status_code != 200:
        raise RuntimeError(f'Funding Rounds backfill failed: {r.json()}')
    print(f'backfilled {len(values)} Funding Rounds rows:')
    for a in appended:
        print('  ', *a)
else:
    print('no Funding Rounds backfill needed')

# ---- pass 2: re-verify wire vs snapshot
rows = get_values(s, "'Lease Comps'!A2:AO105")
mismatch, total_diffs = [], []
for row in rows:
    comp_id = col(row, 'A')
    if not comp_id or comp_id not in snap:
        continue
    want = snap[comp_id]
    want_date, wire_date = datekey(want.get('lr_date')), datekey(col(row, 'V'))
    if want_date and wire_date != want_date:
        mismatch.append((comp_id, 'lr_date', wire_date, want_date))
    wt, gt = want.get('lr_type'), col(row, 'W')
    if wt and gt and str(wt).strip() != str(gt).strip():
        mismatch.append((comp_id, 'lr_type', gt, wt))
    wa, ga = want.get('lr_amt'), col(row, 'X')
    if isinstance(wa, (int, float)) and isinstance(ga, (int, float)) and abs(wa - ga) > 0.5:
        mismatch.append((comp_id, 'lr_amt', ga, wa))
    ts, tg = want.get('total'), col(row, 'Y')
    if isinstance(ts, (int, float)) and isinstance(tg, (int, float)) and abs(ts - tg) > max(5, ts * 0.05):
        total_diffs.append((comp_id, round(tg, 1), ts))
print(f'latest-round wire check: {len(mismatch)} mismatches')
for m in mismatch[:20]:
    print('  MISMATCH', *m)
print(f'total-funding semantic diffs (tracked sum vs researched total, expected where prior '
      f'rounds are untracked): {len(total_diffs)} companies')
for t in sorted(total_diffs, key=lambda x: -abs(x[1] - x[2]))[:15]:
    print('  ', t[0], 'tracked', t[1], 'vs researched', t[2])

# ---- pass 3: economics vs Python reference
sys.path.insert(0, os.path.join(HERE, '..', '..', 'scripts'))
from ner import hub_baseline_ner  # noqa: E402

bad = ok = 0
for row in rows:
    if not col(row, 'C'):
        continue
    L, N, O, P, Q, R, S_ = (col(row, c) for c in 'LNOPQRS')
    y1, pgr, ner_v = col(row, 'AC'), col(row, 'AF'), col(row, 'AH')
    if None not in (L, O) and abs((y1 or 0) - L * O) > 1:
        bad += 1; print('  Y1 MISMATCH', col(row, 'A'), y1, 'vs', L * O)
    if None not in (L, N, O):
        T = round(N * 12)
        rz, r6 = O, (O if P is None else P)
        r11 = r6 if Q is None else Q
        want_pgr = L * (rz * min(T, 60) + r6 * min(max(T - 60, 0), 60) + r11 * max(T - 120, 0)) / 12
        if abs((pgr or 0) - want_pgr) > 1:
            bad += 1; print('  PGR MISMATCH', col(row, 'A'), pgr, 'vs', round(want_pgr))
    want_ner = hub_baseline_ner(N, O, P, Q, R or 0.0, S_) if None not in (N, O) else None
    if want_ner is not None and (ner_v is None or abs(ner_v - want_ner) > 0.01):
        bad += 1; print('  NER MISMATCH', col(row, 'A'), ner_v, 'vs', round(want_ner, 2))
    else:
        ok += 1
print(f'economics check: {ok} rows OK, {bad} mismatches')

summary, fails = qa_status(s)
print('QA:', summary, '| failing checks:', fails or 'none')
if not mismatch and not bad:
    changelog(s, 'MIGRATION VERIFIED',
              f'Wired funding columns reproduce audited values (0 mismatches; '
              f'{len(appended)} Funding Rounds rows backfilled). Economics validated vs '
              f'reference implementation ({ok} rows). QA: {summary[3] if summary else "?"}.',
              len(appended))
    print('VERIFICATION PASSED — receipt appended')
else:
    print('VERIFICATION INCOMPLETE — fix mismatches above before styling/finalize')
