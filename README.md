# DND5E 遊戲內容 — 正體中文

為 Foundry VTT 的 D&D 5e 遊戲內容提供正體中文（透過 Babele）。需要模組：`babele`、`lib-wrapper`；系統：`dnd5e`。翻譯在 Weblate 進行，這個 repo 保存輸出檔。

## 目錄

```
module.json  register.js    模組本體（Foundry 讀取）
lang/zh-tw.json             dnd5e 介面翻譯（變更紀錄見 Changelog.md）
compendium/en | zh-tw/<書>/ Babele 翻譯檔（Weblate 的 filemask 指向這裡，不要搬動）
Changelog.md                lang/zh-tw.json 的變更紀錄
.github/                    發佈流程（只打包上面四項）
```

## 發佈

在 GitHub 建立 release 後，`.github/workflows/release.yml` 會把 `module.json`、`register.js`、`lang/zh-tw.json` 與 `compendium/zh-tw` 打包成 `dnd-contents-zh-tw.zip`。

開發用的腳本、測試與翻譯工作區（`dev/`、`.claude/`、`.agents/`、`_incoming/`）只存在本機，已列入 `.gitignore`，不會進入 repo 或發佈版。
