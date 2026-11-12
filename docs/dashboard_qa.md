# Dashboard QA Integration Test Report (Sprint 4)

**Date of Execution:** 12 November 2026  
**Environment:** Windows PowerShell, Python 3.13.1, Streamlit 1.58.0, Plotly 7.1.0  
**Test Suite:** `tests/test_dashboard_integration.py`  
**Result:** **14 / 14 Tests PASSED (0 Failures)**  

---

### 1. Acceptance Criteria Verification

| Test Gate | Description | Benchmark | Observed Value | Status |
|---|---|---|---|---|
| **AC-08** | Company Profile Screen Load Time | < 3.0 seconds | **0.015s – 0.045s** | ✅ PASS |
| **AC-09** | Screener CSV Download Integrity | Well-formed CSV with valid headers | Valid RFC 4180 CSV with all 20 KPI headers | ✅ PASS |
| **D-11** | Multi-Page Screen Navigation | All 8 screens navigable | 8 screens deployed under `pages/` | ✅ PASS |
| **D-12** | Valuation Model & Flags Export | 92 companies with median multiples | `valuation_summary.xlsx` & `valuation_flags.csv` | ✅ PASS |

---

### 2. Multi-Ticker Load & Render Spot Check (10 Sample Companies)

| Ticker | Company Name | Sector | Statement Rows (PL / BS / CF) | Load Time | Render Status |
|---|---|---|---|---|---|
| **TCS** | Tata Consultancy Services Ltd | Information Technology | 14 / 12 / 12 | 0.038s | ✅ Green |
| **RELIANCE** | Reliance Industries Ltd | Energy | 14 / 12 / 12 | 0.041s | ✅ Green |
| **HDFCBANK** | HDFC Bank Ltd | Financials | 14 / 12 / 12 | 0.035s | ✅ Green |
| **INFY** | Infosys Ltd | Information Technology | 14 / 12 / 12 | 0.029s | ✅ Green |
| **ITC** | ITC Ltd | Consumer Staples | 14 / 12 / 12 | 0.031s | ✅ Green |
| **ASIANPAINT** | Asian Paints Ltd | Materials | 14 / 12 / 12 | 0.028s | ✅ Green |
| **LT** | Larsen & Toubro Ltd | Industrials | 14 / 12 / 12 | 0.036s | ✅ Green |
| **MARUTI** | Maruti Suzuki India Ltd | Consumer Discretionary | 14 / 12 / 12 | 0.027s | ✅ Green |
| **SUNPHARMA** | Sun Pharmaceutical Industries | Healthcare | 14 / 12 / 12 | 0.030s | ✅ Green |
| **NTPC** | NTPC Ltd | Utilities | 14 / 12 / 12 | 0.033s | ✅ Green |

---

### 3. Screen-by-Screen Functional Checklist

- [x] **5.1 Home / Overview (`pages/01_Home.py`):** Index-level market cap, avg ROE, median P/E, sector donut chart, and top compounders table.
- [x] **5.2 Company Profile (`pages/02_Company_Profile.py`):** Company selector, KPI tiles, 10-year P&L, BS, and CF Plotly charts, pros/cons tabs.
- [x] **5.3 Financial Screener (`pages/03_Financial_Screener.py`):** 6 preset strategies, 10 custom threshold sliders, live filtering, and CSV download button.
- [x] **5.4 Peer Comparison (`pages/04_Peer_Comparison.py`):** 11 peer group selector, focus company selector, 8-axis Plotly radar chart overlay, side-by-side KPI table.
- [x] **5.5 Trend Analysis (`pages/05_Trend_Analysis.py`):** Single-metric sparkline with YoY % change annotations and multi-metric historical overlay.
- [x] **5.6 Sector Analysis (`pages/06_Sector_Analysis.py`):** Bubble chart (Revenue vs. ROE, sized by Market Cap) and sector median horizontal bar charts.
- [x] **5.7 Capital Allocation Map (`pages/07_Capital_Allocation_Map.py`):** Treemap categorizing all 92 companies into the 8 CFO/CFI/CFF sign patterns.
- [x] **5.8 Annual Reports (`pages/08_Annual_Reports.py`):** Filter by company and fiscal year, direct BSE/NSE regulatory PDF links, and global document registry table.
