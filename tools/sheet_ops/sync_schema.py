"""Pull the workbook's _Schema and Reference tabs into the repo mirrors.

Writes schema/schema.json (tabs regenerated; top-level metadata preserved),
schema/reference.json, and regenerates docs/DATA_DICTIONARY.md from them.
Read-only against the workbook; run after any change to _Schema or Reference.
"""
import json
import os

from common import session, get_values

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SCHEMA_JSON = os.path.join(ROOT, 'schema', 'schema.json')
REF_JSON = os.path.join(ROOT, 'schema', 'reference.json')
DICT_MD = os.path.join(ROOT, 'docs', 'DATA_DICTIONARY.md')

s = session()

# ---- _Schema -> schema.json
rows = get_values(s, '_Schema!A1:J400', render='FORMATTED_VALUE')
schema = json.load(open(SCHEMA_JSON))
tabs, meta = {}, {}
for r in rows[1:]:
    r = list(r) + [''] * (10 - len(r))
    tab, column, header, key, typ, role, req, enum, formula, desc = (str(x) for x in r[:10])
    if not tab:
        continue
    if tab == '(workbook)':
        meta[key] = desc
        continue
    entry = {'column': column, 'header': header, 'key': key, 'type': typ, 'role': role,
             'required': req.strip().lower() == 'yes'}
    if enum:
        entry['enum_named_range'] = enum
    if formula:
        entry['formula_pattern'] = formula
    entry['description'] = desc
    tabs.setdefault(tab, {'columns': []})['columns'].append(entry)
schema['tabs'] = tabs
if 'contract' in meta:
    schema['contract'] = meta['contract']
if 'version' in meta:
    schema['version_note'] = meta['version']
    schema['version'] = meta['version'].split(' ')[0]
json.dump(schema, open(SCHEMA_JSON, 'w'), indent=2, ensure_ascii=False)
open(SCHEMA_JSON, 'a').write('\n')

# ---- Reference -> reference.json (vocab columns = every header except the variant map pair)
ref_rows = get_values(s, 'Reference!A1:Z200', render='FORMATTED_VALUE')
hdr = list(ref_rows[0]) + [''] * 26
vocab = {}
for j, name in enumerate(hdr[:26]):
    if not name or name in ('Variant Tenant Name', 'Canonical Company'):
        continue
    vals = []
    for r in ref_rows[1:]:
        v = r[j] if j < len(r) else ''
        if v == '':
            break
        vals.append(str(v))
    vocab[name] = vals
jv, jc = hdr.index('Variant Tenant Name'), hdr.index('Canonical Company')
variant_map = {}
for r in ref_rows[1:]:
    v = r[jv] if jv < len(r) else ''
    if v == '':
        break
    variant_map[str(v)] = str(r[jc] if jc < len(r) else '')
reference = {'vocabularies': vocab, 'tenant_variant_map': variant_map}
json.dump(reference, open(REF_JSON, 'w'), indent=2, ensure_ascii=False)
open(REF_JSON, 'a').write('\n')

# ---- DATA_DICTIONARY.md
out = ['# Data Dictionary', '',
       f"Generated from [`schema/schema.json`](../schema/schema.json), a mirror of the workbook's "
       f"`_Schema` tab ({schema['version']}). The live `_Schema` tab is authoritative.", '',
       f"**Workbook contract:** {schema['contract']}", '']
for tab, body in tabs.items():
    out += [f'## {tab}', '', '| Col | Header | Key | Type | Role | Req | Enum | Description |',
            '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for c in body['columns']:
        out.append(f"| {c['column']} | {c['header']} | `{c['key']}` | {c['type']} | {c['role']} | "
                   f"{'yes' if c['required'] else ''} | {c.get('enum_named_range', '')} | "
                   f"{c['description']} |")
    out.append('')
out += ['## Reference vocabularies', '']
for name, vals in vocab.items():
    out.append(f"- **{name}**: {', '.join(vals)}")
out += ['', '### Tenant variant map', '']
for k, v in variant_map.items():
    out.append(f'- `{k}` → `{v}`')
open(DICT_MD, 'w').write('\n'.join(out) + '\n')
print(f'synced: {sum(len(t["columns"]) for t in tabs.values())} columns across {len(tabs)} tabs; '
      f'{len(vocab)} vocabularies; {len(variant_map)} variant mappings')
