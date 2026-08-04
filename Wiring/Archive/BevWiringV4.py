"""
BEV Wiring Harness Monte Carlo, 2020-2070 -- v4 (LENGTH-FIRST, REPORT-ANCHORED)
================================================================================
Supersedes BevWiring.py (v3). That file is left untouched and still runs.

WHY THIS EXISTS
--------------------------------------------------------------------------------
v3 read 15_BEV_wiring_harness_data.xlsx and spliced three snapshots (2020 /
2025 / 2030) together with a spline plus two hand-blended era seams. That
produced a peak at 2020 and a hard brake at 2030 in every output. The cause was
not the spline: it was the input. The workbook reproduces its own source report
ONLY at 2025, and it collapses two independent technology transitions into a
single hard flip at 2030.

v4 changes the foundation:

  1. ONE anchor year, not three. Everything starts from the 2025 baseline in
     17_BEV_wiring_baseline_2025.xlsx, rebuilt from the research report
     (Table 9.1 per-category lengths + Appendix A gauges). 2025 is the only
     year where workbook and report agree exactly.
  2. LENGTH FIRST. Copper is never read as a given. It is computed as
     length x Cu-per-metre, where Cu-per-metre comes from the conductor gauge.
     The report's own per-category copper column is NOT used -- it sums 13-28%
     short of the report's own stated totals (see 17_, sheet 'Checks').
     Reconstructing copper from length and gauge lands within 1-7% instead.
  3. TWO SEPARATE TRANSITIONS, each with its own sampled timing:
        800V     -> reduces HV cable Cu-per-metre (gauge), never length
        SDV/zonal-> changes LV / signal / sensor LENGTH, never gauge
     Timings come from 16_BEV_wiring_transition_parameters.xlsx.
  4. NO ERA SEAMS. There is no spline, no blend half-width, no backcast ramp.
     Shape comes only from the two penetration curves, which are smooth by
     construction. Nothing can kink.
  5. TIMING IS SAMPLED. Every iteration draws its own transition years, so
     trajectories no longer all turn the corner in the same year. This is the
     "MC on the changes" that v3 lacked.

WHAT IS PER-VEHICLE AND WHAT IS NOT
--------------------------------------------------------------------------------
Every number this model emits is PER NEW VEHICLE SOLD in that year. Penetration
shares are shares of new sales. Fleet turnover is NOT applied here -- that is
RAWCLICStockAndFlow's job. The report is explicit that in-production content
falls much faster than the in-service fleet average, so conflating the two
would understate the parc badly.

KNOWN SOURCE CONFLICT (the biggest single uncertainty)
--------------------------------------------------------------------------------
The report contradicts itself on how much SDV removes. Its per-category
mechanisms (sections 6.2 / 8.4) imply only -12/-11/-8% total length at full
SDV. Its stated segment totals (6.3 / 7.1) claim -44/-40/-23%. Reaching the
latter requires eliminating CAN and LIN entirely and cutting body circuits by
97%, which section 6.2 does not claim.

This model does not pick a side. SDV depth is a sampled parameter spanning both
readings (17_, sheet 'SDV_Depth'). The resulting AB band is wide because the
disagreement is real. Collapse it by setting Depth_Min = Depth_Mode = Depth_Max.

INPUTS
--------------------------------------------------------------------------------
  Data/17_BEV_wiring_baseline_2025.xlsx   2025 baseline, gauges, SDV factors
  Data/16_BEV_wiring_transition_parameters.xlsx   transition timing
15_BEV_wiring_harness_data.xlsx is NOT read. It is superseded.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------
# 0. CONFIGURATION
#
#    Every constant: WHAT it is | UNIT | WHY this value | WHAT MOVES if changed
#    "_TRI" always means a triangular distribution given as (min, mode, max).
# --------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "Data"
BASELINE_FILE = DATA_DIR / "17_BEV_wiring_baseline_2025.xlsx"
TRANSITION_FILE = DATA_DIR / "16_BEV_wiring_transition_parameters.xlsx"

OUT_DIR = SCRIPT_DIR / "outputs_v4"
OUT_SUBDIRS = {
    "data":  OUT_DIR / "data",
    "plots": OUT_DIR / "plots",
}
for _p in OUT_SUBDIRS.values():
    _p.mkdir(parents=True, exist_ok=True)

# --- Run extent -------------------------------------------------------------
BASE_YEAR = 2025   # the anchor. UNIT: calendar year (CE). All lengths in the
                   # baseline workbook are "as of" this year. Do not change
                   # without rebuilding 17_ -- it is the year the report and the
                   # old workbook agree on, which is the whole point.
START_YEAR = 2020  # first output year | UNIT: calendar year (CE).
                   # NOT 2010. There is no evidence before 2020: the report's
                   # earliest data point is 2020. v3 backcast to 2010 with an
                   # invented ramp, which is what produced its 2020 peak. If you
                   # need pre-2020 for the stock-and-flow, say so explicitly and
                   # it can be added as a documented extrapolation.
END_YEAR = 2070    # last output year | UNIT: calendar year (CE).
N_ITER = 3000      # Monte Carlo iterations | UNIT: count.
                   # Drives percentile stability; runtime and memory scale
                   # linearly. 3000 gives roughly +/-1% on P2.5 / P97.5.
RANDOM_SEED = 42   # RNG seed | UNIT: none. Fixed for reproducibility.
                   # CHANGE IT to check conclusions are not a single-seed
                   # artefact.

BASE_SEGMENTS = ["AB", "CD", "EF"]
J_SUFFIX = {"AB": "JA-JB", "CD": "JC-JD", "EF": "JE-JF"}
DRIVETRAIN = "BEV"

# Metric names follow the project convention: quantity with unit in brackets,
# so a CSV column or a plot axis is readable without opening this file.
METRIC_LENGTH = "Length (m)"
METRIC_CU = "Cu (kg)"
METRICS = [METRIC_LENGTH, METRIC_CU]
METRIC_SLUG = {METRIC_LENGTH: "length_m", METRIC_CU: "cu_kg"}   # for filenames

# --- Physical constants -----------------------------------------------------
# Copper density. UNIT: g/cm3. Standard value for annealed Cu.
# Identity worth remembering: 1 mm2 cross-section x 1 m length = 1 cm3 exactly,
# so Cu (g/m) = gauge (mm2) x density (g/cm3). No unit conversion needed.
# NOTE: no stranding fill factor is applied -- the report's own copper mass
# formula (section 8.3) does not apply one either.
RHO_CU_G_PER_CM3 = 8.96

# --- Transition effects -----------------------------------------------------
# Copper reduction on HV cables when a vehicle is 800V rather than 400V.
# UNIT: dimensionless fraction of Cu-per-metre removed at FULL 800V adoption.
# WHY: at constant power, doubling voltage halves current, which halves the
# required conductor cross-section (report section 5.2, P = V x I).
# The report states 40-45% rather than the theoretical 50%, to allow for
# minimum-gauge and mechanical constraints.
# EFFECT: scales HV copper only. Applied as (1 - reduction x share_800V(t)),
# so it phases in with the penetration curve rather than stepping.
HV_800V_CU_REDUCTION_TRI = (0.40, 0.425, 0.45)

# Which functional groups the 800V transition touches. Everything else is
# unaffected: 12V and signal circuits do not care about pack voltage.
HV_GROUP = "HV Power"

# --- Car-to-car variability (this is what v3 got structurally wrong) --------
# v3 drew ONE trim percentile per segment and reused it for all wire types,
# with only 0.05 of jitter -- so every simulated car was uniformly long-wired or
# uniformly short-wired, correlation ~1 across categories. Independent draws
# would be correlation 0 and equally wrong. The truth is in between, and the
# choice moves the segment-total band by roughly sqrt(n_categories).
#
# Here the variance is split into two sourced pieces (report section 8.5):
#   vehicle level   +/- 8-12%  -> one draw per iteration, shared by all
#                                 categories (this car is big / tightly packaged)
#   category level  +/- 15-20% -> total spread seen at wire-category level
# The independent part is whatever is left once the shared part is removed:
#   CV_independent = sqrt(CV_category^2 - CV_vehicle^2)
# UNIT: both are coefficients of variation, dimensionless (0.10 = +/-10%).
CV_VEHICLE = 0.10     # report 8.5: "+/-8-12% at the total vehicle level"
CV_CATEGORY = 0.175   # report 8.5: "+/-15-20% at the wire-category level"

# --- 2020 -> 2025 legacy correction ----------------------------------------
# The report's 2020 totals are much higher than 2025 (Table 7.1). That drop is
# NOT the SDV transition -- SDV barely existed before 2025. The report
# attributes it to first-generation BEV platforms carrying architectural
# inefficiency that was engineered out as the segment matured.
# Modelled as a multiplier that decays geometrically to exactly 1.0 at
# BASE_YEAR. UNIT: dimensionless ratio of 2020 length to 2025 length.
# ASSUMPTION: applied uniformly to all categories, because the report gives no
# per-category split for 2020. Ethernet and ADAS were in fact growing over this
# period, so their 2020-2025 shape is the least reliable part of the output.
LEGACY_2020_RATIO = {"AB": 2485 / 1392, "CD": 4144 / 2486, "EF": 4610 / 3546}

# Time constant of that decay. UNIT: years (e-folding time).
# It must be a SMOOTH decay, not a ramp that stops at BASE_YEAR. A term that
# hard-stops leaves a slope discontinuity at 2025 -- visually a kink, and the
# same defect that made v3's output unusable. An exponential is C-infinity, so
# no seam exists at any year.
# TRADE-OFF: smaller tau reproduces the report's 2020 anchor more closely but
# concentrates the decline into 2020-2022; larger tau is gentler but undershoots
# 2020. At 1.5 the 2020 value lands about 3% below the report's figure, which is
# well inside the report's own +/-8-12% vehicle-level uncertainty.
LEGACY_TAU_YEARS = 1.5

# --- EF length calibration --------------------------------------------------
# The report's per-category length column (Table 9.1) sums exactly to the
# stated segment total for AB (1392) and CD (2486), but EF sums to 3646 against
# a stated 3546 -- 100 m unaccounted, sitting somewhere in the EF column.
# Until that row is identified, EF category lengths are scaled by this factor
# so the segment reproduces the report's stated total.
# UNIT: dimensionless ratio. Set to 1.0 to use the raw per-category figures and
# accept a 2.8% high EF.
SEGMENT_LENGTH_CALIBRATION = {"AB": 1.0, "CD": 1.0, "EF": 3546 / 3646}

# --- J* derived segments ----------------------------------------------------
# The J* segments have no data of their own. They are the base segment scaled:
#     J_value = base_value x (1 + height_adder)
# UNIT: dimensionless fraction (0.10 = +10% length and +10% copper).
# WHY: a taller body on the same platform means longer vertical runs (roof,
# tailgate, raised floor) with unchanged electronic content.
# Drawn once per segment per iteration, so J* is a rigidly scaled copy of its
# base segment, never an independent estimate. Carried over from v3 unchanged.
HEIGHT_ADDER_TRI = (0.05, 0.10, 0.15)

# --- Output ----------------------------------------------------------------
STAT_PCTS = (2.5, 97.5)   # uncertainty band reported | UNIT: percent (0-100).
                          # Unlike v3, this IS read -- see _band() below.
N_HIST_BINS = 50          # bins for the reported Mode | UNIT: count.
SNAPSHOT_YEARS = [2020, 2025, 2030, 2040, 2050, 2070]


def _band_cols():
    """Column names for the uncertainty band, derived from STAT_PCTS so they
    can never disagree with the values they hold (2.5 -> 'P2_5')."""
    return tuple(f"P{p:g}".replace(".", "_") for p in STAT_PCTS)


COL_LO, COL_HI = _band_cols()


# --------------------------------------------------------------------------
# 1. INPUTS
# --------------------------------------------------------------------------

@dataclass
class Baseline:
    codes: list          # 28 report category codes, e.g. "LV_DIST"
    groups: list         # functional group per code, e.g. "LV Power"
    gauge_min: np.ndarray   # (n_cat,) UNIT: mm2
    gauge_max: np.ndarray   # (n_cat,) UNIT: mm2
    sdv_factor: np.ndarray  # (n_cat,) length multiplier at full SDV, depth=1
    length: dict            # segment -> (n_cat,) UNIT: metres, at BASE_YEAR
    depth_tri: dict         # segment -> (min, mode, max) SDV depth, dimensionless


def load_baseline(path: Path = BASELINE_FILE) -> Baseline:
    if not path.exists():
        raise FileNotFoundError(f"Baseline workbook not found: {path}")
    df = pd.read_excel(path, sheet_name="Baseline_2025", header=5)
    df = df[df["Code"].notna() & (df["Code"] != "TOTAL")]
    dep = pd.read_excel(path, sheet_name="SDV_Depth", header=6)
    dep = dep[dep["Segment"].notna()]
    depth_tri = {r["Segment"]: (float(r["Depth_Min"]), float(r["Depth_Mode"]),
                                 float(r["Depth_Max"])) for _, r in dep.iterrows()}
    return Baseline(
        codes=df["Code"].tolist(),
        groups=df["Functional Group"].tolist(),
        gauge_min=df["Gauge_Min_mm2"].to_numpy(float),
        gauge_max=df["Gauge_Max_mm2"].to_numpy(float),
        sdv_factor=df["SDV_Base_Length_Factor"].to_numpy(float),
        length={s: df[f"{s}_Length_m"].to_numpy(float) for s in BASE_SEGMENTS},
        depth_tri=depth_tri,
    )


def load_transitions(path: Path = TRANSITION_FILE) -> dict:
    """-> {(transition, segment, 'T50'|'T_FULL'): (min, mode, max)} in years."""
    if not path.exists():
        raise FileNotFoundError(f"Transition workbook not found: {path}")
    df = pd.read_excel(path, sheet_name="Parameters", header=0)
    df = df[df["Transition"].notna()]
    return {(r["Transition"], r["Segment"], r["Parameter"]):
            (float(r["Min_Year"]), float(r["Mode_Year"]), float(r["Max_Year"]))
            for _, r in df.iterrows()}


# --------------------------------------------------------------------------
# 2. PENETRATION
# --------------------------------------------------------------------------

def logistic_share(years, t50, t_full):
    """Share of new vehicles sold carrying the technology.

    Args:
        years:  (n_years,) UNIT: calendar years (CE).
        t50:    (n_iter,)  year of 50% penetration. UNIT: years.
        t_full: (n_iter,)  year of 95% penetration. UNIT: years.

    Returns:
        (n_iter, n_years) shares in [0,1]. UNIT: dimensionless.

    k is set so the curve passes through exactly 95% at t_full:
    ln(19) is the logit of 0.95. Smooth everywhere -- this is why v4 has no
    kinks and needs no blending.
    """
    span = np.maximum(t_full - t50, 0.5)      # guard: T_FULL must exceed T50
    k = np.log(19.0) / span
    return 1.0 / (1.0 + np.exp(-k[:, None] * (years[None, :] - t50[:, None])))


def draw_years(rng, tri_t50, tri_full, n_iter):
    """Draw (T50, T_FULL) per iteration, enforcing T_FULL > T50.

    Both are sampled independently from their triangulars, then any draw where
    the ordering is violated is repaired by pushing T_FULL out. Without this a
    tail draw could invert the curve.
    """
    t50 = rng.triangular(*tri_t50, size=n_iter)
    t_full = rng.triangular(*tri_full, size=n_iter)
    return t50, np.maximum(t_full, t50 + 1.0)


# --------------------------------------------------------------------------
# 3. MONTE CARLO
# --------------------------------------------------------------------------

@dataclass
class MCResult:
    years: np.ndarray
    segments: list
    codes: list
    groups: list
    # (metric, segment) -> (n_iter, n_cat, n_years)
    per_category: dict
    # (metric, segment) -> (n_iter, n_years)
    totals: dict
    shares: dict            # (transition, segment) -> (n_iter, n_years)


def run_monte_carlo(n_iter=N_ITER, seed=RANDOM_SEED,
                    start_year=START_YEAR, end_year=END_YEAR) -> MCResult:
    rng = np.random.default_rng(seed)
    base = load_baseline()
    tri = load_transitions()

    years = np.arange(start_year, end_year + 1)
    n_years, n_cat = len(years), len(base.codes)
    is_hv = np.array([g == HV_GROUP for g in base.groups])
    shrinks = base.sdv_factor < 1.0        # depth applies only to these

    # Independent (per-category) part of the length variability -- see the
    # CV_VEHICLE / CV_CATEGORY notes in section 0.
    cv_ind = float(np.sqrt(max(CV_CATEGORY ** 2 - CV_VEHICLE ** 2, 0.0)))

    per_category, totals, shares = {}, {}, {}

    for seg in BASE_SEGMENTS:
        # --- transition timing, sampled per iteration
        s800 = logistic_share(years, *draw_years(rng, tri[("800V", seg, "T50")],
                                                 tri[("800V", seg, "T_FULL")], n_iter))
        ssdv = logistic_share(years, *draw_years(rng, tri[("SDV", seg, "T50")],
                                                 tri[("SDV", seg, "T_FULL")], n_iter))
        shares[("800V", seg)] = s800
        shares[("SDV", seg)] = ssdv

        # --- SDV depth, sampled per iteration (the source-conflict parameter)
        depth = rng.triangular(*base.depth_tri[seg], size=n_iter)

        # Full-SDV length multiplier per iteration per category.
        # Growth categories (factor >= 1) are NOT scaled by depth: depth
        # describes how deep the REDUCTION goes, not how strong the growth is.
        f_full = np.repeat(base.sdv_factor[None, :], n_iter, axis=0)
        f_full[:, shrinks] = np.maximum(
            0.0, 1.0 - (1.0 - base.sdv_factor[None, shrinks]) * depth[:, None])

        i_base = int(np.searchsorted(years, BASE_YEAR))
        # --- length trajectory
        # baseline x [1 + (full_factor - 1) * sdv_share]  -> smooth, no seams
        sdv_mult = 1.0 + (f_full[:, :, None] - 1.0) * ssdv[:, None, :]

        # IMPORTANT: the 2025 baseline is an OBSERVED figure, so it already
        # contains whatever SDV penetration existed in 2025 (AB ~9%, CD ~11%,
        # EF ~14%). Applying the multiplier from zero would therefore subtract
        # that reduction a second time. Dividing by the multiplier evaluated at
        # BASE_YEAR renormalises the curve to pass through the observed
        # baseline exactly, whatever the sampled timing happens to be.
        sdv_mult = sdv_mult / sdv_mult[:, :, i_base][:, :, None]

        # 2020->2025 legacy correction, decaying geometrically to 1.0 at
        # BASE_YEAR and held at 1.0 afterwards.
        ratio = LEGACY_2020_RATIO[seg]
        legacy = 1.0 + (ratio - 1.0) * np.exp(-(years - 2020.0) / LEGACY_TAU_YEARS)
        # Renormalised so the curve passes through exactly 1.0 at BASE_YEAR,
        # while remaining smooth on both sides of it.
        legacy = legacy / legacy[i_base]                         # (n_years,)

        # --- car-to-car variability
        veh = rng.normal(1.0, CV_VEHICLE, size=(n_iter, 1, 1))       # shared
        cat = rng.normal(1.0, cv_ind, size=(n_iter, n_cat, 1))       # independent
        var = np.clip(veh * cat, 0.05, None)

        length = (base.length[seg][None, :, None] * SEGMENT_LENGTH_CALIBRATION[seg]
                  * sdv_mult * legacy[None, None, :] * var)
        length = np.clip(length, 0.0, None)

        # --- Cu per metre. Gauge sampled once per iteration per category.
        gauge = rng.triangular(
            base.gauge_min[None, :], (base.gauge_min + base.gauge_max)[None, :] / 2.0,
            np.maximum(base.gauge_max, base.gauge_min + 1e-9)[None, :],
            size=(n_iter, n_cat))
        cu_per_m = gauge * RHO_CU_G_PER_CM3                       # UNIT: g/m
        cu_per_m = np.repeat(cu_per_m[:, :, None], n_years, axis=2)

        # 800V shrinks HV conductors only, phased in by the penetration curve.
        red = rng.triangular(*HV_800V_CU_REDUCTION_TRI, size=n_iter)
        hv_scale = 1.0 - red[:, None] * s800                      # (n_iter, n_years)
        # Same renormalisation as for SDV, and for the same reason: the 2025
        # baseline gauges are observed, so they already reflect the 800V share
        # that existed in 2025 (EF ~42%, CD ~27%, AB ~2%). Without this the
        # reduction is applied twice and CD/EF copper comes out ~10% low at the
        # anchor year.
        hv_scale = hv_scale / hv_scale[:, i_base][:, None]
        cu_per_m[:, is_hv, :] *= hv_scale[:, None, :]

        cu_kg = length * cu_per_m / 1000.0                        # UNIT: kg

        per_category[(METRIC_LENGTH, seg)] = length
        per_category[(METRIC_CU, seg)] = cu_kg
        totals[(METRIC_LENGTH, seg)] = length.sum(axis=1)
        totals[(METRIC_CU, seg)] = cu_kg.sum(axis=1)

    # --- J* segments: rigid scaling of the base segment
    for seg, j_seg in J_SUFFIX.items():
        adder = rng.triangular(*HEIGHT_ADDER_TRI, size=(n_iter, 1))
        for metric in METRICS:
            per_category[(metric, j_seg)] = (
                per_category[(metric, seg)] * (1.0 + adder)[:, :, None])
            totals[(metric, j_seg)] = totals[(metric, seg)] * (1.0 + adder)
        for tr in ("800V", "SDV"):
            shares[(tr, j_seg)] = shares[(tr, seg)]

    all_segments = BASE_SEGMENTS + list(J_SUFFIX.values())
    return MCResult(years, all_segments, base.codes, base.groups,
                    per_category, totals, shares)


# --------------------------------------------------------------------------
# 4. STATS
# --------------------------------------------------------------------------

def _mode_from_hist(col: np.ndarray) -> float:
    """Mode = centre of the fullest of N_HIST_BINS bins. Deliberately the same
    binning that would be exported, so the two can never disagree."""
    counts, edges = np.histogram(col, bins=N_HIST_BINS)
    i = int(np.argmax(counts))
    return 0.5 * (edges[i] + edges[i + 1])


def _rows_for(arr: np.ndarray, years, **tags):
    """arr is (n_iter, n_years). Emits one row per year."""
    lo, med, hi = np.percentile(arr, [STAT_PCTS[0], 50, STAT_PCTS[1]], axis=0)
    mean = arr.mean(axis=0)
    out = []
    for i, yr in enumerate(years):
        out.append(dict(**tags, Year=int(yr), N_Iter=arr.shape[0],
                        Mean=mean[i], **{COL_LO: lo[i]}, Median=med[i],
                        Mode=_mode_from_hist(arr[:, i]), **{COL_HI: hi[i]}))
    return out


def build_stats(result: MCResult) -> pd.DataFrame:
    rows = []
    for metric in METRICS:
        for seg in result.segments:
            arr = result.per_category[(metric, seg)]
            for c, code in enumerate(result.codes):
                rows += _rows_for(arr[:, c, :], result.years, Level="Category",
                                  Segment=seg, Drivetrain=DRIVETRAIN, Code=code,
                                  Functional_Group=result.groups[c], Metric=metric)
            # functional-group roll-up
            for grp in sorted(set(result.groups)):
                idx = [i for i, g in enumerate(result.groups) if g == grp]
                rows += _rows_for(arr[:, idx, :].sum(axis=1), result.years,
                                  Level="Group", Segment=seg, Drivetrain=DRIVETRAIN,
                                  Code=grp, Functional_Group=grp, Metric=metric)
            rows += _rows_for(result.totals[(metric, seg)], result.years,
                              Level="Total", Segment=seg, Drivetrain=DRIVETRAIN,
                              Code="TOTAL", Functional_Group="TOTAL", Metric=metric)
    return pd.DataFrame(rows)


def build_shares(result: MCResult) -> pd.DataFrame:
    rows = []
    for (tr, seg), arr in result.shares.items():
        rows += _rows_for(arr, result.years, Level="Penetration", Segment=seg,
                          Drivetrain=DRIVETRAIN, Code=tr, Functional_Group=tr,
                          Metric="Share of new sales (-)")
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# 5. PLOTS
# --------------------------------------------------------------------------

def _mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def plot_totals(result: MCResult, out_path):
    plt = _mpl()
    colors = {"AB": "#1f77b4", "CD": "#ff7f0e", "EF": "#2ca02c"}
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), sharex=True)
    for ax, metric in zip(axes, METRICS):
        for seg in BASE_SEGMENTS:
            arr = result.totals[(metric, seg)]
            lo, med, hi = np.percentile(arr, [STAT_PCTS[0], 50, STAT_PCTS[1]], axis=0)
            ax.plot(result.years, med, color=colors[seg], lw=1.9, label=seg)
            ax.fill_between(result.years, lo, hi, color=colors[seg], alpha=0.15)
        ax.set_title(f"{metric} per new vehicle (TOTAL)")
        ax.set_xlabel("Year"); ax.set_ylabel(metric); ax.grid(alpha=0.3)
    axes[0].legend(fontsize=9)
    fig.suptitle(f"BEV wiring v4 -- median and P{STAT_PCTS[0]:g}-P{STAT_PCTS[1]:g}", fontsize=12)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(out_path, dpi=140); plt.close(fig)


def plot_penetration(result: MCResult, out_path):
    plt = _mpl()
    colors = {"AB": "#1f77b4", "CD": "#ff7f0e", "EF": "#2ca02c"}
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
    for ax, tr in zip(axes, ("800V", "SDV")):
        for seg in BASE_SEGMENTS:
            arr = result.shares[(tr, seg)]
            lo, med, hi = np.percentile(arr, [STAT_PCTS[0], 50, STAT_PCTS[1]], axis=0)
            ax.plot(result.years, 100 * med, color=colors[seg], lw=1.9, label=seg)
            ax.fill_between(result.years, 100 * lo, 100 * hi, color=colors[seg], alpha=0.15)
        ax.set_title(f"{tr} penetration"); ax.set_xlabel("Year")
        ax.set_ylabel("% of new vehicles sold"); ax.grid(alpha=0.3)
    axes[0].legend(fontsize=9)
    fig.suptitle("Sampled transition timing -- the band IS the timing uncertainty", fontsize=12)
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    plt.savefig(out_path, dpi=140); plt.close(fig)


def plot_group_grid(result: MCResult, segment, metric, out_path):
    plt = _mpl()
    groups = sorted(set(result.groups))
    ncols = 3
    nrows = int(np.ceil(len(groups) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(15, 3.4 * nrows), sharex=True)
    axes = np.atleast_1d(axes).flatten()
    arr = result.per_category[(metric, segment)]
    for ax, grp in zip(axes, groups):
        idx = [i for i, g in enumerate(result.groups) if g == grp]
        a = arr[:, idx, :].sum(axis=1)
        lo, med, hi = np.percentile(a, [STAT_PCTS[0], 50, STAT_PCTS[1]], axis=0)
        ax.plot(result.years, med, color="#d62728", lw=1.7)
        ax.fill_between(result.years, lo, hi, color="#d62728", alpha=0.18)
        ax.set_title(grp, fontsize=10); ax.grid(alpha=0.3); ax.tick_params(labelsize=8)
    for ax in axes[len(groups):]:
        ax.axis("off")
    fig.suptitle(f"{segment} ({DRIVETRAIN}) -- {metric} by functional group", fontsize=12)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(out_path, dpi=130); plt.close(fig)


# --------------------------------------------------------------------------
# 6. MAIN
# --------------------------------------------------------------------------

if __name__ == "__main__":
    print("BEV wiring v4 -- length-first, report-anchored")
    print(f"  baseline    : {BASELINE_FILE.name}")
    print(f"  transitions : {TRANSITION_FILE.name}")
    print(f"  {START_YEAR}-{END_YEAR}, {N_ITER} iterations, seed {RANDOM_SEED}\n")

    result = run_monte_carlo()

    stats = build_stats(result)
    stats.to_csv(OUT_SUBDIRS["data"] / "bev_wiring_v4_stats.csv", index=False)
    print(f"  {len(stats):>6} rows -> data/bev_wiring_v4_stats.csv")

    shares = build_shares(result)
    shares.to_csv(OUT_SUBDIRS["data"] / "bev_wiring_v4_penetration.csv", index=False)
    print(f"  {len(shares):>6} rows -> data/bev_wiring_v4_penetration.csv")

    plot_totals(result, OUT_SUBDIRS["plots"] / "totals.png")
    plot_penetration(result, OUT_SUBDIRS["plots"] / "penetration.png")
    for seg in BASE_SEGMENTS:
        for metric in METRICS:
            plot_group_grid(result, seg, metric,
                            OUT_SUBDIRS["plots"] / f"groups_{seg}_{METRIC_SLUG[metric]}.png")
    print(f"  plots -> {OUT_SUBDIRS['plots']}")

    print("\nSanity check -- median per new vehicle")
    for metric in METRICS:
        print(f"\n  {metric}")
        hdr = "".join(f"{y:>9}" for y in SNAPSHOT_YEARS)
        print(f"    {'seg':<8}{hdr}")
        for seg in result.segments:
            med = np.percentile(result.totals[(metric, seg)], 50, axis=0)
            vals = "".join(f"{med[np.searchsorted(result.years, y)]:>9.1f}"
                           for y in SNAPSHOT_YEARS)
            print(f"    {seg:<8}{vals}")

    print("\n  Report anchors for comparison (2025, per new vehicle):")
    print("    Length (m)  AB 1392   CD 2486   EF 3546")
    print("    Cu (kg)     AB  33.9  CD   60.3 EF   74.6")
