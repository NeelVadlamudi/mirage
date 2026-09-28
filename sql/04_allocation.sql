/*
  Mirage allocation module: views.
  Target: SQL Server (T-SQL). Run after 03_allocation_schema.sql and the CSV loads.

  Order of decisions:
    1. v_store_sku_position   where each club stands today, in weeks of supply
    2. v_po_allocation        split the DC purchase order across clubs, whole cases only
    3. v_reallocation_moves   for anything still short, move cases from a long club to a short one
    4. v_store_sku_final      each club and SKU after the PO and the transfers
    5. v_store_performance    before and after, one row per club
*/

-- 1. Position: sales rate, counted units on hand, weeks of supply, and units needed to reach target.
--    On hand uses counted units (floor + backroom), not the system number, because the
--    rest of Mirage exists to show the system number is often wrong.
CREATE OR ALTER VIEW dbo.v_store_sku_position AS
WITH p AS (
    SELECT * FROM dbo.dim_alloc_params
),
sales AS (
    SELECT s.store_id, s.sku_id, SUM(s.units_sold) AS units_sold_window
    FROM dbo.fact_sales_daily AS s
    CROSS JOIN p
    WHERE s.sales_date BETWEEN p.sales_window_start AND p.as_of_date
    GROUP BY s.store_id, s.sku_id
),
inv AS (
    SELECT f.store_id, f.sku_id,
           CAST(f.floor_qty + f.backroom_qty AS INT) AS on_hand_units,
           CAST(f.system_on_hand_qty AS INT)         AS system_on_hand_units
    FROM dbo.fact_inventory_daily AS f
    CROSS JOIN p
    WHERE f.snapshot_date = p.as_of_date
),
base AS (
    SELECT inv.store_id, st.store_name, inv.sku_id, k.sku_name, k.category,
           pk.case_pack,
           COALESCE(sales.units_sold_window, 0) AS units_sold_window,
           7.0 * COALESCE(sales.units_sold_window, 0) / p.sales_window_days AS weekly_rate,
           inv.on_hand_units,
           inv.system_on_hand_units,
           p.target_wos
    FROM inv
    CROSS JOIN p
    JOIN dbo.dim_store    AS st ON st.store_id = inv.store_id
    JOIN dbo.dim_sku      AS k  ON k.sku_id    = inv.sku_id
    JOIN dbo.dim_sku_pack AS pk ON pk.sku_id   = inv.sku_id
    LEFT JOIN sales ON sales.store_id = inv.store_id AND sales.sku_id = inv.sku_id
    WHERE st.format_type = N'club' AND k.is_in_assortment = 1
)
SELECT store_id, store_name, sku_id, sku_name, category, case_pack,
       units_sold_window,
       weekly_rate,
       on_hand_units,
       system_on_hand_units,
       CASE WHEN weekly_rate = 0 THEN NULL
            ELSE on_hand_units / weekly_rate END AS wos,
       CAST(CASE WHEN CEILING(target_wos * weekly_rate) - on_hand_units > 0
                 THEN CEILING(target_wos * weekly_rate) - on_hand_units
                 ELSE 0 END AS INT) AS need_units
FROM base;
GO

-- 2. PO allocation. Each club's share of the PO is proportional to its need.
--    Cases shipped = the smaller of cases received and cases that cover total need.
--    Whole cases first (floor of each share), then leftover cases go to the clubs with the
--    largest remainders (largest remainder method). Ties go to the club with more need.
--    Anything not needed stays at the DC as a hold-back for the next call.
CREATE OR ALTER VIEW dbo.v_po_allocation AS
WITH lines AS (
    SELECT po.po_id, po.sku_id, po.cases_received,
           pos.store_id, pos.store_name, pos.case_pack, pos.need_units, pos.wos,
           SUM(pos.need_units) OVER (PARTITION BY po.po_id, po.sku_id) AS total_need
    FROM dbo.fact_dc_po AS po
    JOIN dbo.v_store_sku_position AS pos ON pos.sku_id = po.sku_id
),
ship AS (
    SELECT lines.*,
           CAST(CASE WHEN total_need = 0 THEN 0
                     WHEN cases_received < CEILING(1.0 * total_need / case_pack) THEN cases_received
                     ELSE CEILING(1.0 * total_need / case_pack) END AS INT) AS cases_to_ship
    FROM lines
),
split AS (
    SELECT ship.*,
           CAST(CASE WHEN total_need = 0 THEN 0
                     ELSE FLOOR(1.0 * cases_to_ship * need_units / total_need) END AS INT) AS base_cases,
           CASE WHEN total_need = 0 THEN 0
                ELSE (cases_to_ship * need_units) % total_need END AS share_remainder
    FROM ship
),
ranked AS (
    SELECT split.*,
           cases_to_ship - SUM(base_cases) OVER (PARTITION BY po_id, sku_id) AS leftover_cases,
           ROW_NUMBER() OVER (PARTITION BY po_id, sku_id
                              ORDER BY share_remainder DESC, need_units DESC, store_id) AS remainder_rank
    FROM split
)
SELECT po_id, sku_id, store_id, store_name, case_pack, cases_received, cases_to_ship,
       total_need, need_units, wos AS wos_before,
       base_cases + CASE WHEN remainder_rank <= leftover_cases THEN 1 ELSE 0 END AS cases_allocated,
       (base_cases + CASE WHEN remainder_rank <= leftover_cases THEN 1 ELSE 0 END) * case_pack AS units_allocated
FROM ranked;
GO

-- PO summary: what shipped and what the DC kept, per PO line.
CREATE OR ALTER VIEW dbo.v_po_summary AS
SELECT po_id, sku_id, MAX(case_pack) AS case_pack, MAX(cases_received) AS cases_received,
       SUM(cases_allocated) AS cases_allocated,
       MAX(cases_received) - SUM(cases_allocated) AS cases_held_at_dc,
       MAX(total_need) AS total_need_units,
       SUM(units_allocated) AS units_allocated
FROM dbo.v_po_allocation
GROUP BY po_id, sku_id;
GO

-- 3. Reallocation, after the PO lands. One move per SKU at most:
--    from the club with the most weeks of supply (above overstock_wos)
--    to the club with the fewest (below receiver_wos).
--    The giving club keeps donor_keep_wos. The move is whole cases, capped at the cases
--    that cover the receiver's gap to target, so a receiver can end up to one case over.
CREATE OR ALTER VIEW dbo.v_reallocation_moves AS
WITH p AS (
    SELECT * FROM dbo.dim_alloc_params
),
proj AS (
    SELECT pos.store_id, pos.store_name, pos.sku_id, pos.sku_name, pos.category, pos.case_pack,
           pos.weekly_rate,
           pos.on_hand_units + COALESCE(a.units_allocated, 0) AS projected_units
    FROM dbo.v_store_sku_position AS pos
    LEFT JOIN dbo.v_po_allocation AS a ON a.store_id = pos.store_id AND a.sku_id = pos.sku_id
),
projw AS (
    SELECT proj.*,
           CASE WHEN weekly_rate = 0 THEN NULL ELSE projected_units / weekly_rate END AS projected_wos
    FROM proj
),
donors AS (
    SELECT projw.*,
           projected_units - CAST(CEILING(p.donor_keep_wos * weekly_rate) AS INT) AS spare_units,
           ROW_NUMBER() OVER (PARTITION BY sku_id
                              ORDER BY CASE WHEN weekly_rate = 0 THEN 1 ELSE 0 END DESC,
                                       projected_wos DESC, store_id) AS donor_rank
    FROM projw
    CROSS JOIN p
    WHERE projected_units > 0
      AND (weekly_rate = 0 OR projected_wos > p.overstock_wos)
),
receivers AS (
    SELECT projw.*,
           CAST(CEILING(p.target_wos * weekly_rate) AS INT) - projected_units AS gap_units,
           ROW_NUMBER() OVER (PARTITION BY sku_id ORDER BY projected_wos, store_id) AS receiver_rank
    FROM projw
    CROSS JOIN p
    WHERE weekly_rate > 0 AND projected_wos < p.receiver_wos
),
pairs AS (
    SELECT d.sku_id, d.sku_name, d.category, d.case_pack,
           d.store_id AS from_store_id, d.store_name AS from_store,
           r.store_id AS to_store_id,   r.store_name AS to_store,
           d.projected_units AS from_units_before, d.weekly_rate AS from_weekly_rate,
           r.projected_units AS to_units_before,   r.weekly_rate AS to_weekly_rate,
           CAST(FLOOR(1.0 * d.spare_units / d.case_pack) AS INT)  AS spare_cases,
           CAST(CEILING(1.0 * r.gap_units / d.case_pack) AS INT)  AS gap_cases
    FROM donors AS d
    JOIN receivers AS r ON r.sku_id = d.sku_id AND r.receiver_rank = 1
    WHERE d.donor_rank = 1 AND d.store_id <> r.store_id
),
moves AS (
    SELECT pairs.*,
           CASE WHEN spare_cases < gap_cases THEN spare_cases ELSE gap_cases END AS cases_moved
    FROM pairs
)
SELECT sku_id, sku_name, category, case_pack,
       from_store_id, from_store, to_store_id, to_store,
       cases_moved,
       cases_moved * case_pack AS units_moved,
       CASE WHEN from_weekly_rate = 0 THEN NULL ELSE from_units_before / from_weekly_rate END AS from_wos_before,
       CASE WHEN from_weekly_rate = 0 THEN NULL
            ELSE (from_units_before - cases_moved * case_pack) / from_weekly_rate END AS from_wos_after,
       to_units_before / to_weekly_rate AS to_wos_before,
       (to_units_before + cases_moved * case_pack) / to_weekly_rate AS to_wos_after
FROM moves
WHERE cases_moved >= 1;
GO

-- 4. Final position per club and SKU after the PO and transfers.
CREATE OR ALTER VIEW dbo.v_store_sku_final AS
SELECT pos.store_id, pos.store_name, pos.sku_id, pos.sku_name, pos.category,
       pos.weekly_rate, pos.on_hand_units, pos.wos AS wos_before,
       COALESCE(a.units_allocated, 0) AS po_units_in,
       COALESCE(tin.units_moved, 0)   AS transfer_units_in,
       COALESCE(tout.units_moved, 0)  AS transfer_units_out,
       pos.on_hand_units + COALESCE(a.units_allocated, 0)
         + COALESCE(tin.units_moved, 0) - COALESCE(tout.units_moved, 0) AS units_after,
       CASE WHEN pos.weekly_rate = 0 THEN NULL
            ELSE (pos.on_hand_units + COALESCE(a.units_allocated, 0)
                  + COALESCE(tin.units_moved, 0) - COALESCE(tout.units_moved, 0)) / pos.weekly_rate
       END AS wos_after
FROM dbo.v_store_sku_position AS pos
LEFT JOIN dbo.v_po_allocation      AS a    ON a.store_id = pos.store_id AND a.sku_id = pos.sku_id
LEFT JOIN dbo.v_reallocation_moves AS tin  ON tin.to_store_id = pos.store_id AND tin.sku_id = pos.sku_id
LEFT JOIN dbo.v_reallocation_moves AS tout ON tout.from_store_id = pos.store_id AND tout.sku_id = pos.sku_id;
GO

-- 5. Club scorecard: sell-through over the window and weeks-of-supply counts before and after.
--    Sell-through = units sold / (units sold + units on hand at the end of the window).
CREATE OR ALTER VIEW dbo.v_store_performance AS
SELECT f.store_id, f.store_name,
       COUNT(*) AS sku_count,
       SUM(pos.units_sold_window) AS units_sold_window,
       SUM(f.on_hand_units) AS on_hand_units_before,
       CAST(1.0 * SUM(pos.units_sold_window)
            / NULLIF(SUM(pos.units_sold_window) + SUM(f.on_hand_units), 0) AS DECIMAL(9,4)) AS sell_through,
       SUM(CASE WHEN f.wos_before < 1 THEN 1 ELSE 0 END) AS skus_under_1_wos_before,
       SUM(CASE WHEN f.wos_after  < 1 THEN 1 ELSE 0 END) AS skus_under_1_wos_after,
       SUM(CASE WHEN f.wos_before > 4 THEN 1 ELSE 0 END) AS skus_over_4_wos_before,
       SUM(CASE WHEN f.wos_after  > 4 THEN 1 ELSE 0 END) AS skus_over_4_wos_after
FROM dbo.v_store_sku_final AS f
JOIN dbo.v_store_sku_position AS pos ON pos.store_id = f.store_id AND pos.sku_id = f.sku_id
GROUP BY f.store_id, f.store_name;
GO
