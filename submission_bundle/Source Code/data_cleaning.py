"""
data_cleaning.py
================
Day 2 Data Cleaning & Transformation Pipeline:
  1. Clean 02_nav_history.csv -> data/processed/clean_nav.csv
     - Parse dates to datetime (ISO YYYY-MM-DD)
     - Sort by amfi_code and date
     - Remove any duplicate entries
     - Forward fill any missing NAV points
     - Validate NAV > 0
     - Compute daily_return per scheme
  2. Clean 08_investor_transactions.csv -> data/processed/clean_transactions.csv
     - Standardize transaction_type (SIP, Lumpsum, Redemption)
     - Standardize date format YYYY-MM-DD
     - Validate amount_inr > 0
     - Check and clean KYC status
  3. Clean 07_scheme_performance.csv -> data/processed/clean_performance.csv
     - Validate numeric returns
     - Check expense_ratio range (0.1% to 2.5%)
     - Flag negative Sharpe ratios
  4. Clean remaining datasets:
     - 01_fund_master.csv -> clean_fund_master.csv
     - 03_aum_by_fund_house.csv -> clean_aum.csv
     - 04_monthly_sip_inflows.csv -> clean_sip_inflows.csv (handle 12 nulls gracefully)
     - 05_category_inflows.csv -> clean_category_inflows.csv
     - 06_industry_folio_count.csv -> clean_folio_count.csv
     - 09_portfolio_holdings.csv -> clean_portfolio_holdings.csv
     - 10_benchmark_indices.csv -> clean_benchmark_indices.csv
"""

import os
import logging
import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_RAW = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED = os.path.join(BASE_DIR, "data", "processed")

os.makedirs(DATA_PROCESSED, exist_ok=True)


def clean_nav_history() -> pd.DataFrame:
    """Task 1: Clean NAV history data."""
    logger.info("Cleaning nav_history.csv...")
    df = pd.read_csv(os.path.join(DATA_RAW, "02_nav_history.csv"))
    
    # 1. Parse dates to datetime
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    
    # 2. Sort by amfi_code and date
    df = df.sort_values(by=["amfi_code", "date"]).reset_index(drop=True)
    
    # 3. Deduplicate
    df = df.drop_duplicates(subset=["amfi_code", "date"])
    
    # 4. Forward fill any missing NAV per scheme
    df["nav"] = df.groupby("amfi_code")["nav"].ffill()
    
    # 5. Validate NAV > 0
    assert (df["nav"] > 0).all(), "Invalid NAV <= 0 found!"
    
    # 6. Compute daily return
    df["daily_return"] = df.groupby("amfi_code")["nav"].pct_change().round(6)
    
    out_file = os.path.join(DATA_PROCESSED, "clean_nav.csv")
    df.to_csv(out_file, index=False)
    logger.info(f"clean_nav.csv saved: {len(df):,} rows -> {out_file}")
    return df


def clean_investor_transactions() -> pd.DataFrame:
    """Task 2: Clean investor transactions data."""
    logger.info("Cleaning investor_transactions.csv...")
    df = pd.read_csv(os.path.join(DATA_RAW, "08_investor_transactions.csv"))
    
    # 1. Standardize transaction_type
    df["transaction_type"] = df["transaction_type"].astype(str).str.strip().str.title()
    # Normalize 'Sip' -> 'SIP'
    df["transaction_type"] = df["transaction_type"].replace({"Sip": "SIP"})
    
    # 2. Parse dates
    df["transaction_date"] = pd.to_datetime(df["transaction_date"]).dt.strftime("%Y-%m-%d")
    
    # 3. Validate amount > 0
    df = df[df["amount_inr"] > 0]
    
    # 4. Standardize KYC status
    df["kyc_status"] = df["kyc_status"].astype(str).str.strip().str.title()
    
    # Deduplicate
    df = df.drop_duplicates().reset_index(drop=True)
    
    out_file = os.path.join(DATA_PROCESSED, "clean_transactions.csv")
    df.to_csv(out_file, index=False)
    logger.info(f"clean_transactions.csv saved: {len(df):,} rows -> {out_file}")
    return df


def clean_scheme_performance() -> pd.DataFrame:
    """Task 3: Clean scheme performance data."""
    logger.info("Cleaning scheme_performance.csv...")
    df = pd.read_csv(os.path.join(DATA_RAW, "07_scheme_performance.csv"))
    
    # Numeric returns validation
    numeric_cols = [
        "return_1yr_pct", "return_3yr_pct", "return_5yr_pct", "benchmark_3yr_pct",
        "alpha", "beta", "sharpe_ratio", "sortino_ratio", "std_dev_ann_pct",
        "max_drawdown_pct", "aum_crore", "expense_ratio_pct"
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        
    # Flag negative Sharpe ratios
    df["is_negative_sharpe"] = df["sharpe_ratio"] < 0
    
    # Validate expense ratio range
    valid_er = df["expense_ratio_pct"].between(0.1, 2.5).all()
    if not valid_er:
        logger.warning("Some expense ratios fall outside 0.1% - 2.5%!")
        
    out_file = os.path.join(DATA_PROCESSED, "clean_performance.csv")
    df.to_csv(out_file, index=False)
    logger.info(f"clean_performance.csv saved: {len(df):,} rows -> {out_file}")
    return df


def clean_all_datasets() -> None:
    """Clean all remaining datasets for complete SQLite database staging."""
    logger.info("Cleaning all remaining 7 datasets...")
    
    # 01 Fund Master
    fm = pd.read_csv(os.path.join(DATA_RAW, "01_fund_master.csv"))
    fm["launch_date"] = pd.to_datetime(fm["launch_date"]).dt.strftime("%Y-%m-%d")
    fm.to_csv(os.path.join(DATA_PROCESSED, "clean_fund_master.csv"), index=False)
    
    # 03 AUM
    aum = pd.read_csv(os.path.join(DATA_RAW, "03_aum_by_fund_house.csv"))
    aum["date"] = pd.to_datetime(aum["date"]).dt.strftime("%Y-%m-%d")
    aum.to_csv(os.path.join(DATA_PROCESSED, "clean_aum.csv"), index=False)
    
    # 04 SIP Inflows
    sip = pd.read_csv(os.path.join(DATA_RAW, "04_monthly_sip_inflows.csv"))
    # Forward fill or fillna for year 1 YoY growth
    sip["yoy_growth_pct"] = sip["yoy_growth_pct"].fillna(0.0)
    sip.to_csv(os.path.join(DATA_PROCESSED, "clean_sip_inflows.csv"), index=False)
    
    # 05 Category Inflows
    ci = pd.read_csv(os.path.join(DATA_RAW, "05_category_inflows.csv"))
    ci.to_csv(os.path.join(DATA_PROCESSED, "clean_category_inflows.csv"), index=False)
    
    # 06 Folio Count
    folio = pd.read_csv(os.path.join(DATA_RAW, "06_industry_folio_count.csv"))
    folio.to_csv(os.path.join(DATA_PROCESSED, "clean_folio_count.csv"), index=False)
    
    # 09 Portfolio Holdings
    port = pd.read_csv(os.path.join(DATA_RAW, "09_portfolio_holdings.csv"))
    port["portfolio_date"] = pd.to_datetime(port["portfolio_date"]).dt.strftime("%Y-%m-%d")
    port.to_csv(os.path.join(DATA_PROCESSED, "clean_portfolio_holdings.csv"), index=False)
    
    # 10 Benchmark Indices
    bench = pd.read_csv(os.path.join(DATA_RAW, "10_benchmark_indices.csv"))
    bench["date"] = pd.to_datetime(bench["date"]).dt.strftime("%Y-%m-%d")
    bench.to_csv(os.path.join(DATA_PROCESSED, "clean_benchmark_indices.csv"), index=False)
    
    logger.info("All 10 clean CSV datasets successfully processed into data/processed/.")


if __name__ == "__main__":
    clean_nav_history()
    clean_investor_transactions()
    clean_scheme_performance()
    clean_all_datasets()
