# Mirage — Install & proof

Two paths. Recruiters can use **Path A** (no SQL Server). Analysts who want the T-SQL layer use **Path B**.

---

## Path A — Python proof (recommended, ~30 seconds)

Requires: Python 3.8+ (stdlib only).

```bash
git clone https://github.com/NeelVadlamudi/mirage.git
cd mirage
python3 scripts/verify_kpis.py
```

### Expected output (PASS)

```
PASS  fact_inventory_daily rows = 1680
PASS  dim_sku rows = 40
PASS  dim_store rows = 4
PASS  v_map_pins rows = 4
PASS  v_map_pins real_site scrubbed (public pin only / empty)
PASS  dim_store has no real_site column
PASS  warehouse_1 2026-09-22 gap_rate = 0.225
PASS  warehouse_1 2026-09-22 gap_sku_count = 9
PASS  warehouse_1 2026-09-22 assortment_sku_count = 40
PASS  warehouse_1 2026-09-22 phantom_sku_count = 7
PASS  warehouse_1 2026-09-22 backroom_rescue_sku_count = 6
PASS  v_inventory_flags cross-check: gaps=9 phantom=7 rescue=6

ALL PASS — warehouse_1 @ 2026-09-22: 22.5% / 7 / 6
```

Locked KPIs: **22.5% / 7 / 6**.

### Open the interactive board

```bash
cd docs
python3 -m http.server 8080
```

Visit `http://localhost:8080/` — chips, tiles, exception list, actions.

---

## Path B — SQL Server Developer / Azure Data Studio

### 1. Install

- [SQL Server Developer](https://www.microsoft.com/sql-server/sql-server-downloads) (free) **or** Azure SQL
- [Azure Data Studio](https://learn.microsoft.com/azure-data-studio/) or SSMS

### 2. Create database

```sql
CREATE DATABASE mirage;
GO
USE mirage;
GO
```

### 3. Run scripts in order

In Azure Data Studio, open and execute:

1. `sql/00_schema.sql`
2. `sql/01_seed.sql`
3. `sql/02_metrics.sql`

### 4. Proof queries

**Row counts**

```sql
SELECT 'dim_store' AS t, COUNT(*) AS n FROM dbo.dim_store
UNION ALL SELECT 'dim_sku', COUNT(*) FROM dbo.dim_sku
UNION ALL SELECT 'fact_inventory_daily', COUNT(*) FROM dbo.fact_inventory_daily;
```

| Table | Expected `n` |
| --- | --- |
| dim_store | 4 |
| dim_sku | 40 |
| fact_inventory_daily | 1680 |

**Locked warehouse_1 KPIs (2026-09-22)**

```sql
SELECT
    store_name,
    snapshot_date,
    gap_rate,
    gap_sku_count,
    assortment_sku_count,
    phantom_sku_count,
    backroom_rescue_sku_count
FROM dbo.v_store_day_kpis
WHERE store_name = N'warehouse_1'
  AND snapshot_date = '2026-09-22';
```

| Field | Expected |
| --- | --- |
| gap_rate | 0.2250 (22.5%) |
| gap_sku_count | 9 |
| assortment_sku_count | 40 |
| phantom_sku_count | 7 |
| backroom_rescue_sku_count | 6 |

**Optional — still run the Python proof on the CSVs**

```bash
python3 scripts/verify_kpis.py
```

---

## Path C — Tableau extracts

1. Open Tableau Public / Desktop.
2. Connect → Text file → `data/tableau/`.
3. Add: `v_store_day_kpis.csv`, `v_inventory_flags.csv`, `v_gaps_by_category.csv`, `v_gap_rate_trend.csv`, `v_map_pins.csv`.
4. Relate on `store_id` (and `snapshot_date` where needed).
5. Follow [`docs/tableau-build.md`](docs/tableau-build.md).

Filter to `warehouse_1` + `2026-09-22` and confirm tiles: **22.5% · 7 · 6**.

---

## GitHub Pages

Repo → Settings → Pages → Build and deployment → Source: **Deploy from a branch** → Branch: `main` → Folder: **`/docs`** → Save.

Board URL shape: `https://neelvadlamudi.github.io/mirage/`
