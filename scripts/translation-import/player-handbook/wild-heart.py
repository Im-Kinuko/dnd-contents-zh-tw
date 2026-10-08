"""Prepare the next Wild Heart subclass batch from its Chinese source."""
import argparse, hashlib, html, json, re, subprocess, sys
from pathlib import Path
from urllib.parse import unquote, urljoin
import opencc
from subclasses import read_all, english_text, leaves

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'_incoming/player-handbook'
DATA=BASE/'subclasses/wild-heart'
WEB=BASE/'_web/barbarian-subclasses'
PREFIX='subclasses.wild-heart.2'
PROJECT='dnd-players-handbook'
KEYS=['Path of the Wild Heart','Animal Speaker','Rage of the Wilds','Aspect of the Wilds','Nature Speaker','Power of the Wilds']
sys.path.insert(0,str(ROOT/'.claude/skills/translation-import/scripts'))
from html_blocks import Plan, visible_text, compare_html, LABEL
from validate import check_description, count_strings
from skeleton import build_entries
from build_index import entry_names, aliases
from lang_compare import flat
from skeleton import draft_sections, norm
import weblate as w
import shutil

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def load(suffix):return read(DATA/(PREFIX+'.'+suffix+'.json'))
def save(suffix,value):
    DATA.mkdir(parents=True,exist_ok=True)
    (DATA/(PREFIX+'.'+suffix+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=1),encoding='utf-8')
def write(suffix,value):
    DATA.mkdir(parents=True,exist_ok=True)
    (DATA/(PREFIX+'.'+suffix)).write_text(value.rstrip()+'\n',encoding='utf-8')

def collect():
    sys.path.insert(0,str(ROOT/'.claude/skills/web-source-extract/scripts'))
    import fetch_site as fetch
    toc=(WEB/'webhelpcontents.html').read_text(encoding='utf-8')
    candidates=sorted(set(urljoin('https://5echm.kagangtuya.top/webhelpcontents.htm',html.unescape(u)) for u in re.findall(r'href="([^"#]+)',toc) if '玩家手册2024/角色职业/野蛮人/' in unquote(u) and '兽心道途' in unquote(u)))
    assert len(candidates)==1,candidates
    url=candidates[0]
    slug=fetch.slug(url)
    text_path=WEB/(slug+'.txt')
    raw_path=WEB/'_raw'/(slug+'.html')
    if not text_path.exists():
        raw=fetch.get(url)
        raw_path.parent.mkdir(parents=True,exist_ok=True)
        raw_path.write_text(raw,encoding='utf-8')
        text_path.write_text(fetch.to_text(raw),encoding='utf-8')
    source=text_path.read_text(encoding='utf-8')
    write('source.txt',source)
    write('source.s2twp.txt',opencc.OpenCC('s2twp').convert(source))
    save('source',{'url':url,'decoded_url':unquote(url),'text_path':str(text_path),'html_path':str(raw_path),'status':'ok'})
    manifest_path=WEB/'manifest.json'
    manifest=read(manifest_path)
    manifest=[r for r in manifest if r['url']!=url]+[{'url':url,'status':'ok','file':slug}]
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=1),encoding='utf-8')
    print('SOURCE',unquote(url))
    print('\n'.join(f'{i}: {line}' for i,line in enumerate(source.splitlines(),1)))
    for component in ['classes','content','spells']:
        comp=PROJECT+'-'+component
        status,translation=__import__('weblate').call('GET',f'/api/translations/{PROJECT}/{comp}/zh_Hant/')
        assert status==200 and translation['filename']==f'compendium/zh-tw/{PROJECT}/{PROJECT}.{component}.json'
        rows,audit=read_all(PROJECT,comp)
        units={row['context']:row for row in rows}
        save(component+'.live',{'filename':translation['filename'],'audit':audit,'units':units})
        print(component,'complete',len(rows))
        if component=='classes':
            scope={p:r for p,r in units.items() if any(p.startswith('entries.'+k+'.') for k in KEYS)}
        elif component=='content':scope={p:r for p,r in units.items() if p.startswith('entries.Barbarian.pages.Path of the Wild Heart.')}
        else:scope={p:r for p,r in units.items() if p in ['entries.Beast Sense.name','entries.Speak with Animals.name','entries.Commune with Nature.name']}
        print(json.dumps({p:{'en':r['source'][0],'zh':r['target'][0]} for p,r in scope.items()},ensure_ascii=False,indent=1))
    for component in ['terms','spells-glossary']:
        rows,audit=read_all('dnd-5e-2024-zh-tw',component)
        save(component+'.live',{'audit':audit,'units':rows})
        print(component,'complete',len(rows))
    terms={r['source'][0]:r['target'][0] for r in load('terms.live')['units'] if any(r['target']) and r['target']!=r['source']}
    glossary={r['source'][0]:r['target'][0] for r in load('spells-glossary.live')['units'] if any(r['target']) and r['target']!=r['source']}
    save('term_index',{'terms':terms,'spells_glossary':glossary,'entry_names':{k:dict(v) for k,v in entry_names(str(ROOT/'compendium/zh-tw'),PROJECT).items()},'aliases':aliases(str(ROOT/'.claude/skills/translation-import/glossary.tsv'))})

def prepare():
    live=load('classes.live')['units']
    intro=Plan(live['entries.Path of the Wild Heart.description']['target'][0]).blocks
    aspect=Plan(live['entries.Aspect of the Wilds.description']['target'][0]).blocks[0]
    main={
      'Path of the Wild Heart':['狂野之心道途','與動物世界一同漫步','跟隨狂野之心道途的野蠻人將自身視作動物們的家人。他們學習與動物交流的魔法手段，他們的狂暴賦予他們超自然的力量來增強與動物們的聯繫。'],
      'Animal Speaker':['動物語者','你可以施放法術野獸知覺與動物交談術，但僅限以儀式施放。感知是你施放這些法術的施法屬性。'],
      'Rage of the Wilds':['野性狂暴','你的狂暴解放來自動物的原初之力。每當你啟用狂暴時，你從下列選項中選擇並獲得一項。','【熊】狂暴啟用期間，你具有除力場、心靈、黯蝕、光耀以外所有傷害類型的抗力。','【鷹】當你啟用狂暴時，你可以以該附贈動作的一部分，同時採取撤離與疾走動作。狂暴啟用期間，你也可以採取一個附贈動作，同時採取這兩個動作。','【狼】狂暴啟用期間，你的盟友對位於你5呎內、與你為敵的任何生物進行的攻擊檢定具有優勢。'],
      'Aspect of the Wilds':['荒野之形',visible_text(aspect.html),'【梟】你具有60呎黑暗視覺。若你已經具有黑暗視覺，則你的黑暗視覺範圍增加60呎。','【豹】你具有等同於你速度的攀爬速度。','【鮭】你具有等同於你速度的游泳速度。'],
      'Nature Speaker':['自然語者','你可以施放法術問道自然，但僅限以儀式施放。感知是你施放該法術的施法屬性。'],
      'Power of the Wilds':['狂野威能','每當你啟用狂暴時，你從下列選項中選擇並獲得一項。','【獵鷹】狂暴啟用期間，只要你沒有著裝任何護甲，你就具有等同於你速度的飛行速度。','【雄獅】狂暴啟用期間，任何位於你5呎內的敵人，對你或另一名啟用了此選項的野蠻人以外的目標進行攻擊檢定時具有劣勢。','【角羊】狂暴啟用期間，當你以近戰攻擊命中一名體型不超過大型的生物時，你可以使其陷入伏地狀態。'],
      'Path of the Wild Heart (journal)':['狂野之心道途','與動物世界一同漫步','跟隨狂野之心道途的野蠻人將自身視作動物們的家人。他們學習與動物交流的魔法手段，他們的狂暴賦予他們超自然的力量來增強與動物們的聯繫。'],
    }
    added={
      'Animal Speaker':['【Foundry註記】','當你提升至3級時，這些法術會加入你的法術分頁，設為儀式，並使用你的感知調整值。'],
      'Rage of the Wilds':['【Foundry註記】','熊行動包含一項Active Effect，可自動加入這些抗力。','鷹行動使用一個附贈動作來採取撤離與疾走動作。','狼行動包含一個5呎目標模板，用於辨識受影響的生物。'],
      'Aspect of the Wilds':['【Foundry註記】','此特性包含一個行動，其中的Active Effect會自動套用梟選項帶來的黑暗視覺變化。速度變化不會自動套用。'],
      'Nature Speaker':['【Foundry註記】','你獲得的該法術已設為僅限以儀式施放，並預先設定使用感知作為你的施法調整值。'],
      'Power of the Wilds':['【Foundry註記】','角羊行動包含一項Active Effect，會加上伏地狀態。','獵鷹與雄獅選項沒有自動化處理。'],
    }
    nested={
      'Path of the Wild Heart':{'advancement':{'Subclass Features':{'title':'子職業特性'},'Animal Speaker':{'title':'動物語者','hint':'動物語者特性賦予你野獸知覺與動物交談術這兩個法術，但僅限以儀式施放。感知是你施放這些法術的施法屬性。'},'Nature Speaker':{'title':'自然語者'}}},
      'Rage of the Wilds':{'activities':{'Bear':{'name':'熊'},'Eagle':{'name':'鷹'},'Wolf':{'name':'狼'}},'effects':{'Rage of the Bear':{'name':'熊之狂暴'},'Rage of the Wolf':{'name':'狼之狂暴','description':'<p>'+main['Rage of the Wilds'][4].removeprefix('【狼】狂暴啟用期間，')+'</p>'}}},
      'Aspect of the Wilds':{'activities':{'Owl':{'name':'梟'},'Panther':{'name':'豹'},'Salmon':{'name':'鮭'}},'effects':{'Aspect of the Owl':{'name':'梟之形','description':'<p>'+main['Aspect of the Wilds'][2].removeprefix('【梟】')+'</p>'}}},
      'Power of the Wilds':{'activities':{'Falcon':{'name':'獵鷹','chatFlavor':'只要你沒有著裝任何護甲，你就獲得等同於你速度的飛行速度。'},'Lion':{'name':'雄獅'},'Ram':{'name':'角羊','condition':'當你以近戰攻擊命中一名大型或更小型的生物時'}},'effects':{'Power of the Wilds: Ram':{'name':'狂野威能：角羊'}}},
    }
    write('draft.txt','\n\n'.join('### '+key+'\n'+'\n'.join(lines) for key,lines in main.items()))
    nested_lines=[path+'\n'+visible_text(value) for path,value in leaves({'entries':nested})]
    write('supplement.draft.txt','\n\n'.join('### '+key+'\n'+'\n'.join(lines) for key,lines in added.items())+'\n\n### Nested Fields\n'+'\n\n'.join(nested_lines))
    save('nested-draft',nested)
    save('draft-fingerprints',{suffix:hashlib.sha256((DATA/(PREFIX+'.'+suffix+'.txt')).read_bytes()).hexdigest() for suffix in ['draft','supplement.draft']})
    save('condition-ruling',{'en':'When you a Large or smaller creature with a melee attack','user_reply':'當你以近戰攻擊命中，才對','proposed_zh':nested['Power of the Wilds']['activities']['Ram']['condition'],'scope':'依完整正文補足上游condition漏字，採使用者指定句式；本批版本仍待確認。'})
    print('Independent Chinese drafts prepared from source and adequate current translations.')

def enrich(en,zh):
    for token,label in [(m[1],m[2]) for m in LABEL.finditer(en)]:
        if token.startswith('@UUID['):
            chosen={'Beast Sense':'野獸知覺','Speak with Animals':'動物交談術','Commune with Nature':'問道自然','Path of the Wild Heart':'狂野之心道途'}[label]
            assert chosen in zh,(token,zh)
            zh=zh.replace(chosen,token+'{'+chosen+'}',1)
        elif 'Reference[' in token:
            assert token.endswith('[Prone]')
            zh=zh.replace('伏地',token+'{伏地}',1)
        elif token.startswith('@Embed['):assert zh==''
    strong=re.findall(r'<strong>(.*?)</strong>',en,re.S)
    if strong:
        names={'Bear':'熊','Eagle':'鷹','Wolf':'狼','Owl':'梟','Panther':'豹','Salmon':'鮭','Falcon':'獵鷹','Lion':'雄獅','Ram':'角羊','Foundry Note':'Foundry註記'}
        for word in strong:
            chosen=names[word.strip().rstrip('.')]
            label='【'+chosen+'】' if word.strip().endswith('.') or word=='Foundry Note' else chosen
            assert label in zh,(word,zh)
            zh=zh.replace(label,'<strong>'+label+'</strong>',1)
    return zh

def map_draft():
    drafts=draft_sections(str(DATA/(PREFIX+'.draft.txt')))
    # draft_sections normalises for the common builder; keep physical lines for
    # mapping to full paragraphs instead of inventing EN-sized phrase slots.
    def sections(suffix):
        text=(DATA/(PREFIX+'.'+suffix+'.txt')).read_text(encoding='utf-8')
        return {match[1]:[s for s in match[2].strip().splitlines() if s.strip()] for match in re.finditer(r'^### ([^\n]+)\n(.*?)(?=^### |\Z)',text,re.M|re.S)}
    main,added=sections('draft'),sections('supplement.draft')
    local=read(ROOT/f'compendium/en/{PROJECT}/{PROJECT}.classes.json')['entries']
    journal=read(ROOT/f'compendium/en/{PROJECT}/{PROJECT}.content.json')['entries']['Barbarian']['pages']['Path of the Wild Heart']
    live=load('classes.live')['units']
    source=(DATA/(PREFIX+'.source.txt')).read_text(encoding='utf-8').splitlines()
    ranges={'Path of the Wild Heart':[(3,3),(4,4)],'Animal Speaker':[(7,8)],'Rage of the Wilds':[(11,11),(12,12),(13,13),(14,14)],'Aspect of the Wilds':[(17,17),(18,18),(19,19),(20,20)],'Nature Speaker':[(22,22)],'Power of the Wilds':[(24,24),(25,25),(26,26),(27,27)]}
    name_ranges={'Path of the Wild Heart':(2,2),'Animal Speaker':(5,6),'Rage of the Wilds':(9,10),'Aspect of the Wilds':(15,16),'Nature Speaker':(21,21),'Power of the Wilds':(23,23)}
    nested=load('nested-draft')
    sheet={'schema_version':2,'book':PROJECT,'component':'classes','entries':{}}
    mapping=[]
    for key in KEYS:
        plan=Plan(local[key]['description'])
        sentences=main[key][1:]+added.get(key,[])
        assert len(sentences)==len(plan.blocks)
        record={'name_en':key,'name':main[key][0],'blocks':[]}
        for i,(block,line) in enumerate(zip(plan.blocks,sentences)):
            preserved=key=='Aspect of the Wilds' and i==0
            is_supplement=i>=len(main[key])-1
            zh=Plan(live['entries.'+key+'.description']['target'][0]).blocks[i].html if preserved else enrich(block.html,line)
            assert visible_text(zh)==line,(key,block.id,'Draft changed')
            assert not compare_html(block.html,zh),(key,block.id,compare_html(block.html,zh))
            bounds=None if is_supplement else ranges[key][i]
            record['blocks'].append({'id':block.id,'en':block.html,'zh':zh,'source':'supplement' if is_supplement else 'draft','basis':'原稿缺Foundry註記；取獨立補翻底稿，活動名、法術及規則詞先核對。' if is_supplement else ''})
            mapping.append({'component':'classes','path':'entries.'+key+'.description/'+block.id,'en':block.html,'zh':zh,'draft':line,'source':'existing' if preserved else ('supplement' if is_supplement else 'draft'),'source_lines':bounds,'source_original':'\n'.join(source[bounds[0]-1:bounds[1]]) if bounds else '原稿無此Foundry註記。','retained':preserved,'exact_visible_match':True})
        record.update(nested.get(key,{}))
        sheet['entries'][key]=record
    save('classes.sheet',sheet)
    built=build_entries(sheet,{k:local[k] for k in KEYS},drafts)['entries']
    retained=[]
    payload={}
    for key,item in built.items():
        out={}
        originals=dict(leaves(local[key]))
        for rel,zh in leaves(item):
            path='entries.'+key+'.'+rel
            assert live[path]['source']==[originals[rel]],'Live EN mismatch: '+path
            old=live[path]['target'][0]
            if old==zh:retained.append({'component':'classes','path':path,'en':originals[rel],'zh':old,'reason':'既有中文語意相符，原樣保留且排除payload。'})
            else:
                target=out;parts=rel.split('.')
                for part in parts[:-1]:target=target.setdefault(part,{})
                target[parts[-1]]=zh
            if rel=='description':continue
            bounds=name_ranges[key] if rel=='name' else None
            # Effect descriptions duplicate available source rules and derive
            # directly from the independent draft, without their option heading.
            body_copy=rel=='effects.Rage of the Wolf.description' or rel=='effects.Aspect of the Owl.description'
            if body_copy:bounds=(14,14) if key=='Rage of the Wilds' else (18,18)
            mapping.append({'component':'classes','path':path,'en':originals[rel],'zh':zh,'draft':visible_text(zh),'source':'existing' if old==zh else ('draft' if rel=='name' or body_copy else 'supplement'),'source_lines':bounds,'source_original':'\n'.join(source[bounds[0]-1:bounds[1]]) if bounds else '原稿無此獨立介面欄位；以特性正文及EN欄位核對。','retained':old==zh,'exact_visible_match':True})
        if out:payload[key]=out
    content_plan=Plan(journal['description'])
    journal_lines=iter(main['Path of the Wild Heart (journal)'][1:])
    replacements={}
    for block in content_plan.blocks:
        line=next(journal_lines) if english_text(block.html) else ''
        zh=enrich(block.html,line) if line else block.html
        assert visible_text(zh)==line and not compare_html(block.html,zh)
        replacements[block.id]=zh
        bounds=(3,3) if block.id=='b0002' else ((4,4) if line else None)
        mapping.append({'component':'content','path':'entries.Barbarian.pages.Path of the Wild Heart.description/'+block.id,'en':block.html,'zh':zh,'draft':line,'source':'draft' if line else 'protected','source_lines':bounds,'source_original':'\n'.join(source[bounds[0]-1:bounds[1]]) if bounds else 'Embed插圖指令無可見文字，原樣保留。','retained':False,'exact_visible_match':True})
    assert next(journal_lines,None) is None
    journal_value={'name':main['Path of the Wild Heart (journal)'][0],'description':content_plan.build(replacements)}
    mapping.append({'component':'content','path':'entries.Barbarian.pages.Path of the Wild Heart.name','en':journal['name'],'zh':journal_value['name'],'draft':journal_value['name'],'source':'existing-corresponding-class','source_lines':[2,2],'source_original':source[1],'retained':False,'exact_visible_match':True})
    content={'entries':{'Barbarian':{'pages':{'Path of the Wild Heart':journal_value}}}}
    classes={'entries':payload}
    for component,value in [('classes',classes),('content',content)]:
        for path,zh in leaves(value):
            en=load(component+'.live')['units'][path]['source'][0]
            assert not check_description(en,zh,{'Foundry','Active','Effect'}),(path,check_description(en,zh,{'Foundry','Active','Effect'}))
        save(component+'.aligned',value)
    for suffix,digest in load('draft-fingerprints').items():assert hashlib.sha256((DATA/(PREFIX+'.'+suffix+'.txt')).read_bytes()).hexdigest()==digest
    save('full-classes',{'entries':built})
    save('retained',retained)
    save('mapping-audit',mapping)
    write('remaining.txt','### Source translator note (no corresponding EN field)\n原稿第28行：'+source[27]+'\n此為原稿譯註，EN classes/content沒有對應獨立欄位；原样保留來源，不將盾牌解說加入規則正文或捏造key。'.replace('原样','原樣'))
    # The common CLI requires a description even for entries whose payload has
    # only changed advancement fields. Validate complete final entries first,
    # then retain only changed leaves from that successful output.
    result=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'.claude/skills/translation-import/scripts/validate.py'),str(DATA/(PREFIX+'.full-classes.json')),'--book',PROJECT,'--component','classes','--allow','Active,Effect','--out',str(DATA/(PREFIX+'.classes.validated.json'))],capture_output=True,text=True,encoding='utf-8')
    write('validation.txt',result.stdout+result.stderr)
    assert result.returncode==0,result.stdout+result.stderr
    validated=load('classes.validated')
    assert validated=={'entries':built}
    for path,zh in leaves(classes):assert dict(leaves(validated))[path]==zh
    save('classes.upload',classes)
    save('content.upload',content)
    save('verification',{'version':'v2','classes_entries':len(payload),'classes_strings':count_strings(classes),'content_entries':1,'content_strings':count_strings(content),'retained_strings':len(retained),'retained_body_blocks':sum(r['retained'] for r in mapping if '.description/' in r['path']),'mapped_positions':len(mapping),'all_exact_draft_matches':True,'mechanical_pass':True,'live_en_match':True,'draft_sha256':load('draft-fingerprints'),'payload_sha256':{c:hashlib.sha256((DATA/(PREFIX+'.'+c+'.upload.json')).read_bytes()).hexdigest() for c in ['classes','content']},'approved':False,'uploaded':False})
    print(json.dumps(load('verification'),ensure_ascii=False))

def compare_terms():
    live=load('classes.live')['units']
    local=read(ROOT/f'compendium/en/{PROJECT}/{PROJECT}.classes.json')['entries']
    journal=read(ROOT/f'compendium/en/{PROJECT}/{PROJECT}.content.json')['entries']['Barbarian']['pages']['Path of the Wild Heart']
    sheet={'schema_version':2,'entries':{}}
    for key,item in [(k,local[k]) for k in KEYS]+[('Path of the Wild Heart (journal)',journal)]:
        row={'name_en':item['name'],'blocks':[{'id':b.id,'en':b.html} for b in Plan(item['description']).blocks]+[{'id':'name-audit','en':item['name']}]}
        for field in ['activities','effects','advancement']:
            if field in item:row[field]=item[field]
        sheet['entries'][key]=row
    save('audit.sheet',sheet)
    combined=(DATA/(PREFIX+'.draft.txt')).read_text(encoding='utf-8')+'\n'+(DATA/(PREFIX+'.supplement.draft.txt')).read_text(encoding='utf-8')
    write('review.draft.txt',combined)
    result=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'.claude/skills/translation-import/scripts/lang_compare.py'),str(DATA/(PREFIX+'.audit.sheet.json')),'--draft',str(DATA/(PREFIX+'.review.draft.txt'))],capture_output=True,text=True,encoding='utf-8')
    assert result.returncode==0,result.stderr
    write('lang-compare.md',result.stdout)
    print(result.stdout)

def review():
    info=load('verification')
    mapping=load('mapping-audit')
    retained=load('retained')
    index=load('term_index')
    lang_en=flat(read(ROOT/'lang/en.json'))
    lang_zh=flat(read(ROOT/'lang/zh-tw.json'))
    choices={
      'ability':('屬性','只出現於施法屬性，採lang完整詞組。'),
      'action':('動作','規則動作採lang；Eagle撤離與疾走同時可採取。'),
      'actions':('動作','兩個動作以兩個表達，不增添另一份資源消耗。'),
      'activity':('行動','使用者裁定；Foundry行動不同於遊戲動作。'),
      'activity uses':('行動使用一個附贈動作','原句The Eagle activity uses a Bonus Action中uses為動詞；不是UI名詞行動使用次數。'),
      'advantage':('優勢','盟友攻擊檢定具有優勢，採lang。'),
      'allies':('盟友','規則複數，不把UI的{number}模板帶入正文。'),
      'applied':('套用','not automatically applied＝不會自動套用；不用UI狀態已套用。'),
      'armor':('護甲','任何護甲均不穿戴，保留原稿著裝句式，沒有補入盾牌限制。'),
      'attack':('攻擊','attack rolls完整譯攻擊檢定；melee attack譯近戰攻擊。'),
      'beast':('野獸知覺','出現在法術Beast Sense名稱，不將類型詞拆出另改完整法術名。'),
      'bonus':('附贈動作','本批只有Bonus Action；不是Bonus加值的UI欄位。'),
      'bonus action':('附贈動作','採lang；啟用狂暴時可併入該附贈動作，狂暴期間另用一個附贈動作。'),
      'cast':('施放','使用者既定句式及lang一致，原稿施展改為施放。'),
      'change':('更改','既有荒野之形起始段落用更改，原樣保留。'),
      'changes':('變化','Darkvision／Speed changes指變化，不是UI更改操作；黑暗視覺變化自動套用，速度變化不會。'),
      'classes':('—','只在Embed參數classes="three right"；原樣保留技術資料，不翻職業。'),
      'climb':('攀爬速度','完整移動類型，與lang一致。'),
      'condition':('狀態','Prone狀態；行動condition技術key保持英文。'),
      'creature':('生物','量詞一名，無額外UI{number}模板。'),
      'creatures':('生物','受影響生物為複数，不加入計數UI模板。'),
      'damage':('傷害','熊除四種類型外的傷害抗力，採lang。'),
      'damage type':('傷害類型','完整類型詞，與lang一致。'),
      'darkvision':('黑暗視覺','採感官語境lang；spells-glossary同名法術中文相同，但不是決定感官詞的來源。'),
      'disadvantage':('劣勢','雄獅對指定例外以外的目標攻擊具有劣勢，採lang。'),
      'effect':('Active Effect','Foundry註記依使用者裁定保留Active Effect，並非一般效果詞。'),
      'enemies':('敵人','所有位於你5呎內的敵人，不帶UI數量模板。'),
      'enemy':('敵人','狼明確為你的敵人，盟友可攻擊任一符合資格者，非限定近戰。'),
      'every':('所有','熊的每種傷害類型除外名單完整；沒有只選一種的限制。'),
      'feature':('特性','Animal Speaker特性及Foundry特性說明一致。'),
      'features':('特性','現行子職業特性已接受，完整title保留。'),
      'feet':('呎','使用台灣單位呎，不用英呎、不換公尺。'),
      'foot':('呎','5 foot target template為5呎目標模板。'),
      'force':('力場','傷害類型，採lang。'),
      'large':('大型','Large or smaller為大型或更小型；正文沿原稿體型不超過大型，範圍相同。'),
      'level':('3級','advance to level 3照中文數字加級，沒有必要寫成3等級。'),
      'long':('長休','只在Long Rest，按完整詞組，不用長距離。'),
      'long rest':('長休','既有荒野之形長休句已核對，原样保留。'),
      'magical':('魔法','依原稿學習與動物交流的魔法手段；使用者明示介紹回到來源底稿。'),
      'melee':('近戰','採lang。'),
      'melee attack':('近戰攻擊','依使用者當你以近戰攻擊命中句式，正文及condition皆明確命中。'),
      'modifier':('調整值','感知調整值／施法調整值；未把modifier改成施法屬性。'),
      'nature':('自然','只在Nature Speaker／Commune with Nature專名，不是技能自然檢定。'),
      'necrotic':('黯蝕','裁定及lang一致；原稿暗蝕不採。'),
      'options':('選項','每次狂暴可選一项，荒野之形每長休可更改；Foundry未自動化選項明列。'),
      'other':('以外','targets other than you or another…為你或另一名…以外的目標，不用UI其他動作。'),
      'prone':('伏地','使用者裁定、terms與lang一致，原稿倒地改為伏地。'),
      'psychic':('心靈','傷害類型，採lang。'),
      'radiant':('光耀','傷害類型，採lang。'),
      'range':('範圍','Darkvision感官範圍不是攻擊射程；沿原稿黑暗視覺範圍。'),
      'reference':('—','Reference為技術標記，不翻目標；Prone標籤加伏地。'),
      'resistances':('抗力','本批只涉及傷害抗力，依使用者限定語境裁定，不用UI泛稱抗性。'),
      'rest':('長休','完整Long Rest，不能拆成一般休息。'),
      'ritual':('儀式','兩個語者法術僅限以儀式施放，採lang。'),
      'rolls':('檢定','attack rolls是攻擊檢定，不是一般UI擲骰。'),
      'speed':('速度','攀爬、游泳、飛行速度皆等同於你的速度，無額外數字。'),
      'spell':('法術','採lang；Nature Speaker單一法術，Animal Speaker兩個法術。'),
      'spellcasting':('施法','按完整施法屬性或施法調整值語境，採lang。'),
      'spellcasting ability':('施法屬性','已裁定及lang一致；感知為施法屬性。'),
      'spells':('法術','指先述野獸知覺及動物交談術兩個法術，不擴張至其他法術。'),
      'subclass':('子職業','現行title子職業特性原樣保留。'),
      'swim':('游泳速度','完整移動類型，與lang一致。'),
      'target':('目標','Foundry模板辨識受影響生物，不帶UI個目標量詞。'),
      'targets':('目標','雄獅的目標例外完整，沒有將目標限縮為生物。'),
      'three':('—','Embed樣式參數three，原樣保留，不是正文三個選項。'),
      'type':('類型','只在傷害類型，與lang一致。'),
      'uses':('使用','Eagle行動使用一個附贈動作；不是使用次數欄位。'),
      'view':('視作','view themselves as kin照原稿將自身視作動物們的家人，不用UI檢視；使用者明示更正。'),
      'walk':('一同漫步／跟隨','標語及道途照原稿；使用者明示介紹全部依來源底稿，不用UI步行速度詞。'),
      'wisdom':('感知','法術施法屬性及調整值，採lang。'),
    }
    def lookup(group,name):return next((v for k,v in index[group].items() if k.lower()==name.lower()),'—')
    terms=[]
    for line in (DATA/(PREFIX+'.lang-compare.md')).read_text(encoding='utf-8').splitlines():
        if not line.startswith('| ') or line.startswith('| EN '):continue
        cells=[s.strip() for s in line.strip('|').split('|')]
        if len(cells)!=4:continue
        name,tool_zh,mark,key=cells
        assert name in choices,('Unexplained lang hit',name)
        chosen,reason=choices[name]
        pattern=re.compile(r'(?<![a-z])'+re.escape(name)+r'(?![a-z])',re.I)
        paths=[r['path'] for r in mapping if pattern.search(english_text(r['en']))]
        technical=[r['path'] for r in mapping if pattern.search(r['en']) and r['path'] not in paths]
        variations=sorted({lang_zh[k] for k,v in lang_en.items() if isinstance(v,str) and v.strip().lower()==name and k in lang_zh})
        terms.append({'en':name,'terms':lookup('terms',name),'spells_glossary':lookup('spells_glossary',name),'lang':'／'.join(variations) or tool_zh,'chosen':chosen,'context':reason.replace('複数','複數').replace('原样','原樣').replace('一项','一項'),'paths':paths,'technical_paths':technical,'tool_draft_mark':mark,'checked':True})
    formal={**{key:load('full-classes')['entries'][key]['name'] for key in KEYS},'Beast Sense':'野獸知覺','Speak with Animals':'動物交談術','Commune with Nature':'問道自然','Rage':'狂暴','Resistance':'抗力','Climb Speed':'攀爬速度','Swim Speed':'游泳速度','Fly Speed':'飛行速度','Active Effect':'Active Effect','Bear':'熊','Eagle':'鷹','Wolf':'狼','Owl':'梟','Panther':'豹','Salmon':'鮭','Falcon':'獵鷹','Lion':'雄獅','Ram':'角羊','Aspect of the Owl':'梟之形','Rage of the Bear':'熊之狂暴','Rage of the Wolf':'狼之狂暴','Power of the Wilds: Ram':'狂野威能：角羊'}
    class_live=load('classes.live')['units'];spell_live=load('spells.live')['units']
    for name,chosen in formal.items():
        current=(class_live.get('entries.'+name+'.name') or spell_live.get('entries.'+name+'.name') or {}).get('target',[''])[0]
        if current==name:current='—'
        paths=[r['path'] for r in mapping if re.search(r'(?<![a-z])'+re.escape(name)+r'(?![a-z])',english_text(r['en']),re.I)]
        if current:reason='現行2024 Weblate名稱優先；本批直接沿用。'
        elif name=='Active Effect':reason='使用者定案保留英文；僅用於Foundry註記。'
        elif name=='Resistance':reason='傷害抗力使用者裁定優先；同名glossary法術提升抗力不適用此規則語境。'
        elif name in ['Climb Speed','Swim Speed','Fly Speed']:reason='使用lang的移動類型攀爬／游泳／飛行及速度組成完整規則詞。'
        elif name in ['Owl','Panther','Salmon']:reason='现行荒野之形同名行動已接受梟／豹／鮭，與原稿轉繁一致，沿用並保留。'.replace('现行','現行')
        elif name in ['Bear','Eagle','Wolf','Falcon','Lion','Ram']:reason='原稿動物選項名稱轉繁，正式兩套術語集查無對應詞條；按該特性名稱語境，待本批v2確認。'
        else:reason='完整現行資料核對後未有中文名稱；依原稿特性名或對應已譯組成詞提出，待本批v2確認，沒有新增正式詞條。'
        lang_values=sorted({lang_zh[k] for k,v in lang_en.items() if isinstance(v,str) and v.lower()==name.lower() and k in lang_zh})
        terms.append({'en':name,'terms':lookup('terms',name),'spells_glossary':lookup('spells_glossary',name),'lang':'／'.join(lang_values) or '—','current_2024':current or '—','chosen':chosen,'context':reason,'paths':paths,'checked':True})
    save('term-audit',terms)
    rules={
      'Path of the Wild Heart':'使用者明示介紹全部照來源底稿；kin以家人表達親屬關係，取代現行伙伴，標語亦依來源。類別name狂野之心道途仍沿用現行；classes與content使用同一獨立中文底稿。Merriam-Webster的kin名詞義為親屬，形容詞為有親屬關係；沒有以該詞指一般伙伴的依據。',
      'Animal Speaker':'兩個指定法術只可儀式施放；感知為兩者施法屬性。Foundry升至3級加入兩個儀式，使用感知調整值；未改成可一般施放或可任選法術。',
      'Rage of the Wilds':'每當啟用狂暴自選並獲得一項；熊四種類型除外，其餘所有傷害抗力；鷹啟用時併入該附贈動作撤離及疾走，期間可再以一個附贈動作同時採取；狼盟友對你5呎內你的任何敵人攻擊有優勢，不限近戰。Foundry熊抗力可自動化，鷹使用附贈動作，狼5呎模板只辨識受影響生物。',
      'Aspect of the Wilds':'獲得自選一項，每當完成長休可更換；梟60呎黑暗視覺或既有範圍增加60呎；豹攀爬、鮭游泳速度等同你的速度。既有完整首段保留，梟未完成中英文需補齊；Foundry只自動套用梟的黑暗視覺，速度不自動套用。',
      'Nature Speaker':'只限問道自然以儀式施放，感知為該法術施法屬性；Foundry預設儀式與感知施法調整值，沒有擴及其他法術。',
      'Power of the Wilds':'每當啟用狂暴自選並獲得一項；獵鷹狂暴期間且未著裝任何護甲有等同速度的飛行速度；雄獅你5呎內所有敵人對例外以外目標的攻擊劣勢，另一名野蠻人必須啟用此選項；角羊狂暴期間近戰命中大型或更小型生物，可選擇使其伏地，無額外豁免。Foundry只自動化角羊伏地，獵鷹／雄獅不自動化。',
    }
    pairs=[]
    for row in mapping:
        key=next((k for k in KEYS if row['path'].startswith('entries.'+k+'.')),KEYS[0] if row['component']=='content' else None)
        assert key is not None
        row['rule_review']=rules[key]
        if row['path'].endswith('.condition'):row['rule_review']='上游英文condition缺少動詞；完整正文寫when you hit it with a melee attack。使用者明示「當你以近戰攻擊命中，才對」，依正文補命中並採其句式。大型或更小型、近戰與命中均保留。'
        elif row['path'].endswith('Falcon.chatFlavor'):row['rule_review']='該介面句只寫未著裝任何護甲則獲得等同速度的飛行速度；未自行加上原句沒有的狂暴条件。'.replace('条件','條件')
        elif row['path'].endswith('effects.Rage of the Wolf.description'):row['rule_review']='效果description的EN只有盟友、你的敵人、你5呎內、攻擊檢定優勢；源自狼底稿完整規則句，去除主描述專用狂暴期間起句，與效果自身EN一致。'
        assert visible_text(row['zh'])==row['draft']
        if row['source']=='protected':continue
        en=english_text(row['en'])
        english=[s.strip() for s in re.split(r'(?<=[.!?])\s+(?=[A-Z])',en) if s.strip()]
        chinese=[s.strip() for s in re.split(r'(?<=[。！？])',row['draft']) if s.strip()]
        paired=list(zip(english,chinese)) if len(english)==len(chinese) else [(en,row['draft'])]
        for i,(e,z) in enumerate(paired,1):pairs.append({'path':row['path'],'unit':i if len(english)==len(chinese) else '完整區塊（小標或既有中文句數不改）','en':e,'zh':z,'qualifiers':re.findall(r'\b(?:this|these|that|the|following|one of|each|any|all|every|only|both|first|same|another)\b',e,re.I),'review':row['rule_review']})
    save('mapping-audit',mapping)
    save('sentence-audit',pairs)
    # Every non-retained mapping is disclosed with its original Chinese, full
    # EN and target, not just a short discrepancy summary.
    issues=[]
    for row in mapping:
        if row['source']=='protected':continue
        special=row['retained'] and (row['path']=='entries.Path of the Wild Heart.description/b0002' or row['path']=='entries.Aspect of the Wilds.name')
        if row['retained'] and not special:continue
        current=load(row['component']+'.live')['units'].get(row['path'].split('/')[0],{}).get('target',[''])[0]
        category='既有譯文保留' if special else ('原稿缺漏補翻' if row['source']=='supplement' else ('現行名稱沿用至未翻欄位' if row['source']=='existing-corresponding-class' else '原稿到底稿／未完成文字'))
        reason=row['rule_review']
        if row['path']=='entries.Aspect of the Wilds.name':reason='現行2024 Weblate已接受荒野之形，與原稿獸之形貌有譯名差異；依使用者不改已有且相符中文，名稱原樣保留。'
        if row['path']=='entries.Aspect of the Wilds.description/b0002':reason+=' 現行梟段落為「你擁有60呎You have Darkvision…」的未完成混合文字；以獨立來源底稿補齊，既有【梟】標題沿用。'
        if row['path']=='entries.Power of the Wilds.description/b0003':reason+=' 原稿另一個選擇該項能力的野蠻人未明寫active，底稿補啟用了此選項，不能只因曾選過就排除劣勢。'
        if '.description/' not in row['path'] and row['source']=='supplement':reason+=' 原稿無獨立介面欄位；依EN欄位與本特性正文、現行法術／動物名称補翻，未新增正式詞條。'.replace('名称','名稱')
        issues.append({'id':f'I{len(issues)+1:02}','component':row['component'],'path':row['path'],'category':category,'en_full':english_text(row['en']),'en_raw':row['en'],'source_full':row['source_original'],'current_full':current,'draft_full':row['draft'],'reason':reason,'retained':row['retained'],'status':'既有中文原樣保留。' if row['retained'] else ('condition句式已裁定；本批v2仍待確認。' if row['path'].endswith('.condition') else '待本批v2確認。')})
    source=(DATA/(PREFIX+'.source.txt')).read_text(encoding='utf-8').splitlines()
    issues.append({'id':f'I{len(issues)+1:02}','component':'source','path':'source.line28','category':'無對應EN欄位','en_full':'No corresponding English field in classes/content.','en_raw':'','source_full':source[27],'current_full':'沒有可對應的EN欄位。','draft_full':'原稿譯註保留於remaining.txt；不加入規則正文、不新增key。','reason':'原稿盾牌解說及SA引述為作者譯註，EN無此段；沒有將其轉作EN規則或更動甲胄條件。','retained':True,'status':'來源保留，未匹配1段譯註，不列payload。'})
    save('issues',issues)
    problem=['# 狂野之心道途第2批 v2：全部差異與補翻','','完整EN、原稿中文、现行譯文及獨立底稿逐項列出；整個description的現行值不截斷。角羊condition句式已依使用者裁定，使用者已授權按本次修正上傳v2；此文件先完成驗收，尚待送出。'.replace('现行','現行'),'']
    for item in issues:
        problem += ['## '+item['id']+' '+item['category'],'','欄位：`'+item['path']+'`','','**EN完整原句／段落／名稱：**',item['en_full'],'','**EN原始標記：**','```html',item['en_raw'],'```','','**中文原稿完整文字：**',item['source_full'],'','**現行Weblate完整值：**',item['current_full'],'','**完整底稿／補翻：**',item['draft_full'],'','**原因與處理：** '+item['reason'],'','狀態：'+item['status'],'']
    write('issues.md','\n'.join(problem))
    full=['# 狂野之心道途第2批 v2：全面對照','','28行來源完整保存。頁面標題Path of Wild Heart少the，已由同站2024頁面、確切UUID及EN key確認為Path of the Wild Heart，沒有另建別名key。','## 原樣保留的7個完整欄位','']
    for row in retained:full+=['### '+row['path'],'','EN：','```html',row['en'],'```','既有中文：','```html',row['zh'],'```','處理：'+row['reason'],'']
    for row in mapping:
        full+=['## '+row['component']+' / '+row['path'],'','來源：'+row['source']+'；行號：'+str(row['source_lines']),'','**EN完整文字：**',english_text(row['en']) or '（Embed無可見文字。）','','**原稿完整中文：**',row['source_original'],'','**独立底稿：**'.replace('独立','獨立'),row['draft'] or '（無可見文字。）','','**成品可見文字：**',visible_text(row['zh']) or '（無可見文字。）','','**規則核對：** '+row['rule_review'],'','可見文字與底稿逐字相同；原始EN與成品標記：','```html',row['en'],'```','```html',row['zh'],'```','']
    full+=['## 全部句子／完整區塊與限定詞','']
    for pair in pairs:full+=['### '+pair['path']+' · '+str(pair['unit']),'','**EN：** '+pair['en'],'','**中文：** '+pair['zh'],'','限定詞：'+(', '.join(pair['qualifiers']) or '無指定限定詞。'),'','核對：'+pair['review'],'']
    write('full-comparison.md','\n'.join(full))
    info.update(rule_review_complete=True,terminology_review_complete=True,chinese_readthrough_complete=True,paired_sentences_or_blocks=len(pairs),issue_count=len(issues),lang_hits=sum('tool_draft_mark' in r for r in terms),terms_reviewed=len(terms),description_supplement_blocks=sum(r['source']=='supplement' and '.description/' in r['path'] for r in mapping),nested_supplement_fields=sum(r['source']=='supplement' and '.description/' not in r['path'] for r in mapping),unmatched_source_notes=1,unresolved_payload_fields=0,condition_user_ruling=True)
    save('verification',info)
    def link(suffix,label):return '['+label+']('+str(DATA/(PREFIX+'.'+suffix)).replace('\\','/')+')'
    preview=['# 狂野之心道途第2批 v2','','已確認28個字串：classes 6條26字串、content 1個日誌頁2字串。**使用者已授權上傳，待送出。** 7個完整既有欄位及1個正文區塊原樣保留。','','- '+link('draft.txt','獨立正文底稿')+'；'+link('supplement.draft.txt','獨立Foundry及介面補翻底稿')+'。','- '+link('preview.html','完整成品預覽')+'。','- '+link('issues.md','全部問題及補翻：完整中英文')+'。','- '+link('full-comparison.md','全面欄位與句子核對')+'。','','## 本批範圍','','| EN key | 名稱 | 來源行號 | 處理 |','|---|---|---|---|','| Path of the Wild Heart | 狂野之心道途 | 2–4 | 既有名稱／子職業特性title保留；介紹依使用者指示改用來源底稿；補3個advancement欄位 |','| Animal Speaker | 動物語者 | 5–8 | 既有名稱保留；正文與Foundry未翻，補齊 |','| Rage of the Wilds | 野性狂暴 | 9–14 | 原稿正文、3動物選項及Foundry、行動／效果 |','| Aspect of the Wilds | 荒野之形 | 15–20 | 既有名稱、完整首段、3行動名保留；補齊混合英文與效果 |','| Nature Speaker | 自然語者 | 21–22 | 原稿正文與Foundry，名稱待本批確認 |','| Power of the Wilds | 狂野威能 | 23–27 | 原稿正文與Foundry、行動／效果 |','| Barbarian.pages.Path of the Wild Heart | 狂野之心道途 | 2–4 | 日誌與classes共用來源底稿，Embed及UUID保留 |','','## 需注意的差異','','1. 狂野之心道途介紹全部依來源底稿。kin採家人，取代現行伙伴；先前未查證就認定可保留不恰當。Merriam-Webster支持親屬／家人的詞義，未找到支持此處一般伙伴的依據。荒野之形名称與原稿獸之形貌不同，採現行名称原樣保留。'.replace('名称','名稱'),'2. 荒野之形的梟段落现行為「你擁有60呎You have Darkvision…」，需補齊未完成中英文；既有起始完整段落逐位元保留。'.replace('现行','現行'),'3. 雄獅原稿只說另一個選擇該項能力的野蠻人；EN要求該野蠻人啟用此選項。底稿補「另一名啟用了此選項的野蠻人」，保留正確劣勢例外。','4. 法術名称沿用現行2024 Weblate：野獸知覺、動物交談術、問道自然；原稿野獸感官與動物交談不採。'.replace('名称','名稱'),'5. 角羊condition的英文漏了命中動詞，使用者已指定「當你以近戰攻擊命中，才對」，正文及condition採此句式。','6. 原稿第28行盾牌譯註在EN沒有對應欄位，原稿保留，未匹配1段，沒有加進規則正文或捏造key。','','## 唯一activities.condition','','**EN原句（上游漏字）：** '+load('condition-ruling')['en'],'','**完整正文依據：** '+english_text(next(r['en'] for r in mapping if r['path']=='entries.Power of the Wilds.description/b0004')),'','**本批中文：** '+load('condition-ruling')['proposed_zh'],'','**裁定：** 使用者「當你以近戰攻擊命中，才對」。本批版本待確認，上傳仍只使用建議。','','## 四項驗收','','- 規則核對：每次狂暴選一項、長休可換選項、熊四種除外、鷹兩個動作、狼盟友與你的敵人、3種速度、雄獅active例外、角羊近戰命中／體型全部逐句核對；原稿譯註不當成EN规则。'.replace('规则','規則'),'- 術語核對：完整分頁classes2209、content1161、spells1639、terms136、spells-glossary640；'+str(info['lang_hits'])+'個lang命中全部逐項說明，另核對完整法術／特性／動物／效果名称；未新增正式詞條。'.replace('名称','名稱'),'- 機械驗證：共用validate對完整6條成品通過，再從該成功輸出排除7個原樣欄位，得到26字串payload；content的2個頁面欄位以相同check_description及compare_html另驗。HTML、UUID、Reference、Embed及參數保留，全部60個映射位置與底稿相同。','- 中文通讀：獨立閱讀底稿，再核對EN主體、例外及否定；既有完整中文不為統一句型改寫。正文及補翻無「它」，格式小標為【】且不留句號。','','## 三方術語對照：每個lang命中及專名','','| EN | terms | spells-glossary | lang | 採用及理由 |','|---|---|---|---|---|']
    for term in terms:preview.append('| '+' | '.join([term['en'],term['terms'],term['spells_glossary'],term['lang'],term['chosen']+'；'+term['context']])+' |')
    preview+=['','全部術語路徑及技術參數命中另見'+link('term-audit.json','術語逐處查核')+'；'+link('lang-compare.md','lang工具原始輸出')+'。原稿缺漏的'+str(info['description_supplement_blocks'])+'個Foundry區塊及'+str(info['nested_supplement_fields'])+'個介面欄位，全部完整列入問題文件。名稱沿用原稿或已接受詞組，未新增正式術語。','','## 確認版本','','classes SHA-256：`'+info['payload_sha256']['classes']+'`。','content SHA-256：`'+info['payload_sha256']['content']+'`。','','使用者已裁定野性狂暴、狂野威能及介紹全部照底稿，並明示「其他應該沒問題，上傳」。本批v2按這些明示修正執行建議上傳。依[translation-import SKILL.md]('+str(ROOT/'.claude/skills/translation-import/SKILL.md').replace('\\','/')+')第5步「每批版本得到使用者明確確認後才上傳」，本批v2已依使用者本次明示修正及上傳授權完成準備。','','主頁先前無EN欄位的等級表／職業說明維持remaining；下一批依序世界樹道途、狂熱者道途，尚未開始。執行腳本留在/scripts/translation-import/player-handbook/。']
    write('preview.md','\n'.join(preview))
    def render(value):return LABEL.sub(lambda m:'<span class="annotation" title="'+html.escape(m[1],quote=True)+'">'+html.escape(m[2])+'</span>' if m[2] else '<span class="technical">〔原始Embed，參數保留〕</span>',value)
    doc=['<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>狂野之心道途第2批v2</title><style>body{font-family:system-ui,"Microsoft JhengHei",sans-serif;background:#f8f7f3;color:#243239;line-height:1.8;max-width:950px;margin:36px auto;padding:0 24px}article{border-top:2px solid #b99a6c;margin:28px 0;padding-top:12px}.secret{background:#eee9e0;padding:4px 16px}.field{background:#e5ece8;padding:8px;margin:5px 0}.annotation{color:#286c7c;border-bottom:1px dotted}.technical{color:#777}.retained{color:#577a51}</style><h1>狂野之心道途第2批 v2</h1><p>28個字串已確認，待送出建議。7個完整既有欄位及1個正文區塊保留。</p>']
    for key,item in load('full-classes')['entries'].items():
        doc+=['<article><h2>'+html.escape(item['name'])+'</h2><p>'+html.escape(key)+'</p>']
        if key==KEYS[0]:doc+=['<p class="retained">名稱與子職業特性title保留；完整介紹依使用者指示改用來源底稿，另補3個advancement欄位。</p>']
        if key=='Aspect of the Wilds':doc+=['<p class="retained">名稱、完整首段及梟／豹／鮭行動名稱保留。</p>']
        doc+=[render(item['description'])]
        for field in ['activities','effects','advancement']:
            for path,value in leaves(item.get(field,{}),field):doc+=['<div class="field"><b>'+html.escape(path)+'</b><div>'+render(value)+'</div></div>']
        doc+=['</article>']
    page=load('content.upload')['entries']['Barbarian']['pages']['Path of the Wild Heart']
    doc+=['<article><h2>日誌頁：'+html.escape(page['name'])+'</h2>',render(page['description']),'</article></html>']
    write('preview.html','\n'.join(doc))
    index_path=BASE/'subclasses/index.md'
    text=index_path.read_text(encoding='utf-8')
    text=re.sub(r'(\| 狂野之心道途 \|[^\n]+\| )尚未抓取／處理( \|)',r'\g<1>第2批v2預覽，未上傳；27字串待確認，保留8既有欄位；原稿譯註無EN欄位1段\g<2>',text)
    marker='狂野之心道途第2批：[完整預覽]('+str(DATA/(PREFIX+'.preview.md')).replace('\\','/')+')。來源2–4介紹、5–8動物語者、9–14野性狂暴、15–20荒野之形、21–22自然語者、23–27狂野威能；第28行譯註留remaining。'
    if marker not in text:text+='\n'+marker+'\n'
    index_path.write_text(text,encoding='utf-8')
    print(json.dumps(info,ensure_ascii=False))

APPROVED_HASHES={
 'classes':'834031f6010bf0dba5c992f4ffbbb56952389a37fe0a4f8638ac0e84fdc88a15',
 'content':'0e490f9b209a92a8091e3bafce0026531e15454567d64641bac47b90f53713b8',
}

def approved_payloads():
    info=load('verification')
    assert info['version']=='v2' and info['payload_sha256']==APPROVED_HASHES
    assert all(info[k] for k in ['mechanical_pass','all_exact_draft_matches','live_en_match','rule_review_complete','terminology_review_complete','chinese_readthrough_complete'])
    rulings=load('user-rulings')
    assert rulings['rulings']['Rage of the Wilds']=='野性狂暴'
    assert rulings['rulings']['Power of the Wilds']=='狂野威能'
    assert rulings['authorization']=='其他應該沒問題，上傳'
    for suffix,digest in info['draft_sha256'].items():assert hashlib.sha256((DATA/(PREFIX+'.'+suffix+'.txt')).read_bytes()).hexdigest()==digest
    expected={}
    for component,digest in APPROVED_HASHES.items():
        file=DATA/(PREFIX+'.'+component+'.upload.json')
        assert hashlib.sha256(file.read_bytes()).hexdigest()==digest
        expected[component]=dict(leaves(read(file)))
        assert len(expected[component])=={'classes':26,'content':2}[component]
        for context,zh in expected[component].items():
            en=load(component+'.live')['units'][context]['source'][0]
            assert not check_description(en,zh,{'Foundry','Active','Effect'}),(context,check_description(en,zh,{'Foundry','Active','Effect'}))
    assert expected['classes']['entries.Rage of the Wilds.name']=='野性狂暴'
    assert expected['classes']['entries.Power of the Wilds.name']=='狂野威能'
    assert expected['classes']['entries.Power of the Wilds.effects.Power of the Wilds: Ram.name']=='狂野威能：角羊'
    for component in expected:
        path='entries.Path of the Wild Heart.description' if component=='classes' else 'entries.Barbarian.pages.Path of the Wild Heart.description'
        assert '家人' in expected[component][path] and '伙伴' not in expected[component][path] and '夥伴' not in expected[component][path]
    for row in load('retained'):assert row['path'] not in expected[row['component']]
    for row in load('mapping-audit'):assert visible_text(row['zh'])==row['draft']
    old=Plan(load('classes.live')['units']['entries.Aspect of the Wilds.description']['target'][0]).blocks[0].html
    new=Plan(expected['classes']['entries.Aspect of the Wilds.description']).blocks[0].html
    assert old==new
    return expected

def preflight():
    expected=approved_payloads();records={}
    for component in expected:
        slug=PROJECT+'-'+component
        status_result=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'.claude/skills/translation-import/scripts/weblate.py'),'status',PROJECT,slug],capture_output=True,text=True,encoding='utf-8')
        write(component+'.status.txt',status_result.stdout+status_result.stderr)
        assert status_result.returncode==0
        status,translation=w.call('GET',f'/api/translations/{PROJECT}/{slug}/zh_Hant/')
        filename=f'compendium/zh-tw/{PROJECT}/{PROJECT}.{component}.json'
        assert status==200 and translation['filename']==filename
        status,settings=w.call('GET',f'/api/components/{PROJECT}/{slug}/')
        assert status==200 and settings.get('push')
        status,repo=w.call('GET',f'/api/components/{PROJECT}/{slug}/repository/')
        assert status==200 and not repo.get('merge_failure')
        rows,pagination=read_all(PROJECT,slug)
        all_units={r['context']:r for r in rows}
        units={p:all_units[p] for p in expected[component]}
        preview=load(component+'.live')['units']
        for path,unit in units.items():
            assert unit['source']==preview[path]['source'],'EN changed: '+path
            assert unit['target']==preview[path]['target'],'Translation changed since review: '+path
        if component=='classes':
            for row in load('retained'):assert all_units[row['path']]['target']==[row['zh']]
        save(component+'.before',units);save(component+'.component-before',all_units)
        records[component]={'filename':filename,'push_url_set':True,'repository':{k:repo.get(k) for k in ['needs_commit','needs_push','needs_merge','merge_failure']},'pagination':pagination,'matched_strings':len(units),'prior_suggestions':[p for p,u in units.items() if u['has_suggestion']],'same_target':[p for p,u in units.items() if u['target']==[expected[component][p]]]}
    save('preflight',records)
    save('approval',{'version':'v2','date':'2026-10-08','approved':True,'authorization':load('user-rulings'),'scope':'按明示修正後上傳野性狂暴、狂野威能及原稿家人完整介紹；classes26＋content2，method=suggest。','payload_sha256':APPROVED_HASHES})
    info=load('verification');info['approved']=True;save('verification',info)
    print(json.dumps(records,ensure_ascii=False))

def upload_component(component):
    expected=approved_payloads()[component]
    assert load('approval')['approved'] and load('approval')['payload_sha256']==APPROVED_HASHES
    assert load('preflight')[component]['matched_strings']==len(expected)
    assert not (DATA/(PREFIX+'.'+component+'.upload-response.json')).exists(),'Already attempted; inspect before retry.'
    status,body=w.upload(PROJECT,PROJECT+'-'+component,str(DATA/(PREFIX+'.'+component+'.upload.json')),method='suggest')
    save(component+'.upload-response',{'http_status':status,'response':body,'sha256':APPROVED_HASHES[component],'method':'suggest'})
    print(json.dumps({'component':component,'http_status':status,'response':body},ensure_ascii=False))
    assert status in [200,201],'Investigate before any retry.'
    assert body['not_found']==0 and body['accepted']+body['skipped']==len(expected)

def audit_upload():
    expected=approved_payloads();audits={}
    for component in expected:
        rows,pagination=read_all(PROJECT,PROJECT+'-'+component)
        after={r['context']:r for r in rows};before=load(component+'.component-before')
        assert set(before)==set(after)
        for path,unit in after.items():
            assert unit['source']==before[path]['source'],'Source changed: '+path
            assert unit['target']==before[path]['target'],'Existing target changed: '+path
        accepted,skipped=[],[]
        for path,zh in expected[component].items():
            if after[path]['target']==[zh]:skipped.append({'context':path,'reason':'與現行譯文相同。'})
            else:
                assert not before[path]['has_suggestion'] and after[path]['has_suggestion'],'Inspect actual suggestions: '+path
                accepted.append({'context':path,'unit_id':after[path]['id'],'reason':'上傳前無建議，上傳後有建議；source及target不變。'})
        response=load(component+'.upload-response')['response']
        assert len(accepted)==response['accepted'] and len(skipped)==response['skipped'] and response['not_found']==0
        statistics={'component_total':len(after),'component_empty_or_source':sum(not any(u['target']) or u['target']==u['source'] for u in after.values()),'batch_strings':len(expected[component]),'batch_empty_or_source':sum(not any(after[p]['target']) or after[p]['target']==after[p]['source'] for p in expected[component]),'batch_has_suggestion':sum(after[p]['has_suggestion'] for p in expected[component])}
        save(component+'.after',{p:after[p] for p in expected[component]});save(component+'.statistics-latest',statistics)
        audits[component]={'accepted':accepted,'skipped':skipped,'not_found':[],'verified_strings':len(expected[component]),'component_verified_strings':len(after),'all_targets_unchanged':True,'pagination':pagination,'statistics':statistics,'response':response}
    result={'components':audits,'complete':True,'accepted':sum(len(a['accepted']) for a in audits.values()),'skipped':sum(len(a['skipped']) for a in audits.values()),'not_found':0,'all_targets_unchanged':True,'component_verified_strings':sum(a['component_verified_strings'] for a in audits.values())}
    save('upload-audit',result);print(json.dumps(result,ensure_ascii=False))

def archive_upload():
    approved_payloads()
    audit=load('upload-audit')
    assert audit['complete'] and audit['all_targets_unchanged'] and audit['accepted']+audit['skipped']==28
    destination=BASE/'_done/subclasses/wild-heart'
    assert DATA.resolve().is_relative_to(BASE.resolve())
    assert destination.resolve().is_relative_to((BASE/'_done').resolve())
    files=sorted(DATA.glob(PREFIX+'.*'))
    assert files and all(f.is_file() and f.resolve().parent==DATA.resolve() and not (destination/f.name).exists() for f in files)
    destination.mkdir(parents=True,exist_ok=True)
    info=load('verification')
    info.update(approved=True,uploaded=True,method='suggest',upload_date='2026-10-08',accepted=audit['accepted'],skipped=audit['skipped'],not_found=0,archive_path=str(destination))
    save('verification',info)
    terms=load('term-audit')
    for term in terms:
        if term['en'] in ['Rage of the Wilds','Power of the Wilds']:
            term['context']='本次使用者明示名稱裁定優先，已確認並上傳建議；沒有新增正式詞條。'
        elif term['en']=='Power of the Wilds: Ram':term['context']='效果名同步使用使用者裁定的狂野威能及原稿角羊選項名稱，已確認並上傳建議。'
    save('term-audit',terms)
    issues=load('issues')
    for item in issues:
        if not item['retained']:item['status']='使用者已確認v2並以建議上傳。'
    save('issues',issues)
    issue_file=DATA/(PREFIX+'.issues.md')
    text=issue_file.read_text(encoding='utf-8').replace('使用者已授權按本次修正上傳v2；此文件先完成驗收，尚待送出。','使用者已確認本次修正v2，28個字串均已以建議上傳。')
    text=text.replace('待本批v2確認。','使用者已確認v2並以建議上傳。').replace('condition句式已裁定；本批v2仍待確認。','condition句式及v2均已確認，已以建議上傳。')
    issue_file.write_text(text,encoding='utf-8')
    preview=DATA/(PREFIX+'.preview.md')
    text=preview.read_text(encoding='utf-8').replace('**使用者已授權上傳，待送出。**','**28個字串已以建議上傳；跳過0、未匹配0。**')
    text=text.replace('本批v2按這些明示修正執行建議上傳。','本批v2已按這些明示修正完成建議上傳。').replace('本批版本待確認，上傳仍只使用建議。','本批v2已確認並完成建議上傳。')
    text=text.replace('待本批v2確認','本批v2已確認').replace('名稱待本批確認','名稱已確認')
    preview.write_text(text,encoding='utf-8')
    preview=DATA/(PREFIX+'.preview.html')
    preview.write_text(preview.read_text(encoding='utf-8').replace('28個字串已確認，待送出建議。','28個字串已確認並以建議上傳。'),encoding='utf-8')
    def link(suffix,label):return '['+label+']('+str(destination/(PREFIX+'.'+suffix)).replace('\\','/')+')'
    report=['# 狂野之心道途第2批 v2：上傳報告（2026-10-08）','','依使用者本次明示名稱／介紹修正及「其他應該沒問題，上傳」授權，以method=suggest上傳28個字串：新增28、跳過0、未匹配0。正式譯文保持不變，建議待接受。','','| 元件 | 本批字串 | HTTP | accepted | skipped | not_found |','|---|---:|---:|---:|---:|---:|']
    preflight_record=load('preflight')
    for component in APPROVED_HASHES:
        reply=load(component+'.upload-response');body=reply['response']
        report += [f"| {component} | {audit['components'][component]['verified_strings']} | {reply['http_status']} | {body['accepted']} | {body['skipped']} | {body['not_found']} |"]
    report += ['','API total／count為整個元件總數2209與1161，不是本批數。28個欄位上傳前無建議、上傳後有建議，API新增數與逐欄核對相符。全部3370個source及target均逐一比較且不變。','','## 使用者裁定與v1到v2修正','','- Rage of the Wilds：野性狂暴。','- Power of the Wilds：狂野威能（「狂寫」經使用者澄清），效果名同步為狂野威能：角羊。','- 狂野之心道途介紹全部依來源底稿，classes與日誌使用相同完整底稿；不是只換kin單字。','- 原v1第2至第6項均接受；角羊condition依先前使用者「當你以近戰攻擊命中，才對」的句式；其餘內容維持v1已確認內容。','- v1未曾上傳，歷史預覽保留於versions/v1；本次只上傳v2，沒有重傳或刪除舊建議。','','## kin詞義查核及完整介紹','','先前沿用Weblate既有伙伴，但未查證就認定可保留不恰當。Merriam-Webster將kin名詞解釋為親屬，形容詞為具有親屬關係，並列family同義詞；未在核對的詞典找到支持此處一般伙伴的義項。依詞義及句中將自己視作動物親屬的語境，原稿家人更適合。這是語境判斷，不宣稱與動物存在生物學血親。','', '[Merriam-Webster：kin](https://www.merriam-webster.com/dictionary/kin)，查閱日期2026-10-08。','', '**EN標語：** Walk in Community with the Animal World','', '**中文標語：** 與動物世界一同漫步','', '**EN完整介紹：** '+english_text(Plan(load('classes.live')['units']['entries.Path of the Wild Heart.description']['source'][0]).blocks[1].html),'', '**中文完整介紹：** '+visible_text(Plan(load('classes.upload')['entries']['Path of the Wild Heart']['description']).blocks[1].html),'', '介紹源自原稿第3–4行的s2twp全文；只沿用已接受子職業名狂野之心道途、整理中文標點，不重組EN槽位。','','## 來源、差異與保留範圍','','來源28行全部保存，範圍：介紹2–4、動物語者5–8、野性狂暴9–14、荒野之形15–20、自然語者21–22、狂野威能23–27。6個classes條目26字串＋1個日誌頁2字串。','','7個完整既有欄位保留且不列payload：狂野之心道途name與子職業特性title、動物語者name、荒野之形name及梟／豹／鮭行動name。荒野之形description第一個完整中文區塊逐位元保持不變。狂野之心道途原已譯介紹此次經使用者明示改用來源底稿，僅以建議提出，未直接修改target。','','原稿第28行盾牌譯註沒有EN欄位，保留原稿與remaining，不加入規則正文；未匹配1段來源譯註不列payload。上傳not_found=0與這段来源未匹配是不同統計。'.replace('来源','來源'),'','13個Foundry正文區塊、15個獨立介面補翻欄位全部披露。53項差異／補翻紀錄、68組完整中英文句子或區塊、70個lang命中及98項术語查核全部保存。'.replace('术語','術語'),'','- '+link('issues.md','全部差異及補翻：完整EN、原稿、現行值與底稿')+'。','- '+link('full-comparison.md','所有欄位、完整句子與限定詞對照')+'。','- '+link('draft.txt','獨立正文底稿')+'；'+link('supplement.draft.txt','補翻底稿')+'。','- '+link('preview.html','完整成品預覽')+'；'+link('kin-research.json','詞義查核紀錄')+'；'+link('upload-audit.json','逐欄上傳稽核')+'。','','## 四項驗收','','規則：每次狂暴自選一項、長休更換、熊四種除外、鷹兩個動作、狼盟友及你的敵人、速度與護甲條件、雄獅啟用例外、角羊體型／命中／伏地逐句核對。術語：terms、spells-glossary、lang三方全部命中均有語境說明；現行2024法術名稱優先，本次兩個特性名依使用者裁定；未新增正式術語。機械：完整6條成品共33字串validate通過，從成功輸出排除7個原樣欄位形成26字串payload；content2字串逐欄驗證，60個映射位置與底稿可見文字完全相同，HTML、UUID、Reference、Embed及參數保留。中文：獨立通讀後回查底稿與EN，完整介紹照來源，不保留伙伴，無「它」與小標句號。','','唯一condition：','', '**EN（上游漏字）：** '+load('condition-ruling')['en'],'', '**正文依據：** '+english_text(next(r['en'] for r in load('mapping-audit') if r['path']=='entries.Power of the Wilds.description/b0004')),'', '**中文：** '+load('condition-ruling')['proposed_zh'],'','## 已確認版本與前置狀態','']
    for component,digest in APPROVED_HASHES.items():
        rec=preflight_record[component]
        report += [f'- {component} SHA-256：`{digest}`；'+link(component+'.upload.json','實際上傳payload')+'。',f'- filename：`{rec["filename"]}`，push URL已設；repository：`'+json.dumps(rec['repository'],ensure_ascii=False)+'`。']
    report += ['','兩元件既存needs_commit／needs_merge為真、merge_failure為空；本批suggest只寫建議，未執行合併、提交或推送。','','## 未翻數與後續','']
    for component,a in audit['components'].items():
        stat=a['statistics']
        report += [f'- {component}空值或target等於source：{stat["component_empty_or_source"]}／{stat["component_total"]}；本批其中{stat["batch_empty_or_source"]}個仍為空或英文相同，本批{stat["batch_has_suggestion"]}個有建議。']
    report += ['','建議不算已接受翻譯。介紹原為中文，荒野之形為中英文混合，因此不計入空值／source相同的24個classes字串，但兩者本次均有新增建議。','','下一批：世界樹道途、狂熱者道途，尚未开始；主頁原先沒有EN欄位的等級表／職業說明維持remaining。'.replace('开始','開始'),'','原稿及未匹配譯註維持於_incoming/player-handbook/subclasses/wild-heart/，成功產物歸檔至_done/subclasses/wild-heart/；共用原始HTML／文字仍留_web。執行腳本留/scripts/translation-import/player-handbook/。']
    write('2026-10-08.report.md','\n'.join(report))
    approved_payloads()
    files=sorted(DATA.glob(PREFIX+'.*'))
    immutable={PREFIX+'.draft.txt',PREFIX+'.supplement.draft.txt',PREFIX+'.classes.upload.json',PREFIX+'.content.upload.json'}
    keep={PREFIX+'.source.txt',PREFIX+'.source.s2twp.txt',PREFIX+'.source.json',PREFIX+'.remaining.txt'}
    for file in files:
        if file.name in immutable:continue
        text=file.read_text(encoding='utf-8')
        for old,new in [(str(DATA),str(destination)),(str(DATA).replace('\\','/'),str(destination).replace('\\','/')),(str(DATA).replace('\\','\\\\'),str(destination).replace('\\','\\\\'))]:text=text.replace(old,new)
        if file.name not in keep:file.write_text(text,encoding='utf-8')
    approved_payloads()
    for file in files:
        assert file.resolve().parent==DATA.resolve() and not (destination/file.name).exists()
        if file.name in keep:shutil.copy2(file,destination/file.name)
        else:file.rename(destination/file.name)
    history=DATA/'versions';history_destination=destination/'versions'
    assert history.resolve().is_relative_to(DATA.resolve()) and history_destination.resolve().is_relative_to(destination.resolve())
    assert history.is_dir() and not history_destination.exists()
    # Rebase historical v1 links to the v1 copies when they exist; these files
    # record the discarded preview, never the successful upload payload.
    v1=history/'v1';v1_destination=history_destination/'v1'
    for file in v1.iterdir():
        if file.suffix not in ['.md','.html']:continue
        text=file.read_text(encoding='utf-8')
        for referenced in v1.iterdir():
            old=str(DATA/referenced.name).replace('\\','/');new=str(v1_destination/referenced.name).replace('\\','/')
            text=text.replace(old,new)
        text=text.replace(str(DATA).replace('\\','/'),str(destination).replace('\\','/'))
        file.write_text(text,encoding='utf-8')
    shutil.move(str(history),str(history_destination))
    index_path=BASE/'subclasses/index.md'
    text=index_path.read_text(encoding='utf-8')
    text=re.sub(r'(\| 狂野之心道途 \|[^\n]+\| )[^\n]*?( \|)',r'\g<1>第2批v2已上傳28個建議（classes26＋content2）；7既有欄位保留；介紹依底稿家人\g<2>',text)
    text=text.replace(str(DATA).replace('\\','/'),str(destination).replace('\\','/')).replace('9–14獸性狂暴','9–14野性狂暴').replace('23–27獸力威能','23–27狂野威能')
    lines=text.splitlines();seen=False;filtered=[]
    for line in lines:
        if line.startswith('狂野之心道途第2批：'):
            if seen:continue
            seen=True
        filtered.append(line)
    index_path.write_text('\n'.join(filtered)+'\n',encoding='utf-8')
    index_path=BASE/'classes.barbarian.index.md'
    if index_path.exists():index_path.write_text(index_path.read_text(encoding='utf-8').replace('狂野之心道途已完成第2批v1預覽','狂野之心道途第2批v2已上傳28個建議'),encoding='utf-8')
    for component,digest in APPROVED_HASHES.items():assert hashlib.sha256((destination/(PREFIX+'.'+component+'.upload.json')).read_bytes()).hexdigest()==digest
    assert {f.name for f in DATA.glob(PREFIX+'.*')}==keep
    print(str(destination/(PREFIX+'.2026-10-08.report.md')))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['collect','prepare','map','compare','review','preflight','upload-classes','upload-content','audit','archive'])
    args=parser.parse_args()
    {'collect':collect,'prepare':prepare,'map':map_draft,'compare':compare_terms,'review':review,'preflight':preflight,'upload-classes':lambda:upload_component('classes'),'upload-content':lambda:upload_component('content'),'audit':audit_upload,'archive':archive_upload}[args.mode]()
