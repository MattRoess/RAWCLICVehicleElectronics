"""
BEV Wiring Harness Monte Carlo, 2020-2070 -- STATE-BASED, SENSOR-COUPLED
================================================================================
This is the current model. Earlier generations (v3, v4) were deleted on
2026-08-05; MODEL_HISTORY.md records why each was replaced, and they are
recoverable from git history up to commit 554633e.

WHY THIS MODEL LOOKS THE WAY IT DOES
(the three defects of the previous generation that shaped it)
--------------------------------------------------------------------------------
v4 moved the model onto a single 2025 anchor and made transition TIMING
stochastic. Three things were still wrong:

  1. It share-WEIGHTED the transitions. Every simulated vehicle got the average
     of an old and a new design. Real vehicles are one or the other. The
     consequence was that uncertainty did not widen during a transition, when
     it should be at its widest -- the fleet is genuinely bimodal then.
     This model draws a DISCRETE state per iteration.
  2. ADAS growth was bolted onto the SDV factor, so sensor content grew
     *because of* zonal architecture. Wrong mechanism. Sensors grow because of
     regulation and feature adoption, on their own clock. Here the two are
     Here they are independent and can oppose each other -- new architecture shortens wiring
     while new sensors lengthen it.
  3. Only two architecture states existed (pre/post 2025, via a legacy fudge).
     This model uses the three the source report actually names: Conventional,
     Transitional, SDV_Zonal. LEGACY_TAU_YEARS is gone.

FOUR INDEPENDENT DRIVERS
--------------------------------------------------------------------------------
    Architecture  Conventional -> Transitional -> SDV_Zonal   LV/signal LENGTH
    Voltage       400V -> 800V                                HV Cu-per-METRE
    Autonomy      L0 .. L5                                    ADAS/sensor LENGTH
    (car-to-car variability, unchanged from v4)

They are sampled independently, so a 2035 vehicle can be zonal AND
sensor-heavy. Net harness length can flatten or rise.

COMONOTONIC STATE SAMPLING
--------------------------------------------------------------------------------
Each iteration draws ONE uniform per driver, held across all years, and takes
whichever state that uniform falls into given the year's shares. So iteration i
is consistently "a vehicle at adoption percentile u" -- an early adopter stays
an early adopter. This reproduces the marginal shares exactly, keeps each
iteration's trajectory smooth, and still yields the bimodal spread mid-
transition. Drawing independently per year would reproduce the shares too, but
would make every trajectory jump around.

WHAT IS PER-VEHICLE AND WHAT IS NOT
--------------------------------------------------------------------------------
Output is PER NEW PRIVATE VEHICLE SOLD. Shares are shares of new sales. Fleet
turnover belongs to RAWCLICStockAndFlow.

!! LABEL COLLISION WARNING !!
--------------------------------------------------------------------------------
The source report BEV_Automation_Adoption_Report_2020_2050.md names its three
SCENARIOS "AB", "CD" and "EF". Those are Conservative / Central / Accelerated.
They are NOT the vehicle size segments of the same name used everywhere in this
project. 18_ renames them to avoid the collision. Never join the report's
scenario tables onto a size segment.

INPUTS
--------------------------------------------------------------------------------
  Data/17_BEV_wiring_baseline_2025.xlsx      2025 baseline, gauges, SDV factors
  Data/18_BEV_technology_penetration.xlsx    all three drivers + sensors
16_ and 15_ are NOT read. Both superseded.

NOTE ON READING 18_: the model recomputes the autonomy conversion from
Report_Scenarios + Conversion rather than reading the Autonomy_Derived sheet.
That sheet is formulas, and openpyxl cannot see formula results until Excel has
opened and saved the file. The Python here mirrors those formulas exactly; if
you change one, change the other.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------
# 0. CONFIGURATION
#    Every constant: WHAT | UNIT | WHY this value | WHAT MOVES if changed
# --------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "Data"
BASELINE_FILE = DATA_DIR / "17_BEV_wiring_baseline_2025.xlsx"
PENETRATION_FILE = DATA_DIR / "18_BEV_technology_penetration.xlsx"
ADAS_FILE = DATA_DIR / "19_ADAS_sensor_adoption.xlsx"

# PROJECT-WIDE scenario selection, read by every model so that choosing a
# scenario once applies it everywhere. It used to live in 19_ sheet Scenarios,
# which is ADAS-specific and the wrong home for a project-wide switch.
# One cell: sheet Control, Active_Scenario.
SCENARIO_FILE = DATA_DIR / "20_scenarios.xlsx"

# Sensor axis | UNIT: none.
# True  = ADAS content is driven by the HARDWARE TIER axis in 19_ (drivers A/B/C).
# False = the old path: SAE certification level x 18_ Sensors_per_Level.
# WHY the change: wiring follows installed hardware, not the certificate. Volvo's
# EX90 carries 31 sensors and is certified L2; BMW's i7 carried 25 and was
# certified L3. Keying sensor count on the certificate gets the near-term trend
# backwards, because certified L3 is being WITHDRAWN in Europe while sensor
# content keeps rising. Full argument: docs/ADAS_Sensor_Adoption_Report_2025_2070.md
# Keep False available for diffing old against new; it is not maintained.
USE_TIER_AXIS = True

# Driver C scenario selection | UNIT: none.
# None  = obey the Active_Scenario cell in 20_ sheet Control (normal use).
# "SAMPLE" / "S1" / "S2" / "S3" = override it, for scripted sweeps.
# SAMPLE draws a scenario per iteration by weight, so ONE run's band contains
# all three. Pinning narrows the band by discarding that spread -- use pinned
# runs to understand the scenarios, quote SAMPLE.
SCENARIO_OVERRIDE = None

OUT_DIR = SCRIPT_DIR / "outputs"
OUT_SUBDIRS = {"data": OUT_DIR / "data", "plots": OUT_DIR / "plots"}
for _p in OUT_SUBDIRS.values():
    _p.mkdir(parents=True, exist_ok=True)

BASE_YEAR = 2025    # the anchor | UNIT: calendar year (CE). 17_ lengths are as
                    # of this year, and it is the one year where the workbook
                    # and the source report agree exactly.
START_YEAR = 2020   # first output year | UNIT: calendar year (CE). BEV market
                    # entry is ~2010 but the report has no data before 2020.
END_YEAR = 2070
N_ITER = 200000     # MC iterations for the STATISTICS | UNIT: count.
                    # Run through the chunked accumulator, so memory does NOT
                    # scale with this -- only runtime does, at ~0.16 s per 1000
                    # iterations. 200,000 is perfectly practical (~35 s).
CHUNK_ITER = 5000   # iterations simulated at once | UNIT: count.
                    # Peak memory is set by THIS, not by N_ITER. 5000 costs
                    # roughly 0.9 GB; lower it on a small machine, raise it for
                    # slightly more speed.
N_ITER_PLOTS = 5000 # iterations for the PLOTS only | UNIT: count.
                    # Plots need every draw in memory, so this is capped
                    # independently of N_ITER. Raising it above ~20,000 is what
                    # exhausts memory.
RANDOM_SEED = 42    # UNIT: none. Fixed for reproducibility; change it to check
                    # conclusions are not a single-seed artefact.

BASE_SEGMENTS = ["AB", "CD", "EF"]
J_SUFFIX = {"AB": "JA-JB", "CD": "JC-JD", "EF": "JE-JF"}
DRIVETRAIN = "BEV"

METRIC_LENGTH = "Length (m)"
METRIC_CU = "Cu (kg)"
METRICS = [METRIC_LENGTH, METRIC_CU]
METRIC_SLUG = {METRIC_LENGTH: "length_m", METRIC_CU: "cu_kg"}

# Copper density | UNIT: g/cm3. 1 mm2 x 1 m = 1 cm3 exactly, so
# Cu (g/m) = gauge (mm2) x density. No stranding fill factor, matching the
# source report's own formula (its section 8.3).
RHO_CU_G_PER_CM3 = 8.96

# 800V copper saving on HV cables | UNIT: dimensionless fraction of Cu-per-metre
# removed at full 800V. WHY: doubling voltage halves current, halving the
# required cross-section (P = V x I). The report says 40-45% rather than the
# theoretical 50%, allowing for minimum-gauge and mechanical limits.
HV_800V_CU_REDUCTION_TRI = (0.40, 0.425, 0.45)
HV_GROUP = "HV Power"
ADAS_GROUP = "ADAS / Sensor"     # driven by sensor counts, not by architecture

# Car-to-car variability, split into a shared and an independent part
# (source report section 8.5). UNIT: coefficient of variation, dimensionless.
CV_VEHICLE = 0.10      # "+/-8-12% at the total vehicle level"
CV_CATEGORY = 0.175    # "+/-15-20% at the wire-category level"

# Conventional-architecture harness size, as a multiple of the 2025 baseline
# total | UNIT: dimensionless ratio. From the report's 2020 totals, which it
# describes as "the first generation of purpose-built BEV platforms" -- an
# architecture generation, not a market average. Used here as the CONVENTIONAL
# state's level, never as the value for the year 2020.
# ASSUMPTION: applied uniformly across non-ADAS categories, because the report
# gives no per-category split for its 2020 figures.
CONVENTIONAL_UPLIFT = {"AB": 2485 / 1392, "CD": 4144 / 2486, "EF": 4610 / 3546}

# EF length calibration | UNIT: dimensionless ratio.
# The source report's per-category length column sums exactly to its stated
# segment total for AB (1392) and CD (2486), but EF sums to 3646 against a
# stated 3546. 100 m is unaccounted and the offending row is still unidentified.
# Set to 1.0 to use the raw per-category figures and accept a 2.8% high EF.
SEGMENT_LENGTH_CALIBRATION = {"AB": 1.0, "CD": 1.0, "EF": 3546 / 3646}

# Spread of transition timing ACROSS MANUFACTURERS | UNIT: years (std dev).
# Without this every iteration switches state in the same year, because they all
# read the same share curve. The whole fleet then turns over at once, which
# produces a visibly too-steep ramp and a stepped median. Each iteration instead
# gets its own time offset, so switch years are spread the way real OEM launch
# timing is spread.
# EFFECT: 0 = every manufacturer moves in lockstep (the artefact); larger =
# gentler aggregate transition, wider band during it. Applies to all three
# drivers independently.
TRANSITION_TIMING_SPREAD_Y = 5.0

# J* derived segments | UNIT: dimensionless fraction. Taller body on the same
# platform: longer vertical runs, unchanged electronic content.
HEIGHT_ADDER_TRI = (0.05, 0.10, 0.15)

STAT_PCTS = (2.5, 97.5)   # reported band | UNIT: percent (0-100)
N_HIST_BINS = 50
SNAPSHOT_YEARS = [2020, 2025, 2030, 2035, 2040, 2050, 2070]
HIST_PLOT_YEARS = [2025, 2050, 2070]   # years given their own per-group
                                       # histogram figure | UNIT: calendar years.
                                       # Must be a subset of SNAPSHOT_YEARS.
COL_LO, COL_HI = (f"P{p:g}".replace(".", "_") for p in STAT_PCTS)

LEVELS = ["L0", "L1", "L2", "L3", "L4", "L5"]
ARCH_STATES = ["Conventional", "Transitional", "SDV_Zonal"]

# ADAS hardware tiers | UNIT: none. H3/H4 are anchored on measured cars
# (Mercedes EQS, BMW i7, Volvo EX90); H0 is pinned by EU GSR-2; H1/H2 are
# assumptions. See 19_ sheet Tiers and report section 3.
TIERS = ["H0", "H1", "H2", "H3", "H4"]
SENSOR_TYPES = ["camera", "radar", "lidar", "ultrasonic"]

# Year from which Driver C scenarios may differ | UNIT: calendar year (CE).
# All scenarios are exactly 1.0 at and before this year by construction, so the
# scenario driver cannot perturb any year for which sourced data exists.
# Enforced by validation V9.
SCENARIO_START_YEAR = 2040


# --------------------------------------------------------------------------
# 1. INPUTS
# --------------------------------------------------------------------------

@dataclass
class Inputs:
    codes: list
    groups: list
    gauge_min: np.ndarray
    gauge_max: np.ndarray
    sdv_factor: np.ndarray
    length: dict            # segment -> (n_cat,) metres at BASE_YEAR
    depth_tri: dict         # segment -> (min, mode, max) SDV depth
    arch: dict              # (segment, state) -> callable(year)->share
    volt: dict              # segment -> callable(year)->share of 800V
    autonomy: dict          # (segment, band) -> (n_levels, n_years) shares
    sensors: pd.DataFrame   # Level, Sensor_Type, Count_Min/Mode/Max  (old axis)
    metres: pd.DataFrame    # Sensor_Type, Segment, m_Min/Mode/Max
    # --- tier axis, from 19_. None when USE_TIER_AXIS is False.
    tier_shares: dict = None    # segment -> (n_tiers, n_years) shares, cols sum to 1
    tier_counts: dict = None    # (tier, sensor_type) -> (min, mode, max) per vehicle
    lidar: np.ndarray = None    # (3, n_years) Min/Mode/Max equipped share, Europe
    lidar_lag: tuple = None     # (mean_y, sd_y) China->Europe lag, SAMPLED
    scen_mult: dict = None      # scenario -> (n_years) multiplier on sensor counts
    scen_w: np.ndarray = None   # (n_scen,) weights, sum 1
    scen_names: list = None
    scen_active: str = None     # "SAMPLE" or one of scen_names


def _monotone_curve(years, anchor_years, anchor_vals):
    """Smooth, shape-preserving read of the share anchors.

    PCHIP is C1 (continuous first derivative) and cannot overshoot between
    anchors, so a share stays in [0,1] and the curve has no kink at the 5-year
    anchor points. np.interp was used first and its slope discontinuities were
    visible as corners in the output bands.
    Outside the anchor range the end values are held flat.
    """
    from scipy.interpolate import PchipInterpolator
    x = np.asarray(anchor_years, float); y = np.asarray(anchor_vals, float)
    o = np.argsort(x); x, y = x[o], y[o]
    if len(x) < 2:
        return np.full(len(years), y[0] if len(y) else 0.0)
    f = PchipInterpolator(x, y, extrapolate=False)
    out = f(np.clip(years, x[0], x[-1]))
    return np.clip(np.nan_to_num(out), 0.0, 1.0)


def _read_active_scenario() -> str:
    """The project-wide scenario selection: 20_ sheet Control, cell B4.

    One cell, read by every model, so that choosing a scenario once applies it
    everywhere. Returns "SAMPLE" (draw per iteration by weight) or a scenario
    name (pin every iteration to it).
    """
    wb = pd.read_excel(SCENARIO_FILE, sheet_name="Control", header=None)
    return str(wb.iloc[3, 1]).strip()          # cell B4


def _load_tier_axis(years) -> dict:
    """Read drivers A, B and C from 19_ADAS_sensor_adoption.xlsx.

    A  tier shares       sheet Tier_Shares       -> (n_tiers, n_years) per segment
    B  lidar penetration sheet Lidar             -> (3, n_years) Min/Mode/Max
    C  scenario          sheet Scenarios         -> multiplier curve per scenario

    Every number traces to docs/ADAS_Sensor_Adoption_Report_2025_2070.md;
    the sheets carry the section references. Anchors are read through the same
    PCHIP curve as every other share table here, so adding or deleting anchor
    years in Excel needs no code change.
    """
    if not ADAS_FILE.exists():
        raise FileNotFoundError(
            f"ADAS adoption workbook not found: {ADAS_FILE}\n"
            f"Generate it with: python3 tools/make_19_adas_sensor_adoption.py")

    # ---- A: tier shares, renormalised so columns sum to 1 after interpolation
    ts = pd.read_excel(ADAS_FILE, sheet_name="Tier_Shares", header=3)
    ts = ts[ts["Segment"].notna()]
    tier_shares = {}
    for seg in BASE_SEGMENTS:
        d = ts[ts.Segment == seg].sort_values("Year")
        m = np.vstack([_monotone_curve(years, d.Year.to_numpy(float),
                                       d[t].to_numpy(float)) for t in TIERS])
        tier_shares[seg] = m / np.maximum(m.sum(axis=0, keepdims=True), 1e-12)

    # ---- A: sensor counts per tier
    td = pd.read_excel(ADAS_FILE, sheet_name="Tiers", header=3)
    td = td[td["Tier"].notna()]
    col = {"camera": ("Cam_min", "Cam_max"), "radar": ("Radar_min", "Radar_max"),
           "ultrasonic": ("Ultra_min", "Ultra_max"),
           "lidar": ("Lidar_min", "Lidar_max")}
    tier_counts = {}
    for _, r in td.iterrows():
        for st, (lo_c, hi_c) in col.items():
            lo, hi = float(r[lo_c]), float(r[hi_c])
            tier_counts[(r["Tier"], st)] = (lo, (lo + hi) / 2.0,
                                            max(hi, lo + 1e-9))

    # ---- B: lidar
    ld = pd.read_excel(ADAS_FILE, sheet_name="Lidar", header=3)
    ld = ld[ld["Year"].notna()].sort_values("Year")
    yr = ld.Year.to_numpy(float)
    lidar = np.vstack([_monotone_curve(years, yr, ld[c].to_numpy(float))
                       for c in ("Share_Min", "Share_Mode", "Share_Max")])

    pr = pd.read_excel(ADAS_FILE, sheet_name="Parameters", header=2)
    pr = pr[pr["Parameter"].notna()].set_index("Parameter")["Value"]
    lidar_lag = (float(pr["Lidar_Europe_Lag_Y_Mean"]),
                 float(pr["Lidar_Europe_Lag_Y_SD"]))

    # ---- C: scenarios, from the PROJECT-WIDE file
    if not SCENARIO_FILE.exists():
        raise FileNotFoundError(
            f"Scenario workbook not found: {SCENARIO_FILE}\n"
            f"Generate it with: python3 tools/make_20_scenarios.py")
    sc = pd.read_excel(SCENARIO_FILE, sheet_name="Scenarios", header=3)
    anchor_cols = [c for c in sc.columns
                   if isinstance(c, (int, float)) or str(c).strip().isdigit()]
    anchor_yrs = np.array([float(str(c).strip()) for c in anchor_cols])
    # Keep only rows that are actually scenario data. Filtering on a single
    # column is not enough: the sheet carries free-text notes below the table,
    # and those land in whichever column they start in.
    sc = sc[sc["Scenario"].notna() & sc["Weight"].notna()
            & sc[anchor_cols].notna().all(axis=1)]
    if sc.empty:
        raise ValueError(f"No scenario rows found in {SCENARIO_FILE} sheet Scenarios")
    scen_names = sc["Scenario"].tolist()
    scen_mult = {}
    for _, r in sc.iterrows():
        vals = np.array([float(r[c]) for c in anchor_cols])
        # PCHIP would clip to [0,1]; multipliers exceed 1, so interpolate here
        # and hold the end values flat outside the anchor range.
        from scipy.interpolate import PchipInterpolator
        f = PchipInterpolator(anchor_yrs, vals, extrapolate=False)
        out = f(np.clip(years, anchor_yrs[0], anchor_yrs[-1]))
        out = np.nan_to_num(out, nan=vals[0])
        # identical to 1.0 at and before SCENARIO_START_YEAR, by construction
        out = np.where(years <= SCENARIO_START_YEAR, 1.0, out)
        scen_mult[r["Scenario"]] = np.maximum(out, 0.0)
    w = sc["Weight"].to_numpy(float)
    scen_w = w / max(w.sum(), 1e-12)

    active = SCENARIO_OVERRIDE
    if active is None:
        active = _read_active_scenario()
    if active not in (["SAMPLE"] + scen_names):
        raise ValueError(
            f"Active_Scenario is {active!r}; expected 'SAMPLE' or one of "
            f"{scen_names}. Set it in 20_ sheet Control cell B4, or via "
            f"SCENARIO_OVERRIDE in section 0.")

    return dict(tier_shares=tier_shares, tier_counts=tier_counts, lidar=lidar,
                lidar_lag=lidar_lag, scen_mult=scen_mult, scen_w=scen_w,
                scen_names=scen_names, scen_active=active)


def load_inputs(years) -> Inputs:
    if not BASELINE_FILE.exists():
        raise FileNotFoundError(f"Baseline workbook not found: {BASELINE_FILE}")
    if not PENETRATION_FILE.exists():
        raise FileNotFoundError(f"Penetration workbook not found: {PENETRATION_FILE}")

    b = pd.read_excel(BASELINE_FILE, sheet_name="Baseline_2025", header=5)
    b = b[b["Code"].notna() & (b["Code"] != "TOTAL")]
    dep = pd.read_excel(BASELINE_FILE, sheet_name="SDV_Depth", header=6)
    dep = dep[dep["Segment"].notna()]
    depth_tri = {r["Segment"]: (float(r["Depth_Min"]), float(r["Depth_Mode"]),
                                float(r["Depth_Max"])) for _, r in dep.iterrows()}

    pen = pd.read_excel(PENETRATION_FILE, sheet_name="Penetration", header=4)
    pen = pen[pen["Driver"].notna()]

    arch, volt = {}, {}
    for seg in BASE_SEGMENTS:
        for st in ARCH_STATES:
            d = pen[(pen.Driver == "Architecture") & (pen.Segment == seg)
                    & (pen.State == st)].sort_values("Year")
            arch[(seg, st)] = _monotone_curve(years, d.Year.to_numpy(float),
                                              d.Share_Mode.to_numpy(float))
        d = pen[(pen.Driver == "Voltage") & (pen.Segment == seg)
                & (pen.State == "800V")].sort_values("Year")
        volt[seg] = _monotone_curve(years, d.Year.to_numpy(float),
                                    d.Share_Mode.to_numpy(float))

    autonomy = _derive_autonomy(years)
    sensors = pd.read_excel(PENETRATION_FILE, sheet_name="Sensors_per_Level", header=4)
    sensors = sensors[sensors["Level"].notna()]
    metres = pd.read_excel(PENETRATION_FILE, sheet_name="Metres_per_Sensor", header=4)
    metres = metres[metres["Sensor_Type"].notna()]

    tier = _load_tier_axis(years) if USE_TIER_AXIS else {}

    return Inputs(
        codes=b["Code"].tolist(), groups=b["Functional Group"].tolist(),
        gauge_min=b["Gauge_Min_mm2"].to_numpy(float),
        gauge_max=b["Gauge_Max_mm2"].to_numpy(float),
        sdv_factor=b["SDV_Base_Length_Factor"].to_numpy(float),
        length={s: b[f"{s}_Length_m"].to_numpy(float) for s in BASE_SEGMENTS},
        depth_tri=depth_tri, arch=arch, volt=volt, autonomy=autonomy,
        sensors=sensors, metres=metres, **tier,
    )


def _derive_autonomy(years) -> dict:
    """Mirror of the Autonomy_Derived sheet, in Python.

    Reads the report's global in-use-fleet scenarios and converts them to
    European private new-vehicle shares by size segment, by shifting the time
    axis. Four levers, all on the Conversion sheet:

        fleet -> new sales   new sales LEAD the parc by ~mean fleet age
        private lag          private follows commercial/robotaxi adoption
        Europe shift         Europe vs global
        segment offset       premium leads, cost-sensitive lags

    net_shift = -(fleet lead) + (private lag) + (Europe) + (segment offset)
    and the report table is read at (year - net_shift), clamped to its range.

    Why recomputed rather than read: Autonomy_Derived is formulas, and formula
    results are invisible to openpyxl until Excel has saved the file.
    """
    raw = pd.read_excel(PENETRATION_FILE, sheet_name="Report_Scenarios", header=None)
    blocks, cur = {}, None
    for i in range(len(raw)):
        v = raw.iloc[i, 0]
        if isinstance(v, str) and v.split("  ")[0] in ("Conservative", "Central", "Accelerated"):
            cur = v.split("  ")[0]; blocks[cur] = []
        elif cur and isinstance(v, (int, float)) and not pd.isna(v) and 1990 < v < 2100:
            blocks[cur].append([float(v)] + [float(raw.iloc[i, 1 + k]) for k in range(6)])
    scen = {k: np.array(v) for k, v in blocks.items()}

    cv = pd.read_excel(PENETRATION_FILE, sheet_name="Conversion", header=3)
    cv = cv[cv["Parameter"].notna()].set_index("Parameter")["Value"]
    lead = float(cv["Fleet_to_NewSales_lead_y"])
    priv = float(cv["Private_lag_y"])
    eur = float(cv["Europe_shift_y"])
    off = {s: float(cv[f"Offset_{s}_y"]) for s in BASE_SEGMENTS}
    band_scen = {"Share_Min": "Conservative", "Share_Mode": "Central",
                 "Share_Max": "Accelerated"}

    out = {}
    for seg in BASE_SEGMENTS:
        net = -lead + priv + eur + off[seg]
        t = np.clip(years - net, 2020, 2050)
        for band, sc in band_scen.items():
            tab = scen[sc]
            m = np.vstack([np.interp(t, tab[:, 0], tab[:, 1 + k]) for k in range(6)])
            m = np.clip(m, 0.0, None)
            m = m / np.maximum(m.sum(axis=0, keepdims=True), 1e-12)   # renormalise
            out[(seg, band)] = m
    return out


# --------------------------------------------------------------------------
# 2. STATE SAMPLING
# --------------------------------------------------------------------------

def _shift_shares(shares, years, delta):
    """Re-read the share curves with each iteration's own time offset.

    Args:
        shares: (n_states, n_years) marginal shares.
        years:  (n_years,) UNIT: calendar years.
        delta:  (n_iter,)  per-iteration offset. UNIT: years. Positive = that
                manufacturer transitions later.

    Returns:
        (n_states, n_iter, n_years), renormalised to sum to 1 over states.
    """
    n_states, n_years = shares.shape
    out = np.empty((n_states, len(delta), n_years))
    for k in range(n_states):
        for i, d in enumerate(delta):
            out[k, i] = np.interp(years - d, years, shares[k])
    out = np.clip(out, 0.0, None)
    return out / np.maximum(out.sum(axis=0, keepdims=True), 1e-12)


def comonotonic_state(u, shares):
    """Pick a discrete state per (iteration, year) from a single uniform per
    iteration, held across years.

    Args:
        u:      (n_iter,)          one uniform per iteration. UNIT: [0,1].
        shares: (n_states, n_years) marginal shares, columns summing to 1.

    Returns:
        (n_iter, n_years) integer state index.

    A vehicle is one design or another, never a blend. Holding u fixed across
    years makes iteration i a consistent adoption percentile, so trajectories
    stay smooth while the cross-iteration spread widens mid-transition -- which
    is the real behaviour a share-weighted average destroys.
    """
    cum = np.cumsum(shares, axis=0)              # (n_states, n_years)
    return (u[:, None, None] > cum[None, :, :]).sum(axis=1)


# --------------------------------------------------------------------------
# 3. MONTE CARLO
# --------------------------------------------------------------------------

@dataclass
class MCResult:
    years: np.ndarray
    segments: list
    codes: list
    groups: list
    per_category: dict
    totals: dict
    diagnostics: dict


def run_monte_carlo(n_iter=N_ITER, seed=RANDOM_SEED,
                    start_year=START_YEAR, end_year=END_YEAR) -> MCResult:
    """Simulate n_iter vehicles and KEEP EVERY DRAW.

    Memory is (n_iter x 28 categories x 51 years) float64 per metric per
    segment -- about 34 MB at 3000 iterations but 2.3 GB at 200,000, times
    twelve arrays. Use this for exploration and plotting up to ~20,000
    iterations; above that use run_accumulated(), which keeps only statistics.
    """
    rng = np.random.default_rng(seed)
    years = np.arange(start_year, end_year + 1)
    inp = load_inputs(years)
    n_years, n_cat = len(years), len(inp.codes)

    is_hv = np.array([g == HV_GROUP for g in inp.groups])
    is_adas = np.array([g == ADAS_GROUP for g in inp.groups])
    shrinks = inp.sdv_factor < 1.0
    cv_ind = float(np.sqrt(max(CV_CATEGORY ** 2 - CV_VEHICLE ** 2, 0.0)))
    i_base = int(np.searchsorted(years, BASE_YEAR))

    sens = inp.sensors.set_index(["Level", "Sensor_Type"])
    met = inp.metres.set_index(["Sensor_Type", "Segment"])
    sensor_types = sorted(inp.sensors.Sensor_Type.unique())

    per_category, totals, diag = {}, {}, {}

    for seg in BASE_SEGMENTS:
        # ---- driver shares for this segment
        arch_sh = np.vstack([inp.arch[(seg, s)] for s in ARCH_STATES])
        arch_sh = np.clip(arch_sh, 0, None)
        arch_sh /= np.maximum(arch_sh.sum(axis=0, keepdims=True), 1e-12)
        aut_sh = inp.autonomy[(seg, "Share_Mode")]
        aut_lo = inp.autonomy[(seg, "Share_Min")]
        aut_hi = inp.autonomy[(seg, "Share_Max")]
        # band membership drawn per iteration, so the scenario spread from the
        # source report becomes part of the MC rather than a separate run
        w = rng.random(n_iter)[:, None, None]
        aut_mix = np.where(w < 1 / 3, aut_lo[None], np.where(w < 2 / 3, aut_sh[None], aut_hi[None]))

        # ---- discrete states
        u_arch = rng.random(n_iter)
        u_aut = rng.random(n_iter)
        d_arch = rng.normal(0.0, TRANSITION_TIMING_SPREAD_Y, size=n_iter)
        d_aut = rng.normal(0.0, TRANSITION_TIMING_SPREAD_Y, size=n_iter)
        arch_i = _shift_shares(arch_sh, years, d_arch)                # (3,n_iter,n_years)
        st_arch = (u_arch[None, :, None] > np.cumsum(arch_i, axis=0)).sum(axis=0)
        aut_i = np.empty((6, n_iter, n_years))
        for k in range(6):
            for i, d in enumerate(d_aut):
                aut_i[k, i] = np.interp(years - d, years, aut_mix[i, k])
        aut_i = np.clip(aut_i, 0, None)
        aut_i /= np.maximum(aut_i.sum(axis=0, keepdims=True), 1e-12)
        st_aut = (u_aut[None, :, None] > np.cumsum(aut_i, axis=0)).sum(axis=0)

        # ---- SDV depth and the three architecture levels, per category
        depth = rng.triangular(*inp.depth_tri[seg], size=n_iter)
        f_sdv = np.repeat(inp.sdv_factor[None, :], n_iter, axis=0)
        f_sdv[:, shrinks] = np.maximum(
            0.0, 1.0 - (1.0 - inp.sdv_factor[None, shrinks]) * depth[:, None])
        f_conv = np.where(is_adas, 1.0, CONVENTIONAL_UPLIFT[seg])[None, :]
        f_trans = np.ones((1, n_cat))
        levels = np.stack([np.broadcast_to(f_conv, (n_iter, n_cat)),
                           np.broadcast_to(f_trans, (n_iter, n_cat)),
                           f_sdv], axis=0)                            # (3, n_iter, n_cat)

        # factor actually realised: pick the drawn state's level
        idx = st_arch[None, :, None, :]                               # (1,n_iter,1,n_years)
        fac = np.take_along_axis(levels[:, :, :, None].repeat(n_years, axis=3),
                                 idx, axis=0)[0]                      # (n_iter,n_cat,n_years)
        # Renormalise so the state mixture reproduces the OBSERVED 2025 baseline.
        # exp_base is the expected factor at BASE_YEAR given that year's shares;
        # dividing by it anchors the ensemble mean without touching the spread.
        exp_base = sum(arch_sh[k, i_base] * levels[k] for k in range(3))   # (n_iter,n_cat)
        fac = fac / np.maximum(exp_base[:, :, None], 1e-12)

        # ---- car-to-car variability
        veh = rng.normal(1.0, CV_VEHICLE, size=(n_iter, 1, 1))
        cat = rng.normal(1.0, cv_ind, size=(n_iter, n_cat, 1))
        var = np.clip(veh * cat, 0.05, None)

        length = (inp.length[seg][None, :, None] * SEGMENT_LENGTH_CALIBRATION[seg]
                  * fac * var)

        # ---- ADAS/sensor categories: driven by SENSOR COUNT, not architecture
        if inp.tier_shares is not None:
            cnt = _adas_metres_tier(rng, inp, seg, years, n_iter, met)
        else:
            cnt = np.zeros((n_iter, n_years))
            for si, stype in enumerate(sensor_types):
                per_level = np.array([
                    rng.triangular(*_tri(sens, lv, stype), size=n_iter) for lv in LEVELS
                ])                                                    # (6, n_iter)
                drawn = np.take_along_axis(per_level.T[:, :, None].repeat(n_years, axis=2),
                                           st_aut[:, None, :], axis=1)[:, 0, :]
                m = rng.triangular(*_tri_m(met, stype, seg), size=n_iter)[:, None]
                cnt += drawn * m                                      # metres
        # scale so the ADAS block reproduces its 2025 baseline total
        adas_base = inp.length[seg][is_adas].sum() * SEGMENT_LENGTH_CALIBRATION[seg]
        # ENSEMBLE mean, not per-iteration: dividing each iteration by its own
        # base-year value would pin every iteration to the same 2025 number and
        # delete the sensor-count uncertainty at precisely the anchor year.
        scale = adas_base / max(float(cnt[:, i_base].mean()), 1e-9)
        adas_len = cnt * scale
        share_within = inp.length[seg][is_adas] / max(adas_base, 1e-9)
        length[:, is_adas, :] = (adas_len[:, None, :] * share_within[None, :, None]
                                 * var[:, is_adas, :])

        length = np.clip(length, 0.0, None)

        # ---- Cu per metre; 800V shrinks HV conductors only
        gauge = rng.triangular(inp.gauge_min[None, :],
                               (inp.gauge_min + inp.gauge_max)[None, :] / 2.0,
                               np.maximum(inp.gauge_max, inp.gauge_min + 1e-9)[None, :],
                               size=(n_iter, n_cat))
        cu_per_m = np.repeat((gauge * RHO_CU_G_PER_CM3)[:, :, None], n_years, axis=2)
        u_volt = rng.random(n_iter)
        is800 = (u_volt[:, None] < inp.volt[seg][None, :])             # discrete, per year
        red = rng.triangular(*HV_800V_CU_REDUCTION_TRI, size=n_iter)[:, None]
        hv_scale = 1.0 - red * is800
        hv_scale = hv_scale / np.maximum(hv_scale[:, i_base][:, None], 1e-12)
        cu_per_m[:, is_hv, :] *= hv_scale[:, None, :]

        cu_kg = length * cu_per_m / 1000.0

        per_category[(METRIC_LENGTH, seg)] = length
        per_category[(METRIC_CU, seg)] = cu_kg
        totals[(METRIC_LENGTH, seg)] = length.sum(axis=1)
        totals[(METRIC_CU, seg)] = cu_kg.sum(axis=1)
        diag[("arch", seg)] = arch_sh
        diag[("autonomy", seg)] = aut_sh
        diag[("volt", seg)] = inp.volt[seg]

    for seg, j_seg in J_SUFFIX.items():
        adder = rng.triangular(*HEIGHT_ADDER_TRI, size=(n_iter, 1))
        for metric in METRICS:
            per_category[(metric, j_seg)] = per_category[(metric, seg)] * (1 + adder)[:, :, None]
            totals[(metric, j_seg)] = totals[(metric, seg)] * (1 + adder)

    return MCResult(years, BASE_SEGMENTS + list(J_SUFFIX.values()),
                    inp.codes, inp.groups, per_category, totals, diag)


def _adas_metres_tier(rng, inp, seg, years, n_iter, met):
    """ADAS wire metres per vehicle, from the hardware-tier axis (drivers A/B/C).

    Args:
        rng:    generator, shared with the caller so the whole run stays
                reproducible from one seed.
        inp:    Inputs, carrying the three drivers loaded from 19_.
        seg:    "AB" | "CD" | "EF".
        years:  (n_years,) UNIT: calendar years.
        n_iter: iterations.
        met:    Metres_per_Sensor, indexed (Sensor_Type, Segment). REUSED
                UNCHANGED from 18_ -- the tier axis changes how many sensors a
                car has, not how much wire each one needs.

    Returns:
        (n_iter, n_years) metres of ADAS wiring, before the 2025 rescale the
        caller applies.

    Three drivers, sampled independently per iteration:

      A  TIER. One uniform per iteration held across years, plus that
         iteration's own timing offset -- same comonotonic scheme as the
         architecture driver, so a vehicle is one hardware tier and not a blend.

      B  LIDAR. Separate, because lidar tracks cost and Chinese competitive
         pressure rather than tier or certification. Band membership is drawn
         per iteration (Min/Mode/Max = radar-substitutes / central /
         cost-collapse), and the China->Europe LAG IS SAMPLED, not fixed, so
         "China leads and Europe follows" is a testable hypothesis rather than
         a baked-in assumption. Lidar count is then tier count x equipped.

      C  SCENARIO. Post-2040 multiplier on every sensor count. Either drawn per
         iteration by weight (Active_Scenario = SAMPLE, so one run's band spans
         all three) or pinned. Identical to 1.0 at and before
         SCENARIO_START_YEAR by construction.
    """
    n_years = len(years)

    # --- A: discrete tier, comonotonic across years, with per-iteration timing
    shares = inp.tier_shares[seg]                                  # (n_tiers, n_years)
    d_tier = rng.normal(0.0, TRANSITION_TIMING_SPREAD_Y, size=n_iter)
    sh_i = _shift_shares(shares, years, d_tier)                    # (n_tiers,n_iter,n_years)
    u_tier = rng.random(n_iter)
    st_tier = (u_tier[None, :, None] > np.cumsum(sh_i, axis=0)).sum(axis=0)

    # --- B: lidar equipped, per iteration and year
    w = rng.random(n_iter)[:, None]
    band = np.where(w < 1 / 3, inp.lidar[0][None, :],
                    np.where(w < 2 / 3, inp.lidar[1][None, :], inp.lidar[2][None, :]))
    lag_mean, lag_sd = inp.lidar_lag
    # the table already embeds the mean lag, so shift by the DEVIATION from it
    d_lidar = rng.normal(lag_mean, lag_sd, size=n_iter) - lag_mean
    lid_share = np.empty((n_iter, n_years))
    for i in range(n_iter):
        lid_share[i] = np.interp(years - d_lidar[i], years, band[i])
    lid_share = np.clip(lid_share, 0.0, 1.0)
    equipped = (rng.random(n_iter)[:, None] < lid_share).astype(float)

    # --- C: scenario multiplier
    if inp.scen_active == "SAMPLE":
        pick = rng.choice(len(inp.scen_names), size=n_iter, p=inp.scen_w)
    else:
        pick = np.full(n_iter, inp.scen_names.index(inp.scen_active))
    mult_tab = np.vstack([inp.scen_mult[s] for s in inp.scen_names])  # (n_scen,n_years)
    mult = mult_tab[pick]                                             # (n_iter,n_years)

    # --- compose
    cnt = np.zeros((n_iter, n_years))
    for stype in SENSOR_TYPES:
        per_tier = np.array([
            rng.triangular(*_tri_tier(inp.tier_counts, t, stype), size=n_iter)
            for t in TIERS
        ])                                                            # (n_tiers,n_iter)
        drawn = np.take_along_axis(
            per_tier.T[:, :, None].repeat(n_years, axis=2),
            st_tier[:, None, :], axis=1)[:, 0, :]                      # (n_iter,n_years)
        if stype == "lidar":
            drawn = drawn * equipped
        m = rng.triangular(*_tri_m(met, stype, seg), size=n_iter)[:, None]
        cnt += drawn * mult * m
    return cnt


def _tri_tier(counts, tier, stype):
    """(min, mode, max) sensor count for a tier. Degenerate triples are widened
    by a hair so rng.triangular does not divide by a zero span."""
    lo, mo, hi = counts.get((tier, stype), (0.0, 0.0, 1e-9))
    return (lo, min(max(mo, lo), hi), max(hi, lo + 1e-9))


def _tri(sens, level, stype):
    """(min, mode, max) sensor count. Degenerate triples are widened by a hair
    so rng.triangular does not divide by a zero span."""
    try:
        r = sens.loc[(level, stype)]
        lo, mo, hi = float(r.Count_Min), float(r.Count_Mode), float(r.Count_Max)
    except KeyError:
        return (0.0, 0.0, 1e-9)
    return (lo, min(max(mo, lo), hi), max(hi, lo + 1e-9))


def _tri_m(met, stype, seg):
    try:
        r = met.loc[(stype, seg)]
        lo, mo, hi = float(r.m_Min), float(r.m_Mode), float(r.m_Max)
    except KeyError:
        return (0.0, 0.0, 1e-9)
    return (lo, min(max(mo, lo), hi), max(hi, lo + 1e-9))


# --------------------------------------------------------------------------
# 3b. CHUNKED ACCUMULATION  (for large n_iter)
#
#     Keeping every draw costs (n_iter x n_cat x n_years) float64 per metric
#     per segment. At 200,000 iterations that is ~31 GB, which no laptop will
#     survive. Instead the run is split into chunks and only STATISTICS are
#     accumulated: a running sum, and a fixed-bin histogram per series per year.
#     Memory then does not depend on n_iter at all.
#
#     Mean comes from the running sum (exact). Percentiles and Mode are read off
#     the histogram, so they are quantised to the bin width -- with
#     N_ACC_BINS bins that is ~0.2% of the range, well below the Monte Carlo
#     noise it replaces. The bin range is set by a pilot chunk and padded, and
#     any draw outside it is clamped into the end bins (reported as overflow).
# --------------------------------------------------------------------------

# INTERNAL accumulator resolution | UNIT: count of bins.
# This is NOT the histogram you get out -- exported histograms are always
# N_HIST_BINS (50), which is the fixed project convention. These finer bins
# exist only so percentiles are not quantised to 1/50th of the range, and they
# are summed down to exactly 50 for export.
# MUST be an exact multiple of N_HIST_BINS, or the summing is not clean.
N_ACC_BINS = 1000
PILOT_ITER = 2000     # iterations used only to find the histogram range
                      # | UNIT: count. Too few and the range is too tight, so
                      # more draws land in the overflow bins.
PILOT_PAD = 0.35      # fractional widening of the pilot range | UNIT: fraction.
                      # Guards against the pilot underestimating the tails.


assert N_ACC_BINS % N_HIST_BINS == 0, \
    f"N_ACC_BINS ({N_ACC_BINS}) must be a multiple of N_HIST_BINS ({N_HIST_BINS})"


class Accumulator:
    """Fixed-bin histogram accumulator. One entry per (key, year).

    Holds N_ACC_BINS fine bins internally for percentile resolution, and
    exposes coarse() which sums them down to exactly N_HIST_BINS for export.
    """

    def __init__(self, lo, hi, n_years, n_bins=N_ACC_BINS):
        span = np.where(hi - lo <= 0, 1.0, hi - lo)
        self.lo = lo - PILOT_PAD * span / 2.0
        self.hi = hi + PILOT_PAD * span / 2.0
        self.width = (self.hi - self.lo) / n_bins
        self.width = np.where(self.width <= 0, 1.0, self.width)
        self.n_bins = n_bins
        self.counts = np.zeros((n_years, n_bins), dtype=np.int64)
        self.total = np.zeros(n_years)
        self.n = 0
        self.under = np.zeros(n_years, dtype=np.int64)
        self.over = np.zeros(n_years, dtype=np.int64)

    def add(self, arr):                      # arr: (n_chunk, n_years)
        self.n += arr.shape[0]
        self.total += arr.sum(axis=0)
        idx = np.floor((arr - self.lo[None, :]) / self.width[None, :]).astype(np.int64)
        self.under += (idx < 0).sum(axis=0)
        self.over += (idx >= self.n_bins).sum(axis=0)
        np.clip(idx, 0, self.n_bins - 1, out=idx)
        for y in range(arr.shape[1]):
            self.counts[y] += np.bincount(idx[:, y], minlength=self.n_bins)

    @property
    def mean(self):
        return self.total / max(self.n, 1)

    def percentile(self, q):
        """q in 0..100. Linear interpolation within the containing bin."""
        out = np.empty(self.counts.shape[0])
        for y in range(self.counts.shape[0]):
            c = np.cumsum(self.counts[y])
            target = q / 100.0 * c[-1]
            i = int(np.searchsorted(c, target))
            i = min(i, self.n_bins - 1)
            below = c[i - 1] if i > 0 else 0
            frac = (target - below) / max(self.counts[y][i], 1)
            out[y] = self.lo[y] + (i + frac) * self.width[y]
        return out

    def mode(self):
        i = self.counts.argmax(axis=1)
        return self.lo + (i + 0.5) * self.width

    def edges(self, y):
        return self.lo[y] + np.arange(self.n_bins + 1) * self.width[y]

    def coarse(self, y, n_out=None):
        """Sum the fine bins down to exactly n_out bins (default N_HIST_BINS).

        Returns (edges, counts) with len(counts) == n_out. Exact, because
        N_ACC_BINS is constrained to be a multiple of N_HIST_BINS.
        """
        n_out = n_out or N_HIST_BINS
        k = self.n_bins // n_out
        counts = self.counts[y].reshape(n_out, k).sum(axis=1)
        w = self.width[y] * k
        edges = self.lo[y] + np.arange(n_out + 1) * w
        return edges, counts

    def coarse_mode(self):
        """Mode read off the SAME 50-bin histogram that gets exported, so the
        reported Mode can always be reproduced from the histogram file."""
        out = np.empty(self.counts.shape[0])
        for y in range(self.counts.shape[0]):
            e, c = self.coarse(y)
            i = int(np.argmax(c))
            out[y] = 0.5 * (e[i] + e[i + 1])
        return out


def _series(result: MCResult):
    """Yield (tags, array) for every series the model reports, so the plain and
    the accumulated paths cannot report different things."""
    for metric in METRICS:
        for seg in result.segments:
            arr = result.per_category[(metric, seg)]
            for c, code in enumerate(result.codes):
                yield dict(Level="Category", Segment=seg, Code=code,
                           Functional_Group=result.groups[c], Metric=metric), arr[:, c, :]
            for grp in sorted(set(result.groups)):
                idx = [i for i, g in enumerate(result.groups) if g == grp]
                yield dict(Level="Group", Segment=seg, Code=grp,
                           Functional_Group=grp, Metric=metric), arr[:, idx, :].sum(axis=1)
            yield dict(Level="Total", Segment=seg, Code="TOTAL",
                       Functional_Group="TOTAL", Metric=metric), result.totals[(metric, seg)]


def run_accumulated(n_iter, chunk=5000, seed=RANDOM_SEED,
                    start_year=START_YEAR, end_year=END_YEAR, verbose=True):
    """Run n_iter iterations in chunks, keeping only statistics.

    Returns (accumulators, years, key_order). Memory is independent of n_iter:
    ~40 MB of histogram counts regardless of whether n_iter is 3,000 or
    200,000. Runtime is linear.
    """
    years = np.arange(start_year, end_year + 1)

    if verbose:
        print(f"  pilot {PILOT_ITER} iterations to set histogram ranges...")
    pilot = run_monte_carlo(n_iter=PILOT_ITER, seed=seed,
                            start_year=start_year, end_year=end_year)
    accs, keys = {}, []
    for tags, arr in _series(pilot):
        k = (tags["Metric"], tags["Segment"], tags["Level"], tags["Code"])
        accs[k] = Accumulator(arr.min(axis=0), arr.max(axis=0), len(years))
        accs[k].tags = tags
        keys.append(k)
    del pilot

    done = 0
    while done < n_iter:
        n = min(chunk, n_iter - done)
        # a distinct seed per chunk keeps chunks independent and the whole run
        # reproducible from `seed` alone
        r = run_monte_carlo(n_iter=n, seed=seed + 1000 + done,
                            start_year=start_year, end_year=end_year)
        for tags, arr in _series(r):
            accs[(tags["Metric"], tags["Segment"], tags["Level"], tags["Code"])].add(arr)
        del r
        done += n
        if verbose:
            print(f"    {done:>7,} / {n_iter:,}")
    return accs, years, keys


def build_stats_accumulated(accs, years, keys) -> pd.DataFrame:
    rows = []
    for k in keys:
        a = accs[k]
        lo = a.percentile(STAT_PCTS[0]); hi = a.percentile(STAT_PCTS[1])
        med = a.percentile(50); mean = a.mean; mode = a.coarse_mode()
        for i, y in enumerate(years):
            rows.append(dict(**a.tags, Drivetrain=DRIVETRAIN, Year=int(y), N_Iter=a.n,
                             Mean=mean[i], **{COL_LO: lo[i]}, Median=med[i],
                             Mode=mode[i], **{COL_HI: hi[i]}))
    return pd.DataFrame(rows)


def build_histograms(accs, years, keys, snapshot_years=None) -> pd.DataFrame:
    """Every series, every snapshot year, exactly N_HIST_BINS (50) bins.

    50 bins is the fixed project convention. Empty bins ARE included, so every
    series-year has exactly 50 rows and nothing downstream has to reindex.
    The Mode in the stats table is the centre of the fullest bin here, so the
    two files can never disagree.
    """
    snapshot_years = snapshot_years or SNAPSHOT_YEARS
    rows = []
    for k in keys:
        a = accs[k]
        for y in snapshot_years:
            i = int(np.searchsorted(years, y))
            if i >= len(years):
                continue
            e, c = a.coarse(i)
            for b in range(N_HIST_BINS):
                rows.append(dict(**a.tags, Drivetrain=DRIVETRAIN, Year=int(y),
                                 Bin=b + 1, Bin_Left=e[b], Bin_Right=e[b + 1],
                                 Count=int(c[b])))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# 4. STATS
# --------------------------------------------------------------------------

def _mode_from_hist(col):
    counts, edges = np.histogram(col, bins=N_HIST_BINS)
    i = int(np.argmax(counts))
    return 0.5 * (edges[i] + edges[i + 1])


def _rows_for(arr, years, **tags):
    lo, med, hi = np.percentile(arr, [STAT_PCTS[0], 50, STAT_PCTS[1]], axis=0)
    mean = arr.mean(axis=0)
    return [dict(**tags, Year=int(y), N_Iter=arr.shape[0], Mean=mean[i],
                 **{COL_LO: lo[i]}, Median=med[i], Mode=_mode_from_hist(arr[:, i]),
                 **{COL_HI: hi[i]}) for i, y in enumerate(years)]


def build_stats(result: MCResult) -> pd.DataFrame:
    rows = []
    for metric in METRICS:
        for seg in result.segments:
            arr = result.per_category[(metric, seg)]
            for c, code in enumerate(result.codes):
                rows += _rows_for(arr[:, c, :], result.years, Level="Category",
                                  Segment=seg, Drivetrain=DRIVETRAIN, Code=code,
                                  Functional_Group=result.groups[c], Metric=metric)
            for grp in sorted(set(result.groups)):
                idx = [i for i, g in enumerate(result.groups) if g == grp]
                rows += _rows_for(arr[:, idx, :].sum(axis=1), result.years,
                                  Level="Group", Segment=seg, Drivetrain=DRIVETRAIN,
                                  Code=grp, Functional_Group=grp, Metric=metric)
            rows += _rows_for(result.totals[(metric, seg)], result.years,
                              Level="Total", Segment=seg, Drivetrain=DRIVETRAIN,
                              Code="TOTAL", Functional_Group="TOTAL", Metric=metric)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# 5. PLOTS
# --------------------------------------------------------------------------

def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def plot_totals(result, out_path):
    plt = _plt()
    colors = {"AB": "#1f77b4", "CD": "#ff7f0e", "EF": "#2ca02c"}
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), sharex=True)
    for ax, metric in zip(axes, METRICS):
        for seg in BASE_SEGMENTS:
            arr = result.totals[(metric, seg)]
            lo, hi = np.percentile(arr, [STAT_PCTS[0], STAT_PCTS[1]], axis=0)
            ax.plot(result.years, arr.mean(axis=0), color=colors[seg], lw=1.9, label=seg)
            ax.fill_between(result.years, lo, hi, color=colors[seg], alpha=0.15)
        ax.set_title(f"{metric} per new vehicle (TOTAL)")
        ax.set_xlabel("Year"); ax.set_ylabel(metric); ax.grid(alpha=0.3)
    axes[0].legend(fontsize=9)
    fig.suptitle(f"BEV wiring -- MEAN and P{STAT_PCTS[0]:g}-P{STAT_PCTS[1]:g}  (mean, not median: the state mixture is bimodal)", fontsize=12)
    plt.tight_layout(rect=[0, 0, 1, 0.95]); plt.savefig(out_path, dpi=140); plt.close(fig)


def plot_drivers(result, out_path):
    plt = _plt()
    colors = {"AB": "#1f77b4", "CD": "#ff7f0e", "EF": "#2ca02c"}
    fig, axes = plt.subplots(1, 3, figsize=(17, 4.6))
    for seg in BASE_SEGMENTS:
        axes[0].plot(result.years, 100 * result.diagnostics[("arch", seg)][2],
                     color=colors[seg], lw=1.8, label=seg)
        axes[1].plot(result.years, 100 * result.diagnostics[("volt", seg)],
                     color=colors[seg], lw=1.8, label=seg)
        aut = result.diagnostics[("autonomy", seg)]
        axes[2].plot(result.years, 100 * aut[3:].sum(axis=0),
                     color=colors[seg], lw=1.8, label=seg)
    for ax, t in zip(axes, ("SDV / zonal architecture", "800V", "Autonomy L3 or better")):
        ax.set_title(t); ax.set_xlabel("Year"); ax.set_ylabel("% of new vehicles sold")
        ax.grid(alpha=0.3); ax.legend(fontsize=8)
    fig.suptitle("The three independent drivers (mode shares)", fontsize=12)
    plt.tight_layout(rect=[0, 0, 1, 0.93]); plt.savefig(out_path, dpi=140); plt.close(fig)


def plot_group_grid(result, segment, metric, out_path):
    plt = _plt()
    groups = sorted(set(result.groups))
    ncols = 3; nrows = int(np.ceil(len(groups) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(15, 3.4 * nrows), sharex=True)
    axes = np.atleast_1d(axes).flatten()
    arr = result.per_category[(metric, segment)]
    for ax, grp in zip(axes, groups):
        idx = [i for i, g in enumerate(result.groups) if g == grp]
        a = arr[:, idx, :].sum(axis=1)
        lo, hi = np.percentile(a, [STAT_PCTS[0], STAT_PCTS[1]], axis=0)
        ax.plot(result.years, a.mean(axis=0), color="#d62728", lw=1.7)
        ax.fill_between(result.years, lo, hi, color="#d62728", alpha=0.18)
        ax.set_title(grp, fontsize=10); ax.grid(alpha=0.3); ax.tick_params(labelsize=8)
    for ax in axes[len(groups):]:
        ax.axis("off")
    fig.suptitle(f"{segment} ({DRIVETRAIN}) -- {metric} by functional group", fontsize=12)
    plt.tight_layout(rect=[0, 0, 1, 0.95]); plt.savefig(out_path, dpi=130); plt.close(fig)



def plot_histograms_total(accs, years, keys, segment, metric, out_path):
    """Distribution of the segment TOTAL at each snapshot year.

    Bars come from Accumulator.coarse(), i.e. the SAME 50 bins written to
    bev_wiring_histograms.csv, so figure and file can never disagree.
    """
    plt = _plt()
    a = accs[(metric, segment, "Total", "TOTAL")]
    yrs = [y for y in SNAPSHOT_YEARS if y <= years[-1]]
    ncols = 4
    nrows = int(np.ceil(len(yrs) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.0 * ncols, 3.1 * nrows))
    axes = np.atleast_1d(axes).flatten()
    for ax, y in zip(axes, yrs):
        i = int(np.searchsorted(years, y))
        e, c = a.coarse(i)
        ax.bar(0.5 * (e[:-1] + e[1:]), c, width=(e[1] - e[0]),
               color="#1f77b4", alpha=0.85, edgecolor="none")
        ax.axvline(a.mean[i], color="#d62728", lw=1.6, label="mean")
        ax.axvline(a.percentile(STAT_PCTS[0])[i], color="k", lw=0.9, ls=":")
        ax.axvline(a.percentile(STAT_PCTS[1])[i], color="k", lw=0.9, ls=":")
        ax.set_title(f"{y}", fontsize=10)
        ax.set_xlabel(metric, fontsize=8)
        ax.tick_params(labelsize=7)
    axes[0].legend(fontsize=7)
    for ax in axes[len(yrs):]:
        ax.axis("off")
    fig.suptitle(f"{segment} ({DRIVETRAIN}) -- {metric} TOTAL distribution, "
                 f"{N_HIST_BINS} bins, n={a.n:,}   (dotted = P{STAT_PCTS[0]:g}/P{STAT_PCTS[1]:g})",
                 fontsize=11)
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    plt.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_histograms_groups(accs, years, keys, segment, metric, year, out_path):
    """Distribution per functional group at one year, same 50 bins as the CSV."""
    plt = _plt()
    groups = sorted({k[3] for k in keys if k[2] == "Group"})
    ncols = 3
    nrows = int(np.ceil(len(groups) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.6 * ncols, 3.2 * nrows))
    axes = np.atleast_1d(axes).flatten()
    i = int(np.searchsorted(years, year))
    for ax, g in zip(axes, groups):
        a = accs[(metric, segment, "Group", g)]
        e, c = a.coarse(i)
        ax.bar(0.5 * (e[:-1] + e[1:]), c, width=(e[1] - e[0]),
               color="#d62728", alpha=0.8, edgecolor="none")
        ax.axvline(a.mean[i], color="k", lw=1.4)
        ax.set_title(g, fontsize=10)
        ax.set_xlabel(metric, fontsize=8)
        ax.tick_params(labelsize=7)
    for ax in axes[len(groups):]:
        ax.axis("off")
    fig.suptitle(f"{segment} ({DRIVETRAIN}) -- {metric} by functional group, {year}   "
                 f"({N_HIST_BINS} bins, n={accs[(metric, segment, 'Total', 'TOTAL')].n:,}; "
                 f"black = mean)", fontsize=11)
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.savefig(out_path, dpi=130)
    plt.close(fig)


# --------------------------------------------------------------------------
# 5b. VALIDATION
#
#     The targets in 19_ sheet Validation, executed. The point is that a report
#     drifting away from the code becomes a TEST FAILURE rather than something
#     discovered six months later.
#
#     Tolerances come from the Uncertainty sheet and are deliberately no tighter
#     than the sources agree with each other. A single source in this chain
#     disagrees with ITSELF by ~3% (the EF row sum, 3646 vs a stated 3546), so
#     demanding better than that of the model would be demanding it reproduce
#     noise.
# --------------------------------------------------------------------------

def validate(result, inp, verbose=True) -> list:
    """Check the model against the report's validation targets.

    Returns a list of (id, name, got, want, tol, passed). Raises nothing --
    the caller decides whether a failure is fatal, because V1 and V4 legitimately
    wobble at low iteration counts.
    """
    years = result.years
    iy = {int(y): i for i, y in enumerate(years)}
    i25 = iy[BASE_YEAR]
    out = []

    def chk(vid, name, got, want, tol, rel=False):
        dev = abs(got - want) / abs(want) if rel else abs(got - want)
        out.append((vid, name, got, want, tol, dev <= tol))

    # V1 -- 2025 length anchors
    for seg, want in (("AB", 1392.0), ("CD", 2486.0), ("EF", 3546.0)):
        got = float(result.totals[(METRIC_LENGTH, seg)][:, i25].mean())
        chk("V1", f"2025 length {seg}", got, want, 0.03, rel=True)

    # V6 -- tier shares sum to 1
    if inp.tier_shares is not None:
        dev = max(float(np.abs(inp.tier_shares[s].sum(axis=0) - 1).max())
                  for s in BASE_SEGMENTS)
        chk("V6", "tier shares sum to 1", dev, 0.0, 1e-9)

    # V8 -- ADAS share of total length at 2025
    ia = [i for i, g in enumerate(result.groups) if g == ADAS_GROUP]
    for seg, want in (("AB", 6.0), ("CD", 9.0), ("EF", 11.0)):
        a = result.per_category[(METRIC_LENGTH, seg)][:, ia, :].sum(axis=1)[:, i25].mean()
        t = result.totals[(METRIC_LENGTH, seg)][:, i25].mean()
        chk("V8", f"ADAS share {seg} %", 100.0 * a / t, want, 3.0)

    # V9 -- Driver C is inert at and before SCENARIO_START_YEAR
    if inp.scen_mult is not None:
        i40 = iy.get(SCENARIO_START_YEAR)
        if i40 is not None:
            dev = max(abs(float(inp.scen_mult[s][i40]) - 1.0) for s in inp.scen_names)
            chk("V9", f"scenario multiplier at {SCENARIO_START_YEAR}", dev, 0.0, 1e-9)

    # V10 -- scenario weights sum to 1
    if inp.scen_w is not None:
        chk("V10", "scenario weights sum", float(inp.scen_w.sum()), 1.0, 1e-9)

    if verbose:
        print("\nValidation (targets: 19_ sheet Validation; tolerances from "
              "sheet Uncertainty)")
        for vid, name, got, want, tol, ok in out:
            mark = "ok  " if ok else "FAIL"
            print(f"  [{mark}] {vid:<4} {name:<26} got {got:>10.4f}   "
                  f"want {want:>8.3f}  tol {tol:g}")
        bad = [o for o in out if not o[5]]
        print(f"  {len(out) - len(bad)}/{len(out)} passed"
              + (f"  --  FAILED: {', '.join(o[0] + ' ' + o[1] for o in bad)}"
                 if bad else ""))
    return out


# --------------------------------------------------------------------------
# 6. MAIN
# --------------------------------------------------------------------------

def _suffix() -> str:
    """Output filename suffix. Empty for SAMPLE, so existing filenames are
    unchanged; '_S2' etc. when pinned, so scenario runs cannot silently
    overwrite one another."""
    if not USE_TIER_AXIS:
        return "_levelaxis"
    act = SCENARIO_OVERRIDE
    if act is None:
        try:
            act = _read_active_scenario()
        except Exception:
            act = "SAMPLE"
    return "" if act == "SAMPLE" else f"_{act}"


if __name__ == "__main__":
    SFX = _suffix()
    if SFX:
        OUT_SUBDIRS = {"data": OUT_DIR / f"data{SFX}", "plots": OUT_DIR / f"plots{SFX}"}
        for _p in OUT_SUBDIRS.values():
            _p.mkdir(parents=True, exist_ok=True)

    print("BEV wiring -- state-based, sensor-coupled")
    print(f"  baseline     : {BASELINE_FILE.name}")
    print(f"  penetration  : {PENETRATION_FILE.name}")
    if USE_TIER_AXIS:
        print(f"  ADAS adoption: {ADAS_FILE.name}  "
              f"(hardware-tier axis, drivers A/B/C)")
        print(f"  scenario     : {SFX[1:] if SFX else 'SAMPLE'}"
              f"{'  (band spans S1/S2/S3)' if not SFX else '  (pinned)'}")
    else:
        print(f"  ADAS adoption: OLD SAE-level axis (18_ Sensors_per_Level)")
    print(f"  {START_YEAR}-{END_YEAR}, {N_ITER} iterations, seed {RANDOM_SEED}\n")

    # Statistics come from the CHUNKED path, so N_ITER can be raised to
    # hundreds of thousands without the memory blowing up. Plots still use a
    # smaller full-draw run, because they need the raw arrays.
    accs, years, keys = run_accumulated(N_ITER, chunk=CHUNK_ITER)
    stats = build_stats_accumulated(accs, years, keys)
    stats.to_csv(OUT_SUBDIRS["data"] / f"bev_wiring_stats{SFX}.csv", index=False)
    print(f"  {len(stats):>7,} rows -> data{SFX}/bev_wiring_stats{SFX}.csv")

    hist = build_histograms(accs, years, keys)
    hist.to_csv(OUT_SUBDIRS["data"] / f"bev_wiring_histograms{SFX}.csv", index=False)
    print(f"  {len(hist):>7,} rows -> data{SFX}/bev_wiring_histograms{SFX}.csv "
          f"({len(keys)} series x {len(SNAPSHOT_YEARS)} snapshot years)")

    ov = sum(int(accs[k].over.sum() + accs[k].under.sum()) for k in keys)
    seen = sum(int(accs[k].n) * len(years) for k in keys)
    print(f"  draws outside histogram range: {ov:,} / {seen:,} ({100*ov/max(seen,1):.4f}%)")

    result = run_monte_carlo(n_iter=min(N_ITER, N_ITER_PLOTS))

    print("  histogram figures (same 50 bins as the CSV)...")
    for seg in result.segments:
        for metric in METRICS:
            plot_histograms_total(accs, years, keys, seg, metric,
                                  OUT_SUBDIRS["plots"] / f"hist_total_{seg}_{METRIC_SLUG[metric]}.png")
    for seg in BASE_SEGMENTS:
        for metric in METRICS:
            for y in HIST_PLOT_YEARS:
                plot_histograms_groups(accs, years, keys, seg, metric, y,
                                       OUT_SUBDIRS["plots"] / f"hist_groups_{seg}_{METRIC_SLUG[metric]}_{y}.png")

    plot_totals(result, OUT_SUBDIRS["plots"] / "totals.png")
    plot_drivers(result, OUT_SUBDIRS["plots"] / "drivers.png")
    for seg in BASE_SEGMENTS:
        for metric in METRICS:
            plot_group_grid(result, seg, metric,
                            OUT_SUBDIRS["plots"] / f"groups_{seg}_{METRIC_SLUG[metric]}.png")
    print(f"  plots -> {OUT_SUBDIRS['plots']}")

    print("\nSanity check -- MEAN per new vehicle (the anchored quantity;\n  the median sits lower because the architecture mixture is bimodal)")
    for metric in METRICS:
        print(f"\n  {metric}")
        print(f"    {'seg':<8}" + "".join(f"{y:>9}" for y in SNAPSHOT_YEARS))
        for seg in result.segments:
            m = result.totals[(metric, seg)].mean(axis=0)
            print(f"    {seg:<8}" + "".join(
                f"{m[np.searchsorted(result.years, y)]:>9.1f}" for y in SNAPSHOT_YEARS))
    print("\n  Report anchors (2025, per new vehicle):")
    print("    Length (m)  AB 1392   CD 2486   EF 3546")
    print("    Cu (kg)     AB  33.9  CD   60.3  EF  74.6")

    validate(result, load_inputs(result.years))
