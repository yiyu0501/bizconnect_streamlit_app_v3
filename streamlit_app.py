from pathlib import Path
import re
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

APP_TITLE = "PEP with VivaVictors｜Marketing Dashboard"
APP_SUBTITLE = "技銓跨境電商：市場區隔、目標市場、產品定位、商品推廣與一對一行銷工作台"
DATA_DIR = Path(__file__).parent / "data"

RIDGE_KEY = "ridge_logit_customer_specific_report"
RFM_KEY = "RFM_CAI"
DESIGN_KEY = "正交設計"
KMEANS_KEY = "KMeans_Full_1024_Result"
REVIEWS_DETAIL_KEY = "reviews_processed_classified.csv"
REVIEWS_SUMMARY_KEY = "reviews_summary_processed.csv"

BRAND_COLS = ["Dolphin Gauges", "Faria", "MOTOR METER RACING", "Speedway Motors", "RACETECH"]
COLOR_MAP = {
    "orange": "橘色", "white": "白色", "beige": "米色", "green": "綠色", "blue": "藍色", "yellow": "黃色", "black": "黑色",
    "紅色": "紅色", "白色": "白色", "黑色": "黑色", "米色": "米色", "橘色": "橘色", "綠色": "綠色", "藍色": "藍色", "黃色": "黃色",
}
COLOR_COLS = list(COLOR_MAP.keys())
SPEC_COLS = ["Npt", "Sae,Npt", "Sae"]

CLUSTER_LABELS = {
    1: "極限性能與規格導向群",
    2: "主流穩健實用群",
    3: "個人風格與美學鑑賞群",
    0: "性能規格導向群",
}

CLUSTER_EN = {
    1: "Performance & Spec Specialists",
    2: "Mainstream Pragmatic Buyers",
    3: "Individual Style & Aesthetic Buyers",
    0: "Performance & Spec Specialists",
}

CLUSTER_NEEDS = {
    "極限性能與規格導向群": "重視 Racing 感、Npt 規格、安裝精準度與專業感。",
    "主流穩健實用群": "重視降低買錯風險、價格合理、基本規格清楚與穩定可用。",
    "個人風格與美學鑑賞群": "重視米色、藍色等特殊色系與車內風格搭配，對差異化外觀與美感較敏感。",
    "性能規格導向群": "重視 Racing 感、Npt 規格、安裝精準度與專業感。",
    "未分群": "資料不足，建議先以整體 Top 商品與商品頁教育內容觸達。",
    "極端值／人工檢查": "偏好值明顯偏離多數顧客，建議人工檢查後再設計特殊行銷。",
}

CLUSTER_ACTIONS = {
    "極限性能與規格導向群": "主推 MOTOR METER RACING、Npt、黑色/橘色等競技風格商品；廣告訊息強調 precision、racing style、fitment confirmed。",
    "主流穩健實用群": "主推高購買率與高評價商品；商品頁強化規格表、安裝確認清單、CP 值與常見問題。",
    "個人風格與美學鑑賞群": "主推米色、藍色與可搭配內裝的視覺款式；素材強調實裝照片、顏色比較與風格搭配。",
    "性能規格導向群": "主推 MOTOR METER RACING、Npt、黑色/橘色等競技風格商品；廣告訊息強調 precision、racing style、fitment confirmed。",
    "未分群": "先以整體主推商品與規格教育內容觸達，並透過點擊/購買行為補足偏好資料。",
    "極端值／人工檢查": "不直接大量投放，先檢查購買紀錄與推薦結果，再做小規模測試。",
}

RFM_STRATEGY = {
    "高價值": ["維持回購", "新品預告、會員專屬優惠、高評價款推薦", "EDM / 再行銷名單 / 會員訊息"],
    "潛力": ["促成轉換", "規格指南、Top 商品比較、限時優惠", "Amazon 商品頁 / EDM / 搜尋廣告"],
    "沉睡": ["喚回互動", "回購券、熱門商品、免運門檻", "再行銷廣告 / 折扣訊息"],
    "低活躍": ["降低嘗試門檻", "入門款、FAQ、規格確認工具", "商品頁教育內容 / 廣告素材"],
}

st.set_page_config(page_title="PEP with VivaVictors", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

CUSTOM_CSS = """
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1280px;}
.vv-hero {padding: 1.35rem 1.5rem; border-radius: 1.2rem; background: linear-gradient(135deg, #0f172a 0%, #1f2937 55%, #334155 100%); color: white; margin-bottom: 1rem;}
.vv-card {padding: 1rem 1.1rem; border: 1px solid rgba(148, 163, 184, .35); border-radius: 1rem; background: rgba(148,163,184,.08); margin-bottom: .8rem;}
.vv-note {padding: .85rem 1rem; border-left: 4px solid #2563eb; background: rgba(37, 99, 235, .08); border-radius: .6rem; margin: .8rem 0;}
.vv-action {padding: .85rem 1rem; border-left: 4px solid #16a34a; background: rgba(22, 163, 74, .08); border-radius: .6rem; margin: .8rem 0;}
.vv-warning {padding: .85rem 1rem; border-left: 4px solid #f59e0b; background: rgba(245, 158, 11, .10); border-radius: .6rem; margin: .8rem 0;}
.vv-danger {padding: .85rem 1rem; border-left: 4px solid #dc2626; background: rgba(220, 38, 38, .08); border-radius: .6rem; margin: .8rem 0;}
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
    out = df.copy()
    out.columns = new_cols
    return out


def to_numeric(series, default=0):
    return pd.to_numeric(series, errors="coerce").fillna(default)


def present_dummy(row, cols, default="未標示"):
    for col in cols:
        if col in row.index:
            try:
                if pd.notna(row[col]) and float(row[col]) == 1:
                    return COLOR_MAP.get(col, col)
            except Exception:
                if pd.notna(row[col]) and str(row[col]).strip() not in ["", "0", "nan", "None"]:
                    return COLOR_MAP.get(str(row[col]).strip(), str(row[col]).strip())
    return default


def product_strategy_tag(rate: float) -> str:
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
    price = int(row.get("Price", 0)) if pd.notna(row.get("Price", 0)) else "-"
    color = row.get("Color", "-")
    spec = row.get("Spec", "-")
    gps = row.get("GPS", "無GPS")
    return f"#{row_no}｜{brand}｜${price}｜{color}｜{spec}｜{gps}"


def cluster_label_value(x):
    if pd.isna(x):
        return "未分群"
    if str(x).lower().startswith("outlier"):
        return "極端值／人工檢查"
    try:
        return CLUSTER_LABELS.get(int(float(x)), f"Cluster {int(float(x))}")
    except Exception:
        return str(x)


def cluster_action(label):
    return CLUSTER_ACTIONS.get(label, "先以主力商品與教育內容觸達，再累積行為資料。")


def render_header():
    st.markdown(
        f"""
        <div class="vv-hero">
            <h1 style="margin:0; font-size:2.15rem;">{APP_TITLE}</h1>
            <p style="margin:.35rem 0 0 0; opacity:.88; font-size:1.05rem;">{APP_SUBTITLE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_product_summary() -> pd.DataFrame:
    ridge_path = file_by_keyword(RIDGE_KEY, ".xlsx")
    if ridge_path is None:
        return pd.DataFrame()
    try:
        df = pd.read_excel(ridge_path, sheet_name="Product_Summary")
    except Exception:
        return pd.DataFrame()
    df = make_unique_columns(df)
    df["Product_Row"] = to_numeric(df.get("Product_Row"), 0).astype(int)
    df["Price"] = to_numeric(df.get("price", df.get("Price", 0)), 0)
    df["Actual_Purchase_Rate"] = to_numeric(df.get("Actual_Purchase_Rate"), 0)
    df["Mean_Predicted_Probability"] = to_numeric(df.get("Mean_Predicted_Probability"), 0)
    df["Actual_Purchase_Count"] = to_numeric(df.get("Actual_Purchase_Count"), 0).astype(int)
    df["N_Customers"] = to_numeric(df.get("N_Customers"), 0).astype(int)
    df["GPS_Flag"] = to_numeric(df.get("GPS", 0), 0).astype(int)
    df["Brand"] = df.apply(lambda r: present_dummy(r, BRAND_COLS), axis=1)
    df["Color"] = df.apply(lambda r: present_dummy(r, COLOR_COLS), axis=1)
    df["Spec"] = df.apply(lambda r: present_dummy(r, SPEC_COLS, default="Sae"), axis=1)
    df["ASIN"] = ""

    design_path = file_by_keyword(DESIGN_KEY, ".xlsx")
    if design_path is not None:
        try:
            design = pd.read_excel(design_path)
            design = make_unique_columns(design).reset_index(drop=True)
            design["Product_Row"] = range(1, len(design) + 1)
            design = design.rename(columns={
                "組合_品牌": "Design_Brand",
                "組合_原價(轉換後)": "Design_Price",
                "組合_錶盤顏色": "Design_Color",
                "組合_螺紋類型": "Design_Spec",
                "組合_GPS天線": "Design_GPS_Flag",
                "對應 ASIN": "Design_ASIN",
            })
            keep_cols = ["Product_Row", "Design_Brand", "Design_Price", "Design_Color", "Design_Spec", "Design_GPS_Flag", "Design_ASIN"]
            design = design[[c for c in keep_cols if c in design.columns]]
            df = df.merge(design, on="Product_Row", how="left")
            for base, design_col in [
                ("Brand", "Design_Brand"), ("Price", "Design_Price"), ("Color", "Design_Color"),
                ("Spec", "Design_Spec"), ("GPS_Flag", "Design_GPS_Flag"), ("ASIN", "Design_ASIN"),
            ]:
                if design_col in df.columns:
                    df[base] = df[design_col].combine_first(df[base])
        except Exception:
            pass
    df["GPS_Flag"] = to_numeric(df["GPS_Flag"], 0).astype(int)
    df["GPS"] = df["GPS_Flag"].map({1: "有GPS", 0: "無GPS"}).fillna("無GPS")
    df["Price"] = to_numeric(df["Price"], 0)
    df["Product_Label"] = df.apply(product_label, axis=1)
    df["Strategy_Tag"] = df["Actual_Purchase_Rate"].apply(product_strategy_tag)
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
def load_customer_code_map() -> pd.DataFrame:
    ridge_path = file_by_keyword(RIDGE_KEY, ".xlsx")
    if ridge_path is None:
        return pd.DataFrame(columns=["Customer_Display", "Customer_ID"])
    try:
        coef = pd.read_excel(ridge_path, sheet_name="Personal_Coefficients", usecols=["Customer_ID", "Variable_Full"])
    except Exception:
        return pd.DataFrame(columns=["Customer_Display", "Customer_ID"])
    coef = coef[coef["Variable_Full"].astype(str).str.contains("__Intercept", na=False)].copy()
    coef["CID_Code"] = coef["Variable_Full"].astype(str).str.extract(r"(CID\d+)__")
    coef["Customer_Display"] = coef["CID_Code"].str.replace("CID", "C", regex=False)
    return coef[["Customer_Display", "Customer_ID"]].drop_duplicates()


@st.cache_data(show_spinner=False)
def load_kmeans() -> tuple[pd.DataFrame, pd.DataFrame]:
    path = file_by_keyword(KMEANS_KEY, ".xlsx")
    if path is None:
        return pd.DataFrame(), pd.DataFrame()
    try:
        customers = pd.read_excel(path, sheet_name="All_Customers_Clustered")
        summary = pd.read_excel(path, sheet_name="Cluster_Summary")
    except Exception:
        return pd.DataFrame(), pd.DataFrame()
    customers = make_unique_columns(customers)
    summary = make_unique_columns(summary)
    if "Customer_Display" in customers.columns:
        customers["Customer_Display"] = customers["Customer_Display"].astype(str)
    if "Cluster" in customers.columns:
        customers["Cluster_Label"] = customers["Cluster"].apply(cluster_label_value)
        customers["Cluster_Action"] = customers["Cluster_Label"].apply(cluster_action)
    if "Cluster" in summary.columns:
        summary["Cluster_Label"] = summary["Cluster"].apply(cluster_label_value)
        summary["Cluster_Action"] = summary["Cluster_Label"].apply(cluster_action)
        summary["Cluster_EN"] = summary["Cluster"].apply(lambda x: CLUSTER_EN.get(int(x), "") if str(x).replace('.', '', 1).isdigit() else "")
    code_map = load_customer_code_map()
    if not code_map.empty and "Customer_Display" in customers.columns:
        customers = customers.merge(code_map, on="Customer_Display", how="left")
    return customers, summary


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
            possible = [c for c in rfm.columns if "顧客" in str(c) or "Customer" in str(c)]
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
        if "Customer_ID" in cai.columns:
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
        if "Sentiment" in df.columns:
            df["Sentiment_Label"] = df["Sentiment"].replace({"Positive": "正向", "Neutral": "中立", "Negative": "負向"})
        else:
            df["Sentiment_Label"] = df["Rating"].apply(lambda x: "正向" if x >= 4 else ("負向" if x <= 2 else "中立"))
    else:
        df["Sentiment_Label"] = df["Sentiment_Label"].replace({"Positive": "正向", "Neutral": "中立", "Negative": "負向"})
    if "Motivation_Type" not in df.columns:
        df["Motivation_Type"] = "未明確判讀"
    df["Motivation_Type"] = df["Motivation_Type"].replace({"其他": "未明確判讀", "功能需求": "功能可靠需求"})
    if "Review_Text" not in df.columns:
        content_col = "Review_Content" if "Review_Content" in df.columns else ("內容" if "內容" in df.columns else None)
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
    if "Main_Motivation" in df.columns:
        df["Main_Motivation"] = df["Main_Motivation"].replace({"其他": "未明確判讀", "功能需求": "功能可靠需求"})
    return df


def metric_row(items):
    cols = st.columns(len(items))
    for col, (label, value, help_text) in zip(cols, items):
        col.metric(label, value, help=help_text if help_text else None)


def overview_page():
    render_header()
    st.header("首頁｜總覽與操作手冊")
    products = load_product_summary()
    recs = load_recommendations()
    reviews = load_reviews_detail()
    k_customers, k_summary = load_kmeans()

    total_customers = recs["Customer_ID"].nunique() if not recs.empty else 0
    total_products = products["Product_Row"].nunique() if not products.empty else 0
    purchases = int(products["Actual_Purchase_Count"].sum()) if not products.empty else 0
    exposure = int(products["N_Customers"].sum()) if not products.empty else 0
    purchase_rate = purchases / exposure * 100 if exposure else 0
    review_count = len(reviews)

    metric_row([
        ("顧客數", f"{total_customers:,}", "推薦模型中的顧客數"),
        ("產品組合", f"{total_products:,}", "正交設計產品組合"),
        ("購買筆數", f"{purchases:,}", "實際購買樣本數"),
        ("整體購買率", f"{purchase_rate:.2f}%", "購買筆數 / 曝光筆數"),
        ("評論數", f"{review_count:,}", "Amazon 評論去重後資料"),
    ])

    st.markdown("""
    <div class="vv-action"><b>本版用途：</b>這不是單純展示圖表，而是讓技詮可以依照「市場區隔 → 目標市場 → 產品定位 → 商品策略 → 產品推廣 → 一對一行銷」的流程，直接產出行銷行動。</div>
    """, unsafe_allow_html=True)

    st.subheader("廠商使用流程")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown("<div class='vv-card'><b>1. 市場區隔</b><br>先看 K-Means 與評論動機，知道買家可分成哪些族群。</div>", unsafe_allow_html=True)
    c2.markdown("<div class='vv-card'><b>2. 目標與定位</b><br>確認技詮優先鎖定誰，以及要用什麼品牌定位降低購買風險。</div>", unsafe_allow_html=True)
    c3.markdown("<div class='vv-card'><b>3. 商品與推廣</b><br>挑出主力商品，設定曝光與成本，做營收/毛利情境試算。</div>", unsafe_allow_html=True)
    c4.markdown("<div class='vv-card'><b>4. 一對一行銷</b><br>查 Customer_ID，輸出推薦商品、EDM、Amazon 文案與 AI 素材 prompt。</div>", unsafe_allow_html=True)

    if not products.empty:
        st.subheader("購買率最高的產品組合")
        chart_df = products.sort_values("Actual_Purchase_Rate", ascending=False).head(10)
        fig = px.bar(chart_df, x="Actual_Purchase_Rate", y="Product_Label", orientation="h", color="Strategy_Tag", text=chart_df["Actual_Purchase_Rate"].map(lambda x: f"{x:.2f}%"), labels={"Actual_Purchase_Rate": "購買率(%)", "Product_Label": "產品組合"}, title="Top 10 商品組合購買率")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=520)
        st.plotly_chart(fig, use_container_width=True)

    if not k_summary.empty:
        st.subheader("K-Means 偏好分群概況")
        kdf = k_summary[["Cluster_Label", "Customer_Count", "Cluster_Action"]].copy()
        st.dataframe(kdf, use_container_width=True, hide_index=True)


def segmentation_page():
    st.header("市場區隔｜顧客動機與偏好分群")
    k_customers, k_summary = load_kmeans()
    reviews = load_reviews_detail()

    st.markdown("""
    本頁回答：市場可分成哪些顧客？他們在意什麼？技詮應如何對不同族群溝通？
    
    本版主要使用 **K-Means 顧客偏好分群** 作為市場區隔主軸，並用評論動機補充顧客需求語言。
    """)
    if k_summary.empty:
        st.warning("尚未偵測到 KMeans_Full_1024_Result.xlsx。請將此檔案放到 GitHub 的 data/ 資料夾。")
    else:
        st.subheader("K-Means 分群結果")
        show = k_summary[["Cluster", "Cluster_Label", "Customer_Count", "Cluster_EN", "Cluster_Action"]].copy()
        st.dataframe(show, use_container_width=True, hide_index=True)
        fig = px.bar(show[show["Cluster_Label"] != "極端值／人工檢查"], x="Cluster_Label", y="Customer_Count", color="Cluster_Label", title="顧客偏好分群人數")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("評論動機分布（排除未明確判讀）")
    if reviews.empty:
        st.info("尚未偵測到評論資料。")
    else:
        valid = reviews[~reviews["Motivation_Type"].isin(["未明確判讀", "其他"])].copy()
        unresolved = len(reviews) - len(valid)
        if valid.empty:
            st.warning("目前所有評論皆未明確判讀，建議人工抽樣修正 Motivation_Type。")
        else:
            mot = valid["Motivation_Type"].value_counts().reset_index()
            mot.columns = ["顧客動機", "評論數"]
            fig = px.bar(mot, x="評論數", y="顧客動機", orientation="h", title="可行銷應用的顧客動機")
            fig.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)
        st.markdown(f"<div class='vv-note'><b>未明確判讀評論：</b>{unresolved} 筆。這類資料不作為主要行銷分群，只作為後續人工標記與模型優化資料。</div>", unsafe_allow_html=True)

    st.subheader("市場區隔命名與落地策略")
    strategy = pd.DataFrame([
        ["極限性能與規格導向群", "在意 Racing 感、Npt 規格、安裝精準度", "主打 MOTOR METER RACING / Npt / 黑橘競技風", "Performance、Precision、Fitment confirmed"],
        ["主流穩健實用群", "在意買對、價格合理、規格清楚", "主打高購買率款、規格表、FAQ、安裝確認清單", "Lower risk、Clear fitment、Good value"],
        ["個人風格與美學鑑賞群", "在意米色、藍色等特殊色系與車內搭配", "主打實裝圖、色系比較、內裝搭配情境", "Style matching、Interior fit、Visual differentiation"],
    ], columns=["市場區隔", "核心需求", "商品/頁面策略", "廣告訊息方向"])
    st.dataframe(strategy, use_container_width=True, hide_index=True)


def target_market_page():
    st.header("目標市場｜技詮優先客群")
    st.markdown("""
    ### 建議優先目標市場
    **技詮應優先鎖定：在 Amazon 等跨境平台購買替換型儀表、重視規格適配與功能可靠的 B2C 顧客。**
    
    這群顧客不是單純追求最低價，而是想降低「買錯規格、安裝不合、功能不穩」的風險。對技詮而言，最有機會的不是價格戰，而是把商品資訊做得比競品更清楚，讓買家更快確認自己買的是正確款式。
    """)
    st.subheader("目標市場輪廓")
    persona = pd.DataFrame([
        ["TA 名稱", "規格適配＋功能可靠型買家"],
        ["主要場景", "Amazon 跨境平台購買汽車／船用／機械儀表替換品"],
        ["主要需求", "確認 Npt / Sae 規格、安裝可用、讀數穩定、商品品質可靠"],
        ["購買障礙", "怕買錯規格、怕安裝失敗、怕圖片與實品不符、怕評價負面問題"],
        ["技詮機會", "用規格表、安裝圖、FAQ、評論摘要與個人化推薦降低購買風險"],
        ["不建議主軸", "單純低價競爭，因為容易被跨境低價賣家取代"],
    ], columns=["項目", "內容"])
    st.dataframe(persona, use_container_width=True, hide_index=True)

    st.subheader("為什麼選這個目標市場？")
    st.markdown("""
    - 產品本身屬於需要確認規格的品類，買錯風險比一般生活用品高。
    - 評論痛點集中在功能、品質、規格與安裝疑慮，這些都可以透過 Amazon Listing 優化改善。
    - K-Means 分群與推薦模型都顯示，Npt、品牌、GPS/功能與價格是影響偏好的重要訊號。
    - 技詮若能把「買前確認」做得更清楚，就能在跨境平台上建立信任感。
    """)


def positioning_page():
    st.header("產品定位｜技詮如何被買家記住")
    st.markdown("""
    ### 建議定位句
    **技詮應定位為：協助跨境買家買對規格、降低安裝風險的專業儀表選購品牌。**
    """)
    st.subheader("定位落地：不是只寫口號，而是改商品頁")
    table = pd.DataFrame([
        ["規格清楚", "Npt / Sae 規格對照表、尺寸圖、適用情境", "降低買錯風險"],
        ["安裝安心", "安裝前確認清單、簡易步驟圖、FAQ", "降低退貨與負評"],
        ["功能可靠", "讀數穩定、GPS/功能說明、使用情境圖", "提高購買信任"],
        ["評論佐證", "高分評論摘要、低分問題回應、改善承諾", "用社會證明補強轉換"],
        ["個人化推薦", "依顧客偏好推 Top 5 商品與文案", "提升再行銷精準度"],
    ], columns=["定位元素", "Amazon / 行銷素材做法", "預期作用"])
    st.dataframe(table, use_container_width=True, hide_index=True)

    st.subheader("定位用在廣告上的一句話")
    st.text_area("可放在 PPT 或商品頁的定位文案", "Find the right gauge faster. PEP with VivaVictors helps buyers confirm fitment, reduce installation risk, and choose reliable gauge products with clearer specs and review-backed recommendations.", height=120)


def product_strategy_page():
    st.header("商品策略｜主推與檢討清單")
    products = load_product_summary()
    if products.empty:
        st.info("目前找不到產品分析資料。")
        return
    st.markdown("本頁回答：哪些商品要主推？哪些商品要檢討？商品策略應該跟目標市場和定位連動。")
    col1, col2, col3, col4 = st.columns(4)
    brand = col1.selectbox("品牌", ["全部"] + sorted(products["Brand"].dropna().unique().tolist()))
    color = col2.selectbox("顏色", ["全部"] + sorted(products["Color"].dropna().unique().tolist()))
    spec = col3.selectbox("規格", ["全部"] + sorted(products["Spec"].dropna().unique().tolist()))
    gps = col4.selectbox("GPS", ["全部"] + sorted(products["GPS"].dropna().unique().tolist()))
    df = products.copy()
    if brand != "全部": df = df[df["Brand"] == brand]
    if color != "全部": df = df[df["Color"] == color]
    if spec != "全部": df = df[df["Spec"] == spec]
    if gps != "全部": df = df[df["GPS"] == gps]
    view = df.sort_values("Actual_Purchase_Rate", ascending=False)[["Product_Row", "Product_Label", "Strategy_Tag", "Actual_Purchase_Rate", "Mean_Predicted_Probability", "Actual_Purchase_Count", "ASIN"]].copy()
    view["Actual_Purchase_Rate"] = view["Actual_Purchase_Rate"].map(lambda x: f"{x:.2f}%")
    view["Mean_Predicted_Probability"] = view["Mean_Predicted_Probability"].map(lambda x: f"{x:.2f}%")
    st.dataframe(view, use_container_width=True, hide_index=True)
    fig = px.scatter(df, x="Mean_Predicted_Probability", y="Actual_Purchase_Rate", size="Actual_Purchase_Count", color="Strategy_Tag", hover_name="Product_Label", labels={"Mean_Predicted_Probability": "平均預測購買機率(%)", "Actual_Purchase_Rate": "實際購買率(%)"}, title="商品潛力矩陣：模型預測 × 實際購買")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("<div class='vv-action'><b>落地做法：</b>右上角商品適合投入廣告與首頁主推；左下角商品要先檢查圖片、規格、價格與低分評論，再決定是否推廣。</div>", unsafe_allow_html=True)


def product_promotion_page():
    st.header("產品推廣｜廣告與效益試算")
    products = load_product_summary()
    if products.empty:
        st.info("目前找不到產品分析資料。")
        return
    st.markdown("本頁不是宣稱真實利潤，而是提供廠商在沒有完整成本資料前的推廣情境試算。")
    product_options = products.sort_values("Actual_Purchase_Rate", ascending=False)["Product_Label"].tolist()
    selected_label = st.selectbox("選擇要推廣的商品組合", product_options)
    product = products[products["Product_Label"] == selected_label].iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    exposure = col1.number_input("預計曝光人數", min_value=100, max_value=500000, value=10000, step=500)
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
    metric_row([
        ("試算轉換率", f"{est_rate*100:.2f}%", "商品購買率 × 調整係數"),
        ("預估購買數", f"{est_orders:,.0f}", "曝光 × 試算轉換率"),
        ("預估營收", f"${revenue:,.0f}", "購買數 × 售價"),
        ("預估毛利", f"${gross_profit:,.0f}", "營收 × 假設毛利率"),
        ("扣廣告後", f"${net_profit:,.0f}", "毛利 - 廣告成本"),
    ])
    st.markdown(f"<div class='vv-note'><b>公式：</b>預估購買數 = 曝光人數 × 商品購買率 × 轉換率調整係數；預估營收 = 預估購買數 × 售價；ROAS = 預估營收 ÷ 廣告成本。{f' 目前 ROAS 試算為 {roas:.2f}。' if roas is not None else ''}</div>", unsafe_allow_html=True)
    scenario = products.sort_values("Actual_Purchase_Rate", ascending=False).head(8).copy()
    scenario["預估購買數"] = exposure * (scenario["Actual_Purchase_Rate"] / 100) * rate_adjust
    scenario["預估營收"] = scenario["預估購買數"] * scenario["Price"]
    scenario["預估毛利"] = scenario["預估營收"] * margin_rate
    fig = px.bar(scenario, x="Product_Label", y="預估營收", color="Strategy_Tag", title="同樣曝光下，不同商品組合的營收試算")
    fig.update_layout(xaxis_tickangle=-25, height=520)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(scenario[["Product_Label", "Actual_Purchase_Rate", "Price", "預估購買數", "預估營收", "預估毛利"]], use_container_width=True, hide_index=True)


def recommendation_page():
    st.header("顧客推薦｜一對一行銷與 AI 廣告素材")
    recs = load_recommendations()
    products = load_product_summary()
    k_customers, _ = load_kmeans()
    rfm = load_rfm()
    if recs.empty:
        st.info("目前找不到 Recommendation_Top5 資料。")
        return
    customer_ids = sorted(recs["Customer_ID"].dropna().astype(str).unique().tolist())
    query = st.text_input("搜尋 Customer_ID", "")
    filtered = [c for c in customer_ids if query.lower() in c.lower()] if query else customer_ids
    selected = st.selectbox("選擇顧客", filtered[:1000])
    cust = recs[recs["Customer_ID"] == selected].copy()
    cust = cust.merge(products[["Product_Row", "Product_Label", "Brand", "Price", "Color", "Spec", "GPS", "Strategy_Tag"]], on="Product_Row", how="left")
    cust = cust.sort_values("Predicted_Probability", ascending=False)
    best = cust.iloc[0]
    cluster_label = "未分群"
    if not k_customers.empty and "Customer_ID" in k_customers.columns:
        tmp = k_customers[k_customers["Customer_ID"].astype(str) == selected]
        if not tmp.empty:
            cluster_label = tmp.iloc[0].get("Cluster_Label", "未分群")
    rfm_label = "未對接"
    if not rfm.empty and selected in set(rfm["Customer_ID"].astype(str)):
        rfm_label = str(rfm[rfm["Customer_ID"].astype(str) == selected].iloc[0].get("RFM_Label", "未標示"))
    metric_row([
        ("最佳推薦商品", best["Product_Label"], "模型 Top 1"),
        ("預測購買機率", f"{best['Predicted_Probability']*100:.2f}%", "Ridge logistic model"),
        ("偏好群集", cluster_label, "K-Means 偏好分群"),
        ("RFM 分群", rfm_label[:20], "顧客價值標籤"),
    ])
    display = cust[["Product_Row", "Product_Label", "Predicted_Probability", "Strategy_Tag"]].copy()
    display["Predicted_Probability"] = display["Predicted_Probability"].map(lambda x: f"{x*100:.2f}%")
    st.dataframe(display, use_container_width=True, hide_index=True)

    st.subheader("個人化行銷輸出")
    channel = st.selectbox("選擇輸出類型", ["EDM 文案", "Amazon 商品標題與五點描述", "Meta/IG 廣告文案", "AI 圖片生成 Prompt", "短影音腳本"])
    brand, color, spec, gps = best["Brand"], best["Color"], best["Spec"], best["GPS"]
    if channel == "EDM 文案":
        text = f"您好，我們根據您的商品偏好，推薦 {brand} 的 {color} {spec} 款式。這款商品符合您可能重視的規格適配與功能可靠需求，並屬於目前可優先推薦的商品組合。建議您在下單前確認螺紋規格與安裝位置，以降低買錯風險。"
    elif channel == "Amazon 商品標題與五點描述":
        text = f"Title: {brand} {color} Gauge, {spec} Fitment, {gps}, Clear Installation Guidance\n\nBullet Points:\n1. Clear {spec} fitment information to reduce wrong-purchase risk.\n2. Designed for buyers who care about reliable gauge performance.\n3. {color} style suitable for replacement and dashboard matching.\n4. Review-backed product information helps buyers confirm before purchase.\n5. Recommended for customers seeking fitment clarity and stable functionality."
    elif channel == "Meta/IG 廣告文案":
        text = f"怕買錯儀表規格？PEP with VivaVictors 幫你更快確認 {spec} 規格與合適款式。現在查看 {brand} {color} 款，降低安裝風險，買得更安心。"
    elif channel == "AI 圖片生成 Prompt":
        text = f"Create a clean Amazon-style product image for a {color} automotive gauge by {brand}. Show the gauge installed on a dashboard with visual callouts for {spec} thread fitment, clear installation guidance, and reliable performance. Use a professional cross-border e-commerce product photography style."
    else:
        text = f"0-3秒：買錯儀表規格很麻煩。\n3-7秒：PEP with VivaVictors 幫你確認 {spec} 規格與合適款式。\n7-12秒：推薦 {brand} {color} 款，降低安裝風險。\n12-15秒：立即查看商品，買對規格更安心。"
    st.text_area("可複製素材", text, height=220)
    st.markdown("<div class='vv-action'><b>落地做法：</b>此區不是直接生成圖片，而是把推薦結果轉成可貼到 Canva、Adobe Express、Firefly、CapCut 等工具的素材草稿與 Prompt。</div>", unsafe_allow_html=True)


def customer_list_page():
    st.header("顧客名單｜RFM／CAI 與行銷策略")
    rfm = load_rfm()
    k_customers, _ = load_kmeans()
    if rfm.empty:
        st.info("目前找不到 RFM／CAI 資料。")
        return
    if not k_customers.empty and "Customer_ID" in k_customers.columns:
        rfm = rfm.merge(k_customers[["Customer_ID", "Cluster_Label", "Cluster_Action"]], on="Customer_ID", how="left")
        rfm["Cluster_Label"] = rfm["Cluster_Label"].fillna("未分群")
    st.subheader("RFM 分群分布")
    counts = rfm["RFM_Label"].value_counts().reset_index()
    counts.columns = ["RFM_Label", "Customer_Count"]
    fig = px.bar(counts, x="Customer_Count", y="RFM_Label", orientation="h", title="顧客價值分群人數")
    fig.update_layout(height=480, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)
    selected = st.selectbox("選擇分群查看行銷策略與名單", counts["RFM_Label"].tolist())
    seg = rfm[rfm["RFM_Label"] == selected].copy()
    keyword = "資料不足"
    for k in RFM_STRATEGY.keys():
        if k in selected:
            keyword = k
            break
    objective, method, channel = RFM_STRATEGY.get(keyword, ["分眾培養", "主力商品推薦＋規格教育", "EDM / 商品頁 / 再行銷"])
    st.markdown(f"""
    <div class='vv-action'><b>此名單的行銷方式：</b><br>
    行銷目標：{objective}<br>
    建議做法：{method}<br>
    建議管道：{channel}</div>
    """, unsafe_allow_html=True)
    st.dataframe(seg.head(300), use_container_width=True, hide_index=True)
    csv = seg.to_csv(index=False).encode("utf-8-sig")
    st.download_button("下載此分群名單 CSV", csv, file_name=f"{selected}_customer_list.csv", mime="text/csv")


def review_insights_page():
    st.header("評論洞察｜痛點與 Amazon Listing 改善")
    reviews = load_reviews_detail()
    summary = load_reviews_summary()
    if reviews.empty:
        st.info("目前找不到評論資料。")
        return
    avg_rating = reviews["Rating"].mean()
    positive_rate = (reviews["Sentiment_Label"].astype(str).str.contains("正|Positive", regex=True).mean() * 100)
    valid = reviews[~reviews["Motivation_Type"].isin(["未明確判讀", "其他"])].copy()
    top_mot = valid["Motivation_Type"].mode().iloc[0] if not valid.empty and not valid["Motivation_Type"].mode().empty else "未明確判讀"
    metric_row([
        ("平均評分", f"{avg_rating:.2f}", "Review rating average"),
        ("正向評論占比", f"{positive_rate:.1f}%", "4-5 星或正向標籤"),
        ("主要明確動機", top_mot, "排除未明確判讀"),
    ])
    if not valid.empty:
        mot = valid["Motivation_Type"].value_counts().reset_index()
        mot.columns = ["Motivation_Type", "Review_Count"]
        fig = px.bar(mot, x="Review_Count", y="Motivation_Type", orientation="h", title="可直接用於行銷的評論動機")
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("評論痛點 → Amazon 頁面改善")
    actions = pd.DataFrame([
        ["規格不清楚", "商品資訊區 / A+ Content", "放 Npt / Sae 對照表、尺寸圖、適用設備說明", "降低買錯規格與退貨風險"],
        ["安裝不確定", "圖片區 / FAQ", "加入安裝前確認清單、步驟圖、常見問題", "讓買家下單前可自行確認"],
        ["功能不明確", "主圖 / 影片 / Bullet Points", "展示讀數、GPS/功能說明、使用情境", "提高對功能可靠性的信任"],
        ["品質疑慮", "Bullet Points / Review Summary", "加入材質、保固、測試說明、低分問題回應", "降低負評疑慮"],
        ["外觀選擇困難", "圖片區", "放黑/白/米色實裝比較與情境圖", "協助外觀搭配型買家選擇"],
    ], columns=["評論痛點", "Amazon 呈現位置", "具體改善做法", "預期效果"])
    st.dataframe(actions, use_container_width=True, hide_index=True)
    st.subheader("ASIN 商品評論摘要")
    if not summary.empty:
        st.dataframe(summary.sort_values("Review_Count", ascending=False), use_container_width=True, hide_index=True)
    st.subheader("低分評論範例與處理建議")
    neg = reviews[reviews["Rating"] <= 2].copy()
    cols = [c for c in ["ASIN", "Rating", "Motivation_Type", "Review_Text"] if c in neg.columns]
    st.dataframe(neg[cols].head(20), use_container_width=True, hide_index=True)
    st.markdown("<div class='vv-note'><b>落地作法：</b>低分評論不只放在報告中，應轉成商品頁 FAQ、A+ Content、客服回覆模板與廣告素材避雷說明。</div>", unsafe_allow_html=True)


pages = {
    "首頁｜總覽與操作手冊": overview_page,
    "市場區隔｜顧客動機分群": segmentation_page,
    "目標市場｜技詮優先客群": target_market_page,
    "產品定位｜技詮如何被記住": positioning_page,
    "商品策略｜主推與檢討清單": product_strategy_page,
    "產品推廣｜廣告與效益試算": product_promotion_page,
    "顧客推薦｜一對一行銷": recommendation_page,
    "顧客名單｜RFM/CAI 策略": customer_list_page,
    "評論洞察｜痛點與 Listing 改善": review_insights_page,
}

with st.sidebar:
    st.title("VivaVictors")
    st.caption("Marketing Dashboard")
    selected_page = st.radio("選擇功能", list(pages.keys()))
    st.divider()
    st.caption("流程：市場區隔 → 目標市場 → 產品定位 → 商品推廣 → 一對一行銷")

pages[selected_page]()
