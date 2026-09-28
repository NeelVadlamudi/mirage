/*
  Mirage maintenance module: schema. warehouse_4 (the DC) equipment, work orders, volume, energy.
  Target: SQL Server (T-SQL). Run after 00-04. Everything here is synthetic.
  Work orders follow the usual CMMS layout: work type (PM / CM) and problem, cause, remedy codes.
*/

IF OBJECT_ID('dbo.fact_workorder', 'U') IS NOT NULL DROP TABLE dbo.fact_workorder;
IF OBJECT_ID('dbo.dim_asset', 'U') IS NOT NULL DROP TABLE dbo.dim_asset;
IF OBJECT_ID('dbo.fact_dc_volume_weekly', 'U') IS NOT NULL DROP TABLE dbo.fact_dc_volume_weekly;
IF OBJECT_ID('dbo.fact_utility_monthly', 'U') IS NOT NULL DROP TABLE dbo.fact_utility_monthly;
IF OBJECT_ID('dbo.dim_maint_params', 'U') IS NOT NULL DROP TABLE dbo.dim_maint_params;

CREATE TABLE dbo.dim_asset (
    asset_id          NVARCHAR(12) NOT NULL PRIMARY KEY,
    site_id           INT          NOT NULL REFERENCES dbo.dim_store (store_id),
    asset_type        NVARCHAR(40) NOT NULL,
    install_year      INT          NOT NULL,
    criticality       INT          NOT NULL,   -- 1 = stops the building, 3 = can wait
    pm_interval_days  INT          NOT NULL,
    pm_skip_prob      DECIMAL(4,2) NOT NULL    -- generator setting, kept for transparency; no view reads it
);

CREATE TABLE dbo.fact_workorder (
    wo_id           NVARCHAR(12)  NOT NULL PRIMARY KEY,
    asset_id        NVARCHAR(12)  NOT NULL REFERENCES dbo.dim_asset (asset_id),
    work_type       NVARCHAR(4)   NOT NULL,   -- PM preventive, CM corrective
    scheduled_date  DATE          NULL,       -- PM only
    reported_date   DATE          NOT NULL,
    completed_date  DATE          NULL,
    pm_status       NVARCHAR(10)  NULL,       -- ON TIME / LATE / SKIPPED / OPEN, PM only
    problem_code    NVARCHAR(20)  NULL,
    cause_code      NVARCHAR(20)  NULL,
    remedy_code     NVARCHAR(20)  NULL,
    downtime_hours  DECIMAL(6,1)  NOT NULL,
    labor_hours     DECIMAL(6,2)  NOT NULL,
    parts_cost      DECIMAL(10,2) NOT NULL
);

CREATE TABLE dbo.fact_dc_volume_weekly (
    week_start     DATE NOT NULL PRIMARY KEY,
    site_id        INT  NOT NULL,
    cases_shipped  INT  NOT NULL
);

CREATE TABLE dbo.fact_utility_monthly (
    month_start    DATE NOT NULL PRIMARY KEY,
    site_id        INT  NOT NULL,
    kwh            INT  NOT NULL,
    cases_shipped  INT  NOT NULL
);

CREATE TABLE dbo.dim_maint_params (
    as_of_date               DATE          NOT NULL,
    wo_window_start          DATE          NOT NULL,
    pm_followup_days         INT           NOT NULL,  -- window after a PM to look for a breakdown
    picker_cases_per_hour    INT           NOT NULL,  -- cases one order picker moves per operating hour
    truck_hours_per_week     INT           NOT NULL,  -- hours one truck can run per week
    forecast_start           DATE          NOT NULL,
    forecast_weeks           INT           NOT NULL,
    trend_weeks              INT           NOT NULL,  -- recent weeks used to measure growth vs last year
    led_done_date            DATE          NOT NULL,
    led_project_cost         DECIMAL(12,2) NOT NULL,
    usd_per_kwh              DECIMAL(6,3)  NOT NULL,
    labor_usd_per_hour       DECIMAL(8,2)  NOT NULL,
    operating_hours_per_day  INT           NOT NULL
);

/*
  Load data/maint/*.csv into the matching tables (BULK INSERT or Import Flat File).
  Empty strings in scheduled_date, completed_date, pm_status and the codes load as NULL.
*/
