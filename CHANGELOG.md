# Changelog

## 0.3.0 - 2026-09-28

- Maintenance module at Avon: 60 assets, 1,009 synthetic work orders (problem / cause / remedy).
- Missed or late PM → breakdown within 30 days 50.0% vs 25.8% after on-time PM (~33 extra breakdowns, $35.8K / year).
- Reach trucks 6+ years old: 4.6x battery failures (lead, small newer sample).
- Order picker need peaks at 20 vs fleet of 18; short in 5 of next 13 weeks.
- LED retrofit 15.1% under volume-adjusted baseline; payback 17.5 months.
- `docs/maintenance_report.pdf`, `docs/maintenance_user_guide.md`, `scripts/verify_maintenance.py`.

## 0.2.1 - 2026-09-28

- Docs pass for clearer operations language. Same locked numbers.

## 0.2.0 - 2026-09-28

- Allocation module: 28-day sales, case packs, one DC PO (PO-26092201).
- Split the PO by need in whole cases (largest remainder). Hold back what no club needs.
- Club-to-club transfer only when one club is under 1 week of supply and another is over 4.
- `scripts/verify_allocation.py` (stdlib) and `scripts/export_allocation_extracts.py` (DuckDB).

## 0.1.0 - 2026-09-23

- First public pack: synthetic club inventory, KPI views, Tableau extracts, interactive gap board.
- Locked day Everett · 2026-09-22: gap 22.5% (9/40), phantom 7, rescue 6.
- Action on every open exception: recount, floor pull, or replenish.
- Avon is supply only (no floor KPIs).
- `scripts/verify_kpis.py` so you can prove the numbers without SQL Server.
- GitHub Pages board under `docs/`.
