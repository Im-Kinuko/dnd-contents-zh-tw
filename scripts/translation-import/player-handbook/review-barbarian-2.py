"""Full bilingual review, source provenance and mechanical evidence for batch 2."""
import collections, hashlib, html, json, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / '_incoming/player-handbook'
sys.path.insert(0,str(ROOT/'.claude/skills/translation-import/scripts'))
from html_blocks import Plan, compare_html, visible_text, LABEL
from validate import check_description, count_strings
from lang_compare import flat
PREFIX='classes.barbarian.2'
def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))
def save(suffix,value):
    (HERE/(PREFIX+'.'+suffix+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=1),encoding='utf-8')
def leaves(node,prefix=''):
    if isinstance(node,dict):
        for key,value in node.items():
            yield from leaves(value,prefix+'.'+key if prefix else key)
    elif isinstance(node,str):yield prefix,node
def display_en(value):
    value=re.sub(r'<[^>]+>','',value)
    def label(m):
        if m[2]:return m[2]
        if m[1].startswith('[['):return m[1]
        if 'Reference[' in m[1]:return m[1].split('[')[1][:-1]
        return m[1]
    return html.unescape(LABEL.sub(label,value))
def display_zh(value):
    # Display raw dynamic macros rather than hiding the amount in a bilingual review.
    return html.unescape(LABEL.sub(lambda m: m[2] or m[1],re.sub(r'<[^>]+>','',value)))
sheet=load(HERE/(PREFIX+'.sheet.json'))
payload=load(HERE/(PREFIX+'.upload.json'))['entries']
mapping=load(HERE/(PREFIX+'.mapping-audit.json'))
live=load(HERE/(PREFIX+'.weblate.json'))['units']
en=load(ROOT/'compendium/en/dnd-players-handbook/dnd-players-handbook.classes.json')['entries']
originals=dict(leaves({key:en[key] for key in payload}))
finals=dict(leaves(payload))
assert len(finals)==29
for path,zh in finals.items():
    original=originals[path]
    assert original==live['entries.'+path]['source'][0],path
    if path.endswith('.description'):
        assert not check_description(original,zh,{'Foundry','Active','Effect'}),(path,check_description(original,zh,{'Foundry','Active','Effect'}))
    assert '它' not in visible_text(zh),path
    assert not re.findall(r'[A-Za-z]{3,}',visible_text(zh).replace('Foundry','').replace('Active Effect','')),path
    assert not compare_html(original,zh),path
fingerprints=load(HERE/(PREFIX+'.draft-fingerprints.json'))
for name,digest in fingerprints.items():
    assert hashlib.sha256((HERE/(PREFIX+'.'+name+'.txt')).read_bytes()).hexdigest()==digest,'Draft changed after mapping'

# Manual rule review covers the whole clause, not only a word match.
decisions={
 'Instinctive Pounce.description/b0001':'移動是進入狂暴的同一個附贈動作的一部分；可選、距離至多速度一半，沒有新增動作或固定距離。',
 'Brutal Strike.description/b0001':'先使用魯莽攻擊；只選自己本回合一次力量攻擊檢定，放棄其任何優勢（使用者指定完整句），且該次不得有劣勢；命中才有同類型額外傷害和一種自選效應；使用EN原始比例值巨集。',
 'Brutal Strike.description/b0002':'推開15呎且直線遠離自己；隨後可直線朝該目標移動至多速度一半，不引發藉機攻擊；已刪除原稿额外的「立刻」。',
 'Brutal Strike.description/b0003':'速度降低15呎，直到自己下回合開始；同一目標只受最近一次影響，沒有疊加。目標不縮限成原稿的生物。',
 'Brutal Strike.description/b0004':'Foundry註記標題，沿用已裁定格式。',
 'Brutal Strike.description/b0005':'可把斷筋猛擊的Active Effect套用到一個目標；不加入自動套用或成功豁免。',
 'Brutal Strike.description/b0006':'獲得17級強化殘暴打擊（2）才自動調整傷害比例值；damage是EN行動類型稱呼，實際activity.name保持殘暴打擊。',
 'Brutal Strike.activities.Brutal Strike.name':'逐字採用正文底稿的殘暴打擊名稱。',
 'Brutal Strike.effects.Hamstrung.name':'補翻「斷筋」，對應斷筋猛擊；不是新增規則狀態。',
 'Brutal Strike.effects.Hamstrung.description':'此角色遭命中後速度降低15呎；到攻擊者下回合開始，與正文的you相對角色一致。',
 'Relentless Rage.description/b0001':'狂暴啟用、生命降0、並未立即死亡才可DC10體質豁免；成功改成等同於野蠻人等級兩倍的生命值；不是回復2點或延後死亡。',
 'Relentless Rage.description/b0002':'第一次以後每次使用DC+5；完成短休或長休皆重置10，不限只長休。',
 'Relentless Rage.description/b0003':'Foundry註記標題。',
 'Relentless Rage.description/b0004':'自動DC+5以啟用時消耗該資源為條件；短休或長休後自動重置10；沒有將消耗資源追加為正文的遊戲規則。',
 'Improved Brutal Strike.description/b0001':'新增下列兩種效應選項，沒有提升傷害骰或提早取得17級效果。',
 'Improved Brutal Strike.description/b0002':'下一次豁免有劣勢沒有本句明載期限；只有不能藉機攻擊的效果明載到自己下回合開始，未把時間子句擴及豁免。',
 'Improved Brutal Strike.description/b0003':'必須在自己下回合開始前；另一名生物的下一次對該目標攻擊檢定+5，自己不受益；單次攻擊只能獲得一次加值。',
 'Improved Brutal Strike.description/b0004':'Foundry註記標題。',
 'Improved Brutal Strike.description/b0005':'每個選項各提供行動及追蹤用Active Effect；不自動處理該效應。each的逐一範圍明確。',
 'Improved Brutal Strike.activities.Sundering Blow.name':'直接取底稿小標破勢猛擊。',
 'Improved Brutal Strike.activities.Staggering Blow.name':'直接取底稿小標震撼猛擊。',
 'Improved Brutal Strike.effects.Staggered.name':'補翻震撼，對應震撼猛擊，非正式規則狀態。',
 'Improved Brutal Strike.effects.Staggered.description':'下一次豁免有劣勢；藉機攻擊限制到攻擊者下回合開始，時間作用範圍同正文。',
 'Improved Brutal Strike.effects.Sundered.name':'補翻破勢，對應破勢猛擊，非新增正式狀態。',
 'Improved Brutal Strike.effects.Sundered.description':'忠實翻譯完整EN效果摘要；此摘要缺正文的時間及疊加限制，上游缺漏已單列I07使用者已確認，未自行補字。',
 'Persistent Rage.description/b0001':'先攻檢定時可重獲所有已消耗狂暴；此方法完成長休前不可再用，不限制短休正常恢復。',
 'Persistent Rage.description/b0002':'持續10分鐘、無需逐輪延長；昏迷或穿重甲提早結束，只有失能不再令此狂暴結束；保留否定範圍及or。',
 'Persistent Rage.description/b0003':'Foundry註記標題。',
 'Persistent Rage.description/b0004':'先攻檢定時可用行動恢復所有狂暴次數；沒添加額外動作種類或消耗。',
 'Persistent Rage.activities.Recharge Rage on Initiative.name':'行動名稱「先攻時恢復狂暴」依完整EN及正文術語。',
 'Persistent Rage.activities.Recharge Rage on Initiative.condition':'When you roll initiative完整對照，與正文觸發完全一致。',
 'Improved Brutal Strike (2).description/b0001':'額外傷害提升至2d10；每當用殘暴打擊可選兩種不同效應；不是相同效應兩次或2個目標。',
 'Improved Brutal Strike (2).description/b0002':'Foundry註記標題。',
 'Improved Brutal Strike (2).description/b0003':'只說殘暴打擊傷害骰自動調整成新數值；沒有改寫其他效果的傷害。',
 'Indomitable Might.description/b0001':'力量檢定或力量豁免的總值嚴格低於力量屬性值才可選擇以該值代替；不是直接設定d20最低結果。',
 'Epic Boon.description/b0001':'一項傳奇恩惠專長或另一項符合先決條件的自選專長；無敵攻勢恩惠是推薦而非強制；兩個UUID目標原樣。',
 'Primal Champion.description/b0001':'力量、體質各+4且上限25；依EN明確上限句式提出修正，不獨立把最大值直接設定25。',
}
assert set(decisions)=={row['path'] for row in mapping},(set(decisions)-{row['path'] for row in mapping},{row['path'] for row in mapping}-set(decisions))

source_path=next((HERE/'_web/barbarian').glob('*.htm.txt'))
source_lines=source_path.read_text(encoding='utf-8').splitlines()
paragraph_ranges={
 'Instinctive Pounce.description/b0001':(204,204),
 'Brutal Strike.description/b0001':(207,207),'Brutal Strike.description/b0002':(208,209),'Brutal Strike.description/b0003':(210,211),
 'Relentless Rage.description/b0001':(213,213),'Relentless Rage.description/b0002':(214,214),
 'Improved Brutal Strike.description/b0001':(216,216),'Improved Brutal Strike.description/b0002':(217,218),'Improved Brutal Strike.description/b0003':(219,221),
 'Persistent Rage.description/b0001':(223,223),'Persistent Rage.description/b0002':(224,224),
 'Improved Brutal Strike (2).description/b0001':(226,226),'Indomitable Might.description/b0001':(228,228),
 'Epic Boon.description/b0001':(230,230),'Primal Champion.description/b0001':(232,232),
}
for row in mapping:
    row['rule_review']=decisions[row['path']].replace('额外','額外')
    if row['path'] in paragraph_ranges:
        a,b=paragraph_ranges[row['path']]
        row['source_lines']=[a,b]
        row['source_original']='\n'.join(source_lines[a-1:b])
    else:row['source_original']='原稿沒有此介面／Foundry欄位。' if row['source']=='supplement' else '來源正文的名稱／小標。'

# Every sentence is paired, including nested fields; inline headings accompany
# their first sentence to preserve complete visible wording.
sentence_pairs=[]
for row in mapping:
    raw_en=row['en']
    leading=''
    lead=re.match(r'^<strong>(.*?)</strong>\s*',raw_en)
    if lead:
        leading=display_en(lead[1])+' '
        raw_en=raw_en[lead.end():]
    ens=[s.strip() for s in re.split(r'(?<=[.!?])\s+(?=[A-Z])',display_en(raw_en)) if s.strip()]
    if leading:
        if ens:ens[0]=leading+ens[0]
        else:ens=[leading.strip()]
    zhs=[s.strip() for s in re.split(r'(?<=[。！？])',display_zh(row['zh'])) if s.strip()]
    assert len(ens)==len(zhs),(row['path'],ens,zhs)
    for index,(eng,zh) in enumerate(zip(ens,zhs),1):
        sentence_pairs.append({'path':row['path'],'sentence':index,'en':eng,'zh':zh,'rule_review':row['rule_review'],'qualifiers':re.findall(r'\b(?:this|these|that|the|following|one of|each|any|all)\b',eng,re.I)})
save('sentence-audit',sentence_pairs)
save('mapping-audit',mapping)

by_path={row['path']:row for row in mapping}
issues=[]
def issue(identifier,title,path,reason,kind='來源修正',extra=None):
    row=by_path[path]
    issues.append({'id':identifier,'title':title,'kind':kind,'path':path,'en_full':display_en(row['en']),'en_raw':row['en'],'source_full':row['source_original'],'draft_full':display_zh(row['zh']),'reason':reason,'extra':extra,'status':'使用者已於2026-10-08確認本批v2。'})
issue('I01','固定1d10與EN比例值巨集','Brutal Strike.description/b0001','原稿寫1d10，EN使用依等級成長的比例值巨集。底稿保留該原始巨集，9級1d10及17級2d10由相對應條目控制；其他完整句子仍逐字取底稿。此段沒有改標補翻。','技術映射差異')
issue('I02','多出立即時點，少了直線方向','Brutal Strike.description/b0002','原稿「立刻」不是EN明載時點，且移動句沒写straight。依EN刪除立刻，補回朝該目標直線移動，保留then及不引發藉機攻擊。')
issue('I03','生物與目標的範圍不同','Brutal Strike.description/b0003','原稿末句只写「一個生物」；EN是target。改為一個目標，不把本來的目標資格縮限成生物；仍只受最新一次影響。')
issue('I04','破勢猛擊的before與單次加值','Improved Brutal Strike.description/b0003','原稿以「直至」表達期限；依EN明確寫「在你的下個回合開始前」，保留另一名生物、下一次攻擊、+5及只能一次加值。這是限定範圍明確化，沒有發現數值錯誤。','限定詞及時間核對')
issue('I05','10分鐘仍有提早結束例外','Persistent Rage.description/b0002','原稿「總是能持續10分鐘」容易忽略後句例外；改為「現在會持續10分鐘」，明列昏迷／重甲提早結束。「not just」譯而不只是，避免讀成仍因單純失能而結束。')
issue('I06','屬性提升與上限的語意','Primal Champion.description/b0001','原稿把「上限變為25」獨立成句；EN明寫increase by 4, to a maximum of 25。本批依EN寫各提升4點、上限25；此處保留完整原稿與英文，供裁定。')
main=by_path['Improved Brutal Strike.description/b0003']
issue('I07','EN效果摘要缺少時間及不可疊加限制','Improved Brutal Strike.effects.Sundered.description','Sundered效果摘要沒写正文的before the start of your next turn及only one Sundering Blow bonus。本批忠實翻譯摘要，沒有自行把正文限制加到該欄；正文限制完整保留。摘要是上游省略，仍使用者已確認。','上游摘要省略',{'main_en_full':display_en(main['en']),'main_zh_full':display_zh(main['zh'])})
issue('I08','專長現行名稱與章節連結','Epic Boon.description/b0001','原稿「無敵攻勢之恩惠」採現行Weblate名稱「無敵攻勢恩惠」；原稿「見第五章」由EN的原始分類UUID承接，正文不額外加未在EN可見文字中的章節括號。傳奇恩惠依使用者全局裁定。','名稱及連結映射')
activity_name=payload['Brutal Strike']['activities']['Brutal Strike']['name']
issue('I09','傷害行動的稱呼與實際行動名稱','Brutal Strike.description/b0006','Foundry註記用小寫damage稱行動，但activities的顯示名称EN是Brutal Strike。本批按兩欄語境分別譯「傷害行動」及「殘暴打擊」，未把實際行動名稱改成傷害；這是用語注意事項，不主張EN規則矛盾。','跨欄位用語注意',{'activity_en_full':'Brutal Strike','activity_zh_full':activity_name})
issues.append({'id':'I10','title':'Epic Boon介面殘留舊譯','kind':'已裁定術語同步修正','path':'lang.DND5E.Feature.SupernaturalGift.EpicBoon','en_full':'Epic Boon','en_raw':'Epic Boon','source_full':'lang原有中文：恩賜','draft_full':'傳奇恩惠','reason':'依2026-10-07使用者全面採用傳奇恩惠的既有裁定，本次只修正此lang漏項，並記入Changelog.md；不修改本批以外的compendium或Weblate。','extra':None,'status':'已同步修正lang；不是新的術語裁定。'})
for item in issues:
    item['reason']=item['reason'].replace('写','寫').replace('名称','名稱')
save('issues',issues)

# The required lang comparison is retained unmodified; a second table explains
# every row, including grammatical words that happen to match UI strings.
result=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'.claude/skills/translation-import/scripts/lang_compare.py'),str(HERE/(PREFIX+'.sheet.json')),'--draft',str(HERE/(PREFIX+'.draft.txt'))],capture_output=True,text=True,encoding='utf-8',check=True)
(HERE/(PREFIX+'.lang-compare.md')).write_text(result.stdout,encoding='utf-8')
term_index=load(HERE/(PREFIX+'.term_index.json'))
lang_en=flat(load(ROOT/'lang/en.json'))
lang_zh=flat(load(ROOT/'lang/zh-tw.json'))
decide={
 'activity':('行動','Foundry語境按使用者裁定與lang；出現在補翻底稿。'),
 'anything':('做任何事／逐輪延長','without needing to do anything說不須做事，非裝備選项的任意類型；底稿以無需逐輪延長完整表達。'),
 'applied':('套用','can be applied為可套用，非已完成UI狀態「已套用」；在補翻底稿。'),
 'armor':('重甲','本批只出現在Heavy armor完整詞組，採既有重甲，不單獨用護甲。'),
 'attack roll':('攻擊檢定','Weblate terms優先於lang攻擊擲骰／攻擊骰。'),
 'change':('改為','生命值變更結果的動詞，非effect的變更欄位。'),
 'damage roll':('傷害骰','採lang完整詞組；出現在補翻底稿。'),
 'each':('每次／每個','each time用每次；each option用每個；補翻明列每個選項各一個行動。'),
 'effect':('效應／Active Effect','規則效應沿用底稿；Active Effect依使用者裁定保留英文，不強改為效果。'),
 'effects':('效應','本批指殘暴打擊規則效應，沿用原稿；不是UI效果分頁。'),
 'epic boon':('傳奇恩惠','使用者全局裁定及terms優先；lang原恩賜已依裁定補正，舊repo史詩恩惠不採。'),
 'heavy armor':('重甲','沿用現行PHB與lang ArmorHeavyProficiency；不套裝備分類的重型護甲。'),
 'increase':('提升','屬性與DC變化，沿用原稿和使用者「提升N點」句式；非生命骰管理按鈕。'),
 'keep':('持續','keep you fighting為持續戰鬥，不是變形設定的保留。'),
 'next':('下個／下一次','回合與檢定的順序，不是UI下一步／下一頁。'),
 'number':('數值','生命值等同於等級兩倍的數值，非骰子數量。'),
 'points':('生命值／點','Hit Points是完整規則詞生命值；屬性提升依裁定加點，不套專長點數。'),
 'recharge':('恢復','狂暴使用次數的恢復，非物品充能；沿用正文與原稿。'),
 'reference':('—','&Reference技術標記的掃描命中，不是可見英文；標籤仍全面核對。'),
 'resource':('資源','採lang，僅在Foundry補翻；未添加成正文使用此能力的額外條件。'),
 'rest':('短休／長休','採完整規則詞；不套一般休息。'),
 'roll':('檢定／傷害骰','attack/Initiative/saving throw roll依完整規則詞；damage roll採傷害骰，不逐字套UI擲骰。'),
 'scale':('調整比例值','沿用使用者scale value＝比例值；此處為Foundry自動化動詞，不單獨套UI比例。'),
 'start of your next turn':('你的下個回合開始／開始前','until依裁定不加前；before明確寫開始前，區分不同時間限定。'),
 'total':('總值','檢定總值，非Total Cover全掩蔽或計算欄標籤總計。'),
}
alltext='\n'.join(display_en(row['en']) for row in mapping)+'\n'+'\n'.join(en[key]['name'] for key in payload)
final_text='\n'.join(visible_text(value) for value in finals.values())
term_audit=[]
for line in result.stdout.splitlines():
    if not line.startswith('| ') or line.startswith('| EN '):continue
    columns=[s.strip() for s in line.strip('|').split('|')]
    if len(columns)!=4:continue
    english,lang,match,langkey=columns
    rg=re.compile(r'(?<![a-z])'+re.escape(english)+r'(?![a-z])',re.I)
    occurrences=[row['path'] for row in mapping if rg.search(display_en(row['en']))]
    adopted=[value for value in lang.split(' ／ ') if value in final_text]
    chosen,reason=decide.get(english,('／'.join(adopted) if adopted else lang,'採lang適用中文；其他UI變體不套於本句，已逐處回查。'))
    reasons={'target':'目標','time':'時間','type':'類型','turn':'回合','score':'屬性值','unarmed':'徒手打擊','long':'長休','heavy':'重甲','half':'一半','uses':'使用次數','hit points':'生命值','maximum':'上限','creature':'生物','bonus':'加值','attacks':'攻擊'}
    if english in reasons and english not in decide:
        chosen=reasons[english]
        reason='採完整規則詞的適用中文及lang；其他體型、掩蔽、介面標籤或計數模板依本句語境不使用。'
    terms=next((value for key,value in term_index['terms'].items() if key.lower()==english),'—')
    glossary=next((value for key,value in term_index['spells_glossary'].items() if key.lower()==english),'—')
    term_audit.append({'en':english,'context':reason,'chosen':chosen,'terms':terms,'spells_glossary':glossary,'lang':lang,'langkey':langkey,'lang_compare_draft_match':match,'paths':occurrences,'result':'已依上列語境逐處回查，沒有以UI單字強制取代完整規則詞。'})

name_sources={
 'Instinctive Pounce':'現行Weblate及其他書的entry_names查無中文名稱；沿用原稿s2twp莽馳，使用者已確認。',
 'Brutal Strike':'現行Weblate Barbarian advancement.Brutal Strike.title＝殘暴打擊；原稿凶蠻打擊不採。',
 'Relentless Rage':'現行name及其他書名稱索引無中文；沿用原稿堅韌狂暴，使用者已確認。',
 'Improved Brutal Strike':'沿用已核實的殘暴打擊組成詞，加原稿強化；使用者已確認。',
 'Persistent Rage':'沿用原稿持久狂暴；現行name及其他書名稱索引無中文，使用者已確認。',
 'Improved Brutal Strike (2)':'以強化殘暴打擊名稱加（2）區分17級版本；不改EN key。',
 'Indomitable Might':'沿用原稿不屈勇武；Indomitable組成詞使用既定不屈，使用者已確認。',
 'Epic Boon':'使用者全局裁定、現行terms及Weblate name＝傳奇恩惠。',
 'Primal Champion':'2024 repo Barbarian advancement.Primal Champion.title＝原初勇士；現行name為英文，採既有2024名稱，原稿原初鬥士不採。',
 'Forceful Blow':'原稿巨力猛擊，未查到同名既有條目，使用者已確認。',
 'Hamstring Blow':'原稿斷筋猛擊，未查到同名既有條目，使用者已確認。',
 'Staggering Blow':'原稿震撼猛擊；正文小標與行動name逐字一致，使用者已確認。',
 'Sundering Blow':'原稿破勢猛擊；正文小標與行動name逐字一致，使用者已確認。',
 'Hamstrung':'補翻斷筋，依對應原稿猛擊名稱，不新增正式狀態。',
 'Staggered':'補翻震撼，依對應原稿猛擊名稱，不新增正式狀態。',
 'Sundered':'補翻破勢，依對應原稿猛擊名稱，不新增正式狀態。',
 'Active Effect':'使用者裁定保留英文Active Effect。',
 'Boon of Irresistible Offense':'已讀取現行2024 Weblate feats名稱無敵攻勢恩惠，UUID標籤照用。',
 'Rage':'現行2024 Weblate name狂暴，已核實。',
 'Reckless Attack':'現行2024 Weblate name魯莽攻擊，原始/item巨集目標不變，只加中文顯示標籤。',
 'Unarmed Strike':'其他2024條目名稱及lang用徒手打擊；原稿同詞。',
 'Opportunity Attack':'使用者裁定與terms藉機攻擊；正文、Reference與巢狀效果均已回查。',
 'Recharge Rage on Initiative':'补翻先攻時恢復狂暴，依完整EN與正文，使用者已確認。',
}
name_chosen={key:row['name'] for key,row in payload.items()}
name_chosen.update({'Forceful Blow':'巨力猛擊','Hamstring Blow':'斷筋猛擊','Staggering Blow':'震撼猛擊','Sundering Blow':'破勢猛擊','Hamstrung':'斷筋','Staggered':'震撼','Sundered':'破勢','Active Effect':'Active Effect','Boon of Irresistible Offense':'無敵攻勢恩惠','Rage':'狂暴','Reckless Attack':'魯莽攻擊','Unarmed Strike':'徒手打擊','Opportunity Attack':'藉機攻擊','Recharge Rage on Initiative':'先攻時恢復狂暴'})
for english,reason in name_sources.items():
    needle=r'Opportunity Attacks?' if english=='Opportunity Attack' else re.escape(english)
    rg=re.compile(r'(?<![a-z])'+needle+r'(?![a-z])',re.I)
    paths=[row['path'] for row in mapping if rg.search(display_en(row['en']))]
    paths += [key+'.name' for key in payload if key==english]
    langvalues=sorted({lang_zh[key] for key,value in lang_en.items() if value.lower()==english.lower() and key in lang_zh})
    term_audit.append({'en':english,'context':reason.replace('补翻','補翻'),'chosen':name_chosen[english],'terms':term_index['terms'].get(english,'—'),'spells_glossary':term_index['spells_glossary'].get(english,'—'),'lang':'／'.join(langvalues) or '—','langkey':'完整名稱／規則詞組','lang_compare_draft_match':'—','paths':paths,'result':'名稱、小標、註記、介面與UUID標籤已逐處回查。'})
save('term-audit',term_audit)

hash_value=hashlib.sha256((HERE/(PREFIX+'.upload.json')).read_bytes()).hexdigest()
name_review=[]
for key,entry in payload.items():
    current=live['entries.'+key+'.name']['target'][0]
    name_review.append({'path':key+'.name','en':en[key]['name'],'current':current,'draft':entry['name'],'reason':name_sources[key]})
save('name-audit',name_review)
condition=by_path['Persistent Rage.activities.Recharge Rage on Initiative.condition']
source_entry_ranges={key:next(row['source_lines'] for row in mapping if row['path'].startswith(key+'.description/')) for key in payload}
entry_ranges={'Instinctive Pounce':(202,204),'Brutal Strike':(205,211),'Relentless Rage':(212,214),'Improved Brutal Strike':(215,221),'Persistent Rage':(222,224),'Improved Brutal Strike (2)':(225,226),'Indomitable Might':(227,228),'Epic Boon':(229,230),'Primal Champion':(231,232)}

def path_link(name,label):
    return '['+label+']('+str((HERE/name).resolve()).replace('\\','/')+')'
header=['# 野蠻人第二批預覽 v2','','2026-10-08。目標：`dnd-players-handbook / dnd-players-handbook-classes`。','',f'9條、{count_strings(payload)}個Weblate字串；26個正文區塊（15個來源區塊、11個Foundry補翻）、11個巢狀欄位，另核對9個條目名稱。','',f'原稿、底稿、映射、EN與現行Weblate全面比對完成。{len(sentence_pairs)}組完整句／欄位逐一核對。**未上傳。**','',f'確認版本payload SHA-256：`{hash_value}`。','', '## 閱讀順序','',
 '- '+path_link(PREFIX+'.draft.txt','獨立中文底稿：原稿順稿後的正文'),
 '- '+path_link(PREFIX+'.supplement.draft.txt','獨立補翻底稿：Foundry與介面欄位'),
 '- '+path_link(PREFIX+'.issues.md','全部問題句：完整EN、原稿中文、底稿中文及處理理由'),
 '- '+path_link(PREFIX+'.full-comparison.md','全面對照：所有區塊、逐句中英文、巢狀欄位及限定詞'),
 '- '+path_link(PREFIX+'.preview.html','完整成品HTML預覽'),
 '- '+path_link(PREFIX+'.upload.json','本次成功驗證的完整payload'),
 '', '底稿先獨立成檔，再由`map-barbarian-2-from-draft.py`逐段讀取，只包上HTML、UUID、Reference與巨集標籤。37個正文／巢狀映射位置都有與底稿逐字相同的斷言。原始比例值巨集保持不變；`draft.validation.txt`只正規化該巨集，不改中文字。', '', '## 條目、來源及名稱','', '| EN key | 中文 | 原稿行號 | 名稱依據 |','|---|---|---|---|']
for key,entry in payload.items():
    a,b=entry_ranges[key]
    header.append(f'| {key} | {entry["name"]} | {a}–{b} | {name_sources[key]} |')
header += ['', '## 四項驗收','',
 '- 規則核對：正文的觸發、主體、目標、條件、距離、數值、次數、持續時間與例外已全面核對。Sundered的EN效果摘要省略正文時間及不可疊加限制，已在I07完整列出；摘要沒有自行補字，使用者已確認。',
 '- 術語核對：現行terms136筆、spells-glossary640筆（639筆獨立中文）、classes2209筆已完整分頁HTTP 200核實；lang全部命中逐條說明。名稱與補翻仍使用者已確認，未新增正式詞條。',
 '- 機械驗證：9條29字串成功；正文與巢狀description另檢查結構、技術標記及英文殘留；29個字串的EN與現行Weblate source逐欄完全一致。',
 '- 中文通讀：獨立閱讀正文與補翻底稿；時間子句、主體及否定範圍已回查。映射後再與底稿逐字比對，未改寫句子。',
 '', '## 補翻範圍與待確認','',
 '原稿沒有11個Foundry正文區塊與8個介面欄位（效果名稱／描述、先攻恢復行動名稱／條件），均由獨立補翻底稿取用。另3個行動名稱直接衍生正文名稱／小標，沒有自行造新譯文。全部EN及中文列在全面對照中。',
 '', '唯一activities.condition：', '', '**EN：** '+condition['en'],'','**中文：** '+display_zh(condition['zh']),'',
 '本批v2已由使用者確認，包括原稿沿用／組成的暫定名稱、Foundry與介面補翻，以及I07效果摘要省略的處理方式。本批名稱「殘暴打擊」及「原初勇士」各依現行Weblate advancement及2024 repo既有title；不由原稿重新定名。',
 '', '## 完整問題清單','']
problem_doc=['# 野蠻人第二批：全部問題句與完整中英文對照','','以下區分來源修正、時間／名稱核對及上游注意事項，不把所有差異都稱作已確定的規則錯誤。每項均完整列出對應區塊，沒有用片段或刪節號代替句子。','']
for item in issues:
    block=['## '+item['id']+' '+item['title'],'','欄位：`'+item['path']+'`；分類：'+item['kind'],'','**EN完整原句／段落：**',item['en_full'],'','**原稿完整中文：**',item['source_full'],'','**提出的完整中文底稿／補翻：**',item['draft_full'],'','**原因與處理：** '+item['reason'],'']
    if item['extra']:
        for field,text in item['extra'].items():
            block += ['**'+{'main_en_full':'正文EN完整句','main_zh_full':'正文中文完整句','activity_en_full':'實際行動EN名稱','activity_zh_full':'實際行動中文名稱'}[field]+'：**',text,'']
    block += ['狀態：'+item['status'],'']
    problem_doc.extend(block)
    header.extend(block)

header += ['## 三方術語／lang每項說明','','| EN | terms | spells-glossary | lang | 採用中文／逐項理由 |','|---|---|---|---|---|']
for row in term_audit:
    header.append('| '+' | '.join([row['en'],row['terms'],row['spells_glossary'],row['lang'],row['chosen']+'；'+row['context']])+' |')
header += ['', '完整欄位路徑與逐處回查結果保存在`term-audit.json`；`lang-compare.md`保留工具原始輸出。語法詞與UI詞的偶然命中也逐項說明，沒有以全局替換套詞。I10已依既有裁定把lang的EpicBoon漏項從恩賜改為傳奇恩惠，重新比對後不再出現此差異。', '', '## 範圍與後續','', '本批涵蓋上頁剩餘9個classes條目；表格、子職業與屬性值提升的content目標仍是另一批，原網頁來源完整保留。第一批已送出的建議未修改；本批未寫入Weblate或compendium。僅同步修正I10的lang漏項並記入Changelog。', '', '使用者提供Brutal Strike首段完整修訂，並明確表示「其他應該沒問題，可以上傳」。v2只採用該段修訂，其餘譯文保留，依此次確認送出建議。']

full=['# 第二批全面對照','','每一個EN區塊都列出完整中文原稿（有來源時）、底稿、成品與人工規則查核；後半段含全部逐句中英文與限定詞。','', '## 全部名稱','']
for row in name_review:
    full += ['### '+row['path'],'','EN：'+row['en'],'','現行中文／英文：'+row['current'],'','底稿：'+row['draft'],'','依據：'+row['reason'],'']
full += ['## 全部正文與巢狀欄位','']
for row in mapping:
    full += ['### '+row['path'],'','來源分類：'+row['source'],'','**EN完整文字：**',display_en(row['en']),'','**原稿完整中文：**',row['source_original'],'','**底稿完整中文：**',display_zh(row['draft']),'','**最終完整中文：**',display_zh(row['zh']),'','**規則核對：** '+row['rule_review'],'','映射驗證：去標記後與對應底稿逐字相同。','', '**保留的EN技術原文：**','```html',row['en'],'```','', '**映射成品：**','```html',row['zh'],'```','']
full += ['## 全部句子／欄位及限定詞核對','']
for pair in sentence_pairs:
    full += ['### '+pair['path']+' · '+str(pair['sentence']),'','**EN：** '+pair['en'],'','**中文：** '+pair['zh'],'','限定詞：'+(', '.join(pair['qualifiers']) or '本句沒有指定限定詞。'),'','核對：'+pair['rule_review'],'']
full += ['## 限定詞逐處說明','','this feature→此特性；the target→目標或該目標；that score→該屬性值；following→下列；each option→每個選項，各一個行動；all expended uses→所有已消耗使用次數；any Advantage→所選一次檢定的任何優勢（使用者指定）；one／two／another→一種／兩種不同／另一名，沒有漏單複數。before與until分別處理，沒有統一套成同一個結束時點。']
for name,text in [(PREFIX+'.preview.md','\n'.join(header)),(PREFIX+'.issues.md','\n'.join(problem_doc)),(PREFIX+'.full-comparison.md','\n'.join(full))]:
    # Source quotations stay byte-for-byte Chinese originals, including simplified
    # characters. Do not run global character replacements over this report.
    source_rows=issues if name.endswith('.issues.md') or name.endswith('.preview.md') else mapping
    for row in source_rows:
        original=row.get('source_full',row.get('source_original',''))
        assert original in text, ('Source quotation altered',name)
    (HERE/name).write_text(text+'\n',encoding='utf-8')

# Human preview shows the dynamic amount explicitly without changing payload.
def render_zh(value):
    value=value.replace('[[lookup @scale.barbarian.brutal-strike]]','〔比例值：9級1d10／17級2d10〕')
    return LABEL.sub(lambda m:'<span class="annotation" title="'+html.escape(m[1],quote=True)+'">'+html.escape(m[2] or m[1])+'</span>',value)
page=['<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>野蠻人第二批v2</title><style>body{font-family:system-ui,"Microsoft JhengHei",sans-serif;background:#f8f7f3;color:#243239;line-height:1.8;max-width:940px;margin:36px auto;padding:0 24px}article{border-top:2px solid #c1a478;margin:32px 0;padding-top:12px}.secret{border-left:4px solid #bbb;padding:1px 16px;background:#eeece8}.field{padding:10px;background:#e9edea;font-size:.9em;margin:6px 0}.annotation{color:#2b6d79;border-bottom:1px dotted}.issue{padding:12px 16px;background:#fff0d9;border-left:4px solid #c99a49;white-space:pre-wrap}h1,h2,h3{line-height:1.4}</style><h1>野蠻人第二批 v2</h1><p>9條 · 29個字串 · 已確認，待上傳</p><p>秘密註記展開供審查；巨集只在此頁以可讀文字代示，payload保留原值。</p>']
for key,entry in payload.items():
    page += ['<article><h2>'+html.escape(entry['name'])+'</h2><p>'+html.escape(key)+'</p>',render_zh(entry['description'])]
    for field in ['activities','effects','advancement']:
        for path,value in leaves(entry.get(field,{}),field):
            page += ['<div class="field"><b>'+html.escape(path)+'</b><div>'+render_zh(value)+'</div></div>']
    for item in issues:
        if item['path'].startswith(key+'.'):
            page += ['<div class="issue"><b>'+html.escape(item['id']+' '+item['title'])+'</b>\nEN：'+html.escape(item['en_full'])+'\n中文：'+html.escape(item['draft_full'])+'\n'+html.escape(item['reason'])+'</div>']
    page += ['</article>']
page += ['</html>']
(HERE/(PREFIX+'.preview.html')).write_text('\n'.join(page),encoding='utf-8')
info={'version':'v2','book':'dnd-players-handbook','component':'classes','entries':9,'strings':29,'description_blocks':26,'source_blocks':15,'supplement_blocks':11,'nested_fields':11,'sentence_pairs':len(sentence_pairs),'issue_count':len(issues),'sha256':hash_value,'draft_sha256':fingerprints,'mechanical_pass':True,'all_draft_visible_matches':True,'live_en_match':True,'upstream_summary_gaps':['Improved Brutal Strike.effects.Sundered.description'],'lang_changes':[{'key':'DND5E.Feature.SupernaturalGift.EpicBoon','before':'恩賜','after':'傳奇恩惠','basis':'2026-10-07使用者全局裁定'}],'approved':True,'uploaded':False}
save('verification',info)
index=HERE/'classes.barbarian.index.md'
index.write_text(index.read_text(encoding='utf-8').replace('第2批v1已預覽，未上傳','第2批v2已確認，待上傳'),encoding='utf-8')
print(json.dumps(info,ensure_ascii=False))
