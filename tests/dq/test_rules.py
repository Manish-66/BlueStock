"""Unit Tests for 14 Data Quality Rules (DQ-01 to DQ-14).

Sprint 3: Screener & Peer Comparison Engine (Day 21).
Validates rules defined in Section 14 and Section 22 of the Project Specification.
All tests must pass with 0 failures.
"""

import os
import sqlite3
import pandas as pd
import pytest

from src.etl.loader import DB_PATH, normalize_ticker, normalize_year
from src.etl.validator import (
    validate_dq01_company_pk_uniqueness,
    validate_dq02_annual_pk_uniqueness,
    validate_dq03_fk_integrity,
    validate_dq04_bs_balance,
    validate_dq05_opm_cross_check,
    validate_dq06_positive_sales,
    validate_dq07_year_format,
    validate_dq08_ticker_format,
    validate_dq09_net_cash_check,
    validate_dq10_non_negative_fixed_assets,
    validate_dq11_tax_rate_range,
    validate_dq12_dividend_payout_cap,
    validate_dq13_url_validity,
    validate_dq14_eps_sign_consistency,
)


@pytest.fixture(scope="module")
def db_conn():
    """Fixture providing read-only SQLite database connection."""
    assert os.path.exists(DB_PATH), f"Database not found at: {DB_PATH}"
    conn = sqlite3.connect(DB_PATH)
    yield conn
    conn.close()


def test_dq01_company_pk_uniqueness(db_conn):
    """DQ-01: Company PK Uniqueness: exactly 92 unique companies."""
    df_comp = pd.read_sql_query("SELECT id FROM companies", db_conn)
    is_valid, total, unique = validate_dq01_company_pk_uniqueness(df_comp)
    assert is_valid is True, f"Company IDs are not unique: total={total}, unique={unique}"
    assert unique == 92, f"Expected 92 companies, found {unique}"


def test_dq02_annual_pk_uniqueness(db_conn):
    """DQ-02: Annual PK Uniqueness: No duplicate (company_id, year) in child tables."""
    for table in ["profitandloss", "balancesheet", "cashflow", "financial_ratios", "market_cap"]:
        df = pd.read_sql_query(f"SELECT company_id, year FROM {table}", db_conn)
        is_valid, dups = validate_dq02_annual_pk_uniqueness(df)
        assert is_valid is True, f"Found {dups} duplicates in {table}"


def test_dq03_fk_integrity(db_conn):
    """DQ-03: FK Integrity: All child table company_id exist in companies table."""
    df_comp = pd.read_sql_query("SELECT id FROM companies", db_conn)
    parent_ids = set(df_comp["id"].str.strip().str.upper())

    for table in ["profitandloss", "balancesheet", "cashflow", "sectors", "peer_groups"]:
        df_child = pd.read_sql_query(f"SELECT DISTINCT company_id FROM {table}", db_conn)
        is_valid, orphans = validate_dq03_fk_integrity(parent_ids, df_child)
        assert is_valid is True, f"Found orphan IDs in {table}: {orphans}"


def test_dq04_bs_balance():
    """DQ-04: Balance Sheet Balance: |total_assets - total_liabilities| / total_assets < 0.01."""
    # Balanced case
    assert validate_dq04_bs_balance(1000.0, 1000.0) is True
    # Within 1% tolerance
    assert validate_dq04_bs_balance(1000.0, 1005.0) is True
    # Violation (> 1% mismatch triggers WARNING flag)
    assert validate_dq04_bs_balance(1000.0, 1020.0) is False


def test_dq05_opm_cross_check():
    """DQ-05: OPM Cross-Check: |opm_percentage - (op_profit / sales * 100)| < 1.0."""
    # Valid matching case
    assert validate_dq05_opm_cross_check(sales=1000.0, op_profit=250.0, opm_pct=25.0) is True
    # Discrepancy case (> 1.0 divergence triggers flag)
    assert validate_dq05_opm_cross_check(sales=1000.0, op_profit=200.0, opm_pct=25.0) is False


def test_dq06_positive_sales():
    """DQ-06: Positive Sales: sales > 0 for all non-bank companies."""
    # Positive sales passes
    assert validate_dq06_positive_sales(sales=50000.0, is_bank=False) is True
    # Non-positive sales flags
    assert validate_dq06_positive_sales(sales=0.0, is_bank=False) is False
    assert validate_dq06_positive_sales(sales=-10.0, is_bank=False) is False
    # Banks can have 0 reported top-line sales
    assert validate_dq06_positive_sales(sales=0.0, is_bank=True) is True


def test_dq07_year_format():
    """DQ-07: Year Format: After normalize_year(), matches r'^\\d{4}-\\d{2}$' or TTM."""
    assert validate_dq07_year_format("2023-03") is True
    assert validate_dq07_year_format("2024-12") is True
    assert validate_dq07_year_format("TTM") is True
    assert validate_dq07_year_format("PARSE_ERROR") is False
    assert validate_dq07_year_format("invalid_year") is False

    # Check normalizer function output directly
    assert normalize_year("Mar-23") == "2023-03"
    assert normalize_year("Dec 2022") == "2022-12"
    assert normalize_year("2024") == "2024-03"


def test_dq08_ticker_format():
    """DQ-08: Ticker Format: uppercase, stripped, 2-12 valid characters."""
    assert validate_dq08_ticker_format("TCS") is True
    assert validate_dq08_ticker_format("BAJAJ-AUTO") is True
    assert validate_dq08_ticker_format("M&M") is True
    assert validate_dq08_ticker_format("A") is False  # Too short
    assert validate_dq08_ticker_format("VERYLONGSYMBOLNAME") is False  # Too long

    # Check normalizer function
    assert normalize_ticker("  infy  ") == "INFY"
    assert normalize_ticker("tcs") == "TCS"


def test_dq09_net_cash_check():
    """DQ-09: Net Cash Check: |net_cash_flow - (CFO + CFI + CFF)| <= 10 Cr."""
    # Balanced cash flows
    assert validate_dq09_net_cash_check(net_cash=100.0, cfo=300.0, cfi=-150.0, cff=-50.0) is True
    # Within 10 Cr tolerance
    assert validate_dq09_net_cash_check(net_cash=105.0, cfo=300.0, cfi=-150.0, cff=-50.0) is True
    # Out of tolerance flag
    assert validate_dq09_net_cash_check(net_cash=150.0, cfo=300.0, cfi=-150.0, cff=-50.0) is False


def test_dq10_non_negative_fixed_assets():
    """DQ-10: Non-Negative Fixed Assets: fixed_assets >= 0."""
    assert validate_dq10_non_negative_fixed_assets(5000.0) is True
    assert validate_dq10_non_negative_fixed_assets(0.0) is True
    assert validate_dq10_non_negative_fixed_assets(-50.0) is False


def test_dq11_tax_rate_range():
    """DQ-11: Tax Rate Range: 0 <= tax_percentage <= 60."""
    assert validate_dq11_tax_rate_range(25.17) is True
    assert validate_dq11_tax_rate_range(0.0) is True
    assert validate_dq11_tax_rate_range(58.0) is True
    assert validate_dq11_tax_rate_range(-5.0) is False
    assert validate_dq11_tax_rate_range(75.0) is False


def test_dq12_dividend_payout_cap():
    """DQ-12: Dividend Payout Cap: dividend_payout <= 200 pct."""
    assert validate_dq12_dividend_payout_cap(35.5) is True
    assert validate_dq12_dividend_payout_cap(100.0) is True
    assert validate_dq12_dividend_payout_cap(180.0) is True
    assert validate_dq12_dividend_payout_cap(250.0) is False


def test_dq13_url_validity():
    """DQ-13: URL Validity: well-formed http/https Annual Report URL."""
    assert validate_dq13_url_validity("https://www.bseindia.com/annualreport/TCS_2023.pdf") is True
    assert validate_dq13_url_validity("http://nseindia.com/reports/infy.pdf") is True
    assert validate_dq13_url_validity("invalid_url_without_protocol") is False
    assert validate_dq13_url_validity("") is False


def test_dq14_eps_sign_consistency():
    """DQ-14: EPS Sign Consistency: eps > 0 if net_profit > 0."""
    # Positive net profit and positive eps passes
    assert validate_dq14_eps_sign_consistency(eps=15.2, net_profit=1200.0) is True
    # Negative net profit with negative eps passes
    assert validate_dq14_eps_sign_consistency(eps=-3.5, net_profit=-200.0) is True
    # Inconsistent case: positive net profit but negative eps flags
    assert validate_dq14_eps_sign_consistency(eps=-1.5, net_profit=500.0) is False
