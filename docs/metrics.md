# Mirage metrics

Operations definitions for the gap board. Check window: 2026-09-09 to 2026-09-22.

Synthetic data. Pins mark town centers, not stores. Not affiliated with any retailer.

## Empty shelves (gap rate)

Share of stocked SKUs with nothing on the sales floor.

`gap_rate = count(floor_qty = 0 AND is_in_assortment = 1) / count(is_in_assortment = 1)`

Locked day at Everett: **22.5%** (9 of 40).

Next step: open the exception list.

## Book is wrong (phantom)

Floor empty; system on-hand still greater than zero.

`is_phantom = 1 when floor_qty = 0 AND system_on_hand_qty > 0`

Locked day: **7** SKUs. Next step: recount / correct the book.

## Stuck in backroom (rescue)

Floor empty; backroom quantity greater than zero.

Locked day: **6** SKUs. Next step: pull to the floor.

## Actually out (pure gap)

Floor empty, backroom empty, system on-hand zero. Next step: replenish / order.

## Summary

| Metric | Question | Next step |
| --- | --- | --- |
| Empty shelves | How empty is the floor? | Open the list |
| Book is wrong | How much emptiness is a bad book? | Recount |
| Stuck in backroom | Is stock off the floor? | Pull |
| Actually out | Are we out? | Order |

## Map pins

| Label | Town | Role | Synthetic id |
| --- | --- | --- | --- |
| Everett | Everett, MA | Club | warehouse_1 |
| Dedham | Dedham, MA | Club | warehouse_2 |
| Waltham | Waltham, MA | Club | warehouse_3 |
| Avon | Avon, MA | DC (no floor tiles) | warehouse_4 |

Avon synthetic DC day context (2026-09-22): outbound cases staged 1840; late truck notices 3.

Locked check: Everett · 2026-09-22 · **22.5% / 7 / 6**.
