"""Valuation and Market Data Analytics Module for Nifty 100 Platform.

Sprint 4: Valuation & Market Data (Module 6).
Computes historical 5-year median multiples, sector medians, FCF yield,
dividend yield rankings, EV/EBITDA comp flags, and overvaluation badges.
Exports:
  - output/valuation_summary.xlsx
  - output/valuation_flags.csv
"""

import os
import sqlite3
from typing import Dict, Optional, Tuple
import numpy as np
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
import pandas as pd

from src.etl.loader import DB_PATH


OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output")
VALUATION_EXCEL_PATH = os.path.join(OUTPUT_DIR, "valuation_summary.xlsx")
VALUATION_FLAGS_PATH = os.path.join(OUTPUT_DIR, "valuation_flags.csv")


def compute_valuation_metrics(db_path: str = DB_PATH) -> pd.DataFrame:
    """Compute comprehensive valuation KPIs and badges for all 92 companies."""
    with sqlite3.connect(db_path) as conn:
        df_mc = pd.read_sql_query("SELECT * FROM market_cap", conn)
        df_comp = pd.read_sql_query("SELECT id AS company_id, company_name, roe_percentage, book_value FROM companies", conn)
        df_sec = pd.read_sql_query("SELECT company_id, broad_sector, sub_sector FROM sectors", conn)
        df_fr = pd.read_sql_query("SELECT company_id, year, free_cash_flow_cr, return_on_equity_pct FROM financial_ratios", conn)

    # Standardize IDs
    for d in [df_mc, df_comp, df_sec, df_fr]:
        d["company_id"] = d["company_id"].astype(str).str.strip().str.upper()

    # 5-year median multiples per company
    hist_medians = df_mc.groupby("company_id").agg({
        "pe_ratio": "median",
        "pb_ratio": "median",
        "ev_ebitda": "median",
        "dividend_yield_pct": "median"
    }).rename(columns={
        "pe_ratio": "pe_ratio_5yr_median",
        "pb_ratio": "pb_ratio_5yr_median",
        "ev_ebitda": "ev_ebitda_5yr_median",
        "dividend_yield_pct": "dividend_yield_5yr_median"
    }).reset_index()

    # Latest market cap records (2024-03)
    latest_mc = df_mc.sort_values("year").groupby("company_id").last().reset_index()

    # Latest financial ratios
    latest_fr = df_fr.sort_values("year").groupby("company_id").last().reset_index()

    # Merge dataset
    val = latest_mc.merge(hist_medians, on="company_id", how="left")
    val = val.merge(df_comp, on="company_id", how="left")
    val = val.merge(df_sec, on="company_id", how="left")
    val = val.merge(latest_fr[["company_id", "free_cash_flow_cr", "return_on_equity_pct"]], on="company_id", how="left")

    val["return_on_equity_pct"] = val["return_on_equity_pct"].fillna(val["roe_percentage"])

    # 6.5 FCF Yield Calculator: FCF / Market_Cap * 100
    val["fcf_yield_pct"] = np.where(
        val["market_cap_crore"] > 0,
        (val["free_cash_flow_cr"] / val["market_cap_crore"]) * 100.0,
        np.nan
    )

    # Sector medians
    sec_pe = val.groupby("broad_sector")["pe_ratio"].transform("median")
    sec_ev = val.groupby("broad_sector")["ev_ebitda"].transform("median")

    val["sector_median_pe"] = sec_pe.round(2)
    val["sector_median_ev_ebitda"] = sec_ev.round(2)

    # 6.3 EV/EBITDA Comp Table: Flag if >20% above sector median
    val["ev_ebitda_premium_pct"] = np.where(
        val["sector_median_ev_ebitda"] > 0,
        ((val["ev_ebitda"] - val["sector_median_ev_ebitda"]) / val["sector_median_ev_ebitda"]) * 100.0,
        0.0
    ).round(2)
    val["ev_ebitda_high_flag"] = val["ev_ebitda_premium_pct"] > 20.0

    # 6.4 Dividend Yield & FCF Yield Rankers
    val["dividend_yield_rank"] = val["dividend_yield_pct"].rank(ascending=False, method="min").astype(int)
    val["fcf_yield_rank"] = val["fcf_yield_pct"].rank(ascending=False, method="min").fillna(92).astype(int)

    # 6.6 Overvaluation Flags:
    # Caution if P/E > (sector_median * 1.5)
    # Discount if P/E < (sector_median * 0.7)
    # Fair otherwise
    def assign_badge(row) -> Tuple[str, str]:
        pe = row["pe_ratio"]
        med = row["sector_median_pe"]
        sec = row["broad_sector"]
        if pd.isna(pe) or pd.isna(med) or med <= 0:
            return "Neutral", "Insufficient data"
        if pe > med * 1.5:
            return "Caution", f"P/E ({pe:.1f}x) > 1.5x of {sec} median ({med:.1f}x) - Overvalued premium"
        elif pe < med * 0.7:
            return "Discount", f"P/E ({pe:.1f}x) < 0.7x of {sec} median ({med:.1f}x) - Value discount"
        return "Fair", f"P/E ({pe:.1f}x) within fair range of {sec} median ({med:.1f}x)"

    badge_data = val.apply(assign_badge, axis=1)
    val["valuation_badge"] = [b[0] for b in badge_data]
    val["valuation_rationale"] = [b[1] for b in badge_data]

    return val.sort_values(by="market_cap_crore", ascending=False).reset_index(drop=True)


def generate_valuation_reports(
    excel_path: str = VALUATION_EXCEL_PATH,
    csv_path: str = VALUATION_FLAGS_PATH,
    db_path: str = DB_PATH
) -> Tuple[str, str]:
    """Generate both valuation_summary.xlsx and valuation_flags.csv."""
    os.makedirs(os.path.dirname(excel_path), exist_ok=True)
    df_val = compute_valuation_metrics(db_path)

    # 1. Export valuation_flags.csv (Caution and Discount companies)
    flagged = df_val[df_val["valuation_badge"].isin(["Caution", "Discount"])][[
        "company_id", "company_name", "broad_sector", "pe_ratio",
        "pe_ratio_5yr_median", "sector_median_pe", "valuation_badge", "valuation_rationale"
    ]].sort_values(by=["valuation_badge", "pe_ratio"], ascending=[True, False])

    flagged.to_csv(csv_path, index=False, encoding="utf-8")

    # 2. Export valuation_summary.xlsx
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Valuation Summary"

    # Styling definitions
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")

    caution_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    caution_font = Font(name="Calibri", size=10, bold=True, color="9C0006")

    discount_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    discount_font = Font(name="Calibri", size=10, bold=True, color="006100")

    fair_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    fair_font = Font(name="Calibri", size=10, color="595959")

    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9")
    )
    default_font = Font(name="Calibri", size=10)

    columns = [
        ("company_id", "Ticker"),
        ("company_name", "Company Name"),
        ("broad_sector", "Sector"),
        ("market_cap_crore", "Market Cap (Cr)"),
        ("pe_ratio", "P/E"),
        ("pe_ratio_5yr_median", "5Y Med P/E"),
        ("sector_median_pe", "Sector P/E"),
        ("valuation_badge", "Valuation Badge"),
        ("pb_ratio", "P/B"),
        ("pb_ratio_5yr_median", "5Y Med P/B"),
        ("ev_ebitda", "EV/EBITDA"),
        ("ev_ebitda_5yr_median", "5Y Med EV/EBITDA"),
        ("sector_median_ev_ebitda", "Sector EV/EBITDA"),
        ("ev_ebitda_premium_pct", "EV Prem vs Sec (%)"),
        ("dividend_yield_pct", "Div Yield (%)"),
        ("dividend_yield_rank", "Div Rank"),
        ("free_cash_flow_cr", "FCF (Cr)"),
        ("fcf_yield_pct", "FCF Yield (%)"),
        ("fcf_yield_rank", "FCF Rank"),
        ("return_on_equity_pct", "ROE (%)")
    ]

    # Write headers
    headers = [col[1] for col in columns]
    ws.append(headers)
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Write data rows
    for r_idx, (_, row) in enumerate(df_val.iterrows(), start=2):
        for c_idx, (col_key, _) in enumerate(columns, start=1):
            val = row.get(col_key, np.nan)
            cell = ws.cell(row=r_idx, column=c_idx)
            cell.border = thin_border
            cell.font = default_font

            if pd.isna(val):
                cell.value = "—"
                cell.alignment = Alignment(horizontal="center")
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

            # Style Valuation Badge
            if col_key == "valuation_badge":
                if val == "Caution":
                    cell.fill, cell.font = caution_fill, caution_font
                elif val == "Discount":
                    cell.fill, cell.font = discount_fill, discount_font
                else:
                    cell.fill, cell.font = fair_fill, fair_font
                cell.alignment = Alignment(horizontal="center")

            # Highlight EV/EBITDA if high
            if col_key == "ev_ebitda_premium_pct" and isinstance(val, (int, float)) and val > 20.0:
                cell.font = Font(name="Calibri", size=10, bold=True, color="9C0006")

    # Column widths
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max(len(str(c.value or "")) for c in col[:20])
        ws.column_dimensions[col_letter].width = max(max_len + 3, 11)

    ws.row_dimensions[1].height = 28
    wb.save(excel_path)

    return excel_path, csv_path


if __name__ == "__main__":
    xl_out, csv_out = generate_valuation_reports()
    print(f"Generated valuation summary at: {xl_out}")
    print(f"Generated valuation flags at: {csv_out}")
