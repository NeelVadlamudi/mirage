# Changelog

## 0.2.0 - 2026-09-28

- Allocation module: synthetic 28-day sales, case packs, and one DC purchase order (PO-26092201).
- `v_po_allocation`: splits the PO across clubs by need in whole cases (largest remainder), holds back what no club needs.
- `v_reallocation_moves`: club-to-club transfers when one club is under 1 week of supply and another is over 4.
- `v_store_performance`: sell-through and weeks-of-supply counts before and after.
- `scripts/verify_allocation.py` (stdlib) and `scripts/export_allocation_extracts.py` (DuckDB, no SQL Server needed).

## 0.1.0 — 2026-09-23

- Public Mirage release pack: synthetic club inventory, KPI views, Tableau extracts, interactive gap board.
- Locked check day **warehouse_1 · 2026-09-22**: gap **22.5%** (9/40), phantom **7**, rescue **6**.
- Action labels on every open exception (recount / floor pull / replenish).
- warehouse_4 treated as supply pin only (no floor KPIs); synthetic DC day context included.
- Docs for metrics, MA map pins, Tableau build; `scripts/verify_kpis.py` for recruiter-proof validation without SQL Server.
- GitHub Pages board under `docs/` (`index.html` + `board_data.json`).
