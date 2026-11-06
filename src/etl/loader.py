"""ETL Loader for Nifty 100 Financial Intelligence Platform.

Loads all core and supplementary Excel files, normalises tickers and years,
resolves duplicates and orphans, and persists clean relational tables to SQLite.
"""

import glob
import os
import re
import sqlite3
from typing import Dict, Optional, Tuple
import pandas as pd


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "nifty100.db")


def normalize_ticker(val: Optional[str]) -> Optional[str]:
    """Normalize ticker: strip whitespace, convert to uppercase."""
    if val is None or pd.isna(val):
        return None
    val_str = str(val).strip().upper()
    return val_str if 2 <= len(val_str) <= 12 else None


def normalize_year(val: Optional[str]) -> Optional[str]:
    """Standardize annual reporting year string to YYYY-MM format or TTM."""
    if val is None or pd.isna(val):
        return None
    s = str(val).strip()
    if s == "TTM":
        return "TTM"
    if re.match(r"^\d{4}-\d{2}$", s):
        return s
    if re.match(r"^\d{4}\.5$", s):
        y = s.split(".")[0]
        return f"{y}-09"

    month_map = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
        "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12",
        "march": "03", "june": "06", "september": "09", "december": "12"
    }

    m = re.match(r"^([a-zA-Z]+)[ -]?(\d{2,4})", s)
    if m:
        mon_str, yr_str = m.group(1).lower(), m.group(2)
        mon = month_map.get(mon_str)
        if mon:
            yr = ("20" + yr_str if int(yr_str) < 50 else "19" + yr_str) if len(yr_str) == 2 else yr_str
            return f"{yr}-{mon}"

    m_int = re.match(r"^(?:FY)?(\d{2,4})$", s, re.IGNORECASE)
    if m_int:
        yr_str = m_int.group(1)
        yr = ("20" + yr_str if int(yr_str) < 50 else "19" + yr_str) if len(yr_str) == 2 else yr_str
        return f"{yr}-03"

    return "PARSE_ERROR"


def find_file(keyword: str, root_dir: str = ".") -> str:
    """Find file by keyword in filename."""
    matches = glob.glob(os.path.join(root_dir, f"*{keyword}*.xlsx"))
    if not matches:
        matches = glob.glob(os.path.join(root_dir, "**", f"*{keyword}*.xlsx"), recursive=True)
    if not matches:
        raise FileNotFoundError(f"Could not find Excel file for keyword: {keyword}")
    return matches[0]


def load_all_datasets(workspace_root: str = ".") -> Dict[str, pd.DataFrame]:
    """Load, clean, and normalise all 12 core and supplementary datasets."""
    datasets: Dict[str, pd.DataFrame] = {}

    # 1. Companies (Core)
    comp_file = find_file("companies", workspace_root)
    df_comp = pd.read_excel(comp_file, header=1)
    df_comp["id"] = df_comp["id"].apply(normalize_ticker)
    df_comp = df_comp.dropna(subset=["id"]).drop_duplicates(subset=["id"], keep="last")
    datasets["companies"] = df_comp

    valid_tickers = set(df_comp["id"].unique())

    # 2. Sectors
    sec_file = find_file("sectors", workspace_root)
    df_sec = pd.read_excel(sec_file)
    df_sec["company_id"] = df_sec["company_id"].apply(normalize_ticker)
    df_sec = df_sec[df_sec["company_id"].isin(valid_tickers)].drop_duplicates(subset=["company_id"], keep="last")
    datasets["sectors"] = df_sec

    # 3. Profit & Loss (Core)
    pl_file = find_file("profitandloss", workspace_root)
    df_pl = pd.read_excel(pl_file, header=1)
    df_pl["company_id"] = df_pl["company_id"].apply(normalize_ticker)
    df_pl = df_pl[df_pl["company_id"].isin(valid_tickers)]
    df_pl["year"] = df_pl["year"].apply(normalize_year)
    df_pl = df_pl[df_pl["year"] != "PARSE_ERROR"].drop_duplicates(subset=["company_id", "year"], keep="last")
    datasets["profitandloss"] = df_pl

    # 4. Balance Sheet (Core)
    bs_file = find_file("balancesheet", workspace_root)
    df_bs = pd.read_excel(bs_file, header=1)
    df_bs["company_id"] = df_bs["company_id"].apply(normalize_ticker)
    df_bs = df_bs[df_bs["company_id"].isin(valid_tickers)]
    df_bs["year"] = df_bs["year"].apply(normalize_year)
    df_bs = df_bs[df_bs["year"] != "PARSE_ERROR"].drop_duplicates(subset=["company_id", "year"], keep="last")
    datasets["balancesheet"] = df_bs

    # 5. Cash Flow (Core)
    cf_file = find_file("cashflow", workspace_root)
    df_cf = pd.read_excel(cf_file, header=1)
    df_cf["company_id"] = df_cf["company_id"].apply(normalize_ticker)
    df_cf = df_cf[df_cf["company_id"].isin(valid_tickers)]
    df_cf["year"] = df_cf["year"].apply(normalize_year)
    df_cf = df_cf[df_cf["year"] != "PARSE_ERROR"].drop_duplicates(subset=["company_id", "year"], keep="last")
    datasets["cashflow"] = df_cf

    # 6. Financial Ratios
    fr_file = find_file("financial_ratios", workspace_root)
    df_fr = pd.read_excel(fr_file)
    df_fr["company_id"] = df_fr["company_id"].apply(normalize_ticker)
    df_fr = df_fr[df_fr["company_id"].isin(valid_tickers)]
    df_fr["year"] = df_fr["year"].apply(normalize_year)
    df_fr = df_fr[df_fr["year"] != "PARSE_ERROR"].drop_duplicates(subset=["company_id", "year"], keep="last")
    datasets["financial_ratios"] = df_fr

    # 7. Market Cap
    mc_file = find_file("market_cap", workspace_root)
    df_mc = pd.read_excel(mc_file)
    df_mc["company_id"] = df_mc["company_id"].apply(normalize_ticker)
    df_mc = df_mc[df_mc["company_id"].isin(valid_tickers)]
    df_mc["year"] = df_mc["year"].apply(normalize_year)
    df_mc = df_mc[df_mc["year"] != "PARSE_ERROR"].drop_duplicates(subset=["company_id", "year"], keep="last")
    datasets["market_cap"] = df_mc

    # 8. Peer Groups
    pg_file = find_file("peer_groups", workspace_root)
    df_pg = pd.read_excel(pg_file)
    df_pg["company_id"] = df_pg["company_id"].apply(normalize_ticker)
    df_pg = df_pg[df_pg["company_id"].isin(valid_tickers)].drop_duplicates(subset=["peer_group_name", "company_id"], keep="last")
    datasets["peer_groups"] = df_pg

    # 9. Stock Prices
    sp_file = find_file("stock_prices", workspace_root)
    df_sp = pd.read_excel(sp_file)
    df_sp["company_id"] = df_sp["company_id"].apply(normalize_ticker)
    df_sp = df_sp[df_sp["company_id"].isin(valid_tickers)]
    datasets["stock_prices"] = df_sp

    # 10. Documents (Core)
    doc_file = find_file("documents", workspace_root)
    df_doc = pd.read_excel(doc_file, header=1)
    df_doc["company_id"] = df_doc["company_id"].apply(normalize_ticker)
    df_doc = df_doc[df_doc["company_id"].isin(valid_tickers)]
    year_col = "Year" if "Year" in df_doc.columns else "year"
    df_doc[year_col] = df_doc[year_col].apply(normalize_year)
    datasets["documents"] = df_doc

    # 11. Analysis (Core)
    an_file = find_file("analysis", workspace_root)
    df_an = pd.read_excel(an_file, header=1)
    df_an["company_id"] = df_an["company_id"].apply(normalize_ticker)
    df_an = df_an[df_an["company_id"].isin(valid_tickers)]
    datasets["analysis"] = df_an

    # 12. Pros and Cons (Core)
    pc_file = find_file("prosandcons", workspace_root)
    df_pc = pd.read_excel(pc_file, header=1)
    df_pc["company_id"] = df_pc["company_id"].apply(normalize_ticker)
    df_pc = df_pc[df_pc["company_id"].isin(valid_tickers)]
    datasets["prosandcons"] = df_pc

    return datasets


def init_database(db_path: str = DB_PATH, workspace_root: str = ".") -> str:
    """Build and populate SQLite database nifty100.db with all normalised tables."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    datasets = load_all_datasets(workspace_root)

    with sqlite3.connect(db_path) as conn:
        for name, df in datasets.items():
            df.to_sql(name, conn, if_exists="replace", index=False)

    return db_path


if __name__ == "__main__":
    path = init_database()
    print(f"nifty100.db successfully initialized at: {path}")
