"""
eda_analysis.py
===============
Day 3: Comprehensive Exploratory Data Analysis (EDA) Pipeline
Generates all 15 publication-quality charts required by the capstone specification:
 1. NAV trend analysis for 40 schemes (COVID recovery, 2023 rally, 2024 corrections)
 2. AUM growth grouped bar chart by AMC (2022-2025, highlighting SBI's 12.5L Cr dominance)
 3. Monthly SIP inflow time series (2022-2025, highlighting Rs. 31,002 Cr Dec 2025 milestone)
 4. Category-wise net inflow heatmap
 5. Investor demographics: Age group distribution pie chart
 6. SIP investment amount box plot by age group
 7. Geographic distribution: SIP investment amount by State
 8. Geographic segmentation: T30 vs B30 transaction volume pie chart
 9. Industry mutual fund folio count growth (13.26 to 26.12 crore)
 10. Pairwise return correlation matrix across 10 selected funds
 11. Top equity portfolio holdings sector distribution (Donut chart)
 12. Expense ratio vs 3-Year CAGR return scatter plot
 13. Risk vs Return scatter plot (Std Dev vs 3-Year Return with Sharpe sizing)
 14. Transaction payment mode distribution
 15. KYC status breakdown by city tier
"""

import os
import logging
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Set style
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#cccccc"
plt.rcParams["axes.linewidth"] = 0.8

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "db", "bluestock_mf.db")
FIG_DIR = os.path.join(BASE_DIR, "reports", "figures")
os.makedirs(FIG_DIR, exist_ok=True)


def get_db_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def chart_01_nav_trends(conn: sqlite3.Connection):
    """1. NAV trend analysis for all 40 schemes 2022-2026."""
    logger.info("Generating Chart 01: NAV Trends...")
    query = """
    SELECT n.date, n.amfi_code, f.scheme_name, f.sub_category, n.nav
    FROM fact_nav n
    JOIN dim_fund f ON n.amfi_code = f.amfi_code
    ORDER BY n.date ASC
    """
    df = pd.read_sql(query, conn)
    df["date"] = pd.to_datetime(df["date"])
    
    # Normalize NAV to base 100 for visual comparison
    df["nav_normalized"] = df.groupby("amfi_code")["nav"].transform(lambda x: (x / x.iloc[0]) * 100)
    
    fig, ax = plt.subplots(figsize=(14, 7), dpi=300)
    
    # Plot faint lines for all schemes
    for code, group in df.groupby("amfi_code"):
        ax.plot(group["date"], group["nav_normalized"], color="#cbd5e1", alpha=0.35, linewidth=0.8)
        
    # Highlight 5 key funds
    key_codes = {
        119551: ("SBI Bluechip", "#2563eb"),
        118634: ("Nippon Small Cap", "#dc2626"),
        120842: ("Kotak Emerging Equity", "#16a34a"),
        148568: ("Mirae Asset Large & Midcap", "#9333ea"),
        120844: ("Kotak Liquid Fund", "#f59e0b")
    }
    
    for code, (label, color) in key_codes.items():
        subset = df[df["amfi_code"] == code]
        if not subset.empty:
            ax.plot(subset["date"], subset["nav_normalized"], label=label, color=color, linewidth=2.2)
            
    ax.set_title("Historical NAV Growth Trajectory (Normalized to Base 100, 2022 - 2026)", fontsize=14, weight="bold", pad=15)
    ax.set_xlabel("Date", fontsize=11, labelpad=10)
    ax.set_ylabel("Normalized NAV (Base = 100)", fontsize=11, labelpad=10)
    ax.legend(frameon=True, facecolor="white", edgecolor="#e2e8f0", loc="upper left")
    
    # Milestones
    ax.axvline(pd.to_datetime("2023-01-01"), color="#64748b", linestyle="--", alpha=0.6)
    ax.text(pd.to_datetime("2023-01-15"), 220, "2023 Equity Rally Begins", fontsize=9, color="#475569", weight="bold")
    
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "01_nav_trends_growth.png"))
    plt.close()


def chart_02_aum_by_amc(conn: sqlite3.Connection):
    """2. AUM growth grouped bar chart by AMC (2022-2025)."""
    logger.info("Generating Chart 02: AUM Growth by AMC...")
    df = pd.read_sql("SELECT date, fund_house, aum_crore, aum_lakh_crore FROM fact_aum", conn)
    df["year"] = pd.to_datetime(df["date"]).dt.year
    
    # Filter years 2022 to 2025
    annual_aum = df.groupby(["fund_house", "year"])["aum_lakh_crore"].last().reset_index()
    top_houses = df.groupby("fund_house")["aum_crore"].max().nlargest(8).index
    annual_aum = annual_aum[annual_aum["fund_house"].isin(top_houses)]
    
    fig, ax = plt.subplots(figsize=(14, 7), dpi=300)
    sns.barplot(data=annual_aum, x="fund_house", y="aum_lakh_crore", hue="year", palette="Blues", ax=ax)
    
    ax.set_title("AUM Growth by Top Fund Houses (2022 - 2025 in Rs. Lakh Crore)", fontsize=14, weight="bold", pad=15)
    ax.set_xlabel("Fund House (AMC)", fontsize=11, labelpad=10)
    ax.set_ylabel("AUM (Rs. Lakh Crore)", fontsize=11, labelpad=10)
    plt.xticks(rotation=25, ha="right")
    ax.legend(title="Calendar Year", frameon=True, facecolor="white")
    
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "02_aum_growth_by_amc.png"))
    plt.close()


def chart_03_sip_inflows(conn: sqlite3.Connection):
    """3. Monthly SIP inflow time series (Rs. 31,002 Cr milestone)."""
    logger.info("Generating Chart 03: Monthly SIP Inflows...")
    df = pd.read_sql("SELECT month, sip_inflow_crore FROM fact_sip_inflows ORDER BY month ASC", conn)
    
    fig, ax = plt.subplots(figsize=(13, 6), dpi=300)
    ax.plot(df["month"], df["sip_inflow_crore"], marker="o", color="#2563eb", linewidth=2.5, markersize=4)
    ax.fill_between(df["month"], df["sip_inflow_crore"], alpha=0.15, color="#3b82f6")
    
    # Highlight all-time high milestone
    max_row = df.loc[df["sip_inflow_crore"].idxmax()]
    ax.scatter([max_row["month"]], [max_row["sip_inflow_crore"]], color="#ef4444", s=100, zorder=5)
    ax.annotate(
        f"All-time High: Rs. {int(max_row['sip_inflow_crore']):,} Cr\n(Dec 2025)",
        xy=(max_row["month"], max_row["sip_inflow_crore"]),
        xytext=(-80, -45),
        textcoords="offset points",
        arrowprops=dict(arrowstyle="->", color="#ef4444", lw=1.5),
        fontsize=10, weight="bold", color="#b91c1c"
    )
    
    ax.set_title("Monthly SIP Inflow Trajectory in India (2022 - 2025)", fontsize=14, weight="bold", pad=15)
    ax.set_xlabel("Month", fontsize=11, labelpad=10)
    ax.set_ylabel("SIP Inflow (Rs. Crore)", fontsize=11, labelpad=10)
    plt.xticks(rotation=45, ha="right", ticks=range(0, len(df), 3), labels=df["month"].iloc[::3])
    
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "03_monthly_sip_inflow_trend.png"))
    plt.close()


def chart_04_category_inflow_heatmap(conn: sqlite3.Connection):
    """4. Category-wise net inflow heatmap."""
    logger.info("Generating Chart 04: Category Inflows Heatmap...")
    df = pd.read_sql("SELECT month, category, net_inflow_crore FROM fact_category_inflows", conn)
    pivot_df = df.pivot(index="category", columns="month", values="net_inflow_crore")
    
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
    sns.heatmap(pivot_df, cmap="crest", annot=False, fmt=".0f", linewidths=0.5, cbar_kws={'label': 'Net Inflow (Rs. Crore)'}, ax=ax)
    
    ax.set_title("Net Inflow by Mutual Fund Category (Heatmap)", fontsize=14, weight="bold", pad=15)
    ax.set_xlabel("Month", fontsize=11, labelpad=10)
    ax.set_ylabel("Fund Category", fontsize=11, labelpad=10)
    plt.xticks(rotation=45, ha="right")
    
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "04_category_inflow_heatmap.png"))
    plt.close()


def chart_05_06_demographics(conn: sqlite3.Connection):
    """5 & 6. Age Group Pie Chart and SIP Boxplot."""
    logger.info("Generating Charts 05 & 06: Investor Demographics...")
    df = pd.read_sql("SELECT age_group, transaction_type, amount_inr FROM fact_transactions", conn)
    
    # 5. Age group distribution pie chart
    age_counts = df["age_group"].value_counts()
    fig, ax = plt.subplots(figsize=(8, 8), dpi=300)
    colors = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"]
    ax.pie(age_counts, labels=age_counts.index, autopct="%1.1f%%", startangle=140, colors=colors, explode=[0.03]*len(age_counts), wedgeprops=dict(width=0.6, edgecolor='white'))
    ax.set_title("Investor Participation by Age Group", fontsize=13, weight="bold")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "05_investor_age_distribution_pie.png"))
    plt.close()
    
    # 6. SIP amount box plot by age group
    sip_df = df[df["transaction_type"] == "SIP"]
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    sns.boxplot(data=sip_df, x="age_group", y="amount_inr", order=sorted(df["age_group"].unique()), palette="Blues", ax=ax, showfliers=False)
    ax.set_title("SIP Ticket Size Distribution across Age Groups (INR)", fontsize=13, weight="bold", pad=15)
    ax.set_xlabel("Age Group", fontsize=11)
    ax.set_ylabel("Monthly SIP Amount (INR)", fontsize=11)
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "06_sip_amount_by_age_group_boxplot.png"))
    plt.close()


def chart_07_08_geographic_distribution(conn: sqlite3.Connection):
    """7 & 8. State-wise total investments and T30 vs B30 split."""
    logger.info("Generating Charts 07 & 08: Geographic Distribution...")
    df = pd.read_sql("SELECT state, city_tier, amount_inr FROM fact_transactions", conn)
    
    # 7. State-wise horizontal bar chart
    state_totals = df.groupby("state")["amount_inr"].sum().sort_values(ascending=True) / 1e7
    fig, ax = plt.subplots(figsize=(11, 8), dpi=300)
    state_totals.plot(kind="barh", color="#2563eb", ax=ax, edgecolor="#1e40af", alpha=0.85)
    ax.set_title("Total Mutual Fund Investment Volume by State (Rs. Crore)", fontsize=13, weight="bold", pad=15)
    ax.set_xlabel("Investment Volume (Rs. Crore)", fontsize=11)
    ax.set_ylabel("State", fontsize=11)
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "07_investment_volume_by_state.png"))
    plt.close()
    
    # 8. T30 vs B30 pie chart
    tier_counts = df["city_tier"].value_counts()
    fig, ax = plt.subplots(figsize=(7, 7), dpi=300)
    ax.pie(tier_counts, labels=[f"T30 ({tier_counts['T30']:,} txns)", f"B30 ({tier_counts['B30']:,} txns)"], autopct="%1.1f%%", colors=["#3b82f6", "#10b981"], startangle=90, explode=[0.04, 0.04])
    ax.set_title("Market Participation: T30 (Top 30 Cities) vs B30 (Beyond 30)", fontsize=13, weight="bold")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "08_t30_vs_b30_distribution_pie.png"))
    plt.close()


def chart_09_folio_growth(conn: sqlite3.Connection):
    """9. Folio count growth (13.26 to 26.12 crore)."""
    logger.info("Generating Chart 09: Industry Folio Growth...")
    df = pd.read_sql("SELECT month, total_folios_crore, equity_folios_crore, debt_folios_crore, hybrid_folios_crore FROM fact_folio_count ORDER BY month ASC", conn)
    
    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    ax.plot(df["month"], df["total_folios_crore"], marker="o", label="Total Folios", color="#1e3a8a", linewidth=3)
    ax.plot(df["month"], df["equity_folios_crore"], marker="s", label="Equity Folios", color="#2563eb", linewidth=2)
    ax.plot(df["month"], df["debt_folios_crore"], marker="^", label="Debt Folios", color="#10b981", linewidth=2)
    ax.plot(df["month"], df["hybrid_folios_crore"], marker="d", label="Hybrid Folios", color="#f59e0b", linewidth=2)
    
    ax.set_title("Mutual Fund Investor Folios Growth (Jan 2022 to Dec 2025)", fontsize=13, weight="bold", pad=15)
    ax.set_xlabel("Month", fontsize=11)
    ax.set_ylabel("Folio Count (Crore)", fontsize=11)
    plt.xticks(rotation=45, ha="right")
    ax.legend(frameon=True, facecolor="white")
    
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "09_industry_folio_count_growth.png"))
    plt.close()


def chart_10_correlation_matrix(conn: sqlite3.Connection):
    """10. Pairwise correlation of NAV returns across 10 funds."""
    logger.info("Generating Chart 10: Return Correlation Matrix...")
    query = """
    SELECT date, amfi_code, daily_return 
    FROM fact_nav 
    WHERE amfi_code IN (119551, 120503, 118632, 119092, 120841, 119598, 118634, 120844, 100025, 118636)
    """
    df = pd.read_sql(query, conn)
    pivot_returns = df.pivot(index="date", columns="amfi_code", values="daily_return")
    
    # Map code to scheme short name
    name_map = {
        119551: "SBI Bluechip",
        120503: "ICICI Bluechip",
        118632: "Nippon Large Cap",
        119092: "Axis Bluechip",
        120841: "Kotak Bluechip",
        119598: "SBI Small Cap",
        118634: "Nippon Small Cap",
        120844: "Kotak Liquid",
        100025: "HDFC Short Term",
        118636: "Nippon Gilt"
    }
    pivot_returns = pivot_returns.rename(columns=name_map)
    corr = pivot_returns.corr()
    
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="vlag", vmin=-0.2, vmax=1.0, linewidths=0.5, ax=ax)
    ax.set_title("Pairwise Return Correlation Matrix Across Asset Classes", fontsize=13, weight="bold", pad=15)
    plt.xticks(rotation=35, ha="right")
    
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "10_return_correlation_matrix.png"))
    plt.close()


def chart_11_sector_distribution(conn: sqlite3.Connection):
    """11. Top equity portfolio holdings sector distribution (Donut chart)."""
    logger.info("Generating Chart 11: Sector Allocation Donut Chart...")
    df = pd.read_sql("SELECT sector, market_value_cr FROM fact_portfolio_holdings", conn)
    sector_weights = df.groupby("sector")["market_value_cr"].sum().sort_values(ascending=False).head(8)
    
    fig, ax = plt.subplots(figsize=(8, 8), dpi=300)
    colors = sns.color_palette("Set2", len(sector_weights))
    wedges, texts, autotexts = ax.pie(
        sector_weights, labels=sector_weights.index, autopct="%1.1f%%",
        startangle=140, colors=colors, wedgeprops=dict(width=0.45, edgecolor="white")
    )
    ax.set_title("Sector Allocation Across Equity Portfolios (Market Value)", fontsize=13, weight="bold")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "11_sector_allocation_donut.png"))
    plt.close()


def chart_12_13_performance_metrics(conn: sqlite3.Connection):
    """12 & 13. Expense Ratio vs Returns, and Risk vs Return Scatter."""
    logger.info("Generating Charts 12 & 13: Risk & Performance Metrics...")
    df = pd.read_sql("SELECT scheme_name, category, return_3yr_pct, expense_ratio_pct, std_dev_ann_pct, sharpe_ratio, aum_crore FROM fact_performance", conn)
    
    # 12. Expense Ratio vs 3-Year CAGR
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    sns.scatterplot(data=df, x="expense_ratio_pct", y="return_3yr_pct", hue="category", s=100, palette="tab10", ax=ax)
    ax.set_title("Total Expense Ratio (TER) vs 3-Year CAGR Return (%)", fontsize=13, weight="bold", pad=15)
    ax.set_xlabel("Expense Ratio (%)", fontsize=11)
    ax.set_ylabel("3-Year CAGR Return (%)", fontsize=11)
    ax.legend(frameon=True, facecolor="white")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "12_expense_ratio_vs_return.png"))
    plt.close()
    
    # 13. Risk vs Return (Std Dev vs 3-Year Return)
    fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
    scatter = ax.scatter(df["std_dev_ann_pct"], df["return_3yr_pct"], c=df["sharpe_ratio"], cmap="viridis", s=df["aum_crore"] / 300, alpha=0.85, edgecolors="#1e293b")
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("Sharpe Ratio (Risk-Adjusted Return)")
    ax.set_title("Risk-Return Profile: Annualized Volatility vs 3-Year CAGR (Bubble Size = AUM)", fontsize=13, weight="bold", pad=15)
    ax.set_xlabel("Annualized Standard Deviation (%)", fontsize=11)
    ax.set_ylabel("3-Year CAGR Return (%)", fontsize=11)
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "13_risk_return_scatter.png"))
    plt.close()


def chart_14_15_transaction_patterns(conn: sqlite3.Connection):
    """14 & 15. Payment modes and KYC by City Tier."""
    logger.info("Generating Charts 14 & 15: Transaction Channels & KYC...")
    df = pd.read_sql("SELECT payment_mode, city_tier, kyc_status FROM fact_transactions", conn)
    
    # 14. Payment mode distribution
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    pm = df["payment_mode"].value_counts()
    sns.barplot(x=pm.index, y=pm.values, palette="Blues_r", ax=ax)
    ax.set_title("Investor Payment Channel Adoption", fontsize=13, weight="bold", pad=15)
    ax.set_xlabel("Payment Mode", fontsize=11)
    ax.set_ylabel("Transaction Count", fontsize=11)
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "14_payment_mode_distribution.png"))
    plt.close()
    
    # 15. KYC Status by City Tier
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    kyc_df = df.groupby(["city_tier", "kyc_status"]).size().unstack()
    kyc_df.plot(kind="bar", stacked=True, color=["#10b981", "#f59e0b"], ax=ax, edgecolor="white")
    ax.set_title("KYC Verification Status Across City Tiers (T30 vs B30)", fontsize=13, weight="bold", pad=15)
    ax.set_xlabel("City Tier", fontsize=11)
    ax.set_ylabel("Number of Transactions", fontsize=11)
    plt.xticks(rotation=0)
    ax.legend(title="KYC Status", frameon=True, facecolor="white")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "15_kyc_status_by_city_tier.png"))
    plt.close()


def main():
    logger.info("Starting Day 3 Exploratory Data Analysis Pipeline...")
    conn = get_db_connection()
    try:
        chart_01_nav_trends(conn)
        chart_02_aum_by_amc(conn)
        chart_03_sip_inflows(conn)
        chart_04_category_inflow_heatmap(conn)
        chart_05_06_demographics(conn)
        chart_07_08_geographic_distribution(conn)
        chart_09_folio_growth(conn)
        chart_10_correlation_matrix(conn)
        chart_11_sector_distribution(conn)
        chart_12_13_performance_metrics(conn)
        chart_14_15_transaction_patterns(conn)
        logger.info(f"All 15 charts successfully generated and saved into: {FIG_DIR}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
