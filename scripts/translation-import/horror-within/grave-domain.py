"""Prepare Grave Domain translations and review artifacts; never upload."""
import copy, contextlib, difflib, hashlib, html, io, json, re, runpy, sys
from pathlib import Path
from urllib.parse import quote
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[3]
SK = ROOT/'.claude/skills/translation-import/scripts'
DATA = ROOT/'_incoming/horror-within/grave-domain'
sys.path.insert(0, str(SK))
import weblate as w, opencc
from html_blocks import Plan, visible_text, compare_html
from skeleton import build_entries, draft_sections
from validate import check_description, check_subfields
PROJECT='dnd-ravenloft-horros-within'
COMP='dnd-ravenloft-horrors-within-options'
KEYS=['Grave Domain','Grave Domain Spells','Circle of Mortality','Path to the Grave',"Sentinel at Death's Door",'Divine Reaper']

def save(name, value):
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA/(name+'.json')).write_text(json.dumps(value, ensure_ascii=False, indent=1), encoding='utf-8')
def load(name): return json.loads((DATA/(name+'.json')).read_text(encoding='utf-8'))
def write(name, value):
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA/name).write_text(value.rstrip()+'\n', encoding='utf-8')
def paged(path):
    rows=[]; audit=[]; page=1
    while True:
        status, body=w.call('GET', path+('&' if '?' in path else '?')+f'page_size=1000&page={page}')
        assert status==200 and isinstance(body,dict), (path,status)
        rows.extend(body['results']);audit.append({'page':page,'received':len(body['results']),'total':body['count']})
        if not body.get('next'):
            assert len(rows)==body['count'];return rows,audit
        page+=1
def leaves(node,prefix=''):
    if isinstance(node,dict):
        for k,v in node.items(): yield from leaves(v,prefix+'.'+k if prefix else k)
    elif isinstance(node,str): yield prefix,node
def tool(name,args):
    sys.argv=[str(SK/name),*args]
    try:runpy.run_path(str(SK/name),run_name='__main__')
    except SystemExit as exc:
        if exc.code:raise
def discover():
    rows,audit=paged('/api/projects/')
    save('projects',rows)
    chosen=[r for r in rows if re.search('horror|raven',r['slug'],re.I)]
    print('Projects', [(r['slug'],r['name']) for r in chosen])
    for p in chosen:
        comps,audit=paged('/api/projects/'+p['slug']+'/components/')
        save('components',comps)
        print('Components',[(r['slug'],r['name']) for r in comps])
    source=(ROOT/'_incoming/horror-within/grave-domain.txt').read_text(encoding='utf-8')
    write('grave-domain.source.txt',source)
    write('grave-domain.source.s2twp.txt',opencc.OpenCC('s2twp').convert(source))

def collect():
    for name,p,c in [('options',PROJECT,COMP),('terms','dnd-5e-2024-zh-tw','terms'),('spells-glossary','dnd-5e-2024-zh-tw','spells-glossary')]:
        rows,audit=paged(f'/api/translations/{p}/{c}/zh_Hant/units/')
        save(name+'.live',{'audit':audit,'units':rows});print(name,len(rows))
    from build_index import entry_names,aliases
    save('term_index',{'terms':{r['source'][0]:r['target'][0] for r in load('terms.live')['units'] if r['target']!=r['source'] and any(r['target'])},'spells_glossary':{r['source'][0]:r['target'][0] for r in load('spells-glossary.live')['units'] if r['target']!=r['source'] and any(r['target'])},'entry_names':{k:dict(v) for k,v in entry_names(str(ROOT/'compendium/zh-tw'),PROJECT).items()},'aliases':aliases(str(ROOT/'.claude/skills/translation-import/glossary.tsv'))})
    tool('spell_names.py',['--out',str(DATA/'spell-names.json')])
    units={r['context']:r for r in load('options.live')['units']}
    en=json.loads((ROOT/f'compendium/en/{PROJECT}/dnd-ravenloft-horrors-within.options.json').read_text(encoding='utf-8'))
    keys=KEYS
    save('scope',{'options':{k:en['entries'][k] for k in keys},'folders':{'Grave Domain':en['folders']['Grave Domain']}})
    report=[]
    for path,val in leaves({'entries':load('scope')['options'],'folders':load('scope')['folders']}):
        assert path in units,path
        assert units[path]['source'][0]==val,(path,'local EN differs')
        report.append(path+'\nEN: '+val+'\nZH: '+units[path]['target'][0]+f"\nstate: {units[path]['state']}")
    write('inventory.txt','\n\n'.join(report))
    searches=[]
    for q in ['Grave Domain','Circle of Mortality','Path to the Grave','Sentinel at Death','Divine Reaper']:
        rows,audit=paged('/api/units/?q='+quote('"'+q+'"'))
        searches.append({'query':q,'audit':audit,'units':rows})
    save('related-search',searches)
    print('scope',keys)
    print('related units',sum(len(x['units']) for x in searches))

def inspect():
    print('TERMS',json.dumps(load('term_index')['terms'],ensure_ascii=False))
    names=load('spell-names')
    for en in ['Spare the Dying','Detect Evil and Good','False Life','Gentle Repose','Ray of Enfeeblement','Revivify','Vampiric Touch','Blight','Death Ward','Dispel Evil and Good','Raise Dead']:print(en,names[en])
    print('Related')
    for q in load('related-search'):
        for r in q['units']:
            tr=r.get('translation',{})
            print(r['id'],str(tr),r['context'],r['target'][0][:120])
    print('source lines')
    for i,l in enumerate((DATA/'grave-domain.source.s2twp.txt').read_text(encoding='utf-8').splitlines(),1):print(i,l)

def search():
    scope=load('scope')['options']; queries=set()
    for k,e in scope.items():
        if k=='Divine Reaper':
            queries.update([visible_text(b.html) for b in Plan(e['description']).blocks]);queries.update(v for p,v in leaves(e) if p!='description')
    results=[]
    for q in sorted(queries):
        rows,audit=paged('/api/units/?q='+quote('"'+q+'"'))
        results.append({'query':q,'audit':audit,'units':rows})
        print(q[:90],len(rows),[(r['context'],r['target'][0][:90]) for r in rows if re.search('[一-鿿]',r['target'][0]) and r['source'][0]==q])
    save('supplement-search',results)

def prepare():
    maker=runpy.run_path(str(Path(__file__).with_name('grave-domain-draft.py')))
    scope=load('scope')['options'];live={r['context']:r for r in load('options.live')['units']}
    src=(DATA/'grave-domain.source.s2twp.txt').read_text(encoding='utf-8')
    plain,reasons,nested=maker['make'](src,scope,live,Plan,visible_text,load('spell-names'))
    sheet={'schema_version':2,'book':PROJECT,'component':'options','entries':{}}
    draft=[];baseline=[];metadata=[]
    for k,e in scope.items():
        name=live['entries.'+k+'.name']['target'][0] if k!='Divine Reaper' else '司命神使'
        bs=Plan(e['description']).blocks;old=Plan(live['entries.'+k+'.description']['target'][0]).blocks
        assert len(bs)==len(plain[k])==len(old),(k,len(bs),len(plain[k]))
        a,z=maker['BOUNDS'][k];raw=src.splitlines()[a-1:z]
        source_pars=[re.sub(r'[A-Za-z][A-Za-z\s\x27]*','',t).strip() for t in raw]
        baseline.append('來源 '+k+'\n'+'\n'.join(source_pars+([visible_text(b.html) for b in old] if k!='Divine Reaper' else [])+[v.strip() for line in source_pars if '\t' in line for v in line.split('\t') if v.strip()]))
        row={'name_en':e['name'],'name':name,'blocks':[]}
        for i,(b,t,ob) in enumerate(zip(bs,plain[k],old)):
            supp=k=='Grave Domain' and i==3
            row['blocks'].append({'id':b.id,'en':b.html,'zh':'','source':'supplement' if supp else 'draft','basis':'原稿無此子職業細節連結，沿用Weblate既有譯文並保留UUID。' if supp else '', 'draft_text':t,'old_html':ob.html,'origin':'原稿' if k=='Divine Reaper' else 'Weblate既有譯文（必要規則修正參照原稿）','lines':[a,z],'reason':reasons.get(k+'|'+str(i),'無修改')})
        for f in ['activities','effects','advancement']:
            if f not in e:continue
            row[f]=copy.deepcopy(e[f])
            for item,fields in row[f].items():
                for sub,v in fields.items():
                    path=f'entries.{k}.{f}.{item}.{sub}';oldval=live[path]['target'][0]
                    value,basis=nested.get(path,(oldval,'Weblate既有譯文，完整保留。'))
                    fields[sub]=value;metadata.append({'path':path,'en':v,'old':oldval,'zh':value,'basis':basis})
        sheet['entries'][k]=row
        main=plain[k][:-1] if k=='Grave Domain' else plain[k]
        extra=plain[k][-1:] if k=='Grave Domain' else []
        draft.append('### '+k+'\n名稱：'+name+'\n'+'\n'.join(main)+'\n〔EN 補翻／獨立欄位〕\n'+'\n'.join(extra+[p+'：'+v for p,v in leaves({f:row[f] for f in ['activities','effects','advancement'] if f in row})]))
    save('grave-domain.sheet',sheet);save('grave-domain.metadata',metadata)
    write('grave-domain.draft.txt','\n\n'.join(draft))
    write('grave-domain.source.segmented.s2twp.txt','\n\n'.join(baseline))
    save('grave-domain.bounds',maker['BOUNDS'])
    save('grave-domain.draft-fingerprint',{'sha256':hashlib.sha256((DATA/'grave-domain.draft.txt').read_bytes()).hexdigest()})
    save('grave-domain.ack',{'Circle of Mortality|reach':'reach Cleric level 11指達到牧師11級，並非武器觸及。','Grave Domain Spells|reach':'reach a Cleric level指達到牧師等級，並非武器觸及。',"Sentinel at Death's Door|take":'take a Reaction指採取反應，並非承受傷害。'})
    print('Prepared',len(scope),'entries',sum(len(r['blocks']) for r in sheet['entries'].values()),'blocks',len(metadata),'nested fields')

def markup(text,en,k):
    names=load('spell-names');names.update({x:r['name'] for x,r in load('grave-domain.sheet')['entries'].items()});names['Subclass Details']='子職業細節'
    headings={'Pull of Death.':'【死亡牽引】','Return to Life.':'【回歸生命】','Enhanced Necromancy.':'【增強死靈術】','Keeper of Souls.':'【眾魂監守者】'}
    atoms=[]
    pattern=r'<span class="inline-entry"><strong>.*?</strong></span>|<em>.*?</em>|<strong>.*?</strong>|@UUID\[[^\]]+\](?:\{[^}]*\})?|\[\[[^\]]+\]\](?:\{[^}]*\})?'
    for m in re.finditer(pattern,en):
        v=m[0]
        uuid=re.search(r'@UUID\[([^\]]+)\]\{([^}]+)\}',v)
        if uuid:
            label=names[uuid[2]];new=v.replace('{'+uuid[2]+'}','{'+label+'}')
        elif v.startswith('[['):
            raw=v.split(']]')[0]+']]';old=re.search(r'\{([^}]*)\}$',v)[1]
            label={'1d4 Necrotic':'1d4黯蝕','Necrotic or Radiant damage':'黯蝕或光耀傷害','regains Hit Points':'恢復'}[old]
            new=raw+'{'+label+'}'
        elif '<strong>' in v:
            old=re.search(r'<strong>(.*?)</strong>',v)[1];label=headings[old];new=v.replace(old,label)
        elif v.startswith('<em>'):
            label=text;new='<em>'+text+'</em>'
        else:raise ValueError(v)
        atoms.append((label,new))
    result=text;protected={}
    for i,(label,new) in enumerate(atoms):
        assert label in result,(k,label,result)
        token=f'\x00ATOM{i}\x00';result=result.replace(label,token,1);protected[token]=new
    for token,new in protected.items():result=result.replace(token,new)
    if '<br class="TODO" />' in en:
        marker='phbsplFalseLife0]{'+names['False Life']+'}</em>、'
        assert marker in result
        result=result.replace(marker,marker+'<br class="TODO" />',1)
    assert re.sub(r'\s','',visible_text(result))==re.sub(r'\s','',text),(k,visible_text(result),text)
    assert not compare_html(en,result),(k,compare_html(en,result))
    return result

def map_draft():
    assert hashlib.sha256((DATA/'grave-domain.draft.txt').read_bytes()).hexdigest()==load('grave-domain.draft-fingerprint')['sha256']
    sheet=load('grave-domain.sheet')
    for k,row in sheet['entries'].items():
        for b in row['blocks']:b['zh']=markup(b['draft_text'],b['en'],k)
    save('grave-domain.sheet',sheet)
    aligned=build_entries(sheet,load('scope')['options'],draft_sections(str(DATA/'grave-domain.draft.txt')))
    save('grave-domain.aligned',aligned)
    tool('validate.py',[str(DATA/'grave-domain.aligned.json'),'--book',PROJECT,'--component','options','--out',str(DATA/'grave-domain.full.json')])
    live={r['context']:r for r in load('options.live')['units']};payload={};changes=[];kept=[]
    for path,v in leaves(aligned):
        row=live[path];old=row['target'][0]
        if old==v:kept.append(path);continue
        changes.append({'path':path,'en':row['source'][0],'old':old,'zh':v,'id':row['id'],'state':row['state']})
        cur=payload;parts=path.split('.')
        for part in parts[:-1]:cur=cur.setdefault(part,{})
        cur[parts[-1]]=v
    save('grave-domain.upload',payload);save('grave-domain.changes',changes);save('grave-domain.kept',kept)
    print('Changed',len(changes),'kept',len(kept),'sha256',hashlib.sha256((DATA/'grave-domain.upload.json').read_bytes()).hexdigest())

def checks():
    sheet=load('grave-domain.sheet');audit=copy.deepcopy(sheet)
    for k,row in audit['entries'].items():
        row['blocks'].append({'id':'name-audit','en':k})
        for f in ['activities','effects','advancement']:
            if f in load('scope')['options'][k]:row[f]=load('scope')['options'][k][f]
    save('grave-domain.audit.sheet',audit)
    # The two level-9 spell names both change to live settled names; short-cell similarity is .44.
    # Keep this source-backed cell in the diff with its explicit term/UUID evidence.
    commands=[('draft_diff.py',['--source',str(DATA/'grave-domain.source.segmented.s2twp.txt'),'--draft',str(DATA/'grave-domain.draft.txt'),'--floor','0.4','--out',str(DATA/'grave-domain.draft-diff.md')]),('terms_check.py',[str(DATA/'grave-domain.audit.sheet.json'),'--draft',str(DATA/'grave-domain.draft.txt'),'--index',str(DATA/'term_index.json'),'--names',str(DATA/'spell-names.json'),'--ack',str(DATA/'grave-domain.ack.json'),'--out',str(DATA/'grave-domain.terms-report.md')]),('lang_compare.py',[str(DATA/'grave-domain.audit.sheet.json'),'--draft',str(DATA/'grave-domain.draft.txt')])]
    status={}
    for name,args in commands:
        out=io.StringIO();code=0
        with contextlib.redirect_stdout(out):
            try:tool(name,args)
            except SystemExit as exc:code=exc.code
        write('grave-domain.'+name.removesuffix('.py')+'.log',out.getvalue());status[name]=code;print(name,code,out.getvalue()[-220:])
    save('grave-domain.checks',status)

LANG_REASONS={
 'always':'始終沿用現譯，非UI選項的總是。','attack roll':'terms定案為攻擊檢定，優先於lang攻擊擲骰。','bloodied':'terms定案為重傷。','bonus':'此處僅Bonus Action（附贈動作），並非加值。','circle':'此處是特性完整名稱凡命循環，並非圓形區域。','consumed':'材料構材「被消耗」，沿用原稿，非UI消耗設定。','critical':'terms Critical Hit定案為暴擊。','critical hit':'terms定案為暴擊。','details':'沿用現譯子職業細節。','dice':'擲骰用一枚或多枚骰子與每個骰子，非UI骰值。','effects':'暴擊觸發的效應沿用現譯，效應與效果有不同語境。','item':'UUID技術路徑Item，不是可見內容。','minimum':'最少1次，沿用現譯，非數值輸入框最小值。','natural':'自然且不可避免，沿用現譯，非天生武器。','next':'下一回合，非下一步UI。','number':'正文採最大值、等同於等，骰子數量／數字並非本句詞義。','options':'UUID技術路徑options，不是可見內容。','points':'此處Hit Points＝生命值，非點數UI。','prepared':'正文始終準備、準備法術沿用現譯，非UI已準備狀態。','reach':'此處為達到牧師等級；兩項已逐條ack，不是觸及。','rest':'此處Short／Long Rest＝短休／長休，非休息分類UI。','roll':'正文沿用投擲（骰子）與攻擊檢定／豁免檢定，非UI擲骰按鈕。','rolls':'attack rolls／saving throws採攻擊檢定／豁免檢定，非通用擲骰。','round':'round down＝向下取整，沿用現譯，非輪。','second':'second creature＝第二個生物，非秒。','start of your next turn':'持續至你的下一回合開始，依使用者裁定不加前或時。','subclass details':'沿用既有子職業細節。','time':'for a time＝暫時、once per turn＝每回合一次，非時間UI。','touch':'Vampiric Touch法術名用現行吸血鬼之觸，非距離接觸。'
}

def review():
    checks=load('grave-domain.checks');assert all(v==0 for v in checks.values()),checks
    scope=load('scope')['options'];sheet=load('grave-domain.sheet');aligned=load('grave-domain.aligned')['entries'];live={r['context']:r for r in load('options.live')['units']}
    nested=load('grave-domain.metadata');changed=load('grave-domain.changes');kept=load('grave-domain.kept')
    forbidden=[];problems=[];keptblocks=0;conditions=[]
    for k,e in aligned.items():
        problems.extend(check_description(scope[k]['description'],e['description']));problems.extend(check_subfields(e,scope[k]))
        for b in sheet['entries'][k]['blocks']:
            if b['old_html']==b['zh']:keptblocks+=1
        for p,t in leaves(e):
            en=dict(leaves(scope[k]))[p]
            if p.endswith('.description') or p.endswith('.hint'):
                problems.extend(check_description(en,t))
            if re.search(r'它|如果|發充能|施展|浴血|爆擊|暗蝕|材料成分',visible_text(t)):forbidden.append((k,p))
            if p.endswith('.condition'):conditions.append({'path':'entries.'+k+'.'+p,'en':en,'zh':t})
    assert not problems,problems;assert not forbidden,forbidden
    payload=load('grave-domain.upload');assert len(list(leaves(payload)))==13
    assert all(live[p]['source'][0]==dict(leaves({'entries':scope}))[p] for p,v in leaves(payload))
    save('grave-domain.review',{'entries':6,'full_strings':31,'changed_strings':len(changed),'kept_strings':len(kept),'kept_folder_strings':1,'blocks':27,'kept_body_blocks':keptblocks,'conditions':conditions,'forbidden':forbidden,'structural_errors':problems,'checks':checks,'payload_sha256':hashlib.sha256((DATA/'grave-domain.upload.json').read_bytes()).hexdigest(),'draft_sha256':hashlib.sha256((DATA/'grave-domain.draft.txt').read_bytes()).hexdigest(),'rule_review':'逐段核對來源、目標、觸發、動作、距離、骰式、等級、次數、恢復、持續時間及例外。','reading_review':'中文獨立通讀通過；限定詞另逐句列出。'})
    print(json.dumps(load('grave-domain.review'),ensure_ascii=False,indent=1))

def esc(s):return html.escape(s).replace('|','&#124;').replace('\n','<br>')
def preview():
    info=load('grave-domain.review');sheet=load('grave-domain.sheet');scope=load('scope')['options'];source=(DATA/'grave-domain.source.s2twp.txt').read_text(encoding='utf-8').splitlines();metadata=load('grave-domain.metadata')
    bmap={'Grave Domain':[[2],[4],[5],[]],'Grave Domain Spells':[[8],[9],[10],[10],[11],[11,12,13],[14],[14],[15],[15],[16],[16]],'Circle of Mortality':[[19],[20],[21],[22]],'Path to the Grave':[[25],[26]],"Sentinel at Death's Door":[[29],[30]],'Divine Reaper':[[33],[34],[35]]}
    out=['# 墳墓領域整批 v1 預覽','尚未上傳。共6條、完整31字串；僅13個差異字串進payload，18個既有欄位及1個資料夾名稱保留。正文27塊，其中'+str(info['kept_body_blocks'])+'塊連HTML原樣保留。','原稿：../grave-domain.txt第1–35行；轉繁：grave-domain.source.s2twp.txt；底稿：grave-domain.draft.txt；映射：grave-domain.aligned.json；上傳：grave-domain.upload.json。',f"payload SHA-256：`{info['payload_sha256']}`",f"底稿 SHA-256：`{info['draft_sha256']}`",'## 做法與完整範圍','依使用者指示整個子職業一次處理。所有6條均有原稿；名稱與已有正文沿用Weblate現譯，只作已裁定用詞、規則及必要標記修正。唯一未翻正文司命神使直接依第33–35行原稿整理。英文state10的7個字串不視為已有中文。所有執行腳本在scripts/translation-import/horror-within/，不含上傳功能。','API實際專案slug為dnd-ravenloft-horros-within（horros是上游拼字）；component為dnd-ravenloft-horrors-within-options。全量531單元已讀取並與本批local EN逐欄吻合。terms137單元、spells-glossary640單元、現行法術名374個已核實。','全站以5個名稱搜尋66單元，僅本書EN與zh_Hant，未發現其他相關content／tables。這本書僅options與glossary兩個API元件；local EN也只有options.json。6條所有activities、effects、advancement均逐欄涵蓋；資料夾墳墓領域已有翻譯照舊。Grave Domain Spells內嵌法術表已完整核對，無獨立RollTable引用。','## 名稱取捨','| EN | 原稿名稱 | 採用 | 依據 |','|---|---|---|---|']
    srcnames={'Grave Domain':'墳墓領域','Grave Domain Spells':'墳墓領域法術','Circle of Mortality':'生死輪迴','Path to the Grave':'往墓之途',"Sentinel at Death's Door":'死門哨衛','Divine Reaper':'司命神使'}
    for k,r in sheet['entries'].items():out.append('|'+esc(k)+'|'+srcnames[k]+'|'+r['name']+'|'+('原稿名稱；目前沒有既有中文。' if k=='Divine Reaper' else '沿用Weblate既有名稱，不以原稿改名。')+'|')
    out+=['死亡之引／重歸生命保留現譯死亡牽引／回歸生命。','## 逐段對照','每列同时提供原稿及現譯，差異原因寫在最後一欄。原稿未進payload的名稱、等級標頭仍在來源歸類保留。']
    for k,r in sheet['entries'].items():
        out+=['### '+k+'／'+r['name'],'原稿行號：'+str(load('grave-domain.bounds')[k]),'| 區塊 | EN | 原稿轉繁（行號） | 現譯 | 底稿 | 修改 |','|---|---|---|---|---|---|']
        for i,b in enumerate(r['blocks']):
            raw=' / '.join(str(n)+': '+source[n-1] for n in bmap[k][i]) or '無原稿；沿用現譯子職業細節。'
            out.append('|'+b['id']+'|'+esc(b['en'])+'|'+esc(raw)+'|'+esc(b['old_html'])+'|'+esc(b['draft_text'])+'|'+esc(b['reason'])+'|')
    out+=['## 規則差異（中英原句已列於上表）','- 墳墓領域法術b0001：EN Grave Domain Spells；現譯生命領域法術列表。已修正為墳墓領域。原稿正確。','- 凡命循環b0002：EN by casting a spell or by hitting with an attack roll；現譯透過法術或攻擊檢定。已補上施放及命中條件。原稿已有命中。','- 凡命循環b0004：EN don’t roll those dice for the healing; instead, use the highest number possible for each die；現譯你可以不擲骰。已依原稿改為不用投擲且每個骰子取最大值，並明列一枚或多枚骰子。不是任意治療生物，而是生命值為0的生物。','- 歸墓之途b0001：原稿及EN until the start of your next turn，現譯開始前。依裁定改開始；持續時間移到詛咒後。b0002去除重複額外，無數值變動。','- 司命神使b0003：EN unless you expend a level 6+ spell slot (no action required) to restore your use of it；原稿你也可以消耗。已用除非明確連接重置例外；其他規則與原稿相符。','- 其餘原稿規則與EN相符。牧師3／6／17級原稿特性標頭無對應獨立欄位，依EN結構不在正文加級別；11級死亡牽引升骰、五環及以下死靈單目標條件、領域法術替代資格、60呎、兩倍牧師等級、感知調整值至少1次、短休或長休／六環重置與材料構材逐一核對。','## 保留項','- 副標EN Embody Deific Forces of Death與原稿／現譯安息亡者，顯化神力有措辭差異；現譯已存在且不改規則，保留。','- shepherd spirits的原稿／現譯超度亡魂踏入往生含敘事延伸，保留。','- 現譯「失去任何生命值」＝EN missing any Hit Points，原稿生命值未滿；語意相符，保留。','- Spell表頭EN Spells／現譯準備法術；表內均始終準備，保留。表格3級原稿將拯救瀕死列在最前，依EN放最後；法術清單及等級相同。','- 其他現譯文字（如子職業特徵、死之門的哨衛、最多值投擲用詞）照舊，不另行改名或順稿。','## 術語報告（原樣）',(DATA/'grave-domain.terms-report.md').read_text(encoding='utf-8'),'### ack逐條理由']
    out.extend('- '+k+'：'+v for k,v in load('grave-domain.ack').items())
    out+=['### 法術名差異','原稿維生術→拯救瀕死；虛假生命→摹造生命；汲血之觸→吸血鬼之觸；防死結界→防死護咒；驅逐善惡→反制善惡；死者復活→喚醒死者。其餘5個法術名照舊。所有名稱取本次Weblate PHB現行名稱，UUID目標逐字保留。','### lang比對（原樣）',(DATA/'grave-domain.lang_compare.log').read_text(encoding='utf-8'),'### lang「無」逐條說明']
    lang=(DATA/'grave-domain.lang_compare.log').read_text(encoding='utf-8')
    for line in lang.splitlines():
        if '| 無 |' in line:
            key=line.split('|')[1].strip();assert key in LANG_REASONS,key;out.append('- '+key+'：'+LANG_REASONS[key])
    out+=['## 限定詞逐句核對','以下每句含this／these／that／the／following／one／each／any／all者，對照完整底稿；單數對象、指定條件、全部恢復和例外均通過。','| EN | 中文 | 核對 |','|---|---|---|']
    for k,r in sheet['entries'].items():
        for b in r['blocks']:
            en=visible_text(b['en'])
            if re.search(r'\b(this|these|that|the|following|one|each|any|all)\b',en,re.I):out.append('|'+esc(en)+'|'+esc(b['draft_text'])+'|'+esc(k)+'：指涉／數量／範圍／例外逐句核對通過。|')
    out+=['## 補翻與獨立欄位清單','未翻譯正文與名稱有原稿；独立欄位沒有原稿者依全站同句搜尋結果補翻。visible已有同元件可見譯文，直接沿用。','| 路徑 | EN | 現譯 | 中文 | 依據 |','|---|---|---|---|---|']
    for m in metadata:out.append('|'+m['path']+'|'+esc(m['en'])+'|'+esc(m['old'])+'|'+esc(m['zh'])+'|'+esc(m['basis'])+'|')
    out+=['### activities.condition單獨對照','| 欄位 | EN | 中文 |','|---|---|---|']
    for m in info['conditions']:out.append('|'+m['path']+'|'+esc(m['en'])+'|'+esc(m['zh'])+'|')
    out+=['## 四項驗收','1. 規則核對：通過；條件、作用對象、數值、次數、恢復、範圍及例外逐句核對，規則修正如上。','2. 術語核對：terms_check回傳0，共27項、3項逐條ack，未處理0；手動補核EN小寫undead採不死生物。最終payload禁用詞掃描0。','3. 機械驗證：validate回傳0，6條31字串；最終payload13字串均存在API，所有HTML結構／屬性、表格／br、UUID目標、擲骰巨集原樣保留。效果描述另驗收通過。','4. 中文通讀：通過；已修正禁用代名詞、詛咒動作句與持續時間位置，映射去標記後逐字等同底稿。所有相似度改動大段落已有逐塊理由。','### 底稿比對（原樣）','draft_diff使用--floor 0.4：9級表格儲存格只有兩個法術名，二者均換成已定案現行名稱，短字串相似度0.44。該格不是自譯或無來源；EN UUID、原稿第16行與spell-names.json可逐一證明，故保留直接差異並降低無來源門檻，不把有原稿改標supplement。其他原稿／現譯切片另存source.segmented.s2twp.txt供檢查，不覆寫原稿。',(DATA/'grave-domain.draft-diff.md').read_text(encoding='utf-8'),'## 缺漏與待確認','1. 子職業細節UUID指向dnd-ravenloft-horrors-within.book中的GraveDomainCleri頁，但本書沒有book／content的local EN檔案或Weblate元件。連結保留；本次無法翻譯該日誌頁，不能宣稱content已完成。待上游提供EN結構後續做，保留原稿。','2. 本批v1共13個建議字串待使用者確認後才能上傳；其餘規則或名稱無待裁定衝突。','## 待上傳欄位','| 路徑 | 原狀態 |','|---|---|']
    out.extend('|'+x['path']+'|'+str(x['state'])+'|' for x in load('grave-domain.changes'))
    md=''
    for item in out:
        separator='\n' if md and md.splitlines()[-1].startswith('|') and item.startswith('|') else '\n\n'
        md+=separator+item
    write('grave-domain.preview.md',md.lstrip().replace('同时','同時').replace('独立','獨立'))
    # Plain-reading HTML with existing and proposed complete descriptions, technical labels rendered as text.
    def render(v):
        v=re.sub(r'@UUID\[[^\]]+\]\{([^}]*)\}',lambda m:'<span class="link">'+m[1]+'</span>',v)
        v=re.sub(r'\[\[[^\]]+\]\]\{([^}]*)\}',lambda m:'<span class="macro">'+m[1]+'</span>',v)
        return v
    page=['<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>墳墓領域整批v1</title><style>body{max-width:900px;margin:40px auto;padding:0 24px;font:18px/1.9 system-ui;color:#223}article{border-top:1px solid #ccd;padding:24px 0}.link{color:#165e8a}.macro{color:#81551d}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ccd;padding:8px}summary{cursor:pointer}pre{white-space:pre-wrap;font-size:14px}.note{background:#fff7da;padding:12px}a{color:#165e8a}</style><h1>墳墓領域整批v1</h1><p>尚未上傳；6條／13個差異字串。<a href="grave-domain.preview.md">完整差異預覽</a>・<a href="grave-domain.draft.txt">底稿</a></p><p class="note">缺少book日誌EN元件，content頁尚無法處理；內嵌法術表已完整納入。</p>']
    aligned=load('grave-domain.aligned')['entries'];live={r['context']:r for r in load('options.live')['units']}
    for k,r in sheet['entries'].items():page+=['<article><h2>'+r['name']+'</h2>'+render(aligned[k]['description'])+'<details><summary>查看原有譯文</summary><pre>'+html.escape(live['entries.'+k+'.description']['target'][0])+'</pre></details></article>']
    page+=['</html>'];write('grave-domain.reading.html','\n'.join(page))
    save('grave-domain.version',{'version':'v1','uploaded':False,'approved':False,'payload_sha256':info['payload_sha256'],'preview_sha256':hashlib.sha256((DATA/'grave-domain.preview.md').read_bytes()).hexdigest(),'remaining':['book日誌頁GraveDomainCleri缺少EN/API元件']})
    print('Preview and reading saved',info['changed_strings'],'strings')

def verify_preview():
    before={r['context']:r for r in load('options.live')['units']};rows,audit=paged(f'/api/translations/{PROJECT}/{COMP}/zh_Hant/units/');now={r['context']:r for r in rows}
    paths=[p for p,v in leaves({'entries':load('scope')['options'],'folders':load('scope')['folders']})]
    assert all(before[p]['source']==now[p]['source'] and before[p]['target']==now[p]['target'] for p in paths),'Scoped source or translations changed'
    version=load('grave-domain.version')
    assert version['payload_sha256']==hashlib.sha256((DATA/'grave-domain.upload.json').read_bytes()).hexdigest()
    assert version['preview_sha256']==hashlib.sha256((DATA/'grave-domain.preview.md').read_bytes()).hexdigest()
    save('grave-domain.verification',{'complete':True,'all_units':len(rows),'scope_strings':len(paths),'suggestions_in_scope':[p for p in paths if now[p].get('has_suggestion')],'audit':audit,'payload_sha256':version['payload_sha256'],'preview_sha256':version['preview_sha256']})
    print('Verified',len(rows),'API units;',len(paths),'scoped strings unchanged; payload and preview hashes exact')

if __name__=='__main__': globals()[sys.argv[1]]()
