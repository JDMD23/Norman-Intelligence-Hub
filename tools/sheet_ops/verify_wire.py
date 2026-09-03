"""Post-migration gate: the wired funding columns must reproduce the audited values.

Compares the wire (V/W/X latest round) per comp against the pre-migration snapshot
(the 2026-08/09 audited values), backfills rounds that Funding Rounds is missing so the
wire becomes correct at its source, then re-verifies. Also validates computed economics
(Y1, flat-tranche PGR, NER) against the verified Python reference.

Classification of a wire-vs-audit difference:
  * wire OLDER than audit, different round      -> backfill the audited round (this script)
  * wire OLDER, same type + amount, date differs -> same round, date conflict: REVIEW (no write)
  * wire NEWER than audit                        -> Funding Rounds knows more; wire wins
  * same month, label differs (e.g. Series F vs
    Late Stage Venture)                          -> vocabulary difference, INFO
  * same month, amount differs                   -> REVIEW item (reported, not auto-fixed)

Exit code is non-zero unless the gate passes. `--dry-run` prints the plan without writing.
"""
import json
import os
import re
import sys

from common import session, get_values, changelog, qa_status, SID, named_ranges

DRY = '--dry-run' in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
snap = json.load(open(os.path.join(HERE, 'data/pre_migration_funding.json')))

s = session()
hdr_check = get_values(s, "'Lease Comps'!T1:V1", render='FORMATTED_VALUE')[0]
assert hdr_check[0] == 'Comp Source', 'v4 layout not present — run migrate_structure.py first'

MON = {m: i for i, m in enumerate(
    ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
     'september', 'october', 'november', 'december'], 1)}


def col(row, letter):
    idx = 0
    for ch in letter:
        idx = idx * 26 + ord(ch) - 64
    idx -= 1
    return row[idx] if idx < len(row) and row[idx] != '' else None


def datekey(v):
    """'2026-05-09' or 'May 2026' -> '2026-05'; anything else -> None."""
    v = str(v or '').strip()
    m = re.match(r'(\d{4})-(\d{2})', v)
    if m:
        return m.group(0)
    m = re.match(r'([A-Za-z]+)\s+(\d{4})$', v)
    if m and m.group(1).lower() in MON:
        return f'{m.group(2)}-{MON[m.group(1).lower()]:02d}'
    return None


def num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def classify(rows):
    """Return (backfill{cid: audit}, review[], info[]) from current wire vs snapshot."""
    backfill, review, info = {}, [], []
    for row in rows:
        comp_id = col(row, 'A')
        if not comp_id or comp_id not in snap:
            continue
        want, cid = snap[comp_id], col(row, 'D')
        want_date, wire_date = datekey(want.get('lr_date')), datekey(col(row, 'V'))
        wire_type, wire_amt = col(row, 'W'), num(col(row, 'X'))
        want_type, want_amt = (want.get('lr_type') or '').strip(), num(want.get('lr_amt'))
        if not want_date:
            continue
        if wire_date != want_date:
            if wire_date and wire_date > want_date:
                info.append((comp_id, 'wire newer than audit — Funding Rounds wins',
                             f'{wire_type} {wire_date}', f'{want_type} {want_date}'))
            elif (wire_type and wire_type.strip() == want_type
                  and wire_amt is not None and want_amt is not None and abs(wire_amt - want_amt) <= 0.5):
                review.append((comp_id, 'same round, date conflict (not backfilled)',
                               f'{wire_type} {wire_date}', f'{want_type} {want_date}'))
            else:
                backfill.setdefault(cid, (comp_id, want))
            continue
        if want_type and wire_type and wire_type.strip() != want_type:
            info.append((comp_id, 'same month, label differs', wire_type, want_type))
        if want_amt is not None and wire_amt is not None and abs(want_amt - wire_amt) > 0.5:
            review.append((comp_id, 'same month, amount differs', wire_amt, want_amt))
    return backfill, review, info


def report(title, items):
    print(f'{title}: {len(items)}')
    for it in items:
        print('  ', *it)


# ---- pass 1: classify and backfill genuinely missing rounds
rows = get_values(s, "'Lease Comps'!A2:AP105")
backfill, review, info = classify(rows)

appended = []
if backfill:
    fr_rows = get_values(s, "'Funding Rounds'!A2:N3000")
    max_fr = max((int(r[0][3:]) for r in fr_rows if r and str(r[0]).startswith('FR-')), default=0)
    last_row = max((i + 2 for i, r in enumerate(fr_rows) if r and r[0] != ''), default=1)
    round_no = {}
    for r in fr_rows:
        if len(r) > 3 and r[0] and num(r[3]) is not None:
            round_no[r[1]] = max(round_no.get(r[1], 0), int(r[3]))
    conf = [r[0] for r in get_values(s, 'ConfidenceLevels', render='FORMATTED_VALUE') if r]
    high = next((c for c in conf if c.upper() == 'HIGH'), 'High')
    values, n = [], max_fr
    for cid, (comp_id, w) in sorted(backfill.items()):
        n += 1
        dk = datekey(w.get('lr_date'))
        amt = num(w.get('lr_amt'))
        rn = round_no.get(cid, 0) + 1
        # C (Company) and J (Months Since Prior) are formula columns pre-filled to row 3000:
        # None leaves them untouched. I (Cumulative After Round) stays blank = unknown.
        values.append([f'FR-{n:04d}', cid, None, rn, w.get('lr_type') or '', f'{dk}-01',
                       amt if amt is not None else '', '', '', None,
                       '2026-08/09 audit (dual-sourced press verification)', '', high,
                       'Backfilled during Lease Comps v4 migration so the wired latest-round '
                       f'lookup reproduces the audited value (was typed on {comp_id}). '
                       'Round date is month-level: day unknown, recorded as the 1st.'])
        appended.append((f'FR-{n:04d}', cid, rn, w.get('lr_type'), f'{dk}-01', amt))
    print(f'{"would backfill" if DRY else "backfilling"} {len(values)} Funding Rounds rows '
          f'at rows {last_row + 1}..{last_row + len(values)}:')
    for a in appended:
        print('  ', *a)
    if not DRY:
        end = last_row + len(values)
        nr = named_ranges(s)
        for name in ('FundingRounds_Dates', 'FundingRounds_Types', 'FundingRounds_Amounts',
                     'FundingRounds_CompanyIds', 'FundingRounds_IDs'):
            assert nr[name]['range']['endRowIndex'] >= end, f'{name} too short for backfill'
        r = s.put(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/'
                  f"'Funding Rounds'!A{last_row + 1}:N{end}?valueInputOption=USER_ENTERED",
                  json={'values': values})
        if r.status_code != 200:
            raise RuntimeError(f'Funding Rounds backfill failed: {r.json()}')
        changelog(s, 'FUNDING ROUNDS BACKFILL',
                  f'Added {len(values)} audited latest rounds missing from Funding Rounds so the '
                  f'Lease Comps v4 wire reproduces the 2026-08/09 audit. IDs FR-{max_fr + 1:04d}..'
                  f'FR-{n:04d}. Dates are month-level (day recorded as 1st).', len(values))
else:
    print('no Funding Rounds backfill needed')

# ---- pass 2: re-verify wire vs snapshot
if not DRY:
    rows = get_values(s, "'Lease Comps'!A2:AP105")
backfill2, review, info = classify(rows)
remaining = [] if DRY else list(backfill2.values())
report('latest-round wire: unresolved (older than audit)', remaining)
report('REVIEW items (need owner research, not auto-fixed)', review)
report('INFO (accepted differences)', info)

total_diffs = []
for row in rows:
    comp_id = col(row, 'A')
    if not comp_id or comp_id not in snap:
        continue
    ts, tg = num(snap[comp_id].get('total')), num(col(row, 'Y'))
    if ts is not None and tg is not None and abs(ts - tg) > max(5, ts * 0.05):
        total_diffs.append((comp_id, round(tg, 1), ts))
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
    y1, pgr, ner_v = col(row, 'AD'), col(row, 'AG'), col(row, 'AI')
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
if DRY:
    print('DRY RUN — nothing written')
    sys.exit(0)
if remaining or bad:
    print('VERIFICATION FAILED — fix mismatches above before styling/finalize')
    sys.exit(1)
rv = '; '.join(f'{c}: {why} ({a} vs audit {b})' for c, why, a, b in review) or 'none'
already_receipted = any(len(r) > 2 and r[2] == 'MIGRATION VERIFIED'
                        for r in get_values(s, 'Changelog!A1:E5000', render='FORMATTED_VALUE'))
if already_receipted and not appended:
    print(f'VERIFICATION PASSED — unchanged since last receipt ({len(review)} REVIEW items for owner)')
    sys.exit(0)
changelog(s, 'MIGRATION VERIFIED',
          f'Wired funding columns reproduce audited values ({len(appended)} Funding Rounds rows '
          f'backfilled; {len(info)} accepted label/newer-round differences). Economics validated '
          f'vs reference implementation ({ok} rows). REVIEW items: {rv}. '
          f'QA: {summary[3] if summary else "?"}.', len(appended))
print(f'VERIFICATION PASSED — receipt appended ({len(review)} REVIEW items for owner)')
