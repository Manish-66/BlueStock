"""Screen 5.4: Peer Comparison Engine.

Nifty 100 Financial Intelligence Platform.
Interactive peer group benchmarking: 11 peer groups, side-by-side KPI comparison,
and 8-axis Plotly polar radar charts.
"""

import numpy as np
import pandas as pd
import streamlit as st

from src.analytics.peer import RADAR_AXES, calculate_peer_percentiles
from src.dashboard.utils.charts import plot_radar_comparison
from src.dashboard.utils.db import load_raw_table, load_universe_data


st.set_page_config(page_title="Peer Comparison — Nifty 100", page_icon="👥", layout="wide")

st.title("👥 Peer Comparison & Intra-Group Benchmarking")
st.markdown("Compare industry peers across 20 KPI metrics and visualize comparative positioning on 8-axis radar charts.")

# Load peer percentiles and enriched peer data
_, df_peers_enriched = calculate_peer_percentiles()
peer_groups = sorted(df_peers_enriched["peer_group_name"].unique())

selected_group = st.selectbox("Select Peer Group (11 Groups):", peer_groups, index=peer_groups.index("IT Services") if "IT Services" in peer_groups else 0)

grp_data = df_peers_enriched[df_peers_enriched["peer_group_name"] == selected_group].copy()
grp_data = grp_data.sort_values(by=["is_benchmark", "return_on_equity_pct"], ascending=[False, False])

# Identify benchmark company
benchmark_row = grp_data[grp_data["is_benchmark"] == 1]
benchmark_ticker = benchmark_row["company_id"].iloc[0] if len(benchmark_row) > 0 else grp_data["company_id"].iloc[0]

st.info(f"🏆 **Peer Group:** {selected_group} ({len(grp_data)} Companies) | **Designated Benchmark:** {benchmark_ticker}")

# Radar comparison controls
col_radar_ctrl, col_radar_plot = st.columns([1, 2])

with col_radar_ctrl:
    st.subheader("Radar Controls")
    group_tickers = grp_data["company_id"].tolist()
    chosen_ticker = st.radio("Focus Company for Radar:", group_tickers, index=0)

    st.markdown("#### Peer Group Median Highlights")
    med_roe = grp_data["return_on_equity_pct"].median()
    med_de = grp_data["debt_to_equity"].median()
    med_fcf = grp_data["free_cash_flow_cr"].median()

    st.metric("Group Median ROE", f"{med_roe:.1f}%")
    st.metric("Group Median D/E", f"{med_de:.2f}" if pd.notna(med_de) else "Debt Free")
    st.metric("Group Median FCF", f"₹ {med_fcf:,.0f} Cr" if pd.notna(med_fcf) else "—")

with col_radar_plot:
    # Build 8 radar axis scores (normalized 0-100)
    focus_row = grp_data[grp_data["company_id"] == chosen_ticker].iloc[0]

    axis_keys = [k for k, _ in RADAR_AXES]
    axis_labels = [lbl for _, lbl in RADAR_AXES]

    c_scores = []
    p_scores = []

    for k in axis_keys:
        val = focus_row.get(k, np.nan)
        avg = grp_data[k].replace([np.inf, -np.inf], np.nan).mean()
        # Scale into 0-100 range
        c_pct = focus_row.get(f"{k}_pctile", 0.5) if f"{k}_pctile" in focus_row else 0.5
        c_scores.append(float(np.clip(c_pct * 100.0, 5, 100)) if pd.notna(c_pct) else 50.0)
        p_scores.append(50.0)  # Peer median baseline at 50%

    fig_radar = plot_radar_comparison(
        chosen_ticker,
        c_scores,
        p_scores,
        axis_labels,
        selected_group
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# Side-by-side Table
st.markdown("---")
st.subheader(f"📋 Side-by-Side Comparison: {selected_group}")

show_cols = [
    "company_id", "company_name", "is_benchmark", "return_on_equity_pct",
    "roce_pct", "debt_to_equity", "operating_profit_margin_pct",
    "free_cash_flow_cr", "pe_ratio", "pb_ratio", "revenue_cagr_5yr", "composite_quality_score"
]
table_df = grp_data[[c for c in show_cols if c in grp_data.columns]].copy()
table_df["is_benchmark"] = table_df["is_benchmark"].apply(lambda x: "★ Benchmark" if x == 1 else "")
table_df.columns = [
    "Ticker", "Company Name", "Benchmark", "ROE (%)",
    "ROCE (%)", "D/E", "OPM (%)", "FCF (Cr)",
    "P/E", "P/B", "5Y Rev CAGR (%)", "Quality Score"
]

st.dataframe(
    table_df.style.format({
        "ROE (%)": "{:.2f}%",
        "ROCE (%)": "{:.2f}%",
        "D/E": "{:.2f}",
        "OPM (%)": "{:.1f}%",
        "FCF (Cr)": "₹ {:,.0f}",
        "P/E": "{:.1f}x",
        "P/B": "{:.2f}x",
        "5Y Rev CAGR (%)": "{:.1f}%",
        "Quality Score": "{:.1f}"
    }),
    use_container_width=True,
    hide_index=True
)
