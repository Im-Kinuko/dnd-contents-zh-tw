---
name: translation-import
description: 將既有中文譯稿依底稿、規則精確度與台灣閱讀語順整理成 Babele JSON，預覽確認後以建議送入 Weblate。由使用者明確呼叫時執行。
---

# translation-import 入口

從 repo 根目錄讀取 [.claude/skills/translation-import/SKILL.md](../../../.claude/skills/translation-import/SKILL.md)，按該檔的流程執行。它是本技能的唯一規則來源。

所有腳本、參考資料與 glossary.tsv 均使用 `.claude/skills/translation-import/` 下的一份。參考文件的相對連結相對於該資料夾解析；不在這裡複製規則。

討論或重製本技能只處理技能文件與工具；實際匯入以使用者指定來源與批次為範圍。
