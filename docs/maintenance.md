# Mirage maintenance module

The shelf is only full if the equipment behind it keeps running. This module looks at
the 60 material handling assets at warehouse_4 (the DC) and asks four questions a
facilities manager would ask.

All inputs are **synthetic**, from `scripts/gen_maintenance_data.py` with a fixed seed.
The generator plants a few patterns. The views and the checker never read the generator's
settings; they have to find the patterns in the work orders.

## Inputs (`data/maint/`)

| File | What |
| --- | --- |
| `dim_asset.csv` | 60 assets: 14 reach trucks, 18 order pickers, 16 electric pallet jacks, 8 conveyor sections, 4 dock levelers. |
| `fact_workorder.csv` | 1,009 work orders over 52 weeks. PM (preventive) and CM (corrective). Problem, cause and remedy codes on every CM, the usual CMMS failure hierarchy. |
| `fact_dc_volume_weekly.csv` | 104 weeks of cases shipped. |
| `fact_utility_monthly.csv` | 23 months of electricity. LED lighting retrofit finished 2025-08-31. |
| `dim_maint_params.csv` | The rules the views read. |

## Results

| Question | Answer | View |
| --- | --- | --- |
| Do missed PMs cost us? | 50.0% of missed or late PMs were followed by a breakdown within 30 days, vs 25.8% of on-time PMs (1.9x). About 33 extra breakdowns, $35,832 and 251 downtime hours in a year. | `v_pm_followup`, `v_pm_missed_cost` |
| Where do failures cluster? | Reach trucks 6+ years old had 3.1 battery breakdowns per truck, vs 0.7 for newer ones (4.6x). | `v_failure_patterns` |
| Do we have enough trucks for peak? | Order pickers needed peaks at 20 in December against a fleet of 18. Short in 5 of the next 13 weeks. | `v_fleet_need_forecast` |
| Did the LED retrofit pay off? | 15.1% below the energy baseline, $167,643 a year, payback in 17.5 months on a $245,000 project. | `v_utility_baseline`, `v_utility_roi` |

Also: `v_asset_reliability` has one row per asset with breakdowns, MTBF, MTTR, PM compliance,
maintenance cost and availability.

Check it: `python3 scripts/verify_maintenance.py`. One-page report: `docs/maintenance_report.pdf`.
How to read it: `docs/maintenance_user_guide.md`.

## Decisions

**Missed and late PMs go in one group.** A PM done 15 days late leaves the machine unserviced
for most of the month, same as a skipped one. Splitting them would halve an already small group.

**30-day follow-up window, and only PMs whose window has closed.** PMs are due every 30 days, so
a breakdown inside 30 days belongs to that PM cycle. A PM scheduled in the last 30 days of data
can't be judged yet, so it's left out rather than counted as "no breakdown."

**Extra breakdowns = missed PMs x (missed rate - on-time rate).** That counts only the
breakdowns above what on-time PMs already see. Blaming every breakdown after a missed PM would
overstate the cost.

**Failures per asset, not failure counts.** There are 11 older reach trucks and 3 newer ones.
Raw counts would say older trucks fail more just because there are more of them.

**Fleet forecast = same week last year x recent growth.** One year of work orders but two years
of volume is enough for a seasonal forecast and not enough for anything fancier. Growth is the
last 13 weeks against the same 13 weeks a year earlier. Trucks needed divides by fleet
availability, so downtime from breakdowns reduces the hours each truck can give.

**Energy baseline is fit on volume, not on last year's bill.** The DC ships more every year.
Comparing this year's bill to last year's would hide part of the savings under growth. The
baseline is a least-squares line of kWh against cases shipped, fit only on months before the
retrofit.

## Limits

- Synthetic data, one site, one year of work orders.
- Only 3 reach trucks are under 6 years old. The 4.6x battery gap points in a direction; it
  isn't proof.
- No weather in the energy baseline. A real one adds heating and cooling degree days.
- Truck need assumes every order picker is interchangeable and runs 120 hours a week. It
  ignores shift patterns and operator headcount, which often run out before trucks do.
- PM "late" is judged from the scheduled date. There's no meter-based PM (hours run), which
  many sites use for trucks.

## What I'd do next

Rank each asset by expected breakdown cost for the next 90 days (age, open CMs, PM compliance)
so the repair-or-replace list writes itself. Add degree days to the energy baseline.
