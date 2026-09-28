/*
  Mirage maintenance module: views. Target: SQL Server (T-SQL).

    v_asset_reliability     one row per asset: breakdowns, MTBF, MTTR, PM compliance, cost, availability
    v_pm_followup           breakdown rate in the 30 days after an on-time PM vs a missed or late one
    v_pm_missed_cost        what the extra breakdowns after missed PMs cost
    v_failure_patterns      breakdowns per asset by type, age band and problem code
    v_fleet_need_forecast   order pickers needed each week of the next 13, vs the fleet on hand
    v_utility_baseline      energy baseline from pre-retrofit months, savings after the LED retrofit
    v_utility_roi           annual savings, payback and ROI for the retrofit
*/

-- Asset reliability over the work order window.
CREATE OR ALTER VIEW dbo.v_asset_reliability AS
WITH p AS (SELECT * FROM dbo.dim_maint_params),
wo AS (
    SELECT w.*
    FROM dbo.fact_workorder AS w
    CROSS JOIN p
    WHERE w.reported_date BETWEEN p.wo_window_start AND p.as_of_date
),
agg AS (
    SELECT a.asset_id, a.asset_type, a.install_year, a.criticality,
           SUM(CASE WHEN wo.work_type = 'CM' THEN 1 ELSE 0 END) AS cm_count,
           SUM(CASE WHEN wo.work_type = 'CM' THEN wo.downtime_hours ELSE 0 END) AS cm_downtime_hours,
           SUM(COALESCE(wo.downtime_hours, 0)) AS total_downtime_hours,
           SUM(CASE WHEN wo.work_type = 'PM' AND wo.pm_status <> 'OPEN' THEN 1 ELSE 0 END) AS pm_due,
           SUM(CASE WHEN wo.work_type = 'PM' AND wo.pm_status = 'ON TIME' THEN 1 ELSE 0 END) AS pm_on_time,
           SUM(COALESCE(wo.parts_cost, 0) + COALESCE(wo.labor_hours, 0) * p.labor_usd_per_hour) AS maint_cost_usd
    FROM dbo.dim_asset AS a
    CROSS JOIN p
    LEFT JOIN wo ON wo.asset_id = a.asset_id
    GROUP BY a.asset_id, a.asset_type, a.install_year, a.criticality
)
SELECT agg.*,
       YEAR(p.as_of_date) - agg.install_year AS age_years,
       CASE WHEN cm_count = 0 THEN NULL
            ELSE 1.0 * (DATEDIFF(day, p.wo_window_start, p.as_of_date) + 1) / cm_count END AS mtbf_days,
       CASE WHEN cm_count = 0 THEN NULL ELSE 1.0 * cm_downtime_hours / cm_count END AS mttr_hours,
       CASE WHEN pm_due = 0 THEN NULL ELSE 1.0 * pm_on_time / pm_due END AS pm_compliance,
       1.0 - 1.0 * total_downtime_hours
             / ((DATEDIFF(day, p.wo_window_start, p.as_of_date) + 1) * p.operating_hours_per_day) AS availability
FROM agg
CROSS JOIN p;
GO

-- Did a breakdown follow within 30 days of each PM? Grouped by whether the PM was on time.
-- Only PMs whose 30-day follow-up window closes inside the data count.
CREATE OR ALTER VIEW dbo.v_pm_followup AS
WITH p AS (SELECT * FROM dbo.dim_maint_params),
pm AS (
    SELECT w.wo_id, w.asset_id, w.scheduled_date,
           CASE WHEN w.pm_status = 'ON TIME' THEN 'ON TIME' ELSE 'MISSED OR LATE' END AS pm_group
    FROM dbo.fact_workorder AS w
    CROSS JOIN p
    WHERE w.work_type = 'PM' AND w.pm_status IN ('ON TIME', 'LATE', 'SKIPPED')
      AND w.scheduled_date >= p.wo_window_start
      AND DATEADD(day, p.pm_followup_days, w.scheduled_date) <= p.as_of_date
),
flag AS (
    SELECT pm.pm_group, pm.wo_id,
           CASE WHEN EXISTS (
                SELECT 1 FROM dbo.fact_workorder AS c
                WHERE c.asset_id = pm.asset_id AND c.work_type = 'CM'
                  AND c.reported_date >  pm.scheduled_date
                  AND c.reported_date <= DATEADD(day, p.pm_followup_days, pm.scheduled_date)
           ) THEN 1 ELSE 0 END AS had_breakdown
    FROM pm
    CROSS JOIN p
)
SELECT pm_group,
       COUNT(*) AS pm_count,
       SUM(had_breakdown) AS followed_by_breakdown,
       1.0 * SUM(had_breakdown) / COUNT(*) AS breakdown_rate
FROM flag
GROUP BY pm_group;
GO

-- Extra breakdowns after missed PMs = missed PMs x (missed rate - on-time rate).
-- Cost of one breakdown = average CM parts + labor. Downtime hours carried alongside.
CREATE OR ALTER VIEW dbo.v_pm_missed_cost AS
WITH p AS (SELECT * FROM dbo.dim_maint_params),
r AS (
    SELECT MAX(CASE WHEN pm_group = 'ON TIME' THEN breakdown_rate END) AS rate_on_time,
           MAX(CASE WHEN pm_group = 'MISSED OR LATE' THEN breakdown_rate END) AS rate_missed,
           MAX(CASE WHEN pm_group = 'MISSED OR LATE' THEN pm_count END) AS missed_pm_count
    FROM dbo.v_pm_followup
),
cm AS (
    SELECT AVG(w.parts_cost + w.labor_hours * p.labor_usd_per_hour) AS avg_cm_cost_usd,
           AVG(1.0 * w.downtime_hours) AS avg_cm_downtime_hours
    FROM dbo.fact_workorder AS w
    CROSS JOIN p
    WHERE w.work_type = 'CM' AND w.reported_date BETWEEN p.wo_window_start AND p.as_of_date
)
SELECT r.rate_on_time, r.rate_missed, r.rate_missed / r.rate_on_time AS rate_ratio,
       r.missed_pm_count,
       r.missed_pm_count * (r.rate_missed - r.rate_on_time) AS extra_breakdowns,
       cm.avg_cm_cost_usd, cm.avg_cm_downtime_hours,
       r.missed_pm_count * (r.rate_missed - r.rate_on_time) * cm.avg_cm_cost_usd AS extra_cost_usd,
       r.missed_pm_count * (r.rate_missed - r.rate_on_time) * cm.avg_cm_downtime_hours AS extra_downtime_hours
FROM r CROSS JOIN cm;
GO

-- Breakdowns per asset by type, age band and problem code.
CREATE OR ALTER VIEW dbo.v_failure_patterns AS
WITH p AS (SELECT * FROM dbo.dim_maint_params),
a AS (
    SELECT asset_id, asset_type,
           CASE WHEN YEAR(p.as_of_date) - install_year >= 6 THEN '6+ years' ELSE 'under 6 years' END AS age_band
    FROM dbo.dim_asset CROSS JOIN p
),
fleet AS (
    SELECT asset_type, age_band, COUNT(*) AS asset_count FROM a GROUP BY asset_type, age_band
),
cm AS (
    SELECT a.asset_type, a.age_band, w.problem_code,
           COUNT(*) AS cm_count, SUM(w.downtime_hours) AS downtime_hours
    FROM dbo.fact_workorder AS w
    JOIN a ON a.asset_id = w.asset_id
    CROSS JOIN p
    WHERE w.work_type = 'CM' AND w.reported_date BETWEEN p.wo_window_start AND p.as_of_date
    GROUP BY a.asset_type, a.age_band, w.problem_code
)
SELECT cm.asset_type, cm.age_band, cm.problem_code, fleet.asset_count,
       cm.cm_count, cm.downtime_hours,
       1.0 * cm.cm_count / fleet.asset_count AS cm_per_asset
FROM cm
JOIN fleet ON fleet.asset_type = cm.asset_type AND fleet.age_band = cm.age_band;
GO

-- Order pickers needed per week for the next 13 weeks.
-- Forecast = same week last year x growth, where growth = last 13 weeks vs the same 13 weeks a year earlier.
-- Trucks needed = forecast cases / cases per truck-hour / (hours per truck-week x fleet availability).
CREATE OR ALTER VIEW dbo.v_fleet_need_forecast AS
WITH p AS (SELECT * FROM dbo.dim_maint_params),
recent AS (
    SELECT SUM(CASE WHEN v.week_start >= DATEADD(day, -7 * p.trend_weeks, p.as_of_date)
                     AND v.week_start <  p.as_of_date
                    THEN v.cases_shipped ELSE 0 END) AS cases_recent,
           SUM(CASE WHEN v.week_start >= DATEADD(day, -7 * p.trend_weeks - 364, p.as_of_date)
                     AND v.week_start <  DATEADD(day, -364, p.as_of_date)
                    THEN v.cases_shipped ELSE 0 END) AS cases_year_ago
    FROM dbo.fact_dc_volume_weekly AS v
    CROSS JOIN p
),
fleet AS (
    SELECT COUNT(*) AS picker_count, AVG(availability) AS picker_availability
    FROM dbo.v_asset_reliability
    WHERE asset_type = 'Order Picker'
),
ly AS (
    SELECT DATEADD(day, 364, v.week_start) AS forecast_week, v.cases_shipped AS cases_last_year
    FROM dbo.fact_dc_volume_weekly AS v
    CROSS JOIN p
    WHERE DATEADD(day, 364, v.week_start) >= p.forecast_start
      AND DATEADD(day, 364, v.week_start) <  DATEADD(day, 7 * p.forecast_weeks, p.forecast_start)
),
f AS (
    SELECT ly.forecast_week, ly.cases_last_year,
           1.0 * recent.cases_recent / recent.cases_year_ago AS growth,
           ly.cases_last_year * (1.0 * recent.cases_recent / recent.cases_year_ago) AS forecast_cases,
           fleet.picker_count, fleet.picker_availability,
           p.picker_cases_per_hour, p.truck_hours_per_week
    FROM ly CROSS JOIN recent CROSS JOIN fleet CROSS JOIN p
)
SELECT forecast_week, cases_last_year, growth, forecast_cases,
       forecast_cases / picker_cases_per_hour AS truck_hours_needed,
       CAST(CEILING(forecast_cases / picker_cases_per_hour
                    / (truck_hours_per_week * picker_availability)) AS INT) AS pickers_needed,
       picker_count,
       CASE WHEN CEILING(forecast_cases / picker_cases_per_hour / (truck_hours_per_week * picker_availability)) > picker_count
            THEN CAST(CEILING(forecast_cases / picker_cases_per_hour / (truck_hours_per_week * picker_availability)) AS INT) - picker_count
            ELSE 0 END AS pickers_short
FROM f;
GO

-- Energy baseline: fit kWh = a + b x cases on the months before the LED retrofit (least squares),
-- then predict what each later month would have used without it. Savings = predicted - actual.
CREATE OR ALTER VIEW dbo.v_utility_baseline AS
WITH p AS (SELECT * FROM dbo.dim_maint_params),
pre AS (
    SELECT CAST(u.cases_shipped AS DOUBLE PRECISION) AS x, CAST(u.kwh AS DOUBLE PRECISION) AS y
    FROM dbo.fact_utility_monthly AS u CROSS JOIN p
    WHERE u.month_start <= p.led_done_date
),
fit AS (
    SELECT (COUNT(*) * SUM(x * y) - SUM(x) * SUM(y)) / (COUNT(*) * SUM(x * x) - SUM(x) * SUM(x)) AS slope,
           AVG(y) AS mean_y, AVG(x) AS mean_x, COUNT(*) AS pre_months
    FROM pre
)
SELECT u.month_start, u.cases_shipped, u.kwh,
       CASE WHEN u.month_start <= p.led_done_date THEN 'BEFORE' ELSE 'AFTER' END AS period,
       fit.mean_y + fit.slope * (u.cases_shipped - fit.mean_x) AS baseline_kwh,
       fit.mean_y + fit.slope * (u.cases_shipped - fit.mean_x) - u.kwh AS savings_kwh,
       (fit.mean_y + fit.slope * (u.cases_shipped - fit.mean_x) - u.kwh) * p.usd_per_kwh AS savings_usd,
       fit.slope AS kwh_per_case, fit.pre_months
FROM dbo.fact_utility_monthly AS u
CROSS JOIN fit
CROSS JOIN p;
GO

CREATE OR ALTER VIEW dbo.v_utility_roi AS
WITH p AS (SELECT * FROM dbo.dim_maint_params),
post AS (
    SELECT COUNT(*) AS post_months, SUM(savings_kwh) AS savings_kwh, SUM(savings_usd) AS savings_usd,
           SUM(baseline_kwh) AS baseline_kwh
    FROM dbo.v_utility_baseline WHERE period = 'AFTER'
)
SELECT post.post_months, post.savings_kwh, post.savings_usd,
       post.savings_kwh / post.baseline_kwh AS savings_share,
       12.0 * post.savings_usd / post.post_months AS annual_savings_usd,
       p.led_project_cost,
       p.led_project_cost / (post.savings_usd / post.post_months) AS payback_months,
       (12.0 * post.savings_usd / post.post_months) / p.led_project_cost AS simple_annual_roi
FROM post CROSS JOIN p;
GO
