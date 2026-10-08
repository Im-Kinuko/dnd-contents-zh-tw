"""Archive the successful journal batch, keeping unresolved source at hand."""
import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / '_incoming/player-handbook'
DONE=HERE/'_done'
PREFIX='content.barbarian.3'
def load(suffix):
    return json.loads((HERE/(PREFIX+'.'+suffix+'.json')).read_text(encoding='utf-8'))
def save(suffix,value):
    (HERE/(PREFIX+'.'+suffix+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=1),encoding='utf-8')
audit,info,response,stats,approval,preflight=[load(s) for s in ['upload-audit','verification','upload-response','statistics-latest','approval','preflight']]
assert audit['complete'] and audit['all_targets_unchanged'] and approval['approved']
assert info['version']=='v1'
assert hashlib.sha256((HERE/(PREFIX+'.upload.json')).read_bytes()).hexdigest()==info['sha256']==approval['sha256']
accepted,skipped=len(audit['accepted']),len(audit['skipped'])
assert accepted==4 and skipped==1 and response['response']['not_found']==0
info.update(approved=True,approval_date='2026-10-08',uploaded=True,uploaded_date='2026-10-08',method='suggest',accepted=accepted,skipped=skipped,not_found=0,all_targets_unchanged=True,component_verified_strings=audit['component_verified_strings'])
save('verification',info)
issues=load('issues')
for item in issues:
    if item['id'] in ['I01','I02','I03','I04','I05','I06']:
        item['status']='使用者於2026-10-08確認第3批v1，對應欄位已以建議上傳。'
save('issues',issues)
def link(suffix,label,archived=True):
    parent=DONE if archived else HERE
    return '['+label+']('+str(parent/(PREFIX+'.'+suffix)).replace('\\','/')+')'
repo=preflight['repository']
report=[
 '# 野蠻人第3批 v1上傳報告','','日期：2026-10-08。使用者看過第3批v1底稿、完整預覽及中英文問題清單後，明確指示「上傳」。確認後未修改譯文或新增欄位。','',
 '目標：`dnd-players-handbook / dnd-players-handbook-content / zh_Hant`。',
 '檔案路徑：`compendium/zh-tw/dnd-players-handbook/dnd-players-handbook.content.json`；push URL已設定。',
 '上傳前儲存庫狀態：'+json.dumps(repo,ensure_ascii=False)+'。本次以建議送出，沒有pull、merge、commit或push。','',
 '## 確認版本及結果','',
 f'- 1個Barbarian日誌條目、1個Barbarian頁面、5個字串；SHA-256：`{info["sha256"]}`。',
 f'- method=suggest，HTTP {response["http_status"]}；accepted={accepted}、skipped={skipped}、not_found=0。',
 '- 跳過字串`entries.Barbarian.name`的现行譯文為「野蠻人」，與payload完全相同。',
 '- 四個新增建議：頁面name、subclassHeader、description及subclass。上傳前均無建議，上傳後有建議；source及target保持不變。',
 f'- 整個content元件{audit["component_verified_strings"]}個字串的source及target在上傳前後完全相同；沒有覆寫已完成譯文。',
 '- API total/count=1161是元件總數；本批5個字串由4個新增建議＋1個相同譯文跳過核對吻合。','',
 '## 四項驗收','',
 '- 規則核對：主體、some／others／every、all與following，以及1級角色／兼職所得特質逐句核對。content子職業導讀較完整3級原稿短，I05完整列出範圍差異；使用者確認本批導讀。沒有把缺少EN欄位的表格及職業能力句加入payload。',
 '- 術語核對：本次完整取讀terms136筆、spells-glossary640筆、classes2209筆及content1161筆，分頁HTTP 200核對count；lang每個命中逐項說明。四個道途採現行2024名稱，獸心道途改用狂野之心道途；未新增正式術語或修改lang。',
 '- 機械驗證：5個實際巢狀欄位與現行Weblate EN完全相同；使用skeleton.build_entries及validate.check_description覆蓋全部實際pages欄位。16個映射位置（14個可見中文、2個保留Embed）与獨立底稿逐字相同；HTML、UUID、Embed目標及參數保留。',
 '- 中文通讀：職業介紹完全沿用第一批已確認來源底稿；子職業段落從原稿特化、等級與清單順稿，映射未另造句。全部20組完整中英文及限定詞已列出。','',
 '## 來源、差異及補翻','',
 '- 成品正文來源為原網頁19–30行；subclass與subclassHeader來源為186–187行，名稱來源為第2行。兼職最後一句的正確來源是第30行，已修正來源索引。',
 '- I01–I04是相同介紹原稿的EN／術語回查，沿用第一批確認底稿；I05–I06為導讀範圍與現行道途名稱差異。本批確認及上傳只涉及上述5個欄位。',
 '- 本批沒有Foundry正文補翻或activities.condition。兩個原網頁沒有的插圖Embed沒有可見文字，原始命令完整保留。','',
 '## 全面對照及上傳證據','',
 '- '+link('preview.md','確認版本預覽、來源行號及三方術語說明'),
 '- '+link('draft.txt','獨立中文底稿'),
 '- '+link('issues.md','全部8項差異及未匹配來源：完整中英文'),
 '- '+link('full-comparison.md','16個映射位置與20組完整中英文逐句對照'),
 '- '+link('upload.json','確認版本payload'),
 '- '+link('upload-audit.json','逐字串及整個元件上傳稽核'),
 '- '+link('remaining.txt','仍待處理的完整來源',False),'',
 '## 剩餘範圍','',
 '- 本批5個payload字串全部匹配，沒有部分成功或未確認的上傳內容；I07／I08的未匹配來源不在payload，未標完成。',
 f'- 本批仍有{stats["batch_empty_or_source"]}個現行target為英文或空值；建議未接受前不計為完成譯文。content元件共{stats["component_total"]}個字串，其中{stats["component_empty_or_source"]}個target為空或與source相同。',
 '- 原網頁31–159行職業特性引介與等級表、192–193行屬性值提升職業說明沒有獨立EN欄位；來源保留於原目錄remaining.txt，不新增不存在的key。原稿3級子職業段落中超出EN導讀的句子亦完整保留。',
 '- 四個子職業連結頁尚未抓取或處理；完整原網頁及共同來源索引保留於原目錄。第一、第二批已上傳建議未修改。',
]
text='\n'.join(report).replace('现行','現行').replace('）与','）與')+'\n'
(HERE/(PREFIX+'.2026-10-08.report.md')).write_text(text,encoding='utf-8')

# Status-only updates preserve the exact approved payload and all source quotes.
preview=HERE/(PREFIX+'.preview.md')
text=preview.read_text(encoding='utf-8').replace('**未上傳，待本批v1確認。**','**使用者已確認v1並以suggest上傳：4個新增建議、1個相同譯文跳過、0個未匹配。**')
text=text.replace('用詞及限定詞回查完成，待本批確認。','用詞及限定詞回查完成，本批v1已確認。')
text=text.replace('本批停在可供審查的v1預覽。','本批v1已由使用者明確確認，並完成建議上傳與核對。')
preview.write_text(text,encoding='utf-8')
problem=HERE/(PREFIX+'.issues.md')
problem.write_text(problem.read_text(encoding='utf-8').replace('狀態：本批v1待確認；重複正文採第一批已確認底稿。','狀態：使用者於2026-10-08確認第3批v1，對應欄位已以建議上傳。'),encoding='utf-8')
page=HERE/(PREFIX+'.preview.html')
page.write_text(page.read_text(encoding='utf-8').replace('待確認，未上傳','已確認並以建議上傳：4新增／1相同譯文跳過'),encoding='utf-8')

DONE.mkdir(exist_ok=True)
remaining=HERE/(PREFIX+'.remaining.txt')
assert remaining.is_file()
files=[p for p in HERE.glob(PREFIX+'.*') if p!=remaining]
for source in files:
    destination=DONE/source.name
    assert source.resolve().parent==HERE.resolve()
    assert destination.resolve().parent==DONE.resolve() and DONE.resolve().parent==HERE.resolve()
    assert source.is_file() and not destination.exists(),destination
for source in files:source.rename(DONE/source.name)
for suffix in ['preview.md','full-comparison.md','issues.md']:
    path=DONE/(PREFIX+'.'+suffix)
    text=path.read_text(encoding='utf-8')
    for source in files:
        text=text.replace(str(source),str(DONE/source.name))
        text=text.replace(str(source).replace('\\','/'),str(DONE/source.name).replace('\\','/'))
    path.write_text(text,encoding='utf-8')
index=HERE/'classes.barbarian.index.md'
index.write_text(index.read_text(encoding='utf-8').replace('第3批v1已預覽，未上傳','第3批v1已送出建議，2026-10-08'),encoding='utf-8')
assert remaining.is_file()
assert hashlib.sha256((DONE/(PREFIX+'.upload.json')).read_bytes()).hexdigest()==info['sha256']
print(json.dumps({'archived_files':len(files),'remaining_preserved':str(remaining),'report':str(DONE/(PREFIX+'.2026-10-08.report.md')),'accepted':accepted,'skipped':skipped,'not_found':0},ensure_ascii=False))
