"""Dashboard Integration Tests for Sprint 4.

Validates Acceptance Criteria AC-08 (<3s load time), AC-09 (CSV export),
and tests chart generation across 10 sample tickers.
"""

import time
import pandas as pd
import pytest

from src.dashboard.utils.charts import (
    plot_bs_history,
    plot_capital_allocation_treemap,
    plot_cf_history,
    plot_pb_roe_scatter,
    plot_pl_history,
    plot_radar_comparison,
    plot_sector_bubble,
    plot_sector_donut,
    plot_trend_sparkline,
)
from src.dashboard.utils.db import (
    get_capital_allocation_data,
    get_company_details,
    load_universe_data,
)
from src.screener.engine import run_preset


SAMPLE_TICKERS = [
    "TCS", "RELIANCE", "HDFCBANK", "INFY", "ITC",
    "ASIANPAINT", "LT", "MARUTI", "SUNPHARMA", "NTPC"
]


def test_universe_loading():
    """Verify universe loads exactly 92 companies with complete KPI schema."""
    df_u = load_universe_data()
    assert len(df_u) == 92
    assert "composite_quality_score" in df_u.columns
    assert "valuation_badge" in df_u.columns


def test_capital_allocation_classification():
    """Verify all 92 companies are assigned to one of the 8 patterns without nulls."""
    df_cap = get_capital_allocation_data()
    assert len(df_cap) == 92
    assert df_cap["pattern"].isna().sum() == 0
    assert df_cap["pattern_label"].isna().sum() == 0


@pytest.mark.parametrize("ticker", SAMPLE_TICKERS)
def test_company_profile_load_time_and_charts(ticker):
    """AC-08: Verify Company Profile loads in < 3.0 seconds and charts render correctly."""
    t0 = time.time()
    details = get_company_details(ticker)
    elapsed = time.time() - t0

    assert elapsed < 3.0, f"Load time exceeded 3s for {ticker}: {elapsed:.3f}s"
    assert len(details["company"]) > 0, f"Company info empty for {ticker}"

    # Verify chart creation
    fig_pl = plot_pl_history(details["pl"])
    fig_bs = plot_bs_history(details["bs"])
    fig_cf = plot_cf_history(details["cf"])

    assert fig_pl is not None
    assert fig_bs is not None
    assert fig_cf is not None


def test_global_dashboard_charts():
    """Verify macro charts render without errors."""
    df_u = load_universe_data()
    df_cap = get_capital_allocation_data()

    fig_donut = plot_sector_donut(df_u)
    fig_bubble = plot_sector_bubble(df_u)
    fig_scatter = plot_pb_roe_scatter(df_u)
    fig_treemap = plot_capital_allocation_treemap(df_cap)

    assert fig_donut is not None
    assert fig_bubble is not None
    assert fig_scatter is not None
    assert fig_treemap is not None


def test_screener_csv_export():
    """AC-09: Verify Screener produces valid CSV export with correct headers."""
    df_u = load_universe_data()
    res = run_preset("quality_compounder", df_u)
    csv_str = res.to_csv(index=False)

    assert len(csv_str) > 0
    assert "company_id" in csv_str
    assert "composite_quality_score" in csv_str
