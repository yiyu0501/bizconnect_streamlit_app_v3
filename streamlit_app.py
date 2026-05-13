"""
Streamlit dashboard for the 2026 BizConnect Taipei B2C consumer preference project.

This application consolidates the key insights from your data
analysis into a single web interface.  The dashboard is divided
into several pages accessible from the sidebar:

* **Overview** – high‑level metrics summarising the data set and
  product performance.  Includes a bar chart of the top performing
  product combinations and a short narrative explaining what the
  analysis accomplished.

* **Customer Segmentation** – visualises the distribution of
  customer value segments (RFM/CAI).  You can filter by segment to
  view summary statistics for that group, such as purchase count
  and average predicted probability of purchase.  This page uses
  the `RFM_CAI 統整.xlsx` file to classify customers into value
  buckets.

* **Product Performance** – presents the 22 product combinations
  together with their observed purchase rates, predicted
  probabilities and core attributes (brand, price, colour,
  specification and GPS).  Use the filters to narrow down to
  specific brands, colours or specifications.  A bar chart
  highlights the purchase rate for each combination.

* **Review Analysis** – explores the customer reviews collected
  from Amazon (448 unique reviews after deduplication).  A bar
  chart shows the distribution of motivations (price sensitivity,
  quality, function, appearance, specification, brand or other).
  Another chart shows the sentiment split by star rating.  At
  the bottom of the page you can select an ASIN to view the
  product‑level summary of review statistics.

* **Personalised Recommendation** – type in or select a
  `Customer_ID` to retrieve that customer’s top recommended product
  combination along with the next four alternatives.  Details on
  each product are displayed to provide context for the
  recommendation.

* **Market Strategy** – summarises actionable recommendations
  derived from your analyses.  This page is intentionally kept
  concise so that business stakeholders can quickly grasp how
  these findings translate into tangible value.

Before running this app you should ensure that the `data/` folder
contains the following files:

```
RFM_CAI 統整.xlsx               # customer value labels (RFM/CAI)
ridge_logit_customer_specific_report_20260508_110837.xlsx
                                # logistic model output with recommendation tables
正交設計_產品組合.xlsx             # design file linking product attributes to ASINs
reviews_processed_classified.csv # consolidated review data with sentiment & motivation
reviews_summary_processed.csv    # summary of reviews by ASIN
```

You can run this app locally by executing:

```
streamlit run streamlit_app.py
```

Or deploy it on Streamlit Community Cloud by uploading
this directory to a public GitHub repository and creating
a new app from that repository.
"""

import streamlit as st
import pandas as pd
import altair as alt
from functools import lru_cache
import os

# -----------------------------------------------------------------------------
# Data loading helpers
# -----------------------------------------------------------------------------

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@st.cache_data(show_spinner=False)
def load_rfm_data():
    """Load RFM/CAI customer label data.

    The Excel file should contain a sheet named either 'RFM' or
    '完成檔'.  We prioritise the sheet that contains both RFM and CAI
    labels merged together.  If only RFM is available we still
    return that.
    """
    xls_path = os.path.join(DATA_DIR, "RFM_CAI 統整.xlsx")
    xls = pd.ExcelFile(xls_path)
    sheet_name = None
    for candidate in ["完成檔", "整合檔", "RFM"]:
        if candidate in xls.sheet_names:
            sheet_name = candidate
            break
    if sheet_name is None:
        st.warning("RFM/CAI sheet not found in RFM_CAI 統整.xlsx")
        return pd.DataFrame()
    df = pd.read_excel(xls_path, sheet_name=sheet_name)
    # normalise column names for ease of use
    df = df.rename(columns={
        "顧客代號": "Customer_ID",
        "Customer_ID": "Customer_ID",
        "RFM組別": "RFM_Label",
        "CAI組別": "CAI_Label",
        "Label": "Final_Label",
    })
    # ensure Customer_ID is string
    df["Customer_ID"] = df["Customer_ID"].astype(str)
    return df


@st.cache_data(show_spinner=False)
@st.cache_data(show_spinner=False)
def load_product_summary():
    """
    Load product performance summary from logistic regression output.
    This version avoids duplicate column names after merging the product design file.
    """
    path = os.path.join(DATA_DIR, "ridge_logit_customer_specific_report_20260508_110837.xlsx")

    if not os.path.isfile(path):
        st.error("Missing logistic regression output file in data folder.")
        return pd.DataFrame()

    prod_summary = pd.read_excel(path, sheet_name="Product_Summary")

    design_path = os.path.join(DATA_DIR, "正交設計_產品組合.xlsx")

    if os.path.isfile(design_path):
        design_df = pd.read_excel(design_path)

        design_df = design_df.rename(columns={
            "組合_品牌": "Design_Brand",
            "組合_原價(轉換後)": "Design_Price_Level",
            "組合_錶盤顏色": "Design_Color",
            "組合_螺紋類型": "Design_Spec",
            "組合_GPS天線": "Design_GPS",
            "對應 ASIN": "Design_ASIN"
        })

        keep_cols = [
            "Design_Brand",
            "Design_Price_Level",
            "Design_Color",
            "Design_Spec",
            "Design_GPS",
            "Design_ASIN"
        ]

        design_df = design_df[[col for col in keep_cols if col in design_df.columns]].copy()

        if len(prod_summary) == len(design_df):
            combined = pd.concat(
                [
                    prod_summary.reset_index(drop=True),
                    design_df.reset_index(drop=True)
                ],
                axis=1
            )
        else:
            combined = prod_summary.copy()
    else:
        combined = prod_summary.copy()

    combined = combined.loc[:, ~combined.columns.duplicated()].copy()

    combined["Brand"] = combined.get("Design_Brand", combined.get("Brand", None))
    combined["Price_Level"] = combined.get("Design_Price_Level", combined.get("price", None))
    combined["Color"] = combined.get("Design_Color", combined.get("Color", None))
    combined["Spec"] = combined.get("Design_Spec", combined.get("Spec", None))
    combined["GPS"] = combined.get("Design_GPS", combined.get("GPS", None))
    combined["ASIN"] = combined.get("Design_ASIN", combined.get("ASIN", None))

    if "Actual_Purchase_Rate" in combined.columns:
        combined["Actual_Purchase_Rate"] = pd.to_numeric(
            combined["Actual_Purchase_Rate"],
            errors="coerce"
        )

    if "Mean_Predicted_Probability" in combined.columns:
        combined["Mean_Predicted_Probability"] = pd.to_numeric(
            combined["Mean_Predicted_Probability"],
            errors="coerce"
        )

    return combined


@st.cache_data(show_spinner=False)
def load_recommendations():
    """Load personalised recommendation tables.
    Returns a DataFrame with one row per recommendation (top 5 per customer).
    """
    path = os.path.join(DATA_DIR, "ridge_logit_customer_specific_report_20260508_110837.xlsx")
    try:
        recs = pd.read_excel(path, sheet_name="Recommendation_Top5")
        # standardise Customer_ID to string
        recs['Customer_ID'] = recs['Customer_ID'].astype(str)
        return recs
    except Exception as e:
        st.error(f"Failed to load Recommendation_Top5: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_reviews_detail():
    """Load detailed review dataset with sentiment and motivation classification."""
    path = os.path.join(DATA_DIR, "reviews_processed_classified.csv")
    if not os.path.isfile(path):
        st.warning("reviews_processed_classified.csv not found in data folder.")
        return pd.DataFrame()
    df = pd.read_csv(path)
    # ensure date is parsed
    if 'Review_Date' in df.columns:
        df['Review_Date'] = pd.to_datetime(df['Review_Date'], errors='coerce')
    return df


@st.cache_data(show_spinner=False)
def load_reviews_summary():
    """Load summary of reviews by ASIN."""
    path = os.path.join(DATA_DIR, "reviews_summary_processed.csv")
    if not os.path.isfile(path):
        st.warning("reviews_summary_processed.csv not found in data folder.")
        return pd.DataFrame()
    df = pd.read_csv(path)
    return df


# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------


def motivation_palette():
    """Define a consistent colour palette for motivations."""
    return {
        '價格敏感': '#1f77b4',  # blue
        '品質信任': '#ff7f0e',  # orange
        '功能需求': '#2ca02c',  # green
        '外觀偏好': '#d62728',  # red
        '規格適配': '#9467bd',  # purple
        '品牌信任': '#8c564b',  # brown
        '其他': '#7f7f7f',    # grey
    }


def display_metrics(total_customers: int, total_purchases: int, purchase_rate: float,
                    review_count: int):
    """Show key figures on the overview page."""
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Unique Customers", f"{total_customers}")
    col2.metric("Total Purchases", f"{total_purchases}")
    col3.metric("Overall Purchase Rate", f"{purchase_rate:.2f}%")
    col4.metric("Total Reviews", f"{review_count}")


def product_table(df: pd.DataFrame):
    """Render a product performance table with optional style."""
    # round numeric columns
    if 'Actual_Purchase_Rate' in df.columns:
        df['Actual_Purchase_Rate'] = df['Actual_Purchase_Rate'].map(lambda x: f"{x:.2f}%")
    if 'Mean_Predicted_Probability' in df.columns:
        df['Mean_Predicted_Probability'] = df['Mean_Predicted_Probability'].map(lambda x: f"{x:.2f}%")
    st.dataframe(df, use_container_width=True)


def main():
    st.set_page_config(page_title="Consumer Preference Dashboard", layout="wide")
    st.title("BizConnect Taipei: Consumer Preference Dashboard")
    st.sidebar.header("Navigation")
    pages = [
        "Overview",
        "Customer Segmentation",
        "Product Performance",
        "Review Analysis",
        "Personalised Recommendation",
        "Market Strategy",
    ]
    page_selection = st.sidebar.radio("Select a page:", pages)

    # Load data lazily only when needed
    if page_selection == "Overview":
        overview_page()
    elif page_selection == "Customer Segmentation":
        segmentation_page()
    elif page_selection == "Product Performance":
        product_performance_page()
    elif page_selection == "Review Analysis":
        review_analysis_page()
    elif page_selection == "Personalised Recommendation":
        recommendation_page()
    elif page_selection == "Market Strategy":
        strategy_page()


def overview_page():
    st.header("Overview")
    # Load core data
    prod_summary = load_product_summary()
    reviews_detail = load_reviews_detail()
    recs = load_recommendations()
    # compute metrics
    total_customers = recs['Customer_ID'].nunique() if not recs.empty else 0
    total_purchases = int(prod_summary['Actual_Purchase_Count'].sum()) if 'Actual_Purchase_Count' in prod_summary else 0
    overall_rate = float(prod_summary['Actual_Purchase_Count'].sum() / prod_summary['N_Customers'].sum() * 100) if 'N_Customers' in prod_summary and prod_summary['N_Customers'].sum() > 0 else 0.0
    review_count = len(reviews_detail) if not reviews_detail.empty else 0
    display_metrics(total_customers, total_purchases, overall_rate, review_count)

    st.subheader("What this dashboard does")
    st.markdown(
        """
        This interactive dashboard summarises consumer preferences and product
        performance for the BizConnect Taipei B2C case study.  The analyses are
        derived from multiple data sources:
        
        * **Transaction logs** (1,024 customers × 22 product combinations) to
          model purchase probability for each customer using a ridge logistic
          regression.
        * **RFM/CAI labels** to identify high‑value customers and construct
          segments.
        * **Design file** that maps each product combination to its brand,
          price, colour, specification and GPS attributes.
        * **Amazon reviews** consolidated from 29 spreadsheets to infer
          customer motivations and overall sentiment towards our products.

        Use the pages on the left to drill into specific aspects of the data.
        """
    )

    # show top product combinations by purchase rate
    st.subheader("Top Product Combinations by Purchase Rate")
    if not prod_summary.empty and 'Actual_Purchase_Rate' in prod_summary.columns:
        top_df = prod_summary.sort_values(by='Actual_Purchase_Rate', ascending=False).head(10)
        chart = alt.Chart(top_df).mark_bar().encode(
        x=alt.X('Actual_Purchase_Rate:Q', title='Purchase Rate (%)'),
        y=alt.Y('Product_Row:N', sort='-x', title='Product Combination'),
        tooltip=['Brand','Price_Level','Color','Spec','GPS','Actual_Purchase_Rate']
        ).properties(height=400)
        st.altair_chart(chart, use_container_width=True)
        st.markdown(
            """
            The bar chart shows the ten product combinations with the highest observed purchase rates.  Use the
            **Product Performance** page to explore all 22 combinations in detail and apply filters for brand,
            colour or specification.
            """
        )
    else:
        st.info("Product summary data is not available.")


def segmentation_page():
    st.header("Customer Segmentation (RFM/CAI)")
    rfm = load_rfm_data()
    if rfm.empty:
        st.info("RFM/CAI data not available.")
        return
    st.subheader("Distribution of Customer Value Segments")
    # Count RFM labels
    if 'RFM_Label' in rfm.columns:
        rfm_counts = rfm['RFM_Label'].value_counts().reset_index()
        rfm_counts.columns = ['Segment','Count']
        rfm_bar = alt.Chart(rfm_counts).mark_bar().encode(
            x=alt.X('Count:Q', title='Number of Customers'),
            y=alt.Y('Segment:N', sort='-x', title='RFM Segment'),
            tooltip=['Segment','Count']
        )
        st.altair_chart(rfm_bar, use_container_width=True)
    else:
        st.info("RFM labels not found in data.")
    if 'CAI_Label' in rfm.columns and rfm['CAI_Label'].notna().any():
        st.subheader("CAI Distribution")
        cai_counts = rfm['CAI_Label'].value_counts().reset_index()
        cai_counts.columns = ['CAI_Label','Count']
        cai_bar = alt.Chart(cai_counts).mark_bar().encode(
            x=alt.X('Count:Q', title='Number of Customers'),
            y=alt.Y('CAI_Label:N', sort='-x', title='CAI Segment'),
            tooltip=['CAI_Label','Count']
        )
        st.altair_chart(cai_bar, use_container_width=True)
    # allow selecting a segment to view summary statistics
    st.subheader("Segment Detail")
    segment_options = rfm['RFM_Label'].unique().tolist() if 'RFM_Label' in rfm.columns else []
    selected_segment = st.selectbox("Select RFM segment to view", options=segment_options)
    seg_df = rfm[rfm['RFM_Label'] == selected_segment]
    st.write(f"Customers in segment '{selected_segment}': {len(seg_df)}")
    # join with recommendation summary to compute average predicted probability or purchase rate
    recs = load_recommendations()
    if not recs.empty:
        merged = pd.merge(seg_df[['Customer_ID']], recs[['Customer_ID','Predicted_Probability']], on='Customer_ID', how='left')
        st.write(f"Average predicted purchase probability: {merged['Predicted_Probability'].mean() * 100:.2f}%")
    st.dataframe(seg_df[['Customer_ID','RFM_Label','CAI_Label']].head(50), use_container_width=True)


def product_performance_page():
    st.header("Product Performance")
    prod_summary = load_product_summary()
    if prod_summary.empty:
        st.info("Product summary data not available.")
        return
    # Filters
    brands = ['All'] + sorted(prod_summary['Brand'].dropna().unique().tolist())
    colours = ['All'] + sorted(prod_summary['Color'].dropna().unique().tolist())
    specs = ['All'] + sorted(prod_summary['Spec'].dropna().unique().tolist())
    col1, col2, col3 = st.columns(3)
    brand_filter = col1.selectbox("Filter by Brand", brands)
    colour_filter = col2.selectbox("Filter by Colour", colours)
    spec_filter = col3.selectbox("Filter by Specification", specs)
    # Apply filters
    df = prod_summary.copy()
    if brand_filter != 'All':
        df = df[df['Brand'] == brand_filter]
    if colour_filter != 'All':
        df = df[df['Color'] == colour_filter]
    if spec_filter != 'All':
        df = df[df['Spec'] == spec_filter]
    st.subheader("Summary Table")
    # Display table
    product_table(df[['Product_Row','Brand','Price_Level','Color','Spec','GPS','Actual_Purchase_Rate','Mean_Predicted_Probability']])
    st.subheader("Purchase Rate by Product Combination")
    chart_data = df.sort_values('Actual_Purchase_Rate', ascending=False)
    bar = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('Actual_Purchase_Rate:Q', title='Purchase Rate (%)'),
        y=alt.Y('Product_Row:N', sort='-x', title='Product Combination'),
        color=alt.Color('Brand:N', legend=alt.Legend(title='Brand')),
        tooltip=['Brand','Price_Level','Color','Spec','GPS','Actual_Purchase_Rate']
    ).properties(height=500)
    st.altair_chart(bar, use_container_width=True)


def review_analysis_page():
    st.header("Review Analysis")
    reviews = load_reviews_detail()
    reviews_summary = load_reviews_summary()
    if reviews.empty:
        st.info("No review data available.")
        return
    st.subheader("Motivation Distribution")
    mot_counts = reviews['Motivation_Type'].value_counts().reset_index()
    mot_counts.columns = ['Motivation','Count']
    palette = motivation_palette()
    mot_chart = alt.Chart(mot_counts).mark_bar().encode(
        x=alt.X('Count:Q', title='Number of Reviews'),
        y=alt.Y('Motivation:N', sort='-x', title='Motivation Type'),
        color=alt.Color('Motivation:N', scale=alt.Scale(domain=list(palette.keys()), range=list(palette.values())), legend=None),
        tooltip=['Motivation','Count']
    ).properties(height=300)
    st.altair_chart(mot_chart, use_container_width=True)
    st.markdown(
        """
        The chart above categorises each review into a primary motivation.
        Although the classification is heuristic, it provides a
        high‑level sense of why customers purchase or do not purchase the
        products.  *功能需求* and *品質信任* are the two most common
        motivations, suggesting that highlighting functionality and
        reliability can influence conversion.
        """
    )
    st.subheader("Sentiment by Star Rating")
    sentiment_counts = reviews.groupby(['Rating','Sentiment']).size().reset_index(name='Count')
    sentiment_chart = alt.Chart(sentiment_counts).mark_bar().encode(
        x=alt.X('Rating:O', title='Star Rating'),
        y=alt.Y('Count:Q', stack='normalize', title='Percentage of Reviews'),
        color=alt.Color('Sentiment:N', scale=alt.Scale(domain=['Positive','Neutral','Negative'], range=['#2ca02c','#ffbb78','#d62728'])),
        tooltip=['Rating','Sentiment','Count']
    ).properties(height=300)
    st.altair_chart(sentiment_chart, use_container_width=True)
    st.markdown(
        """
        This normalised bar chart shows the distribution of review sentiment
        across star ratings.  Unsurprisingly, 4–5 star reviews are mostly
        positive, while 1–2 star reviews are negative.  Neutral
        sentiment appears mainly in 3‑star reviews.
        """
    )
    st.subheader("Product‑Level Review Summary")
    if reviews_summary.empty:
        st.info("Review summary file missing or empty.")
    else:
        # Merge with design to attach brand info
        design_path = os.path.join(DATA_DIR, "正交設計_產品組合.xlsx")
        design = pd.read_excel(design_path)
        design = design.rename(columns={'對應 ASIN': 'ASIN', '組合_品牌':'Brand'})
        # Some cells contain multiple ASINs; we'll split and explode
        design['ASIN'] = design['ASIN'].astype(str)
        design = design.assign(ASIN=design['ASIN'].str.split(',')).explode('ASIN')
        summary = pd.merge(reviews_summary, design[['ASIN','Brand']], on='ASIN', how='left')
        # filter by selected brand if desired
        asin_options = ['All'] + sorted(summary['ASIN'].unique().tolist())
        selected_asin = st.selectbox("Select ASIN to view details", asin_options)
        if selected_asin != 'All':
            sub_summary = summary[summary['ASIN'] == selected_asin]
        else:
            sub_summary = summary
        st.dataframe(sub_summary[['ASIN','Brand','Review_Count','Avg_Rating','Positive_Count','Negative_Count','Main_Motivation']], use_container_width=True)
        st.markdown(
            """
            **ASIN** identifies the product on Amazon.  The summary table
            displays the number of reviews, average rating, count of
            positive and negative sentiments, and the most frequent
            motivation observed in the reviews.  Use this information to
            prioritise improvements to documentation, imagery or
            product design.
            """
        )


def recommendation_page():
    st.header("Personalised Recommendation")
    recs = load_recommendations()
    prod_summary = load_product_summary()
    if recs.empty:
        st.info("Recommendation data not available.")
        return
    customer_ids = sorted(recs['Customer_ID'].unique().tolist())
    default_id = customer_ids[0] if customer_ids else None
    selected_id = st.selectbox("Select Customer ID", customer_ids, index=0 if default_id else 0)
    # Filter the top 5 recs for this customer
    cust_recs = recs[recs['Customer_ID'] == selected_id]
    if cust_recs.empty:
        st.warning("No recommendations found for the selected customer.")
        return
    # Join with product summary to get descriptive info
    # product row is the key
    merged = pd.merge(cust_recs, prod_summary[['Product_Row','Brand','Price_Level','Color','Spec','GPS','Actual_Purchase_Rate']], on='Product_Row', how='left')
    # Display the best recommendation prominently
    best = merged.iloc[0]
    st.subheader("Best Product for this Customer")
    st.markdown(
        f"**Product Combination:** {int(best['Product_Row'])}  \
        **Brand:** {best['Brand']}  \
        **Price Level:** {best['Price_Level']}  \
        **Colour:** {best['Color']}  \
        **Spec:** {best['Spec']}  \
        **GPS:** {best['GPS']}  \
        **Predicted Purchase Probability:** {best['Predicted_Probability']*100:.2f}%"
    )
    st.write("\n")
    st.subheader("Top 5 Recommendations")
    # Format numeric probability
    display_df = merged[['Product_Row','Brand','Price_Level','Color','Spec','GPS','Predicted_Probability']].copy()
    display_df['Predicted_Probability'] = (display_df['Predicted_Probability']*100).map(lambda x: f"{x:.2f}%")
    st.dataframe(display_df, use_container_width=True)
    st.markdown(
        """
        The table above lists the top five product combinations for the
        selected customer based on the ridge logistic regression model.
        The probabilities indicate the likelihood of purchase should the
        customer be presented with each combination.
        """
    )
    # Show RFM/CAI labels if available
    rfm = load_rfm_data()
    if not rfm.empty:
        labels = rfm[rfm['Customer_ID'] == selected_id]
        if not labels.empty:
            st.subheader("Customer Segment")
            row = labels.iloc[0]
            st.write(f"RFM Segment: {row.get('RFM_Label','N/A')}")
            st.write(f"CAI Segment: {row.get('CAI_Label','N/A')}")
        else:
            st.write("This customer does not have RFM/CAI labels available.")


def strategy_page():
    st.header("Market Strategy and Next Steps")
    st.markdown(
        """
        ### Key Findings

        * **High‑performing product combinations** – The analysis shows that
          combinations featuring *MOTOR METER RACING* and the *Npt* thread
          consistently achieve higher purchase rates.  Black and white
          colourways are particularly strong.  These should be focal
          points in future campaigns and inventory planning.
        * **Customer motivations** – Reviews highlight that **功能需求**
          (functionality) and **品質信任** (quality trust) are the
          dominant reasons customers choose these products.  Marketing
          material and product pages should emphasise accuracy,
          reliability and durability.
        * **Customer value segments** – RFM/CAI analysis reveals that
          a relatively small number of customers drive a large
          proportion of purchases.  Prioritising high RFM score
          customers with loyalty programmes or early access to new
          products can yield outsized returns.

        ### Recommended Actions

        1. **Prioritise top combinations** – Focus inventory and
           marketing resources on the product combinations with the
           highest purchase rates, particularly those featuring
           *MOTOR METER RACING*, *black* or *white* colours, and
           the *Npt* specification.
        2. **Segmented messaging** – Use the RFM and review
           motivations to tailor marketing messages.  For example,
           customers in the *功能需求* segment respond well to
           technical specifications and performance testimonials,
           while *外觀偏好* customers should see more lifestyle
           imagery and colour options.
        3. **Feedback loop** – Continue collecting and analysing
           customer reviews.  Deploy an automated pipeline (see
           `reviews_processed_classified.csv`) to categorise new
           feedback into motivations and sentiment.  Use this to
           refine product copy and prioritise feature improvements.

        ### Deployment & Maintenance

        * **Self‑hosting** – This app is built with Streamlit and can be
          deployed on Streamlit Community Cloud or any Python web server.
          Simply upload the `bizconnect_streamlit_app_v3` directory to
          GitHub and create a new Streamlit app pointing at `streamlit_app.py`.
        * **Updating data** – Replace the files in the `data/` folder with
          updated versions to refresh the dashboard.  The review
          processing scripts live outside the app (see the project’s
          repository) and can be rerun when new reviews are available.
        * **Extending functionality** – Possible next steps include
          integrating pricing sensitivity analysis, pulling true cost data
          to support profit optimisation, and adding advertising spend
          dashboards to evaluate ROI.
        """
    )


if __name__ == "__main__":
    main()
