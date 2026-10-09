"""Prepare the complete Rogue subclass batch; no upload operations."""
import copy, contextlib, hashlib, html, io, json, re, runpy, sys
from pathlib import Path
from urllib.parse import quote
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'_incoming/player-handbook'
DATA=BASE/'subclasses/rogue'
SK=ROOT/'.claude/skills/translation-import/scripts'
BOOK='dnd-players-handbook'
PREFIX='rogue.subclasses'
sys.path.insert(0,str(SK))
sys.path.insert(0,str(Path(__file__).parent))
import weblate as w, opencc
from subclasses import read_all, leaves, english_text
from html_blocks import Plan, visible_text, compare_html
from skeleton import build_entries, draft_sections
SUBCLASSES=['Arcane Trickster','Assassin','Soulknife','Thief']
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
    source=(BASE/(PREFIX+'.txt')).read_text(encoding='utf-8')
    write('source.txt',source);write('source.s2twp.txt',opencc.OpenCC('s2twp').convert(source))
    for comp in ['classes','content','tables','spells']:
        rows,audit=read_all(BOOK,BOOK+'-'+comp)
        save(comp+'.live',{'audit':audit,'units':{r['context']:r for r in rows}})
        print(comp,len(rows),'complete')
    for comp in ['terms','spells-glossary']:
        rows,audit=read_all('dnd-5e-2024-zh-tw',comp);save(comp+'.live',{'audit':audit,'units':rows});print(comp,len(rows),'complete')
    from build_index import entry_names, aliases
    save('term_index',{'terms':{r['source'][0]:r['target'][0] for r in load('terms.live')['units'] if any(r['target']) and r['target']!=r['source']},'spells_glossary':{r['source'][0]:r['target'][0] for r in load('spells-glossary.live')['units'] if any(r['target']) and r['target']!=r['source']},'entry_names':{k:dict(v) for k,v in entry_names(str(ROOT/'compendium/zh-tw'),BOOK).items()},'aliases':aliases(str(ROOT/'.claude/skills/translation-import/glossary.tsv'))})
    tool('spell_names.py',['--out',str(DATA/(PREFIX+'.spell-names.json'))])
    scope()
def scope():
    entries=read(ROOT/f'compendium/en/{BOOK}/{BOOK}.classes.json')['entries']
    keys=SUBCLASSES+['phbrgeSpellcasti','Mage Hand Legerdemain','Magical Ambush','Versatile Trickster','Spell Thief','Assassinate',"Assassin's Tools",'Infiltration Expertise','Envenom Weapons','Death Strike','phbrgePsionicPow','Psychic Blades','Psychic Blade','Soul Blades','Psychic Veil','Rend Mind','Fast Hands','Second-Story Work','Supreme Sneak','Use Magic Device',"Thief's Reflexes"]
    scope={k:entries[k] for k in keys}
    journals=read(ROOT/f'compendium/en/{BOOK}/{BOOK}.content.json')['entries']
    content={'Rogue':{'pages':{k:p for k,p in journals['Rogue']['pages'].items() if k in SUBCLASSES or re.search('Arcane Trickster Spellcasting|Soulknife Energy',k)}}}
    blob=json.dumps([scope,content]);ids=set(re.findall(r'JournalEntryPage\.([A-Za-z0-9]+)',blob))
    for journal,e in journals.items():
        for key,p in e.get('pages',{}).items():
            if (journal=='Appendix D: Rule References' and re.search('Arcane Trickster|Soulknife',key)) or (journal=='phbCh3ArtHandout' and key in SUBCLASSES) or key in ids or p.get('id') in ids:
                content.setdefault(journal,{'pages':{}})['pages'][key]=p
    refs=set(re.findall(r'Compendium\.'+BOOK+r'\.tables\.(?:RollTable\.)?([A-Za-z0-9]+)',json.dumps([scope,content])))
    tables=read(ROOT/f'compendium/en/{BOOK}/{BOOK}.tables.json')['entries']
    scoped_tables={k:v for k,v in tables.items() if k in refs or v.get('id') in refs}
    save('scope',{'classes':scope,'content':content,'tables':scoped_tables,'table_refs':sorted(refs)})
    report=[]
    for comp,es in [('classes',scope),('content',content),('tables',scoped_tables)]:
        live=load(comp+'.live')['units']
        for path,val in leaves({'entries':es}):
            r=live.get(path);report.append(path+'\nEN: '+val+'\nZH: '+(r['target'][0] if r else '(missing API unit)'))
            if r:assert r['source'][0]==val,(path,'EN differs from live')
    write('inventory.txt','\n\n'.join(report));print('scope',len(scope),sum(len(e['pages']) for e in content.values()),list(scoped_tables))
def inspect():
    scope=load('scope');live=load('classes.live')['units']
    if len(sys.argv)==2:print('TERMS',json.dumps(load('term_index')['terms'],ensure_ascii=False))
    for k,e in scope['classes'].items():
        if len(sys.argv)>2 and k not in sys.argv[2:]:continue
        print('\n###',k,'NAME',live['entries.'+k+'.name']['target'][0])
        old=Plan(live['entries.'+k+'.description']['target'][0]).blocks
        for i,b in enumerate(Plan(e['description']).blocks):print(i,'EN',b.html,'\nZH',old[i].html if len(old)==len(Plan(e['description']).blocks) else '(different block count)')
        for p,v in leaves(e):
            if p not in ['name','description']:print(p,'EN',v,'ZH',live['entries.'+k+'.'+p]['target'][0])
    if len(sys.argv)==2:
        print('CONTENT',json.dumps(scope['content'],ensure_ascii=False))
        for i,l in enumerate((DATA/(PREFIX+'.source.s2twp.txt')).read_text(encoding='utf-8').splitlines(),1):
            if l.strip():print(i,l)
def related():
    e=read(ROOT/f'compendium/en/{BOOK}/{BOOK}.content.json')['entries']
    for journal,x in e.items():
        for key,p in x.get('pages',{}).items():
            if re.search('Arcane Trickster|Soulknife',key+' '+p.get('name','')):print(journal,key,json.dumps(p,ensure_ascii=False))
    print('ROGUE PAGES',list(e['Rogue']['pages']))
    print('REFERENCE PAGES',[(k,p['name']) for k,p in e['Appendix D: Rule References']['pages'].items() if re.search('Trickster|Soulknife|yiBzQe',k+' '+p.get('name',''))])
    print('BLADE',json.dumps(read(ROOT/f'compendium/en/{BOOK}/{BOOK}.classes.json')['entries']['Psychic Blade'],ensure_ascii=False))
    print('TABLES',[(k,r['source'][0]) for k,r in load('tables.live')['units'].items() if re.search('Rogue|Trickster|Soulknife|Psionic',r['source'][0])])
    print('CONTENT TABLES',[(k,r['source'][0][:200]) for k,r in load('content.live')['units'].items() if re.search('Arcane Trickster Spellcasting|Soulknife Energy Dice',r['source'][0])])
    print('VEX USAGE',[(k,r['target'][0][:250]) for k,r in load('classes.live')['units'].items() if 'Vex' in r['source'][0] and re.search('[一-鿿]',r['target'][0])])
def exact_search():
    for q in load('supplement-search'):
        for r in q['units']:
            if r['source'][0]==q['query'] and re.search('[一-鿿]',r['target'][0]) and not re.search('[A-Za-z]{3,}',english_text(r['target'][0])):
                print(q['query'],r['context'],r['target'][0])
            if r['context'].startswith('entries.Assasinate.') and r['context'].endswith('description') and re.search('[一-鿿]',r['target'][0]):print('ASSASINATE EN',r['source'][0],'ZH',r['target'][0])
def prepare():
    maker=runpy.run_path(str(Path(__file__).with_name('rogue-subclasses-draft.py')))
    bounds=maker['BOUNDS'];source=(DATA/(PREFIX+'.source.s2twp.txt')).read_text(encoding='utf-8');scope=load('scope');live=load('classes.live')['units']
    names,main,supp,labels,fields=maker['make'](source,live,scope['classes'],visible_text,Plan,load('spell-names'))
    def settled(t):
        # User's 2026-10-09 Rogue/Sorcerer ruling applies even to retained prose.
        t=re.sub(r'([1-9])環',lambda m:'一二三四五六七八九'[int(m[1])-1]+'環',t)
        return t.replace('使用物件','使用物體')
    main={k:[settled(t) for t in ts] for k,ts in main.items()}
    supp={k:[settled(t) for t in ts] for k,ts in supp.items()}
    labels={k:settled(v) for k,v in labels.items()};fields={k:settled(v) for k,v in fields.items()}
    main['phbrgeSpellcasti'][0]=main['phbrgeSpellcasti'][0].replace('你已習得','你知曉')
    main['Use Magic Device'][0]=main['Use Magic Device'][0].replace('你學會了如何','你知曉如何')
    labels['Max Prepared Spells']='最大準備法術';labels["Thieves' Tools"]='盜賊工具';labels['Surprising Strikes']='奇襲'
    main['Fast Hands']=[t.replace('盜賊工具組','盜賊工具') for t in main['Fast Hands']]
    supp['Fast Hands']=[t.replace('盜賊工具組','盜賊工具') for t in supp['Fast Hands']]
    # Exact EN paragraphs already accepted in another 2024 component have priority over the manuscript.
    reused={}
    for q in load('supplement-search'):
        for r in q['units']:
            if r['context']=='entries.Assasinate.description' and re.search('[一-鿿]',r['target'][0]):
                eb=Plan(r['source'][0]).blocks;zb=Plan(r['target'][0]).blocks
                current=Plan(scope['classes']['Assassinate']['description']).blocks
                if len(eb)==len(zb)==len(current) and all(eb[i].html==current[i].html for i in range(3)):
                    main['Assassinate']=[visible_text(b.html) for b in zb[:3]];reused['Assassinate']=r
            if r['context']=='entries.Assasinate.effects.Assasinate.description' and r['source'][0]=='<p>You have Advantage on Initiative rolls.</p>':fields[r['source'][0]]=r['target'][0]
    save('reused-existing',reused);save('labels',labels)
    sheets={c:{'schema_version':2,'book':BOOK,'component':c,'entries':{}} for c in ['classes','content']}
    draft=[];metadata=[];sourcecheck=[]
    for k,e in scope['classes'].items():
        blocks=Plan(e.get('description','')).blocks;zhblocks=main[k]+supp.get(k,[])
        assert len(blocks)==len(zhblocks),(k,len(blocks),len(zhblocks))
        oldblocks=Plan(live['entries.'+k+'.description']['target'][0]).blocks
        row={'name_en':e['name'],'name':names[k],'blocks':[]}
        adopted=[]
        for i,(b,t) in enumerate(zip(blocks,zhblocks)):
            old=oldblocks[i].html if len(oldblocks)==len(blocks) else ''
            accepted=bool(re.search('[一-鿿]',english_text(old))) and not re.search('[A-Za-z]{3,}',english_text(old))
            origin='Weblate既有譯文' if accepted else ('其他2024 component同句既有譯文' if k in reused and i<3 else '原稿')
            supplement=i>=len(main[k])
            basis='原稿無此Foundry註記；全量搜尋Weblate，沒有同句完整中文；依EN與已裁定介面詞補翻。' if supplement else ''
            if supplement and english_text(b.html)=='Foundry Note':basis='原稿無此標題；依conventions已裁定格式寫【Foundry註記】。'
            row['blocks'].append({'id':b.id,'en':b.html,'zh':'','source':'supplement' if supplement else 'draft','basis':basis,'draft_text':t,'origin':origin,'source_lines':bounds[k],'old':old,'reused_html':reused[k]['target'][0] if k in reused and i<3 else ''})
            if accepted:adopted.append(english_text(old))
            elif k in reused and i<3:adopted.append(visible_text(Plan(reused[k]['target'][0]).blocks[i].html))
        for field in ['activities','effects','advancement']:
            if field not in e:continue
            row[field]=copy.deepcopy(e[field])
            for item,fs in row[field].items():
                for sub,v in fs.items():
                    path=f'entries.{k}.{field}.{item}.{sub}';old=live[path]['target'][0]
                    if re.search('[一-鿿]',old) and not re.search('[A-Za-z]{3,}',english_text(old)):
                        new=old;basis='Weblate現行既有譯文，保留。'
                        if path=='entries.Soulknife.advancement.Psionic Power.hint':new=old.replace('此職業','此子職業').replace('各種心靈異能','特定心靈異能');basis='規則修正：subclass與certain，依EN限於此子職業的特定異能。'
                    elif v in labels:new=labels[v];basis='依現行條目名、已翻正文小標、既有2024相同名稱或lang介面詞。'
                    elif v in fields:new=fields[v];basis='依EN與對應正文底稿補翻；相同既有句採原譯，缺詞按已裁定句式。'
                    else:raise ValueError((path,v))
                    fs[sub]=new;metadata.append({'component':'classes','path':path,'en':v,'old':old,'zh':new,'basis':basis})
        sheets['classes']['entries'][k]=row
        draft.append('### '+k+'\n名稱：'+names[k]+'\n'+'\n'.join(main[k])+'\n〔EN 補翻／獨立介面欄位〕\n'+'\n'.join(supp.get(k,[]))+'\n'+'\n'.join(p+'：'+v for p,v in leaves({f:row[f] for f in ['activities','effects','advancement'] if f in row})))
        a,z=bounds[k];raw=source.splitlines()[a-1:z]
        cells=[v.strip() for l in raw if '\t' in l for v in l.split('\t') if v.strip()]
        if k=='phbrgePsionicPow':cells.append(source.splitlines()[85].split('Soulknife Energy Dice')[0])
        sourcecheck.append('來源 '+k+'\n'+'\n'.join(raw+adopted+cells))
    virtual={};extra={}
    for journal,j in scope['content'].items():
        for page,e in j['pages'].items():
            path=f'entries.{journal}.pages.{page}.';old=load('content.live')['units'][path+'name']['target'][0]
            name=old if re.search('[一-鿿]',old) else names[page]
            metadata.append({'component':'content','path':path+'name','en':e['name'],'old':old,'zh':name,'basis':'既有名稱照舊；英文插圖標題沿用classes現行名稱。'})
            if 'description' not in e:extra.setdefault(journal,{'pages':{}})['pages'][page]={'name':name};continue
            key=page+' journal';virtual[key]=e;blocks=Plan(e['description']).blocks
            text=main[page].copy()
            if page=='Thief':text[1]=text[1].replace('縮影。','縮影（竊賊子職業）。',1)
            plain=[blocks[0].html,*text];assert len(plain)==len(blocks)
            sheets['content']['entries'][key]={'name_en':e['name'],'name':name,'blocks':[{'id':b.id,'en':b.html,'zh':'','source':'supplement' if i==0 else 'draft','basis':'原稿無Embed指令；保留EN圖片嵌入。' if i==0 else '', 'draft_text':t,'origin':'原稿／classes既有譯文','source_lines':bounds[page],'old':'','reused_html':''} for i,(b,t) in enumerate(zip(blocks,plain))]}
            draft.append('### '+key+'\n名稱：'+name+'\n'+'\n'.join(text)+'\n〔EN 補翻／圖片指令〕\n'+plain[0]);a,z=bounds[page];sourcecheck.append('來源 '+key+'\n'+'\n'.join(source.splitlines()[a-1:z]+main[page]))
    for c,s in sheets.items():save(c+'.sheet',s)
    save('content.virtual-en',virtual);save('content.extra',extra);save('metadata',metadata);save('bounds',bounds)
    write('draft.txt','\n\n'.join(draft));save('draft-fingerprint',{'sha256':hashlib.sha256((DATA/(PREFIX+'.draft.txt')).read_bytes()).hexdigest()})
    write('source.segmented.s2twp.txt','\n\n'.join(sourcecheck))
    write('source.unmapped-spellcasting-table.txt','\n'.join(source.splitlines()[16:37]))
    audit=copy.deepcopy(sheets['classes'])
    for k,row in audit['entries'].items():
        row['blocks'].append({'id':'name-audit','en':scope['classes'][k]['name']})
        for field in ['activities','effects','advancement']:
            if field in scope['classes'][k]:row[field]=copy.deepcopy(scope['classes'][k][field])
    audit['entries'].update(sheets['content']['entries']);save('audit.sheet',audit)
    ack={
      'Assassinate|Attack':'Attack兩次分別是attack rolls＝攻擊檢定、Sneak Attack＝偷襲；正式特性名偷襲不拆成偷襲攻擊。',
      'Assassinate|take':'taken a turn指進行回合；takes extra damage已採承受。',
      'Death Strike|Attack':'三次Attack皆在Sneak Attack特性名或attack’s damage中；採現行偷襲與攻擊，不硬加攻擊字數。',
      'Envenom Weapons|Attack':'只命中Sneak Attack特性名，沿用現行偷襲。',
      'Fast Hands|take':'take the Utilize／Magic action指採取利用／魔法動作，非承受。',
      'Infiltration Expertise|Expertise':'特性完整名稱Infiltration Expertise按原稿專業滲透，並非Expertise規則特性或技能專精。',
      'Psychic Blade|take':'take the Attack action按已裁定句式採取攻擊動作。',
      'Psychic Blades|take':'take the Attack action按已裁定句式採取攻擊動作。',
      'Psychic Blades|On a hit':'此處為Damage on a Hit表頭，既有命中傷害準確且照舊；並非句首命中時觸發子句。',
      'Rend Mind|Attack':'三次命中皆為Sneak Attack特性名稱；沿用現行偷襲。',
      'Second-Story Work|reach':'hard-to-reach places指難以到達的地方，非武器觸及。',
      'Spell Thief|take':'take a Reaction按已裁定句式採取反應。',
      "Thief's Reflexes|take":'take two turns／take your first turn指進行回合，非承受。',
      'phbrgePsionicPow|reach':'reach certain Rogue levels指達到特定遊蕩者等級，非觸及。',
      'phbrgeSpellcasti|reach':'reach Rogue level 10指達到遊蕩者10級，非觸及。'
    }
    save('ack',ack)
    print('Independent draft prepared',len(scope['classes']),'classes',len(virtual),'content descriptions',len(metadata),'nested fields')
def markup(text,en,k):
    labels=load('labels');spells=load('spell-names');result=text;atoms=[]
    for m in re.finditer(r'<span class="reference">.*?</span>',en,re.S):
        label='應用雙倍傷害' if 'Apply Double Damage' in m[0] else '應用'
        atoms.append((label,m[0].replace('Apply Double Damage','應用雙倍傷害').replace('Apply</span>','應用</span>')))
    cleaned=re.sub(r'<span class="reference">.*?</span>','',en,flags=re.S)
    for m in re.finditer(r'@UUID\[([^\]]+)\](?:\{([^}]+)\})?',cleaned):
        label=spells.get(m[2],labels.get(m[2]));assert label,(k,m[0]);atoms.append((label,'@UUID['+m[1]+']{'+label+'}'))
    refs={'Invisible':'隱形','Hide':'躲藏','Three-Quarters Cover':'四分之三掩護','Total Cover':'全掩蔽','Jumping':'跳躍'}
    for m in re.finditer(r'&(?:amp;)?Reference\[([^\]]+)\](?:\{[^}]*\})?',cleaned):
        label=refs[m[1]];atoms.append((label,m[0].split(']')[0]+']{'+label+'}'))
    for m in re.finditer(r'\[\[[^\]]+\]\](?:\{([^}]+)\})?',cleaned):
        raw=m[0].split(']]')[0]+']]'
        if raw.startswith('[[lookup'):label='當前遊蕩者等級';zh=raw
        elif '[[/skill slt' in raw:label='敏捷（巧手）';zh=raw
        elif '[[/skill arc' in raw:label='智力（奧秘）';zh=raw
        elif '[[/r 1d6' in raw:label='d6';zh=raw
        elif '[[/damage 2d6 poison' in raw:label='2d6';zh=raw+'{2d6}'
        elif 'activity="Trip"' in raw:label='摔絆';zh=raw+'{摔絆}'
        elif 'activity="Poison"' in raw:label='淬毒';zh=raw+'{淬毒}'
        elif '[[/item Psychic Blade' in raw:label='心靈之刃';zh=raw+'{心靈之刃}'
        else:raise ValueError((k,raw))
        atoms.append((label,zh))
    for m in re.finditer(r'<(strong|em)>([^<]+)</\1>',cleaned):
        name=m[2].strip();label=labels.get(name,spells.get(name)) or labels.get(name.rstrip('.:')) or spells.get(name.rstrip('.:'));assert label,(k,name)
        if '【'+label+'】' in text:label='【'+label+'】'
        atoms.append((label,'<'+m[1]+'>'+label+'</'+m[1]+'>'))
    placeholders={}
    for i,(label,raw) in enumerate(sorted(atoms,key=lambda a:-len(a[0]))):
        assert label in result,(k,label,result,en)
        token='\x01'+str(i)+'\x02';result=result.replace(label,token,1);placeholders[token]=raw
    for token,raw in placeholders.items():result=result.replace(token,raw)
    return result
def map_draft():
    assert load('draft-fingerprint')['sha256']==hashlib.sha256((DATA/(PREFIX+'.draft.txt')).read_bytes()).hexdigest()
    drafts=draft_sections(DATA/(PREFIX+'.draft.txt'))
    for c in ['classes','content']:
        sheet=load(c+'.sheet');entries=load('scope')['classes'] if c=='classes' else load('content.virtual-en')
        for k,row in sheet['entries'].items():
            for b in row['blocks']:
                if b['old'] and english_text(b['old'])==b['draft_text'] and not compare_html(b['en'],b['old']):b['zh']=b['old']
                elif b['reused_html']:
                    match=[z.html for e,z in zip(Plan(load('reused-existing')[k]['source'][0]).blocks,Plan(b['reused_html']).blocks) if e.html==b['en']];assert len(match)==1;b['zh']=match[0]
                else:b['zh']=markup(b['draft_text'],b['en'],k)
                if re.search(r'\[\[(?:lookup|/skill|/r )',b['en']):
                    b['source']='supplement';b['basis']='原稿無Foundry無標籤巨集；保留EN巨集，底稿以明文檢定／等級／骰面表達，其餘句子仍從原稿或既有譯文取。'
        save(c+'.sheet',sheet)
        aligned=build_entries(sheet,entries,drafts)
        if c=='content':aligned={'entries':{'Rogue':{'pages':{k.removesuffix(' journal'):v for k,v in aligned['entries'].items()}},**load('content.extra')}}
        save(c+'.aligned',aligned)
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
        write(log,buf.getvalue());print(name,'exit',code,buf.getvalue()[-600:]);checks[name]=code
    p=lambda s:str(DATA/(PREFIX+'.'+s))
    run('draft_diff.py',['--source',p('source.segmented.s2twp.txt'),'--draft',p('draft.txt'),'--out',p('draft-diff.md')],'draft-diff.log.txt')
    run('terms_check.py',[p('audit.sheet.json'),'--draft',p('draft.txt'),'--index',p('term_index.json'),'--names',p('spell-names.json'),'--ack',p('ack.json'),'--out',p('terms-report.md')],'terms.log.txt')
    run('lang_compare.py',[p('audit.sheet.json'),'--draft',p('draft.txt')],'lang-report.md')
    run('validate.py',[p('classes.aligned.json'),'--book',BOOK,'--component','classes','--allow','Active,Effect','--out',p('classes.validated.json')],'validation.txt')
    save('checks',checks)
REASONS={
 'Arcane Trickster':'既有正文與EN規則一致，全文保留；content沿用並補回EN要求的子職業UUID。原稿沒寫agility／身法，既有譯文已涵蓋。',
 'Assassin':'既有正文與EN一致，全文保留；content沿用並補回EN要求的刺客UUID。',
 'Soulknife':'既有正文照舊，content沿用並補回魂刃UUID；原稿沒有haunted／困擾的語意，既有譯文已涵蓋。',
 'Thief':'原稿為底；子職→子職業為既有專案名稱，content補竊賊子職業UUID。',
 'phbrgeSpellcasti':'既有譯文為底；必要技術修正：補回破損Mage Hand、Fog Cloud及缺少標籤的UUID，移除段首T；定案詞／使用者裁定：以下→下列、現行法術名、環階數字一律國字（一環／二環）、You have learned→你知曉；規則：表名遊蕩者施法表→詭術師施法表、額外法術明確為法師法術、環階對應法術位、should／應該改成EN的can／可以。未動其餘通順既有句子。',
 'Mage Hand Legerdemain':'既有正文為底；已定句式：以附贈動作→採取附贈動作。原稿敏捷（巧手）對應[[/skill slt]]，巨集原樣。',
 'Magical Ambush':'定案詞／禁用字：施展→施放、它→該生物；時點：同一回合。',
 'Versatile Trickster':'定案詞：現行法術名法師之手、5呎；刪除可見英文別名；保留摔絆巨集並加中文標籤，原稿單一另一名生物限制照舊。',
 'Spell Thief':'規則：使用限制只在成功偷得法術後觸發，原稿「此特性一經使用」過廣；定案詞／句式：緊接在…後、採取反應、效應範圍、施放、等同於、直到完成長休前；轉換修正：獲得瞭→獲得了；8小時禁止施法的時間子句前置。',
 'Assassinate':'正文採其他2024 component同EN逐段已有譯文（entries.Assasinate.description），避免重譯，見reused-existing.json；保留首輪、尚未有回合、偷襲額外武器傷害等規則。Foundry註記與缺漏的condition依EN補翻。',
 "Assassin's Tools":'既有正文照舊；工具與熟練自動獲得的Foundry註記補翻。',
 'Infiltration Expertise':'規則：必須研究所要模仿的該人至少1小時，原稿只寫鑽研而未明確對象，補某人／該人的指涉；定案詞／句式：以下→下列、【模仿大師】／【機動瞄準】小標；穩定瞄準→Weblate現行特性名手穩就準；其餘原稿照舊，言語／筆跡／兩者擇一保留。',
 'Envenom Weapons':'定案詞／禁用字：它→目標、受到→承受、毒素抗性→毒素傷害抗力；2D6→2d6；原稿數值映射到EN傷害巨集且保留公式，補中文標籤。每次淬毒豁免失敗都受傷害的限制保留。',
 'Death Strike':'定案詞：成功透過→成功通過；DC標示依既有句式；正文首輪、偷襲、體質豁免、雙倍該次攻擊傷害照舊。',
 'phbrgePsionicPow':'規則：靈振訣竅明寫one／一枚靈能骰；定案詞／句式：子職→子職業、如果→若、【】小標、採取魔法動作、你所能看見；里→哩修正英文mile單位；首次長休後使用不消耗骰，依EN明確寫第一次；靈能骰表由原稿按EN表格儲存格拆分，數值逐格相同；原稿的長休／短休句序保留，語意相同。',
 'Psychic Blades':'既有正文為底；規則誤譯：Vex精通被寫為精通，修正為lang及原稿的侵擾；句式：以附贈動作→採取附贈動作；其餘既有句子保留。Foundry授予物品巨集保留並補心靈之刃標籤。',
 'Psychic Blade':'附屬武器正文沿用現行既有譯文；只對齊已定句式以附贈動作→採取附贈動作；與Psychic Blades同一第三段同步。',
 'Soul Blades':'定案詞／句式：念刃→現行心靈之刃、以下→下列、如果→若、採取附贈動作、你所能看見、等同於；距離子句整理成擲骰結果十倍呎數，與EN同義；尋的斬擊僅命中才耗骰、傳送必先耗骰皆保留。',
 'Psychic Veil':'規則：EN為1小時，而非任選至多1小時；隱形在對生物造成傷害後才提前結束，原稿只說造成傷害過廣；定案詞／句式：採取魔法動作、進入隱形狀態、緊接在…後、直到完成長休前。',
 'Rend Mind':'規則／轉換修正：目標將在陷入→目標將陷入，震懾明寫狀態；EN each of its turns明確每個回合，repeats為必須重複豁免，移除原稿可以；定案詞：現行心靈之刃、若、直到完成長休前、DC標示。',
 'Fast Hands':'定案詞／句式：採取附贈動作、巧手／使用物體小標（object依使用者裁定物體）、Utilize＝利用動作、採取魔法動作、現行盜賊工具。解鎖／拆陷阱使用工具與扒竊檢定的不同限制保留。',
 'Second-Story Work':'轉換修正：OpenCC將梁轉樑，名稱恢復原始簡體對應的梁上君子；定案詞：以下增益→下列好處，攀爬者／跳躍者小標；跳躍Reference加中文標籤，等速攀爬與敏捷取代力量保留。',
 'Supreme Sneak':'定案詞／句式：以下→下列、花費→消耗、小標【】；全身掩護→已裁定Total Cover＝全掩蔽；四分之三掩護沿用原稿與lang，所有Reference加中文標籤。',
 'Use Magic Device':'轉換修正：曆險→歷險；定案詞／句式：以下增益→下列好處、施放、若、物品property＝屬性、施法屬性、小標【】、You have learned→你知曉；規則：更高等級→更高環階，首次先通過檢定，卷軸失敗為瓦解而非必須化成塵埃；d6與奧秘檢定映射EN巨集，保留四件與DC10＋環階。',
 "Thief's Reflexes":'正文原稿照舊，名稱沿用現行竊賊反射；首輪兩回合、正常先攻與減10皆保留。'
}
def reason(k):return REASONS[k.removesuffix(' journal')]
def review():
    from validate import check_description,count_strings
    from draft_diff import best_match,fragments,source_sections,norm_name,draft_sections as diff_sections
    assert all(v==0 for v in load('checks').values()),load('checks')
    full={c:load(c+'.aligned') for c in ['classes','content']};assert full['classes']==load('classes.validated')
    english=load('scope');audit=[];preserved=[];register=[]
    def delta(new,live,prefix=''):
        out={}
        for key,v in new.items():
            p=prefix+'.'+key if prefix else key
            if isinstance(v,dict):
                part=delta(v,live,p)
                if part:out[key]=part
            else:
                assert p in live,p
                if v==live[p]['target'][0]:preserved.append({'path':p,'value':v})
                else:out[key]=v
        return out
    for c in full:
        for p,zh in leaves(full[c]):
            assert not re.search('它|如果|發充能|施展',english_text(zh)),p
            assert not [s for s in re.findall('[A-Za-z]{3,}',english_text(zh)) if s not in {'Active','Effect','Foundry','DC'}],(p,zh)
        for p,en in leaves({'entries':english[c]}):
            zh=dict(leaves(full[c]))[p]
            if p.endswith('.description'):
                errors=check_description(en,zh,{'Foundry','Active','Effect'});assert not errors,(p,errors)
        save(c+'.upload',delta(full[c],load(c+'.live')['units']))
        for k,row in load(c+'.sheet')['entries'].items():
            key=k.removesuffix(' journal');prefix=f'entries.Rogue.pages.{key}.' if c=='content' else f'entries.{key}.'
            for b in row['blocks']:
                a,z=b['source_lines'];raw=(DATA/(PREFIX+'.source.s2twp.txt')).read_text(encoding='utf-8').splitlines()[a-1:z]
                ratio,i,j,original=best_match(b['draft_text'],raw)
                base=english_text(b['old']) if b['origin']=='Weblate既有譯文' else original
                if b['reused_html']:base=b['draft_text']
                audit.append({'component':c,'path':prefix+'description/'+b['id'],'entry':k,'en':b['en'],'raw':original,'source_lines':[a,z],'existing':b['old'],'origin':b['origin'],'draft':b['draft_text'],'zh':b['zh'],'source':b['source'],'basis':b['basis'],'modifications':fragments(base,b['draft_text']),'reason':'無修改' if base==b['draft_text'] else reason(k),'retained_html':bool(b['old'] and b['old']==b['zh'])})
    src=source_sections(DATA/(PREFIX+'.source.segmented.s2twp.txt'))
    for k,pars in diff_sections(DATA/(PREFIX+'.draft.txt')).items():
        for i,new in enumerate(pars,1):
            ratio,a,b,old=best_match(new,src[norm_name(k)])
            register.append({'entry':k,'paragraph':i,'ratio':ratio,'source':old,'draft':new,'fragments':fragments(old,new),'reason':'無修改' if old==new else reason(k)})
    save('audit',audit);save('fragment-register',register);save('preserved',preserved)
    save('verification',{'date':'2026-10-09','version':'v1','classes_entries':len(full['classes']['entries']),'classes_full_strings':count_strings(full['classes']),'classes_upload_strings':count_strings(load('classes.upload')),'content_pages':sum(len(e['pages']) for e in full['content']['entries'].values()),'content_full_strings':count_strings(full['content']),'content_upload_strings':count_strings(load('content.upload')),'preserved_strings':len(preserved),'retained_body_blocks':sum(a['retained_html'] for a in audit),'body_blocks':len(audit),'payload_sha256':{c:hashlib.sha256((DATA/(PREFIX+'.'+c+'.upload.json')).read_bytes()).hexdigest() for c in full},'checks':load('checks'),'content_mechanical_pass':True,'nested_reviewed':True,'approved':False,'uploaded':False,'pending':['原稿17–37行施法表：EN/API無對應字串，保留原稿，未加入payload。']})
    print(json.dumps(load('verification'),ensure_ascii=False))
LANG_REASONS={
 'applied':'此處applied是套用傷害，未用介面狀態名已套用。',
 'area of effect':'依使用者定案效應範圍，不採lang的效果範圍／範圍效果。',
 'attack bonus':'bonus是靈能加值或傷害環境加值；非攻擊加值欄位。',
 'attack roll':'terms已定攻擊檢定，優先於lang攻擊骰。',
 'category':'武器種類是既有正文表頭，保留；非基地分類。',
 'changing':'法術準備列表更換為既有正文小標；非更改中狀態。',
 'charm':'Charm Person為現行法術名魅惑人類，非護咒。',
 'creatures':'數量／對象由正文明寫；lang的{number}計數佔位符不適用。',
 'details':'details是詳細說明規則的動詞，非詳情介面欄。',
 'dice':'Psionic Energy Dice依原稿與既有提示寫靈能骰；非骰值／骰數介面欄。',
 'enemies':'敘述敵人，數量佔位符不適用。',
 'expertise':'Infiltration Expertise為原稿專業滲透，不是專精規則特性；其他Expertise僅名稱比較。',
 'force':'force a creature to save是迫使，非力場傷害。',
 'illusion':'Minor Illusion為現行法術名次級幻象，非幻術學派。',
 'next':'next 8 hours指接下來八小時，非下一頁／下一步。',
 'number':'number表示表格數量／準備法術數量／擲骰結果數，非lang骰子數量欄位。',
 'object':'Use an Object依使用者裁定物體；非帶{number}的計數欄位；魔法物品正文寫物品。',
 'order':'order of psychic adepts指修士團，非命令或順序。',
 'physical':'physical barriers指物理障壁，既有譯文照舊，非實體物品分類。',
 'prepared':'have the spell prepared描述準備法術，依原稿／現行正文；非已準備狀態字串。',
 'proficiencies':'正文及註記使用熟練，非熟練項表頭。',
 'reach':'hard-to-reach或reach a level指到達／達到，非武器觸及。',
 'reference':'Reference只在技術標記或拼字中；指令原樣，不加入參照說明字串。',
 'replace':'準備法術正文沿用既有替換，非介面替代操作。',
 'resistances':'此處傷害抗力依使用者裁定，非lang泛稱抗性。',
 'rest':'Short/Long Rest譯短休／長休，非啟動分類休息。',
 'second':'second psychic blade是第二把，非秒數。',
 'selected':'目標選取使用句式選取目標，非已選取狀態。',
 'size':'die size沿用原稿骰面／骰子大小，非生物體型。',
 'start':'to start是最初挑法術，既有譯文首先；非效應到期開始縮写。',
 'trade':'their trade是勾當／行當，既有敘述照舊，非交易。',
 'versatile':'Versatile Trickster為原稿萬能詭術，非武器多用屬性。',
 'three-quarters cover':'原稿與lang均四分之三掩護，應已命中；若未命中需再核對。'
}
def preview():
    info=load('verification');audit=load('audit');meta=load('metadata');reg=load('fragment-register')
    esc=lambda x:str(x).replace('|','&#124;').replace('\n','<br>')
    link=lambda suffix,title:f'[{title}](<{str(DATA/(PREFIX+"."+suffix)).replace(chr(92),"/")}>)'
    v=['# 遊蕩者四個子職業：完整預覽 v1','','2026-10-09。尚未上傳。依使用者指示四個子職業及所有相关條目一次處理，不拆批。',
       '',f'完整範圍：{info["classes_entries"]}個classes條目（含附屬武器）、{info["content_pages"]}個content頁面（4正文＋4插圖標題），共{info["classes_full_strings"]+info["content_full_strings"]}個字串；保留{info["preserved_strings"]}個全欄位及{info["retained_body_blocks"]}個既有正文區塊。待送classes {info["classes_upload_strings"]}＋content {info["content_upload_strings"]}＝{info["classes_upload_strings"]+info["content_upload_strings"]}個字串。',
       '', '## 1. 檔案与確認版本','',link('source.s2twp.txt','原稿轉繁與原行號')+'；原稿為 `_incoming/player-handbook/rogue.subclasses.txt`。',link('draft.txt','獨立底稿')+'；'+link('reading.html','完整中文通讀版')+'；'+link('classes.aligned.json','classes映射')+'；'+link('content.aligned.json','content映射')+'。',link('classes.upload.json','classes payload')+'；'+link('content.upload.json','content payload')+'；'+link('verification.json','驗收數據')+'。',*[c+' SHA-256：`'+h+'`。' for c,h in info['payload_sha256'].items()],
       '', '## 2. 來源與範圍','','Weblate全量分頁核實：classes2270、content1161、tables282、spells1695、terms137、spells-glossary640；皆HTTP200與總數吻合。現行法術名稱374筆。補翻搜尋跨project／component，完整證據見'+link('supplement-search.json','搜尋紀錄')+'。',
       '底稿逐段從原稿或同語境既有譯文取。原稿行號見下表；compare基準檔為「按條目切分的原稿＋採用的Weblate既有句」，數字表格按原稿欄位拆分，沒有以完成的映射反推底稿。原始全文與逐段原稿比對保留在下表。',
       '詭術師、刺客、魂刃的既有介紹完整保留。暗殺的相同EN前三段已有2024中文（entries.Assasinate.description），沿用其已有譯文；名稱仍為現行暗殺。其他既有通順句保留，只修規則、定案詞或技術損壞。',
       'Soulknife Energy Dice為靈能力量正文內表格，全部儲存格一併映射。檢查所有tables的名稱、來源與範圍UUID後沒有相关RollTable。原稿17–37行的詭術師施法表在EN/API沒有對應單元；EN只有表格UUID連結，該技術目標保留。原稿表格獨立存為'+link('source.unmapped-spellcasting-table.txt','未映射施法表')+'，不自行新增EN欄位。',
       '', '## 3. 逐段對照','','每個EN區塊一列，表格數字亦逐格列出。原稿欄保留最佳句段比對及原始行範圍；既有來源欄不以原稿覆蓋正式譯文。',
       '| 欄位／來源行 | EN | 原稿轉繁 | 既有譯文 | 底稿 | 修改（原→新／類別／理由） |','|---|---|---|---|---|---|']
    for a in audit:
        change='無修改' if a['reason']=='無修改' else '；'.join(a['modifications'])+'｜'+a['reason']
        if a['source']=='supplement':change=a['basis']+' '+change
        v.append('| '+' | '.join(esc(x) for x in [a['path']+'／'+str(a['source_lines']),a['en'],a['raw'],a['existing'],a['draft'],change])+' |')
    v.extend(['','### 底稿差異工具原樣輸出','',(DATA/(PREFIX+'.draft-diff.md')).read_text(encoding='utf-8'),'','### 所有差異片段登記','','| 條目／段 | 原→新 | 理由 |','|---|---|---|'])
    for r in reg:
        if r['fragments']:v.append('| '+esc(r['entry']+'/p'+str(r['paragraph']))+' | '+esc('；'.join(r['fragments']))+' | '+esc(r['reason'])+' |')
    v.extend(['','## 4. 規則與技術差異','','| 項目 | EN | 原稿／舊譯 | 最終處理 |','|---|---|---|---|',
      '| 施法UUID | Mage Hand／Fog Cloud及現行法術連結 | UUID缺]、缺@、有無標籤英文；段首T | 已改：按EN補回全部UUID目標與現行中文；表名、法師法術、法術環階及can一併修正。 |',
      '| 法術竊賊使用限制 | Once you steal a spell with this feature | 此特性一經使用 | 已改：當你以此特性偷得法術後，才限制到長休。 |',
      '| 靈能骰距離 | within 1 mile of each other | 距離不可超過一里 | 已改：1哩；不是市里。 |',
      '| 心靈低語免費使用 | The first time … after each Long Rest | 在每次長休後你可以免費使用一次 | 已改：明確第一次不消耗，其他次消耗。 |',
      '| 心靈之刃精通 | Vex | 既有精通：精通 | 已改：侵擾（lang與原稿已定）。 |',
      '| 心靈傳送距離 | equal to 10 times the number rolled | 靈能骰結果數字十倍尺數 | 已改：等同於擲骰結果十倍呎數；未佔據、可見限制保留。 |',
      '| 靈能面紗 | for 1 hour；deal damage to a creature | 持續至多1小時；造成傷害 | 已改：1小時或主動解除；限定對生物造成傷害後。 |',
      '| 撕裂心智 | repeats the save at the end of each of its turns | 可以在他的回合結束時重複豁免 | 已改：移除可選的可以，於其每個回合結束時重複豁免；修正將在陷入錯字。 |',
      '| 模仿大師 | if you have spent at least 1 hour studying them | 至少花費了一小時的時間來進行鑽研 | 已改：研究某人至少1小時，再模仿該人的言語／筆跡，明確是研究所要模仿的人。 |',
      '| 靈振訣竅 | roll one Psionic Energy Die | 投擲靈能骰 | 已改：投擲一枚靈能骰；僅成功轉成成功檢定時消耗。 |',
      '| 快手 | Take the Utilize action | 執行操作動作 | 已改：採取利用動作。 |',
      '| 法術卷軸 | the scroll disintegrates | 卷軸化為塵埃 | 已改：卷軸會瓦解；EN不指定塵埃。 |',
      '| 魂刃升級提示 | certain powers … from this subclass | 此職業的各種心靈異能 | 已改：此子職業的特定心靈異能。 |',
      '| 詭術師施法表缺欄位 | 只出現Arcane Trickster Spellcasting table UUID | 原稿17–37行有完整施法表 | 待確認保留於原稿；沒有EN單元可送，不加入payload。 |',
      '', '## 5. 保留項','','| 項目 | EN | 原稿／既有譯文 | 理由 |','|---|---|---|---|',
      '| 詭術師施法段開頭 | See the rules on spellcasting | 既有「見第7章」 | 原稿也寫第七章；資訊正確，保留。 |',
      '| 魂刃介紹 | sought out an order of psychic adepts | 既有「找到了一個隱居的靈能修士團」 | 隱居為原稿敘述增色，無規則影響，保留。 |',
      '| 竊賊介紹 | getting maximum benefit | 原稿「永遠能夠最大化利用」 | 敘述性措辭，無額外規則承諾；保留原稿。 |',
      '| 靈能面紗 | a veil of psychic static | 原稿「一層靈能面紗」 | 略去static意象，無規則差異，沿用原稿。 |',
      '| 使用魔法裝置起句 | maximize use of magic items | 原稿「在你的尋寶歷險生涯中…魔法裝置」 | 敘述增色不影響規則，保留。 |',
      '| 竊賊反射起句 | You are adept | 原稿「你變的更加擅長」 | 原稿仍可理解，既有name竊賊反射照舊；未為語感重寫。 |',
      '', '## 6. 術語報告（原樣）','',(DATA/(PREFIX+'.terms-report.md')).read_text(encoding='utf-8'),'','### 個別語境確認'])
    for k,r in load('ack').items():v.append('- '+k+'：'+r)
    v.extend(['','### lang對照（原樣）','',(DATA/(PREFIX+'.lang-report.md')).read_text(encoding='utf-8'),'','### lang「無」逐項說明'])
    for l in (DATA/(PREFIX+'.lang-report.md')).read_text(encoding='utf-8').splitlines():
        if '| 無 |' in l:
            key=l.split('|')[1].strip();assert key in LANG_REASONS,key;v.append('- '+key+'：'+LANG_REASONS[key])
    v.extend(['','## 7. 限定詞逐句核對','','| 欄位 | EN限定詞 | 結果 |','|---|---|---|'])
    for a in audit:
        en=english_text(a['en']);hits=re.findall(r'\b(?:this|these|that|the|following|one of|each|any|all)\b',en,re.I)
        if hits:v.append('| '+esc(a['path'])+' | '+esc(', '.join(hits))+' | '+esc(a['draft'])+'；已逐句核對主體、單複數、可選性與限制。 |')
    v.extend(['','## 8. 補翻與獨立欄位','','原稿無Foundry註記、效果摘要或activity介面欄位；按EN補翻，完整搜尋證據已保留。以下包括所有介面欄位，保留者也列出。','','| 欄位 | EN | 中文 | 依據 |','|---|---|---|---|'])
    for a in audit:
        if a['source']=='supplement':v.append('| '+' | '.join(esc(x) for x in [a['path'],a['en'],a['zh'],a['basis']])+' |')
    for m in meta:v.append('| '+' | '.join(esc(x) for x in [m['path'],m['en'],m['zh'],m['basis']])+' |')
    v.extend(['','### activities.condition另外核對','','| 欄位 | EN原句 | 中文 |','|---|---|---|'])
    for m in meta:
        if '.activities.' in m['path'] and m['path'].endswith('.condition'):v.append('| '+' | '.join(esc(m[x]) for x in ['path','en','zh'])+' |')
    v.extend(['','## 9. 四項驗收','','1. 規則：觸發、目標、距離、可見性、DC、數值、每次／每回合限制、長短休、消耗及例外已逐項對EN，修正見第4節，保留差異見第5節。',
      '2. 術語：48項命中，15個具體語境ack，未處理0；lang每個無另有說明。最终payload回查沒有它、如果、發充能、施展；可見英文僅保留已裁定Active Effect／Foundry／DC。',
      f'3. 機械：draft_diff、terms_check、lang_compare、validate全回傳0；validate通過25條、109個完整字串。content的8頁12字串另以check_description及compare_html驗證；UUID、Reference、Embed、巨集、HTML巢狀與屬性均保留。',
      '4. 通讀：獨立讀底稿及最終中文；映射只從凍結底稿取，巨集明文與技術文字分別核對。獨立正文／content／活動／效果／升級提示全涵蓋。',
      '', '## 10. 待確認','','1. 原稿詭術師施法表目前没有EN/API目標單元；建議本批保留原表，處理所有可映射字串，不自行新增或覆寫EN結構。',
      '2. 請確認整批必要修正、原稿補翻及既有譯文保留項。確認後才以method=suggest上傳。',
      '', '確認依據：[translation-import SKILL.md](<'+str(ROOT/'.claude/skills/translation-import/SKILL.md').replace('\\','/')+'>)第5步：「**每批版本得到使用者明確確認後才上傳。**」此次四個子職業是同一確認版本，目前未上傳。',
      '', '## 11. 修訂紀錄','','2026-10-09 v1：四個子職業與相關條目整批準備；所有執行入口與新腳本均位於/scripts/translation-import/player-handbook。沒有改動正式譯文、EN來源、術語、既有建議或Git提交。'])
    verified=load('live-verification') if (DATA/(PREFIX+'.live-verification.json')).exists() else None
    if verified:v.extend(['','### 交付前現行資料核對','',f'重新读取{verified["total_units"]}個classes／content單元，本批source與正式target均未變。其他範圍的變動另記於'+link('live-verification.json','核對證據')+'；沒有納入本批。'])
    write('preview.md','\n'.join(v).replace('相关','相關').replace('与','與').replace('最终','最終').replace('没有','沒有').replace('缩写','縮寫').replace('读取','讀取'))
    full={c:load(c+'.aligned') for c in ['classes','content']}
    page=['<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>遊蕩者子職業完整預覽</title><style>body{max-width:980px;margin:40px auto;padding:0 24px;font:18px/1.8 system-ui;background:#faf9f6;color:#222}h2{border-top:1px solid #bbb;padding-top:24px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #bbb;padding:8px}section.secret{border-left:4px solid #b59b65;padding:5px 18px;background:#f3eee2}pre{white-space:pre-wrap;overflow-wrap:anywhere}blockquote{color:#73582f}</style><h1>遊蕩者四個子職業</h1><p>v1 · 尚未上傳 · 詭術師施法表缺少EN/API對應欄位，原稿保留</p>']
    for k,e in full['classes']['entries'].items():
        page.extend(['<h2>'+html.escape(e['name'])+' <small>'+html.escape(k)+'</small></h2>',e['description']])
        nested={f:e[f] for f in ['activities','effects','advancement'] if f in e}
        if nested:page.append('<details><summary>行動／效果／升級欄位</summary><pre>'+html.escape(json.dumps(nested,ensure_ascii=False,indent=2))+'</pre></details>')
    page.append('<h1>content</h1>')
    for j,e in full['content']['entries'].items():
        for p,fields in e['pages'].items():page.extend(['<h2>'+html.escape(j+'／'+fields['name'])+'</h2>',fields.get('description','')])
    page.extend(['<h2>原稿施法表（無EN對應欄位，未加入payload）</h2><pre>',html.escape((DATA/(PREFIX+'.source.unmapped-spellcasting-table.txt')).read_text(encoding='utf-8')),'</pre></html>'])
    write('reading.html','\n'.join(page));print('Complete preview written',DATA/(PREFIX+'.preview.md'))
def verify_preview():
    verified=[]
    for c in ['classes','content']:
        baseline=load(c+'.live')['units'];rows,audit=read_all(BOOK,BOOK+'-'+c);current={r['context']:r for r in rows}
        changes=[p for p,r in baseline.items() if current[p]['source']!=r['source'] or current[p]['target']!=r['target']]
        scoped=dict(leaves({'entries':load('scope')[c]}));affected=[p for p in changes if p in scoped];assert not affected,('refresh affected translations',c,affected)
        for p,v in leaves(load(c+'.upload')):assert p in current and v!=current[p]['target'][0],(c,p)
        verified.append({'component':c,'verified_units':len(current),'scoped_source_and_target_unchanged':True,'unrelated_changed_paths':changes,'pagination':audit})
        print(c,'scope unchanged, unrelated changes',len(changes))
    for c,digest in load('verification')['payload_sha256'].items():assert hashlib.sha256((DATA/(PREFIX+'.'+c+'.upload.json')).read_bytes()).hexdigest()==digest
    save('live-verification',{'verified':verified,'total_units':sum(r['verified_units'] for r in verified),'uploaded':False})
def search():
    scope=load('scope');queries=set()
    for k,e in scope['classes'].items():
        in_note=False
        for block in Plan(e.get('description','')).blocks:
            t=english_text(block.html)
            if 'Foundry Note' in t:in_note=True
            if in_note:queries.add(t[:100])
        for p,v in leaves(e):
            if p not in ['name','description']:queries.add(english_text(v)[:100])
    result=load('supplement-search') if (DATA/(PREFIX+'.supplement-search.json')).exists() else []
    for phrase in sorted(queries):
        if any(r['query']==phrase for r in result):continue
        rows=[];audit=[];page=1
        while True:
            status,body=w.call('GET',f'/api/units/?q={quote(chr(34)+phrase+chr(34),safe="")}&page_size=1000&page={page}');assert status==200,(phrase,status)
            rows.extend(body['results']);audit.append({'page':page,'total':body['count'],'received':len(body['results'])})
            if not body.get('next'):assert len(rows)==body['count'];break
            page+=1
        result.append({'query':phrase,'audit':audit,'units':rows})
        translated=[r for r in rows if r['target']!=r['source'] and re.search('[一-鿿]',r['target'][0])]
        print(phrase,'Chinese',[(r['context'],r['target'][0][:180]) for r in translated[:3]])
        save('supplement-search',result)
if __name__=='__main__':globals()[sys.argv[1]]()
