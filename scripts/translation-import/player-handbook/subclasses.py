"""Prepare subclass previews while preserving adequate existing translations."""
import argparse, html, json, re, sys
from pathlib import Path
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'_incoming/player-handbook'
DATA=BASE/'subclasses/berserker'
WEB=BASE/'_web/barbarian-subclasses'
sys.path.insert(0,str(ROOT/'.claude/skills/translation-import/scripts'))
import weblate as w
from html_blocks import Plan, compare_html, visible_text, LABEL
from validate import check_description, count_strings
from skeleton import build_entries, norm
from build_index import entry_names, aliases
import opencc
import hashlib, subprocess
from lang_compare import flat

KEYS=['Path of the Berserker','Frenzy','Mindless Rage','Retaliation','Intimidating Presence']
PREFIX='subclasses.berserker.1'
def read_json(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def english_text(value):
    # Unlabelled Reference links display their term; reports must not omit it.
    value=re.sub(r'&(?:amp;)?Reference\[([^\]]+)\](?!\{)',lambda m:m[1],value)
    return visible_text(value)
def load(suffix):return read_json(DATA/(PREFIX+'.'+suffix+'.json'))
def save(suffix,value):
    DATA.mkdir(parents=True,exist_ok=True)
    (DATA/(PREFIX+'.'+suffix+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=1),encoding='utf-8')
def write(suffix,text):
    DATA.mkdir(parents=True,exist_ok=True)
    (DATA/(PREFIX+'.'+suffix)).write_text(text+'\n',encoding='utf-8')
def leaves(node,prefix=''):
    if isinstance(node,dict):
        for key,value in node.items():yield from leaves(value,prefix+'.'+key if prefix else key)
    elif isinstance(node,str):yield prefix,node
def read_all(project,component):
    rows,audit,page=[],[],1
    while True:
        status,body=w.call('GET',f'/api/translations/{project}/{component}/zh_Hant/units/?page_size=1000&page={page}')
        assert status==200,(project,component,status)
        rows.extend(body['results'])
        audit.append({'page':page,'status':status,'received':len(body['results']),'total':body['count']})
        if not body.get('next'):
            assert len(rows)==body['count']
            return rows,audit
        page+=1

def collect():
    sys.path.insert(0,str(ROOT/'.claude/skills/web-source-extract/scripts'))
    import fetch_site as fetch
    WEB.mkdir(parents=True,exist_ok=True)
    toc_url='https://5echm.kagangtuya.top/webhelpcontents.htm'
    toc_path=WEB/'webhelpcontents.html'
    if not toc_path.exists():toc_path.write_text(fetch.get(toc_url),encoding='utf-8')
    candidates=[url for url in fetch.links(toc_url,toc_path.read_text(encoding='utf-8')) if '玩家手册2024/角色职业/野蛮人/' in unquote(url) and '狂战士' in unquote(url)]
    candidates=sorted(set(candidates))
    assert len(candidates)==1,candidates
    url=candidates[0]
    name=fetch.slug(url)
    txt=WEB/(name+'.txt')
    raw_path=WEB/'_raw'/(name+'.html')
    raw_path.parent.mkdir(exist_ok=True)
    if not txt.exists():
        raw=fetch.get(url)
        raw_path.write_text(raw,encoding='utf-8')
        txt.write_text(fetch.to_text(raw),encoding='utf-8')
    save('source',{'url':url,'decoded_url':unquote(url),'text_path':str(txt),'html_path':str(raw_path),'status':'ok'})
    manifest_path=WEB/'manifest.json'
    manifest=read_json(manifest_path) if manifest_path.exists() else []
    manifest=[entry for entry in manifest if entry['url']!=url]+[{'url':url,'status':'ok','file':name}]
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=1),encoding='utf-8')
    print('Verified source:',unquote(url))
    print(txt.read_text(encoding='utf-8'))
    for component in ['classes','content']:
        slug='dnd-players-handbook-'+component
        status,translation=w.call('GET','/api/translations/dnd-players-handbook/'+slug+'/zh_Hant/')
        assert status==200 and translation['filename']=='compendium/zh-tw/dnd-players-handbook/dnd-players-handbook.'+component+'.json'
        rows,audit=read_all('dnd-players-handbook',slug)
        units={row['context']:row for row in rows}
        save(component+'.live',{'filename':translation['filename'],'audit':audit,'units':units})
        relevant={path:row['target'][0] for path,row in units.items() if (component=='classes' and any(path.startswith('entries.'+key+'.') for key in KEYS)) or (component=='content' and path.startswith('entries.Barbarian.pages.Path of the Berserker.'))}
        print(component,len(rows),'complete HTTP 200')
        print(json.dumps(relevant,ensure_ascii=False,indent=1))
    for component in ['terms','spells-glossary']:
        rows,audit=read_all('dnd-5e-2024-zh-tw',component)
        save(component+'.live',{'audit':audit,'units':rows})
        print(component,len(rows),'complete HTTP 200')
    terms={row['source'][0]:row['target'][0] for row in load('terms.live')['units'] if any(row['target']) and row['target']!=row['source']}
    glossary={row['source'][0]:row['target'][0] for row in load('spells-glossary.live')['units'] if any(row['target']) and row['target']!=row['source']}
    save('term_index',{'terms':terms,'spells_glossary':glossary,'entry_names':{k:dict(v) for k,v in entry_names(str(ROOT/'compendium/zh-tw'),'dnd-players-handbook').items()},'aliases':aliases(str(ROOT/'.claude/skills/translation-import/glossary.tsv'))})

def prepare():
    source=load('source')
    original=Path(source['text_path']).read_text(encoding='utf-8')
    write('source.txt',original.rstrip())
    write('source.s2twp.txt',opencc.OpenCC('s2twp').convert(original).rstrip())
    live=load('classes.live')['units']
    existing_intro=Plan(live['entries.Path of the Berserker.description']['target'][0]).blocks
    existing_frenzy=Plan(live['entries.Frenzy.description']['target'][0]).blocks[0]
    assert len(existing_intro)==2 and all(re.search('[一-鿿]',visible_text(b.html)) for b in existing_intro)
    assert re.search('[一-鿿]',visible_text(existing_frenzy.html))
    texts={
      'Path of the Berserker':['狂戰士道途']+[visible_text(b.html) for b in existing_intro],
      'Frenzy':['狂怒',visible_text(existing_frenzy.html)],
      'Mindless Rage':['無我狂暴','狂暴啟用期間，你具有對魅惑與恐慌狀態的免疫。當你進入狂暴時，若你已陷入魅惑或恐慌狀態，則你身上的該狀態會結束。'],
      'Retaliation':['報償','當位於你5呎內的一名生物對你造成傷害時，你可以採取反應，使用武器或徒手打擊對該生物發動一次近戰攻擊。'],
      'Intimidating Presence':['威懾之姿','你可以採取一個附贈動作，用你那令人魂消膽喪的氣勢，在原初之力的輔助下令他者心生恐懼。當你如此做時，每名位於源自你的30呎發散範圍內、由你選擇的生物都必須進行一次感知豁免檢定（DC等同於8＋你的力量調整值＋你的熟練加值）。豁免失敗的生物陷入恐慌狀態，持續1分鐘。陷入恐慌的生物在其每個回合結束時重複該豁免，成功則結束其身上的該效應。','此特性一經使用，直到完成長休前，你都無法再次使用，除非你消耗一次狂暴使用次數（無需動作）來恢復此特性的使用次數。'],
      'Path of the Berserker (journal)':['狂戰士道途']+[visible_text(b.html) for b in existing_intro],
    }
    write('draft.txt','\n\n'.join('### '+key+'\n'+'\n'.join(value) for key,value in texts.items()))
    supplements={
      'Frenzy':['【Foundry註記】','傷害行動會隨著你的等級提升自動調整比例值，並讓你在傷害骰的對話框中選擇要使用的傷害類型。此行動之後會記住你的選擇。'],
      'Mindless Rage':['【Foundry註記】','此特性包含一項Active Effect，可提供對魅惑與恐慌狀態的免疫。不過，當你開始狂暴時，此Active Effect不會自動套用。'],
      'Intimidating Presence':['【Foundry註記】','豁免行動包含一項Active Effect，會加上恐慌狀態。','恢復行動會消耗一次狂暴使用次數，並恢復威懾之姿的使用次數。'],
      'Nested Fields':['子職業特性','無我狂暴','報償','當位於你5呎內的一名生物對你造成傷害時','以狂暴恢復使用次數','受威懾'],
    }
    write('supplement.draft.txt','\n\n'.join('### '+key+'\n'+'\n'.join(value) for key,value in supplements.items()))
    save('draft-fingerprints',{suffix:__import__('hashlib').sha256((DATA/(PREFIX+'.'+suffix+'.txt')).read_bytes()).hexdigest() for suffix in ['draft','supplement.draft']})
    print('Independent source/retained Chinese draft and supplement draft prepared; no payload written yet.')

def sections(suffix):
    text=(DATA/(PREFIX+'.'+suffix+'.txt')).read_text(encoding='utf-8')
    return {m[1]:[line for line in m[2].strip().splitlines() if line.strip()] for m in re.finditer(r'^### ([^\r\n]+)\n(.*?)(?=^### |\Z)',text,re.M|re.S)}

def map_draft():
    draft,supp=sections('draft'),sections('supplement.draft')
    local=read_json(ROOT/'compendium/en/dnd-players-handbook/dnd-players-handbook.classes.json')['entries']
    journal=read_json(ROOT/'compendium/en/dnd-players-handbook/dnd-players-handbook.content.json')['entries']['Barbarian']['pages']['Path of the Berserker']
    clive,plive=load('classes.live')['units'],load('content.live')['units']
    source_lines=Path(load('source')['text_path']).read_text(encoding='utf-8').splitlines()
    source_ranges={'Path of the Berserker':[(3,3),(4,4)],'Frenzy':[(6,6)],'Mindless Rage':[(9,9)],'Retaliation':[(12,12)],'Intimidating Presence':[(14,14),(15,15)]}
    mapping=[]
    retained=[]
    sheet={'schema_version':2,'book':'dnd-players-handbook','component':'classes','entries':{}}
    built_classes={}
    for key in KEYS:
        name=draft[key][0]
        base='entries.'+key
        record={'name_en':local[key]['name'],'name':name,'blocks':[]}
        plan=Plan(local[key]['description'])
        main=draft[key][1:]
        added=supp.get(key,[])
        assert len(main)+len(added)==len(plan.blocks)
        for index,(block,line) in enumerate(zip(plan.blocks,main+added)):
            is_supplement=index>=len(main)
            zh=line
            preserved=key=='Path of the Berserker' or (key=='Frenzy' and index==0)
            if preserved:
                zh=Plan(clive[base+'.description']['target'][0]).blocks[index].html
                assert visible_text(zh)==line
            elif '<strong>Foundry Note</strong>' in block.html:
                zh='<strong>'+line+'</strong>'
            else:
                for word,label in [('Damage','傷害'),('Save','豁免'),('Recharge','恢復')]:
                    if '<strong>'+word+'</strong>' in block.html:
                        assert label+'行動' in zh
                        zh=zh.replace(label+'行動','<strong>'+label+'</strong>行動',1)
                for target,label in [('Charmed','魅惑'),('Frightened','恐慌')]:
                    token='&amp;Reference['+target+']'
                    if token not in block.html:continue
                    if key=='Intimidating Presence':
                        assert '陷入恐慌的生物在' in zh
                        zh=zh.replace('陷入恐慌的生物在','陷入'+token+'{'+label+'}的生物在',1)
                    else:
                        assert label in zh
                        zh=zh.replace(label,token+'{'+label+'}',1)
            assert visible_text(zh)==line,(key,block.id,'Mapping changed draft')
            assert not compare_html(block.html,zh),(key,block.id,compare_html(block.html,zh))
            basis='原稿沒有Foundry註記；採獨立補翻底稿，使用行動、Active Effect、比例值及既有規則詞。' if is_supplement else ''
            record['blocks'].append({'id':block.id,'en':block.html,'zh':zh,'source':'supplement' if is_supplement else 'draft','basis':basis})
            bounds=None if is_supplement else source_ranges[key][index]
            mapping.append({'component':'classes','path':base+'.description/'+block.id,'en':block.html,'zh':zh,'draft':line,'source':'existing' if preserved else ('supplement' if is_supplement else 'draft'),'source_lines':bounds,'source_original':'\n'.join(source_lines[bounds[0]-1:bounds[1]]) if bounds else '原稿無此Foundry註記。','retained':preserved,'exact_visible_match':True})
        sheet['entries'][key]=record
    nested=supp['Nested Fields']
    extras={
      'Path of the Berserker':{'advancement':{'Subclass Features':{'title':nested[0]}}},
      'Mindless Rage':{'effects':{'Mindless Rage':{'name':nested[1]}}},
      'Retaliation':{'activities':{'Retaliate':{'name':nested[2],'condition':nested[3]}}},
      'Intimidating Presence':{'activities':{'Recharge with Rage':{'name':nested[4]}},'effects':{'Intimidated':{'name':nested[5]}}},
    }
    for key,value in extras.items():sheet['entries'][key].update(value)
    save('classes.sheet',sheet)
    normalized={key:norm('\n'.join(draft[key])) for key in KEYS}
    all_classes=build_entries(sheet,{key:local[key] for key in KEYS},normalized)['entries']
    for key,row in all_classes.items():
        base='entries.'+key
        out={}
        for field,zh in row.items():
            if isinstance(zh,str):
                target=clive[base+'.'+field]['target'][0]
                assert clive[base+'.'+field]['source']==[local[key][field]]
                if key=='Path of the Berserker':assert target==zh,(base,field,'Adequate existing translation changed')
                if target==zh:
                    retained.append({'component':'classes','path':base+'.'+field,'en':local[key][field],'zh':target,'reason':'現行中文語意及規則核對後沿用；不列入上傳payload。'})
                    continue
                out[field]=zh
            else:
                # Nested translations are compared leaf by leaf, not blindly
                # emitted with the entry; retained leaves are omitted.
                for relative,leaf in leaves(zh,field):
                    path=base+'.'+relative
                    original=dict(leaves(local[key]))[relative]
                    assert clive[path]['source']==[original]
                    current=clive[path]['target'][0]
                    if current==leaf:
                        retained.append({'component':'classes','path':path,'en':original,'zh':current,'reason':'現行已翻欄位語意一致，原樣保留；不列入payload。'})
                    else:
                        obj=out
                        parts=relative.split('.')
                        for part in parts[:-1]:obj=obj.setdefault(part,{})
                        obj[parts[-1]]=leaf
            if field!='description':
                for relative,leaf in leaves({field:zh}):
                    path=base+'.'+relative
                    mapping.append({'component':'classes','path':path,'en':dict(leaves(local[key]))[relative],'zh':leaf,'draft':leaf,'source':'existing' if clive[path]['target']==[leaf] else ('draft' if relative=='name' else 'supplement'),'source_lines':None,'source_original':'原稿名稱或正文可推得；嵌套介面欄位無獨立原稿。','retained':clive[path]['target']==[leaf],'exact_visible_match':True})
        if out:built_classes[key]=out
    # Journal text has the same English introduction as the already translated
    # class. Reuse that accepted Chinese as its independent draft.
    jp=Plan(journal['description'])
    journal_text=draft['Path of the Berserker (journal)'][1:]
    replacements={}
    iterator=iter(journal_text)
    for block in jp.blocks:
        line=next(iterator) if visible_text(block.html) else ''
        zh=line or block.html
        if '@UUID[' in block.html:
            token=next(LABEL.finditer(block.html))[1]
            label=draft['Path of the Berserker'][0]
            zh=zh.replace(label,token+'{'+label+'}',1)
        assert visible_text(zh)==line
        assert not compare_html(block.html,zh),(block.id,compare_html(block.html,zh))
        replacements[block.id]=zh
        mapping.append({'component':'content','path':'entries.Barbarian.pages.Path of the Berserker.description/'+block.id,'en':block.html,'zh':zh,'draft':line,'source':'existing-corresponding-class' if line else 'protected','source_lines':[3,3] if block.id=='b0002' else ([4,4] if line else None),'source_original':source_lines[2] if block.id=='b0002' else (source_lines[3] if line else '插圖Embed無可見文字，原樣保留。'),'retained':False,'exact_visible_match':True})
    assert next(iterator,None) is None
    journal_value={'name':draft['Path of the Berserker (journal)'][0],'description':jp.build(replacements)}
    content_fields={}
    for field,zh in journal_value.items():
        path='entries.Barbarian.pages.Path of the Berserker.'+field
        assert plive[path]['source']==[journal[field]]
        if plive[path]['target']==[zh]:retained.append({'component':'content','path':path,'en':journal[field],'zh':zh,'reason':'現行中文與底稿相同，不列入payload。'})
        else:content_fields[field]=zh
    mapping.append({'component':'content','path':'entries.Barbarian.pages.Path of the Berserker.name','en':journal['name'],'zh':journal_value['name'],'draft':journal_value['name'],'source':'existing-corresponding-class','source_lines':[2,2],'source_original':source_lines[1],'retained':False,'exact_visible_match':True})
    class_payload={'entries':built_classes}
    content_payload={'entries':{'Barbarian':{'pages':{'Path of the Berserker':content_fields}}}}
    for component,payload in [('classes',class_payload),('content',content_payload)]:
        originals={key:value for key,value in leaves({'entries':{key:local[key] for key in KEYS}})} if component=='classes' else dict(leaves({'entries':{'Barbarian':{'pages':{'Path of the Berserker':journal}}}}))
        for path,zh in leaves(payload):
            assert not check_description(originals[path],zh,{'Foundry','Active','Effect'}),(path,check_description(originals[path],zh,{'Foundry','Active','Effect'}))
            assert path not in [r['path'] for r in retained]
        save(component+'.aligned',payload)
        save(component+'.upload',payload)
    assert Plan(class_payload['entries']['Frenzy']['description']).blocks[0].html==Plan(clive['entries.Frenzy.description']['target'][0]).blocks[0].html
    save('mapping-audit',mapping)
    save('retained',retained)
    fingerprints=load('draft-fingerprints')
    for suffix,digest in fingerprints.items():assert __import__('hashlib').sha256((DATA/(PREFIX+'.'+suffix+'.txt')).read_bytes()).hexdigest()==digest
    info={'version':'v1','scope':'Path of the Berserker and four subclass features + matching journal introduction','classes_entries':len(built_classes),'classes_strings':count_strings(class_payload),'content_entries':1,'content_strings':count_strings(content_payload),'retained_strings':len(retained),'retained_body_blocks':sum(r['retained'] for r in mapping if '/' in r['path']),'mapped_positions':len(mapping),'supplement_blocks':sum(r['source']=='supplement' for r in mapping),'all_exact_draft_matches':True,'live_en_match':True,'mechanical_pass':True,'draft_sha256':fingerprints,'payload_sha256':{c:__import__('hashlib').sha256((DATA/(PREFIX+'.'+c+'.upload.json')).read_bytes()).hexdigest() for c in ['classes','content']},'approved':False,'uploaded':False}
    save('verification',info)
    print(json.dumps(info,ensure_ascii=False))

def review():
    mapping,retained,info=load('mapping-audit'),load('retained'),load('verification')
    draft,supp=sections('draft'),sections('supplement.draft')
    src=load('source')
    original_lines=Path(src['text_path']).read_text(encoding='utf-8').splitlines()
    by_path={row['path']:row for row in mapping}
    names={'Path of the Berserker':(2,2),'Frenzy':(5,5),'Mindless Rage':(7,8),'Retaliation':(10,11),'Intimidating Presence':(13,13)}
    rule={
      'Path of the Berserker/b0001':'標語的Channel Rage into Violent Fury為引導狂暴進入暴力狂怒；既有中文與EN方向一致，原樣保留。原稿以憤怒進入狂暴的方向不同，未採原稿重新改寫。',
      'Path of the Berserker/b0002':'primarily toward violence、untrammeled fury、thrill in chaos、Rage seize and empower均有對應；既有中文的捨生忘死投入廝殺較EN有文學增飾，未引入遊戲機制，依使用者指示不改。',
      'Frenzy/b0001':'啟用狂暴且使用魯莽攻擊；自己回合力量攻擊命中的第一個目標，而非要求第一下攻擊必須命中；額外骰數由狂暴傷害加值決定，傷害類型沿用武器／徒手打擊。既有中文以擲等同於加值的D6簡述骰數，結果簡述合計；此表達較EN精簡，原样保留並報告。',
      'Frenzy/b0002':'Foundry註記標題是新補翻；保留原strong格式。',
      'Frenzy/b0003':'Damage行動隨升級自動調整比例值；在傷害骰對話框選類型，之後記住選擇。沒有自行加入自動套用遊戲傷害的規則。',
      'Mindless Rage/b0001':'狂暴啟用期間對魅惑及恐慌兩種狀態免疫；進入狂暴時既有狀態結束；不新增其他狀態免疫或額外豁免。',
      'Mindless Rage/b0002':'Foundry註記標題。',
      'Mindless Rage/b0003':'Active Effect提供兩種狀態免疫，但開始狂暴時不自動套用；保留否定與時點。',
      'Retaliation/b0001':'受到距自己不超過5呎的生物傷害才可反應；對同一生物進行一次近戰攻擊，使用武器或徒手打擊；沒有視線或傷害類型限制。',
      'Intimidating Presence/b0001':'附贈動作；源自自己30呎發散範圍，每名自選生物而非所有生物；感知豁免DC8＋力量調整值＋熟練加值；失敗恐慌1分鐘，每個受影響生物自身每回合結束再豁免，成功结束其身上效應。',
      'Intimidating Presence/b0002':'使用後長休前不可再用，除非消耗一次狂暴使用次數恢復，恢復無需動作；没有把恢復改成附贈動作或只限狂暴啟用期間。',
      'Intimidating Presence/b0003':'Foundry註記標題。',
      'Intimidating Presence/b0004':'Save行動包含加入恐慌的Active Effect；不宣稱自動成功或省略豁免。',
      'Intimidating Presence/b0005':'Recharge行動消耗一次狂暴，恢復威懾之姿的使用；介面行動实际key是Recharge with Rage，顯示名稱為以狂暴恢復使用次數，技術key不變。',
    }
    pairs=[]
    for row in mapping:
        local=row['path'].removeprefix('entries.')
        if row['component']=='classes' and '.description/' in local:
            key,block=local.split('.description/')
            row['rule_review']=rule[key+'/'+block]
        elif row['component']=='content' and '.description/' in local:
            block=local.split('.description/')[1]
            row['rule_review']='插圖Embed無可見文字，原樣保留全部參數。' if row['source']=='protected' else rule['Path of the Berserker/'+('b0001' if block=='b0002' else 'b0002')]+' 日誌正文EN與classes介紹相同，套回既有中文底稿並保留UUID。'
        else:
            row['rule_review']='名稱及介面欄位依來源名稱／正文逐字映射；參照既定術語及已查核同名欄位，技術key不变。'
            key=next((k for k in KEYS if row['path'].startswith('entries.'+k+'.')),None)
            if key and row['path'].endswith('.name') and row['path']=='entries.'+key+'.name':
                a,b=names[key]
                row['source_lines']=[a,b]
                row['source_original']='\n'.join(original_lines[a-1:b])
        row['rule_review']=row['rule_review'].replace('原样','原樣').replace('结束','結束').replace('没有','沒有').replace('实际','實際').replace('不变','不變')
        assert visible_text(row['zh'])==row['draft']
        if row['source']=='protected':continue
        english=english_text(row['en'])
        clauses=[s.strip() for s in re.split(r'(?<=[.!?])\s+(?=[A-Z])',english) if s.strip()]
        chinese=[s.strip() for s in re.split(r'(?<=[。！？])',row['draft']) if s.strip()]
        # Existing narrative has three Chinese sentences for two English ones;
        # preserving the approved paragraph takes precedence over forced slots.
        if len(clauses)!=len(chinese):
            assert 'Path of the Berserker' in row['path']
            pairs.append({'path':row['path'],'unit':'完整段落（既有句子拆分不改）','en':english,'zh':row['draft'],'qualifiers':re.findall(r'\b(?:this|these|that|the|following|one of|each|any|all|first|same|once)\b',english,re.I),'review':row['rule_review']})
        else:
            for i,(en,zh) in enumerate(zip(clauses,chinese),1):
                pairs.append({'path':row['path'],'unit':i,'en':en,'zh':zh,'qualifiers':re.findall(r'\b(?:this|these|that|the|following|one of|each|any|all|first|same|once)\b',en,re.I),'review':row['rule_review']})
    save('mapping-audit',mapping)
    save('sentence-audit',pairs)

    # Use untouched EN nested values so the required lang comparison covers
    # conditions as well as descriptions, retained text and both components.
    cl=read_json(ROOT/'compendium/en/dnd-players-handbook/dnd-players-handbook.classes.json')['entries']
    co=read_json(ROOT/'compendium/en/dnd-players-handbook/dnd-players-handbook.content.json')['entries']['Barbarian']['pages']['Path of the Berserker']
    audit_sheet={'schema_version':2,'entries':{}}
    for key,item in [(k,cl[k]) for k in KEYS]+[('Path of the Berserker (journal)',co)]:
        item_row={'name_en':item['name'],'blocks':[{'id':b.id,'en':b.html} for b in Plan(item['description']).blocks]}
        for field in ['activities','effects','advancement']:
            if field in item:item_row[field]=item[field]
        audit_sheet['entries'][key]=item_row
    save('audit.sheet',audit_sheet)
    combined=(DATA/(PREFIX+'.draft.txt')).read_text(encoding='utf-8')+'\n'+(DATA/(PREFIX+'.supplement.draft.txt')).read_text(encoding='utf-8')
    write('review.draft.txt',combined.rstrip())
    result=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'.claude/skills/translation-import/scripts/lang_compare.py'),str(DATA/(PREFIX+'.audit.sheet.json')),'--draft',str(DATA/(PREFIX+'.review.draft.txt'))],capture_output=True,text=True,encoding='utf-8')
    assert result.returncode==0,result.stderr
    write('lang-compare.md',result.stdout.rstrip())
    index=load('term_index')
    lang_en=flat(read_json(ROOT/'lang/en.json'))
    lang_zh=flat(read_json(ROOT/'lang/zh-tw.json'))
    choices={
      'action':('動作','遊戲規則動作，採lang；no action required＝無需動作。'),
      'activity':('行動','使用者裁定及lang一致；只出現於補翻底稿，合併底稿已納入查核。'),
      'applied':('套用','not applied automatically是自動套用的否定，非UI完成狀態已套用。'),
      'attack':('攻擊','採lang；Strength-based為基於力量攻擊，melee為近戰。'),
      'bonus':('加值','狂暴傷害加值／熟練加值，不用UI未翻Bonus。'),
      'bonus action':('附贈動作','遊戲附贈動作，採既定用語及lang。'),
      'charmed':('魅惑','採現行lang及原稿；正文Reference標籤及補翻免疫均回查。'),
      'classes':('—','Embed參數classes="right three"是技術資料，無可見中文，保留原值。'),
      'condition':('狀態','遊戲狀態，採lang；非行動condition欄位中文名。'),
      'condition immunity':('狀態免疫','補翻以對魅惑與恐慌狀態的免疫完整表達；未添加其他狀態。'),
      'conditions':('狀態','魅惑與恐慌兩項狀態，中文不加英文複數詞尾。'),
      'creature':('生物','採規則詞生物；數量依句中each／a，用每名／一名，不套UI計數模板。'),
      'damage':('傷害','正文及Damage行動標籤同詞，原strong位置保留。'),
      'damage bonus':('傷害加值','Rage Damage bonus為狂暴傷害加值，沿用已譯正文。'),
      'damage roll':('傷害骰','新Foundry補翻使用lang傷害骰；已譯Frenzy正文不為統一格式改寫。'),
      'each':('每名／每個','each creature用每名；each turns用每個回合，逐句範圍完整。'),
      'each creature':('每名生物','不是每個生物UI模板；每名自選生物保留選擇範圍。'),
      'effect':('效應／Active Effect','規則effect用效應；Foundry Active Effect依使用者保留英文，不用UI效果強制替換。'),
      'emanation':('發散','terms Emanation＝發散優先，與lang適用變體一致；原稿光環區域改為30呎發散範圍。'),
      'empower':('加持','已接受介紹以因狂暴與怒火加持表達empower，語意一致，依使用者保留，不強改強化。'),
      'feature':('特性','採lang及原稿；此特性為Intimidating Presence等能力。'),
      'features':('特性','子職業特性標題已接受，原樣保留。'),
      'feet':('呎','台灣單位呎；不採英呎、不換公尺。'),
      'foot':('呎','30-foot作距離單位同呎。'),
      'forward':('之後','going forward為之後記住選擇，不是UI聯動。'),
      'frightened':('恐慌','使用者／lang既定用語；Reference與效應、補翻均回查，不用恐懼作正式狀態。'),
      'level':('等級','Foundry隨你的等級提升，採lang，沒有改已翻正文。'),
      'level up':('等級提升','Foundry自動調整的條件，完整中文等級提升，非UI升級按鈕。'),
      'long':('長休','完整Long Rest採長休，不套長距離。'),
      'long rest':('長休','採lang；until依使用者句式直到完成長休前，例外狂暴消耗保留。'),
      'melee':('近戰','採lang及原稿。'),
      'melee attack':('近戰攻擊','同完整規則詞；一次、同一來源生物及武器／徒手限制保留。'),
      'minute':('分鐘','1分鐘，採lang；不是延長每回合重新1分鐘。'),
      'modifier':('調整值','力量調整值，採lang。'),
      'number':('骰數（既有精簡表達）','Frenzy既有正文擲等同於狂暴傷害加值的D6簡述骰數；較EN精簡，依使用者原樣保留並完整報告。'),
      'proficiency':('熟練加值','本批只在完整Proficiency Bonus中，正是熟練加值語境。'),
      'proficiency bonus':('熟練加值','完整規則詞，與lang一致。'),
      'reaction':('反應','使用者裁定採取反應，不加動作；lang另有反應動作變體不採。'),
      'recharge':('恢復使用次數','恢復的是狂暴／威懾之姿使用次數，不是物品充能；按原稿恢復用法與正文。'),
      'reference':('—','&Reference技術標記的lang工具命中；技術英文保留，顯示標籤完整中文。'),
      'rest':('長休','只出現在Long Rest，按完整詞組不拆成休息。'),
      'roll':('擲／傷害骰','Frenzy已譯擲D6保留；Foundry damage roll依lang傷害骰，不改成UI擲骰。'),
      'save':('豁免','Save行動及repeat the save採豁免；不添加新行動消耗。'),
      'saving throw':('豁免檢定','本批感知豁免檢定，採既有用詞與lang適用變體，不用豁免骰。'),
      'select':('選擇','傷害對話框的選擇，lang一致。'),
      'strength':('力量','已譯Frenzy力量攻擊、DC力量調整值，lang一致。'),
      'subclass':('子職業','使用者已裁定、lang及已接受子職業特性一致，不用子職。'),
      'target':('目標','Frenzy第一個命中目標，已譯正文保留；不套個目標UI模板。'),
      'three':('—','Embed CSS類別three，沒有可見三字，原樣保留。'),
      'turn':('回合','自己回合與目標每回合結束分別核對。'),
      'turns':('回合','每個恐慌生物自身每個回合；與自己回合不同。'),
      'type':('類型','傷害類型，採lang。'),
      'unarmed':('徒手打擊','完整Unarmed Strike採徒手打擊，不只徒手。'),
      'walk':('遵行','walk the Path是遵行道途，既有接受譯文原樣保留，不改成移動速度的步行。'),
      'weapon':('武器','武器或徒手打擊，採lang；傷害類型同源。'),
      'wisdom':('感知','感知豁免，lang一致。'),
    }
    def lookup(section,name):return next((v for k,v in index[section].items() if k.lower()==name.lower()),'—')
    terms=[]
    for line in result.stdout.splitlines():
        if not line.startswith('| ') or line.startswith('| EN '):continue
        cells=[c.strip() for c in line.strip('|').split('|')]
        if len(cells)!=4:continue
        en,lang,mark,key=cells
        assert en in choices,('Unexplained lang difference',en)
        chosen,reason=choices[en]
        rg=re.compile(r'(?<![a-z])'+re.escape(en)+r'(?![a-z])',re.I)
        terms.append({'en':en,'chosen':chosen,'terms':lookup('terms',en),'spells_glossary':lookup('spells_glossary',en),'lang':lang,'lang_key':key,'tool_draft_mark':mark,'context':reason,'paths':[r['path'] for r in mapping if rg.search(visible_text(r['en']))],'technical_paths':[r['path'] for r in mapping if r['source']=='protected' and rg.search(r['en'])],'checked':True})
    complete_names={**{key:draft[key][0] for key in KEYS},'Rage':'狂暴','Reckless Attack':'魯莽攻擊','Unarmed Strike':'徒手打擊','Active Effect':'Active Effect','scale value':'比例值','Retaliate':supp['Nested Fields'][2],'Intimidated':supp['Nested Fields'][5],'Recharge with Rage':supp['Nested Fields'][4]}
    for english,chosen in complete_names.items():
        paths=[r['path'] for r in mapping if re.search(r'(?<![a-z])'+re.escape(english)+r'(?![a-z])',visible_text(r['en']),re.I)]
        if not paths and english=='scale value':paths=['entries.Frenzy.description/b0003']
        # Untranslated leaf names are also matched via EN source, even when an
        # identical retained name is only in the retained-field audit.
        paths+= [r['path'] for r in retained if r['en']==english and r['path'] not in paths]
        langs=sorted({lang_zh[k] for k,v in lang_en.items() if isinstance(v,str) and v.lower()==english.lower() and k in lang_zh})
        if english=='Path of the Berserker':reason='現行Weblate已接受狂戰士道途，根名稱、正文及子職業特性標題保留；未翻日誌頁採同名。'
        elif english in ['Rage','Reckless Attack']:reason='現行2024 Weblate名稱已核實，沿用；没有新增正式詞條。'
        elif english in ['Active Effect','scale value']:reason='使用者已裁定保留Active Effect及scale value＝比例值；只用於Foundry註記。'
        elif english=='Unarmed Strike':reason='原稿、既有正文及lang完整用詞徒手打擊，沒有改既有正文。'
        elif english in KEYS:reason='現行Weblate、2024 repo、其他書名稱索引及兩套術語集查無中文名稱，沿用來源s2twp名稱，待本批確認。'
        else:reason='原稿無獨立介面名稱；按正文、對應特性及EN補翻，待本批確認，未新增正式詞條。'
        terms.append({'en':english,'chosen':chosen,'terms':lookup('terms',english),'spells_glossary':lookup('spells_glossary',english),'lang':'／'.join(langs) or '—','context':reason.replace('没有','沒有'),'paths':paths,'checked':True})
    save('term-audit',terms)

    issues=[]
    def add(identifier,title,path,reason,category='差異核對',source_text=None):
        row=by_path[path]
        issues.append({'id':identifier,'title':title,'component':row['component'],'path':path,'en_full':english_text(row['en']),'source_full':source_text or row['source_original'],'current_full':row['draft'] if row['retained'] else ((load(row['component']+'.live')['units'].get(path.split('/')[0],{}).get('target') or [''])[0]),'draft_full':row['draft'],'reason':reason,'category':category,'retained':row['retained'],'status':'原樣保留，無修改建議。' if row['retained'] else '待本批v1確認。'})
    add('D01','原稿標語方向與EN不同，但既有中文正確','entries.Path of the Berserker.description/b0001','原稿以強烈憤怒進入狂暴；EN為引導狂暴進入暴力狂怒。既有中文方向相符，依使用者原樣保留；未翻日誌欄位沿用此中文。','既有譯文保留')
    add('D02','既有介紹有文學增飾，沒有規則差異','entries.Path of the Berserker.description/b0002','既有中文的捨生忘死投入廝殺較EN有文學增飾，Rage加持與戰鬥狂亂方向一致。原稿句式亦不同，均完整列出；依使用者已有翻譯差異不大就不改，原樣保留。','既有譯文保留')
    add('D03','狂怒既有正文精簡了骰數與加總表達','entries.Frenzy.description/b0001','EN明寫骰數等同狂暴傷害加值並將骰子相加；既有中文以擲等同於加值的D6及結果簡述。沒有不同數值、觸發、目標或傷害類型，原樣保留此正文；只補同一description內的英文Foundry註記。','既有正文區塊保留')
    add('D04','無我狂暴的狀態術語及進入狂暴時點','entries.Mindless Rage.description/b0001','原稿立即結束與EN進入狂暴時狀態結束對應；底稿沿用觸發時點，不追加立即修飾。兩種狀態均免疫，Reference目標及中文標籤完整。')
    add('D05','報償的距離單位及反應句式','entries.Retaliation.description/b0001','原稿5尺改為台灣單位5呎；以反應改為採取反應。保持同一造成傷害生物、一次近戰攻擊、武器或徒手打擊，未新增視線限制。')
    add('D06','威懾之姿的面相／氣勢及光環／發散','entries.Intimidating Presence.description/b0001','menacing presence不限面相，底稿順為氣勢；Emanation依terms／lang為發散，原稿光環區域不採。附贈動作、自選每名生物、30呎、DC、1分鐘及每名生物自身回合末重複豁免完整保留。')
    add('D07','威懾之姿的長休限制與狂暴恢復例外','entries.Intimidating Presence.description/b0002','原稿兩句合併為完整例外句：長休前不能再次使用，除非消耗一次狂暴使用次數，無需動作。不是消耗狂暴後還要等待長休，也不是恢復需要附贈動作。')
    for key in KEYS[1:]:
        add('N'+str(KEYS.index(key)),'未翻名稱：'+key,'entries.'+key+'.name','已核實現行Weblate、2024 repo及其他書名稱索引均無中文名称，按來源名稱轉繁及既定組成詞提出此名；待本批確認，沒有新增正式詞條。'.replace('名称','名稱'),'未翻名稱')
    for i,row in enumerate([r for r in mapping if r['source']=='supplement'],1):
        add('S'+str(i).zfill(2),'原稿缺少的Foundry／介面欄位',row['path'],'原稿無此獨立Foundry／介面欄位，依完整EN與獨立補翻底稿處理。行動、Active Effect、比例值及既有狀態詞沿用裁定；所有句子與欄位均完整列出。','自行補翻')
    for item in issues:
        # Multi-block current values are retained whole; do not truncate the
        # comparison just because one sentence is being reviewed.
        assert isinstance(item['en_full'],str) and isinstance(item['draft_full'],str)
    save('issues',issues)
    problem=['# 狂戰士道途第1批 v1：全部差異與補翻','','原稿、EN、既有譯文及提出底稿均完整列出。D01–D03原樣保留，不因小差異改寫；其餘依來源底稿或原稿缺漏補翻。','']
    for item in issues:
        problem += ['## '+item['id']+' '+item['title'],'','元件：'+item['component']+'；欄位：`'+item['path']+'`；分類：'+item['category'],'','**EN完整原句／段落／名稱：**',item['en_full'],'','**中文原稿完整文字：**',item['source_full'],'','**現行Weblate完整值：**',item['current_full'],'','**本批完整底稿／補翻：**',item['draft_full'],'','**原因與處理：** '+item['reason'],'','狀態：'+item['status'],'']
    problem_text='\n'.join(problem)
    for item in issues:assert item['source_full'] in problem_text
    write('issues.md',problem_text)
    full=['# 狂戰士道途第1批 v1：全面對照','','原稿15行全部保存；依來源範圍及完整區塊映射。既有中文原樣保留，未翻正文取獨立底稿，補翻另行標記。','## 保留的完整既有欄位','']
    for row in retained:
        full += ['### '+row['path'],'','EN完整值：','```html',row['en'],'```','既有中文（不改）：','```html',row['zh'],'```','判定：'+row['reason'],'']
    for row in mapping:
        full += ['## '+row['component']+' / '+row['path'],'','來源類別：'+row['source'],'','**EN完整文字：**',visible_text(row['en']) or '（無可見文字；技術命令保留。）','','**原稿完整中文／來源：**',row['source_original'],'','**獨立底稿：**',row['draft'] or '（無可見文字。）','','**成品可見文字：**',visible_text(row['zh']) or '（無可見文字。）','','**核對：** '+row['rule_review'],'','可見文字與底稿逐字相同；EN與成品技術標記：','```html',row['en'],'```','```html',row['zh'],'```','']
    full += ['## 全部句子／完整段落及限定詞','']
    for pair in pairs:
        full += ['### '+pair['path']+' · '+str(pair['unit']),'','**EN：** '+pair['en'],'','**中文：** '+pair['zh'],'','限定詞：'+(', '.join(pair['qualifiers']) or '沒有指定限定詞。'),'','核對：'+pair['review'],'']
    write('full-comparison.md','\n'.join(full))

    # Run the shared CLI on the real class payload; the journal fields use its
    # check_description function separately because pages aren't CLI-supported.
    validation=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'.claude/skills/translation-import/scripts/validate.py'),str(DATA/(PREFIX+'.classes.aligned.json')),'--book','dnd-players-handbook','--component','classes','--allow','Active,Effect','--out',str(DATA/(PREFIX+'.classes.upload.json'))],capture_output=True,text=True,encoding='utf-8')
    assert validation.returncode==0,validation.stdout+validation.stderr
    write('validation.txt',validation.stdout.rstrip())
    for component in ['classes','content']:
        assert load(component+'.upload')==load(component+'.aligned')
    info['payload_sha256']={c:hashlib.sha256((DATA/(PREFIX+'.'+c+'.upload.json')).read_bytes()).hexdigest() for c in ['classes','content']}
    info.update(rule_review_complete=True,terminology_review_complete=True,chinese_readthrough_complete=True,paired_sentences_or_paragraphs=len(pairs),issue_count=len(issues),description_supplement_blocks=7,nested_supplement_fields=5,approved=False,uploaded=False)
    old_frenzy=load('classes.live')['units']['entries.Frenzy.description']['target'][0]
    prefix_unchanged=old_frenzy.split('<section',1)[0]
    assert load('classes.upload')['entries']['Frenzy']['description'].startswith(prefix_unchanged)
    info['frenzy_existing_paragraph_byte_for_byte_unchanged']=True
    save('verification',info)
    def link(suffix,label):return '['+label+']('+str(DATA/(PREFIX+'.'+suffix)).replace('\\','/')+')'
    condition=next(r for r in mapping if r['path']=='entries.Retaliation.activities.Retaliate.condition')
    preview=[
      '# 狂戰士道途第1批 v1預覽','','日期：2026-10-08。使用者要求：已有中文與英文語意／規則差異不大就保留；其餘未翻內容依底稿處理，所有差異報告。',
      '', '[中文原稿來源]('+src['url']+')：玩家手冊2024／野蠻人／狂戰士道途，1–15行；本批只處理此子職業。',
      '', '候選5個classes條目及同名content日誌介紹。保留3個完整既有字串及狂怒正文的1個既有中文區塊；待上傳payload為classes 4條13字串、content 1個頁面2字串，合計15字串。**未上傳，待本批v1確認。**',
      '', '## 閱讀文件','',
      '- '+link('draft.txt','獨立正文底稿，含保留的現行中文'),
      '- '+link('supplement.draft.txt','獨立Foundry與介面補翻底稿'),
      '- '+link('preview.html','完整成品預覽'),
      '- '+link('issues.md','全部差異、名稱及補翻：完整中英文'),
      '- '+link('full-comparison.md','所有欄位、既有譯文與限定詞全面對照'),
      '- '+link('retained.json','原樣保留且不送入payload的3個字串'),
      '', '## 條目、來源及保留範圍','',
      '| EN key | 中文 | 原稿行號 | 處理 |','|---|---|---|---|',
      '| Path of the Berserker | 狂戰士道途 | 2–4 | name、description、advancement.title全部保留，不列classes payload |',
      '| Frenzy | 狂怒 | 5–6 | 保留既有中文正文；只補英文Foundry註記，另翻未翻name |',
      '| Mindless Rage | 無我狂暴 | 7–9 | 未翻正文依原稿順稿；Foundry及效果名補翻 |',
      '| Retaliation | 報償 | 10–12 | 未翻正文依原稿；行動名與condition另核對 |',
      '| Intimidating Presence | 威懾之姿 | 13–15 | 未翻正文依原稿；Foundry及介面補翻 |',
      '| Barbarian.pages.Path of the Berserker | 狂戰士道途 | 2–4 | 同EN介紹沿用已接受classes中文為底稿；補上原UUID標籤，Embed原樣 |',
      '', '日誌root的野蠻人名稱及其他pages不列payload。沒有用文字較流暢、格式偏好或術語工具偶然命中，去改已有且語意一致的中文。Frenzy的中文第一個p及Path of the Berserker完整description均有逐位元相同斷言。',
      '', '## 四項驗收','',
      '- 規則核對：全部條件、作用對象、目標、次數、距離、豁免、持續時間及例外逐句核對。狂怒已譯骰數／加總表達較精簡，D03完整揭露並保留；其他特性沒有新增規則條件。',
      '- 術語核對：本次完整讀取classes2209、content1161、terms136、spells-glossary640筆，分頁HTTP 200核對count。三方術語／lang每個命中逐項說明。未翻名稱沿用原稿轉繁，待本批確認；沒有新增正式術語。',
      '- 機械驗證：共用validate CLI通過classes 4條13字串；content頁面2欄位另用相同check_description檢查。所有payload EN對上現行Weblate source，HTML、UUID、Reference、Embed及參數保留，映射可見文字與底稿相同。',
      '- 中文通讀：獨立閱讀正文及補翻底稿，回查主體、否定及例外；原稿順稿後才映射。既有中文不為湊EN句子數拆改；介紹以完整段落對照。',
      '', '## 唯一activities.condition','', '**EN：** '+condition['en'],'','**中文：** '+condition['draft'],
      '', '## 全部差異與補翻','',
      f'{len(issues)}项完整紀錄：D01–D03為原稿／EN／既有中文差異但保留；D04–D07為未翻正文用詞或例外調整；N1–N4為查無現行中文名稱；S01–S12為7個Foundry區塊及5個介面欄位補翻。全部完整EN、原稿中文、現行值及底稿都在問題文件，沒有省略句子。',
      '', '## 三方術語／lang每項說明','', '| EN | terms | spells-glossary | lang | 採用中文／原因 |','|---|---|---|---|---|',
    ]
    for row in terms:preview.append('| '+' | '.join([row['en'],row['terms'],row['spells_glossary'],row['lang'],row['chosen']+'；'+row['context']])+' |')
    preview += ['', 'lang_compare含正文與補翻底稿，原始輸出保留。所有名稱、正文、嵌套欄位、連結標籤及技術參數命中都逐處回查；classes／three是Embed參數，不翻；原樣保留的文學表達不以UI字串強制改寫。',
      '', '## 確認版本','',
      'classes SHA-256：`'+info['payload_sha256']['classes']+'`。',
      'content SHA-256：`'+info['payload_sha256']['content']+'`。',
      '', '下一批依序為狂野之心道途、世界樹道途、狂熱者道途；尚未抓取。野蠻人主頁原先缺少EN欄位的表格／職業說明仍保留，不標為完成。',
      '', '17個舊批次執行腳本已移到`/scripts/translation-import/player-handbook/`，來源與產物目錄不再混放執行腳本。本批集中的collect／prepare／map／review由同一份`subclasses.py`執行；沒有修改共用技能工具。',
      '', '依[translation-import SKILL.md]('+str(ROOT/'.claude/skills/translation-import/SKILL.md').replace('\\','/')+')第5步「每批版本得到使用者明確確認後才上傳」，本批停在已完成驗收的v1預覽。',
    ]
    write('preview.md','\n'.join(preview).replace('项','項'))
    classes_final={key:cl[key] for key in KEYS}
    # Full preview shows retained descriptions and translated ones together;
    # never confuse this complete view with the changed-fields-only payload.
    def merge(left,right):
        out=json.loads(json.dumps(left))
        for key,value in right.items():
            if isinstance(value,dict):out[key]=merge(out.get(key,{}),value)
            else:out[key]=value
        return out
    live_units=load('classes.live')['units']
    for key in KEYS:
        translated={}
        for rel,_ in leaves(cl[key]):
            obj=translated; parts=rel.split('.')
            for part in parts[:-1]:obj=obj.setdefault(part,{})
            obj[parts[-1]]=live_units['entries.'+key+'.'+rel]['target'][0]
        classes_final[key]=merge(translated,load('classes.upload')['entries'].get(key,{}))
    def render(value):
        return LABEL.sub(lambda m:'<span class="annotation" title="'+html.escape(m[1],quote=True)+'">'+html.escape(m[2])+'</span>' if m[2] else '<span class="technical">〔原始Embed，位置與參數保留〕</span>',value)
    doc=['<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>狂戰士道途第1批v1</title><style>body{font-family:system-ui,"Microsoft JhengHei",sans-serif;background:#f8f7f3;color:#243239;line-height:1.8;max-width:950px;margin:36px auto;padding:0 24px}article{border-top:2px solid #b99a6c;margin:28px 0;padding-top:12px}.secret{background:#eee9e0;padding:4px 16px}.field{background:#e5ece8;padding:8px;margin:5px 0}.annotation{color:#286c7c;border-bottom:1px dotted}.technical{color:#777}.retained{color:#577a51}</style><h1>狂戰士道途第1批 v1</h1><p>保留3個完整既有字串及狂怒正文；待確認15字串，未上傳。</p>']
    for key,item in classes_final.items():
        doc += ['<article><h2>'+html.escape(draft[key][0])+'</h2><p>'+html.escape(key)+'</p>']
        if key=='Path of the Berserker':doc += ['<p class="retained">本條既有中文完全保留，不列classes payload。</p>']
        elif key=='Frenzy':doc += ['<p class="retained">首段中文逐字保留，只補Foundry註記。</p>']
        doc += [render(item['description'])]
        for field in ['activities','effects','advancement']:
            for path,value in leaves(item.get(field,{}),field):doc += ['<div class="field"><b>'+html.escape(path)+'</b><div>'+render(value)+'</div></div>']
        doc += ['</article>']
    jp=load('content.upload')['entries']['Barbarian']['pages']['Path of the Berserker']
    doc += ['<article><h2>日誌頁：'+html.escape(jp['name'])+'</h2>',render(jp['description']),'</article></html>']
    write('preview.html','\n'.join(doc))
    # The source itself has already been fetched and checked; record it without
    # fetching again when regenerating review artifacts.
    manifest_path=WEB/'manifest.json'
    manifest=read_json(manifest_path) if manifest_path.exists() else []
    manifest=[entry for entry in manifest if entry['url']!=src['url']]+[{'url':src['url'],'status':'ok','file':Path(src['text_path']).stem}]
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=1),encoding='utf-8')
    subclass_index=BASE/'subclasses/index.md'
    toc=(WEB/'webhelpcontents.html').read_text(encoding='utf-8')
    raw_links=re.findall(r'href="([^"#]+)',toc)
    from urllib.parse import urljoin
    subclass_names=[('Path of the Berserker','狂戰士道途','狂战士'),('Path of the Wild Heart','狂野之心道途','兽心'),('Path of the World Tree','世界樹道途','世界树'),('Path of the Zealot','狂熱者道途','狂热')]
    index_lines=['# 野蠻人子職業來源索引','','| 子職業 | 2024同站來源 | 狀態 |','|---|---|---|']
    for key,label,needle in subclass_names:
        urls=sorted({urljoin('https://5echm.kagangtuya.top/webhelpcontents.htm',html.unescape(u)) for u in raw_links if '玩家手册2024/角色职业/野蛮人/' in unquote(u) and needle in unquote(u)})
        assert len(urls)==1,(key,urls)
        state='第1批v1預覽，未上傳；classes保留3既有字串，只處理13變更字串＋content2字串' if key==KEYS[0] else '尚未抓取／處理'
        index_lines.append('| '+label+' | [原稿]('+urls[0]+') | '+state+' |')
    index_lines += ['', '狂戰士道途來源行號：2–4介紹、5–6狂怒、7–9無我狂暴、10–12報償、13–15威懾之姿。未匹配0條；Foundry及介面缺漏全列補翻。', '', '[本批完整預覽]('+str(DATA/(PREFIX+'.preview.md')).replace('\\','/')+')', '', '主頁先前缺EN欄位的等級表與職業說明仍保留在`../content.barbarian.3.remaining.txt`，不標完成。']
    subclass_index.write_text('\n'.join(index_lines)+'\n',encoding='utf-8')
    main_index=BASE/'classes.barbarian.index.md'
    if main_index.exists():
        text=main_index.read_text(encoding='utf-8').replace('沒有抓取四個子職業頁面。','狂戰士道途已抓取並完成v1預覽；其餘三個子職業尚未抓取。')
        marker='子職業後續：[來源及批次索引]('+str(subclass_index).replace('\\','/')+')。'
        if marker not in text:text+='\n'+marker+'\n'
        main_index.write_text(text,encoding='utf-8')
    print(json.dumps(info,ensure_ascii=False))

APPROVED_HASHES={
 'classes':'7513dafe81d4e3835092043c5a6f480ce7a6a6b65d6c6d0b2c15ab39d4b9b037',
 'content':'212e21be0939cdfc812d59c31704db917c57de28ad7ddac55c722fe2fb04f790',
}
PROJECT='dnd-players-handbook'

def approved_payloads():
    info=load('verification')
    assert info['version']=='v1' and info['payload_sha256']==APPROVED_HASHES
    assert all(info[k] for k in ['mechanical_pass','all_exact_draft_matches','live_en_match','rule_review_complete','terminology_review_complete','chinese_readthrough_complete'])
    for suffix,digest in info['draft_sha256'].items():
        assert hashlib.sha256((DATA/(PREFIX+'.'+suffix+'.txt')).read_bytes()).hexdigest()==digest
    expected={}
    for component in APPROVED_HASHES:
        path=DATA/(PREFIX+'.'+component+'.upload.json')
        assert hashlib.sha256(path.read_bytes()).hexdigest()==APPROVED_HASHES[component]
        expected[component]=dict(leaves(read_json(path)))
        assert len(expected[component])=={'classes':13,'content':2}[component]
        live=load(component+'.live')['units']
        for context,zh in expected[component].items():
            assert context in live
            en=live[context]['source'][0]
            allowed={'Foundry','Active','Effect'}
            assert not check_description(en,zh,allowed),(context,check_description(en,zh,allowed))
            if context.endswith('.description'):assert not compare_html(en,zh),(context,compare_html(en,zh))
    for row in load('mapping-audit'):assert visible_text(row['zh'])==row['draft']
    for row in load('retained'):assert row['path'] not in expected[row['component']]
    old=load('classes.live')['units']['entries.Frenzy.description']['target'][0]
    assert re.match(r'<p>.*?</p>',old,re.S).group()==re.match(r'<p>.*?</p>',expected['classes']['entries.Frenzy.description'],re.S).group()
    return expected

def preflight():
    expected=approved_payloads()
    records={}
    for component in expected:
        slug=PROJECT+'-'+component
        command=[sys.executable,'-X','utf8',str(ROOT/'.claude/skills/translation-import/scripts/weblate.py'),'status',PROJECT,slug]
        result=subprocess.run(command,capture_output=True,text=True,encoding='utf-8')
        write(component+'.status.txt',result.stdout+result.stderr)
        assert result.returncode==0
        status,translation=w.call('GET',f'/api/translations/{PROJECT}/{slug}/zh_Hant/')
        filename=f'compendium/zh-tw/{PROJECT}/{PROJECT}.{component}.json'
        assert status==200 and translation['filename']==filename
        status,settings=w.call('GET',f'/api/components/{PROJECT}/{slug}/')
        assert status==200 and settings.get('push')
        status,repo=w.call('GET',f'/api/components/{PROJECT}/{slug}/repository/')
        assert status==200 and not repo.get('merge_failure')
        rows,pagination=read_all(PROJECT,slug)
        all_units={row['context']:row for row in rows}
        units={path:all_units[path] for path in expected[component]}
        preview=load(component+'.live')['units']
        for path,unit in units.items():
            assert unit['source']==preview[path]['source'],'EN changed: '+path
            assert unit['target']==preview[path]['target'],'Current translation changed: '+path
        if component=='classes':
            for row in load('retained'):assert all_units[row['path']]['target']==[row['zh']]
        save(component+'.before',units)
        save(component+'.component-before',all_units)
        records[component]={'filename':filename,'push_url_set':True,'repository':{key:repo.get(key) for key in ['needs_commit','needs_push','needs_merge','merge_failure']},'pagination':pagination,'matched_strings':len(units),'prior_suggestions':[p for p,u in units.items() if u['has_suggestion']],'same_target':[p for p,u in units.items() if u['target']==[expected[component][p]]]}
    save('approval',{'version':'v1','date':'2026-10-08','authorization':'上傳','approved':True,'scope':'狂戰士道途第1批：classes 13字串、content 2字串；method=suggest。','payload_sha256':APPROVED_HASHES})
    save('preflight',records)
    print(json.dumps(records,ensure_ascii=False))

def upload_component(component):
    expected=approved_payloads()[component]
    assert load('approval')['approved'] and load('approval')['payload_sha256']==APPROVED_HASHES
    assert load('preflight')[component]['matched_strings']==len(expected)
    assert not (DATA/(PREFIX+'.'+component+'.upload-response.json')).exists(),'Already attempted; inspect before retry.'
    status,body=w.upload(PROJECT,PROJECT+'-'+component,str(DATA/(PREFIX+'.'+component+'.upload.json')),method='suggest')
    save(component+'.upload-response',{'http_status':status,'response':body,'sha256':APPROVED_HASHES[component],'method':'suggest'})
    print(json.dumps({'component':component,'http_status':status,'response':body},ensure_ascii=False))
    assert status in [200,201],'Investigate; do not blindly retry.'
    assert body['not_found']==0 and body['accepted']+body['skipped']==len(expected)

def audit_upload():
    expected=approved_payloads()
    audits={}
    for component in expected:
        rows,pagination=read_all(PROJECT,PROJECT+'-'+component)
        after={row['context']:row for row in rows}
        before=load(component+'.component-before')
        assert set(before)==set(after)
        for path,unit in after.items():
            assert unit['source']==before[path]['source'],'Source changed: '+path
            assert unit['target']==before[path]['target'],'Existing target changed: '+path
        accepted,skipped=[],[]
        for path,zh in expected[component].items():
            if after[path]['target']==[zh]:skipped.append({'context':path,'reason':'與現行譯文相同。'})
            else:
                assert not before[path]['has_suggestion'] and after[path]['has_suggestion'],'Suggestion requires inspection: '+path
                accepted.append({'context':path,'unit_id':after[path]['id'],'reason':'上傳前無建議、上傳後有建議；現行source及target不變。'})
        response=load(component+'.upload-response')['response']
        assert len(accepted)==response['accepted'] and len(skipped)==response['skipped'] and response['not_found']==0
        statistics={'component_total':len(after),'component_empty_or_source':sum(not any(u['target']) or u['target']==u['source'] for u in after.values()),'batch_strings':len(expected[component]),'batch_empty_or_source':sum(not any(after[p]['target']) or after[p]['target']==after[p]['source'] for p in expected[component]),'batch_has_suggestion':sum(after[p]['has_suggestion'] for p in expected[component])}
        save(component+'.after',{p:after[p] for p in expected[component]})
        save(component+'.statistics-latest',statistics)
        audits[component]={'accepted':accepted,'skipped':skipped,'not_found':[],'verified_strings':len(expected[component]),'component_verified_strings':len(after),'all_targets_unchanged':True,'pagination':pagination,'statistics':statistics,'response':response}
    save('upload-audit',{'components':audits,'complete':True,'accepted':sum(len(a['accepted']) for a in audits.values()),'skipped':sum(len(a['skipped']) for a in audits.values()),'not_found':0,'all_targets_unchanged':True,'component_verified_strings':sum(a['component_verified_strings'] for a in audits.values())})
    print(json.dumps(load('upload-audit'),ensure_ascii=False))

def archive_upload():
    approved_payloads()
    audit=load('upload-audit')
    assert audit['complete'] and audit['all_targets_unchanged'] and audit['accepted']+audit['skipped']==15
    destination=BASE/'_done/subclasses/berserker'
    assert DATA.resolve().is_relative_to(BASE.resolve()) and destination.resolve().is_relative_to((BASE/'_done').resolve())
    files=sorted(DATA.glob(PREFIX+'.*'))
    assert files and all(p.is_file() and p.resolve().parent==DATA.resolve() and not (destination/p.name).exists() for p in files)
    destination.mkdir(parents=True,exist_ok=True)
    info=load('verification')
    info.update(approved=True,uploaded=True,method='suggest',upload_date='2026-10-08',accepted=audit['accepted'],skipped=audit['skipped'],not_found=audit['not_found'],archive_path=str(destination))
    save('verification',info)
    mapping={r['path']:r for r in load('mapping-audit')}
    # Correct only report rendering of unlabelled Reference terms. Approved
    # drafts and upload payloads remain byte for byte unchanged.
    replacements={}
    for row in mapping.values():
        old,new=visible_text(row['en']),english_text(row['en'])
        if old!=new:
            replacements[old]=new
            old_sent=[s.strip() for s in re.split(r'(?<=[.!?])\s+(?=[A-Z])',old) if s.strip()]
            new_sent=[s.strip() for s in re.split(r'(?<=[.!?])\s+(?=[A-Z])',new) if s.strip()]
            assert len(old_sent)==len(new_sent)
            replacements.update(zip(old_sent,new_sent))
    pairs=load('sentence-audit')
    for pair in pairs:pair['en']=replacements.get(pair['en'],pair['en'])
    save('sentence-audit',pairs)
    issues=load('issues')
    for issue in issues:
        issue['en_full']=english_text(mapping[issue['path']]['en'])
        issue['en_raw']=mapping[issue['path']]['en']
        if not issue['retained']:issue['status']='使用者確認v1，已以建議上傳。'
    save('issues',issues)
    problem=['# 狂戰士道途第1批 v1：全部差異與補翻','','本批已由使用者確認並以建議上傳。EN連結顯示詞完整展開；原始HTML／技術標記亦保留。D01–D03的既有中文原樣保留。','']
    for item in issues:
        problem += ['## '+item['id']+' '+item['title'],'','元件：'+item['component']+'；欄位：`'+item['path']+'`；分類：'+item['category'],'','**EN完整原句／段落／名稱：**',item['en_full'],'','**EN原始值：**','```html',item['en_raw'],'```','','**中文原稿完整文字：**',item['source_full'],'','**上傳前Weblate完整值：**',item['current_full'],'','**本批完整底稿／補翻：**',item['draft_full'],'','**原因與處理：** '+item['reason'],'','狀態：'+item['status'],'']
    write('issues.md','\n'.join(problem))
    full_path=DATA/(PREFIX+'.full-comparison.md')
    full=full_path.read_text(encoding='utf-8')
    for old,new in sorted(replacements.items(),key=lambda item:-len(item[0])):
        if old!=new:full=full.replace(old,new)
    full_path.write_text(full,encoding='utf-8')
    preview=DATA/(PREFIX+'.preview.md')
    text=preview.read_text(encoding='utf-8').replace('**未上傳，待本批v1確認。**','**使用者已確認v1；15個字串均已以建議上傳。**')
    text=text.replace('本批停在已完成驗收的v1預覽。','本批v1已由使用者以「上傳」明確確認，並完成建議上傳及稽核。')
    preview.write_text(text,encoding='utf-8')
    preview_html=DATA/(PREFIX+'.preview.html')
    preview_html.write_text(preview_html.read_text(encoding='utf-8').replace('待確認15字串，未上傳。','15字串已確認並以建議上傳。'),encoding='utf-8')
    def link(suffix,label):return '['+label+']('+str(destination/(PREFIX+'.'+suffix)).replace('\\','/')+')'
    report=['# 狂戰士道途第1批 v1：上傳報告（2026-10-08）','','使用者以「上傳」確認本批v1。以method=suggest送入Weblate審閱佇列：新增15個建議、跳過0、未匹配0。正式譯文沒有改動。','','| 元件 | payload字串 | HTTP | accepted | skipped | not_found |','|---|---:|---:|---:|---:|---:|']
    preflight_record=load('preflight')
    for component in APPROVED_HASHES:
        response=load(component+'.upload-response')
        data=response['response']
        report += [f"| {component} | {audit['components'][component]['verified_strings']} | {response['http_status']} | {data['accepted']} | {data['skipped']} | {data['not_found']} |"]
    report += ['','兩個元件全部3370個字串的source及target逐一比較，均保持不變。15個待上傳欄位在上傳前無建議、上傳後有建議，且API新增數與逐欄核對一致。API total／count為整個元件總數，不是本批字串數。','','狂戰士道途既有name、完整description、子職業特性title共3個欄位完全保留，不列payload。狂怒既有中文第一段也逐字保留，只補同欄位的英文Foundry註記。日誌root名稱與其他pages不列payload。','','## 版本與前置核對','']
    for component,digest in APPROVED_HASHES.items():
        record=preflight_record[component]
        report += [f'- {component} SHA-256：`{digest}`；'+link(component+'.upload.json','已確認payload')+'。',f'- {component} filename：`{record["filename"]}`；push URL已設；repository狀態：`'+json.dumps(record['repository'],ensure_ascii=False)+'`。']
    report += ['','content有既存needs_commit／needs_merge，merge_failure為空；本批suggest只寫入建議佇列，未執行合併、提交或推送。','','## 來源、映射與全部差異','','狂戰士道途來源15行全部保存。介紹2–4、狂怒5–6、無我狂暴7–9、報償10–12、威懾之姿13–15；對應4個classes條目13字串＋1個日誌頁2字串。3個完整既有欄位保留。28個映射位置與獨立底稿可見文字全部一致。','','原稿缺少的7個Foundry正文區塊及5個介面欄位均以獨立補翻底稿處理，並在差異文件逐項披露。23項差異／名稱／補翻紀錄及35組完整中英文句子或段落全部保留。沒有待裁定或未匹配的本批字串。','','- '+link('issues.md','全部差異與補翻：完整中英文、原始EN標記及原稿')+'。','- '+link('full-comparison.md','全面對照及每句限定詞核對')+'。','- '+link('draft.txt','獨立正文底稿')+'；'+link('supplement.draft.txt','Foundry及介面補翻底稿')+'。','- '+link('preview.html','完整成品預覽')+'；'+link('upload-audit.json','逐欄上傳稽核')+'。','','## 四項驗收','','規則：觸發、否定、目標、數量、距离、持續、豁免及例外全面核對；D01–D03的既有小差異完整報告並保留。術語：完整分頁讀取terms136、spells-glossary640及兩元件，與lang三方逐項核對；每個工具命中均有解釋，沒有新增正式詞條。機械：classes共用validate及content逐欄check_description通過，HTML、UUID、Reference、Embed與參數保留；已確認payload與底稿雜湊未變。中文：獨立通讀底稿與補翻，映射後逐句回查。','','唯一condition：','', '**EN：** When you take damage from a creature that is within 5 feet of you','', '**中文：** '+dict(leaves(load('classes.upload')))['entries.Retaliation.activities.Retaliate.condition'],'','## 未翻數與後續','']
    condition_path='entries.Retaliation.activities.Retaliate.condition'
    report[report.index('**EN：** When you take damage from a creature that is within 5 feet of you')]='**EN：** '+load('classes.live')['units'][condition_path]['source'][0]
    for component,a in audit['components'].items():
        stats=a['statistics']
        report += [f'- {component}現行空值或target等於source：{stats["component_empty_or_source"]}／{stats["component_total"]}；本批仍為此狀態的欄位：{stats["batch_empty_or_source"]}，本批有建議：{stats["batch_has_suggestion"]}。']
    report += ['','建議尚待接受，未翻統計不將建議當成完成譯文。狂怒description含既有中文，所以不計空值／英文相同，但其中原英文Foundry註記的補翻已送入建議。','','下一批尚未開始：狂野之心道途、世界樹道途、狂熱者道途。主頁先前缺少EN欄位的等級表與職業說明仍留在原remaining檔，不標完成。同站共用原始HTML、文字及來源索引保持原位；本批成功產物歸檔。執行腳本統一放在/scripts/translation-import/player-handbook/。']
    write('2026-10-08.report.md','\n'.join(report).replace('距离','距離'))
    approved_payloads()
    # Rewrite moved-artifact links only, including JSON path metadata. The
    # immutable drafts and payloads do not contain links to this directory.
    files=sorted(DATA.glob(PREFIX+'.*'))
    immutable={PREFIX+'.draft.txt',PREFIX+'.supplement.draft.txt',PREFIX+'.classes.upload.json',PREFIX+'.content.upload.json'}
    for file in files:
        if file.name in immutable:continue
        value=file.read_text(encoding='utf-8')
        for before_path,after_path in [(str(DATA),str(destination)),(str(DATA).replace('\\','/'),str(destination).replace('\\','/')),(str(DATA).replace('\\','\\\\'),str(destination).replace('\\','\\\\'))]:value=value.replace(before_path,after_path)
        file.write_text(value,encoding='utf-8')
    approved_payloads()
    for file in files:
        assert file.resolve().parent==DATA.resolve() and not (destination/file.name).exists()
        file.rename(destination/file.name)
    index=BASE/'subclasses/index.md'
    text=index.read_text(encoding='utf-8').replace('第1批v1預覽，未上傳；classes保留3既有字串，只處理13變更字串＋content2字串','第1批v1已上傳15個建議（classes13＋content2）；既有譯文完全保留')
    text=text.replace(str(DATA).replace('\\','/'),str(destination).replace('\\','/'))
    index.write_text(text,encoding='utf-8')
    index=BASE/'classes.barbarian.index.md'
    if index.exists():index.write_text(index.read_text(encoding='utf-8').replace('狂戰士道途已抓取並完成v1預覽；','狂戰士道途v1已上傳15個建議；'),encoding='utf-8')
    for component,digest in APPROVED_HASHES.items():assert hashlib.sha256((destination/(PREFIX+'.'+component+'.upload.json')).read_bytes()).hexdigest()==digest
    assert not list(DATA.glob(PREFIX+'.*'))
    print(str(destination/(PREFIX+'.2026-10-08.report.md')))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['collect','prepare','map','review','preflight','upload-classes','upload-content','audit','archive'])
    args=parser.parse_args()
    {'collect':collect,'prepare':prepare,'map':map_draft,'review':review,'preflight':preflight,'upload-classes':lambda:upload_component('classes'),'upload-content':lambda:upload_component('content'),'audit':audit_upload,'archive':archive_upload}[args.mode]()
