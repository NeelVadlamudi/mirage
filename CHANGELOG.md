# Changelog

## 0.2.0 - 2026-09-28

- Allocation module: 28-day sales, case packs, one DC PO (PO-26092201).
- Split the PO by need in whole cases (largest remainder). Hold back what no club needs.
- Club-to-club transfer only when one club is under 1 week of supply and another is over 4.
- `scripts/verify_allocation.py` (stdlib) and `scripts/export_allocation_extracts.py` (DuckDB).

## 0.1.0 - 2026-09-23

- First public pack: synthetic club inventory, KPI views, Tableau extracts, interactive gap board.
- Locked day warehouse_1 · 2026-09-22: gap 22.5% (9/40), phantom 7, rescue 6.
- Action on every open exception: recount, floor pull, or replenish.
- warehouse_4 is supply only (no floor KPIs).
- `scripts/verify_kpis.py` so you can prove the numbers without SQL Server.
- GitHub Pages board under `docs/`.
