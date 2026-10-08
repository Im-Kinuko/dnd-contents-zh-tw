# 玩家手冊翻譯執行腳本

批次執行腳本統一放在本目錄；來源、底稿、預覽及上傳證據仍放在 `_incoming/player-handbook/`。

腳本以自身路徑解析 repo 根目錄，不依目前 shell 的工作目錄。已歸檔批次的歷史腳本保留作流程追溯；子職業批次的讀取、準備、上傳及歸檔集中於 `subclasses.py`。共用技能工具仍使用 `.claude/skills/translation-import/scripts/`。

`subclasses.py` 目前對應狂戰士道途第1批v1。準備階段為 `collect`、`prepare`、`map`、`review`；使用者確認後依序執行 `preflight`、`upload-classes`、`upload-content`、`audit`、`archive`，只使用 `method=suggest`。上傳回應檔存在時禁止直接重傳。

本批已完成歸檔至 `_incoming/player-handbook/_done/subclasses/berserker/`，歷史操作不應重新執行。下一批需先設定其獨立範圍與使用者確認版本。

`world-tree.py` 對應世界樹道途第3批v1。2026-10-09依使用者確認補足效果摘要的速度0，重新抽取新版advancement.name，保留既有5個正文區塊，完成22個建議（classes20＋content2）上傳。驗收與稽核完成後歸檔至 `_incoming/player-handbook/_done/subclasses/world-tree/`；歷史操作不要重新執行。各階段為collect、search、prepare、map_draft、review、preflight、upload_classes、upload_content、audit_upload、archive，只使用method=suggest。

`compare-latest-classes.py --refresh-live` 重新讀取Weblate英文並比較工作區classes.json。以完全吻合API來源的歷史Git版本為基準，避免工作途中HEAD更新造成錯誤比較。只產出 `_incoming/player-handbook/subclasses/world-tree/` 的完整中英文版本報告與快照，不修改EN、翻譯、建議或Git狀態。

`wild-heart.py` 對應狂野之心道途第2批：準備階段為 `collect`、`prepare`、`map`、`compare`、`review`，確認後依序執行 `preflight`、`upload-classes`、`upload-content`、`audit`、`archive`。v2按使用者明示修正後已上傳28個建議，成功產物歸檔至 `_incoming/player-handbook/_done/subclasses/wild-heart/`，v1未上傳的歷史預覽位於其中 `versions/v1/`。原稿及無對應EN欄位的譯註保留於 `_incoming/player-handbook/subclasses/wild-heart/`；已歸檔操作不應重新執行。

`zealot.py` 對應狂熱者道途第4批v1，準備階段為 `collect`、`search`、`prepare`、`map`、`review`、`verify-preview`；使用者明確確認後依序執行 `preflight`、`upload-classes`、`upload-content`、`audit`、`archive`。2026-10-09依使用者「目前沒甚麼問題，可以上傳」確認，已送出26個建議（classes24＋content2），跳過0、未匹配0；全部3431個API單元正式譯文未變。來源、底稿、完整中英差異及上傳證據已歸檔至 `_incoming/player-handbook/_done/subclasses/zealot/`。歷史操作不要重新執行；上傳attempt／response存在時禁止盲目重傳。`prepare`每次先重新extract，避免映射後的中文嵌套欄位誤當EN檢查來源。`verify-preview`重新讀全量Weblate，確認本批EN及正式譯文未變、payload雜湊一致。
