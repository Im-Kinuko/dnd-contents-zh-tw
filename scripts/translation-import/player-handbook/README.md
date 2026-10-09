# 玩家手冊翻譯執行腳本

批次執行腳本統一放在本目錄；來源、底稿、預覽及上傳證據仍放在 `_incoming/player-handbook/`。

腳本以自身路徑解析 repo 根目錄，不依目前 shell 的工作目錄。已歸檔批次的歷史腳本保留作流程追溯；子職業批次的讀取、準備、上傳及歸檔集中於 `subclasses.py`。共用技能工具仍使用 `.claude/skills/translation-import/scripts/`。

`subclasses.py` 目前對應狂戰士道途第1批v1。準備階段為 `collect`、`prepare`、`map`、`review`；使用者確認後依序執行 `preflight`、`upload-classes`、`upload-content`、`audit`、`archive`，只使用 `method=suggest`。上傳回應檔存在時禁止直接重傳。

本批已完成歸檔至 `_incoming/player-handbook/_done/subclasses/berserker/`，歷史操作不應重新執行。下一批需先設定其獨立範圍與使用者確認版本。

`world-tree.py` 對應世界樹道途第3批v1。2026-10-09依使用者確認補足效果摘要的速度0，重新抽取新版advancement.name，保留既有5個正文區塊，完成22個建議（classes20＋content2）上傳。驗收與稽核完成後歸檔至 `_incoming/player-handbook/_done/subclasses/world-tree/`；歷史操作不要重新執行。各階段為collect、search、prepare、map_draft、review、preflight、upload_classes、upload_content、audit_upload、archive，只使用method=suggest。

`compare-latest-classes.py --refresh-live` 重新讀取Weblate英文並比較工作區classes.json。以完全吻合API來源的歷史Git版本為基準，避免工作途中HEAD更新造成錯誤比較。只產出 `_incoming/player-handbook/subclasses/world-tree/` 的完整中英文版本報告與快照，不修改EN、翻譯、建議或Git狀態。

`wild-heart.py` 對應狂野之心道途第2批：準備階段為 `collect`、`prepare`、`map`、`compare`、`review`，確認後依序執行 `preflight`、`upload-classes`、`upload-content`、`audit`、`archive`。v2按使用者明示修正後已上傳28個建議，成功產物歸檔至 `_incoming/player-handbook/_done/subclasses/wild-heart/`，v1未上傳的歷史預覽位於其中 `versions/v1/`。原稿及無對應EN欄位的譯註保留於 `_incoming/player-handbook/subclasses/wild-heart/`；已歸檔操作不應重新執行。

`zealot.py` 對應狂熱者道途第4批v1，準備階段為 `collect`、`search`、`prepare`、`map`、`review`、`verify-preview`；使用者明確確認後依序執行 `preflight`、`upload-classes`、`upload-content`、`audit`、`archive`。2026-10-09依使用者「目前沒甚麼問題，可以上傳」確認，已送出26個建議（classes24＋content2），跳過0、未匹配0；全部3431個API單元正式譯文未變。來源、底稿、完整中英差異及上傳證據已歸檔至 `_incoming/player-handbook/_done/subclasses/zealot/`。歷史操作不要重新執行；上傳attempt／response存在時禁止盲目重傳。`prepare`每次先重新extract，避免映射後的中文嵌套欄位誤當EN檢查來源。`verify-preview`重新讀全量Weblate，確認本批EN及正式譯文未變、payload雜湊一致。

`warlock.py` 對應魔契師（契術師）classes 第1批與 content 第2批。子命令：`classes`（extract→fill→build→validate→合併升級項目名稱，產出 `classes.warlock.1.upload.json`）、`checks`（terms／draft_diff／lang_compare／路徑稽核）、`content`（日誌頁面 name／description／subclass 與子職業頁面名稱，產出 `content.warlock.2.upload.json`）。只產 payload，不上傳；上傳仍用 `.claude/skills/translation-import/scripts/weblate.py upload … --method suggest`，且須使用者確認。使用者 2026-10-09 指示：執行用腳本一律放在 `scripts/`。

`rogue.py` 對應遊蕩者 classes 第1–2批與 content 第3批，匯入 `warlock.py` 的共用函式。子命令 `prep`（原稿轉繁與整理、術語索引）、`classes`、`checks`、`content`；只產 payload，不上傳。

`rogue-subclasses.py` 對應遊蕩者四個子職業整批 v1；`rogue-subclasses-draft.py` 保存從原稿及既有譯文整理底稿的規則。準備階段為 `collect`、`scope`、`inspect`、`search`、`prepare`、`map_draft`、`checks`、`review`、`preview`、`verify_preview`。本批共25個classes條目與8個content頁面，2026-10-09依使用者「好像也沒甚麼問題，可以上傳」確認，已送出100個建議（classes92＋content8），跳過0、未匹配0。`rogue-subclasses-upload.py` 提供 `preflight`、`prepare_inspection`、`record_before`、`upload_classes`、`upload_content`、`record_after`、`audit`、`archive`；只用 `method=suggest`，實際100個建議內容已逐一核對。產物歸檔於 `_incoming/player-handbook/_done/subclasses/rogue/`。原稿詭術師施法表在EN/API沒有對應單元，因此原稿與 `rogue.subclasses.remaining.txt` 保留於 `_incoming/player-handbook/`。歷史操作不要重新執行；存在upload-attempt／response時禁止盲目重傳。

## 整理（2026-10-09）
- 已完成的批次資料（`_incoming/player-handbook` 內）已全數刪除；`history/` 已移除。
- 現行範本：`ranger.py`／`monk.py`（FULL／KEEP 條目、nested 欄位、拆批、`checks`、`content`）；`warlock.py` 提供共用函式（`read_draft`、`live`、`jload`、`jdump` 等，其他腳本 import 之）；`sorcerer.py` 提供 `fix_labeled`（補未標籤 `@UUID`、環階國字）；`rogue.py` 同 ranger 結構。子職業範本：`rogue-subclasses*.py`、`warlock-subclasses*.py`。
- `cleanup.py`：整理 `_incoming/player-handbook`（預設 dry run，`--apply` 執行）；在新批次累積後可再用。
- 其餘 `archive-*`、`upload-*`、`review-*`、`world-tree.py`、`zealot.py`、`wild-heart.py`、`subclasses.py`、`content_condition.py` 為野蠻人／條件頁的歷史腳本，依賴的資料已刪除，不要重新執行；確定不需要時可刪。
- 建議的下一步見 `class-import-playbook.md` 第 4 節（通用 `class_import.py`、`legacy_audit.py`、`review_diff.py`）。
