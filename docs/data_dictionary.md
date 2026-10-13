# Data Dictionary: Bluestock Mutual Fund Platform

Comprehensive schema and column-level documentation for all datasets stored in the SQLite database `bluestock_mf.db`.

---

## 1. `dim_fund` (Fund Master Dimension)
**Source:** `01_fund_master.csv`  
**Primary Key:** `amfi_code`  
**Description:** Dimension table storing scheme profile metadata for all 40 tracked mutual funds.

| Column | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | PRIMARY KEY | Unique 6-digit identifier assigned by AMFI |
| `fund_house` | TEXT | NOT NULL | Asset Management Company (AMC) name |
| `scheme_name` | TEXT | NOT NULL | Full mutual fund scheme name |
| `category` | TEXT | NOT NULL | High-level asset class (Equity, Debt) |
| `sub_category` | TEXT | NOT NULL | Specific mandate (Large Cap, Mid Cap, Liquid, Gilt, etc.) |
| `plan` | TEXT | NOT NULL | Plan distribution type (`Regular` or `Direct`) |
| `launch_date` | TEXT | ISO Date | Scheme inception date (`YYYY-MM-DD`) |
| `benchmark` | TEXT | - | Benchmark index (e.g. NIFTY 100 TRI) |
| `expense_ratio_pct`| REAL | [0.1 - 2.5] | Total Expense Ratio (TER) in percentage |
| `exit_load_pct` | REAL | - | Exit load applicable on premature redemption |
| `min_sip_amount` | REAL | - | Minimum monthly SIP amount in INR |
| `min_lumpsum_amount`| REAL | - | Minimum initial lump-sum investment in INR |
| `fund_manager` | TEXT | - | Lead portfolio manager |
| `risk_category` | TEXT | - | SEBI Riskometer level (Low, Moderate, High, Very High) |
| `sebi_category_code`| TEXT | - | Regulatory categorization code (e.g. EC01) |

---

## 2. `fact_nav` (Historical Daily NAV)
**Source:** `02_nav_history.csv`  
**Primary Key:** `id` (Auto-increment)  
**Foreign Key:** `amfi_code` -> `dim_fund(amfi_code)`  
**Description:** Daily net asset value time series from Jan 2022 to May 2026.

| Column | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY | Unique record identifier |
| `amfi_code` | INTEGER | FOREIGN KEY | References `dim_fund(amfi_code)` |
| `date` | TEXT | ISO Date | Market trading date (`YYYY-MM-DD`) |
| `nav` | REAL | > 0 | Net Asset Value in INR per unit |
| `daily_return` | REAL | - | Daily percentage return relative to preceding trading day |

---

## 3. `fact_transactions` (Investor Transactions)
**Source:** `08_investor_transactions.csv`  
**Primary Key:** `id` (Auto-increment)  
**Foreign Key:** `amfi_code` -> `dim_fund(amfi_code)`  
**Description:** Transaction records capturing retail and HNI investments, redemptions, and investor demographics.

| Column | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY | Unique transaction record identifier |
| `investor_id` | TEXT | NOT NULL | Unique masked investor identifier |
| `transaction_date` | TEXT | ISO Date | Date of transaction execution (`YYYY-MM-DD`) |
| `amfi_code` | INTEGER | FOREIGN KEY | Target mutual fund scheme |
| `transaction_type` | TEXT | - | `SIP`, `Lumpsum`, or `Redemption` |
| `amount_inr` | REAL | > 0 | Transaction amount in INR |
| `state` | TEXT | - | Investor Indian state |
| `city` | TEXT | - | Investor residential city |
| `city_tier` | TEXT | - | AMFI geography category (`T30` Top 30, `B30` Beyond 30) |
| `age_group` | TEXT | - | Demographic bracket (`18-25`, `26-35`, `36-45`, `46-55`, `56+`) |
| `gender` | TEXT | - | `Male`, `Female` |
| `annual_income_lakh`| REAL| - | Investor annual declared income in Lakh INR |
| `payment_mode` | TEXT | - | Channel used (`UPI`, `Net Banking`, `Mandate`, `Cheque`) |
| `kyc_status` | TEXT | - | KYC compliance state (`Verified`, `Pending`) |

---

## 4. `fact_performance` (Risk & Return Metrics)
**Source:** `07_scheme_performance.csv`  
**Primary Key:** `amfi_code`  
**Foreign Key:** `amfi_code` -> `dim_fund(amfi_code)`  
**Description:** Quantitative performance and risk-adjusted metrics calculated over 1, 3, and 5-year periods.

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `amfi_code` | INTEGER | Primary Key referencing `dim_fund` |
| `scheme_name` | TEXT | Scheme name |
| `fund_house` | TEXT | AMC name |
| `category` | TEXT | Sub-category mandate |
| `plan` | TEXT | Plan type (`Regular` / `Direct`) |
| `return_1yr_pct` | REAL | 1-Year annualized return percentage |
| `return_3yr_pct` | REAL | 3-Year CAGR return percentage |
| `return_5yr_pct` | REAL | 5-Year CAGR return percentage |
| `benchmark_3yr_pct`| REAL | Benchmark return over 3 years |
| `alpha` | REAL | Jensen's Alpha (excess return over CAPM prediction) |
| `beta` | REAL | Sensitivity to market benchmark movements |
| `sharpe_ratio` | REAL | Excess return per unit of total risk |
| `sortino_ratio` | REAL | Excess return per unit of downside deviation |
| `std_dev_ann_pct`| REAL | Annualized standard deviation of daily returns |
| `max_drawdown_pct`| REAL | Peak-to-trough decline over observation period |
| `aum_crore` | REAL | Total Assets Under Management in Crore INR |
| `expense_ratio_pct`| REAL | Total expense ratio percentage |
| `morningstar_rating`| INTEGER | Qualitative rating from 1 to 5 stars |
| `risk_grade` | TEXT | Risk classification (Low, Moderate, High, Very High) |
| `is_negative_sharpe`| INTEGER | Binary flag (1 if negative Sharpe, else 0) |

---

## 5. `fact_aum` (AUM by Fund House)
**Source:** `03_aum_by_fund_house.csv`  
| Column | Data Type | Description |
| :--- | :--- | :--- |
| `date` | TEXT | Quarter-ending date (`YYYY-MM-DD`) |
| `fund_house` | TEXT | Asset Management Company |
| `aum_lakh_crore` | REAL | AUM in Lakh Crore INR |
| `aum_crore` | REAL | AUM in Crore INR |
| `num_schemes` | INTEGER | Total live schemes managed |

---

## 6. `fact_sip_inflows` (Monthly SIP Inflows)
**Source:** `04_monthly_sip_inflows.csv`  
| Column | Data Type | Description |
| :--- | :--- | :--- |
| `month` | TEXT | Reporting month (`YYYY-MM`) |
| `sip_inflow_crore` | REAL | Monthly gross SIP collections in Crore INR |
| `active_sip_accounts_crore` | REAL | Active SIP folios in Crore |
| `new_sip_accounts_lakh` | REAL | Fresh SIP accounts registered in Month (Lakh) |
| `sip_aum_lakh_crore` | REAL | Total cumulative SIP AUM in Lakh Crore INR |
| `yoy_growth_pct` | REAL | Year-over-Year SIP growth percentage |

---

## 7. `fact_category_inflows` (Inflows by Fund Category)
**Source:** `05_category_inflows.csv`  
| Column | Data Type | Description |
| :--- | :--- | :--- |
| `month` | TEXT | Reporting month (`YYYY-MM`) |
| `category` | TEXT | Scheme category (e.g. Large Cap, Mid Cap, Liquid) |
| `net_inflow_crore` | REAL | Monthly net net inflow in Crore INR |

---

## 8. `fact_portfolio_holdings` (Equity Portfolio Holdings)
**Source:** `09_portfolio_holdings.csv`  
| Column | Data Type | Description |
| :--- | :--- | :--- |
| `amfi_code` | INTEGER | Scheme code |
| `stock_symbol` | TEXT | NSE ticker symbol (e.g. RELIANCE, HDFCBANK) |
| `stock_name` | TEXT | Corporate name |
| `sector` | TEXT | Sector classification (Banking, IT, Auto, etc.) |
| `weight_pct` | REAL | Percentage portfolio allocation |
| `market_value_cr` | REAL | Position market value in Crore INR |
| `current_price_inr` | REAL | Underlying stock market price |
| `portfolio_date` | TEXT | Reporting cutoff date (`YYYY-MM-DD`) |

---

## 9. `fact_benchmark_indices` (Daily Index Closings)
**Source:** `10_benchmark_indices.csv`  
| Column | Data Type | Description |
| :--- | :--- | :--- |
| `date` | TEXT | Trading date (`YYYY-MM-DD`) |
| `index_name` | TEXT | Benchmark name (`NIFTY50`, `NIFTY100`, etc.) |
| `close_value` | REAL | Official daily closing index points |

---

## 10. `fact_folio_count` (Industry Milestones)
**Source:** `06_industry_folio_count.csv`  
| Column | Data Type | Description |
| :--- | :--- | :--- |
| `month` | TEXT | Milestone date (`YYYY-MM`) |
| `total_folios_crore` | REAL | Industry total investor folios in Crore |
| `equity_folios_crore` | REAL | Total equity folios in Crore |
| `debt_folios_crore` | REAL | Total debt folios in Crore |
| `hybrid_folios_crore`| REAL | Total hybrid folios in Crore |
| `others_folios_crore`| REAL | Other folios (Index, ETFs, FoFs) |
