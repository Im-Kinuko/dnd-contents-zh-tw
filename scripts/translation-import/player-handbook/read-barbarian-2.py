"""Read current names and every relevant Weblate source without mutations."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / '_incoming/player-handbook'
sys.path.insert(0,str(ROOT/'.claude/skills/translation-import/scripts'))
import weblate as w
keys = list(json.loads((HERE/'classes.barbarian.2.sheet.json').read_text(encoding='utf-8'))['entries'])
def read_all(project,component):
    page,rows,audit = 1,[],[]
    while True:
        status,body = w.call('GET',f'/api/translations/{project}/{component}/zh_Hant/units/?page_size=1000&page={page}')
        assert status == 200,(project,component,status)
        rows.extend(body['results'])
        audit.append({'page':page,'status':status,'count':body['count'],'received':len(body['results'])})
        if not body.get('next'):
            assert len(rows)==body['count']
            break
        page+=1
    return rows,audit
units,audit = read_all('dnd-players-handbook','dnd-players-handbook-classes')
data = {'audit':audit,'units':{row['context']:row for row in units}}
(HERE/'classes.barbarian.2.weblate.json').write_text(json.dumps(data,ensure_ascii=False,indent=1),encoding='utf-8')
print('classes:',len(units),'complete HTTP 200')
print(json.dumps({key:{'name':data['units']['entries.'+key+'.name']['target'][0], 'nested':{context:row['target'][0] for context,row in data['units'].items() if context.startswith('entries.'+key+'.') and not context.endswith('.description')}} for key in keys},ensure_ascii=False,indent=1))
for component in ['terms','spells-glossary']:
    rows,audit = read_all('dnd-5e-2024-zh-tw',component)
    (HERE/f'classes.barbarian.2.{component}.live.json').write_text(json.dumps({'audit':audit,'units':rows},ensure_ascii=False,indent=1),encoding='utf-8')
    print(component,':',len(rows),'complete HTTP 200')
rows,audit = read_all('dnd-players-handbook','dnd-players-handbook-feats')
names = {row['context']:row for row in rows if row['context']=='entries.Boon of Irresistible Offense.name'}
assert len(names)==1
(HERE/'classes.barbarian.2.feat-names.live.json').write_text(json.dumps({'audit':audit,'units':names},ensure_ascii=False,indent=1),encoding='utf-8')
print(json.dumps({key:row['target'] for key,row in names.items()},ensure_ascii=False))
print('Brutal Strike advancement:',data['units']['entries.Barbarian.advancement.Brutal Strike.title']['target'])
