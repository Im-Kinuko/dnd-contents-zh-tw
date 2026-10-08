"""Full source/English/draft comparison and three-way terminology review."""
import hashlib, html, json, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / '_incoming/player-handbook'
PREFIX='content.barbarian.3'
sys.path.insert(0,str(ROOT/'.claude/skills/translation-import/scripts'))
from html_blocks import LABEL, visible_text
from lang_compare import flat
def load(suffix):
    return json.loads((HERE/(PREFIX+'.'+suffix+'.json')).read_text(encoding='utf-8'))
def save(suffix,value):
    (HERE/(PREFIX+'.'+suffix+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=1),encoding='utf-8')
def write(suffix,text):
    (HERE/(PREFIX+'.'+suffix)).write_text(text+'\n',encoding='utf-8')
def link(suffix,label):
    return '['+label+']('+str((HERE/(PREFIX+'.'+suffix)).resolve()).replace('\\','/')+')'
rows=load('mapping-audit')
info=load('verification')
source_map=load('source-map')
assert info['sha256']==hashlib.sha256((HERE/(PREFIX+'.upload.json')).read_bytes()).hexdigest()
assert info['draft_sha256']==hashlib.sha256((HERE/(PREFIX+'.draft.txt')).read_bytes()).hexdigest()
prefix='entries.Barbarian.pages.Barbarian.'
decisions={
 'description/b0001':'插圖Embed，無可見譯文；目標及caption=false完整保留。',
 'description/b0002':'狂暴是多元宇宙原初之力的表現；more than a mere emotion及not limited to anger兩個否定層次均完整保留；三種比喻沒有新增絕境或憤怒限定。',
 'description/b0003':'插圖Embed，無可見譯文；目標、caption=false及classes="right three"完整保留。',
 'description/b0004':'Some／Others保留不同解釋；三種Others觀點並列；for every Barbarian明列對每一位；不只戰鬥能力，也涵蓋反應及感官。',
 'description/b0005':'often→常常，不是全部皆如此；衝向危險使受保護者不必面對危險；原稿的毫不動搖非EN明載，底稿沿用第一批確認版本。',
 'description/b0006':'成為一名野蠻人的節標，省略號保留；不是取得另一項遊戲特性。',
 'description/b0007':'1級角色，不擴及首次兼職時的角色總等級。',
 'description/b0008':'all the traits→所有特質；來源是野蠻人核心特質表，沒有遺失所有或誤寫只有下列部分。',
 'description/b0009':'野蠻人的1級特性；特性表作查閱來源，未自行增補沒有EN欄位的表格。',
 'description/b0010':'兼職角色的獨立節標，不與1級起始角色的所有特質混合。',
 'description/b0011':'following只含生命骰、軍用武器熟練及盾牌訓練；不加入力量／體質豁免、技能或其他護甲受訓。沿用第一批已確認的盾牌護甲訓練用語。',
 'description/b0012':'兼職時同樣取得野蠻人的1級特性；同一句的兩次出現以獨立block ID映射，沒有互相覆蓋。',
 'subclass/b0001':'子職業在其指定等級提供特性；four paths全部列出，wild heart按現行2024名稱為狂野之心道途。原稿額外的選擇、後續能力及表格句沒有加入較短的EN導讀；不把摘要翻成完整3級能力規則。',
 'name':'頁面名稱沿用現行2024 Weblate classes.name野蠻人；同名根條目另行核对。',
 'subclassHeader':'野蠻人子職業，採使用者既定子職業及lang，中文不另造複數形式。',
}
for row in rows:
    local=row['path'][len(prefix):] if row['path'].startswith(prefix) else 'name'
    row['rule_review']=decisions[local].replace('核对','核對')
    assert row['exact_visible_match']
    assert visible_text(row['zh'])==row['draft']
save('mapping-audit',rows)
by_path={row['path']:row for row in rows}
pairs=[]
for row in rows:
    if row['kind']=='protected':continue
    eng=visible_text(row['en'])
    ens=[s.strip() for s in re.split(r'(?<=[.!?])\s+(?=[A-Z])',eng) if s.strip()]
    zhs=[s.strip() for s in re.split(r'(?<=[。！？])',row['draft']) if s.strip()]
    assert len(ens)==len(zhs),(row['path'],ens,zhs)
    for i,(en,zh) in enumerate(zip(ens,zhs),1):
        pairs.append({'path':row['path'],'sentence':i,'en':en,'zh':zh,'qualifiers':re.findall(r'\b(?:this|these|that|the|following|one of|each|any|all|every|some|others)\b',en,re.I),'rule_review':row['rule_review']})
save('sentence-audit',pairs)

# Keep the raw required lang_compare output, then explain every hit by context.
result=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'.claude/skills/translation-import/scripts/lang_compare.py'),str(HERE/(PREFIX+'.sheet.json')),'--draft',str(HERE/(PREFIX+'.draft.txt'))],capture_output=True,text=True,encoding='utf-8')
assert result.returncode==0,result.stderr
write('lang-compare.md',result.stdout.rstrip())
index=load('term_index')
lang_en=flat(json.loads((ROOT/'lang/en.json').read_text(encoding='utf-8-sig')))
lang_zh=flat(json.loads((ROOT/'lang/zh-tw.json').read_text(encoding='utf-8-sig')))
contexts={
 'charge':('一頭衝進','動詞charge headlong是衝進危險；lang的充能為物品資源UI，語境不同。沿用第一批已確認底稿。'),
 'classes':('—','本次lang工具命中Embed參數classes="right three"；不是可見職業名稱。技術參數必須保留，不能改成職業。'),
 'every':('每一位','for every Barbarian逐句譯對每一位野蠻人；lang目標數量UI的所有未套入此句。工具顯示底稿有所有是別句all traits的命中，不能代替逐句查核。'),
 'features':('特性','遊戲職業特性，沿用原稿與lang；不與核心traits的特質混為一談。'),
 'hit point die':('生命骰','使用者裁定、lang以及第一批底稿均為生命骰，不擴寫生命值骰。'),
 'level':('級／等級','1級角色、1級特性與特定等級；沿用第一批數字＋級格式，不逐字改成1等級。'),
 'levels':('等級','子職業給予特性的等級，採原稿及lang。'),
 'martial':('軍用','完整詞组Martial weapons軍用武器；lang相同。'),
 'next':('接下來的頁面','the next pages為下文頁面，不是UI下一步。底稿合併表達為接下來的頁面。'),
 'proficiency':('熟練','proficiency with Martial weapons為軍用武器熟練；不指Proficiency Bonus熟練加值，不能把UI縮略字套入正文。'),
 'self':('真我','deepest self為內心深處的真我，非變形設定的自身外觀或距離自身。沿用原稿及已確認底稿。'),
 'senses':('感官能力','heightened senses是增強的感官能力，採lang感官組成詞及已確認完整句。'),
 'shields':('盾牌','training with Shields為盾牌的護甲訓練；是裝備，不能用法術Shield的glossary護盾術。'),
 'subclass':('子職業','使用者已裁定及lang皆為子職業；原稿子職不採用。'),
 'subclasses':('子職業','同Subclass語境及裁定；四項名稱逐一列出，中文不用額外複數詞尾。'),
 'three':('—','僅是插圖Embed的CSS類別right three，無可見三字；原始命令保持不變。'),
 'traits':('特質','Core Barbarian Traits用第一批已確認野蠻人核心特質表；lang的特徵／特性是UI取值變體，不追改已確認用詞。'),
 'weapons':('武器','完整軍用武器詞組，採lang與已確認底稿。'),
}
def lookup(section,name):
    return next((value for key,value in index[section].items() if key.lower()==name.lower()),'—')
term_rows=[]
for line in result.stdout.splitlines():
    if not line.startswith('| ') or line.startswith('| EN '):continue
    cells=[c.strip() for c in line.strip('|').split('|')]
    if len(cells)!=4:continue
    english,lang,mark,key=cells
    assert english in contexts,('Unexplained lang hit',english)
    chosen,reason=contexts[english]
    rg=re.compile(r'(?<![a-z])'+re.escape(english)+r'(?![a-z])',re.I)
    paths=[row['path'] for row in rows if rg.search(visible_text(row['en']))]
    technical=[row['path'] for row in rows if row['kind']=='protected' and rg.search(row['en'])]
    term_rows.append({'en':english,'context':reason.replace('詞组','詞組'),'chosen':chosen,'terms':lookup('terms',english),'spells_glossary':lookup('spells_glossary',english),'lang':lang,'lang_key':key,'lang_compare_draft_mark':mark,'paths':paths,'technical_paths':technical,'checked':True})

name_sources={
 'Barbarian':('野蠻人','現行2024 Weblate classes entries.Barbarian.name及content根name均已接受野蠻人；三個位置包括UUID標籤一致。'),
 'Rage':('狂暴','現行2024 Weblate classes entries.Rage.name已接受狂暴；沿用第一批底稿。'),
 'Primal':('原初','使用者Primal＝原初裁定及第一批底稿，原稿原力／原始不另套為新譯名。'),
 'Multiverse':('多元宇宙','原稿及第一批已確認底稿；本次沒有新增正式詞條。'),
 'Core Barbarian Traits':('野蠻人核心特質','沿用第一批已確認名稱；所有特質／下列特質的範圍逐句核對。'),
 'Barbarian Features':('野蠻人特性','原稿及第一批已確認特性表名稱；表格沒有獨立EN欄位，引用名稱仍翻。'),
 'Multiclass Character':('兼職角色','原稿及第一批已確認底稿；規則只列三項核心特質與1級特性，不混入完整初始特質。'),
 'Path of the Berserker':('狂戰士道途','現行2024 Weblate classes entries.Path of the Berserker.name，中文UUID標籤完全一致。'),
 'Path of the Wild Heart':('狂野之心道途','現行2024 Weblate classes entries.Path of the Wild Heart.name；原稿獸心道途不採用。'),
 'Path of the World Tree':('世界樹道途','現行2024 Weblate classes entries.Path of the World Tree.name。'),
 'Path of the Zealot':('狂熱者道途','現行2024 Weblate classes entries.Path of the Zealot.name。'),
}
for english,(chosen,reason) in name_sources.items():
    needle=r'Barbarians?' if english=='Barbarian' else re.escape(english)
    rg=re.compile(r'(?<![a-z])'+needle+r'(?![a-z])',re.I)
    paths=[row['path'] for row in rows if rg.search(visible_text(row['en']))]
    assert paths,(english,'Not covered')
    assert all(chosen in row['draft'] for row in rows if row['path'] in paths),(english,chosen,paths)
    langs=sorted({lang_zh[key] for key,value in lang_en.items() if isinstance(value,str) and value.lower()==english.lower() and key in lang_zh})
    term_rows.append({'en':english,'context':reason,'chosen':chosen,'terms':lookup('terms',english),'spells_glossary':lookup('spells_glossary',english),'lang':'／'.join(langs) or '—','lang_key':'完整名稱／規則詞組','paths':paths,'checked':True})
save('term-audit',term_rows)

issues=[]
def issue(identifier,title,field,reason,kind='來源／EN差異'):
    row=by_path[prefix+field]
    issues.append({'id':identifier,'title':title,'path':row['path'],'kind':kind,'en_full':visible_text(row['en']),'source_full':row['source_original'],'draft_full':row['draft'],'reason':reason,'status':'本批v1待確認；重複正文採第一批已確認底稿。'})
issue('I01','原稿把「不限於憤怒」寫成相反方向','description/b0002','原稿「局限于肤浅的愤怒」與EN not limited to anger相反。沿用第一批確認的「也不限於憤怒」；本批是content副本，未變更已送出的classes建議。')
issue('I02','每一位及反應／感官的範圍','description/b0004','EN for every Barbarian及uncanny reflexes / heightened senses已在底稿明列「每一位」「反應力」「感官能力」。來源的戰鬥狂熱改為符合battle prowess的戰鬥能力，仍沿用第一批確認版本。','限定詞與敘述核對')
issue('I03','原稿新增毫不動搖的限定','description/b0005','EN只說面對危險的勇氣，沒有「毫不動搖」限定。底稿依EN保留勇氣及適合冒險，沿用第一批確認版本。')
issue('I04','兼職特質的欄位與範圍','description/b0011','原稿把traits稱能力；底稿使用已確認特質。兼職只列生命骰、軍用武器熟練及盾牌訓練，沒有把1級角色可獲得的所有特質一併套用。','規則及術語核對')
issue('I05','EN子職業導讀比原稿完整3級段落短','subclass/b0001','本欄是導讀，EN只有定義及四種子職業清單。原稿「你選擇獲得」「此後你將獲得」「野蠻人特性表列出」不在此欄EN中，不能直接整段塞入。底稿保留來源的特化、等級給予特性與子職業清單，補回EN明示的各子職業指定內容及接下來頁面；省略的来源句另留remaining，沒有標為已完成。','來源範圍對齊')
issue('I06','獸心道途與現行2024名稱不同','subclass/b0001','UUID所指2024 classes名稱已接受「狂野之心道途」。採該名稱，保留原始UUID目標；其他三個道途亦逐項查過現行名稱。','名稱差異')
source_lines=Path(source_map['source_path']).read_text(encoding='utf-8').splitlines()
issues.append({'id':'I07','title':'職業特性引介及等級表沒有獨立EN欄位','path':'原網頁31–159行','kind':'未匹配來源（不在payload）','en_full':'（目前classes及content的Barbarian模板沒有對應的職業特性引介／等級表欄位；沒有可提供的對應英文表格原句。）模板仍引用特性表：'+visible_text(by_path[prefix+'description/b0009']['en']),'source_full':'\n'.join(source_lines[30:159]),'draft_full':'不新增不存在的key；原稿完整保留於remaining.txt。本批正文的表格名稱引用依底稿映射。','reason':'上批索引把這段記為待做content，核對實際EN後確認無獨立翻譯欄位；本次更正索引及剩餘紀錄，不把這段誤標為已匯入，也不自行寫進日誌正文。','status':'保留未匹配來源，等待對應模板／另行指定匯入目標；不阻塞本批已確定欄位。'})
issues.append({'id':'I08','title':'屬性值提升的職業說明沒有獨立EN欄位','path':'原網頁192–193行','kind':'未匹配來源（不在payload）','en_full':'（本批Barbarian日誌頁及classes的Barbarian條目沒有對應獨立EN欄位；feats的Ability Score Improvement是另一條目，不能冒充本段英文來源。）','source_full':'\n'.join(source_lines[191:193]),'draft_full':'不新增不存在的key；原稿完整保留於remaining.txt。','reason':'這段是4、8、12、16級獲得專長的職業說明，不是同名專長本身的正文；本批不混入feats。','status':'保留未匹配來源，未標完成。'})
save('issues',issues)
problem=['# 野蠻人第3批 v1：全部問題句與完整中英文','','以下每项完整列出EN、原稿中文、底稿及處理理由。I07／I08沒有對應EN欄位，明列缺漏，不捏造英文原句；原稿仍全部列出。','']
for item in issues:
    problem += ['## '+item['id']+' '+item['title'],'','欄位：`'+item['path']+'`；分類：'+item['kind'],'','**EN完整原句／段落或缺漏說明：**',item['en_full'],'','**原稿完整中文：**',item['source_full'],'','**底稿完整中文／處理結果：**',item['draft_full'],'','**原因：** '+item['reason'].replace('来源','來源'),'','狀態：'+item['status'],'']
text='\n'.join(problem).replace('每项','每項')
for item in issues:assert item['source_full'] in text
write('issues.md',text)

full=['# 野蠻人第3批 v1全面對照','','1個真實日誌條目、1個頁面、5個字串；16個映射位置逐一列出，其中14個有可見中文，2個為原樣保留的插圖Embed。','']
for row in rows:
    full += ['## '+row['path'],'','来源類別：'+row['source'],'','**EN完整文字：**',visible_text(row['en']) or '（沒有可見文字，完整技術命令見下方。）','','**原稿完整中文／技術來源：**',row['source_original'],'','**獨立中文底稿：**',row['draft'] or '（不產生中文文字。）','','**成品可見中文：**',visible_text(row['zh']) or '（不產生中文文字。）','','**規則核對：** '+row['rule_review'],'','映射：可見文字与底稿逐字相同；原始HTML／標記：','```html',row['en'],'```','成品：','```html',row['zh'],'```','']
full += ['# 全部逐句中英文及限定詞','']
for pair in pairs:
    full += ['## '+pair['path']+' · '+str(pair['sentence']),'','**EN：** '+pair['en'],'','**中文：** '+pair['zh'],'','限定詞：'+(', '.join(pair['qualifiers']) or '無指定限定詞。'),'','核對：'+pair['rule_review'],'']
text='\n'.join(full).replace('来源類別','來源類別').replace('文字与底稿','文字與底稿')
for row in rows:assert row['source_original'] in text
write('full-comparison.md',text)

payload=load('upload')['entries']['Barbarian']
live=load('content.live')['units']
name_current=live['entries.Barbarian.name']['target'][0]
preview=[
 '# 野蠻人第3批 v1預覽','','日期：2026-10-08。範圍沿用原野蠻人網頁；實際技術元件為`dnd-players-handbook / dnd-players-handbook-content`。',
 '', '1個條目、1個頁面、5個Weblate字串；13個描述區塊（11個可見正文、2個無文字插圖Embed），另核對根名稱、頁名及子職業標題。**未上傳，待本批v1確認。**',
 f'payload SHA-256：`{info["sha256"]}`。',
 '', '## 閱讀文件','',
 '- '+link('draft.txt','獨立中文底稿'),
 '- '+link('preview.html','完整成品HTML預覽'),
 '- '+link('issues.md','全部8項問題：完整中英文及來源'),
 '- '+link('full-comparison.md',f'全面對照：16個映射位置及全部{len(pairs)}組完整中英文'),
 '- '+link('remaining.txt','完整未匹配／尚未抓取來源'),
 '- '+link('upload.json','本次成功驗證payload'),
 '', '## 條目與來源','',
 '| 實際欄位 | 中文／來源 | Weblate目前 |','|---|---|---|',
 '| entries.Barbarian.name | 野蠻人；原稿2行 | 野蠻人，相同譯文 |',
 '| entries.Barbarian.pages.Barbarian.name | 野蠻人；原稿2行 | 英文 |',
 '| entries.Barbarian.pages.Barbarian.subclassHeader | 野蠻人子職業；原稿186行子職標題、採既定子職業 | 英文 |',
 '| entries.Barbarian.pages.Barbarian.description | 原稿19–30行；逐字沿用第一批已確認介紹底稿 | 英文 |',
 '| entries.Barbarian.pages.Barbarian.subclass | 原稿186–187行；依此欄EN導讀範圍映射 | 英文 |',
 '', '未處理Barbarian下四個子職業頁面；payload只含上述5個key，不包含其餘pages或其他職業。root name是現行相同譯文；其餘4個字串目前target仍為source。',
 '', '## 四項驗收','',
 '- 規則核對：主體、some／others／every、all與following，以及起始1級與兼職所得項目全部逐句核對。content導讀和完整3級能力原稿範圍差異列I05；沒有自行增加無EN欄位的表格與職業能力段落。',
 '- 術語核對：本次完整讀取Weblate terms136筆、spells-glossary640筆、classes2209筆及content1161筆，均分頁HTTP 200與count核對。四個道途名稱採現行2024 classes名稱；所有lang命中逐條說明，沒有新增正式術語或修改lang。',
 '- 機械驗證：5個實際巢狀欄位EN與現行Weblate source完全相同；全部HTML骨架、UUID目標、2個Embed及參數保持原樣。16個映射位置可見文字與獨立底稿逐字相同；無英文殘留及「它」。',
 '- 中文通讀：正文獨立閱讀；第一批已確認相同段落完全沿用。子職業段落保留原稿的特化與等級概念，清楚列出四個道途；用詞及限定詞回查完成，待本批確認。',
 '', '## 工具邊界及映射方式','',
 '共用CLI目前只處理entry頂層description，不能直接處理日誌pages。本批腳本把description及subclass欄位在記憶體展成兩筆描述record，使用同一個skeleton.build_entries檢查整段底稿與HTML，再還原為真實entries.Barbarian.pages.Barbarian路徑。每個實際欄位另使用validate.check_description檢查；未修改共用技能工具或EN模板，不能把CLI頂層通過冒充pages已驗證。',
 '兩個Embed沒有可見翻譯，直接保留原始命令；没有另造插圖標籤。此批沒有Foundry文字或activities.condition，沒有原稿缺失的正文補翻；EN範圍調整仍在I05完整揭露。',
 '', '## 三方術語及lang每項說明','',
 '| EN | terms | spells-glossary | lang | 採用中文／原因 |','|---|---|---|---|---|',
]
for row in term_rows:
    preview.append('| '+' | '.join([row['en'],row['terms'],row['spells_glossary'],row['lang'],row['chosen']+'；'+row['context']])+' |')
preview += ['', '完整欄位路徑與逐處回查保存在term-audit.json。lang工具的classes／three為Embed技術參數命中，proficiency並非熟練加值；every在別句出現所有不能代替本句每一位的回查。', '', '## 原稿修改、完整問題及剩餘範圍','',
 'I01–I04是同一來源在content副本的核對，沿用第一批已確認底稿；I05–I06為本批子職業導讀範圍與現行名稱差異；I07–I08為無EN欄位的未匹配來源。每项完整EN及中文均列於問題文件，未用刪節號替代原句。',
 '本次逐行查回原檔，兼職最後一句是第30行，職業特性引介與等級表段自第31行開始；已更正來源索引。前次索引把該段及192–193行記為待做content，實際EN没有這些獨立欄位，本次更正為保留未匹配來源，不能說原頁內容已全部完成。四個子職業連結頁尚未抓取。原頁來源完整保留，第一、第二批已送出建議不變。',
 '', '依 '+ '[translation-import SKILL.md]('+str(ROOT/'.claude/skills/translation-import/SKILL.md').replace('\\','/')+')'+ ' 第5步「每批版本得到使用者明確確認後才上傳」，本批停在可供審查的v1預覽。',
]
write('preview.md','\n'.join(preview).replace('没有','沒有').replace('每项','每項'))

def render(value):
    return LABEL.sub(lambda match:'<span class="annotation" title="'+html.escape(match[1],quote=True)+'">'+html.escape(match[2])+'</span>' if match[2] else '<span class="technical">〔原始插圖Embed，位置及參數保留〕</span>',value)
page=payload['pages']['Barbarian']
doc=['<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>野蠻人第3批v1</title><style>body{font-family:system-ui,"Microsoft JhengHei",sans-serif;line-height:1.8;max-width:950px;margin:36px auto;padding:0 24px;background:#f8f7f3;color:#243239}.annotation{color:#276879;border-bottom:1px dotted}.technical{color:#777;font-size:.85em}article{border-top:2px solid #b99a6c;padding-top:12px}aside{background:#fff1db;padding:16px}h1,h2,h3{line-height:1.5}</style><h1>野蠻人第3批 v1</h1><p>1個日誌條目 · 1個頁面 · 5字串 · 待確認，未上傳</p><article><h2>'+html.escape(page['name'])+'</h2>',render(page['description']),'<h2>'+html.escape(page['subclassHeader'])+'</h2>',render(page['subclass']),'</article><aside>本批只翻此頁正文及子職業導讀。插圖以提示代示，payload保留原始Embed命令；缺少EN欄位的表格與職業說明仍保留於remaining。完整問題、中英文及術語回查另見Markdown文件。</aside></html>']
write('preview.html','\n'.join(doc))
info.update(rule_review_complete=True,terminology_review_complete=True,chinese_readthrough_complete=True,sentence_pairs=len(pairs),issue_count=len(issues),unmatched_source_ranges=[[31,159],[192,193]],supplement_blocks=0,activities_condition=None,approved=False,uploaded=False)
save('verification',info)

index_path=HERE/'classes.barbarian.index.md'
contents=index_path.read_text(encoding='utf-8').replace('| 2–29 | Barbarian |','| 2–30 | Barbarian |').replace('| 30–159 |','| 31–159 |').replace('| 19–29 |','| 19–30 |')
contents=contents.replace('| 31–159 | Barbarian 的職業特性引介及等級表 | content | classes 的EN沒有此段；保留原稿，需另開 content 批次 |','| 31–159 | Barbarian 的職業特性引介及等級表 | 未匹配 | 實際classes及content EN無獨立欄位；保留來源，不新增key（第3批I07） |')
contents=contents.replace('| 186–187 | Barbarian Subclass | content | classes 沒有獨立key；保留原稿，未混入本批 |','| 186–187 | Barbarian.pages.Barbarian.subclass / subclassHeader | content | 第3批v1已預覽，未上傳；較短導讀範圍差異完整列I05 |')
contents=contents.replace('| 192–193 | 職業獲得 Ability Score Improvement 的說明 | content | 不是 feats 的同名專長正文；保留原稿，未混入本批 |','| 192–193 | 職業獲得 Ability Score Improvement 的說明 | 未匹配 | classes及本批content頁面無獨立欄位；不是feats同名專長正文，保留來源（第3批I08） |')
marker='| 19–30 | Barbarian.pages.Barbarian.description | content | 第3批v1已預覽，未上傳；沿用第一批已確認介紹底稿 |'
if marker not in contents:
    contents=contents.replace('| 31–159 |',marker+'\n| 31–159 |',1)
contents=contents.replace('content 是同章節的另一個技術目標；本批只處理已精確匹配的 classes 內容。沒有抓取四個子職業頁面。','content 是同章節的另一個技術目標；第3批僅處理已有精確EN欄位的野蠻人頁面。無獨立EN欄位的來源另留remaining，不能標已匯入。沒有抓取四個子職業頁面。')
index_path.write_text(contents,encoding='utf-8')
print(json.dumps(info,ensure_ascii=False))
