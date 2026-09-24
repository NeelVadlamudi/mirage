# Mirage

Empty shelf. Full backroom. Phantom inventory.

**Purpose:** Show where the club floor is empty, and whether the next step is a recount, a backroom pull, or a replenish/order.

## Honesty first

- Inventory, SKUs, and day metrics are **synthetic**.
- Map pins use **real publicly listed warehouse addresses** (lat/long) only so the Massachusetts map looks real.
- This demo is **not affiliated** with Costco, BJ’s, or Sam’s Club.
- Public CSVs use `warehouse_N` labels and street addresses only — no retailer brand on chips or store display fields.

**Sample scale:** 3 clubs + 1 DC, 40 SKUs, check window 2026-09-09 → 2026-09-22 (14 days). Locked check day: **2026-09-22**.

## Metrics (plain English)

| Metric | Meaning | Next step when flagged |
| --- | --- | --- |
| **Gap rate** | Share of assortment with floor qty = 0 | Dig into exception type |
| **Phantom SKUs** | Floor empty, system still shows on-hand | Recount / system fix |
| **Backroom rescue** | Floor empty, backroom > 0 | Floor pull from backroom |
| **Pure gap** | Floor empty, no backroom, no book | Replenish / order |

Formulas and talk tracks: [`docs/metrics.md`](docs/metrics.md).

## Locked check — warehouse_1 · 2026-09-22

| KPI | Value |
| --- | --- |
| Gap rate | **22.5%** (9 of 40) |
| Phantom SKUs | **7** |
| Backroom rescue | **6** |

Prove it without SQL Server:

```bash
python3 scripts/verify_kpis.py
```

Expected: `ALL PASS — warehouse_1 @ 2026-09-22: 22.5% / 7 / 6`

## Folder map

| Path | What |
| --- | --- |
| `sql/` | T-SQL schema, seed, KPI views |
| `data/` | `dim_*` + `fact_inventory_daily.csv` |
| `data/tableau/` | Extracts for Tableau Public / Desktop |
| `docs/` | Metrics, map pins, Tableau build notes |
| `docs/index.html` | Interactive gap board (GitHub Pages) |
| `docs/board_data.json` | Board payload (same grain as extracts) |
| `docs/screenshots/` | Desktop / tablet captures |
| `scripts/verify_kpis.py` | Stdlib KPI lock checker |
| `INSTALL.md` | Step-by-step install + proof commands |

## How to open the board

**Local:** open [`docs/index.html`](docs/index.html) in a browser (serve the folder if `fetch` is blocked by `file://`):

```bash
cd docs && python3 -m http.server 8080
# then visit http://localhost:8080/
```

**GitHub Pages:** Settings → Pages → Deploy from branch → folder **`/docs`**.  
The board is interactive: club chips, KPI tiles, exception list, action labels, shelf-pull panel, warehouse_4 supply pin.

Chips: `warehouse_1` (Everett), `warehouse_2` (Dedham), `warehouse_3` (Waltham).  
`warehouse_4` (Avon) is a **supply pin only — no floor KPIs**.

## How to run SQL

1. Install SQL Server Developer (or Azure SQL) + Azure Data Studio / SSMS.
2. Create an empty database (e.g. `mirage`).
3. Run in order:
   - `sql/00_schema.sql`
   - `sql/01_seed.sql`
   - `sql/02_metrics.sql`
4. Spot-check:

```sql
SELECT gap_rate, gap_sku_count, phantom_sku_count, backroom_rescue_sku_count
FROM dbo.v_store_day_kpis
WHERE store_name = N'warehouse_1' AND snapshot_date = '2026-09-22';
-- expect 0.2250, 9, 7, 6
```

Full installer proof path: [`INSTALL.md`](INSTALL.md).

## How to point Tableau at extracts

1. Tableau Public or Desktop → connect to Text file.
2. Open each CSV under `data/tableau/` (see [`docs/tableau-build.md`](docs/tableau-build.md)).
3. Relate on `store_id` (+ `snapshot_date` where needed).
4. Build chips → tiles → exception queue → map. Match the board layout.

## Screenshots

| Capture | File |
| --- | --- |
| House UI · desktop 1440 | [`docs/screenshots/desktop_1440_house_ui.png`](docs/screenshots/desktop_1440_house_ui.png) |
| House UI · tablet 1024 | [`docs/screenshots/tablet_1024_house_ui.png`](docs/screenshots/tablet_1024_house_ui.png) |

Captions: warehouse_1 open queue on 2026-09-22 — gap **22.5%**, phantom **7**, rescue **6**, action labels on each row.  
Interactive Pages board (`docs/index.html`) ships the polished data shell; additional house chrome may arrive in a later pass.

## Map pins

See [`docs/map-pins-ma.md`](docs/map-pins-ma.md). Public labels are `warehouse_1`…`warehouse_4` with city, street, and lat/lon only.

## Troubleshooting

| Issue | Fix |
| --- | --- |
| Board blank / `fetch` fails on `file://` | Serve `docs/` with `python3 -m http.server` |
| `verify_kpis.py` FAIL on gap_rate | Confirm you did not edit `data/tableau/v_store_day_kpis.csv` |
| Tableau map empty | Use `v_map_pins.csv` lat/lon; set geographic roles |
| warehouse_4 shows no KPIs | Expected — supply pin only; select warehouse_1–3 |
| SQL seed fails on FK | Run `00_schema` → `01_seed` → `02_metrics` on a fresh DB |
| Pages 404 | Repo Settings → Pages → source branch, folder `/docs` |

## License

MIT — Copyright (c) 2026 Neel Vittal Bharath Vadlamudi. See [`LICENSE`](LICENSE).
