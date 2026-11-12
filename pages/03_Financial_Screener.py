"""Screen 5.3: Multi-Criteria Stock Screener.

Nifty 100 Financial Intelligence Platform.
Supports 6 preset strategies, 10 custom interactive sliders, live filtering, and CSV export (AC-09).
"""

import io
import pandas as pd
import streamlit as st

from src.dashboard.utils.db import load_universe_data
from src.screener.engine import apply_filters, load_config, run_preset


st.set_page_config(page_title="Financial Screener — Nifty 100", page_icon="🔍", layout="wide")

st.title("🔍 Multi-Criteria Financial Screener")
st.markdown("Screen all 92 Nifty 100 companies using industry-standard institutional presets or custom threshold filters.")

df_u = load_universe_data()
config = load_config()
presets = config.get("presets", {})

st.sidebar.header("🎯 Screener Presets")
mode = st.sidebar.radio("Screening Mode", ["Preset Strategy", "Custom Sliders"])

filtered_df = df_u.copy()

if mode == "Preset Strategy":
    preset_names = {k: v["name"] for k, v in presets.items()}
    selected_preset_key = st.sidebar.selectbox(
        "Choose Institutional Preset:",
        list(preset_names.keys()),
        format_func=lambda k: preset_names[k]
    )

    preset_meta = presets[selected_preset_key]
    st.info(f"**Strategy: {preset_meta['name']}** — {preset_meta.get('description', '')}")
    filtered_df = run_preset(selected_preset_key, df_u)

else:
    st.sidebar.header("🎛️ Custom Sliders (10 Metrics)")
    min_roe = st.sidebar.slider("Min ROE (%)", min_value=0.0, max_value=50.0, value=12.0, step=1.0)
    max_de = st.sidebar.slider("Max Debt-to-Equity", min_value=0.0, max_value=5.0, value=1.5, step=0.1)
    min_fcf = st.sidebar.slider("Min FCF (₹ Cr)", min_value=-5000.0, max_value=10000.0, value=0.0, step=250.0)
    min_rev_cagr = st.sidebar.slider("Min 5Y Rev CAGR (%)", min_value=-10.0, max_value=30.0, value=8.0, step=1.0)
    min_pat_cagr = st.sidebar.slider("Min 5Y PAT CAGR (%)", min_value=-10.0, max_value=40.0, value=10.0, step=1.0)
    min_opm = st.sidebar.slider("Min OPM (%)", min_value=0.0, max_value=50.0, value=10.0, step=1.0)
    max_pe = st.sidebar.slider("Max P/E Multiple", min_value=5.0, max_value=80.0, value=40.0, step=2.0)
    max_pb = st.sidebar.slider("Max P/B Multiple", min_value=0.5, max_value=20.0, value=8.0, step=0.5)
    min_div_yield = st.sidebar.slider("Min Dividend Yield (%)", min_value=0.0, max_value=5.0, value=0.5, step=0.2)
    min_mkt_cap = st.sidebar.slider("Min Market Cap (₹ Cr)", min_value=0, max_value=200000, value=10000, step=5000)

    custom_filters = {
        "return_on_equity_pct_min": min_roe,
        "debt_to_equity_max": max_de,
        "free_cash_flow_cr_min": min_fcf,
        "revenue_cagr_5yr_min": min_rev_cagr,
        "pat_cagr_5yr_min": min_pat_cagr,
        "operating_profit_margin_pct_min": min_opm,
        "pe_ratio_max": max_pe,
        "pb_ratio_max": max_pb,
        "dividend_yield_pct_min": min_div_yield,
        "market_cap_crore_min": min_mkt_cap
    }
    filtered_df = apply_filters(df_u, custom_filters)

# Display Results & Metrics
count_col, exp_col = st.columns([2, 1])
with count_col:
    st.subheader(f"Screening Results: {len(filtered_df)} / {len(df_u)} Companies Matched")

with exp_col:
    # CSV Download Button (AC-09)
    csv_buffer = io.StringIO()
    filtered_df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="📥 Download Results as CSV",
        data=csv_buffer.getvalue(),
        file_name="nifty100_screener_results.csv",
        mime="text/csv",
        use_container_width=True
    )

display_cols = [
    "company_id", "company_name", "broad_sector", "composite_quality_score",
    "market_cap_crore", "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr",
    "revenue_cagr_5yr", "pat_cagr_5yr", "operating_profit_margin_pct", "pe_ratio", "pb_ratio", "dividend_yield_pct"
]

show_df = filtered_df[[c for c in display_cols if c in filtered_df.columns]].copy()
show_df.columns = [
    "Ticker", "Company Name", "Sector", "Quality Score",
    "Mkt Cap (Cr)", "ROE (%)", "D/E", "FCF (Cr)",
    "5Y Rev CAGR (%)", "5Y PAT CAGR (%)", "OPM (%)", "P/E", "P/B", "Div Yield (%)"
]

st.dataframe(
    show_df.style.format({
        "Quality Score": "{:.1f}",
        "Mkt Cap (Cr)": "₹ {:,.0f}",
        "ROE (%)": "{:.2f}%",
        "D/E": "{:.2f}",
        "FCF (Cr)": "₹ {:,.0f}",
        "5Y Rev CAGR (%)": "{:.1f}%",
        "5Y PAT CAGR (%)": "{:.1f}%",
        "OPM (%)": "{:.1f}%",
        "P/E": "{:.1f}x",
        "P/B": "{:.2f}x",
        "Div Yield (%)": "{:.2f}%"
    }),
    use_container_width=True,
    hide_index=True
)
