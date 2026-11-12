"""Screen 5.2: Company Profile.

Nifty 100 Financial Intelligence Platform.
Interactive company dossier: ticker search, KPI tiles, 10-year P&L, BS, Cash Flow charts, and Pros/Cons.
"""

import numpy as np
import pandas as pd
import streamlit as st

from src.dashboard.utils.charts import plot_bs_history, plot_cf_history, plot_pl_history
from src.dashboard.utils.db import get_company_details, load_universe_data


st.set_page_config(page_title="Company Profile — Nifty 100", page_icon="🏢", layout="wide")

df_u = load_universe_data()
ticker_options = sorted(df_u["company_id"].tolist())

# Header and Company Selector
st.title("🏢 Company Financial Dossier & Profile")
selected_ticker = st.selectbox(
    "Select or Search Company (Ticker / Symbol):",
    ticker_options,
    index=ticker_options.index("TCS") if "TCS" in ticker_options else 0
)

details = get_company_details(selected_ticker)
comp = details["company"]
u_row = df_u[df_u["company_id"] == selected_ticker].iloc[0]

# Company Header Card
col_hdr, col_badges = st.columns([3, 1])
with col_hdr:
    st.subheader(f"{comp.get('company_name', selected_ticker)} ({selected_ticker})")
    st.markdown(f"**Sector:** {u_row.get('broad_sector', 'N/A')}  |  **Sub-Sector:** {u_row.get('sub_sector', 'N/A')}")
    about = comp.get("about_company", "Nifty 100 benchmark constituent.")
    if pd.notna(about):
        st.write(str(about).strip())

with col_badges:
    val_badge = u_row.get("valuation_badge", "Fair")
    badge_color = "#E74C3C" if val_badge == "Caution" else ("#2ECC71" if val_badge == "Discount" else "#3498DB")
    st.markdown(f"""
    <div style='text-align: center; padding: 12px; border-radius: 8px; border: 2px solid {badge_color}; background-color: #F8F9FA;'>
        <div style='font-size: 0.85rem; color: #7F8C8D; font-weight: bold;'>VALUATION STATUS</div>
        <div style='font-size: 1.4rem; font-weight: bold; color: {badge_color};'>{val_badge}</div>
        <div style='font-size: 0.8rem; margin-top: 4px;'>Score: {u_row.get('composite_quality_score', '—')} / 100</div>
    </div>
    """, unsafe_allow_html=True)

# 6 Executive KPI Tiles
st.markdown("---")
k1, k2, k3, k4, k5, k6 = st.columns(6)

roe_val = u_row.get("return_on_equity_pct")
roce_val = u_row.get("roce_pct")
de_val = u_row.get("debt_to_equity")
fcf_val = u_row.get("free_cash_flow_cr")
pe_val = u_row.get("pe_ratio")
rev_cagr = u_row.get("revenue_cagr_5yr")

k1.metric("ROE (%)", f"{roe_val:.2f}%" if pd.notna(roe_val) else "—")
k2.metric("ROCE (%)", f"{roce_val:.2f}%" if pd.notna(roce_val) else "—")
k3.metric("D/E Ratio", f"{de_val:.2f}" if pd.notna(de_val) else "Debt Free")
k4.metric("FCF (₹ Cr)", f"₹ {fcf_val:,.0f}" if pd.notna(fcf_val) else "—")
k5.metric("P/E Ratio", f"{pe_val:.1f}x" if pd.notna(pe_val) else "—")
k6.metric("5Y Rev CAGR", f"{rev_cagr:.1f}%" if pd.notna(rev_cagr) else "—")

# Tabs for Financial Statements and Analysis
st.markdown("---")
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Profit & Loss (P&L)",
    "🏛️ Balance Sheet (BS)",
    "💵 Cash Flow (CF)",
    "⚖️ Strengths & Weaknesses (Pros/Cons)"
])

with tab1:
    st.plotly_chart(plot_pl_history(details["pl"]), use_container_width=True)
    with st.expander("View Raw P&L Data Table"):
        st.dataframe(details["pl"], use_container_width=True)

with tab2:
    st.plotly_chart(plot_bs_history(details["bs"]), use_container_width=True)
    with st.expander("View Raw Balance Sheet Data Table"):
        st.dataframe(details["bs"], use_container_width=True)

with tab3:
    st.plotly_chart(plot_cf_history(details["cf"]), use_container_width=True)
    with st.expander("View Raw Cash Flow Data Table"):
        st.dataframe(details["cf"], use_container_width=True)

with tab4:
    col_p, col_c = st.columns(2)
    pc = details["prosandcons"]
    pros = pc["pros"].dropna().tolist() if len(pc) > 0 and "pros" in pc.columns else []
    cons = pc["cons"].dropna().tolist() if len(pc) > 0 and "cons" in pc.columns else []

    with col_p:
        st.markdown("#### 🟢 Key Strengths (Pros)")
        if pros:
            for p in pros:
                st.success(f"✓ {p}")
        else:
            st.info("No explicit flags identified in source documents.")

    with col_c:
        st.markdown("#### 🔴 Watch Items (Cons)")
        if cons:
            for c in cons:
                st.error(f"⚠ {c}")
        else:
            st.success("No critical warnings identified.")
