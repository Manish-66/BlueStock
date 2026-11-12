"""Screen 5.8: Document Intelligence & Annual Reports.

Nifty 100 Financial Intelligence Platform.
Company and year-wise searchable annual report repository with clickable BSE/NSE regulatory PDF links.
"""

import pandas as pd
import streamlit as st

from src.dashboard.utils.db import get_company_details, load_raw_table, load_universe_data


st.set_page_config(page_title="Annual Reports — Nifty 100", page_icon="📑", layout="wide")

st.title("📑 Regulatory Document Intelligence & Annual Reports")
st.markdown("Direct access to official BSE/NSE regulatory filings, disclosures, and annual report PDF archives.")

df_u = load_universe_data()
df_docs = load_raw_table("documents")
df_comp = load_raw_table("companies")[["id", "company_name"]].rename(columns={"id": "company_id"})

# Summary Metrics
m1, m2, m3 = st.columns(3)
total_filings = len(df_docs)
unique_filing_cos = df_docs["company_id"].nunique()
valid_links = df_docs["Annual_Report"].str.startswith("http", na=False).sum()

m1.metric("Indexed Regulatory Filings", f"{total_filings} Reports")
m2.metric("Companies Covered", f"{unique_filing_cos} / {len(df_u)} Companies")
m3.metric("Verified Regulatory URLs", f"{valid_links} Links", "BSE / NSE Archive")

st.markdown("---")

# Company and Year Filter
col_comp, col_yr = st.columns([2, 1])

with col_comp:
    ticker_list = sorted(df_u["company_id"].tolist())
    selected_ticker = st.selectbox("Select Company:", ticker_list, index=ticker_list.index("INFY") if "INFY" in ticker_list else 0)

with col_yr:
    sub_docs = df_docs[df_docs["company_id"] == selected_ticker].sort_values("Year", ascending=False)
    available_years = ["All Available Years"] + sub_docs["Year"].dropna().unique().tolist()
    selected_year = st.selectbox("Filter Fiscal Year:", available_years)

st.markdown(f"#### Annual Report Filings for {selected_ticker}")

if selected_year != "All Available Years":
    sub_docs = sub_docs[sub_docs["Year"] == selected_year]

if len(sub_docs) == 0:
    st.warning(f"No annual reports currently archived for {selected_ticker} ({selected_year}).")
else:
    for _, row in sub_docs.iterrows():
        yr = row.get("Year", "N/A")
        url = row.get("Annual_Report")

        card_col1, card_col2 = st.columns([3, 1])
        with card_col1:
            st.markdown(f"**Fiscal Year: {yr}**")
            if pd.notna(url) and str(url).startswith("http"):
                st.markdown(f"📄 [Direct BSE/NSE Annual Report Link]({url})")
            else:
                st.markdown("⚠️ *No direct digital PDF URL available in registry.*")

        with card_col2:
            if pd.notna(url) and str(url).startswith("http"):
                st.markdown("🟢 **Available**")
            else:
                st.markdown("🔴 **Missing URL**")
        st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #EAEAEA;'>", unsafe_allow_html=True)

# Full repository browser
with st.expander("🔍 Browse Global Documents Repository Table"):
    merged_docs = df_docs.merge(df_comp, on="company_id", how="left")
    st.dataframe(
        merged_docs[["company_id", "company_name", "Year", "Annual_Report"]].rename(columns={
            "company_id": "Ticker", "company_name": "Company Name", "Year": "Fiscal Year", "Annual_Report": "URL"
        }),
        use_container_width=True,
        hide_index=True
    )
