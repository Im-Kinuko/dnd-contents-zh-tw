# 職業匯入手冊（2026-10-09，Wizard→Monk 十批後的經驗彙整）

本檔是 SKILL.md 的補充：把職業（classes＋content 日誌頁）匯入反覆出現的做法、陷阱與建議集中，下次開工先讀這一份，再讀 conventions.md 的各職業定案。

## 1. 標準流程（每個職業約 2–4 批）
1. 審閱前一批：用上傳 payload 對 Weblate 現況做 diff（`has_suggestion=False` 且值不同＝使用者改過；相同＝原樣接受），把改動寫進 conventions.md＋memory。
2. `X.py prep`：原稿轉繁（OpenCC s2twp）、整理成 `中文 English` 標題檔給 `draft_diff.py`、建術語索引。
3. 抓 Weblate 全元件單元（classes、content），逐條分類：已翻（state≥20 且 ≠EN）／**英文冒充已翻（state 20 但內文仍英文）**／fuzzy／英文。
4. 寫底稿 `classes.X.1.draft.txt`：只含「依原稿重做」與「補註記／名稱」的條目；Foundry 註記放 `〔EN 補翻〕` 之後。
5. `X.py classes`：extract → 填 blocks（全由底稿或既有譯文產生）→ `skeleton build` → `validate` → 手動併入「僅 advancement／僅名稱／僅修正描述」的部分條目 → 依 10 條／60 字串拆批。
6. `X.py checks`（terms_check、draft_diff、lang_compare、禁用詞 grep、payload 路徑稽核 same/new/over）→ 寫預覽 → 使用者確認 → `weblate.py upload --method suggest` → （歸檔可省略，審閱後整批刪除）。
7. `X.py content`：日誌頁（name／description／subclass）＋子職業頁名稱，內文沿用 classes 已審定譯文。
8. 使用者審完後回到步驟 1。

## 2. 已驗證的取捨規則
- **已有譯文且差異不大 → 不進 payload**；只補註記、嵌套名稱、錯字／定案詞。fuzzy 或英文冒充已翻 → 依底稿重做。
- 名稱優先序：使用者最新裁定 > Weblate 現譯 > 原稿。原稿名稱常與現譯不同（功力／內力、奧術化神／奧法極致…）；現譯被使用者推翻過一次（Perfect Focus），名稱衝突要列出問。
- `description` 以外的欄位（activities.name／condition／target／range／chatFlavor、effects.name／description／changes、advancement.name／hint）都要逐欄處理；沒翻的英文會被 validate 當「英文殘留」，已翻的要從 Weblate 現值帶入，否則 payload 會把英文送出去。
- advancement 用 EN 模板的 `name` key（不是 `title`）；ID 鍵（如 `sqWH6tnUg7jiGaEj`）只有 hint 的略過。
- 部分條目（僅 advancement／僅名稱）不通過 validate 的整條檢查：用 `validate.check_subfields` 驗鍵，再手動併入 payload。
- 既有描述含未標籤 `@UUID[...]` → 補 `{名稱}`（法術取 spell_names.json；裝備取 Weblate equipment 現譯，Arcane Focus＝奧術法器，Druidic Focus＝德魯伊法器（多類）；Hunter's Mark 等 EN 有標籤處對照 EN）。
- content 日誌頁：`pages.<Page>.description／subclass／text`；說明沿用 classes 的已審定譯文（對應 EN 區塊順序，去掉 classes 的核心特質表區塊，只留 @Embed 與段落）；內文連結 `@UUID{職業}` 補在 EN 有連結處；subclass 導讀用固定句式；`Eldritch Invocation Options`／`Metamagic Options` 頁的 text＝標題連結＋@Embed，標題取 classes 現譯名稱。
- 不要替使用者決定刪除舊建議；需要時列出建議 id、核對與舊 payload 完全相同、徵得同意才用 `Suggestion.delete()`。

## 3. 工具陷阱
- 這個環境的 shell 會吃掉/轉換反斜線序列：`\1`、`\n` 在 heredoc 內可能被改成控制字元或真換行。**程式碼一律用 Write／Edit 工具寫檔**，需要換行用 `chr(10)`、需要反向參照用 lambda。
- Git Bash 的 `/tmp` 與 Windows Python 的 `/tmp` 不同；腳本與暫存檔放專案目錄或 scratchpad，並用 `export PYTHONUTF8=1`。
- Docker：`docker exec -i weblate-docker-weblate-1 weblate shell < 專案內的腳本檔`。
- 使用者指示：執行用腳本一律放 `scripts/translation-import/player-handbook/`，只產生 payload，不內建上傳。
- `terms_check.py` 以 sheet 的 key 找底稿標題：key 是 ID（phbxxx…）時，用 terms-sheet 副本把 key 改成英文名；existing-kept 條目排除在 terms-sheet 之外並另行報告。
- `Foundry Note` 區塊結構：`<section class="secret">` ＝ 標題區塊（`<strong>Foundry Note</strong>`）＋註記段落；EN 有時沒有標題區塊（Deflect Energy）或整個沒有註記（Favored Enemy、Unarmored Movement，既有 fuzzy 譯文的舊註記不採）。
- 上傳回應：`accepted＋skipped` 必須等於 payload 字串數；skipped＝與現譯相同。classes 的 `has_suggestion` 數字會包含使用者其他待審項目，不等於本批數量。

## 4. 系統性建議（待做）
1. **合併成一支通用 `class_import.py`**：目前 warlock／rogue／sorcerer／ranger／monk 五支約 70% 相同（extract、填 blocks、KEEP 條目沿用現譯、nested 欄位、拆批、checks、content）。把「條目清單＋底稿＋各條處理方式（FULL／KEEP／ADVANCEMENT_ONLY）」改為每職業一份 JSON 設定，由單一腳本執行。
2. **既有譯文自動稽核**：每批開工先跑一支 `legacy_audit.py`，掃 Weblate 現譯的已知問題並直接輸出修正清單：阿拉伯數字環階、施展、以下、如果、法術槽、同伴、無力、遊說、著裝、全掩護、倒地、它、未標籤 `@UUID`、`&Reference` 殘留純文字、state 20 但英文、fuzzy。使用者已多次一律同意這類修正。
3. **把名稱與用字裁定寫進 Weblate `terms`**（內力／內力點、消耗N點內力、周天運轉、堅忍不拔、明鏡止水、眾敵屠戮、手穩就準…），讓 `terms_check.py` 自動擋；目前只靠 conventions.md，容易漏。
4. **審稿 diff 自動化**：把本次手寫的比對（payload vs Weblate）做成 `review_diff.py`，輸出「原樣接受／改動」並自動貼進 conventions 的審稿修正區，不再手抄。
5. **預覽模板產生器**：預覽的「來源歸類／修改登記／規則差異／補翻清單」可由底稿、draft_diff、payload 稽核結果自動產出骨架，只由人補規則差異與保留項。
6. **名稱衝突表**：維護 `class-feature-names.tsv`（EN、Weblate 現譯、原稿名稱、使用者最終裁定），開工先比對，衝突項一次問清，不要批批追問。
7. **子職業批次獨立**：子職業（Fast Hands 等）與 content 的子職業頁描述有原稿後再做；先確認 classes 的子職業條目是否也要一併。

## 5. 進度（2026-10-09 整理後）
已匯入並審閱（classes＋content）：Barbarian、Cleric、Eldritch Invocation、Wizard、Warlock、Rogue、Sorcerer、Ranger、Monk。子職業已完成：Barbarian 四個、Wizard 四個、Rogue、Warlock（另一場 session；資料已於 2026-10-09 清除）。
待處理：Sorcerer／Ranger／Monk 的子職業特性（使用者稍後提供原稿）；Bard、Druid、Fighter、Paladin（含 content 日誌頁、子職業）；各職業 remaining（特性表、3 級子職、屬性值提升）在 Weblate 無對應 EN 欄位。工作區說明見 `_incoming/player-handbook/README.md`（已完成的批次資料全部刪除，只留 README）。
