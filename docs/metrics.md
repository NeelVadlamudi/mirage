# Mirage metrics

Numbers a hiring manager can say in one sentence. Check window: 2026-09-09 → 2026-09-22. Floor grain: store × SKU × day.

Synthetic data for a portfolio demo. Pins mark town centers, not stores. Not affiliated with any retailer.

## Gap rate

Share of stocked SKUs with nothing on the sales floor today.

`gap_rate = count(floor_qty = 0 AND is_in_assortment = 1) / count(is_in_assortment = 1)`

Say it like: "22.5% of the assortment is empty on the floor right now."

When it's high, open the exception list. Each row already has the next step.

## Phantom SKUs

Floor is empty. The system still shows on-hand. Book says yes. Shelf says no.

`is_phantom = 1 when floor_qty = 0 AND system_on_hand_qty > 0`

Rollup: count distinct SKUs with that flag.

Next step: **Recount / fix the book**.

## Backroom rescue

Floor empty, backroom has stock. That's a labor miss, not a buy miss.

Rescue row: `floor_qty = 0 AND backroom_qty > 0`

Next step: **Pull to the floor**. If it's also phantom: **Pull · recount**.

## Pure gap

Floor empty, backroom empty, book is zero. You need product.

Next step: **Replenish / order**.

## How they stack

| Metric | Question | Next step |
| --- | --- | --- |
| Gap rate | How empty is the floor today? | Open the list |
| Phantom | How much of that emptiness is a bad book? | Recount |
| Backroom rescue | Is the stock just not on the floor? | Pull |
| Pure gap | Are we actually out? | Order |

## Map pins

| Pin | Town | Lat, lon | Role |
| --- | --- | --- | --- |
| warehouse_1 | Everett, MA | 42.4084, -71.0537 | Club — floor KPIs |
| warehouse_2 | Dedham, MA | 42.2418, -71.1662 | Club — floor KPIs |
| warehouse_3 | Waltham, MA | 42.3765, -71.2356 | Club — floor KPIs |
| warehouse_4 | Avon, MA | 42.1306, -71.0412 | Supply only — no floor KPIs |

### warehouse_4 on the check day (synthetic)

| Field | Value |
| --- | --- |
| `outbound_cases_staged` | 1840 |
| `late_asn_count` | 3 |

These are DC context, not floor KPIs. See `docs/data/board_data.json` → `dc`.

## Locked check — warehouse_1 · 2026-09-22

Gap **22.5%** (9 of 40). Phantom **7**. Rescue **6**.
