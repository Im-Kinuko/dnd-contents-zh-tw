---
name: translation-import
description: 將既有中文譯稿依底稿、規則精確度與台灣閱讀語順整理成 Babele JSON，預覽確認後以建議送入 Weblate。由使用者明確呼叫時執行。
disable-model-invocation: true
---

# translation-import

中文以既有譯稿（**原稿**）為底，核對規則與定案詞後產出**底稿**，再整段映射到 EN 的區塊結構。**底稿決定中文句子；EN 決定規則語意與技術目標，不決定中文語序；定案詞（terms、現行法術名、使用者裁定）決定用字。**

三個固定用語：

- **原稿**：使用者提供的中文來源（簡體先 OpenCC `s2twp` 轉繁）。
- **底稿**：`<批次>.draft.txt`。由原稿逐段產生，每個修改都登記類別與理由；映射時中文只從底稿取。
- **定案詞**：已有裁定的用字，優先序見 [references/translation-quality.md](references/translation-quality.md)「優先序」。

討論、檢查或重製此技能時，只處理技能文件與工具；實際匯入以使用者指定的來源、component 和批次為範圍。

本檔是流程的唯一來源。`.agents/skills/translation-import/SKILL.md` 是入口；所有腳本與參考資料均位於 repo 根目錄下的 `.claude/skills/translation-import/`，以下指令都從 repo 根目錄執行，以 `$S` 表示 `.claude/skills/translation-import/scripts`。

## 呼叫與範圍

| 呼叫 | 工作範圍 |
|---|---|
| `/translation-import` | 列出 `_incoming/` 待處理來源，等待使用者指定 |
| `/translation-import <book> <component> [批次]` | 準備指定批次的底稿、JSON 與預覽 |
| `/translation-import <book> extract` | 只抽取 PDF、整理 component txt，交付後結束 |

支援 feats、backgrounds、spells、subclasses、items、bastions；tables（DMG RollTable，results 每列一塊）已支援；actors 回報尚未支援，不套用本流程。檔名不能確定範圍時，先列出候選讓使用者選擇。每批最多 10 條或 60 個字串，先達上限即拆批；單條超限時保持條目完整，單獨預覽並說明。

批次來源通常為 `_incoming/<book>/<component>.<批次>.txt`，相關產物留在同一目錄。使用者指定其他來源時沿用其路徑，不自行搬動來源。網頁來源先交由 `/web-source-extract` 產出 txt；PDF 操作讀 [references/preparation.md](references/preparation.md)。

Weblate 的 project 與 component 名稱以 API 為準（component slug 常帶 project 前綴，例如 `dnd-tashas-cauldron-tcoe-magic-items`），規則見 [references/weblate-notes.md](references/weblate-notes.md)「名稱」。

## 1. 確認來源與條目

以 EN key 清單對照原稿標題，或用 `### English Name` 明確指定邊界。列出每個 EN 條目的歸類：

- **有原稿**：記原稿行號。原稿段落與 EN 區塊可能合併、拆分或順序不同，記下對應。
- **無原稿**：EN 有而原稿沒有的條目或段落（附屬法術、Foundry 註記、欄位文字）。
- **EN 缺漏**：原稿有而 EN 沒有。

精確匹配可繼續；模糊匹配、範圍不明或 EN 缺漏列為問題，等使用者裁定受影響條目，其餘確定條目可繼續。

完成條件：本批每條都有「有原稿（行號）」或「無原稿」的歸類與 EN key；未確定項目分開列出，不混入待上傳內容。

## 2. 術語查核與底稿

先讀 [references/translation-quality.md](references/translation-quality.md) 與 [references/conventions.md](references/conventions.md)。前者定義優先序、允許的修改類別與檢查；後者保存使用者已裁定的譯名和語境例外。

### 2.1 準備資料

```bash
python $S/weblate.py samples <project> <component>
python $S/build_index.py --skip-book <book> --out <批次>.term_index.json
python $S/spell_names.py --out spell-names.json      # 批次含法術名時
python $S/skeleton.py extract --book <book> --component <component> --keys "Entry A" "Entry B" --out sheet.json
```

`sheet.json` 保存本批的 EN 區塊與欄位，2.3 的比對與第 3 步的映射共用它；EN 變動時重新 `extract`。

讀取失敗記「術語集未核實」，不記「查無」。`spell_names.py` 取的是 Weblate 現行名稱；repo 的 zh-tw 檔常未同步。

### 2.2 產出底稿

底稿由原稿逐段產生，並**先於**任何 `blocks[].zh`。原句保留；只在 [translation-quality.md](references/translation-quality.md)「允許的修改類別」六類之內改動，每處改動登記 `原→新｜類別｜理由`。原稿段落與 EN 區塊的合併、拆分、重排也登記。

- 原稿用字和 terms 衝突時，用 terms（含普通動詞與片語，例如 take→承受）。
- 原稿與 EN 語意衝突時，依 EN 修正並列入預覽的規則差異。
- 原稿缺漏的內容，依 [translation-quality.md](references/translation-quality.md)「無原稿內容的來源順序」處理：先找 Weblate 既有譯文，查無才自譯。
- 每條用 `### English Name`，保留逐段對照；`+1/+2/+3` 這類內容相同的版本各自一節。

### 2.3 檢查底稿

```bash
python $S/draft_diff.py --source <原稿轉繁>.txt --draft <批次>.draft.txt --supplements "<整條無原稿的條目>" --out draft-diff.md
python $S/terms_check.py sheet.json --draft <批次>.draft.txt --index <批次>.term_index.json --names spell-names.json --ack ack.json --out terms-report.md
python $S/lang_compare.py sheet.json --draft <批次>.draft.txt
```

- `draft_diff.py`：列出每個底稿段對原稿的相似度與差異片段。「改動大」逐項寫理由；「無原稿」只允許出現在 `--supplements` 列出的條目，其餘視為底稿脫離原稿，退回 2.2。
- `terms_check.py`：把 Weblate `terms` 與現行法術名對 EN 可見文字（含 activities、effects、advancement）做詞形展開比對，未含中文詞者為 ❌。每個 ❌ 先修底稿；確為一般用字（例如 `takes 10 minutes`）的，才在 `ack.json` 登記理由。指令回傳 0 才完成。
- `lang_compare.py`：列出 lang 與底稿的差異，預覽逐條說明。lang 與使用者裁定衝突時依裁定，同步修改 lang 並記入 `Changelog.md`。

### 2.4 規則核對與中文通讀

分兩輪：先對 EN 核對觸發、條件、主體、目標、範圍、數值、次數、持續時間和例外；再單獨讀中文，整理修飾語、條件與結果的關係。順稿時另對 EN 的 this／these／that／the／following／one of／each／any／all 逐句核對（見 conventions.md「限定詞逐句核對」）。

完成條件（逐項可檢查）：

1. `draft_diff.py` 回傳 0，所有「改動大」段落在預覽有理由。
2. `terms_check.py` 回傳 0，報告原樣貼進預覽；`ack.json` 的理由逐條列出。
3. `lang_compare.py` 的每個「無」有說明。
4. 原稿每段都有底稿對應；規則差異逐項列出，每項附 EN 原句與原稿原句。
5. 底稿符合格式慣例（不用「它」等，見 conventions.md）。

## 3. 整段映射

底稿完成後讀 [references/block-mapping.md](references/block-mapping.md)，用工具建置（`sheet.json` 已在 2.1 抽取）：

```bash
python $S/skeleton.py build sheet.json --draft <批次>.draft.txt --out aligned.json
```

每個 `blocks[].zh` 取底稿的完整句段，再套入句內 HTML：整個 `<em>…</em>`、`<strong>…</strong>`、UUID、Reference 隨中文語順安排。段落、表格、區塊、屬性與技術內容由 EN 保留。**`zh` 以程式從底稿段落加標記產生，不重新手打。**

原稿沒有的內容標 `source=supplement` 並填 `basis`（EN、中文、欄位、依據）。這個分類只用於原稿缺漏的內容，以及含 `[[…]]` 巨集而無法讓底稿明文逐字相同的區塊（`basis` 寫明）；有原稿的句子必須來自底稿。

完成條件：每個區塊的中文可在底稿找到；名稱與嵌套欄位已處理；補翻區塊都有 `basis`。

## 4. 分別驗收

```bash
python $S/validate.py aligned.json --book <book> --component <component> --out upload.json
```

分別報告四項結果：

1. **規則核對**：全部條件、作用對象、數值與限制符合 EN 或使用者已裁定例外。
2. **術語核對**：附 `terms_check.py` 報告，並對最終 `upload.json` 以 grep 回查被禁用詞（它、如果、發充能、施展…）；未裁定項目明列。
3. **機械驗證**：`validate.py` 通過；嵌套欄位另行核對（工具不保證其規則語意）。
4. **中文通讀**：暫時遮住 EN，逐段讀最終中文；再比對底稿，確認映射未改句。

程式通過只證明其檢查範圍內的機械條件。失敗時修正來源階段後重建；只使用本次成功驗證產生的 payload。

## 5. 預覽與確認

預覽依 [references/preview-template.md](references/preview-template.md) 的欄位撰寫：條目與字串數、底稿、payload 雜湊、逐段「EN／原稿／底稿／修改」對照、規則差異、術語報告、自行補翻清單、保留原稿但與 EN 有出入之處、四項驗收結果、待裁定事項。`activities.condition` 另列 EN 原句與中文對照。

**每批版本得到使用者明確確認後才上傳。** 術語裁定、補翻授權或上一批的確認不代表本批版本已確認。「上傳並做下一批」上傳已確認批次，下一批做到預覽。使用者在確認時提出修改，修改後的版本以使用者該次明確指示為準，並在預覽末尾補修訂紀錄。

完成條件：使用者所確認的範圍與實際 payload 一致（雜湊相同或已列明修訂）；待裁定或未確認內容留在草稿。

## 6. 上傳與收尾

只有到了已確認版本的上傳階段，才讀 [references/weblate-notes.md](references/weblate-notes.md) 與 [references/upload.md](references/upload.md)，完成前置檢查並以 `method=suggest` 上傳。新書無 zh-tw 骨架時，先讀 [references/preparation.md](references/preparation.md) 的新書分支。

上傳成功且回應已核對後才歸檔；部分成功或回應不明保留來源並記錄待處理範圍，不把整批當作完成。報告包含確認版本、四項驗收、上傳結果及剩餘字串。

匯入確認的範圍是該批建議。新增術語、刪除既有建議或其他 Weblate 維護，依使用者明示範圍另行處理（刪除建議的程序見 upload.md）。翻譯檔由 Weblate 寫入；本流程的 git 寫入限新書骨架，commit／push 由使用者處理。保留既有禁止刪除 Weblate translation 的約束。
