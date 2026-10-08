"""Prepare Zealot batch 4; stop at preview until batch approval."""
import argparse, difflib, hashlib, html, json, re, subprocess, sys
from pathlib import Path
from urllib.parse import unquote, urljoin, quote
import opencc
from subclasses import read_all, english_text, leaves

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'_incoming/player-handbook'
DATA=BASE/'subclasses/zealot'
WEB=BASE/'_web/barbarian-subclasses'
PREFIX='subclasses.zealot.4'
PROJECT='dnd-players-handbook'
KEYS=['Path of the Zealot','Divine Fury','Warrior of the Gods','Fanatical Focus','Zealous Presence','Rage of the Gods']
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
    candidates=sorted(set(urljoin('https://5echm.kagangtuya.top/webhelpcontents.htm',html.unescape(u)) for u in re.findall(r'href="([^"#]+)',toc) if '玩家手册2024/角色职业/野蛮人/' in unquote(u) and '狂热者道途' in unquote(u)))
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
        scope={p:r for p,r in units.items() if any(p.startswith('entries.'+k+'.') for k in KEYS)} if component=='classes' else {p:r for p,r in units.items() if p.startswith('entries.Barbarian.pages.Path of the Zealot.')}
        print(json.dumps({p:{'en':r['source'][0],'zh':r['target'][0]} for p,r in scope.items()},ensure_ascii=False,indent=1))
    for component in ['terms','spells-glossary']:
        rows,audit=read_all('dnd-5e-2024-zh-tw',component);save(component+'.live',{'audit':audit,'units':rows});print(component,'complete',len(rows))
    terms={r['source'][0]:r['target'][0] for r in load('terms.live')['units'] if any(r['target']) and r['target']!=r['source']}
    glossary={r['source'][0]:r['target'][0] for r in load('spells-glossary.live')['units'] if any(r['target']) and r['target']!=r['source']}
    save('term_index',{'terms':terms,'spells_glossary':glossary,'entry_names':{k:dict(v) for k,v in entry_names(str(ROOT/'compendium/zh-tw'),PROJECT).items()},'aliases':aliases(str(ROOT/'.claude/skills/translation-import/glossary.tsv'))})
    command('skeleton.py',['extract','--book',PROJECT,'--component','classes','--keys',*KEYS,'--out',str(DATA/(PREFIX+'.classes.sheet.json'))],'extract.txt')

def search():
    queries=['Subclass Features','Pool Size','Battle Cry','Recharge with Rage','Revivification','Barbarian Level',
      'you hit a creature on your turn while Rage is active','First creature you hit with a weapon or an Unarmed Strike',
      'When a creature within 30 feet of you would drop to 0 Hit Points','When you activate your Rage',
      'You gain Advantage on attack rolls and saving throws until the start of Zealots next turn.',
      'This "Battle Cry" activity includes an Active Effect',
      'for tracking impacted creatures','restores a use of this feature','automatically adding the resistances',
      'includes a healing roll of your Barbarian level','This feature includes an activity for','includes an Active Effect']
    queries+=['While in this form, you gain the benefits below.','You have a Fly Speed equal to your Speed and can hover.','You have Resistance to Necrotic, Psychic, and Radiant damage.']
    results=[]
    for phrase in queries:
        query='"'+phrase+'"';rows=[];pages=[];page=1
        while True:
            status,body=w.call('GET',f'/api/units/?q={quote(query,safe="")}&page_size=1000&page={page}')
            assert status==200,(phrase,status)
            rows.extend(body['results']);pages.append({'page':page,'status':status,'received':len(body['results']),'total':body['count']})
            if not body.get('next'):
                assert len(rows)==body['count'];break
            page+=1
        results.append({'query':query,'audit':pages,'units':rows})
        exact=[r for r in rows if r['source'][0]==phrase and r['target']!=r['source'] and re.search('[\u3400-\u9fff]',r['target'][0])]
        chinese=[r for r in rows if r['target']!=r['source'] and re.search('[\u3400-\u9fff]',r['target'][0])]
        print(phrase,'total',len(rows),'translated',len(chinese),'EXACT',[(r['id'],r['target'][0]) for r in exact])
        if not exact:print('RELATED',[(r['id'],r['context'],r['target'][0][:700]) for r in chinese[:5]])
    save('supplement-search',results)

def prepare():
    command('skeleton.py',['extract','--book',PROJECT,'--component','classes','--keys',*KEYS,'--out',str(DATA/(PREFIX+'.classes.sheet.json'))],'extract.txt')
    source=(DATA/(PREFIX+'.source.s2twp.txt')).read_text(encoding='utf-8').splitlines()
    live=load('classes.live')['units']
    accepted=lambda k:[visible_text(b.html) for b in Plan(live['entries.'+k+'.description']['target'][0]).blocks]
    intro=accepted(KEYS[0]);divine=accepted(KEYS[1])[0];warrior=accepted(KEYS[2])[:3]
    # Only repair the malformed damage label; the rest of accepted prose stays exact.
    divine=divine.replace('該額外傷類型害','該額外傷害類型')
    divine=divine.replace('在你狂暴啟用時的每一回合','在你狂暴啟用時，你的每一回合中')
    warrior[2]=warrior[2].replace('治療池中骰子的數量','治療池中骰子的最大數量')
    focus='每次啟用狂暴一次，若你豁免失敗，則你可以重骰，在結果加上等同於你狂暴傷害加值的加值（當前[[@scale.barbarian.rage-damage]]），並且你必須使用新的結果。'
    main={
      KEYS[0]:['狂熱者道途',*intro],
      KEYS[1]:['神性之怒',divine],
      KEYS[2]:['神之勇者',*warrior],
      KEYS[3]:['專心熾志',focus],
      KEYS[4]:['狂熱威儀','以一個附贈動作，你以滿腔神聖能量發出戰吼。選擇至多十名位於你60呎內的其他生物，直至你的下個回合開始，他們的攻擊檢定和豁免檢定具有優勢。','此特性一經使用，直到完成長休前你都無法再次使用。你也可以消耗一次狂暴使用次數（無需動作）來重置此特性的使用權。'],
      KEYS[5]:['眾神之怒','當你啟用狂暴時，你可以呈現出聖鬥士姿態。聖鬥士姿態持續1分鐘，且在你生命值降至0時提前結束。此特性一經使用，直到完成長休前你都無法再次使用。','處於聖鬥士姿態期間，你獲得下列好處。','【飛翔】你具有等於你速度的飛行速度，並且可以懸浮。','【抗力】你具有對黯蝕、心靈和光耀傷害的抗力。','【回春】當位於你30呎內的一名生物的生命值將要降至0時，你可以採取反應消耗一次狂暴使用次數，改為令目標的生命值變為等於你野蠻人等級的值（當前[[lookup @classes.barbarian.levels]]）。'],
    }
    supp={KEYS[4]:['【Foundry註記】','戰吼行動包含一項Active Effect，用來追蹤受影響的生物，但不會自動套用攻擊檢定和豁免檢定的優勢。','以狂暴充能會消耗一次狂暴使用次數，並恢復此特性的使用次數。'],KEYS[5]:['【Foundry註記】','眾神之怒行動包含一項Active Effect，可自動加入抗力、懸浮和飛行速度。','回春行動包含等於你野蠻人等級的治療擲骰。']}
    nested={
      KEYS[0]:{'advancement':{'Subclass Features':{'name':'子職業特性'}}},
      KEYS[1]:{'activities':{'Divine Fury':{'name':'神性之怒','condition':'你的狂暴啟用期間，當你在你的回合內命中一名生物時','target':'你以武器或徒手打擊命中的第一個生物'}}},
      KEYS[2]:{'advancement':{'Pool Size':{'name':'治療池骰數'}}},
      KEYS[4]:{'activities':{'Battle Cry':{'name':'戰吼'},'Recharge with Rage':{'name':'以狂暴充能'}},'effects':{'Zealous Presence':{'name':'狂熱威儀','description':'你在攻擊檢定和豁免檢定中具有優勢，持續至賦予此效果的狂熱者的下個回合開始。'}}},
      KEYS[5]:{'activities':{'Revivification':{'name':'回春','roll':'野蠻人等級','condition':'當位於你30呎內的一名生物的生命值將要降至0時'},'Rage of the Gods':{'name':'眾神之怒','condition':'當你啟用狂暴時'}},'effects':{'Rage of the Gods':{'name':'眾神之怒','description':'\n'.join(main[KEYS[5]][2:5])}}},
    }
    bounds={KEYS[0]:[(3,3),(4,4)],KEYS[1]:[(7,7)],KEYS[2]:[(10,10),(11,11),(12,12)],KEYS[3]:[(15,15)],KEYS[4]:[(17,17),(18,18)],KEYS[5]:[(21,21),(22,22),(23,23),(24,24),(25,25)]}
    original={k:[''.join(source[a-1:b]) for a,b in bounds[k]] for k in KEYS}
    # Metadata-only English labels become the EN heading; prose is unchanged.
    for i,(name,label) in enumerate([('飛翔','Flight'),('抗性','Resistance'),('回春','Revivification')],2):
        original[KEYS[5]][i]=original[KEYS[5]][i].replace(name+label+'。',name+'。')
    sourcecheck='\n\n'.join(main[k][0]+' '+k+'\n'+'\n'.join(original[k]) for k in KEYS)
    sourcecheck+='\n\n狂熱者道途 '+JOURNAL_KEY+'\n'+'\n'.join(original[KEYS[0]])
    write('source.segmented.s2twp.txt',sourcecheck)
    sections=[]
    for k in KEYS:
        parts=['### '+k,'名稱：'+main[k][0],*main[k][1:]]
        if supp.get(k) or nested.get(k):
            parts+=['〔EN 補翻／獨立介面欄位〕',*supp.get(k,[])]+[path+'：'+v for path,v in leaves(nested.get(k,{}))]
        sections.append('\n'.join(parts))
    sections.append('### '+JOURNAL_KEY+'\n名稱：狂熱者道途\n'+'\n'.join(main[KEYS[0]][1:]))
    write('draft.txt','\n\n'.join(sections))
    save('draft-data',{'main':main,'supplements':supp,'nested':nested,'bounds':bounds,'original':original})
    # Register every fragment shown by the common draft_diff tool.
    from draft_diff import best_match,fragments
    changes=[];diff=[]
    for k in [*KEYS,JOURNAL_KEY]:
        src=KEYS[0] if k==JOURNAL_KEY else k
        for i,new in enumerate(main[src][1:],1):
            ratio,a,b,old=best_match(new,original[src]);pieces=fragments(old,new)
            diff.append({'entry':k,'paragraph':i,'ratio':ratio,'matched_source':old,'draft':new,'fragments':pieces})
            for fragment in pieces:
                before,after=re.match('「(.*?)」→「(.*?)」',fragment,re.S).groups()
                category,reason=change_reason(src,i,before,after)
                changes.append({'entry':k,'paragraph':i,'fragment':fragment,'category':category,'reason':reason})
    save('draft-diff-register',diff);save('fragment-register',changes)
    audit=load('classes.sheet')
    for k,row in audit['entries'].items():row['blocks'].append({'id':'name-audit','en':k})
    journal=read(ROOT/f'compendium/en/{PROJECT}/{PROJECT}.content.json')['entries']['Barbarian']['pages'][KEYS[0]]
    audit['entries'][JOURNAL_KEY]={'name_en':KEYS[0],'blocks':[{'id':b.id,'en':b.html} for b in Plan(journal['description']).blocks]+[{'id':'name-audit','en':KEYS[0]}]}
    save('audit.sheet',audit)
    save('ack',{'Rage of the Gods|take':'take a Reaction 為採取反應，依使用者句式裁定；不是承受傷害。','Warrior of the Gods|reach':'reach Barbarian levels 為達到野蠻人等級，不是武器觸及；沿用已接受正文「達到」。'})
    save('draft-fingerprints',{'draft.txt':digest('draft.txt')})
    command('draft_diff.py',['--source',str(DATA/(PREFIX+'.source.segmented.s2twp.txt')),'--draft',str(DATA/(PREFIX+'.draft.txt')),'--out',str(DATA/(PREFIX+'.draft-diff.md'))],'draft-diff.log.txt')
    command('terms_check.py',[str(DATA/(PREFIX+'.audit.sheet.json')),'--draft',str(DATA/(PREFIX+'.draft.txt')),'--index',str(DATA/(PREFIX+'.term_index.json')),'--ack',str(DATA/(PREFIX+'.ack.json')),'--out',str(DATA/(PREFIX+'.terms-report.md'))],'terms-report.log.txt')
    command('lang_compare.py',[str(DATA/(PREFIX+'.audit.sheet.json')),'--draft',str(DATA/(PREFIX+'.draft.txt'))],'lang-report.md')

def change_reason(k,i,before,after):
    if k in KEYS[:4]:
        return '定案詞','沿用同語境已接受Weblate正文（unit '+str(load('classes.live')['units']['entries.'+k+'.description']['id'])+'），與原稿差異完整列報；神性之怒只修傷害類型倒字及明寫你的回合，神之勇者只補最大數量，專心熾志只補完整狂暴傷害加值與新版巨集／span及標點。'
    if before and set(before)<=set(',():'):
        return '禁用字','依中文全形標點格式，規則不變。'
    if '其他' in after or '改為' in after:
        return '規則','other creatures 排除自身；instead 以野蠻人等級生命值取代降至0。完整規則差異見第4節。'
    if '[[lookup' in after:
        return '規則','原稿缺目前等級的動態顯示，依EN加入原樣巨集；不改等級計算。'
    if before in ['。'] or after in ['【','】']:
        return '禁用字','小標文字套入【】並移除句號，依conventions格式；英中並列索引只保留中文。'
    if k==KEYS[5] and i==2:
        return '定案詞','原稿「以下增益」依已裁定benefits句式改為「下列好處」。'
    if '黯' in after or '抗力' in after or '好處' in after or before=='尺':
        return '定案詞','黯蝕、傷害抗力、下列好處與呎依conventions使用者裁定。'
    return '句式','長休恢复與採取反應依conventions；小標改【】且不留句號；不另改聖鬥士等敘事措辭。'.replace('恢复','恢復')

def enrich(en,line):
    for token,label in [(m[1],m[2]) for m in LABEL.finditer(en)]:
        if token.startswith('@UUID['):
            assert label==KEYS[0]
            line=line.replace('狂熱者道途',token+'{狂熱者道途}',1)
        elif token.startswith('@Embed['):assert not line
        elif token.startswith('[['):assert token in line
        else:raise AssertionError(token)
    names={'Foundry Note':'【Foundry註記】','Battle Cry':'戰吼','Recharge with Rage':'以狂暴充能','Rage of the Gods':'眾神之怒','Revivification':'回春','Flight':'飛翔','Resistance':'抗力'}
    for word in re.findall(r'<strong>(.*?)</strong>',en,re.S):
        chosen=names[word.strip().rstrip('.')]
        if word.endswith('.'):chosen='【'+chosen+'】'
        assert chosen in line,(word,line)
        line=line.replace(chosen,'<strong>'+chosen+'</strong>',1)
    if '<span' in en:
        assert 'hide-in-embed' in en and k_placeholder(en)=='[[@scale.barbarian.rage-damage]]'
        text='（當前[[@scale.barbarian.rage-damage]]）'
        assert text in line
        line=line.replace(text,'<span class="hide-in-embed">'+text+'</span>')
    return line

def k_placeholder(en):
    return re.search(r'\[\[.*?\]\]',en).group(0)

def report_text(value):
    protected=[]
    def remember(m):
        protected.append(m.group(0));return 'PROTECTEDMACRO'+str(len(protected)-1)+'TOKEN'
    out=english_text(re.sub(r'\[\[.*?\]\]',remember,value))
    for i,token in enumerate(protected):out=out.replace('PROTECTEDMACRO'+str(i)+'TOKEN',token)
    return out

def map_draft():
    data=load('draft-data');main,supp,nested=data['main'],data['supplements'],data['nested']
    assert all(digest(s)==h for s,h in load('draft-fingerprints').items())
    sheet=load('classes.sheet');local=read(ROOT/f'compendium/en/{PROJECT}/{PROJECT}.classes.json')['entries'];live=load('classes.live')['units'];audit=[]
    for k,row in sheet['entries'].items():
        row['name']=main[k][0];body=main[k][1:]+supp.get(k,[])
        assert len(body)==len(row['blocks'])
        accepted=Plan(live['entries.'+k+'.description']['target'][0]).blocks
        for i,(block,line) in enumerate(zip(row['blocks'],body)):
            added=i>=len(main[k])-1
            retained=k in KEYS[:3] and i<len(accepted) and visible_text(accepted[i].html)==line
            zh=accepted[i].html if retained else enrich(block['en'],line)
            assert visible_text(zh)==visible_text(line),(k,i,line,visible_text(zh))
            assert not compare_html(block['en'],zh),(k,i,compare_html(block['en'],zh))
            macro='[[' in block['en']
            block.update(zh=zh,source='supplement' if added or macro else 'draft',basis=('原稿無Foundry註記；Weblate原句／片段查詢已成功，沒有同句中文；依已接受同類註記補翻，詳supplement-basis。' if added else 'EN含無標籤動態值巨集，無法與底稿可見文字逐字相同，依block-mapping巨集例外；整段仍由獨立底稿產生，巨集及span原樣保留。' if macro else ''))
            audit.append({'entry':k,'path':'entries.'+k+'.description/'+block['id'],'en':report_text(block['en']),'en_html':block['en'],'source':data['original'][k][i] if not added else '無原稿','draft':line,'source_lines':data['bounds'][k][i] if not added else None,'retained':retained,'supplement':added,'macro':macro})
        for field,value in nested.get(k,{}).items():
            row[field]=json.loads(json.dumps(value))
            for name,child in row[field].items():
                if 'description' in child:
                    en=local[k][field][name]['description'];plan=Plan(en);lines=child['description'].splitlines()
                    assert len(lines)==len(plan.blocks)
                    child['description']=plan.build({b.id:enrich(b.html,line) for b,line in zip(plan.blocks,lines)})
    save('classes.sheet',sheet)
    command('skeleton.py',['build',str(DATA/(PREFIX+'.classes.sheet.json')),'--draft',str(DATA/(PREFIX+'.draft.txt')),'--out',str(DATA/(PREFIX+'.classes.aligned.json'))],'mapping.log.txt')
    built=load('classes.aligned');changed={};retained=[];expected=dict(leaves({'entries':{k:local[k] for k in KEYS}}))
    name_bounds={KEYS[0]:[2,2],KEYS[1]:[5,6],KEYS[2]:[8,9],KEYS[3]:[13,14],KEYS[4]:[16,16],KEYS[5]:[19,20]}
    for path,zh in leaves(built):
        assert expected[path]==live[path]['source'][0],'EN drift: '+path
        old=live[path]['target'][0]
        if old==zh:retained.append({'path':path,'en':live[path]['source'][0],'zh':zh})
        if not path.endswith('.description') or '.effects.' in path:
            k=path.split('.')[1];isname=path.endswith('.name') and path.count('.')==2
            audit.append({'entry':k,'path':path,'en':report_text(live[path]['source'][0]),'source':old if old==zh else '原稿標題' if isname else '無原稿獨立介面欄位','draft':report_text(zh),'source_lines':name_bounds[k] if isname else None,'retained':old==zh,'supplement':not isname})
        if old==zh:continue
        node=changed;parts=path.split('.')
        for part in parts[:-1]:node=node.setdefault(part,{})
        node[parts[-1]]=zh
    journal=read(ROOT/f'compendium/en/{PROJECT}/{PROJECT}.content.json')['entries']['Barbarian']['pages'][KEYS[0]]
    plan=Plan(journal['description']);replacements={};i=0
    for block in plan.blocks:
        protected=not english_text(block.html)
        if protected:zh=block.html;line='';bounds=None
        else:
            line=main[KEYS[0]][i+1];bounds=data['bounds'][KEYS[0]][i];i+=1;zh=enrich(block.html,line)
        assert not compare_html(block.html,zh) and visible_text(zh)==line
        replacements[block.id]=zh
        audit.append({'entry':JOURNAL_KEY,'path':'entries.Barbarian.pages.'+KEYS[0]+'.description/'+block.id,'en':english_text(block.html),'source':data['original'][KEYS[0]][i-1] if bounds else '@Embed無可見文字','draft':line,'source_lines':bounds,'retained':False,'supplement':False,'protected':protected})
    assert i==2
    content={'entries':{'Barbarian':{'pages':{KEYS[0]:{'name':'狂熱者道途','description':plan.build(replacements)}}}}}
    audit.append({'entry':JOURNAL_KEY,'path':'entries.Barbarian.pages.'+KEYS[0]+'.name','en':KEYS[0],'source':'同語境已接受class名稱狂熱者道途','draft':'狂熱者道途','source_lines':[2,2],'retained':False,'supplement':False})
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
    save('classes.upload',changed);save('content.upload',content);save('retained',retained);save('mapping-audit',audit)
    save('verification',{'version':'v1','classes_entries':len(changed['entries']),'classes_strings':count_strings(changed),'content_entries':1,'content_strings':count_strings(content),'full_classes_strings':count_strings(built),'retained_strings':len(retained),'retained_body_blocks':sum(r['retained'] for r in audit if '.description/' in r['path']),'mapped_positions':len(audit),'all_exact_draft_matches':True,'mechanical_pass':True,'live_en_match':True,'draft_check_pass':True,'terms_check_pass':True,'pending_fields':[],'draft_sha256':load('draft-fingerprints'),'payload_sha256':{c:digest(c+'.upload.json') for c in ['classes','content']},'approved':False,'uploaded':False})
    print(json.dumps(load('verification'),ensure_ascii=False,indent=1))

LANG_REASONS={
 'allies':'敘事沿用已接受的盟友，未出現{number}變數，不插入介面計數模板。',
 'change':'正文change the target’s Hit Points為令生命值變為；保留原稿句式，不套介面更改／變更標籤。',
 'continue':'沿用已接受的持續不斷地戰鬥；不改為介面繼續按鈕。',
 'creatures':'正文保留至多十名位於你60呎內的其他生物，無{number}變數。',
 'each':'every turn／each time用每一回合／每次；不硬插每個，限制仍完整。',
 'focus':'Fanatical Focus是特性名專心熾志，不是施法法器。',
 'four':'保留已接受4枚d12的阿拉伯數字，不改為四。',
 'maximum':'已補最大數量（治療池骰子的容量）；不改為介面屬性最大值。',
 'next':'next turn是下個回合，不是下一步／下一頁。',
 'number':'正文生命值數值與治療池骰子數量依既有及原稿，不套介面數字／骰子數量標籤。',
 'points':'Hit Points使用生命值，不是屬性點數。',
 'reach':'reach Barbarian levels是達到等級，非武器觸及；terms ack已登記。',
 'resistances':'傷害抗力依使用者裁定，Foundry註記中的resistances亦為傷害抗力；不採lang泛用抗性。',
 'rest':'Long Rest使用长休，非泛指休息。'.replace('长','長'),
 'round':'round down是向下取整，非戰鬥時間的輪。',
 'size':'Pool Size為治療池骰數，非尺寸／生物體型。',
 'start of your next turn':'原稿直至你的下個回合開始已完整保留時點；不加介面模板末尾時字。效果摘要改為賦予此效果的狂熱者的下個回合，主體明確。',
 'three':'@Embed classes="three right"為受保護參數，不是可見數字。',
 'time':'each time譯每次，不是持續時間或時間類別。',
 'total':'roll’s total用既有結果總數，不是全掩蔽，也不改成介面總量。',
 'walk':'walk the Path是遵行道途的敘事，非步行速度。',
}

def supplemental_basis(row):
    path,en,zh=row['path'],row['en'],row['draft']
    if row.get('macro'):
        return '技術例外，非整段無原稿：無標籤動態巨集使可見字串不同；完整中文出自獨立底稿。保留EN巨集、專心熾志hide-in-embed span與屬性；詳block-mapping巨集例外。'
    if not row.get('supplement'):return ''
    if path.endswith('advancement.Subclass Features.name'):
        return '全站精確EN查詢264筆，73筆含中文；同名精確已接受unit109543「子職業特性」原樣沿用。'
    if path.endswith('advancement.Pool Size.name'):
        return '全站Pool Size查詢4筆，无中文；依神之勇者治療池的骰子最大數量，自譯治療池骰數。'.replace('无','無')
    if path.endswith('activities.Recharge with Rage.name'):
        return '全站Recharge with Rage查詢14筆；精確已接受unit109714「以狂暴充能」原樣沿用。'
    if path.endswith('activities.Battle Cry.name'):
        return '全站Battle Cry查詢10筆，無中文；從原稿17行戰吼直接取名。'
    if path.endswith('activities.Revivification.name'):
        return '全站Revivification查詢21筆，無同名中文（中文2筆僅是roll「野蠻人等級」）；從原稿25行回春取名。'
    if path.endswith('activities.Revivification.roll'):
        return '同欄位unit109746已有「野蠻人等級」，與全站精確unit96688一致；原樣保留且排除payload。'
    if path.endswith('activities.Rage of the Gods.condition'):
        return '全站原句查詢24筆；精確已接受unit109785「當你啟用狂暴時」原樣沿用。'
    if path.endswith('activities.Revivification.condition'):
        return '全站原句查詢11筆，無中文；從原稿25行觸發條件摘取，尺→呎按裁定。'
    if path.endswith('activities.Divine Fury.condition'):
        return '全站原句查詢2筆，無中文；依原稿7行及本條EN保留狂暴啟用、自己的回合及命中生物。此欄位未寫武器／徒手及第一個，完整限制另由target與正文保留。'
    if path.endswith('activities.Divine Fury.target'):
        return '全站原句片段查詢6筆，已有同條正文中文unit109679；從既有正文摘取武器或徒手打擊命中的第一個生物。'
    if '.effects.Zealous Presence.description' in path:
        return '全站英文原句查詢4筆，無中文。依原稿17行與EN正文補翻；Zealots缺所有格符號，按同條正文解為賦予此效果者的下個回合，非受益者的回合。'
    if '.effects.Rage of the Gods.description' in path:
        return '全站三句查詢分別8／26／8筆，各對应段無中文；依本條原稿22–24行與独立底稿三段，沿用聖鬥士姿態、飛翔，抗性→傷害抗力。新版效果摘要不含回春；不加入已移除段落。'.replace('对','對').replace('应','應').replace('独','獨')
    if ('.activities.' in path or '.effects.' in path) and path.endswith('.name'):
        return '原稿無獨立介面名；取本條原稿／已接受主名稱。神性之怒取原稿5行；狂熱威儀取16行；眾神之怒優先沿用已接受root name unit'+str(load('classes.live')['units']['entries.Rage of the Gods.name']['id'])+'，不改回原稿神之狂暴。'
    if zh=='【Foundry註記】':
        return '原稿沒有Foundry小標；沿用已接受unit109701的小標，依conventions格式。'
    if row['entry']==KEYS[4] and '戰吼' in zh:
        return '全站tracking impacted creatures查詢12筆，2筆含中文但此對應註記段仍英文；完整戰吼註記查詢4筆無中文。參照unit109701「各行動皆包含一項Active Effect，用來追蹤…但不會自動套用…」句式，改為戰吼、受影響生物與攻擊／豁免優勢。'
    if row['entry']==KEYS[4]:
        return '全站restores a use of this feature查詢12筆，2筆已有中文正文但其對應註記段仍英文；參照已接受unit109713「恢復行動會消耗一次狂暴使用次數，並恢復威懾之姿的使用次數」，改為本條行動名與此特性。行動名精確沿用unit109714。'
    if row['entry']==KEYS[5] and 'Active Effect' in zh:
        return '全站automatically adding the resistances查詢4筆，無中文；參照unit109753「熊行動包含一項Active Effect，可自動加入這些抗力」，改為眾神之怒並依新版EN補懸浮及飛行速度。'
    if row['entry']==KEYS[5]:
        return '全站includes a healing roll of your Barbarian level查詢4筆，無中文；参照已接受unit118238「強化體魄行動包含額外治療效果」，改為回春與等於野蠻人等級的治療擲骰；roll同欄位已有野蠻人等級，lang healing roll為治療擲骰。'.replace('参','參')
    raise AssertionError(path)

def review():
    info=load('verification');audit=load('mapping-audit');data=load('draft-data');changes=load('fragment-register');diff=load('draft-diff-register');live=load('classes.live')['units'];source=(DATA/(PREFIX+'.source.s2twp.txt')).read_text(encoding='utf-8').splitlines()
    esc=lambda v:str(v).replace('|','\\|').replace('\n','<br>')
    table=lambda cols:'| '+' | '.join(esc(x) for x in cols)+' |'
    link=lambda suffix,label:'['+label+']('+str(DATA/(PREFIX+'.'+suffix)).replace('\\','/')+')'
    basis=[]
    for r in audit:
        r['basis']=supplemental_basis(r)
        if r.get('supplement') or r.get('macro'):basis.append({'path':r['path'],'en':r['en'],'zh':r['draft'],'basis':r['basis']})
    save('supplement-basis',basis)
    missing=[]
    for line in (DATA/(PREFIX+'.lang-report.md')).read_text(encoding='utf-8').splitlines():
        if '| 無 |' in line:
            term=line.split('|')[1].strip();assert term in LANG_REASONS,term
            missing.append({'en':term,'reason':LANG_REASONS[term]})
    save('lang-resolutions',missing)
    accepted_edits=[]
    for k in KEYS[:4]:
        oldblocks=Plan(live['entries.'+k+'.description']['target'][0]).blocks
        for i,new in enumerate(data['main'][k][1:]):
            old=report_text(oldblocks[i].html)
            for tag,a,b,c,d in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
                if tag=='equal':continue
                reason={KEYS[1]:'On each of your turns明寫你的回合；damage type傷害類型倒字修正。',KEYS[2]:'EN maximum number，原稿也有最大；既有譯文漏最大。',KEYS[3]:'補完整Rage Damage bonus與bonus，對齊新版無/r巨集；補全形標點使並且銜接清楚。'}[k]
                accepted_edits.append({'entry':k,'paragraph':i+1,'before':old[a:b],'after':new[c:d],'category':'規則' if k!=KEYS[3] or any(x in old[a:b]+new[c:d] for x in ['值','/r','scale']) else '禁用字','reason':reason})
    save('accepted-edit-register',accepted_edits)
    preview=['# 狂熱者道途第4批 v1：完整預覽','','## 1. 標頭','',f'2026-10-09。尚未上傳。本批6個classes條目（完整28字串，排除4個既有全欄位，待送24字串）＋1個日誌頁2字串，合計26個建議；未超過10條／60字串。', '', '來源：['+load('source')['decoded_url']+']('+load('source')['url']+')；'+link('source.s2twp.txt','原稿轉繁25行')+'，canonical原稿位於'+str(BASE/'_source'/(PREFIX+'.s2twp.txt')).replace('\\','/')+'。原稿行號：2–4介紹、5–7神性之怒、8–12神之勇者、13–15專心熾志、16–18狂熱威儀、19–25眾神之怒。','', '- '+link('draft.txt','獨立底稿')+'；'+link('classes.sheet.json','EN完整區塊sheet')+'。','- '+link('classes.aligned.json','classes完整成品')+'；'+link('content.aligned.json','日誌完整成品')+'。','- '+link('classes.upload.json','classes實際payload')+'；'+link('content.upload.json','content實際payload')+'。','- '+link('reading.html','中文通讀版')+'；'+link('verification.json','驗收數據')+'。','','classes SHA-256：`'+info['payload_sha256']['classes']+'`。','content SHA-256：`'+info['payload_sha256']['content']+'`。','底稿 SHA-256：`'+info['draft_sha256']['draft.txt']+'`。','','## 2. 做法','','同站目錄已精確匹配狂熱者道途頁面，6條均有原稿，整條無原稿0條、EN缺漏0段。跨行標題5+6、8+9、13+14、19+20合併為索引，等級不插入name。23–25行英中並列小標只將英文名稱移至索引，不改正文。原稿中文逐段產生獨立底稿，先跑三項檢查，再由程式整段映射；沒有從成品反推底稿。','','Weblate全量分頁核實classes '+str(len(live))+'、content '+str(len(load('content.live')['units']))+'、terms '+str(len(load('terms.live')['units']))+'、spells-glossary '+str(len(load('spells-glossary.live')['units']))+'單元，均HTTP200且筆數符合API。project為dnd-players-handbook，檔案路徑核實為compendium/zh-tw/dnd-players-handbook/。所有最終欄位與目前本地EN／Weblate source逐字相同；未使用其他project的舊手冊副本代替現行來源。','','既有狂熱者道途name／description、眾神之怒name及回春roll「野蠻人等級」共4個全欄位不重送。介紹2個區塊、神之勇者前2個區塊共4個正文區塊原HTML逐字保留。神性之怒／神之勇者／專心熾志只做第4節列出的必要修正；已從最新EN移除的Foundry註記不插回。其餘未翻譯內容依原稿及定案詞處理。','','## 3. 逐段及全部欄位對照','',f'全部{len(audit)}個映射位置（含1個純Embed保護區塊），全部列出EN、原稿或既有來源、底稿與修改。巨集在EN文字中完整顯示，不用空白取代。','','| 區塊／欄位 | EN全文 | 原稿／既有來源 | 底稿全文 | 修改與理由 |','|---|---|---|---|---|']
    for r in audit:
        bounds=r['source_lines'];raw='\n'.join(source[bounds[0]-1:bounds[1]]) if bounds else r['source']
        if r.get('protected'):reason='無可見文字；Embed目標及caption=false、classes="three right"原樣保護。'
        elif r.get('supplement'):reason=r['basis']
        elif r.get('retained'):reason='無修改（相對既有Weblate）；原稿差異見修改登記及保留項。'
        elif '.description/b' in r['path']:
            m=[d for d in diff if d['entry']==r['entry'] and d['draft']==r['draft']]
            reason='；'.join(x['fragment']+'｜'+x['category']+'｜'+x['reason'] for x in changes if m and x['entry']==m[0]['entry'] and x['paragraph']==m[0]['paragraph']) or '無修改；整段取底稿。'
            if r.get('macro'):reason+='；'+r['basis']
        else:reason='名稱：取原稿標題；眾神之怒沿用現行已接受名稱，不改回神之狂暴。移除等級／英文並列索引，不改規則。'
        if r['entry'] in KEYS[:4] and '.description/' in r['path']:
            idx=int(r['path'].split('/b')[1])-1
            raw+='\n既有Weblate：'+report_text(Plan(live['entries.'+r['entry']+'.description']['target'][0]).blocks[idx].html)
        preview.append(table([r['path'],r['en'],raw,r['draft'],reason]))
    preview+=['','### draft_diff原始報告','',(DATA/(PREFIX+'.draft-diff.md')).read_text(encoding='utf-8'),'','### 工具差異片段逐項登記','',f'共{len(changes)}個片段，與工具片段總數相同；每個片段都有類別與理由。保留既有譯文所產生的原稿差異不代表本次改了既有中文。','','| 條目／段落 | 原→新 | 類別 | 理由 |','|---|---|---|---|']
    assert len(changes)==sum(len(d['fragments']) for d in diff)
    for c in changes:preview.append(table([c['entry']+'/p'+str(c['paragraph']),c['fragment'],c['category'],c['reason']]))
    preview+=['','改動大11段逐項理由：Path介紹p1/p2及日誌p1/p2沿用同語境已接受介紹；Divine Fury p1沿用既有正文且僅修第4節兩处；Warrior p1原樣沿用、p3只補最大；Fanatical p1沿用既有句子且修完整加值與新版巨集；Rage p2改下列好處、p4改黯蝕／抗力與小標、p5採取反應／呎／instead及動態等級顯示，均為已裁定詞或EN規則／格式。'.replace('处','處'),'','## 4. 規則與必要修正差異','']
    issues=[
      ('神性之怒：明寫自己的回合，並修傷害類型倒字（已改）',KEYS[1],[7],data['main'][KEYS[1]][1],'EN限定On each of your turns；既有每一回合未明寫自己的回合，最小修正為在你狂暴啟用時，你的每一回合中。該額外傷類型害修為該額外傷害類型，以恢復傷害類型完整語意。其餘既有中文一字不改。'),
      ('神之勇者：最大數量（已改）',KEYS[2],[12],data['main'][KEYS[2]][3],'原稿已寫最大數量，既有中文只寫數量。依EN maximum補最大，6／12／17級的5／6／7枚d12不變；前兩段原HTML保留。'),
      ('專心熾志：完整加值與最新版顯示巨集（已改）',KEYS[3],[15],data['main'][KEYS[3]][1],'既有狂暴傷害的加漏加值且名詞不完整，改為狂暴傷害加值的加值。新版EN巨集為[[@scale.barbarian.rage-damage]]，已取代舊[[/r @scale.barbarian.rage-damage]]，並保留hide-in-embed span。每次啟用狂暴一次、豁免失敗、可重骰且必須使用新結果保持。'),
      ('狂熱威儀：其他生物（已改）',KEYS[4],[17],data['main'][KEYS[4]][1],'EN up to ten other creatures排除自身；原稿沒有其他，補其他。至多十名、60呎、你選擇、攻擊及豁免優勢、到你的下回合開始完整保留。'),
      ('回春：取代降至0而非降至0後治療（已改）',KEYS[5],[25],data['main'][KEYS[5]][5],'EN would drop...to instead change表示將要降至0時的取代，原稿用令但沒有明寫改為，已補改為。30呎、反應、消耗一次狂暴、生命值等於野蠻人等級均保留；原稿無當前等級顯示，加入新版原樣lookup。'),
    ]
    save('rule-differences',[{'title':t,'entry':k,'source_lines':lines,'en':live['entries.'+k+'.description']['source'][0],'original':'\n'.join(source[i-1] for i in lines),'old_target':live['entries.'+k+'.description']['target'][0],'draft':zh,'reason':why} for t,k,lines,zh,why in issues])
    for t,k,lines,zh,why in issues:
        preview+=['### '+t,'','EN完整正文：'+report_text(live['entries.'+k+'.description']['source'][0]),'','原稿完整原句：'+'\n'.join(source[i-1] for i in lines),'','既有Weblate完整可見正文／註記：'+report_text(live['entries.'+k+'.description']['target'][0]),'','本句底稿：'+zh,'','理由：'+why,'']
    preview+=['### 既有中文→本批底稿的全部實際修訂片段','','以下逐字差異只涉及三個已有中文的正文；已移除的舊英文註記與span結構另列下一表。','','| 條目／段落 | 原→新 | 類別 | 理由 |','|---|---|---|---|']
    for r in accepted_edits:preview.append(table([r['entry']+'/p'+str(r['paragraph']),'「'+r['before']+'」→「'+r['after']+'」',r['category'],r['reason']]))
    preview+=['### 最新EN技術內容的差異（已依新版處理）','','| 欄位 | 舊註記／內容EN全文 | 最新EN全文 | 中文處理 |','|---|---|---|---|',table(['Divine Fury.description','This feature includes an activity for each type of damage.','最新EN已無此句；現有activity為Divine Fury，condition／target見第8節。','移除已退役的英文Foundry註記，不補翻插回；原意為此特性為各傷害類型各包含一個行動。']),table(['Warrior of the Gods.description',"The pool’s increase is automatically handled in this feature. This feature also allows scaling up the number of dice you would like to expend for healing.",'最新EN已無這兩句。','移除已退役英文Foundry註記；原意為治療池增長由特性自動處理，可提高消耗骰數進行治療。現行advancement.Pool Size.name譯為治療池骰數。']),table(['Rage of the Gods Foundry註記','The Rage of the Gods activity includes an Active Effect for automatically adding the resistances and hover but does not provide the fly speed.','The Rage of the Gods activity includes an Active Effect for automatically adding the resistances, hover, and fly speed.',data['supplements'][KEYS[5]][1]+' 舊註記的中文意思是自動加入抗力和懸浮但不提供飛行速度；最新版已會加入飛行速度，依新版補翻。']),table(['Rage of the Gods.effects.Rage of the Gods.description','Revivification. When a creature within 30 feet of you would drop to 0 Hit Points, you can take a Reaction to expend a use of your Rage to instead change the target\'s Hit Points to a number equal to your Barbarian level.',report_text(live['entries.Rage of the Gods.effects.Rage of the Gods.description']['source'][0]),'新版效果摘要只保留姿態／飛翔／抗力，移除舊回春段；回春完整規則仍在主正文，不從主正文刪除。舊句中文對照即上方回春底稿（不含當前lookup）。']),table(['Fanatical Focus.description','[[/r @scale.barbarian.rage-damage]]','<span class="hide-in-embed">(currently [[@scale.barbarian.rage-damage]])</span>','動態狂暴傷害加值顯示：保留新巨集和hide-in-embed屬性；中文當前顯示置於同span。']),'','### 狂熱威儀效果摘要的時點（依正文對齊）','','EN完整原句：You gain Advantage on attack rolls and saving throws until the start of Zealots next turn.','','原稿17行：'+source[16],'','EN正文完整段：'+report_text(Plan(live['entries.Zealous Presence.description']['source'][0]).blocks[0].html),'','底稿：'+data['nested'][KEYS[4]]['effects'][KEYS[4]]['description'],'','Zealots缺所有格符號；依同特性正文，Zealot指賦予此效果的野蠻人，故明寫賦予此效果的狂熱者的下個回合，避免誤讀為受益者的下個回合。沒有改持續時間。','','## 5. 保留項','','| EN完整句段 | 原稿全文／既有中文全文 | 保留與理由 |','|---|---|---|']
    retained_notes=[
      (report_text(Plan(live['entries.Path of the Zealot.description']['source'][0]).blocks[0].html),source[2]+'；既有：'+data['main'][KEYS[0]][1],'沿用已接受標語；原稿至高愉悅／既有欣喜若狂屬敘事措辭，未重新翻譯。'),
      (report_text(Plan(live['entries.Path of the Zealot.description']['source'][0]).blocks[1].html),source[3]+'；既有：'+data['main'][KEYS[0]][2],'divine union／ecstatic episode既有神人合一的狂想曲；priests既有祭司、原稿牧師；god神靈／神明，boons恩賜／恩惠，都是敘事措辭差異。已接受介绍原HTML保留，日誌共用。'.replace('介绍','介紹')),
      ('A divine entity helps ensure you can continue the fight.',source[9]+'；既有完整段：'+data['main'][KEYS[2]][1],'既有總能使你持續不斷地戰鬥敘事较絕對，未增添無限治療規則；骰池／動作／治療數值完整，保留既有。'.replace('较','較')),
      ('When you activate your Rage, you can assume the form of a divine warrior.',source[20]+'；底稿完整段：'+data['main'][KEYS[5]][1],'divine warrior原稿聖鬥士姿態屬敘事名稱，保留原稿而非自行重命名。'),
      ('Rage of the Gods','原稿19–20行：'+source[18]+source[19]+'；已接受name：眾神之怒','名稱優先採現行已接受眾神之怒；各行動／效果／註記同步此名，不改回原稿神之狂暴。'),
      ('Once per active Rage, if you fail a saving throw, you can reroll it with a bonus equal to your Rage Damage bonus (currently [[@scale.barbarian.rage-damage]]), and you must use the new roll.',source[14]+'；底稿：'+data['main'][KEYS[3]][1],'每次啟用狂暴一次沿用既有；指每次有效狂暴期間僅一次重骰，未改為每回合一次。'),
    ]
    for row in retained_notes:preview.append(table(row))
    preview+=['','## 6. 術語報告','','terms及spells-glossary均全量核實。本批無法術名，未新增正式術語。以下terms_check報告原樣貼入：','',(DATA/(PREFIX+'.terms-report.md')).read_text(encoding='utf-8'),'','ack逐條：','']
    for k,v in load('ack').items():preview.append('- '+k+'：'+v)
    preview+=['','人工術語回查：狂暴／狂暴傷害加值、野蠻人等級、生命值、治療池、d12、附贈動作、長休、攻擊檢定、豁免、優勢、反應、飛行速度、懸浮、黯蝕／心靈／光耀、傷害抗力均核對。抗力依使用者定案，聖鬥士保留原稿敘事，Active Effect保留英文。工具5項命中不代表涵蓋所有規則詞。','',(DATA/(PREFIX+'.lang-report.md')).read_text(encoding='utf-8'),'','lang所有「無」逐條說明：','']
    for r in missing:preview.append('- '+r['en']+'：'+r['reason'])
    preview+=['','## 7. 限定詞逐句核對','','| 完整EN句段 | 完整中文句段 | 核對結果 |','|---|---|---|']
    qualified=[]
    for r in audit:
        words=re.findall(r'\b(?:this|these|that|the|following|one of|each|any|all)\b',r['en'],re.I)
        if not words:continue
        why='已核對 '+', '.join(sorted(set(x.lower() for x in words)))+' 的主體、指涉與範圍。'
        if r['entry']==KEYS[1]:why+='each of your turns限自己回合；the first creature限該回合第一個；the extra damage只指此額外傷害，每次獨立選傷害類型。'
        if r['entry']==KEYS[2]:why+='all expended dice是所有已消耗骰；the pool只指本條治療池；最大數量已補，等級數量限制保留。'
        if r['entry']==KEYS[3]:why+='the new roll是此次重骰的新結果，必須使用；不是任選新舊。'
        if r['entry']==KEYS[4]:why+='this feature指狂熱威儀；their/Zealots時點以賦予效果者的下回合為準，other creatures排除自身。'
        if r['entry']==KEYS[5]:why+='this form指聖鬥士姿態；the target指將要降至0生命值的生物；these resistances只指黯蝕、心靈、光耀，正文和效果摘要皆保留此范围。'.replace('范围','範圍')
        preview.append(table([r['en'],r['draft'],why]));qualified.append({'path':r['path'],'en':r['en'],'zh':r['draft'],'result':why})
    save('qualifier-review',qualified)
    preview+=['','## 8. 全部補翻與conditions','','| 欄位 | EN完整原句 | 中文全文 | 依據 |','|---|---|---|---|']
    for r in basis:preview.append(table([r['path'],r['en'],r['zh'],r['basis']]))
    preview+=['','### 全部activities.condition','','| 欄位 | EN完整原句 | 中文全文 |','|---|---|---|']
    for r in audit:
        if '.activities.' in r['path'] and r['path'].endswith('.condition'):preview.append(table([r['path'],r['en'],r['draft']]))
    preview+=['','### 全站補翻查詢證據','','| 查詢 | HTTP狀態／筆數 | 核實 |','|---|---|---|']
    for q in load('supplement-search'):preview.append(table([q['query'],'；'.join(str(p['status'])+'／'+str(p['received'])+'/'+str(p['total']) for p in q['audit']),'全部分頁讀取，'+str(len(q['units']))+'筆；實際units與id保存於supplement-search.json，已逐段確認有中文的container是否有對應中文段。']))
    preview+=['','## 9. 四項驗收','','- 規則核對：神性之怒自己回合第一個武器／徒手命中、1d6＋半等級向下取整與每次選類型；神之勇者4枚d12、附贈動作、長休全恢復及6／12／17級容量5／6／7；每次有效狂暴一次豁免重骰＋狂暴傷害加值且必須使用新結果；狂熱威儀附贈動作、至多10其他生物60呎、攻擊／豁免優勢到本人下回合、長休或消耗狂暴無需動作恢復；眾神之怒狂暴啟用時可變身、1分鐘或生命值0即止、長休恢復、飛行速度等於速度且懸浮、三種傷害抗力、30呎生物將降0時反應消耗狂暴取代生命值為等級，全部逐句核對。','','- 術語核對：draft_diff.py及terms_check.py皆回傳0；5項terms命中、2項逐條語境ack；lang '+str(len(missing))+'個無全部說明；最終完整成品及payload無它／如果／發充能／施展。','','- 機械驗證：validate.py完整classes6條28字串通過；排除4個原樣全欄位後payload為24字串，逐葉核對是本次成功產物的子集。content2個pages欄位另以check_description、compare_html和現行EN逐欄核對（共用CLI不涵蓋pages）。'+str(len(audit))+'映射位置已核對完整底稿／HTML；section、blockquote、span hide-in-embed、strong、UUID目標、Embed參數與2個新版巨集全保留；已移除註記及效果摘要回春不插回。','','- 中文通讀：遮住EN逐段閱讀完整中文，再對EN及底稿回查；介紹與神之勇者前兩段原HTML保留。條件／作用主體／資源與持續時間可辨，映射没有另造句子。'.replace('没有','沒有'),'','## 10. 待裁定','','1. 請確認第4節對既有神性之怒／神之勇者／專心熾志的最小修正，以及第8節補翻。本批尚未上傳。','2. 狂熱威儀效果摘要的Zealots缺所有格，建議採「賦予此效果的狂熱者的下個回合開始」；其規則依完整正文對齊，沒有改為受益者回合。','3. 保留項完整列在第5節，包括既有介紹與原稿聖鬥士姿態；建議保留以遵守既有翻譯／原稿優先規則。','','技能確認規則：translation-import [SKILL.md]('+str(ROOT/'.claude/skills/translation-import/SKILL.md').replace('\\','/')+') 第5步：「每批版本得到使用者明確確認後才上傳。」上一批確認不涵蓋本批。','','## 11. 修訂紀錄','','- 2026-10-09 v1：首次完成狂熱者道途底稿、26字串payload及完整預覽，尚未上傳；所有必要修正與來源差異已列報。']
    preview=[p.replace('所有最終欄位與目前本地EN／Weblate source逐字相同','所有待送欄位所對應的EN來源與目前本地EN／Weblate source逐字相同') for p in preview]
    write('preview.md','\n'.join(preview));write('full-comparison.md','\n'.join(preview[preview.index('## 3. 逐段及全部欄位對照'):]))
    pieces=['<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>狂熱者道途第4批中文通讀</title><style>body{max-width:1000px;margin:40px auto;font:18px/1.8 sans-serif;padding:0 20px}section.secret{background:#eee;padding:10px}pre{white-space:pre-wrap;font-size:14px}article{border-bottom:1px solid #ccc;padding:15px}</style><body><h1>狂熱者道途第4批 v1（尚未上傳）</h1>']
    for k,row in load('classes.aligned')['entries'].items():
        pieces+=['<article><h2>'+html.escape(row['name'])+'</h2>'+row['description']]
        for field in ['activities','effects','advancement']:
            for path,value in leaves(row.get(field,{})):pieces.append('<div><b>'+html.escape(field+'.'+path)+'：</b><div>'+value+'</div></div>')
        pieces.append('</article>')
    pieces+=['<h2>日誌</h2>',load('content.aligned')['entries']['Barbarian']['pages'][KEYS[0]]['description'],'</body></html>']
    write('reading.html','\n'.join(pieces))
    print('PREVIEW',DATA/(PREFIX+'.preview.md'),'mapping',len(audit),'supplements',len(basis),'qualifiers',len(qualified),'fragments',len(changes),'lang-misses',len(missing))

def verify_preview():
    info=load('verification');assert not info['approved'] and not info['uploaded']
    for suffix,sha in info['draft_sha256'].items():assert digest(suffix)==sha
    for c,sha in info['payload_sha256'].items():assert digest(c+'.upload.json')==sha
    checks=[]
    for c in ['classes','content']:
        full=dict(leaves(load(c+'.aligned')));payload=dict(leaves(load(c+'.upload')))
        assert all(full[p]==v for p,v in payload.items())
        local=read(ROOT/f'compendium/en/{PROJECT}/{PROJECT}.{c}.json')
        local_en=dict(leaves(local));cached=load(c+'.live')['units']
        current,audit=read_all(PROJECT,PROJECT+'-'+c);units={r['context']:r for r in current}
        for p in full:
            assert local_en[p]==cached[p]['source'][0]==units[p]['source'][0],('EN changed',p)
            assert cached[p]['target']==units[p]['target'],('Accepted target changed',p)
        checks.append({'component':c,'audit':audit,'scoped_strings':len(full),'payload_strings':len(payload),'sources_and_targets_unchanged':True,'payload_subset_of_validated_artifact':True})
    preview=(DATA/(PREFIX+'.preview.md')).read_text(encoding='utf-8')
    for i in range(1,12):assert '## '+str(i)+'. ' in preview
    assert (DATA/(PREFIX+'.terms-report.md')).read_text(encoding='utf-8') in preview
    assert len(load('mapping-audit'))==info['mapped_positions']
    assert (BASE/'_source'/(PREFIX+'.s2twp.txt')).read_text(encoding='utf-8')==(DATA/(PREFIX+'.source.s2twp.txt')).read_text(encoding='utf-8')
    assert not list(DATA.glob(PREFIX+'.*upload-response*'))
    save('preview-verification',{'checks':checks,'all_11_preview_sections':True,'raw_terms_report_included':True,'source_canonical_match':True,'no_upload_performed':True,'payload_hashes_match_preview':all(sha in preview for sha in info['payload_sha256'].values())})
    print(json.dumps(load('preview-verification'),ensure_ascii=False,indent=1))

APPROVED_HASHES={
 'classes':'bcebab2854534061aad15b9f6f8607b49c09ae0732ead95623c1b868eb54acc6',
 'content':'dbd9cf370d99f2da54a65024e62d8a52d14b7bb609476b8161f5336c7782234a',
}
AUTHORIZATION='目前沒甚麼問題，可以上傳'

def checked_payloads():
    info=load('verification');preview=(DATA/(PREFIX+'.preview.md')).read_text(encoding='utf-8')
    assert info['version']=='v1' and not info['pending_fields']
    assert info['payload_sha256']==APPROVED_HASHES
    for flag in ['mechanical_pass','all_exact_draft_matches','live_en_match','draft_check_pass','terms_check_pass']:assert info[flag],flag
    assert load('preview-verification')['all_11_preview_sections']
    assert digest('draft.txt')==info['draft_sha256']['draft.txt']
    assert load('classes.validated')==load('classes.aligned')
    expected={}
    for c,sha in APPROVED_HASHES.items():
        assert digest(c+'.upload.json')==sha and sha in preview
        expected[c]=dict(leaves(load(c+'.upload')))
        assert len(expected[c])=={'classes':24,'content':2}[c]
        full=dict(leaves(load(c+'.aligned')))
        for p,zh in expected[c].items():
            assert full[p]==zh
            en=load(c+'.live')['units'][p]['source'][0]
            assert not check_description(en,zh,{'Foundry','Active','Effect'}) and not compare_html(en,zh),p
    for row in load('retained'):assert row['path'] not in expected['classes']
    assert len(load('mapping-audit'))==46 and len(load('fragment-register'))==130
    return expected

def preflight():
    expected=checked_payloads();records={}
    assert not list(DATA.glob(PREFIX+'.*upload-attempt.json')) and not list(DATA.glob(PREFIX+'.*upload-response.json'))
    for c in expected:
        slug=PROJECT+'-'+c
        command('weblate.py',['status',PROJECT,slug],c+'.status.txt')
        status,translation=w.call('GET',f'/api/translations/{PROJECT}/{slug}/zh_Hant/')
        filename=f'compendium/zh-tw/{PROJECT}/{PROJECT}.{c}.json'
        assert status==200 and translation['filename']==filename
        status,settings=w.call('GET',f'/api/components/{PROJECT}/{slug}/')
        assert status==200 and settings.get('push')
        status,repo=w.call('GET',f'/api/components/{PROJECT}/{slug}/repository/')
        assert status==200 and not repo.get('merge_failure')
        rows,pagination=read_all(PROJECT,slug);units={r['context']:r for r in rows}
        cached=load(c+'.live')['units'];local=dict(leaves(read(ROOT/f'compendium/en/{PROJECT}/{PROJECT}.{c}.json')))
        for p in dict(leaves(load(c+'.aligned'))):
            assert local[p]==cached[p]['source'][0]==units[p]['source'][0],('EN changed',p)
            assert units[p]['target']==cached[p]['target'],('Accepted target changed',p)
        prior=[p for p in expected[c] if units[p]['has_suggestion']]
        assert not prior,('Inspect prior suggestions before proceeding',prior)
        save(c+'.component-before',units);save(c+'.before',{p:units[p] for p in expected[c]})
        records[c]={'filename':filename,'push_url_set':True,'repository':{k:repo.get(k) for k in ['needs_commit','needs_push','needs_merge','merge_failure']},'pagination':pagination,'matched_strings':len(expected[c]),'prior_suggestions':prior}
    save('preflight',records)
    save('approval',{'version':'v1','date':'2026-10-09','approved':True,'authorization':AUTHORIZATION,'scope':'狂熱者道途第4批v1，classes24＋content2；包含預覽中必要修正、補翻及效果摘要時點。method=suggest。','pending_preview_items_resolved':[1,2,3],'payload_sha256':APPROVED_HASHES,'draft_sha256':load('verification')['draft_sha256']})
    info=load('verification');info.update(approved=True,rule_review_complete=True,terminology_review_complete=True,chinese_readthrough_complete=True,preview_complete=True);save('verification',info)
    print(json.dumps(records,ensure_ascii=False,indent=1))

def upload_component(c):
    expected=checked_payloads()[c]
    assert load('approval')['approved'] and load('approval')['authorization']==AUTHORIZATION and load('approval')['payload_sha256']==APPROVED_HASHES
    assert load('preflight')[c]['matched_strings']==len(expected)
    assert not (DATA/(PREFIX+'.'+c+'.upload-response.json')).exists(),'Prior response exists; inspect actual suggestions before retrying.'
    assert not (DATA/(PREFIX+'.'+c+'.upload-attempt.json')).exists(),'Interrupted attempt exists; inspect actual suggestions before retrying.'
    # Record the attempt before POST so an interruption cannot lead to a blind retry.
    save(c+'.upload-attempt',{'date':'2026-10-09','method':'suggest','payload_sha256':APPROVED_HASHES[c]})
    status,body=w.upload(PROJECT,PROJECT+'-'+c,str(DATA/(PREFIX+'.'+c+'.upload.json')),method='suggest')
    save(c+'.upload-response',{'http_status':status,'response':body,'method':'suggest','sha256':APPROVED_HASHES[c]})
    print(json.dumps({'component':c,'http_status':status,'response':body},ensure_ascii=False))
    assert status in [200,201] and isinstance(body,dict),'Unclear upload; inspect actual suggestions before retrying'
    assert body['not_found']==0 and body['accepted']+body['skipped']==len(expected)
    assert body.get('total')==len(load(c+'.component-before')),'API total is component unit count'

def upload_classes():upload_component('classes')
def upload_content():upload_component('content')

def audit_upload():
    expected=checked_payloads();audits={}
    for c in expected:
        rows,pagination=read_all(PROJECT,PROJECT+'-'+c);after={r['context']:r for r in rows};before=load(c+'.component-before')
        assert set(before)==set(after)
        for p,unit in after.items():
            assert unit['source']==before[p]['source'],('EN changed after upload',p)
            assert unit['target']==before[p]['target'],('Formal target changed after upload',p)
        accepted=[];skipped=[]
        for p,zh in expected[c].items():
            if after[p]['target']==[zh]:skipped.append({'path':p,'reason':'Identical accepted target'})
            else:
                assert not before[p]['has_suggestion'] and after[p]['has_suggestion'],('Inspect suggestion',p)
                accepted.append({'path':p,'unit_id':after[p]['id'],'source_unchanged':True,'target_unchanged':True,'before_suggestion':False,'after_suggestion':True})
        response=load(c+'.upload-response')['response']
        assert len(accepted)==response['accepted'] and len(skipped)==response['skipped'] and response['not_found']==0
        stats={'component_units':len(after),'component_empty_or_source':sum(not any(u['target']) or u['target']==u['source'] for u in after.values()),'batch_strings':len(expected[c]),'batch_empty_or_source':sum(not any(after[p]['target']) or after[p]['target']==after[p]['source'] for p in expected[c]),'batch_has_suggestion':sum(after[p]['has_suggestion'] for p in expected[c])}
        save(c+'.after',{p:after[p] for p in expected[c]})
        audits[c]={'accepted':accepted,'skipped':skipped,'not_found':0,'response':response,'all_component_sources_unchanged':True,'all_component_targets_unchanged':True,'pagination':pagination,'statistics':stats}
    result={'complete':True,'accepted':sum(len(a['accepted']) for a in audits.values()),'skipped':sum(len(a['skipped']) for a in audits.values()),'not_found':0,'all_targets_unchanged':True,'component_verified_strings':sum(a['statistics']['component_units'] for a in audits.values()),'components':audits}
    save('upload-audit',result);print(json.dumps({k:v for k,v in result.items() if k!='components'},ensure_ascii=False))

def archive():
    import shutil
    checked_payloads();audit=load('upload-audit');assert audit['complete'] and audit['accepted']+audit['skipped']==26
    destination=BASE/'_done/subclasses/zealot'
    assert DATA.resolve().is_relative_to(BASE.resolve()) and destination.resolve().is_relative_to((BASE/'_done').resolve())
    files=sorted(DATA.glob(PREFIX+'.*'));assert files and all(f.is_file() and not (destination/f.name).exists() for f in files)
    destination.mkdir(parents=True,exist_ok=True)
    info=load('verification');info.update(approved=True,uploaded=True,method='suggest',upload_date='2026-10-09',accepted=audit['accepted'],skipped=audit['skipped'],not_found=0,archive_path=str(destination));save('verification',info)
    save('status',{'phase':'uploaded-and-audited','approved':True,'uploaded':True,'method':'suggest','accepted':audit['accepted'],'skipped':audit['skipped'],'not_found':0,'remaining_to_submit':0,'archive_path':str(destination)})
    def link(suffix,label):return '['+label+']('+str(destination/(PREFIX+'.'+suffix)).replace('\\','/')+')'
    report=['# 狂熱者道途第4批 v1：上傳報告（2026-10-09）','',f'使用者「{AUTHORIZATION}」確認完整v1，以method=suggest送出26個字串。新增{audit["accepted"]}、跳過{audit["skipped"]}、未匹配0；正式譯文未變動。','','| 元件 | 待送字串 | HTTP | accepted | skipped | not_found | total（全元件） |','|---|---:|---:|---:|---:|---:|---:|']
    for c in APPROVED_HASHES:
        reply=load(c+'.upload-response');body=reply['response']
        report.append(f'| {c} | {len(dict(leaves(load(c+".upload"))))} | {reply["http_status"]} | {body["accepted"]} | {body["skipped"]} | {body["not_found"]} | {body["total"]} |')
    report+=['','## 範圍及已確認差異','','6個classes條目24字串＋同名日誌頁2字串，原稿2–25行全部有對應，原稿全文、來源HTML及canonical轉繁檔保留。4個既有全欄位排除payload：狂熱者道途name／description、眾神之怒name與回春roll；介紹2個區塊及神之勇者前2個区塊原HTML保留。'.replace('区','區'),'','已確認必要修正：神性之怒明寫自己的回合並修傷害類型倒字；神之勇者補最大數量；專心熾志補完整狂暴傷害加值及新版巨集/span；狂熱威儀補其他生物，效果結束時點明寫賦予此效果者的下個回合；回春明寫取代降0。舊Foundry註記與舊效果摘要回春段依新版移除，主正文仍保留回春規則。眾神之怒沿用既有名稱；聖鬥士等敘事保留原稿。','', '所有問題句子的完整EN、原稿／既有中文、底稿、130個原稿差異片段、既有正文的最小修訂片段、補翻與3個activities.condition已在'+link('preview.md','完整預覽')+'逐項列出；使用者此次確認涵蓋預覽第10節全部3項。','','## 四項驗收','','- 規則：觸發、自己的回合／第一個目標、治療池容量及長休、豁免重骰加值與次數、其他生物及60呎／下回合、神聖姿態持續時間、飛行／懸浮／三種傷害抗力、30呎反應消耗狂暴取代降0均逐句核對完成。','- 術語：terms136、spells-glossary640完整核實；terms5項命中、2項語境ack；lang21個無逐條說明，130個draft_diff片段登記，24個補翻或巨集技術例外位置完整披露。draft_diff與terms_check均回傳0。','- 機械：完整classes6條28字串validate通過，排除4個原樣欄位得24字串payload；content真實pages2欄位另以check_description、compare_html及EN核對。46個映射位置與獨立底稿一致，HTML、span屬性、UUID、Embed參數及兩個巨集保留。','- 中文通讀：獨立通讀後回查EN與底稿；既有正文僅作已確認必要修正，映射未另造句子，禁用字回查通過。','','## 上傳及稽核','',f'上傳前後{audit["component_verified_strings"]}個API單元逐一比對，全部source及正式target不變。本批26個單元從無建議變為有建議，與HTTP回應accepted一致。total是整個元件筆數。建議待使用者於Weblate以has:suggestion審閱／接受，不標為正式已接受翻譯。','']
    for c,sha in APPROVED_HASHES.items():
        rec=load('preflight')[c];stat=audit['components'][c]['statistics']
        report+=['- '+c+' SHA-256：`'+sha+'`；'+link(c+'.upload.json','實際payload')+'。','- filename：`'+rec['filename']+'`；push URL已核實；repository：`'+json.dumps(rec['repository'],ensure_ascii=False)+'`。',f'- {c}空值或target等於source：{stat["component_empty_or_source"]}/{stat["component_units"]}；本批{stat["batch_empty_or_source"]}個為空值或target等於source，{stat["batch_has_suggestion"]}個有建議。']
    report+=['','底稿 SHA-256：`'+info['draft_sha256']['draft.txt']+'`。','','## 完整紀錄','','- '+link('preview.md','完整中英文預覽、來源差異、補翻、術語與conditions')+'。','- '+link('draft.txt','獨立底稿')+'；'+link('reading.html','中文通讀版')+'。','- '+link('upload-audit.json','逐欄上傳稽核')+'；'+link('approval.json','使用者確認版本與雜湊')+'。','','本批剩餘0個待送字串，未匹配0。野蠻人4個子職業已完成各批建議上傳；主頁原先無EN欄位的等級表／職業說明及狂野之心譯註仍留remaining，不標完成。沒有處理其他職業或舊批次因新版EN變更的重新映射。腳本留/scripts/translation-import/player-handbook/；沒有commit／push、新增術語或刪除建議。']
    write('2026-10-09.report.md','\n'.join(report))
    for suffix in ['preview.md','full-comparison.md']:
        path=DATA/(PREFIX+'.'+suffix);text=path.read_text(encoding='utf-8')
        text='> 2026-10-09：使用者「'+AUTHORIZATION+'」確認v1，已以建議上傳26字串（classes24＋content2），跳過0、未匹配0。下方保留確認時的完整對照；第10節事項均已確認。\n\n'+text
        path.write_text(text,encoding='utf-8')
    reading=DATA/(PREFIX+'.reading.html');reading.write_text(reading.read_text(encoding='utf-8').replace('v1（尚未上傳）','v1（已上傳26個建議）'),encoding='utf-8')
    immutable={PREFIX+'.draft.txt',PREFIX+'.classes.upload.json',PREFIX+'.content.upload.json'}
    # These resolved paths stay inside _incoming; move only this batch's files.
    for file in sorted(DATA.glob(PREFIX+'.*')):
        if file.name not in immutable:
            text=file.read_text(encoding='utf-8')
            text=text.replace(str(DATA).replace('\\','/'),str(destination).replace('\\','/'))
            text=text.replace(str(DATA).replace('\\','\\\\'),str(destination).replace('\\','\\\\'))
            file.write_text(text,encoding='utf-8')
        shutil.move(str(file),str(destination/file.name))
    for c,sha in APPROVED_HASHES.items():assert hashlib.sha256((destination/(PREFIX+'.'+c+'.upload.json')).read_bytes()).hexdigest()==sha
    assert hashlib.sha256((destination/(PREFIX+'.draft.txt')).read_bytes()).hexdigest()==info['draft_sha256']['draft.txt']
    index=BASE/'subclasses/index.md';lines=index.read_text(encoding='utf-8').splitlines()
    for i,line in enumerate(lines):
        if line.startswith('| 狂熱者道途 |'):
            parts=line.split('|');parts[-2]=' 第4批v1已上傳26個建議（classes24＋content2）；既有4全欄位及4正文區塊保留，必要修正／效果時點已確認 ';lines[i]='|'.join(parts)
        elif line.startswith('狂熱者道途第4批：'):
            lines[i]='狂熱者道途第4批：'+link('2026-10-09.report.md','上傳報告')+'；'+link('preview.md','完整預覽')+'。原稿2–25行全有對應；剩餘0個待送字串，未匹配0。'
    index.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'archive_path':str(destination),'accepted':audit['accepted'],'skipped':audit['skipped'],'not_found':0,'all_targets_unchanged':True},ensure_ascii=False))

if __name__=="__main__":
    {'collect':collect,'search':search,'prepare':prepare,'map':map_draft,'review':review,'verify-preview':verify_preview,'preflight':preflight,'upload-classes':upload_classes,'upload-content':upload_content,'audit':audit_upload,'archive':archive}[sys.argv[1]]()
