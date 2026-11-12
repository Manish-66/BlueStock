"""Screen 5.1: Home & Market Overview.

Nifty 100 Financial Intelligence Platform.
Displays summary KPIs (avg ROE, median P/E, sector distribution donut, market health banner).
"""

import numpy as np
import pandas as pd
import streamlit as st

from src.dashboard.utils.charts import plot_sector_donut
from src.dashboard.utils.db import load_universe_data


st.set_page_config(page_title="Home — Nifty 100 Intelligence", page_icon="🏛️", layout="wide")

st.markdown("""
<div style='background: linear-gradient(135deg, #1F4E79 0%, #2F5597 100%); padding: 24px 28px; border-radius: 12px; color: white; margin-bottom: 24px;'>
    <h1 style='color: white; margin: 0; font-size: 2.2rem;'>🏛️ Nifty 100 Financial Intelligence Platform</h1>
    <p style='margin: 8px 0 0 0; opacity: 0.9; font-size: 1.05rem;'>
        Executive Overview, Sector Distribution & Macro Quality Analytics across all 92 Nifty 100 Constituents
    </p>
</div>
""", unsafe_allow_html=True)

df_u = load_universe_data()

# Executive KPI Tiles
col1, col2, col3, col4, col5 = st.columns(5)
total_mkt_cap = df_u["market_cap_crore"].sum() / 1e5  # Lakh Crore
avg_roe = df_u["return_on_equity_pct"].replace([np.inf, -np.inf], np.nan).mean()
med_pe = df_u["pe_ratio"].median()
avg_fcf = df_u["free_cash_flow_cr"].sum() / 1000  # Thousand Cr
healthy_debt = (df_u["debt_to_equity"].fillna(0) < 1.0).sum()

col1.metric("Constituents", f"{len(df_u)} Companies", "Nifty 100 Index")
col2.metric("Total Market Cap", f"₹ {total_mkt_cap:.2f} L Cr", "FY2024")
col3.metric("Average ROE", f"{avg_roe:.1f} %", "Baseline")
col4.metric("Median P/E Multiple", f"{med_pe:.1f} x", "India Large Cap")
col5.metric("Conservative D/E (<1.0)", f"{healthy_debt} / {len(df_u)} Cos", f"{healthy_debt/len(df_u)*100:.0f}%")

st.markdown("---")

# Market Health & Sector Composition
left_col, right_col = st.columns([3, 2])

with left_col:
    st.subheader("📊 Market Health & Quality Distribution")
    st.markdown("""
    The Nifty 100 platform evaluates large-cap Indian corporate health across **Profitability (35%)**, **Cash Quality (30%)**,
    **Growth (20%)**, and **Balance Sheet Leverage (15%)**.
    """)

    badge_counts = df_u["valuation_badge"].value_counts().reset_index()
    badge_counts.columns = ["Valuation Status", "Company Count"]
    badge_counts["% of Index"] = (badge_counts["Company Count"] / len(df_u) * 100).round(1).astype(str) + "%"
    st.dataframe(badge_counts, use_container_width=True, hide_index=True)

    st.markdown("#### Top Quality Compounders (Highest Composite Score)")
    top_quality = df_u.sort_values(by="composite_quality_score", ascending=False)[[
        "company_id", "company_name", "broad_sector", "return_on_equity_pct", "debt_to_equity", "composite_quality_score"
    ]].head(6)
    top_quality.columns = ["Ticker", "Name", "Sector", "ROE (%)", "D/E", "Composite Score"]
    st.dataframe(top_quality, use_container_width=True, hide_index=True)

with right_col:
    fig_donut = plot_sector_donut(df_u)
    st.plotly_chart(fig_donut, use_container_width=True)

st.info("💡 **Navigation Tip:** Use the sidebar on the left to navigate to Company Profiles, Screener, Peer Rankings, Sector Analysis, Capital Allocation, or Annual Reports.")
