"""
Marketing Campaign Analytics Dashboard
Streamlit App — MySQL version (app_mysql.py)

Run: streamlit run app.py

Prerequisites:
    pip install streamlit plotly pandas sqlalchemy pymysql anthropic
"""

import streamlit as st
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os

load_dotenv()


import json
import re


# ─── MySQL connection settings ─────────────────────────────
# Edit these or set them as environment variables:
#   MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
MYSQL_HOST     = os.getenv("MYSQL_HOST")
MYSQL_PORT     = int(os.getenv("MYSQL_PORT"))
MYSQL_USER     = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")   
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
# ──────────────────────────────────────────────────────────

# ─── AI Provider Settings ──────────────────────────────────
# Choose your provider and paste the key.
# "groq"   → free at console.groq.com   (recommended)
# "gemini" → free at aistudio.google.com
# "ollama" → 100% local, no key needed (install ollama.com first)

AI_PROVIDER = "ollama"          # ← change to "gemini" or "ollama" if preferred

GROQ_API_KEY   = os.getenv("GROQ_API_KEY")   # paste Groq key here
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")   # paste Gemini key here
OLLAMA_MODEL   = "mistral"                           # any model pulled via: ollama pull llama3
OLLAMA_URL     = "http://localhost:11434"           # default Ollama endpoint
# ──────────────────────────────────────────────────────────

try:
    from sqlalchemy import create_engine
    ENGINE_URL = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
    )
    _engine = create_engine(ENGINE_URL, pool_pre_ping=True)
except ImportError:
    _engine = None

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY = True
except ImportError:
    PLOTLY = False

# ─── Page config ───────────────────────────────────────────
st.set_page_config(
    page_title="Marketing Campaign Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #0f3460; border-radius: 12px;
        padding: 20px; text-align: center; color: white;
    }
    .metric-value { font-size: 2rem; font-weight: 700; color: #e94560; }
    .metric-label { font-size: 0.9rem; color: #a8a8b3; margin-top: 4px; }
    .section-title {
        font-size: 1.3rem; font-weight: 600;
        border-left: 4px solid #e94560;
        padding-left: 12px; margin: 16px 0;
    }
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #0f3460; border-radius: 10px; padding: 16px;
    }
</style>
""", unsafe_allow_html=True)

# ─── Data loading — reads from MySQL ──────────────────────
@st.cache_data(ttl=300)   # cache for 5 minutes; refresh when data changes
def load_data():
    """Load the customers table from MySQL into a DataFrame."""
    if _engine is None:
        st.error("SQLAlchemy / PyMySQL not installed. Run: pip install sqlalchemy pymysql")
        st.stop()
    try:
        df = pd.read_sql("SELECT * FROM customers", con=_engine)
    except Exception as e:
        st.error(
            f"Could not connect to MySQL.\n\n"
            f"Error: {e}\n\n"
            f"Make sure you have:\n"
            f"1. Run `01_eda_cleaning_segmentation_mysql.py` to populate the DB.\n"
            f"2. Updated the MYSQL_* variables at the top of this file."
        )
        st.stop()
    return df

# Fallback: try loading from the clean CSV if MySQL is unavailable
@st.cache_data
def load_csv_fallback():
    base = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base, "..", "outputs", "marketing_clean.csv")
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return None

df_full = load_data()

# ─── Sidebar filters ───────────────────────────────────────
st.sidebar.title("Filters")
st.sidebar.markdown("---")

def make_filter(label, col):
    opts = ["All"] + sorted(df_full[col].dropna().unique().tolist())
    return st.sidebar.selectbox(label, opts)

selected_country      = make_filter("Country",        "Country")
selected_education    = make_filter("Education",      "Education")
selected_marital      = make_filter("Marital Status", "Marital_Status")

age_band_order   = ["18-29","30-39","40-49","50-59","60-69","70+"]
income_band_order = ["<25K","25K-50K","50K-75K","75K-100K",">100K"]

ab_opts = ["All"] + [b for b in age_band_order    if b in df_full["Age_Band"].values]
ib_opts = ["All"] + [b for b in income_band_order if b in df_full["Income_Band"].values]
selected_age_band    = st.sidebar.selectbox("Age Band",    ab_opts)
selected_income_band = st.sidebar.selectbox("Income Band", ib_opts)
selected_segment     = make_filter("Segment", "Primary_Segment")

st.sidebar.markdown("---")
st.sidebar.caption("Connected to MySQL")
st.sidebar.caption(f"`{MYSQL_HOST}/{MYSQL_DATABASE}`")

# Apply filters
df = df_full.copy()
if selected_country      != "All": df = df[df["Country"]        == selected_country]
if selected_education    != "All": df = df[df["Education"]      == selected_education]
if selected_marital      != "All": df = df[df["Marital_Status"] == selected_marital]
if selected_age_band     != "All": df = df[df["Age_Band"]       == selected_age_band]
if selected_income_band  != "All": df = df[df["Income_Band"]    == selected_income_band]
if selected_segment      != "All": df = df[df["Primary_Segment"]== selected_segment]

# ─── Header ────────────────────────────────────────────────
st.title("Marketing Campaign Analytics Dashboard")
st.markdown(f"Showing **{len(df):,}** customers (filtered from 56,000 total)")
st.markdown("---")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Demographic Overview", "Campaign Analysis", "Spending Patterns",
    "Channel Analysis", "Customer Segments", "AI Data Explorer"
])

# ══════════════════════════════════════════════════════════
# TAB 1: DEMOGRAPHIC OVERVIEW
# ══════════════════════════════════════════════════════════
with tab1:
    st.markdown("### Key Performance Indicators")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("Total Customers",  f"{len(df):,}")
    with col2: st.metric("Avg Income",       f"{df['Income'].mean():,.0f}")
    with col3: st.metric("Avg Total Spend",  f"{df['Total_Spend'].mean():,.0f}")
    with col4: st.metric("Response Rate (latest)",    f"{df['Response'].mean()*100:.1f}%")
    with col5: st.metric("Avg Age",          f"{df['Age'].mean():.0f} yrs")

    st.markdown("---")
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown('<div class="section-title">Age Band Distribution</div>', unsafe_allow_html=True)
        inc_counts = df["Age_Band"].value_counts().reset_index()
        inc_counts.columns = ["Age Band", "Count"]
        inc_counts["Age Band"] = pd.Categorical(inc_counts["Age Band"],
                                                   categories=age_band_order, ordered=True)
        inc_counts = inc_counts.sort_values("Age Band")
        if PLOTLY:
            fig = px.bar(inc_counts, x="Age Band", y="Count",
                         color="Count", color_continuous_scale="Greens")
            fig.update_layout(margin=dict(t=10, b=10), coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(inc_counts.set_index("Age Band"))

    with col_r:
        st.markdown('<div class="section-title">Income Band Distribution</div>', unsafe_allow_html=True)
        inc_counts = df["Income_Band"].value_counts().reset_index()
        inc_counts.columns = ["Income Band", "Count"]
        inc_counts["Income Band"] = pd.Categorical(inc_counts["Income Band"],
                                                   categories=income_band_order, ordered=True)
        inc_counts = inc_counts.sort_values("Income Band")
        if PLOTLY:
            fig = px.bar(inc_counts, x="Income Band", y="Count",
                         color="Count", color_continuous_scale="Blues")
            fig.update_layout(margin=dict(t=10, b=10), coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(inc_counts.set_index("Income Band"))

    st.markdown("---")
    st.markdown('<div class="section-title">Education & Marital Status Overview</div>', unsafe_allow_html=True)
    col_edu, col_mar = st.columns(2)

    def summary_table(group_col):
        t = df.groupby(group_col).agg(
            Customers=("ID","count"),
            Avg_Income=("Income","mean"),
            Avg_Spend=("Total_Spend","mean"),
            Response_Rate=("Response","mean")
        ).reset_index()
        t["Avg_Income"]    = t["Avg_Income"].map("{:,.0f}".format)
        t["Avg_Spend"]     = t["Avg_Spend"].map("{:,.0f}".format)
        t["Response_Rate"] = (t["Response_Rate"]*100).map("{:.1f}%".format)
        return t

    with col_edu:
        st.dataframe(summary_table("Education"), use_container_width=True, hide_index=True)
    with col_mar:
        st.dataframe(summary_table("Marital_Status"), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════
# TAB 2: CAMPAIGN ANALYSIS
# ══════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Campaign Performance")

    campaigns = {
        "Campaign 1": "AcceptedCmp1", "Campaign 2": "AcceptedCmp2",
        "Campaign 3": "AcceptedCmp3", "Campaign 4": "AcceptedCmp4",
        "Campaign 5": "AcceptedCmp5", "Last Campaign": "Response",
    }
    cmp_data = pd.DataFrame({
        "Campaign": list(campaigns.keys()),
        "Response Rate (%)": [df[col].mean() * 100 for col in campaigns.values()],
        "Total Accepted":    [int(df[col].sum()) for col in campaigns.values()],
    })

    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.markdown('<div class="section-title">Campaign Response Rates (%)</div>', unsafe_allow_html=True)
        if PLOTLY:
            fig = px.bar(cmp_data, x="Campaign", y="Response Rate (%)",
                         color="Response Rate (%)", color_continuous_scale="RdYlGn",
                         text="Response Rate (%)")
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig.update_layout(coloraxis_showscale=False,
                              yaxis_range=[0, cmp_data["Response Rate (%)"].max() * 1.25])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(cmp_data.set_index("Campaign")["Response Rate (%)"])
    with col_b:
        st.markdown('<div class="section-title">Acceptance Count</div>', unsafe_allow_html=True)
        st.dataframe(cmp_data[["Campaign","Total Accepted"]], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown('<div class="section-title">Response Rate by Segment (Last Campaign)</div>', unsafe_allow_html=True)
    seg_resp = df.groupby("Primary_Segment")["Response"].mean().mul(100).reset_index()
    seg_resp.columns = ["Segment", "Response Rate (%)"]
    seg_resp = seg_resp.sort_values("Response Rate (%)", ascending=False)
    if PLOTLY:
        fig = px.bar(seg_resp, x="Segment", y="Response Rate (%)",
                     color="Response Rate (%)", color_continuous_scale="Viridis")
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.bar_chart(seg_resp.set_index("Segment"))

    st.markdown("---")
    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown('<div class="section-title">Response Rate by Income Band</div>', unsafe_allow_html=True)
        inc_resp = df.groupby("Income_Band")["Response"].mean().mul(100).reset_index()
        inc_resp.columns = ["Income Band", "Response Rate (%)"]
        inc_resp["Income Band"] = pd.Categorical(inc_resp["Income Band"],
                                                  categories=income_band_order, ordered=True)
        inc_resp = inc_resp.sort_values("Income Band")
        if PLOTLY:
            fig = px.line(inc_resp, x="Income Band", y="Response Rate (%)", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.line_chart(inc_resp.set_index("Income Band"))
    with col_d:
        st.markdown('<div class="section-title">Response Rate by Age Band</div>', unsafe_allow_html=True)
        age_resp = df.groupby("Age_Band")["Response"].mean().mul(100).reset_index()
        age_resp.columns = ["Age Band", "Response Rate (%)"]
        age_resp["Age Band"] = pd.Categorical(age_resp["Age Band"],
                                               categories=age_band_order, ordered=True)
        age_resp = age_resp.sort_values("Age Band")
        if PLOTLY:
            fig = px.line(age_resp, x="Age Band", y="Response Rate (%)",
                          markers=True, color_discrete_sequence=["#e94560"])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.line_chart(age_resp.set_index("Age Band"))

    st.markdown("---")
    st.markdown('<div class="section-title">Multi-Campaign Acceptance Profile</div>', unsafe_allow_html=True)
    multi = df.groupby("Total_Campaign_Accepted").agg(
        Customers=("ID","count"),
        Avg_Income=("Income","mean"),
        Avg_Spend=("Total_Spend","mean"),
        Avg_Age=("Age","mean")
    ).reset_index().round(0)
    st.dataframe(multi, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════
# TAB 3: SPENDING PATTERNS
# ══════════════════════════════════════════════════════════
with tab3:
    st.markdown("### Spending Patterns")

    product_cols = {
        "Wines": "MntWines", "Fruits": "MntFruits", "Meat": "MntMeatProducts",
        "Fish": "MntFishProducts", "Sweets": "MntSweetProducts", "Gold": "MntGoldProds"
    }

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="section-title">Avg Spend by Product Category</div>', unsafe_allow_html=True)
        cat_spend = pd.DataFrame({
            "Category": list(product_cols.keys()),
            "Avg Spend": [df[v].mean() for v in product_cols.values()]
        }).sort_values("Avg Spend", ascending=False)
        if PLOTLY:
            fig = px.bar(cat_spend, x="Category", y="Avg Spend",
                         color="Avg Spend", color_continuous_scale="Oranges")
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(cat_spend.set_index("Category"))
    with col_b:
        st.markdown('<div class="section-title">Spend by Category (Box Plot)</div>', unsafe_allow_html=True)
        if PLOTLY:
            fig = go.Figure([go.Box(y=df[v], name=k, boxpoints=False)
                             for k, v in product_cols.items()])
            fig.update_layout(margin=dict(t=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.dataframe(df[[v for v in product_cols.values()]].describe().T)

    st.markdown("---")
    st.markdown('<div class="section-title">Avg Spend by Product — by Age Band</div>', unsafe_allow_html=True)

    raw_product_columns = list(product_cols.values())

    age_prod = df.melt(
        id_vars="Age_Band", 
        value_vars=raw_product_columns, 
        var_name="Product", 
        value_name="Spend"
    )

    age_prod['Product'] = (age_prod['Product']
                            .str.replace('Mnt', '', regex=False)
                            .str.replace('Products', '', regex=False)
                            .str.replace('Prods', '', regex=False))

    agg = age_prod.groupby(["Age_Band", "Product"])["Spend"].mean().reset_index()

    age_order = ["18-29", "30-39", "40-49", "50-59", "60-69", "70+"]
    agg["Age_Band"] = pd.Categorical(agg["Age_Band"], categories=age_order, ordered=True)
    agg = agg.sort_values("Age_Band")
    product_color_map = {
        "Wines": "#19D3F3",
        "Fruits": "#EF553B",
        "Meat": "#AB63FA",
        "Fish": "#636EFA",
        "Sweets": "#FFA15A",
        "Gold": "#00CC96"
    }
    if PLOTLY:
        fig = px.bar(
            agg, 
            x="Age_Band", 
            y="Spend", 
            color="Product", 
            barmode="group",
            title="Average Product Spend by Age Band",
            category_orders={'Age_Band': age_order},
            color_discrete_map=product_color_map
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.dataframe(agg.pivot(index="Age_Band", columns="Product", values="Spend").round(0))

    st.markdown("---")
    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown('<div class="section-title">Avg Total Spend by Education</div>', unsafe_allow_html=True)
        edu_sp = df.groupby("Education")["Total_Spend"].mean().sort_values(ascending=False).reset_index()
        edu_sp.columns = ["Education", "Avg Total Spend ()"]
        if PLOTLY:
            fig = px.bar(edu_sp, x="Education", y="Avg Total Spend ()",
                         color="Avg Total Spend ()", color_continuous_scale="Teal")
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(edu_sp.set_index("Education"))
    with col_d:
        st.markdown('<div class="section-title">Avg Total Spend by Country</div>', unsafe_allow_html=True)
        ctry_sp = df.groupby("Country")["Total_Spend"].mean().sort_values(ascending=False).reset_index()
        ctry_sp.columns = ["Country", "Avg Total Spend ()"]
        if PLOTLY:
            fig = px.bar(ctry_sp, x="Country", y="Avg Total Spend ()",
                         color="Avg Total Spend ()", color_continuous_scale="Purples")
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(ctry_sp.set_index("Country"))

    st.markdown("---")
    st.markdown('<div class="section-title">Revenue Contribution by Product Category</div>', unsafe_allow_html=True)
    
    # 1. Prepare the data (Aggregation)
    # Using the same cleaning logic as your other charts
    contribution = df[raw_product_columns].sum().reset_index()
    contribution.columns = ["Product", "Total_Spend"]
    contribution['Product_Label'] = (contribution['Product']
                                     .str.replace('Mnt', '', regex=False)
                                     .str.replace('Products', '', regex=False)
                                     .str.replace('Prods', '', regex=False))

    # 2. Define the Color Map (Shared across your dashboard)
    product_color_map = {
        "Wines": "#19D3F3",
        "Fruits": "#EF553B",
        "Meat": "#AB63FA",
        "Fish": "#636EFA",
        "Sweets": "#FFA15A",
        "Gold": "#00CC96"
    }

    if PLOTLY:
        # 3. Create the Pie Chart
        fig = px.pie(
            contribution,
            names='Product_Label',
            values='Total_Spend',
            color='Product_Label',
            color_discrete_map=product_color_map # Ensures color consistency
        )

        fig.update_traces(
            textinfo='label+percent',
            textfont_size=12,
            # Slight separation for visibility as in your EDA
            pull=[0.05] * len(contribution) 
        )

        fig.update_layout(
            height=500,
            margin=dict(t=0, b=0, l=0, r=0) # Removes excess white space in Streamlit
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Static fallback table if PLOTLY is False
        st.dataframe(contribution[["Product_Label", "Total_Spend"]].set_index("Product_Label"))

# ══════════════════════════════════════════════════════════
# TAB 4: CHANNEL ANALYSIS
# ══════════════════════════════════════════════════════════
with tab4:
    st.markdown("### Channel Analysis")

    channels = {
        "Web Purchases":     "NumWebPurchases",
        "Catalog Purchases": "NumCatalogPurchases",
        "Store Purchases":   "NumStorePurchases",
        "Deal Purchases":    "NumDealsPurchases",
    }

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="section-title">Avg Purchases by Channel</div>', unsafe_allow_html=True)
        ch_avg = pd.DataFrame({
            "Channel": list(channels.keys()),
            "Avg Purchases": [df[v].mean() for v in channels.values()]
        })
        if PLOTLY:
            fig = px.bar(ch_avg, x="Channel", y="Avg Purchases",
                         color="Channel", color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(ch_avg.set_index("Channel"))
    with col_b:
        st.markdown('<div class="section-title">High vs Low Spenders by Channel</div>', unsafe_allow_html=True)
        spend_90 = df["Total_Spend"].quantile(0.9)
        high_sp  = df[df["Total_Spend"] >= spend_90]
        low_sp   = df[df["Total_Spend"] <  df["Total_Spend"].median()]
        compare  = pd.DataFrame({
            "Channel":       list(channels.keys()),
            "High Spenders": [high_sp[v].mean() for v in channels.values()],
            "Low Spenders":  [low_sp[v].mean()  for v in channels.values()],
        })
        if PLOTLY:
            fig = px.bar(
                compare.melt(id_vars="Channel", var_name="Group", value_name="Avg"),
                x="Channel", y="Avg", color="Group", barmode="group"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.dataframe(compare)

    st.markdown("---")
    st.markdown('<div class="section-title">Channel Purchases by Segment</div>', unsafe_allow_html=True)
    seg_ch = df.groupby("Primary_Segment")[[v for v in channels.values()]].mean().round(2).reset_index()
    seg_ch.columns = ["Segment"] + list(channels.keys())
    if PLOTLY:
        fig = px.bar(
            seg_ch.melt(id_vars="Segment", var_name="Channel", value_name="Avg"),
            x="Segment", y="Avg", color="Channel", barmode="group"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.dataframe(seg_ch)

    st.markdown("---")
    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown('<div class="section-title">Web Visits vs Total Spend</div>', unsafe_allow_html=True)
        visit_sp = df.groupby("NumWebVisitsMonth")["Total_Spend"].mean().reset_index()
        visit_sp.columns = ["Web Visits/Month", "Avg Total Spend"]
        if PLOTLY:
            fig = px.scatter(visit_sp, x="Web Visits/Month", y="Avg Total Spend",
                             trendline="lowess", color_discrete_sequence=["#e94560"])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.line_chart(visit_sp.set_index("Web Visits/Month"))
    with col_d:
        st.markdown('<div class="section-title">Under-served Customers</div>', unsafe_allow_html=True)
        under = df[
            (df["NumWebVisitsMonth"] >= 5) &
            (df["Total_Spend"] < df["Total_Spend"].median()) &
            (df["Response"] == 0)
        ]
        st.metric("Under-served Count",   f"{len(under):,}")
        st.metric("Their Avg Income",     f"{under['Income'].mean():,.0f}")
        st.metric("Their Avg Age",        f"{under['Age'].mean():.0f} yrs")
        st.metric("Their Avg Web Visits", f"{under['NumWebVisitsMonth'].mean():.1f}")
        edu_u = under["Education"].value_counts().head(3).reset_index()
        edu_u.columns = ["Education", "Count"]
        st.markdown("**Top Education:**")
        st.dataframe(edu_u, hide_index=True, use_container_width=True)

# ══════════════════════════════════════════════════════════
# TAB 5: CUSTOMER SEGMENTS
# ══════════════════════════════════════════════════════════
with tab5:
    st.markdown("### Customer Segment Deep-Dive")

    seg_summary = df.groupby("Primary_Segment").agg(
        Customers=("ID","count"),
        Avg_Income=("Income","mean"),
        Avg_Age=("Age","mean"),
        Avg_Spend=("Total_Spend","mean"),
        Response_Rate=("Response","mean"),
        Avg_Web_Visits=("NumWebVisitsMonth","mean"),
        Avg_Children=("Children","mean")
    ).round(1).reset_index()
    seg_summary["Response_Rate"] = (seg_summary["Response_Rate"] * 100).round(1)
    seg_summary.columns = ["Segment","Customers","Avg Income","Avg Age",
                           "Avg Spend","Response Rate (%)","Avg Web Visits","Avg Children"]
    st.dataframe(seg_summary.sort_values("Avg Spend", ascending=False),
                 use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown('<div class="section-title">Segment KPI Radar</div>', unsafe_allow_html=True)
    if PLOTLY:
        metrics = ["Avg Income","Avg Spend","Response Rate (%)","Avg Web Visits"]
        radar_data = seg_summary.set_index("Segment")[metrics]
        radar_norm = (radar_data - radar_data.min()) / (radar_data.max() - radar_data.min())
        fig = go.Figure()
        for seg in radar_norm.index:
            vals = radar_norm.loc[seg].tolist()
            fig.add_trace(go.Scatterpolar(
                r=vals + [vals[0]], theta=metrics + [metrics[0]],
                fill="toself", name=seg, opacity=0.7
            ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                          margin=dict(t=40))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="section-title">Age Distribution by Segment</div>', unsafe_allow_html=True)
        if PLOTLY:
            fig = px.box(df, x="Primary_Segment", y="Age", color="Primary_Segment",
                         color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_layout(showlegend=False, xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.dataframe(df.groupby("Primary_Segment")["Age"].describe())
    with col_b:
        st.markdown('<div class="section-title">Income Distribution by Segment</div>', unsafe_allow_html=True)
        if PLOTLY:
            fig = px.box(df, x="Primary_Segment", y="Income", color="Primary_Segment",
                         color_discrete_sequence=px.colors.qualitative.Pastel2)
            fig.update_layout(showlegend=False, xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.dataframe(df.groupby("Primary_Segment")["Income"].describe())

    st.markdown("---")
    st.markdown('<div class="section-title"> Ideal Target Customer Profile</div>', unsafe_allow_html=True)
    st.info("High income (>75K) + any campaign accepted + above-median spend")
    ideal = df[
        (df["Income"] > 75000) &
        (df["Any_Campaign_Accepted"] == 1) &
        (df["Total_Spend"] > df["Total_Spend"].median())
    ]
    if len(ideal) > 0:
        col_i1, col_i2, col_i3, col_i4 = st.columns(4)
        with col_i1: st.metric("Count",       f"{len(ideal):,}")
        with col_i2: st.metric("Avg Age",     f"{ideal['Age'].mean():.0f}")
        with col_i3: st.metric("Avg Income",  f"{ideal['Income'].mean():,.0f}")
        with col_i4: st.metric("Avg Spend",   f"{ideal['Total_Spend'].mean():,.0f}")
        ideal_profile = ideal.groupby(["Age_Band","Education"]).agg(
            Count=("ID","count"),
            Avg_Spend=("Total_Spend","mean"),
            Response_Rate=("Response","mean")
        ).round(1).reset_index()
        ideal_profile["Response_Rate"] = (ideal_profile["Response_Rate"]*100).round(1)
        ideal_profile = ideal_profile.sort_values("Response_Rate", ascending=False).head(10)
        st.dataframe(ideal_profile, use_container_width=True, hide_index=True)
    else:
        st.warning("No ideal customers match current filters.")


# ══════════════════════════════════════════════════════════
# TAB 6: AI DATA EXPLORER
# ══════════════════════════════════════════════════════════
with tab6:
    st.markdown("###  AI Data Explorer")
    st.markdown(
        "Type any question in plain English. AI will generate a query, "
        "run it, and show you the result as a table or chart."
    )

    # ── Schema context sent to Claude ──────────────────────
    COLUMN_DESCRIPTIONS = """
You have access to a pandas DataFrame called `df` with the following columns.
All monetary values are in USD. The data is already filtered by the sidebar.

DEMOGRAPHICS
  ID                      : Unique customer identifier (int)
  Year_Birth              : Customer birth year (int)
  Age                     : Derived age as of 2015 (int)
  Age_Band                : Age group string: 18-29 | 30-39 | 40-49 | 50-59 | 60-69 | 70+
  Education               : Graduation | Master | PhD | 2n Cycle | Basic
  Marital_Status          : Married | Together | Single | Divorced | Widow
  Income                  : Annual household income (float)
  Income_Band             : <25K | 25K-50K | 50K-75K | 75K-100K | >100K
  Kidhome                 : Number of children at home (int)
  Teenhome                : Number of teenagers at home (int)
  Children                : Kidhome + Teenhome (int)
  Country                 : Spain | Canada | Saudi Arabia | Australia | India | Germany | USA | Mexico
  Dt_Customer             : Enrollment date string YYYY-MM-DD
  Customer_Tenure_Days    : Days since enrollment (int)
  Customer_Tenure_Months  : Months since enrollment (int)
  Recency                 : Days since last purchase (int)
  Complain                : 1 if complained in last 2 years, else 0

SPENDING (last 2 years)
  MntWines                : Amount spent on wine (int)
  MntFruits               : Amount spent on fruit (int)
  MntMeatProducts         : Amount spent on meat (int)
  MntFishProducts         : Amount spent on fish (int)
  MntSweetProducts        : Amount spent on sweets (int)
  MntGoldProds            : Amount spent on gold (int)
  Total_Spend             : Sum of all Mnt* columns (float)

PURCHASES BY CHANNEL
  NumWebPurchases         : Purchases via website (int)
  NumCatalogPurchases     : Purchases via catalogue (int)
  NumStorePurchases       : Purchases in store (int)
  NumDealsPurchases       : Purchases using discounts/deals (int)
  Total_Purchases         : Sum of all channel purchases (int)
  NumWebVisitsMonth       : Website visits in last month (int)

CAMPAIGN FLAGS  (1 = accepted, 0 = rejected)
  AcceptedCmp1 ... AcceptedCmp5 : Campaigns 1-5
  Response                       : Last/most recent campaign
  Total_Campaign_Accepted        : Total campaigns accepted (0-6)
  Any_Campaign_Accepted          : 1 if accepted at least one campaign, else 0

SEGMENTS
  Primary_Segment         : Premium | High Income | High Spender | Campaign Responder |
                            Web Engaged | Family | Young | Standard
  Seg_High_Income         : 1 if Income > 75000
  Seg_Young_Customer      : 1 if Age < 30
  Seg_Campaign_Responder  : 1 if Response == 1
  Seg_High_Web_Engagement : 1 if NumWebVisitsMonth > 5
  Seg_Family_Customer     : 1 if Children > 0
  Seg_High_Spender        : 1 if Total_Spend > 90th percentile
"""

    SYSTEM_PROMPT = f"""You are a data analyst assistant. The user will ask questions about a
marketing customer dataset. You must respond with a JSON object — nothing else, no markdown fences.

The JSON must have exactly these keys:
  "explanation" : 1-2 sentence plain-English description of what the result shows
  "code"        : valid Python code that operates on a pandas DataFrame called `df`
                  and stores the final result in a variable called `result`.
                  `result` must be a pandas DataFrame or Series.
                  Do NOT import anything — pandas (pd), numpy (np) are already available.
                  Do NOT use .plot() or matplotlib — only produce a DataFrame/Series.
  "chart_type"  : one of "table" | "bar" | "line" | "scatter" | "pie"
                  Choose the most appropriate type for the data returned.
  "x_col"       : column name to use as x-axis  (null if chart_type is "table" or "pie")
  "y_col"       : column name to use as y-axis  (null if chart_type is "table")
  "color_col"   : column name to colour by      (null if not needed)

Rules for the code:
  - Always reset_index() before assigning to `result` if groupby is used.
  - Column names are case-sensitive — use exact names from the schema.
  - For percentage calculations multiply by 100 and round to 2 decimal places.
  - If the question is unanswerable with the available columns, set code to:
      result = pd.DataFrame({{"error": ["Column or data not available"]}})

Dataset schema:
{COLUMN_DESCRIPTIONS}
"""

    # ── Helper: call AI provider ────────────────────────────
    def ask_claude(user_question: str) -> dict:
        """Send prompt to the configured AI provider and return parsed JSON."""

        fallback = {
            "explanation": "",
            "code": 'result = pd.DataFrame({"error": ["AI provider not configured — check settings at top of app_mysql.py"]})',
            "chart_type": "table", "x_col": None, "y_col": None, "color_col": None,
        }

        messages_payload = [{"role": "user", "content": user_question}]

        # ── GROQ ──────────────────────────────────────────────
        if AI_PROVIDER == "groq":
            if not GROQ_API_KEY:
                fallback["code"] = 'result = pd.DataFrame({"error": ["GROQ_API_KEY not set"]})'
                return fallback
            try:
                from groq import Groq
            except ImportError:
                fallback["code"] = 'result = pd.DataFrame({"error": ["Run: pip install groq"]})'
                return fallback
            client = Groq(api_key=GROQ_API_KEY)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_question},
                ],
                temperature=0.1,
                max_tokens=1024,
            )
            raw = response.choices[0].message.content.strip()

        # ── GEMINI ─────────────────────────────────────────────
        elif AI_PROVIDER == "gemini":
            if not GEMINI_API_KEY:
                fallback["code"] = 'result = pd.DataFrame({"error": ["GEMINI_API_KEY not set"]})'
                return fallback
            try:
                import google.generativeai as genai
            except ImportError:
                fallback["code"] = 'result = pd.DataFrame({"error": ["Run: pip install google-generativeai"]})'
                return fallback
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=SYSTEM_PROMPT,
            )
            resp = model.generate_content(user_question)
            raw = resp.text.strip()

        # ── OLLAMA (local) ─────────────────────────────────────
        elif AI_PROVIDER == "ollama":
            try:
                import urllib.request
                body = json.dumps({
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": user_question},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.1},
                }).encode()
                req = urllib.request.Request(
                    f"{OLLAMA_URL}/api/chat",
                    data=body,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=600) as resp:
                    data = json.loads(resp.read())
                raw = data["message"]["content"].strip()
            except Exception as e:
                fallback["code"] = f'result = pd.DataFrame({{"error": ["Ollama error: {e}"]}})'
                return fallback

        else:
            fallback["code"] = 'result = pd.DataFrame({"error": ["Unknown AI_PROVIDER — use groq / gemini / ollama"]})'
            return fallback

        # ── Parse JSON from any provider's response ────────────
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```", "",         raw)
        # Some models wrap in extra text — extract first {...} block
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            raw = match.group(0)
        return json.loads(raw)

    # ── Helper: execute generated code safely ───────────────
    def run_code(code: str, df: pd.DataFrame) -> pd.DataFrame:
        local_vars = {"df": df.copy(), "pd": pd, "np": np}
        exec(code, {}, local_vars)          # restricted namespace
        result = local_vars.get("result")
        if isinstance(result, pd.Series):
            result = result.reset_index()
            result.columns = [str(c) for c in result.columns]
        return result

    # ── Helper: render result ───────────────────────────────
    def render_result(result: pd.DataFrame, parsed: dict):
        chart_type = parsed.get("chart_type", "table")
        x_col      = parsed.get("x_col")
        y_col      = parsed.get("y_col")
        color_col  = parsed.get("color_col")

        # Validate column names against actual result
        cols = result.columns.tolist()
        if x_col     not in cols: x_col     = cols[0] if cols else None
        if y_col     not in cols: y_col     = cols[1] if len(cols) > 1 else None
        if color_col not in cols: color_col = None

        if chart_type == "table" or not PLOTLY or x_col is None:
            st.dataframe(result, use_container_width=True)
            return

        try:
            if chart_type == "bar":
                fig = px.bar(result, x=x_col, y=y_col, color=color_col,
                             color_discrete_sequence=px.colors.qualitative.Set2)
            elif chart_type == "line":
                fig = px.line(result, x=x_col, y=y_col, color=color_col, markers=True)
            elif chart_type == "scatter":
                fig = px.scatter(result, x=x_col, y=y_col, color=color_col, opacity=0.6)
            elif chart_type == "pie":
                fig = px.pie(result, names=x_col, values=y_col,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            else:
                st.dataframe(result, use_container_width=True)
                return
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            # Fallback to table if chart fails
            st.dataframe(result, use_container_width=True)

    # ── Conversation history (persisted in session state) ───
    if "ai_history" not in st.session_state:
        st.session_state.ai_history = []   # list of {"role","content","result","parsed"}

    # ── Example prompts ─────────────────────────────────────
    st.markdown("**Try these examples:**")
    examples = [
        "Show average total spend by country, sorted highest to lowest",
        "What is the response rate for each education level?",
        "Top 10 customers by total spend with their age, income and segment"
    ]
    cols = st.columns(4)
    for i, ex in enumerate(examples):
        if cols[i % 4].button(ex, key=f"ex_{i}", use_container_width=True):
            st.session_state["prefill_prompt"] = ex

    st.markdown("---")

    # ── Prompt input ────────────────────────────────────────
    prefill = st.session_state.pop("prefill_prompt", "")
    user_input = st.chat_input(
        placeholder="e.g. Show me average spend by country sorted by highest first…"
    )
    # Also allow example button prefills
    if not user_input and prefill:
        user_input = prefill

    # ── Process new prompt ──────────────────────────────────
    if user_input:
        st.session_state.ai_history.append(
            {"role": "user", "content": user_input, "result": None, "parsed": None}
        )
        with st.spinner("analysing your request…"):
            try:
                parsed = ask_claude(user_input)
                result = run_code(parsed["code"], df)
                st.session_state.ai_history[-1]["result"] = result
                st.session_state.ai_history[-1]["parsed"] = parsed
            except json.JSONDecodeError as e:
                st.session_state.ai_history[-1]["result"] = pd.DataFrame(
                    {"error": [f"Could not parse Claude response: {e}"]}
                )
                st.session_state.ai_history[-1]["parsed"] = {"chart_type": "table"}
            except Exception as e:
                st.session_state.ai_history[-1]["result"] = pd.DataFrame(
                    {"error": [f"Code execution error: {e}"]}
                )
                st.session_state.ai_history[-1]["parsed"] = {"chart_type": "table"}

    # ── Render conversation history ─────────────────────────
    for turn in reversed(st.session_state.ai_history):
        with st.chat_message("user"):
            st.write(turn["content"])

        if turn["result"] is not None:
            with st.chat_message("assistant"):
                parsed = turn["parsed"] or {}
                explanation = parsed.get("explanation", "")
                if explanation:
                    st.markdown(f"**{explanation}**")
                render_result(turn["result"], parsed)

                # Download button for every result
                csv_bytes = turn["result"].to_csv(index=False).encode()
                st.download_button(
                    label="Download as CSV",
                    data=csv_bytes,
                    file_name="ai_query_result.csv",
                    mime="text/csv",
                    key=f"dl_{id(turn)}",
                )

    # ── Clear history button ────────────────────────────────
    if st.session_state.ai_history:
        st.markdown("---")
        if st.button("Clear conversation", type="secondary"):
            st.session_state.ai_history = []
            st.rerun()

    # ── Provider status warning ─────────────────────────────
    key_missing = (
        (AI_PROVIDER == "groq"   and not GROQ_API_KEY) or
        (AI_PROVIDER == "gemini" and not GEMINI_API_KEY)
    )
    if key_missing:
        provider_links = {
            "groq":   ("GROQ_API_KEY",   "console.groq.com",       "pip install groq"),
            "gemini": ("GEMINI_API_KEY", "aistudio.google.com",    "pip install google-generativeai"),
        }
        var, url, pkg = provider_links[AI_PROVIDER]
        st.warning(
            f"**{var} is not set.**\n\n"
            f"1. Get a free key at [{url}](https://{url})\n"
            f"2. Install the package: `{pkg}`\n"
            f"3. Paste the key at the top of `app_mysql.py`:\n"
            f"```\n{var} = \"your-key-here\"\n```\n"
            f"or set it as an environment variable:\n"
            f"```\nexport {var}=\"your-key-here\"\nstreamlit run app_mysql.py\n```"
        )
    if AI_PROVIDER == "ollama":
        st.info(
            " **Using Ollama (local).** Make sure Ollama is running:\n"
            f"```\nollama serve\nollama pull {OLLAMA_MODEL}\n```"
        )
