# Internship Progress Tracker: Bluestock Mutual Fund Capstone Project

**Student:** Manish Kumar (B23082@students.iitmandi.ac.in)  
**GitHub Repository:** [https://github.com/Manish-66/BlueStock](https://github.com/Manish-66/BlueStock)  
**Portal:** [https://workspace.bluestock.in/](https://workspace.bluestock.in/)  
**Evaluation Weightage Total:** 100%

---

## 📊 7-Day Capstone Roadmap & Status

| Day | Focus Area | Deliverables | Weight | Status |
| :--- | :--- | :--- | :---: | :---: |
| **Day 1** | **Project Setup + Data Ingestion (ETL)** | Folder structure, `requirements.txt`, `data_ingestion.py`, `live_nav_fetch.py`, raw CSVs, Git repo commit | **15%** | ✅ **COMPLETED & PUSHED** |
| **Day 2** | **Data Cleaning + SQL Database Design** | `clean_nav.csv`, `clean_transactions.csv`, `clean_performance.csv`, `schema.sql`, `bluestock_mf.db` (SQLite), 10 queries, data dictionary | **10%** | ✅ **COMPLETED & PUSHED** |
| **Day 3** | **Exploratory Data Analysis (EDA)** | `03_eda_analysis.ipynb` with distributions, trends, heatmaps, and outlier detection | **15%** | ⏳ *Next Step* |
| **Day 4** | **Fund Performance Analytics** | `04_performance_analytics.ipynb`, CAGR, Sharpe, Sortino, Alpha, Beta vs Benchmarks | **15%** | ⬜ *Pending* |
| **Day 5** | **Interactive Dashboard Development** | Power BI / Tableau / Streamlit interactive multi-page dashboard | **20%** | ⬜ *Pending* |
| **Day 6** | **Advanced Analytics + Risk Metrics** | Value at Risk (VaR), investor cohort analysis, Monte Carlo simulation | **10%** | ⬜ *Pending* |
| **Day 7** | **Final Report + Presentation + Deployment** | `Final_Report.pdf` (15-20 pages), 12-slide deck (`Presentation.pptx`), cleaned codebase | **15%** | ⬜ *Pending* |

---

## 🎯 Day 1 Verification Checklist

- [x] Folder structure created (`data/raw`, `data/processed`, `notebooks/`, `sql/`, `dashboard/`, `reports/`)
- [x] `requirements.txt` created and dependencies installed (`pandas`, `numpy`, `matplotlib`, `seaborn`, `plotly`, `sqlalchemy`, `requests`, `scipy`, `jupyter`)
- [x] All 10 CSV datasets loaded, inspected (.shape, .dtypes, .head()), anomalies checked
- [x] Live NAV fetched for HDFC Top 100 Direct (`125497`) and saved to raw CSV
- [x] Live NAV fetched for 5 key schemes:
  - SBI Bluechip (`119551`)
  - ICICI Bluechip (`120503`)
  - Nippon Large Cap (`118632`)
  - Axis Bluechip (`119092`)
  - Kotak Bluechip (`120841`)
- [x] Fund master explored (unique fund houses, categories, sub-categories, risk grades, AMFI code structure)
- [x] AMFI codes validated (100% 1:1 match between `fund_master` and `nav_history`)
- [x] Git repository initialised and committed: `"Day 1: Data ingestion complete"`
- [x] Remote GitHub repository linked and pushed: `https://github.com/Manish-66/BlueStock`
