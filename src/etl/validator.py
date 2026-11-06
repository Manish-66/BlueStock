"""Data Quality Validator for Nifty 100 Platform.

Sprint 3 & ETL Validation: Implements the 14 mandatory Data Quality rules
(DQ-01 to DQ-14) specified in Section 14 and Section 22 of the Project Specification.
"""

import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd


def validate_dq01_company_pk_uniqueness(companies_df: pd.DataFrame) -> Tuple[bool, int, int]:
    """DQ-01: Company PK Uniqueness: len(companies) == companies.id.nunique() (CRITICAL)."""
    id_col = "id" if "id" in companies_df.columns else "company_id"
    total = len(companies_df)
    unique = companies_df[id_col].nunique()
    return total == unique, total, unique


def validate_dq02_annual_pk_uniqueness(df: pd.DataFrame) -> Tuple[bool, int]:
    """DQ-02: Annual PK Uniqueness: No duplicate (company_id, year) (CRITICAL)."""
    dups = df.duplicated(subset=["company_id", "year"], keep=False).sum()
    return int(dups) == 0, int(dups)


def validate_dq03_fk_integrity(parent_ids: Set[str], child_df: pd.DataFrame, col: str = "company_id") -> Tuple[bool, Set[str]]:
    """DQ-03: FK Integrity: All company_id in child tables exist in companies.id (CRITICAL)."""
    child_ids = set(child_df[col].dropna().astype(str).str.strip().str.upper())
    orphans = child_ids - parent_ids
    return len(orphans) == 0, orphans


def validate_dq04_bs_balance(total_assets: float, total_liabilities: float, tolerance: float = 0.01) -> bool:
    """DQ-04: Balance Sheet Balance: |total_assets - total_liabilities| / total_assets < 0.01 (WARNING)."""
    if total_assets == 0 or pd.isna(total_assets) or pd.isna(total_liabilities):
        return True
    diff_pct = abs(total_assets - total_liabilities) / abs(total_assets)
    return diff_pct < tolerance


def validate_dq05_opm_cross_check(sales: float, op_profit: float, opm_pct: float, tolerance: float = 1.0) -> bool:
    """DQ-05: OPM Cross-Check: |opm_percentage - (op_profit/sales * 100)| < 1.0 (WARNING)."""
    if sales == 0 or pd.isna(sales) or pd.isna(op_profit) or pd.isna(opm_pct):
        return True
    computed = (op_profit / sales) * 100.0
    return abs(opm_pct - computed) < tolerance


def validate_dq06_positive_sales(sales: float, is_bank: bool = False) -> bool:
    """DQ-06: Positive Sales: sales > 0 for all non-bank companies (WARNING)."""
    if is_bank:
        return True
    if pd.isna(sales):
        return False
    return sales > 0


def validate_dq07_year_format(norm_year: str) -> bool:
    """DQ-07: Year Format: After normalize_year(), matches r'^\\d{4}-\\d{2}$' or TTM (CRITICAL)."""
    if not norm_year or pd.isna(norm_year):
        return False
    s = str(norm_year).strip()
    return bool(re.match(r"^\d{4}-\d{2}$", s)) or s == "TTM"


def validate_dq08_ticker_format(ticker: str) -> bool:
    """DQ-08: Ticker Format: company_id uppercase, stripped, length 2-12 chars (CRITICAL)."""
    if not ticker or pd.isna(ticker):
        return False
    s = str(ticker).strip().upper()
    return 2 <= len(s) <= 12 and bool(re.match(r"^[A-Z0-9&\-]+$", s))


def validate_dq09_net_cash_check(net_cash: float, cfo: float, cfi: float, cff: float, tolerance: float = 10.0) -> bool:
    """DQ-09: Net Cash Check: |net_cash_flow - (CFO + CFI + CFF)| <= 10 (Cr tolerance) (WARNING)."""
    if any(pd.isna(v) for v in [net_cash, cfo, cfi, cff]):
        return True
    expected = cfo + cfi + cff
    return abs(net_cash - expected) <= tolerance


def validate_dq10_non_negative_fixed_assets(fixed_assets: float) -> bool:
    """DQ-10: Non-Negative Fixed Assets: fixed_assets >= 0 (WARNING)."""
    if pd.isna(fixed_assets):
        return True
    return fixed_assets >= 0


def validate_dq11_tax_rate_range(tax_pct: float) -> bool:
    """DQ-11: Tax Rate Range: 0 <= tax_percentage <= 60 (WARNING)."""
    if pd.isna(tax_pct):
        return True
    return 0.0 <= tax_pct <= 60.0


def validate_dq12_dividend_payout_cap(payout_pct: float) -> bool:
    """DQ-12: Dividend Payout Cap: dividend_payout <= 200 pct (WARNING)."""
    if pd.isna(payout_pct):
        return True
    return payout_pct <= 200.0


def validate_dq13_url_validity(url: str) -> bool:
    """DQ-13: URL Validity: well-formed http/https URL format (WARNING)."""
    if not url or pd.isna(url):
        return False
    url_pattern = re.compile(
        r"^https?://"
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
        r"localhost|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        r"(?::\d+)?"
        r"(?:/?|[/?]\S+)$", re.IGNORECASE
    )
    return bool(url_pattern.match(str(url).strip()))


def validate_dq14_eps_sign_consistency(eps: float, net_profit: float) -> bool:
    """DQ-14: EPS Sign Consistency: eps > 0 if net_profit > 0 (WARNING)."""
    if pd.isna(eps) or pd.isna(net_profit):
        return True
    if net_profit > 0:
        return eps > 0
    return True
