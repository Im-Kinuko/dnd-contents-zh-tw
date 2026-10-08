"""檢視 skeleton sheet 的區塊（輸出 UTF-8 檔）。用法：python scripts/aa_view.py sheet.json out.txt"""
import json, sys
d = json.load(open(sys.argv[1], encoding='utf8'))
out = []
for k, v in d['entries'].items():
    out.append('## ' + k)
    for b in v['blocks']:
        out.append('  %s %s' % (b['id'], b['en']))
    for x in v:
        if x not in ('blocks', 'name_en', 'name'):
            out.append('  * %s %s' % (x, json.dumps(v[x], ensure_ascii=False)))
open(sys.argv[2], 'w', encoding='utf8').write('\n'.join(out))
