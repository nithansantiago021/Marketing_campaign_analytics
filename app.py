"""
Marketing Campaign Analytics Dashboard
Streamlit App — SQLite / MySQL Production Version

Run:
    streamlit run app.py

Prerequisites:
    pip install streamlit plotly pandas sqlalchemy pymysql groq python-dotenv
"""

import json
import os
import re
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from groq import Groq
import streamlit as st
from sqlalchemy import create_engine

# Load Environment Variables (.env)
load_dotenv()

# ─── DATABASE CONNECTION SETTINGS ──────────────────────────
# Defaulting to your local SQLite file database for portable hosting.
# To toggle back to a remote MySQL production cluster, swap the comments below.
DB_URL = "sqlite:///marketing_clean.db"

try:
    engine = create_engine(DB_URL, pool_pre_ping=True)
except Exception:
    engine = None
# ──────────────────────────────────────────────────────────

# ─── AI PROVIDER CONFIGURATION (GROQ) ─────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"
# ──────────────────────────────────────────────────────────

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY = True
except ImportError:
    PLOTLY = False

# ─── Page Config ───────────────────────────────────────────
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

# ─── Data Loading ──────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    """Load the customers table into a DataFrame."""
    if engine is None:
        st.error("Database engine could not be initialized. Verify database credentials/paths.")
        st.stop()
    try:
        df = pd.read_sql("SELECT * FROM customers", con=engine)
    except Exception as e:
        st.error(
            f"Could not connect to database table.\n\n"
            f"Error Details: {e}\n\n"
            f"Troubleshooting actions:\n"
            f"1. Verify your database connection settings/files.\n"
            f"2. Ensure you have parsed your data into a table named 'customers'."
        )
        st.stop()
    return df

df_full = load_data()

# ─── Sidebar Filters ───────────────────────────────────────
st.sidebar.title("Filters")
st.sidebar.markdown("---")

def make_filter(label, col):
    opts = ["All"] + sorted(df_full[col].dropna().unique().tolist())
    return st.sidebar.selectbox(label, opts)

selected_country      = make_filter("Country",        "Country")
selected_education    = make_filter("Education",      "Education")
selected_marital      = make_filter("Marital Status", "Marital_Status")

age_band_order   = ["18-29", "30-39", "40-49", "50-59", "60-69", "70+"]
income_band_order = ["<25K", "25K-50K", "50K-75K", "75K-100K", ">100K"]

ab_opts = ["All"] + [b for b in age_band_order    if b in df_full["Age_Band"].values]
ib_opts = ["All"] + [b for b in income_band_order if b in df_full["Income_Band"].values]
selected_age_band    = st.sidebar.selectbox("Age Band",    ab_opts)
selected_income_band = st.sidebar.selectbox("Income Band", ib_opts)
selected_segment     = make_filter("Segment", "Primary_Segment")

st.sidebar.markdown("---")
st.sidebar.caption("Connected Infrastructure Active")

# Apply filters to target slice
df = df_full.copy()
if selected_country      != "All": df = df[df["Country"]        == selected_country]
if selected_education    != "All": df = df[df["Education"]      == selected_education]
if selected_marital      != "All": df = df[df["Marital_Status"] == selected_marital]
if selected_age_band     != "All": df = df[df["Age_Band"]       == selected_age_band]
if selected_income_band  != "All": df = df[df["Income_Band"]    == selected_income_band]
if selected_segment      != "All": df = df[df["Primary_Segment"]== selected_segment]

# ─── Header ────────────────────────────────────────────────
st.title("Marketing Campaign Analytics Dashboard")
st.markdown(f"Showing **{len(df):,}** customers (filtered from {len(df_full):,} total)")
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
    with col2: st.metric("Avg Income",       f"${df['Income'].mean():,.0f}")
    with col3: st.metric("Avg Total Spend",  f"${df['Total_Spend'].mean():,.0f}")
    with col4: st.metric("Response Rate (latest)",    f"{df['Response'].mean()*100:.1f}%")
    with col5: st.metric("Avg Age",          f"{df['Age'].mean():.0f} yrs")

    st.markdown("---")
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown('<div class="section-title">Age Band Distribution</div>', unsafe_allow_html=True)
        inc_counts = df["Age_Band"].value_counts().reset_index()
        inc_counts.columns = ["Age Band", "Count"]
        inc_counts["Age Band"] = pd.Categorical(inc_counts["Age Band"], categories=age_band_order, ordered=True)
        inc_counts = inc_counts.sort_values("Age Band")
        if PLOTLY:
            fig = px.bar(inc_counts, x="Age Band", y="Count", color="Count", color_continuous_scale="Greens")
            fig.update_layout(margin=dict(t=10, b=10), coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(inc_counts.set_index("Age Band"))

    with col_r:
        st.markdown('<div class="section-title">Income Band Distribution</div>', unsafe_allow_html=True)
        inc_counts = df["Income_Band"].value_counts().reset_index()
        inc_counts.columns = ["Income Band", "Count"]
        inc_counts["Income Band"] = pd.Categorical(inc_counts["Income Band"], categories=income_band_order, ordered=True)
        inc_counts = inc_counts.sort_values("Income Band")
        if PLOTLY:
            fig = px.bar(inc_counts, x="Income Band", y="Count", color="Count", color_continuous_scale="Blues")
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
        t["Avg_Income"]    = t["Avg_Income"].map("${:,.0f}".format)
        t["Avg_Spend"]     = t["Avg_Spend"].map("${:,.0f}".format)
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
            fig = px.bar(cmp_data, x="Campaign", y="Response Rate (%)", color="Response Rate (%)", color_continuous_scale="RdYlGn", text="Response Rate (%)")
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig.update_layout(coloraxis_showscale=False, yaxis_range=[0, cmp_data["Response Rate (%)"].max() * 1.25])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(cmp_data.set_index("Campaign")["Response Rate (%)"])
    with col_b:
        st.markdown('<div class="section-title">Acceptance Count</div>', unsafe_allow_html=True)
        st.dataframe(cmp_data[["Campaign","Total Accepted"]], use_container_width=True, hide_index=True)

    st.markdown("---")
    # ─── New Segment Campaign Uplift Analysis ─────────────────
    st.markdown('<div class="section-title">Segment Campaign Acceptance Uplift (%)</div>', unsafe_allow_html=True)
    
    seg_cols = ['Seg_High_Income', 'Seg_Young_Customer', 'Seg_High_Web_Engagement',
                'Seg_Family_Customer', 'Seg_High_Spender']

    summary = []
    for col in seg_cols:
        # Check if column exists in the active data dataframe slice
        if col in df.columns:
            # Slices for segment vs non-segment
            seg_slice = df.loc[df[col] == 1, "Total_Campaign_Accepted"]
            non_seg_slice = df.loc[df[col] == 0, "Total_Campaign_Accepted"]
            
            # Safeguard against empty slices caused by aggressive sidebar filters
            if len(seg_slice) > 0 and len(non_seg_slice) > 0:
                segment_avg = seg_slice.mean()
                non_segment_avg = non_seg_slice.mean()
                
                # Prevent division by zero if non-segment average is 0
                if non_segment_avg > 0:
                    pct_uplift = ((segment_avg - non_segment_avg) / non_segment_avg) * 100
                else:
                    pct_uplift = 0.0

                summary.append({
                    "Segment": col.replace("Seg_", "").replace("_", " "),
                    "Non-Segment Avg": round(non_segment_avg, 3),
                    "Segment Avg": round(segment_avg, 3),
                    "Pct_Uplift": round(pct_uplift, 1)
                })

    if summary:
        summary_df = pd.DataFrame(summary)
        
        if PLOTLY:
            # Generate the horizontal bar chart exactly like your EDA notebook
            fig = px.bar(
                summary_df.sort_values("Pct_Uplift"),
                x="Pct_Uplift", 
                y="Segment", 
                orientation="h",
                color="Pct_Uplift", 
                color_continuous_scale="RdYlGn",
                text="Pct_Uplift"
            )
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig.update_layout(
                height=400, 
                xaxis_title="% Uplift vs Non-Segment",
                yaxis_title="",
                coloraxis_showscale=False,
                margin=dict(l=20, r=40, t=10, b=10) # Clean formatting adjustments for layout container
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Native fallback table view if Plotly dependencies fail to load
            st.dataframe(summary_df.sort_values("Pct_Uplift", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.warning("Insufficient data available in the current filtered view to calculate segment uplift metrics.")
        
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
            fig = px.bar(cat_spend, x="Category", y="Avg Spend", color="Avg Spend", color_continuous_scale="Oranges")
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(cat_spend.set_index("Category"))
    with col_b:
        st.markdown('<div class="section-title">Spend by Category (Box Plot)</div>', unsafe_allow_html=True)
        if PLOTLY:
            fig = go.Figure([go.Box(y=df[v], name=k, boxpoints=False) for k, v in product_cols.items()])
            fig.update_layout(margin=dict(t=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.dataframe(df[[v for v in product_cols.values()]].describe().T)

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
            fig = px.bar(ch_avg, x="Channel", y="Avg Purchases", color="Channel", color_discrete_sequence=px.colors.qualitative.Pastel)
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
            fig = px.bar(compare.melt(id_vars="Channel", var_name="Group", value_name="Avg"), x="Channel", y="Avg", color="Group", barmode="group")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.dataframe(compare)

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
    seg_summary.columns = ["Segment","Customers","Avg Income","Avg Age","Avg Spend","Response Rate (%)","Avg Web Visits","Avg Children"]
    st.dataframe(seg_summary.sort_values("Avg Spend", ascending=False), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════
# TAB 6: AI DATA EXPLORER (GROQ ENGINE)
# ══════════════════════════════════════════════════════════
with tab6:
    st.markdown("### 🤖 Groq Data Explorer")
    st.markdown(
        "Type any analysis instruction or question in plain English. "
        "The model will write the appropriate execution code against the active data dataframe."
    )

    COLUMN_DESCRIPTIONS = """
You have access to a pandas DataFrame called `df` with the following columns. All monetary values are in USD.

DEMOGRAPHICS
  ID                      : Unique customer identifier (int)
  Year_Birth              : Customer birth year (int)
  Age                     : Derived age as of 2015 (int)
  Age_Band                : 18-29 | 30-39 | 40-49 | 50-59 | 60-69 | 70+
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

CAMPAIGN FLAGS (1 = accepted, 0 = rejected)
  AcceptedCmp1 ... AcceptedCmp5 : Campaigns 1-5
  Response                       : Last campaign
  Total_Campaign_Accepted        : Total campaigns accepted (0-6)
  Any_Campaign_Accepted          : 1 if accepted at least one campaign, else 0

SEGMENTS
  Primary_Segment         : Premium | High Income | High Spender | Campaign Responder | Web Engaged | Family | Young | Standard
"""

    SYSTEM_PROMPT = f"""You are an elite data scientist assistant. You evaluate instructions about a marketing dataset.
You MUST respond exclusively with a valid JSON block containing zero markdown formatting structures.

The JSON formatting layout required:
{{
  "explanation" : "A brief summary of what the data segment presents.",
  "code"        : "Valid Python logic processing data frame `df` storing outcomes into variable `result`. `result` must be a pandas DataFrame or Series. Do not import pandas or numpy.",
  "chart_type"  : "table" | "bar" | "line" | "scatter" | "pie",
  "x_col"       : "Column title string mapping to X axes mapping parameters (or null if table/pie)",
  "y_col"       : "Column title string mapping to Y axes mapping parameters (or null if table)"
}}

Rules:
- Always call reset_index() on groupby summaries.
- If unanswerable, set: result = pd.DataFrame({{"error": ["Information missing."]}})

Dataset Schema Context:
{COLUMN_DESCRIPTIONS}
"""

    def ask_groq(user_question: str) -> dict:
        """Query Groq via official library wrapper implementation."""
        fallback = {
            "explanation": "Execution Error",
            "code": 'result = pd.DataFrame({"error": ["Groq pipeline error encountered."]})',
            "chart_type": "table", "x_col": None, "y_col": None
        }

        if not GROQ_API_KEY:
            fallback["code"] = 'result = pd.DataFrame({"error": ["GROQ_API_KEY environment configuration missing."]})'
            return fallback

        try:
            client = Groq(api_key=GROQ_API_KEY)
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_question}
                ],
                temperature=0.1,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content.strip()
            return json.loads(raw)
        except Exception as e:
            fallback["code"] = f'result = pd.DataFrame({{"error": ["Error communicating with Groq: {e}"]}})'
            return fallback

    def run_code(code: str, df: pd.DataFrame) -> pd.DataFrame:
        local_vars = {"df": df.copy(), "pd": pd, "np": np}
        exec(code, {}, local_vars)
        result = local_vars.get("result")
        if isinstance(result, pd.Series):
            result = result.reset_index()
            result.columns = [str(c) for c in result.columns]
        return result

    def render_result(result: pd.DataFrame, parsed: dict):
        chart_type = parsed.get("chart_type", "table")
        x_col      = parsed.get("x_col")
        y_col      = parsed.get("y_col")

        cols = result.columns.tolist()
        if x_col not in cols: x_col = cols[0] if cols else None
        if y_col not in cols: y_col = cols[1] if len(cols) > 1 else None

        if chart_type == "table" or not PLOTLY or x_col is None:
            st.dataframe(result, use_container_width=True)
            return

        try:
            if chart_type == "bar":
                fig = px.bar(result, x=x_col, y=y_col, color_discrete_sequence=px.colors.qualitative.Set2)
            elif chart_type == "line":
                fig = px.line(result, x=x_col, y=y_col, markers=True)
            elif chart_type == "scatter":
                fig = px.scatter(result, x=x_col, y=y_col, opacity=0.7)
            elif chart_type == "pie":
                fig = px.pie(result, names=x_col, values=y_col, color_discrete_sequence=px.colors.qualitative.Pastel)
            else:
                st.dataframe(result, use_container_width=True)
                return
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.dataframe(result, use_container_width=True)

    # Persistent Session History initialization
    if "ai_history" not in st.session_state:
        st.session_state.ai_history = []

    # Quick Analysis Presets
    st.markdown("**Try these preset requests:**")
    examples = [
        "Show average total spend by country, sorted highest to lowest",
        "What is the response rate for each education level?",
        "Top 10 customers by total spend with their age, income and segment"
    ]
    cols = st.columns(3)
    for i, ex in enumerate(examples):
        if cols[i].button(ex, key=f"ex_{i}", use_container_width=True):
            st.session_state["prefill_prompt"] = ex

    st.markdown("---")

    # Dynamic inputs configuration
    prefill = st.session_state.pop("prefill_prompt", "")
    user_input = st.chat_input(placeholder="Ask anything about the target cohort parameters...")
    
    if not user_input and prefill:
        user_input = prefill

    if user_input:
        st.session_state.ai_history.append({"role": "user", "content": user_input, "result": None, "parsed": None})
        with st.spinner("Analyzing request via Groq pipeline..."):
            try:
                parsed = ask_groq(user_input)
                result = run_code(parsed["code"], df)
                st.session_state.ai_history[-1]["result"] = result
                st.session_state.ai_history[-1]["parsed"] = parsed
            except Exception as e:
                st.session_state.ai_history[-1]["result"] = pd.DataFrame({"error": [f"Pipeline compilation error: {e}"]})
                st.session_state.ai_history[-1]["parsed"] = {"chart_type": "table"}

    # Display History Stream
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

                csv_bytes = turn["result"].to_csv(index=False).encode()
                st.download_button(
                    label="Download Result Set (CSV)",
                    data=csv_bytes,
                    file_name="groq_analysis_output.csv",
                    mime="text/csv",
                    key=f"dl_{id(turn)}",
                )

    if st.session_state.ai_history:
        st.markdown("---")
        if st.button("Clear Conversation Stream", type="secondary"):
            st.session_state.ai_history = []
            st.rerun()

    # Dynamic Global Key Status Checker Warnings
    if not GROQ_API_KEY:
        st.warning(
            "⚠️ **GROQ_API_KEY Missing.**\n\n"
            "Provide your key via a local `.env` configuration template file:\n"
            "```env\nGROQ_API_KEY=\"gsk_your_key_here\"\n```"
        )