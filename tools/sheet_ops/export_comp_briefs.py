"""Export every comp as a plain-language brief, for handing to an analyst.

The format is JD's: tenant, address, floors in words, RSF, the rent schedule, the term, free
rent, TIA. Nothing is computed here and nothing is inferred — every line is read straight off
Lease Comps, so the brief and the workbook cannot disagree.

Three renderings are deliberate:

  Term is stated in full, with the month count in parentheses. A brief that says "10 year"
  when the lease runs 135 months hands the analyst the wrong NER input, and the difference is
  invisible once it is out of the workbook.

  The rent schedule is derived from the three flat tranches (P1 months 1-60, P2 61-120,
  P3 121+, blank carrying the prior rate) and adjacent tranches at the same rate are merged,
  so a genuinely flat lease reads as flat rather than as three identical lines.

  Blank and zero stay distinct, as they are in the book. "TIA unknown" and "$0 TIA — as-is"
  are different facts, and so are "free rent unknown" and "no free rent".

Usage:  python3 tools/sheet_ops/export_comp_briefs.py [outfile.md]
"""
import re
import sys

from common import session, get_values, headers

ORD = {1: 'st', 2: 'nd', 3: 'rd', 21: 'st', 22: 'nd', 23: 'rd', 31: 'st'}


def ordinal(n):
    return f'{n}{ORD.get(n, "th")}'


def money(v):
    """$92.00 -> '$92'; $92.50 -> '$92.50'."""
    return f'${v:,.0f}' if float(v).is_integer() else f'${v:,.2f}'


def floors(raw):
    """'E2-E3' -> 'Entire 2nd and 3rd floors'. Falls back to the raw string if unparseable."""
    raw = str(raw).strip()
    if not raw:
        return None
    parts, ok = [], True
    for chunk in re.split(r'\s*[,+]\s*', raw):
        chunk = chunk.strip()
        if not chunk:
            continue
        m = re.fullmatch(r'([EP])\s*(\d+)\s*-\s*(?:[EP])?\s*(\d+)', chunk, re.I)
        if m:
            kind, a, b = m.group(1).upper(), int(m.group(2)), int(m.group(3))
            word = 'Entire' if kind == 'E' else 'Partial'
            nums = [ordinal(n) for n in range(a, b + 1)]
            joined = ' and '.join(nums) if len(nums) == 2 else \
                     f'{nums[0]} through {nums[-1]}' if len(nums) > 2 else nums[0]
            parts.append((word, joined, len(nums) > 1))
            continue
        m = re.fullmatch(r'([EP])\s*(\d+)', chunk, re.I)
        if m:
            kind, n = m.group(1).upper(), int(m.group(2))
            parts.append(('Entire' if kind == 'E' else 'Partial', ordinal(n), False))
            continue
        if re.fullmatch(r'[EP]?\s*PH', chunk, re.I):
            parts.append(('Entire' if chunk.upper().startswith('E') else '', 'penthouse', False))
            continue
        if re.fullmatch(r'\d+', chunk):          # a bare number continues the prior kind
            parts.append((parts[-1][0] if parts else 'Entire', ordinal(int(chunk)), False))
            continue
        ok = False
        break
    if not ok or not parts:
        return raw
    # collapse a run of same-kind single floors into one phrase
    out, i = [], 0
    while i < len(parts):
        kind, label, plural = parts[i]
        same = [label]
        j = i + 1
        while j < len(parts) and parts[j][0] == kind and not parts[j][2] and not plural:
            same.append(parts[j][1]); j += 1
        if len(same) > 1:
            phrase = ' and '.join(same) if len(same) == 2 else \
                     ', '.join(same[:-1]) + ' and ' + same[-1]
            out.append(f'{kind} {phrase} floors'.strip())
        else:
            noun = 'floors' if plural else 'floor'
            out.append(f'{kind} {label} {noun}'.strip() if label != 'penthouse'
                       else f'{kind} penthouse'.strip())
        i = j
    s = ', '.join(out)
    return s[0].upper() + s[1:]


def rent_schedule(term_months, p1, p2, p3):
    """Merge the three flat tranches into the fewest true statements."""
    r2 = p1 if p2 is None else p2
    r3 = r2 if p3 is None else p3
    segs = []
    for rate, lo, hi in ((p1, 1, 60), (r2, 61, 120), (r3, 121, term_months)):
        hi = min(hi, term_months)
        if lo <= hi:
            if segs and segs[-1][0] == rate:
                segs[-1][2] = hi
            else:
                segs.append([rate, lo, hi])
    if len(segs) == 1:
        return f'{money(segs[0][0])}/SF flat for the full term'
    bits = []
    for rate, lo, hi in segs:
        y0 = (lo - 1) // 12 + 1
        bits.append(f'{money(rate)}/SF years {y0}+' if hi == term_months
                    else f'{money(rate)}/SF years {y0}-{hi // 12}')
    return ', '.join(bits)


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else 'comp_briefs.md'
    s = session()
    H = headers(s, 'Lease Comps')
    rows = get_values(s, "'Lease Comps'!A2:AS1206", render='UNFORMATTED_VALUE')
    fmt = get_values(s, "'Lease Comps'!A2:AS1206", render='FORMATTED_VALUE')

    def col(r, hdr):
        i = 0
        for ch in H[hdr]:
            i = i * 26 + ord(ch) - 64
        return r[i-1] if i-1 < len(r) else ''

    def num(r, hdr):
        v = col(r, hdr)
        if isinstance(v, (int, float)):
            return float(v)
        v = str(v).strip()
        if not v:
            return None
        try:
            return float(v.replace('$', '').replace(',', ''))
        except ValueError:
            return None

    briefs, skipped = [], []
    for r, fr in zip(rows, fmt):
        cid = str(col(r, 'Comp ID')).strip()
        if not cid:
            continue
        term = num(r, 'Term (Years)')
        p1 = num(r, 'Rent P1 ($/RSF, mo 1-60)')
        rsf = num(r, 'RSF')
        if term is None or p1 is None or rsf is None:
            skipped.append(cid)
            continue
        tm = round(term * 12)
        yrs, mos = divmod(tm, 12)
        term_line = (f'{yrs} year term ({tm} months)' if mos == 0
                     else f'{yrs} year, {mos} month term ({tm} months)')

        free = num(r, 'Free Rent (months)')
        free_line = ('Free rent unknown' if free is None
                     else 'No free rent' if free == 0
                     else f'{free:.0f} months free' if float(free).is_integer()
                     else f'{free} months free')

        ti = num(r, 'TI $/SF')
        ti_line = ('TIA unknown' if ti is None
                   else '$0 TIA — as-is, no allowance' if ti == 0
                   else f'{money(ti)}/SF TIA')

        deal = str(col(r, 'Deal Type')).strip()
        date = str(next((x for x in [col(fr, 'Date Signed')] if x), '')).strip()
        head = f'{cid} · Signed {date}' + (f' · {deal}' if deal and deal != 'New Lease' else '')

        lines = [head, str(col(r, 'Tenant')).strip(), str(col(r, 'Address')).strip()]
        fl = floors(col(r, 'Floor(s)'))
        if fl:
            lines.append(fl)
        lines += [f'{rsf:,.0f} RSF',
                  rent_schedule(tm, p1, num(r, 'Rent P2 ($/RSF, mo 61-120)'),
                                num(r, 'Rent P3 ($/RSF, mo 121+)')),
                  term_line, free_line, ti_line]
        briefs.append('\n'.join(lines))

    body = (f'# Lease comp briefs\n\n'
            f'{len(briefs)} comps, exported from the Norman Intelligence Hub workbook, newest '
            f'first. Every line is read directly off Lease Comps — nothing here is computed or '
            f'inferred.\n\n'
            f'Term is stated in full with the month count, because that is the NER input. '
            f'"TIA unknown" and "$0 TIA" are different facts and so are "free rent unknown" and '
            f'"no free rent" — blanks mean nobody knows, not zero.\n\n---\n\n'
            + '\n\n---\n\n'.join(briefs) + '\n')
    open(out_path, 'w').write(body)
    print(f'{len(briefs)} briefs -> {out_path}')
    if skipped:
        print(f'skipped (missing term, rent or RSF): {", ".join(skipped)}')


if __name__ == '__main__':
    main()
