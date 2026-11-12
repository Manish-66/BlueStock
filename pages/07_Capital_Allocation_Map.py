"""Screen 5.7: Capital Allocation Map.

Nifty 100 Financial Intelligence Platform.
Treemap visualization and classification of all 92 companies across the 8 corporate cash flow sign patterns.
"""

import pandas as pd
import streamlit as st

from src.dashboard.utils.charts import plot_capital_allocation_treemap
from src.dashboard.utils.db import get_capital_allocation_data


st.set_page_config(page_title="Capital Allocation Map — Nifty 100", page_icon="🗺️", layout="wide")

st.title("🗺️ Capital Allocation & Cash Flow Classification Map")
st.markdown("""
Classifies all 92 companies into the **8 canonical corporate capital allocation archetypes** based on the
net sign pattern of **Operating Cash Flow (CFO)**, **Investing Cash Flow (CFI)**, and **Financing Cash Flow (CFF)**.
""")

df_cap = get_capital_allocation_data()

# Summary Metric Cards
c1, c2, c3, c4 = st.columns(4)
reinvest_cnt = (df_cap["pattern"] == "(+, -, -)").sum()
growth_cnt = (df_cap["pattern"] == "(+, -, +)").sum()
distress_cnt = df_cap["pattern"].isin(["(-, +, +)", "(-, -, -)", "(-, +, -)"]).sum()
other_cnt = len(df_cap) - reinvest_cnt - growth_cnt - distress_cnt

c1.metric("Reinvestor / Cash Cow (+, -, -)", f"{reinvest_cnt} Companies", "Self-funding dividends & debt")
c2.metric("Rapid Growth / Expansion (+, -, +)", f"{growth_cnt} Companies", "Raising capital for capex")
c3.metric("Restructuring / Divesting", f"{other_cnt} Companies", "Asset sales / debt payback")
c4.metric("Capital Distress / High Burn", f"{distress_cnt} Companies", "Negative operational cash flow")

st.markdown("---")

# Treemap Chart
fig_tree = plot_capital_allocation_treemap(df_cap)
st.plotly_chart(fig_tree, use_container_width=True)

st.markdown("---")

# Drill-down by Pattern
st.subheader("🔍 Pattern Drill-Down & Constituent Table")
patterns = sorted(df_cap["pattern_label"].unique())
selected_pattern = st.selectbox("Filter Companies by Archetype:", ["All Archetypes"] + patterns)

filtered_cap = df_cap if selected_pattern == "All Archetypes" else df_cap[df_cap["pattern_label"] == selected_pattern]

disp_cols = [
    "company_id", "company_name", "broad_sector", "pattern", "pattern_label",
    "operating_activity", "investing_activity", "financing_activity", "market_cap_crore"
]
out_table = filtered_cap[disp_cols].sort_values("market_cap_crore", ascending=False).copy()
out_table.columns = [
    "Ticker", "Company Name", "Sector", "Sign Pattern", "Capital Archetype",
    "CFO (Cr)", "CFI (Cr)", "CFF (Cr)", "Market Cap (Cr)"
]

st.dataframe(
    out_table.style.format({
        "CFO (Cr)": "₹ {:,.0f}",
        "CFI (Cr)": "₹ {:,.0f}",
        "CFF (Cr)": "₹ {:,.0f}",
        "Market Cap (Cr)": "₹ {:,.0f}"
    }),
    use_container_width=True,
    hide_index=True
)
