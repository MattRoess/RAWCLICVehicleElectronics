#!/usr/bin/env python3
"""Build ONE material-composition file for the stock-and-flow model.

Every model in this suite reports its own slice: wiring copper, PCB elements,
sensor elements, motor elements. A stock-and-flow model needs them in a single
table -- material mass per vehicle, per segment, per year -- the same shape as a
car-frame composition.

    python3 tools/build_composition.py

Output: Data/30_BEV_electronics_composition.csv  (+ .xlsx)

    Year, Segment, Domain, Component_Type, Element, Mass_g_per_vehicle,
    Basis, Histogram_File

COMPONENT_TYPE is the split needed for detailed work:

    Wiring    functional group -- HV Power, LV Power, Signal/Comm, ADAS/Sensor,
              Specialized
    PCB       PCB category x board size -- e.g. "PE_HVS / medium"
    Motors    motor type -- SmallStepperMotors, MediumStepperMotors,
              MediumDCMotors_metal, MediumDCMotors_plastic
    Sensors   sensor type -- temperature, pressure, accelerometer, camera, ...
              59 types. An earlier version of this file claimed sensor type was
              NOT resolvable; that was wrong. 07_ holds per-SensorType element
              masses and sensor_year_stats.csv holds counts by type per year, so
              mass per type is a direct product -- "modelled", not "scaled".

HISTOGRAM_FILE points at the probability density function behind each series --
the 50-bin histogram CSV the models export. Empty where the model does not emit
a per-series histogram.

WHAT IS YEAR-RESOLVED AND WHAT IS NOT -- read this before using the numbers.

    Wiring copper     year-resolved     BevWiring
    PCB elements      year-resolved     PCBElementMC (P-f)
    Motor elements    year-resolved     static composition x motor MASS growth
    Sensor elements   year-resolved     count(type, year) x composition(type)

The two "static composition" cases are deliberate. Composition -- what a motor
or sensor is made OF -- is not forecastable and is frozen at its 2025 value by
decision (02_MODEL_STATUS.md section 3). What DOES change is how many there are and
how heavy they are, and that is sourced. So mass per vehicle moves with count
and mass while the material split inside each unit stays put.

    Basis column:  "modelled"  the model itself produced the year value
                   "scaled"    2025 composition x a year-resolved driver

Everything is a MEAN per vehicle. Bands live in the source models; this file is
the central estimate a stock-and-flow model consumes.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT_CSV = ROOT / "Data" / "30_BEV_electronics_composition.csv"
OUT_XLSX = ROOT / "Data" / "30_BEV_electronics_composition.xlsx"
SEGMENTS = ["AB", "CD", "EF"]
YEARS = np.arange(2020, 2071)
BASE_YEAR = 2025

VAL_C, LO_C, HI_C = "Mass_g_per_vehicle", "P2_5_g", "P97_5_g"

rows: list[dict] = []


def add(year, seg, domain, element, grams, basis, ctype="", hist="",
        lo=None, hi=None, band=""):
    """band: what the P2.5/P97.5 columns actually represent, per row.

    This is a Monte Carlo model and the range is the point, so the deliverable
    carries it. But the band does not mean the same thing in every domain, and
    saying so per row is better than a footnote nobody reads.
    """
    rows.append({"Year": int(year), "Segment": seg, "Domain": domain,
                 "Component_Type": ctype, "Element": element,
                 "Mass_g_per_vehicle": float(grams),
                 "P2_5_g": float(lo) if lo is not None else float("nan"),
                 "P97_5_g": float(hi) if hi is not None else float("nan"),
                 "Basis": basis, "Band_meaning": band, "Histogram_File": hist})


# ---------------------------------------------------------------- 1. WIRING
def wiring():
    """Copper in the low-voltage and high-voltage harness. Year-resolved."""
    f = ROOT / "Wiring" / "outputs" / "data" / "bev_wiring_stats.csv"
    if not f.exists():
        print(f"  SKIP wiring -- {f} not found (run Wiring/BevWiring.py)")
        return
    d = pd.read_csv(f)
    # Group level, not Total -- Total would discard the functional split
    # (HV Power / LV Power / Signal-Comm / ADAS-Sensor / Specialized).
    cu = d[(d.get("Metric") == "Cu (kg)") & (d.get("Level") == "Group")]
    if cu.empty:
        print(f"  SKIP wiring -- no 'Cu (kg)' / 'Group' rows in {f.name}")
        return
    n = 0
    for _, r in cu.iterrows():
        seg = str(r["Segment"])
        if seg not in SEGMENTS:
            continue
        add(r["Year"], seg, "Wiring", "Cu", float(r["Mean"]) * 1000.0, "modelled",
            ctype=str(r["Code"]),
            hist="Wiring/outputs/data/bev_wiring_histograms.csv",
            lo=float(r["P2_5"]) * 1000.0, hi=float(r["P97_5"]) * 1000.0,
            band="full model band")
        n += 1
    print(f"  wiring        {n:5d} rows")


# ------------------------------------------------------------ 2. PCB ELEMENTS
def pcb():
    """Element mass in printed circuit boards. Year-resolved by P-f."""
    # The DETAILED file, not the totals -- totals discard Category and Size.
    f = ROOT / "PCBElementMC" / "csv_results" / "element_mass_by_year.csv"
    if not f.exists():
        print(f"  SKIP PCB -- {f} not found (run PCBAreaMC then PCBElementMC)")
        return
    d = pd.read_csv(f)
    for _, r in d.iterrows():
        cat, size = str(r["Category"]), str(r["Size"])
        add(r["Year"], r["Segment"], "PCB", r["Element"], r["Mean_g"], "modelled",
            ctype=f"{cat} / {size}",
            hist=f"PCBAreaMC/histograms/histogram_{r['Segment']}_{cat}_{size}_area.csv",
            lo=r["P025_g"], hi=r["P975_g"], band="full model band")
    print(f"  PCB           {len(d):5d} rows")


# ------------------------------------------------------- 3. MOTOR ELEMENTS
def motors():
    """Motor element mass = static composition x year-resolved motor MASS.

    ElectricMotorElementMC is static by decision, so it gives the 2025 material
    split. ElectricMotorMC gives the year trajectory of total motor mass. The
    product is exact rather than an approximation, because composition carries
    no year dimension -- the same argument that made P-f exact for PCB.
    """
    yf = ROOT / "ElectricMotorMC" / "summary_csv" / "motor_counts_by_year.csv"
    if not yf.exists():
        print(f"  SKIP motors -- {yf} not found (run ElectricMotorMC.py)")
        return
    y = pd.read_csv(yf)
    mass = y[y.Quantity == "mass"]
    scale, scale_lo, scale_hi = {}, {}, {}
    for seg in SEGMENTS:
        m = mass[mass.Segment == seg].set_index("Year")
        if m.empty:
            continue
        base = m["Mean"].loc[BASE_YEAR]
        scale[seg] = m["Mean"] / base
        # The band here is the MOTOR MASS band only -- how many motors and how
        # heavy. Composition is frozen at 2025 by decision, so its own
        # uncertainty is NOT included. Labelled per row rather than buried.
        scale_lo[seg] = m["P025"] / base
        scale_hi[seg] = m["P975"] / base

    # Case encodes BOTH segment and motor type, e.g. "EF_MediumDCMotors_metal".
    # Filter to the segment, then SUM its four motor types -- averaging across
    # cases would hand every segment the same motor content, which is wrong by
    # roughly 4x between AB and EF.
    # ElectricMotorElementMC writes the SAME combined summary into every stream
    # folder ("Combined summary -> elemental_summary.csv in all summary_csv
    # folders"). Globbing all four counted every element 4x. Read ONE.
    files = sorted(ROOT.glob("ElectricMotorElementMC/*/summary_csv/elemental_summary.csv"))
    tot: dict[str, dict[str, float]] = {s: {} for s in SEGMENTS}
    found = bool(files)
    if found:
        d = pd.read_csv(files[0])
        for seg in SEGMENTS:
            sub = d[d["Case"].astype(str).str.startswith(seg + "_")]
            # keep the motor TYPE; Case is "{seg}_{type}". TOTAL_* rows do not
            # match the prefix and are correctly excluded.
            for (case, el), kg in sub.groupby(["Case", "Element"])["Mean_mass_kg"].sum().items():
                mtype = str(case).split("_", 1)[1]
                tot[seg][(mtype, el)] = float(kg) * 1000.0                 # kg -> g
    if not found:
        print("  SKIP motors -- no elemental_summary.csv (run ElectricMotorElementMC.py)")
        return

    n = 0
    for seg in SEGMENTS:
        if seg not in scale:
            continue
        for (mtype, el), g25 in tot[seg].items():
            hist = f"ElectricMotorMC/materials_histograms_csv/hist_{seg}_{mtype}_mass.csv"
            for yr in YEARS:
                if yr in scale[seg].index:
                    add(yr, seg, "Motors", el, g25 * float(scale[seg].loc[yr]),
                        "scaled", ctype=mtype, hist=hist,
                        lo=g25 * float(scale_lo[seg].loc[yr]),
                        hi=g25 * float(scale_hi[seg].loc[yr]),
                        band="motor count/mass only; composition fixed")
                    n += 1
    print(f"  motors        {n:5d} rows   (2025 composition x motor-mass growth)")


# ------------------------------------------------------ 4. SENSOR ELEMENTS
def sensors():
    """Element mass PER SENSOR TYPE per year.

        mass(element, sensor type, seg, year)
            = count(sensor type, seg, year) x composition(element | sensor type)

    Both halves exist and are used directly, so this is fully resolved by
    sensor type (temperature, pressure, camera, radar, ...) rather than an
    aggregate:

        counts        SensorNumbersMC/csv_results/sensor_year_stats.csv
                      rows with Level == "SensorType", year-resolved
        composition   07_VehicleSensorComposition.xlsx, sheet "Sensor Details",
                      per-element mg per sensor, Min/Mode/Max

    Composition is the 2025 value and is held constant by decision -- what a
    sensor is MADE OF is not forecastable (02_MODEL_STATUS.md section 3). What
    changes is HOW MANY there are, and that is modelled. Mode is used here;
    the Min/Max band lives in the source models.
    """
    cf = ROOT / "SensorNumbersMC" / "csv_monte_carlo" / "sensor_year_stats.csv"
    comp_f = ROOT / "Data" / "07_VehicleSensorComposition.xlsx"
    if not cf.exists() or not comp_f.exists():
        print(f"  SKIP sensors -- need {cf.name} and {comp_f.name}")
        return

    c = pd.read_csv(cf)
    c = c[c["Level"].astype(str) == "SensorType"]

    comp = pd.read_excel(comp_f, sheet_name="Sensor Details")
    elements = sorted({m.group(1) for col in comp.columns
                       if (m := re.match(r"^([A-Z][a-z]?)_mode_mg$", str(col)))})
    comp["_key"] = comp["SensorType"].astype(str).str.strip().str.lower()
    lut = {r["_key"]: {el: float(r.get(f"{el}_mode_mg", 0) or 0) for el in elements}
           for _, r in comp.iterrows()}

    n, unmatched = 0, set()
    for seg in SEGMENTS:
        sub = c[c["Segment"] == seg]
        for stype, g in sub.groupby("Name"):
            key = str(stype).strip().lower()
            if key not in lut:
                unmatched.add(str(stype))
                continue
            per = lut[key]
            for _, r in g.iterrows():
                cnt = float(r["Mean"])
                clo, chi = float(r.get("P025", np.nan)), float(r.get("P975", np.nan))
                for el, mg in per.items():
                    if mg > 0:
                        add(r["Year"], seg, "Sensors", el, cnt * mg / 1000.0,
                            "modelled", ctype=str(stype),
                            hist="SensorNumbersMC/csv_monte_carlo/sensor_year_stats.csv",
                            lo=clo * mg / 1000.0, hi=chi * mg / 1000.0,
                            band="sensor count only; composition fixed")
                        n += 1
    print(f"  sensors       {n:5d} rows   (per sensor type x year)")
    if unmatched:
        print(f"    NOTE {len(unmatched)} sensor type(s) in the count file have no "
              f"07_ composition and are omitted: {sorted(unmatched)[:6]}")


def main():
    print("Building the combined composition file\n")
    wiring(); pcb(); motors(); sensors()

    if not rows:
        sys.exit("No inputs found -- run the models first (see docs/01_USER_GUIDE.md).")

    df = pd.DataFrame(rows)
    # Percentiles do NOT add across independent series -- summing P2.5 would
    # imply every component sits at its low simultaneously. Rows are already at
    # the finest grain, so nothing is aggregated here; the grouping only removes
    # exact duplicates.
    df = (df.groupby(["Year", "Segment", "Domain", "Component_Type", "Element",
                      "Basis", "Band_meaning", "Histogram_File"], as_index=False)
            [["Mass_g_per_vehicle", "P2_5_g", "P97_5_g"]].sum()
            .sort_values(["Year", "Segment", "Domain", "Component_Type", "Element"]))
    # Enforce P2.5 <= mean <= P97.5.
    #
    # Some sensor counts are effectively DETERMINISTIC -- exactly one belt-buckle
    # sensor per seat -- so the distribution is a point mass and Monte Carlo
    # noise puts P2.5 a few parts per million ABOVE the mean. Harmless in
    # itself, but it produced negative error bars downstream and would confuse
    # anyone consuming the file. Clipping keeps the deliverable self-consistent;
    # the adjustment is ~1e-6 relative and only touches degenerate series.
    n_clip = int(((df[LO_C] > df[VAL_C]) | (df[HI_C] < df[VAL_C])).sum())
    df[LO_C] = np.minimum(df[LO_C], df[VAL_C])
    df[HI_C] = np.maximum(df[HI_C], df[VAL_C])
    if n_clip:
        print(f"  clipped {n_clip:,} degenerate band(s) so P2.5 <= mean <= P97.5")

    df.to_csv(OUT_CSV, index=False)
    # The CSV is the deliverable. The workbook is a convenience and is now large
    # enough that writing it into iCloud Drive can time out -- never let that
    # failure take the CSV down with it.
    try:
        with pd.ExcelWriter(OUT_XLSX) as xl:
            df.to_excel(xl, sheet_name="Composition", index=False)
            (df[df.Year == BASE_YEAR]
               .pivot_table(index=["Domain", "Component_Type", "Element"],
                            columns="Segment", values="Mass_g_per_vehicle",
                            aggfunc="sum")
               .to_excel(xl, sheet_name=f"Pivot_{BASE_YEAR}"))
    except Exception as e:
        print(f"  (xlsx not written: {type(e).__name__} -- the CSV above is complete)")

    print(f"\n  -> {OUT_CSV.relative_to(ROOT)}   ({len(df):,} rows)")
    print(f"  -> {OUT_XLSX.relative_to(ROOT)}")

    print(f"\n  Total electronics material per vehicle, grams:")
    print(f"    {'seg':5}{'2025':>12}{'2070':>12}{'change':>10}")
    for seg in SEGMENTS:
        s = df[df.Segment == seg].groupby("Year")["Mass_g_per_vehicle"].sum()
        if BASE_YEAR in s.index and 2070 in s.index:
            a, b = s.loc[BASE_YEAR], s.loc[2070]
            print(f"    {seg:5}{a:12,.0f}{b:12,.0f}{b/a - 1:+9.1%}")
    print("\n  By domain at 2025 (g/vehicle):")
    p = df[df.Year == BASE_YEAR].pivot_table(index="Domain", columns="Segment",
                                             values="Mass_g_per_vehicle", aggfunc="sum")
    print(p.round(0).to_string())


if __name__ == "__main__":
    main()
