from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

APP_TITLE = "PEP with VivaVictors｜Marketing Dashboard"
APP_SUBTITLE = "跨境電商日常行銷工作台：市場區隔、目標客群、產品定位、商品推廣與一對一行銷"
DATA_DIR = Path(__file__).parent / "data"

RIDGE_KEY = "ridge_logit_customer_specific_report"
RFM_KEY = "RFM_CAI"
DESIGN_KEY = "正交設計"
KMEANS_FINAL_KEY = "KMeans_Final_Result"
KMEANS_FALLBACK_KEY = "KMeans_Full_1024_Result"
REVIEWS_DETAIL_KEY = "reviews_processed_classified.csv"
REVIEWS_SUMMARY_KEY = "reviews_summary_processed.csv"

BRAND_COLS = ["Dolphin Gauges", "Faria", "MOTOR METER RACING", "Speedway Motors", "RACETECH"]
COLOR_MAP = {
    "orange": "橘色", "white": "白色", "beige": "米色", "green": "綠色", "blue": "藍色", "yellow": "黃色", "black": "黑色",
    "紅色": "紅色", "白色": "白色", "黑色": "黑色", "米色": "米色",
}
COLOR_COLS = list(COLOR_MAP.keys())
SPEC_COLS = ["Npt", "Sae,Npt", "Sae"]

SEGMENT_CONFIG = {
    1: {
        "name": "性能規格導向客群",
        "subtitle": "重視 Racing 感、NPT 規格與安裝精準度",
        "business_name": "高涉入技術買家",
        "priority": "Moto Meter Racing 主推客群",
        "need": "買家想快速確認產品是否符合性能需求與安裝規格，避免買錯或安裝失敗。",
        "message": "強調精準、穩定、Racing 風格與清楚規格表。",
        "landing": "Amazon Listing 首圖與五點描述要清楚標出 NPT 規格、安裝情境與 Racing / Performance 使用語境。",
    },
    2: {
        "name": "主流實用與價格敏感客群",
        "subtitle": "重視黑色主流外觀、GPS 功能、價格與實用性",
        "business_name": "大眾轉換買家",
        "priority": "大量曝光與轉換測試客群",
        "need": "買家希望商品看起來可靠、價格合理、功能實用，並能降低跨境購買風險。",
        "message": "強調 CP 值、GPS 功能、主流黑色款與正向評價。",
        "landing": "可用折扣、免運、主流款式比較表與評論摘要提升轉換。",
    },
    3: {
        "name": "風格美學與內裝搭配客群",
        "subtitle": "重視米色、特殊色系與車內視覺搭配",
        "business_name": "風格差異化買家",
        "priority": "差異化素材與情境圖客群",
        "need": "買家不是只看規格，也在意儀表與內裝是否搭配、是否有獨特風格。",
        "message": "強調內裝搭配、特殊色系、質感與安裝後效果。",
        "landing": "商品圖要補足米色／特殊色系實裝照、情境圖與顏色比較。",
    },
}

ATTRIBUTE_LABELS = {
    "MOTOR.METER.RACING": "Moto Meter Racing 品牌偏好",
    "Dolphin.Gauges": "Dolphin Gauges 品牌偏好",
    "Speedway.Motors": "Speedway Motors 品牌偏好",
    "Faria": "Faria 品牌偏好",
    "GPS": "GPS 功能偏好",
    "Npt": "NPT 螺紋規格偏好",
    "Sae.Npt": "SAE/NPT 規格偏好",
    "price": "價格敏感度",
    "black": "黑色外觀偏好",
    "white": "白色外觀偏好",
    "beige": "米色外觀偏好",
    "blue": "藍色外觀偏好",
    "green": "綠色外觀偏好",
    "orange": "橘色外觀偏好",
    "yellow": "黃色外觀偏好",
    "Intercept": "基礎購買傾向",
}

TERM_EXPLAIN = {
    "NPT": "NPT 是常見螺紋規格之一。對行銷人員來說，重點不是技術細節，而是買家需要清楚知道商品是否能安裝、是否買對規格。",
    "SAE/NPT": "SAE/NPT 代表不同規格相容或標示方式。若商品頁說明不清，跨境買家容易因規格不確定而放棄購買。",
    "GPS": "GPS 代表商品具備定位或訊號相關功能。行銷上可轉譯為『功能更完整、使用情境更明確』。",
    "購買率": "在本資料中，購買率代表某產品組合被購買的比例。它可作為商品主推優先順序的參考，但仍需搭配庫存、成本與廣告預算判斷。",
    "分群": "分群是把相似偏好的產品組合或顧客放在一起。儀表板前台不使用統計術語，會直接呈現為『市場區隔』與『客群輪廓』。",
}

st.set_page_config(page_title="PEP with VivaVictors", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

CUSTOM_CSS = """
<style>
.block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1360px;}
.vv-hero {padding: 1.35rem 1.55rem; border-radius: 1.25rem; background: linear-gradient(135deg, #0f172a 0%, #1f2937 55%, #334155 100%); color: white; margin-bottom: 1.2rem;}
.vv-card {padding: 1rem 1.1rem; border: 1px solid rgba(148, 163, 184, .35); border-radius: 1rem; background: rgba(148, 163, 184, .08); margin-bottom: .85rem;}
.vv-note {padding: .85rem 1rem; border-left: 4px solid #2563eb; background: rgba(37, 99, 235, .09); border-radius: .6rem; margin: .8rem 0;}
.vv-action {padding: .85rem 1rem; border-left: 4px solid #16a34a; background: rgba(22, 163, 74, .09); border-radius: .6rem; margin: .8rem 0;}
.vv-warning {padding: .85rem 1rem; border-left: 4px solid #f59e0b; background: rgba(245, 158, 11, .12); border-radius: .6rem; margin: .8rem 0;}
.vv-source {font-size:.82rem; opacity:.68; margin-top:-.2rem; margin-bottom: .8rem;}
.small-text {font-size: .92rem; opacity: .86;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def file_by_keyword(keyword: str, suffix: str | None = None) -> Path | None:
    if not DATA_DIR.exists():
        return None
    for path in sorted(DATA_DIR.iterdir()):
        name = path.name
        if keyword in name and (suffix is None or name.endswith(suffix)):
            return path
    return None


def data_source(filename: str, note: str = ""):
    text = f"資料來源：`data/{filename}`"
    if note:
        text += f"｜{note}"
    st.markdown(f"<div class='vv-source'>{text}</div>", unsafe_allow_html=True)


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
    if series is None:
        return pd.Series(dtype=float)
    return pd.to_numeric(series, errors="coerce").fillna(default)


def first_present(row, cols, default="未標示"):
    for col in cols:
        if col in row.index:
            try:
                if pd.notna(row[col]) and float(row[col]) == 1:
                    return COLOR_MAP.get(col, col)
            except Exception:
                value = str(row[col]).strip()
                if pd.notna(row[col]) and value not in ["", "0", "nan"]:
                    return COLOR_MAP.get(value, value)
    return default


def action_label(rate: float) -> str:
    if pd.isna(rate):
        return "資料不足"
    if rate >= 10:
        return "立即主推"
    if rate >= 5:
        return "優先測試"
    if rate >= 2:
        return "維持觀察"
    return "需要檢討"


def action_definition(tag: str) -> str:
    mapping = {
        "立即主推": "購買率高，適合放入首頁主打、廣告素材與 EDM 主推清單。",
        "優先測試": "具備潛力，建議用小額廣告或 A/B 素材測試是否能放大。",
        "維持觀察": "表現中等，先維持上架與自然流量觀察，不宜大量投放。",
        "需要檢討": "購買率偏低，建議檢查價格、圖片、規格說明、評論痛點或暫緩推廣。",
        "資料不足": "目前資料不足，需累積更多曝光或購買紀錄。",
    }
    return mapping.get(tag, "需由行銷人員進一步判讀。")


def product_label(row) -> str:
    row_no = int(row.get("Product_Row", 0)) if pd.notna(row.get("Product_Row", 0)) else 0
    brand = row.get("Brand", "未標示")
    price = row.get("Price", "-")
    color = row.get("Color", "-")
    spec = row.get("Spec_Display", row.get("Spec", "-"))
    gps = row.get("GPS_Display", row.get("GPS", "-"))
    try:
        price = int(float(price))
    except Exception:
        pass
    return f"#{row_no}｜{brand}｜${price}｜{color}｜{spec}｜{gps}"


def spec_display(value) -> str:
    value = str(value)
    if value.lower() == "npt":
        return "NPT 螺紋規格"
    if value.lower() in ["sae,npt", "sae.npt"]:
        return "SAE/NPT 複合規格"
    if value.lower() == "sae":
        return "SAE 規格"
    return value


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

    df["Brand"] = df.apply(lambda r: first_present(r, BRAND_COLS), axis=1)
    df["Color"] = df.apply(lambda r: first_present(r, COLOR_COLS), axis=1)
    df["Spec"] = df.apply(lambda r: first_present(r, SPEC_COLS, default="Sae"), axis=1)
    df["ASIN"] = ""

    design_path = file_by_keyword(DESIGN_KEY, ".xlsx")
    if design_path is not None:
        design = pd.read_excel(design_path)
        design = make_unique_columns(design).reset_index(drop=True).copy()
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
        df = df.merge(design, on="Product_Row", how="left", suffixes=("", "_design"))
        for base, design_col in [("Brand", "Design_Brand"), ("Price", "Design_Price"), ("Color", "Design_Color"), ("Spec", "Design_Spec"), ("GPS_Flag", "Design_GPS_Flag"), ("ASIN", "Design_ASIN")]:
            if design_col in df.columns:
                df[base] = df[design_col].combine_first(df[base])

    df["GPS_Flag"] = to_numeric(df["GPS_Flag"], 0).astype(int)
    df["GPS_Display"] = df["GPS_Flag"].map({1: "有 GPS 功能", 0: "無 GPS 功能"})
    df["GPS"] = df["GPS_Display"]
    df["Spec_Display"] = df["Spec"].apply(spec_display)
    df["Price"] = to_numeric(df["Price"], 0)
    df["Strategy_Tag"] = df["Actual_Purchase_Rate"].apply(action_label)
    df["Strategy_Action"] = df["Strategy_Tag"].apply(action_definition)
    df["Product_Label"] = df.apply(product_label, axis=1)
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
        if "CAI_Label" not in result.columns:
            result["CAI_Label"] = "未對接"
        result["CAI_Label"] = result["CAI_Label"].fillna("未對接")
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
    if "Motivation_Type" not in df.columns:
        df["Motivation_Type"] = "未明確判讀"
    df["Motivation_Type"] = df["Motivation_Type"].replace({"其他": "未明確判讀", "功能需求": "功能可靠需求"})
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


@st.cache_data(show_spinner=False)
def load_market_segments() -> tuple[pd.DataFrame, pd.DataFrame, str]:
    final_path = file_by_keyword(KMEANS_FINAL_KEY, ".xlsx")
    source_name = "KMeans_Final_Result.xlsx"
    if final_path is None:
        final_path = file_by_keyword(KMEANS_FALLBACK_KEY, ".xlsx")
        source_name = "KMeans_Full_1024_Result.xlsx"
    if final_path is None:
        return pd.DataFrame(), pd.DataFrame(), ""
    try:
        detail = pd.read_excel(final_path, sheet_name="Clustering_Data")
    except Exception:
        try:
            detail = pd.read_excel(final_path, sheet_name="All_Customers_Clustered")
        except Exception:
            detail = pd.DataFrame()
    try:
        summary = pd.read_excel(final_path, sheet_name="Cluster_Summary")
    except Exception:
        summary = pd.DataFrame()
    detail = make_unique_columns(detail) if not detail.empty else detail
    summary = make_unique_columns(summary) if not summary.empty else summary
    if not summary.empty:
        summary["Cluster"] = to_numeric(summary["Cluster"], 0).astype(int)
        total = summary["Customer_Count"].sum() if "Customer_Count" in summary.columns else len(detail)
        summary["Share"] = summary["Customer_Count"] / total * 100 if total else 0
        summary["Segment_Name"] = summary["Cluster"].map(lambda x: SEGMENT_CONFIG.get(int(x), {}).get("name", f"第{x}群"))
        summary["Business_Name"] = summary["Cluster"].map(lambda x: SEGMENT_CONFIG.get(int(x), {}).get("business_name", "未命名客群"))
        summary["Subtitle"] = summary["Cluster"].map(lambda x: SEGMENT_CONFIG.get(int(x), {}).get("subtitle", ""))
        summary["Priority"] = summary["Cluster"].map(lambda x: SEGMENT_CONFIG.get(int(x), {}).get("priority", ""))
    return detail, summary, source_name


def render_header():
    st.markdown(
        f"""
        <div class="vv-hero">
            <h1 style="margin:0; font-size:2.15rem;">{APP_TITLE}</h1>
            <p style="margin:.35rem 0 0 0; opacity:.9; font-size:1.05rem;">{APP_SUBTITLE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def term_box():
    with st.expander("名詞說明：讓非技術行銷人員也看得懂", expanded=False):
        for key, value in TERM_EXPLAIN.items():
            st.markdown(f"**{key}：**{value}")


def overview_page():
    render_header()
    st.header("首頁｜總覽與操作手冊")
    products = load_product_summary()
    recs = load_recommendations()
    reviews = load_reviews_detail()
    _, seg_summary, source_name = load_market_segments()

    total_customers = recs["Customer_ID"].nunique() if not recs.empty else 0
    total_products = products["Product_Row"].nunique() if not products.empty else 0
    purchases = int(products["Actual_Purchase_Count"].sum()) if not products.empty else 0
    exposure = int(products["N_Customers"].sum()) if not products.empty else 0
    purchase_rate = purchases / exposure * 100 if exposure else 0
    review_count = len(reviews)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("顧客數", f"{total_customers:,}", help="來自推薦模型輸出，代表目前可進行推薦查詢的顧客數。")
    c2.metric("產品組合", f"{total_products:,}", help="目前可分析與推薦的商品組合數。")
    c3.metric("購買筆數", f"{purchases:,}", help="歷史資料中 purchasing=1 的筆數。")
    c4.metric("整體購買率", f"{purchase_rate:.2f}%", help="購買筆數 ÷ 總曝光／組合資料筆數。")
    c5.metric("評論數", f"{review_count:,}", help="已整理後可進行動機與痛點判讀的評論數。")

    st.markdown("""
    <div class="vv-action"><b>行銷人員每天先看什麼？</b><br>
    先看市場區隔與目標市場，確認今天要對誰說話；再看商品策略與產品推廣，決定推哪個商品、用多少預算；最後看顧客推薦與名單策略，把商品轉成一對一行銷訊息。</div>
    """, unsafe_allow_html=True)

    if not products.empty:
        top = products.sort_values("Actual_Purchase_Rate", ascending=False).iloc[0]
        st.markdown(
            f"""
            <div class="vv-card"><b>今日主推候選：</b>{top['Product_Label']}<br>
            <b>判斷原因：</b>目前實際購買率為 <b>{top['Actual_Purchase_Rate']:.2f}%</b>，屬於「{top['Strategy_Tag']}」。<br>
            <b>下一步：</b>{top['Strategy_Action']}</div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("操作路徑：從策略到執行")
    steps = pd.DataFrame([
        ["1 市場區隔", "看 28 種產品偏好原型被分成哪些客群", "決定市場要怎麼切"],
        ["2 目標市場", "選擇技詮最應優先鎖定的客群", "決定資源投放對象"],
        ["3 產品定位", "把商品定位轉成可說服買家的訊息", "決定產品頁與廣告主張"],
        ["4 商品策略", "看哪些商品立即主推、哪些需要檢討", "決定上架與推廣優先順序"],
        ["5 產品推廣", "用曝光、價格、毛利率與廣告成本做試算", "決定預算與活動可行性"],
        ["6 一對一行銷", "依 Customer_ID 產生推薦與廣告素材草稿", "執行 EDM、再行銷與客服推薦"],
    ], columns=["順序", "看什麼", "得到什麼決策"])
    st.dataframe(steps, width="stretch", hide_index=True)

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
            labels={"Actual_Purchase_Rate": "購買率(%)", "Product_Label": "產品組合", "Strategy_Tag": "行銷判斷"},
            title="Top 10 商品組合購買率",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=520)
        st.plotly_chart(fig, width="stretch")
        data_source("ridge_logit_customer_specific_report_*.xlsx", "Product_Summary 工作表；商品屬性補充自 正交設計_產品組合.xlsx")

    term_box()
    if source_name:
        st.caption(f"目前市場區隔資料來源：data/{source_name}。若更換分群結果，請替換此檔案並重啟 Streamlit。")


def market_segmentation_page():
    st.header("市場區隔｜顧客偏好族群")
    detail, summary, source_name = load_market_segments()
    if summary.empty:
        st.info("目前找不到市場區隔資料。請在 data/ 放入 KMeans_Final_Result.xlsx。")
        return
    st.markdown("本頁把統計分群結果轉成行銷人員可理解的市場區隔。前台不使用 K-Means 等技術術語，而是直接呈現每個客群的偏好、痛點與行銷用途。")
    data_source(source_name, "Clustering_Data 與 Cluster_Summary 工作表；本頁為 28 種產品偏好原型分群")

    cols = st.columns(3)
    for i, (_, row) in enumerate(summary.sort_values("Cluster").iterrows()):
        cluster = int(row["Cluster"])
        cfg = SEGMENT_CONFIG.get(cluster, {})
        with cols[(cluster - 1) % 3]:
            st.markdown(
                f"""
                <div class="vv-card">
                <h4 style="margin:.1rem 0;">第 {cluster} 群｜{cfg.get('name', row['Segment_Name'])}</h4>
                <b>占比：</b>{row.get('Share', 0):.1f}%｜<b>樣本：</b>{int(row.get('Customer_Count', 0))} 種產品偏好原型<br>
                <b>行銷角色：</b>{cfg.get('business_name', '')}<br>
                <b>使用情境：</b>{cfg.get('priority', '')}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.subheader("各客群占比")
    fig = px.pie(summary, names="Segment_Name", values="Customer_Count", title="產品偏好原型分布")
    st.plotly_chart(fig, width="stretch")

    st.subheader("客群偏好雷達圖")
    radar_attrs = ["MOTOR.METER.RACING", "Npt", "GPS", "price", "black", "beige", "orange"]
    fig_r = go.Figure()
    for _, row in summary.iterrows():
        values = [float(row.get(a, 0)) for a in radar_attrs]
        fig_r.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=[ATTRIBUTE_LABELS.get(a, a) for a in radar_attrs] + [ATTRIBUTE_LABELS.get(radar_attrs[0], radar_attrs[0])],
            fill="toself",
            name=row["Segment_Name"],
        ))
    fig_r.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True, height=560)
    st.plotly_chart(fig_r, width="stretch")

    st.subheader("這些客群代表什麼？")
    rows = []
    for _, row in summary.sort_values("Cluster").iterrows():
        cluster = int(row["Cluster"])
        cfg = SEGMENT_CONFIG.get(cluster, {})
        rows.append([cfg.get("name", f"第{cluster}群"), cfg.get("need", ""), cfg.get("message", ""), cfg.get("landing", "")])
    st.dataframe(pd.DataFrame(rows, columns=["客群", "主要需求", "行銷訊息", "落地做法"]), width="stretch", hide_index=True)

    st.markdown("""
    <div class="vv-warning"><b>重要提醒：</b>這份分群資料是以 28 種產品偏好原型建立市場區隔，不是直接把 1024 位顧客逐一分群。若要回推到全體顧客比例，需要再把每位顧客實際購買或最高偏好產品組合對應回這 28 種原型。</div>
    """, unsafe_allow_html=True)


def target_market_page():
    st.header("目標市場｜技詮優先客群")
    st.markdown("老師問的核心其實是：技詮到底要先服務誰？本頁將市場區隔轉成目標市場選擇。")
    st.markdown("""
    <div class="vv-action"><b>建議優先目標市場：</b><br>
    技詮應優先鎖定「性能規格導向客群」與「主流實用與價格敏感客群」。前者適合推 Moto Meter Racing 與 NPT 規格商品，後者適合做主流款大量曝光與價格／功能轉換測試。</div>
    """, unsafe_allow_html=True)

    df = pd.DataFrame([
        ["第一優先", "性能規格導向客群", "Moto Meter Racing、NPT、Racing 感、安裝精準", "這群買家對規格與性能敏感，最容易被清楚規格與專業感說服", "Moto Meter Racing 主推頁、規格表、安裝示意圖、Performance 文案"],
        ["第二優先", "主流實用與價格敏感客群", "黑色、GPS、價格、CP 值", "占比最大、最適合做廣告放量與促銷測試", "主流黑色款、折扣、免運、GPS 功能說明"],
        ["差異化補充", "風格美學與內裝搭配客群", "米色、特殊色系、內裝搭配", "適合做差異化品牌素材，不一定是最大量但有定位價值", "實裝圖、顏色比較、風格情境素材"],
    ], columns=["優先順序", "目標市場", "關鍵偏好", "選擇理由", "落地行動"])
    st.dataframe(df, width="stretch", hide_index=True)
    data_source("KMeans_Final_Result.xlsx", "依 28 種產品偏好原型的市場區隔結果整理")

    st.subheader("Moto Meter Racing 應該主推哪一群？")
    st.markdown("""
    <div class="vv-card"><b>結論：</b>Moto Meter Racing 應優先主推「性能規格導向客群」。<br>
    理由是此群對 Moto Meter Racing、NPT 規格與 Racing 感的偏好最明確。行銷上不要只說品牌名稱，而要把它轉成買家看得懂的價值：<b>規格清楚、安裝風險低、性能感強、適合重度 DIY 或改裝需求。</b></div>
    """, unsafe_allow_html=True)


def positioning_page():
    st.header("產品定位｜技詮如何被記住")
    st.markdown("產品定位不是描述商品有哪些屬性，而是讓目標買家知道：為什麼我要買技詮，而不是買其他 Amazon 賣家的相似商品？")
    st.markdown("""
    <div class="vv-action"><b>建議定位句：</b><br>
    技詮應定位為「協助跨境買家買對規格、降低安裝風險的專業汽車儀表選購品牌」。</div>
    """, unsafe_allow_html=True)

    positioning_df = pd.DataFrame([
        ["目標對象", "Amazon 跨境平台上的 DIY／維修／改裝型儀表買家"],
        ["核心痛點", "怕買錯規格、怕安裝不合、怕功能不穩、怕跨境退換貨麻煩"],
        ["技詮價值", "用清楚規格表、安裝示意圖、評論佐證與個人化推薦降低購買風險"],
        ["品牌印記", "專業、清楚、穩定、規格可信任，而不是單純低價"],
        ["產品頁主張", "Fit Right, Install Easier, Drive with Confidence"],
    ], columns=["定位元素", "建議內容"])
    st.dataframe(positioning_df, width="stretch", hide_index=True)

    st.subheader("如何落實在 Amazon Listing？」")
    landing = pd.DataFrame([
        ["主圖", "標出儀表外觀、顏色、NPT / SAE 規格提示，不只放產品本體"],
        ["第二張圖", "加入規格尺寸圖與安裝前確認清單"],
        ["第三張圖", "放車內實裝情境，尤其黑色、米色等內裝搭配"],
        ["五點描述", "第一點先解決規格與相容性，第二點再講功能，第三點講品質"],
        ["FAQ", "回答是否相容、如何確認規格、GPS 功能如何使用、安裝需要注意什麼"],
        ["A+ Content", "用『買錯規格很麻煩 → 技詮幫你確認』作為故事線"],
    ], columns=["Listing 區塊", "具體做法"])
    st.dataframe(landing, width="stretch", hide_index=True)


def product_strategy_page():
    st.header("商品策略｜主推與檢討清單")
    products = load_product_summary()
    if products.empty:
        st.info("目前找不到產品分析資料。")
        return

    st.markdown("本頁是日常商品管理工具：行銷人員可用它判斷今天要推哪個商品、哪些商品先小額測試、哪些商品需要檢查頁面或暫緩投放。")
    with st.expander("行銷判斷標籤怎麼看？", expanded=True):
        st.markdown("""
        - **立即主推**：購買率高，適合放到廣告、EDM、首頁或商品頁推薦區。
        - **優先測試**：有潛力，但需要用小額預算測試素材、受眾或折扣方案。
        - **維持觀察**：維持自然流量與基本曝光，不建議大量增加預算。
        - **需要檢討**：先檢查圖片、規格說明、價格、評論痛點或是否暫緩推廣。
        """)

    col1, col2, col3, col4 = st.columns(4)
    brand = col1.selectbox("品牌", ["全部"] + sorted(products["Brand"].dropna().unique().tolist()))
    color = col2.selectbox("顏色", ["全部"] + sorted(products["Color"].dropna().unique().tolist()))
    spec = col3.selectbox("規格", ["全部"] + sorted(products["Spec_Display"].dropna().unique().tolist()))
    gps = col4.selectbox("GPS", ["全部"] + sorted(products["GPS_Display"].dropna().unique().tolist()))

    df = products.copy()
    if brand != "全部": df = df[df["Brand"] == brand]
    if color != "全部": df = df[df["Color"] == color]
    if spec != "全部": df = df[df["Spec_Display"] == spec]
    if gps != "全部": df = df[df["GPS_Display"] == gps]

    view = df.sort_values("Actual_Purchase_Rate", ascending=False)[["Product_Row", "Product_Label", "Strategy_Tag", "Strategy_Action", "Actual_Purchase_Rate", "Mean_Predicted_Probability", "Actual_Purchase_Count", "ASIN"]].copy()
    view["Actual_Purchase_Rate"] = view["Actual_Purchase_Rate"].map(lambda x: f"{x:.2f}%")
    view["Mean_Predicted_Probability"] = view["Mean_Predicted_Probability"].map(lambda x: f"{x:.2f}%")
    st.dataframe(view, width="stretch", hide_index=True)
    data_source("ridge_logit_customer_specific_report_*.xlsx", "Product_Summary 工作表；商品屬性補充自 正交設計_產品組合.xlsx")

    fig = px.scatter(df, x="Mean_Predicted_Probability", y="Actual_Purchase_Rate", size="Actual_Purchase_Count", color="Strategy_Tag", hover_name="Product_Label", labels={"Mean_Predicted_Probability": "平均預測購買機率(%)", "Actual_Purchase_Rate": "實際購買率(%)"}, title="商品推廣優先順序矩陣")
    st.plotly_chart(fig, width="stretch")
    term_box()


def product_promotion_page():
    st.header("產品推廣｜廣告與效益試算")
    products = load_product_summary()
    if products.empty:
        st.info("目前找不到產品分析資料。")
        return
    st.markdown("本頁不是精算真實利潤，而是讓行銷人員快速評估：若投入曝光與廣告預算，哪個商品比較值得測試。因目前沒有真實成本，因此毛利率採假設值。")
    product_options = products.sort_values("Actual_Purchase_Rate", ascending=False)["Product_Label"].tolist()
    selected_label = st.selectbox("選擇要推廣的商品組合", product_options)
    product = products[products["Product_Label"] == selected_label].iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    exposure = col1.number_input("預計曝光人數", min_value=100, max_value=200000, value=10000, step=500)
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

    st.markdown("""
    <div class="vv-note"><b>公式：</b><br>
    預估購買數 = 曝光人數 × 商品購買率 × 轉換率調整係數<br>
    預估營收 = 預估購買數 × 售價<br>
    預估毛利 = 預估營收 × 假設毛利率<br>
    推廣後淨效益 = 預估毛利 − 廣告成本<br>
    ROAS = 預估營收 ÷ 廣告成本</div>
    """, unsafe_allow_html=True)
    if roas is not None:
        st.markdown(f"<div class='vv-action'><b>ROAS 試算：</b>{roas:.2f}。這代表每 1 元廣告成本可帶來約 {roas:.2f} 元營收；但是否賺錢仍需搭配真實成本確認。</div>", unsafe_allow_html=True)

    scenario = products.sort_values("Actual_Purchase_Rate", ascending=False).head(5).copy()
    scenario["預估購買數"] = exposure * (scenario["Actual_Purchase_Rate"] / 100) * rate_adjust
    scenario["預估營收"] = scenario["預估購買數"] * scenario["Price"]
    scenario["預估毛利"] = scenario["預估營收"] * margin_rate
    fig = px.bar(scenario, x="Product_Label", y="預估營收", color="Strategy_Tag", title="同樣曝光下 Top 商品營收試算", labels={"Product_Label": "產品組合"})
    fig.update_layout(xaxis_tickangle=-25, height=520)
    st.plotly_chart(fig, width="stretch")
    data_source("ridge_logit_customer_specific_report_*.xlsx", "購買率與售價；毛利率與廣告成本為使用者輸入假設")


def recommendation_page():
    st.header("顧客推薦｜一對一行銷與 AI 素材")
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
    cust = cust.merge(products[["Product_Row", "Product_Label", "Brand", "Price", "Color", "Spec_Display", "GPS_Display", "Strategy_Tag"]], on="Product_Row", how="left")
    cust = cust.sort_values("Predicted_Probability", ascending=False)
    best = cust.iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("最佳推薦商品", best["Product_Label"])
    c2.metric("預測購買機率", f"{best['Predicted_Probability']*100:.2f}%")
    if not rfm.empty and selected in set(rfm["Customer_ID"].astype(str)):
        seg = rfm[rfm["Customer_ID"].astype(str) == selected].iloc[0]
        c3.metric("RFM 分群", str(seg.get("RFM_Label", "未標示"))[:18])
    else:
        c3.metric("RFM 分群", "未對接")

    display = cust[["Product_Row", "Product_Label", "Predicted_Probability", "Strategy_Tag"]].copy()
    display["Predicted_Probability"] = display["Predicted_Probability"].map(lambda x: f"{x*100:.2f}%")
    st.dataframe(display, width="stretch", hide_index=True)
    data_source("ridge_logit_customer_specific_report_*.xlsx", "Recommendation_Top5 工作表")

    st.subheader("可直接交給 AI 設計工具的素材草稿")
    edmsg = f"根據您的商品偏好，我們推薦 {best['Brand']} 的 {best['Color']}、{best['Spec_Display']} 款式。這款商品可降低規格選錯風險，適合需要穩定安裝與清楚規格的買家。"
    amazon_bullets = f"1. 清楚標示 {best['Spec_Display']}，降低買錯規格風險\n2. {best['GPS_Display']}，適合明確功能需求買家\n3. {best['Color']}外觀，適合車內搭配\n4. 適合替換與 DIY 安裝情境\n5. 建議搭配規格確認圖與安裝前檢查表"
    image_prompt = f"Create a professional Amazon product image for an automotive gauge. Show a {best['Color']} gauge installed in a car dashboard, with clean callout labels for {best['Spec_Display']}, fitment guide, and easy installation. Minimal, premium, technical style."
    video_script = f"3秒痛點：買錯規格很麻煩。5秒解法：{best['Brand']} 提供清楚 {best['Spec_Display']} 與安裝確認。3秒行動：立即查看適合你的儀表款式。"
    tabs = st.tabs(["EDM 文案", "Amazon 五點描述", "AI 圖片 Prompt", "短影音腳本"])
    tabs[0].text_area("EDM / 再行銷文案", edmsg, height=130)
    tabs[1].text_area("Amazon Bullet Points", amazon_bullets, height=170)
    tabs[2].text_area("可貼到 Canva / Firefly / AI 圖像工具", image_prompt, height=150)
    tabs[3].text_area("可貼到 CapCut / 短影音腳本工具", video_script, height=130)


def customer_list_page():
    st.header("顧客名單｜RFM／CAI 行銷策略")
    rfm = load_rfm()
    if rfm.empty:
        st.info("目前找不到 RFM／CAI 資料。")
        return
    st.markdown("名單本身沒有價值，必須轉成行銷動作。本頁提供不同顧客價值分群的經營方式。")
    strategy_df = pd.DataFrame([
        ["高價值／活躍顧客", "提高回購與客單", "新品預告、會員專屬優惠、高單價款推薦", "EDM、會員訊息、再行銷名單"],
        ["潛力顧客", "促成首次或二次購買", "規格指南、商品比較、熱門款推薦", "EDM、商品頁推薦、搜尋廣告"],
        ["價格敏感顧客", "用誘因提高轉換", "折扣券、免運、組合價、限時優惠", "促銷頁、再行銷廣告"],
        ["沉睡顧客", "喚回互動", "回購券、熱門商品、評論佳商品", "再行銷廣告、喚回 EDM"],
        ["資料不足顧客", "先蒐集偏好", "推通用高購買率商品、觀察點擊與收藏", "EDM 測試、站內推薦"],
    ], columns=["顧客類型", "行銷目標", "建議做法", "建議通路"])
    st.dataframe(strategy_df, width="stretch", hide_index=True)

    counts = rfm["RFM_Label"].value_counts().reset_index()
    counts.columns = ["RFM_Label", "Customer_Count"]
    fig = px.bar(counts, x="Customer_Count", y="RFM_Label", orientation="h", title="RFM 顧客價值分群人數")
    fig.update_layout(height=520, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, width="stretch")
    data_source("RFM_CAI 統整.xlsx", "RFM 與 CAI 顧客標籤")

    selected = st.selectbox("選擇分群查看名單", counts["RFM_Label"].tolist())
    seg = rfm[rfm["RFM_Label"] == selected].copy()
    st.dataframe(seg.head(200), width="stretch", hide_index=True)


def review_insights_page():
    st.header("評論洞察｜痛點與 Listing 改善")
    reviews = load_reviews_detail()
    summary = load_reviews_summary()
    if reviews.empty:
        st.info("目前找不到評論資料。")
        return
    avg_rating = reviews["Rating"].mean()
    positive_rate = (reviews["Sentiment_Label"].astype(str).str.contains("正|Positive", regex=True).mean() * 100)
    usable = reviews[reviews["Motivation_Type"] != "未明確判讀"].copy()
    top_mot = usable["Motivation_Type"].mode().iloc[0] if not usable.empty and not usable["Motivation_Type"].mode().empty else "資料不足"
    c1, c2, c3 = st.columns(3)
    c1.metric("平均評分", f"{avg_rating:.2f}")
    c2.metric("正向評論占比", f"{positive_rate:.1f}%")
    c3.metric("主要可用動機", top_mot)

    st.markdown("""
    <div class="vv-note"><b>分類說明：</b>「未明確判讀」不作為主要市場區隔，只代表該評論沒有足夠明確的行銷訊號。正式策略會優先使用規格適配、功能可靠、品質信任、外觀搭配與價格敏感等可行動分類。</div>
    """, unsafe_allow_html=True)
    mot = usable["Motivation_Type"].value_counts().reset_index()
    mot.columns = ["Motivation_Type", "Review_Count"]
    fig = px.bar(mot, x="Review_Count", y="Motivation_Type", orientation="h", title="可行動評論動機分布")
    fig.update_layout(height=420, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, width="stretch")
    data_source("reviews_processed_classified.csv", "評論文字與星等整理後的顧客動機分類")

    st.subheader("評論痛點 → Amazon Listing 改善做法")
    pain_df = pd.DataFrame([
        ["規格不清楚", "商品圖與五點描述", "加入 NPT / SAE 規格對照表、尺寸圖、適用情境與安裝前確認清單"],
        ["安裝不確定", "圖片區、FAQ、A+ Content", "用三步驟安裝圖說明如何確認規格，降低退貨風險"],
        ["功能可靠疑慮", "主圖、影片、五點描述", "補充讀數穩定、GPS 功能、測試情境與使用後效果"],
        ["品質信任不足", "評論摘要、保固說明", "整理高分評論關鍵句，搭配保固、材質與包裝說明"],
        ["外觀搭配困難", "情境圖與顏色比較", "補上黑色、米色、白色等車內實裝圖與比較圖"],
        ["價格敏感", "促銷與組合包", "提供組合價、免運、限時折扣，並說明價格對應的功能價值"],
    ], columns=["評論痛點", "應改善的位置", "具體作法"])
    st.dataframe(pain_df, width="stretch", hide_index=True)

    if not summary.empty:
        st.subheader("ASIN 商品評論摘要")
        st.dataframe(summary.sort_values("Review_Count", ascending=False), width="stretch", hide_index=True)
        data_source("reviews_summary_processed.csv", "依 ASIN 彙整評論數、平均星等與正負評")


pages = {
    "首頁｜總覽與操作手冊": overview_page,
    "市場區隔｜顧客偏好族群": market_segmentation_page,
    "目標市場｜技詮優先客群": target_market_page,
    "產品定位｜技詮如何被記住": positioning_page,
    "商品策略｜主推與檢討清單": product_strategy_page,
    "產品推廣｜廣告與效益試算": product_promotion_page,
    "顧客推薦｜一對一行銷與 AI 素材": recommendation_page,
    "顧客名單｜RFM/CAI 策略": customer_list_page,
    "評論洞察｜痛點與 Listing 改善": review_insights_page,
}

with st.sidebar:
    st.title("VivaVictors")
    st.caption("Marketing Dashboard")
    selected_page = st.radio("選擇功能", list(pages.keys()))
    st.divider()
    st.markdown("**日常使用重點**")
    st.caption("先決定目標客群，再決定主推商品與廣告素材。")
    st.divider()
    if st.button("清除快取後重新整理"):
        st.cache_data.clear()
        st.rerun()

pages[selected_page]()
