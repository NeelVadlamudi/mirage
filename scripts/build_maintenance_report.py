#!/usr/bin/env python3
"""
Mirage maintenance module: one-page PDF report for the facilities manager.

Reads data/maint/extracts/*.csv (built by export_maintenance_extracts.py) and writes
docs/maintenance_report.pdf. Four panels, each answering one question, with the number
to act on in its title.

  pip install matplotlib
  python3 scripts/build_maintenance_report.py
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
X = ROOT / "data" / "maint" / "extracts"
OUT = ROOT / "docs" / "maintenance_report.pdf"

BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"


def read(name: str) -> list[dict]:
    with (X / f"{name}.csv").open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def style(ax) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def title(ax, head: str, sub: str) -> None:
    ax.set_title(head, loc="left", fontsize=10.5, color=INK, fontweight="bold", pad=18)
    ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=8, color=INK2)


def main() -> None:
    plt.rcParams["font.family"] = "DejaVu Sans"
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.5), facecolor=SURFACE)
    fig.subplots_adjust(left=0.07, right=0.97, top=0.86, bottom=0.08, hspace=0.55, wspace=0.25)
    fig.text(0.07, 0.945, "warehouse_4 (DC) maintenance report", fontsize=16, fontweight="bold", color=INK)
    fig.text(0.07, 0.915, "Work orders 2025-09-22 to 2026-09-21. Synthetic data. "
             "Every number is rechecked by scripts/verify_maintenance.py.", fontsize=9, color=INK2)

    # 1. PM follow-up.
    ax = axes[0][0]
    style(ax)
    pm = {r["pm_group"]: r for r in read("v_pm_followup")}
    mc = read("v_pm_missed_cost")[0]
    labels = ["PM done on time", "PM missed or late"]
    vals = [float(pm["ON TIME"]["breakdown_rate"]) * 100, float(pm["MISSED OR LATE"]["breakdown_rate"]) * 100]
    ax.bar(labels, vals, color=[BLUE, ORANGE], width=0.5)
    for i, v in enumerate(vals):
        ax.text(i, v + 1.2, f"{v:.0f}%", ha="center", fontsize=9, color=INK)
    ax.set_ylim(0, 60)
    ax.set_ylabel("PMs followed by a breakdown\nwithin 30 days (%)", fontsize=8, color=INK2)
    title(ax, f"Missed PMs nearly doubled the breakdown rate",
          f"About {float(mc['extra_breakdowns']):.0f} extra breakdowns, \\${float(mc['extra_cost_usd']):,.0f} "
          f"and {float(mc['extra_downtime_hours']):.0f} downtime hours")

    # 2. Reach truck batteries.
    ax = axes[0][1]
    style(ax)
    fp = {r["age_band"]: r for r in read("v_failure_patterns")
          if r["asset_type"] == "Reach Truck" and r["problem_code"] == "BATTERY"}
    labels = [f"Under 6 years ({fp['under 6 years']['asset_count']} trucks)",
              f"6+ years ({fp['6+ years']['asset_count']} trucks)"]
    vals = [float(fp["under 6 years"]["cm_per_asset"]), float(fp["6+ years"]["cm_per_asset"])]
    ax.bar(labels, vals, color=[BLUE, ORANGE], width=0.5)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.08, f"{v:.1f}", ha="center", fontsize=9, color=INK)
    ax.set_ylim(0, 3.8)
    ax.set_ylabel("Battery breakdowns per truck\nin 12 months", fontsize=8, color=INK2)
    title(ax, f"Older reach trucks: {vals[1] / vals[0]:.1f}x the battery failures",
          "Candidate list for battery replacement before the holiday peak")

    # 3. Fleet need.
    ax = axes[1][0]
    style(ax)
    fc = read("v_fleet_need_forecast")
    weeks = [r["forecast_week"][5:] for r in fc]
    need = [int(r["pickers_needed"]) for r in fc]
    fleet = int(fc[0]["picker_count"])
    x = range(len(weeks))
    ax.plot(x, need, color=BLUE, linewidth=2, marker="o", markersize=5, label="Order pickers needed")
    ax.axhline(fleet, color=ORANGE, linewidth=2, label=f"Fleet on hand ({fleet})")
    ax.set_xticks(list(x))
    ax.set_xticklabels(weeks, rotation=45, fontsize=7)
    ax.set_ylim(12, 22)
    ax.set_ylabel("Trucks", fontsize=8, color=INK2)
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    short = [n - fleet for n in need if n > fleet]
    title(ax, f"Short up to {max(short)} order pickers in {len(short)} peak weeks",
          f"Forecast = same week last year x {float(fc[0]['growth']) - 1:.1%} growth; week starting (MM-DD)")

    # 4. Energy.
    ax = axes[1][1]
    style(ax)
    ub = read("v_utility_baseline")
    roi = read("v_utility_roi")[0]
    months = [r["month_start"][:7] for r in ub]
    actual = [float(r["kwh"]) / 1000 for r in ub]
    base = [float(r["baseline_kwh"]) / 1000 for r in ub]
    x = range(len(months))
    ax.plot(x, base, color=ORANGE, linewidth=2, label="Baseline (no retrofit)")
    ax.plot(x, actual, color=BLUE, linewidth=2, label="Actual")
    cut = sum(1 for r in ub if r["period"] == "BEFORE") - 0.5
    ax.axvline(cut, color=MUTED, linewidth=1, linestyle=":")
    ax.text(cut + 0.2, max(base) * 0.99, "LED retrofit done", fontsize=7.5, color=INK2, va="top")
    ax.set_xticks(list(x)[::3])
    ax.set_xticklabels(months[::3], rotation=45, fontsize=7)
    ax.set_ylabel("Electricity (MWh per month)", fontsize=8, color=INK2)
    ax.legend(fontsize=8, frameon=False, loc="lower left")
    title(ax, f"LED retrofit pays back in {float(roi['payback_months']):.1f} months",
          f"{float(roi['savings_share']):.1%} below baseline, "
          f"\\${float(roi['annual_savings_usd']):,.0f} a year on a \\${float(roi['led_project_cost']):,.0f} project")

    fig.savefig(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
