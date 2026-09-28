# Mirage

**Live board:** [https://neelvadlamudi.github.io/mirage/](https://neelvadlamudi.github.io/mirage/)

Empty shelf. Full backroom. System still shows stock.

Mirage is a distribution and club inventory project. Pick a club and a day. See which shelves are empty, why, and what to do next. When a purchase order lands at the DC, see how many whole cases go to each club and whether one club should send stock to another. At the DC, track preventive maintenance cost, fleet coverage for peak weeks, and whether a lighting retrofit actually cut energy use after shipping volume is accounted for.

## Data note

All inventory, sales, work orders, and utility figures in this repository are synthetic. Map pins mark town centers, not stores. Not affiliated with any retailer. Clubs are Everett, Dedham, and Waltham. The DC is Avon. (Synthetic ids stay `warehouse_1`…`warehouse_4` in extracts.)

## Gap board

| Tile | Meaning | Next step |
| --- | --- | --- |
| **Empty shelves** | Share of assortment with nothing on the floor | Open the exception list |
| **Book is wrong** | Floor empty; system still shows on-hand | Recount / correct the book |
| **Stuck in backroom** | Floor empty; backroom has stock | Pull to the floor |
| **Actually out** | Floor empty; backroom empty; book is zero | Replenish / order |

Locked check day (**Everett**, 2026-09-22):

- Empty shelves: **22.5%** (9 of 40)
- Book is wrong: **7**
- Stuck in backroom: **6**

```bash
python3 scripts/verify_kpis.py
```

Expected: `ALL PASS — warehouse_1 @ 2026-09-22: 22.5% / 7 / 6`

Detail: [`docs/metrics.md`](docs/metrics.md).

## Allocation

PO-26092201 arrives at Avon with **98** cases (12 SKUs).

- **60** cases allocated to clubs (whole cases, by need)
- **38** held at the DC (no club need)
- **1** club-to-club transfer: Sticky Notes Value, 5 cases, Everett → Dedham
- Club-SKUs under 1 week of supply: **40 → 32**

Rules and decisions: [`docs/allocation.md`](docs/allocation.md).

```bash
python3 scripts/verify_allocation.py
```

Expected last line: `ALL PASS - PO 98 cases: 60 allocated, 38 held at DC; 1 transfer(s); club-SKUs under 1 week of supply 40 -> 32`

## Maintenance (Avon)

60 material-handling assets. 1,009 synthetic work orders with problem, cause, and remedy codes.

| Question | Result |
| --- | --- |
| Missed or late PM follow-up | Breakdown within 30 days **50.0%** vs **25.8%** after on-time PM. About **33** extra breakdowns and **$35.8K** / year. |
| Failure concentration | Reach trucks 6+ years old: **4.6x** battery failures per truck vs newer units (3 newer trucks in sample). |
| Peak fleet coverage | December need **20** order pickers vs fleet **18**. Short in **5** of the next 13 weeks. |
| LED retrofit | **15.1%** below volume-adjusted energy baseline. Payback **17.5** months. |

Methods and limits: [`docs/maintenance.md`](docs/maintenance.md).  
One-page report: [`docs/maintenance_report.pdf`](docs/maintenance_report.pdf).  
Operator guide: [`docs/maintenance_user_guide.md`](docs/maintenance_user_guide.md).

```bash
python3 scripts/verify_maintenance.py
```

## Open the board

https://neelvadlamudi.github.io/mirage/

Local:

```bash
cd docs && python3 -m http.server 8080
```

Then open http://localhost:8080/

## SQL and Tableau

Install: [`INSTALL.md`](INSTALL.md).  
Tableau extracts: `data/tableau/`. Build notes: [`docs/tableau-build.md`](docs/tableau-build.md).

## Screenshots

| View | File |
| --- | --- |
| Desktop | [`docs/screenshots/desktop_1440.png`](docs/screenshots/desktop_1440.png) |
| Phone | [`docs/screenshots/phone_390.png`](docs/screenshots/phone_390.png) |

## License

MIT. Copyright (c) 2026 Neel Vittal Bharath Vadlamudi. See [`LICENSE`](LICENSE).
