"""Screen 5.5: Trend & Growth Analytics.

Nifty 100 Financial Intelligence Platform.
10-year sparklines, YoY percentage change annotations, and multi-metric historical overlays.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.utils.charts import plot_trend_sparkline
from src.dashboard.utils.db import get_company_details, load_universe_data


st.set_page_config(page_title="Trend Analysis — Nifty 100", page_icon="📈", layout="wide")

st.title("📈 Multi-Year Trend & Growth Analytics")
st.markdown("Examine 10-year historical trajectory, YoY growth momentum, and multi-metric correlation overlays.")

df_u = load_universe_data()
ticker_options = sorted(df_u["company_id"].tolist())

col_sel1, col_sel2 = st.columns([1, 1])
with col_sel1:
    selected_ticker = st.selectbox("Select Company:", ticker_options, index=ticker_options.index("RELIANCE") if "RELIANCE" in ticker_options else 0)

with col_sel2:
    mode = st.radio("Trend View Mode:", ["Single Metric (with YoY %)", "Multi-Metric Overlay"], horizontal=True)

details = get_company_details(selected_ticker)
pl_df = details["pl"][details["pl"]["year"] != "TTM"].copy()
bs_df = details["bs"].copy()

# Merge P&L and Balance Sheet for unified trend analysis
merged_history = pl_df.merge(bs_df[["company_id", "year", "total_assets", "borrowings", "equity_capital", "reserves"]], on=["company_id", "year"], how="left")

metric_choices = {
    "sales": ("Revenue (Sales)", "₹ Cr"),
    "net_profit": ("Net Profit", "₹ Cr"),
    "operating_profit": ("Operating Profit (EBITDA)", "₹ Cr"),
    "opm_percentage": ("Operating Profit Margin (OPM)", "%"),
    "eps": ("Earnings Per Share (EPS)", "₹"),
    "total_assets": ("Total Assets", "₹ Cr"),
    "borrowings": ("Total Borrowings (Debt)", "₹ Cr")
}

if mode == "Single Metric (with YoY %)":
    chosen_metric = st.selectbox(
        "Choose Financial Metric for Sparkline:",
        list(metric_choices.keys()),
        format_func=lambda k: metric_choices[k][0]
    )
    metric_label, unit = metric_choices[chosen_metric]

    fig_spark = plot_trend_sparkline(
        merged_history,
        chosen_metric,
        unit,
        f"{selected_ticker} — 10-Year {metric_label} Trend with YoY % Growth"
    )
    st.plotly_chart(fig_spark, use_container_width=True)

    # Historical data summary table
    st.markdown("#### Historical Values & Annual Growth")
    d_table = merged_history[["year", chosen_metric]].dropna().copy()
    d_table["YoY Change (%)"] = d_table[chosen_metric].pct_change() * 100.0
    d_table.columns = ["Fiscal Year", f"{metric_label} ({unit})", "YoY Change (%)"]
    st.dataframe(
        d_table.style.format({
            f"{metric_label} ({unit})": "{:,.2f}",
            "YoY Change (%)": "{:+.2f}%"
        }),
        use_container_width=True,
        hide_index=True
    )

else:
    selected_metrics = st.multiselect(
        "Select up to 4 metrics for comparative overlay:",
        list(metric_choices.keys()),
        default=["sales", "net_profit"],
        format_func=lambda k: metric_choices[k][0]
    )

    if selected_metrics:
        fig_multi = go.Figure()
        for m in selected_metrics:
            m_label, _ = metric_choices[m]
            fig_multi.add_trace(go.Scatter(
                x=merged_history["year"],
                y=merged_history[m],
                mode="lines+markers",
                name=m_label
            ))

        fig_multi.update_layout(
            title=f"<b>{selected_ticker} — Multi-Metric Trajectory Overlay</b>",
            xaxis=dict(title="Fiscal Year"),
            yaxis=dict(title="₹ in Crore / Absolute Units", showgrid=True),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(t=50, b=40, l=40, r=40),
            height=450
        )
        st.plotly_chart(fig_multi, use_container_width=True)
