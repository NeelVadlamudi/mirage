# Mirage allocation module

The gap board answers "why is this shelf empty?" This module answers the next question:
when a purchase order lands at the DC, how many cases go to each club, and should any
club send stock to another?

All inputs are **synthetic**, from `scripts/gen_allocation_data.py` with a fixed seed.

## Inputs

| File | What |
| --- | --- |
| `data/fact_sales_daily.csv` | Units sold per club, SKU and day. 28 days ending 2026-09-22. |
| `data/dim_sku_pack.csv` | Case pack per SKU. Clubs get whole cases only. |
| `data/fact_dc_po.csv` | PO-26092201: 12 SKUs, 98 cases received at warehouse_4. |
| `data/dim_alloc_params.csv` | The planning rules. One row. |

Store demand is different on purpose. warehouse_1 sells more grocery and household,
warehouse_3 sells more GM and office, warehouse_2 sits near average.

## Rules

| Rule | Value | Meaning |
| --- | --- | --- |
| `target_wos` | 2.0 | Fill a club up to 2 weeks of supply. |
| `receiver_wos` | 1.0 | Under 1 week, a club can get stock from another club. |
| `overstock_wos` | 4.0 | Over 4 weeks, a club can give stock away. |
| `donor_keep_wos` | 3.0 | A club giving stock away keeps at least 3 weeks. |

## Steps

1. **Position** (`v_store_sku_position`). Weekly rate = units sold in the window x 7 / 28.
   Weeks of supply = units on hand / weekly rate. Need = units to reach 2 weeks.
2. **PO allocation** (`v_po_allocation`, `v_po_summary`). Each club's share is its need
   divided by the total need for that SKU. Whole cases first, then the leftover cases go to
   the clubs with the largest remainders. If the PO is bigger than total need, the rest
   stays at the DC.
3. **Transfers** (`v_reallocation_moves`). After the PO lands, if one club is still under
   1 week and another is over 4, move whole cases from the long club to the short one.
4. **After** (`v_store_sku_final`, `v_store_performance`). Each club and SKU after the PO and
   transfers, and a scorecard per club.

## Result on the locked day (2026-09-22)

| | |
| --- | --- |
| PO cases received | 98 |
| Cases allocated to clubs | 60 |
| Cases held at the DC | 38 (3 SKUs had no need at any club) |
| Store-to-store transfers | 1 (Sticky Notes Value, 5 cases, warehouse_1 to warehouse_2) |
| Club-SKUs under 1 week of supply | 40 before, 32 after |

| Club | Sell-through (28 days) | Under 1 week before | After |
| --- | --- | --- | --- |
| warehouse_1 | 77.2% | 15 | 11 |
| warehouse_2 | 75.0% | 12 | 10 |
| warehouse_3 | 71.9% | 13 | 11 |

Check it: `python3 scripts/verify_allocation.py` recomputes every number above in plain Python.

## Decisions

**On hand uses counted units, not the system number.** The gap board exists because the system
number is often wrong (phantom inventory). Allocating against a number I already know is wrong
would send cases to clubs that don't need them.

**Allocate by need, not by sales.** A plain sales-share split sends cases to a club that already
has 6 weeks on the shelf. Splitting by need (units short of target) sends nothing there.

**Largest remainder for the leftover cases.** Rounding every club's share up can ship more cases
than arrived. Rounding down leaves cases at the DC that a club needs. Largest remainder ships
exactly what's needed, in whole cases.

**Hold back what nobody needs.** 38 of 98 cases stayed at the DC. Pushing them out would only
move the overstock problem into the clubs, where it's harder to fix.

**Transfers run after the PO, and only for big gaps.** A transfer costs a truck and labor at two
clubs. So the PO covers what it can first, and a transfer happens only when one club is under
1 week and another is over 4. That rule produced one transfer on this data.

## Limits

- Synthetic data. The sales and inventory files were generated separately, so they don't move
  together the way real ones would. That is why so many club-SKUs start under 1 week.
- One PO, one day. No lead times, no second delivery, no forecast of next week.
- The weekly rate is a flat 28-day average. It ignores trend and weekends.
- No presentation minimums or shelf capacity. A real club needs enough units to fill the shelf
  face no matter how slow the item sells.
- One transfer per SKU at most, between the longest and shortest club.

## What I'd do next

Add a presentation minimum per SKU so slow items still look stocked. Swap the flat average for
a forecast and allocate against the weeks until the next delivery instead of a fixed 2 weeks.
