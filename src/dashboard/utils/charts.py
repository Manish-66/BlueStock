"""Plotly interactive chart builders for Nifty 100 Dashboard.

Sprint 4: Interactive Dashboard (Module 5).
Ensures all charts are responsive, readable, and styled with consistent themes.
"""

from typing import List, Optional
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


THEME_COLORS = {
    "primary": "#1F4E79",
    "secondary": "#2F5597",
    "accent": "#00A86B",
    "warning": "#E67E22",
    "danger": "#E74C3C",
    "neutral": "#7F8C8D",
    "background": "#F8F9FA"
}


def plot_sector_donut(df: pd.DataFrame) -> go.Figure:
    """Create interactive donut chart showing company counts and weights by sector."""
    sec_counts = df["broad_sector"].value_counts().reset_index()
    sec_counts.columns = ["Sector", "Companies"]

    fig = px.pie(
        sec_counts,
        values="Companies",
        names="Sector",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Prism,
        title="<b>Nifty 100 — Sector Diversification</b>"
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hoverinfo="label+value+percent",
        marker=dict(line=dict(color="#FFFFFF", width=2))
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        margin=dict(t=50, b=50, l=20, r=20),
        height=420
    )
    return fig


def plot_pl_history(df_pl: pd.DataFrame) -> go.Figure:
    """Plot 10-year Revenue and Net Profit historical bars and margin line."""
    df = df_pl[df_pl["year"] != "TTM"].copy()
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["year"],
        y=df["sales"],
        name="Revenue (Cr)",
        marker_color="#1F4E79"
    ))
    fig.add_trace(go.Bar(
        x=df["year"],
        y=df["net_profit"],
        name="Net Profit (Cr)",
        marker_color="#2ECC71"
    ))
    fig.add_trace(go.Scatter(
        x=df["year"],
        y=df["opm_percentage"],
        name="OPM (%)",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color="#E67E22", width=2.5)
    ))

    fig.update_layout(
        title="<b>Historical P&L Performance (Sales, Net Profit & OPM)</b>",
        barmode="group",
        yaxis=dict(title="₹ in Crore", showgrid=True),
        yaxis2=dict(title="OPM (%)", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=60, b=40, l=40, r=40),
        height=380
    )
    return fig


def plot_bs_history(df_bs: pd.DataFrame) -> go.Figure:
    """Plot Balance Sheet evolution (Total Assets vs Borrowings & Equity)."""
    df = df_bs.copy()
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["year"],
        y=df["total_assets"],
        name="Total Assets",
        marker_color="#3498DB"
    ))
    fig.add_trace(go.Bar(
        x=df["year"],
        y=df["borrowings"],
        name="Borrowings (Debt)",
        marker_color="#E74C3C"
    ))
    fig.add_trace(go.Bar(
        x=df["year"],
        y=df["equity_capital"] + df["reserves"],
        name="Net Worth (Equity + Reserves)",
        marker_color="#27AE60"
    ))

    fig.update_layout(
        title="<b>Balance Sheet Structure & Asset Growth</b>",
        barmode="group",
        yaxis=dict(title="₹ in Crore", showgrid=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=60, b=40, l=40, r=40),
        height=380
    )
    return fig


def plot_cf_history(df_cf: pd.DataFrame) -> go.Figure:
    """Plot Cash Flow breakdown: CFO, CFI, CFF, and Net Cash Flow."""
    df = df_cf.copy()
    fig = go.Figure()

    fig.add_trace(go.Bar(x=df["year"], y=df["operating_activity"], name="CFO (Ops)", marker_color="#2ECC71"))
    fig.add_trace(go.Bar(x=df["year"], y=df["investing_activity"], name="CFI (Investments/CapEx)", marker_color="#E67E22"))
    fig.add_trace(go.Bar(x=df["year"], y=df["financing_activity"], name="CFF (Financing)", marker_color="#9B59B6"))
    fig.add_trace(go.Scatter(x=df["year"], y=df["net_cash_flow"], name="Net Cash Flow", mode="lines+markers", line=dict(color="#1F4E79", width=2)))

    fig.update_layout(
        title="<b>Cash Flow Trajectory (CFO, CFI, CFF & Net)</b>",
        barmode="relative",
        yaxis=dict(title="₹ in Crore", showgrid=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=60, b=40, l=40, r=40),
        height=380
    )
    return fig


def plot_radar_comparison(
    ticker: str,
    company_scores: List[float],
    peer_scores: List[float],
    categories: List[str],
    peer_group_name: str
) -> go.Figure:
    """Generate 8-axis Plotly polar radar chart comparing company to peer benchmark."""
    fig = go.Figure()

    # Close the loop
    r_comp = company_scores + [company_scores[0]]
    r_peer = peer_scores + [peer_scores[0]]
    theta = categories + [categories[0]]

    fig.add_trace(go.Scatterpolar(
        r=r_comp,
        theta=theta,
        fill="toself",
        fillcolor="rgba(31, 119, 180, 0.35)",
        line=dict(color="#1F77B4", width=2.5),
        name=ticker
    ))

    fig.add_trace(go.Scatterpolar(
        r=r_peer,
        theta=theta,
        line=dict(color="#D62728", width=2, dash="dash"),
        name=f"Peer Avg ({peer_group_name})"
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="#E0E0E0"),
            angularaxis=dict(gridcolor="#E0E0E0")
        ),
        title=f"<b>{ticker} — 8-Axis Multi-Metric Peer Radar</b>",
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        margin=dict(t=50, b=50, l=40, r=40),
        height=450
    )
    return fig


def plot_trend_sparkline(df: pd.DataFrame, col_name: str, label: str, title: str) -> go.Figure:
    """Generate interactive trend line with YoY change annotations."""
    d = df[df["year"] != "TTM"].dropna(subset=[col_name]).copy()
    if len(d) == 0:
        return go.Figure()

    d["yoy_change"] = d[col_name].pct_change() * 100.0

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d["year"],
        y=d[col_name],
        mode="lines+markers+text",
        text=[f"{v:+.1f}%" if not np.isnan(v) else "" for v in d["yoy_change"]],
        textposition="top center",
        line=dict(color="#1F4E79", width=2.5),
        marker=dict(size=7, color="#2ECC71"),
        name=label
    ))

    fig.update_layout(
        title=f"<b>{title}</b>",
        xaxis=dict(title="Fiscal Year"),
        yaxis=dict(title=label, showgrid=True),
        margin=dict(t=50, b=40, l=40, r=40),
        height=380
    )
    return fig


def plot_sector_bubble(df: pd.DataFrame) -> go.Figure:
    """Create Sector bubble chart: Revenue vs. ROE, sized by Market Cap."""
    fig = px.scatter(
        df,
        x="sales",
        y="return_on_equity_pct",
        size="market_cap_crore",
        color="broad_sector",
        hover_name="company_id",
        hover_data={"company_name": True, "sales": ":,.0f", "return_on_equity_pct": ":.2f", "market_cap_crore": ":,.0f"},
        size_max=55,
        title="<b>Sector Landscape: Revenue vs. ROE (Bubble Size = Market Cap)</b>",
        labels={"sales": "Revenue (₹ Cr)", "return_on_equity_pct": "Return on Equity (ROE %)"}
    )
    fig.update_layout(
        xaxis=dict(type="log", title="Revenue ₹ Cr (Log Scale)", showgrid=True),
        yaxis=dict(title="ROE (%)", range=[-10, 80], showgrid=True),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        margin=dict(t=50, b=70, l=40, r=40),
        height=520
    )
    return fig


def plot_capital_allocation_treemap(df: pd.DataFrame) -> go.Figure:
    """Create interactive treemap of all 92 companies by capital allocation pattern."""
    fig = px.treemap(
        df,
        path=["pattern_label", "broad_sector", "company_id"],
        values="market_cap_crore",
        color="pattern_label",
        color_discrete_sequence=px.colors.qualitative.Safe,
        title="<b>Capital Allocation Treemap (Grouped by CFO/CFI/CFF Pattern)</b>",
        hover_data={"company_name": True, "market_cap_crore": ":,.0f"}
    )
    fig.update_layout(margin=dict(t=50, b=20, l=20, r=20), height=540)
    return fig


def plot_pb_roe_scatter(df: pd.DataFrame) -> go.Figure:
    """Generate P/B vs ROE valuation scatter plot with sector color coding."""
    fig = px.scatter(
        df,
        x="pb_ratio",
        y="return_on_equity_pct",
        size="market_cap_crore",
        color="broad_sector",
        hover_name="company_id",
        hover_data={"company_name": True, "pb_ratio": ":.2f", "return_on_equity_pct": ":.2f", "pe_ratio": ":.1f"},
        size_max=50,
        title="<b>Valuation Map: Price-to-Book (P/B) vs. Return on Equity (ROE)</b>",
        labels={"pb_ratio": "Price-to-Book (P/B)", "return_on_equity_pct": "ROE (%)"}
    )
    fig.update_layout(
        xaxis=dict(title="P/B Multiple", range=[0, 20], showgrid=True),
        yaxis=dict(title="ROE (%)", range=[-10, 70], showgrid=True),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        margin=dict(t=50, b=70, l=40, r=40),
        height=520
    )
    return fig
