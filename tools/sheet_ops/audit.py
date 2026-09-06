"""Read-only consistency audit of the workbook. Writes nothing, ever.

The QA Harness tab checks that the workbook is structurally sound — no formula errors, no
duplicate or dangling IDs. It cannot check whether the *data* is coherent: a submarket entered
two ways, a building filed under two submarkets, a lease asserting flat rent for eleven years,
a turnkey comp still carrying the benchmark estimate. Those were all found by hand on
2026-09-06 and all of them were real.

The harder half is that most of those findings have a legitimate answer of "yes, and that is
correct". A blank cell cannot say whether nobody has answered the question or whether JD
answered it and the answer was "unknown". So every finding here is cross-referenced against
schema/decisions.json, and anything settled is reported as settled rather than raised again.
That file is the record; this script is the reader.

Run it before starting work and before finishing:

    python3 tools/sheet_ops/audit.py            # open findings, grouped by severity
    python3 tools/sheet_ops/audit.py --all      # also list what has been settled and why

Exit code is 1 if anything CRITICAL or HIGH is open, else 0.
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

from common import session, get_values, headers, qa_status

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from ner import hub_baseline_ner  # noqa: E402

DECISIONS = os.environ.get(  # override to test that the checks still fail without the record
    'HUB_DECISIONS',
    os.path.join(os.path.dirname(__file__), '..', '..', 'schema', 'decisions.json'))
SHOW_ALL = '--all' in sys.argv

# header -> Reference column holding its vocabulary
ENUMS = {'Submarket': 'A', 'Building Class': 'B', 'Deal Type': 'C',
         'Condition': 'D', 'Delivery Condition': 'E'}
TEXT_COLS = ['Tenant', 'Address', 'Submarket', 'Building Class', 'Floor(s)',
             'Condition', 'Deal Type', 'Delivery Condition', 'Notes']
BANDS = [('RSF', 1_000, 500_000), ('Term (Years)', 1, 25),
         ('Rent P1 ($/RSF, mo 1-60)', 30, 250), ('Free Rent (months)', 0, 30),
         ('TI $/SF', 0, 300), ('Seats', 5, 3_000)]

findings = []       # (severity, check, headline, [detail lines])


def add(sev, check, headline, detail=()):
    findings.append((sev, check, headline, list(detail)))


def num(v):
    if isinstance(v, (int, float)):
        return float(v)
    v = str(v).strip()
    if not v:
        return None
    try:
        return float(v.replace('$', '').replace(',', '').replace('%', ''))
    except ValueError:
        return None


def norm_address(a):
    """Fold an address to a comparison key: casing, abbreviations, spelled-out numbers."""
    a = a.lower().strip()
    for pat, rep in ((r'\b(avenue|ave\.?)\b', 'ave'), (r'\b(street|st\.?)\b', 'st'),
                     (r'\b(south|s\.?)\b', 's'), (r'\b(west|w\.?)\b', 'w'),
                     (r'\b(east|e\.?)\b', 'e')):
        a = re.sub(pat, rep, a)
    for word, digit in zip(('one two three four five six seven eight nine ten eleven twelve'
                            .split()), '1 2 3 4 5 6 7 8 9 10 11 12'.split()):
        a = re.sub(rf'\b{word}\b', digit, a)
    return re.sub(r'[^a-z0-9]', '', a)


def main():
    dec = json.load(open(DECISIONS))
    settled = {}
    for d in dec['settled']:
        settled.setdefault(d['check'], set()).update(d.get('comps', []) or d.get('values', []))
    deliberate = {}
    for o in dec['open']:
        deliberate.setdefault(o['check'], set()).update(o['comps'])

    def unsettled(check, items):
        """Drop anything already decided, and anything held open on purpose."""
        return sorted(set(items) - settled.get(check, set()) - deliberate.get(check, set()))

    s = session()
    H = headers(s, 'Lease Comps')
    rows = get_values(s, "'Lease Comps'!A2:AS1206", render='UNFORMATTED_VALUE')

    def col(r, hdr):
        i = 0
        for ch in H[hdr]:
            i = i * 26 + ord(ch) - 64
        return r[i-1] if i-1 < len(r) else ''

    def txt(r, hdr):
        return str(col(r, hdr)).strip()

    comps = [r for r in rows if txt(r, 'Comp ID')]
    cid = {id(r): txt(r, 'Comp ID') for r in comps}
    ref = get_values(s, 'Reference!A2:H60', render='FORMATTED_VALUE')

    def vocab(letter):
        i = ord(letter) - 65
        return {r[i] for r in ref if len(r) > i and r[i]}

    # ---- 1. the NER model still agrees with the sheet -----------------------------------
    drift = []
    for r in comps:
        model = hub_baseline_ner(num(col(r, 'Term (Years)')), num(col(r, 'Rent P1 ($/RSF, mo 1-60)')),
                                 num(col(r, 'Rent P2 ($/RSF, mo 61-120)')),
                                 num(col(r, 'Rent P3 ($/RSF, mo 121+)')),
                                 num(col(r, 'Free Rent (months)')) or 0, num(col(r, 'TI $/SF')))
        sheet = num(col(r, 'NER Annuity ($/RSF/Yr) @ 6%'))
        if model is None and sheet is None:
            continue
        if model is None or sheet is None or abs(sheet - model) > 0.02:
            drift.append(f'{cid[id(r)]}  sheet {sheet} vs model {model}')
    if drift:
        add('CRITICAL', 'ner_model_agreement',
            f'{len(drift)} comps where the sheet NER disagrees with scripts/ner.py', drift)

    # ---- 2. vocabulary -------------------------------------------------------------------
    for hdr, rc in ENUMS.items():
        used = Counter(txt(r, hdr) for r in comps)
        allowed = vocab(rc)
        orphans = {k: v for k, v in used.items() if k and k not in allowed}
        if orphans:
            add('HIGH', 'enum_orphan', f'{hdr}: value in use that Reference does not allow',
                [f'{k!r} on {v} comps' for k, v in orphans.items()])
        blanks = unsettled('blank_enum', [cid[id(r)] for r in comps if not txt(r, hdr)])
        if blanks:
            add('MEDIUM', 'blank_enum', f'{hdr} blank on {len(blanks)} comps',
                [', '.join(blanks)])
        unused = unsettled('enum_unused', allowed - set(used))
        if unused:
            add('INFO', 'enum_unused', f'{hdr}: {len(unused)} Reference values with no comps',
                [', '.join(sorted(unused))])

    # ---- 3. text dirt --------------------------------------------------------------------
    dirt = [f'{cid[id(r)]}  {h}: {txt(r, h)!r}' for r in comps for h in TEXT_COLS
            if str(col(r, h)) and (str(col(r, h)) != str(col(r, h)).strip()
                                   or '  ' in str(col(r, h)))]
    if dirt:
        add('MEDIUM', 'text_dirt', f'{len(dirt)} fields with stray whitespace', dirt)

    # ---- 4. the same building written or filed two ways ----------------------------------
    by_key = defaultdict(set)
    subs_by_key = defaultdict(set)
    for r in comps:
        k = norm_address(txt(r, 'Address'))
        by_key[k].add(txt(r, 'Address'))
        subs_by_key[k].add(txt(r, 'Submarket'))
    spell = [f'{sorted(v)}' for v in by_key.values() if len(v) > 1]
    if spell:
        add('HIGH', 'address_variant', f'{len(spell)} buildings written more than one way', spell)
    conflict = [f'{sorted(by_key[k])[0]}: {sorted(v)}' for k, v in subs_by_key.items() if len(v) > 1]
    if unsettled('building_submarket_conflict', conflict):
        add('HIGH', 'building_submarket_conflict',
            f'{len(conflict)} buildings filed under more than one submarket', conflict)

    # ---- 5. duplicate transactions -------------------------------------------------------
    dupes = defaultdict(list)
    for r in comps:
        dupes[(txt(r, 'Tenant').lower(), norm_address(txt(r, 'Address')),
               txt(r, 'Date Signed'))].append(cid[id(r)])
    hits = [v for v in dupes.values() if len(v) > 1]
    flat_hits = unsettled('duplicate_comps', [c for v in hits for c in v])
    if flat_hits:
        add('CRITICAL', 'duplicate_comps',
            'same tenant, building and date recorded more than once',
            [', '.join(v) for v in hits if set(v) & set(flat_hits)])

    # ---- 6. referential integrity --------------------------------------------------------
    co = get_values(s, 'Companies!A2:B300', render='FORMATTED_VALUE')
    coids = {r[0] for r in co if r and r[0]}
    broken = [cid[id(r)] for r in comps if txt(r, 'Company ID') and txt(r, 'Company ID') not in coids]
    if broken:
        add('CRITICAL', 'fk_company', f'{len(broken)} comps point at a company that does not exist',
            [', '.join(broken)])
    orphan_co = sorted(coids - {txt(r, 'Company ID') for r in comps})
    if orphan_co:
        add('INFO', 'company_no_comps', f'{len(orphan_co)} companies with no comp',
            [', '.join(orphan_co)])

    # ---- 7. numeric sanity ---------------------------------------------------------------
    for hdr, lo, hi in BANDS:
        out = [f'{cid[id(r)]}  {hdr} = {num(col(r, hdr))}' for r in comps
               if num(col(r, hdr)) is not None and not lo <= num(col(r, hdr)) <= hi]
        if out:
            add('HIGH', 'numeric_outlier', f'{hdr} outside [{lo:,}, {hi:,}]', out)

    # ---- 8. semantic gaps, each one answerable ------------------------------------------
    flat = unsettled('long_lease_flat_rent',
                     [cid[id(r)] for r in comps if (num(col(r, 'Term (Years)')) or 0) > 5
                      and num(col(r, 'Rent P2 ($/RSF, mo 61-120)')) is None])
    if flat:
        add('HIGH', 'long_lease_flat_rent',
            f'{len(flat)} leases over five years assert flat rent for the whole term',
            [', '.join(flat)])

    seatless = unsettled('missing_seats', [cid[id(r)] for r in comps
                                           if num(col(r, 'Seats')) is None])
    if seatless:
        rsf = sum(num(col(r, 'RSF')) or 0 for r in comps if cid[id(r)] in seatless)
        add('MEDIUM', 'missing_seats',
            f'{len(seatless)} comps have no seat count ({rsf:,.0f} RSF)', [', '.join(seatless)])

    bench = dec['conventions']['turnkey_benchmark_psf']
    on_bench = unsettled('turnkey_on_benchmark',
                         [cid[id(r)] for r in comps if txt(r, 'Delivery Condition') == 'LL Turnkey'
                          and num(col(r, 'TI $/SF')) == bench])
    if on_bench:
        add('HIGH', 'turnkey_on_benchmark',
            f'{len(on_bench)} turnkey comps carry the ${bench} benchmark rather than a real figure',
            [', '.join(on_bench)])

    no_ti = unsettled('missing_ti', [cid[id(r)] for r in comps if num(col(r, 'TI $/SF')) is None])
    if no_ti:
        add('HIGH', 'missing_ti', f'{len(no_ti)} comps have no TI, so no NER is computed',
            [', '.join(no_ti)])

    bad_zero = unsettled('ti_zero', [cid[id(r)] for r in comps if num(col(r, 'TI $/SF')) == 0
                                     and txt(r, 'Delivery Condition') != 'As-Is'])
    if bad_zero:
        add('CRITICAL', 'ti_zero',
            f'{len(bad_zero)} comps carry TI $0 against a contributing delivery condition — '
            'a Custom TIA or LL Turnkey deal cannot have a zero allowance', [', '.join(bad_zero)])

    # ---- 9. building-level TI conventions ------------------------------------------------
    for rule in dec['conventions']['building_ti']:
        key = norm_address(rule['address'])
        off = [f"{cid[id(r)]}  TI ${num(col(r, 'TI $/SF')):.0f}, rule says ${rule['ti_psf']}"
               for r in comps
               if norm_address(txt(r, 'Address')) == key
               and txt(r, 'Delivery Condition') == 'LL Turnkey'
               and (rule['applies_to_condition'] is None
                    or txt(r, 'Condition') == rule['applies_to_condition'])
               and num(col(r, 'TI $/SF')) not in (None, rule['ti_psf'])]
        if off:
            add('HIGH', 'building_ti_convention',
                f"{rule['address']} turnkey comps that depart from the ${rule['ti_psf']} rule", off)

    # ---- report --------------------------------------------------------------------------
    print(f'Audit — {len(comps)} comps, {len(coids)} companies')
    qa, fails = qa_status(s)
    print(f'QA Harness: {qa[3] if len(qa) > 3 else qa}  |  failing: {fails or "none"}\n')

    order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'INFO': 3}
    findings.sort(key=lambda f: order[f[0]])
    if not findings:
        print('No open findings. Every check is clean or settled in schema/decisions.json.')
    for sev, check, headline, detail in findings:
        print(f'[{sev}] {check}: {headline}')
        for d in detail[:8]:
            print(f'    {d}')
        if len(detail) > 8:
            print(f'    … and {len(detail) - 8} more')
        print()

    n_settled = sum(len(d.get('comps', []) or d.get('values', [])) for d in dec['settled'])
    print(f'Settled and therefore not raised: {n_settled} items across '
          f'{len(dec["settled"])} decisions (schema/decisions.json, updated {dec["updated"]}).')
    for o in dec['open']:
        print(f'  held open on purpose — {o["check"]}: {", ".join(o["comps"])}')
    if SHOW_ALL:
        print()
        for d in dec['settled']:
            items = d.get('comps') or d.get('values') or []   # a ruling can carry no comp ids
            print(f'  {d["check"]} ({d["decided"]}, {d["by"]}, {len(items)} items)')
            print(f'      {d["ruling"]}')

    blocking = [f for f in findings if f[0] in ('CRITICAL', 'HIGH')]
    if blocking:
        print(f'\n{len(blocking)} finding(s) at CRITICAL or HIGH.')
    return 1 if blocking else 0


if __name__ == '__main__':
    raise SystemExit(main())
