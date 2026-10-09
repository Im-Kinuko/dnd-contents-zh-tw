# Horror Within 翻譯腳本

所有執行腳本放在本目錄，批次資料放在 `_incoming/horror-within/grave-domain/`。沿用 player-handbook README 與 class-import-playbook 的保留既有譯文、處理巢狀欄位及預覽確認流程。

`grave-domain.py` 只準備翻譯，不提供上傳功能。依序執行 `discover`、`collect`、`search`、`prepare`、`map_draft`、`checks`、`review`、`preview`、`verify_preview`。`inspect` 提供現行術語與來源行號。`grave-domain-draft.py` 保存原稿及既有譯文的底稿修訂；先產底稿再映射，不在映射時另寫中文。

墳墓領域整批 v1 已於 2026-10-09 依使用者「bloodied用重傷；其他沒什麼問題，可以上傳」確認，送出 13 個建議，跳過 0、未匹配 0。6 條、31 個完整欄位中，18 個既有欄位與資料夾名稱照舊；7 個英文欄位屬司命神使，其餘 6 個是必要的規則／定案詞／標記修正。內嵌法術表已涵蓋。Bloodied 兩處原已使用重傷，核准 payload 無需修改。

`grave-domain-upload.py` 提供 `preflight`、`inspect_before`、`upload`、`inspect_after`、`audit`、`archive`，只用 `method=suggest`；`grave-domain-suggestions.py` 為唯讀 Django 建議全文查詢。531 個 API 單元與 13 個實際建議已逐項核對。成功產物歸檔於 `_incoming/horror-within/_done/grave-domain/`；原稿及 `grave-domain.remaining.txt` 因缺少日誌 EN 元件保留。這些歷史操作不要重新執行，已有 upload-attempt／response 時禁止盲目重傳。

實際 API project：`dnd-ravenloft-horros-within`；component：`dnd-ravenloft-horrors-within-options`。本書目前僅 options／glossary，無 book／content／tables EN 元件；子職業細節連結所指的 `GraveDomainCleri` 日誌頁保留待上游提供結構，不能記為完成。

下一批須另行定義範圍、建立預覽並取得使用者確認，才依技能 upload 規範以 `method=suggest` 上傳。不要重跑其他書的歷史上傳或清理腳本；不得改動正式譯文或刪除既有建議。
