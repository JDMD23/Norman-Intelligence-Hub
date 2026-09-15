import json, re, sys
from difflib import SequenceMatcher
from collections import defaultdict
sys.path.insert(0,'tools/sheet_ops')
import common
SC='/tmp/claude-0/-home-user-Norman-Intelligence-Hub/2568e279-3cbb-5941-be03-4e24cdf0c2fe/scratchpad'
rows=json.load(open(f'{SC}/deck_rows.json'))

def na(a):
    a=a.split('/')[0].lower().strip()
    for pat,rep in ((r'\bavenue of the americas\b','6ave'),(r'\bsixth avenue\b','6ave'),
                    (r'\b(avenue|ave\.?)\b','ave'),(r'\b(street|st\.?)\b','st'),
                    (r'\b(south|s\.?)\b','s'),(r'\b(west|w\.?)\b','w'),(r'\b(east|e\.?)\b','e')):
        a=re.sub(pat,rep,a)
    for w,dg in zip('one two three four five six seven eight nine ten eleven twelve'.split(),
                    '1 2 3 4 5 6 7 8 9 10 11 12'.split()):
        a=re.sub(rf'\b{w}\b',dg,a)
    return re.sub(r'[^a-z0-9]','',a)
def nt(t):
    t=t.lower().replace('&',' and ')
    t=re.sub(r'\b(inc|llc|lp|ltd|corp|co|group|worldwide|technologies|technology|systems|the)\b',' ',t)
    return re.sub(r'[^a-z0-9]','',t)
def mdist(a,b):
    if not a or not b: return 99
    return abs((a[0]-b[0])*12+(a[1]-b[1]))

# --- one transaction = same tenant, RSF within 5%, signed within 2 months
tx=[]
for r in rows:
    r['nt']=nt(r['tenant']); r['na']=na(r['address'])
    for t in tx:
        h=t[0]
        if h['nt']==r['nt'] and h['rsf'] and r['rsf'] \
           and abs(h['rsf']-r['rsf'])/max(h['rsf'],r['rsf'])<=0.05 and mdist(h['date'],r['date'])<=2:
            t.append(r); break
    else:
        tx.append([r])
print(f'{len(rows)} deck rows -> {len(tx)} distinct transactions')

s=common.session(); H=common.headers(s,'Lease Comps')
raw=common.get_values(s,"'Lease Comps'!A2:AS1206",render='UNFORMATTED_VALUE')
fmt=common.get_values(s,"'Lease Comps'!A2:AS1206",render='FORMATTED_VALUE')
def c(r,h):
    k=0
    for ch in H[h]: k=k*26+ord(ch)-64
    return r[k-1] if k-1<len(r) else ''
def n_(r,h):
    v=c(r,h)
    if isinstance(v,(int,float)): return float(v)
    v=str(v).strip(); return None if v=='' else float(v.replace('$','').replace(',',''))
MON={m:i for i,m in enumerate('january february march april may june july august september october november december'.split(),1)}
hub=[]
for r,fr in zip(raw,fmt):
    cid=str(c(r,'Comp ID')).strip()
    if not cid: continue
    ds=str(c(fr,'Date Signed')).strip(); dt=None
    m=re.match(r'([A-Za-z]+)\s+(\d{4})',ds)
    if m and m.group(1).lower() in MON: dt=(int(m.group(2)),MON[m.group(1).lower()])
    hub.append(dict(cid=cid,tenant=str(c(r,'Tenant')).strip(),address=str(c(r,'Address')).strip(),
        na=na(str(c(r,'Address'))),nt=nt(str(c(r,'Tenant'))),floor=str(c(r,'Floor(s)')).strip(),
        rsf=n_(r,'RSF'),term=n_(r,'Term (Years)'),p1=n_(r,'Rent P1 ($/RSF, mo 1-60)'),
        p2=n_(r,'Rent P2 ($/RSF, mo 61-120)'),p3=n_(r,'Rent P3 ($/RSF, mo 121+)'),
        free=n_(r,'Free Rent (months)'),ti=n_(r,'TI $/SF'),deal=str(c(r,'Deal Type')).strip(),
        date=ds,dt=dt))

pairs=[]
for t in tx:
    h0=t[0]; cands=[]
    for h in hub:
        # tenant similarity is mandatory: two different tenants can take near-identical
        # floor plates in the same building in the same month (Veeva / Altana at 2 Penn Plaza),
        # so building + RSF + date alone is not evidence of the same transaction.
        a,b=h['nt'],h0['nt']
        sim=SequenceMatcher(None,a,b).ratio() if a and b else 0
        ten = bool(a) and bool(b) and (a==b or a in b or b in a or sim>=0.7)
        if not ten: continue
        addr= h['na']==h0['na']
        rsf = h['rsf'] and h0['rsf'] and abs(h['rsf']-h0['rsf'])/max(h['rsf'],h0['rsf'])<=0.05
        dm  = mdist(h['dt'],h0['date'])
        sc  = (3 if a==b else 2)+(2 if addr else 0)+(2 if rsf else 0)+(1 if dm<=2 else 0)
        if addr or rsf:
            # RSF closeness breaks ties: a tenant with two deals in one building in one month
            # (BILT at 837 Washington: 39,591 on E2-6 and 58,434 on the ground/lower level)
            # scores identically on every other signal.
            gap = abs(h['rsf']-h0['rsf'])/max(h['rsf'],h0['rsf']) if (h['rsf'] and h0['rsf']) else 9
            cands.append((sc,-dm,-gap,h))
    cands.sort(key=lambda x:(-x[0],-x[1],-x[2]))
    pairs.append((t, cands[0][3] if cands else None, cands[0][0] if cands else -1,
                  -cands[0][2] if cands else 9))
# resolve: one hub comp to at most one transaction (best score wins)
# one hub comp maps to at most one transaction: keep the strongest claim on it.
# Score first, then RSF closeness — a tenant with two deals in one building in the same
# month (BILT at 837 Washington) ties on every other signal.
best={}
for t,h,sc,gap in pairs:
    if h is None: continue
    key=h['cid']
    if key not in best or (sc,-gap) > (best[key][2],-best[key][3]):
        best[key]=(t,h,sc,gap)
final=[]
for t,h,sc,gap in pairs:
    final.append((t, h if (h and best[h['cid']][0] is t) else None))
print(f'matched: {sum(1 for _,h in final if h)}   missing from hub: {sum(1 for _,h in final if not h)}')
json.dump({'pairs':[{'deck':t,'hub':h} for t,h in final],'hub':hub},
          open(f'{SC}/pairs.json','w'), indent=1, default=str)
