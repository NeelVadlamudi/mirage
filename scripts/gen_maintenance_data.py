#!/usr/bin/env python3
"""
Mirage maintenance module: generate the synthetic inputs for warehouse_4 (the DC).

Writes (all synthetic, fixed seed):
  data/maint/dim_asset.csv            60 material handling assets at the DC
  data/maint/fact_workorder.csv       one year of preventive (PM) and corrective (CM) work orders,
                                      with problem / cause / remedy codes in the style most CMMS tools use
  data/maint/fact_dc_volume_weekly.csv  104 weeks of cases shipped
  data/maint/fact_utility_monthly.csv   23 months of electricity use; LED lighting retrofit finished 2025-08-31
  data/maint/dim_maint_params.csv       planning rules the views read (one row)

Patterns built in on purpose, so the analysis has something real to find:
  - An asset whose last PM was missed or done late fails more often in the next 30 days.
  - Reach trucks 6+ years old have far more battery failures.
  - Volume peaks in November and December and grows about 6% a year.
The views and checker do not read these settings. They have to find the patterns in the data.

Stdlib only.
"""
from __future__ import annotations

import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "maint"
SEED = 20260928
DC_ID = 901
WO_START, WO_END = date(2025, 9, 22), date(2026, 9, 21)      # 52 weeks
VOL_START = date(2024, 9, 23)                                  # 104 weeks, Mondays
UTIL_MONTHS = [(2024, m) for m in range(10, 13)] + [(2025, m) for m in range(1, 13)] + [(2026, m) for m in range(1, 9)]
LED_DONE = date(2025, 8, 31)

ASSET_TYPES = {
    # type: (count, daily CM hazard, problem codes with weights)
    "Reach Truck":     (14, 0.010, {"BATTERY": 4, "HYDRAULIC": 3, "MAST": 2, "TIRES": 2, "ELECTRICAL": 2}),
    "Order Picker":    (18, 0.009, {"BATTERY": 3, "ELECTRICAL": 3, "TIRES": 3, "BRAKES": 2, "HYDRAULIC": 1}),
    "Electric Pallet Jack": (16, 0.006, {"BATTERY": 3, "WHEELS": 4, "CONTROLS": 2}),
    "Conveyor Section": (8, 0.008, {"BELT": 4, "MOTOR": 2, "SENSOR": 3, "BEARING": 2}),
    "Dock Leveler":    (4, 0.004, {"HYDRAULIC": 3, "LIP": 2, "CONTROLS": 1}),
}
CAUSES = {"BATTERY": ["CELL WEAR", "CHARGING", "WATERING"], "HYDRAULIC": ["SEAL LEAK", "HOSE WEAR"],
          "MAST": ["CHAIN WEAR", "ROLLER WEAR"], "TIRES": ["TREAD WEAR", "DEBRIS"], "ELECTRICAL": ["WIRING", "CONNECTOR"],
          "BRAKES": ["PAD WEAR", "ADJUSTMENT"], "WHEELS": ["BEARING WEAR", "DEBRIS"], "CONTROLS": ["SWITCH", "WIRING"],
          "BELT": ["TRACKING", "WEAR"], "MOTOR": ["OVERHEAT", "BEARING WEAR"], "SENSOR": ["MISALIGNED", "DIRT"],
          "BEARING": ["LUBRICATION", "WEAR"], "LIP": ["HINGE WEAR", "IMPACT"]}
REMEDY = {"BATTERY": "REPLACE", "HYDRAULIC": "REPAIR", "MAST": "ADJUST", "TIRES": "REPLACE", "ELECTRICAL": "REPAIR",
          "BRAKES": "ADJUST", "WHEELS": "REPLACE", "CONTROLS": "REPAIR", "BELT": "ADJUST", "MOTOR": "REPLACE",
          "SENSOR": "CLEAN", "BEARING": "LUBRICATE", "LIP": "REPAIR"}
PART_COST = {"REPLACE": (400, 2400), "REPAIR": (120, 900), "ADJUST": (0, 150), "CLEAN": (0, 40), "LUBRICATE": (10, 60)}


def pick(rng: random.Random, weights: dict) -> str:
    keys = list(weights)
    return rng.choices(keys, weights=[weights[k] for k in keys])[0]


def main() -> None:
    rng = random.Random(SEED)
    OUT.mkdir(parents=True, exist_ok=True)

    assets = []
    n = 1
    for atype, (count, _, _) in ASSET_TYPES.items():
        for _ in range(count):
            install = rng.randint(2014, 2024)
            crit = 1 if atype in ("Conveyor Section", "Order Picker") else (2 if atype != "Dock Leveler" else 3)
            assets.append({"asset_id": f"DC4-{n:03d}", "site_id": DC_ID, "asset_type": atype,
                           "install_year": install, "criticality": crit,
                           "pm_interval_days": 30, "pm_skip_prob": round(rng.uniform(0.03, 0.35), 2)})
            n += 1

    wos = []
    wo_n = 1
    days = (WO_END - WO_START).days + 1
    for a in assets:
        atype = a["asset_type"]
        _, hazard, problems = ASSET_TYPES[atype]
        age = 2026 - a["install_year"]
        # PM schedule: every 30 days, offset per asset. Some PMs are late (8-20 days) or skipped.
        pm_state = {}  # date -> "missed" flag window
        d = WO_START + timedelta(days=rng.randint(0, 29))
        while d <= WO_END:
            r = rng.random()
            if r < a["pm_skip_prob"] * 0.5:
                status, done = "SKIPPED", None
            elif r < a["pm_skip_prob"]:
                status, done = "LATE", d + timedelta(days=rng.randint(8, 20))
            else:
                status, done = "ON TIME", d + timedelta(days=rng.randint(0, 3))
            if done and done > WO_END:
                done, status = None, "OPEN"
            wos.append({"wo_id": f"WO{wo_n:06d}", "asset_id": a["asset_id"], "work_type": "PM",
                        "scheduled_date": d.isoformat(), "reported_date": d.isoformat(),
                        "completed_date": done.isoformat() if done else "", "pm_status": status,
                        "problem_code": "", "cause_code": "", "remedy_code": "",
                        "downtime_hours": round(rng.uniform(0.5, 1.5), 1) if done else 0,
                        "labor_hours": round(rng.uniform(0.75, 2.0), 2) if done else 0,
                        "parts_cost": round(rng.uniform(15, 90), 2) if done else 0})
            wo_n += 1
            if status in ("SKIPPED", "LATE"):
                for k in range(30):
                    pm_state[d + timedelta(days=k)] = True
            d += timedelta(days=a["pm_interval_days"])
        # Corrective failures.
        age_factor = 1 + 0.08 * max(0, age - 3)
        for k in range(days):
            day = WO_START + timedelta(days=k)
            h = hazard * age_factor * (2.4 if pm_state.get(day) else 1.0)
            if rng.random() < h:
                pw = dict(problems)
                if atype == "Reach Truck" and age >= 6:
                    pw["BATTERY"] = pw["BATTERY"] * 3
                prob = pick(rng, pw)
                remedy = REMEDY[prob]
                lo, hi = PART_COST[remedy]
                down = round(rng.uniform(2, 10) * (1.6 if a["criticality"] == 1 else 1.0), 1)
                done = day + timedelta(days=rng.randint(0, 2))
                wos.append({"wo_id": f"WO{wo_n:06d}", "asset_id": a["asset_id"], "work_type": "CM",
                            "scheduled_date": "", "reported_date": day.isoformat(),
                            "completed_date": done.isoformat() if done <= WO_END else "", "pm_status": "",
                            "problem_code": prob, "cause_code": rng.choice(CAUSES[prob]), "remedy_code": remedy,
                            "downtime_hours": down, "labor_hours": round(rng.uniform(1.0, 6.0), 2),
                            "parts_cost": round(rng.uniform(lo, hi), 2)})
                wo_n += 1

    # Weekly volume: seasonal, 6% yearly growth, noise.
    vol = []
    for w in range(104):
        wk = VOL_START + timedelta(weeks=w)
        doy = wk.timetuple().tm_yday
        season = 1 + 0.22 * math.exp(-((doy - 340) / 25) ** 2) + 0.10 * math.exp(-((doy - 185) / 20) ** 2)
        growth = 1.06 ** (w / 52)
        vol.append({"week_start": wk.isoformat(), "site_id": DC_ID,
                    "cases_shipped": int(410000 * season * growth * rng.uniform(0.96, 1.04))})

    # Monthly electricity: fixed load + lighting + per-case load. Lighting drops after LED retrofit.
    month_cases = {}
    for v in vol:
        y, m = int(v["week_start"][:4]), int(v["week_start"][5:7])
        month_cases[(y, m)] = month_cases.get((y, m), 0) + v["cases_shipped"]
    util = []
    for y, m in UTIL_MONTHS:
        cases = month_cases[(y, m)]
        lighting = 118000 if date(y, m, 1) <= LED_DONE else 118000 * 0.42
        kwh = int((210000 + lighting + 0.055 * cases) * rng.uniform(0.975, 1.025))
        util.append({"month_start": date(y, m, 1).isoformat(), "site_id": DC_ID,
                     "kwh": kwh, "cases_shipped": cases})

    params = {"as_of_date": WO_END.isoformat(), "wo_window_start": WO_START.isoformat(),
              "pm_followup_days": 30, "picker_cases_per_hour": 250, "truck_hours_per_week": 120,
              "forecast_start": "2026-09-28", "forecast_weeks": 13, "trend_weeks": 13,
              "led_done_date": LED_DONE.isoformat(), "led_project_cost": 245000, "usd_per_kwh": 0.21,
              "labor_usd_per_hour": 55, "operating_hours_per_day": 20}

    def write(name, rows):
        with (OUT / name).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)

    write("dim_asset.csv", assets)
    write("fact_workorder.csv", wos)
    write("fact_dc_volume_weekly.csv", vol)
    write("fact_utility_monthly.csv", util)
    write("dim_maint_params.csv", [params])
    print(f"assets={len(assets)} workorders={len(wos)} "
          f"(CM={sum(w['work_type']=='CM' for w in wos)}) weeks={len(vol)} months={len(util)}")


if __name__ == "__main__":
    main()
