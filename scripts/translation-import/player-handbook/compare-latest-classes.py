"""Read-only comparison of workspace classes, Git baseline and current Weblate EN.

Writes review artifacts only. Does not update source files or publish translations.
"""
import argparse, collections, datetime, difflib, hashlib, html, json, re, subprocess, sys
from pathlib import Path
from subclasses import read_all, leaves

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'_incoming/player-handbook/subclasses/world-tree'
PREFIX='subclasses.world-tree.3'
BOOK='dnd-players-handbook'
FILE=ROOT/f'compendium/en/{BOOK}/{BOOK}.classes.json'
sys.path.insert(0,str(ROOT/'.claude/skills/translation-import/scripts'))
from html_blocks import Plan

def save(suffix,value):
    DATA.mkdir(parents=True,exist_ok=True)
    (DATA/(PREFIX+'.'+suffix+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=1),encoding='utf-8')
def write(suffix,value):(DATA/(PREFIX+'.'+suffix)).write_text(value.rstrip()+'\n',encoding='utf-8')
def read(suffix):return json.loads((DATA/(PREFIX+'.'+suffix+'.json')).read_text(encoding='utf-8-sig'))
def link(suffix,label):return '['+label+']('+str(DATA/(PREFIX+'.'+suffix)).replace('\\','/')+')'
def plain(value):
    value=re.sub(r'@UUID\[[^\]]+\]\{([^}]+)\}',r'\1',value)
    value=re.sub(r'&(?:amp;)?Reference\[([^\]]+)\]',lambda m:re.sub(r'\s+\w+=\S+','',m[1]),value)
    return html.unescape(re.sub('<[^>]+>','',value)).strip()
def notes(value):
    m=re.search(r'<section\b[^>]*\bclass="secret"[^>]*>(.*?)</section>',value,re.S)
    return [b.html for b in Plan(m[1]).blocks if plain(b.html)!='Foundry Note'] if m else []
def without_notes(value):return re.sub(r'<section\b[^>]*\bclass="secret"[^>]*>.*?</section>','',value,flags=re.S)
def chinese(value):return bool(re.search('[\u3400-\u9fff]',value))

# Comparison-only glosses; they are never used to populate a translation payload.
NOTE_ZH={
 'Aquatic Affinity':(['發散區域的大小會自動增加，但此特性不會自動加入游泳速度。'],[]),
 'Aspect of the Wilds':(['此特性包含一個行動，其中的Active Effect會自動套用梟選項帶來的黑暗視覺變化。速度變化不會自動套用。'],[]),
 'Avatar of Battle':(['此特性包含一項Active Effect，可自動套用傷害抗力。'],[]),
 'Blessing of the Trickster':(['此特性包含一項Active Effect，用於追蹤祝福，但不會自動套用隱匿檢定的優勢，也不會在你再次使用此特性時自動結束。'],[]),
 'Disarming Attack':(['此特性會自動使用你的力量與敏捷中較高者進行豁免。','豁免中的傷害可讓你在擲骰對話框中選擇傷害類型，並會記住你之後的選擇。'],[]),
 'Disciplined Survivor':(['當你升級時，系統會自動賦予你額外的豁免熟練。','使用此特性來消耗1點專注點數。'],['使用此特性來消耗1點專注點數。']),
 'Divine Fury':(['此特性為每種傷害類型各提供一個行動。'],[]),
 'Divine Order: Protector':(['此特性包含一項Active Effect，會賦予該熟練與護甲訓練。'],[]),
 'Dreadful Strikes':(['傷害行動包含額外傷害，並會隨你升級自動調整。'],[]),
 'Eldritch Hex':(['當你升級時，此法術會自動加入你的角色表。'],[]),
 'Favored Enemy':(['你在此等級獲得該法術，免費使用次數會隨你升級自動增加。'],[]),
 'Frenzy':(['傷害行動會隨你升級自動調整，且可讓你在傷害擲骰的對話框中選擇傷害類型。此後會記住你的選擇。'],[]),
 'Goading Attack':(['此特性包含依你的力量或敏捷進行豁免的行動。你可以使用句內傷害擲骰或傷害行動來擲出額外傷害。','傷害行動可讓你在擲骰對話框中選擇其傷害類型。'],[]),
 'Investment of the Chain Master':(['具有飛行與具有游泳的Find Familiar行動，都可讓你召喚具有對應移動加值的魔寵。兩個行動都消耗一個契約魔法法術位。','Invest with Resistance行動包含對應各種傷害類型的Active Effect，可套用以獲得相應抗力。當你更換抗力時，請在角色表的效果分頁停用或刪除先前的Active Effect。','魔寵會自動使用你的豁免DC。'],['Find Familiar行動會同時將飛行與水生效果套用到召喚的生物上。可以刪除生物身上未使用的效果。','Resistance行動包含用於抵抗各種傷害類型的可選Active Effect。']),
 'Menacing Attack':(['此特性包含力量豁免與敏捷豁免行動，會消耗一次你的卓越骰使用次數。','傷害行動可讓你在擲骰對話框中選擇其傷害類型。'],[]),
 "Nature's Ward":(['此特性包含一項用於中毒狀態免疫的Active Effect，以及對應每種土地類型的Active Effect。你可以啟用對應所選土地類型的Active Effect。'],['此特性包含對應每種土地類型的Active Effect。你可以啟用對應所選土地類型的Active Effect。']),
 'Primal Order: Warden':(['此特性包含一項Active Effect，會自動加入你的軍用武器熟練與中甲訓練。'],[]),
 'Pushing Attack':(['此特性包含力量豁免與敏捷豁免行動，會消耗一次你的卓越骰使用次數。','傷害行動可讓你在擲骰對話框中選擇其傷害類型。'],[]),
 'Rage of the Gods':(['眾神之怒行動包含一項Active Effect，會自動加入抗力與懸浮，但不會提供飛行速度。','Revivification行動包含等同於你野蠻人等級的治療擲骰。'],['眾神之怒行動包含一項Active Effect，會自動加入抗力、懸浮與飛行速度。','Revivification行動包含等同於你野蠻人等級的治療擲骰。']),
 'Revelation in Flesh':(['Expend Sorcery Points行動可讓你選擇要消耗的術法點數。此行動包含對應各選項的Active Effect，可用於追蹤，但不會自動套用其變化。'],['Expend Sorcery Points行動可讓你選擇要消耗的術法點數。']),
 'Roving':(['此特性包含一項Active Effect，會使你的速度增加10呎，但不會自動賦予相等的攀爬速度與游泳速度。若你選擇穿戴重甲，可以停用此效果。'],['此特性包含一項Active Effect，若你穿戴重甲，可以停用此效果。']),
 'Shadow Arts':(['Expend Focus Point行動會消耗一次使用次數，之後你便可使用在此等級獲得的[[/item Darkness]]法術。','此特性包含一項Active Effect，會增加你的黑暗視覺。','你達到此等級時，會獲得Minor Illusion法術。'],[]),
 'Stormborn':(['你可以使用此特性取代海之怒。此特性包含一項Active Effect，會自動加入抗力，但不會加入飛行速度。'],['你可以使用此特性取代海之怒。此特性包含一項Active Effect，會自動加入抗力與飛行速度。']),
 'Stride of the Elements':(['此特性不會自動賦予飛行速度與游泳速度。'],['這些變化由你的四象同調特性處理。']),
 'Tandem Footwork':(['使用此特性會消耗一次你的吟遊激勵使用次數。'],[]),
 'Telekinetic Adept':(['Psi-Powered Leap行動包含一次免費使用，你也可以透過Psi-Powered Leap Using Psionic Energy行動消耗一枚靈能骰再次使用。此行動不會自動加入飛行速度。','Telekinetic Thrust行動包含一項Active Effect，可使目標陷入伏地狀態。'],['Psi-Powered Leap行動包含一次免費使用，你也可以透過Psi-Powered Leap Using Psionic Energy行動消耗一枚靈能骰再次使用。','Telekinetic Thrust行動包含一項Active Effect，可使目標陷入伏地狀態。']),
 'Trip Attack':(['此特性會自動使用你的力量與敏捷中較高者進行豁免。','豁免中的傷害可讓你在擲骰對話框中選擇傷害類型，並會記住你之後的選擇。'],[]),
 'Unarmored Movement':(['此特性包含一項無甲移動Active Effect，會使你的移動增加10呎，但無法隨你升級自動更新。你可以編輯其數值，使其符合當前增加量。'],[]),
 'War Domain Spells':(['當你提升等級時，會自動獲得這些法術。'],[]),
 "War God's Blessing":(['施放此法術時，取消勾選Consumption與Concentration核取方塊。'],[]),
 'Warrior of the Gods':(['此資源池的大小會由這項特性的比例值升級自動處理。'],[]),
}
MAIN_ZH={
 'Arcane Recovery':('可用的總環數：[[(@classes.wizard.levels / 2)]]','可用的總環數：[[ceil(@classes.wizard.levels / 2)]]','加入ceil，明確向上取整；規則正文原本就寫round up。'),
 'Fanatical Focus':('每次啟用的狂暴期間僅一次，若你豁免失敗，你可以重擲，並獲得等同於你狂暴傷害加值的加值（目前為[[/r @scale.barbarian.rage-damage]]），且必須使用新的擲骰結果。','每次啟用的狂暴期間僅一次，若你豁免失敗，你可以重擲，並獲得等同於你狂暴傷害加值的加值（目前為[[@scale.barbarian.rage-damage]]），且必須使用新的擲骰結果。','移除/r並加入hide-in-embed；重擲條件、次數與加值規則相同。'),
 'Inspiring Movement':('當位於你5呎內一名你所能看見的敵人結束其回合時，你可以採取反應並消耗一次吟遊激勵，移動至多等同於你速度一半的距離（目前為[[lookup @attributes.movement.walk]]）。隨後，位於你30呎內一名你所選擇的盟友也可以使用其反應，移動至多等同於其速度一半的距離。','當位於你5呎內一名你所能看見的敵人結束其回合時，你可以採取反應並消耗一次吟遊激勵，移動至多等同於你速度一半的距離（目前為[[lookup @attributes.movement.speed]]）。隨後，位於你30呎內一名你所選擇的盟友也可以使用其反應，移動至多等同於其速度一半的距離。','巨集欄位walk→speed，並加入hide-in-embed；文字規則仍為half your Speed。'),
 "Land's Aid":('你可以採取一個魔法動作，消耗一次荒野形態的使用次數，並選擇位於你60呎內的一點。賦予生命的花朵與汲取生命的荊棘，在以該點為中心、半徑10呎的球形區域中短暫出現。球形區域內每個你所選擇的生物，必須對抗你的法術豁免DC進行體質豁免；失敗時承受2d6黯蝕傷害，成功時傷害減半。該區域內一名你所選擇的生物恢復[[lookup @scale.land.lands-aid]]點生命值。','你可以採取一個魔法動作，消耗一次荒野形態的使用次數，並選擇位於你60呎內的一點。賦予生命的花朵與汲取生命的荊棘，在以該點為中心、半徑10呎的球形區域中短暫出現。球形區域內每個你所選擇的生物，必須對抗你的法術豁免DC進行體質豁免；失敗時承受2d6黯蝕傷害，成功時傷害減半。該區域內一名你所選擇的生物恢復2d6點生命值。','治療連結由比例值改為[[/heal]]{2d6 Hit Points}；後段10級3d6、14級4d6仍在，不能把規則解讀成所有等級固定2d6。'),
 "Physician's Touch":('【奪命之手】當你對一名生物使用奪命之手時，你也可以使該生物陷入中毒狀態，持續至你的下個回合結束。','【奪命之手】當你對一名生物使用奪命之手時，你也可以使該生物陷入中毒狀態，持續至你的下個回合結束。','中毒文字改為Reference[Poisoned apply=false]；規則與持續時間相同。'),
 'Shadow Arts':('【幽影幻象】你知曉Minor Illusion法術。感知是你施放該法術的施法屬性。','【幽影幻象】你知曉Minor Illusion法術。感知是你施放該法術的施法屬性。','Minor Illusion新增UUID連結；刪除Foundry註記。正式法術名留待對應匯入批次核實，這裡只作版本比較。'),
 'Stunning Strike':('每回合一次，當你以武僧武器或徒手打擊命中一名生物時，你可以消耗1點專注點數，嘗試施以震懾拳。目標必須進行體質豁免。若豁免失敗，目標陷入震懾狀態，持續至你的下個回合開始。若豁免成功，目標的速度減半，持續至你的下個回合開始，且在此之前對目標進行的下一次攻擊檢定具有優勢。','每回合一次，當你以武僧武器或徒手打擊命中一名生物時，你可以消耗1點專注點數，嘗試施以震懾拳。目標必須進行體質豁免。若豁免失敗，目標陷入震懾狀態，持續至你的下個回合開始。若豁免成功，目標的速度減半，持續至你的下個回合開始，且在此之前對目標進行的下一次攻擊檢定具有優勢。','震懾文字改為Reference[Stunned apply=false]；規則相同。'),
 'Unarmored Movement':('當前增加量：[[lookup @scale.monk.unarmored-movement]]','當前增加量：[[lookup @scale.monk.unarmored-movement]]','Current Increase段落新增hide-in-embed；刪除舊Foundry註記。'),
 'Rage of the Gods/effect':('【復甦】當位於你30呎內的一名生物將降至0點生命值時，你可以採取反應，消耗一次狂暴的使用次數，改使目標的生命值等同於你的野蠻人等級。','此效果摘要移除復甦段落；特性正文仍保留該完整段落。','只從效果摘要移除，不能據此刪除正文的復甦能力。'),
}

def compare(refresh=False):
    latest_bytes=FILE.read_bytes();new=json.loads(latest_bytes.decode('utf-8-sig'))
    head_commit=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    if refresh:
        rows,audit=read_all(BOOK,BOOK+'-classes')
        save('latest-classes.live',{'audit':audit,'units':{r['context']:r for r in rows}})
    live=read('latest-classes.live')['units'] if (DATA/(PREFIX+'.latest-classes.live.json')).exists() else read('classes.live')['units']
    refs=subprocess.run(['git','log','-10','--format=%H','--',FILE.relative_to(ROOT).as_posix()],cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines()
    # The user may commit the new source while this review is running. Pin the
    # baseline to a historical EN file matching the current API, rather than HEAD.
    old=None
    for ref in refs:
        candidate_bytes=subprocess.run(['git','show',ref+':'+FILE.relative_to(ROOT).as_posix()],cwd=ROOT,capture_output=True,check=True).stdout
        candidate=json.loads(candidate_bytes);fields={p:v for p,v in leaves(candidate) if not p.startswith('mapping.')}
        if set(fields)==set(live) and all(live[p]['source']==[v] for p,v in fields.items()):
            old=candidate;old_bytes=candidate_bytes;baseline_commit=ref;break
    assert old is not None,'No historical template matches the API; preserve snapshots and review the baseline'
    before=dict(leaves(old));after=dict(leaves(new))
    changed=[{'path':p,'old':before[p],'new':after[p],'current_zh':live.get(p,{}).get('target',[''])[0]} for p in sorted(before.keys()&after.keys()) if before[p]!=after[p]]
    added={p:after[p] for p in sorted(after.keys()-before.keys())};removed={p:before[p] for p in sorted(before.keys()-after.keys())}
    migrations=[{'old_path':p,'new_path':p.removesuffix('.title')+'.name','en':v,'current_zh':live[p]['target'][0]} for p,v in removed.items() if p.endswith('.title') and added.get(p.removesuffix('.title')+'.name')==v]
    old_m={r['old_path'] for r in migrations};new_m={r['new_path'] for r in migrations}
    technical=[p for p in added if p.startswith('mapping.')]
    old_core=[p for p in before if not p.startswith('mapping.')];new_core=[p for p in after if not p.startswith('mapping.')]
    rootkeys=set(new['entries'])-set(old['entries']);lostkeys=set(old['entries'])-set(new['entries'])
    checks={'api_matches_git_baseline':set(live)==set(old_core) and all(live[p]['source']==[before[p]] for p in old_core),'api_changed_sources':sum(p in live and live[p]['source']!=[v] for p,v in after.items() if not p.startswith('mapping.')),'api_missing_new_paths':sum(p not in live for p in new_core),'api_obsolete_paths':sum(p not in after for p in live),'file_unchanged_during_comparison':FILE.read_bytes()==latest_bytes}
    assert checks['file_unchanged_during_comparison']
    results={'file':str(FILE),'checked_at':datetime.datetime.now().astimezone().isoformat(),'head_commit':head_commit,'baseline_commit':baseline_commit,'old_sha256':hashlib.sha256(old_bytes).hexdigest(),'latest_sha256':hashlib.sha256(latest_bytes).hexdigest(),'old_strings':len(old_core),'new_strings':len(new_core),'technical_mapping_strings':len(technical),'changed_count':len(changed),'added_count':len(added)-len(technical),'removed_count':len(removed),'unchanged_count':sum(before[p]==after[p] for p in before.keys()&after.keys()),'title_name_migrations':len(migrations),'added_entry_keys':sorted(rootkeys),'removed_entry_keys':sorted(lostkeys),'checks':checks,'changed':changed,'added':added,'removed':removed,'migrations':migrations}
    save('latest-classes-comparison',results);save('latest-classes.baseline-en',old);save('latest-classes.workspace-en',new)
    full=['# classes.json 新舊全檔差異','', '2026-10-09。比對工作區現行檔、與Weblate一致的Git舊版與Weblate現行英文；本報告只比較，沒有上傳或修改任何翻譯。中文對照供理解版本變更，並非已核准的匯入底稿。','',f'翻譯字串：{len(old_core)} → {len(new_core)}；原路徑改文{len(changed)}；新增{len(added)-len(technical)}；刪除{len(removed)}。另新增{len(technical)}個mapping技術設定字串，不算翻譯單元。','', '## 38個原路徑描述差異：完整英文與現行中文','']
    block_pairs=[]
    for i,r in enumerate(changed,1):
        key=r['path'].split('.')[1]
        full += [f'### {i}. {r["path"]}','', '**舊EN完整欄位：**','```html',r['old'],'```','', '**新EN完整欄位：**','```html',r['new'],'```','', '**Weblate現行完整中文（若混有英文，原樣列出）：**','```html',r['current_zh'],'```','']
        on,nn=notes(r['old']),notes(r['new'])
        if on!=nn:
            assert key in NOTE_ZH,key
            oz,nz=NOTE_ZH[key];assert len(on)==len(oz) and len(nn)==len(nz),(key,len(on),len(nn))
            full+=['**Foundry註記逐段中英文：**','']
            for state,enpars,zhpars in [('舊',on,oz),('新',nn,nz)]:
                if not enpars:full += [state+'：無此Foundry註記。','']
                for en,zh in zip(enpars,zhpars):
                    full += [state+' EN：'+plain(en),'',state+' 中：'+zh,''];block_pairs.append({'path':r['path'],'version':state,'en':plain(en),'zh':zh})
        if without_notes(r['old'])!=without_notes(r['new']):
            mk='Rage of the Gods/effect' if '.effects.' in r['path'] else key
            assert mk in MAIN_ZH,mk
            oz,nz,reason=MAIN_ZH[mk]
            ob=[b.html for b in Plan(without_notes(r['old'])).blocks];nb=[b.html for b in Plan(without_notes(r['new'])).blocks]
            full+=['**正文／效果／格式差異的完整句段：**','']
            for state,parts,other,zh in [('舊',ob,nb,oz),('新',nb,ob,nz)]:
                diffs=[p for p in parts if p not in other]
                if not diffs:full += [state+' EN：無對應段落。','']
                for en in diffs:full += [state+' EN：'+plain(en),'']
                full += [state+' 中：'+zh,''];block_pairs.append({'path':r['path'],'version':state,'en':'\n'.join(plain(p) for p in diffs),'zh':zh})
            full+=['判讀：'+reason,'']
        elif on!=nn:full+=['判讀：規則正文相同；變更位於Foundry註記。註記描述的自動化能力需隨新版資料使用，不沿用舊註記。','']
    full+=['## title → name：250個路徑逐一列出','','英文值未變，不是250句重譯；舊已接受中文可作新欄位的來源。必須以新版Weblate單元完成匹配後才送建議。','','| 舊路徑 | 新路徑 | EN | 現行中文 |','|---|---|---|---|']
    cell=lambda s:plain(s).replace('|','\\|').replace('\n','<br>')
    for r in migrations:full.append('| '+' | '.join(cell(r[k]) for k in ['old_path','new_path','en','current_zh'])+' |')
    full+=['','## 其餘新增／移除欄位（含行動、效果與技術設定）','','下列列出全部未歸入title→name的欄位。新增欄位尚未出現在目前Weblate；不是新名稱全部都要另譯，先匹配既有正文及舊路徑。同一段英文明文仍在，移除介面欄位不表示刪除該遊戲能力。','','| 類型 | 路徑 | 完整EN | 現行相關中文／說明 |','|---|---|---|---|']
    for state,rows,paired in [('新增',added,new_m),('移除',removed,old_m)]:
        for p,v in rows.items():
            if p in paired:continue
            key=p.split('.')[1] if p.startswith('entries.') else None
            matches=[r for path,r in live.items() if r['source']==[v] and chinese(r['target'][0]) and (not key or path.startswith('entries.'+key+'.'))]
            basis=matches[0]['target'][0] if matches else '未有可直接匹配的同條目中文；此處只作版本差異清單。'
            if p in live:basis=live[p]['target'][0]
            if p.startswith('mapping.'):basis='Babele技術設定，保留英文，不送翻譯。'
            full.append('| '+' | '.join(cell(x) for x in [state,p,v,basis])+' |')
    save('latest-classes-bilingual-differences',block_pairs)
    write('latest-classes-full-diff.md','\n'.join(full))
    review=['# 最新 classes.json 比對結果','', '2026-10-09；「最新版」指使用者目前工作區這份檔案，沒有推定其官方版本號。已比較整份檔案、與Weblate一致的Git舊版及重新讀取的Weblate來源。','', '**世界樹道途沒有規則正文更新；目前不能把效果摘要漏字當成新版已修正。**','',f'檔案：`{FILE}`。','',f'Git舊版基準：`{results["baseline_commit"]}`；目前HEAD：`{results["head_commit"]}`。','',f'新檔SHA-256：`{results["latest_sha256"]}`。','', '## 全檔統計','', '| 項目 | 數量 |','|---|---:|',f'| Weblate／Git舊翻譯字串 | {len(old_core)} |',f'| 工作區新翻譯字串 | {len(new_core)} |',f'| 原路徑內容變更 | {len(changed)} |',f'| 新增翻譯路徑 | {len(added)-len(technical)} |',f'| 移除舊路徑 | {len(removed)} |',f'| 其中title→name且EN值完全相同 | {len(migrations)} |',f'| 額外mapping技術字串（不翻譯） | {len(technical)} |','', '38個內容變更全部是description；另有Assasinate→Assassinate的條目拼字與路徑修正，以及新增Hex (Powerful)輔助條目。原路徑的name、condition、target沒有文字變更，不代表新版新增或改名的行動欄位沒有變更。','',f'Weblate重新讀取成功；全部{len(live)}個EN單元與Git舊版基準一致：`{checks["api_matches_git_baseline"]}`。新檔有{checks["api_missing_new_paths"]}個新路徑尚不在API，{checks["api_obsolete_paths"]}個舊路徑仍在API，{checks["api_changed_sources"]}個同路徑的英文來源尚未更新。','', '## 世界樹本批的逐欄結果','', '| 條目 | 本文、行動、效果 | advancement |','|---|---|---|']
    scope=['Path of the World Tree','Vitality of the Tree','Branches of the Tree','Battering Roots','Travel Along the Tree']
    for key in scope:
        diffs=[r for r in changed if r['path'].startswith('entries.'+key+'.')]
        adds=[p for p in added if p.startswith('entries.'+key+'.')];drops=[p for p in removed if p.startswith('entries.'+key+'.')]
        assert not diffs
        review.append('| '+key+' | 舊新文字完全相同 | '+('Subclass Features.title→Subclass Features.name，值仍為Subclass Features' if adds else '無變動')+' |')
    review+=['', '**效果摘要（舊、新完全相同）：**','', 'EN：'+plain(after['entries.Branches of the Tree.effects.Branches of the Tree.description']),'', '中：被靈樹枝杈移動的生物，其速度可以降至〔英文漏數值〕，持續至其當前回合結束。英文所有格亦錯置。','', '**完整正文依據（舊、新完全相同）：**','', 'EN：After the target teleports, you can reduce its Speed to 0 until the end of the current turn.','', '中：目標被传送後，你可以令其速度降為0，持續至當前回合結束。'.replace('传','傳'),'','**行動condition（舊、新完全相同）：**','','EN：'+after['entries.Branches of the Tree.activities.save.condition'],'','中：你的狂暴啟用期間，每當一名位於你30呎內你所能看見的生物的回合開始時。英文your Raging文法仍有錯字。','','補0的提案尚未裁定；使用者要求先核對新檔，不視為同意補字。','', '## 有實際影響的更新','', '1. advancement欄位由title改為name，共250個同值路徑。已有中文需遷移匹配，不能將舊title直接當新版name送入仍是舊版的Weblate。','2. 自動化說明更新：眾神之怒與風暴降生由「不提供飛行速度」改成會加入飛行速度；四象行步改由四象同調處理。這些是Foundry註記，不是刪改飛行能力的規則正文。','3. 奧術恢復的總環數巨集加入ceil向上取整；Inspiring Movement的讀取欄位由movement.walk改為movement.speed。','4. Land’s Aid治療由比例值連結改為顯示2d6；10級3d6、14級4d6的後段規則仍在，需保留等級增幅，不能照顯示文字誤譯成固定2d6。','5. 荒野之形的梟／豹／鮭三個舊行動名稱移除，新增Choose Aspect行動，以及豹、鮭的速度效果與說明。對上一批已送出的建議有路徑影響，正文的三種選項仍保留。','6. Hex (Powerful)新增智力、力量效果摘要只寫屬性檢定劣勢，其他四項寫檢定及豁免劣勢；Eldritch Hex正文仍寫所選屬性的豁免具有劣勢。這是新資料內部不一致，不能自行把智力／力量例外當成規則。','','**Hex新增效果疑義：完整中英文**','','智力、力量 EN：The target has Disadvantage on ability checks made with the chosen ability.','','中：目標以所選屬性進行屬性檢定時具有劣勢。','','魅力、體質、敏捷、感知 EN：The target has Disadvantage on ability checks and saves made with the chosen ability.','','中：目標以所選屬性進行屬性檢定與豁免時具有劣勢。','','Eldritch Hex正文 EN：When you cast Hex and choose an ability, the target also has Disadvantage on saving throws of the chosen ability for the duration of the spell.','','中：當你施放Hex並選擇一項屬性時，在法術持續期間，目標以該屬性進行的豁免也具有劣勢。','','## 已處理批次的影響','','狂戰士：Frenzy（狂怒）規則正文不變，新檔移除Foundry註記；子職業advancement的title→name。已送的舊建議需在新版來源同步後重新核對，不能沿用舊註記整段。','','狂野之心：Aspect of the Wilds（荒野之形）規則正文不變，但Foundry註記移除、三個行動路徑改動、新增豹／鮭效果。其餘已處理主文無本次規則更新；各advancement的title→name仍需匹配。','','野蠻人主職業：英文正文未變；advancement欄位改名，已完成中文優先沿用，不因欄位改名重譯。','','## 完整資料與本批狀態','', '- '+link('latest-classes-full-diff.md','完整38個描述的舊EN／新EN／現行中文及逐段中英文差異，全部新增／移除路徑清單'),'- '+link('latest-classes-comparison.json','全檔比對、數量與雜湊'),'- '+link('latest-classes-bilingual-differences.json','逐段中英文差異資料'),'- '+link('latest-classes.workspace-en.json','比對時的新EN快照'),'- '+link('latest-classes.baseline-en.json','Git舊EN快照'),'','世界樹本批保留原稿、底稿與術語檢查紀錄；之前依舊結構抽取的sheet需重抽。沒有產生可上傳的最終payload，沒有上傳，也沒有變更既有譯文或建議。下一步依新檔重抽本批結構，並將本次仍未修正的效果摘要列為待裁定。']
    issue_heading=review.index('## 已處理批次的影響')
    review[issue_heading:issue_heading]=[
        '## 其他新版操作說明疑義','',
        'Monk’s Focus新版已移除activities.Expend Focus Point.name，但Foundry註記仍要求使用該行動。這是本檔的欄位與操作說明不一致；實際行動是否由其他機制提供，還需看Foundry資料，不能僅憑翻譯檔判定功能失效。','',
        'EN：If your [[/item Unarmed Strike]] is impacted by other magic items, you can use the Expend Focus Point activity and then use your Unarmed Strike as usual.','',
        '中：若你的徒手打擊受到其他魔法物品影響，你可以使用Expend Focus Point行動，再照常使用你的徒手打擊。','',
        '移除欄位：entries.Monk\'s Focus.activities.Expend Focus Point.name。正式行動譯名留待對應批次核實，此處不修改既有內容。','',
    ]
    write('latest-classes-review.md','\n'.join(review))
    save('status',{'phase':'latest-classes-compared','approved':False,'uploaded':False,'import_preview_complete':False,'reason':'使用者先要求新版Class.json比對；世界樹本文相同，advancement結構已變；Weblate來源仍舊版。效果補0提案尚未裁定。','latest_sha256':results['latest_sha256'],'review':str(DATA/(PREFIX+'.latest-classes-review.md'))})
    print(json.dumps({k:v for k,v in results.items() if k not in ['changed','added','removed','migrations']},ensure_ascii=False,indent=1))
    print('BILINGUAL BLOCK PAIRS',len(block_pairs))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--refresh-live',action='store_true');args=parser.parse_args();compare(args.refresh_live)
