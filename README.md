# PEP with VivaVictors｜Marketing Dashboard

本專案為「2026 BizConnect Taipei－台北數位產學實作計畫」之電商行銷分析儀表板。  
我們將顧客購買資料、RFM／CAI 顧客標籤、產品組合資料、Amazon 顧客評論與個人化推薦模型整合為一個 Streamlit 互動式網頁，讓廠商可以用更直覺的方式檢視商品表現與顧客行銷策略。

---

## 線上使用連結

正式儀表板：  
https://pepwithvivavictors.streamlit.app/

目前 GitHub 專案：  
https://github.com/yiyu0501/bizconnect_streamlit_app_v3

建議重新命名後的 GitHub 專案名稱：  
`Marketing-Dashboard_VivaVictors`

---

## 這個儀表板在做什麼？

本儀表板主要回答三個問題：

1. **哪些商品組合值得優先推廣？**  
   透過產品組合購買率、預測購買機率與產品屬性，找出高潛力商品。

2. **不同顧客適合推薦哪些商品？**  
   透過個人化推薦模型，為每位顧客產出 Top 5 推薦商品。

3. **顧客評論反映哪些購買動機？**  
   透過 Amazon 評論文字與星級，歸納功能需求、品質信任、價格敏感、外觀偏好、規格適配等動機。

---

## 主要功能

### 1. 首頁總覽

顯示整體顧客數、購買筆數、購買率與評論數，並呈現購買率最高的前 10 個產品組合。

### 2. 顧客標籤 RFM／CAI

整合顧客 RFM 與 CAI 標籤，用來觀察高價值顧客、潛力顧客與需喚回顧客的分布。

### 3. 產品組合分析

可依品牌、顏色、規格篩選 22 種產品組合，檢視實際購買率與模型預測結果。

### 4. 評論動機分析

將顧客評論整理為不同購買動機與情緒類型，用來補強市場區隔與商品頁優化建議。

### 5. 個人化推薦查詢

輸入或選擇 Customer_ID，即可查看該顧客的最佳推薦商品與 Top 5 推薦清單。

### 6. 策略建議與維護

整理本專案對廠商的應用價值，並說明資料更新、模型更新與後續維護方式。

---

## 專案資料夾結構

```text
Marketing-Dashboard_VivaVictors/
├── streamlit_app.py
├── requirements.txt
├── README.md
└── data/
    ├── RFM_CAI 統整.xlsx
    ├── reviews_processed_classified.csv
    ├── reviews_summary_processed.csv
    ├── ridge_logit_customer_specific_report_20260508_110837.xlsx
    └── 正交設計_產品組合.xlsx
```

---

## 資料檔說明

| 檔案名稱 | 用途 |
|---|---|
| `RFM_CAI 統整.xlsx` | 顧客 RFM／CAI 標籤資料 |
| `reviews_processed_classified.csv` | 已分類之評論明細，包含動機與情緒 |
| `reviews_summary_processed.csv` | ASIN 層級評論摘要 |
| `ridge_logit_customer_specific_report_20260508_110837.xlsx` | Ridge Logistic Regression 與個人化推薦模型輸出 |
| `正交設計_產品組合.xlsx` | 產品組合、品牌、價格、顏色、規格、GPS 與 ASIN 對照 |

---

## 如何更新資料？

若後續有新版資料，直接替換 `data/` 資料夾中的同名檔案即可。

- 重新跑推薦模型：更新 `ridge_logit_customer_specific_report_20260508_110837.xlsx`
- 新增或重整評論：更新 `reviews_processed_classified.csv` 與 `reviews_summary_processed.csv`
- 產品組合或 ASIN 改變：更新 `正交設計_產品組合.xlsx`
- 顧客標籤更新：更新 `RFM_CAI 統整.xlsx`

GitHub 更新後，Streamlit Cloud 通常會自動重新部署。若畫面沒有更新，可至 Streamlit 的 **Manage app** 手動 Reboot。

---

## 本機執行方式

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

---

## 對廠商的應用價值

本專案可協助廠商：

1. 找出高購買率產品組合，作為商品主推依據。
2. 透過 RFM／CAI 標籤辨識高價值顧客與潛力顧客。
3. 依顧客評論歸納購買動機，補強市場區隔分析。
4. 為每位顧客產出 Top 5 推薦商品，作為個人化行銷雛形。
5. 將 Excel 與模型結果轉換為互動式儀表板，降低廠商閱讀大量數據表的成本。
6. 後續可延伸至商品頁優化、廣告素材設計、再行銷名單與 ROI 分析。

---

## 目前限制

1. 評論資料目前以 ASIN／商品層級分析，尚未完全對應到每位 Customer_ID。
2. 尚未取得完整成本、毛利與廣告成本，因此目前不計算真實 ROI。
3. 願付價格與最適定價仍需依課堂公式或廠商實際資料補強。
4. 推薦模型目前為初步模型，後續可加入交叉驗證、模型校準與 A/B Test。
