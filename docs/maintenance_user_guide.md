# How to use the maintenance report

For supervisors and technicians at Avon. One page. Open `docs/maintenance_report.pdf`.

## What each panel tells you, and what to do

**1. Breakdown rate after a PM (top left)**
The orange bar is how often a machine broke down in the 30 days after its PM was missed or done
late. The blue bar is the same for PMs done on time.
*What to do:* if the orange bar is well above the blue one, protect the PM schedule first,
before adding repair hours. Look up the assets with the lowest PM compliance in
`v_asset_reliability` (column `pm_compliance`).

**2. Battery failures by truck age (top right)**
Battery breakdowns per reach truck in the last 12 months, split by age.
*What to do:* use the older group as the battery replacement list before peak season. Check each
truck's own count in `v_asset_reliability` before ordering.

**3. Order pickers needed (bottom left)**
The blue line is how many order pickers each coming week needs. The orange line is the fleet.
*What to do:* any week where blue is above orange needs rentals or extra shifts booked ahead.
Rentals for December usually need to be reserved weeks in advance.

**4. Energy use vs baseline (bottom right)**
The orange line is what the building would have used without the LED retrofit, given how much it
shipped. Blue is what it did use.
*What to do:* nothing, unless blue climbs back toward orange. That usually means fixtures or
controls need attention.

## When a number looks wrong

1. Run `python3 scripts/verify_maintenance.py`. It rechecks every number on the report.
2. Check for work orders with no completed date. Open work orders count as downtime still
   running.
3. Check problem codes. A CM with the wrong problem code moves a failure into the wrong bar.

## What changed in this release

- New views: `v_asset_reliability`, `v_pm_followup`, `v_pm_missed_cost`, `v_failure_patterns`,
  `v_fleet_need_forecast`, `v_utility_baseline`, `v_utility_roi`.
- New report: `docs/maintenance_report.pdf`, rebuilt by `scripts/build_maintenance_report.py`.
