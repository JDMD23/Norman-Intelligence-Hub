"""Resolve the Warp (CO-0090) identity conflation and record its June 2026 Series B.

Owner decision 2026-09-02: the tenant is Warp the payroll/HR/compliance company
(warp.co, Crunchbase warp-e7b9, YC W23, NYC) — NOT warp.dev the terminal company.
The Companies row already carries the right Crunchbase URL but the wrong website,
industry, and narrative. Also appends the Series B the audit predated:
$60M, 2026-06-25, Battery Ventures lead (Peak XV, Sound Ventures, YC, HOF
participating; ~$85M total) — sources: SiliconANGLE 2026-06-25, Dealroom,
company PR via Barchart.
"""
from common import session, get_values, values_batch, changelog, SID

s = session()

row = get_values(s, 'Companies!A91:B91', render='FORMATTED_VALUE')
assert row and row[0][0] == 'CO-0090' and row[0][1] == 'Warp', f'unexpected row 91: {row}'

values_batch(s, [
    {'range': 'Companies!D91:L91', 'values': [[
        'https://www.warp.co',
        'Payroll / HR / compliance automation (AI)',
        2023,
        'NY',
        'YC W23. Seed ~$6M 2024; Series A $18M Jun 2025 (Sound Ventures); '
        'Series B $60M Jun 2026 (Battery Ventures lead; Peak XV, Sound Ventures, YC, HOF). '
        'Total ~$85M.',
        'Seed -> A ~18mo; A -> B ~12mo (accelerating).',
        'Series B 3.3x the Series A twelve months later — clear acceleration.',
        'SiliconANGLE 2026-06-25; Dealroom; company PR (Barchart); Crunchbase warp-e7b9.',
        'IDENTITY RESOLVED (owner, 2026-09-02): tenant is Warp payroll (warp.co / warp-e7b9), '
        'not warp.dev the terminal company. Prior sheet rows conflated the two.',
    ]]},
])
print('Companies CO-0090 identity corrected (website/industry/history/notes)')

fr_ids = get_values(s, "'Funding Rounds'!A2:G3000")
warp_rounds = [r for r in fr_ids if len(r) > 4 and r[1] == 'CO-0090']
if not any('Series B' in str(r[4]) for r in warp_rounds):
    n = max(int(r[0][3:]) for r in fr_ids if r and str(r[0]).startswith('FR-')) + 1
    r = s.post(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/'
               "'Funding Rounds'!A:N:append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS",
               json={'values': [[f'FR-{n:04d}', 'CO-0090', '', '3', 'Series B', '2026-06-25', 60.0,
                                 'Battery Ventures', 85.0, '',
                                 'SiliconANGLE 2026-06-25 + Dealroom + company PR (Barchart)',
                                 'https://siliconangle.com/2026/06/25/warp-lands-60m-automate-payroll-compliance-hr-ai/',
                                 'HIGH', 'Postdates 2026-08-12 audit; added on identity resolution.']]})
    assert r.status_code == 200, r.json()
    print(f'appended FR-{n:04d}: Warp Series B $60M 2026-06-25')
else:
    print('Warp Series B already present')

changelog(s, 'IDENTITY RESOLUTION',
          'Warp (CO-0090) resolved to the payroll company (warp.co / crunchbase warp-e7b9) per '
          'owner decision; Companies row corrected; Series B $60M 2026-06-25 (Battery) appended '
          'to Funding Rounds.', 2)
print('done — wired Lease Comps rows for Warp update automatically')
