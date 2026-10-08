"""Map journal fields by complete draft paragraphs using existing block tools."""
import hashlib, json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / '_incoming/player-handbook'
PREFIX='content.barbarian.3'
sys.path.insert(0,str(ROOT/'.claude/skills/translation-import/scripts'))
from html_blocks import Plan, compare_html, visible_text, LABEL
from skeleton import build_entries, norm
from validate import check_description, count_strings
def load(suffix):
    return json.loads((HERE/(PREFIX+'.'+suffix+'.json')).read_text(encoding='utf-8-sig'))
def save(suffix,value):
    (HERE/(PREFIX+'.'+suffix+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=1),encoding='utf-8')
def leaves(node,prefix=''):
    if isinstance(node,dict):
        for key,value in node.items():yield from leaves(value,prefix+'.'+key if prefix else key)
    elif isinstance(node,str):yield prefix,node
draft_path=HERE/(PREFIX+'.draft.txt')
lines=[line for line in draft_path.read_text(encoding='utf-8').splitlines() if line.strip()]
assert lines[0]=='### Barbarian' and len(lines)==14
name=lines[1]
body=lines[2:12]
subclass_header,subclass_body=lines[12:14]
assert len(body)==10
sheet=load('sheet')
original=load('en-scope')['entries']['Barbarian']
page=original['pages']['Barbarian']
live=load('content.live')['units']
class_live=load('classes.live')['units']
name_keys=['Barbarian','Path of the Berserker','Path of the Wild Heart','Path of the World Tree','Path of the Zealot']
labels={key:class_live['entries.'+key+'.name']['target'][0] for key in name_keys}
assert labels['Barbarian']==name
for label in labels.values():assert re.search('[一-鿿]',label)
english_aliases={'Barbarians':'Barbarian',**{key:key for key in name_keys}}
source_lines=next((HERE/'_web/barbarian').glob('*.htm.txt')).read_text(encoding='utf-8').splitlines()
ranges={'b0002':(19,19),'b0004':(20,20),'b0005':(21,21),'b0006':(22,22),'b0007':(23,24),'b0008':(25,25),'b0009':(26,26),'b0010':(27,28),'b0011':(29,29),'b0012':(30,30)}
mapping=[]
synthetic={}
for field,texts,record_name in [('description',body,name),('subclass',[subclass_body],subclass_header)]:
    key='Barbarian.'+field
    record=sheet['entries'][key]
    record['name']=record_name
    synthetic[key]={'name':record['name_en'],'description':page[field]}
    text_iter=iter(texts)
    for block in record['blocks']:
        if not visible_text(block['en']).strip():
            line=''
            zh=block['en']
            kind='protected'
            bounds=None
            original_source='原網頁無插圖Embed命令；沒有可翻譯文字，原樣保留EN技術命令。'
        else:
            line=next(text_iter)
            zh=line
            kind='draft'
            bounds=ranges[block['id']] if field=='description' else (186,187)
            original_source='\n'.join(source_lines[bounds[0]-1:bounds[1]])
            # Replace complete visible names with the original technical link;
            # no sentence text is generated in this mapping step.
            for match in LABEL.finditer(block['en']):
                assert match[1].startswith('@UUID[') and match[2] in english_aliases
                label=labels[english_aliases[match[2]]]
                assert label in zh,(key,block['id'],label)
                zh=zh.replace(label,match[1]+'{'+label+'}',1)
            assert visible_text(zh)==line,(key,block['id'],'Draft wording changed')
        assert not compare_html(block['en'],zh),(key,block['id'],compare_html(block['en'],zh))
        block.update(zh=zh,source='draft',basis='')
        mapping.append({'path':'entries.Barbarian.pages.Barbarian.'+field+'/'+block['id'],'en':block['en'],'draft':line,'zh':zh,'kind':kind,'source':'draft' if kind=='draft' else 'protected','source_lines':bounds,'source_original':original_source,'exact_visible_match':visible_text(zh)==line})
    assert next(text_iter,None) is None
save('sheet',sheet)

# The CLI only supports entry-level descriptions. Adapt journal fields in memory
# to call exactly the same skeleton provenance/structure validation, then restore
# the genuine pages payload. Do not change shared skill scripts or EN templates.
synthetic_drafts={key:norm(draft_path.read_text(encoding='utf-8')) for key in synthetic}
built=build_entries(sheet,synthetic,synthetic_drafts)['entries']
payload={'entries':{'Barbarian':{'name':name,'pages':{'Barbarian':{'name':name,'subclassHeader':subclass_header,'description':built['Barbarian.description']['description'],'subclass':built['Barbarian.subclass']['description']}}}}}
save('aligned',payload)
expected=dict(leaves(load('en-scope')))
actual=dict(leaves(payload))
assert set(expected)==set(actual) and count_strings(payload)==5
for path,zh in actual.items():
    en=expected[path]
    assert live[path]['source']==[en],(path,'Live EN changed')
    problems=check_description(en,zh)
    assert not problems,(path,problems)
    assert '它' not in visible_text(zh)
for path in ['entries.Barbarian.name','entries.Barbarian.pages.Barbarian.name','entries.Barbarian.pages.Barbarian.subclassHeader']:
    mapping.append({'path':path,'en':expected[path],'draft':actual[path],'zh':actual[path],'kind':'name' if path.endswith('.name') else 'heading','source':'draft','source_lines':[2,2] if path.endswith('.name') else [186,186],'source_original':source_lines[1] if path.endswith('.name') else source_lines[185],'exact_visible_match':True})
save('mapping-audit',mapping)
save('upload',payload)
digest=hashlib.sha256((HERE/(PREFIX+'.upload.json')).read_bytes()).hexdigest()
save('verification',{'version':'v1','book':'dnd-players-handbook','component':'content','entries':1,'pages':1,'strings':5,'blocks':13,'visible_blocks':11,'protected_embed_blocks':2,'mapped_fields':len(mapping),'all_exact_draft_matches':True,'live_en_match':True,'mechanical_pass':True,'adapter':'skeleton.build_entries + validate.check_description on every real nested field; CLI does not cover pages','sha256':digest,'draft_sha256':hashlib.sha256(draft_path.read_bytes()).hexdigest(),'approved':False,'uploaded':False})
print('1 journal entry / 1 page / 5 strings; 16 mapping positions (14 visible + 2 protected), exact draft matches; all nested paths validated; SHA-256 '+digest)
