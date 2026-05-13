from pathlib import Path
import re

import pandas as pd
import plotly.express as px
import streamlit as st

APP_TITLE = "PEP with VivaVictors｜Marketing Dashboard"
APP_SUBTITLE = "電商顧客標籤、商品策略、評論洞察與個人化推薦工作台"
DATA_DIR = Path(__file__).parent / "data"

RIDGE_KEY = "ridge_logit_customer_specific_report"
RFM_KEY = "RFM_CAI"
DESIGN_KEY = "正交設計"
REVIEWS_DETAIL_KEY = "reviews_processed_classified.csv"
REVIEWS_SUMMARY_KEY = "reviews_summary_processed.csv"

BRAND_COLS = ["Dolphin Gauges", "Faria", "MOTOR METER RACING", "Speedway Motors", "RACETECH"]
COLOR_MAP = {
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
COLOR_COLS = list(COLOR_MAP.keys())
SPEC_COLS = ["Npt", "Sae,Npt", "Sae"]

st.set_page_config(
    page_title="PEP with VivaVictors",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
.block-container {padding-top: 2rem; padding-bottom: 3rem;}
.vv-hero {
    padding: 1.3rem 1.5rem;
    border-radius: 1.2rem;
    background: linear-gradient(135deg, #0f172a 0%, #1f2937 55%, #334155 100%);
    color: white;
    margin-bottom: 1.2rem;
}
.vv-card {
    padding: 1rem 1.1rem;
    border: 1px solid rgba(148, 163, 184, .35);
    border-radius: 1rem;
    background: rgba(248, 250, 252, .06);
    margin-bottom: .8rem;
}
.vv-note {
    padding: .85rem 1rem;
    border-left: 4px solid #2563eb;
    background: rgba(37, 99, 235, .08);
    border-radius: .6rem;
    margin: .8rem 0;
}
.vv-action {
    padding: .85rem 1rem;
    border-left: 4px solid #16a34a;
    background: rgba(22, 163, 74, .08);
    border-radius: .6rem;
    margin: .8rem 0;
}
.vv-warning {
    padding: .85rem 1rem;
    border-left: 4px solid #f59e0b;
    background: rgba(245, 158, 11, .10);
    border-radius: .6rem;
    margin: .8rem 0;
}
.small-text {font-size: .92rem; opacity: .86;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def file_by_keyword(keyword: str, suffix: str | None = None) -> Path | None:
    if not DATA_DIR.exists():
        return None
    for path in DATA_DIR.iterdir():
        name = path.name
        if keyword in name and (suffix is None or name.endswith(suffix)):
            return path
    return None


def make_unique_columns(df: pd.DataFrame) -> pd.DataFrame:
    counts = {}
    new_cols = []
    for col in df.columns:
        col = str(col)
        if col in counts:
            counts[col] += 1
            new_cols.append(f"{col}_{counts[col]}")
        else:
            counts[col] = 0
            new_cols.append(col)
    df = df.copy()
    df.columns = new_cols
    return df


def to_numeric(series, default=0):
    return pd.to_numeric(series, errors="coerce").fillna(default)


def first_present(row, cols, default="未標示"):
    for col in cols:
        if col in row.index:
            try:
                if pd.notna(row[col]) and float(row[col]) == 1:
                    return COLOR_MAP.get(col, col)
            except Exception:
                if pd.notna(row[col]) and str(row[col]).strip() not in ["", "0", "nan"]:
                    return COLOR_MAP.get(str(row[col]).strip(), str(row[col]).strip())
    return default


def classify_product_strategy(rate: float, review_negative: float | None = None) -> str:
    if pd.isna(rate):
        return "資料不足"
    if rate >= 10:
        return "主力推廣"
    if rate >= 5:
        return "潛力商品"
    if rate < 2:
        return "低效檢討"
    return "穩定觀察"


def product_label(row) -> str:
    row_no = int(row.get("Product_Row", 0)) if pd.notna(row.get("Product_Row", 0)) else 0
    brand = row.get("Brand", "未標示")
    price = row.get("Price", "-")
    color = row.get("Color", "-")
    spec = row.get("Spec", "-")
    gps = "GPS" if int(row.get("GPS_Flag", 0) or 0) == 1 else "無GPS"
    return f"#{row_no}｜{brand}｜${price}｜{color}｜{spec}｜{gps}"


@st.cache_data(show_spinner=False)
def load_product_summary() -> pd.DataFrame:
    ridge_path = file_by_keyword(RIDGE_KEY, ".xlsx")
    if ridge_path is None:
        st.error("找不到模型輸出檔：ridge_logit_customer_specific_report_*.xlsx。請確認檔案已放在 data/ 資料夾。")
        return pd.DataFrame()

    df = pd.read_excel(ridge_path, sheet_name="Product_Summary")
    df = make_unique_columns(df)
    df["Product_Row"] = to_numeric(df.get("Product_Row"), 0).astype(int)
    df["Price"] = to_numeric(df.get("price", df.get("Price", 0)), 0)
    df["Actual_Purchase_Rate"] = to_numeric(df.get("Actual_Purchase_Rate"), 0)
    df["Mean_Predicted_Probability"] = to_numeric(df.get("Mean_Predicted_Probability"), 0)
    df["Actual_Purchase_Count"] = to_numeric(df.get("Actual_Purchase_Count"), 0).astype(int)
    df["N_Customers"] = to_numeric(df.get("N_Customers"), 0).astype(int)
    df["GPS_Flag"] = to_numeric(df.get("GPS", 0), 0).astype(int)

    # Derive attributes from dummy columns as fallback.
    df["Brand"] = df.apply(lambda r: first_present(r, BRAND_COLS), axis=1)
    df["Color"] = df.apply(lambda r: first_present(r, COLOR_COLS), axis=1)
    df["Spec"] = df.apply(lambda r: first_present(r, SPEC_COLS, default="Sae"), axis=1)
    df["ASIN"] = ""

    design_path = file_by_keyword(DESIGN_KEY, ".xlsx")
    if design_path is not None:
        design = pd.read_excel(design_path)
        design = make_unique_columns(design)
        design = design.reset_index(drop=True).copy()
        design["Product_Row"] = range(1, len(design) + 1)
        rename_map = {
            "組合_品牌": "Design_Brand",
            "組合_原價(轉換後)": "Design_Price",
            "組合_錶盤顏色": "Design_Color",
            "組合_螺紋類型": "Design_Spec",
            "組合_GPS天線": "Design_GPS_Flag",
            "對應 ASIN": "Design_ASIN",
        }
        design = design.rename(columns=rename_map)
        keep_cols = ["Product_Row", "Design_Brand", "Design_Price", "Design_Color", "Design_Spec", "Design_GPS_Flag", "Design_ASIN"]
        design = design[[c for c in keep_cols if c in design.columns]]
        df = df.merge(design, on="Product_Row", how="left", suffixes=("", "_design"))
        for base, design_col in [
            ("Brand", "Design_Brand"),
            ("Price", "Design_Price"),
            ("Color", "Design_Color"),
            ("Spec", "Design_Spec"),
            ("GPS_Flag", "Design_GPS_Flag"),
            ("ASIN", "Design_ASIN"),
        ]:
            if design_col in df.columns:
                df[base] = df[design_col].combine_first(df[base])

    df["GPS_Flag"] = to_numeric(df["GPS_Flag"], 0).astype(int)
    df["GPS"] = df["GPS_Flag"].map({1: "有GPS", 0: "無GPS"})
    df["Price"] = to_numeric(df["Price"], 0)
    df["Product_Label"] = df.apply(product_label, axis=1)
    df["Strategy_Tag"] = df["Actual_Purchase_Rate"].apply(classify_product_strategy)
    return make_unique_columns(df)


@st.cache_data(show_spinner=False)
def load_recommendations() -> pd.DataFrame:
    ridge_path = file_by_keyword(RIDGE_KEY, ".xlsx")
    if ridge_path is None:
        return pd.DataFrame()
    try:
        df = pd.read_excel(ridge_path, sheet_name="Recommendation_Top5")
    except Exception:
        return pd.DataFrame()
    df = make_unique_columns(df)
    df["Customer_ID"] = df.get("Customer_ID", "").astype(str)
    df["Product_Row"] = to_numeric(df.get("Product_Row"), 0).astype(int)
    df["Predicted_Probability"] = to_numeric(df.get("Predicted_Probability"), 0)
    if df["Predicted_Probability"].max() > 1.5:
        df["Predicted_Probability"] = df["Predicted_Probability"] / 100
    return df


@st.cache_data(show_spinner=False)
def load_rfm() -> pd.DataFrame:
    rfm_path = file_by_keyword(RFM_KEY, ".xlsx")
    if rfm_path is None:
        return pd.DataFrame()
    try:
        rfm = pd.read_excel(rfm_path, sheet_name="RFM")
    except Exception:
        rfm = pd.DataFrame()
    try:
        cai = pd.read_excel(rfm_path, sheet_name="CAI")
    except Exception:
        cai = pd.DataFrame()

    if not rfm.empty:
        rfm = make_unique_columns(rfm)
        if "Customer_ID" not in rfm.columns:
            possible = [c for c in rfm.columns if "顧客" in c or "Customer" in c]
            if possible:
                rfm = rfm.rename(columns={possible[0]: "Customer_ID"})
        rfm["Customer_ID"] = rfm["Customer_ID"].astype(str)
        if "Segment_Name" in rfm.columns:
            rfm["RFM_Label"] = rfm["Segment_Name"].astype(str)
        elif "RFM_Label" not in rfm.columns:
            rfm["RFM_Label"] = "未標示"
    if not cai.empty:
        cai = make_unique_columns(cai)
        if "顧客編號" in cai.columns:
            cai = cai.rename(columns={"顧客編號": "Customer_ID"})
        if "顧客分群" in cai.columns:
            cai = cai.rename(columns={"顧客分群": "CAI_Label"})
        cai["Customer_ID"] = cai["Customer_ID"].astype(str)
        cai = cai[[c for c in ["Customer_ID", "CAI", "CAI_Label"] if c in cai.columns]]
    if rfm.empty and cai.empty:
        return pd.DataFrame()
    if rfm.empty:
        result = cai
    elif cai.empty:
        result = rfm
        result["CAI_Label"] = "未對接"
    else:
        result = rfm.merge(cai, on="Customer_ID", how="left")
        result["CAI_Label"] = result.get("CAI_Label", "未對接").fillna("未對接")
    return result


@st.cache_data(show_spinner=False)
def load_reviews_detail() -> pd.DataFrame:
    path = DATA_DIR / REVIEWS_DETAIL_KEY
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, encoding="utf-8-sig")
    df = make_unique_columns(df)
    df["Rating"] = to_numeric(df.get("Rating"), 0)
    if "Sentiment_Label" not in df.columns:
        df["Sentiment_Label"] = df["Rating"].apply(lambda x: "正向" if x >= 4 else ("負向" if x <= 2 else "中立"))
    if "Motivation_Type" not in df.columns:
        df["Motivation_Type"] = "其他"
    if "Review_Text" not in df.columns:
        content_col = "Review_Content" if "Review_Content" in df.columns else None
        df["Review_Text"] = df[content_col] if content_col else ""
    df["ASIN"] = df.get("ASIN", "").astype(str)
    return df


@st.cache_data(show_spinner=False)
def load_reviews_summary() -> pd.DataFrame:
    path = DATA_DIR / REVIEWS_SUMMARY_KEY
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, encoding="utf-8-sig")
    df = make_unique_columns(df)
    for col in ["Review_Count", "Avg_Rating", "Positive_Count", "Negative_Count", "Neutral_Count"]:
        if col in df.columns:
            df[col] = to_numeric(df[col], 0)
    return df


def kpi(label, value, help_text=""):
    st.metric(label, value, help=help_text if help_text else None)


def render_header():
    st.markdown(
        f"""
        <div class="vv-hero">
            <h1 style="margin:0; font-size:2.2rem;">{APP_TITLE}</h1>
            <p style="margin:.35rem 0 0 0; opacity:.88; font-size:1.05rem;">{APP_SUBTITLE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def overview_page():
    render_header()
    st.header("首頁總覽與操作手冊")
    products = load_product_summary()
    recs = load_recommendations()
    reviews = load_reviews_detail()

    total_customers = recs["Customer_ID"].nunique() if not recs.empty else 0
    total_products = products["Product_Row"].nunique() if not products.empty else 0
    purchases = int(products["Actual_Purchase_Count"].sum()) if not products.empty else 0
    exposure = int(products["N_Customers"].sum()) if not products.empty else 0
    purchase_rate = purchases / exposure * 100 if exposure else 0
    review_count = len(reviews)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("顧客數", f"{total_customers:,}")
    c2.metric("產品組合", f"{total_products:,}")
    c3.metric("購買筆數", f"{purchases:,}")
    c4.metric("整體購買率", f"{purchase_rate:.2f}%")
    c5.metric("評論數", f"{review_count:,}")

    if not products.empty:
        top = products.sort_values("Actual_Purchase_Rate", ascending=False).iloc[0]
        st.markdown(
            f"""
            <div class="vv-action">
            <b>本週優先觀察商品：</b>{top['Product_Label']}<br>
            實際購買率為 <b>{top['Actual_Purchase_Rate']:.2f}%</b>，可作為主推商品、廣告素材與商品頁優化的優先對象。
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("廠商日常使用方式")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("""
        <div class="vv-card"><b>1. 先看商品策略</b><br>
        判斷哪些商品適合主推、哪些需要檢討，並查看購買率與推薦強度。</div>
        """, unsafe_allow_html=True)
    with col_b:
        st.markdown("""
        <div class="vv-card"><b>2. 再做效益試算</b><br>
        輸入曝光人數、廣告成本與假設毛利率，估算營收、毛利與回收狀況。</div>
        """, unsafe_allow_html=True)
    with col_c:
        st.markdown("""
        <div class="vv-card"><b>3. 最後查顧客推薦</b><br>
        用 Customer_ID 查詢 Top 5 商品，作為 EDM、再行銷或客服推薦依據。</div>
        """, unsafe_allow_html=True)

    st.subheader("購買率最高的產品組合")
    if not products.empty:
        chart_df = products.sort_values("Actual_Purchase_Rate", ascending=False).head(10).copy()
        fig = px.bar(
            chart_df,
            x="Actual_Purchase_Rate",
            y="Product_Label",
            orientation="h",
            color="Strategy_Tag",
            text=chart_df["Actual_Purchase_Rate"].map(lambda x: f"{x:.2f}%"),
            labels={"Actual_Purchase_Rate": "購買率(%)", "Product_Label": "產品組合"},
            title="Top 10 商品組合購買率",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=520)
        st.plotly_chart(fig, width="stretch")
    with st.expander("操作手冊：這個儀表板如何配合報告使用？", expanded=True):
        st.markdown("""
        - **商品策略頁**：放入報告的「最適產品組合分析」與「商品主推策略」。
        - **效益試算頁**：放入報告的「效益示範」，但因目前沒有真實成本，採毛利率假設試算。
        - **顧客推薦頁**：放入報告的「個人化行銷應用」，顯示不同顧客的 Top 5 推薦。
        - **評論洞察頁**：放入報告的「顧客動機市場區隔」，用評論動機替代單純產品特性分群。
        - **維護方式**：後續只要更新 `data/` 裡的 Excel 或 CSV，重新部署後即可更新儀表板。
        """)


def product_strategy_page():
    st.header("商品策略工作台")
    products = load_product_summary()
    if products.empty:
        st.info("目前找不到產品分析資料。")
        return

    st.markdown("本頁提供廠商日常判斷商品主推順序的依據。可依品牌、顏色、規格與 GPS 篩選，快速找出高潛力商品組合。")
    col1, col2, col3, col4 = st.columns(4)
    brand = col1.selectbox("品牌", ["全部"] + sorted(products["Brand"].dropna().unique().tolist()))
    color = col2.selectbox("顏色", ["全部"] + sorted(products["Color"].dropna().unique().tolist()))
    spec = col3.selectbox("規格", ["全部"] + sorted(products["Spec"].dropna().unique().tolist()))
    gps = col4.selectbox("GPS", ["全部"] + sorted(products["GPS"].dropna().unique().tolist()))

    df = products.copy()
    if brand != "全部":
        df = df[df["Brand"] == brand]
    if color != "全部":
        df = df[df["Color"] == color]
    if spec != "全部":
        df = df[df["Spec"] == spec]
    if gps != "全部":
        df = df[df["GPS"] == gps]

    st.subheader("商品策略清單")
    view = df.sort_values("Actual_Purchase_Rate", ascending=False)[[
        "Product_Row", "Product_Label", "Strategy_Tag", "Actual_Purchase_Rate", "Mean_Predicted_Probability", "Actual_Purchase_Count", "ASIN"
    ]].copy()
    view["Actual_Purchase_Rate"] = view["Actual_Purchase_Rate"].map(lambda x: f"{x:.2f}%")
    view["Mean_Predicted_Probability"] = view["Mean_Predicted_Probability"].map(lambda x: f"{x:.2f}%")
    st.dataframe(view, width="stretch", hide_index=True)

    fig = px.scatter(
        df,
        x="Mean_Predicted_Probability",
        y="Actual_Purchase_Rate",
        size="Actual_Purchase_Count",
        color="Strategy_Tag",
        hover_name="Product_Label",
        labels={"Mean_Predicted_Probability": "平均預測購買機率(%)", "Actual_Purchase_Rate": "實際購買率(%)"},
        title="商品潛力矩陣：實際購買率 × 模型預測機率",
    )
    st.plotly_chart(fig, width="stretch")

    st.markdown("""
    <div class="vv-note"><b>判讀方式：</b>右上方商品代表實際表現與模型預測都較高，適合優先主推；左下方商品需檢查商品頁、價格、圖片或規格說明。</div>
    """, unsafe_allow_html=True)


def impact_simulator_page():
    st.header("效益示範：曝光、營收與毛利試算")
    products = load_product_summary()
    if products.empty:
        st.info("目前找不到產品分析資料。")
        return

    st.markdown("本頁讓廠商快速試算：若把某個商品組合投入廣告或 EDM 曝光，可能帶來多少購買數、營收與毛利。因目前沒有真實成本，毛利採假設值，不宣稱為實際 ROI。")

    product_options = products.sort_values("Actual_Purchase_Rate", ascending=False)["Product_Label"].tolist()
    selected_label = st.selectbox("選擇要試算的商品組合", product_options)
    product = products[products["Product_Label"] == selected_label].iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    exposure = col1.number_input("預計曝光人數", min_value=100, max_value=100000, value=10000, step=500)
    ad_cost = col2.number_input("廣告／推廣成本", min_value=0, max_value=1000000, value=10000, step=1000)
    margin_rate = col3.slider("假設毛利率", min_value=5, max_value=80, value=30, step=5) / 100
    rate_adjust = col4.slider("轉換率調整係數", min_value=0.2, max_value=2.0, value=1.0, step=0.1)

    base_rate = float(product["Actual_Purchase_Rate"]) / 100
    est_rate = base_rate * rate_adjust
    est_orders = exposure * est_rate
    revenue = est_orders * float(product["Price"])
    gross_profit = revenue * margin_rate
    net_profit = gross_profit - ad_cost
    roas = revenue / ad_cost if ad_cost > 0 else None

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("試算轉換率", f"{est_rate*100:.2f}%")
    k2.metric("預估購買數", f"{est_orders:,.0f}")
    k3.metric("預估營收", f"${revenue:,.0f}")
    k4.metric("預估毛利", f"${gross_profit:,.0f}")
    k5.metric("扣廣告後", f"${net_profit:,.0f}")

    if roas is not None:
        st.markdown(f"<div class='vv-action'><b>ROAS 試算：</b>{roas:.2f}。若大於 1，代表每 1 元廣告成本可帶來超過 1 元營收；但仍需搭配實際成本確認利潤。</div>", unsafe_allow_html=True)

    st.subheader("Top 5 商品同曝光情境比較")
    scenario = products.sort_values("Actual_Purchase_Rate", ascending=False).head(5).copy()
    scenario["預估購買數"] = exposure * (scenario["Actual_Purchase_Rate"] / 100) * rate_adjust
    scenario["預估營收"] = scenario["預估購買數"] * scenario["Price"]
    scenario["預估毛利"] = scenario["預估營收"] * margin_rate
    fig = px.bar(
        scenario,
        x="Product_Label",
        y="預估營收",
        color="Strategy_Tag",
        title="同樣曝光下，不同商品組合的營收試算",
        labels={"Product_Label": "產品組合"},
    )
    fig.update_layout(xaxis_tickangle=-25, height=520)
    st.plotly_chart(fig, width="stretch")
    st.dataframe(scenario[["Product_Label", "Actual_Purchase_Rate", "Price", "預估購買數", "預估營收", "預估毛利"]], width="stretch", hide_index=True)


def recommendation_page():
    st.header("顧客個人化推薦")
    recs = load_recommendations()
    products = load_product_summary()
    rfm = load_rfm()
    if recs.empty:
        st.info("目前找不到 Recommendation_Top5 資料。")
        return
    customer_ids = sorted(recs["Customer_ID"].dropna().astype(str).unique().tolist())
    query = st.text_input("快速搜尋 Customer_ID", "")
    filtered = [c for c in customer_ids if query.lower() in c.lower()] if query else customer_ids
    selected = st.selectbox("選擇顧客", filtered[:1000])
    cust = recs[recs["Customer_ID"] == selected].copy()
    cust = cust.merge(products[["Product_Row", "Product_Label", "Brand", "Price", "Color", "Spec", "GPS", "Strategy_Tag"]], on="Product_Row", how="left")
    cust = cust.sort_values("Predicted_Probability", ascending=False)
    best = cust.iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("最佳推薦", best["Product_Label"])
    c2.metric("預測購買機率", f"{best['Predicted_Probability']*100:.2f}%")
    if not rfm.empty and selected in set(rfm["Customer_ID"].astype(str)):
        seg = rfm[rfm["Customer_ID"].astype(str) == selected].iloc[0]
        c3.metric("RFM 分群", str(seg.get("RFM_Label", "未標示"))[:18])
    else:
        c3.metric("RFM 分群", "未對接")

    display = cust[["Product_Row", "Product_Label", "Predicted_Probability", "Strategy_Tag"]].copy()
    display["Predicted_Probability"] = display["Predicted_Probability"].map(lambda x: f"{x*100:.2f}%")
    st.dataframe(display, width="stretch", hide_index=True)

    st.subheader("可直接使用的行銷訊息草稿")
    message = f"推薦您查看 {best['Brand']} 的 {best['Color']} {best['Spec']} 款式。此組合符合您過去偏好的商品特徵，並且在整體資料中屬於「{best['Strategy_Tag']}」商品，適合作為優先推薦選項。"
    st.text_area("訊息草稿", message, height=120)
    st.markdown("""
    <div class="vv-note"><b>使用方式：</b>此訊息可作為 EDM、客服推薦、再行銷廣告受眾或商品頁個人化區塊的初稿。</div>
    """, unsafe_allow_html=True)


def customer_segmentation_page():
    st.header("顧客分群與名單管理")
    rfm = load_rfm()
    if rfm.empty:
        st.info("目前找不到 RFM／CAI 資料。")
        return
    st.subheader("RFM 分群分布")
    counts = rfm["RFM_Label"].value_counts().reset_index()
    counts.columns = ["RFM_Label", "Customer_Count"]
    fig = px.bar(counts, x="Customer_Count", y="RFM_Label", orientation="h", title="顧客價值分群人數")
    fig.update_layout(height=520, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, width="stretch")
    selected = st.selectbox("選擇分群查看名單", counts["RFM_Label"].tolist())
    seg = rfm[rfm["RFM_Label"] == selected].copy()
    st.dataframe(seg.head(200), width="stretch", hide_index=True)
    st.markdown("""
    <div class="vv-action"><b>行銷應用：</b>高價值或活躍顧客適合新品預告、組合優惠與會員維繫；沉睡或待喚回顧客可用折扣、免運或規格指南降低回購門檻。</div>
    """, unsafe_allow_html=True)


def review_insights_page():
    st.header("評論洞察與顧客動機")
    reviews = load_reviews_detail()
    summary = load_reviews_summary()
    if reviews.empty:
        st.info("目前找不到評論資料。")
        return
    avg_rating = reviews["Rating"].mean()
    positive_rate = (reviews["Sentiment_Label"].astype(str).str.contains("正|Positive", regex=True).mean() * 100)
    top_mot = reviews["Motivation_Type"].mode().iloc[0] if not reviews["Motivation_Type"].mode().empty else "其他"
    c1, c2, c3 = st.columns(3)
    c1.metric("平均評分", f"{avg_rating:.2f}")
    c2.metric("正向評論占比", f"{positive_rate:.1f}%")
    c3.metric("主要動機", top_mot)

    mot = reviews["Motivation_Type"].value_counts().reset_index()
    mot.columns = ["Motivation_Type", "Review_Count"]
    fig = px.bar(mot, x="Review_Count", y="Motivation_Type", orientation="h", title="評論動機分布")
    fig.update_layout(height=420, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, width="stretch")

    sentiment = reviews["Sentiment_Label"].value_counts().reset_index()
    sentiment.columns = ["Sentiment", "Count"]
    fig2 = px.pie(sentiment, names="Sentiment", values="Count", title="評論情緒分布")
    st.plotly_chart(fig2, width="stretch")

    st.subheader("ASIN 商品評論摘要")
    if not summary.empty:
        st.dataframe(summary.sort_values("Review_Count", ascending=False), width="stretch", hide_index=True)
    st.subheader("低分評論範例：可作為商品頁或客服改善方向")
    neg = reviews[reviews["Rating"] <= 2].copy()
    cols = [c for c in ["ASIN", "Rating", "Motivation_Type", "Review_Text"] if c in neg.columns]
    st.dataframe(neg[cols].head(20), width="stretch", hide_index=True)


def positioning_page():
    st.header("市場定位與維護工作台")
    st.subheader("建議定位")
    st.markdown("""
    <div class="vv-card">
    <b>PEP with VivaVictors 的建議定位：</b><br>
    針對重視規格適配、功能可靠與購買風險降低的 B2C 顧客，提供清楚產品資訊、評論佐證與個人化推薦，協助廠商提升商品轉換效率與再行銷精準度。
    </div>
    """, unsafe_allow_html=True)
    st.subheader("STP 與行動建議")
    strategy_df = pd.DataFrame([
        ["規格適配型", "在意 Npt / Sae 是否買對", "商品頁加上規格對照表、安裝說明、FAQ"],
        ["功能需求型", "重視準確度、可用性與穩定", "廣告主打功能、使用情境與正向評論"],
        ["品質信任型", "在意耐用、品牌與負評風險", "強化保固、評價、實測與客服承諾"],
        ["外觀偏好型", "重視顏色、風格與車款搭配", "加強商品圖片、情境照與顏色比較"],
        ["價格敏感型", "在意折扣與 CP 值", "推組合價、限時折扣、免運或回購券"],
    ], columns=["目標族群", "主要需求", "建議行動"])
    st.dataframe(strategy_df, width="stretch", hide_index=True)
    st.subheader("後續維護")
    st.markdown("""
    - 更新推薦模型：重新上傳 `ridge_logit_customer_specific_report_*.xlsx`。
    - 更新評論：重新整理 `reviews_processed_classified.csv` 與 `reviews_summary_processed.csv`。
    - 更新產品：替換 `正交設計_產品組合.xlsx`。
    - 若取得成本資料，可將效益試算從「營收／毛利假設」升級為「實際利潤與 ROI」。
    """)


pages = {
    "首頁｜總覽與操作手冊": overview_page,
    "商品策略｜主推與檢討清單": product_strategy_page,
    "效益試算｜曝光與營收模擬": impact_simulator_page,
    "顧客推薦｜一對一行銷": recommendation_page,
    "顧客分群｜RFM/CAI 名單": customer_segmentation_page,
    "評論洞察｜動機與痛點": review_insights_page,
    "市場定位｜行動與維護": positioning_page,
}

with st.sidebar:
    st.title("VivaVictors")
    st.caption("Marketing Dashboard")
    selected_page = st.radio("選擇功能", list(pages.keys()))
    st.divider()
    st.caption("資料來源：購買模型、RFM／CAI、產品組合、Amazon 評論")

pages[selected_page]()
