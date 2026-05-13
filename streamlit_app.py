import os
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

APP_TITLE = "PEP with VivaVictors｜Marketing Dashboard"
REPO_URL = "https://github.com/yiyu0501/bizconnect_streamlit_app_v3"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

MODEL_FILE = "ridge_logit_customer_specific_report_20260508_110837.xlsx"
DESIGN_FILE = "正交設計_產品組合.xlsx"
RFM_FILE = "RFM_CAI 統整.xlsx"
REVIEWS_FILE = "reviews_processed_classified.csv"
REVIEWS_SUMMARY_FILE = "reviews_summary_processed.csv"

BRAND_COLUMNS = ["Dolphin Gauges", "Faria", "MOTOR METER RACING", "Speedway Motors", "RACETECH"]
COLOR_COLUMNS = ["orange", "white", "beige", "green", "blue", "yellow", "black", "紅色", "白色", "黑色", "米色"]
SPEC_COLUMNS = ["Npt", "Sae,Npt", "Sae"]

COLOR_ZH = {
    "orange": "橘色",
    "white": "白色",
    "beige": "米色",
    "green": "綠色",
    "blue": "藍色",
    "yellow": "黃色",
    "black": "黑色",
    "紅色": "紅色",
    "白色": "白色",
    "黑色": "黑色",
    "米色": "米色",
}

MOTIVATION_ORDER = ["功能需求", "品質信任", "外觀偏好", "價格敏感", "規格適配", "品牌信任", "其他"]

st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")

# -----------------------------
# Common helpers
# -----------------------------

def ensure_numeric(series, default=0):
    return pd.to_numeric(series, errors="coerce").fillna(default)


def unique_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[:, ~df.columns.duplicated()].copy()


def first_existing(df: pd.DataFrame, candidates, default=None):
    for col in candidates:
        if col in df.columns:
            return df[col]
    return pd.Series([default] * len(df), index=df.index)


def one_hot_label(row, columns, default="未標示"):
    for col in columns:
        if col in row.index:
            try:
                if float(row[col]) == 1:
                    return col
            except Exception:
                if str(row[col]).strip() in ["1", "是", "TRUE", "True", "true"]:
                    return col
    return default


def build_product_label(row):
    gps = "有GPS" if str(row.get("GPS_Flag", "0")) in ["1", "1.0", "有", "True", "true"] else "無GPS"
    return f"#{int(row['Product_Row'])}｜{row.get('Brand', '未標示')}｜${row.get('Price', '')}｜{row.get('Color', '未標示')}｜{row.get('Spec', '未標示')}｜{gps}"


def show_data_warning(missing_files):
    if not missing_files:
        return
    with st.expander("資料檔案缺漏提醒", expanded=True):
        st.warning("目前 GitHub 的 data/ 資料夾還缺少以下檔案，部分頁面可能無法完整顯示。")
        for f in missing_files:
            st.write(f"- `{f}`")
        st.write("請確認檔案名稱完全一致，且檔案放在 `data/` 資料夾內。")


@st.cache_data(show_spinner=False)
def check_required_files():
    required = [MODEL_FILE, DESIGN_FILE, RFM_FILE, REVIEWS_FILE, REVIEWS_SUMMARY_FILE]
    return [name for name in required if not (DATA_DIR / name).exists()]


# -----------------------------
# Data loading
# -----------------------------

@st.cache_data(show_spinner=False)
def load_product_design():
    path = DATA_DIR / DESIGN_FILE
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_excel(path)
    df = unique_columns(df)
    df = df.rename(columns={
        "組合_品牌": "Design_Brand",
        "組合_原價(轉換後)": "Design_Price",
        "組合_錶盤顏色": "Design_Color",
        "組合_螺紋類型": "Design_Spec",
        "組合_GPS天線": "Design_GPS",
        "對應 ASIN": "ASIN",
    })
    df["Product_Row"] = range(1, len(df) + 1)
    return df


@st.cache_data(show_spinner=False)
def load_product_summary():
    path = DATA_DIR / MODEL_FILE
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_excel(path, sheet_name="Product_Summary")
    df = unique_columns(df)
    df["Product_Row"] = ensure_numeric(df.get("Product_Row"), default=0).astype(int)

    design = load_product_design()
    if not design.empty:
        keep = ["Product_Row", "Design_Brand", "Design_Price", "Design_Color", "Design_Spec", "Design_GPS", "ASIN"]
        df = df.merge(design[[c for c in keep if c in design.columns]], on="Product_Row", how="left")
        df = unique_columns(df)

    df["Price"] = ensure_numeric(first_existing(df, ["Design_Price", "price", "Price", "Price_Level"]), default=0).astype(int)
    df["Brand"] = first_existing(df, ["Design_Brand", "Brand"], default=None)
    df["Color"] = first_existing(df, ["Design_Color", "Color"], default=None)
    df["Spec"] = first_existing(df, ["Design_Spec", "Spec"], default=None)
    df["GPS_Flag"] = ensure_numeric(first_existing(df, ["Design_GPS", "GPS", "GPS_Flag"], default=0), default=0).astype(int)

    for idx, row in df.iterrows():
        if pd.isna(row.get("Brand")) or row.get("Brand") in [None, ""]:
            df.at[idx, "Brand"] = one_hot_label(row, BRAND_COLUMNS)
        if pd.isna(row.get("Color")) or row.get("Color") in [None, ""]:
            df.at[idx, "Color"] = COLOR_ZH.get(one_hot_label(row, COLOR_COLUMNS), one_hot_label(row, COLOR_COLUMNS))
        else:
            df.at[idx, "Color"] = COLOR_ZH.get(str(row.get("Color")), row.get("Color"))
        if pd.isna(row.get("Spec")) or row.get("Spec") in [None, ""]:
            df.at[idx, "Spec"] = one_hot_label(row, SPEC_COLUMNS)

    df["Actual_Purchase_Count"] = ensure_numeric(df.get("Actual_Purchase_Count"), default=0).astype(int)
    df["N_Customers"] = ensure_numeric(df.get("N_Customers"), default=0).astype(int)
    df["Actual_Purchase_Rate"] = ensure_numeric(df.get("Actual_Purchase_Rate"), default=0)
    df["Mean_Predicted_Probability"] = ensure_numeric(df.get("Mean_Predicted_Probability"), default=0)
    df["Product_Label"] = df.apply(build_product_label, axis=1)

    return df


@st.cache_data(show_spinner=False)
def load_recommendations():
    path = DATA_DIR / MODEL_FILE
    if not path.exists():
        return pd.DataFrame()

    rec = pd.read_excel(path, sheet_name="Recommendation_Top5")
    rec = unique_columns(rec)
    rec["Customer_ID"] = rec["Customer_ID"].astype(str)
    rec["Product_Row"] = ensure_numeric(rec.get("Product_Row"), default=0).astype(int)
    rec["Predicted_Probability"] = ensure_numeric(rec.get("Predicted_Probability"), default=0)
    rec["Predicted_Probability_Percent"] = ensure_numeric(
        first_existing(rec, ["Predicted_Probability_Percent"], default=rec["Predicted_Probability"] * 100), default=0
    )
    rec["Rank"] = rec.groupby("Customer_ID")["Predicted_Probability"].rank(method="first", ascending=False).astype(int)

    product = load_product_summary()
    if not product.empty:
        attrs = product[["Product_Row", "Brand", "Price", "Color", "Spec", "GPS_Flag", "Product_Label"]].drop_duplicates("Product_Row")
        rec = rec.merge(attrs, on="Product_Row", how="left", suffixes=("", "_prod"))

    return rec


@st.cache_data(show_spinner=False)
def load_rfm():
    path = DATA_DIR / RFM_FILE
    if not path.exists():
        return pd.DataFrame()

    xls = pd.ExcelFile(path)
    sheet = "整合檔" if "整合檔" in xls.sheet_names else xls.sheet_names[0]
    df = pd.read_excel(path, sheet_name=sheet)
    df = unique_columns(df)
    df = df.rename(columns={
        "顧客代號": "Customer_ID",
        "Segment_Name": "RFM_Label",
        "RFM組別": "RFM_Label",
        "顧客分群": "CAI_Label",
    })
    if "Customer_ID" in df.columns:
        df["Customer_ID"] = df["Customer_ID"].astype(str)
    if "RFM_Label" not in df.columns and "RFM" in df.columns:
        df["RFM_Label"] = df["RFM"].astype(str)
    if "CAI_Label" not in df.columns:
        df["CAI_Label"] = "未對接 CAI"
    return df


@st.cache_data(show_spinner=False)
def load_reviews():
    path = DATA_DIR / REVIEWS_FILE
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df = unique_columns(df)
    if "Rating" in df.columns:
        df["Rating"] = ensure_numeric(df["Rating"], default=0)
    if "Motivation_Type" not in df.columns:
        df["Motivation_Type"] = "其他"
    if "Sentiment" not in df.columns:
        df["Sentiment"] = df.get("Sentiment_Label", "未分類")
    return df


@st.cache_data(show_spinner=False)
def load_reviews_summary():
    path = DATA_DIR / REVIEWS_SUMMARY_FILE
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    return unique_columns(df)


# -----------------------------
# UI pages
# -----------------------------

def sidebar():
    st.sidebar.title("導覽")
    st.sidebar.caption("2026 BizConnect Taipei｜VivaVictors")
    return st.sidebar.radio(
        "請選擇頁面",
        ["首頁總覽", "顧客標籤 RFM／CAI", "產品組合分析", "評論動機分析", "個人化推薦查詢", "策略建議與維護"],
    )


def overview_page():
    st.title(APP_TITLE)
    st.caption("以顧客標籤、產品組合、評論動機與個人化推薦模型，輔助廠商制定電商行銷策略。")

    missing = check_required_files()
    show_data_warning(missing)

    product = load_product_summary()
    rec = load_recommendations()
    reviews = load_reviews()

    total_customers = rec["Customer_ID"].nunique() if not rec.empty else 0
    total_purchase = int(product["Actual_Purchase_Count"].sum()) if not product.empty else 0
    total_exposure = int(product["N_Customers"].sum()) if not product.empty else 0
    purchase_rate = total_purchase / total_exposure * 100 if total_exposure else 0
    review_count = len(reviews) if not reviews.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("顧客數", f"{total_customers:,}")
    c2.metric("購買筆數", f"{total_purchase:,}")
    c3.metric("整體購買率", f"{purchase_rate:.2f}%")
    c4.metric("評論數", f"{review_count:,}")

    st.markdown("---")
    st.subheader("這個儀表板可以幫廠商做什麼？")
    st.markdown(
        """
        本儀表板把原本分散在 Excel、R 模型與顧客評論中的資料整合在一起，讓廠商可以快速回答三個問題：

        1. **哪些商品組合值得優先推廣？** 透過購買率與產品屬性比較，找出高潛力組合。
        2. **不同顧客應該推薦什麼商品？** 透過 Top 5 個人化推薦，支援一對一行銷與再行銷。
        3. **顧客真正重視什麼？** 透過評論動機與情緒分析，了解功能、品質、外觀、價格與規格等購買因素。
        """
    )

    if not product.empty:
        st.subheader("購買率最高的前 10 個產品組合")
        chart_df = product.sort_values("Actual_Purchase_Rate", ascending=False).head(10).copy()
        chart_df = chart_df[["Product_Label", "Actual_Purchase_Rate", "Actual_Purchase_Count", "Brand", "Price", "Color", "Spec", "GPS_Flag"]]
        chart_df = chart_df.rename(columns={
            "Product_Label": "產品組合",
            "Actual_Purchase_Rate": "購買率",
            "Actual_Purchase_Count": "購買筆數",
            "Brand": "品牌",
            "Price": "售價",
            "Color": "顏色",
            "Spec": "規格",
            "GPS_Flag": "GPS",
        })
        chart = alt.Chart(chart_df).mark_bar().encode(
            x=alt.X("購買率:Q", title="實際購買率（%）"),
            y=alt.Y("產品組合:N", sort="-x", title="產品組合"),
            tooltip=[
                alt.Tooltip("產品組合:N"),
                alt.Tooltip("品牌:N"),
                alt.Tooltip("售價:Q"),
                alt.Tooltip("顏色:N"),
                alt.Tooltip("規格:N"),
                alt.Tooltip("GPS:Q"),
                alt.Tooltip("購買率:Q", format=".2f"),
                alt.Tooltip("購買筆數:Q"),
            ],
        ).properties(height=420)
        st.altair_chart(chart, use_container_width=True)
        st.info("圖表解讀：購買率較高的組合可作為商品主推、廣告素材與庫存配置的優先參考。")


def segmentation_page():
    st.title("顧客標籤 RFM／CAI")
    rfm = load_rfm()
    if rfm.empty:
        st.warning("目前沒有讀到 RFM／CAI 標籤資料。")
        return

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("RFM 顧客價值分布")
        if "RFM_Label" in rfm.columns:
            counts = rfm["RFM_Label"].fillna("未分類").value_counts().reset_index()
            counts.columns = ["顧客標籤", "人數"]
            chart = alt.Chart(counts).mark_bar().encode(
                x=alt.X("人數:Q"),
                y=alt.Y("顧客標籤:N", sort="-x"),
                tooltip=["顧客標籤", "人數"],
            ).properties(height=420)
            st.altair_chart(chart, use_container_width=True)

    with c2:
        st.subheader("CAI 活躍標籤分布")
        if "CAI_Label" in rfm.columns:
            counts = rfm["CAI_Label"].fillna("未對接 CAI").value_counts().reset_index()
            counts.columns = ["CAI 標籤", "人數"]
            chart = alt.Chart(counts).mark_bar().encode(
                x=alt.X("人數:Q"),
                y=alt.Y("CAI 標籤:N", sort="-x"),
                tooltip=["CAI 標籤", "人數"],
            ).properties(height=420)
            st.altair_chart(chart, use_container_width=True)

    st.subheader("顧客標籤明細")
    cols = [c for c in ["Customer_ID", "RFM", "RFM_Label", "CAI_Label"] if c in rfm.columns]
    st.dataframe(rfm[cols], use_container_width=True, hide_index=True)


def product_page():
    st.title("產品組合分析")
    product = load_product_summary()
    if product.empty:
        st.warning("目前沒有讀到產品組合資料。")
        return

    brands = ["全部"] + sorted(product["Brand"].dropna().astype(str).unique().tolist())
    colors = ["全部"] + sorted(product["Color"].dropna().astype(str).unique().tolist())
    specs = ["全部"] + sorted(product["Spec"].dropna().astype(str).unique().tolist())

    c1, c2, c3 = st.columns(3)
    b = c1.selectbox("品牌", brands)
    color = c2.selectbox("顏色", colors)
    spec = c3.selectbox("規格", specs)

    df = product.copy()
    if b != "全部":
        df = df[df["Brand"].astype(str) == b]
    if color != "全部":
        df = df[df["Color"].astype(str) == color]
    if spec != "全部":
        df = df[df["Spec"].astype(str) == spec]

    st.subheader("產品組合表現")
    view = df[["Product_Row", "Product_Label", "Brand", "Price", "Color", "Spec", "GPS_Flag", "Actual_Purchase_Count", "Actual_Purchase_Rate", "Mean_Predicted_Probability"]].copy()
    view = view.rename(columns={
        "Product_Row": "產品編號",
        "Product_Label": "產品組合",
        "Brand": "品牌",
        "Price": "售價",
        "Color": "顏色",
        "Spec": "規格",
        "GPS_Flag": "GPS",
        "Actual_Purchase_Count": "購買筆數",
        "Actual_Purchase_Rate": "實際購買率(%)",
        "Mean_Predicted_Probability": "平均預測機率(%)",
    })
    st.dataframe(view.sort_values("實際購買率(%)", ascending=False), use_container_width=True, hide_index=True)

    st.subheader("購買率視覺化")
    chart = alt.Chart(view).mark_bar().encode(
        x=alt.X("實際購買率(%):Q", title="購買率（%）"),
        y=alt.Y("產品組合:N", sort="-x", title="產品組合"),
        color=alt.Color("品牌:N"),
        tooltip=["產品組合", "品牌", "售價", "顏色", "規格", "GPS", alt.Tooltip("實際購買率(%):Q", format=".2f")],
    ).properties(height=520)
    st.altair_chart(chart, use_container_width=True)


def review_page():
    st.title("評論動機分析")
    reviews = load_reviews()
    summary = load_reviews_summary()
    if reviews.empty:
        st.warning("目前沒有讀到評論資料。")
        return

    avg_rating = reviews["Rating"].mean() if "Rating" in reviews.columns else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("評論數", f"{len(reviews):,}")
    c2.metric("平均星級", f"{avg_rating:.2f}")
    c3.metric("主要動機", reviews["Motivation_Type"].mode().iloc[0] if not reviews["Motivation_Type"].mode().empty else "未分類")

    st.subheader("顧客評論動機分布")
    mot = reviews["Motivation_Type"].fillna("其他").value_counts().reset_index()
    mot.columns = ["動機類型", "評論數"]
    mot["排序"] = mot["動機類型"].apply(lambda x: MOTIVATION_ORDER.index(x) if x in MOTIVATION_ORDER else 99)
    mot = mot.sort_values(["排序", "評論數"])
    chart = alt.Chart(mot).mark_bar().encode(
        x=alt.X("評論數:Q"),
        y=alt.Y("動機類型:N", sort="-x"),
        tooltip=["動機類型", "評論數"],
    ).properties(height=360)
    st.altair_chart(chart, use_container_width=True)
    st.info("圖表解讀：評論動機可用來支撐市場區隔，避免只用產品屬性分群。")

    if "Sentiment" in reviews.columns:
        st.subheader("評論情緒分布")
        senti = reviews["Sentiment"].fillna("未分類").value_counts().reset_index()
        senti.columns = ["情緒", "評論數"]
        st.bar_chart(senti.set_index("情緒"))

    st.subheader("ASIN 層級評論摘要")
    if summary.empty:
        st.write("尚未讀到 ASIN 摘要檔。")
    else:
        st.dataframe(summary, use_container_width=True, hide_index=True)


def recommendation_page():
    st.title("個人化推薦查詢")
    rec = load_recommendations()
    rfm = load_rfm()
    if rec.empty:
        st.warning("目前沒有讀到推薦模型資料。")
        return

    customer_ids = sorted(rec["Customer_ID"].dropna().unique().tolist())
    selected = st.selectbox("選擇 Customer_ID", customer_ids)
    one = rec[rec["Customer_ID"] == selected].sort_values("Rank").copy()

    if one.empty:
        st.warning("找不到此顧客的推薦資料。")
        return

    best = one.iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("最佳推薦", f"Product Row {int(best['Product_Row'])}")
    c2.metric("預測購買機率", f"{best['Predicted_Probability']*100:.2f}%")
    c3.metric("推薦品牌", str(best.get("Brand", "未標示")))

    if not rfm.empty and "Customer_ID" in rfm.columns:
        labels = rfm[rfm["Customer_ID"] == selected]
        if not labels.empty:
            row = labels.iloc[0]
            st.info(f"RFM 標籤：{row.get('RFM_Label', '未對接')}｜CAI 標籤：{row.get('CAI_Label', '未對接')}")
        else:
            st.info("此顧客尚未對接 RFM／CAI 標籤。")

    st.subheader("Top 5 推薦商品")
    view = one[["Rank", "Product_Row", "Product_Label", "Brand", "Price", "Color", "Spec", "GPS_Flag", "Predicted_Probability"]].copy()
    view["Predicted_Probability"] = view["Predicted_Probability"] * 100
    view = view.rename(columns={
        "Rank": "排名",
        "Product_Row": "產品編號",
        "Product_Label": "產品組合",
        "Brand": "品牌",
        "Price": "售價",
        "Color": "顏色",
        "Spec": "規格",
        "GPS_Flag": "GPS",
        "Predicted_Probability": "預測購買機率(%)",
    })
    st.dataframe(view, use_container_width=True, hide_index=True)


def strategy_page():
    st.title("策略建議與維護")
    st.markdown(
        f"""
        ## 專案定位
        **PEP with VivaVictors｜Marketing Dashboard** 是一套以 Streamlit 建置的電商行銷分析儀表板，目標是將模型結果轉成廠商可直接理解與使用的決策工具。

        ## 目前已完成
        - 整合 RFM／CAI 顧客標籤
        - 建立產品組合購買率分析
        - 建立顧客 Top 5 個人化推薦查詢
        - 整合 Amazon 評論並分類顧客動機
        - 將靜態 Excel 結果轉為互動式儀表板

        ## 對廠商的價值
        1. 找出值得優先投放廣告或補庫存的商品組合。
        2. 依顧客標籤與推薦結果進行分眾行銷。
        3. 用評論動機補強市場區隔與商品頁文案。
        4. 後續可接入成本、毛利、廣告資料，延伸為 ROI 儀表板。

        ## 後續維護方式
        - 若重新跑模型：更新 `data/{MODEL_FILE}`。
        - 若新增評論：更新 `data/{REVIEWS_FILE}` 與 `data/{REVIEWS_SUMMARY_FILE}`。
        - 若產品組合或 ASIN 改變：更新 `data/{DESIGN_FILE}`。
        - GitHub 更新後，Streamlit Cloud 會重新部署；若沒有自動更新，可到 Manage app 手動 Reboot。

        GitHub 專案：[{REPO_URL}]({REPO_URL})
        """
    )


page = sidebar()
if page == "首頁總覽":
    overview_page()
elif page == "顧客標籤 RFM／CAI":
    segmentation_page()
elif page == "產品組合分析":
    product_page()
elif page == "評論動機分析":
    review_page()
elif page == "個人化推薦查詢":
    recommendation_page()
elif page == "策略建議與維護":
    strategy_page()
