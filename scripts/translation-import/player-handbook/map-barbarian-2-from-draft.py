"""Read complete draft lines; only add EN structure and inline annotations."""
import hashlib, json, re, sys
from pathlib import Path
import opencc
ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / '_incoming/player-handbook'
sys.path.insert(0,str(ROOT/'.claude/skills/translation-import/scripts'))
from html_blocks import Plan, compare_html, visible_text
PREFIX = 'classes.barbarian.2'
def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))
def save(suffix,value):
    (HERE/(PREFIX+'.'+suffix+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=1),encoding='utf-8')
def sections(path):
    result={}
    for match in re.finditer(r'^### ([^\r\n]+)\n(.*?)(?=^### |\Z)',path.read_text(encoding='utf-8'),re.M|re.S):
        result[match[1]]=[line for line in match[2].strip().splitlines() if line.strip()]
    return result
draft = sections(HERE/(PREFIX+'.draft.txt'))
supp = sections(HERE/(PREFIX+'.supplement.draft.txt'))
sheet = load(HERE/(PREFIX+'.sheet.json'))
en = load(ROOT/'compendium/en/dnd-players-handbook/dnd-players-handbook.classes.json')['entries']
live = load(HERE/(PREFIX+'.weblate.json'))['units']
source = sections(HERE/(PREFIX+'.txt'))
source_text = (HERE/(PREFIX+'.txt')).read_text(encoding='utf-8')
(HERE/(PREFIX+'.source.s2twp.txt')).write_text(opencc.OpenCC('s2twp').convert(source_text),encoding='utf-8')
source_ranges = {'Instinctive Pounce':(202,204),'Brutal Strike':(205,211),'Relentless Rage':(212,214),'Improved Brutal Strike':(215,221),'Persistent Rage':(222,224),'Improved Brutal Strike (2)':(225,226),'Indomitable Might':(227,228),'Epic Boon':(229,230),'Primal Champion':(231,232)}
counts = {'Instinctive Pounce':1,'Brutal Strike':3,'Relentless Rage':2,'Improved Brutal Strike':3,'Persistent Rage':2,'Improved Brutal Strike (2)':1,'Indomitable Might':1,'Epic Boon':1,'Primal Champion':1}
supp_counts = {'Brutal Strike':3,'Relentless Rage':2,'Improved Brutal Strike':2,'Persistent Rage':2,'Improved Brutal Strike (2)':2}
mapping=[]

for key,row in sheet['entries'].items():
    row['name'] = draft[key][0]
    lines = draft[key][1:]
    assert len(lines)==counts[key]
    assert len(row['blocks']) == len(lines)+supp_counts.get(key,0)
    for block,line in zip(row['blocks'],lines):
        zh=line
        # Read the heading from the draft, rather than making a second translation.
        if block['en'].startswith('<strong>'):
            heading = re.match(r'^【[^】]+】',zh)[0]
            zh = zh.replace(heading,'<strong>'+heading+'</strong>',1)
        if '[[/item Reckless Attack]]' in block['en']:
            label=draft.get('Reckless Attack',['魯莽攻擊'])[0]
            # This is an existing name already present verbatim in the source draft.
            assert label in line
            zh=zh.replace(label,'[[/item Reckless Attack]]{'+label+'}',1)
        for target,label in [('Opportunity Attacks','藉機攻擊'),('Unconscious','昏迷'),('Incapacitated','失能')]:
            token='&amp;Reference['+target+']'
            if token in block['en']:
                assert label in zh
                zh=zh.replace(label,token+'{'+label+'}',1)
        if key=='Epic Boon':
            for target,label in [('Compendium.dnd-players-handbook.content.JournalEntry.phbFeats00000000.JournalEntryPage.GxfrwkJbrIvn7reC','傳奇恩惠專長'),('Compendium.dnd-players-handbook.feats.Item.phbBoonofIrresis','無敵攻勢恩惠')]:
                assert label in zh
                zh=zh.replace(label,'@UUID['+target+']{'+label+'}',1)
        assert visible_text(zh)==visible_text(line),(key,block['id'],'Chinese changed')
        assert not compare_html(block['en'],zh),(key,block['id'],compare_html(block['en'],zh))
        block.update(zh=zh,source='draft',basis='')
        mapping.append({'path':key+'.description/'+block['id'],'en':block['en'],'draft':line,'zh':zh,'source':'draft','source_lines':source_ranges[key],'exact_visible_match':True})
    for block,line in zip(row['blocks'][len(lines):],supp.get(key,[])[:supp_counts.get(key,0)]):
        zh=line
        if block['en'].startswith('<strong>'):
            zh='<strong>'+zh+'</strong>'
        elif '<strong>damage</strong>' in block['en']:
            assert '傷害行動' in line
            zh=zh.replace('傷害行動','<strong>傷害</strong>行動',1)
        assert visible_text(zh)==line
        assert not compare_html(block['en'],zh),(key,block['id'],compare_html(block['en'],zh))
        basis='網頁沒有Foundry註記；依此區塊EN與獨立supplement.draft.txt補翻。行動、Active Effect、比例值沿用使用者裁定；名稱沿用來源底稿。'
        block.update(zh=zh,source='supplement',basis=basis)
        mapping.append({'path':key+'.description/'+block['id'],'en':block['en'],'draft':line,'zh':zh,'source':'supplement','basis':basis,'exact_visible_match':True})

def get_supp(key,label,index=0):
    return [line[len(label):] for line in supp[key] if line.startswith(label)][index]
row=sheet['entries']['Brutal Strike']
row['activities']['Brutal Strike']['name']=row['name']
row['effects']['Hamstrung']={'name':get_supp('Brutal Strike','效果名稱：'),'description':'<p>'+get_supp('Brutal Strike','效果描述：')+'</p>'}
row=sheet['entries']['Improved Brutal Strike']
for option,index in [('Staggering Blow',2),('Sundering Blow',3)]:
    row['activities'][option]['name']=re.match(r'^【([^】]+)】',draft['Improved Brutal Strike'][index])[1]
for effect,index in [('Staggered',0),('Sundered',1)]:
    row['effects'][effect]={'name':get_supp('Improved Brutal Strike','效果名稱：',index),'description':'<p>'+get_supp('Improved Brutal Strike','效果描述：',index)+'</p>'}
row=sheet['entries']['Persistent Rage']
row['activities']['Recharge Rage on Initiative']={'name':get_supp('Persistent Rage','行動名稱：'),'condition':get_supp('Persistent Rage','行動條件：')}

def leaves(node,prefix=''):
    if isinstance(node,dict):
        for key,value in node.items():
            yield from leaves(value,prefix+'.'+key if prefix else key)
    elif isinstance(node,str):
        yield prefix,node
orig=dict(leaves({key:en[key] for key in sheet['entries']}))
for key,row in sheet['entries'].items():
    for field in ['activities','effects','advancement']:
        for path,zh in leaves(row.get(field,{}),key+'.'+field):
            original=orig[path]
            assert live['entries.'+path]['source'][0]==original,(path,'Live EN changed')
            assert not compare_html(original,zh),(path,compare_html(original,zh))
            visible=visible_text(zh)
            text='\n'.join(draft[key]+supp.get(key,[]))
            assert visible in text,(path,'Nested field not in either draft')
            source_kind='derived-from-draft' if not path.endswith('.description') and visible in '\n'.join(draft[key]) else 'supplement'
            mapping.append({'path':path,'en':original,'draft':visible,'zh':zh,'source':source_kind,'basis':'正文底稿名稱直接衍生，不另造中文。' if source_kind=='derived-from-draft' else 'Foundry介面欄位在原稿缺漏；完整中文來自supplement.draft.txt，依EN並沿用正文術語。','exact_visible_match':True})
    assert live['entries.'+key+'.name']['source'][0]==en[key]['name']
    assert live['entries.'+key+'.description']['source'][0]==en[key]['description']

save('sheet',sheet)
save('mapping-audit',mapping)
# Normalize only existing technical enrichment syntax in a derivative. Chinese
# sentences remain exactly the draft, so macros do not become false supplements.
norm='\n\n'.join('### '+key+'\n'+'\n'.join(visible_text(line) for line in lines) for key,lines in draft.items())+'\n'
(HERE/(PREFIX+'.draft.validation.txt')).write_text(norm,encoding='utf-8')
save('draft-fingerprints',{name:hashlib.sha256((HERE/(PREFIX+'.'+name+'.txt')).read_bytes()).hexdigest() for name in ['draft','supplement.draft']})
print('Mapped',len(sheet['entries']),'entries;',len(mapping),'body/nested fields; all exact draft matches.')
