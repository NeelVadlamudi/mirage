# Mirage — Tableau Public build

Use the extracts below in Tableau Public / Desktop, then publish when ready.

## Connect

Folder: `data/tableau/`

| Extract | Use |
| --- | --- |
| `v_store_day_kpis.csv` | Three tiles (filter to latest date + selected club chip) |
| `v_inventory_flags.csv` | Exception list + shelf pull + **action_label** |
| `v_gaps_by_category.csv` | Gaps by aisle bars |
| `v_gap_rate_trend.csv` | Gap rate sparkline |
| `v_map_pins.csv` | Map pins (lat/lon); warehouse_4 pin_role = supply pin only |

Relationships: `store_id` (+ `snapshot_date` where needed).

## Dashboard layout

1. **Chips** — filter on `chip_label` (`warehouse_1` / `warehouse_2` / `warehouse_3`). warehouse_4 is DC / supply pin — not a floor KPI chip.
2. **Gap rate** — `gap_rate` from KPIs; show `gap_ceiling` (15%); subtitle `gap_sku_count of assortment_sku_count`.
3. **Phantom SKUs** — `phantom_sku_count` → action: recount / system fix.
4. **Backroom rescue** — `backroom_rescue_sku_count` → action: floor pull from backroom.
5. **Gaps by aisle** — bar on `v_gaps_by_category`.
6. **Open exceptions** — rows where `is_shelf_gap = 1`; icons from `is_phantom` / `is_backroom_rescue`; columns SKU, category, book (`system_on_hand_qty`), backroom, **action_label**.
7. **Shelf pull** — selected exception with `is_backroom_rescue = 1` (default Bottled Water on warehouse_1 when present).
8. **Map** — Tableau map on `v_map_pins` lat/lon; warehouse_4 labeled **supply pin only — no floor KPIs**.

### Action labels (from `action_label`)

| Condition | action_label |
| --- | --- |
| Rescue + phantom | Floor pull · recount |
| Rescue only | Floor pull from backroom |
| Phantom only | Recount / system fix |
| Pure gap (no backroom, no book) | Replenish / order |

## warehouse_1 check (2026-09-22)

Gap rate **22.5%** (9 of 40), phantom **7**, rescue **6**.

## Sample scale

3 clubs + 1 DC, 40 SKUs, check window 2026-09-09 → 2026-09-22.

## Live preview without Tableau

Open the Pages board: `docs/index.html` (same grain, same numbers). Replace with a Tableau Public link in the README when published.
