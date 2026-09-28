# Mirage

Empty shelf. Full backroom. System still says we have stock.

I built this for people who run clubs and for people who hire analysts. One board. You pick a club and a day. You see how many shelves are empty, why each one is empty, and what to do next. When a truck of cases lands at the DC, you also see how many go to each club and whether one club should send stock to another.

## Straight talk

The data is made up for a portfolio demo. Map pins sit on town centers, not real stores. This is not affiliated with any retailer. Clubs are labeled `warehouse_1`, `warehouse_2`, `warehouse_3`. The DC is `warehouse_4`.

## What the board shows

| Tile | In plain words | Next move |
| --- | --- | --- |
| **Empty shelves** | How much of the assortment has nothing on the floor | Open the list |
| **Book is wrong** | Floor is empty but the system still shows stock | Recount |
| **Stuck in backroom** | Floor is empty but the backroom has it | Pull it to the floor |
| **Actually out** | Nothing on floor, nothing in back, book is zero | Order more |

On the locked check day (**warehouse_1**, Sep 22, 2026):

- Empty shelves: **22.5%** (9 of 40 items)
- Book is wrong: **7** items
- Stuck in backroom: **6** items

Prove those three numbers on any laptop:

```bash
python3 scripts/verify_kpis.py
```

## Where the truck goes (allocation)

A purchase order lands at the DC: **98** cases across 12 items.

- **60** cases go out to the three clubs
- **38** stay at the DC because no club needs them
- **1** club-to-club move: Sticky Notes Value, 5 cases, from warehouse_1 to warehouse_2
- Clubs short on stock: **40 → 32** after the plan

The short writeup a recruiter can read in two minutes: [`docs/allocation.md`](docs/allocation.md). That page is also the interview sheet (why need beats sales share, what largest remainder means, why 38 stay at the DC, why only one transfer, why we use counted units).

Prove it:

```bash
python3 scripts/verify_allocation.py
```

## Open the board

```bash
cd docs && python3 -m http.server 8080
```

Then open http://localhost:8080/

Live site uses the `docs` folder on GitHub Pages.

## For people who want the SQL / Tableau layer

Install steps: [`INSTALL.md`](INSTALL.md).  
Metric definitions: [`docs/metrics.md`](docs/metrics.md).  
Tableau extracts sit under `data/tableau/`.

## Screenshots

| View | File |
| --- | --- |
| Desktop | [`docs/screenshots/desktop_1440_house_ui.png`](docs/screenshots/desktop_1440_house_ui.png) |
| Tablet | [`docs/screenshots/tablet_1024_house_ui.png`](docs/screenshots/tablet_1024_house_ui.png) |

## License

MIT. Copyright (c) 2026 Neel Vittal Bharath Vadlamudi. See [`LICENSE`](LICENSE).
