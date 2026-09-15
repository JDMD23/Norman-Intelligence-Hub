import json, re, sys
SC='/tmp/claude-0/-home-user-Norman-Intelligence-Hub/2568e279-3cbb-5941-be03-4e24cdf0c2fe/scratchpad'
MON={m:i for i,m in enumerate(
 'jan feb mar apr may jun jul aug sep oct nov dec'.split(),1)}

def date(s):
    s=s.strip()
    m=re.match(r'([A-Za-z]{3})[a-z]*[-/ ](\d{2,4})', s)
    if not m: return None
    mo=MON.get(m.group(1).lower()); y=int(m.group(2)); y=2000+y if y<100 else y
    return (y,mo) if mo else None

def rsf(s):
    s=re.sub(r'[^\d]','',s.split('\n')[0])
    return int(s) if s else None

def term(s):
    s=s.strip().lower()
    if 'confidential' in s or not s: return None
    m=re.search(r'(\d+)\s*y(?:ea)?r?s?\.?\s*(?:(\d+)\s*m)?', s)
    if m: return int(m.group(1))*12+int(m.group(2) or 0)
    m=re.search(r'(\d+)\s*m(?:o|onths?)\b', s)
    if m: return int(m.group(1))
    return None

def rents(s):
    if 'confidential' in s.lower(): return None
    out=[]
    for tok in re.split(r'[/|]', s):
        m=re.search(r'\$?\s*([\d,]+(?:\.\d+)?)', tok)
        if m:
            v=float(m.group(1).replace(',',''))
            if 20<=v<=400: out.append(v)
    return out or None

def free(s):
    s=s.strip()
    if 'confidential' in s.lower(): return None
    m=re.search(r'(\d+(?:\.\d+)?)', s)
    return float(m.group(1)) if m else None

def ti(s):
    """returns (value or None, label) — label preserves Turnkey / Pre-Built / As-Is wording"""
    raw=' '.join(s.split())
    low=raw.lower()
    if 'confidential' in low: return None, raw
    m=re.search(r'\$\s*([\d,]+)(?:\.+(\d{1,2}))?', raw)
    val=float(m.group(1).replace(',','')) if m else None
    if val is not None and val>1000: val=None           # e.g. "$52MM Termination"
    if val is None:
        if 'as-is' in low or 'as is' in low: val=0.0
    return val, raw

FIELDS=['Date','Completed','Tenant','Address','Floor','RSF','Term','Base Rent (PSF)',
        'Free Rent (Mos.)','TI (PSF)','Deal Type','Renovated / Amenitized']
rows=[]
d=json.load(open(f'{SC}/decks.json'))
for deck,slides in d.items():
    for s in slides:
        for t in s['tables']:
            hdr=[h.strip() for h in t[0]]
            idx={h:i for i,h in enumerate(hdr)}
            dk=idx.get('Date', idx.get('Completed'))
            for r in t[1:]:
                if not any(x.strip() for x in r): continue
                g=lambda k: r[idx[k]].strip() if k in idx and idx[k]<len(r) else ''
                tv,tl=ti(g('TI (PSF)'))
                rec=dict(deck=deck.split('-',1)[1][:-5], tenant=g('Tenant'),
                         address=g('Address'), floor=g('Floor'),
                         date=date(r[dk] if dk is not None and dk<len(r) else ''),
                         date_raw=(r[dk] if dk is not None and dk<len(r) else '').strip(),
                         rsf=rsf(g('RSF')), term_mo=term(g('Term')), term_raw=g('Term'),
                         rents=rents(g('Base Rent (PSF)')), rent_raw=' '.join(g('Base Rent (PSF)').split()),
                         free=free(g('Free Rent (Mos.)')), free_raw=' '.join(g('Free Rent (Mos.)').split()),
                         ti=tv, ti_raw=tl, deal=g('Deal Type'))
                if rec['tenant'] and rec['address']: rows.append(rec)
print(f'{len(rows)} deck rows parsed')
json.dump(rows, open(f'{SC}/deck_rows.json','w'), indent=1)
bad=[r for r in rows if r['rsf'] is None]
print(f'rows with unparseable RSF: {len(bad)}', [(r["tenant"],r["rsf"]) for r in bad][:5])
conf=[r for r in rows if r['rents'] is None]
print(f'rows with confidential/unparseable rent: {len(conf)}', [r["tenant"] for r in conf][:8])
