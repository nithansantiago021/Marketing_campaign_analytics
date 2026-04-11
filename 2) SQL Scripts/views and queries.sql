-- Marketing Campaign Analytics — SQL Scripts
-- PART 1: DDL — Table Creation
-- 		a) Create a database named 'marketing_analytics'
-- 		b) Right - click on the left panel (schemas) and select 'Table Data Import wizard'
-- 		c) select the 'marketing_clean.csv' file 
-- 		d) Choose --> Create new table
-- 		e) Map columns (Workbench auto-detects this)
-- 		f) Click Next --> Finish


-- PART 2: VIEWS

-- ── View 1: Campaign KPIs ────────────────────────────────────────────────────
DROP VIEW IF EXISTS v_campaign_kpis;
CREATE VIEW v_campaign_kpis AS 
-- MySQL: CAST(x AS DOUBLE) instead of CAST(x AS REAL)
SELECT 'Campaign 1'               AS campaign,
       ROUND(AVG(AcceptedCmp1 + 0.0) * 100, 2) AS response_rate_pct,
       SUM(AcceptedCmp1)                         AS total_accepted
FROM customers
UNION ALL
SELECT 'Campaign 2',
       ROUND(AVG(AcceptedCmp2 + 0.0) * 100, 2), SUM(AcceptedCmp2)
FROM customers
UNION ALL
SELECT 'Campaign 3',
       ROUND(AVG(AcceptedCmp3 + 0.0) * 100, 2), SUM(AcceptedCmp3)
FROM customers
UNION ALL
SELECT 'Campaign 4',
       ROUND(AVG(AcceptedCmp4 + 0.0) * 100, 2), SUM(AcceptedCmp4)
FROM customers
UNION ALL
SELECT 'Campaign 5',
       ROUND(AVG(AcceptedCmp5 + 0.0) * 100, 2), SUM(AcceptedCmp5)
FROM customers
UNION ALL
SELECT 'Last Campaign (Response)',
       ROUND(AVG(Response + 0.0) * 100, 2), SUM(Response)
FROM customers;


-- ── View 2: Segment KPI summary ──────────────────────────────────────────────
CREATE VIEW v_segment_kpis AS
SELECT
    Primary_Segment                                     AS segment,
    COUNT(*)                                            AS n_customers,
    ROUND(AVG(Income), 0)                               AS avg_income,
    ROUND(AVG(Age), 1)                                  AS avg_age,
    ROUND(AVG(Total_Spend), 0)                          AS avg_total_spend,
    ROUND(AVG(Total_Purchases), 1)                      AS avg_total_purchases,
    ROUND(AVG(Response + 0.0) * 100, 2)                 AS response_rate_pct,
    ROUND(AVG(Any_Campaign_Accepted + 0.0) * 100, 2)    AS any_campaign_rate_pct,
    ROUND(AVG(NumWebVisitsMonth), 1)                    AS avg_web_visits,
    ROUND(AVG(Children), 2)                             AS avg_children
FROM customers
GROUP BY Primary_Segment
ORDER BY avg_total_spend DESC;


-- ── View 3: Product spend by segment ─────────────────────────────────────────
DROP VIEW IF EXISTS v_product_spend_by_segment;
CREATE VIEW v_product_spend_by_segment AS
SELECT
    Primary_Segment                  AS segment,
    ROUND(AVG(MntWines), 0)          AS avg_wines,
    ROUND(AVG(MntFruits), 0)         AS avg_fruits,
    ROUND(AVG(MntMeatProducts), 0)   AS avg_meat,
    ROUND(AVG(MntFishProducts), 0)   AS avg_fish,
    ROUND(AVG(MntSweetProducts), 0)  AS avg_sweets,
    ROUND(AVG(MntGoldProds), 0)      AS avg_gold
FROM customers
GROUP BY Primary_Segment;


-- ── View 4: Channel usage by segment ─────────────────────────────────────────
DROP VIEW IF EXISTS v_channel_by_segment;
CREATE VIEW v_channel_by_segment AS
SELECT
    Primary_Segment                       AS segment,
    ROUND(AVG(NumWebPurchases), 2)        AS avg_web,
    ROUND(AVG(NumCatalogPurchases), 2)    AS avg_catalog,
    ROUND(AVG(NumStorePurchases), 2)      AS avg_store,
    ROUND(AVG(NumDealsPurchases), 2)      AS avg_deals,
    ROUND(AVG(NumWebVisitsMonth), 2)      AS avg_web_visits,
    COUNT(*)                              AS n
FROM customers
GROUP BY Primary_Segment;


-- ── View 5: Country summary ───────────────────────────────────────────────────
DROP VIEW IF EXISTS v_country_summary;
CREATE VIEW v_country_summary AS
SELECT
    Country,
    COUNT(*)                                AS n_customers,
    ROUND(AVG(Income), 0)                   AS avg_income,
    ROUND(AVG(Total_Spend), 0)              AS avg_total_spend,
    ROUND(AVG(Response + 0.0) * 100, 2)     AS response_rate_pct,
    ROUND(AVG(NumWebVisitsMonth), 1)        AS avg_web_visits
FROM customers
GROUP BY Country
ORDER BY avg_total_spend DESC;


-- ── View 6: Age-band × Income-band cross-tab ─────────────────────────────────
DROP VIEW IF EXISTS v_age_income_summary;
CREATE VIEW v_age_income_summary AS
SELECT
    Age_Band,
    Income_Band,
    COUNT(*)                               AS n_customers,
    ROUND(AVG(Total_Spend), 0)             AS avg_total_spend,
    ROUND(AVG(Response + 0.0) * 100, 2)    AS response_rate_pct
FROM customers
WHERE Age_Band IS NOT NULL
  AND Income_Band IS NOT NULL
GROUP BY Age_Band, Income_Band;


-- PART 3: ANALYTICAL QUERIES

-- Q1: Campaign response rates — use v_campaign_kpis view
SELECT * FROM v_campaign_kpis ORDER BY response_rate_pct DESC;


-- Q2: Segment response rates (last campaign)
SELECT
    Primary_Segment   AS segment,
    COUNT(*)          AS n,
    SUM(Response)     AS responders,
    ROUND(AVG(Response + 0.0) * 100, 2) AS response_rate_pct
FROM customers
GROUP BY Primary_Segment
ORDER BY response_rate_pct DESC;


-- Q3: Top 5 countries by avg spend + response rate
SELECT
    Country,
    COUNT(*)                              AS n_customers,
    ROUND(AVG(Total_Spend), 0)            AS avg_spend,
    ROUND(AVG(Response + 0.0) * 100, 2)   AS response_rate_pct
FROM customers
GROUP BY Country
ORDER BY avg_spend DESC
LIMIT 5;


-- Q4: Under-served customers (high web visits, low spend, no response)
SELECT
    Education,
    Marital_Status,
    COUNT(*)                        AS n_underserved,
    ROUND(AVG(Age), 1)              AS avg_age,
    ROUND(AVG(Income), 0)           AS avg_income,
    ROUND(AVG(Total_Spend), 0)      AS avg_spend,
    ROUND(AVG(NumWebVisitsMonth),1) AS avg_web_visits
FROM customers
WHERE NumWebVisitsMonth >= 5
  AND Total_Spend < (SELECT AVG(Total_Spend) FROM customers)
  AND Response = 0
GROUP BY Education, Marital_Status
ORDER BY n_underserved DESC;


-- Q5: Ideal target customer profiles
--     MySQL: HAVING must reference the actual expression or alias
SELECT
    Age_Band,
    Income_Band,
    Education,
    Marital_Status,
    COUNT(*)                                    AS n_customers,
    ROUND(AVG(Total_Spend), 0)                  AS avg_spend,
    ROUND(AVG(Response + 0.0) * 100, 2)          AS last_cmp_response_rate,
    ROUND(AVG(Any_Campaign_Accepted + 0.0) * 100, 2) AS any_cmp_acceptance_rate
FROM customers
WHERE Seg_High_Income = 1
  AND Total_Campaign_Accepted >= 1
GROUP BY Age_Band, Income_Band, Education, Marital_Status
HAVING COUNT(*) >= 30           -- ← MySQL: use COUNT(*) not the alias
ORDER BY last_cmp_response_rate DESC, avg_spend DESC
LIMIT 20;


-- Q6: Channel preference by spend tier
SELECT
    CASE
        WHEN Seg_High_Spender = 1 THEN 'Top 10% Spenders'
        WHEN Total_Spend <= (SELECT AVG(Total_Spend) FROM customers) THEN 'Bottom ~50%'
        ELSE 'Mid Spenders'
    END                                 AS customer_tier,
    COUNT(*)                            AS n,
    ROUND(AVG(NumWebPurchases), 2)      AS avg_web_purch,
    ROUND(AVG(NumCatalogPurchases), 2)  AS avg_catalog_purch,
    ROUND(AVG(NumStorePurchases), 2)    AS avg_store_purch,
    ROUND(AVG(NumDealsPurchases), 2)    AS avg_deal_purch,
    ROUND(AVG(NumWebVisitsMonth), 2)    AS avg_web_visits
FROM customers
GROUP BY customer_tier;


-- Q7: Window function — rank customers by spend within each country
SELECT
    ID,
    Country,
    Total_Spend,
    Income,
    Age,
    Primary_Segment,
    RANK()  OVER (PARTITION BY Country ORDER BY Total_Spend DESC) AS spend_rank_in_country,
    NTILE(4) OVER (PARTITION BY Country ORDER BY Total_Spend DESC) AS spend_quartile
FROM customers
ORDER BY Country, spend_rank_in_country
LIMIT 50;


-- Q8: Running total of customer enrollments per month
SELECT
    YEAR(STR_TO_DATE(Dt_Customer, '%Y-%m-%d'))                       AS enroll_year,
    MONTH(STR_TO_DATE(Dt_Customer, '%Y-%m-%d'))                      AS enroll_month,
    COUNT(*)                                                          AS new_customers,
    SUM(COUNT(*)) OVER (
        ORDER BY YEAR(STR_TO_DATE(Dt_Customer, '%Y-%m-%d')),
                 MONTH(STR_TO_DATE(Dt_Customer, '%Y-%m-%d'))
    )                                                                 AS running_total
FROM customers
GROUP BY enroll_year, enroll_month
ORDER BY enroll_year, enroll_month;


-- Q9: Multi-campaign acceptance profile
SELECT
    Total_Campaign_Accepted   AS campaigns_accepted,
    COUNT(*)                  AS n_customers,
    ROUND(AVG(Income), 0)     AS avg_income,
    ROUND(AVG(Total_Spend), 0) AS avg_spend,
    ROUND(AVG(Age), 1)        AS avg_age
FROM customers
GROUP BY Total_Campaign_Accepted
ORDER BY Total_Campaign_Accepted;


-- Q10: Product spend by age band
SELECT
    Age_Band,
    ROUND(AVG(MntWines), 0)         AS avg_wines,
    ROUND(AVG(MntFruits), 0)        AS avg_fruits,
    ROUND(AVG(MntMeatProducts), 0)  AS avg_meat,
    ROUND(AVG(MntFishProducts), 0)  AS avg_fish,
    ROUND(AVG(MntSweetProducts), 0) AS avg_sweets,
    ROUND(AVG(MntGoldProds), 0)     AS avg_gold,
    ROUND(AVG(Total_Spend), 0)      AS avg_total
FROM customers
WHERE Age_Band IS NOT NULL
GROUP BY Age_Band
ORDER BY Age_Band;
