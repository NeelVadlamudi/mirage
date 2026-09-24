/*
  Mirage — pass 1 metrics
  Grain in: store × SKU × day
  Grain out: store × day (KPIs) + detail flags for the rescue / phantom lists
*/

-- Detail flags (feeds Tableau detail sheets)
CREATE OR ALTER VIEW dbo.v_inventory_flags AS
SELECT
    f.snapshot_date,
    f.store_id,
    s.store_name,
    s.region,
    s.city,
    s.lat,
    s.lon,
    s.map_label,
    s.format_type,
    s.chip_label,
    f.sku_id,
    k.sku_name,
    k.category,
    k.subcategory,
    k.is_in_assortment,
    f.floor_qty,
    f.backroom_qty,
    f.system_on_hand_qty,
    CAST(CASE
        WHEN k.is_in_assortment = 1 AND f.floor_qty = 0 THEN 1 ELSE 0
    END AS BIT) AS is_shelf_gap,
    CAST(CASE
        WHEN f.floor_qty = 0 AND f.system_on_hand_qty > 0 THEN 1 ELSE 0
    END AS BIT) AS is_phantom,
    CAST(CASE
        WHEN f.floor_qty = 0 AND f.backroom_qty > 0 THEN 1 ELSE 0
    END AS BIT) AS is_backroom_rescue,
    CASE
        WHEN f.floor_qty = 0 AND f.backroom_qty > 0 AND f.system_on_hand_qty > 0
            THEN N'Floor pull · recount'
        WHEN f.floor_qty = 0 AND f.backroom_qty > 0
            THEN N'Floor pull from backroom'
        WHEN f.floor_qty = 0 AND f.system_on_hand_qty > 0
            THEN N'Recount / system fix'
        WHEN k.is_in_assortment = 1 AND f.floor_qty = 0
            THEN N'Replenish / order'
        ELSE N''
    END AS action_label,
    CAST(CASE
        WHEN (f.floor_qty + f.backroom_qty) = 0 THEN NULL
        ELSE f.floor_qty / (f.floor_qty + f.backroom_qty)
    END AS DECIMAL(9, 4)) AS floor_share,
    CAST(CASE
        WHEN (f.floor_qty + f.backroom_qty) = 0 THEN NULL
        ELSE f.backroom_qty / (f.floor_qty + f.backroom_qty)
    END AS DECIMAL(9, 4)) AS backroom_share
FROM dbo.fact_inventory_daily AS f
JOIN dbo.dim_store AS s ON s.store_id = f.store_id
JOIN dbo.dim_sku   AS k ON k.sku_id   = f.sku_id;
GO

-- Glance KPIs: store × day
CREATE OR ALTER VIEW dbo.v_store_day_kpis AS
SELECT
    snapshot_date,
    store_id,
    store_name,
    region,
    COUNT(*) AS assortment_sku_count,
    SUM(CASE WHEN is_shelf_gap = 1 THEN 1 ELSE 0 END) AS gap_sku_count,
    CAST(
        1.0 * SUM(CASE WHEN is_shelf_gap = 1 THEN 1 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN is_in_assortment = 1 THEN 1 ELSE 0 END), 0)
        AS DECIMAL(9, 4)
    ) AS gap_rate,
    SUM(CASE WHEN is_phantom = 1 THEN 1 ELSE 0 END) AS phantom_sku_count,
    SUM(CASE WHEN is_backroom_rescue = 1 THEN 1 ELSE 0 END) AS backroom_rescue_sku_count,
    SUM(floor_qty) AS floor_units,
    SUM(backroom_qty) AS backroom_units,
    CAST(
        SUM(floor_qty) / NULLIF(SUM(floor_qty) + SUM(backroom_qty), 0)
        AS DECIMAL(9, 4)
    ) AS floor_share_units
FROM dbo.v_inventory_flags
WHERE is_in_assortment = 1
GROUP BY snapshot_date, store_id, store_name, region;
GO


-- Map pins (real building coords). warehouse_4 = supply pin only — no floor KPIs; clubs drive floor KPIs.
CREATE OR ALTER VIEW dbo.v_map_pins AS
SELECT
    store_id,
    store_name,
    region,
    format_type,
    city,
    lat,
    lon,
    map_label,
    chip_label
FROM dbo.dim_store;
GO
