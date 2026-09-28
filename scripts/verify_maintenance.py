#!/usr/bin/env python3
"""
Mirage maintenance module: check the extracts without SQL Server or DuckDB.

Recomputes every headline number from data/maint/*.csv with plain Python and compares it to
data/maint/extracts/*.csv:
  - breakdown rate within 30 days after on-time vs missed or late PMs, and the extra cost
  - reach truck battery failures per truck, 6+ years old vs newer
  - order pickers needed per week for the next 13 weeks
  - LED retrofit savings, payback and ROI from a least-squares energy baseline
Stdlib only. Exit 0 on PASS, 1 on FAIL.
"""
from __future__ import annotations

import csv
import math
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
M = ROOT / "data" / "maint"
X = M / "extracts"


def read(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def d(s: str) -> date:
    return date.fromisoformat(s)


def fail(msg: str) -> None:
    print(f"FAIL  {msg}")
    sys.exit(1)


def close(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) <= tol * max(1.0, abs(b))


def main() -> None:
    p = read(M / "dim_maint_params.csv")[0]
    as_of, start = d(p["as_of_date"]), d(p["wo_window_start"])
    follow = int(p["pm_followup_days"])
    labor = float(p["labor_usd_per_hour"])
    assets = read(M / "dim_asset.csv")
    wos = [w for w in read(M / "fact_workorder.csv") if start <= d(w["reported_date"]) <= as_of]
    cms = [w for w in wos if w["work_type"] == "CM"]

    # 1. PM follow-up.
    cm_by_asset: dict[str, list[date]] = {}
    for w in cms:
        cm_by_asset.setdefault(w["asset_id"], []).append(d(w["reported_date"]))
    groups = {"ON TIME": [0, 0], "MISSED OR LATE": [0, 0]}
    for w in wos:
        if w["work_type"] != "PM" or w["pm_status"] not in ("ON TIME", "LATE", "SKIPPED"):
            continue
        s = d(w["scheduled_date"])
        if s < start or s + timedelta(days=follow) > as_of:
            continue
        g = "ON TIME" if w["pm_status"] == "ON TIME" else "MISSED OR LATE"
        hit = any(s < c <= s + timedelta(days=follow) for c in cm_by_asset.get(w["asset_id"], []))
        groups[g][0] += 1
        groups[g][1] += int(hit)
    rate = {g: v[1] / v[0] for g, v in groups.items()}
    for r in read(X / "v_pm_followup.csv"):
        g = r["pm_group"]
        if int(r["pm_count"]) != groups[g][0] or not close(float(r["breakdown_rate"]), rate[g]):
            fail(f"v_pm_followup {g} differs")
    avg_cost = sum(float(w["parts_cost"]) + float(w["labor_hours"]) * labor for w in cms) / len(cms)
    extra = groups["MISSED OR LATE"][0] * (rate["MISSED OR LATE"] - rate["ON TIME"])
    mc = read(X / "v_pm_missed_cost.csv")[0]
    if not (close(float(mc["extra_breakdowns"]), extra) and close(float(mc["extra_cost_usd"]), extra * avg_cost)):
        fail("v_pm_missed_cost differs")
    print(f"PASS  breakdown within {follow} days: on-time PM {rate['ON TIME']:.1%}, "
          f"missed or late {rate['MISSED OR LATE']:.1%} ({rate['MISSED OR LATE'] / rate['ON TIME']:.1f}x); "
          f"{extra:.0f} extra breakdowns, ${extra * avg_cost:,.0f}")

    # 2. Reach truck battery failures by age band.
    yr = as_of.year
    band = {a["asset_id"]: ("6+ years" if yr - int(a["install_year"]) >= 6 else "under 6 years")
            for a in assets if a["asset_type"] == "Reach Truck"}
    per = {}
    for b in ("6+ years", "under 6 years"):
        n_assets = sum(1 for v in band.values() if v == b)
        n_cm = sum(1 for w in cms if w["asset_id"] in band and band[w["asset_id"]] == b and w["problem_code"] == "BATTERY")
        per[b] = n_cm / n_assets
    for r in read(X / "v_failure_patterns.csv"):
        if r["asset_type"] == "Reach Truck" and r["problem_code"] == "BATTERY":
            if not close(float(r["cm_per_asset"]), per[r["age_band"]]):
                fail(f"v_failure_patterns reach truck battery {r['age_band']} differs")
    print(f"PASS  reach truck battery failures per truck: 6+ years {per['6+ years']:.2f}, "
          f"under 6 years {per['under 6 years']:.2f} ({per['6+ years'] / per['under 6 years']:.1f}x)")

    # 3. Fleet need forecast.
    vol = {d(v["week_start"]): int(v["cases_shipped"]) for v in read(M / "fact_dc_volume_weekly.csv")}
    tw = int(p["trend_weeks"])
    recent = sum(c for w, c in vol.items() if as_of - timedelta(days=7 * tw) <= w < as_of)
    ago = sum(c for w, c in vol.items() if as_of - timedelta(days=7 * tw + 364) <= w < as_of - timedelta(days=364))
    growth = recent / ago
    days_in = (as_of - start).days + 1
    oph = int(p["operating_hours_per_day"])
    pick_avail = []
    for a in assets:
        if a["asset_type"] != "Order Picker":
            continue
        down = sum(float(w["downtime_hours"]) for w in wos if w["asset_id"] == a["asset_id"])
        pick_avail.append(1 - down / (days_in * oph))
    avail = sum(pick_avail) / len(pick_avail)
    fstart, fw = d(p["forecast_start"]), int(p["forecast_weeks"])
    cph, hpw = int(p["picker_cases_per_hour"]), int(p["truck_hours_per_week"])
    need = {}
    for w, c in vol.items():
        fwk = w + timedelta(days=364)
        if fstart <= fwk < fstart + timedelta(days=7 * fw):
            need[fwk] = math.ceil(c * growth / cph / (hpw * avail))
    got = {d(r["forecast_week"]): int(r["pickers_needed"]) for r in read(X / "v_fleet_need_forecast.csv")}
    if got != need:
        fail(f"v_fleet_need_forecast differs: {got} vs {need}")
    fleet = len(pick_avail)
    short = {w: n - fleet for w, n in need.items() if n > fleet}
    print(f"PASS  order pickers: growth {growth - 1:.1%}, fleet {fleet}, short in {len(short)} of {fw} weeks, "
          f"worst {max(short.values()) if short else 0} short")

    # 4. LED retrofit.
    util = read(M / "fact_utility_monthly.csv")
    led = d(p["led_done_date"])
    pre = [(float(u["cases_shipped"]), float(u["kwh"])) for u in util if d(u["month_start"]) <= led]
    n = len(pre)
    sx, sy = sum(x for x, _ in pre), sum(y for _, y in pre)
    sxy, sxx = sum(x * y for x, y in pre), sum(x * x for x, _ in pre)
    slope = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    base = lambda x: sy / n + slope * (x - sx / n)
    post = [(float(u["cases_shipped"]), float(u["kwh"])) for u in util if d(u["month_start"]) > led]
    sav_kwh = sum(base(x) - y for x, y in post)
    sav_usd = sav_kwh * float(p["usd_per_kwh"])
    annual = 12 * sav_usd / len(post)
    payback = float(p["led_project_cost"]) / (sav_usd / len(post))
    share = sav_kwh / sum(base(x) for x, _ in post)
    roi = read(X / "v_utility_roi.csv")[0]
    if not (close(float(roi["savings_kwh"]), sav_kwh) and close(float(roi["payback_months"]), payback)):
        fail("v_utility_roi differs")
    print(f"PASS  LED retrofit: {share:.1%} less energy than baseline, ${annual:,.0f} a year, "
          f"payback {payback:.1f} months")

    print()
    print("ALL PASS - maintenance module")


if __name__ == "__main__":
    main()
