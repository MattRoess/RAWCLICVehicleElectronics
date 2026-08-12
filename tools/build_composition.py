#!/usr/bin/env python3
"""Build ONE material-composition file for the stock-and-flow model.

Every model in this suite reports its own slice: wiring copper, PCB elements,
sensor elements, motor elements. A stock-and-flow model needs them in a single
table -- material mass per vehicle, per segment, per year -- the same shape as a
car-frame composition.

    python3 tools/build_composition.py

Output: Data/30_BEV_electronics_composition.csv  (+ .xlsx)

    Year, Segment, Domain, Element, Mass_g_per_vehicle, Basis

WHAT IS YEAR-RESOLVED AND WHAT IS NOT -- read this before using the numbers.

    Wiring copper     year-resolved     BevWiring
    PCB elements      year-resolved     PCBElementMC (P-f)
    Motor elements    year-resolved     static composition x motor MASS growth
    Sensor elements   year-resolved     static composition x sensor COUNT growth

The two "static composition" cases are deliberate. Composition -- what a motor
or sensor is made OF -- is not forecastable and is frozen at its 2025 value by
decision (MODEL_STATUS.md section 3). What DOES change is how many there are and
how heavy they are, and that is sourced. So mass per vehicle moves with count
and mass while the material split inside each unit stays put.

    Basis column:  "modelled"  the model itself produced the year value
                   "scaled"    2025 composition x a year-resolved driver

Everything is a MEAN per vehicle. Bands live in the source models; this file is
the central estimate a stock-and-flow model consumes.
"""

from __future__ import annotations

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

rows: list[dict] = []


def add(year, seg, domain, element, grams, basis):
    rows.append({"Year": int(year), "Segment": seg, "Domain": domain,
                 "Element": element, "Mass_g_per_vehicle": float(grams),
                 "Basis": basis})


# ---------------------------------------------------------------- 1. WIRING
def wiring():
    """Copper in the low-voltage and high-voltage harness. Year-resolved."""
    f = ROOT / "Wiring" / "outputs" / "data" / "bev_wiring_stats.csv"
    if not f.exists():
        print(f"  SKIP wiring -- {f} not found (run Wiring/BevWiring.py)")
        return
    d = pd.read_csv(f)
    cu = d[(d.get("Metric") == "Cu (kg)") & (d.get("Level") == "Total")]
    if cu.empty:
        print(f"  SKIP wiring -- no 'Cu (kg)' / 'Total' rows in {f.name}")
        return
    n = 0
    for _, r in cu.iterrows():
        seg = str(r["Segment"])
        if seg not in SEGMENTS:
            continue
        add(r["Year"], seg, "Wiring", "Cu", float(r["Mean"]) * 1000.0, "modelled")
        n += 1
    print(f"  wiring        {n:5d} rows")


# ------------------------------------------------------------ 2. PCB ELEMENTS
def pcb():
    """Element mass in printed circuit boards. Year-resolved by P-f."""
    f = ROOT / "PCBElementMC" / "csv_results" / "element_mass_totals_by_year.csv"
    if not f.exists():
        print(f"  SKIP PCB -- {f} not found (run PCBAreaMC then PCBElementMC)")
        return
    d = pd.read_csv(f)
    for _, r in d.iterrows():
        add(r["Year"], r["Segment"], "PCB", r["Element"], r["Mean_g"], "modelled")
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
    scale = {}
    for seg in SEGMENTS:
        s = mass[mass.Segment == seg].set_index("Year")["Mean"]
        if s.empty:
            continue
        scale[seg] = s / s.loc[BASE_YEAR]

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
            for el, kg in sub.groupby("Element")["Mean_mass_kg"].sum().items():
                tot[seg][el] = float(kg) * 1000.0                          # kg -> g
    if not found:
        print("  SKIP motors -- no elemental_summary.csv (run ElectricMotorElementMC.py)")
        return

    n = 0
    for seg in SEGMENTS:
        if seg not in scale:
            continue
        for el, g25 in tot[seg].items():
            for yr in YEARS:
                if yr in scale[seg].index:
                    add(yr, seg, "Motors", el, g25 * float(scale[seg].loc[yr]), "scaled")
                    n += 1
    print(f"  motors        {n:5d} rows   (2025 composition x motor-mass growth)")


# ------------------------------------------------------ 4. SENSOR ELEMENTS
def sensors():
    """Sensor element mass = static composition x year-resolved sensor COUNT.

    SensorElementsMC is static by decision (composition is not forecastable),
    but SensorNumbersMC gives the count trajectory. Mass per vehicle therefore
    moves with count while the split inside each sensor stays at 2025.
    """
    cf = ROOT / "SensorNumbersMC" / "csv_results" / "sensor_counts_by_year.csv"
    counts = None
    if cf.exists():
        c = pd.read_csv(cf)
        col = "Mean" if "Mean" in c.columns else c.columns[-1]
        counts = {seg: c[c.Segment == seg].set_index("Year")[col] for seg in SEGMENTS
                  if (c.Segment == seg).any()}

    n = 0
    for seg in SEGMENTS:
        f = (ROOT / "SensorElementsMC" / "csv_monte_carlo"
             / f"element_monte_carlo_{seg}_summary_stats.csv")
        if not f.exists():
            print(f"  SKIP sensors {seg} -- {f.name} not found")
            continue
        d = pd.read_csv(f)
        ecol = "Element" if "Element" in d.columns else d.columns[0]
        mcol = "mean" if "mean" in d.columns else "Mean"
        for _, r in d.iterrows():
            # SensorElementsMC reports MILLIGRAMS -- Cu at ~69,000 is 69 g, not
            # 69 kg. Read as grams this inflated the whole file ~1000x.
            g25 = float(r[mcol]) / 1000.0
            if counts and seg in counts and BASE_YEAR in counts[seg].index:
                s = counts[seg] / counts[seg].loc[BASE_YEAR]
                for yr in YEARS:
                    if yr in s.index:
                        add(yr, seg, "Sensors", r[ecol], g25 * float(s.loc[yr]), "scaled")
                        n += 1
            else:
                # No count trajectory available -- hold the 2025 value flat and
                # SAY SO, rather than silently implying it was modelled.
                for yr in YEARS:
                    add(yr, seg, "Sensors", r[ecol], g25, "static-2025")
                    n += 1
    print(f"  sensors       {n:5d} rows")


def main():
    print("Building the combined composition file\n")
    wiring(); pcb(); motors(); sensors()

    if not rows:
        sys.exit("No inputs found -- run the models first (see docs/USER_GUIDE.md).")

    df = pd.DataFrame(rows)
    df = (df.groupby(["Year", "Segment", "Domain", "Element", "Basis"],
                     as_index=False)["Mass_g_per_vehicle"].sum()
            .sort_values(["Year", "Segment", "Domain", "Element"]))
    df.to_csv(OUT_CSV, index=False)
    with pd.ExcelWriter(OUT_XLSX) as xl:
        df.to_excel(xl, sheet_name="Composition", index=False)
        (df[df.Year == BASE_YEAR].pivot_table(index="Element", columns="Segment",
                                              values="Mass_g_per_vehicle", aggfunc="sum")
           .to_excel(xl, sheet_name=f"Pivot_{BASE_YEAR}"))

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
