"""Peer Comparison Engine and Percentile Ranking for Nifty 100 Platform.

Sprint 3: Screener & Peer Comparison Engine (Days 18-20).
Computes intra-group percentile rankings for 11 peer groups, populates the
SQLite peer_percentiles table, generates 8-axis radar charts (reports/radar_charts/),
and exports peer_comparison.xlsx with 11 sheets and conditional formatting.
"""

import os
import sqlite3
from typing import Dict, List, Optional, Tuple, Union
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
import pandas as pd

from src.etl.loader import DB_PATH
from src.screener.engine import build_universe_dataframe


PEER_METRICS_CORE = [
    ("return_on_equity_pct", "ROE", False),
    ("roce_pct", "ROCE", False),
    ("net_profit_margin_pct", "Net Profit Margin", False),
    ("debt_to_equity", "D/E", True),  # Inverted: lower is better
    ("free_cash_flow_cr", "Free Cash Flow", False),
    ("pat_cagr_5yr", "PAT CAGR 5yr", False),
    ("revenue_cagr_5yr", "Revenue CAGR 5yr", False),
    ("eps_cagr_5yr", "EPS CAGR 5yr", False),
    ("interest_coverage", "Interest Coverage", False),
    ("asset_turnover", "Asset Turnover", False),
]

PEER_METRICS_ALL = [
    ("sales", "Revenue (Cr)", False),
    ("net_profit", "Net Profit (Cr)", False),
    ("market_cap_crore", "Market Cap (Cr)", False),
    ("operating_profit_margin_pct", "OPM (%)", False),
    ("net_profit_margin_pct", "NPM (%)", False),
    ("return_on_equity_pct", "ROE (%)", False),
    ("roce_pct", "ROCE (%)", False),
    ("debt_to_equity", "D/E", True),
    ("interest_coverage", "ICR", False),
    ("free_cash_flow_cr", "FCF (Cr)", False),
    ("cfo_pat_ratio", "CFO/PAT", False),
    ("asset_turnover", "Asset Turnover", False),
    ("pe_ratio", "P/E", True),
    ("pb_ratio", "P/B", True),
    ("ev_ebitda", "EV/EBITDA", True),
    ("dividend_yield_pct", "Div Yield (%)", False),
    ("dividend_payout", "Div Payout (%)", False),
    ("revenue_cagr_5yr", "Rev CAGR 5yr (%)", False),
    ("pat_cagr_5yr", "PAT CAGR 5yr (%)", False),
    ("eps_cagr_5yr", "EPS CAGR 5yr (%)", False),
]

RADAR_AXES = [
    ("return_on_equity_pct", "ROE"),
    ("roce_pct", "ROCE"),
    ("net_profit_margin_pct", "NPM"),
    ("debt_to_equity", "D/E (Inv)"),
    ("free_cash_flow_cr", "FCF Score"),
    ("pat_cagr_5yr", "PAT CAGR 5yr"),
    ("revenue_cagr_5yr", "Rev CAGR 5yr"),
    ("composite_quality_score", "Composite Score")
]


def compute_percent_rank(series: pd.Series, invert: bool = False) -> pd.Series:
    """Compute PERCENT_RANK (0.0 to 1.0) with support for inverted ranking."""
    s = series.astype(float).copy()
    valid = s.dropna()
    n = len(valid)
    if n <= 1:
        ranks = pd.Series(1.0 if not invert else 1.0, index=s.index)
        return ranks.where(s.notna(), np.nan)

    # rank(method='min') 1 to N
    rk = valid.rank(method="min", ascending=True)
    pct_rank = (rk - 1.0) / (n - 1.0)

    if invert:
        pct_rank = 1.0 - pct_rank

    out = pd.Series(index=s.index, dtype=float)
    out.loc[valid.index] = pct_rank
    return out


def load_peer_groups_data(db_path: str = DB_PATH) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load peer groups mapping and merge with the 92-company analytical universe."""
    df_u = build_universe_dataframe(db_path)

    with sqlite3.connect(db_path) as conn:
        df_pg = pd.read_sql_query("SELECT * FROM peer_groups", conn)

    df_pg["company_id"] = df_pg["company_id"].astype(str).str.strip().str.upper()
    merged = df_pg.merge(df_u, on="company_id", how="left")
    return df_pg, merged


def calculate_peer_percentiles(db_path: str = DB_PATH) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Compute PERCENT_RANK for 10 core metrics (and all 20 KPIs) across all 11 peer groups."""
    df_pg, df_merged = load_peer_groups_data(db_path)
    percentile_records = []
    enriched_peer_dfs = []

    for group_name, group_df in df_merged.groupby("peer_group_name"):
        grp = group_df.copy()

        # Compute percentile ranks for all 20 metrics
        for col_name, display_name, invert in PEER_METRICS_ALL:
            pct_col = f"{col_name}_pctile"
            grp[pct_col] = compute_percent_rank(grp[col_name], invert=invert)

        enriched_peer_dfs.append(grp)

        # Populate records for the 10 core peer metrics to persist into SQLite
        for col_name, metric_label, invert in PEER_METRICS_CORE:
            for _, row in grp.iterrows():
                cid = row["company_id"]
                val = row.get(col_name, np.nan)
                pct_val = row.get(f"{col_name}_pctile", np.nan)
                percentile_records.append({
                    "company_id": cid,
                    "peer_group_name": group_name,
                    "metric": col_name,
                    "value": None if pd.isna(val) else float(val),
                    "percentile_rank": None if pd.isna(pct_val) else round(float(pct_val), 4),
                    "year": "2024"
                })

    df_peer_percentiles = pd.DataFrame(percentile_records)
    df_all_peers_enriched = pd.concat(enriched_peer_dfs, ignore_index=True)

    # Populate SQLite table peer_percentiles
    with sqlite3.connect(db_path) as conn:
        df_peer_percentiles.to_sql("peer_percentiles", conn, if_exists="replace", index=False)

    return df_peer_percentiles, df_all_peers_enriched


def get_company_peer_percentiles(company_id: str, db_path: str = DB_PATH) -> Union[pd.DataFrame, str]:
    """Retrieve peer percentiles for a company. Returns 'No peer group assigned' if ungrouped."""
    cid = company_id.strip().upper()
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(
            "SELECT * FROM peer_percentiles WHERE company_id = ?",
            conn,
            params=(cid,)
        )

    if len(df) == 0:
        return "No peer group assigned"
    return df


def generate_peer_comparison_excel(
    output_path: str = os.path.join("output", "peer_comparison.xlsx"),
    db_path: str = DB_PATH
) -> str:
    """Generate peer_comparison.xlsx with exactly 11 sheets, colour coding, benchmark highlight, and median row."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    _, df_peers_enriched = calculate_peer_percentiles(db_path)

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    sub_header_fill = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")

    benchmark_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")  # Gold/amber
    median_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")     # Soft blue-grey
    median_font = Font(name="Calibri", size=10, bold=True)

    green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    green_font = Font(name="Calibri", size=10, color="006100")
    yellow_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    yellow_font = Font(name="Calibri", size=10, color="9C6500")
    red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    red_font = Font(name="Calibri", size=10, color="9C0006")
    default_font = Font(name="Calibri", size=10)

    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9")
    )

    peer_groups = sorted(df_peers_enriched["peer_group_name"].unique())

    for group_name in peer_groups:
        grp = df_peers_enriched[df_peers_enriched["peer_group_name"] == group_name].copy()
        # Sort so benchmark company is at top, followed by other peers
        grp = grp.sort_values(by=["is_benchmark", "company_name"], ascending=[False, True])

        ws = wb.create_sheet(title=group_name[:31])

        # Build column definitions: Company Info + 20 pairs of (Metric Value, Percentile Rank)
        headers = ["Ticker", "Company Name", "Benchmark?"]
        for _, display_name, _ in PEER_METRICS_ALL:
            headers.append(display_name)
            headers.append(f"{display_name} Rank")

        ws.append(headers)
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill if col_idx <= 3 else sub_header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Write company rows
        for r_idx, (_, row) in enumerate(grp.iterrows(), start=2):
            is_bench = bool(row.get("is_benchmark", 0) == 1)

            # Metadata cells
            ws.cell(row=r_idx, column=1, value=row["company_id"]).alignment = Alignment(horizontal="center")
            ws.cell(row=r_idx, column=2, value=row["company_name"]).alignment = Alignment(horizontal="left")
            ws.cell(row=r_idx, column=3, value="★ Benchmark" if is_bench else "").alignment = Alignment(horizontal="center")

            curr_col = 4
            for col_name, _, _ in PEER_METRICS_ALL:
                val = row.get(col_name, np.nan)
                pct = row.get(f"{col_name}_pctile", np.nan)

                # Metric Value Cell
                v_cell = ws.cell(row=r_idx, column=curr_col)
                v_cell.border = thin_border
                v_cell.font = default_font
                if pd.isna(val):
                    v_cell.value = "—"
                    v_cell.alignment = Alignment(horizontal="center")
                elif np.isinf(val):
                    v_cell.value = "Debt Free"
                    v_cell.alignment = Alignment(horizontal="center")
                else:
                    v_cell.value = round(float(val), 2)
                    v_cell.alignment = Alignment(horizontal="right")
                    v_cell.number_format = "#,##0.00"

                # Percentile Rank Cell
                p_cell = ws.cell(row=r_idx, column=curr_col + 1)
                p_cell.border = thin_border
                if pd.isna(pct):
                    p_cell.value = "—"
                    p_cell.alignment = Alignment(horizontal="center")
                else:
                    pct_float = float(pct)
                    p_cell.value = round(pct_float * 100.0, 1)
                    p_cell.alignment = Alignment(horizontal="right")
                    p_cell.number_format = "0.0\"%\""

                    # Conditional Colour Coding:
                    # Green >= 75th, Yellow 25th-75th, Red <= 25th
                    if pct_float >= 0.75:
                        p_cell.fill, p_cell.font = green_fill, green_font
                    elif pct_float >= 0.25:
                        p_cell.fill, p_cell.font = yellow_fill, yellow_font
                    else:
                        p_cell.fill, p_cell.font = red_fill, red_font

                curr_col += 2

            # If benchmark company, highlight background of info cells with gold/amber
            if is_bench:
                for c in range(1, 4):
                    ws.cell(row=r_idx, column=c).fill = benchmark_fill
                    ws.cell(row=r_idx, column=c).font = Font(name="Calibri", size=10, bold=True)

        # Median Summary Row at bottom
        summary_row_idx = len(grp) + 2
        ws.cell(row=summary_row_idx, column=1, value="MEDIAN").alignment = Alignment(horizontal="center")
        ws.cell(row=summary_row_idx, column=2, value="Peer Group Median").alignment = Alignment(horizontal="left")
        ws.cell(row=summary_row_idx, column=3, value="").alignment = Alignment(horizontal="center")

        curr_col = 4
        for col_name, _, _ in PEER_METRICS_ALL:
            series = grp[col_name].replace([np.inf, -np.inf], np.nan).dropna()
            med_val = series.median() if len(series) > 0 else np.nan

            m_cell = ws.cell(row=summary_row_idx, column=curr_col)
            m_cell.font = median_font
            m_cell.fill = median_fill
            m_cell.border = thin_border
            if pd.isna(med_val):
                m_cell.value = "—"
            else:
                m_cell.value = round(float(med_val), 2)
                m_cell.number_format = "#,##0.00"
            m_cell.alignment = Alignment(horizontal="right")

            # Blank percentile for median
            mp_cell = ws.cell(row=summary_row_idx, column=curr_col + 1, value="—")
            mp_cell.font = median_font
            mp_cell.fill = median_fill
            mp_cell.border = thin_border
            mp_cell.alignment = Alignment(horizontal="center")

            curr_col += 2

        # Style median label row
        for c in range(1, 4):
            c_cell = ws.cell(row=summary_row_idx, column=c)
            c_cell.font = median_font
            c_cell.fill = median_fill
            c_cell.border = thin_border

        # Adjust column widths
        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            max_len = max(len(str(cell.value or "")) for cell in col[:15])
            ws.column_dimensions[col_letter].width = max(max_len + 3, 11)

        ws.row_dimensions[1].height = 28

    wb.save(output_path)
    return output_path


def _normalize_radar_val(metric: str, val: float, p10: float, p90: float) -> float:
    """Normalize raw metric value to 0-100 radar coordinate."""
    if pd.isna(val):
        return 50.0
    if metric == "debt_to_equity":
        if val <= 0.05:
            return 100.0
        if val <= 1.0:
            return 100.0 - val * 30.0
        if val <= 3.0:
            return max(10.0, 70.0 - (val - 1.0) * 25.0)
        return 10.0
    if metric == "composite_quality_score":
        return float(np.clip(val, 0.0, 100.0))

    if np.isclose(p90, p10):
        return 50.0
    scaled = (np.clip(val, p10, p90) - p10) / (p90 - p10) * 100.0
    return float(np.clip(scaled, 5.0, 100.0))


def generate_all_radar_charts(
    output_dir: str = os.path.join("reports", "radar_charts"),
    db_path: str = DB_PATH
) -> int:
    """Generate 8-axis radar PNG charts for all 92 companies with peer group or Nifty 100 overlay."""
    os.makedirs(output_dir, exist_ok=True)
    df_u = build_universe_dataframe(db_path)

    with sqlite3.connect(db_path) as conn:
        df_pg = pd.read_sql_query("SELECT * FROM peer_groups", conn)

    df_pg["company_id"] = df_pg["company_id"].astype(str).str.strip().str.upper()
    peer_dict = dict(zip(df_pg["company_id"], df_pg["peer_group_name"]))

    # Precalculate global P10, P90, and means for each axis
    axis_keys = [k for k, _ in RADAR_AXES]
    axis_labels = [lbl for _, lbl in RADAR_AXES]
    num_axes = len(axis_keys)

    p10_dict = {}
    p90_dict = {}
    nifty_mean_dict = {}

    for k in axis_keys:
        s = df_u[k].replace([np.inf, -np.inf], np.nan).dropna()
        p10_dict[k] = np.percentile(s, 10) if len(s) > 0 else 0.0
        p90_dict[k] = np.percentile(s, 90) if len(s) > 0 else 100.0
        nifty_mean_dict[k] = s.mean() if len(s) > 0 else 50.0

    # Peer group average radar values
    group_means: Dict[str, List[float]] = {}
    for grp_name, sub in df_pg.groupby("peer_group_name"):
        tickers = sub["company_id"].unique()
        grp_universe = df_u[df_u["company_id"].isin(tickers)]
        scores = []
        for k in axis_keys:
            vals = grp_universe[k].replace([np.inf, -np.inf], np.nan).dropna()
            mean_v = vals.mean() if len(vals) > 0 else nifty_mean_dict[k]
            scores.append(_normalize_radar_val(k, mean_v, p10_dict[k], p90_dict[k]))
        group_means[grp_name] = scores

    # Angles for 8 axes
    angles = np.linspace(0, 2 * np.pi, num_axes, endpoint=False).tolist()
    angles += angles[:1]  # Complete circle

    # Nifty 100 baseline scores
    nifty_scores = [
        _normalize_radar_val(k, nifty_mean_dict[k], p10_dict[k], p90_dict[k])
        for k in axis_keys
    ]
    nifty_scores += nifty_scores[:1]

    generated_count = 0

    for _, row in df_u.iterrows():
        ticker = row["company_id"]
        c_name = row["company_name"]
        grp_name = peer_dict.get(ticker)

        # Company scores
        c_scores = [
            _normalize_radar_val(k, row.get(k, np.nan), p10_dict[k], p90_dict[k])
            for k in axis_keys
        ]
        c_scores += c_scores[:1]

        fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))

        # Rotate so first axis is at top
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)

        # Set axis labels with padding
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(axis_labels, size=9, weight="bold", color="#333333")
        ax.set_ylim(0, 100)
        ax.set_yticks([25, 50, 75, 100])
        ax.set_yticklabels(["25", "50", "75", "100"], size=7, color="#777777")
        ax.grid(color="#E0E0E0", linestyle="solid", linewidth=0.7)

        # Plot Company Polygon
        ax.plot(angles, c_scores, color="#1F77B4", linewidth=2.2, label=f"{ticker} ({c_name[:20]})")
        ax.fill(angles, c_scores, color="#1F77B4", alpha=0.30)

        # Plot Benchmark Overlay
        if grp_name and grp_name in group_means:
            b_scores = group_means[grp_name] + [group_means[grp_name][0]]
            ax.plot(angles, b_scores, color="#D62728", linewidth=1.8, linestyle="dashed", label=f"Peer Avg: {grp_name}")
        else:
            ax.plot(angles, nifty_scores, color="#7F7F7F", linewidth=1.5, linestyle="dashed", label="Nifty 100 Average")

        ax.legend(loc="upper right", bbox_to_anchor=(1.30, 1.12), fontsize=8, frameon=True)
        title = f"{ticker} — Financial Health & Peer Radar"
        if grp_name:
            subtitle = f"Peer Group: {grp_name} | Composite Score: {row.get('composite_quality_score', '—')}"
        else:
            subtitle = f"Standalone (No peer group) | Composite Score: {row.get('composite_quality_score', '—')}"

        plt.title(f"{title}\n{subtitle}", size=11, weight="bold", pad=25, color="#111111")
        plt.tight_layout()

        out_file = os.path.join(output_dir, f"{ticker}_radar.png")
        plt.savefig(out_file, dpi=120, bbox_inches="tight")
        plt.close(fig)
        generated_count += 1

    return generated_count


if __name__ == "__main__":
    df_pct, df_all = calculate_peer_percentiles()
    print(f"Calculated peer percentiles: {len(df_pct)} records in SQLite peer_percentiles.")
    excel_path = generate_peer_comparison_excel()
    print(f"Generated peer comparison Excel at: {excel_path}")
    count_radar = generate_all_radar_charts()
    print(f"Generated {count_radar} radar charts in reports/radar_charts/.")
