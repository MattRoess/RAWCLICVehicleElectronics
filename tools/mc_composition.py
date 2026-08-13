#!/usr/bin/env python3
"""The JOINT Monte Carlo — one simulated car through all four domains.

    python3 tools/mc_composition.py [n_iter]

Writes  Composition/csv/joint_mc_stats.csv        mean, P2.5, median, P97.5
        Composition/csv/joint_mc_histograms.csv   50 bins per series-year

WHY THIS EXISTS. The composition band used to be built by taking each domain's
mean/P2.5/P97.5, inventing a lognormal that matched those three numbers, drawing
from the invention, and summing the four domains as independent. The models' own
draws never entered. See docs/12_JOINT_MC_DESIGN.md §1.

WHAT THIS DOES INSTEAD. One vehicle at a time, through every domain:

    st    = draw_vehicle_state(rng, m)     the shared drivers, drawn ONCE
    total = wiring(st) + sensors(st) + pcb(st) + motors(st)
    acc.add(total)                         summed PER DRAW, then binned

Because the same `st` goes to all four models, a car that is zonal, 800 V and
carrying H4 hardware is all of those things in its harness AND its sensor count
AND its boards AND its motors -- at the same time, in the same draw. The
correlation is then in the sum by construction, rather than being asserted or
ignored afterwards.

THE BAND IS WIDER THAN INDEPENDENT SUMMING AND NARROWER THAN THE COMONOTONIC
BOUND, and where it falls between them is the answer, not an assumption.

WHAT IS SHARED AND WHAT IS NOT: tools/vehicle_state.py. Short version -- the
drivers more than one model reads (architecture, ADAS tier, 800 V, scenario,
lidar) are drawn here and injected; everything private to a model (wire gauge,
board dimensions, motor mass, the count within each sensor row's min-max) stays
inside that model and is still drawn there.

MEMORY is independent of n_iter: draws are summed per chunk and pushed into the
shared fixed-bin Accumulator, exactly as the individual models do. Raising
n_iter costs time, never memory.

THE FOUR MASS MAPPINGS, and why each is exact rather than a fit:

    Wiring    the model reports Cu directly, in kg. x1000 -> g.

    Sensors   count(type) x composition(type). 07_ gives mg per element per
              sensor type and the chunk gives per-draw counts by type, so the
              product is exact. Composition is frozen at 2025 by decision
              (02_MODEL_STATUS.md §3) -- what a sensor is MADE OF is not
              forecastable; how many there are is modelled.

    PCB       area x (g per cm2). PCBElementMC builds element mass FROM area, so
              the ratio is a constant of that model, not a regression: measured
              across all years it moves by 0.08% (0.032930-0.032956 g/cm2 on
              CD). Taken per segment.

    Motors    2025 element mass x that vehicle's growth trajectory. The 2025
              per-draw masses are the motor model's OWN 200,000 draws, read from
              samples_csv/*.npy -- not a distribution refitted to its summary
              statistics. Legitimate to read from disk rather than redraw
              because the 2025 motor mass shares no driver with any other
              domain; only the growth trajectory does, through u_scen, and that
              IS drawn here and injected.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "Wiring"))
sys.path.insert(0, str(ROOT / "SensorNumbersMC"))
sys.path.insert(0, str(ROOT / "PCBAreaMC"))
sys.path.insert(0, str(ROOT / "ElectricMotorMC"))

from accumulator import Accumulator, N_HIST_BINS          # noqa: E402
from drivers import load_lidar_bands                      # noqa: E402
from vehicle_state import draw_vehicle_state              # noqa: E402

# ---------------------------------------------------------------- parameters

N_ITER = 200_000     # vehicles simulated per segment. UNIT: draws. Memory does
                     # not scale with this; runtime does, linearly.
CHUNK = 2_000        # vehicles simulated at once. UNIT: draws. Peak memory is
                     # set by THIS. The wiring model holds
                     # (chunk x 28 categories x 51 years) per metric, so 2,000
                     # is about 45 MB there and everything else is smaller.
SEED = 20260813      # one seed for the whole joint run, so the composition is
                     # reproducible end to end from this single number.

SEGMENTS = ["AB", "CD", "EF"]
DOMAINS = ["Wiring", "Sensors", "PCB", "Motors"]
YEARS = np.arange(2020, 2071)
BASE_YEAR = 2025
I_BASE = int(np.searchsorted(YEARS, BASE_YEAR))

OUT = ROOT / "Composition" / "csv"
OUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------- composition factors

def sensor_mg_per_type():
    """{sensor type (lowercased): mg of material in one sensor of that type}.

    Summed over every element 07_ reports. Mode is used; the Min/Max band lives
    in the source model. Types with no 07_ row return nothing and are skipped by
    the caller -- silently dropping them would understate sensor mass, so the
    caller reports the count.
    """
    import re
    f = ROOT / "Data" / "07_VehicleSensorComposition.xlsx"
    comp = pd.read_excel(f, sheet_name="Sensor Details")
    els = sorted({m.group(1) for c in comp.columns
                  if (m := re.match(r"^([A-Z][a-z]?)_mode_mg$", str(c)))})
    out = {}
    for _, r in comp.iterrows():
        key = str(r["SensorType"]).strip().lower()
        out[key] = float(sum(float(r.get(f"{e}_mode_mg", 0) or 0) for e in els))
    return out


def pcb_g_per_cm2():
    """{segment: grams of element material per cm2 of board}.

    PCBElementMC derives element mass FROM area, so this ratio is a constant of
    that model rather than a fitted relationship. Taken at BASE_YEAR; the
    year-to-year drift is 0.08%.
    """
    e = pd.read_csv(ROOT / "PCBElementMC" / "csv_results" / "element_mass_by_year.csv")
    tot = e.groupby(["Segment", "Year"])["Mean_g"].sum()
    out = {}
    for seg in SEGMENTS:
        a = pd.read_csv(ROOT / "PCBAreaMC" / "csv_monte_carlo"
                        / f"pcb_year_resolved_{seg}.csv").set_index("Year")
        out[seg] = float(tot.loc[(seg, BASE_YEAR)] / a.loc[BASE_YEAR, "Mean"])
    return out


def motor_2025():
    """({segment: (n,) per-draw 2025 motor mass in kg},
        {segment: total 2025 element mass in g}).

    The per-draw masses are the motor model's own draws from
    ElectricMotorMC/samples_csv/*.npy, summed over the four motor types. Column
    2 is total_mass_kg (see the companion .json).

    The element total comes from ElectricMotorElementMC. That model writes the
    SAME combined summary into every stream folder, so exactly ONE file is read
    -- globbing all four counts every element four times.

    ###################################################################
    #  KNOWN INCONSISTENCY, NOT INTRODUCED HERE -- flagged 2026-08-13 #
    ###################################################################
    The element decomposition does NOT reconcile with the motor model's own
    mass. Measured at 2025:

        segment   element sum   ElectricMotorMC mass   ratio
        AB           23.393 kg              13.044 kg   1.79
        CD           45.573 kg              27.591 kg   1.65
        EF           95.791 kg              61.182 kg   1.57

    The elements decompose the motors, so these should be EQUAL. The four
    Streams are complementary materials (Cast Fe Steel, Copper, Electrical
    Steel, NdFeB), not duplicate runs, so summing them is correct -- the gap is
    a genuine disagreement between ElectricMotorMC and ElectricMotorElementMC,
    not a reading error.

    tools/build_composition.py has the same behaviour, so Data/30_ already
    carries it. The element sum is kept HERE so the joint band stays comparable
    with the published deliverable rather than silently disagreeing with it.
    Whichever way it is resolved, the Motors LEVEL moves and the total moves
    with it. The band shape and the correlation structure are unaffected.
    """
    per_draw = {}
    for seg in SEGMENTS:
        acc = None
        for p in sorted((ROOT / "ElectricMotorMC" / "samples_csv")
                        .glob(f"samples_{seg}_*.npy")):
            a = np.load(p, mmap_mode="r")[:, 2].astype(float)   # total_mass_kg
            acc = a.copy() if acc is None else acc + a
        if acc is None:
            raise FileNotFoundError(
                f"no motor samples for {seg} -- run ElectricMotorMC.py first")
        per_draw[seg] = acc

    files = sorted(ROOT.glob("ElectricMotorElementMC/*/summary_csv/elemental_summary.csv"))
    if not files:
        raise FileNotFoundError("no elemental_summary.csv -- run ElectricMotorElementMC.py")
    d = pd.read_csv(files[0])
    g25 = {}
    for seg in SEGMENTS:
        sub = d[d["Case"].astype(str).str.startswith(seg + "_")]
        g25[seg] = float(sub["Mean_mass_kg"].sum() * 1000.0)
    return per_draw, g25


# --------------------------------------------------------------- the domains

def domain_masses(seg, st, rng, ctx):
    """Grams per vehicle for each domain, for ONE chunk of vehicles.

    Args:
        seg: "AB" | "CD" | "EF".
        st:  VehicleState for this chunk -- the SAME cars in every domain.
        rng: generator for this run's private draws.
        ctx: the loaded models and factors, from build_context().

    Returns:
        {domain: (m, n_years)} grams per vehicle.
    """
    m = len(st)
    out = {}

    # ---- wiring: Cu in kg, straight from the model
    r = ctx["wiring"].run_monte_carlo(n_iter=m, seed=int(rng.integers(2**31)),
                                      state=st)
    out["Wiring"] = r.totals[("Cu (kg)", seg)] * 1000.0

    # ---- sensors: per-draw counts by type x 2025 composition
    chunk_fn = ctx["sensor_chunk"][seg]
    counts = chunk_fn(m, state=st)
    mg = ctx["sensor_mg"]
    acc = np.zeros((m, len(YEARS)))
    for key, arr in counts.items():
        if not isinstance(key, str) or key == "total":
            continue                      # skip the domain tuples and the total
        per = mg.get(str(key).strip().lower())
        if per:
            acc += arr * per / 1000.0     # mg -> g
    out["Sensors"] = acc

    # ---- PCB: area x g/cm2
    area = ctx["pcb"].run_year_resolved(seg, ndraws=m, chunk=m, state=st,
                                        return_draws=True)
    out["PCB"] = area * ctx["pcb_k"][seg]

    # ---- motors: 2025 element mass x this vehicle's growth trajectory
    pool = ctx["motor_draws"][seg]
    mass25 = pool[rng.integers(0, len(pool), size=m)]          # the model's own draws
    g = ctx["motor_growth"](m, seg, st)                        # (m, n_years), 1.0 at 2025
    out["Motors"] = ctx["motor_g25"][seg] * g * (mass25 / pool.mean())[:, None]

    return out


def build_context():
    """Import the four models and load every composition factor once."""
    print("Loading models (as libraries -- their own runs stay guarded)...")
    import BevWiring
    import SensorNumbersMC as SN
    import PCBAreaMC as PA
    import ElectricMotorMC as EM

    print("  building the per-segment sensor chunk functions...")
    sensor_chunk = {seg: SN.make_sensor_chunk(SN.merged, seg)[0] for seg in SEGMENTS}

    print("  loading motor draws and growth inputs...")
    motor_draws, motor_g25 = motor_2025()
    df_growth = EM.read_motor_growth(EM.XLSX_FILE)
    # Assembled exactly as ElectricMotorMC.main does -- read_motor_scenarios
    # returns three items and the active scenario is a separate read.
    _names, _w, _table = EM.read_motor_scenarios()
    scen = (_names, _w, _table, EM.read_active_scenario())
    print(f"  Driver F: {', '.join(_names)}   active = {scen[3]}")
    em_rng = np.random.default_rng(SEED + 99)

    def motor_growth(m, seg, st):
        return EM.growth_curve(em_rng, df_growth.loc[seg], m, seg, scen, st)

    return dict(wiring=BevWiring, pcb=PA,
                sensor_chunk=sensor_chunk,
                sensor_mg=sensor_mg_per_type(),
                pcb_k=pcb_g_per_cm2(),
                motor_draws=motor_draws, motor_g25=motor_g25,
                motor_growth=motor_growth)


# ------------------------------------------------------------------- the run

def run(n_iter=N_ITER, chunk=CHUNK, seed=SEED):
    ctx = build_context()
    rng = np.random.default_rng(seed)
    _, lidar_lag = load_lidar_bands(YEARS)

    stats, hists = [], []
    for seg in SEGMENTS:
        print(f"\n{seg}: {n_iter:,} vehicles through four domains, "
              f"chunks of {chunk:,}")
        accs, done = None, 0
        while done < n_iter:
            m = min(chunk, n_iter - done)
            st = draw_vehicle_state(rng, m, YEARS, lidar_lag=lidar_lag)
            dm = domain_masses(seg, st, rng, ctx)
            dm["Total"] = sum(dm[d] for d in DOMAINS)

            if accs is None:
                # Ranges from the first chunk, padded, exactly as the models do.
                accs = {}
                for k, v in dm.items():
                    lo, hi = v.min(axis=0), v.max(axis=0)
                    pad = 0.25 * (hi - lo) + 1e-9
                    accs[k] = Accumulator(lo - pad, hi + pad, n_series=len(YEARS))
            for k, v in dm.items():
                accs[k].add(v)
            done += m
            print(f"    {done:>8,} / {n_iter:,}")

        for k, a in accs.items():
            lo, med, hi = a.percentile(2.5), a.percentile(50), a.percentile(97.5)
            mean, mode = a.mean, a.coarse_mode()
            for i, y in enumerate(YEARS):
                stats.append(dict(Segment=seg, Series=k, Year=int(y), N_Iter=n_iter,
                                  Mean_g=mean[i], P2_5_g=lo[i], Median_g=med[i],
                                  Mode_g=mode[i], P97_5_g=hi[i]))
            # Exactly N_HIST_BINS bins, EMPTY BINS INCLUDED, so every
            # series-year has the same number of rows and the Mode above can be
            # reproduced from this file. 50 is the fixed project convention.
            for i, y in enumerate(YEARS):
                edges, counts = a.coarse(i, N_HIST_BINS)
                for b in range(N_HIST_BINS):
                    hists.append(dict(Segment=seg, Series=k, Year=int(y), Bin=b + 1,
                                      Bin_Left=edges[b], Bin_Right=edges[b + 1],
                                      Count=float(counts[b])))

    pd.DataFrame(stats).to_csv(OUT / "joint_mc_stats.csv", index=False)
    pd.DataFrame(hists).to_csv(OUT / "joint_mc_histograms.csv", index=False)
    print(f"\n  -> {OUT/'joint_mc_stats.csv'}")
    print(f"  -> {OUT/'joint_mc_histograms.csv'}  ({N_HIST_BINS} bins per series-year)")
    return pd.DataFrame(stats)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else N_ITER
    df = run(n_iter=n)

    # ---- what the joint band actually bought, against the two wrong answers
    print("\n" + "=" * 74)
    print("JOINT BAND vs THE TWO THINGS IT REPLACES")
    print("=" * 74)
    print("  independent = summing the domains as if uncorrelated (too narrow)")
    print("  comonotonic = summing their percentiles (too wide)")
    print()
    for seg in SEGMENTS:
        for y in (2025, 2040, 2070):
            d = df[(df.Segment == seg) & (df.Year == y)].set_index("Series")
            tot = d.loc["Total"]
            var = sum((d.loc[k, "P97_5_g"] - d.loc[k, "P2_5_g"]) ** 2 for k in DOMAINS)
            indep = np.sqrt(var)
            como = sum(d.loc[k, "P97_5_g"] - d.loc[k, "P2_5_g"] for k in DOMAINS)
            joint = tot["P97_5_g"] - tot["P2_5_g"]
            print(f"  {seg} {y}   mean {tot['Mean_g']/1000:7.3f} kg   "
                  f"independent {indep/1000:6.3f}   JOINT {joint/1000:6.3f}   "
                  f"comonotonic {como/1000:6.3f} kg")
