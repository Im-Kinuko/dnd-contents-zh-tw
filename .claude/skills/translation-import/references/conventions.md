# 行文與格式慣例

## 每批上傳前須確認（2026-10-04 使用者更正）

執行 [SKILL.md](../SKILL.md) 第 5 步「預覽與確認」：該節統一定義每批預覽、版本確認及上傳範圍。自行補翻的授權只適用於準備譯文。

## 查不到既有譯文時的處理（2026-10-04 使用者更新）

按 [translation-quality.md](translation-quality.md) 的「術語與句式來源」與「無原稿內容的來源順序」先確認所有適用來源（含 Weblate 既有譯文）。確認查不到既有中文時，自行依 EN 語意翻譯，句式與術語沿用之前的風格；這項授權也適用於介面欄位，如 activity 的 name、target、hint、chatFlavor 與 effect 的顯示文字。讀取失敗不算查無詞條，已有術語也不屬於自行定名。這項授權不取代每批上傳前的確認。

每個自行補翻的欄位在預覽或匯入報告列出欄位路徑、EN 原句、中文譯文及用詞依據，讓使用者知道翻了什麼。既有譯名有衝突、EN 語意不明或結構無法對齊時，仍需提出具體問題。已確認的詞、HTML、UUID、Reference 目標、巨集及佔位符規則照常套用；原稿沒有的 EN 正文、表格文字及 Foundry 註記照常補翻。

每一條都是從既有 zh-tw 譯文的實際用量得出的，不是偏好。數字是 `scripts/usage.py` 在 `compendium/zh-tw/` 底下數到的出現次數。遇到新的分歧時，用同一個方法數給使用者看，讓他們拍板，不要自己挑。

## 句式

| 項目 | 採用 | 用量 |
|---|---|---|
| benefit | 好處 | 好處 145 : 增益 25 |
| 起手句 | 你獲得下列好處。 | 下列好處 114 : 下列增益 5 |
| 次數句 | 你能使用此好處的次數等同於你的熟練加值 | 等同於 17 : 等於 1 |
| cast | 施放 | 施放 373 : 施展 21 |
| take a ⋯ action | 採取⋯動作 | 採取…動作 82 : 執行…動作 7 |
| to a maximum of 20 | 上限為20 | 上限為20 43 : 至多提升至20 0 |
| Increase ⋯ by 1 | 提升1**點** | 三種變體一律加「點」：<br>指定屬性「你的智力、感知或魅力提升1點，上限為20。」<br>自選屬性「提升一項你所選擇的屬性1點，上限為20。」 |
| always have certain spells at the ready | 你的造詣令你始終準備特定法術 | 使用者手改的版本，比「始終將特定法術準備就緒」精簡 |
| a creature you can see within X feet | 位於你X呎內**一名**你所能看見的生物 | 你所能看見 79 : 你可見 3。量詞跟著 EN 的 `one`／`a` 走，位置在距離之後、「你所能看見」之前；「一名位於你…」是 0 次，量詞不要前移到句首 |
| (you are) within X feet of a creature | 與一名生物相距不超過X呎 | 使用者 2026-10-05 定案。例：If you are within 5 feet of an ally that doesn’t have the Incapacitated condition → 若你與一名未陷入失能狀態的盟友相距不超過5呎。不寫「位於…X呎內」；以「你」為中心的 within X feet of you 仍用「位於你X呎內」 |
| until you finish a Long Rest | 直到完成長休前 | 取代「直至完成長休」 |
| take a Reaction | 可以採取反應 | 與「採取⋯動作」同一句式，取代「能以反應」 |
| Until ⋯ ends | 直到⋯結束前 | 使用者慣例（2026-10-03），不寫「在⋯結束前」 |
| When ⋯ | 當⋯時 | 同上 |
| Whenever ⋯ | 每當⋯ | 同上 |
| something you can see | 你所能看見的某物 | 同上（與既有「你所能看見」一致） |
| Each time ⋯ | 每次⋯ | 與「Whenever→每當」區分（2026-10-03 第 3 環法術第 4 批） |
| Very Rare（稀有度） | 極珍稀 | 使用者 2026-10-04 定案，不用既有的「非常珍稀」；Uncommon＝非普通、Rare＝珍稀、Legendary＝傳說 |
| If ⋯ | 若⋯ | 使用者 2026-10-04 定案，不寫「如果」（既有譯文 若 349 : 如果 44） |
| the／that／this | 該／該／此 | 大致規則；上下文可例外（the target 仍可用「目標」）。**this＋實體物品**（this potion／cloak／weapon）寫「這瓶藥水」「這件斗篷」「這把武器」，不寫「此藥水」（2026-10-04 使用者確認，與既有藥水譯文一致）；抽象概念（this property／effect／spell）仍用「此特性」「此效應」「此法術」 |

「施展」和「執行」都是正體字，OpenCC 不會動這些詞。這類詞只能靠比對既有譯文抓出來，所以術語比對不能省。

## 代名詞：不用「它」（2026-10-01 使用者定案）

譯文裡**不使用「它」**。凡是會寫成「它」的地方，改用適合的「其」（例如「其移動範圍」「受益於其所擁有的特殊感官」「將其餵給位於你5呎內的另一名生物」「其重複豁免」）；只有「其」會造成指涉不清、或實在讀不通時，才改成重複名詞。原文（簡體稿）裡的「它」「它們」同樣要處理，不要照搬。`validate.py` 會擋下含「它」的段落。

**範圍只到「它」**（使用者 2026-10-02 澄清）：原本沒有用代名詞的句子，不需要為了湊「其」而硬補；已上傳內容裡省略代名詞的地方也不用回頭補。要處理的只有「用到『它』的地方」。

## 已裁定的譯名

| EN | zh-tw | 取代 |
|---|---|---|
| Arcane Undertaker | 奧法送葬者 | 奧法殯葬師 |
| Masterful Illusions | 精湛幻象 | 幻象宗師 |
| Oil（冒險裝備） | 燃油 | 油（2026-10-01 使用者拍板，與套裝清單標籤一致） |
| Paper（冒險裝備） | 紙張 | 紙（同上） |
| Pouch（冒險裝備） | 囊袋 | 維持既有名稱，原文「小包」不採用（2026-10-01 使用者拍板） |
| Rules Glossary | 規則詞彙表 | 原文「术语汇编」；已寫進 Weblate `terms`（2026-10-01） |
| Persuasion（技能） | 說服 | PHB 舊譯「遊說」；使用者 2026-10-04 定案，與 lang `DND5E.SkillPer` 一致；已寫進 `terms` |
| Order of the Gauntlet（陣營） | 鐵腕 | 對齊「鐵腕騎士」；Tyro of the Gauntlet＝鐵腕新兵，原文「新锻臂铠」不採用（2026-10-04） |
| Zhentarim（陣營） | 散塔林 | 不加「會」；Zhentarim Ruffian＝散塔林暴徒（2026-10-04） |
| Opportunity Attack | 藉機攻擊 | 使用者 2026-10-04 確認；`&Reference[Opportunity Attacks]{藉機攻擊}` |
| Active Effect（Foundry 註記） | **保留英文 Active Effect** | 使用者 2026-10-04 定案，與 lang 介面一致；不譯「主動效果」 |
| Reaction（`&Reference` 標籤） | 反應 | 使用者 2026-10-04 確認；`&Reference[Reaction]{反應}`，與 lang `DND5E.Reaction` 一致 |
| Expertise | 專精 | 使用者 2026-10-05 確認；lang `DND5E.Expertise` 寫「專長」不採用；已寫進 `terms` |
| Cold Caster（專長名） | 寒地施法者 | 使用者 2026-10-05 確認的名稱例外；名稱內的 Cold 不套 terms「寒冷」 |
| Silver Marches／Myth Drannor（地名） | 銀月聯邦／迷斯卓諾 | 使用者 2026-10-05 確認，不附英文；已寫進 `terms` |
| Bladesinger／Arcane Recovery | 劍詠者／奧術恢復 | 劍詠者沿用 folder 譯名；原稿「奧術回想」不採用（PHB 條目名）；已寫進 `terms` |
| Bladesong 的子好處 Focus | 凝神 | 使用者 2026-10-05 確認，避免與 Concentration（專注）同字 |
| tradition of wizardry | 奧法傳承 | 使用者 2026-10-05 確認，雖含 Wizard 字根，不譯「法師魔法」 |
| the Realms | 國度（國度各地） | 使用者 2026-10-05 確認，沿用原稿「被遺忘的國度」 |
| Bardic Inspiration（含 die） | 吟遊激勵（骰） | PHB 條目名，使用者 2026-10-06 確認；原稿「詩人激勵」不採用。簡稱 Inspiration die 寫「激勵骰」，不統一加「吟遊」 |
| fey magic（月影群島的妖精之力） | 妖精魔法 | 使用者 2026-10-06 定案；此語境不套「Fey＝精類」（生物類型） |
| `[[/heal]]{XdY}` Hit Points | 後接「點生命值」 | 使用者 2026-10-06：恢復[[/heal]]{2d4}點生命值（傷害巨集後仍不加點） |
| Moonshae Isles／moonwell／Primal | 月影群島／月井／原初 | 使用者 2026-10-06 確認，沿用原稿與全庫既有 |
| Indomitable（戰士特性，PHB 尚未翻） | 不屈 | 使用者 2026-10-06 確認；已寫進 `terms` |
| area of effect／scale value | 效應範圍／比例值 | 使用者 2026-10-06 定案（全庫無既有譯文） |
| Damara／Chessenta（地名） | 達馬拉／闕森塔 | 使用者 2026-10-06 確認；已寫進 `terms` |
| Unshakable Bravery（Inspiring Commander） | 不撓之勇 | 使用者 2026-10-06：原稿「不當之勇」疑為誤寫，改「不撓之勇」 |
| Knightly Envoy | 騎士使節 | 使用者 2026-10-06：原稿「騎士禮節」不採用 |
| Weave／Old Empires／Red Wizards | 魔網／古老帝國／紅袍法師 | 使用者 2026-10-06 確認並記錄；已寫進 `terms`。紅袍法師為專案既有，原稿「紅袍巫師」不採用 |
| 效果 changes.name「{} (Active)」 | {}（啟用中） | 使用者 2026-10-06 定案，與 PHB 正文 active＝啟用一致；lang 的「作用中」不採用 |
| 咒火術法的 PHB 法術名 | 治療傷勢／次級復原術／反制法術；Innate Sorcery＝天生術法 | Weblate PHB 現行名稱；原稿的療傷術／次等復原術／法術反制／先天術法不採用 |
| Plan（奇械師魔法物品 Plan） | 方案 | 使用者 2026-10-06 定案，不用 lang 原「藍圖」；已同步改 lang `ArtificerPlan`＝奇械師方案；子職名暫定：煉金師、裝甲師、魔炮師、戰地匠師、製圖師 |
| EN advancement hint 與正文矛盾 | 依正文譯 | 使用者 2026-10-05：Zhentarim Tactics hint 寫 Str/Dex，依正文譯「敏捷或魅力」（同 Dragonscarred 補正） |

## 標記

**EN 的描述不是一串 `<p>`。** 它可能把內容包在 `<section class="secret hide-in-embed">` 裡、含有整個 `<table>`（`caption`／`thead`／`tr`／`th`／`tbody`／`td`），也會用 `<p class="hanging">` 標記子項好處。用正規式抽段落再重組，這些會**無聲消失**：Weblate 裡的文字讀起來沒問題，Foundry 的呈現卻壞掉，而且 `class="hanging"` 的內容會被誤判成「EN 沒有」。

所以用新版 `scripts/skeleton.py` 保留 EN 的區塊骨架，以底稿完整句段填入 `blocks[].zh`。句內標記可以隨台灣中文語順移動；留白會停止建立，不填回英文。格式必須繼續包覆其對應中文詞組，詳見 [block-mapping.md](block-mapping.md)。

小標維持 EN 的標籤種類（`<strong>` 或 `<em><strong>`），文字包進【】，**後面一律不留句號**（無論 EN 是否帶有半形 `.` 或全形 `。`，標籤內外的句號皆須移除），結束標籤後面不留空格，正文緊接著寫：

```html
<p><em><strong>【升環法術效應】</strong></em>法術位每升一個環階，傷害就增加1d6。</p>
<p><span class="inline-h4">【戲法】</span>你習得<em>@UUID[…]{次級幻象}</em>戲法。…</p>
```

EN 若用 `<strong>` 或 `<em><strong>` 就保留原標籤。常用小標對照：
- `Using a Higher-Level Spell Slot` → `【升環法術效應】`
- `Combat` → `【戰鬥】`
- `Disappearance of the Familiar` → `【魔寵消失】`
- `One Familiar at a Time` → `【數量限制】`

`@UUID[目標]{標籤}`：目標原樣保留，只翻標籤，而且標籤要用術語索引查，不要照抄原文（原文常用大陸譯名）。

`&Reference[Target]` 標籤（2026-10-01 使用者定案）：`[...]` 內的英文目標（含 `apply=false` 等修飾詞）一個字都不能改，**一律要在後面加 `{中文}`**，例如 `&Reference[Concentration]{專注}`、`&Reference[Dash]{疾走}`、`&Reference[blindsight]{盲視}`。`{}` 裡的中文依 [translation-quality.md](translation-quality.md)「術語與句式來源」選詞，缺詞與衝突按該節處理；中文語意接在 `{}` 後面照常寫（例如「陷入&Reference[Poisoned]{中毒}狀態。」）。

既有譯文裡有 2128 處沒加 `{}`、只有 342 處有加，那是舊的欠帳，不是慣例，**不要拿這種數量統計來決定規則**。這條規則曾被我依據該統計改成「預設不加」，是錯的，已改回；過去 Antigravity 沒搞懂這條規則而亂做，要防的是亂做（改動 `[...]` 目標、自己編標籤），不是不要加 `{}`。`validate.py` 會擋下沒有 `{中文}` 的 `&Reference`。

`Hit Point Dice` 統一譯為 **`生命骰`**（不需要擴寫為「生命值骰」）。

**`<section class="secret">` 包住的 Foundry Note 要翻**（2026-10-01 使用者拍板）。全庫 1077 個這種區塊裡有 985 個（91%）還是英文，但那是欠帳，不是「不用翻」——`class="secret"` 只代表預設對玩家隱藏，GM 展開時一樣要看到中文。標題照已翻的 92 個樣本裡的多數寫法譯成 `Foundry 註記`（或 `Foundry 說明`），不要照抄英文字面的「Foundry Note」；`Foundry` 本身維持英文（专有产品名）。內文提到的 Foundry activity／effect 名稱（例如 `Recover Ball Bearings`）也要翻，`activity` 譯為「**行動**」（使用者定案；遊戲 `lang/zh-tw.json` 的 `DOCUMENT.Activity` 就是「行動」，原先我用的「活動」是錯的）。

**表格（`<table>`）內容要翻**（2026-10-01 使用者拍板）：`caption`、`<thead>` 表頭、`@UUID[...]{...}` 品項名全部都要翻，不是只翻表格外的介紹段落。這也是補欠帳——同一張表在全庫可能有好幾份英文殘留的副本（例如 Ammunition 表在 `dnd-players-handbook.equipment`／`dnd-players-handbook.content`／`dnd5e.equipment24` 各有一份，翻的時候只會動到當次在處理的那一份，其他副本要另外排進度補上）。

## 單位與數字

距離寫「30呎」，數字和單位之間不留空格，不換算公尺。原文若已經換算成公尺（大陸譯本常見「9米」），以 EN 句子裡的數字為準還原，不要從公尺反推。

## 術語

Weblate 的 `dnd-5e-2024-zh-tw/terms` 是規則術語的正本，`spells-glossary` 是咒語名稱的正本（取自舊版，只當後備）。2024 zh-tw 檔的條目名稱優先於 `spells-glossary`。

來源優先順序、索引查詢方法、逐詞查核及衝突分支統一見 [translation-quality.md](translation-quality.md)「術語與句式來源」。

## 遊戲介面用詞：`lang/zh-tw.json` 只是參考，使用者已確認的詞優先

專案根目錄 `lang/zh-tw.json` 是遊戲介面實際用的 zh-tw 用詞，作為規則術語以外的介面文字及缺詞後備。選狀態名稱、`&Reference` 標籤及 Foundry Note 的規則詞時，依 [translation-quality.md](translation-quality.md)「術語與句式來源」先查裁定與 `terms`。使用者已裁定的詞與正式術語優先於 lang；已有定義時，不以 lang 或用量統計改選另一個詞。確定缺詞時依已授權規則補翻，列入預覽待確認。

| EN | 採用（使用者已確認） | lang 的寫法（僅供參考） |
|---|---|---|
| Activity | 行動（Foundry Note 裡的 activity 一律譯「行動」，不是「活動」） | 行動 |
| Prone | 伏地 | 倒地 |
| Grappled | 受擒 | 被擒 |
| Malnutrition | 飢餓 | 營養不良 |
| Frightened | 恐慌（原文與 lang 一致，不要改成「恐懼」） | 恐慌 |
| Medicine（技能） | 醫藥（使用者確認，lang 為「醫療」） | 醫療 |
| Incapacitated | 失能 | 失能 |
| Critical Hit | 暴擊（2026-10-03 使用者定案） | 重擊 |
| Restrained | 束縛 | 束縛 |
| burning／dehydration | 燃燒／脫水 | 燃燒／脫水 |
| Damage Resistance／對傷害的 Resistance | **抗力**（傷害抗力；2026-10-02 使用者定案，**只限傷害抗力**，其餘仍用「抗性」：傳奇抗性、魔法抗性、天界抗性、能量抗性等名稱不改） | 傷害抗性（lang 已改成傷害抗力） |

## 2026-10-03 第 3 環法術匯入新定的譯名與做法

| EN | zh-tw | 備註 |
|---|---|---|
| Ethereal Plane／Ethereal（效果名） | 乙太位面／乙太 | 使用者確認；lang 的「以太」不採用 |
| Necrotic | 黯蝕 | lang 與語料多數一致，原文「暗蝕」不採用 |
| truesight（`&Reference` 標籤） | 真視 | 與盲視同系 |
| Far Realm | 遙遠國度 | 全庫既有 6 處 |
| Leomund | 李歐蒙 | 對齊既有「李歐蒙祕藏」 |
| Celestials／Elementals／Fey／Fiends／Undead（生物類型列舉） | 天界、元素、精類、邪魔、不死生物 | 對齊 Protection from Evil and Good |
| Incapacitated 的 `&Reference` 標籤 | 失能 | 既有「無力」是舊錯誤，遇到就改 |
| Cataleptic | 僵直 | 待使用者最終確認 |
| stat block | 數值面板 | 使用者 2026-10-03 定案，取代「屬性值」「數據卡」；Summon Beast 等舊譯文仍寫「屬性值」 |
| Summon Fey／Summon Undead（咒語名） | 精類召喚術／不死生物召喚術 | 使用者定案，與專案類型詞「精類」「不死生物」一致，不採原文的妖精／亡靈 |
| activity「Cast and Save」 | 施放並豁免 | 使用者確認 |
| chatFlavor | 翻譯 | 使用者 2026-10-03 改為要翻（先前「留英文」作廢）；同一個 activity 的 chatFlavor 一併處理 |

做法：
- **效果名稱要翻**（比照 Warding Bond 的「受聯結」）；activity 名稱照既有慣例翻。系列效果名稱仿 activity 名稱（例如 activity「詛咒攻擊」→ 效果「受詛咒的攻擊」）。
- **咒語本身已有譯名時，name 一律沿用既有譯名**，原文名稱不採用；name 仍是英文才依原文定名並請使用者驗收。
- **`chatFlavor` 要翻譯**：依上表更新後的授權與術語查核處理，巨集及佔位符保留，補翻內容列入預覽。
- EN 巨集若有上游錯誤（如 Glyph of Warding 五種傷害巨集全是 `type=acid`），原樣保留並在預覽提出，不自行改。
- **`skipped` 的意思**：上傳內容與 Weblate 現有譯文一字不差（多半是沿用的 name），不是被拒絕。

## 使用者在 Weblate 審稿後的修正（第 3 環法術，2026-10-03）

拿我上傳的 199 個字串與 Weblate 現況比對：161 個原樣被接受，38 個被使用者改過。以下是從修正中歸納出來的用法，**照 Weblate 上的為準**，之後對齊直接套用：

| EN 情境 | 採用 | 不用（我原寫的） |
|---|---|---|
| Zombie | 喪屍 | 殭屍 |
| When you cast (the/this) spell | 當你施放該法術時／當你施放法術時 | 施放此法術時 |
| When you create ⋯, and ⋯ | 當你創造該靈光，以及⋯（句末可省「時」） | 當你創造該靈光時，以及 |
| When the spell ends | 當法術結束時（句首一律帶「當」） | 法術結束時 |
| must succeed on a ⋯ saving throw | 必須成功通過一次⋯豁免 | （2026-10-03 使用者改回：先前審稿曾刪去「成功」，後來裁定一律保留「成功」；不寫「必須通過」） |
| takes extra ⋯ damage from the attack | 從該次攻擊中承受額外的⋯傷害 | 會受到該次攻擊額外的⋯傷害 |
| unoccupied space | 未佔據空間 | 未被佔據空間 |
| a (unoccupied) space you can see within range | 射程內一處你所能看見的（未佔據）空間 | 射程內你可見的一個⋯ |
| a creature you can see | 你所能看見的生物 | 你可見的生物 |
| Each creature of your choice that you can see in a 60-foot Cone | 位於你所能看見的60呎錐形區域內每個你所選擇的生物 | 你所選擇、位於你可見⋯的每個生物 |
| spectral weapon | 靈體武器 | 幽靈武器 |
| on the ground | 地面上 | 地面 |
| radiate an aura in a 30-foot Emanation | 你散發出30呎發散區域的魔法靈光 | 你以30呎發散區域散發魔法靈光 |
| sunlight spreads and fills | 擴散出來，並充滿 | 散發出來，充滿 |
| that other spell is dispelled | 則其他法術即被解除 | 該法術即被解除 |
| 列舉最後一項 ⋯, Lightning, or Thunder | 強酸、寒冷、火焰、閃電、雷鳴（不加「或」） | ⋯閃電或雷鳴 |
| A bright streak flashes from you to a point | 從你射程內所選擇的一點閃爍出一道明亮的光芒 | 一道明亮的光芒從你射向⋯ |
| The spell ends on the target | 目標身上的法術結束 | 法術對目標結束 |
| Gateway | 通道（Open Gateway→開啟通道） | 門戶 |
| 30-foot Cube（Hypnotic Pattern） | 30立方呎區域 | 30呎立方體區域 |
| [[/damage ⋯]] 後接傷害 | 直接接「傷害」，不加「點」 | ⋯]]點傷害 |
| color you choose | 可呈現你所選擇的任何顏色 | 可為你選擇的任何顏色 |
| fails / falls into liquid | 此法術宣告失敗／墜入液體 | 此法術即告失敗／掉入 |
| 效果名稱「Cursed X」 | X受詛（魅力受詛、攻擊受詛⋯） | 受詛咒的X |
| 效果名稱「Fear」 | 恐懼（效果名不加「術」） | 恐懼術 |
| Use the spell slot's level for the spell's level in the stat block.（召喚類法術） | 該生物的數值面板使用新的法術環階。（使用者 2026-10-07 定案） | 使用法術位的環階作為數值面板中的法術環階 |
| 效果名稱「Hidden from Divination」 | 隱藏於預言學派法術 | 隱藏於預言學派 |
| chatFlavor | 已被接受：閃電擊中雲下一點，半徑5呎範圍 | — |

說明：
- 這些 activity 名稱全數被接受，只有「開啟通道」被改動：施放並豁免、創造單一／分段風牆、法術刻紋、爆炸符文、施加倦怠、回合開始的傷害、創造幻象、研究、繁茂、豐產。
- 「Cube」的立方呎寫法只有 Hypnotic Pattern 被改；Major Image 的「20呎立方體」被接受。兩種並存，遇到再問。
- 「成功時傷害減半」被改成「成功時則傷害減半」只出現在 Fireball，不算通則。

## 使用者在 Weblate 審稿後的修正（費倫英雄起源專長，2026-10-04）

| EN 情境 | 採用 | 不用（我原寫的） |
|---|---|---|
| DC 8 plus your X modifier and Proficiency Bonus | DC為8 + 你的X調整值 + 你的熟練加值 | 8加上…再加上… |
| cause a creature to have ⋯ condition | 使一名生物陷入⋯狀態 | 令 |
| take damage | 承受傷害 | 受到傷害 |
| (choose when you select this feat) | （當你選取此專長時選擇） | （在你選取此專長時選擇） |
| choose a number of creatures equal to ⋯ that you can see within 30 feet | 選擇數量等同於你熟練加值（⋯），且位於你30呎內你所能看見的生物 | 照 EN 語序，數量放前面 |

## 使用者在 Weblate 審稿後的修正（費倫英雄通用專長第 1 批，2026-10-05）

| EN 情境 | 採用 | 不用（我原寫的） |
|---|---|---|
| as part of the Attack or Magic action | 以攻擊或魔法動作的一部分 | 作為⋯的一部分 |
| You have Resistance to the chosen damage type | 你擁有所選傷害類型的抗力 | 你具有（僅此一例，未必通則） |
| cast it without a spell slot using this feature | 使用此特性**而**無需法術位施放該法術 | 少了「而」 |
| until you have the Incapacitated condition | 直到你陷入失能狀態（不加「前」） | 直到你陷入失能狀態前 |
| You can take this Bonus Action a number of times | 你**可以**採取此附贈動作的次數 | 你能採取 |
| When you make a damage roll that deals X damage | 當你擲出造成X傷害的傷害骰時 | 當你進行⋯的傷害擲骰時 |
| If ⋯, you can ⋯ | 若⋯，則你可以⋯ | 省略「則」 |
| (within X feet of an ally) | 與一名⋯盟友相距不超過X呎 | 位於⋯盟友X呎內（見句式表） |
| EN 上游漏寫（Dragonscarred hint 漏 Charisma） | 使用者直接補正為「體質或魅力」 | 照錯誤 EN 譯 |

名稱改動：Harper Teamwork＝**豎琴手合力**（非協同）；Inspiring Willpower＝**激勵人心**；Two Hearts, One Mind＝**雙心一意**。

## 使用者在 Weblate 審稿後的修正（費倫英雄皓月學院，2026-10-06）

| EN 情境 | 採用 | 不用（我原寫的） |
|---|---|---|
| until the start of your next turn | 直到你的下個回合開始（**不加「前」**；until the end of ⋯ turn 仍是「結束前」） | 直到⋯開始前 |
| you can have the Invisible condition | 你可以**進入**隱形狀態 | 陷入隱形狀態 |
| teleport up to 30 feet to an unoccupied space you can see | 傳送到**至多**30呎一處你所能看見的未佔據空間 | 傳送到最多30呎外一處⋯ |
| ⋯ also increases by 10 feet until the end of its next turn | 時間子句前置：直到其下個回合結束前，該生物的速度也會增加10呎 | 句尾「⋯，直到其下個回合結束前」 |
| a number equal to a roll of the die | 等同於該骰擲出的數值 | 擲出結果的數值 |
| the effects of this Moonbeam（this＋法術名） | 這道月華之光效應（法術名前用「這道」） | 此月華之光效應 |
| fails its saving throw against this modified casting of Moonbeam | 對抗這道經調整的月華之光豁免失敗時 | 對抗此次經調整的月華之光效應的豁免失敗時 |
| modify a casting of Moonbeam | 調整月華之光的施放 | 調整一次月華之光的施放 |
| in place of expending a die | 取代將消耗的一枚吟遊激勵骰 | 取代消耗一枚⋯ |

## 使用者在 Weblate 審稿後的修正（費倫英雄旗將，2026-10-06）

| EN 情境 | 採用 | 不用（我原寫的） |
|---|---|---|
| within a 30-foot Emanation originating from yourself | 位於以你自己為中心30呎發散區域內 | 位於源自你的30呎發散區域內 |
| roll label「Reroll Bonus」 | 重骰加值（label 用「重骰」；正文 reroll the saving throw 仍寫「重擲」） | 重擲加值 |
| When an ally you can see within 60 feet of yourself fails a saving throw（主語位置） | 當一名位於你60呎內你所能看見的盟友豁免檢定失敗時（作主語時「一名」放最前，後接「位於…」） | 當位於你60呎內一名你所能看見的盟友 |
| expend a use of your Indomitable feature | 消耗一次你的不屈特性 | 消耗你的不屈特性的一次使用次數 |
| bonus equal to your Fighter level (+[[lookup …]]{15}) | 等同於你戰士等級的加值（+[[lookup …]]{15}） | 括號放在「戰士等級」後 |
| You have Immunity to the Charmed and Frightened conditions | 你具有對魅惑與恐慌狀態的免疫 | 你對魅惑與恐慌狀態具有免疫 |

## 使用者在 Weblate 審稿後的修正（費倫英雄咒火術法，2026-10-06）

| EN 情境 | 採用 | 不用（我原寫的） |
|---|---|---|
| You can do so only once per turn | 你每回合只能這麼做一次 | 如此做 |
| advancement hint「You always have the X spell prepared」 | 你始終準備X法術（hint 不加「著」；description 正文仍是「始終準備著」） | 你始終準備著X法術 |
| a saving throw against a Counterspell you cast | 對抗你所施放的反制法術豁免失敗時（法術名後不加「的」） | 對抗你所施放的反制法術的豁免失敗時 |
| multiclass into a subclass that does not use d6 | 兼職不使用d6的子職業 | 兼職進入不使用d6的子職業 |

## 已裁定的同詞多義

同一個英文在不同語境有不同譯名，查索引時會回報「同一來源內部衝突」。下面是已經定案的，直接照用，不必再問：

| EN | 語境 | zh-tw |
|---|---|---|
| Shield | 法術 | 護盾術 |
| Shield | 物品／護甲 | 盾牌 |
| Arcane | 視語感選，奧術／祕法／奧法皆可（「奧術藝術家」拗口，故用奧法藝術家） | — |

同詞多義的詞不要強制取代。例如 `Arcane` 在既有譯文裡有奧術 26、祕法 12、奧法 11，三者都對，取決於語感（「奧術藝術家」拗口，所以用「奧法藝術家」）。遇到這種詞，列出選項和用量給使用者挑。

已確立的 2024 動作與狀態術語（已寫進 Weblate `terms`）：

| EN | zh-tw |
|---|---|
| Attack | 攻擊 |
| Dash | 疾走 |
| Disengage | 撤離 |
| Dodge | 迴避 |
| Help | 協助 |
| Hide | 躲藏 |
| Influence | 影響 |
| Magic | 魔法 |
| Ready | 準備 |
| Search | 搜索 |
| Study | 研究 |
| Utilize | 利用 |
| Bloodied | 重傷 |
| Carrying Capacity | 負重 |
| Emanation | 發散 |
| Line / Cone / Sphere / Cube / Cylinder | 直線／錐形／球形／立方體／圓柱體 |

## 魔法物品的譯名參考來源（2026-10-04 使用者指定）

魔法物品（DMG／XGE 等）的**名稱**優先查繁中資料，其次才是簡體稿轉繁：

1. **5etools 繁中站** `https://5etools.wayneh.tw/data/items.json`：每筆有 `name`（繁中）與 `ENG_name`，可直接用 `ENG_name` 比對；另有完整的 2014 版內文可參照用詞（只參照用詞，規則文字以 2024 稿與 EN 模板為準）。網頁版 `https://5etools.wayneh.tw/items.html`。
2. **DnD 5e 繁中資料站（Google Sites）** `https://sites.google.com/view/dnd5e-2/dnd職業資料`：使用者提供的另一份參考。
3. 簡體稿（OpenCC `s2twp` 轉繁）只當最後備援，且先確認專案既有譯名。

優先序：使用者已確認 > 專案既有譯名（Weblate／zh-tw）> Wayne 站 > 簡體稿轉繁。與既有譯名衝突時以既有為準（例：Orb 用「法球」，不用 Wayne 的「寶珠」）。Wayne 查無的名稱，轉繁後在預覽請使用者確認。

### DMG 魔法物品已定案的寫法（2026-10-04）
- 「採取…動作」；Consume 依物品（藥水→飲用、食物→食用）；Orb→法球；Pole→長桿；Prosthetic Limb→義肢。
- effect `changes.name` 也翻（`{} of X`→`X{}`）。
- 充能：「具有X點充能」「消耗X點充能」。
- **property（魔法物品的特殊能力）→「屬性」**（使用者 2026-10-05 定案）：this property→此屬性、any of its properties→其下列任一屬性、loses its properties→失去其所有屬性、magical properties→魔法屬性。與武器屬性（精通屬性）及 lang `DND5E.Properties` 一致；不用「特性」（留給 feature）或「特質」（PHB 種族 Traits 已用）。DMG equipment 既有 17 條「特性」已於同日以建議重傳。
- Giant Constrictor Snake → **巨型蟒蛇**（使用者 2026-10-05 定案，不用 Wayne／原稿的「巨蟒蛇」）。
- archfey → **至高妖精**（使用者 2026-10-06 定案；專案 Fey 類型詞為「精類」，但 archfey 不改）。芭芭·雅嘎的舞空帚、活化掃帚（Animated Broom）採原稿轉繁。
- 單位：ft.→呎、mi.→哩；gallon／ounce／quart→加侖／盎司／夸脫（台灣常見）；Mayonnaise→美乃滋。Driftglobe→漂浮光球（Wayne）；Water, fresh／salt→淡水／鹽水。
- Foundry 註記中的 UUID、@Embed 為技術名詞，validate 時用 `--allow UUID,Embed`。
- words→字；1 inch→1吋；Tiny（大寫，體型）→微型（2026-10-07 使用者更正，原「超小型」作廢，與 lang SizeTiny 一致）；tiny 小寫視情況。

### DMG 魔法物品名稱對照表（2026-10-04）
[dmg-magic-item-names.tsv](dmg-magic-item-names.tsv)：DMG `equipment` 全部 548 個 EN key 對 Wayne 站、Google Sites 兩邊的繁中名稱與專案現有 name。兩邊都沒有的有 248 條（多為 2024 新增或變體），需由稿子轉繁並請使用者確認。Google Sites 的名稱是從頁面表格抽取，少數因換行被截斷（例如「之靴」），以 Wayne 為準；兩邊 15 條不同的（錘／鎚、藥水名等）要問使用者。

## 舊版 sheet 的遷移（2026-10-07 重製）

舊版 `runs` 以 EN 文字作替換 key，相同文字可能互相覆蓋。新版 `schema_version=2` 以獨立區塊 ID 映射，重複表格文字可以各自填寫。保留原稿與底稿，重新 extract；不沿用舊的文字槽位，也不再以相同標籤序列限制中文語順。

## 2026-10-07 wondrous-a 重做定案（使用者）

重做原則：中文一律從原稿 OpenCC `s2twp` 轉繁再順稿，不從 EN 直譯；原稿與 EN 規則語意衝突時以 EN 為準並列入預覽。

| EN | zh-tw | 備註 |
|---|---|---|
| immediately after ⋯ | 緊接在⋯後 | 使用者指正；不寫「⋯後立即」 |
| on your Initiative count | 在你的先攻順位（上） | 不用「先攻值」；已寫進 `terms` |
| enricher | 擴充格式 | 依 lang `EnrichersGroup`＝D&D 擴充格式；已寫進 `terms` |
| Oil（酒壺／煉金壺液體表） | 油 | 使用者維持「油」；僅此語境，冒險裝備 Oil 仍為燃油 |
| Geyser／Fountain／Splash（無盡水瓶） | 井噴／落泉／水花 | 採原稿，不用自行直譯的間歇泉／噴泉 |
| Water, salt | 鹽水 | 原稿「鹹水」不採用 |
| archfey | 至高妖精 | 已寫進 `terms` |

**順稿原則（2026-10-07 使用者再次糾正與重製裁定）**：以原稿 s2twp 為底，核對規則精確度，再依台灣閱讀語順整理；規則語意衝突依 EN 提出修正並列出。映射沿用完整底稿，不照 EN 句型重新拼接。過去的逐句相似度供定位改動，驗收以來源對照、規則核對與中文通讀為準。

舊建議的刪除是另外的 Weblate 維護，需要使用者明確指定範圍；重製技能或準備新版底稿不包含刪除授權。

## 2026-10-07 wondrous-b 定案
- Oil 一律「油」（含顯像提燈「1品脫油」、行動「消耗油」）；先前「冒險裝備 Oil＝燃油」的例外作廢。
- 做法：底稿先獨立成檔給使用者審閱，再用腳本從底稿切取、只套標記（斷言去標記後逐字相同）；範例見 `_incoming/dungeon-master/_source/map-wondrous-b-from-draft.py`。

## 限定詞逐句核對（2026-10-07 使用者提醒）
順稿後、映射前，列出 EN 含 this／these／that／the／following／one of／each／any／all 的句子，與底稿並排核對：this＋實體物品→這個／這件／這支；this＋抽象（effect／property）→此；the→該或重述名詞（不沿用原稿的「此」）；following→下列；one of the following→下列其中一種。預覽列出核對結果。

## 2026-10-07 lang 比對規則與 suppressed／object 定案
- 詞彙比對一律三方並列：terms、glossary、`lang/zh-tw.json`（`scripts/lang_compare.py`），差異在預覽逐條說明。
- suppressed → **失效**（使用者裁定，全面改，含舊譯文與 lang）；lang `DND5E.Suppressed`、兩條 PromptTooltip 已改，記於 Changelog.md。已寫進 `terms`。
- object → 物體（lang 與語料 121:19）；已上傳的 wondrous-a／b 內「物件」暫不追改（使用者 2026-10-07）。
- swarm（一般名詞）→ 老鼠群等「X群」，不用 lang 的「集群」（使用者 2026-10-07：老鼠群就好）。
- this＋實體物品在 Foundry 註記亦寫「這件物品」，不採 lang UI 的「此物品」。

## 2026-10-07 Forge of the Artificer 第 2 批裁定
- **As a ⋯ action while ⋯**：譯「持握／手持…期間以一個魔法動作…」（與「採取某動作」同為規則文字句式；使用者確認）。例：While holding Tinker's Tools → 持握修補匠工具期間。
- **書名**：Player's Handbook、Dungeon Master's Guide 等寫成《玩家手冊》《城主指南》，加書名號（em 內）。第 1 批已上傳者未加，之後統一。
- **Tinkered X（效果名）**＝工藝X（例：工藝滾珠）；Item Options＝物品選項；Create Item（活動）＝創造物品。
- **disintegrate（動詞）**＝瓦解（使用者 2026-10-07；Soul of Artifice 的 Cheat Death，不用「解離」；Disintegrate 法術名仍為解離術）。
- **equals／equal to**＝等同於（次數句、加值句皆用）。2026-10-09使用者再次確認，`equal to` 已寫入 Weblate `terms`（unit193790）；後續底稿依此術語對照。

## 2026-10-07 wondrous-c.2 定案
- 力場珠的 sphere's wall／force barrier → **力場障壁**（照簡體原稿）；隱形力場（不改透明）。
- Object interaction → 物體互動。
- 含擲骰巨集（`[[/r …]]`）的句子：validator 會剔除巨集，底稿以明文骰式（如「1d4 + 4」）書寫，該區塊標 supplement 並在 basis 說明，其餘句子仍逐字取自底稿。

## 2026-10-07 wondrous-d.1 定案
- Wall of Force → **力場牆**（使用者裁定，全面更改，原 Weblate「力牆術」作廢）：spells-glossary 已改；PHB spells、dnd5e spells24 的法術名已以建議送出（待接受）；dnd5e-items／2024 專案副本的 Staff of Power 描述、Disintegrate 描述內仍有「力牆術」，路徑非 compendium/zh-tw（副本），未處理，待使用者指示。
- Tiny（大寫）→ 微型（同 lang）；Tiny→超小型 的舊裁定作廢；小寫 tiny 視情況。
- 召喚魔方行動名：構裝體／精類（既有法術名），也可用構裝／妖精（使用者：皆可）。
- 免疫句式：「免疫除攻城器械以外所造成的鈍擊、穿刺、揮砍傷害」（使用者 2026-10-07）。
- 戴恩的瞬間要塞：「推到緊鄰高塔外的未佔據空間」；the tower has a single door 照原稿「會出現一扇門」。

## 召喚生物回合句式（2026-10-07 使用者更正）
takes its turn immediately after you on your Initiative count → **並緊接在你的先攻順位後進行其回合**（取代「並在你的先攻順位上緊接在你之後進行其回合」）。適用元素寶石、命令水元素水缽、命令火元素火盆、控制氣元素香爐，以及之後所有同句式條目。

## 2026-10-07 wondrous-d.2 定案
- Total Cover → **全掩蔽**（使用者裁定，全局改動；PHB 既有）：lang `StatusTotalCover` 已由「完全掩護」改，記入 Changelog.md；arcana-unleashed Spell Subterfuge 描述的「全身掩護」以建議送出；已寫進 `terms`。lang 的 `StatusHalfCover`（半掩護）、`StatusThreeQuartersCover`（四分之三掩護）仍是「掩護」，與 `DND5E.CoverHalf` 等的「掩蔽」不一致，待使用者決定是否一併改。
- 「from using any method of extradimensional movement」照原稿：進行異次元移動（不加「任何形式」）。
- 空氣句式：「所容納的空氣量足以維持呼吸10分鐘，並由其中所有需要呼吸的生物均分」（霍華德的便利袋；次元袋已上傳的句式不同，未追改）。
- Seeing（真視寶石效果名）→ 真視；啟動摺疊船、划艇、龍骨船、condition 譯法：可。
- **子職業**（Subclass）：全庫既有 93 處皆為「子職業」、「子職」0 處，lang 亦同；2026-10-07 發現第 1 批誤寫「子職」，重做改回。先前 `usage.py 子職 子職業` 的用量相同是子字串重疊造成，不是兩者並用。
- **Components＝構材、Material component＝材料構材**（使用者 2026-10-07；取代「成分」「材料成分」）。`&Reference[components]{構材}`。已對 Weblate 送出既有「材料成分」的改寫建議。
- **Epic Boon＝傳奇恩惠**（使用者 2026-10-07 全面採用，取代「史詩恩惠」）；lang 與既有 PHB／dnd5e classes 已同步送建議。
- **SpellAbility／Spellcasting Ability＝施法屬性**（lang 已改，取代「施法能力」）。

## 2026-10-07 wondrous-e 定案
- 書名一律加《》：「該生物的數值面板見《怪物圖鑑》」，EN 的 `<em>Monster Manual</em>` 譯為 `<em>《怪物圖鑑》</em>`（使用者 2026-10-07）。已上傳的 wondrous-d.2「玩家手冊」未加《》，未追改。
- 灰色／鐵鏽色／棕褐色魔術袋：照原稿；控制土元素之石：名稱沿用專案既有，內文參照原稿（無）與已存在的同類條目補翻。
- 召喚生物「acts immediately after you on your Initiative count」→ 並緊接在你的先攻順位後行動；「takes its turn…」→ 並緊接在你的先攻順位後進行其回合。

## 2026-10-08 tables 元件（DMG RollTable）定案
- **Undead＝不死生物**、**Ethereal＝乙太（Ethereal Plane＝乙太位面）**：使用者全面裁定；lang 已改（Changelog.md）。
- tables 條目 `results` 每列一塊（`r:<區間>`），用 `skeleton.py extract/build` 與 `validate.py` 處理；區間鍵不翻。含 `[[/…]]` 巨集的列標 supplement（底稿以明文骰式書寫）。
- 無標籤的 `@UUID[…]`（EN 本身無 `{}`）在中文補上可見標籤。表名＝物品名時沿用物品譯名（雜貨法袍）。
- 「Weblate 現行 2024 名稱優先於舊簡體稿」（緩速術、老鼠、騎用馬、便攜型攻城鎚、鯊蜥獸、尖叫蕈、治療傷勢、虔誠守衛）。
- 單位：吋（inch）、呎；GP 寫「500 GP」（數字與 GP 間留空格，與 EN 一致）。

## 2026-10-08 tables 第二輪裁定
- **Gnoll＝鬣狗人**（使用者裁定；Gnoll Warrior＝鬣狗人武者）。lang `Language.Gnoll` 已改「鬣狗人語」。Weblate 怪物 `Gnoll`（現「豺狼人」）尚未送建議。Jackal＝豺狼、Hyena＝鬣狗不變。
- **Emerald＝翡翠**（寶石、藝術品皆是）；**Bloodstone＝血石**。
- 兩個 Bane（歷史表 History 與特殊目標 Special Purpose）語境不同，分別用「破滅」「制造災禍」，不統一。
- 魔法物品 Minor／Major Property 表名用「次要／主要屬性」，Quirk 表＝魔法物品的影響。
- **Goblin＝哥布林**（使用者 2026-10-08；Goblin Warrior＝哥布林武者）。Weblate 怪物現為「地精」，尚未改；lang `Language.Goblin`＝哥布林語已一致。Bugbear＝熊地精、Hobgoblin＝大地精暫沿用 Weblate，若要連動改「熊哥布林」「大哥布林」需使用者另行裁定。
- 已上傳的 tables.items-c1（幻象牌組）第 15 列仍是「地精武者」，使用者指示不重傳；之後 Weblate 審閱時請改為哥布林武者。
- **Bugbear＝熊哥布林、Hobgoblin＝大哥布林**（使用者 2026-10-08，連動 Goblin＝哥布林）；Bugbear Warrior＝熊哥布林武者、Hobgoblin Warrior＝大哥布林武者。Weblate 怪物現為熊地精／大地精，尚未改。已上傳的幻象牌組第 7、18 列仍是「熊地精武者」「大地精武者」，不重傳。

## 2026-10-08 塔莎的熔爐魔法物品（tcoe-magic-items）定案
- **稀有度不寫**：EN 描述沒有稀有度時，原稿的稀有度（非普通（+1）…）不入可見文字；類型行寫「奇物，需由X同調」（武器寫「武器（鏈枷），需由X同調」）。
- **名稱**：鍊金總綱（用「鍊」）、守禦詩篇、鐘鈴聖枝（簡轉繁「鍾」改「鐘」）、外界精粹碎晶（保留「外界」）、星卜編集、寰宇圖纂、兩面花言、爆鳴專論、織心入門、靈肉聖契、異界行訪錄、萬能工具、虔信護符、奧法祕典（祕）、血源瓶、月鐮、調律者之鼓、妖精荒野碎晶、星界碎晶、遙遠國度碎晶、墮影冥界碎晶、元素精粹碎晶、守護者紋章、自然斗篷、狂宴手風琴、奉獻香爐、建築里拉琴。Wayne 站沒有 TCE 條目，名稱以原稿轉繁。
- **詞**：pristine＝一塵不染；indifferent（態度）＝冷漠；skin（皮製封面）依原稿「人皮」；implement＝器具；Wild Magic Sorcerous Origin 用 PHB 現行「狂野術法」；Otto's irresistible dance＝奧圖狂舞術（詞彙表「狂舞術」）；spiritual tradition＝靈性傳統；effect 名「Cursed X」＝X受詛；薰香（台灣用字，取代「熏香」）；Great Wheel 暫用原稿「巨輪」待裁定。
- **魔法學派**：一律「X學派」（防護／咒法／預言／惑控／塑能／幻術／死靈／變化學派），lang `DND5E.School*` 已同步，記於 Changelog.md。
- **一般用字依 terms**：take（承受傷害）→承受；immediately after→緊接在…後；`It takes 10 minutes`、`take on a semblance`、`takes its turn`、`takes the Dodge action`、`fiend hide` 屬一般用字，不套 terms，須在 `ack.json` 登記。
- **保留原稿**：奉獻香爐「你可以將這把鏈枷視為聖徽」（使用者確認不改）；奉獻香爐攻擊句補 magic（使用者確認改）。
- **修訂的判準**：使用者 2026-10-08 指示「已有譯文且與 EN 差異不大者不改，其餘依底稿處理，有差異皆報告」→ 實作為 translation-quality.md 的「允許的修改類別」。
