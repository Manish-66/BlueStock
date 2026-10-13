# Bluestock Mutual Fund Analytics Platform

A full-stack quantitative Mutual Fund Analytics Platform ingesting, cleaning, and modelling data from AMFI India, NSE/BSE benchmark indices, and live REST APIs (`mfapi.in`).

## 📁 Project Structure

```
BlueStock/
├── data/
│   ├── raw/                 # Original 10 CSV datasets + live fetched API CSVs
│   │   ├── 01_fund_master.csv
│   │   ├── 02_nav_history.csv
│   │   ├── 03_aum_by_fund_house.csv
│   │   ├── 04_monthly_sip_inflows.csv
│   │   ├── 05_category_inflows.csv
│   │   ├── 06_industry_folio_count.csv
│   │   ├── 07_scheme_performance.csv
│   │   ├── 08_investor_transactions.csv
│   │   ├── 09_portfolio_holdings.csv
│   │   ├── 10_benchmark_indices.csv
│   │   └── live_nav_*.csv   # Live NAV files pulled via mfapi.in
│   ├── processed/           # Transformed & cleaned datasets (Day 2+)
│   └── db/                  # SQLite relational database bluestock_mf.db
├── notebooks/
│   └── 01_data_ingestion.ipynb
├── sql/                     # DDL schemas and analytical SQL queries
├── dashboard/               # BI dashboards (.pbix / Tableau)
├── reports/                 # Quality reports and presentations
│   └── day1_data_quality_report.md
├── docs/                    # Capstone specification & reference PDFs
├── data_ingestion.py        # Day 1 data profiling & referential integrity script
├── live_nav_fetch.py        # Automated mfapi.in REST API ingestion script
├── requirements.txt         # Core dependencies
└── .gitignore
```

## 🚀 Day 1 Setup & Execution

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Fetch Live NAVs via REST API
```bash
python live_nav_fetch.py
```
Fetches live and historical NAV time series for HDFC Top 100 Direct (`125497`) and the 5 key schemes:
- SBI Bluechip (`119551`)
- ICICI Prudential Bluechip (`120503`)
- Nippon India Large Cap (`118632`)
- Axis Bluechip (`119092`)
- Kotak Bluechip (`120841`)

### 3. Run Data Ingestion & Quality Validation
```bash
python data_ingestion.py
```
Performs schema analysis across all 10 CSV datasets and validates AMFI code referential integrity between `01_fund_master.csv` and `02_nav_history.csv`.
