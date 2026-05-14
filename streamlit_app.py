from pathlib import Path
from datetime import datetime
import json

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


SOURCE_ITEMS = [
    ("KMeans_Final_Result.xlsx", "市場區隔與目標市場排序", "用 28 種產品偏好原型判斷三種可行銷客群。"),
    ("ridge_logit_customer_specific_report_*.xlsx", "購買率與推薦模型", "提供 Product_Summary 與每位顧客 Top 5 推薦。"),
    ("正交設計_產品組合.xlsx", "產品屬性對照", "對應品牌、價格、顏色、規格、GPS 與 ASIN。"),
    ("RFM_CAI 統整.xlsx", "顧客名單策略", "用於顧客價值標籤、CAI 分群與名單經營。"),
    ("reviews_processed_classified.csv", "評論痛點與動機", "用評論內容判讀功能、規格、品質、外觀與價格需求。"),
    ("reviews_summary_processed.csv", "ASIN 評論摘要", "彙整各商品評論數、平均星等與正負評。"),
]

GLOSSARY_ITEMS = [
    ("NPT / SAE-NPT", "螺紋或安裝規格。對行銷人員來說，重點是買家要能快速確認是否買對、能否安裝。"),
    ("購買率", "某產品組合在資料中被購買的比例，可作為主推優先順序參考。"),
    ("立即主推", "表現較好，適合優先放大曝光、投放廣告或放入 EDM 主推。"),
    ("優先測試", "有潛力但不宜一次加大預算，建議先做 A/B Test。"),
    ("維持觀察", "表現普通，維持基本曝光與自然流量，不急著加預算。"),
    ("需要檢討", "先檢查價格、圖片、規格說明、評論痛點或是否暫緩推廣。"),
    ("準個人化行銷", "不是每人一支廣告，而是依客群、推薦商品與偏好分配素材、話術與優惠。"),
]

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

[data-testid="stSidebar"] .stRadio label {
    white-space: pre-line !important;
    align-items: flex-start !important;
    padding: .55rem .65rem !important;
    border-radius: .85rem !important;
    margin: .08rem 0 !important;
    border: 1px solid rgba(148, 163, 184, .18);
}
[data-testid="stSidebar"] .stRadio label p {
    white-space: pre-line !important;
    line-height: 1.28 !important;
    font-size: .88rem !important;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(148, 163, 184, .10) !important;
}
.vv-side-block {padding:.65rem .7rem; border:1px solid rgba(148,163,184,.25); border-radius:.8rem; margin:.45rem 0; background:rgba(148,163,184,.06); overflow-wrap:anywhere; word-break:break-word;}
.vv-side-title {font-weight:700; font-size:.86rem; line-height:1.25; display:block; margin-bottom:.18rem;}
.vv-side-body {font-size:.78rem; line-height:1.35; opacity:.86; display:block;}
.vv-tag {font-size:.68rem; padding:.1rem .35rem; border-radius:999px; background:rgba(37,99,235,.12); color:#1d4ed8; margin-right:.25rem;}

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



def infer_marketing_route(row) -> str:
    """Translate product preference into a practical marketing content route."""
    brand = str(row.get("Brand", "")).lower()
    spec = str(row.get("Spec_Display", row.get("Spec", ""))).lower()
    color = str(row.get("Color", "")).lower()
    gps = str(row.get("GPS_Display", row.get("GPS", "")))
    price = float(row.get("Price", 0) or 0)
    if "motor" in brand or "npt" in spec:
        return "技術規格型"
    if any(c in color for c in ["米", "藍", "beige", "blue"]):
        return "風格美學型"
    if "有 gps" in gps.lower() or "gps" in gps.lower():
        return "實用功能型"
    if price and price <= 206:
        return "價格誘因型"
    return "主流實用型"


def creative_package(route: str) -> dict:
    packages = {
        "技術規格型": {
            "video": "影片A：技術規格／安裝確認",
            "copy": "規格清楚、安裝更安心、降低買錯風險",
            "channel": "Amazon Listing、搜尋廣告、EDM 技術型內容",
            "image_style": "深色背景、規格標籤、安裝細節、專業工具感",
        },
        "實用功能型": {
            "video": "影片B：實用功能／日常使用",
            "copy": "功能完整、使用直覺、適合日常替換與升級",
            "channel": "Meta 再行銷、EDM、Amazon Sponsored Products",
            "image_style": "實裝情境、功能 icon、GPS 或功能重點 callout",
        },
        "風格美學型": {
            "video": "影片C：車內風格／顏色搭配",
            "copy": "不只可用，也要搭配你的車內風格",
            "channel": "IG/Meta 視覺素材、Amazon 圖片區、A+ Content",
            "image_style": "車內情境、內裝搭配、色系比較、質感光影",
        },
        "價格誘因型": {
            "video": "影片D：限時優惠／高 CP 值",
            "copy": "用更低門檻完成替換，限時優惠降低猶豫成本",
            "channel": "促銷 EDM、再行銷廣告、優惠券受眾",
            "image_style": "促銷標籤、價格比較、限時感、免運或折扣提示",
        },
        "主流實用型": {
            "video": "影片B：實用功能／日常使用",
            "copy": "主流款式、穩定可靠、適合多數替換需求",
            "channel": "Amazon 主推頁、搜尋廣告、EDM 熱門商品區",
            "image_style": "乾淨商品圖、黑白主流款比較、功能重點",
        },
    }
    return packages.get(route, packages["主流實用型"])


def offer_tier(probability: float, strategy_tag: str = "", rfm_label: str = "") -> tuple[str, str]:
    """Suggest incentive strength without claiming exact willingness-to-pay."""
    p = float(probability or 0)
    label = str(rfm_label)
    tag = str(strategy_tag)
    if p >= 0.38 and "高" in label:
        return "無折扣／會員感訊息", "購買意願高，先用新品、品質與規格信任溝通，不急著讓利。"
    if p >= 0.32:
        return "低誘因：0–5% 或免運", "顧客已有明顯偏好，用小誘因或免運推動即可。"
    if p >= 0.22:
        return "中誘因：5–10%", "需要一點促銷刺激，適合搭配限時優惠或組合包。"
    if "需要檢討" in tag:
        return "暫緩折扣，先修 Listing", "商品本身轉換表現偏弱，優先改善頁面與素材，不建議直接砸折扣。"
    return "強誘因：10–15% 或清庫存券", "購買意願較低，若有庫存壓力可用較強誘因測試喚回。"


def build_campaign_audience(recs: pd.DataFrame, products: pd.DataFrame, rfm: pd.DataFrame) -> pd.DataFrame:
    """Create a practical audience table from top-1 recommendation for each customer."""
    if recs.empty or products.empty:
        return pd.DataFrame()
    base = recs.sort_values(["Customer_ID", "Predicted_Probability"], ascending=[True, False]).groupby("Customer_ID", as_index=False).first()
    cols = ["Product_Row", "Product_Label", "Brand", "Price", "Color", "Spec_Display", "GPS_Display", "Strategy_Tag"]
    base = base.merge(products[[c for c in cols if c in products.columns]], on="Product_Row", how="left")
    if not rfm.empty and "Customer_ID" in rfm.columns:
        rfm_cols = [c for c in ["Customer_ID", "RFM_Label", "CAI_Label"] if c in rfm.columns]
        base = base.merge(rfm[rfm_cols].drop_duplicates("Customer_ID"), on="Customer_ID", how="left")
    base["行銷素材路線"] = base.apply(infer_marketing_route, axis=1)
    base["建議影片素材"] = base["行銷素材路線"].map(lambda x: creative_package(x)["video"])
    base["核心話術"] = base["行銷素材路線"].map(lambda x: creative_package(x)["copy"])
    base["建議通路"] = base["行銷素材路線"].map(lambda x: creative_package(x)["channel"])
    offer = base.apply(lambda r: offer_tier(r.get("Predicted_Probability", 0), r.get("Strategy_Tag", ""), r.get("RFM_Label", "")), axis=1)
    base["優惠級距"] = [x[0] for x in offer]
    base["優惠理由"] = [x[1] for x in offer]
    base["預測購買機率(%)"] = base["Predicted_Probability"] * 100
    return base


def campaign_copy_templates(route: str, product_row: pd.Series, offer: str = "") -> dict:
    pkg = creative_package(route)
    brand = product_row.get("Brand", "本商品")
    color = product_row.get("Color", "")
    spec = product_row.get("Spec_Display", product_row.get("Spec", "規格"))
    gps = product_row.get("GPS_Display", "")
    product_name = product_row.get("Product_Label", f"{brand} {color} {spec}")
    offer_text = f"本次建議優惠：{offer}。" if offer else ""
    return {
        "EDM 主旨": f"為你的安裝需求挑選：{brand} {spec} 推薦款",
        "EDM 內文": f"我們依據你的商品偏好，推薦 {product_name}。這款商品主打 {pkg['copy']}。{offer_text}建議先確認規格，再完成下單，降低跨境購買後不相容的風險。",
        "Meta/IG 廣告文案": f"怕買錯儀表規格？{brand} {spec} 款式幫你把安裝重點講清楚。{pkg['copy']}，現在就查看適合你的款式。",
        "Amazon 五點描述": f"1. 清楚標示 {spec}，降低買錯規格風險\n2. {gps}，讓功能需求更清楚\n3. {color}外觀，適合車內搭配\n4. 適合替換與 DIY 安裝情境\n5. 建議搭配尺寸圖、規格對照表與安裝確認清單",
        "AI 圖片 Prompt": f"Create a professional Amazon product image for an automotive gauge. Show a {color} gauge installed in a car dashboard. Add clean callout labels for {spec}, fitment guide, and easy installation. Style: {pkg['image_style']}. Premium, realistic, conversion-focused.",
        "短影音腳本": f"3秒痛點：買錯規格很麻煩。5秒解法：用清楚的 {spec} 與安裝確認降低風險。5秒展示：{brand} {color} 儀表實裝與功能重點。3秒 CTA：立即查看適合你的款式。",
    }

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
        ["6 準個人化行銷", "批次分配素材、優惠與投放通路，也可保留 Customer_ID 查詢", "執行 EDM、再行銷、AI 素材與 A/B 測試"],
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



def _norm_score(value: float, min_v: float, max_v: float) -> float:
    """Normalize a metric to 0-100. If min/max are identical, return 60 as neutral."""
    try:
        value = float(value)
        min_v = float(min_v)
        max_v = float(max_v)
    except Exception:
        return 0.0
    if max_v == min_v:
        return 60.0
    return max(0.0, min(100.0, (value - min_v) / (max_v - min_v) * 100))


def _get_segment_products(products: pd.DataFrame, cluster: int) -> pd.DataFrame:
    """Approximate product mapping for each target segment using product attributes.
    This does not overwrite the original KMeans result; it translates segment meaning into
    products that marketers can actually promote.
    """
    if products.empty:
        return pd.DataFrame()
    brand = products.get("Brand", pd.Series("", index=products.index)).astype(str).str.lower()
    spec = products.get("Spec_Display", products.get("Spec", pd.Series("", index=products.index))).astype(str).str.lower()
    color = products.get("Color", pd.Series("", index=products.index)).astype(str)
    gps = products.get("GPS_Display", products.get("GPS", pd.Series("", index=products.index))).astype(str).str.lower()

    if cluster == 1:
        mask = brand.str.contains("motor", na=False) | spec.str.contains("npt", na=False)
    elif cluster == 2:
        mask = (
            brand.str.contains("dolphin|faria|speedway", na=False)
            | gps.str.contains("gps", na=False)
            | color.isin(["黑色", "白色", "黃色", "綠色", "black", "white", "yellow", "green"])
        )
    elif cluster == 3:
        mask = color.isin(["米色", "藍色", "beige", "blue"])
    else:
        mask = pd.Series(False, index=products.index)
    subset = products[mask].copy()
    return subset if not subset.empty else products.copy()


def build_target_market_scores(weights: dict) -> pd.DataFrame:
    """Create an evidence-based target market ranking table.
    Scores are intentionally transparent and adjustable. They combine market segment size,
    product performance, product fit, review pain clarity, promotion feasibility and benefit potential.
    """
    _, segment_summary, source_name = load_market_segments()
    products = load_product_summary()
    reviews = load_reviews_detail()

    rows = []
    # Fallback if the cluster summary is missing.
    if segment_summary.empty:
        segment_summary = pd.DataFrame({"Cluster": [1, 2, 3], "Customer_Count": [0, 0, 0], "Share": [0, 0, 0]})

    count_min = float(segment_summary.get("Customer_Count", pd.Series([0])).min())
    count_max = float(segment_summary.get("Customer_Count", pd.Series([1])).max())

    # Product performance base for normalization.
    product_perf_values = []
    revenue_potential_values = []
    for cluster in [1, 2, 3]:
        subset = _get_segment_products(products, cluster)
        product_perf_values.append(float(subset.get("Actual_Purchase_Rate", pd.Series([0])).mean() if not subset.empty else 0))
        revenue_potential_values.append(float((subset.get("Actual_Purchase_Rate", pd.Series([0])) * subset.get("Price", pd.Series([0]))).mean() if not subset.empty else 0))
    perf_min, perf_max = min(product_perf_values), max(product_perf_values)
    rev_min, rev_max = min(revenue_potential_values), max(revenue_potential_values)

    # Review evidence: not perfectly linked to clusters, so this is a strategy-level proxy.
    review_mot = reviews.get("Motivation_Type", pd.Series(dtype=str)).astype(str) if not reviews.empty else pd.Series(dtype=str)
    review_text = reviews.get("Review_Text", pd.Series(dtype=str)).astype(str) if not reviews.empty else pd.Series(dtype=str)
    def review_signal(cluster: int) -> float:
        if reviews.empty:
            return 60.0
        if cluster == 1:
            keywords = ["規格", "適配", "NPT", "Sae", "安裝", "功能", "可靠"]
        elif cluster == 2:
            keywords = ["價格", "CP", "GPS", "品牌", "實用", "功能", "品質"]
        else:
            keywords = ["外觀", "顏色", "美學", "內裝", "beige", "blue", "搭配"]
        joined = (review_mot + " " + review_text).str.lower()
        hits = sum(joined.str.contains(str(k).lower(), regex=False, na=False).sum() for k in keywords)
        return min(100.0, 45.0 + hits / max(len(reviews), 1) * 200.0)

    # Manual feasibility reflects how easy it is to execute with current assets.
    feasibility = {1: 76.0, 2: 90.0, 3: 72.0}
    product_fit_manual = {1: 88.0, 2: 92.0, 3: 70.0}

    for cluster in [1, 2, 3]:
        cfg = SEGMENT_CONFIG.get(cluster, {})
        seg_row = segment_summary[segment_summary["Cluster"].astype(int) == cluster]
        raw_count = float(seg_row["Customer_Count"].iloc[0]) if not seg_row.empty and "Customer_Count" in seg_row.columns else 0.0
        share = float(seg_row["Share"].iloc[0]) if not seg_row.empty and "Share" in seg_row.columns else 0.0
        subset = _get_segment_products(products, cluster)
        purchase_rate = float(subset.get("Actual_Purchase_Rate", pd.Series([0])).mean() if not subset.empty else 0)
        revenue_proxy = float((subset.get("Actual_Purchase_Rate", pd.Series([0])) * subset.get("Price", pd.Series([0]))).mean() if not subset.empty else 0)
        product_count = int(subset.get("Product_Row", pd.Series(dtype=int)).nunique() if not subset.empty else 0)

        metrics = {
            "市場規模": _norm_score(raw_count, count_min, count_max),
            "購買表現": _norm_score(purchase_rate, perf_min, perf_max),
            "商品匹配度": product_fit_manual.get(cluster, 70.0),
            "評論痛點明確度": review_signal(cluster),
            "推廣可執行性": feasibility.get(cluster, 70.0),
            "效益潛力": _norm_score(revenue_proxy, rev_min, rev_max),
        }
        total_score = sum(metrics[k] * weights.get(k, 0) for k in metrics)
        rows.append({
            "目標市場": cfg.get("name", f"第{cluster}群"),
            "行銷名稱": cfg.get("business_name", "未命名客群"),
            "主要需求": cfg.get("need", ""),
            "資料群別": f"偏好族群 {cluster}",
            "產品原型數": int(raw_count),
            "占比": f"{share:.1f}%",
            "對應商品數": product_count,
            "平均購買率": f"{purchase_rate:.2f}%",
            "市場規模": round(metrics["市場規模"], 1),
            "購買表現": round(metrics["購買表現"], 1),
            "商品匹配度": round(metrics["商品匹配度"], 1),
            "評論痛點明確度": round(metrics["評論痛點明確度"], 1),
            "推廣可執行性": round(metrics["推廣可執行性"], 1),
            "效益潛力": round(metrics["效益潛力"], 1),
            "決策分數": round(total_score, 1),
            "建議訊息": cfg.get("message", ""),
            "落地做法": cfg.get("landing", ""),
            "資料來源": f"{source_name}；ridge_logit_customer_specific_report；reviews_processed_classified",
        })
    df = pd.DataFrame(rows).sort_values("決策分數", ascending=False).reset_index(drop=True)
    df["排名"] = range(1, len(df) + 1)
    return df[["排名", "目標市場", "行銷名稱", "決策分數", "產品原型數", "占比", "對應商品數", "平均購買率", "市場規模", "購買表現", "商品匹配度", "評論痛點明確度", "推廣可執行性", "效益潛力", "建議訊息", "落地做法", "資料來源"]]


def preset_weights(preset: str) -> dict:
    presets = {
        "短期衝銷售": {"市場規模": .20, "購買表現": .30, "商品匹配度": .15, "評論痛點明確度": .10, "推廣可執行性": .20, "效益潛力": .05},
        "建立專業品牌": {"市場規模": .10, "購買表現": .15, "商品匹配度": .25, "評論痛點明確度": .25, "推廣可執行性": .15, "效益潛力": .10},
        "清庫存與促銷": {"市場規模": .25, "購買表現": .20, "商品匹配度": .10, "評論痛點明確度": .10, "推廣可執行性": .15, "效益潛力": .20},
        "差異化內容行銷": {"市場規模": .10, "購買表現": .10, "商品匹配度": .20, "評論痛點明確度": .30, "推廣可執行性": .20, "效益潛力": .10},
        "自訂權重": {"市場規模": .20, "購買表現": .25, "商品匹配度": .20, "評論痛點明確度": .15, "推廣可執行性": .15, "效益潛力": .05},
    }
    return presets.get(preset, presets["自訂權重"]).copy()


def decision_filename(suffix: str) -> str:
    return f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{suffix}"


def target_market_page():
    st.header("目標市場｜可調整決策工具")
    st.markdown(
        "本頁不是直接給固定答案，而是把市場區隔、商品表現、評論痛點與推廣可行性轉成可調整的目標市場排序。行銷人員可以依不同策略情境調整權重，保留本次判斷紀錄，未來再比較成效。"
    )
    st.subheader("1｜選擇策略情境與決策權重")
    col_preset, col_note = st.columns([1, 2])
    with col_preset:
        preset = st.selectbox(
            "策略情境",
            ["短期衝銷售", "建立專業品牌", "清庫存與促銷", "差異化內容行銷", "自訂權重"],
            index=0,
            help="不同情境會影響目標市場排序。例如短期衝銷售會提高購買表現與推廣可行性權重；建立專業品牌會提高商品匹配度與評論痛點權重。",
        )
    with col_note:
        st.markdown(
            "<div class='vv-note'><b>判讀原則：</b>目標市場不是憑一句話決定，而是由市場規模、購買表現、商品匹配、評論痛點、推廣可執行性與效益潛力共同評估。權重可以依老闆策略、庫存壓力或市場時事調整。</div>",
            unsafe_allow_html=True,
        )

    base = preset_weights(preset)
    st.caption("權重合計會自動正規化成 100%，因此你可以依策略重要性調整，不需要手動算總和。")
    w_cols = st.columns(3)
    raw_weights = {}
    labels = list(base.keys())
    for i, metric in enumerate(labels):
        with w_cols[i % 3]:
            raw_weights[metric] = st.slider(metric, min_value=0, max_value=50, value=int(base[metric] * 100), step=5)
    total_raw = sum(raw_weights.values()) or 1
    weights = {k: v / total_raw for k, v in raw_weights.items()}

    score_df = build_target_market_scores(weights)
    if score_df.empty:
        st.warning("目前無法讀取分群或商品資料，請確認 data/ 資料夾是否包含 KMeans_Final_Result.xlsx 與模型輸出檔。")
        return

    best = score_df.iloc[0]
    second = score_df.iloc[1] if len(score_df) > 1 else None
    third = score_df.iloc[2] if len(score_df) > 2 else None

    st.subheader("2｜目前權重下的目標市場建議")
    k1, k2, k3 = st.columns(3)
    k1.metric("第一優先", str(best["目標市場"]), f"決策分數 {best['決策分數']}/100")
    if second is not None:
        k2.metric("第二優先", str(second["目標市場"]), f"決策分數 {second['決策分數']}/100")
    if third is not None:
        k3.metric("第三優先", str(third["目標市場"]), f"決策分數 {third['決策分數']}/100")

    st.markdown(
        f"""
        <div class="vv-action">
        <b>目前建議：</b>在「{preset}」情境下，系統建議優先鎖定 <b>{best['目標市場']}</b>。<br>
        主要原因是此客群在目前權重設定下，於市場規模、商品對應、購買表現或推廣可行性等指標的綜合分數最高。這不是固定結論；如果策略改為品牌建立、清庫存或差異化內容，排序可能改變。
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("3｜數據證據表：為什麼是這個客群？")
    display_cols = ["排名", "目標市場", "行銷名稱", "決策分數", "產品原型數", "占比", "對應商品數", "平均購買率", "市場規模", "購買表現", "商品匹配度", "評論痛點明確度", "推廣可執行性", "效益潛力"]
    st.dataframe(score_df[display_cols], width="stretch", hide_index=True)
    data_source("KMeans_Final_Result.xlsx + ridge_logit_customer_specific_report_*.xlsx + reviews_processed_classified.csv", "分群、商品表現與評論痛點共同計算；本頁權重可由使用者調整")

    fig = px.bar(
        score_df.sort_values("決策分數", ascending=True),
        x="決策分數",
        y="目標市場",
        orientation="h",
        color="目標市場",
        title="目標市場優先排序｜依目前權重計算",
        text="決策分數",
    )
    fig.update_layout(height=420, showlegend=False)
    st.plotly_chart(fig, width="stretch")

    with st.expander("評分公式與權重說明", expanded=False):
        st.markdown(
            """
            **目標市場優先分數 =**  
            市場規模 × 權重 + 購買表現 × 權重 + 商品匹配度 × 權重 + 評論痛點明確度 × 權重 + 推廣可執行性 × 權重 + 效益潛力 × 權重

            - **市場規模：**來自分群結果中的產品偏好原型數與占比。
            - **購買表現：**對應商品組合的平均購買率。
            - **商品匹配度：**技詮現有商品是否容易服務該客群。
            - **評論痛點明確度：**評論中是否能明確找到規格、功能、外觀、價格等可操作痛點。
            - **推廣可執行性：**是否能轉成 Amazon Listing、EDM、再行銷廣告或素材腳本。
            - **效益潛力：**以購買率與售價作為初步推廣潛力 proxy；若未來有真實成本，可升級為毛利或 ROI。
            """
        )
        weight_df = pd.DataFrame({"指標": list(weights.keys()), "目前權重": [f"{v*100:.1f}%" for v in weights.values()]})
        st.dataframe(weight_df, width="stretch", hide_index=True)

    st.subheader("4｜落地行銷建議")
    action_cols = ["目標市場", "建議訊息", "落地做法"]
    st.dataframe(score_df[action_cols], width="stretch", hide_index=True)

    st.subheader("5｜下載本次決策紀錄")
    record_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record_df = score_df.copy()
    record_df.insert(0, "決策時間", record_time)
    record_df.insert(1, "策略情境", preset)
    for metric, value in weights.items():
        record_df[f"權重_{metric}"] = round(value, 4)

    csv_data = record_df.to_csv(index=False, encoding="utf-8-sig")
    json_data = json.dumps(
        {
            "decision_time": record_time,
            "strategy_preset": preset,
            "weights": {k: round(v, 4) for k, v in weights.items()},
            "ranking": score_df[["排名", "目標市場", "決策分數"]].to_dict(orient="records"),
        },
        ensure_ascii=False,
        indent=2,
    )
    d1, d2 = st.columns(2)
    d1.download_button(
        "下載 CSV 決策紀錄",
        data=csv_data,
        file_name=decision_filename("target_market_decision_record.csv"),
        mime="text/csv",
    )
    d2.download_button(
        "下載 JSON 權重設定",
        data=json_data,
        file_name=decision_filename("target_market_weight_setting.json"),
        mime="application/json",
    )
    st.caption("檔名會自動使用 YYYYMMDD_HHMMSS 開頭，方便與 Excel 版本一樣留存、回溯與比較。")



def segment_name_to_id(name: str) -> int:
    for sid, cfg in SEGMENT_CONFIG.items():
        if cfg.get("name") == name:
            return sid
    return 2


def default_target_segment_id() -> int:
    try:
        scores = build_target_market_scores(preset_weights("短期衝銷售"))
        if not scores.empty:
            return segment_name_to_id(str(scores.iloc[0]["目標市場"]))
    except Exception:
        pass
    return 2


def segment_options_with_default(label: str = "套用目標市場"):
    options = [SEGMENT_CONFIG[sid]["name"] for sid in sorted(SEGMENT_CONFIG)]
    default_sid = st.session_state.get("current_target_segment_id", default_target_segment_id())
    default_name = SEGMENT_CONFIG.get(default_sid, SEGMENT_CONFIG[2])["name"]
    index = options.index(default_name) if default_name in options else 1
    selected_name = st.selectbox(
        label,
        options,
        index=index,
        help="這裡可手動切換目標市場，用來檢視不同客群下的定位與商品策略；若已在目標市場頁調整權重，系統會優先帶入目前第一優先客群。",
    )
    sid = segment_name_to_id(selected_name)
    st.session_state["current_target_segment_id"] = sid
    return sid, SEGMENT_CONFIG[sid]


def positioning_profile(segment_id: int) -> dict:
    profiles = {
        1: {
            "pain": "怕買錯 NPT / SAE 規格、怕安裝不合、重視性能與儀表穩定度。",
            "value": "用清楚規格、安裝確認與性能語境，讓專業買家快速判斷是否符合需求。",
            "positioning": "面向改裝與專業使用者的精準規格與性能感儀表選購品牌。",
            "claim": "精準規格、穩定性能，讓改裝與維修更有把握。",
            "listing_focus": "NPT / SAE 規格對照、安裝情境、性能與耐用性說明。",
            "ad_angle": "規格買對、性能穩定、Racing 風格。",
        },
        2: {
            "pain": "希望商品可靠、價格合理、功能實用，並降低跨境購買風險。",
            "value": "用主流款式、價格透明、GPS / 功能說明與評論佐證提升購買信心。",
            "positioning": "規格清楚、功能可靠、價格透明的高 CP 值汽車儀表選購夥伴。",
            "claim": "清楚規格、可靠功能，在合理價格中找到安心選擇。",
            "listing_focus": "主流黑白款、GPS 功能、價格與評論摘要、常見問題。",
            "ad_angle": "好理解、好比較、好下單的主流可靠選擇。",
        },
        3: {
            "pain": "除了規格與功能，也在意儀表是否能搭配車內色調與個人風格。",
            "value": "用特殊色系、情境實裝圖與風格比較，讓買家看到安裝後效果。",
            "positioning": "能搭配車內風格與個人品味的汽車儀表視覺方案。",
            "claim": "不只買得到能用的儀表，也能找到符合內裝風格的選擇。",
            "listing_focus": "米色、藍色等特殊色實裝圖、內裝搭配與顏色比較。",
            "ad_angle": "內裝搭配、色系質感、個性化風格。",
        },
    }
    return profiles.get(segment_id, profiles[2])


def product_positioning_fit(row, segment_id: int) -> float:
    brand = str(row.get("Brand", "")).lower()
    spec = str(row.get("Spec_Display", row.get("Spec", ""))).lower()
    color = str(row.get("Color", "")).lower()
    gps = str(row.get("GPS_Display", row.get("GPS", ""))).lower()
    price = float(row.get("Price", 0) or 0)
    score = 35
    if segment_id == 1:
        if "motor" in brand: score += 28
        if "npt" in spec: score += 25
        if "racing" in brand: score += 8
        if color in ["橘色", "黑色", "orange", "black"]: score += 4
    elif segment_id == 2:
        if any(b in brand for b in ["dolphin", "faria", "speedway"]): score += 18
        if "gps" in gps and "無" not in gps: score += 18
        if color in ["黑色", "白色", "黃色", "black", "white", "yellow"]: score += 16
        if price > 0: score += 10
        if "sae" in spec or "npt" in spec: score += 8
    elif segment_id == 3:
        if color in ["米色", "藍色", "beige", "blue"]: score += 42
        if color not in ["未標示", "黑色", "白色", "black", "white"]: score += 14
        if price > 0: score += 6
    return max(0, min(100, score))


def product_role(row, segment_id: int, rate_max: float) -> str:
    rate = float(row.get("Actual_Purchase_Rate", 0) or 0)
    fit = float(row.get("定位符合度", 0) or 0)
    color = str(row.get("Color", ""))
    price = float(row.get("Price", 0) or 0)
    rate_norm = 100 * rate / rate_max if rate_max else rate
    if rate < 2 or fit < 45:
        return "檢討改善商品"
    if rate_norm >= 75 and fit >= 70:
        return "主力轉換商品"
    if fit >= 85:
        return "定位證明商品"
    if segment_id == 3 or color in ["米色", "藍色", "beige", "blue"]:
        return "差異化商品"
    if segment_id == 2 or price > 0:
        return "流量導入商品"
    return "優先測試商品"


def product_role_action(role: str) -> str:
    mapping = {
        "主力轉換商品": "加大曝光，放入主推廣告、首頁推薦與 EDM 主商品。",
        "定位證明商品": "用於品牌定位、Amazon A+ Content、規格圖與案例素材。",
        "流量導入商品": "作為促銷入口或再行銷入口，用價格、主流款式或高 CP 值吸引點擊。",
        "差異化商品": "做情境圖、社群素材、顏色比較與風格內容。",
        "檢討改善商品": "暫緩加大預算，先檢查價格、圖片、規格說明與評論痛點。",
        "優先測試商品": "先用小額預算測素材、受眾與折扣，不直接大規模投放。",
    }
    return mapping.get(role, "依商品表現與定位符合度安排測試。")


def role_message(role: str, profile: dict) -> str:
    if role == "主力轉換商品":
        return profile["claim"]
    if role == "定位證明商品":
        return f"用來證明品牌定位：{profile['positioning']}"
    if role == "流量導入商品":
        return "以主流款式、價格透明與低風險選購作為點擊入口。"
    if role == "差異化商品":
        return "以視覺風格、色系搭配與情境圖建立差異化印象。"
    if role == "檢討改善商品":
        return "先補強圖片、規格表、FAQ 或價格說明，再決定是否投放。"
    return "小額測試不同素材與受眾，觀察點擊率與轉換率。"


def add_product_strategy_columns(df: pd.DataFrame, segment_id: int) -> pd.DataFrame:
    out = df.copy()
    rate_max = float(out["Actual_Purchase_Rate"].max() or 1)
    out["定位符合度"] = out.apply(lambda r: product_positioning_fit(r, segment_id), axis=1)
    out["購買表現分數"] = (out["Actual_Purchase_Rate"] / rate_max * 100).clip(0, 100)
    feasibility_map = {"立即主推": 95, "優先測試": 75, "維持觀察": 55, "需要檢討": 35, "資料不足": 30}
    out["推廣可執行性"] = out["Strategy_Tag"].map(feasibility_map).fillna(55)
    out["評論風險反向分數"] = 80
    out["商品策略分數"] = (
        out["購買表現分數"] * 0.40
        + out["定位符合度"] * 0.35
        + out["推廣可執行性"] * 0.15
        + out["評論風險反向分數"] * 0.10
    ).round(1)
    out["商品角色"] = out.apply(lambda r: product_role(r, segment_id, rate_max), axis=1)
    profile = positioning_profile(segment_id)
    out["建議行動"] = out["商品角色"].apply(product_role_action)
    out["推廣話術"] = out["商品角色"].apply(lambda role: role_message(role, profile))
    return out


def positioning_page():
    st.header("產品定位｜技詮如何被記住")
    st.markdown("本頁把上一頁的目標市場轉成產品定位。重點不是列出商品功能，而是說清楚：技詮要用什麼價值打動這群買家，以及這個定位如何落實到 Amazon Listing、EDM 與廣告素材。")

    seg_id, cfg = segment_options_with_default("套用目標市場")
    profile = positioning_profile(seg_id)
    st.markdown(
        f"""
        <div class="vv-action">
        <b>目前套用目標市場：</b>{cfg['name']}｜{cfg['business_name']}<br>
        <b>品牌總定位：</b>技詮以「規格透明、安裝安心、功能可靠」作為核心定位，並依不同目標市場調整商品頁與廣告訊息。<br>
        <b>本客群定位：</b>{profile['positioning']}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("1｜定位推導：從目標市場到產品主張")
    positioning_df = pd.DataFrame([
        ["目標客群", cfg["name"]],
        ["顧客核心痛點", profile["pain"]],
        ["技詮可提供的價值", profile["value"]],
        ["產品定位方向", profile["positioning"]],
        ["可放入簡報的定位句", profile["claim"]],
    ], columns=["推導項目", "內容"])
    st.dataframe(positioning_df, width="stretch", hide_index=True)
    data_source("KMeans_Final_Result.xlsx + reviews_processed_classified.csv + 正交設計_產品組合.xlsx", "由目標市場、評論痛點與產品屬性共同推導定位")

    st.subheader("2｜定位證據：這不是一句口號")
    evidence = pd.DataFrame([
        ["市場區隔", "KMeans_Final_Result.xlsx", "確認目前客群是依產品偏好與購買原型切分，而不是主觀命名。"],
        ["商品表現", "ridge_logit_customer_specific_report_*.xlsx", "檢查此定位下哪些商品具備購買率與推薦潛力。"],
        ["產品屬性", "正交設計_產品組合.xlsx", "把品牌、價格、顏色、規格與 GPS 對應到定位主張。"],
        ["評論痛點", "reviews_processed_classified.csv", "確認顧客在規格、功能、品質、外觀或價格上的可操作痛點。"],
    ], columns=["證據類型", "資料來源", "如何支持定位"])
    st.dataframe(evidence, width="stretch", hide_index=True)

    st.subheader("3｜定位如何轉成 Amazon 與廣告素材")
    landing = pd.DataFrame([
        ["Amazon 標題", profile["listing_focus"], "標題不要只塞關鍵字，要讓買家一眼知道這款解決什麼問題。"],
        ["五點描述", profile["claim"], "第一點先解決購買疑慮，第二點再講功能，第三點講品質或風格。"],
        ["主圖 / A+ Content", profile["landing"], "用圖像降低理解成本，讓非技術買家也能判斷是否適合。"],
        ["EDM / 再行銷", profile["ad_angle"], "依客群痛點改寫訊息，不用所有人收到同一種文案。"],
        ["短影音腳本", "3 秒痛點 → 5 秒解法 → 3 秒 CTA", "可銜接一對一行銷頁的 AI 素材提示。"],
    ], columns=["使用場景", "定位轉譯", "具體做法"])
    st.dataframe(landing, width="stretch", hide_index=True)

    st.markdown(
        """
        <div class="vv-note"><b>行銷判讀：</b>產品定位不是固定不變的 slogan。當目標市場切換時，商品頁主張、廣告素材與 EDM 話術也應跟著改變；這樣才會讓 STP 從簡報概念變成行銷執行流程。</div>
        """,
        unsafe_allow_html=True,
    )


def product_strategy_page():
    st.header("商品策略｜主推與檢討清單")
    products = load_product_summary()
    if products.empty:
        st.info("目前找不到產品分析資料。")
        return

    seg_id, cfg = segment_options_with_default("套用產品定位")
    profile = positioning_profile(seg_id)
    products = add_product_strategy_columns(products, seg_id)

    st.markdown(
        f"""
        <div class="vv-action">
        <b>目前套用定位：</b>{profile['positioning']}<br>
        <b>對應目標客群：</b>{cfg['name']}<br>
        商品策略不只看購買率，而是同時評估「購買表現、定位符合度、推廣可執行性與評論風險」。
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("商品角色怎麼看？", expanded=True):
        role_df = pd.DataFrame([
            ["主力轉換商品", "購買率高且符合目前定位", "加大曝光，放入主推廣告、首頁推薦與 EDM 主商品。"],
            ["定位證明商品", "最能代表技詮的定位價值", "用於品牌定位、Amazon A+ Content、規格圖與案例素材。"],
            ["流量導入商品", "容易吸引點擊或促銷進站", "作為促銷入口或再行銷入口。"],
            ["差異化商品", "特殊色系、特殊規格或風格明顯", "做情境圖、社群素材與顏色比較。"],
            ["檢討改善商品", "購買率偏低或與定位不符", "先檢查圖片、規格、價格、FAQ 與評論痛點。"],
        ], columns=["商品角色", "判斷邏輯", "建議行動"])
        st.dataframe(role_df, width="stretch", hide_index=True)
        st.caption("商品策略分數 = 購買表現 40% + 定位符合度 35% + 推廣可執行性 15% + 評論風險反向分數 10%。")

    col1, col2, col3, col4, col5 = st.columns(5)
    brand = col1.selectbox("品牌", ["全部"] + sorted(products["Brand"].dropna().unique().tolist()))
    color = col2.selectbox("顏色", ["全部"] + sorted(products["Color"].dropna().unique().tolist()))
    spec = col3.selectbox("規格", ["全部"] + sorted(products["Spec_Display"].dropna().unique().tolist()))
    gps = col4.selectbox("GPS", ["全部"] + sorted(products["GPS_Display"].dropna().unique().tolist()))
    role_filter = col5.selectbox("商品角色", ["全部"] + sorted(products["商品角色"].dropna().unique().tolist()))

    df = products.copy()
    if brand != "全部": df = df[df["Brand"] == brand]
    if color != "全部": df = df[df["Color"] == color]
    if spec != "全部": df = df[df["Spec_Display"] == spec]
    if gps != "全部": df = df[df["GPS_Display"] == gps]
    if role_filter != "全部": df = df[df["商品角色"] == role_filter]

    st.subheader("1｜商品角色與推廣清單")
    view = df.sort_values("商品策略分數", ascending=False)[[
        "Product_Row", "Product_Label", "商品角色", "商品策略分數", "定位符合度", "Actual_Purchase_Rate", "Mean_Predicted_Probability", "建議行動", "推廣話術", "ASIN"
    ]].copy()
    view["Actual_Purchase_Rate"] = view["Actual_Purchase_Rate"].map(lambda x: f"{x:.2f}%")
    view["Mean_Predicted_Probability"] = view["Mean_Predicted_Probability"].map(lambda x: f"{x:.2f}%")
    st.dataframe(view, width="stretch", hide_index=True)
    data_source("ridge_logit_customer_specific_report_*.xlsx + 正交設計_產品組合.xlsx", "商品購買表現、產品屬性與目前定位共同計算商品角色")

    st.subheader("2｜商品策略矩陣")
    fig = px.scatter(
        df,
        x="定位符合度",
        y="Actual_Purchase_Rate",
        size="Actual_Purchase_Count",
        color="商品角色",
        hover_name="Product_Label",
        labels={"定位符合度": "定位符合度", "Actual_Purchase_Rate": "實際購買率(%)"},
        title="商品角色矩陣｜定位符合度 × 實際購買率",
    )
    st.plotly_chart(fig, width="stretch")
    st.markdown(
        """
        <div class="vv-note"><b>判讀方式：</b>右上角商品同時具備高購買率與高定位符合度，適合優先推廣；左上角商品雖賣得動但定位弱，可作流量入口；右下角商品能代表定位但轉換不足，適合作為內容或品牌素材；左下角商品應優先檢討 Listing 或暫緩投放。</div>
        """,
        unsafe_allow_html=True,
    )


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
    st.header("顧客推薦｜準個人化行銷與 AI 素材")
    recs = load_recommendations()
    products = load_product_summary()
    rfm = load_rfm()
    if recs.empty or products.empty:
        st.info("目前找不到推薦模型或商品資料。")
        return

    st.markdown("""
    <div class="vv-action"><b>本頁定位：</b>這裡不是要替每位顧客拍一支完全不同的廣告，而是建立「準個人化行銷」流程：
    依據顧客偏好與推薦商品，把顧客分配到不同素材路線、話術、優惠級距與投放通路。這比所有人看到同一支廣告更精準，也比完全一人一廣告更可落地。</div>
    """, unsafe_allow_html=True)

    audience = build_campaign_audience(recs, products, rfm)
    tab1, tab2, tab3, tab4 = st.tabs(["批次投放工作台", "素材與優惠規則", "單一顧客查詢", "A/B 測試與迭代"])

    with tab1:
        st.subheader("批次投放工作台：一次找到適合某類素材的客群")
        st.caption("行銷人員日常使用時，不必一個一個查 Customer_ID；先選素材路線、商品或優惠級距，再輸出受眾名單做 EDM、再行銷或廣告測試。")
        if audience.empty:
            st.info("目前無法建立批次投放名單。")
        else:
            f1, f2, f3, f4 = st.columns(4)
            route_filter = f1.multiselect("素材路線", sorted(audience["行銷素材路線"].dropna().unique().tolist()), default=[])
            tag_filter = f2.multiselect("商品策略", sorted(audience["Strategy_Tag"].dropna().unique().tolist()), default=[])
            offer_filter = f3.multiselect("優惠級距", sorted(audience["優惠級距"].dropna().unique().tolist()), default=[])
            product_filter = f4.multiselect("推薦商品編號", sorted(audience["Product_Row"].dropna().astype(int).unique().tolist()), default=[])

            batch = audience.copy()
            if route_filter:
                batch = batch[batch["行銷素材路線"].isin(route_filter)]
            if tag_filter:
                batch = batch[batch["Strategy_Tag"].isin(tag_filter)]
            if offer_filter:
                batch = batch[batch["優惠級距"].isin(offer_filter)]
            if product_filter:
                batch = batch[batch["Product_Row"].isin(product_filter)]

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("符合條件顧客", f"{len(batch):,}")
            k2.metric("平均預測購買機率", f"{batch['預測購買機率(%)'].mean():.2f}%" if len(batch) else "0.00%")
            k3.metric("主要素材路線", batch["行銷素材路線"].mode().iloc[0] if len(batch) else "—")
            k4.metric("主要優惠級距", batch["優惠級距"].mode().iloc[0] if len(batch) else "—")

            summary = batch.groupby(["行銷素材路線", "建議影片素材", "優惠級距"], dropna=False).agg(
                顧客數=("Customer_ID", "nunique"),
                平均預測購買機率=("預測購買機率(%)", "mean"),
                代表商品=("Product_Label", lambda x: x.mode().iloc[0] if not x.mode().empty else "—"),
                核心話術=("核心話術", lambda x: x.mode().iloc[0] if not x.mode().empty else "—"),
            ).reset_index()
            if not summary.empty:
                summary["平均預測購買機率"] = summary["平均預測購買機率"].map(lambda x: f"{x:.2f}%")
            st.dataframe(summary, width="stretch", hide_index=True)
            data_source("ridge_logit_customer_specific_report_*.xlsx + RFM_CAI 統整.xlsx", "以每位顧客 Top 1 推薦商品建立批次投放名單")

            export_cols = [c for c in ["Customer_ID", "Product_Row", "Product_Label", "Brand", "Color", "Spec_Display", "GPS_Display", "預測購買機率(%)", "行銷素材路線", "建議影片素材", "核心話術", "優惠級距", "優惠理由", "建議通路", "RFM_Label", "CAI_Label"] if c in batch.columns]
            csv = batch[export_cols].to_csv(index=False).encode("utf-8-sig")
            st.download_button("下載目前篩選名單 CSV", csv, file_name="personalized_campaign_audience.csv", mime="text/csv")

    with tab2:
        st.subheader("素材與優惠規則：用有限素材做準個人化")
        rule_df = pd.DataFrame([
            ["技術規格型", "影片A：技術規格／安裝確認", "規格精準、安裝安心、降低買錯", "NPT / SAE 規格圖、安裝步驟、性能感", "高意願可少折扣；中意願給免運或 5%"],
            ["實用功能型", "影片B：實用功能／日常使用", "GPS、功能完整、穩定可靠", "功能 icon、使用情境、比較表", "用 5–10% 或組合優惠促進轉換"],
            ["風格美學型", "影片C：車內風格／顏色搭配", "內裝搭配、特殊色系、質感", "實裝圖、車內情境、色系比較", "少折扣，強調稀有感與視覺價值"],
            ["價格誘因型", "影片D：限時優惠／高 CP 值", "限時、免運、組合價、CP 值", "促銷圖卡、倒數、優惠券", "10–15% 或清庫存券，僅給需要刺激者"],
        ], columns=["素材路線", "主影片", "話術方向", "設計重點", "優惠原則"])
        st.dataframe(rule_df, width="stretch", hide_index=True)
        st.markdown("""
        <div class="vv-note"><b>行銷邏輯：</b>不是 1,024 位顧客各拍一支影片，而是把「商品推薦 × 偏好路線 × 話術 × 優惠」模組化。
        例如同一支技術規格影片，可以搭配不同商品、不同規格文案與不同優惠級距，形成多組個人化素材。</div>
        """, unsafe_allow_html=True)

    with tab3:
        st.subheader("單一顧客查詢：保留一對一推薦，但用來產生素材，不只看 Top 5")
        customer_ids = sorted(recs["Customer_ID"].dropna().astype(str).unique().tolist())
        query = st.text_input("快速搜尋 Customer_ID", "")
        filtered = [c for c in customer_ids if query.lower() in c.lower()] if query else customer_ids
        selected = st.selectbox("選擇顧客", filtered[:1000])
        cust = recs[recs["Customer_ID"] == selected].copy()
        cust = cust.merge(products[["Product_Row", "Product_Label", "Brand", "Price", "Color", "Spec_Display", "GPS_Display", "Strategy_Tag"]], on="Product_Row", how="left")
        cust = cust.sort_values("Predicted_Probability", ascending=False)
        best = cust.iloc[0]
        route = infer_marketing_route(best)
        offer, reason = offer_tier(best.get("Predicted_Probability", 0), best.get("Strategy_Tag", ""), "")
        templates = campaign_copy_templates(route, best, offer)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("最佳推薦商品", best["Product_Label"])
        c2.metric("預測購買機率", f"{best['Predicted_Probability']*100:.2f}%")
        c3.metric("素材路線", route)
        c4.metric("優惠建議", offer)
        st.caption(f"優惠判斷：{reason}")

        display = cust[["Product_Row", "Product_Label", "Predicted_Probability", "Strategy_Tag"]].copy()
        display["Predicted_Probability"] = display["Predicted_Probability"].map(lambda x: f"{x*100:.2f}%")
        st.dataframe(display, width="stretch", hide_index=True)
        data_source("ridge_logit_customer_specific_report_*.xlsx", "Recommendation_Top5 工作表；此處以單一顧客查詢生成素材草稿")

        st.subheader("AI 素材輸出草稿")
        tabs = st.tabs(["EDM", "Meta/IG 廣告", "Amazon 五點", "AI 圖片 Prompt", "短影音腳本"])
        tabs[0].text_area("EDM 主旨", templates["EDM 主旨"], height=80)
        tabs[0].text_area("EDM 內文", templates["EDM 內文"], height=150)
        tabs[1].text_area("Meta/IG 廣告文案", templates["Meta/IG 廣告文案"], height=130)
        tabs[2].text_area("Amazon Bullet Points", templates["Amazon 五點描述"], height=170)
        tabs[3].text_area("可貼到 Canva / Firefly / AI 圖像工具", templates["AI 圖片 Prompt"], height=150)
        tabs[4].text_area("可貼到 CapCut / 短影音腳本工具", templates["短影音腳本"], height=130)

    with tab4:
        st.subheader("A/B 測試與迭代：讓創意變成可驗證的成效")
        st.markdown("""
        <div class="vv-warning"><b>重要原則：</b>目前資料只能支撐「推薦與素材分配建議」，不能保證每個人一定會轉換。
        真正的效益要靠 A/B Test 驗證：把客群分成控制組與測試組，追蹤點擊率、轉換率、客單價與 ROAS，再回來調整素材與優惠。</div>
        """, unsafe_allow_html=True)
        test_df = pd.DataFrame([
            ["測試假設", "技術規格型客群看到規格／安裝確認素材，轉換率會高於一般商品廣告"],
            ["控制組", "同商品一般廣告，不分話術與優惠"],
            ["測試組", "依素材路線分配技術型、實用型、風格型或促銷型素材"],
            ["主要 KPI", "CTR 點擊率、CVR 轉換率、AOV 客單價、ROAS 廣告收益"],
            ["追蹤方式", "使用 UTM、優惠碼、EDM 名單標籤或廣告受眾名稱記錄"],
            ["迭代方式", "每 1–2 週更新素材表現，保留高轉換素材，淘汰低轉換素材"],
        ], columns=["項目", "做法"])
        st.dataframe(test_df, width="stretch", hide_index=True)
        st.markdown("""
        <div class="vv-action"><b>競賽呈現重點：</b>我們不是宣稱現在已經做到完全一人一價，而是提出一套可落地、可測試、可迭代的準個人化行銷流程，讓廠商逐步從大眾廣告走向分眾素材與個人化優惠。</div>
        """, unsafe_allow_html=True)


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
    "顧客推薦｜準個人化行銷與 AI 素材": recommendation_page,
    "顧客名單｜RFM/CAI 策略": customer_list_page,
    "評論洞察｜痛點與 Listing 改善": review_insights_page,
}

NAV_META = {
    "首頁｜總覽與操作手冊": {"label": "00  Overview\n首頁｜總覽與操作手冊", "desc": "快速掌握今天應該看什麼、怎麼用這套儀表板。"},
    "市場區隔｜顧客偏好族群": {"label": "01  Segmentation\n市場區隔｜顧客偏好族群", "desc": "把產品偏好與顧客需求轉成可理解的市場區隔。"},
    "目標市場｜技詮優先客群": {"label": "02  Targeting\n目標市場｜技詮優先客群", "desc": "用可調整權重決定技詮目前最該鎖定哪一個目標市場。"},
    "產品定位｜技詮如何被記住": {"label": "03  Positioning\n產品定位｜技詮如何被記住", "desc": "把目標市場轉成產品頁、廣告與品牌主張。"},
    "商品策略｜主推與檢討清單": {"label": "04  Product Strategy\n商品策略｜主推與檢討清單", "desc": "依目前定位判斷商品角色、推廣優先順序與檢討方向。"},
    "產品推廣｜廣告與效益試算": {"label": "05  Promotion Simulator\n產品推廣｜廣告與效益試算", "desc": "用曝光、毛利率與廣告成本模擬推廣效益。"},
    "顧客推薦｜準個人化行銷與 AI 素材": {"label": "06  Personalized Marketing\n顧客推薦｜AI素材與優惠分配", "desc": "把顧客推薦轉成素材路線、話術、優惠與 AI 產出提示。"},
    "顧客名單｜RFM/CAI 策略": {"label": "07  Customer List Strategy\n顧客名單｜RFM/CAI 策略", "desc": "將顧客名單轉成不同經營策略。"},
    "評論洞察｜痛點與 Listing 改善": {"label": "08  Review Insights\n評論洞察｜痛點與 Listing 改善", "desc": "把評論痛點轉成 Amazon Listing 與客服改善方向。"},
}

with st.sidebar:
    st.title("VivaVictors")
    st.caption("Marketing Dashboard")
    st.markdown("<div class='small-text'>功能目錄</div>", unsafe_allow_html=True)
    selected_page = st.radio(
        "選擇功能",
        list(pages.keys()),
        label_visibility="collapsed",
        format_func=lambda key: NAV_META.get(key, {}).get("label", key),
    )
    st.caption(NAV_META.get(selected_page, {}).get("desc", ""))
    st.divider()
    st.markdown("<div class='vv-side-block'><span class='vv-side-title'>日常使用流程</span><span class='vv-side-body'>先確認市場與目標客群，再決定定位、商品、推廣與個人化素材。</span></div>", unsafe_allow_html=True)

    with st.expander("資料來源 Data Sources", expanded=False):
        for fname, purpose, detail in SOURCE_ITEMS:
            st.markdown(
                f"<div class='vv-side-block'><span class='vv-tag'>Data</span><span class='vv-side-title'>{fname}</span><span class='vv-side-body'>{purpose}<br>{detail}</span></div>",
                unsafe_allow_html=True,
            )

    with st.expander("常用名詞 Glossary", expanded=False):
        for term, explanation in GLOSSARY_ITEMS:
            st.markdown(
                f"<div class='vv-side-block'><span class='vv-tag'>Term</span><span class='vv-side-title'>{term}</span><span class='vv-side-body'>{explanation}</span></div>",
                unsafe_allow_html=True,
            )

    st.divider()
    if st.button("清除快取後重新整理"):
        st.cache_data.clear()
        st.rerun()


pages[selected_page]()
