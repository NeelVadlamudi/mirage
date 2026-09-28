#!/usr/bin/env python3
"""
Mirage allocation module: generate the synthetic inputs.

Writes (all synthetic, fixed seed, so every run gives the same files):
  data/fact_sales_daily.csv   store x SKU x day units sold, 28 days ending 2026-09-22
  data/dim_sku_pack.csv       case pack per SKU (the smallest unit a store can be sent)
  data/fact_dc_po.csv         one inbound purchase order landing at warehouse_4 (the DC)
  data/dim_alloc_params.csv   the planning rules the views read (one row)

Store demand differs on purpose so allocation has something to decide:
  warehouse_1 (Everett) sells more grocery and household, less GM.
  warehouse_2 (Dedham)  is close to average, a bit heavier on baby.
  warehouse_3 (Waltham) sells more GM and office, less grocery.
Weekends run about 30% above weekdays.

Stdlib only.
"""
from __future__ import annotations

import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

SEED = 20260922
AS_OF = date(2026, 9, 22)
WINDOW_DAYS = 28
CLUBS = (101, 102, 103)
DC_ID = 901

# Average units per club per day before store and weekend effects.
CATEGORY_BASE_RATE = {
    "Grocery": 4.0, "Household": 3.0, "Deli": 3.5, "Dairy": 3.5, "Produce": 3.0,
    "Meat": 2.0, "GM": 1.0, "Office": 0.8, "Baby": 1.5,
}
STORE_CATEGORY_FACTOR = {
    101: {"Grocery": 1.3, "Household": 1.3, "GM": 0.6, "Office": 0.6},
    102: {"Baby": 1.4},
    103: {"GM": 1.6, "Office": 1.6, "Grocery": 0.7, "Household": 0.8},
}
CATEGORY_CASE_PACK = {
    "Grocery": 6, "Household": 4, "Deli": 6, "Dairy": 6, "Produce": 6,
    "Meat": 4, "GM": 2, "Office": 3, "Baby": 4,
}
WEEKEND_LIFT = 1.3


def poisson(rng: random.Random, lam: float) -> int:
    """Knuth's method. Fine for the small rates used here."""
    if lam <= 0:
        return 0
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def main() -> None:
    rng = random.Random(SEED)
    with (DATA / "dim_sku.csv").open(newline="", encoding="utf-8") as f:
        skus = [r for r in csv.DictReader(f) if r["is_in_assortment"] == "1"]

    # Each SKU gets its own speed around the category average (0.6x to 1.4x).
    sku_speed = {r["sku_id"]: rng.uniform(0.6, 1.4) for r in skus}

    start = AS_OF - timedelta(days=WINDOW_DAYS - 1)
    rows = []
    for d in range(WINDOW_DAYS):
        day = start + timedelta(days=d)
        lift = WEEKEND_LIFT if day.weekday() >= 5 else 1.0
        for store in CLUBS:
            for r in skus:
                cat = r["category"]
                lam = (CATEGORY_BASE_RATE[cat]
                       * sku_speed[r["sku_id"]]
                       * STORE_CATEGORY_FACTOR[store].get(cat, 1.0)
                       * lift)
                rows.append((day.isoformat(), store, r["sku_id"], poisson(rng, lam)))

    with (DATA / "fact_sales_daily.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sales_date", "store_id", "sku_id", "units_sold"])
        w.writerows(rows)

    with (DATA / "dim_sku_pack.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sku_id", "case_pack"])
        for r in skus:
            w.writerow([r["sku_id"], CATEGORY_CASE_PACK[r["category"]]])

    # One PO covering 12 SKUs. Case counts are drawn at random, not fitted to need,
    # so some SKUs arrive short of what the clubs need and some arrive long.
    po_skus = rng.sample([r["sku_id"] for r in skus], 12)
    with (DATA / "fact_dc_po.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["po_id", "dc_store_id", "sku_id", "receipt_date", "cases_received"])
        for sku in sorted(po_skus):
            w.writerow(["PO-26092201", DC_ID, sku, AS_OF.isoformat(), rng.randint(2, 14)])

    with (DATA / "dim_alloc_params.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["as_of_date", "sales_window_start", "sales_window_days",
                    "target_wos", "donor_keep_wos", "overstock_wos", "receiver_wos"])
        w.writerow([AS_OF.isoformat(), start.isoformat(), WINDOW_DAYS, 2.0, 3.0, 4.0, 1.0])

    print(f"fact_sales_daily rows = {len(rows)}; PO lines = {len(po_skus)}")


if __name__ == "__main__":
    main()
