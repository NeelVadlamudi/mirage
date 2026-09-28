# Mirage allocation

The gap board answers why a shelf is empty. This module answers the next two questions:

1. When a PO lands at the DC, how many whole cases go to each club?
2. Should one club send stock to another?

Inputs are synthetic (`scripts/gen_allocation_data.py`, fixed seed).

## Inputs

| File | What |
| --- | --- |
| `data/fact_sales_daily.csv` | Units sold per club × SKU × day. 28 days ending 2026-09-22. |
| `data/dim_sku_pack.csv` | Case pack per SKU. Clubs only get whole cases. |
| `data/fact_dc_po.csv` | PO-26092201: 12 SKUs, 98 cases at warehouse_4. |
| `data/dim_alloc_params.csv` | Planning rules. One row. |

Demand mix is different on purpose. warehouse_1 sells more grocery and household. warehouse_3 sells more GM and office. warehouse_2 sits near average.

## Rules

| Rule | Value | Meaning |
| --- | --- | --- |
| `target_wos` | 2.0 | Fill a club up to 2 weeks of supply |
| `receiver_wos` | 1.0 | Under 1 week → can receive a transfer |
| `overstock_wos` | 4.0 | Over 4 weeks → can give stock away |
| `donor_keep_wos` | 3.0 | A donor keeps at least 3 weeks |

## Steps

1. **Position** (`v_store_sku_position`). Weekly rate = units sold in the window × 7 / 28. Weeks of supply = on-hand / weekly rate. Need = units short of 2 weeks.
2. **PO split** (`v_po_allocation`, `v_po_summary`). Each club's share = its need / total need for that SKU. Hand out whole cases first. Leftover cases go to the clubs with the largest remainders. If the PO is bigger than total need, the rest stays at the DC.
3. **Transfers** (`v_reallocation_moves`). After the PO, if one club is still under 1 week and another is over 4 on the same SKU, move whole cases from the long club to the short one.
4. **After** (`v_store_sku_final`, `v_store_performance`). Position and scorecard once the PO and transfers land.

## Result — 2026-09-22

| | |
| --- | --- |
| PO cases received | 98 |
| Cases to clubs | 60 |
| Cases held at DC | 38 (3 SKUs had no need at any club) |
| Store-to-store transfers | 1 (Sticky Notes Value, 5 cases, warehouse_1 → warehouse_2) |
| Club-SKUs under 1 week | 40 before, 32 after |

| Club | Sell-through (28d) | Under 1 week before | After |
| --- | --- | --- | --- |
| warehouse_1 | 77.2% | 15 | 11 |
| warehouse_2 | 75.0% | 12 | 10 |
| warehouse_3 | 71.9% | 13 | 11 |

`python3 scripts/verify_allocation.py` recomputes every number above in plain Python.

## Decisions (say these without notes)

**Counted units, not the system book.** The gap board exists because the book is often wrong (phantom). If I allocate off a number I already know is wrong, I ship cases to clubs that don't need them.

**Need, not sales share.** A sales-share split still dumps cases on a club sitting on 6 weeks. Need (units short of target) sends nothing there.

**Largest remainder for leftover whole cases.** Round every share up and you ship more than arrived. Round everything down and you leave cases at the DC that a club actually needs. Largest remainder: give out the whole cases first, then hand the leftovers to whoever was closest to earning one more. You ship exactly the right count, in whole cases.

**Hold what nobody needs.** 38 of 98 cases stayed at the DC. Pushing them out just moves overstock into the clubs, where it's harder to fix.

**Transfers after the PO, and only for a real imbalance.** A transfer costs a truck and labor at two clubs. So the PO covers what it can first. A transfer only fires when one club is under 1 week and another is over 4 on the same item. On this data that rule produced one move.

## Limits

- Synthetic. Sales and inventory were generated separately, so they don't move together the way a live club would. That's why so many club-SKUs start under 1 week.
- One PO, one day. No lead times, no second delivery, no next-week forecast.
- Weekly rate is a flat 28-day average. No trend, no weekend pattern.
- No presentation minimums or shelf capacity. Real clubs still need enough units to fill the face on a slow SKU.
- At most one transfer per SKU, between the longest and shortest club.

## What I'd do next

Add a presentation minimum so slow items still look stocked. Swap the flat average for a short forecast and allocate against weeks until the next delivery instead of a fixed 2-week target.
