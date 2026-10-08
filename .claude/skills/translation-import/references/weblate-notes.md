# 這個 Weblate 實例的行為（全部經實測確認，2026-09-23）

自架於 Docker，主機端口 `http://localhost:8080`，容器名 `weblate-docker-weblate-1`。腳本從 `WEBLATE_URL` 和 `WEBLATE_API_TOKEN` 讀設定。

## 會咬人的地方

**不要用 `DELETE /api/translations/{p}/{c}/{lang}/`。** 它不只刪掉 Weblate 內部的翻譯物件，還會產生一個 `Deleted translation using Weblate` commit 把檔案從 repo 移除，而且因為 `push_on_commit` 是開的，會直接推上 GitHub。實際發生過：feats 的 zh-tw 檔被刪掉 545 行並推送，只能靠 `git checkout <舊 commit> -- <檔案>` 還原。刪掉之後 Weblate 也救不回來，因為 `loadpo`、repository `reset`、`create_translations(force=True)` 都找不到不存在的檔案。要清掉一批建議，請在 Weblate 介面逐條刪，或直接重傳新版，審稿時挑正確的那個。

**API 回傳的絕對網址不能跟。** `WEBLATE_SITE_DOMAIN` 設定錯誤，回傳的 URL 是 `http://weblate.com/...`。`scripts/weblate.py` 的 `paged()` 自己組 `?page=N`，不要改成跟隨 `next`。

**`push_on_commit` 是開的，但 API 觸發的 commit 不會連帶 push**，要另外呼叫 `operation=push`。相對地，使用者在網頁上編輯造成的 commit 會自動推送。

## 檔案與狀態

**Weblate 會把翻譯檔補滿。** commit 時每個字串都會寫出，未翻譯的寫英文。使用者刻意接受這個行為，功能上無害（Babele 用英文翻英文等於沒翻）。但這表示：

- 看檔案無法判斷哪些還沒翻，要靠 Weblate 的標籤或比對 target 是否等於 source。
- 掃描 zh-tw 檔建立條目名稱索引時，值等於 key 的一律略過，否則會把英文當成譯名。

**「需要編輯」狀態只活在資料庫，不在檔案裡。** 翻譯物件一旦重建，原本的需要編輯會全部變成「已翻譯（英文）」。所以 `state:needs-editing` 不能當審稿佇列，`has:suggestion` 才可以。

**`mapping` 會被保留。** Weblate 重寫檔案時，EN 模板以外的 key 不會被刪掉（實測 commit `c472714` 之後 `mapping` 仍在）。但上傳 API 寫不進 `mapping`，它只能從 git 進來。

## 上傳

`POST /api/translations/{p}/{c}/{lang}/file/`（multipart）

- `method`：`suggest`（預設用這個）、`translate`、`fuzzy`、`approve`、`replace`、`add`、`source`
- `conflicts`：`ignore`、`replace-translated`、`replace-approved`
- 回應：`{"accepted": n, "skipped": n, "not_found": n, "total": n}`

`method=fuzzy` 不能用：它會立刻 commit，而且檔案裡寫的是中文而非英文原文，等於讓未審的譯文直接流進 Foundry。`suggest` 不會動檔案，接受之後才寫入。

內容完全相同的建議不會重複產生，會計入 `skipped`。已有相同譯文的字串也會被跳過。

## 新書的路徑陷阱

component 的 filemask 是 `compendium/*/<book>/<book>.<component>.json`，`language_code_style` 為空。只要 `compendium/zh-tw/<book>/` 底下沒有檔案可對應，Weblate 就會用預設語言代碼自己建立 `compendium/zh_Hant/<book>/`，而 `register.js` 只讀 `zh-tw`，於是整本書的譯文都不會生效。所以新書一定要先由 git 放進 zh-tw 骨架檔。

pull 進新檔案之後，Weblate 不會自動建立翻譯物件，要重新掃描：

```bash
docker exec weblate-docker-weblate-1 weblate loadpo --force "<project>/<component>"
```

`loadpo` 只對已存在的翻譯物件有效。翻譯物件不存在時，要用：

```bash
docker exec weblate-docker-weblate-1 weblate shell -c "
from weblate.trans.models import Component
c = Component.objects.get(project__slug='<project>', slug='<component>')
c.create_translations(force=True)
print([(t.language.code, t.filename) for t in c.translation_set.all()])"
```

掃描完務必確認 `filename` 是 `compendium/zh-tw/...`。

## 詞彙表

`dnd-5e-2024-zh-tw/terms` 和 `dnd-5e-2024-zh-tw/spells-glossary` 都是 `is_glossary: true`、repo 為 `local:` 的 component，存在 Weblate 內部，不經過 git，所以新增條目不會動到 repo。

新增條目要分兩步，直接對 zh_Hant 新增會被擋（`permission_denied: Add the string to the source language instead.`）：

1. `POST /api/translations/{p}/{c}/en/units/`，帶 `key` 和 `value`（都填英文）
2. `PATCH /api/units/{id}/`，帶 `state=20` 和 `target`

`scripts/weblate.py glossary-add` 已經包好這兩步。

## 目前的專案狀態

- `dnd-arcana-unleashed` 的 8 個 component 已設好 push URL，zh-tw 骨架檔已在 GitHub 上，路徑正確。
- Weblate 的 `terms` 有 65 條。
- 其他書（PHB、DMG 等）的 zh-tw 檔早就存在，不需要骨架步驟。

## DMG 書本元件的 project 是 `dnd-dungeon-masters-guide`（2026-10-07 踩雷）

DMG equipment 的正確目標是 `dnd-dungeon-masters-guide/dnd-dungeon-masters-guide-equipment`（檔案 `compendium/zh-tw/...`、push URL 已設）。`dnd-5e-2024-zh-tw` 只放術語表（terms、spells-glossary），其下同名的 `dnd-dungeon-masters-guide-equipment` 是檔案路徑為 `<component>/zh_Hant.json` 的無關副本，上傳進去使用者看不到。**上傳前先跑 `weblate.py status <project> <component>`：必須看到「push url set: True」且檔案路徑是 `compendium/zh-tw/`，否則停止。** 術語表寫入才用 `dnd-5e-2024-zh-tw`。

## 名稱

腳本的 `<project> <component>` 用 API 的 slug。component slug 常帶 project 前綴：`dnd-tashas-cauldron` 專案的魔法物品 component 是 `dnd-tashas-cauldron-tcoe-magic-items`，不是 `tcoe-magic-items`。slug 錯誤時 `weblate.py status` 會對三項都回 `not_found`，不代表 Weblate 沒有這個 component。確認方式：

```bash
python - <<'PY'
import sys; sys.path.insert(0, ".claude/skills/translation-import/scripts")
import weblate as w
for c in w.paged("/api/projects/<project>/components/"): print(c["slug"], c["filemask"])
PY
```

API 路徑要帶 `/api/`（`WEBLATE_URL` 不含）。

## 容器操作

容器 root 檔案系統為唯讀，`docker cp` 失敗；需要執行 Django 程式碼時，用 `docker exec -i weblate-docker-weblate-1 weblate shell` 從 stdin 送入腳本。Windows Git Bash 下路徑參數加 `MSYS_NO_PATHCONV=1`。
