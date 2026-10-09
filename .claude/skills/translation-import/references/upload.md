# 已確認批次的上傳與歸檔

執行本分支前讀 [weblate-notes.md](weblate-notes.md)。這是對特定批次版本的上傳，不包含新增術語、刪除建議或其他維護。

## 前置與版本

```bash
python .claude/skills/translation-import/scripts/weblate.py status <project> <component-slug>
```

核對 push URL、未推送變更及 `zh_Hant` 的 filename。路徑必須是 `compendium/zh-tw/...`；讀取失敗或路徑不符時先停止上傳並處理。不要只看 status 的 exit code，現有腳本有些問題只印警告。

核對使用者確認的條目、譯文與本次 payload；譯文修改或新增內容後重新預覽。將 payload SHA-256 記入預覽／報告，可用來辨識版本；雜湊是版本資料，不能代替使用者的確認。

## 上傳

```bash
python .claude/skills/translation-import/scripts/weblate.py upload <project> <component> upload.json --method suggest
```

只使用 `suggest`。現有通用 helper 仍提供其他方法，不代表本技能允許使用。檢查 HTTP 狀態與 accepted、skipped、not_found、total；skipped 可能是已存在相同建議或譯文，須核對而非一律當成功。

回應不明或失敗時保留檔案、列出已知狀態；先查建議是否已寫入，再決定是否重試，避免盲目重傳。部分成功按條目／字串記錄，不把未匹配內容歸為完成。

`suggest` 送入審閱佇列，使用者以 `has:suggestion` 篩出、接受後由 Weblate 寫入翻譯檔。新建術語需要獨立的使用者明示範圍。保留禁止刪除 Weblate translation 的約束，原因見實例筆記。

## 收尾

確認本批已成功處理後，將本批原稿、底稿及報告歸檔到 `_incoming/<book>/_done/`。來源檔含有未完成條目時保留原稿，按範圍歸檔成功產物、另寫 remaining，避免移走仍待處理的內容。

未確定 key、結構無法對齊、未裁定規則或術語等，以 `### English Name` 留在 `<component>.<批次>.remaining.txt`。報告為 `<component>.<批次>.<日期>.report.md`，記錄：

- 條目與來源對照、原稿到底稿的修改、規則差異。
- 術語核對、自行補翻、condition 的 EN／中文對照和待裁定項目。
- 四項驗收結果、使用者確認的版本、payload 雜湊和上傳回應。
- 成功、跳過、待確認與未匹配範圍，以及還剩多少字串未翻。

未翻數依 Weblate 狀態或 source／target 核對，不依翻譯檔是否有值判斷；這個實例會用英文補滿未翻字串。

## 取代已上傳的舊建議（只在使用者明示範圍時）

重做已上傳的批次時，Weblate 審閱佇列會同時有新舊兩版。清除舊版需要使用者明示「清除哪一批」；範圍以使用者指定的條目為限，不擴及其他批次。

1. **先列後刪**：用 Weblate 管理 shell 列出範圍內每個 unit 的建議（建議 id、context、建立者、是否與舊 payload 的同欄位文字完全相同）。只刪「與舊 payload 完全相同」的建議；有任何一條不同（例如使用者在網頁上改過）停下來回報。
2. **腳本從 stdin 送入**：容器 root 檔案系統唯讀，`docker cp` 會失敗；把腳本內容（含舊 payload 以 JSON 字串嵌入）用管線送給 `docker exec -i weblate-docker-weblate-1 weblate shell`。
3. **刪除**：以 `Suggestion.delete()` 逐條刪除；再次列出，確認範圍內剩 0 條。這只動建議，不動翻譯，也不使用 `DELETE /api/translations/…`（見 weblate-notes.md）。
4. **刪完再上傳新版**：新舊字串相同者會被視為已存在而跳過（`skipped`），先刪舊再上傳可避免新版被舊建議吃掉。
5. **核對**：上傳回應的 `accepted + skipped` 等於 payload 字串數；範圍內建議數等於新版字串數。

補充（2026-10-09）：用 `Unit`／`Suggestion`（`weblate.trans.models`）以 unit id 列出；腳本請寫在專案目錄內，再 `docker exec -i weblate-docker-weblate-1 weblate shell < 腳本.py`；不要寫到 `/tmp`（Git Bash 與 Windows Python 的路徑不同）。
