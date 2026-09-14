import json, re
def na(a):
    a=a.split('/')[0].lower().strip()
    a=re.sub(r'^(\d+)\s*-\s*\d+', r'\1', a)   # '11-15 East 26th' -> '11 East 26th'
    for pat,rep in ((r'\bavenue of the americas\b','6ave'),(r'\bsixth avenue\b','6ave'),
                    (r'\b(avenue|ave\.?)\b','ave'),(r'\b(street|st\.?)\b','st'),
                    (r'\b(south|s\.?)\b','s'),(r'\b(west|w\.?)\b','w'),(r'\b(east|e\.?)\b','e')):
        a=re.sub(pat,rep,a)
    for w,dg in zip('one two three four five six seven eight nine ten eleven twelve'.split(),
                    '1 2 3 4 5 6 7 8 9 10 11 12'.split()):
        a=re.sub(rf'\b{w}\b',dg,a)
    a=re.sub(r'[^a-z0-9]','',a)
    return re.sub(r'^(\d+)\d*-(\d+)', r'\1', a)   # 11-15 east 26th -> 11 east 26th
SC='/tmp/claude-0/-home-user-Norman-Intelligence-Hub/2568e279-3cbb-5941-be03-4e24cdf0c2fe/scratchpad'
d=json.load(open(f'{SC}/pairs.json'))
DEAL={'relocation':'new lease','new lease':'new lease','renewal':'renewal','sublease':'sublease',
      'expansion':'expansion','renewal + expansion':'renewal + expansion','extension':'renewal'}
def uniq(vals):
    out=[]
    for v in vals:
        if v is not None and v not in out: out.append(v)
    return out
def fl(s):  # floor comparison key: E4-6 vs E4 - E6 vs e4-e6
    return re.sub(r'[^a-z0-9,]','', s.lower().replace('e','e').replace(' ',''))

rows=[]
for p in d['pairs']:
    dk=p['deck']; h=p['hub']
    if not h: continue
    diffs=[]; conflicts=[]
    def deckvals(key):
        return uniq([r[key] for r in dk])
    # RSF
    dv=deckvals('rsf')
    if len(dv)>1: conflicts.append(f"decks disagree on RSF: {dv}")
    if h['rsf'] and dv and not any(abs(h['rsf']-v)<=max(1,0.005*h['rsf']) for v in dv):
        diffs.append(('RSF', f"{h['rsf']:,.0f}", '/'.join(f'{v:,}' for v in dv)))
    # Address (buildings often carry two legitimate addresses - flag, don't assume)
    da=uniq([r['address'] for r in dk if r['address']])
    if da and not any(na(x)==na(h['address']) or na(x).startswith(na(h['address'])[:8])
                      or na(h['address']).startswith(na(x)[:8]) for x in da):
        diffs.append(('Address', h['address'], ' / '.join(da)))
    # Tenant name variant
    dtn=uniq([r['tenant'] for r in dk if r['tenant']])
    if dtn and not any(x.lower()==h['tenant'].lower() for x in dtn):
        diffs.append(('Tenant name', h['tenant'], ' / '.join(dtn)))
    # Floor
    df=uniq([r['floor'] for r in dk if r['floor']])
    if df and not any(fl(h['floor'])==fl(x) for x in df):
        diffs.append(('Floor', h['floor'], ' / '.join(df)))
    # Term
    dt=uniq([r['term_mo'] for r in dk])
    if len(dt)>1: conflicts.append(f"decks disagree on term: {dt} months")
    hm=round(h['term']*12) if h['term'] else None
    if hm and dt and hm not in dt:
        diffs.append(('Term', f"{hm} mo ({hm/12:.2f}y)", ' / '.join(f'{v} mo' for v in dt)))
    # Rents
    dr=uniq([tuple(r['rents']) for r in dk if r['rents']])
    if len(dr)>1: conflicts.append(f"decks disagree on rent: {[list(x) for x in dr]}")
    hr=[x for x in (h['p1'],h['p2'],h['p3']) if x is not None]
    if dr and tuple(hr) not in dr:
        diffs.append(('Rent', ' / '.join(f'${x:,.0f}' for x in hr),
                      '  or  '.join(' / '.join(f'${y:,.0f}' for y in x) for x in dr)))
    # Free rent
    dfr=uniq([r['free'] for r in dk])
    if len(dfr)>1: conflicts.append(f"decks disagree on free rent: {dfr}")
    if h['free'] is not None and dfr and h['free'] not in dfr:
        diffs.append(('Free rent', f"{h['free']:.0f} mo", ' / '.join(f'{v:.0f} mo' for v in dfr)))
    elif h['free'] is None and dfr:
        diffs.append(('Free rent', 'blank (unknown)', ' / '.join(f'{v:.0f} mo' for v in dfr)))
    # TI
    dti=uniq([r['ti'] for r in dk])
    tiraw=uniq([r['ti_raw'] for r in dk])
    if len(dti)>1: conflicts.append(f"decks disagree on TI: {dti}")
    if dti and h['ti'] is not None and h['ti'] not in dti:
        diffs.append(('TI', f"${h['ti']:,.0f}", ' / '.join(f'${v:,.0f}' for v in dti)+f"  [{'; '.join(tiraw)}]"))
    elif h['ti'] is None and dti:
        diffs.append(('TI', 'blank (unknown)', ' / '.join(f'${v:,.0f}' for v in dti)))
    # Deal type
    dd=uniq([DEAL.get(r['deal'].strip().lower(), r['deal'].strip().lower()) for r in dk if r['deal']])
    if dd and DEAL.get(h['deal'].lower(),h['deal'].lower()) not in dd:
        diffs.append(('Deal type', h['deal'], ' / '.join(dd)))
    rows.append(dict(cid=h['cid'],tenant=h['tenant'],address=h['address'],hub_rsf=h['rsf'],
                     date=h['date'],deck_date=dk[0]['date_raw'],n_decks=len(dk),
                     decks=uniq([r['deck'] for r in dk]),diffs=diffs,conflicts=conflicts))
exact=[r for r in rows if not r['diffs']]
differ=[r for r in rows if r['diffs']]
print(f'MATCHED {len(rows)}  |  exact {len(exact)}  |  differs {len(differ)}')
json.dump({'exact':exact,'differ':differ,
           'missing':[p['deck'] for p in d['pairs'] if not p['hub']]},
          open(f'{SC}/report.json','w'), indent=1, default=str)
print()
print('=== TERM EVIDENCE (settles the open NER question) ===')
tm=[r for r in rows if any(f[0]=='Term' for f in r['diffs'])]
print(f'matched comps where the deck term differs from the hub: {len(tm)}')
for r in tm: print('   ',r['cid'],r['tenant'][:18],[f for f in r['diffs'] if f[0]=='Term'])
