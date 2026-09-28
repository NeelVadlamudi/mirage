#!/usr/bin/env python3
"""
Mirage maintenance module: build the extracts without SQL Server.

Runs sql/06_maintenance.sql against data/maint/*.csv in DuckDB, using the same T-SQL text swaps
as export_allocation_extracts.py (plus a dateadd_day macro for DATEADD).

  pip install duckdb
  python3 scripts/export_maintenance_extracts.py
"""
from __future__ import annotations

from pathlib import Path

import duckdb

from export_allocation_extracts import tsql_to_duckdb

ROOT = Path(__file__).resolve().parents[1]
MAINT = ROOT / "data" / "maint"
OUT = MAINT / "extracts"
TABLES = ["dim_asset", "fact_workorder", "fact_dc_volume_weekly", "fact_utility_monthly", "dim_maint_params"]
VIEWS = ["v_asset_reliability", "v_pm_followup", "v_pm_missed_cost", "v_failure_patterns",
         "v_fleet_need_forecast", "v_utility_baseline", "v_utility_roi"]


def main() -> None:
    con = duckdb.connect()
    con.execute("CREATE MACRO dateadd_day(n, d) AS CAST(d AS DATE) + CAST(n AS INTEGER)")
    for t in TABLES:
        con.execute(f"CREATE TABLE {t} AS SELECT * FROM read_csv_auto('{MAINT / (t + '.csv')}', header=true)")
    for batch in tsql_to_duckdb((ROOT / "sql" / "06_maintenance.sql").read_text(encoding="utf-8")):
        con.execute(batch)
    OUT.mkdir(parents=True, exist_ok=True)
    for v in VIEWS:
        con.execute(f"COPY (SELECT * FROM {v} ORDER BY ALL) TO '{OUT / (v + '.csv')}' (HEADER, DELIMITER ',')")
        print(f"{v}: {con.execute(f'SELECT COUNT(*) FROM {v}').fetchone()[0]} rows")


if __name__ == "__main__":
    main()
