-- UK (GB) electricity generation analysis
-- Database: data/energy.db (created by scripts/clean_data.py)
-- Table:    monthly_generation (one row per complete month, Jan 2009 onwards, values in GWh)
-- Open in DB Browser for SQLite, or run:  sqlite3 data/energy.db < sql/analysis.sql


-- Q1. How much electricity did nuclear generate each year, and what share of the total was it?
SELECT year,
       ROUND(SUM(nuclear_gwh) / 1000, 1)                       AS nuclear_twh,
       ROUND(SUM(total_gwh) / 1000, 1)                         AS total_twh,
       ROUND(100.0 * SUM(nuclear_gwh) / SUM(total_gwh), 1)     AS nuclear_share_pct
FROM monthly_generation
GROUP BY year
HAVING COUNT(*) = 12            -- full years only
ORDER BY year;


-- Q2. How has the mix changed? Share of each major source, first full year vs latest full year.
SELECT year,
       ROUND(100.0 * SUM(gas_gwh)        / SUM(total_gwh), 1) AS gas_pct,
       ROUND(100.0 * SUM(coal_gwh)       / SUM(total_gwh), 1) AS coal_pct,
       ROUND(100.0 * SUM(nuclear_gwh)    / SUM(total_gwh), 1) AS nuclear_pct,
       ROUND(100.0 * SUM(wind_total_gwh) / SUM(total_gwh), 1) AS wind_pct,
       ROUND(100.0 * SUM(solar_gwh)      / SUM(total_gwh), 1) AS solar_pct,
       ROUND(100.0 * SUM(imports_gwh)    / SUM(total_gwh), 1) AS imports_pct
FROM monthly_generation
WHERE year IN (2009, 2025)
GROUP BY year;


-- Q3. In which year did wind first generate more electricity than nuclear?
SELECT year,
       ROUND(SUM(wind_total_gwh) / 1000, 1) AS wind_twh,
       ROUND(SUM(nuclear_gwh) / 1000, 1)    AS nuclear_twh
FROM monthly_generation
GROUP BY year
HAVING COUNT(*) = 12 AND SUM(wind_total_gwh) > SUM(nuclear_gwh)
ORDER BY year
LIMIT 1;


-- Q4. Seasonality: average nuclear output and share by season (last 5 full years, 2021-2025).
SELECT season,
       ROUND(AVG(nuclear_gwh), 0)          AS avg_monthly_nuclear_gwh,
       ROUND(100.0 * AVG(nuclear_share), 1) AS avg_nuclear_share_pct
FROM monthly_generation
WHERE year BETWEEN 2021 AND 2025
GROUP BY season
ORDER BY avg_nuclear_share_pct DESC;


-- Q5. The five months with the highest nuclear share since 2020.
SELECT month,
       ROUND(nuclear_gwh, 0)              AS nuclear_gwh,
       ROUND(100.0 * nuclear_share, 1)    AS nuclear_share_pct
FROM monthly_generation
WHERE year >= 2020
ORDER BY nuclear_share DESC
LIMIT 5;


-- Q6. Nuclear vs gas: how many months each year did nuclear generate more than gas?
SELECT year,
       SUM(CASE WHEN nuclear_gwh > gas_gwh THEN 1 ELSE 0 END) AS months_nuclear_beat_gas
FROM monthly_generation
GROUP BY year
HAVING COUNT(*) = 12
ORDER BY year;


-- Q7. Carbon intensity: average grid carbon intensity per year (gCO2/kWh).
--     Note: an average of monthly averages, which is close to but not exactly the true annual average.
SELECT year,
       ROUND(AVG(carbon_intensity_g_per_kwh), 0) AS avg_carbon_intensity
FROM monthly_generation
GROUP BY year
HAVING COUNT(*) = 12
ORDER BY year;
