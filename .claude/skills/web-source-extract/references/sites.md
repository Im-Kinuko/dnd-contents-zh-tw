# 各站特性

## 5echm.kagangtuya.top（簡體，WinCHM「5E 不全書」）

- 使用者給的網址是外殼：`/?page=<路徑>`。真實內容在 `/topics/<路徑>`，腳本會自動轉換。
- 內容頁本身不含子頁連結，要靠目錄 `https://5echm.kagangtuya.top/webhelpcontents.htm`（`--toc`）列出，所有頁面都以 `topics/` 開頭。
- 內容格式：每個條目以 `<H6>中文 English` 開頭，內文用 `<P>`、`<BR>`、表格。分類頁路徑為 `城主指南2024/7.宝藏/魔法物品详述/<類別>/<稀有度>.htm`，類別有藥水、護甲、武器、戒指、卷軸、法杖、魔杖、權杖、奇物（著裝品／裝飾品／其他物品），稀有度有普通、非普通、珍稀、極珍稀、傳說、神器、多種稀有度。
- 簡體字，要先 OpenCC `s2twp`，並以 `dmg-magic-item-names.tsv` 的繁中名稱為準。
- 稿子常把變體寫成同一條裡的表格列（治療藥水、巨人之力藥水），EN 模板則拆成多個 key，`split` 會把這類標為「對不上 EN 模板」，需另外對齊。

## sites.google.com/view/dnd5e-2（繁體，Google Sites）

- 每頁約 16–40 KB，其中大半是導覽列雜訊；真正內容混在表格裡。
- 條目名稱與英文名分散在相鄰行，英文名還會被換行與 `_` 截斷（例如 `Moon-Touched`／`_`／`Sword`）。以 `split` 的標題規則抓不到，需要先讀 `fetch` 產生的 `.txt`，自行以「中文名行＋英文名行」比對。
- 康熙部首字（如「⼔⾸」）由 NFKC 正規化還原。
- 子頁連結在首頁的 HTML `href="/view/dnd5e-2/…"`，以 `--prefix 魔法物品定價與規則` 或 `一般物品` 篩選。

## 5etools.wayneh.tw

- 不用網頁，直接讀 `/data/items.json`；每筆有繁中 `name` 與 `ENG_name`，以 `ENG_name` 對 EN key。不屬於本腳本，查名稱時另外用 `curl` 即可。
