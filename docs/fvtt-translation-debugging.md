# 這次 Foundry 翻譯錯誤的原因與修正

你不需要先學會整套 Foundry 開發。先掌握兩個概念：**顯示名稱可以翻譯，規則識別碼要保持穩定；翻譯句子可以換語序，花括號裡的變數名稱不能換。**

## 第一個錯誤：法術的來源缺少識別碼

錯誤堆疊雖然很長，關鍵只有 `system.sourceItem`。這不是法術的中文名稱，而是法術從哪個職業、裝備或特性取得的規則關聯。

例如 `equipment:spellbook` 的意思是：「裝備類別中，識別碼為 spellbook 的物品」。這個欄位不接受 `equipment:`，因為冒號後面沒有識別碼。

本機唯讀查得的資料如下；並未修改世界資料庫：

| 文件 | 目前資料 | 問題 |
| --- | --- | --- |
| 法術書，Item.hY0c3vxHK35KTTxp | `system.identifier: ""` | 識別碼是空字串 |
| 完全復活術，Item.Vy6OkLLu3Ewi0glo | `system.sourceItem: "equipment:"` | 沒有指定是哪件裝備 |
| 完全復活術的 `flags.dnd5e.cachedFor` | `.Item.hY0c3vxHK35KTTxp.Activity.5qVxZoKDUruKL2Ts` | 可以確認它由上述法術書的施法活動產生 |

這些物品屬於 Actor.jerdFmPpz3DwElm7。該世界記錄的版本為 Foundry 14.368、D&D 5e 6.0.5；本機 Babele 為 2.9.1。

D&D 5e 的 [Cast 活動程式碼](https://github.com/foundryvtt/dnd5e/blob/release-6.0.5/module/documents/activity/cast.mjs) 會將物品類別及物品識別碼組合成 `sourceItem`。物品未設定識別碼時，[Document mixin](https://github.com/foundryvtt/dnd5e/blob/release-6.0.5/module/documents/mixins/document.mjs) 會以名稱產生識別碼；[formatIdentifier](https://github.com/foundryvtt/dnd5e/blob/release-6.0.5/module/utils.mjs) 使用嚴格的 slugify。

因此，全中文名稱、空識別碼，再加上產生快取法術的流程，能造成這次的 `equipment:`。實際資料證明來源關聯已損壞；無法僅憑這些資料判定當初是哪一次編輯造成空識別碼。錯誤訊息列出 `vision-5e`，也不等於已證明它是原因。

`register.js` 現在透過 [libWrapper](https://github.com/ruipin/fvtt-lib-wrapper) 在物品驗證前處理這個情況：

1. 保留已有的識別碼。
2. 空識別碼優先從 Babele 保留的原英文名稱產生，其次使用目前名稱。
3. 名稱仍無法產生識別碼時，使用 `item-` 加上文件 ID。本例為 `item-hy0c3vxhk35kttxp`。
4. 僅當快取法術的 `cachedFor` 明確指向同一角色上、同類別物品的 Cast 活動，才將不完整的 `equipment:` 修成對應的完整來源。無法確認來源時不猜測。

這是在載入時修復記憶體中的資料，沒有批次寫回世界資料庫。模組必須啟用才會執行；遊戲中之後正常儲存文件時，修正資料可能隨之保存。若要不依賴此修正，可在來源法術書設定一個固定英文識別碼，並讓相關快取法術使用相同來源識別碼。

## 第二個錯誤：翻譯模板要求了不存在的變數

`[[/damage average extended]]` 是由系統執行的文字指令，不是普通英文句子。保留整段指令，讓系統依物品上的傷害活動計算數值及建立擲骰連結。[官方 Enrichers 說明](https://github.com/foundryvtt/dnd5e/wiki/Enrichers) 列出了格式與選項。

系統實際分三步處理：

| 步驟 | 翻譯模板 | 系統提供的變數 |
| --- | --- | --- |
| 組合平均傷害、骰式、類型 | `DamageAverage` | `{average}`、`{formula}`、`{type}` |
| 為完整傷害連結加上「傷害」文字 | `DamageLong` | `{damage}` |
| 加上「命中」標籤 | `DamageExtended` | `{damage}` |

原本中文的 `DamageLong` 是：

```json
"DamageLong": "{average} ({formula}) {type}"
```

但這一步系統只提供 `{damage}`，所以另外三個變數都變成 `undefined`。不是擲骰算不出結果，而是翻譯模板拿錯變數。[官方傷害函式](https://github.com/foundryvtt/dnd5e/blob/release-6.0.5/module/enrichers.mjs) 可以直接核對呼叫時傳入的資料。

現在改為：

```json
"DamageLong": "{damage} 傷害",
"DamageExtended": "<em>命中：</em> {damage}"
```

`{damage}` 本身已包含可點擊的擲骰連結。保留它，連結與數值就會一起保留；「傷害」只需加入一次。

## 以後翻譯時怎麼判斷

| 內容 | 作法 |
| --- | --- |
| 物品 `name`、描述中的一般句子 | 翻成中文 |
| `system.identifier`、`sourceItem`、文件 ID、UUID | 保留規則用值，不當作顯示文字翻譯 |
| `{damage}`、`{formula}` 等變數 | 保留花括號與英文變數名稱，可調整前後中文和語序 |
| `[[/damage average extended]]` | 保留指令；它會自動讀取傷害活動 |
| `<em>`、`<a>` 等 HTML | 保留結構，翻譯裡面的顯示文字 |

例如：英文 `{damage} damage` 可以譯為 `{damage} 傷害`，不能因為想顯示傷害骰就自行換成 `{formula}`。

## 套用與驗證

專案已修改 `register.js`、`lang/zh-tw.json`、`module.json` 及發佈流程。`module.json` 現在指向真正的語言 JSON，發佈 ZIP 也會包含它；Babele 的圖鑑翻譯仍由 `register.js` 註冊。

1. 完全關閉 Foundry 程式。
2. 將專案中的 `register.js`、`module.json`、`lang/zh-tw.json` 複製到目前 `Data/modules/dnd-contents-zh-tw` 的對應位置，取代同名模組檔案。
3. 啟動 Foundry，確認此翻譯模組、Babele 和 libWrapper 已啟用。
4. 進入原本出錯的世界。重新檢查完全復活術是否正常載入。
5. 在具有傷害活動的物品描述測試 `[[/damage average extended]]`，確認顯示中文傷害並能點擊擲骰。單獨放到沒有活動的普通文字位置，無法靠這條指令取得物品的傷害資料。

本機 `D:/TRPG/FoundryVirtualTabletop/Foundry VTT/Data/modules/dnd-contents-zh-tw` 已同步三個修正檔案，並逐一核對檔案雜湊。本機直接從重新啟動 Foundry 開始即可。2026-10-04 專案清理已移除一次性修復 ZIP 與修復前備份，其他安裝請依上述步驟複製專案檔案。

目前已完成 7 個回歸測試，並以官方 6.0.5 傷害函式、識別碼驗證器及本機出錯物品的最小資料重現、驗證修復；尚未在完整 Foundry 遊戲介面中重新啟動驗證。

開發時使用 Node.js 22 或以上，在專案目錄執行：

```powershell
node --test tests/fvtt-compatibility.test.mjs
```

測試會檢查來源關聯修復、既有識別碼保留、中文名稱的穩定備用識別碼、模糊來源不被猜測修改、傷害變數及語言檔案打包。發佈工作流程也會執行這組檢查。
