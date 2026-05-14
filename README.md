# Marketing Dashboard_VivaVictors

本專案為 **PEP with VivaVictors** 的跨境電商行銷儀表板。它的目的不是只展示圖表，而是讓行銷人員可以每天用來判斷：要鎖定哪個市場、推哪個商品、給什麼素材、用什麼優惠、如何追蹤成效。

## 線上儀表板

- Streamlit 網頁：<https://bizconnectappv3.streamlit.app/>
- GitHub 專案：<https://github.com/yiyu0501/bizconnect_streamlit_app_v3>

## 這一版的重點

這版新增並強化「準個人化行銷」功能。它不能為 1,024 位顧客各拍一支影片，但能用比較接近實務的方式，將顧客依照推薦商品、偏好路線、RFM／CAI 標籤與購買意願，分配到不同的：

- 主推商品
- 廣告素材路線
- 行銷話術
- 優惠級距
- 投放通路
- AI 素材 Prompt
- A/B 測試方向

這樣可以把有限素材，例如 3–4 支影片、10 多種文案與數種優惠，組合成可測試、可迭代的個人化行銷方案。

## 儀表板頁面

1. 首頁｜總覽與操作手冊
2. 市場區隔｜顧客偏好族群
3. 目標市場｜技詮優先客群
4. 產品定位｜技詮如何被記住
5. 商品策略｜主推與檢討清單
6. 產品推廣｜廣告與效益試算
7. 顧客推薦｜準個人化行銷與 AI 素材
8. 顧客名單｜RFM/CAI 策略
9. 評論洞察｜痛點與 Listing 改善

## 一對一行銷頁面的使用方式

此頁分成四個區塊：

| 區塊 | 用途 |
|---|---|
| 批次投放工作台 | 依素材路線、商品策略、優惠級距快速篩出受眾名單 |
| 素材與優惠規則 | 說明技術規格型、實用功能型、風格美學型、價格誘因型素材如何使用 |
| 單一顧客查詢 | 保留 Customer_ID 查詢，可產出 Top 5 商品與 AI 素材草稿 |
| A/B 測試與迭代 | 說明如何用 CTR、CVR、AOV、ROAS 驗證素材是否有效 |

## 資料檔案

請將下列檔案放在 `data/` 資料夾：

| 檔案 | 用途 |
|---|---|
| `KMeans_Final_Result.xlsx` | 市場區隔／產品偏好族群資料，取代舊版 KMeans 檔案 |
| `RFM_CAI 統整.xlsx` | 顧客價值標籤與名單策略 |
| `ridge_logit_customer_specific_report_20260508_110837.xlsx` | 商品購買率、推薦模型與 Top 5 推薦 |
| `reviews_processed_classified.csv` | 評論動機與情緒分析 |
| `reviews_summary_processed.csv` | ASIN 層級評論摘要 |
| `正交設計_產品組合.xlsx` | 商品組合、品牌、價格、顏色、規格、GPS 與 ASIN 對照 |

## 本機執行

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 更新資料方式

若老師或組員提供新版分群資料，請用新版 `KMeans_Final_Result.xlsx` 取代 `data/` 裡的同名檔案。不要刪掉 RFM／CAI、推薦模型、評論或產品對照資料，因為它們分別支撐其他頁面。
