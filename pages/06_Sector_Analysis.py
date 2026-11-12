"""Screen 5.6: Sector Analytics & Landscape.

Nifty 100 Financial Intelligence Platform.
Interactive macro sector comparison: Revenue vs. ROE bubble charts, sector median KPI benchmarks, and constituent breakdowns.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.utils.charts import plot_pb_roe_scatter, plot_sector_bubble
from src.dashboard.utils.db import load_universe_data


st.set_page_config(page_title="Sector Analysis — Nifty 100", page_icon="🌐", layout="wide")

st.title("🌐 Sector Intelligence & Industry Landscape")
st.markdown("Macro sector benchmark analytics, constituent positioning, and sector-relative quality metrics.")

df_u = load_universe_data()
sectors = sorted(df_u["broad_sector"].unique())

selected_sector = st.selectbox("Select Broad Sector to Drill Down (or 'All Sectors'):", ["All Sectors"] + sectors)

# Overall Bubble Chart
st.subheader("📊 Industry Landscape: Revenue vs. ROE vs. Market Cap")
if selected_sector == "All Sectors":
    fig_bubble = plot_sector_bubble(df_u)
    st.plotly_chart(fig_bubble, use_container_width=True)
else:
    sub_df = df_u[df_u["broad_sector"] == selected_sector]
    fig_bubble = plot_sector_bubble(sub_df)
    st.plotly_chart(fig_bubble, use_container_width=True)

st.markdown("---")

# Sector Median Comparison Bar Charts
st.subheader("🏛️ Sector Median KPI Comparison")

sec_medians = df_u.groupby("broad_sector").agg({
    "company_id": "count",
    "return_on_equity_pct": "median",
    "pe_ratio": "median",
    "debt_to_equity": "median",
    "operating_profit_margin_pct": "median",
    "free_cash_flow_cr": "median"
}).reset_index().rename(columns={"company_id": "Companies"})

col_bar1, col_bar2 = st.columns(2)

with col_bar1:
    fig_roe_bar = px.bar(
        sec_medians.sort_values("return_on_equity_pct", ascending=True),
        x="return_on_equity_pct",
        y="broad_sector",
        orientation="h",
        color="return_on_equity_pct",
        color_continuous_scale="Viridis",
        title="<b>Median ROE (%) by Sector</b>",
        labels={"return_on_equity_pct": "Median ROE (%)", "broad_sector": "Sector"}
    )
    fig_roe_bar.update_layout(height=360, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_roe_bar, use_container_width=True)

with col_bar2:
    fig_pe_bar = px.bar(
        sec_medians.sort_values("pe_ratio", ascending=True),
        x="pe_ratio",
        y="broad_sector",
        orientation="h",
        color="pe_ratio",
        color_continuous_scale="Plasma",
        title="<b>Median P/E Multiple by Sector</b>",
        labels={"pe_ratio": "Median P/E", "broad_sector": "Sector"}
    )
    fig_pe_bar.update_layout(height=360, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_pe_bar, use_container_width=True)

# Constituent Table for selected sector
st.markdown("---")
st.subheader(f"📋 Constituents in {selected_sector}")
target_df = df_u if selected_sector == "All Sectors" else df_u[df_u["broad_sector"] == selected_sector]

cols_display = [
    "company_id", "company_name", "sub_sector", "market_cap_crore",
    "sales", "net_profit", "return_on_equity_pct", "debt_to_equity",
    "pe_ratio", "valuation_badge", "composite_quality_score"
]
table_view = target_df[cols_display].sort_values("market_cap_crore", ascending=False).copy()
table_view.columns = [
    "Ticker", "Company Name", "Sub-Sector", "Mkt Cap (Cr)",
    "Sales (Cr)", "Net Profit (Cr)", "ROE (%)", "D/E",
    "P/E", "Valuation", "Quality Score"
]

st.dataframe(
    table_view.style.format({
        "Mkt Cap (Cr)": "₹ {:,.0f}",
        "Sales (Cr)": "₹ {:,.0f}",
        "Net Profit (Cr)": "₹ {:,.0f}",
        "ROE (%)": "{:.2f}%",
        "D/E": "{:.2f}",
        "P/E": "{:.1f}x",
        "Quality Score": "{:.1f}"
    }),
    use_container_width=True,
    hide_index=True
)
