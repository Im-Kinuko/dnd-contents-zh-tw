import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / '_incoming/player-handbook'
DONE = HERE/'_done'
PREFIX = 'classes.barbarian.2'
def load(suffix):
    return json.loads((HERE/(PREFIX+'.'+suffix+'.json')).read_text(encoding='utf-8'))
audit, info, response, stats, approval = [load(s) for s in ['upload-audit','verification','upload-response','statistics-latest','approval']]
assert audit['complete'] and audit['all_targets_unchanged'] and approval['approved']
assert info['version']=='v2'
assert hashlib.sha256((HERE/(PREFIX+'.upload.json')).read_bytes()).hexdigest()==info['sha256']
accepted, skipped = len(audit['accepted']), len(audit['skipped'])
assert accepted+skipped==29 and response['response']['not_found']==0
info.update(approved=True,approval_date='2026-10-08',uploaded=True,uploaded_date='2026-10-08',method='suggest',accepted=accepted,skipped=skipped,not_found=0,all_targets_unchanged=True,component_verified_strings=audit['component_verified_strings'])
(HERE/(PREFIX+'.verification.json')).write_text(json.dumps(info,ensure_ascii=False,indent=1),encoding='utf-8')

def link(suffix,label):
    return '['+label+']('+str(DONE/(PREFIX+'.'+suffix)).replace('\\','/')+')'
report = [
    '# 野蠻人第2批 v2 上傳報告','','日期：2026-10-08。',
    '使用者提供Brutal Strike首段完整修訂，並表示「其他應該沒問題，可以上傳」。v2只採用該段修訂；其餘28個字串及Brutal Strike其他區塊與v1完全相同。',
    '', '**使用者指定首段（映射可見文字逐字相同）：**',approval['approved_paragraph'],'',
    '目標：`dnd-players-handbook / dnd-players-handbook-classes / zh_Hant`。',
    '檔案：`compendium/zh-tw/dnd-players-handbook/dnd-players-handbook.classes.json`；push URL已設定。上傳前needs_commit=true、needs_merge=true、needs_push=false、merge_failure=null；本次只送建議。',
    '', '## 版本及上傳結果','',
    f'- 9條、29字串；payload SHA-256：`{info["sha256"]}`。',
    f'- `method=suggest`，HTTP {response["http_status"]}；accepted={accepted}、skipped={skipped}、not_found=0。',
    '- 跳過的1個字串是`entries.Epic Boon.name`，現行譯文「傳奇恩惠」與payload完全相同。',
    '- 28個新增建議逐項核對：上傳前無建議，上傳後有建議；現行譯文未替換。',
    f'- 整個classes元件{audit["component_verified_strings"]}個字串的source及target上傳前後完全相同；API total/count=2209是元件總數，本批29字串由accepted+skipped核對。',
    '', '## 四項驗收','',
    '- 規則核對：26個正文區塊與11個巢狀欄位全面核對觸發、主體、目標、數值、次數、持續時間及例外；53組完整中英文句／欄位列於全面對照。Brutal Strike首句按使用者指定採「任何優勢」。Sundered的上游摘要省略正文期限及不可疊加限制，完整列於I07，使用者確認保留忠實摘要。',
    '- 術語核對：現行Weblate terms、spells-glossary及lang三方逐項說明；名稱、正文、標籤與介面欄位均回查。補翻及暫定名稱隨本批確認；沒有新增正式詞條。先前I10的lang漏項修正已記入Changelog，本次只修指定首段。',
    '- 機械驗證：9條29字串成功；HTML、UUID、Reference及巨集保留。37個正文／巢狀映射位置與對應底稿可見文字逐字相同；29個EN字串與上傳前Weblate source完全一致。',
    '- 中文通讀：獨立通讀底稿，回查主體、限定詞、修飾範圍及否定；使用者指定首段逐字保留。映射未另改中文語序。',
    '', '## 補翻與condition','',
    '原稿缺少的11個Foundry正文區塊與8個介面欄位，從獨立補翻底稿整段映射；另3個行動名稱由正文名稱／小標直接取用。全部中英文及依據已確認，保存在全面對照。',
    '', '**activities.condition EN：** When you roll initiative',
    '**中文：** 當你進行先攻檢定時',
    '', '## 詳細紀錄','',
    '- '+link('preview.md','確認版本、來源行號、術語對照與修改摘要'),
    '- '+link('issues.md','全部問題句：完整中文與英文'),
    '- '+link('full-comparison.md','全部區塊及53組完整中英文對照'),
    '- '+link('draft.txt','中文底稿'),
    '- '+link('supplement.draft.txt','Foundry及介面補翻底稿'),
    '- '+link('upload.json','成功驗證的確認版本payload'),
    '- '+link('revision-audit.json','只有指定首段變更的版本稽核'),
    '- '+link('upload-audit.json','逐字串上傳稽核'),
    '', '## 剩餘範圍','',
    f'- 本批9條29字串已全部處理，沒有未匹配或未確認內容。{stats["batch_empty_or_source"]}個現行target仍為空或英文；建議未接受前不算完成譯文。',
    f'- classes元件共{stats["component_total"]}字串，其中{stats["component_empty_or_source"]}個現行target為空或與source相同。',
    '- 原網頁的19個classes條目皆已送出第一、第二批建議；同頁的職業引介、等級表、子職業與屬性值提升說明仍須另做content批次。沒有處理四個子職業連結頁。',
    '- 完整網頁原稿及來源索引保留於原目錄；第二批原稿、底稿、預覽與上傳證據歸檔至_done。',
]
(HERE/(PREFIX+'.2026-10-08.report.md')).write_text('\n'.join(report)+'\n',encoding='utf-8')

# Only update the documentation status; never rewrite approved payloads.
preview = HERE/(PREFIX+'.preview.md')
text = preview.read_text(encoding='utf-8')
text = text.replace('**未上傳。**',f'**已以suggest上傳：28個新增建議，1個相同譯文跳過，0個未匹配。**')
text = text.replace('名稱與補翻仍使用者已確認','名稱與補翻已由使用者確認').replace('仍使用者已確認','使用者已確認')
text = text.replace('## 補翻範圍與待確認','## 已確認補翻範圍')
text = text.replace('本批未寫入Weblate或compendium。','本批已送入Weblate建議佇列，現行翻譯與compendium未被替換。')
preview.write_text(text,encoding='utf-8')
page = HERE/(PREFIX+'.preview.html')
page.write_text(page.read_text(encoding='utf-8').replace('已確認，待上傳','已確認並上傳建議：28新增／1相同譯文跳過'),encoding='utf-8')

DONE.mkdir(exist_ok=True)
files = list(HERE.glob(PREFIX+'.*'))
for source in files:
    destination = DONE/source.name
    assert source.resolve().parent==HERE.resolve()
    assert destination.resolve().parent==DONE.resolve() and DONE.resolve().parent==HERE.resolve()
    assert source.is_file() and not destination.exists(),destination
for source in files:
    source.rename(DONE/source.name)
for name in ['preview.md','full-comparison.md','issues.md']:
    document = DONE/(PREFIX+'.'+name)
    text = document.read_text(encoding='utf-8')
    for source in files:
        text = text.replace(str(source),str(DONE/source.name))
        text = text.replace(str(source).replace('\\','/'),str(DONE/source.name).replace('\\','/'))
    document.write_text(text,encoding='utf-8')
index = HERE/'classes.barbarian.index.md'
index.write_text(index.read_text(encoding='utf-8').replace('第2批v2已確認，待上傳','第2批v2已送出建議，2026-10-08'),encoding='utf-8')
assert hashlib.sha256((DONE/(PREFIX+'.upload.json')).read_bytes()).hexdigest()==info['sha256']
print(json.dumps({'archived_files':len(files),'report':str(DONE/(PREFIX+'.2026-10-08.report.md')),'accepted':accepted,'skipped':skipped,'not_found':0},ensure_ascii=False))
