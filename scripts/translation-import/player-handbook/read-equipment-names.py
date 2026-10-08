import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / '_incoming/player-handbook'
sys.path.insert(0, str(HERE.parents[1] / '.claude/skills/translation-import/scripts'))
import weblate as w
names, audit, page = {}, [], 1
while True:
    status, body = w.call('GET', '/api/translations/dnd-players-handbook/dnd-players-handbook-equipment/zh_Hant/units/?page_size=1000&page='+str(page))
    assert status == 200, status
    audit.append({'page':page,'status':status,'rows':len(body['results']),'count':body['count']})
    for row in body['results']:
        if row['context'] in ["entries.Explorer's Pack.name", 'entries.Greataxe.name', 'entries.Handaxe.name']:
            names[row['context']] = row['target'][0]
    if not body.get('next'):
        break
    page += 1
assert len(names) == 3
(HERE/'barbarian.equipment_names.json').write_text(json.dumps({'audit':audit,'names':names},ensure_ascii=False,indent=1),encoding='utf-8')
print(json.dumps(names,ensure_ascii=False))
