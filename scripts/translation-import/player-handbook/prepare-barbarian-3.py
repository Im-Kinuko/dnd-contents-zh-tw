"""Prepare the next journal batch from the same Chinese source, with exact scope."""
import json, re, sys
from pathlib import Path
import opencc
ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / '_incoming/player-handbook'
PREFIX='content.barbarian.3'
sys.path.insert(0,str(ROOT/'.claude/skills/translation-import/scripts'))
from html_blocks import Plan
def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))
def save(suffix,value):
    (HERE/(PREFIX+'.'+suffix+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=1),encoding='utf-8')
source_path=next((HERE/'_web/barbarian').glob('*.htm.txt'))
lines=source_path.read_text(encoding='utf-8').splitlines()
selected='### Barbarian\n'+'\n'.join(lines[18:30])+'\n\n'+'\n'.join(lines[185:187])+'\n'
(HERE/(PREFIX+'.txt')).write_text(selected,encoding='utf-8')
(HERE/(PREFIX+'.source.s2twp.txt')).write_text(opencc.OpenCC('s2twp').convert(selected),encoding='utf-8')

# The same introduction was already approved in classes batch 1. Its independent
# draft originated from these Chinese source lines; reuse it verbatim here.
previous=(HERE/'_done/classes.barbarian.1.draft.txt').read_text(encoding='utf-8')
section=re.search(r'^### Barbarian\n(.*?)(?=^### |\Z)',previous,re.M|re.S)[1].strip().splitlines()
start=next(i for i,line in enumerate(section) if line.startswith('野蠻人是強大的戰士，'))
intro=section[start:]
assert len(intro)==10
subclass='野蠻人子職業是一種特化，在特定等級給予你對應的特性，具體內容見各子職業的說明。接下來的頁面介紹狂戰士道途、狂野之心道途、世界樹道途和狂熱者道途這四種子職業。'
draft=['### Barbarian','野蠻人']+intro+['野蠻人子職業',subclass]
(HERE/(PREFIX+'.draft.txt')).write_text('\n'.join(draft)+'\n',encoding='utf-8')

en=load(ROOT/'compendium/en/dnd-players-handbook/dnd-players-handbook.content.json')['entries']['Barbarian']
page=en['pages']['Barbarian']
assert set(page)=={'name','subclassHeader','description','subclass'}
save('en-scope',{'entries':{'Barbarian':{'name':en['name'],'pages':{'Barbarian':page}}}})
sheet={'schema_version':2,'book':'dnd-players-handbook','component':'content','adapter':'journal page fields expanded as description records for skeleton.build_entries; payload restores real pages paths','entries':{}}
for field in ['description','subclass']:
    key='Barbarian.'+field
    row={'name_en':page['name'] if field=='description' else page['subclassHeader'],'name':'','blocks':[],'payload_path':'entries.Barbarian.pages.Barbarian.'+field}
    for block in Plan(page[field]).blocks:
        row['blocks'].append({'id':block.id,'en':block.html,'zh':'','source':'draft','basis':''})
    sheet['entries'][key]=row
save('sheet',sheet)

remaining=[
    '### Barbarian Class Features / Barbarian Features',
    '# 原網頁31–159行：content及classes現行EN模板沒有獨立欄位；不能自行添加不存在的key。表格引用保留於本批正文。',
    '\n'.join(lines[30:159]),'',
    '### Barbarian Subclass — source-only clauses',
    '# 原網頁187行的選擇、後續能力取得及特性表句，不在content的subclass摘要EN中；保留來源，不追加到摘要。',
    lines[186],'',
    '### Ability Score Improvement — class progression explanation',
    '# 原網頁192–193行：本批日誌頁及classes無對應獨立欄位；不是feats同名專長正文。',
    '\n'.join(lines[191:193]),'',
    '### Path of the Berserker / Path of the Wild Heart / Path of the World Tree / Path of the Zealot',
    '# 四個子職業連結頁尚未抓取；各自的classes特性與content介紹留待後續批次。',
]
(HERE/(PREFIX+'.remaining.txt')).write_text('\n'.join(remaining)+'\n',encoding='utf-8')
save('source-map',{'source_path':str(source_path.resolve()),'entry':'Barbarian','page':'Barbarian','source_ranges':[[19,30],[186,187]],'reused_approved_draft':'classes.barbarian.1.draft.txt','remaining_ranges':[[31,159],[192,193]],'missing_en_is_not_completed_translation':True,'subclasses_not_fetched':True})
print('Prepared 1 real journal entry / 1 page / 5 payload strings; 10 description text blocks + 1 subclass text block + 2 protected embeds.')
