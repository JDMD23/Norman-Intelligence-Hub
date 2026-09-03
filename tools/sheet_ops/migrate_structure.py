"""Lease Comps formula contract (F_SPEC) and the ensure step that keeps the sheet on it.

History: the v4 migration (2026-09-02, docs/LEASE_COMPS_DESIGN.md) rebuilt the tab from the
pre-v4 layout; that column surgery has run and the pre-migration copy lives in the hidden tab
LC_BACKUP_2026-09-02. Later structural moves have their own scripts (migrate_cohort_column.py,
remove_provenance_columns.py). What remains here is the single source of truth for the wired
and computed formulas: any column whose row-2 formula drifts from F_SPEC is rewritten and
receipted as FORMULA PATCH.
"""
from common import session, values_batch, get_values, changelog

s = session()

hdr = get_values(s, "'Lease Comps'!A1:AN1", render='FORMATTED_VALUE')[0]
assert hdr[14].startswith('Rent P1') and hdr[19].startswith('Latest Round Date') and len(hdr) == 40, \
    f'unexpected layout ({len(hdr)} cols): O={hdr[14]!r} T={hdr[19]!r}'


F_SPEC = {
    'T': '=IF($D{r}="","",IF(COUNTIF(FundingRounds_CompanyIds,$D{r})=0,"",'
         'MAXIFS(FundingRounds_Dates,FundingRounds_CompanyIds,$D{r})))',
    # Sort: date desc, then amount desc — same-day rounds (e.g. a seed + Series A
    # disclosed together) surface the larger primary, matching the audit convention.
    'U': '=IF(OR($D{r}="",$T{r}=""),"",IFERROR(INDEX(SORT(FILTER({{FundingRounds_Dates,'
         'FundingRounds_Types,FundingRounds_Amounts}},FundingRounds_CompanyIds=$D{r}),'
         '1,FALSE,3,FALSE),1,2),""))',
    'V': '=IF(OR($D{r}="",$T{r}=""),"",IFERROR(LET(a,INDEX(SORT(FILTER({{FundingRounds_Dates,'
         'FundingRounds_Amounts}},FundingRounds_CompanyIds=$D{r}),1,FALSE,2,FALSE),1,2),'
         'IF(a=0,"",a)),""))',
    'W': '=IF($D{r}="","",IFERROR(LET(t,INDEX(\'Company Metrics\'!$M:$M,'
         'MATCH($D{r},\'Company Metrics\'!$A:$A,0)),IF(OR(t="",t=0),"",t)),""))',
    'X': '=IF($D{r}="","",IFERROR(INDEX(Companies!$B:$B,'
         'MATCH($D{r},Companies!$A:$A,0)),"UNKNOWN ID"))',
    'Y': '=IF($D{r}="","",IFERROR(LET(h,INDEX(Companies!$G:$G,'
         'MATCH($D{r},Companies!$A:$A,0)),IF(h=0,"",h)),""))',
    'Z': '=IF($C{r}="","",IF($U{r}="","No Funding Data",'
         'IFERROR(INDEX(CohortLabels,MATCH($U{r},CohortTypes,0)),"Stage Unknown")))',
    'AE': '=IF(OR($L{r}="",$N{r}="",$O{r}=""),"",LET(nmo,ROUND($N{r}*12,0),rz,$O{r},'
          'rsix,IF($P{r}="",rz,$P{r}),relev,IF($Q{r}="",rsix,$Q{r}),mA,MIN(nmo,60),'
          'mB,MIN(MAX(nmo-60,0),60),mC,MAX(nmo-120,0),$L{r}*(rz*mA+rsix*mB+relev*mC)/12))',
    'AF': '=IF(OR($AE{r}="",$L{r}="",$N{r}=""),"",$AE{r}/$L{r}/$N{r})',
    'AJ': '=IF(OR($AB{r}="",$V{r}=""),"",$AB{r}/($V{r}*1000000))',
    'AK': '=IF(OR($AE{r}="",$W{r}="",$W{r}=0),"",$AE{r}/($W{r}*1000000))',
    'AL': '=IF(OR($W{r}="",$AB{r}="",$AB{r}=0),"",($W{r}*1000000)/($AB{r}/12))',
    'AM': '=IF($C{r}="","",IF(OR($A{r}="",$L{r}="",$N{r}="",$O{r}="",$B{r}="",$F{r}=""),'
          '"MISSING INPUTS",IF(OR($M{r}="",$S{r}=""),"NEEDS REVIEW","READY")))',
    'AN': '=IF($C{r}="","",TEXTJOIN("; ",TRUE,IF($A{r}="","MISSING COMP ID",""),'
          'IF($L{r}="","MISSING RSF",""),IF($N{r}="","MISSING TERM",""),'
          'IF($O{r}="","MISSING STARTING RENT",""),IF($B{r}="","MISSING DATE",""),'
          'IF($F{r}="","MISSING SUBMARKET",""),IF($M{r}="","SEATS UNKNOWN",""),'
          'IF($S{r}="","TI UNKNOWN - NER BLANK","")))',
}


current = get_values(s, "'Lease Comps'!A2:AN2", render='FORMULA')[0]
drift = []
for c, tpl in F_SPEC.items():
    i = 0
    for ch in c:
        i = i * 26 + ord(ch) - 64
    if (current[i - 1] if i - 1 < len(current) else '') != tpl.format(r=2):
        drift.append(c)
if drift:
    res = values_batch(s, [{'range': f"'Lease Comps'!{c}2:{c}1207",
                            'values': [[F_SPEC[c].format(r=row)] for row in range(2, 1208)]}
                           for c in drift])
    changelog(s, 'FORMULA PATCH', 'Lease Comps wired/computed columns re-synced to '
              f'migrate_structure.py spec: {", ".join(drift)}.', '1206')
    print('formula drift patched in columns', drift, '| cells:', res.get('totalUpdatedCells'))
else:
    print('formulas current — nothing to do')
