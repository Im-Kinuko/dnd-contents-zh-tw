"""Prepare World Tree batch 3; publication remains a separate approved step."""
import argparse, difflib, hashlib, html, json, re, subprocess, sys
from pathlib import Path
from urllib.parse import unquote, urljoin, quote
import opencc
from subclasses import read_all, english_text, leaves

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'_incoming/player-handbook'
DATA=BASE/'subclasses/world-tree'
WEB=BASE/'_web/barbarian-subclasses'
PREFIX='subclasses.world-tree.3'
PROJECT='dnd-players-handbook'
KEYS=['Path of the World Tree','Vitality of the Tree','Branches of the Tree','Battering Roots','Travel Along the Tree']
JOURNAL_KEY=KEYS[0]+' journal'
sys.path.insert(0,str(ROOT/'.claude/skills/translation-import/scripts'))
import weblate as w
from html_blocks import Plan, visible_text, compare_html, LABEL
from skeleton import build_entries, draft_sections, norm
from validate import check_description, count_strings
from build_index import entry_names, aliases
from lang_compare import flat

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def load(suffix):return read(DATA/(PREFIX+'.'+suffix+'.json'))
def save(suffix,value):
    DATA.mkdir(parents=True,exist_ok=True)
    (DATA/(PREFIX+'.'+suffix+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=1),encoding='utf-8')
def write(suffix,value):
    DATA.mkdir(parents=True,exist_ok=True)
    (DATA/(PREFIX+'.'+suffix)).write_text(value.rstrip()+'\n',encoding='utf-8')
def digest(suffix):return hashlib.sha256((DATA/(PREFIX+'.'+suffix)).read_bytes()).hexdigest()
def command(script,args,suffix):
    result=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'.claude/skills/translation-import/scripts'/script)]+args,capture_output=True,text=True,encoding='utf-8')
    write(suffix,result.stdout+result.stderr)
    print(result.stdout+result.stderr)
    assert result.returncode==0,(script,result.returncode)

def collect():
    sys.path.insert(0,str(ROOT/'.claude/skills/web-source-extract/scripts'))
    import fetch_site as fetch
    toc=(WEB/'webhelpcontents.html').read_text(encoding='utf-8')
    candidates=sorted(set(urljoin('https://5echm.kagangtuya.top/webhelpcontents.htm',html.unescape(u)) for u in re.findall(r'href="([^"#]+)',toc) if '玩家手册2024/角色职业/野蛮人/' in unquote(u) and '世界树道途' in unquote(u)))
    assert len(candidates)==1,candidates
    url=candidates[0];slug=fetch.slug(url)
    text_path=WEB/(slug+'.txt');raw_path=WEB/'_raw'/(slug+'.html')
    if not text_path.exists():
        raw=fetch.get(url)
        raw_path.parent.mkdir(parents=True,exist_ok=True)
        raw_path.write_text(raw,encoding='utf-8')
        text_path.write_text(fetch.to_text(raw),encoding='utf-8')
    source=text_path.read_text(encoding='utf-8')
    write('source.txt',source)
    converted=opencc.OpenCC('s2twp').convert(source)
    write('source.s2twp.txt',converted)
    source_path=BASE/'_source'/(PREFIX+'.s2twp.txt')
    source_path.parent.mkdir(parents=True,exist_ok=True);source_path.write_text(converted,encoding='utf-8')
    save('source',{'url':url,'decoded_url':unquote(url),'text_path':str(text_path),'html_path':str(raw_path),'converted_path':str(source_path),'status':'ok'})
    manifest_path=WEB/'manifest.json';manifest=read(manifest_path)
    manifest=[r for r in manifest if r['url']!=url]+[{'url':url,'status':'ok','file':slug}]
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=1),encoding='utf-8')
    print('SOURCE',unquote(url))
    print('\n'.join(f'{i}: {line}' for i,line in enumerate(converted.splitlines(),1)))
    for component in ['classes','content']:
        comp=PROJECT+'-'+component
        status,translation=w.call('GET',f'/api/translations/{PROJECT}/{comp}/zh_Hant/')
        assert status==200 and translation['filename']==f'compendium/zh-tw/{PROJECT}/{PROJECT}.{component}.json'
        rows,audit=read_all(PROJECT,comp);units={row['context']:row for row in rows}
        save(component+'.live',{'filename':translation['filename'],'audit':audit,'units':units})
        print(component,'complete',len(rows))
        scope={p:r for p,r in units.items() if any(p.startswith('entries.'+k+'.') for k in KEYS)} if component=='classes' else {p:r for p,r in units.items() if p.startswith('entries.Barbarian.pages.Path of the World Tree.')}
        print(json.dumps({p:{'en':r['source'][0],'zh':r['target'][0]} for p,r in scope.items()},ensure_ascii=False,indent=1))
    for component in ['terms','spells-glossary']:
        rows,audit=read_all('dnd-5e-2024-zh-tw',component);save(component+'.live',{'audit':audit,'units':rows});print(component,'complete',len(rows))
    terms={r['source'][0]:r['target'][0] for r in load('terms.live')['units'] if any(r['target']) and r['target']!=r['source']}
    glossary={r['source'][0]:r['target'][0] for r in load('spells-glossary.live')['units'] if any(r['target']) and r['target']!=r['source']}
    save('term_index',{'terms':terms,'spells_glossary':glossary,'entry_names':{k:dict(v) for k,v in entry_names(str(ROOT/'compendium/zh-tw'),PROJECT).items()},'aliases':aliases(str(ROOT/'.claude/skills/translation-import/glossary.tsv'))})
    command('skeleton.py',['extract','--book',PROJECT,'--component','classes','--keys',*KEYS,'--out',str(DATA/(PREFIX+'.classes.sheet.json'))],'extract.txt')

def search():
    queries=['"This feature includes an activity for"','"This feature includes an Active Effect which can be applied to the target"','"This feature includes an Active Effect which grants you"','"A creature moved by Branches"','"Vitality Surge"','"Life-Giving Force"','"Extended Teleport"','"Subclass Features"','"When you activate your Rage"','"Start of each of your turns while your Rage is active"','"within 10 feet of you"','"Teleport"']
    results=[]
    for query in queries:
        rows=[];pages=[];page=1
        while True:
            status,body=w.call('GET',f'/api/units/?q={quote(query,safe="")}&page_size=1000&page={page}')
            assert status==200,(query,status)
            rows.extend(body['results']);pages.append({'page':page,'status':status,'received':len(body['results']),'total':body['count']})
            if not body.get('next'):
                assert len(rows)==body['count'];break
            page+=1
        results.append({'query':query,'audit':pages,'units':rows})
        print(query,'complete',len(rows))
        exact=[row for row in rows if row['source'][0]==query.strip('"') and row['target'][0]!=row['source'][0] and re.search('[\u3400-\u9fff]',row['target'][0])]
        print('Exact translated units:',[(row['id'],row['target'][0]) for row in exact])
    save('supplement-search',results)

def prepare():
    # Chinese decisions are made here, before any block.zh is filled.
    source=(DATA/(PREFIX+'.source.s2twp.txt')).read_text(encoding='utf-8').splitlines()
    live=load('classes.live')['units']
    intro=[visible_text(b.html) for b in Plan(live['entries.Path of the World Tree.description']['target'][0]).blocks]
    vitality=[visible_text(b.html) for b in Plan(live['entries.Vitality of the Tree.description']['target'][0]).blocks[:3]]
    main={
      KEYS[0]:['世界樹道途',*intro],
      KEYS[1]:['聖樹活力',*vitality],
      KEYS[2]:['靈樹枝杈','你的狂暴啟用期間，每當一名位於你30呎內你所能看見的生物的回合開始時，你可以採取反應在其周圍召喚世界樹的靈體枝條。目標必須成功通過一次力量豁免（DC等於8+你的力量調整值+你的熟練加值），否則將被傳送到位於你5呎內的你所能看見的未佔據空間內或距離你最近的你所能看見的未佔據空間內。目標被你傳送後，你可以令其速度降為0，持續至當前回合結束。'],
      KEYS[3]:['根擊千鈞','世界樹的卷鬚將你的武器延長。你的回合內，你持用的任何具有重型或多用屬性的近戰武器的觸及增加10呎。當你在你的回合內以該武器命中時，除了你正以該武器使用的一種不同精通屬性外，你還可以啟用推離或失衡精通屬性。'],
      KEYS[4]:['世界樹之奇旅','當你啟用狂暴時，你可以傳送至多60呎的距離，到一處你所能看見的未佔據空間中。在你的狂暴啟用期間，你也能夠以一個附贈動作來進行傳送。','此外，每次狂暴期間僅一次，你可以使傳送的距離提升至150呎，並可以選擇帶上至多6個位於你10呎內的自願生物同你一起傳送。每個其他生物都將被傳送至位於你目的地10呎內的你選擇的未佔據空間中。'],
    }
    supplements={
      KEYS[1]:['【Foundry註記】','此特性包含活力如潮與生命賦予的行動，可用來擲出臨時生命值。狂暴結束時，生命賦予的臨時生命值不會自動移除。'],
      KEYS[2]:['【Foundry註記】','此特性包含一項Active Effect，可套用於目標並降低其速度。'],
      KEYS[3]:['【Foundry註記】','此特性包含一項Active Effect，會賦予你推離與失衡精通屬性。'],
    }
    nested={
      KEYS[0]:{'advancement':{'Subclass Features':{next(iter(load('classes.sheet')['entries'][KEYS[0]]['advancement']['Subclass Features'])):'子職業特性'}}},
      KEYS[1]:{'activities':{'Vitality Surge':{'name':'活力如潮','condition':'當你啟用狂暴時'},'Life-Giving Force':{'name':'生命賦予','condition':'狂暴啟用期間，在你每一回合開始時'}}},
      KEYS[2]:{'activities':{'save':{'condition':'你的狂暴啟用期間，每當一名位於你30呎內你所能看見的生物的回合開始時'}},'effects':{'Branches of the Tree':{'name':'靈樹枝杈','description':'被靈樹枝杈傳送的生物，其速度可以降為0，持續至其當前回合結束。'}}},
      KEYS[3]:{'effects':{'Battering Roots':{'name':'根擊千鈞'}}},
      KEYS[4]:{'activities':{'Teleport':{'name':'傳送'},'Extended Teleport':{'name':'延伸傳送','target':'位於你10呎內'}}},
    }
    bounds={KEYS[0]:[(3,3),(4,4)],KEYS[1]:[(7,7),(8,8),(9,10)],KEYS[2]:[(13,13)],KEYS[3]:[(15,15)],KEYS[4]:[(17,17),(18,18)]}
    original={
      KEYS[0]:[source[2],source[3]],
      KEYS[1]:[source[6],source[7],source[8]+source[9]],
      KEYS[2]:[source[12]],KEYS[3]:[source[14]],KEYS[4]:[source[16],source[17]],
    }
    # English repetitions within Chinese source headings are metadata, not prose.
    original[KEYS[1]][1]=original[KEYS[1]][1].replace('Vitality Surge 。','。')
    original[KEYS[1]][2]=original[KEYS[1]][2].replace('Life-GivingForce 。','。')
    sourcecheck='\n\n'.join(main[k][0]+' '+k+'\n'+'\n'.join(original[k]) for k in KEYS)
    sourcecheck+='\n\n'+main[KEYS[0]][0]+' '+JOURNAL_KEY+'\n'+'\n'.join(original[KEYS[0]])
    write('source.segmented.s2twp.txt',sourcecheck)
    sections=[]
    for key in KEYS:
        parts=['### '+key,'名稱：'+main[key][0],*main[key][1:]]
        if supplements.get(key) or nested.get(key):
            parts+=['〔EN 補翻／獨立介面欄位〕',*supplements.get(key,[])]
            parts += [path+'：'+value for path,value in leaves(nested.get(key,{}))]
        sections.append('\n'.join(parts))
    sections.append('### '+JOURNAL_KEY+'\n名稱：'+main[KEYS[0]][0]+'\n'+'\n'.join(main[KEYS[0]][1:]))
    write('draft.txt','\n\n'.join(sections))
    save('draft-data',{'main':main,'supplements':supplements,'nested':nested,'bounds':bounds,'original':original})
    changes=[]
    for key in KEYS:
        for index,(old,new) in enumerate(zip(original[key],main[key][1:]),1):
            for tag,a,b,c,d in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
                if tag=='equal':continue
                before,after=old[a:b],new[c:d]
                if key in KEYS[:2]:
                    category='禁用字' if '它' in before else '定案詞'
                    reason='沿用同語境Weblate已接受正文（unit '+str(live['entries.'+key+'.description']['id'])+'）；不改既有中文，原稿差異另完整列報。'
                elif before in ['尺','詞條'] or '精通詞條' in before:
                    category='定案詞';reason='呎與武器／精通屬性用字依conventions及terms Property→屬性。'
                elif before in [',',':','(',')']:
                    category='禁用字';reason='中文全形標點格式；數值與語意不變。'
                elif key==KEYS[3] and index==1 and (a>old.find('除了') and a<old.find('你還可以')):
                    category='規則';reason='a different mastery property you\'re using：限於你正使用的一種不同精通屬性，不是武器本身所有精通。'
                else:
                    category='句式';reason='可見性、主語、take a Reaction及must succeed句式依conventions；規則條件與數值不變。'
                changes.append({'entry':key,'paragraph':index,'before':before,'after':after,'category':category,'reason':reason})
    save('changes',changes)
    from draft_diff import best_match,fragments
    toolchanges=[]
    for key in [*KEYS,JOURNAL_KEY]:
        sourcekey=KEYS[0] if key==JOURNAL_KEY else key
        for index,new in enumerate(main[sourcekey][1:],1):
            ratio,a,b,old=best_match(new,original[sourcekey])
            registered=[r for r in changes if r['entry']==sourcekey and r['paragraph']==index]
            toolchanges.append({'entry':key,'paragraph':index,'ratio':ratio,'matched_source':old,'draft':new,'fragments':fragments(old,new),'registrations':registered,'basis':'保留同語境已接受正文，依使用者指示不改。' if sourcekey in KEYS[:2] else ('精通屬性限制依EN修正；其餘為已裁定詞與格式。' if sourcekey==KEYS[3] else '呎、可見性、反應與豁免句式依conventions；數值限制不變。')})
    save('draft-diff-register',toolchanges)
    # Audit all visible fields including names; key labels are intentionally kept.
    sheet=load('classes.sheet');audit=json.loads(json.dumps(sheet))
    for key,row in audit['entries'].items():row['blocks'].append({'id':'name-audit','en':key})
    journal=read(ROOT/f'compendium/en/{PROJECT}/{PROJECT}.content.json')['entries']['Barbarian']['pages'][KEYS[0]]
    audit['entries'][JOURNAL_KEY]={'name_en':KEYS[0],'blocks':[{'id':b.id,'en':b.html} for b in Plan(journal['description']).blocks]+[{'id':'name-audit','en':KEYS[0]}]}
    save('audit.sheet',audit)
    save('ack',{'Branches of the Tree|take':'take a Reaction 為採取反應，依使用者句式裁定；不是承受傷害。'})
    save('draft-fingerprints',{'draft.txt':digest('draft.txt')})
    command('draft_diff.py',['--source',str(DATA/(PREFIX+'.source.segmented.s2twp.txt')),'--draft',str(DATA/(PREFIX+'.draft.txt')),'--out',str(DATA/(PREFIX+'.draft-diff.md'))],'draft-diff.log.txt')
    command('terms_check.py',[str(DATA/(PREFIX+'.audit.sheet.json')),'--draft',str(DATA/(PREFIX+'.draft.txt')),'--index',str(DATA/(PREFIX+'.term_index.json')),'--ack',str(DATA/(PREFIX+'.ack.json')),'--out',str(DATA/(PREFIX+'.terms-report.md'))],'terms-report.log.txt')
    command('lang_compare.py',[str(DATA/(PREFIX+'.audit.sheet.json')),'--draft',str(DATA/(PREFIX+'.draft.txt'))],'lang-report.md')

def enrich(en,line):
    for token,label in [(m[1],m[2]) for m in LABEL.finditer(en)]:
        if token.startswith('@UUID['):
            assert label==KEYS[0] and '世界樹道途' in line
            line=line.replace('世界樹道途',token+'{世界樹道途}',1)
        elif token.startswith('@Embed['):assert not line
        else:raise AssertionError(token)
    names={'Foundry Note':'【Foundry註記】','Vitality Surge':'活力如潮','Life-Giving Force':'生命賦予'}
    for word in re.findall(r'<strong>(.*?)</strong>',en,re.S):
        chosen=names[word.strip().rstrip('.')]
        if word.endswith('.'):chosen='【'+chosen+'】'
        assert chosen in line,(word,line)
        line=line.replace(chosen,'<strong>'+chosen+'</strong>',1)
    return line

def map_draft():
    data=load('draft-data');main,supp,nested=data['main'],data['supplements'],data['nested']
    for suffix,h in load('draft-fingerprints').items():assert digest(suffix)==h,'Draft changed; re-run prepare'
    sheet=load('classes.sheet');local=read(ROOT/f'compendium/en/{PROJECT}/{PROJECT}.classes.json')['entries']
    # A shared workspace may receive a new EN export while a batch is prepared.
    extracted=load('audit.sheet')['entries']
    for key in KEYS:
        if any(extracted[key].get(f)!=local[key].get(f) for f in ['activities','effects','advancement']):
            raise SystemExit('EN模板已更新：'+key+'。先重新extract並核對新版Weblate來源，再重建底稿檢查；不得沿用舊sheet。')
    live=load('classes.live')['units'];audit=[]
    for key,row in sheet['entries'].items():
        row['name']=main[key][0]
        body=main[key][1:]+supp.get(key,[])
        assert len(body)==len(row['blocks'])
        for i,(block,line) in enumerate(zip(row['blocks'],body)):
            retained=key==KEYS[0] or key==KEYS[1] and i<3
            added=i>=len(main[key])-1
            zh=Plan(live['entries.'+key+'.description']['target'][0]).blocks[i].html if retained else enrich(block['en'],line)
            assert visible_text(zh)==line and not compare_html(block['en'],zh)
            block['zh']=zh;block['source']='supplement' if added else 'draft'
            block['basis']='原稿無Foundry註記；全站Weblate英文原句片段查詢成功，無同句中文。以既有行動名與相關註記句式補翻，詳supplement-basis。' if added else ''
            audit.append({'entry':key,'path':'entries.'+key+'.description/'+block['id'],'en':english_text(block['en']),'source':data['original'][key][i] if not added else '無原稿','draft':line,'source_lines':data['bounds'][key][i] if not added else None,'retained':retained,'supplement':added})
        for field in ['activities','effects','advancement']:
            if field in nested.get(key,{}):
                row[field]=json.loads(json.dumps(nested[key][field]))
                for label,value in row[field].items():
                    if 'description' in value:value['description']='<p>'+value['description']+'</p>'
    save('classes.sheet',sheet)
    # Run the common builder; all visible Chinese is already in the independent draft.
    command('skeleton.py',['build',str(DATA/(PREFIX+'.classes.sheet.json')),'--draft',str(DATA/(PREFIX+'.draft.txt')),'--out',str(DATA/(PREFIX+'.classes.aligned.json'))],'mapping.log.txt')
    built=load('classes.aligned')
    retained=[];changed={}
    unresolved='entries.Branches of the Tree.effects.Branches of the Tree.description'
    ruling_path=DATA/(PREFIX+'.effect-ruling.json')
    ruling=read(ruling_path) if ruling_path.exists() else {'resolved':False,'approved':False,'en':live[unresolved]['source'][0],'proposal':nested[KEYS[2]]['effects'][KEYS[2]]['description'],'basis':'正文reduce its Speed to 0 until the end of the current turn；英文效果摘要缺0且所有格錯置。'}
    save('effect-ruling',ruling)
    for path,zh in leaves(built):
        en=live[path]['source'][0];old=live[path]['target'][0]
        assert dict(leaves({'entries':{k:local[k] for k in KEYS}}))[path]==en,'Live EN drift: '+path
        if old==zh:retained.append({'path':path,'en':en,'zh':zh,'reason':'同語境已接受且規則語意相符，原樣保留、排除payload。'})
        if path not in {'entries.'+key+'.description' for key in KEYS}:
            isname=path.endswith('.name') and path.count('.')==2
            audit.append({'entry':path.split('.')[1],'path':path,'en':english_text(en),'source':'名稱取原稿標題；移除等級與英文並列索引。' if isname else ('既有Weblate譯文' if old==zh else '无原稿獨立介面欄位'.replace('无','無')),'draft':visible_text(zh),'source_lines':{'Path of the World Tree':[2,2],'Vitality of the Tree':[5,6],'Branches of the Tree':[11,12],'Battering Roots':[14,14],'Travel Along the Tree':[16,16]}.get(path.split('.')[1]) if isname else None,'retained':old==zh,'supplement':not isname,'pending':path==unresolved and not ruling['resolved']})
        if old==zh or path==unresolved and not ruling['resolved']:continue
        target=changed;parts=path.split('.')
        for part in parts[:-1]:target=target.setdefault(part,{})
        target[parts[-1]]=zh
    journal=read(ROOT/f'compendium/en/{PROJECT}/{PROJECT}.content.json')['entries']['Barbarian']['pages'][KEYS[0]]
    plan=Plan(journal['description']);replacements={};i=0
    for block in plan.blocks:
        if not english_text(block.html):zh=block.html;line='';bounds=None
        else:
            line=main[KEYS[0]][i+1];bounds=data['bounds'][KEYS[0]][i];i+=1
            zh=enrich(block.html,line)
        assert visible_text(zh)==line and not compare_html(block.html,zh)
        replacements[block.id]=zh
        audit.append({'entry':JOURNAL_KEY,'path':'entries.Barbarian.pages.'+KEYS[0]+'.description/'+block.id,'en':english_text(block.html),'source':data['original'][KEYS[0]][i-1] if bounds else '@Embed插圖無可見文字','draft':line,'source_lines':bounds,'retained':False,'supplement':False,'protected':bounds is None})
    assert i==2
    content={'entries':{'Barbarian':{'pages':{KEYS[0]:{'name':main[KEYS[0]][0],'description':plan.build(replacements)}}}}}
    audit.append({'entry':JOURNAL_KEY,'path':'entries.Barbarian.pages.'+KEYS[0]+'.name','en':KEYS[0],'source':'既有對應class名稱世界樹道途','draft':main[KEYS[0]][0],'source_lines':[2,2],'retained':False,'supplement':False})
    save('content.aligned',content)
    for component,value in [('classes',built),('content',content)]:
        for path,zh in leaves(value):
            en=load(component+'.live')['units'][path]['source'][0]
            assert not check_description(en,zh,{'Foundry','Active','Effect'}),(path,check_description(en,zh,{'Foundry','Active','Effect'}))
            assert not compare_html(en,zh),(path,compare_html(en,zh))
            assert not re.search('它|如果|發充能|施展',visible_text(zh)),path
            if component=='content':assert dict(leaves({'entries':{'Barbarian':{'pages':{KEYS[0]:journal}}}}))[path]==en
    command('validate.py',[str(DATA/(PREFIX+'.classes.aligned.json')),'--book',PROJECT,'--component','classes','--allow','Active,Effect','--out',str(DATA/(PREFIX+'.classes.validated.json'))],'validation.txt')
    assert load('classes.validated')==built
    for path,zh in leaves(changed):assert dict(leaves(built))[path]==zh
    save('classes.upload',changed);save('content.upload',content)
    save('retained',retained);save('mapping-audit',audit)
    for suffix,h in load('draft-fingerprints').items():assert digest(suffix)==h
    save('verification',{'version':'v1','classes_entries':len(changed['entries']),'classes_strings':count_strings(changed),'content_entries':1,'content_strings':count_strings(content),'retained_strings':len(retained),'retained_body_blocks':sum(r['retained'] for r in audit if '.description/' in r['path']),'mapped_positions':len(audit),'all_exact_draft_matches':True,'mechanical_pass':True,'live_en_match':True,'draft_check_pass':True,'terms_check_pass':True,'pending_fields':[] if ruling['resolved'] else [unresolved],'draft_sha256':load('draft-fingerprints'),'payload_sha256':{c:digest(c+'.upload.json') for c in ['classes','content']},'approved':False,'uploaded':False})
    print(json.dumps(load('verification'),ensure_ascii=False,indent=1))

LANG_REASONS={
 'applied':'EN是可套用於目標，未宣稱已套用；使用可套用，不採UI完成狀態的已套用。',
 'creatures':'底稿明寫至多6個位於你10呎內的自願生物；EN沒有{number}變數，不插入UI模板。',
 'current':'current turn為當前回合，不是UI當前值／目前進度。',
 'each creature':'原稿每個其他生物指同行生物，保留完整限制，不為符合短UI字串刪去其他。',
 'effect':'Foundry Active Effect依使用者裁定保留英文。',
 'force':'Life-Giving Force是特性小標，沿用既有生命賦予；不是力場傷害。',
 'material':'Material Plane為物質位面，不是法術構材或材料。',
 'number':'臨時生命值的數值及d6數量，沿用已接受正文；不是介面數字標籤。',
 'points':'Hit Points沿用臨時生命值，不拆成點數。',
 'roll':'既有正文使用擲，補翻使用擲出；保留語意相符的既有句，不改成UI擲骰字串。',
 'saving throw':'使用已裁定成功通過一次力量豁免句式，不以UI豁免檢定／豁免骰改写正文。'.replace('写','寫'),
 'temporary':'Temporary Hit Points使用臨時生命值；不是UI暫時效果狀態。',
 'temporary hp':'Foundry註記使用完整臨時生命值，不採UI簡稱臨時HP。',
 'three':'@Embed的classes="three right"為保護參數，不是可見數字，不翻譯。',
 'willing creatures':'底稿為6個位於你10呎內的自願生物；量詞和名詞之間保留資格限制，不插入UI模板。',
}

def supplemental_basis(row):
    path=row['path'];en=row['en'];zh=row['draft']
    if not row.get('supplement'):return ''
    if path.endswith('advancement.Subclass Features.name'):
        return '原稿無獨立欄位；全站同句查詢有既有子職業特性（unit109543 folders.Subclass Features等）；原樣沿用，舊title對應新name。'
    if path.endswith('activities.Teleport.name'):
        return '原稿無行動名；全站精確EN匹配unit118203，PHB feats/Boon of Dimensional Travel.activities.Teleport.name：傳送；原樣沿用。'
    if path.endswith('activities.Extended Teleport.name'):
        return '原稿無行動名；全站Extended Teleport查詢成功6筆，未有同句中文；依150呎擴充傳送自譯延伸傳送。'
    if path.endswith('effects.Branches of the Tree.description'):
        return '原稿無獨立效果摘要；全站英文查詢成功4筆，未有同句中文；依原稿13行及EN完整正文，使用者2026-10-09已確認補速度0。'
    if 'Vitality Surge.name' in path or 'Life-Giving Force.name' in path:
        return '原稿無獨立行動名；全站查詢成功但該欄位未有中文，依同語境已接受正文小標（unit109783）原樣沿用活力如潮／生命賦予，不另用原稿活力之湧／賜命之源。'
    if '.condition' in path or '.target' in path:
        return '原稿無獨立介面欄位；全站原句／片段查詢成功，未有可直接沿用的同句中文；依該特性完整正文與底稿摘取。狂暴、可見性、距離及每回合條件均核對；your Raging依正文解為狂暴啟用期間。'
    if '.effects.' in path and path.endswith('.name'):
        return '原稿無獨立效果名；直接採同特性的原稿名稱靈樹枝杈／根擊千鈞，不另造名稱。'
    if row.get('source')=='無原稿':
        if zh=='【Foundry註記】':return '原稿缺Foundry小標；沿用PHB已接受【Foundry註記】格式（unit109701）。'
        if row['entry']==KEYS[1]:return '全站查詢This feature includes an activity for成功41筆，未有此完整註記的中文；以unit109701行動註記句式為底補翻，行動名取本條已接受小標，保留狂暴結束不自動移除限制。'
        if row['entry']==KEYS[2]:return '全站查詢This feature includes an Active Effect which can be applied to the target成功4筆，未有同句中文；自譯，沿用使用者Active Effect裁定與速度用字。'
        if row['entry']==KEYS[3]:return '全站查詢This feature includes an Active Effect which grants you成功12筆，未有同句中文；參照unit118269真實視覺註記的此特性包含／賦予句式，改為推離與失衡，Active Effect依裁定保留英文。'
    return '原稿無此獨立欄位；從獨立底稿及本條原稿名稱衍生；全部補翻仍只送建議。'

def review():
    info=load('verification');audit=load('mapping-audit');data=load('draft-data');source=(DATA/(PREFIX+'.source.s2twp.txt')).read_text(encoding='utf-8').splitlines()
    changes=load('changes');diff=load('draft-diff-register');basis=[]
    link=lambda suffix,label:'['+label+']('+str(DATA/(PREFIX+'.'+suffix)).replace('\\','/')+')'
    esc=lambda v:str(v).replace('|','\\|').replace('\n','<br>')
    table=lambda cols:'| '+' | '.join(esc(x) for x in cols)+' |'
    for row in audit:
        row['basis']=supplemental_basis(row)
        if row.get('supplement'):basis.append({'path':row['path'],'en':row['en'],'zh':row['draft'],'basis':row['basis']})
    save('supplement-basis',basis)
    # Every fragment emitted by draft_diff receives an explicit registration.
    registered=[]
    for r in diff:
        srckey=KEYS[0] if r['entry']==JOURNAL_KEY else r['entry']
        for fragment in r['fragments']:
            before,after=re.match('「(.*?)」→「(.*?)」',fragment,re.S).groups()
            if srckey in KEYS[:2]:category='定案詞';reason=r['basis']+'來源為同語境現行Weblate，原稿與既有譯文差異並列，不代表本次改了已接受正文。'
            elif before and set(before)<=set(',():'):
                category='禁用字';reason='中文全形標點慣例，語意與數值不變。'
            elif '詞條' in before or '屬性' in after or before=='尺' or '呎' in after:
                category='定案詞';reason='依武器／精通屬性、呎的已裁定用字；保留EN距離數值。'
            elif srckey==KEYS[3] and before in ['啟用這把','本身具有','其他']:
                category='規則';reason='a different mastery property you\'re using：你正使用的一種不同精通屬性。'
            else:category='句式';reason='依conventions可見性、主語、可以採取反應、成功通過的已裁定句式。'
            registered.append({'entry':r['entry'],'paragraph':r['paragraph'],'fragment':fragment,'category':category,'reason':reason})
    assert len(registered)==sum(len(r['fragments']) for r in diff)
    save('fragment-register',registered)
    missing=[]
    for line in (DATA/(PREFIX+'.lang-report.md')).read_text(encoding='utf-8').splitlines():
        if '| 無 |' in line:
            term=line.split('|')[1].strip();assert term in LANG_REASONS,term
            missing.append({'en':term,'reason':LANG_REASONS[term]})
    save('lang-resolutions',missing)
    preview=['# 世界樹道途第3批 v1：確認版预覽'.replace('预','預'),'','## 1. 標頭','', '2026-10-09。使用者「好OK，可以上傳」已確認本批及依正文補0；本預覽先完成驗收，尚未送出。', '', f'{info["classes_entries"]}個classes條目、{info["classes_strings"]}個字串；另1個日誌頁、{info["content_strings"]}個字串。共{info["classes_strings"]+info["content_strings"]}個待送建議字串；未超過10條／60字串。', '', '來源：['+load('source')['decoded_url']+']('+load('source')['url']+')；'+link('source.s2twp.txt','原稿轉繁全文18行')+'。原稿對照：2–4介紹、5–10聖樹活力、11–13靈樹枝杈、14–15根擊千鈞、16–18世界樹之奇旅。', '', '- '+link('draft.txt','獨立底稿')+'；'+link('classes.sheet.json','新版EN映射sheet')+'。','- '+link('classes.aligned.json','classes完整成品')+'；'+link('content.aligned.json','日誌完整成品')+'。','- '+link('classes.upload.json','classes實際payload')+'；'+link('content.upload.json','content實際payload')+'。', '', 'classes SHA-256：`'+info['payload_sha256']['classes']+'`。','content SHA-256：`'+info['payload_sha256']['content']+'`。','底稿 SHA-256：`'+info['draft_sha256']['draft.txt']+'`。','', '## 2. 做法','', '本批5條特性及同名日誌都有原稿，整條無原稿0條，原稿無EN對應的內容0段。原稿跨行的標題合併：5+6、11+12；賜命之源9+10合併。原稿等級與英中並列標題是索引資料，不插入EN正文；正文轉為中文全形標點，其他修改逐處登記。', '', '依使用者指示，Path of the World Tree既有name、description全欄位排除payload；介紹2個區塊、Vitality of the Tree3個已接受正文區塊逐字與原HTML保留。聖樹活力description只補翻仍為英文的Foundry註記。小標及行動名稱沿用已接受活力如潮／生命賦予，不改回原稿活力之湧／賜命之源。日誌沿用相同class介紹，再加回原UUID。', '', 'Weblate現行classes已同步新版（'+str(len(load('classes.live')['units']))+'單元），content'+str(len(load('content.live')['units']))+'單元；兩者均完整分頁成功。原title已改為name且此新欄位尚是英文，沿用已有「子職業特性」並以新版name路徑送建議。全檔版本比對是前一階段的歷史快照，當時Weblate尚舊版；本次上傳以重新核對的新快照為準。','', '## 3. 逐段／全部欄位對照','',f'全部{len(audit)}個映射位置（含1個純Embed保護區塊）如下。原稿、EN、既有譯文與底稿全部列出，不以摘要取代有問題句子。','', '| 區塊／欄位 | EN全文 | 原稿／既有來源 | 底稿全文 | 修改與理由 |','|---|---|---|---|---|']
    for row in audit:
        bounds=row['source_lines'];raw='\n'.join(source[bounds[0]-1:bounds[1]]) if bounds else row['source']
        if row.get('protected'):reason='無可見文字；@Embed與caption／classes參數原樣保留。'
        elif row.get('supplement'):reason=row['basis']
        elif row['retained']:reason='無修改（相對既有Weblate）；原稿差異見下方修改登記與保留項。'
        elif '.description/b' in row['path']:
            matching=[r for r in diff if r['entry']==row['entry'] and r['draft']==row['draft']]
            reason='；'.join(f['fragment']+'｜'+f['category']+'｜'+f['reason'] for f in registered if matching and f['entry']==matching[0]['entry'] and f['paragraph']==matching[0]['paragraph']) or '無修改；整段取底稿。'
        else:reason='移除等級／英文索引、合併跨行標題｜句式｜EN name僅顯示中文名稱；數值等級由原資料保留。'
        if row.get('retained'):raw+='\n既有Weblate：'+row['draft']
        preview.append(table([row['path'],row['en'],raw,row['draft'],reason]))
    preview+=['','### draft_diff原始報告','',(DATA/(PREFIX+'.draft-diff.md')).read_text(encoding='utf-8'),'','### 每個工具差異片段的修改登記','', '| 條目／段落 | 原→新 | 類別 | 理由 |','|---|---|---|---|']
    for r in registered:preview.append(table([r['entry']+'/p'+str(r['paragraph']),r['fragment'],r['category'],r['reason']]))
    preview+=['','改動大段落的理由：介紹與聖樹活力的段落差異來自沿用同語境已接受正文，對既有譯文沒有修改；根擊千鈞須修正正在使用的一種不同精通屬性，其他改動僅為定案詞／標點。日誌介紹複用同段底稿，來源仍是原稿3–4行。','', '## 4. 規則差異','', '### 根擊千鈞：已改','', 'EN：'+next(r['en'] for r in audit if r['path']=='entries.Battering Roots.description/b0001'),'','原稿：'+source[14],'','底稿：'+data['main'][KEYS[3]][1],'','理由：a different mastery property you’re using with that weapon 是正在使用的一種不同精通屬性，原稿武器本身具有的其他精通範圍不準確。你的回合、重型或多用、觸及增加10呎、命中後推離或失衡均保留。','', '### 靈樹枝杈效果摘要：已依使用者裁定補0','', 'EN：'+load('effect-ruling')['en'],'','原稿正文13行：'+source[12],'','EN完整正文：After the target teleports, you can reduce its Speed to 0 until the end of the current turn.','','底稿：'+load('effect-ruling')['proposal'],'','理由：摘要漏數值且所有格錯置；新版仍未修正。使用者貼出完整正文確認後明示「好OK，可以上傳」，依正文補速度0，持續至該生物當前回合結束。','', '## 5. 保留項','', '以下是原稿／既有譯文與EN的敘事或措辭差異，依使用者保留既有翻譯及原稿要求處理，不自行重譯。','', '| EN原句／區塊 | 原稿／既有 | 保留與理由 |','|---|---|---|']
    retained_notes=[
      (next(r['en'] for r in audit if r['path']=='entries.Path of the World Tree.description/b0001'),source[2]+'；既有：'+data['main'][KEYS[0]][1],'Roots/Branches原稿根系／枝杈、既有根源／分支，既有措辭未改；日誌共用既有。'),
      (next(r['en'] for r in audit if r['path']=='entries.Path of the World Tree.description/b0002'),source[3]+'；既有：'+data['main'][KEYS[0]][2],'Yggdrasil原稿尤格德拉希爾／既有伊格德拉希爾；ENconnecting them to each other and the Material Plane，既有未明寫彼此相連；屬敘事細節，既有介紹原樣保留。世界樹／世界之樹並存、工具／手段措辭亦不改。'),
      (next(r['en'] for r in audit if r['path']=='entries.Vitality of the Tree.description/b0001'),source[6]+'；既有：'+data['main'][KEYS[1]][1],'taps into為汲取，原稿浸潤著；既有汲取符合EN。以下→下列既有已符合裁定。'),
      (next(r['en'] for r in audit if r['path']=='entries.Vitality of the Tree.description/b0002'),source[7]+'；既有：'+data['main'][KEYS[1]][2],'活力之湧→活力如潮僅取已接受小標為行動名，不改既有正文。'),
      (next(r['en'] for r in audit if r['path']=='entries.Vitality of the Tree.description/b0003'),source[8]+source[9]+'；既有：'+data['main'][KEYS[1]][3],'賜命之源→生命賦予；既有「他們」指擲出的d6，文字用法保留。每回合開始、另一個生物、10呎、骰數與狂暴傷害加值、剩餘臨時生命值消失全部符合EN。'),
      ('During your turn, your reach is 10 feet greater with any Melee weapon that has the Heavy or Versatile property, as tendrils of the World Tree extend from you.',source[14].split('。')[0]+'。','原稿將卷鬚描寫為延長武器，EN為卷鬚從你延伸；敘事保留原稿，實際規則仍是限定武器觸及增加10呎。'),
    ]
    for row in retained_notes:preview.append(table(row))
    preview+=['', '## 6. 術語報告','', 'terms '+str(len(load('terms.live')['units']))+'筆、spells-glossary '+str(len(load('spells-glossary.live')['units']))+'筆完整讀取成功。本批無法術名，未使用spell_names或新增正式詞條。','',(DATA/(PREFIX+'.terms-report.md')).read_text(encoding='utf-8'),'','ack逐條：','']
    for key,reason in load('ack').items():preview.append('- '+key+'：'+reason)
    preview+=['','額外人工回查：property／mastery property使用屬性／精通屬性，Heavy重型、Versatile多用、Push推離、Topple失衡與lang一致；Rage狂暴、Temporary Hit Points臨時生命值、Proficiency Bonus熟練加值、Strength力量、Speed速度沿用已接受語境及原稿。terms工具對單字大寫詞有大小寫界線，未以3項工具命中聲稱涵蓋所有術語。','',(DATA/(PREFIX+'.lang-report.md')).read_text(encoding='utf-8'),'','lang所有「無」逐條說明：','']
    for r in missing:preview.append('- '+r['en']+'：'+r['reason'])
    preview+=['', '## 7. 限定詞逐句核對','', '| 完整EN句段 | 完整中文句段 | 核對 |','|---|---|---|']
    qualified=[]
    for r in audit:
        words=re.findall(r'\b(?:this|these|that|the|following|one of|each|any|all)\b',r['en'],re.I)
        if not words:continue
        reason='已核對：'+', '.join(sorted(set(x.lower() for x in words)))+'；主體、指涉、單複數與範圍保留。'
        if r['entry'] in [KEYS[0],JOURNAL_KEY]:reason+='既有敘事省略外層位面彼此連接，已列保留項。'
        if r['entry']==KEYS[3]:reason+='any保留任何；that weapon保留該武器，different為一種不同且正使用。'
        if r['entry']==KEYS[4]:reason+='that teleport指前段同一传送；each creature指同行自願生物，每個其他生物均傳至目的地10呎內所選空間。'.replace('传','傳')
        if r['entry']==KEYS[1]:reason+='each每回合、another另一個生物、these僅指此特性賦予的臨時生命值；現有剩餘時消失的條件保留。'
        preview.append(table([r['en'],r['draft'],reason]));qualified.append({'path':r['path'],'en':r['en'],'zh':r['draft'],'result':reason})
    save('qualifier-review',qualified)
    preview+=['', '## 8. 補翻清單與conditions','', '| 欄位 | EN完整原句 | 中文 | 依據 |','|---|---|---|---|']
    for r in basis:preview.append(table([r['path'],r['en'],r['zh'],r['basis']]))
    preview+=['','### 全部activities.condition','', '| 欄位 | EN原句 | 中文 |','|---|---|---|']
    for r in audit:
        if '.activities.' in r['path'] and r['path'].endswith('.condition'):preview.append(table([r['path'],r['en'],r['draft']]))
    preview+=['','## 9. 四項驗收','', '- 規則：狂暴啟用／每回合開始、另一名生物10呎、d6骰數、剩餘臨時生命值、30呎可見生物、反應、力量DC8+力量調整值+熟練加值、5呎或最近空間、速度0至當前回合結束、自己回合的重型或多用觸及+10呎與精通、60／150呎傳送、每次狂暴僅一次增程、至多6個自願生物及兩個10呎範圍，逐句核對完成。','- 術語：draft_diff.py及terms_check.py均回傳0；3項terms命中全部處理、1項take a Reaction例外逐條登記。lang每個無逐條解釋，最終payload禁用字回查無它／如果／發充能／施展。','- 機械：validate.py對完整classes5條22字串通過，排除2個原樣既有欄位形成20字串payload；content2個頁面欄位以check_description、compare_html及EN逐欄比對驗證（共用CLI不覆蓋pages）。'+str(info['mapped_positions'])+'個映射位置核對，完整段落來自底稿，HTML、section屬性、UUID、Embed與參數保留。','- 中文通讀：獨立通讀底稿及最終中文後回查EN；條件與結果可辨，改動僅在已允許類別。既有介紹與聖樹活力正文逐字保留；映射沒有另造句子。','', '## 10. 待裁定','', '無。本批使用者已同意依完整正文補0並上傳；保留項與補翻已完整披露。其他職業／上一批因全檔更新而需要重配的內容不屬本次上傳範圍。','', '## 11. 修訂紀錄','', '- 2026-10-09：使用者要求先比對新classes.json；已完成全檔歷史比對。','- 2026-10-09：使用者貼靈樹枝杈正文確認reduce its Speed to 0；本次「好OK，可以上傳」確認補0及本批建議。','- 上傳前重新extract、對齊新advancement.name，沿用子職業特性；不送舊title。最終payload與雜湊見標頭。']
    write('preview.md','\n'.join(preview))
    write('full-comparison.md','\n'.join(preview[preview.index('## 3. 逐段／全部欄位對照'):]))
    # A plain HTML reading copy exposes secret notes as well as all nested fields.
    parts=['<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>世界樹道途第3批</title><style>body{font:16px/1.8 system-ui,"Microsoft JhengHei";max-width:960px;margin:40px auto;padding:24px;background:#f9f8f5;color:#243239}article{border-top:1px solid #bbb;margin-top:32px}section.secret{background:#efefeb;padding:12px}pre{white-space:pre-wrap}h1,h2{line-height:1.4}</style><h1>世界樹道途第3批 v1</h1><p>22個建議字串；使用者已確認，尚未送出。</p>']
    for key,item in load('classes.aligned')['entries'].items():
        parts+=['<article><h2>'+html.escape(item['name'])+'</h2>'+item['description']]
        for path,value in leaves(item):
            if path not in ['name','description']:parts+=['<p><code>'+html.escape(path)+'</code></p><div>'+value+'</div>']
        parts+=['</article>']
    journal=load('content.aligned')['entries']['Barbarian']['pages'][KEYS[0]]
    parts+=['<article><h2>日誌：'+journal['name']+'</h2>'+re.sub(r'@UUID\[[^\]]+\]\{([^}]+)\}',r'\1',re.sub(r'@Embed\[[^\]]+\]','〔插圖Embed原樣保留〕',journal['description']))+'</article></html>']
    write('preview.html','\n'.join(parts))
    info.update(rule_review_complete=True,terminology_review_complete=True,chinese_readthrough_complete=True,preview_complete=True,all_exact_draft_matches=True,fragment_registrations=len(registered),qualifier_review_positions=len(qualified),supplement_positions=len(basis),lang_missing_resolved=len(missing))
    save('verification',info)
    print(json.dumps(info,ensure_ascii=False,indent=1))

APPROVED_HASHES={
 'classes':'577a38042f0caa8d8826ba5c392b43595e61ffa73aca041bfa577a1d2ae4e079',
 'content':'3e2963fcc4787afcacfa7090d1b9a11fa0d1058c9c2fe7d50d1b93115f39ff50',
}

def checked_payloads():
    info=load('verification')
    assert info['version']=='v1' and not info['pending_fields']
    assert info['payload_sha256']==APPROVED_HASHES
    for flag in ['mechanical_pass','all_exact_draft_matches','live_en_match','draft_check_pass','terms_check_pass','rule_review_complete','terminology_review_complete','chinese_readthrough_complete','preview_complete']:assert info[flag],flag
    ruling=load('effect-ruling');assert ruling['resolved'] and ruling['approved'] and ruling['authorization']=='好OK，可以上傳'
    assert digest('draft.txt')==info['draft_sha256']['draft.txt']
    expected={}
    for component,sha in APPROVED_HASHES.items():
        assert digest(component+'.upload.json')==sha
        value=load(component+'.upload');expected[component]=dict(leaves(value))
        assert len(expected[component])=={'classes':20,'content':2}[component]
        for path,zh in expected[component].items():
            assert not check_description(load(component+'.live')['units'][path]['source'][0],zh,{'Foundry','Active','Effect'})
    assert expected['classes']['entries.Branches of the Tree.effects.Branches of the Tree.description']=='<p>'+ruling['proposal']+'</p>'
    assert expected['classes']['entries.Path of the World Tree.advancement.Subclass Features.name']=='子職業特性'
    for row in load('retained'):assert row['path'] not in expected['classes']
    old=Plan(load('classes.live')['units']['entries.Vitality of the Tree.description']['target'][0]).blocks
    new=Plan(expected['classes']['entries.Vitality of the Tree.description']).blocks
    assert [b.html for b in old[:3]]==[b.html for b in new[:3]]
    return expected

def preflight():
    expected=checked_payloads();records={}
    for component in expected:
        slug=PROJECT+'-'+component
        command('weblate.py',['status',PROJECT,slug],component+'.status.txt')
        status,translation=w.call('GET',f'/api/translations/{PROJECT}/{slug}/zh_Hant/')
        filename=f'compendium/zh-tw/{PROJECT}/{PROJECT}.{component}.json'
        assert status==200 and translation['filename']==filename
        status,settings=w.call('GET',f'/api/components/{PROJECT}/{slug}/')
        assert status==200 and settings.get('push')
        status,repo=w.call('GET',f'/api/components/{PROJECT}/{slug}/repository/')
        assert status==200 and not repo.get('merge_failure')
        rows,pagination=read_all(PROJECT,slug);all_units={r['context']:r for r in rows}
        reviewed=load(component+'.live')['units']
        for path,zh in expected[component].items():
            assert path in all_units and all_units[path]['source']==reviewed[path]['source'],'EN changed: '+path
            assert all_units[path]['target']==reviewed[path]['target'],'Accepted Chinese changed: '+path
        if component=='classes':
            for row in load('retained'):assert all_units[row['path']]['target']==[row['zh']]
        save(component+'.component-before',all_units)
        save(component+'.before',{p:all_units[p] for p in expected[component]})
        records[component]={'filename':filename,'push_url_set':True,'repository':{k:repo.get(k) for k in ['needs_commit','needs_push','needs_merge','merge_failure']},'pagination':pagination,'matched_strings':len(expected[component]),'prior_suggestions':[p for p in expected[component] if all_units[p]['has_suggestion']]}
    save('preflight',records)
    save('approval',{'version':'v1','date':'2026-10-09','approved':True,'authorization':'好OK，可以上傳','scope':'世界樹道途第3批classes20＋content2，沿用既有正文、補0效果摘要及新版advancement.name；method=suggest。','payload_sha256':APPROVED_HASHES})
    info=load('verification');info['approved']=True;save('verification',info)
    print(json.dumps(records,ensure_ascii=False,indent=1))

def upload_classes():upload_component('classes')
def upload_content():upload_component('content')
def upload_component(component):
    expected=checked_payloads()[component]
    assert load('approval')['approved'] and load('approval')['payload_sha256']==APPROVED_HASHES
    assert load('preflight')[component]['matched_strings']==len(expected)
    response_path=DATA/(PREFIX+'.'+component+'.upload-response.json')
    assert not response_path.exists(),'Prior attempt exists; inspect actual suggestions before retrying.'
    assert not (DATA/(PREFIX+'.'+component+'.upload-attempt.json')).exists(),'Interrupted attempt exists; inspect actual suggestions before retrying.'
    save(component+'.upload-attempt',{'date':'2026-10-09','method':'suggest','payload_sha256':APPROVED_HASHES[component]})
    status,body=w.upload(PROJECT,PROJECT+'-'+component,str(DATA/(PREFIX+'.'+component+'.upload.json')),method='suggest')
    save(component+'.upload-response',{'http_status':status,'response':body,'method':'suggest','sha256':APPROVED_HASHES[component]})
    print(json.dumps({'component':component,'http_status':status,'response':body},ensure_ascii=False))
    assert status in [200,201],'Unclear or failed upload; inspect before retrying'
    assert body['not_found']==0 and body['accepted']+body['skipped']==len(expected)

def audit_upload():
    expected=checked_payloads();audits={}
    for component in expected:
        rows,pagination=read_all(PROJECT,PROJECT+'-'+component);after={r['context']:r for r in rows}
        before=load(component+'.component-before');assert set(before)==set(after)
        for path,unit in after.items():
            assert unit['source']==before[path]['source'],'EN changed after upload: '+path
            assert unit['target']==before[path]['target'],'Existing target changed: '+path
        accepted=[];skipped=[]
        for path,zh in expected[component].items():
            if after[path]['target']==[zh]:skipped.append({'path':path,'reason':'Already accepted same target'})
            else:
                assert not before[path]['has_suggestion'] and after[path]['has_suggestion'],'Inspect suggestions for '+path
                accepted.append({'path':path,'unit_id':after[path]['id'],'source_unchanged':True,'target_unchanged':True,'before_suggestion':False,'after_suggestion':True})
        response=load(component+'.upload-response')['response']
        assert len(accepted)==response['accepted'] and len(skipped)==response['skipped'] and response['not_found']==0
        stats={'component_units':len(after),'component_empty_or_source':sum(not any(u['target']) or u['target']==u['source'] for u in after.values()),'batch_strings':len(expected[component]),'batch_empty_or_source':sum(not any(after[p]['target']) or after[p]['target']==after[p]['source'] for p in expected[component]),'batch_has_suggestion':sum(after[p]['has_suggestion'] for p in expected[component])}
        save(component+'.after',{p:after[p] for p in expected[component]})
        audits[component]={'accepted':accepted,'skipped':skipped,'not_found':0,'response':response,'all_component_sources_unchanged':True,'all_component_targets_unchanged':True,'pagination':pagination,'statistics':stats}
    result={'complete':True,'accepted':sum(len(a['accepted']) for a in audits.values()),'skipped':sum(len(a['skipped']) for a in audits.values()),'not_found':0,'all_targets_unchanged':True,'component_verified_strings':sum(a['statistics']['component_units'] for a in audits.values()),'components':audits}
    save('upload-audit',result);print(json.dumps({k:v for k,v in result.items() if k!='components'},ensure_ascii=False))

def archive():
    import shutil
    checked_payloads();audit=load('upload-audit');assert audit['complete'] and audit['accepted']+audit['skipped']==22
    destination=BASE/'_done/subclasses/world-tree'
    assert DATA.resolve().is_relative_to(BASE.resolve()) and destination.resolve().is_relative_to((BASE/'_done').resolve())
    files=sorted(DATA.glob(PREFIX+'.*'));assert files and all(f.is_file() and not (destination/f.name).exists() for f in files)
    destination.mkdir(parents=True,exist_ok=True)
    info=load('verification');info.update(approved=True,uploaded=True,method='suggest',upload_date='2026-10-09',accepted=audit['accepted'],skipped=audit['skipped'],not_found=0,archive_path=str(destination));save('verification',info)
    save('status',{'phase':'uploaded-and-audited','approved':True,'uploaded':True,'import_preview_complete':True,'method':'suggest','accepted':audit['accepted'],'skipped':audit['skipped'],'not_found':0,'archive_path':str(destination),'reason':'使用者确认依正文補0，重新抽取並核對已同步的新版EN，22個字串全部以建議上傳，正式譯文保持不變。'.replace('确认','確認')})
    def link(suffix,label):return '['+label+']('+str(destination/(PREFIX+'.'+suffix)).replace('\\','/')+')'
    report=['# 世界樹道途第3批 v1：上傳報告（2026-10-09）','',f'依使用者「好OK，可以上傳」授權，以method=suggest送出22個字串。新增{audit["accepted"]}、跳過{audit["skipped"]}、未匹配0；正式譯文沒有變動。','', '| 元件 | 字串 | HTTP | accepted | skipped | not_found |','|---|---:|---:|---:|---:|---:|']
    for component in APPROVED_HASHES:
        reply=load(component+'.upload-response');body=reply['response']
        report.append(f'| {component} | {len(dict(leaves(load(component+".upload"))))} | {reply["http_status"]} | {body["accepted"]} | {body["skipped"]} | {body["not_found"]} |')
    report+=['','## 翻譯範圍與保留','', '5個classes條目20字串＋1個同名日誌頁2字串。原稿2–18行全部有對應；無EN缺漏、無未確定字串。共用原始HTML／文字與_source轉繁檔保留。','', '世界樹道途name、description原樣保留，不列payload。介紹2個區塊與聖樹活力3個既有規則區塊逐字與HTML不變；聖樹活力只補英文Foundry註記及介面。行動名沿用已接受活力如潮、生命賦予。','', '根擊千鈞精通條件依EN修正為正使用的一種不同精通屬性。靈樹枝杈效果摘要依使用者確認補速度0；完整正文、condition的狂暴與可見性、DC、距離及時間均核對。相關中英文原句、原稿及底稿全部在預覽逐欄列出。','', '本次重新抽取新版classes.json；Weblate已同步2270單元（包含其讀入的mapping設定單元）。本批只送翻譯欄位，不含mapping；advancement使用新版name，沿用子職業特性。前一階段版本報告保留歷史快照，不改寫當時Weblate尚舊版的查核記錄。','', '## 四項驗收','', '- 規則：狂暴、臨時生命值、30／5呎傳送與速度0、重型／多用觸及及不同精通、60／150呎與同行生物限制全部逐句完成。','- 術語：terms136、spells-glossary640完整讀取；terms工具3項全處理，take a Reaction例外單獨登記；15個lang未含項全部解釋，97個draft_diff片段全部登記，18個補翻位置完整披露。','- 機械：完整classes5條22字串validate通過，排除2個既有原樣欄位形成20字串payload；content2個真實頁面欄位另驗。36個映射位置與獨立底稿一致，HTML、UUID與Embed參數保留。','- 中文通讀：單獨通讀後回查EN；既有正文不為統一風格改寫，新增正文依原稿。全部payload禁用字回查通過。','', '## 上傳與回查','', f'上傳前後共{audit["component_verified_strings"]}個現行API單元逐一比對：source与target全都不變；本批22個單元上傳前無建議、上傳後有建議，與accepted回應吻合。'.replace('与','與'),'','component total是整個元件筆數，不是本批筆數。建議尚待使用者在Weblate接受，不標為已接受翻譯。','']
    for component,sha in APPROVED_HASHES.items():
        rec=load('preflight')[component];stat=audit['components'][component]['statistics']
        report+=['- '+component+' SHA-256：`'+sha+'`；'+link(component+'.upload.json','實際payload')+'。','- filename：`'+rec['filename']+'`，push URL已核實；repository：`'+json.dumps(rec['repository'],ensure_ascii=False)+'`。',f'- {component}空值或source相同：{stat["component_empty_or_source"]}/{stat["component_units"]}；本批{stat["batch_empty_or_source"]}個為空值或target等於source，{stat["batch_has_suggestion"]}個有建議。']
    report+=['','## 完整紀錄','', '- '+link('preview.md','完整中英文預覽、修改、術語、限定詞、補翻與conditions')+'。','- '+link('preview.html','成品閱讀預覽')+'；'+link('draft.txt','獨立中文底稿')+'。','- '+link('upload-audit.json','逐欄上傳稽核')+'；'+link('approval.json','使用者確認版本與雜湊')+'。','', '本批剩餘0個待送字串。主頁原先無EN欄位的等級表／職業說明仍保留remaining；其他已上傳批次因新版結構需要重配的工作未包含本次授權。下一個尚未處理子職業是狂熱者道途。執行腳本留/scripts/translation-import/player-handbook/；沒有提交、推送、新增術語或刪除建議。']
    write('2026-10-09.report.md','\n'.join(report))
    preview=DATA/(PREFIX+'.preview.md')
    preview.write_text(preview.read_text(encoding='utf-8').replace('本預覽先完成驗收，尚未送出。','本預覽已完成驗收並上傳22個建議，跳過0、未匹配0。'),encoding='utf-8')
    preview=DATA/(PREFIX+'.preview.html')
    preview.write_text(preview.read_text(encoding='utf-8').replace('使用者已確認，尚未送出。','使用者已確認，已上傳22個建議。'),encoding='utf-8')
    history=DATA/(PREFIX+'.latest-classes-review.md')
    history.write_text('> 歷史比對快照：本文記錄使用者要求先比對新版EN時的狀態。後續Weblate已同步、本批22個字串已確認並上傳建議；最終結果見本批2026-10-09.report.md。\n\n'+history.read_text(encoding='utf-8'),encoding='utf-8')
    immutable={PREFIX+'.draft.txt',PREFIX+'.classes.upload.json',PREFIX+'.content.upload.json'}
    for file in sorted(DATA.glob(PREFIX+'.*')):
        if file.name not in immutable:
            text=file.read_text(encoding='utf-8')
            text=text.replace(str(DATA).replace('\\','/'),str(destination).replace('\\','/'))
            text=text.replace(str(DATA).replace('\\','\\\\'),str(destination).replace('\\','\\\\'))
            file.write_text(text,encoding='utf-8')
        shutil.move(str(file),str(destination/file.name))
    for component,sha in APPROVED_HASHES.items():assert hashlib.sha256((destination/(PREFIX+'.'+component+'.upload.json')).read_bytes()).hexdigest()==sha
    index=BASE/'subclasses/index.md';text=index.read_text(encoding='utf-8')
    lines=text.splitlines()
    for i,line in enumerate(lines):
        if line.startswith('| 世界樹道途 |'):
            parts=line.split('|');parts[-2]=' 第3批v1已上傳22個建議（classes20＋content2）；既有5個正文區塊保留；效果摘要補0已確認 ';lines[i]='|'.join(parts)
    lines+=['', '世界樹道途第3批：'+link('2026-10-09.report.md','上傳報告')+'；'+link('preview.md','完整預覽')+'。原稿2–18行均有對應；剩餘0字串。']
    index.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'archive_path':str(destination),'accepted':audit['accepted'],'skipped':audit['skipped'],'not_found':0,'all_targets_unchanged':True},ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['collect','search','prepare','map_draft','review','preflight','upload_classes','upload_content','audit_upload','archive']);args=parser.parse_args()
    globals()[args.stage]()
