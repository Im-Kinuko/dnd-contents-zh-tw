import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / '_incoming/player-handbook'
DONE = HERE/'_done'
PREFIX = 'classes.barbarian.1'
def load(suffix):
    return json.loads((HERE/(PREFIX+'.'+suffix+'.json')).read_text(encoding='utf-8'))
audit = load('upload-audit')
assert audit['complete'] and audit['all_targets_unchanged']
info, response, statistics = load('verification'), load('upload-response'), load('statistics-latest')
assert hashlib.sha256((HERE/(PREFIX+'.upload.json')).read_bytes()).hexdigest() == info['sha256']
info.update(approved=True, approval_date='2026-10-08', uploaded=True, uploaded_date='2026-10-08', method='suggest', accepted=18, skipped=25, not_found=0, all_targets_unchanged=True)
(HERE/(PREFIX+'.verification.json')).write_text(json.dumps(info,ensure_ascii=False,indent=1),encoding='utf-8')
report = [
    '# 野蠻人第1批 v1 上傳報告', '',
    '日期：2026-10-08。使用者在看過v1预覽及「既有譯文只送建議、不直接覆寫」的說明後，明確指示「上傳」。', '',
    '目標：`dnd-players-handbook / dnd-players-handbook-classes / zh_Hant`。',
    '檔案路徑：`compendium/zh-tw/dnd-players-handbook/dnd-players-handbook.classes.json`；push URL已設定。',
    '上傳前儲存庫needs_commit=true、needs_merge=true、needs_push=false、merge_failure=null；只寫入建議，沒有pull、merge、commit或push。', '',
    '## 確認版本及結果', '',
    f'- 10條、43個字串；SHA-256：`{info["sha256"]}`。',
    '- method=suggest；HTTP 200；accepted=18、skipped=25、not_found=0。',
    '- API的total/count=2209是整个元件字串數；本批43個字串由18+25核對吻合。',
    '- 25個跳過字串逐項確認為現行target與本批中文完全相同，無需重複產生建議。',
    '- 18個新增建議逐項確認：上傳前無建議、上傳後有建議；現行target保持不變。',
    '- 全部43個字串的source及target在上傳前後完全相同。只有建議佇列新增內容。', '',
    '## 四項驗收', '',
    '- 規則核對：已核對主體、条件、數值、次數及持續時間。原稿否定誤譯與既有無甲防禦／武器精通錯譯的修正，詳見v1預覽。原初知識Foundry註記忠實保留上游調整值／屬性值比較。',
    '- 術語核對：terms、spells-glossary、lang三方查核及逐處回查已完成；野性直覺與Foundry補翻隨本批v1由使用者確認。沒有新增正式術語。',
    '- 機械驗證：10條43字串通過；正文及巢狀description保留HTML骨架、UUID、Reference、巨集；逐欄比對Weblate現行EN成功。',
    '- 中文通讀：完整底稿獨立通讀，映射去標記後與底稿逐字相同。', '',
    '## 範圍及詳細紀錄', '',
    f'- [來源行號、原稿修改、規則差異、三方術語、全部補翻與巢狀欄位對照]({DONE/(PREFIX+".preview.md")})',
    f'- [中文底稿]({DONE/(PREFIX+".draft.txt")})',
    f'- [確認版本payload]({DONE/(PREFIX+".upload.json")})',
    f'- [逐字串上傳稽核]({DONE/(PREFIX+".upload-audit.json")})',
    f'- [全頁來源索引]({HERE/"classes.barbarian.index.md"})', '',
    '## 剩餘範圍', '',
    f'- 第2批來源已拆分為9條，共{statistics["next_batch_strings"]}個EN字串；其中{statistics["next_batch_empty_or_source"]}個現行target仍為空或與source相同。尚未順稿、預覽或上傳。',
    f'- 整個classes元件共{statistics["component_total"]}個字串，其中{statistics["component_empty_or_source"]}個target為空或與source相同；建議未接受前不計為完成譯文。',
    '- 等級表、子職業與屬性值提升的職業说明保留於完整網頁原稿，尚未做content元件匯入。',
    '- 本次沒有未匹配、部分成功或未確認的上傳內容。', '',
    '完整網頁來源與第2批原稿保留在原目錄；第一批成功產物歸檔至_done。',
]
text = '\n'.join(report)+'\n'
for old,new in [('预覽','預覽'),('整个','整個'),('条件','條件'),('说明','說明')]:
    text = text.replace(old,new)
(HERE/(PREFIX+'.2026-10-08.report.md')).write_text(text,encoding='utf-8')

DONE.mkdir(exist_ok=True)
files = list(HERE.glob(PREFIX+'.*'))
for source in files:
    destination = DONE/source.name
    assert source.resolve().parent == HERE.resolve()
    assert destination.resolve().parent == DONE.resolve()
    assert DONE.resolve().parent == HERE.resolve()
    assert source.is_file() and not destination.exists(), destination
for source in files:
    source.rename(DONE/source.name)

# Update only artifact links in the historical preview; preserve the approved
# payload, translations and checksum exactly.
preview = DONE/(PREFIX+'.preview.md')
contents = preview.read_text(encoding='utf-8')
for source in files:
    contents = contents.replace(str(source),str(DONE/source.name))
preview.write_text(contents,encoding='utf-8')
index = HERE/'classes.barbarian.index.md'
index.write_text(index.read_text(encoding='utf-8').replace('第1批已預覽','第1批已送出建議，2026-10-08'),encoding='utf-8')
assert hashlib.sha256((DONE/(PREFIX+'.upload.json')).read_bytes()).hexdigest() == info['sha256']
print(json.dumps({'archived_files':len(files),'report':str(DONE/(PREFIX+'.2026-10-08.report.md')),'next_batch_strings':statistics['next_batch_strings'],'next_batch_empty_or_source':statistics['next_batch_empty_or_source'],'component_empty_or_source':statistics['component_empty_or_source']},ensure_ascii=False))
