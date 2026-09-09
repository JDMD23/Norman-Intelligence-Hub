"""Lease Comps formula contract (F_SPEC) and the ensure step that keeps the sheet on it.

History: the v4 migration (2026-09-02, docs/LEASE_COMPS_DESIGN.md) rebuilt the tab from the
pre-v4 layout; the pre-migration copy lives in the hidden tab LC_BACKUP_2026-09-02. Later
structural moves have their own scripts (migrate_cohort_column.py, remove_provenance_columns.py,
migrate_floor_detail.py). What remains here is the single source of truth for the wired and
computed formulas: any column whose row-2 formula drifts from F_SPEC is rewritten and receipted
as FORMULA PATCH.

The header guard below is load-bearing. F_SPEC keys are column letters, so running this against
a layout it was not written for writes correct formulas into the wrong columns.
"""
from common import session, values_batch, get_values, changelog

s = session()

hdr = get_values(s, "'Lease Comps'!A1:AS1", render='FORMATTED_VALUE')[0]
EXPECT = {14: 'Rent P1', 19: 'Latest Round Date', 26: 'Floors on File', 30: 'Blend Check',
          31: 'Notes', 43: 'Record Status', 44: 'QA Notes'}
assert len(hdr) == 45, f'expected 45 columns, found {len(hdr)}'
for i, want in EXPECT.items():
    assert hdr[i].startswith(want), f'column index {i} is {hdr[i]!r}, expected {want!r}'

F_SPEC = {
    # ---- Zone 4a: funding + company, wired from Funding Rounds / Company Metrics / Companies
    'T': '=IF($D{r}="","",IF(COUNTIF(FundingRounds_CompanyIds,$D{r})=0,"",'
         'MAXIFS(FundingRounds_Dates,FundingRounds_CompanyIds,$D{r})))',
    # Sort: date desc, then amount desc — same-day rounds (a seed and Series A disclosed
    # together) surface the larger primary, matching the audit convention.
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

    # ---- Zone 4b: floor detail, wired from the Floor Detail tab. Blank unless the comp has
    #      floor rows. The weighted averages cover only floors that carry the field, so a
    #      floor with RSF but no TI does not drag the TI blend toward zero.
    'AA': '=IF($A{r}="","",LET(n,COUNTIF(FloorDetail_CompIds,$A{r}),IF(n=0,"",n)))',
    'AB': '=IF(OR($A{r}="",$AA{r}=""),"",SUMIF(FloorDetail_CompIds,$A{r},FloorDetail_RSF))',
    'AC': '=IF(OR($A{r}="",$AA{r}=""),"",LET(m,(FloorDetail_CompIds=$A{r})*(FloorDetail_Rents<>""),'
          'd,SUMPRODUCT(m*N(FloorDetail_RSF)),IF(d=0,"",'
          'SUMPRODUCT(m*N(FloorDetail_RSF)*N(FloorDetail_Rents))/d)))',
    'AD': '=IF(OR($A{r}="",$AA{r}=""),"",LET(m,(FloorDetail_CompIds=$A{r})*(FloorDetail_TIs<>""),'
          'd,SUMPRODUCT(m*N(FloorDetail_RSF)),IF(d=0,"",'
          'SUMPRODUCT(m*N(FloorDetail_RSF)*N(FloorDetail_TIs))/d)))',
    # Tolerances: 1 SF, $0.50/RSF, $1/SF. A typed 0 or blank TI against a positive detail
    # blend is called out separately — that failure mode cost ~$15/SF of NER on LC-0103.
    'AE': '=IF(OR($A{r}="",$AA{r}=""),"",LET(t,TEXTJOIN("; ",TRUE,'
          'IF(AND($AB{r}<>"",$L{r}<>"",ABS($L{r}-$AB{r})>1),"RSF MISMATCH",""),'
          'IF(AND($AC{r}<>"",$O{r}<>"",ABS($O{r}-$AC{r})>0.5),"RENT MISMATCH",""),'
          'IF(AND($AD{r}<>"",$AD{r}>0,OR($S{r}="",$S{r}=0)),"TI MISSING",'
          'IF(AND($AD{r}<>"",$S{r}<>"",ABS($S{r}-$AD{r})>1),"TI MISMATCH",""))),'
          'IF(t="","OK",t)))',

    # ---- Zones 5-6: economics on flat rent tranches (no assumed escalation)
    'AJ': '=IF(OR($L{r}="",$N{r}="",$O{r}=""),"",LET(nmo,ROUND($N{r}*12,0),rz,$O{r},'
          'rsix,IF($P{r}="",rz,$P{r}),relev,IF($Q{r}="",rsix,$Q{r}),mA,MIN(nmo,60),'
          'mB,MIN(MAX(nmo-60,0),60),mC,MAX(nmo-120,0),$L{r}*(rz*mA+rsix*mB+relev*mC)/12))',
    'AK': '=IF(OR($AJ{r}="",$L{r}="",$N{r}=""),"",$AJ{r}/$L{r}/$N{r})',
    'AO': '=IF(OR($AG{r}="",$V{r}=""),"",$AG{r}/($V{r}*1000000))',
    'AP': '=IF(OR($AJ{r}="",$W{r}="",$W{r}=0),"",$AJ{r}/($W{r}*1000000))',
    'AQ': '=IF(OR($W{r}="",$AG{r}="",$AG{r}=0),"",($W{r}*1000000)/($AG{r}/12))',


    # Recovered verbatim from LC_BACKUP_2026-09-02 after the 2026-09-03 bad write.
    'AG': '=IF(OR($L{r}="",$O{r}=""),"",$L{r}*$O{r})',
    'AH': '=IF(OR($R{r}="",$O{r}="",$L{r}=""),"",$R{r}/12*$O{r}*$L{r})',
    'AI': '=IF(OR($S{r}="",$L{r}=""),"",$S{r}*$L{r})',
    'AL': '=IF(OR($N{r}="",$O{r}="",$S{r}=""),"",LET(nmo,ROUND($N{r}*12,0),im,0.06/12,rz,$O{r},rsix,IF($P{r}="",rz,$P{r}),relev,IF($Q{r}="",rsix,$Q{r}),mos,SEQUENCE(nmo),pvbeg,SUMPRODUCT(MAP(mos,LAMBDA(mm,IF(mm<=60,rz,IF(mm<=120,rsix,relev))/12*(1+im)^-(mm-1)))),afbeg,(1-(1+im)^-nmo)/im/12*(1+im),freemo,IF($R{r}="",0,$R{r}),ROUND(pvbeg/afbeg,2)-(freemo/12*rz+$S{r})/afbeg))',
    'AM': '=IF(OR($AG{r}="",$M{r}="",$M{r}=0),"",$AG{r}/$M{r})',
    'AN': '=IF(OR($L{r}="",$M{r}="",$M{r}=0),"",$L{r}/$M{r})',

    # ---- Zone 7: governance. A floor-detail mismatch reaches both, so it lands in the
    #      Dashboard's "comps needing review" count and not only in its own column.
    'AR': '=IF($C{r}="","",IF(OR($A{r}="",$L{r}="",$N{r}="",$O{r}="",$B{r}="",$F{r}=""),'
          '"MISSING INPUTS",IF(OR($M{r}="",$S{r}="",AND($AE{r}<>"",$AE{r}<>"OK")),'
          '"NEEDS REVIEW","READY")))',
    'AS': '=IF($C{r}="","",TEXTJOIN("; ",TRUE,IF($A{r}="","MISSING COMP ID",""),'
          'IF($L{r}="","MISSING RSF",""),IF($N{r}="","MISSING TERM",""),'
          'IF($O{r}="","MISSING STARTING RENT",""),IF($B{r}="","MISSING DATE",""),'
          'IF($F{r}="","MISSING SUBMARKET",""),IF($M{r}="","SEATS UNKNOWN",""),'
          'IF($S{r}="","TI UNKNOWN - NER BLANK",""),'
          'IF(AND($AE{r}<>"",$AE{r}<>"OK"),"FLOOR DETAIL: "&$AE{r},"")))',
}

# Every F_SPEC key must be a calc/qa column — never an input column such as AF Notes.
INPUT_HEADERS = {'Notes', 'RSF', 'Seats', 'Term (Years)', 'TI $/SF', 'Tenant', 'Comp ID'}
for col in F_SPEC:
    i = 0
    for ch in col:
        i = i * 26 + ord(ch) - 64
    assert hdr[i - 1] not in INPUT_HEADERS, \
        f'F_SPEC would write a formula into input column {col} ({hdr[i - 1]!r})'

current = get_values(s, "'Lease Comps'!A2:AS2", render='FORMULA')[0]
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
