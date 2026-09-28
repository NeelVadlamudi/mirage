#!/usr/bin/env python3
"""
Mirage allocation module: build the Tableau extracts without SQL Server.

Runs sql/04_allocation.sql against the CSVs in DuckDB. The T-SQL is translated with a
few plain text swaps (dbo. prefix, CREATE OR ALTER, GO batches, N'' strings), so the
view logic is the same text that runs on SQL Server.

  pip install duckdb
  python3 scripts/export_allocation_extracts.py

Writes data/tableau/v_store_sku_position.csv, v_po_allocation.csv, v_po_summary.csv,
v_reallocation_moves.csv, v_store_sku_final.csv, v_store_performance.csv.
"""
from __future__ import annotations

import re
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "tableau"

TABLES = {
    "dim_store": "dim_store.csv",
    "dim_sku": "dim_sku.csv",
    "fact_inventory_daily": "fact_inventory_daily.csv",
    "fact_sales_daily": "fact_sales_daily.csv",
    "dim_sku_pack": "dim_sku_pack.csv",
    "fact_dc_po": "fact_dc_po.csv",
    "dim_alloc_params": "dim_alloc_params.csv",
}
VIEWS = [
    "v_store_sku_position", "v_po_allocation", "v_po_summary",
    "v_reallocation_moves", "v_store_sku_final", "v_store_performance",
]


def tsql_to_duckdb(sql: str) -> list[str]:
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.S)
    sql = sql.replace("dbo.", "")
    sql = sql.replace("CREATE OR ALTER VIEW", "CREATE OR REPLACE VIEW")
    sql = re.sub(r"\bN'", "'", sql)
    batches = re.split(r"^\s*GO\s*$", sql, flags=re.M)
    return [b.strip() for b in batches if b.strip()]


def main() -> None:
    con = duckdb.connect()
    for table, fname in TABLES.items():
        con.execute(f"CREATE TABLE {table} AS SELECT * FROM read_csv_auto('{DATA / fname}', header=true)")
    for batch in tsql_to_duckdb((ROOT / "sql" / "04_allocation.sql").read_text(encoding="utf-8")):
        con.execute(batch)
    OUT.mkdir(parents=True, exist_ok=True)
    for v in VIEWS:
        con.execute(f"COPY (SELECT * FROM {v} ORDER BY ALL) TO '{OUT / (v + '.csv')}' (HEADER, DELIMITER ',')")
        n = con.execute(f"SELECT COUNT(*) FROM {v}").fetchone()[0]
        print(f"{v}: {n} rows")


if __name__ == "__main__":
    main()
