"""Fetch complete live content/classes and glossary snapshots for journal preview."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / '_incoming/player-handbook'
PREFIX='content.barbarian.3'
sys.path.insert(0,str(ROOT/'.claude/skills/translation-import/scripts'))
import weblate as w
def save(suffix,value):
    (HERE/(PREFIX+'.'+suffix+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=1),encoding='utf-8')
def read_all(project,component):
    page,rows,audit=1,[],[]
    while True:
        status,body=w.call('GET',f'/api/translations/{project}/{component}/zh_Hant/units/?page_size=1000&page={page}')
        assert status==200,(project,component,status)
        rows.extend(body['results'])
        audit.append({'page':page,'status':status,'count':body['count'],'received':len(body['results'])})
        if not body.get('next'):
            assert len(rows)==body['count']
            return rows,audit
        page+=1
for component in ['content','classes']:
    slug='dnd-players-handbook-'+component
    status,translation=w.call('GET','/api/translations/dnd-players-handbook/'+slug+'/zh_Hant/')
    assert status==200 and translation['filename']=='compendium/zh-tw/dnd-players-handbook/dnd-players-handbook.'+component+'.json'
    rows,audit=read_all('dnd-players-handbook',slug)
    save(component+'.live',{'filename':translation['filename'],'audit':audit,'units':{row['context']:row for row in rows}})
    print(component,len(rows),'complete HTTP 200; correct filename')
    if component=='content':
        print(json.dumps({row['context']:row['target'] for row in rows if row['context']=='entries.Barbarian.name' or row['context'].startswith('entries.Barbarian.pages.Barbarian.')},ensure_ascii=False))
    else:
        names=['Barbarian','Path of the Berserker','Path of the Wild Heart','Path of the World Tree','Path of the Zealot']
        print(json.dumps({row['context']:row['target'] for row in rows if row['context'] in ['entries.'+name+'.name' for name in names]},ensure_ascii=False))
for component in ['terms','spells-glossary']:
    rows,audit=read_all('dnd-5e-2024-zh-tw',component)
    save(component+'.live',{'audit':audit,'units':rows})
    print(component,len(rows),'complete HTTP 200')
