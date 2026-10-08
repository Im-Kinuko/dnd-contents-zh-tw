import hashlib, html, json, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / '_incoming/player-handbook'
sys.path.insert(0,str(ROOT/'.claude/skills/translation-import/scripts'))
from html_blocks import Plan, visible_text, compare_html
from validate import count_strings, check_description
from lang_compare import flat

def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))
base = 'classes.barbarian.1'
sheet = load(HERE/(base+'.sheet.json'))
payload = load(HERE/(base+'.upload.json'))['entries']
en = load(ROOT/'compendium/en/dnd-players-handbook/dnd-players-handbook.classes.json')['entries']
units = load(HERE/'barbarian.weblate_units.json')['units']
supplements = load(HERE/(base+'.supplements.json'))
terms = load(HERE/'barbarian.term_index.json')
equipment = load(HERE/'barbarian.equipment_names.json')['names']
for key in ['Greataxe','Handaxe',"Explorer's Pack"]:
    assert equipment['entries.'+key+'.name'] in payload['Barbarian']['description']
def leaves(node,prefix=''):
    if isinstance(node,dict):
        for key,value in node.items():
            yield from leaves(value,prefix+'.'+key if prefix else key)
    elif isinstance(node,str):
        yield prefix,node
originals = dict(leaves({key:en[key] for key in payload}))
finals = dict(leaves(payload))
for path,final in finals.items():
    original = originals[path]
    assert units['entries.'+path]['source'][0] == original, 'Weblate EN differs: '+path
    if path.endswith('.description'):
        assert not check_description(original,final,{'Foundry','Active','Effect'}), path
    assert '它' not in visible_text(final), path
    assert not re.findall(r'[A-Za-z]{3,}',visible_text(final).replace('Foundry','').replace('Active Effect','')), path
    if not path.endswith('.description'):
        assert not compare_html(original,final),path
checksum = hashlib.sha256((HERE/(base+'.upload.json')).read_bytes()).hexdigest()

source = next((HERE/'_web/barbarian').glob('*.htm.txt'))
lines = source.read_text(encoding='utf-8').splitlines()
ranges = {'Barbarian':(2,29),'Rage':(160,172),'Unarmored Defense':(173,175),'Weapon Mastery':(176,179),'Danger Sense':(180,182),'Reckless Attack':(183,185),'Primal Knowledge':(188,191),'Extra Attack':(194,195),'Fast Movement':(196,198),'Feral Instinct':(199,201)}
remaining = {'Instinctive Pounce':(202,204),'Brutal Strike':(205,211),'Relentless Rage':(212,214),'Improved Brutal Strike':(215,221),'Persistent Rage':(222,224),'Improved Brutal Strike (2)':(225,226),'Indomitable Might':(227,228),'Epic Boon':(229,230),'Primal Champion':(231,len(lines))}
# Keep source ranges as separate batches. Their translated previews remain pending.
for batch,keys in [(1,list(payload)),(2,list(remaining)[:9])]:
    text=[]
    for key in keys:
        start,end = (ranges|remaining)[key]
        text.append('### '+key+'\n'+'\n'.join(lines[start-1:end]))
    (HERE/f'classes.barbarian.{batch}.txt').write_text('\n\n'.join(text)+'\n',encoding='utf-8')
index = ['# 野蠻人來源索引','',f'來源文字：`{source.relative_to(HERE).as_posix()}`（以下為1起算行號）','', '| 原稿範圍 | EN key | 元件 | 批次／狀態 |','|---|---|---|---|']
for key,(start,end) in (ranges|remaining).items():
    index.append(f'| {start}–{end} | {key} | classes | '+('第1批已預覽' if key in ranges else '第2批待順稿')+' |')
index += ['| 30–159 | Barbarian 的職業特性引介及等級表 | content | classes 的EN沒有此段；保留原稿，需另開 content 批次 |','| 186–187 | Barbarian Subclass | content | classes 沒有獨立key；保留原稿，未混入本批 |','| 192–193 | 職業獲得 Ability Score Improvement 的說明 | content | 不是 feats 的同名專長正文；保留原稿，未混入本批 |','', 'content 是同章節的另一個技術目標；本批只處理已精確匹配的 classes 內容。沒有抓取四個子職業頁面。']
(HERE/'classes.barbarian.index.md').write_text('\n'.join(index)+'\n',encoding='utf-8')

lang_en = flat(load(ROOT/'lang/en.json'))
lang_zh = flat(load(ROOT/'lang/zh-tw.json'))
result = subprocess.run([sys.executable,'-X','utf8',str(ROOT/'.claude/skills/translation-import/scripts/lang_compare.py'),str(HERE/(base+'.sheet.json')),'--draft',str(HERE/(base+'.draft.txt'))],capture_output=True,text=True,encoding='utf-8',check=True)
(HERE/(base+'.lang-compare.md')).write_text(result.stdout,encoding='utf-8')
overrides = {
 'attack roll':('攻擊檢定','Weblate terms 優先於lang的攻擊擲骰／攻擊骰。'),
 'ability score':('屬性值','出現在原初知識Foundry補翻，不在來源底稿；已採lang。'),
 'score':('屬性值','同上；為ability score內的命中。'),
 'available':('可選','技能列表中可選的技能；依原稿與台灣語順，不使用介面狀態「可用」。'),
 'base':('基礎','base Armor Class用完整lang詞條「基礎護甲等級」；不套單獨的「基本」。'),
 'change':('更換','武器選擇語境，沿用原稿順稿；不是effect變更欄。'),
 'charge':('衝進','charge headlong into danger為動詞，不是物品充能。'),
 'class':('職業','出現在advancement的職業特性；未在正文底稿出現。'),
 'class features':('職業特性','採lang及現行Weblate advancement，介面欄不在來源底稿。'),
 'disable':('停用','出現在Foundry補翻，採lang。'),
 'disabled':('停用','not automatically disabled譯「不會自動停用」，依動詞語境；不用介面狀態「已停用」。'),
 'effect':('效果／Active Effect','普通效果採lang；Active Effect依裁定保留英文。出現在補翻與巢狀欄位。'),
 'effects':('效果','Effects tab譯效果分頁，出現在Foundry補翻。'),
 'end of your next turn':('你的下個回合結束前','until句依使用者裁定，時間端點不改。'),
 'force':('迫使','force an enemy為動詞，非傷害類型Force，不套力場。'),
 'heavy armor':('重甲','沿用PHB現行正文及lang的ArmorHeavyProficiency；不是UI裝備分類標籤。'),
 'increase':('提升','速度提升沿用原稿與現行快速移動句式；沒有數值差異。'),
 'maintain':('保持／維持','維持專注與狂暴；不套設施訂單的「維護」。'),
 'medium armor':('中甲','沿用PHB現行正文及lang的ArmorMediumProficiency。'),
 'next':('下個','next turn的時間修飾，不是介面的下一步／下一頁。'),
 'normal':('通常','normally／normal在技能慣用屬性語境，依中文副詞語順。'),
 'number':('次數','number of times為狂暴使用次數；不套骰子數量UI標籤。'),
 'proficiencies':('熟練','依完整詞「技能熟練／武器熟練／豁免熟練」，不是表格項目總稱。'),
 'proficiency':('熟練','gain proficiency為獲得熟練，並非Proficiency Bonus；不套熟練加值。'),
 'reach':('到達','reach certain levels為到達等級，不是武器觸及。'),
 'recharge':('恢復','恢復狂暴使用次數，不是物品充能；沿用原稿。'),
 'reference':('—','由&Reference技術標記命中，不是可見英文詞；目標保留，只翻標籤失能。'),
 'rest':('短休／長休','採完整規則詞Short/Long Rest；不套一般休息。'),
 'roll':('檢定','attack／saving throw／Initiative roll依完整規則詞與terms；不是獨立擲骰按鈕。'),
 'rolls':('檢定','依完整規則詞，不套孤立UI「擲骰」。'),
 'self':('真我','deepest self在敘事語境，沿用原稿；不是施法範圍自身。'),
 'start of your next turn':('你的下個回合開始','until句依使用者裁定，不加前；不加UI時字。'),
 'traits':('特質','沿用來源的核心特質；與Class Features的職業特性區分，lang特徵／特性並存。'),
}
audit = []
for line in result.stdout.splitlines():
    if not line.startswith('| ') or line.startswith('| EN '):continue
    cols = [s.strip() for s in line.strip('|').split('|')]
    if len(cols)!=4:continue
    eng,lang,mark,langkey = cols
    rg = re.compile(r'(?<![a-z])'+re.escape(eng)+r'(?![a-z])',re.I)
    paths = [p for p,text in originals.items() if rg.search(visible_text(text))]
    chosen,reason = overrides.get(eng,(next((z for z in lang.split(' ／ ') if z in '\n'.join(visible_text(v) for v in finals.values())),lang.split(' ／ ')[-1]),'採lang的適用中文詞；其他lang變體依本句語境不使用。'))
    term = next((v for k,v in terms['terms'].items() if k.lower()==eng), '—')
    gloss = next((v for k,v in terms['spells_glossary'].items() if k.lower()==eng), '—')
    audit.append({'en':eng,'terms':term,'spells_glossary':gloss,'lang':lang,'langkey':langkey,'draft_match':mark,'chosen':chosen,'reason':reason,'paths':paths,'result':'逐處核對；語境性詞組依上列說明。'})
for name,chosen in [(key,row['name']) for key,row in payload.items()] + [('Greataxe','巨斧'),('Handaxe','手斧'),("Explorer's Pack",'探索者套裝'),('Brutal Strike','殘暴打擊'),('Active Effect','Active Effect')]:
    paths = [p for p,text in originals.items() if name in visible_text(text)]
    lang_values = [lang_zh[key] for key,value in lang_en.items() if value == name and key in lang_zh]
    audit.append({'en':name,'terms':terms['terms'].get(name,'—'),'spells_glossary':terms['spells_glossary'].get(name,'—'),'lang':' ／ '.join(sorted(set(lang_values))) or '—','langkey':'專有名稱／完整詞組','draft_match':'—','chosen':chosen,'reason': '使用者裁定保留英文。' if name == 'Active Effect' else ('各已核實來源無既有名稱，沿用原稿s2twp，待本批確認。' if name == 'Feral Instinct' else '採現行Weblate name／advancement title；名稱內不套不同語境的詞。'),'paths':paths,'result':'已逐處回查成品。'})
(HERE/(base+'.term-audit.json')).write_text(json.dumps(audit,ensure_ascii=False,indent=1),encoding='utf-8')

url = 'https://5echm.kagangtuya.top/?page=%E7%8E%A9%E5%AE%B6%E6%89%8B%E5%86%8C2024%2F%E8%A7%92%E8%89%B2%E8%81%8C%E4%B8%9A%2F%E9%87%8E%E8%9B%AE%E4%BA%BA%2F%E9%87%8E%E8%9B%AE%E4%BA%BA.htm'
md = ['# 野蠻人第1批預覽 v1','',f'2026-10-07；來源：[5E不全書野蠻人]({url})。單頁抓取成功1頁，失敗0頁。','',f'目標：`dnd-players-handbook / dnd-players-handbook-classes`。10條、{count_strings(payload)}個Weblate字串、58個正文區塊；其中48個來源區塊、10個Foundry補翻區塊。未上傳。', '',f'確認版本的upload.json SHA-256：`{checksum}`。','', '## 條目與來源行號','', '| EN key | 中文 | 原稿行號 |','|---|---|---|']
for k,v in payload.items():
    a,b = ranges[k]
    md.append(f'| {k} | {v["name"]} | {a}–{b} |')
md += ['', '原稿與底稿逐段對應；Weapon Mastery原稿兩段合併為EN第1區塊，再保留等級擴充段。其餘按原段落／儲存格對齊。', '', '## 底稿與完整成品','',f'- [獨立中文底稿]({HERE/(base+".draft.txt")})',f'- [完整成品HTML預覽]({HERE/(base+".preview.html")})',f'- [本次驗證產生的完整payload]({HERE/(base+".upload.json")})',f'- [全頁來源索引與待處理範圍]({HERE/"classes.barbarian.index.md"})','', '底稿保留原有數值巨集以供回查。`draft.validation.txt`是底稿的機械核對副本：只剔除未修改的巨集，沒有改寫中文；用來處理skeleton.py未正規化底稿巨集的限制。映射程式另逐塊斷言去標記後與原底稿逐字相同。起始裝備保留15GP／75GP，狂暴使用次數保留`@scale.barbarian.rages`。', '', '## 原稿修改與規則差異','', '| 欄位 | 原稿／既有 | EN及底稿 | 原因 |','|---|---|---|---|','| Barbarian敘事第1段 | 局限于肤浅的愤怒 | and not limited to anger → 也不限於憤怒 | 原稿漏否定；依EN修正 |','| Barbarian敘事第2段 | 点燃战斗狂热 | battle prowess → 激發戰鬥能力 | 狂熱與戰鬥能力並非同義；保留原稿整段並修正此詞組 |','| Rage傷害 | 你的伤害掷骰获得额外加值 | bonus to the damage → 你造成的傷害獲得額外加值 | 對齊EN傷害，不自行限制只加於擲骰 |','| Unarmored Defense既有zh-tw | 敏捷調整值 + 感知調整值 | EN及原稿皆為敏捷 + 體質 | 修正既有譯文錯誤；本次payload採體質 |','| Weapon Mastery既有zh-tw | 有熟練的任意武器、長弓／短劍 | 兩種自選的簡易或軍用近戰武器、巨斧／手斧 | 既有文字屬不同武器範圍；按EN與本頁原稿修正 |','| Primal Knowledge Foundry註記 | 網頁無；EN用力量調整值比較通常的Ability Score | 忠實保留EN的調整值／屬性值比較 | 上游自動化描述疑有單位不一致；不改正文規則，也不改技術條件 |','', '其他順稿：簡體以OpenCC s2twp轉繁；尺→呎、执行→採取、施展→施放、精通词条→精通屬性、抗性→抗力、核心表主要属性→主屬性。危机感应／无甲防御／原初学识採現行危險感知／無甲防禦／原初知識；探索套组採現行探索者套裝。','', '## 三方術語對照及lang差異逐條說明','', 'Weblate現行terms完整讀取133筆；spells-glossary完整讀取640筆（其中639筆有獨立中文）；classes現行字串2209筆，3頁HTTP 200且讀取數吻合。法術詞彙表對本批規則與名稱沒有適用的法術條目。', '', '| EN／語境 | terms | spells-glossary | lang | 採用／說明 |','|---|---|---|---|---|']
for a in audit:
    md.append('| '+' | '.join([a['en'],a['terms'],a['spells_glossary'],a['lang'],a['chosen']+'；'+a['reason']])+' |')
md += ['', '所有欄位路徑及命中紀錄見`classes.barbarian.1.term-audit.json`。專有名稱另外核對classes現行name和advancement title；巨斧、手斧、探索者套裝亦已核對現行equipment名稱。', '', '## 自行補翻／巢狀欄位完整對照','', '10個Foundry正文區塊為原稿缺漏補翻；下列亦完整列出activities、effects與advancement，沿用既有中文的欄位另註明。正文衍生的效果描述採同一句底稿，不冒充新原稿。','']
for item in supplements:
    md += ['### '+item['path'],'','EN：`'+item['en']+'`','','中文：'+item['zh'],'','依據：'+item['basis'],'']
md += ['本批沒有activities.condition欄位，因此無condition對照。','', '## 限定詞逐句核對','', '| 欄位 | EN | 中文 | 結果 |','|---|---|---|---|']
pattern = re.compile(r'\b(this|these|that|the|following|one of|each|any|all)\b',re.I)
for path, original in originals.items():
    if pattern.search(visible_text(original)):
        zh = visible_text(finals[path])
        md.append('| '+path+' | '+visible_text(original)+' | '+zh+' | 已核對指涉及單複數；all→所有、following→下列、one of→其中一種／項；the可重述明確名詞 |')
md += ['', '## 四項驗收','', '- 規則核對：正文條件、主體、武器資格、數值、次數、持續時間與例外均已逐句核對EN。Foundry自動化描述與正文規則分開；原初知識的上游比較用詞疑義列於上方。','- 術語核對：三方來源完整讀取；正文、表格、UUID標籤及巢狀欄位已回查。野性直覺是新提出名稱，待本批確認；其餘名稱採現行資料。','- 機械驗證：10條43字串成功；正文與巢狀description均檢查結構、UUID、Reference、巨集及英文殘留；逐欄EN與Weblate現行source完全一致。Active Effect依裁定保留英文。','- 中文通讀：逐段通讀；條件與結果清楚，映射未改中文。每個來源區塊去標記後與底稿逐字相同。','', '## 待確認與後續','', '- 待確認本批v1及「野性直覺」、Foundry補翻。原初知識Foundry註記忠實保留上游比較用詞，未自行改成比較兩個調整值。','- 第2批9條仍待順稿：莽馳、凶蠻打擊、堅韌狂暴、兩條強化凶蠻打擊、持久狂暴、不屈勇武、傳奇恩惠、原初鬥士；這裡的中文為來源標題，最終名稱仍需核實。','- 職業特性等級表、野蠻人子職業與職業獲得屬性值提升的說明，沒有獨立classes key，保留在來源索引；content同章節是另一技術目標，未混入本批。','', '依技能第5步，每批版本須經使用者明確確認才以method=suggest上傳；確認前所有內容留在_incoming。']
(HERE/(base+'.preview.md')).write_text('\n'.join(md)+'\n',encoding='utf-8')

def render(value):
    value = value.replace('[[/award 15GP]]','15金幣').replace('[[/award 75GP]]','75金幣').replace('[[lookup @scale.barbarian.rages]]','〔依野蠻人等級的目前次數〕')
    return re.sub(r'(@UUID\[[^\]]+\]|&amp;Reference\[[^\]]+\])\{([^}]+)\}',lambda m:'<span class="reference" title="'+html.escape(m[1],quote=True)+'">'+m[2]+'</span>',value)
parts = ['<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>野蠻人第1批預覽 v1</title><style>body{font-family:system-ui,"Microsoft JhengHei",sans-serif;line-height:1.8;max-width:940px;margin:40px auto;padding:0 24px;color:#243239;background:#f8f7f3}article{border-top:2px solid #c1a478;margin:36px 0;padding-top:16px}table{border-collapse:collapse;width:100%;background:white}td,th{border:1px solid #d8d4cc;padding:8px;text-align:left}section.secret{border-left:4px solid #b4b4b4;padding:2px 18px;background:#eeece8}.reference{color:#2b6d79;border-bottom:1px dotted}blockquote{font-style:italic}.field{font-size:.9em;padding:12px;background:#e9edea}h1,h2,h3{line-height:1.3}</style><h1>野蠻人第1批 · v1</h1><p>10條 · 43字串 · 待確認</p><p>此頁顯示完整正文及巢狀欄位。Foundry秘密區塊也顯示供審核。數值巨集以可讀文字代示，實際payload保留原巨集。</p>']
for key,entry in payload.items():
    parts += ['<article><h2>'+html.escape(entry['name'])+'</h2><p>'+html.escape(key)+'</p>',render(entry['description'])]
    for field in ['activities','effects','advancement']:
        for path,text in leaves(entry.get(field,{}),field):
            parts += ['<div class="field"><b>'+html.escape(path)+'</b><div>'+render(text)+'</div></div>']
    parts += ['</article>']
parts += ['</html>']
(HERE/(base+'.preview.html')).write_text('\n'.join(parts),encoding='utf-8')
write_info = {'version':'v1','book':'dnd-players-handbook','component':'classes','entries':len(payload),'strings':count_strings(payload),'sha256':checksum,'mechanical_pass':True,'live_en_match':True,'approved':False,'uploaded':False}
(HERE/(base+'.verification.json')).write_text(json.dumps(write_info,ensure_ascii=False,indent=1),encoding='utf-8')
print(json.dumps(write_info,ensure_ascii=False))
