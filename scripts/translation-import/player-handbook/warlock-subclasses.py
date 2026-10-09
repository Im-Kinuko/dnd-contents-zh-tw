"""Prepare all four Warlock subclasses together. No upload operations."""
import argparse, copy, difflib, hashlib, html, json, re, runpy, sys, contextlib, io
from pathlib import Path
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'_incoming/player-handbook'
DATA=BASE/'subclasses/warlock'
SK=ROOT/'.claude/skills/translation-import/scripts'
BOOK='dnd-players-handbook'
PREFIX='warlock-subclasses'
sys.path.insert(0,str(SK))
sys.stdout.reconfigure(encoding='utf-8')
sys.dont_write_bytecode=True
import weblate as w, opencc
from subclasses import read_all, leaves, english_text
from html_blocks import Plan, visible_text, compare_html
from skeleton import build_entries, draft_sections
KEYS=['Archfey Patron','Archfey Spells','Steps of the Fey','Misty Escape','Beguiling Defenses','Bewitching Magic','Celestial Patron','Celestial Spells','Healing Light','Radiant Soul','Celestial Resilience','Searing Vengeance','Fiend Patron','Fiend Spells',"Dark One's Blessing","Dark One's Own Luck",'Fiendish Resilience','Hurl Through Hell','Great Old One Patron','Great Old One Spells','Awakened Mind','Psychic Spells','Clairvoyant Combatant','Eldritch Hex','Thought Shield','Create Thrall']
PATRONS=[k for k in KEYS if k.endswith(' Patron')]
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def save(name,obj):
    DATA.mkdir(parents=True,exist_ok=True)
    (DATA/(PREFIX+'.'+name+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=1),encoding='utf-8')
def load(name):return read(DATA/(PREFIX+'.'+name+'.json'))
def write(name,text):
    DATA.mkdir(parents=True,exist_ok=True)
    (DATA/(PREFIX+'.'+name)).write_text(text.rstrip()+'\n',encoding='utf-8')
def tool(name,args):
    sys.argv=[str(SK/name),*args]
    try:runpy.run_path(str(SK/name),run_name='__main__')
    except SystemExit as exc:
        if exc.code:raise
def collect():
    source=(BASE/PREFIX).read_text(encoding='utf-8')
    write('source.txt',source);write('source.s2twp.txt',opencc.OpenCC('s2twp').convert(source))
    for comp in ['classes','content','tables','spells']:
        rows,audit=read_all(BOOK,BOOK+'-'+comp)
        save(comp+'.live',{'audit':audit,'units':{r['context']:r for r in rows}})
        print(comp,len(rows),'complete')
    for comp in ['terms','spells-glossary']:
        rows,audit=read_all('dnd-5e-2024-zh-tw',comp);save(comp+'.live',{'audit':audit,'units':rows});print(comp,len(rows),'complete')
    from build_index import entry_names, aliases
    idx={'terms':{r['source'][0]:r['target'][0] for r in load('terms.live')['units'] if any(r['target']) and r['target']!=r['source']},'spells_glossary':{r['source'][0]:r['target'][0] for r in load('spells-glossary.live')['units'] if any(r['target']) and r['target']!=r['source']},'entry_names':{k:dict(v) for k,v in entry_names(str(ROOT/'compendium/zh-tw'),BOOK).items()},'aliases':aliases(str(ROOT/'.claude/skills/translation-import/glossary.tsv'))}
    save('term_index',idx)
    tool('spell_names.py',['--out',str(DATA/(PREFIX+'.spell-names.json'))])
    entries=read(ROOT/f'compendium/en/{BOOK}/{BOOK}.classes.json')['entries']
    scope={k:entries[k] for k in KEYS}
    pages=read(ROOT/f'compendium/en/{BOOK}/{BOOK}.content.json')['entries']['Warlock']['pages']
    content={k:pages[k] for k in PATRONS}
    refs=set(re.findall(r'Compendium\.'+BOOK+r'\.tables\.(?:RollTable\.)?([A-Za-z0-9]+)',json.dumps([scope,content])))
    tables=read(ROOT/f'compendium/en/{BOOK}/{BOOK}.tables.json')['entries']
    scoped_tables={k:v for k,v in tables.items() if k in refs or v.get('id') in refs}
    save('scope',{'classes':scope,'content':content,'tables':scoped_tables,'table_refs':sorted(refs)})
    report=[]
    for comp,es in [('classes',scope),('content',content),('tables',scoped_tables)]:
        live=load(comp+'.live')['units']
        for k,e in es.items():
            report.append('\n### '+comp+' / '+k)
            prefix='entries.Warlock.pages.'+k+'.' if comp=='content' else 'entries.'+k+'.'
            for path,val in leaves(e):
                r=live.get(prefix+path)
                report.append(path+'\nEN: '+val+'\nZH: '+(r['target'][0] if r else '(missing API unit)'))
                if r:assert r['source'][0]==val,(prefix+path,'EN differs from live')
    write('inventory.txt','\n'.join(report));print('scope',len(scope),len(content),list(scoped_tables),'refs',refs)
def inspect():
    scope=load('scope');live=load('classes.live')['units']
    print('TERMS',json.dumps(load('term_index')['terms'],ensure_ascii=False))
    print('NAMES',json.dumps({k:v['target'][0] for k,v in live.items() if k.startswith('entries.Magical Cunning.') or k=='entries.Warlock.name'},ensure_ascii=False))
    print('SPELL FORMAT',json.dumps(load('spell-names'),ensure_ascii=False)[:600])
    for i,line in enumerate((DATA/(PREFIX+'.source.s2twp.txt')).read_text(encoding='utf-8').splitlines(),1):
        if line.strip():print(i,line)
    tables=read(ROOT/f'compendium/en/{BOOK}/{BOOK}.tables.json')['entries']
    print('TABLE CANDIDATES',[(k,v.get('name')) for k,v in tables.items() if re.search(r'warlock|archfey|celestial|fiend|old one|fey|patron',k,re.I)])
def related():
    content=read(ROOT/f'compendium/en/{BOOK}/{BOOK}.content.json')['entries']
    for k,e in content.items():
        for page,p in e.get('pages',{}).items():
            if page in PATRONS or any(s.lower() in page.lower() for s in ['archfey','celestial','fiend','old one']):print(k,page,json.dumps(p,ensure_ascii=False))
    tables=read(ROOT/f'compendium/en/{BOOK}/{BOOK}.tables.json')['entries']
    for k in ['Feywild Gifts','Fiendish Legacy']:print('TABLE',k,json.dumps(tables[k],ensure_ascii=False))
    live=load('content.live')['units']
    ids=re.findall(r'JournalEntryPage\.([A-Za-z0-9]+)',json.dumps(load('scope')['content']))
    for k,e in content.items():
        for page,p in e.get('pages',{}).items():
            if page in ids or p.get('id') in ids:
                print('ART',k,page,json.dumps(p,ensure_ascii=False))
                for path,val in live.items():
                    if path.startswith('entries.'+k+'.pages.'+page+'.'):print(path,val['source'],val['target'])
def search():
    scope=load('scope');queries=set()
    for k,e in scope['classes'].items():
        in_note=False
        for block in Plan(e.get('description','')).blocks:
            text=english_text(block.html)
            if 'Foundry Note' in text:in_note=True
            if in_note or any(s in text for s in ['activity','activities','automatically']):queries.add(text[:100])
        for path,val in leaves(e):
            if path not in ['name','description']:queries.add(english_text(val)[:100])
    result=load('supplement-search') if (DATA/(PREFIX+'.supplement-search.json')).exists() else []
    for phrase in sorted(queries):
        if any(r['query']==phrase for r in result):continue
        rows=[];audit=[];page=1
        while True:
            status,body=w.call('GET',f'/api/units/?q={quote(chr(34)+phrase+chr(34),safe="")}&page_size=1000&page={page}')
            assert status==200,(phrase,status)
            rows.extend(body['results']);audit.append({'page':page,'total':body['count'],'received':len(body['results'])})
            if not body.get('next'):assert len(rows)==body['count'];break
            page+=1
        translated=[r for r in rows if r['target']!=r['source'] and re.search('[一-鿿]',r['target'][0])]
        result.append({'query':phrase,'audit':audit,'units':rows})
        print(phrase,'matches',len(rows),'Chinese',[(r['context'],r['target'][0][:250]) for r in translated[:4]])
    save('supplement-search',result)
def verify_preview():
    verification=[]
    for comp in ['classes','content']:
        baseline=load(comp+'.live')['units'];rows,audit=read_all(BOOK,BOOK+'-'+comp);current={r['context']:r for r in rows}
        for path,row in baseline.items():
            assert current[path]['source']==row['source'] and current[path]['target']==row['target'],('Weblate changed; refresh preview required',comp,path)
        for path,value in leaves(load(comp+'.upload')):
            assert path in current,(comp,path)
            assert value!=current[path]['target'][0],(comp,path,'unchanged field must not be sent')
        verification.append({'component':comp,'verified_units':len(current),'source_and_target_unchanged':True,'pagination':audit})
        print(comp,len(current),'source and formal translations unchanged')
    for comp,digest in load('verification')['payload_sha256'].items():assert hashlib.sha256((DATA/(PREFIX+'.'+comp+'.upload.json')).read_bytes()).hexdigest()==digest
    if not load('pending').get('resolved'):assert load('pending')['path'] not in dict(leaves(load('classes.upload')))
    save('live-verification',{'verified':verification,'total_units':sum(r['verified_units'] for r in verification),'uploaded':False})
def clean_bytecode():
    import subprocess
    path='scripts/translation-import/player-handbook/__pycache__/subclasses.cpython-310.pyc'
    result=subprocess.run(['git','show','HEAD:'+path],cwd=ROOT,capture_output=True)
    assert result.returncode==0
    (ROOT/path).write_bytes(result.stdout)
    print('Restored incidental tracked bytecode; future runs disable bytecode writes.')
def refresh_provenance():
    # Metadata-only clarification; the frozen draft and verified payload stay identical.
    basis='原稿無此標題；依conventions已裁定Foundry註記及既有中文小標格式，寫【Foundry註記】。'
    for component in ['classes','content']:
        sheet=load(component+'.sheet')
        for row in sheet['entries'].values():
            for block in row['blocks']:
                if english_text(block['en'])=='Foundry Note':block['basis']=basis
        save(component+'.sheet',sheet)
    audit=load('audit')
    for row in audit:
        if english_text(row['en'])=='Foundry Note':row['basis']=basis
    save('audit',audit)
    print('Clarified established Foundry heading provenance; no text changes.')
def prepare():
    scope=load('scope');live=load('classes.live')['units']
    spell_names=load('spell-names');fallbacks=[]
    for k,e in scope['classes'].items():
        original=Plan(live['entries.'+k+'.description']['target'][0]).blocks;enblocks=Plan(e['description']).blocks
        if len(original)!=len(enblocks):continue
        for a,b in zip(enblocks,original):
            enlabels=re.findall(r'@UUID\[[^\]]+\]\{([^}]+)\}',a.html);zhlabels=re.findall(r'@UUID\[[^\]]+\]\{([^}]+)\}',b.html)
            for en,zh in zip(enlabels,zhlabels):
                if en not in spell_names and re.search('[一-鿿]',zh):spell_names[en]=zh;fallbacks.append({'en':en,'zh':zh,'basis':'Weblate現行法術名稱尚未翻譯，沿用此子職業既有表格標籤。'})
    save('effective-spell-names',spell_names);save('spell-name-fallbacks',fallbacks)
    maker=runpy.run_path(str(Path(__file__).with_name('warlock-subclasses-draft.py')))['make']
    source=(DATA/(PREFIX+'.source.s2twp.txt')).read_text(encoding='utf-8')
    names,main,supp,labels,conditions=maker(source,live,scope['classes'],visible_text,Plan,spell_names)
    labels['Taunted']='受到嘲弄'
    labels['Magical Cunning']=live['entries.Magical Cunning.name']['target'][0]
    draft=[];sheet={'schema_version':2,'book':BOOK,'component':'classes','entries':{}}
    metadata=[]
    bounds={'Archfey Patron':(2,4),'Archfey Spells':(7,24),'Steps of the Fey':(27,30),'Misty Escape':(33,36),'Beguiling Defenses':(39,40),'Bewitching Magic':(43,43),'Celestial Patron':(46,48),'Celestial Spells':(51,69),'Healing Light':(72,74),'Radiant Soul':(77,77),'Celestial Resilience':(80,80),'Searing Vengeance':(83,84),'Fiend Patron':(87,89),'Fiend Spells':(92,109),"Dark One's Blessing":(112,112),"Dark One's Own Luck":(115,116),'Fiendish Resilience':(119,119),'Hurl Through Hell':(122,123),'Great Old One Patron':(126,128),'Great Old One Spells':(131,148),'Awakened Mind':(151,152),'Psychic Spells':(155,155),'Clairvoyant Combatant':(158,159),'Eldritch Hex':(162,162),'Thought Shield':(165,165),'Create Thrall':(168,169)}
    for k,e in scope['classes'].items():
        zhblocks=main[k]+supp.get(k,[]);blocks=Plan(e['description']).blocks
        assert len(zhblocks)==len(blocks),(k,len(zhblocks),len(blocks))
        row={'name_en':k,'name':names[k],'blocks':[]}
        oldblocks=Plan(live['entries.'+k+'.description']['target'][0]).blocks
        for i,(b,t) in enumerate(zip(blocks,zhblocks)):
            supplement=i>=len(main[k]);basis='原稿無Foundry註記；已搜尋Weblate，未找到同句完整中文；依EN、現行介面詞補翻。' if supplement else ''
            if supplement and english_text(b.html)=='Foundry Note':basis='原稿無此標題；依conventions已裁定Foundry註記及既有中文小標格式，寫【Foundry註記】。'
            oldtext=visible_text(oldblocks[i].html) if len(oldblocks)==len(blocks) else ''
            accepted=bool(re.search('[一-鿿]',oldtext)) and not re.search('[A-Za-z]{3,}',oldtext)
            row['blocks'].append({'id':b.id,'en':b.html,'zh':'','source':'supplement' if supplement else 'draft','basis':basis,'draft_text':t,'origin':'Weblate既有譯文' if accepted else '原稿','source_lines':list(bounds[k]),'old':oldtext})
        for field in ['activities','effects','advancement']:
            if field not in e:continue
            row[field]=copy.deepcopy(e[field])
            for item,fields in row[field].items():
                for sub,value in fields.items():
                    path=f'entries.{k}.{field}.{item}.{sub}';old=live[path]['target'][0]
                    if re.search('[一-鿿]',old) and not re.search('[A-Za-z]{3,}',visible_text(old)):
                        new=old;basis='Weblate現行既有譯文，照舊。'
                    elif sub=='description':
                        new='<p>'+ (main['Thought Shield'][0] if k=='Thought Shield' else conditions[english_text(value)])+'</p>';basis='依正文與EN補翻效果摘要。'
                    elif value in labels:new=labels[value];basis='沿用現行條目名、已翻正文子標或介面詞；缺詞自譯。'
                    elif value in conditions:new=conditions[value];basis='依EN條件／目標補翻，沿用正文與已定句式。'
                    elif value.startswith('Your patron teaches'):new=main['Beguiling Defenses'][0];basis='沿用此特性底稿。'
                    elif value.startswith('Your link to your patron'):new=main['Radiant Soul'][0].split('每回合一次')[0];basis='沿用此特性底稿的抗力段。'
                    else:raise ValueError((path,value))
                    fields[sub]=new;metadata.append({'component':'classes','path':path,'en':value,'old':old,'zh':new,'basis':basis})
        sheet['entries'][k]=row
        draft.append('### '+k+'\n名稱：'+names[k]+'\n'+'\n'.join(main[k])+'\n〔EN 補翻／獨立介面欄位〕\n'+'\n'.join(supp.get(k,[]))+'\n'+'\n'.join(p+'：'+v for p,v in leaves({f:row[f] for f in ['activities','effects','advancement'] if f in row})))
    content_sheet={'schema_version':2,'book':BOOK,'component':'content','entries':{}}
    virtual={}
    for k,e in scope['content'].items():
        key=k+' journal';virtual[key]=e;blocks=Plan(e['description']).blocks
        plain=[blocks[0].html,*main[k]]
        plain[-1]=plain[-1].rstrip('。')+'（'+names[k]+'子職業）。'
        content_sheet['entries'][key]={'name_en':k,'name':names[k],'blocks':[{'id':b.id,'en':b.html,'zh':'','source':'supplement' if i==0 else 'draft','basis':'原稿無圖片嵌入指令；保留EN的Embed。' if i==0 else '', 'draft_text':t,'origin':'原稿／已審定classes正文','source_lines':list(bounds[k]),'old':english_text(b.html)} for i,(b,t) in enumerate(zip(blocks,plain))]}
        draft.append('### '+key+'\n名稱：'+names[k]+'\n'+'\n'.join(plain[1:])+'\n〔EN 補翻／圖片指令〕\n'+plain[0])
    extra={};content=read(ROOT/f'compendium/en/{BOOK}/{BOOK}.content.json')['entries'];clive=load('content.live')['units']
    for journal,page_keys in [('Appendix D: Rule References',[k for k in KEYS if k.endswith(' Spells') and k!='Psychic Spells']),('phbCh3ArtHandout',['Archfey','Celestial','Fiend','Great Old One'])]:
        extra[journal]={'pages':{}}
        for page in page_keys:
            e=content[journal]['pages'][page];assert list(e)==['name']
            path=f'entries.{journal}.pages.{page}.name';r=clive[path];assert r['source'][0]==e['name']
            new=r['target'][0] if re.search('[一-鿿]',r['target'][0]) else names.get(page,names.get(page+' Patron'))
            extra[journal]['pages'][page]={'name':new};metadata.append({'component':'content','path':path,'en':e['name'],'old':r['target'][0],'zh':new,'basis':'沿用對應子職業／法術表名稱；圖像標題依子職業名。'})
    save('classes.sheet',sheet);save('content.sheet',content_sheet);save('content.virtual-en',virtual);save('content.extra',extra);save('metadata',metadata);save('labels',labels)
    write('draft.txt','\n\n'.join(draft));save('draft-fingerprint',{'sha256':hashlib.sha256((DATA/(PREFIX+'.draft.txt')).read_bytes()).hexdigest()})
    # Keep the raw source and the exact accepted text as independent comparison sources.
    sourcecheck=[]
    for k in KEYS:
        a,b=bounds[k];raw=[x for x in source.splitlines()[a-1:b] if x.strip()]
        accepted=[visible_text(b.html) for b in Plan(live['entries.'+k+'.description']['target'][0]).blocks if re.search('[一-鿿]',visible_text(b.html)) and not re.search('[A-Za-z]{3,}',visible_text(b.html))]
        sourcecheck.append(names[k]+' '+k+'\n'+'\n'.join(raw+accepted))
        if k in PATRONS:sourcecheck.append(names[k]+' '+k+' journal\n'+'\n'.join(raw+accepted))
    write('source.segmented.s2twp.txt','\n\n'.join(sourcecheck))
    save('bounds',bounds)
    audit=copy.deepcopy(sheet)
    for key,row in audit['entries'].items():
        row['blocks'].append({'id':'name-audit','en':key})
        for field in ['activities','effects','advancement']:
            if field in row:row[field]=copy.deepcopy(scope['classes'][key][field])
    audit['entries'].update(content_sheet['entries']);save('audit.sheet',audit)
    ack={k+'|reach':'reach a Warlock level表示達到契術師等級，非武器觸及；沿用既有正文「達到」。' for k in KEYS if k.endswith(' Spells') and k!='Psychic Spells'}
    ack.update({k+'|reach':'升級提示的reach表示達到契術師等級，非武器觸及；沿用既有提示「達到」。' for k in PATRONS})
    ack['Beguiling Defenses|take']='四個take含一個take a Reaction，依裁定譯採取反應，其餘傷害義皆譯承受。'
    ack['Celestial Patron|Archfey']='此升級提示誤寫Archfey Spells；正文是Celestial Spells，既有中文天界法術已正確。依2026-10-05使用者裁定：提示與正文矛盾時依正文；保留既有譯文並報告上游錯誤。'
    save('ack',ack)
    print('Draft prepared',len(sheet['entries']),len(content_sheet['entries']),'extra',len(metadata))
def markup(text,en,k):
    labels=load('labels');spells=load('effective-spell-names')
    result=text
    if '[[lookup' in en:
        macro=re.search(r'\[\[lookup[^\]]+\]\]',en)[0]
        result=result.replace('當前魅力調整值','當前'+macro,1)
    atoms=[]
    # The two UI spans include icon-only em elements; preserve their exact classes and nesting.
    for match in re.finditer(r'<span class="reference">.*?</span>',en,re.S):
        raw=match[0];label='應用半傷' if 'Apply Half Damage' in raw else '應用'
        zh=raw.replace('Apply Half Damage','應用半傷').replace('Apply</span>','應用</span>');atoms.append((label,zh))
    cleaned=re.sub(r'<span class="reference">.*?</span>','',en,flags=re.S)
    for match in re.finditer(r'@UUID\[([^\]]+)\](?:\{([^}]+)\})?',cleaned):
        name=match[2];zh=spells.get(name,labels.get(name));assert zh,(k,match[0]);atoms.append((zh,'@UUID['+match[1]+']{'+zh+'}'))
    for match in re.finditer(r'&(?:amp;)?Reference\[([^\]]+)\](?:\{[^}]*\})?',cleaned):
        zh={'Invisible':'隱形','Charmed':'魅惑','Prone':'伏地','Blinded':'目盲','Incapacitated':'失能'}[match[1]];atoms.append((zh,match[0].split(']')[0]+']{'+zh+'}'))
    for match in re.finditer(r'<(strong|em)>([^<]+)</\1>',cleaned):
        name=match[2].strip().rstrip('.').strip();label=labels.get(name,spells.get(name));assert label,(k,name)
        if text.startswith('【'+label+'】'):label='【'+label+'】'
        atoms.append((label,'<'+match[1]+'>'+label+'</'+match[1]+'>'))
    placeholders={}
    for i,(label,raw) in enumerate(atoms):
        assert label in result,(k,label,result,en)
        token='\x01'+str(i)+'\x02';result=result.replace(label,token,1);placeholders[token]=raw
    for token,raw in placeholders.items():result=result.replace(token,raw)
    return result
def map_draft():
    assert load('draft-fingerprint')['sha256']==hashlib.sha256((DATA/(PREFIX+'.draft.txt')).read_bytes()).hexdigest()
    drafts=draft_sections(DATA/(PREFIX+'.draft.txt'))
    for component in ['classes','content']:
        sheet=load(component+'.sheet');entries=load('scope')['classes'] if component=='classes' else load('content.virtual-en')
        for k,row in sheet['entries'].items():
            for b in row['blocks']:
                b['zh']=markup(b['draft_text'],b['en'],k)
                # Unlabelled lookup macros may not appear in visible_text: explain this narrowly.
                if '[[lookup' in b['en']:b['source']='supplement';b['basis']='原稿無Foundry lookup巨集；保留EN巨集原樣，正文以Weblate既有譯文為底，只修單位／已定句式。'
        save(component+'.sheet',sheet)
        aligned=build_entries(sheet,entries,drafts)
        if component=='content':
            pages={k.removesuffix(' journal'):v for k,v in aligned['entries'].items()}
            aligned={'entries':{'Warlock':{'pages':pages},**load('content.extra')}}
        save(component+'.aligned',aligned)
    print('Mapped from frozen draft')
def checks():
    checks={}
    def run(name,args,log):
        class Buffer(io.StringIO):
            def reconfigure(self,**kwargs):pass
        buf=Buffer();code=0
        with contextlib.redirect_stdout(buf),contextlib.redirect_stderr(buf):
            try:tool(name,args)
            except SystemExit as exc:code=exc.code
        write(log,buf.getvalue());print(name,'exit',code,buf.getvalue()[-400:]);checks[name]=code
    path=lambda suffix:str(DATA/(PREFIX+'.'+suffix))
    run('draft_diff.py',['--source',path('source.segmented.s2twp.txt'),'--draft',path('draft.txt'),'--out',path('draft-diff.md')],'draft-diff.log.txt')
    run('terms_check.py',[path('audit.sheet.json'),'--draft',path('draft.txt'),'--index',path('term_index.json'),'--names',path('effective-spell-names.json'),'--ack',path('ack.json'),'--out',path('terms-report.md')],'terms.log.txt')
    run('lang_compare.py',[path('audit.sheet.json'),'--draft',path('draft.txt')],'lang-report.md')
    run('validate.py',[path('classes.aligned.json'),'--book',BOOK,'--component','classes','--allow','Active,Effect','--out',path('classes.validated.json')],'validation.txt')
    save('checks',checks)
def review():
    from validate import check_description, check_subfields, count_strings
    from draft_diff import best_match, fragments, source_sections, norm_name, draft_sections as diff_sections
    assert all(v==0 for v in load('checks').values()),load('checks')
    full={c:load(c+'.aligned') for c in ['classes','content']}
    assert full['classes']==load('classes.validated')
    english=read(ROOT/f'compendium/en/{BOOK}/{BOOK}.content.json')['entries']
    for journal,value in full['content']['entries'].items():
        for page,fields in value['pages'].items():
            for sub,zh in fields.items():
                en=english[journal]['pages'][page][sub];errors=check_description(en,zh,{'Foundry','Active','Effect'}) if sub=='description' else []
                assert not errors,(journal,page,errors)
    source=(DATA/(PREFIX+'.source.s2twp.txt')).read_text(encoding='utf-8').splitlines()
    audit=[];preserved=[];changed={c:{'entries':{}} for c in full}
    def delta(new,live,prefix,component):
        out={}
        for key,value in new.items():
            if isinstance(value,dict):
                part=delta(value,live,prefix+'.'+key if prefix else key,component)
                if part:out[key]=part
            else:
                row=live[prefix+'.'+key];old=row['target'][0]
                if value==old:preserved.append({'component':component,'path':prefix+'.'+key,'value':value})
                else:out[key]=value
        return out
    for c in full:
        changed[c]=delta(full[c],load(c+'.live')['units'],'',c)
    # This condition has an unresolved upstream spell-name contradiction; keep both proposals out of the payload.
    resolved=(DATA/(PREFIX+'.approval-revision.json')).exists()
    pending=changed['classes']['entries']['Create Thrall']['activities']['Thrall Temporary HP'].get('condition')
    if not resolved:changed['classes']['entries']['Create Thrall']['activities']['Thrall Temporary HP'].pop('condition')
    else:assert pending=='當你不需專注施放異怪召喚術時'
    save('pending',{'path':'entries.Create Thrall.activities.Thrall Temporary HP.condition','en':'When you cast Hex without Concentration','literal':'當你不需專注施放脆弱詛咒時','recommended':'當你不需專注施放異怪召喚術時','resolved':resolved,'status':'使用者確認依正文修正，已列入payload' if resolved else '等待使用者裁定，兩方案均未列入payload'})
    for c in full:
        save(c+'.upload',changed[c])
    print('PAYLOAD',[(c,count_strings(changed[c])) for c in full])
    for c in ['classes','content']:
        sheet=load(c+'.sheet')
        for k,row in sheet['entries'].items():
            key=k.removesuffix(' journal');live=load(c+'.live')['units'];prefix=f'entries.Warlock.pages.{key}.' if c=='content' else f'entries.{key}.'
            liveblocks=Plan(live[prefix+'description']['target'][0]).blocks
            for i,b in enumerate(row['blocks']):
                a,z=b['source_lines'];raw=source[a-1:z]
                ratio,start,end,match=best_match(b['draft_text'],raw) if b['source']=='draft' else (0,None,None,'')
                existing=liveblocks[i].html if len(liveblocks)==len(row['blocks']) else ''
                existingtext=english_text(existing)
                base=b['old'] if b['origin']=='Weblate既有譯文' else match
                reason='無修改' if base==b['draft_text'] else reason_for(key,b['draft_text'],b['en'],base)
                audit.append({'component':c,'path':prefix+'description/'+b['id'],'en':b['en'],'source_lines':[a,z],'source':match or '\n'.join(raw),'existing':existing,'draft':b['draft_text'],'zh':b['zh'],'basis':b['basis'],'origin':b['origin'],'modifications':fragments(base,b['draft_text']),'reason':reason,'retained_html':bool(existing and existing==b['zh'])})
    # Register the exact fragments output by the independent draft-diff tool.
    raw_sections=source_sections(DATA/(PREFIX+'.source.segmented.s2twp.txt'));draft_pars=diff_sections(DATA/(PREFIX+'.draft.txt'));registry=[]
    for k,pars in draft_pars.items():
        src=raw_sections[norm_name(k)]
        for i,new in enumerate(pars,1):
            ratio,a,b,old=best_match(new,src)
            registry.append({'entry':k,'paragraph':i,'ratio':ratio,'source':old,'draft':new,'fragments':fragments(old,new),'reason':reason_for(k.removesuffix(' journal'),new,'',old)})
    save('fragment-register',registry);save('audit',audit);save('preserved',preserved)
    allowed={'Foundry','Active','Effect','DC'}
    for c in full:
        for path,val in leaves(full[c]):
            assert not re.search('它|如果|發充能|施展',visible_text(val)),path
            assert not [s for s in re.findall('[A-Za-z]{3,}',visible_text(val)) if s not in allowed],(path,val)
    hashes={c:hashlib.sha256((DATA/(PREFIX+'.'+c+'.upload.json')).read_bytes()).hexdigest() for c in full}
    save('verification',{'date':'2026-10-09','version':'v2' if resolved else 'v1','classes_entries':len(full['classes']['entries']),'classes_full_strings':count_strings(full['classes']),'classes_upload_strings':count_strings(changed['classes']),'content_pages':sum(len(e['pages']) for e in full['content']['entries'].values()),'content_full_strings':count_strings(full['content']),'content_upload_strings':count_strings(changed['content']),'preserved_strings':len(preserved),'body_blocks':len(audit),'payload_sha256':hashes,'checks':load('checks'),'content_mechanical_pass':True,'nested_reviewed':True,'approved':resolved,'uploaded':False,'pending':[] if resolved else ['Create Thrall.activities.Thrall Temporary HP.condition']})
    print(json.dumps(load('verification'),ensure_ascii=False))
def reason_for(k,new,en,old):
    notes={
      'Archfey Patron':'沿用原稿；content僅補EN的子職業UUID標籤。',
      'Celestial Patron':'規則語意：EN為體驗到些許聖潔輝光，原稿「沐浴在…之下」改為「體驗到些許…」；其餘沿用，content補子職業UUID標籤。',
      'Fiend Patron':'規則漏譯：原稿缺少「你的道路取決於抵抗宗主目標的程度」，依EN補上；content補子職業UUID標籤。',
      'Great Old One Patron':'既有正文照舊；原稿「擇取一位」與EN「不束縛於單一存在」不同，既有譯文已正確處理；content僅補子職業UUID標籤。',
      'Steps of the Fey':'規則／句式：振奮步伐補單一生物、明寫以自己為中心10呎；嘲弄步伐修離開空間的5呎範圍、按已定句式寫直到下回合開始。既有前兩段照舊。',
      'Misty Escape':'定案詞／句式：施放、承受、採取反應、下列、成功通過、呎、進入隱形；名稱沿用原稿但振奮步伐沿用既有。',
      'Beguiling Defenses':'規則：EN觸發是可見生物而非僅敵人，減半的是你承受的傷害；定案詞／句式：緊接在…後、採取反應、承受、直到完成長休前。',
      'Bewitching Magic':'規則時點：緊接在消耗法術位施放惑控／幻術學派法術後，同一動作中施放迷蹤步；定案詞／句式：學派、施放、不消耗法術位、以動作的一部分。',
      'Healing Light':'既有正文為底，只將作為附贈動作改為已裁定的採取附贈動作；原稿73、74行依EN合併，治療池、上限與長休恢復保留。',
      'Radiant Soul':'定案詞：施放、傷害抗力；保留原稿每回合一次及單一法術目標的限制。',
      'Celestial Resilience':'定案詞：祕法迴流、契術師、等同於、你所能看見；保留等級＋魅力與半等級＋魅力及至多五個生物。',
      'Searing Vengeance':'定案詞／轉換修正：呎、等同於、承受、伏地、直到完成長休前；其餘依原稿，保留60呎／30呎、半生命值上限、2d8＋魅力與當前回合末。',
      "Dark One's Blessing":'既有正文照舊；新介面條件依EN補翻。',
      "Dark One's Own Luck":'規則：before any effects為任何擲骰效應生效前、per roll為每次擲骰，不只檢定；定案詞：等同於。',
      'Fiendish Resilience':'轉換修正：型別→類型；定案詞：傷害抗力。名稱邪魔韌性沿用既有，不用原稿邪魔體魄。',
      'Hurl Through Hell':'定案詞／句式／禁用字：成功通過、承受、呎、失能、下回合結束前、直到完成長休前、它→目標。豁免失敗的條件與非邪魔才承受8d10保留。',
      'Awakened Mind':'轉換修正：30尺→30呎；句式：採取附贈動作；巨集：移除舊譯多加的哩，lookup原樣保留，底稿用明文魅力調整值表示。',
      'Psychic Spells':'既有正文照舊；現行聲音／姿勢構材、惑控／幻術學派用字保留。',
      'Clairvoyant Combatant':'規則：既有智力豁免修正為EN的感知豁免；其餘已譯正文照舊。',
      'Eldritch Hex':'定案詞：施放、現行法術名脆弱詛咒；原稿的屬性豁免劣勢限制保留。',
      'Thought Shield':'定案詞：傷害抗力、承受；原稿思維保護與等量反傷保留。',
      'Create Thrall':'定案詞：施放、契術師、等同於、現行法術名；保留1分鐘、免專注、臨時生命值與每回合首次命中被脆弱詛咒影響生物的額外傷害。'}
    if k.endswith(' Spells') and k!='Psychic Spells':return '定案詞／補漏：法術名依Weblate現行名稱，法術表保留既有譯文與排序，Spells表頭補為法術；英文法術名移至索引，不加入可見正文。'
    return notes[k]
def preview():
    info=load('verification');audit=load('audit');meta=load('metadata');reg=load('fragment-register');full={c:load(c+'.aligned') for c in ['classes','content']}
    table=lambda s:str(s).replace('|','&#124;').replace('\n','<br>')
    link=lambda suffix,label:f'[{label}](<{str(DATA/(PREFIX+"."+suffix)).replace(chr(92),"/")}>)'
    sourcepath=str(DATA/(PREFIX+'.source.s2twp.txt')).replace('\\','/')
    v=['# 契術師四個子職業：完整預覽 v1','','2026-10-09。尚未上傳。依使用者指示不拆批，四個子職業及相關content一次處理。',
       '',f'完整範圍：26個classes條目、{info["content_pages"]}個content頁面（4正文＋4附錄法術表標題＋4插圖標題），共141字串。保留{info["preserved_strings"]}個既有全欄位；待送classes {info["classes_upload_strings"]}＋content {info["content_upload_strings"]}＝113字串；1個有上游矛盾的行動條件留在pending，未放入payload。',
       '', '## 1. 檔案與確認版本','','- '+link('source.s2twp.txt','原稿轉繁，原行號保留')+'；原檔為 `_incoming/player-handbook/warlock-subclasses`。',
       '- '+link('draft.txt','獨立中文底稿')+'；'+link('reading.html','中文通讀版')+'。',
       '- '+link('classes.sheet.json','classes區塊映射')+'；'+link('content.sheet.json','content區塊映射')+'。',
       '- '+link('classes.upload.json','classes payload')+'；'+link('content.upload.json','content payload')+'；'+link('pending.json','待裁定欄位（未送）')+'。',
       '- '+link('verification.json','驗收數據')+'；'+link('fragment-register.json','全部差異片段與理由')+'；'+link('supplement-search.json','Weblate搜尋證據')+'。',
       '',*[c+' SHA-256：`'+h+'`。' for c,h in info['payload_sha256'].items()],
       '', '## 2. 來源、範圍與保留策略','','Weblate全量分頁核實：classes 2270、content 1161、tables 282、spells 1695、terms 137、spells-glossary 640；皆HTTP200、分頁總數吻合。現行法術名稱取得374筆，天界召喚術的名稱欄尚未翻譯，沿用同表已有標籤「天界召喚術」，沒有自行改名。交付前重新讀取3431個classes／content單元，source與正式target全部未變；證據見 '+link('live-verification.json','交付前核對')+'。',
       '', '原稿26條全有對應，整條無原稿0條。原稿每段保留在原檔及分節檔；已譯正文以現行Weblate為底，不為改善文風重寫。所有名稱、獨立介面欄位與补翻均在下表；有原稿正文不得以補翻分類避開底稿。含無標籤lookup巨集的單一區塊另記技術例外，正文仍取自底稿。'.replace('补','補'),
       '', '四子職業及正文均未引用骰表。名稱相近的「Feywild Gifts」為遊俠Fey Wanderer Spells所引用；「Fiendish Legacy」為提夫林傳承，均不屬於此次範圍。四份子職業法術表已包含在classes description，11／12／10／10個法術的名稱標籤全核對。content插圖Embed目標與參數原樣保留；附錄只有name可翻，未虛構描述欄位。',
       '', '| EN key | 既有／採用名稱 | 原稿行號 |','|---|---|---|']
    for k,(a,b) in load('bounds').items():v.append(f'| {k} | {full["classes"]["entries"][k]["name"]} | {a}–{b} |')
    v+=['','## 3. 全部正文區塊對照','',f'共{len(audit)}個區塊，包含4個純圖片Embed。原稿欄保留來源原文；既有譯文欄提供實際現行HTML；底稿欄是映射前中文。無變更的HTML列「原HTML保留」。','','| 欄位／區塊 | EN原文 | 原稿與行號 | 既有譯文 | 底稿 | 修改／類別／理由 |','|---|---|---|---|---|---|']
    for r in audit:
        reason=r['basis'] or r['reason'];mods='；'.join(r['modifications'])
        if r['retained_html']:reason='原HTML保留；'+reason
        v.append('| '+' | '.join(table(x) for x in [r['path'],r['en'],str(r['source_lines'])+' '+r['source'],r['existing'],r['draft'],mods+'；'+reason])+' |')
    v+=['','### 名稱與所有嵌套欄位','','| 路徑 | EN | 既有譯文 | 底稿／採用 | 修改與來源 |','|---|---|---|---|---|']
    live=load('classes.live')['units'];src=(DATA/(PREFIX+'.source.s2twp.txt')).read_text(encoding='utf-8').splitlines()
    for k,e in full['classes']['entries'].items():
        header=next(line for line in src if line.endswith(k));old=live['entries.'+k+'.name']['target'][0]
        v.append('| '+' | '.join(table(x) for x in ['entries.'+k+'.name',k,old,e['name'],'既有名稱照舊。原稿標題：'+header if old==e['name'] else '原稿標題為底；現行名稱仍是英文。原稿：'+header])+' |')
    for k,e in full['content']['entries']['Warlock']['pages'].items():v.append('| '+' | '.join(table(x) for x in [f'entries.Warlock.pages.{k}.name',k,k,e['name'],'沿用classes名稱，原稿有對應'])+' |')
    for r in meta:v.append('| '+' | '.join(table(x) for x in [r['path'],r['en'],r['old'],r['zh'],r['basis']+(' 此欄待裁定，未放入payload。' if r['path']==load('pending')['path'] else '')])+' |')
    v+=['','### draft_diff全部修改片段','','以下登記包含既有譯文作為可保留來源的比對；獨立原稿仍完整保留，沒有把新底稿倒寫成原稿。所有「改動大」段落附理由。','','| 條目／段 | 相似度 | 對應來源 | 底稿 | 全部差異片段 | 類別／理由 |','|---|---|---|---|---|---|']
    for r in reg:
        if r['fragments']:v.append('| '+' | '.join(table(x) for x in [r['entry']+'/'+str(r['paragraph']),f'{r["ratio"]:.2f}',r['source'],r['draft'],'；'.join(r['fragments']),r['reason']])+' |')
    differences=[
      ('洞若觀火：既有譯文豁免屬性錯誤','Wisdom saving throw','既有：智力豁免；原稿158行：感知豁免。','只把智力改感知，其餘已譯正文保留。'),
      ('振奮步伐：單一目標及距離中心','you or one creature you can see within 10 feet of yourself','既有：你或10呎內你所能看見的生物。','補「位於你…一名」，避免被讀為多個生物。'),
      ('嘲弄步伐：空間周圍的範圍','Creatures within 5 feet of the space you left','既有：位於你傳送前5呎空間內的生物。','修為「位於你離開的空間5呎內」，持續到施放者下回合開始。'),
      ('斗轉星移：觸發對象及傷害','a creature you can see hits you with an attack roll; reduce the damage you take by half','原稿40行：你能看見的敵人；該次攻擊的傷害减半。'.replace('减','減'),'EN未限敵人；改為可見生物、明寫減半你承受的傷害。'),
      ('醉心魔法：明確的施放後時點','Immediately after you cast an Enchantment or Illusion spell using an action and a spell slot','原稿43行：當你…施展…時，立刻施展迷蹤步。','緊接在施放後，同一動作中且不消耗另一法術位，補正式學派詞。'),
      ('天界宗主：光輝程度','experience a hint of the holy light','原稿48行：沐浴在…聖潔輝光之下。','改為體驗到些許聖潔輝光，保留原稿其他敘述。'),
      ('邪魔宗主：漏譯末句','your path is defined by the extent to which you strive against those aims','原稿89行缺少此句。','補「你的道路，取決於你在多大程度上努力對抗那些目標」。'),
      ('黑暗強運：擲骰效應與上限','before any of the roll’s effects occur; no more than once per roll','原稿115–116行：其結果生效前；一次檢定一次。','改為任何擲骰效應生效前、每次擲骰一次，涵蓋豁免骰。'),
      ('舊日支配者宗主：原稿與EN矛盾','invoke several entities without yoking yourself to one','原稿128行：並擇取一位，與之結合。','既有譯文已寫「並沒有束縛在單一存在上」，因此保留既有正確譯文。'),
      ('天界法術升級提示：EN誤寫法術表','when you reach a Warlock level specified in the Archfey Spells table','既有中文：天界法術表；原稿51行／正式正文也是天界法術。','既有譯文已正確，原樣保留；依2026-10-05提示依正文裁定。'),
      ('創造奴僕：行動條件與正文矛盾','When you cast Hex without Concentration','原稿168行／正文：Summon Aberration不需專注；不是Hex。','保留两方案在pending，未列入payload，等待使用者裁定。'.replace('两','兩')),
      ('驚懼步伐：range欄比正文狹窄','Of the space you just left; body: the space you left or the space you appear in (your choice)','原稿36行：傳送前或傳送後的空間（由你選擇）。','正文完整保留兩處擇一；range欄照EN「你剛離開的空間周圍」，報告此上游欄位限制。'),
      ('最新EN刪去旧註記'.replace('旧','舊'),'Misty Escape / Eldritch Hex current description has no extra spell-grant note','既有中文（仍英文）多一段The spell is granted…／automatically added…。','按現行EN骨架不加入兩段已刪去註記，其餘現存Foundry註記全翻。'),
    ]
    v+=['','## 4. 規則差異、既有修正及英文上游疑點','','| 問題 | EN原句 | 原稿／既有原句 | 處理 |','|---|---|---|---|']+[ '| '+' | '.join(table(x) for x in r)+' |' for r in differences]
    v+=['','## 5. 保留項','','| EN／原稿差異 | 保留理由 |','|---|---|',
      '| 原稿Archfey紹介多「神秘的妖精國度」，Gloaming／Summer譯薄暮／仲夏。 | 敘事不影響規則，沿用原稿；未另造人名。 |',
      '| Fey favors and debts原稿寫好感與人情；inscrutable and whimsical原稿寫難以理解、不可理喻。 | 原稿通順，保留其敘事語氣；未為文風改写。 |'.replace('写','寫'),
      '| Celestial／Fiend原稿另有「當你選擇此子職時」與「結識」。 | 未影響規則；依原稿保留。 |',
      '| Lower Planes, realms of perdition原稿寫邪魔之鄉。 | 敘事差異保留；末句的原稿缺漏已補。 |',
      '| Great Old One既有你便與…對應EN you might bind，密傳多多少少對應nevertheless。 | 既有敘事小差異照舊；原稿擇一的矛盾不帶入。 |',
      '| 名稱原稿天界韌性／邪魔體魄／銳眼鬥士／黑暗賜福；現行天族韌性／邪魔韌性／洞若觀火／黑暗者賜福。 | 名稱沿用Weblate現行，未因原稿不同改名。 |',
      '| 原稿Refreshing Step復甦步伐；現行振奮步伐。 | 沿用既有已譯小標，同步行動與Foundry註記。 |',
      '| Archfey Spells既有首段無句末句號。 | 無規則差異，依「已翻照舊」保留。 |',
      '| Thought Shield名稱保留盾，Radiant Soul保留魂。 | 為名稱，不套lang的裝備盾牌／其他語境。 |',
      '', '## 6. 術語與lang報告','', (DATA/(PREFIX+'.terms-report.md')).read_text(encoding='utf-8'), '', 'ack逐條：','']
    for k,reason in load('ack').items():v.append('- '+k+'：'+reason)
    lang=(DATA/(PREFIX+'.lang-report.md')).read_text(encoding='utf-8');missing=[]
    for line in lang.splitlines():
        if '| 無 |' in line:missing.append(line.split('|')[1].strip())
    lang_reasons={'additional effects':'正文沿用額外效果，非附魔子效果介面。','always':'規則正文始終準備，非戰鬥設定總是。','attack roll':'terms已定攻擊檢定。','blessing':'現行名稱賜福；非超自然贈禮類型祝福。','bolt':'Guiding Bolt為光導箭法術，非彈藥弩矢。','change':'沿用原稿改為／修改，非效果欄位變更。','creatures':'{number}是介面佔位模板，正文按實際主體寫生物。','current':'保留既有當前，非進度或數值欄名稱。','dark':'黑暗為名稱，非深色主題。','dice':'本文骰子／骰池，非比例骰值欄。','each creature':'修飾語中插入由你選擇，不要求字串每個生物連續。','each turn':'原稿每個回合／每回合，語意完整。','end of your next turn':'依已定句式直到下個回合結束前。','faith':'Guardian of Faith現行法術名虔誠守衛。','half damage':'介面Apply Half Damage按已定應用半傷；正文傷害減半。','hint':'hint沒有作為可見正文單字；是API欄位名。','light':'治癒之光／Light光亮術是光，非輕甲或主題。','minimum':'正文至少／最少，非數值欄最小值。','next':'下回合，非下一步／下一頁。','night':'Night Hag沿用原稿夜鬼婆，未改名。','points':'生命值，非屬性點數。','prepared':'始終準備，非介面已準備。','reach':'達到等級，非武器觸及；ack已登記。','reference':'API／連結名稱不是正文參照說明。','rest':'正文短休／長休，非一般動作類別休息。','round':'round down為向下取整，非回合輪。','scale':'調整骰數，非比例值名。','selected':'選取指示物的動作，非狀態已選取。','shield':'名稱思維之盾，非裝備盾牌。','start of your next turn':'已定直到下個回合開始，不加時。','summer':'原稿專名仲夏王庭，不拆譯為夏。','temporary':'臨時生命值，非效果狀態暫時。','temporary hp':'完整寫臨時生命值，不用介面縮寫HP。','three':'僅Embed屬性classes="three right"，原樣保留。','total':'擲骰總和，非掩蔽全掩蔽。','verbal':'2026-10-09裁定聲音構材；原有聲音／姿勢構材照舊。','wall':'Wall of Fire火牆術，非法術目標範本牆面。'}
    assert not set(missing)-set(lang_reasons),set(missing)-set(lang_reasons)
    v+=['',lang,'',f'lang的「無」共{len(missing)}項，逐項說明：','','| EN | 理由 |','|---|---|']+['| '+k+' | '+lang_reasons[k]+' |' for k in missing]
    v+=['','## 7. 限定詞逐句核對','','| EN限定詞 | 核對结果 |','|---|---|'.replace('结果','結果'),
      '| this／that spell | 指迷蹤步或同一前述法術，底稿該／此指涉保留。 |',
      '| one creature／one of the spell’s targets | 振奮步伐一名；治癒之光一個；光耀之魂其中一個目標。 |',
      '| following／one of | 妖精步伐下列額外效果之一；霧遁增加選項，非同時全用。 |',
      '| each／every turn | 嘲弄步伐範圍所有生物；灼光復仇每個所選生物；黑暗強運每次擲骰；創造奴僕每回合首次命中。 |',
      '| any／all | 黑暗強運任何效應生效前；長休恢復所有已消耗次數／骰子。 |',
      '| these Temporary Hit Points／those creatures | 天族韌性自己臨時生命值等級＋魅力；至多五名所選生物半等級＋魅力，各自均取得。 |',
      '| your next turn／current turn | 妖精步伐／無蹤到施放者下回合開始；直墜噩夢到施放者下回合結束；灼光復仇目盲到當前回合結束。 |',
      '| your Hex | 創造奴僕須受你自己的脆弱詛咒影響；新行動條件也保留此限定。 |',
      '', '## 8. 補翻清單與activities.condition','','所有Foundry、嵌套欄位的EN／中文／依據已在第3節逐項列出。自行補翻來自已成功搜尋的現行Weblate語料，逐句無完整既有中文的部分依EN自譯；子標沿用已譯正文，activity為行動、Active Effect保留英文。未新增正式terms。',
      '', '| 路徑 | EN条件原句 | 中文 | 狀態 |','|---|---|---|---|'.replace('条件','條件')]
    for r in meta:
        if '.activities.' in r['path'] and r['path'].endswith('.condition'):v.append('| '+' | '.join(table(x) for x in [r['path'],r['en'],r['zh'],'待裁定，未列入payload' if r['path']==load('pending')['path'] else '已對正文核對'])+' |')
    v+=['','## 9. 四項驗收','','- 規則核對：四宗主、四法術表、所有特性與嵌套字段逐句核對；已修正與保留的差異見第4–5節。創造奴僕condition有上游矛盾，留在pending，其餘均依正文或已裁定例外。',
      '- 術語核對：draft_diff.py／terms_check.py均回傳0；90項terms／法術名稱命中均完成，10個明示語境ack；最終payload未出現它／如果／發充能／施展。lang每個無已逐項說明。',
      '- 機械驗證：validate.py通過完整classes26條125字串；content12頁16字串另以check_description／compare_html逐欄檢查（共用CLI不支援pages）。所有HTML標籤、屬性、section、blockquote、span、UUID／Reference目標、Embed參數及lookup均保留。待送payload由本次通過產物移除27既有欄位及1待裁定欄位。',
      '- 中文通讀：遮住EN單獨讀完整中文，修正源稿轉换造成的連句問題後，再核對EN及底稿。現行已譯句子僅作上述規則／定案句式必要修改。'.replace('换','換'),
      '', '## 10. 待裁定與確認','','1. 創造奴僕條件：建議依正文修正為「當你不需專注施放異怪召喚術時」；目前此欄未放入payload，直譯與建議皆保留於pending。',
      '2. 驚懼步伐range提示僅涵蓋剛離開的空間，但正文允許離開或出現的空間擇一；目前正文完整翻譯、range照EN，請確認可維持此處理。',
      '3. 請確認本預覽的必要修正、補翻及保留項；確認後才會以建議上傳。',
      '', '確認依據：[translation-import SKILL.md](<'+str(ROOT/'.claude/skills/translation-import/SKILL.md').replace('\\','/')+'>) 第5步：「**每批版本得到使用者明確確認後才上傳。**」此次完整四子職業為同一確認版本；目前未上傳。',
      '', '## 11. 修訂紀錄','','2026-10-09 v1：四子職業整批預覽；已執行腳本均由 `/scripts/translation-import/player-handbook/warlock-subclasses.py` 提供入口，新腳本全放在 `/scripts`。沒有改動正式翻譯檔、術語、既有建議或Git提交。']
    write('preview.md','\n'.join(v))
    page=['<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>契術師子職業翻譯預覽</title><style>body{max-width:960px;margin:40px auto;padding:0 24px;font:18px/1.85 system-ui;background:#faf9f6;color:#222}h1,h2,h3{line-height:1.4}h2{border-top:1px solid #bbb;padding-top:30px}table{width:100%;border-collapse:collapse}td,th{border:1px solid #bbb;padding:8px}section.secret{border-left:4px solid #b59b65;padding:5px 18px;background:#f3eee2}blockquote{color:#73582f}small{color:#666}nav a{margin-right:16px}code{overflow-wrap:anywhere}</style><h1>契術師四個子職業</h1><p>完整中文通讀版 · v1 · 尚未上傳 · 1個條件待裁定</p><nav>']
    for i,k in enumerate(KEYS):page.append(f'<a href="#k{i}">{html.escape(full["classes"]["entries"][k]["name"])}</a>')
    page.append('</nav>')
    for i,(k,e) in enumerate(full['classes']['entries'].items()):
        page.extend([f'<h2 id="k{i}">{html.escape(e["name"])}</h2>',e['description']])
        nested={f:e[f] for f in ['activities','effects','advancement'] if f in e}
        if nested:
            page.append('<details><summary>行動／效果／升級欄位</summary><table>')
            for path,value in leaves(nested):page.append('<tr><td><small>'+html.escape(path)+'</small></td><td>'+value+'</td></tr>')
            page.append('</table></details>')
    page.append('<h2>書籍頁面</h2>')
    for k,e in full['content']['entries']['Warlock']['pages'].items():page.extend(['<h3>'+e['name']+'</h3>',e['description']])
    page.append('</html>');write('reading.html','\n'.join(page));print(str(DATA/(PREFIX+'.preview.md')))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode');args=parser.parse_args()
    globals()[args.mode]()
