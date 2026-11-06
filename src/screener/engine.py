"""Financial Screener and Scoring Engine for Nifty 100 Platform.

Sprint 3: Screener & Peer Comparison Engine (Days 15-17).
Supports 15 filterable metrics, 6 preset templates, sector-relative
composite quality scoring (0-100 scale), and formatted Excel reporting.
"""

import os
import re
import sqlite3
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
import pandas as pd
import yaml

from src.etl.loader import DB_PATH, init_database


CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "config",
    "screener_config.yaml"
)

OUTPUT_EXCEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "output",
    "screener_output.xlsx"
)


def load_config(path: str = CONFIG_PATH) -> Dict[str, Any]:
    """Load analyst-editable screener configuration YAML."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _calc_cagr(series: pd.Series, n: int = 5) -> float:
    """Compute Compound Annual Growth Rate handling sign changes and missing values."""
    s = series.dropna()
    if len(s) < 2:
        return np.nan
    end_val = float(s.iloc[-1])
    if len(s) <= n:
        start_val = float(s.iloc[0])
        actual_n = len(s) - 1
    else:
        start_val = float(s.iloc[-n - 1])
        actual_n = n

    if actual_n <= 0 or start_val <= 0 or end_val <= 0:
        return np.nan
    try:
        return ((end_val / start_val) ** (1.0 / actual_n) - 1.0) * 100.0
    except (ZeroDivisionError, ValueError):
        return np.nan


def _winsorized_min_max_scale(series: pd.Series, p_low: float = 0.10, p_high: float = 0.90) -> pd.Series:
    """Normalize series to 0-100 scale using P10/P90 winsorisation."""
    s = series.astype(float).copy()
    valid = s.dropna()
    if len(valid) == 0:
        return pd.Series(50.0, index=s.index)

    low_val = np.percentile(valid, p_low * 100)
    high_val = np.percentile(valid, p_high * 100)

    if np.isclose(high_val, low_val):
        return pd.Series(50.0, index=s.index)

    clipped = s.clip(lower=low_val, upper=high_val)
    scaled = (clipped - low_val) / (high_val - low_val) * 100.0
    return scaled.fillna(scaled.median() if not np.isnan(scaled.median()) else 50.0)


def _compute_de_score(de: float, is_financial: bool) -> float:
    """Score Debt-to-Equity (0-100) where lower leverage yields higher score."""
    if is_financial:
        return 85.0
    if pd.isna(de) or de <= 0.05:
        return 100.0
    if de <= 0.5:
        return 100.0 - (de / 0.5) * 15.0
    if de <= 1.0:
        return 85.0 - ((de - 0.5) / 0.5) * 15.0
    if de <= 2.0:
        return 70.0 - ((de - 1.0) / 1.0) * 20.0
    if de <= 5.0:
        return 50.0 - ((de - 2.0) / 3.0) * 50.0
    return 0.0


def _compute_icr_score(icr: float, is_debt_free: bool) -> float:
    """Score Interest Coverage Ratio (0-100) where higher coverage yields higher score."""
    if is_debt_free or pd.isna(icr) or np.isinf(icr) or icr >= 10.0:
        return 100.0
    if icr >= 5.0:
        return 75.0 + ((icr - 5.0) / 5.0) * 25.0
    if icr >= 3.0:
        return 50.0 + ((icr - 3.0) / 2.0) * 25.0
    if icr >= 1.5:
        return ((icr - 1.5) / 1.5) * 50.0
    return 0.0


def build_universe_dataframe(db_path: str = DB_PATH) -> pd.DataFrame:
    """Build the comprehensive 92-company analytical universe dataframe from SQLite."""
    if not os.path.exists(db_path):
        init_database(db_path)

    with sqlite3.connect(db_path) as conn:
        df_comp = pd.read_sql_query("SELECT * FROM companies", conn)
        df_sec = pd.read_sql_query("SELECT * FROM sectors", conn)
        df_pl = pd.read_sql_query("SELECT * FROM profitandloss", conn)
        df_fr = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
        df_mc = pd.read_sql_query("SELECT * FROM market_cap", conn)
        df_bs = pd.read_sql_query("SELECT * FROM balancesheet", conn)

    # Standardize IDs
    df_comp["company_id"] = df_comp["id"].str.strip().str.upper()
    for d in [df_sec, df_pl, df_fr, df_mc, df_bs]:
        d["company_id"] = d["company_id"].str.strip().str.upper()

    valid_tickers = sorted(df_comp["company_id"].unique())

    # Multi-year growth metrics from P&L
    cagr_list = []
    for cid in valid_tickers:
        sub_pl = df_pl[(df_pl["company_id"] == cid) & (df_pl["year"] != "TTM")].sort_values("year")
        rev_5 = _calc_cagr(sub_pl["sales"], 5)
        rev_3 = _calc_cagr(sub_pl["sales"], 3)
        pat_5 = _calc_cagr(sub_pl["net_profit"], 5)
        pat_3 = _calc_cagr(sub_pl["net_profit"], 3)
        eps_5 = _calc_cagr(sub_pl["eps"], 5)
        cagr_list.append({
            "company_id": cid,
            "revenue_cagr_5yr": rev_5,
            "revenue_cagr_3yr": rev_3,
            "pat_cagr_5yr": pat_5,
            "pat_cagr_3yr": pat_3,
            "eps_cagr_5yr": eps_5
        })
    df_cagr = pd.DataFrame(cagr_list)

    # Multi-year cashflow & leverage trends
    fcf_cagr_list = []
    for cid in valid_tickers:
        sub_fr = df_fr[df_fr["company_id"] == cid].sort_values("year")
        fcf_5 = _calc_cagr(sub_fr["free_cash_flow_cr"], 5) if len(sub_fr) > 0 else np.nan
        de_series = sub_fr["debt_to_equity"].dropna()
        de_declining = bool(de_series.iloc[-1] < de_series.iloc[-2]) if len(de_series) >= 2 else False
        fcf_cagr_list.append({
            "company_id": cid,
            "fcf_cagr_5yr": fcf_5,
            "de_declining": de_declining
        })
    df_fcf_cagr = pd.DataFrame(fcf_cagr_list)

    # Latest year records for ratios, multiples, and P&L
    latest_pl = df_pl[df_pl["year"] != "TTM"].sort_values("year").groupby("company_id").last().reset_index()
    latest_fr = df_fr.sort_values("year").groupby("company_id").last().reset_index()
    latest_mc = df_mc.sort_values("year").groupby("company_id").last().reset_index()

    # Base dataframe
    u = df_comp[["company_id", "company_name", "roe_percentage", "roce_percentage", "book_value"]].copy()
    u = u.merge(df_sec[["company_id", "broad_sector", "sub_sector", "market_cap_category"]], on="company_id", how="left")
    u = u.merge(
        latest_pl[["company_id", "sales", "net_profit", "opm_percentage", "dividend_payout", "operating_profit", "interest"]],
        on="company_id",
        how="left"
    )
    u = u.merge(
        latest_fr[[
            "company_id", "net_profit_margin_pct", "operating_profit_margin_pct",
            "return_on_equity_pct", "debt_to_equity", "interest_coverage",
            "free_cash_flow_cr", "asset_turnover", "cash_from_operations_cr"
        ]],
        on="company_id",
        how="left"
    )
    u = u.merge(
        latest_mc[["company_id", "market_cap_crore", "pe_ratio", "pb_ratio", "ev_ebitda", "dividend_yield_pct"]],
        on="company_id",
        how="left"
    )
    u = u.merge(df_cagr, on="company_id", how="left")
    u = u.merge(df_fcf_cagr, on="company_id", how="left")

    # Data harmonisation fallbacks
    u["return_on_equity_pct"] = u["return_on_equity_pct"].fillna(u["roe_percentage"])
    u["roce_pct"] = u["roce_percentage"].fillna(u["return_on_equity_pct"])
    u["operating_profit_margin_pct"] = u["operating_profit_margin_pct"].fillna(u["opm_percentage"])
    fallback_npm = pd.Series(np.where(u["sales"] > 0, (u["net_profit"] / u["sales"]) * 100.0, 0.0), index=u.index)
    u["net_profit_margin_pct"] = u["net_profit_margin_pct"].fillna(fallback_npm)
    u["cfo_pat_ratio"] = pd.Series(
        np.where(
            u["net_profit"].fillna(0) != 0,
            u["cash_from_operations_cr"].fillna(0) / u["net_profit"],
            1.0
        ),
        index=u.index
    )

    # Debt-free & interest coverage handling
    u["is_debt_free"] = (u["debt_to_equity"].fillna(0) <= 0.05) & (u["broad_sector"] != "Financials")
    u.loc[u["is_debt_free"], "interest_coverage"] = np.inf

    # Calculate sector-relative composite quality score
    u = calculate_composite_score(u)

    return u


def calculate_composite_score(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the 0-100 sector-relative composite quality score.

    Weights:
      Profitability (35%): ROE (15%) + ROCE (10%) + NPM (10%)
      Cash Quality (30%): FCF CAGR (15%) + CFO/PAT (10%) + FCF > 0 flag (5%)
      Growth (20%): Revenue CAGR (10%) + PAT CAGR (10%)
      Leverage (15%): D/E score (10%) + ICR score (5%)
    """
    res = df.copy()

    # Rule-based leverage scores
    res["de_score"] = [
        _compute_de_score(de, sec == "Financials")
        for de, sec in zip(res["debt_to_equity"], res["broad_sector"])
    ]
    res["icr_score"] = [
        _compute_icr_score(icr, df_free)
        for icr, df_free in zip(res["interest_coverage"], res["is_debt_free"])
    ]
    res["fcf_pos_score"] = np.where(res["free_cash_flow_cr"].fillna(0) > 0, 100.0, 0.0)

    # Sector-relative winsorized normalization for continuous metrics
    norm_metrics = [
        "return_on_equity_pct", "roce_pct", "net_profit_margin_pct",
        "fcf_cagr_5yr", "cfo_pat_ratio",
        "revenue_cagr_5yr", "pat_cagr_5yr"
    ]

    for m in norm_metrics:
        # Group by broad sector; if sector group is too small (<3), use global
        res[f"{m}_norm"] = res.groupby("broad_sector")[m].transform(
            lambda s: _winsorized_min_max_scale(s) if len(s.dropna()) >= 3 else _winsorized_min_max_scale(s, 0.0, 1.0)
        )
        res[f"{m}_norm"] = res[f"{m}_norm"].fillna(_winsorized_min_max_scale(res[m]))

    # Weighted sum
    composite = (
        0.15 * res["return_on_equity_pct_norm"] +
        0.10 * res["roce_pct_norm"] +
        0.10 * res["net_profit_margin_pct_norm"] +
        0.15 * res["fcf_cagr_5yr_norm"] +
        0.10 * res["cfo_pat_ratio_norm"] +
        0.05 * res["fcf_pos_score"] +
        0.10 * res["revenue_cagr_5yr_norm"] +
        0.10 * res["pat_cagr_5yr_norm"] +
        0.10 * res["de_score"] +
        0.05 * res["icr_score"]
    )

    res["composite_quality_score"] = composite.round(2)
    return res


def apply_filters(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """Apply multi-criteria threshold filters supporting all 15 metrics.

    Features:
      - Automatically skips D/E max filter for Financials sector companies
      - Treats Debt Free label as ICR = infinity (always passes ICR min)
    """
    passed = df.copy()

    for key, threshold in filters.items():
        if threshold is None:
            continue

        # 1. ROE min
        if key == "return_on_equity_pct_min":
            passed = passed[passed["return_on_equity_pct"] >= float(threshold)]

        # 2. D/E max (Financials sector exempted)
        elif key == "debt_to_equity_max":
            is_fin = passed["broad_sector"] == "Financials"
            de_pass = passed["debt_to_equity"].fillna(0) <= float(threshold)
            passed = passed[is_fin | de_pass]

        # 3. FCF min
        elif key == "free_cash_flow_cr_min":
            passed = passed[passed["free_cash_flow_cr"] >= float(threshold)]

        # 4. Revenue CAGR 5yr min
        elif key == "revenue_cagr_5yr_min":
            passed = passed[passed["revenue_cagr_5yr"] >= float(threshold)]

        # 5. PAT CAGR 5yr min
        elif key == "pat_cagr_5yr_min":
            passed = passed[passed["pat_cagr_5yr"] >= float(threshold)]

        # 6. OPM min
        elif key == "operating_profit_margin_pct_min":
            passed = passed[passed["operating_profit_margin_pct"] >= float(threshold)]

        # 7. P/E max
        elif key == "pe_ratio_max":
            passed = passed[passed["pe_ratio"] <= float(threshold)]

        # 8. P/B max
        elif key == "pb_ratio_max":
            passed = passed[passed["pb_ratio"] <= float(threshold)]

        # 9. Dividend Yield min
        elif key == "dividend_yield_pct_min":
            passed = passed[passed["dividend_yield_pct"] >= float(threshold)]

        # 10. ICR min (Debt-Free is treated as infinity and always passes)
        elif key == "interest_coverage_min":
            icr_pass = (passed["is_debt_free"]) | (passed["interest_coverage"] >= float(threshold))
            passed = passed[icr_pass]

        # 11. Market Cap min
        elif key == "market_cap_crore_min":
            passed = passed[passed["market_cap_crore"] >= float(threshold)]

        # 12. Net Profit min
        elif key == "net_profit_min":
            passed = passed[passed["net_profit"] >= float(threshold)]

        # 13. EPS CAGR min
        elif key == "eps_cagr_5yr_min":
            passed = passed[passed["eps_cagr_5yr"] >= float(threshold)]

        # 14. Asset Turnover min
        elif key == "asset_turnover_min":
            passed = passed[passed["asset_turnover"] >= float(threshold)]

        # 15. Sales min
        elif key == "sales_min":
            passed = passed[passed["sales"] >= float(threshold)]

        # Special presets flags
        elif key == "dividend_payout_max":
            passed = passed[passed["dividend_payout"] <= float(threshold)]
        elif key == "revenue_cagr_3yr_min":
            passed = passed[passed["revenue_cagr_3yr"] >= float(threshold)]
        elif key == "de_declining" and threshold is True:
            passed = passed[passed["de_declining"] == True]

    return passed.sort_values("composite_quality_score", ascending=False)


def run_preset(preset_key: str, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Run one of the 6 predefined presets and return sorted results."""
    config = load_config()
    presets = config.get("presets", {})
    if preset_key not in presets:
        raise ValueError(f"Unknown preset: {preset_key}. Available: {list(presets.keys())}")

    if df is None:
        df = build_universe_dataframe()

    filters = presets[preset_key]["filters"]
    return apply_filters(df, filters)


def get_all_preset_results(df: Optional[pd.DataFrame] = None) -> Dict[str, pd.DataFrame]:
    """Execute all 6 presets on the 92-company universe."""
    if df is None:
        df = build_universe_dataframe()

    config = load_config()
    results = {}
    for key in config.get("presets", {}).keys():
        results[key] = run_preset(key, df)
    return results


# 20 Standard KPI Display Columns for Output Reports
KPI_COLUMNS_DISPLAY = [
    ("company_id", "Ticker"),
    ("company_name", "Company Name"),
    ("broad_sector", "Broad Sector"),
    ("market_cap_crore", "Market Cap (Cr)"),
    ("sales", "Revenue (Cr)"),
    ("net_profit", "Net Profit (Cr)"),
    ("operating_profit_margin_pct", "OPM (%)"),
    ("net_profit_margin_pct", "NPM (%)"),
    ("return_on_equity_pct", "ROE (%)"),
    ("roce_pct", "ROCE (%)"),
    ("debt_to_equity", "D/E"),
    ("interest_coverage", "ICR"),
    ("free_cash_flow_cr", "FCF (Cr)"),
    ("cfo_pat_ratio", "CFO/PAT"),
    ("pe_ratio", "P/E"),
    ("pb_ratio", "P/B"),
    ("dividend_yield_pct", "Div Yield (%)"),
    ("dividend_payout", "Div Payout (%)"),
    ("revenue_cagr_5yr", "Rev CAGR 5yr (%)"),
    ("pat_cagr_5yr", "PAT CAGR 5yr (%)"),
    ("composite_quality_score", "Composite Score")
]


def generate_screener_excel(
    output_path: str = OUTPUT_EXCEL_PATH,
    df_universe: Optional[pd.DataFrame] = None
) -> str:
    """Generate screener_output.xlsx with 6 sheets, 20 KPIs, and conditional formatting."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if df_universe is None:
        df_universe = build_universe_dataframe()

    config = load_config()
    presets = config.get("presets", {})

    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # Remove default initial sheet

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    score_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")

    green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")  # soft green
    green_font = Font(name="Calibri", size=10, color="006100")
    red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")    # soft red
    red_font = Font(name="Calibri", size=10, color="9C0006")
    default_font = Font(name="Calibri", size=10)

    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9")
    )

    for preset_key, preset_cfg in presets.items():
        sheet_title = preset_cfg.get("name", preset_key)[:31]
        ws = wb.create_sheet(title=sheet_title)
        filters = preset_cfg["filters"]

        filtered_df = apply_filters(df_universe, filters)

        # Write Header Row
        headers = [disp for _, disp in KPI_COLUMNS_DISPLAY]
        col_keys = [k for k, _ in KPI_COLUMNS_DISPLAY]
        ws.append(headers)

        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Write Data Rows
        for r_idx, (_, row) in enumerate(filtered_df.iterrows(), start=2):
            for c_idx, key in enumerate(col_keys, start=1):
                val = row.get(key, np.nan)
                cell = ws.cell(row=r_idx, column=c_idx)
                cell.border = thin_border
                cell.font = default_font

                if isinstance(val, (int, float, np.floating, np.integer)) and np.isinf(val):
                    cell.value = "Debt Free"
                    cell.alignment = Alignment(horizontal="center")
                elif pd.isna(val):
                    cell.value = "—"
                    cell.alignment = Alignment(horizontal="center")
                    continue
                elif isinstance(val, (int, np.integer)):
                    cell.value = int(val)
                    cell.alignment = Alignment(horizontal="right")
                    cell.number_format = "#,##0"
                elif isinstance(val, (float, np.floating)):
                    cell.value = round(float(val), 2)
                    cell.alignment = Alignment(horizontal="right")
                    cell.number_format = "#,##0.00"
                else:
                    cell.value = str(val)
                    cell.alignment = Alignment(horizontal="left" if c_idx <= 3 else "center")

                # Highlight composite score
                if key == "composite_quality_score":
                    cell.fill = score_fill
                    cell.font = Font(name="Calibri", size=10, bold=True)

                # Conditional formatting based on preset filter thresholds
                # Green fill for cells meeting threshold, red fill for cells failing
                if key == "return_on_equity_pct" and "return_on_equity_pct_min" in filters:
                    thresh = filters["return_on_equity_pct_min"]
                    if val >= thresh:
                        cell.fill, cell.font = green_fill, green_font
                    else:
                        cell.fill, cell.font = red_fill, red_font

                elif key == "debt_to_equity" and "debt_to_equity_max" in filters:
                    thresh = filters["debt_to_equity_max"]
                    if row.get("broad_sector") == "Financials" or val <= thresh:
                        cell.fill, cell.font = green_fill, green_font
                    else:
                        cell.fill, cell.font = red_fill, red_font

                elif key == "free_cash_flow_cr" and "free_cash_flow_cr_min" in filters:
                    thresh = filters["free_cash_flow_cr_min"]
                    if val >= thresh:
                        cell.fill, cell.font = green_fill, green_font
                    else:
                        cell.fill, cell.font = red_fill, red_font

                elif key == "revenue_cagr_5yr" and "revenue_cagr_5yr_min" in filters:
                    thresh = filters["revenue_cagr_5yr_min"]
                    if val >= thresh:
                        cell.fill, cell.font = green_fill, green_font
                    else:
                        cell.fill, cell.font = red_fill, red_font

                elif key == "pat_cagr_5yr" and "pat_cagr_5yr_min" in filters:
                    thresh = filters["pat_cagr_5yr_min"]
                    if val >= thresh:
                        cell.fill, cell.font = green_fill, green_font
                    else:
                        cell.fill, cell.font = red_fill, red_font

                elif key == "pe_ratio" and "pe_ratio_max" in filters:
                    thresh = filters["pe_ratio_max"]
                    if val <= thresh:
                        cell.fill, cell.font = green_fill, green_font
                    else:
                        cell.fill, cell.font = red_fill, red_font

                elif key == "pb_ratio" and "pb_ratio_max" in filters:
                    thresh = filters["pb_ratio_max"]
                    if val <= thresh:
                        cell.fill, cell.font = green_fill, green_font
                    else:
                        cell.fill, cell.font = red_fill, red_font

                elif key == "dividend_yield_pct" and "dividend_yield_pct_min" in filters:
                    thresh = filters["dividend_yield_pct_min"]
                    if val >= thresh:
                        cell.fill, cell.font = green_fill, green_font
                    else:
                        cell.fill, cell.font = red_fill, red_font

                elif key == "dividend_payout" and "dividend_payout_max" in filters:
                    thresh = filters["dividend_payout_max"]
                    if val <= thresh:
                        cell.fill, cell.font = green_fill, green_font
                    else:
                        cell.fill, cell.font = red_fill, red_font

                elif key == "sales" and "sales_min" in filters:
                    thresh = filters["sales_min"]
                    if val >= thresh:
                        cell.fill, cell.font = green_fill, green_font
                    else:
                        cell.fill, cell.font = red_fill, red_font

        # Auto-adjust column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        ws.row_dimensions[1].height = 28

    wb.save(output_path)
    return output_path


if __name__ == "__main__":
    df_u = build_universe_dataframe()
    print(f"Loaded universe: {len(df_u)} companies.")
    res = get_all_preset_results(df_u)
    for p, sub in res.items():
        print(f"Preset '{p}': {len(sub)} matches (Valid: {5 <= len(sub) <= 50})")
    out = generate_screener_excel(df_universe=df_u)
    print(f"Generated screener Excel at: {out}")
