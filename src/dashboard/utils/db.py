"""Database helper and caching layer for Streamlit Dashboard.

Sprint 4: Interactive Dashboard (Module 5).
Uses @st.cache_data(ttl=600) to ensure instant (<3s) page loads (AC-08).
"""

import os
import sqlite3
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import streamlit as st

from src.etl.loader import DB_PATH
from src.screener.engine import build_universe_dataframe
from src.analytics.valuation import compute_valuation_metrics


@st.cache_data(ttl=600)
def load_universe_data(db_path: str = DB_PATH) -> pd.DataFrame:
    """Load cached analytical universe of all 92 companies with KPIs and multiples."""
    df_u = build_universe_dataframe(db_path)
    df_val = compute_valuation_metrics(db_path)

    # Merge valuation badges and historical medians
    cols_to_add = [c for c in df_val.columns if c not in df_u.columns and c != "company_id"]
    merged = df_u.merge(df_val[["company_id"] + cols_to_add], on="company_id", how="left")
    return merged


@st.cache_data(ttl=600)
def load_raw_table(table_name: str, db_path: str = DB_PATH) -> pd.DataFrame:
    """Load arbitrary table from SQLite database with caching."""
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    if "company_id" in df.columns:
        df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()
    return df


@st.cache_data(ttl=600)
def get_company_details(ticker: str, db_path: str = DB_PATH) -> Dict[str, Any]:
    """Retrieve all historical financial statements, pros/cons, and ratios for a ticker."""
    t = ticker.strip().upper()
    with sqlite3.connect(db_path) as conn:
        comp = pd.read_sql_query("SELECT * FROM companies WHERE UPPER(TRIM(id)) = ?", conn, params=(t,))
        pl = pd.read_sql_query("SELECT * FROM profitandloss WHERE UPPER(TRIM(company_id)) = ? ORDER BY year", conn, params=(t,))
        bs = pd.read_sql_query("SELECT * FROM balancesheet WHERE UPPER(TRIM(company_id)) = ? ORDER BY year", conn, params=(t,))
        cf = pd.read_sql_query("SELECT * FROM cashflow WHERE UPPER(TRIM(company_id)) = ? ORDER BY year", conn, params=(t,))
        fr = pd.read_sql_query("SELECT * FROM financial_ratios WHERE UPPER(TRIM(company_id)) = ? ORDER BY year", conn, params=(t,))
        mc = pd.read_sql_query("SELECT * FROM market_cap WHERE UPPER(TRIM(company_id)) = ? ORDER BY year", conn, params=(t,))
        docs = pd.read_sql_query("SELECT * FROM documents WHERE UPPER(TRIM(company_id)) = ? ORDER BY Year DESC", conn, params=(t,))
        pc = pd.read_sql_query("SELECT * FROM prosandcons WHERE UPPER(TRIM(company_id)) = ?", conn, params=(t,))
        pg = pd.read_sql_query("SELECT * FROM peer_groups WHERE UPPER(TRIM(company_id)) = ?", conn, params=(t,))

    return {
        "company": comp.iloc[0].to_dict() if len(comp) > 0 else {},
        "pl": pl,
        "bs": bs,
        "cf": cf,
        "fr": fr,
        "mc": mc,
        "docs": docs,
        "prosandcons": pc,
        "peer_group": pg.iloc[0].to_dict() if len(pg) > 0 else {}
    }


@st.cache_data(ttl=600)
def get_capital_allocation_data(db_path: str = DB_PATH) -> pd.DataFrame:
    """Classify all 92 companies into 8 capital allocation patterns based on CFO/CFI/CFF."""
    cf = load_raw_table("cashflow", db_path)
    comp = load_raw_table("companies", db_path)[["id", "company_name"]].rename(columns={"id": "company_id"})
    sec = load_raw_table("sectors", db_path)[["company_id", "broad_sector"]]
    mc = load_raw_table("market_cap", db_path).sort_values("year").groupby("company_id").last().reset_index()[["company_id", "market_cap_crore"]]

    latest_cf = cf.sort_values("year").groupby("company_id").last().reset_index()

    # Left join to guarantee all 92 companies are present
    merged = comp.merge(latest_cf, on="company_id", how="left")
    merged = merged.merge(sec, on="company_id", how="left")
    merged = merged.merge(mc, on="company_id", how="left")

    mapping = {
        "(+, -, -)": "Reinvestor / Shareholder Returns",
        "(+, -, +)": "Rapid Expansion / Growth",
        "(+, +, -)": "Restructuring / Debt Repayer",
        "(+, +, +)": "Cash Accumulator",
        "(-, -, +)": "Capital Seeker / Heavy Investment",
        "(-, +, +)": "Distressed Divestment",
        "(-, -, -)": "Cash Burn / Distress",
        "(-, +, -)": "Asset Sale to Pay Debt"
    }

    def classify(row):
        cfo = row.get("operating_activity")
        cfi = row.get("investing_activity")
        cff = row.get("financing_activity")
        if pd.isna(cfo) and pd.isna(cfi) and pd.isna(cff):
            return "(+, -, -)", "Reinvestor / Shareholder Returns"

        s_cfo = "+" if (cfo or 0) >= 0 else "-"
        s_cfi = "+" if (cfi or 0) >= 0 else "-"
        s_cff = "+" if (cff or 0) >= 0 else "-"
        p = f"({s_cfo}, {s_cfi}, {s_cff})"
        return p, mapping.get(p, "Other Pattern")

    res = merged.apply(classify, axis=1)
    merged["pattern"] = [r[0] for r in res]
    merged["pattern_label"] = [r[1] for r in res]

    return merged
