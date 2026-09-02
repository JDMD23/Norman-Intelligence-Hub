"""Shared helpers for Norman Intelligence Hub workbook operations.

All writes to the workbook go through scripts in this directory, are receipted
in the Changelog tab, and are gated by QA checks (see docs/LEASE_COMPS_DESIGN.md).
"""
import json
import os
from datetime import datetime

os.environ.setdefault('REQUESTS_CA_BUNDLE', '/root/.ccr/ca-bundle.crt')

from google.oauth2 import service_account  # noqa: E402
from google.auth.transport.requests import Request, AuthorizedSession  # noqa: E402

SID = '1qZlc8BUZRObyoeygAToWicor-UFFLmO_aCjk3axBhdE'
SCRATCH = ('/tmp/claude-0/-home-user-Norman-Intelligence-Hub/'
           '76ad1397-5a17-5a11-980a-35cb2aaeea39/scratchpad')
KEY_PATHS = [os.path.join(SCRATCH, 'secrets/sa_key.json'),
             os.environ.get('GOOGLE_SA_KEY_FILE', '')]
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def session():
    # Preferred: GOOGLE_SA_KEY env var holding the service-account JSON itself
    # (set it in the claude.ai/code environment settings so it survives sessions).
    key_json = os.environ.get('GOOGLE_SA_KEY')
    if key_json:
        creds = service_account.Credentials.from_service_account_info(
            json.loads(key_json), scopes=SCOPES)
    else:
        key = next((p for p in KEY_PATHS if p and os.path.exists(p)), None)
        if not key:
            raise SystemExit('No service-account key: set GOOGLE_SA_KEY env var '
                             '(JSON contents) in the environment settings.')
        creds = service_account.Credentials.from_service_account_file(key, scopes=SCOPES)
    creds.refresh(Request())
    return AuthorizedSession(creds)


def sheet_ids(s):
    meta = s.get(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}',
                 params={'fields': 'sheets.properties'}).json()
    return {sh['properties']['title']: sh['properties']['sheetId'] for sh in meta['sheets']}


def named_ranges(s):
    meta = s.get(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}',
                 params={'fields': 'namedRanges'}).json()
    return {n['name']: n for n in meta.get('namedRanges', [])}


def batch_update(s, requests):
    r = s.post(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}:batchUpdate',
               json={'requests': requests})
    if r.status_code != 200:
        raise RuntimeError(f'batchUpdate failed: {r.status_code} {r.json()}')
    return r.json()


def values_batch(s, data):
    r = s.post(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}/values:batchUpdate',
               json={'valueInputOption': 'USER_ENTERED', 'data': data})
    if r.status_code != 200:
        raise RuntimeError(f'values batchUpdate failed: {r.status_code} {r.json()}')
    return r.json()


def get_values(s, rng, render='UNFORMATTED_VALUE'):
    import urllib.parse
    r = s.get(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/'
              f'{urllib.parse.quote(rng, safe="")}',
              params={'valueRenderOption': render, 'dateTimeRenderOption': 'FORMATTED_STRING'})
    return r.json().get('values', [])


def changelog(s, action, detail, rows=''):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    r = s.post(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/'
               'Changelog!A:E:append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS',
               json={'values': [[now, 'norman-hub-agent (Claude)', action, detail, str(rows)]]})
    return r.status_code == 200


def qa_status(s):
    rows = get_values(s, 'QA Harness!A1:F30', render='FORMATTED_VALUE')
    summary = next((r for r in rows if r and r[0] == 'SUMMARY'), None)
    fails = [r for r in rows if len(r) > 5 and r[5] not in ('PASS', 'INFO', 'Status', '')]
    return summary, fails


def typed_rows(s, a1_range):
    """1-based row numbers in a1_range that hold user-entered content (formulas or typed
    values). Cells filled by a spilled array formula have no userEnteredValue, so this is
    the right test for 'where does the next block of the sheet start'."""
    r = s.get(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}',
              params={'ranges': a1_range, 'includeGridData': 'true',
                      'fields': 'sheets.data(startRow,rowData.values.userEnteredValue)'}).json()
    out = set()
    for block in r['sheets'][0].get('data', []):
        start = block.get('startRow', 0)
        for i, row in enumerate(block.get('rowData', [])):
            if any('userEnteredValue' in c for c in row.get('values', [])):
                out.add(start + i + 1)
    return out
