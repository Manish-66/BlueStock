# Data Quality Summary Report (Day 1)
**Project:** Bluestock Mutual Fund Analytics Platform
**Date:** 2026-10-13

## 1. AMFI Scheme Code Referential Integrity
- **Fund Master Scheme Count:** 40 schemes
- **NAV History Scheme Count:** 40 schemes
- **Missing in NAV History:** 0
- **Orphan Codes in NAV History:** 0
- **Validation Status:** PASSED - Perfect 1:1 match between fund_master and nav_history

## 2. Dataset Overview & Anomaly Scan
| File Name | Rows | Columns | Null Values | Duplicates | Anomaly Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `01_fund_master.csv` | 40 | 15 | 0 | 0 | Clean. Complete metadata for 40 schemes. |
| `02_nav_history.csv` | 46,000 | 3 | 0 | 0 | Exactly 1,150 trading days per scheme (40 x 1,150 = 46,000 rows). Clean. |
| `03_aum_by_fund_house.csv` | 90 | 5 | 0 | 0 | Quarterly AUM for top 10 AMCs across 9 quarters. Clean. |
| `04_monthly_sip_inflows.csv` | 48 | 6 | 12 | 0 | Notice: `yoy_growth_pct` has 12 nulls in Year 1 (expected: requires 12-month lag). |
| `05_category_inflows.csv` | 144 | 3 | 0 | 0 | Clean monthly category-level inflows across 12 categories. |
| `06_industry_folio_count.csv` | 21 | 6 | 0 | 0 | Clean milestones of industry folios (Equity, Debt, Hybrid). |
| `07_scheme_performance.csv` | 40 | 19 | 0 | 0 | Comprehensive return and risk metrics for all 40 schemes. Clean. |
| `08_investor_transactions.csv` | 32,778 | 13 | 0 | 0 | Simulated retail and HNI transactions across Indian states. Clean. |
| `09_portfolio_holdings.csv` | 322 | 8 | 0 | 0 | Top equity holdings for equity schemes. Clean. |
| `10_benchmark_indices.csv` | 8,050 | 3 | 0 | 0 | Daily close for 7 benchmark indices across 1,150 dates. Clean. |

## 3. Key Observations & Ingestion Recommendations
1. **Historical NAV Timelines:** All 40 schemes contain continuous daily NAV series from January 2022 to May 2026.
2. **Lagged Variables:** In `04_monthly_sip_inflows.csv`, the 12 missing values in `yoy_growth_pct` are structurally valid because year-over-year calculation requires a 12-month historical lookback window.
3. **Date Consistency:** Formats should be strictly parsed to ISO 8601 `YYYY-MM-DD` during the Day 2 SQLite staging phase.
