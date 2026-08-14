#!/usr/bin/env python3
"""The JOINT Monte Carlo — one simulated car through all four domains.

    python3 tools/mc_composition.py [n_iter]

Writes  Composition/draws/<seg>_<series>.npy     raw per-draw arrays (n_iter x years)
        Composition/csv/joint_mc_stats.csv        mean, P2.5, median, P97.5
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

# The elemental summary reports each stream's ELEMENTS and then that same
# stream's mass again under this name. It is a subtotal, not an element, and
# summing it double-counts every stream. UNIT: none, a row label.
TOTALMASS_ROW = "TotalMass"

# Materials ElectricMotorMC puts in a motor that ElectricMotorElementMC does not
# break down into elements. Aluminium IS an element; plastic is not resolved
# further. Together 17.7% of motor mass, so dropping them is not negligible.
# UNIT: none, material names as spelled in materials_mc_summary.csv.
UNRESOLVED_MATERIALS = ["Aluminum", "Plastic"]

# How far the reconstructed motor composition may sit from ElectricMotorMC's own
# mass before it is treated as a defect. UNIT: fraction.
#
# Measured error is now 0.008-0.022%, so this is ~20x headroom. It was 0.03
# while the element model still resampled each material from a 50-bin histogram
# and left NdFeB unnormalised; both were fixed 2026-08-13 and the tolerance was
# tightened to match. Set tighter and it will fail on ordinary draw noise; set
# looser and it stops catching a missing material stream -- at 0.03 it would no
# longer notice NdFeB, which is 9% of motor mass, going wrong by a third.
MOTOR_RECON_TOL = 0.005

SEGMENTS = ["AB", "CD", "EF"]
DOMAINS = ["Wiring", "Sensors", "PCB", "Motors"]
YEARS = np.arange(2020, 2071)
BASE_YEAR = 2025
I_BASE = int(np.searchsorted(YEARS, BASE_YEAR))

OUT = ROOT / "Composition" / "csv"
OUT.mkdir(parents=True, exist_ok=True)

# [NEW] Where the RAW per-draw arrays go. Until now this run built the draws, pushed
# them into the histogram accumulators and threw them away -- so anything downstream
# could only ever resample a 50-bin approximation of the distribution. The stock-flow
# model (RAWCLICStockAndFlow, stage 04_02) has to multiply these draws by its OWN
# per-draw vehicle counts, one draw against one draw, which needs the real values.
#
# One file per (segment, series), shape (n_iter, n_years), float32 -- 40 MB each,
# ~600 MB for the full set. float32 because these are grams per vehicle in the
# 1e2-1e5 range: ~7 significant digits, far beyond the models' actual precision.
# Written chunk by chunk through a memmap, so peak memory stays at one chunk
# regardless of n_iter, exactly as the histogram path already does.
DRAWS_OUT = ROOT / "Composition" / "draws"


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
    e = pd.read_pickle(ROOT / "PCBElementMC" / "data_results" / "element_mass_by_year.pkl")
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

    TWO DEFECTS FIXED HERE, both found 2026-08-13. Before the fix the element
    total was 1.57-1.79x the motor model's own mass, which is impossible: the
    elements DECOMPOSE the motors, so the two must be equal.

    1. TotalMass WAS BEING SUMMED AS IF IT WERE AN ELEMENT. Each stream reports
       its elements (Cu, plus traces in ppm) AND a TotalMass row holding that
       same stream's mass again. Summing every row therefore counted every
       stream exactly twice -- the clean 2.00x ratio that gave it away.

    2. ALUMINIUM AND PLASTIC WERE MISSING ENTIRELY. ElectricMotorElementMC only
       runs four material streams (Cast Fe Steel, Copper, Electrical Steel,
       NdFeB). ElectricMotorMC's motors are made of six: those four plus
       Aluminium and Plastic, which together are 17.7% of motor mass. They have
       no elemental breakdown -- aluminium IS an element and plastic is not
       resolved further -- so they are taken straight from the material summary
       and carried under their own names.

    Reconciliation after the fix, against ElectricMotorMC's own mass:

        segment   elements + Al + Plastic   motor mass   error
        AB                      13.041 kg     13.044 kg   0.02%
        CD                      27.728 kg     27.591 kg   0.50%
        EF                      61.755 kg     61.182 kg   0.94%

    The residual is histogram-reconstruction noise: the element model resamples
    each material mass from an exported 50-bin histogram rather than from the
    original draws, which cannot reproduce a mean exactly. It is checked below
    and will raise if it ever drifts past MOTOR_RECON_TOL.
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
    d = d[d["Element"].astype(str) != TOTALMASS_ROW]          # defect 1

    mat = pd.read_csv(ROOT / "ElectricMotorMC" / "materials_summary_csv"
                      / "materials_mc_summary.csv")

    g25 = {}
    for seg in SEGMENTS:
        elements = d[d["Case"].astype(str).str.startswith(seg + "_")]["Mean_mass_kg"].sum()
        extra = mat[(mat.Segment == seg) & (mat.Motor == "GrandTotal")
                    & (mat.Material.isin(UNRESOLVED_MATERIALS))]["Mean_mass_kg"].sum()
        total_kg = float(elements + extra)                    # defect 2

        # Must reconcile with the motor model's own mass -- the elements
        # decompose the motors, so anything else means a stream is missing or
        # counted twice. This is the check that would have caught both defects.
        ref = float(per_draw[seg].mean())
        err = abs(total_kg - ref) / ref
        if err > MOTOR_RECON_TOL:
            raise ValueError(
                f"motor composition does not reconcile for {seg}: "
                f"elements+{'+'.join(UNRESOLVED_MATERIALS)} = {total_kg:.3f} kg "
                f"vs ElectricMotorMC mass {ref:.3f} kg ({err:.1%} > "
                f"{MOTOR_RECON_TOL:.0%}). Check for a duplicated '{TOTALMASS_ROW}' "
                f"row or a material with no elemental breakdown.")
        g25[seg] = total_kg * 1000.0
    return per_draw, g25


# --------------------------------------------------------------- the domains

def domain_masses(seg, st, rng, ctx, row0):
    """Grams per vehicle for each domain, for ONE chunk of vehicles.

    Args:
        seg: "AB" | "CD" | "EF".
        st:   VehicleState for this chunk -- the SAME cars in every domain.
        rng:  generator for this run's private draws.
        ctx:  the loaded models and factors, from build_context().
        row0: index of this chunk's first vehicle within the whole run. Used to
              walk the motor model's saved draws in step, so each is consumed
              exactly once instead of being resampled.

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
    #
    # EACH SAVED DRAW IS USED EXACTLY ONCE, walking the pool in step with the
    # joint run rather than resampling it with replacement. Bootstrapping would
    # be correct in distribution but it is still resampling: it adds noise that
    # is not in the model and lets one motor stand in for several vehicles.
    # Consuming the pool sequentially is exact, because these ARE the motor
    # model's own 200,000 draws and the joint run is the same length.
    pool = ctx["motor_draws"][seg]
    if row0 + m > len(pool):
        raise ValueError(
            f"joint run wants motor draws [{row0}:{row0+m}] but the pool holds "
            f"{len(pool):,}. Lower N_ITER to the pool size, or re-run "
            f"ElectricMotorMC.py with at least N_ITER draws.")
    mass25 = pool[row0:row0 + m]
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

def run(n_iter=N_ITER, chunk=CHUNK, seed=SEED, save_draws=True):
    ctx = build_context()
    rng = np.random.default_rng(seed)
    _, lidar_lag = load_lidar_bands(YEARS)

    stats, hists = [], []
    for seg in SEGMENTS:
        print(f"\n{seg}: {n_iter:,} vehicles through four domains, "
              f"chunks of {chunk:,}")
        accs, done = None, 0
        memmaps = {}
        if save_draws:
            DRAWS_OUT.mkdir(parents=True, exist_ok=True)
            for k in DOMAINS + ["Total"]:
                memmaps[k] = np.lib.format.open_memmap(
                    DRAWS_OUT / f"{seg}_{k}.npy", mode="w+",
                    dtype=np.float32, shape=(n_iter, len(YEARS)),
                )
        while done < n_iter:
            m = min(chunk, n_iter - done)
            st = draw_vehicle_state(rng, m, YEARS, lidar_lag=lidar_lag)
            dm = domain_masses(seg, st, rng, ctx, done)
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
                if save_draws:
                    memmaps[k][done:done + m, :] = v.astype(np.float32, copy=False)
            done += m
            print(f"    {done:>8,} / {n_iter:,}")

        for k, mm in memmaps.items():
            mm.flush()
            print(f"    draws -> {DRAWS_OUT / f'{seg}_{k}.npy'}")
        memmaps.clear()

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


def validate(df):
    """C1-C4 -- properties the joint band must have, whatever the inputs say.

    These are not calibration checks against data; they are arithmetic facts. If
    any fails, the summation or the accumulator is wrong, not the model.
    """
    piv = df.pivot_table(index=["Segment", "Year"], columns="Series",
                         values=["Mean_g", "P2_5_g", "P97_5_g"])
    bound = mean_in = order = 0
    mean_err = 0.0
    for _, r in piv.iterrows():
        lo_b = sum(r[("P2_5_g", d)] for d in DOMAINS)
        hi_b = sum(r[("P97_5_g", d)] for d in DOMAINS)
        lo, hi, mn = r[("P2_5_g", "Total")], r[("P97_5_g", "Total")], r[("Mean_g", "Total")]
        # C1 the joint band can never exceed the comonotonic bound: summing
        #    percentiles assumes every domain peaks together, the widest case
        if lo < lo_b - 1e-6 or hi > hi_b + 1e-6:
            bound += 1
        if not (lo <= mn <= hi):                                  # C2
            mean_in += 1
        if lo > hi:                                               # C3
            order += 1
        # C4 means ADD exactly, because the total was summed draw by draw --
        #    unlike percentiles, which do not
        mean_err = max(mean_err, abs(sum(r[("Mean_g", d)] for d in DOMAINS) - mn) / mn)

    print("\n" + "=" * 74)
    print(f"VALIDATION -- {len(piv)} (segment, year) cells")
    print("=" * 74)
    for tag, msg, bad in [
            ("C1", "joint band within the comonotonic bound", bound),
            ("C2", "mean inside its own band", mean_in),
            ("C3", "P2.5 <= P97.5", order)]:
        print(f"  [{'ok  ' if not bad else 'FAIL'}] {tag}  {msg:48s} {bad} bad")
    ok4 = mean_err < 1e-9
    print(f"  [{'ok  ' if ok4 else 'FAIL'}] C4  "
          f"{'sum(domain means) == total mean':48s} {mean_err:.2e}")
    n_bad = bound + mean_in + order + (0 if ok4 else 1)
    print(f"\n  {4 - (bool(bound)+bool(mean_in)+bool(order)+(0 if ok4 else 1))}/4 passed")
    return n_bad == 0


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else N_ITER
    df = run(n_iter=n)
    validate(df)

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
