# Mirage

Empty shelf. Full backroom. Phantom inventory.

I built this so a floor lead can see which empty shelves are a recount, which are a backroom pull, and which need a real order. Then, when a PO lands at the DC, how many whole cases go to each club, and whether one club should ship to another.

## What this is (and isn't)

Synthetic data for a portfolio demo. Pins mark town centers, not stores. Not affiliated with any retailer. Public files use `warehouse_1`…`warehouse_4` only.

## Gap board

| Metric | What it means | What to do |
| --- | --- | --- |
| **Gap rate** | Share of assortment with floor qty = 0 | Open the exception list |
| **Phantom SKUs** | Floor empty, system still shows on-hand | Recount / fix the book |
| **Backroom rescue** | Floor empty, backroom has stock | Pull to the floor |
| **Pure gap** | Floor empty, no backroom, book is zero | Replenish / order |

More detail: [`docs/metrics.md`](docs/metrics.md).

### Locked check — warehouse_1 · 2026-09-22

| KPI | Value |
| --- | --- |
| Gap rate | **22.5%** (9 of 40) |
| Phantom SKUs | **7** |
| Backroom rescue | **6** |

```bash
python3 scripts/verify_kpis.py
```

You should see: `ALL PASS — warehouse_1 @ 2026-09-22: 22.5% / 7 / 6`

## Allocation (PO split + one transfer)

PO-26092201 hits warehouse_4 with **98** cases. The plan ships **60** to the three clubs in whole cases, keeps **38** at the DC (nobody needs them), and runs **one** club-to-club move when one club is under 1 week of supply and another is over 4 on the same item. Club-SKUs under 1 week go from **40 → 32**.

Why need beats sales share, what largest remainder means, why counted units (not the system book), and why only one transfer: [`docs/allocation.md`](docs/allocation.md). Read that before you interview on this.

```bash
python3 scripts/verify_allocation.py
```

Last line should be: `ALL PASS - PO 98 cases: 60 allocated, 38 held at DC; 1 transfer(s); club-SKUs under 1 week of supply 40 -> 32`

T-SQL: `sql/03_allocation_schema.sql`, `sql/04_allocation.sql`.

## Open the board

```bash
cd docs && python3 -m http.server 8080
# http://localhost:8080/
```

GitHub Pages: Settings → Pages → branch, folder **`/docs`**.

Clubs: `warehouse_1` (Everett), `warehouse_2` (Dedham), `warehouse_3` (Waltham).  
`warehouse_4` (Avon) is supply only. No floor KPIs there.

## Run the SQL

1. SQL Server Developer (or Azure SQL) + Azure Data Studio / SSMS.
2. Empty database, e.g. `mirage`.
3. Run in order: `sql/00_schema.sql` → `01_seed.sql` → `02_metrics.sql` → (optional) `03_allocation_schema.sql` → `04_allocation.sql`.

```sql
SELECT gap_rate, gap_sku_count, phantom_sku_count, backroom_rescue_sku_count
FROM dbo.v_store_day_kpis
WHERE store_name = N'warehouse_1' AND snapshot_date = '2026-09-22';
-- expect 0.2250, 9, 7, 6
```

Step-by-step proof: [`INSTALL.md`](INSTALL.md).

## Tableau

Connect Tableau Public/Desktop to the CSVs under `data/tableau/`. Build notes: [`docs/tableau-build.md`](docs/tableau-build.md).

## What's in the folder

| Path | What |
| --- | --- |
| `sql/` | Schema, seed, gap views, allocation |
| `data/` | Dims, inventory, sales, PO, packs |
| `data/tableau/` | Extracts |
| `docs/` | Board (`index.html`), metrics, allocation writeup |
| `docs/data/board_data.json` | Gap board feed |
| `docs/data/allocation_board.json` | Allocation strip feed |
| `scripts/verify_kpis.py` | Gap lock (stdlib) |
| `scripts/verify_allocation.py` | Allocation lock (stdlib) |

## Screenshots

| Capture | File |
| --- | --- |
| Desktop 1440 | [`docs/screenshots/desktop_1440_house_ui.png`](docs/screenshots/desktop_1440_house_ui.png) |
| Tablet 1024 | [`docs/screenshots/tablet_1024_house_ui.png`](docs/screenshots/tablet_1024_house_ui.png) |

warehouse_1 on 2026-09-22: gap **22.5%**, phantom **7**, rescue **6**.

## Map pins

[`docs/map-pins-ma.md`](docs/map-pins-ma.md). Labels are `warehouse_N` + city / street / lat-lon only.

## If something breaks

| Issue | Fix |
| --- | --- |
| Board blank on `file://` | Serve `docs/` with `python3 -m http.server` |
| `verify_kpis.py` fails gap_rate | Don't edit `data/tableau/v_store_day_kpis.csv` |
| Tableau map empty | Geographic roles on `v_map_pins.csv` lat/lon |
| warehouse_4 has no KPIs | Expected. Use warehouse_1–3 |
| SQL seed FK errors | Fresh DB, run scripts in order |
| Pages 404 | Pages source = branch, folder `/docs` |

## License

MIT — Copyright (c) 2026 Neel Vittal Bharath Vadlamudi. See [`LICENSE`](LICENSE).
