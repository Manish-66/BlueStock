-- ====================================================================
-- queries.sql
-- Day 2: 10 Analytical SQL Queries for Mutual Fund Platform
-- Executed against bluestock_mf.db
-- ====================================================================

-- 1. Top 5 Mutual Funds by AUM
SELECT 
    f.amfi_code,
    f.scheme_name,
    f.fund_house,
    f.category,
    p.aum_crore,
    p.morningstar_rating
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.aum_crore DESC
LIMIT 5;

-- 2. Average NAV per Month for Key Schemes (e.g. SBI Bluechip 119551)
SELECT 
    f.scheme_name,
    SUBSTR(n.date, 1, 7) AS year_month,
    ROUND(AVG(n.nav), 2) AS avg_nav,
    ROUND(MIN(n.nav), 2) AS min_nav,
    ROUND(MAX(n.nav), 2) AS max_nav
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
WHERE n.amfi_code = 119551
GROUP BY f.scheme_name, SUBSTR(n.date, 1, 7)
ORDER BY year_month DESC
LIMIT 12;

-- 3. Monthly SIP Inflow & Year-over-Year (YoY) Growth Trend
SELECT 
    month,
    sip_inflow_crore,
    active_sip_accounts_crore,
    ROUND(yoy_growth_pct, 2) AS yoy_growth_pct,
    sip_aum_lakh_crore
FROM fact_sip_inflows
ORDER BY month DESC
LIMIT 12;

-- 4. Investor Transaction Volume and Total Amount by State
SELECT 
    state,
    COUNT(*) AS total_transactions,
    ROUND(SUM(amount_inr) / 10000000.0, 2) AS total_invested_crore,
    ROUND(AVG(amount_inr), 2) AS avg_transaction_amount
FROM fact_transactions
GROUP BY state
ORDER BY total_invested_crore DESC
LIMIT 10;

-- 5. Cost-Effective Funds with Expense Ratio < 1.0%
SELECT 
    f.amfi_code,
    f.scheme_name,
    f.fund_house,
    f.sub_category,
    f.plan,
    f.expense_ratio_pct,
    p.return_3yr_pct,
    p.sharpe_ratio
FROM dim_fund f
JOIN fact_performance p ON f.amfi_code = p.amfi_code
WHERE f.expense_ratio_pct < 1.0
ORDER BY f.expense_ratio_pct ASC;

-- 6. Total Inflows by Category for Latest Period
SELECT 
    category,
    ROUND(SUM(net_inflow_crore), 2) AS total_net_inflow_cr
FROM fact_category_inflows
GROUP BY category
ORDER BY total_net_inflow_cr DESC;

-- 7. Fund House AUM Market Share (Latest Quarter)
SELECT 
    fund_house,
    aum_crore,
    ROUND(aum_crore * 100.0 / (SELECT SUM(aum_crore) FROM fact_aum WHERE date = '2024-03-31'), 2) AS market_share_pct
FROM fact_aum
WHERE date = '2024-03-31'
ORDER BY aum_crore DESC;

-- 8. Top 10 Heavily Weighted Stock Holdings Across All Portfolios
SELECT 
    stock_symbol,
    stock_name,
    sector,
    COUNT(DISTINCT amfi_code) AS held_by_num_funds,
    ROUND(AVG(weight_pct), 2) AS avg_portfolio_weight_pct,
    ROUND(SUM(market_value_cr), 2) AS total_market_value_cr
FROM fact_portfolio_holdings
GROUP BY stock_symbol, stock_name, sector
ORDER BY total_market_value_cr DESC
LIMIT 10;

-- 9. Transaction Breakdown: SIP vs Lumpsum vs Redemption by City Tier
SELECT 
    city_tier,
    transaction_type,
    COUNT(*) AS txn_count,
    ROUND(SUM(amount_inr) / 10000000.0, 2) AS total_amount_cr,
    ROUND(AVG(amount_inr), 2) AS avg_ticket_size
FROM fact_transactions
GROUP BY city_tier, transaction_type
ORDER BY city_tier, total_amount_cr DESC;

-- 10. Risk-Adjusted Leaders: Top Funds Ranked by Sharpe Ratio
SELECT 
    f.scheme_name,
    f.sub_category,
    p.return_3yr_pct,
    p.sharpe_ratio,
    p.sortino_ratio,
    p.alpha,
    p.beta,
    p.risk_grade
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.sharpe_ratio DESC
LIMIT 10;
