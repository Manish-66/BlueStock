# Bluestock Nifty 100 Financial Intelligence Platform

An enterprise-grade quantitative and fundamental financial intelligence platform covering all 92 constituents of the Nifty 100 Index across 14 fiscal years. Transforms raw financial statements into actionable multi-criteria screening, peer benchmarking, capital allocation classification, valuation models, and interactive dashboards.

---

## 🚀 Quick Start: Run the Interactive Dashboard

Launch the 8-screen Streamlit application locally:

```bash
streamlit run app.py
```
*Access the live web application on `http://localhost:8501`.*

---

## 🧭 Platform Features & 8 Multi-Page Screens

1. **01 — Home / Overview (`pages/01_Home.py`):** Executive index health banner, total market capitalization, average ROE, median P/E, and sector distribution donut chart.
2. **02 — Company Profile (`pages/02_Company_Profile.py`):** Interactive company dossier: KPI tiles, 10-year P&L bar charts, Balance Sheet structure, Cash Flow trajectory, and pros/cons badges.
3. **03 — Financial Screener (`pages/03_Financial_Screener.py`):** 6 institutional presets (Quality Compounder, Value Pick, Growth Accelerator, Dividend Champion, Debt-Free Blue Chip, Turnaround Watch) + 10 custom threshold sliders with real-time CSV download.
4. **04 — Peer Comparison (`pages/04_Peer_Comparison.py`):** 11 peer group benchmarks with 8-axis Plotly polar radar charts and side-by-side KPI comparison tables.
5. **05 — Trend Analysis (`pages/05_Trend_Analysis.py`):** 10-year sparklines with annual YoY % change annotations and multi-metric historical overlays.
6. **06 — Sector Analysis (`pages/06_Sector_Analysis.py`):** Macro sector bubble chart (Revenue vs. ROE vs. Market Cap) and horizontal sector median bar charts.
7. **07 — Capital Allocation Map (`pages/07_Capital_Allocation_Map.py`):** Treemap categorizing companies into the 8 canonical CFO/CFI/CFF cash flow sign patterns.
8. **08 — Annual Reports (`pages/08_Annual_Reports.py`):** Searchable regulatory document intelligence repository with clickable BSE/NSE PDF filing links.

---

## 📁 Repository Structure

```
BlueStock/
├── app.py                       # Main Streamlit web application entry point
├── config/
│   └── screener_config.yaml     # Analyst-editable screening thresholds & composite weights
├── data/
│   └── nifty100.db              # SQLite database (10 core & supplementary tables)
├── docs/
│   ├── dashboard_qa.md          # Integration testing report across 10 sample companies
│   └── sprint4_retro.md         # Sprint 4 retrospective and deliverable audit
├── output/
│   ├── screener_output.xlsx     # 6 sheets, one per preset with 20 KPIs & color-coded cells
│   ├── peer_comparison.xlsx     # 11 sheets, one per peer group with median summary row
│   ├── valuation_summary.xlsx   # 92 companies with 5Y median multiples & valuation badges
│   └── valuation_flags.csv      # 44 Caution & Discount flagged companies with written rationale
├── pages/                       # Streamlit multi-page dashboard screens (01 to 08)
├── reports/
│   └── radar_charts/            # 92 PNG radar charts (8 axes) with peer group overlays
├── src/
│   ├── analytics/
│   │   ├── peer.py              # Peer percentile ranking engine
│   │   └── valuation.py         # Valuation multiple modeling & overvaluation flags
│   ├── dashboard/
│   │   ├── app.py               # Dashboard mirroring entry point
│   │   └── utils/
│   │       ├── charts.py        # Reusable Plotly chart components
│   │       └── db.py            # SQLite caching layer (@st.cache_data ttl=600s)
│   ├── etl/
│   │   ├── loader.py            # Excel loader, year normalizer, and SQLite database builder
│   │   └── validator.py         # 14 Data Quality rules validation engine
│   └── screener/
│       └── engine.py            # 15-metric filter engine & sector-relative composite scoring
└── tests/
    ├── dq/
    │   └── test_rules.py        # Unit tests for 14 Data Quality rules (DQ-01 to DQ-14)
    └── test_dashboard_integration.py # End-to-end integration tests & AC-08/AC-09 verification
```

---

## 🧪 Running the Automated Test Suite

Execute all 28 automated pytest test cases (DQ rules + Dashboard integration):

```bash
python -m pytest tests/ -v
```

All 28 tests pass with 0 failures:
- 14 Data Quality validation tests (`tests/dq/test_rules.py`)
- 14 Dashboard integration tests (`tests/test_dashboard_integration.py`) verifying AC-08 (<3s load times) and AC-09 (CSV downloads).
