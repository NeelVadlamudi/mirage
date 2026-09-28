# Where the truck goes

The empty-shelf board tells you why a bay is empty. This page is the next conversation: a truck of cases hits the DC. Who gets what? Does one club send stock to another?

Made-up data on purpose. Same clubs as the rest of Mirage.

## What happened on Sep 22, 2026

Purchase order **PO-26092201** arrives at the DC with **98** cases (12 items).

| | |
| --- | --- |
| Cases that go to clubs | 60 |
| Cases that stay at the DC | 38 |
| Club-to-club moves | 1 (Sticky Notes Value, 5 cases, warehouse_1 → warehouse_2) |
| Clubs short on stock (under 1 week) | 40 before the plan, 32 after |

| Club | How fast stock sold (28 days) | Short before | Short after |
| --- | --- | --- | --- |
| warehouse_1 | 77.2% | 15 | 11 |
| warehouse_2 | 75.0% | 12 | 10 |
| warehouse_3 | 71.9% | 13 | 11 |

Check every number above with:

```bash
python3 scripts/verify_allocation.py
```

## Say this in an interview (no notes)

**We split by need, not by who sells the most.**  
If warehouse_1 already sits on six weeks of an item, it does not get more just because it usually sells a lot. Need means "how many units until that club has about two weeks of stock." Clubs that are already fine get zero.

**Largest remainder is how leftover whole cases get handed out.**  
You cannot ship half a case. So each club gets the whole cases it clearly earned first. Whatever cases are left go to the clubs that were closest to earning one more. That way you ship the exact count that arrived, in whole cases, without rounding up past the truck.

**38 cases stay at the DC.**  
Three items had no need at any club. Pushing those cases out would just plant overstock in the clubs. Overstock is easier to hold at the DC than to dig out of three backrooms later.

**Only one transfer happened.**  
A transfer costs a truck and labor at two buildings. So the PO goes first. A club-to-club move only fires when the same item is under 1 week at one club and over 4 weeks at another. On this data, that bar cleared once: Sticky Notes Value, 5 cases, warehouse_1 to warehouse_2.

**We plan off counted units, not what the system says is on hand.**  
Mirage exists because the book is often wrong (empty floor, system still shows stock). If you allocate off a bad book, you send cases to the wrong place.

## How the plan runs (still plain)

1. Figure each club's weeks of stock from recent sales and what is actually on hand.
2. Split the PO by need, whole cases only. Hold leftovers nobody needs at the DC.
3. After that, look for the under-1 / over-4 pairs and move whole cases if needed.
4. Re-check who is still short.

Planning knobs on this demo: fill to 2 weeks, receive a transfer under 1 week, give stock away over 4 weeks, leave a donor with at least 3 weeks.

## Limits (be honest)

- Synthetic sales and inventory. They were built separately, so they do not move together like a live club.
- One PO, one day. No lead times, no second truck, no next-week forecast.
- Sales rate is a flat 28-day average.
- No shelf-face minimums. Real clubs still need enough units to look stocked on a slow item.
- At most one transfer per item.

## What I'd do next

Add a shelf-face minimum so slow items still look full. Use a short forecast and plan against weeks until the next delivery instead of a fixed two-week target.
