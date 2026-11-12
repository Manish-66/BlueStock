# Sprint 4 Retrospective — Dashboard & Valuation

**Date:** 12 November 2026  
**Sprint Duration:** Days 22–28 (Target Story Points: 49 SP)  
**Status:** **COMPLETED & VERIFIED**  

---

### 1. Goals vs. Actual Achievements

| Sprint Objective | Planned Deliverable | Actual Outcome | Status |
|---|---|---|---|
| Scaffold Streamlit Web App | `app.py`, `src/dashboard/app.py`, `pages/` | Multi-page app structured with 8 dedicated screens | ✅ Done |
| Home & Profile Screens | `pages/01_Home.py`, `pages/02_Company_Profile.py` | Macro index health KPIs + interactive 10-year P&L, BS, CF charts | ✅ Done |
| Screener & Peer Screens | `pages/03_Financial_Screener.py`, `pages/04_Peer_Comparison.py` | 10 dynamic sliders + CSV export + 8-axis Plotly radar overlay | ✅ Done |
| Trends, Sectors & Reports | `pages/05–08.py` | Sparklines with YoY annotations, bubble charts, capital treemap, document repository | ✅ Done |
| Valuation Summary Model | `output/valuation_summary.xlsx` | 92 companies with 5Y median multiples, FCF yield, and overvaluation flags | ✅ Done |
| Valuation Flags Rationale | `output/valuation_flags.csv` | 44 Caution & Discount flagged companies with written business rationale | ✅ Done |
| Integration QA & Test Suite | `tests/test_dashboard_integration.py` | 14 integration tests passing (100% green); load times < 0.05s | ✅ Done |

---

### 2. Key Learnings & Engineering Wins
1. **Caching Architecture:** Integrating `@st.cache_data(ttl=600)` in `src/dashboard/utils/db.py` reduced company dossier load times from ~0.8s to <0.04s, well below the AC-08 requirement of 3.0s.
2. **Missing Cash Flow Handling:** ATGL lacked raw rows in `cashflow.xlsx`; a left join in `get_capital_allocation_data` ensured 100% (92/92) company coverage without dropping constituents.
3. **Valuation Multiples Distribution:** Historical 5-year median computations provided robust benchmarks against temporary multiple inflation, generating 14 *Caution* flags and 30 *Discount* flags.

---

### 3. Next Steps (Sprint 5: Days 29–35)
- **Module 7:** Cash Flow Intelligence (`cashflow_intelligence.xlsx` — CFO quality scores, CapEx intensity, distress pattern flagging).
- **Module 8 & 9:** Automated NLP parser for `analysis.xlsx` and Rule-based Pros/Cons generator (`pros_cons_generated.csv`).
- **Module 10:** Automated PDF Report Generator for 92 Company Tearsheets (2 pages each in `reports/tearsheets/`).
