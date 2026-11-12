"""Nifty 100 Financial Intelligence Platform — Main Application Entry Point.

Sprint 4: Interactive Dashboard (Module 5).
Run via: `streamlit run app.py`
Provides global multi-page navigation, executive summary, and quick launchpad.
"""

import numpy as np
import pandas as pd
import streamlit as st

from src.dashboard.utils.charts import plot_sector_donut
from src.dashboard.utils.db import load_universe_data


st.set_page_config(
    page_title="Nifty 100 Intelligence Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%);
        padding: 28px 32px;
        border-radius: 12px;
        color: white;
        margin-bottom: 24px;
    }
    .metric-card {
        background-color: #F8F9FA;
        border: 1px solid #E9ECEF;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .nav-card {
        background: white;
        border: 1px solid #DEE2E6;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        transition: transform 0.2s;
    }
</style>
""", unsafe_allow_html=True)

# Hero Banner
st.markdown("""
<div class="main-header">
    <h1 style="color: white; margin: 0; font-size: 2.3rem;">📊 Nifty 100 Financial Intelligence Platform</h1>
    <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 1.1rem;">
        Enterprise Financial Statement Analysis, Screener & Valuation Intelligence Suite
    </p>
</div>
""", unsafe_allow_html=True)

df_u = load_universe_data()

# Executive Summary Metrics
c1, c2, c3, c4, c5 = st.columns(5)
total_mkt_cap = df_u["market_cap_crore"].sum() / 1e5
avg_roe = df_u["return_on_equity_pct"].replace([np.inf, -np.inf], np.nan).mean()
med_pe = df_u["pe_ratio"].median()
total_fcf = df_u["free_cash_flow_cr"].sum() / 1000
debt_free_count = (df_u["debt_to_equity"].fillna(0) <= 0.05).sum()

c1.metric("Constituents", f"{len(df_u)} Cos", "Nifty 100")
c2.metric("Index Market Cap", f"₹ {total_mkt_cap:.2f} L Cr", "FY2024")
c3.metric("Average Index ROE", f"{avg_roe:.1f}%", "Profitability")
c4.metric("Median P/E Multiple", f"{med_pe:.1f}x", "Valuation")
c5.metric("Debt-Free Leaders", f"{debt_free_count} Cos", "D/E ≤ 0.05")

st.markdown("---")

# Navigation Launchpad (8 Screens)
st.subheader("🧭 Platform Navigation & Modules (8 Screens)")
st.markdown("Select any screen from the sidebar or choose from the executive modules below:")

row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4)

with row1_col1:
    st.markdown("""
    #### 🏠 1. Overview
    Macro index health, market cap aggregation, and sector diversification breakdown.
    """)
    st.page_link("pages/01_Home.py", label="Open Home Screen", icon="👉")

with row1_col2:
    st.markdown("""
    #### 🏢 2. Company Profile
    Search 92 companies: KPI dossier, 10-year P&L, Balance Sheet, and Cash Flow charts.
    """)
    st.page_link("pages/02_Company_Profile.py", label="Open Company Profile", icon="👉")

with row1_col3:
    st.markdown("""
    #### 🔍 3. Financial Screener
    6 institutional presets and 10 custom threshold sliders with real-time CSV export.
    """)
    st.page_link("pages/03_Financial_Screener.py", label="Open Screener", icon="👉")

with row1_col4:
    st.markdown("""
    #### 👥 4. Peer Comparison
    Intra-group benchmarking across 11 peer groups with 8-axis Plotly polar radar charts.
    """)
    st.page_link("pages/04_Peer_Comparison.py", label="Open Peer Engine", icon="👉")

row2_col1, row2_col2, row2_col3, row2_col4 = st.columns(4)

with row2_col1:
    st.markdown("""
    #### 📈 5. Trend Analysis
    10-year sparklines, YoY growth momentum, and multi-metric historical overlays.
    """)
    st.page_link("pages/05_Trend_Analysis.py", label="Open Trend Analytics", icon="👉")

with row2_col2:
    st.markdown("""
    #### 🌐 6. Sector Analysis
    Interactive Revenue vs. ROE bubble charts and sector median financial KPI rankings.
    """)
    st.page_link("pages/06_Sector_Analysis.py", label="Open Sector Analysis", icon="👉")

with row2_col3:
    st.markdown("""
    #### 🗺️ 7. Capital Allocation
    Treemap classifying all 92 companies into the 8 canonical CFO/CFI/CFF cash flow patterns.
    """)
    st.page_link("pages/07_Capital_Allocation_Map.py", label="Open Capital Map", icon="👉")

with row2_col4:
    st.markdown("""
    #### 📑 8. Annual Reports
    Searchable regulatory document intelligence repository with clickable BSE/NSE links.
    """)
    st.page_link("pages/08_Annual_Reports.py", label="Open Annual Reports", icon="👉")

st.markdown("---")

# Quick Sector Composition Visualization
chart_col, table_col = st.columns([1, 1])

with chart_col:
    st.plotly_chart(plot_sector_donut(df_u), use_container_width=True)

with table_col:
    st.subheader("⭐ Top 5 Quality Compounders")
    top_5 = df_u.sort_values("composite_quality_score", ascending=False)[[
        "company_id", "company_name", "broad_sector", "return_on_equity_pct", "debt_to_equity", "composite_quality_score"
    ]].head(5)
    top_5.columns = ["Ticker", "Company Name", "Sector", "ROE (%)", "D/E", "Quality Score"]
    st.dataframe(
        top_5.style.format({
            "ROE (%)": "{:.2f}%",
            "D/E": "{:.2f}",
            "Quality Score": "{:.1f}"
        }),
        use_container_width=True,
        hide_index=True
    )

st.sidebar.title("BlueStock Nifty 100")
st.sidebar.info("📌 **System Status:** All 10 relational tables loaded in SQLite (`data/nifty100.db`). Live cache TTL: 600s.")
