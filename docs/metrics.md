# Mirage metrics (plain English)

For a hiring manager or a floor lead. One screen. Numbers you can say out loud.

Check window: Sep 9 to Sep 22, 2026. Made-up data for a portfolio demo. Pins mark town centers, not stores. Not affiliated with any retailer.

## Empty shelves (gap rate)

Share of stocked items with nothing on the sales floor today.

On the locked day at warehouse_1 that is **22.5%** (9 of 40).

Say it like: "About one in four items on the assortment is empty on the floor right now."

Next move: open the list. Each row already says what to do.

## Book is wrong (phantom)

Floor is empty. The system still shows stock.

On the locked day: **7** items.

Next move: recount. Fix the book.

## Stuck in backroom (rescue)

Floor is empty. The backroom has it.

On the locked day: **6** items.

Next move: pull it to the floor. If the book is also wrong, pull and recount.

## Actually out (pure gap)

Floor empty, backroom empty, book is zero.

Next move: order more.

## How to read the four together

| Tile | Question | Next move |
| --- | --- | --- |
| Empty shelves | How bad is empty-shelf today? | Open the list |
| Book is wrong | How much of that is a bad book? | Recount |
| Stuck in backroom | Is the stock just not on the floor? | Pull |
| Actually out | Are we really out? | Order |

## Clubs on the map

| Label | Town | Role |
| --- | --- | --- |
| warehouse_1 | Everett, MA | Club |
| warehouse_2 | Dedham, MA | Club |
| warehouse_3 | Waltham, MA | Club |
| warehouse_4 | Avon, MA | DC only (no floor tiles) |

On the check day the DC shows synthetic outbound cases staged (1840) and late advance ship notices (3). That is context for the truck, not a floor score.

## Formulas (for analysts who want them)

- Empty shelves: count(floor = 0 and in assortment) / count(in assortment)
- Book is wrong: floor = 0 and system on-hand > 0
- Stuck in backroom: floor = 0 and backroom > 0
- Actually out: floor empty, not phantom, not backroom rescue

Locked check: warehouse_1 · 2026-09-22 · **22.5% / 7 / 6**.
