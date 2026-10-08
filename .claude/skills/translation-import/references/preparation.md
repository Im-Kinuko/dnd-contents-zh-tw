# 來源準備與新書骨架

只在對應分支讀取本檔。

## PDF

以 `pdftotext -layout` 逐頁抽出文字，放到 `_incoming/<book>/_extracted/p###.txt`，依章節分派到 component txt，清除頁首頁尾頁碼並接回跨頁斷行。保留頁碼／行號來源，讓使用者可回查。

抽取完成後交使用者檢查；未確認的抽取結果不當成可靠譯稿繼續匯入。`extract` 模式到此結束。處理 PDF 時使用可用的 PDF 技能與工具，完成抽取不代表語意或章節對齊已通過。

## 新書第一次

只有當 `compendium/zh-tw/<book>/` 缺少目標檔案時使用此分支。先讀 `weblate-notes.md`，確認這個實例的路徑行為。

```bash
python .claude/skills/translation-import/scripts/make_skeleton.py <book>
```

產生 `label`、`folders`、`mapping` 與空 `entries` 的 zh-tw 骨架，提供 diff，由使用者 commit 並 push。再依 Weblate 筆記 pull／重新掃描，確認翻譯物件 `filename` 為 `compendium/zh-tw/...`。

順序為 git 骨架先、Weblate 上傳後，否則 Weblate 可能自行建立 `zh_Hant` 路徑，Foundry 不會讀取。`mapping` 也只能由 git 放入，不能透過翻譯上傳 API 寫入。
