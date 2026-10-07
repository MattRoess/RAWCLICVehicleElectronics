#!/usr/bin/env python3
"""
ElectricMotorElementMC.py
────
Monte Carlo elemental analysis for four material streams produced by
ElectricMotorMC.py:

**Copyright notice:** Copyright © 2025 & 2026 Empa, Matthias Roesslein

  1. COPPER          — grades ETP, OF, OFE (equal weight 1/3, all segments)
  2. ELECTRICAL STEEL — grades M19, M27, M36, M43, M47
       Fe is "balance" → Fe = 1 − Σ(Si + C + Mn + Al + P + S)
       Grade weights per segment group:
         AB  → 1/3 M19, 1/3 M27, 1/3 M43
         CD  → 2/5 M19, 2/5 M27, 1/5 M43
         EF  → 1/2 M19, 1/2 M27
  3. NdFeB (permanent magnets)
       Grade weights per motor type AND segment group:
         SmallStepperMotors:
           AB  → 1/3 N35, 1/3 N42, 1/3 N48
           CD  → 1/2 N35, 1/2 N42
           EF  → 1/2 N42, 1/2 N48
         MediumStepperMotors / MediumDCMotors_metal / MediumDCMotors_plastic:
           AB  → 80% {N40,N42,N45,N48}, 20% {N35SH,N42SH,N45SH,N48SH}
           CD  → 30% {N40,N42,N45,N48}, 30% {N35SH,N42SH,N45SH,N48SH},
                 30% {N40UH,N42UH,N45UH}
           EF  → 30% {N35SH,N42SH,N45SH,N48SH}, 30% {N40UH,N42UH,N45UH},
                 30% {N40EH,N42EH}
  4. CAST FE STEEL   — grade DC01 only
       Fe is "balance" → Fe = 1 − Σ(C + Mn + P + S)
       Elements with max=0 are excluded entirely:
         Si, Cr, Ni, Al  (not sampled, not in output)

Grand totals per segment group (AB / CD / EF) are computed via MC
(sample-wise sum across all motor types) and appended to the summary CSV
with full distribution figures and histogram CSVs.

Output folders (siblings of this script):
  CopperElemental/
  ElectricalSteelElemental/
  NdFeBElemental/
  CastFeSteelElemental/
    each with: summary_csv/ | histograms_csv/ | distribution_figures/ | sensitivity_figures/
"""

from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde, spearmanr


# ────────────────────────────────────────────────────────────────────────────
# PATHS
# ────────────────────────────────────────────────────────────────────────────
HERE         = Path(__file__).resolve().parent
DATA_DIR     = (HERE.parent / "Data").resolve()
XLSX_FILE    = DATA_DIR / "10_MaterialElementDefinitions.xlsx"

# Folder produced by ElectricMotorMC.py that contains the material histogram CSVs
MAT_HIST_DIR = HERE.parent / "06_ElectricMotorMC" / "materials_histograms_csv"

# Output roots
CU_ROOT       = HERE / "CopperElemental"
ESTL_ROOT     = HERE / "ElectricalSteelElemental"
# NAMED FOR THE ROLE, NOT THE CHEMISTRY. This is "the magnet stream", whatever
# magnet material is currently modelled. Naming it after the material -- it was
# NdFeBElemental until 2026-08-13 -- orphans the old folder the moment the
# chemistry changes, and the orphan then sits in the tree holding superseded
# numbers that a glob can still pick up. The Stream column inside the data
# records the actual chemistry; the folder does not need to.
MAGNET_ROOT   = HERE / "MagnetElemental"
CFSTEEL_ROOT  = HERE / "CastFeSteelElemental"

for root in [CU_ROOT, ESTL_ROOT, MAGNET_ROOT, CFSTEEL_ROOT]:
    for sub in ["summary_csv", "histograms_csv", "distribution_figures", "sensitivity_figures"]:
        (root / sub).mkdir(parents=True, exist_ok=True)


# ────────────────────────────────────────────────────────────────────────────
# SETTINGS
# ────────────────────────────────────────────────────────────────────────────
# [CHANGED] 100_000 -> 200_000, the full length of the upstream sample files.
#
# `load_material_draws` takes the FIRST N_SAMPLES rows of ElectricMotorMC's own
# per-draw material masses, and those files hold 200,000. At 100,000 half of every
# file went unused, and -- more importantly -- the draws could not be paired with the
# fleet model or the joint composition run, both of which use 200,000. Pairing draw i
# with draw i is the whole basis of carrying uncertainty between models.
#
# This is what that function's docstring already recommended: "Set N_SAMPLES to the
# full file length to use every draw and resample nothing at all."
N_SAMPLES = 200_000

# [NEW] Where the RAW per-draw element masses go, for the stock-and-flow model.
#
# WHY. This model already builds `(N_SAMPLES, n_elements)` arrays per segment and
# material stream; it then reduces them to histograms and summary CSVs and throws the
# draws away. Anything downstream could therefore only resample a binned
# approximation. The stock-and-flow model (RAWCLICStockAndFlow, stage 04_02)
# multiplies these against its own per-draw vehicle counts, one draw against one
# draw, which needs the real values.
#
# WHAT IS STORED, AND WHY IT IS SMALL. Element FRACTIONS of the stream mass, not
# absolute masses, and with no year axis. This study freezes composition at its 2025
# value by decision -- what a motor is MADE OF is not forecastable -- so the fraction
# has no time dimension, and the consumer recovers a year-resolved element mass as
#     element_mass[draw, year] = stream_mass[draw, year] x fraction[draw, element]
# Storing element x year x draw arrays instead would cost about 9 GB; fractions cost
# roughly 180 MB for the whole study.
ELEM_DRAWS_DIR = HERE.parent / "Composition" / "element_draws"
RNG_SEED  = 42
HIST_BINS = 100

# ── Copper ──────────────────────────────────────────────────────────────────
CU_GRADES  = ["ETP", "OF", "OFE"]
CU_WEIGHTS = {g: 1 / 3 for g in CU_GRADES}

# The copper sheet states these impurities in ppm, so these are the SHEET's column
# names -- `load_grades` divides them by 1e6 on read and what comes out is an
# ordinary mass fraction like every other element.
#
# THE SUFFIX MUST NOT SURVIVE INTO THE ELEMENT NAME. It says how the sheet writes
# the number, not what the element is: `S_ppm` is sulfur. It used to be carried
# through as the element name, and the effect was silent -- the combined motor
# table accumulates streams BY ELEMENT NAME, so the electrical steel's `S` and the
# copper's `S_ppm` never collided and never merged. Sulfur was reported as two
# elements, neither of them its mass, and the same for O, Fe, Mn, P, Ag, Pb, Sn,
# Zn, Ni and As. Bi, Cd, Sb, Se and Te occur only here and were reported under a
# name that reads as a unit.
#
# So the element name is derived once, here, and the accumulator does the rest --
# exactly as it already does for the iron shared by four streams.
PPM_COLS = [
    "O_ppm", "Ag_ppm", "Pb_ppm", "Bi_ppm", "Fe_ppm",
    "Sb_ppm", "As_ppm", "Sn_ppm", "Zn_ppm", "Ni_ppm",
    "S_ppm",  "P_ppm",  "Se_ppm", "Te_ppm", "Cd_ppm", "Mn_ppm",
]

# sheet column -> element. Cu is in RATIO_COLS and needs no mapping.
PPM_ELEMENT = {c: c[: -len("_ppm")] for c in PPM_COLS}

# The elements the copper stream resolves, in output order: copper, then its
# impurities under their own names.
CU_ELEMENTS = ["Cu", *(PPM_ELEMENT[c] for c in PPM_COLS)]

RATIO_COLS   = ["Cu"]
COPPER_COLOR = "#B87333"

# ── Electrical Steel ────────────────────────────────────────────────────────
ESTL_ELEMENTS = ["Si", "C", "Mn", "Al", "P", "S"]   # Fe is balance

ESTL_SEGMENT_WEIGHTS: Dict[str, Dict[str, float]] = {
    "AB": {"M19": 1/3, "M27": 1/3, "M43": 1/3},
    "CD": {"M19": 2/5, "M27": 2/5, "M43": 1/5},
    "EF": {"M19": 1/2, "M27": 1/2},
}
ESTL_COLOR = "#607D8B"

# ── NdFeB ────────────────────────────────────────────────────────────────────
NDFEB_ELEMENTS = ["Nd", "Fe", "B", "Dy", "Tb", "Pr", "Co", "Al", "Cu", "Nb", "Ga"]

# How far the DRAWN Fe balance (1 - sum of the other ten) may sit outside the
# Fe range the NdFeB sheet itself reports, before it is worth warning about.
# UNIT: mass fraction. The two are independent statements about the same alloy,
# so a small gap is ordinary rounding in the published grade table; a large one
# means the sheet's rows contradict each other and should be re-read.
NDFEB_FE_TOL = 0.02

# ---------------------------------------------------------------------------
# PERMANENT MAGNETS ARE FERRITE, NOT NdFeB          decided 2026-08-13
#
# The magnet mass in every auxiliary motor is now split with a STRONTIUM FERRITE
# composition. It used to be split with NdFeB, which put 0.37-1.66 kg of
# neodymium and up to 0.38 kg of dysprosium into the auxiliary motors of a single
# car -- more rare earth than many traction motors contain.
#
# WHY. Auxiliary motors -- window lifters, wipers, blowers, seat adjusters -- use
# ferrite. NdFeB is a traction-motor and high-value-actuator material. The
# project's own source already said so and was not being read: the `notes` column
# of 05_VehicleElectricMotorsWeight.xlsx describes the DC motor magnets as
# "Strontium/barium ferrite, Sintered NdFeB", while its `material` column says
# NdFeB and the element model therefore split 100% of the mass as NdFeB.
#
# The user's own independent investigation (2026-08-13) went further than the
# notes: at most a few of the smallest steppers, where there is no room for a
# ferrite magnet of sufficient strength, might use NdFeB, and those are not
# separately recycled. Too small to model -> ALL magnet mass is ferrite.
#
# BARIUM IS EXCLUDED by the same decision. The sheet offers Barium Ferrite (Y30);
# it is not used. Strontium ferrite dominates automotive production.
#
# WHAT DID NOT CHANGE. The magnet MASS. It comes from 05_ as a fraction of motor
# mass and is unchanged, so this is a composition switch, not a mass switch.
#
# KNOWN BIAS, MEASURED AGAINST THE SOURCE 2026-08-31, LEFT IN DELIBERATELY.
# Ferrite is roughly an order of magnitude less energy-dense than sintered NdFeB,
# so a ferrite motor needs MORE magnet for the same torque. Whether 05_'s mass
# fractions already reflect that depends on which magnet they were measured on,
# and its `notes` column answers that differently for the two motor families:
#
#   MediumDCMotors_plastic  "Strontium/barium ferrite, Sintered NdFeB (N-series)"
#   MediumDCMotors_metal     same -- FERRITE IS NAMED FIRST
#       -> plausibly ferrite-based already. No bias expected. These are the
#          window lifters, wipers and blowers, i.e. most of the auxiliary mass.
#
#   SmallStepperMotors      "Sintered NdFeB (N42, N48SH, N45UH) & retentive Steel"
#   MediumStepperMotors     "High-coercivity sintered NdFeB (N42EH, ...)"
#       -> NdFeB ONLY, no ferrite mentioned. Their fractions (0.05/0.075/0.10 and
#          0.10/0.125/0.15) were measured on NdFeB magnets, and this model splits
#          that mass as ferrite. THE STEPPER MAGNET MASS IS THEREFORE LOW.
#
# The direction is known, the size is not. Correcting it needs a source for
# ferrite magnet mass in small auxiliary steppers; picking a multiplier from the
# energy-density ratio would be inventing a number, since magnet mass in a real
# motor does not scale with that ratio. Decided with the user 2026-08-31: leave
# the values, record the bias. Note also that the stepper magnet row is "NdFeB &
# retentive Steel", so it is not purely magnet material to begin with.
#
# LABEL STILL SAYS NdFeB UPSTREAM. 05_'s `material` column, and therefore every
# ElectricMotorMC output column and histogram filename, still calls this stream
# NdFeB. Only the composition applied here has changed. See the STREAMS table.
# ---------------------------------------------------------------------------

# Elements resolved for strontium ferrite. Ba is deliberately absent -- see above.
FERRITE_ELEMENTS = ["Sr", "Fe", "O"]

# Grades used, and their weights. Equal thirds by decision: the three Y-grades
# differ in magnetic performance, not meaningfully in elemental composition, and
# no source gives their production split. UNIT: none, weights are normalised.
FERRITE_GRADES = {
    "Strontium Ferrite (Y30)": 1.0,
    "Strontium Ferrite (Y35)": 1.0,
    "Strontium Ferrite (Y40)": 1.0,
}

FERRITE_SHEET = "PermanentMagnetFerrit"
FERRITE_COLOR = "#4C6E8A"

# Same role as NDFEB_FE_TOL, for the ferrite balance. UNIT: mass fraction.
# Wider because 10_'s ferrite rows are mutually inconsistent at their edges: Sr
# 0.15-0.20 plus O 0.35-0.40 forces Fe into 0.40-0.50, while the sheet's own Fe
# row stops at 0.45. See the stoichiometry note in load_ferrite_grades.
FERRITE_FE_TOL = 0.06
NDFEB_COLOR    = "#8B4513"

# Motor type tokens as they appear in histogram CSV filenames
_SMALL              = "SmallStepperMotors"
_MEDIUM_STEPPER     = "MediumStepperMotors"
_MEDIUM_DC_METAL    = "MediumDCMotors_metal"
_MEDIUM_DC_PLASTIC  = "MediumDCMotors_plastic"

NDFEB_GRADE_WEIGHTS: Dict[str, Dict[str, Dict[str, float]]] = {
    _SMALL: {
        "AB": {"N35": 1/3, "N42": 1/3, "N48": 1/3},
        "CD": {"N35": 1/2, "N42": 1/2},
        "EF": {"N42": 1/2, "N48": 1/2},
    },
    _MEDIUM_STEPPER: {
        # AB: 80% standard {N40,N42,N45,N48} + 20% SH {N35SH,N42SH,N45SH,N48SH}
        "AB": {
            "N40": 0.20, "N42": 0.20, "N45": 0.20, "N48": 0.20,
            "N35SH": 0.05, "N42SH": 0.05, "N45SH": 0.05, "N48SH": 0.05,
        },
        # CD: 30% standard + 30% SH + 30% UH  (remaining 10% → normalise)
        "CD": {
            "N40": 0.075, "N42": 0.075, "N45": 0.075, "N48": 0.075,
            "N35SH": 0.075, "N42SH": 0.075, "N45SH": 0.075, "N48SH": 0.075,
            "N40UH": 0.10,  "N42UH": 0.10,  "N45UH": 0.10,
        },
        # EF: 30% SH + 30% UH + 30% EH  (remaining 10% → normalise)
        "EF": {
            "N35SH": 0.075, "N42SH": 0.075, "N45SH": 0.075, "N48SH": 0.075,
            "N40UH": 0.10,  "N42UH": 0.10,  "N45UH": 0.10,
            "N40EH": 0.15,  "N42EH": 0.15,
        },
    },
}
# DC motor variants share the same grade weights as MediumStepperMotors
NDFEB_GRADE_WEIGHTS[_MEDIUM_DC_METAL]   = NDFEB_GRADE_WEIGHTS[_MEDIUM_STEPPER]
NDFEB_GRADE_WEIGHTS[_MEDIUM_DC_PLASTIC] = NDFEB_GRADE_WEIGHTS[_MEDIUM_STEPPER]

# ── Cast Fe Steel ────────────────────────────────────────────────────────────
# Only DC01 grade from the CastFeSteel sheet; Fe is the balance element.
# All non-Fe elements in the sheet (excluding Fe which is balance):
CFSTEEL_ALL_ELEMENTS = ["C", "Mn", "P", "S", "Si", "Cr", "Ni", "Al"]
# Elements whose max value is 0 for DC01 are excluded entirely
# (not sampled, not included in composition, not in any output).
# Excluded: Si, Cr, Ni, Al  (all have max=0 for DC01)
_CFSTEEL_EXCLUDED    = {"Si", "Cr", "Ni", "Al"}
CFSTEEL_ELEMENTS     = [e for e in CFSTEEL_ALL_ELEMENTS if e not in _CFSTEEL_EXCLUDED]
CFSTEEL_COLOR        = "#708090"

# Map lowercase motor-type substrings (as they appear in filenames) to keys
# Order matters: more specific tokens first to avoid partial matches
NDFEB_MOTOR_MAP: Dict[str, str] = {
    "mediumdcmotors_metal":   _MEDIUM_DC_METAL,
    "mediumdcmotors_plastic": _MEDIUM_DC_PLASTIC,
    "mediumsteppermotors":    _MEDIUM_STEPPER,
    "smallsteppermotors":     _SMALL,
}


# ────────────────────────────────────────────────────────────────────────────
# SHARED HELPERS
# ────────────────────────────────────────────────────────────────────────────
def uniform(rng: np.random.Generator, lo: float, hi: float, n: int) -> np.ndarray:
    if lo == hi:
        return np.full(n, lo, dtype=float)
    return rng.uniform(lo, hi, size=n)


def export_histogram_csv(data: np.ndarray, path: Path, bins: int = HIST_BINS) -> None:
    counts, edges = np.histogram(data, bins=bins)
    density, _    = np.histogram(data, bins=edges, density=True)
    pd.DataFrame({
        "bin_left":  edges[:-1],
        "bin_right": edges[1:],
        "bin_mid":   (edges[:-1] + edges[1:]) / 2,
        "count":     counts,
        "density":   density,
    }).to_csv(path, index=False)


def add_kde(ax, x: np.ndarray, color: str) -> None:
    if np.std(x) < 1e-15:
        return
    kde  = gaussian_kde(x)
    grid = np.linspace(x.min(), x.max(), 500)
    ax.plot(grid, kde(grid), color=color, linewidth=2)


# --------------------------------------------------------------------------
# MATERIAL MASS INPUT
#
# This model splits a MATERIAL mass into ELEMENTS. The material mass comes from
# ElectricMotorMC, and there are two ways to get it:
#
#   the draws      ElectricMotorMC/materials_samples_csv/*.npy
#                  its actual 200,000 per-draw material masses
#   a histogram    ElectricMotorMC/materials_histograms_csv/*.csv
#                  those same draws binned into 50 bins and exported
#
# Until 2026-08-13 this model read the HISTOGRAM and resampled from it. That
# discards information that exists on disk, and it showed: the reconstructed
# motor composition missed ElectricMotorMC's own mass by up to 0.94%.
#
# WORSE, IT BROKE THE PAIRING BETWEEN MATERIALS. Each stream was resampled from
# its own histogram independently, so "draw i" of copper and "draw i" of steel
# came from two unrelated motors. A heavy motor is heavy in every material at
# once; independent resampling destroys that, and every grand total formed by
# summing streams inherited the error.
#
# Reading the .npy fixes both: row i is ONE simulated motor, and its copper,
# electrical steel, NdFeB and cast steel masses all belong to it.
# --------------------------------------------------------------------------

MAT_SAMPLES_DIR = HERE.parent / "06_ElectricMotorMC" / "materials_samples_csv"

# Which column of ElectricMotorMC's per-draw sample file each stream reads.
# The stream keys are this model's internal names; the column names are
# ElectricMotorMC's material names, listed in the companion .json.
# NOTE cfsteel -> "Steel": ElectricMotorMC calls it Steel, this model calls the
# same material Cast Fe Steel. Same quantity, two names.
# (the mass column now lives in each Stream entry as `mass_col`)
# Materials ElectricMotorMC puts in a motor that this model does not break down
# into elements. Aluminium IS an element and is folded into `Al`; plastic is not
# resolved further and is carried under its own name.
# UNIT: none, material names as spelled in the materials_samples .json.
UNRESOLVED_MATERIAL_COL = {
    "Al":      "mass_kg__Aluminum",
    "Plastic": "mass_kg__Plastic",
}

# How large the UNSPECIFIED remainder of a motor may be before it is treated as a
# defect rather than as trace chemistry. UNIT: fraction of motor mass.
#
# There IS a real remainder, and it is not float noise. The copper stream's named
# elements sum to 99.9916% of that stream's mass -- Cu at ~99.97% plus a list of
# impurities in ppm, whose specification does not quite close. The other three
# streams close to ~3e-8, which is float32 storage precision. Measured at the
# motor level the shortfall is ~5e-5 of motor mass.
#
# So this is NOT a tolerance that absorbs the residual. The residual is carried as
# an explicit `Unspecified` entry below, and the fractions sum to exactly 1 by
# construction. This constant only bounds how big that entry may get: 1e-3 is 20x
# the measured value, and still 30x below the smallest resolved material
# (aluminium in AB, 3.1% of the motor), so a whole missing stream cannot hide
# inside it.
#
# An earlier version of this constant was set to 1e-9 on the stated grounds that
# "nothing but float64 rounding sits between the two sides". That was asserted,
# not measured, and it was wrong -- the check fired on 199,989 of 200,000 draws.
# The number above comes from the measurement that should have been done first.
MOTOR_FRAC_TOL = 1e-3


def motor_mass_and_unresolved(seg: str, n: int):
    """Full per-draw motor mass for one segment, and the two unresolved materials.

    Returns:
        (total_mass_kg, aluminium_kg, plastic_kg), each (n,) in kg, summed over
        every motor-type case belonging to this segment.

    WHY THIS EXISTS. The element streams alone do not add up to a motor -- see the
    long note in process_grand_totals. The fractions written there must divide by
    the WHOLE motor, which only ElectricMotorMC knows, so it is read here from the
    same per-draw files the streams themselves are read from.

    The first n rows are taken, matching load_material_draws exactly, so row i is
    the same simulated motor on both sides. Taking a different slice, or a random
    one, would silently break the pairing that this whole module was rewritten in
    August 2026 to preserve.

    A motor-type case that has no plastic (most of them) simply contributes zero,
    rather than being skipped -- a missing column means "none of this material",
    not "unknown".
    """
    tot = al = pl = None
    for p in sorted(MAT_SAMPLES_DIR.glob(f"materials_samples_{seg}_*.npy")):
        js = p.with_suffix(".json")
        if not js.exists():
            raise FileNotFoundError(f"{p.name} has no companion .json naming its columns")
        cols = json.load(open(js))["columns"]
        a = np.load(p, mmap_mode="r")
        if a.shape[0] < n:
            raise ValueError(
                f"{p.name} holds {a.shape[0]:,} draws but {n:,} are needed. Re-run "
                f"ElectricMotorMC.py with at least N_SAMPLES={n:,}, or lower "
                f"N_SAMPLES here -- do NOT resample, it breaks the row pairing.")

        def col(name: str) -> np.ndarray:
            if name not in cols:
                return np.zeros(n, dtype=float)
            return np.asarray(a[:n, cols.index(name)], dtype=float)

        t = col("total_mass_kg")
        if not np.all(np.isfinite(t)):
            raise ValueError(f"{p.name} has non-finite total_mass_kg")
        tot = t if tot is None else tot + t
        x = col(UNRESOLVED_MATERIAL_COL["Al"]);      al = x if al is None else al + x
        y = col(UNRESOLVED_MATERIAL_COL["Plastic"]); pl = y if pl is None else pl + y

    if tot is None:
        raise FileNotFoundError(
            f"no materials_samples_{seg}_*.npy in {MAT_SAMPLES_DIR} -- "
            f"run ElectricMotorMC.py first")
    return tot, al, pl


def load_material_draws(stem: str, stream: str, n: int) -> np.ndarray:
    """ElectricMotorMC's OWN per-draw material mass, in kg. (n,)

    Args:
        stem:   the histogram stem this case was discovered under, e.g.
                "hist_materialmass_CD_MediumDCMotors_metal_Steel". Only used to
                recover the case; the histogram itself is not read.
        stream: a key of STREAMS.
        n:      draws wanted. UNIT: draws.

    Returns:
        (n,) material mass. UNIT: kg.

    THE FIRST n ROWS, NOT A RANDOM SUBSET. The draws are i.i.d., so the first n
    are a valid sample -- and taking the SAME row indices for every stream is
    what keeps a motor's copper and its steel belonging to the same motor. A
    random subset per stream would silently reintroduce the pairing bug this
    function exists to fix. Set N_SAMPLES to the full file length to use every
    draw and resample nothing at all.
    """
    if stream not in STREAMS:
        raise KeyError(f"no stream {stream!r} in STREAMS")

    # "hist_materialmass_<CASE>_<Material>" -> "<CASE>"
    parts = stem.split("_")
    case = "_".join(parts[2:-1])
    npy = MAT_SAMPLES_DIR / f"materials_samples_{case}.npy"
    js = npy.with_suffix(".json")
    if not npy.exists() or not js.exists():
        raise FileNotFoundError(
            f"per-draw material samples not found for case {case!r}:\n"
            f"  {npy}\n"
            f"Run ElectricMotorMC.py first -- it writes these. This model no "
            f"longer resamples from the exported histograms, because that loses "
            f"the pairing between materials of the same motor.")

    cols = json.load(open(js))["columns"]
    want = STREAMS[stream].mass_col
    if want not in cols:
        raise KeyError(f"{npy.name} has no column {want!r}; it has {cols}")

    a = np.load(npy, mmap_mode="r")
    if a.shape[0] < n:
        raise ValueError(
            f"{npy.name} holds {a.shape[0]:,} draws but N_SAMPLES is {n:,}. "
            f"Lower N_SAMPLES or re-run ElectricMotorMC.py with more draws.")
    return np.asarray(a[:n, cols.index(want)], dtype=float)


def sample_from_histogram(hist_csv: Path, rng: np.random.Generator, n: int) -> np.ndarray:
    """Inverse-CDF sampling from a histogram CSV.

    NO LONGER USED FOR MATERIAL MASS -- see load_material_draws above and the
    note on why resampling a histogram was wrong here. Kept because it is a
    correct implementation of what it says, and because reading a histogram is
    still the only option for any input whose draws were never exported.
    """
    df        = pd.read_csv(hist_csv)
    bin_left  = df["bin_left"].to_numpy(float)
    bin_right = df["bin_right"].to_numpy(float)
    density   = df["density"].to_numpy(float)
    widths    = bin_right - bin_left
    probs     = np.maximum(density * widths, 0.0)
    total     = probs.sum()
    if total == 0:
        raise ValueError(f"All-zero density in {hist_csv}")
    probs    /= total
    bin_idx   = rng.choice(len(probs), size=n, p=probs)
    u         = rng.uniform(0, 1, size=n)
    return bin_left[bin_idx] + u * widths[bin_idx]


def save_distribution_figure(
    label: str,
    elements: List[str],
    elem_mass_kg: np.ndarray,
    total_mass_kg: np.ndarray,
    color: str,
    title_prefix: str,
    out_dir: Path,
    file_prefix: str,
) -> None:
    n_elem = len(elements)
    ncols  = 4
    nrows  = int(np.ceil((n_elem + 1) / ncols))

    fig, axes = plt.subplots(nrows, ncols, figsize=(18, 4.2 * nrows))
    axes = np.atleast_1d(axes).reshape(nrows, ncols)
    fig.suptitle(f"{title_prefix} Elemental Mass Distributions — {label}",
                 fontsize=15, fontweight="bold")

    ax0 = axes[0, 0]
    ax0.hist(total_mass_kg, bins=80, density=True, alpha=0.35, color=color, edgecolor="none")
    add_kde(ax0, total_mass_kg, color)
    for p, ls in [(0.05, "--"), (0.50, "-"), (0.95, "--")]:
        ax0.axvline(np.quantile(total_mass_kg, p), color="black", linestyle=ls, alpha=0.7)
    ax0.axvline(np.mean(total_mass_kg), color="red", linestyle=":", linewidth=2)
    ax0.set_title(f"Total {title_prefix} Mass", fontsize=11, fontweight="bold")
    ax0.set_xlabel("[kg]"); ax0.set_ylabel("Density")

    for idx, elem in enumerate(elements):
        panel = idx + 1
        ax    = axes[panel // ncols, panel % ncols]
        x     = elem_mass_kg[:, idx]
        ax.hist(x, bins=80, density=True, alpha=0.35, color=color, edgecolor="none")
        add_kde(ax, x, color)
        for p, ls in [(0.05, "--"), (0.50, "-"), (0.95, "--")]:
            ax.axvline(np.quantile(x, p), color="black", linestyle=ls, alpha=0.7)
        ax.axvline(np.mean(x), color="red", linestyle=":", linewidth=2)
        display = elem.replace("_ppm", " [ppm→kg]")
        ax.set_title(display, fontsize=10, fontweight="bold")
        ax.set_xlabel("[kg]"); ax.set_ylabel("Density")

    for p in range(n_elem + 1, nrows * ncols):
        axes[p // ncols, p % ncols].axis("off")

    fig.tight_layout(rect=[0, 0.03, 1, 0.94])
    safe = label.replace(" ", "_").replace("/", "_")
    fig.savefig(out_dir / f"{file_prefix}_distribution_{safe}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def save_sensitivity_heatmap(
    label: str,
    elements: List[str],
    elem_mass_kg: np.ndarray,
    total_mass_kg: np.ndarray,
    mean_fractions: np.ndarray,
    title_prefix: str,
    out_dir: Path,
    file_prefix: str,
) -> None:
    n_elem  = len(elements)
    drivers = [f"{title_prefix} Mass [kg]", "Element Fraction"]
    H       = np.zeros((2, n_elem), dtype=float)
    for j in range(n_elem):
        y       = elem_mass_kg[:, j]
        H[0, j] = abs(spearmanr(total_mass_kg,        y).statistic)
        H[1, j] = abs(spearmanr(mean_fractions[:, j],  y).statistic)

    order        = np.argsort(elem_mass_kg.mean(axis=0))[::-1]
    H_sorted     = H[:, order]
    elems_sorted = [elements[i].replace("_ppm", "") for i in order]

    fig, ax = plt.subplots(figsize=(max(8, 1.2 * n_elem), 3.2))
    im = ax.imshow(H_sorted, vmin=0, vmax=1, aspect="auto", cmap="YlOrRd")
    ax.set_yticks(np.arange(2)); ax.set_yticklabels(drivers, fontsize=11)
    ax.set_xticks(np.arange(n_elem))
    ax.set_xticklabels(elems_sorted, rotation=45, ha="right", fontsize=9)
    ax.set_title(f"{title_prefix} Elemental Sensitivity (|Spearman ρ|) — {label}",
                 fontsize=12, fontweight="bold")
    for r in range(H_sorted.shape[0]):
        for c in range(H_sorted.shape[1]):
            ax.text(c, r, f"{H_sorted[r,c]:.2f}", ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04).set_label("|Spearman ρ|")
    fig.tight_layout()
    safe = label.replace(" ", "_").replace("/", "_")
    fig.savefig(out_dir / f"{file_prefix}_sensitivity_{safe}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def build_summary_row(
    stream: str, label: str, elem: str,
    x: np.ndarray, mean_frac: float,
) -> dict:
    return {
        "Stream":        stream,
        "Case":          label,
        "Element":       elem,
        "Mean_mass_kg":  float(np.mean(x)),
        "Std_mass_kg":   float(np.std(x)),
        "P05_mass_kg":   float(np.quantile(x, 0.05)),
        "P50_mass_kg":   float(np.quantile(x, 0.50)),
        "P95_mass_kg":   float(np.quantile(x, 0.95)),
        "Mean_fraction": float(mean_frac),
    }


# ────────────────────────────────────────────────────────────────────────────
# FILENAME PARSING HELPERS
# ────────────────────────────────────────────────────────────────────────────
def parse_csv_filename(stem: str) -> Tuple[str | None, str | None]:
    """
    Parse a histogram CSV stem of the form:
        hist_materialmass_<SEG>_<MotorType>[_ExtraTokens...]_<Material>

    Returns (segment, motor_token_lower) where motor_token_lower is the
    lowercase motor-type string as it appears in NDFEB_MOTOR_MAP.

    Strategy:
      - Segment is the first token after 'hist_materialmass_' that is AB/CD/EF.
      - Motor type is found by substring-searching the stem (lowercase) for
        known motor tokens, longest match first (most specific first).
    """
    lower = stem.lower()

    # Extract segment
    parts   = stem.split("_")
    segment = None
    for p in parts:
        if p.upper() in ("AB", "CD", "EF"):
            segment = p.upper()
            break

    # Extract motor type by substring search (most-specific first)
    motor_key = None
    for token_lower in NDFEB_MOTOR_MAP:   # dict is ordered, specific first
        if token_lower in lower:
            motor_key = token_lower
            break

    return segment, motor_key


def build_label(stem: str, stream: str) -> str:
    """
    Build a clean human-readable label from the CSV stem.
    For NdFeB: <SEG>_<MotorType>  (drops extra tokens like 'Ferrite')
    For copper/esteel: everything between 'hist_materialmass_' and the last token.
    """
    parts = stem.split("_")
    # parts[0]="hist", parts[1]="materialmass", parts[-1]=material name
    inner = parts[2:-1]

    if stream == "magnet":
        seg, motor_token = parse_csv_filename(stem)
        if seg and motor_token:
            # Use the canonical motor key name (not the lowercase token)
            motor_name = NDFEB_MOTOR_MAP[motor_token]
            return f"{seg}_{motor_name}"
        # fallback
        return "_".join(inner)
    else:
        return "_".join(inner)


# ===========================================================================
# THE STREAM TABLE
#
# One row per material stream. Everything that differs between copper,
# electrical steel, the magnets and the housing steel lives HERE, as data --
# which sheet of 10_ to read, which elements, which grades and their weights,
# whether an element is the balance, and which mass column of ElectricMotorMC's
# per-draw file the stream is splitting.
#
# WHY THIS EXISTS. Until 2026-08-13 each material had its own loader function,
# its own sampler function, and a branch in two hardcoded `if stream == ...`
# config blocks. Switching the magnets from NdFeB to strontium ferrite -- a pure
# COMPOSITION change, which is data -- therefore required five code edits and
# orphaned an output folder. The project rule it broke:
#
#     A change of composition must not change the structure or the run design.
#
# With this table, changing a material is one entry. Adding one is one entry.
# Nothing else in the file needs to know a material exists.
#
# ADDING OR CHANGING A MATERIAL
#   1. put its grades in Data/10_MaterialElementDefinitions.xlsx
#   2. add or edit its Stream entry below
#   3. re-run. There is no step 3.
# ===========================================================================

@dataclass(frozen=True)
class Stream:
    """One material stream: where to read it, how to sample it, where it goes.

    Fields:
        key:        internal name, and the file prefix of everything it writes.
                    NAMED FOR ITS ROLE, never for its current chemistry -- the
                    magnet stream stays "magnet" whatever magnet it models.
        label:      human name, used in figure titles and the Stream column.
                    THIS is where the chemistry is recorded.
        folder:     output root.
        color:      figure colour.
        sheet:      sheet of 10_MaterialElementDefinitions.xlsx.
        mass_col:   column of ElectricMotorMC's materials_samples_csv/*.npy
                    holding this stream's per-draw mass. UNIT: kg.
        grades:     grade names to read from the sheet.
        order:      element output order. Includes the balance element.
        ratio_cols: element columns read as-is (already mass fractions).
        ppm_cols:   element columns given in ppm; divided by 1e6 on read.
        balance:    element computed as 1 - sum(others), or None if the sheet's
                    fractions are already complete. See sample_composition.
        weights:    (segment, motor_token) -> {grade: weight}. A callable rather
                    than a dict because electrical steel's grade mix depends on
                    segment, and NdFeB's depended on segment AND motor type.
        balance_tol: warn if the computed balance falls this far outside the
                    sheet's own stated range for that element. None to skip.
    """
    key: str
    label: str
    folder: Path
    color: str
    sheet: str
    mass_col: str
    grades: List[str]
    order: List[str]
    ratio_cols: List[str]
    ppm_cols: List[str]
    balance: str | None
    weights: object
    hist_globs: List[str] = field(default_factory=list)
    balance_tol: float | None = None

    @property
    def drawn(self) -> List[str]:
        """Elements actually sampled -- everything except the balance."""
        return [e for e in self.order if e != self.balance]


STREAMS: Dict[str, Stream] = {
    "copper": Stream(
        key="copper", label="Copper", folder=CU_ROOT, color=COPPER_COLOR,
        sheet="Copper", mass_col="mass_kg__Copper",
        grades=CU_GRADES, order=CU_ELEMENTS,
        ratio_cols=RATIO_COLS, ppm_cols=PPM_COLS,
        balance=None,
        weights=lambda seg, motor: CU_WEIGHTS,
        hist_globs=["hist_materialmass_*_Copper.csv"],
    ),
    "esteel": Stream(
        key="esteel", label="Electrical Steel", folder=ESTL_ROOT, color=ESTL_COLOR,
        sheet="ElectricalSteel", mass_col="mass_kg__ElectricalSteel",
        grades=sorted({g for w in ESTL_SEGMENT_WEIGHTS.values() for g in w}),
        order=["Fe"] + ESTL_ELEMENTS,
        ratio_cols=ESTL_ELEMENTS, ppm_cols=[],
        balance="Fe",
        weights=lambda seg, motor: ESTL_SEGMENT_WEIGHTS[seg],
        hist_globs=["hist_materialmass_*_ElectricalSteel.csv",
                    "hist_materialmass_*_electrosteel.csv"],
    ),
    # THE MAGNET STREAM. Strontium ferrite since 2026-08-13; it was NdFeB
    # before. Changing it back, or to anything else, is this entry plus a sheet
    # in 10_ -- see the note above FERRITE_ELEMENTS for why ferrite is right for
    # auxiliary motors. The mass column is `mass_kg__Magnet`, named for the PART:
    # ElectricMotorMC keys this row on 05_'s `component` column, so the column
    # name no longer moves when the magnet material does.
    "magnet": Stream(
        key="magnet", label="Strontium Ferrite", folder=MAGNET_ROOT,
        color=FERRITE_COLOR,
        sheet=FERRITE_SHEET, mass_col="mass_kg__Magnet",
        grades=list(FERRITE_GRADES), order=FERRITE_ELEMENTS,
        ratio_cols=FERRITE_ELEMENTS, ppm_cols=[],
        balance="Fe", balance_tol=FERRITE_FE_TOL,
        weights=lambda seg, motor: FERRITE_GRADES,
        # `_Magnet` ONLY. ElectricMotorMC names this file from the component now,
        # so the old `_NdFeB` spelling can only come from a stale histogram set --
        # and matching both is not a harmless fallback: these files are iterated
        # and accumulated into mc_accum per (segment, stream), so an old set beside
        # a new one adds the magnet to the grand totals TWICE. Delete stale files
        # rather than widening this glob.
        hist_globs=["hist_materialmass_*_Magnet.csv"],
    ),
    "cfsteel": Stream(
        key="cfsteel", label="Cast Fe Steel", folder=CFSTEEL_ROOT,
        color=CFSTEEL_COLOR,
        sheet="CastFeSteel", mass_col="mass_kg__Steel",
        grades=["DC01"], order=["Fe"] + CFSTEEL_ELEMENTS,
        ratio_cols=CFSTEEL_ELEMENTS, ppm_cols=[],
        balance="Fe",
        weights=lambda seg, motor: {"DC01": 1.0},
        hist_globs=["hist_materialmass_*_CastFeSteel.csv",
                    "hist_materialmass_*_castfesteel.csv",
                    "hist_materialmass_*_CastFe Steel.csv",
                    "hist_materialmass_*_Steel.csv",
                    "hist_materialmass_*_steel.csv"],
    ),
}


def load_grades(xlsx: Path, spec: Stream) -> Dict[str, Dict[str, Tuple[float, float]]]:
    """{grade: {element: (min, max)}} for one stream. Replaces four loaders.

    Column headers are stripped on read: the ferrite sheet's header is 'Grade '
    with a trailing space, and matching on 'Grade' silently returns nothing --
    the same class of trap as the non-breaking spaces in 11_.
    """
    df = pd.read_excel(xlsx, sheet_name=spec.sheet, header=0)
    df.columns = [str(c).strip() for c in df.columns]
    df["Grade"] = df["Grade"].astype(str).str.strip()
    df["Range"] = df["Range"].astype(str).str.strip().str.lower()

    out: Dict[str, Dict[str, Tuple[float, float]]] = {}
    for grade in spec.grades:
        sub = df[df["Grade"] == grade]
        lo_rows, hi_rows = sub[sub["Range"] == "min"], sub[sub["Range"] == "max"]
        if lo_rows.empty or hi_rows.empty:
            raise KeyError(
                f"grade {grade!r} needs both a min and a max row in sheet "
                f"{spec.sheet!r}. Found: {sorted(df['Grade'].unique())}")
        lo, hi = lo_rows.iloc[0], hi_rows.iloc[0]
        elems: Dict[str, Tuple[float, float]] = {}
        for col in spec.ratio_cols:
            elems[col] = (float(lo[col]), float(hi[col]))
        for col in spec.ppm_cols:
            # read by the sheet's column name, store under the ELEMENT's name
            elems[PPM_ELEMENT.get(col, col)] = (
                float(lo[col]) / 1e6, float(hi[col]) / 1e6)
        out[grade] = elems
    return out


def sample_composition(spec: Stream,
                       grades: Dict[str, Dict[str, Tuple[float, float]]],
                       rng: np.random.Generator, n: int,
                       segment: str, motor_token: str | None):
    """(element_names, fractions[n, n_elem]) for one stream. Replaces four samplers.

    Each element is drawn uniformly between its min and max, weighted across
    grades. The balance element is NOT drawn -- it is 1 minus the others, so the
    fractions sum to exactly 1 by construction.

    WHY A BALANCE ELEMENT AT ALL. Drawing every element independently lets a
    kilogram of material become 0.9-1.1 kg of elements. That is not a rounding
    concern: NdFeB was doing exactly this until 2026-08-13 and inflated magnet
    mass by 4.1% on average, up to 11%. Iron is the balance in all three alloys
    that have one -- it is the majority constituent and the one whose reported
    range is widest.
    """
    w_raw = spec.weights(segment, motor_token)
    total = sum(w_raw.values())
    drawn = spec.drawn

    acc = np.zeros((n, len(drawn)), dtype=float)
    bal_lo = bal_hi = 0.0
    for grade, w in w_raw.items():
        weight = w / total
        if grade not in grades:
            raise KeyError(f"grade {grade!r} not loaded for stream {spec.key!r}")
        for i, elem in enumerate(drawn):
            lo, hi = grades[grade][elem]
            acc[:, i] += weight * uniform(rng, lo, hi, n)
        if spec.balance and spec.balance in grades[grade]:
            g_lo, g_hi = grades[grade][spec.balance]
            bal_lo += weight * g_lo
            bal_hi += weight * g_hi

    if spec.balance is None:
        return list(spec.order), acc

    bal = np.clip(1.0 - acc.sum(axis=1), 0.0, 1.0)
    if spec.balance_tol is not None and not (
            bal_lo - spec.balance_tol <= bal.mean() <= bal_hi + spec.balance_tol):
        print(f"    WARNING: {spec.label} balance {spec.balance} = {bal.mean():.4f} "
              f"sits outside the sheet's weighted range "
              f"[{bal_lo:.4f}, {bal_hi:.4f}]. The sheet's rows disagree.")

    col = {e: acc[:, i] for i, e in enumerate(drawn)}
    col[spec.balance] = bal
    return list(spec.order), np.column_stack([col[e] for e in spec.order])


# ────────────────────────────────────────────────────────────────────────────
# GENERIC STREAM PROCESSOR
# Returns a dict keyed by (seg, stream) → {"elem_mass": ndarray, "total_mass": ndarray}
# for use in grand-total MC aggregation.
# ────────────────────────────────────────────────────────────────────────────
def process_stream(
    stream: str,
    rng: np.random.Generator,
    summary_rows: list,
) -> Dict[Tuple[str, str], Dict]:
    """Process one material stream end to end.

    Everything the stream needs -- its sheet, grades, elements, balance, file
    globs and output folder -- comes from its STREAMS entry. Adding a material
    does not change this function.

    Returns mc_accum: dict keyed by (segment, stream) with accumulated MC arrays
    for grand-total computation.
    """
    spec         = STREAMS[stream]
    hist_csvs    = sorted({f for g in spec.hist_globs for f in MAT_HIST_DIR.glob(g)})
    grades       = load_grades(XLSX_FILE, spec)
    color        = spec.color
    title_prefix = spec.label
    file_prefix  = spec.key
    out_root     = spec.folder

    dir_hist = out_root / "histograms_csv"
    dir_dist = out_root / "distribution_figures"
    dir_sens = out_root / "sensitivity_figures"

    # Accumulator for grand totals: (seg, stream) → {elem_mass, total_mass, elements}
    mc_accum: Dict[Tuple[str, str], Dict] = {}

    for hist_csv in hist_csvs:
        stem      = hist_csv.stem
        seg_token, motor_token_lower = parse_csv_filename(stem)
        label     = build_label(stem, stream)

        if seg_token is None:
            print(f"    WARNING: cannot resolve segment from '{stem}', skipping.")
            continue

        print(f"\n  [{title_prefix}] {label}")

        # 1. ElectricMotorMC's OWN draws for this material -- not a resample of
        #    its exported histogram. Row i is one motor in every stream, so a
        #    heavy motor is heavy in all of its materials at once.
        mat_mass_kg = load_material_draws(stem, stream, N_SAMPLES)
        print(f"    mass: mean={mat_mass_kg.mean():.4f} kg, std={mat_mass_kg.std():.4f} kg")

        # 2. Sample composition -- one call, whatever the material is
        elements, mean_fractions = sample_composition(
            spec, grades, rng, N_SAMPLES, seg_token, motor_token_lower)

        # 3. Elemental mass  (N, n_elem)
        elem_mass_kg = mat_mass_kg[:, None] * mean_fractions

        # 4. Accumulate for grand totals (sample-wise sum across motor types)
        key = (seg_token, stream)
        if key not in mc_accum:
            mc_accum[key] = {
                "elem_mass":  np.zeros_like(elem_mass_kg),
                "total_mass": np.zeros(N_SAMPLES, dtype=float),
                "elements":   elements,
            }
        mc_accum[key]["elem_mass"]  += elem_mass_kg
        mc_accum[key]["total_mass"] += mat_mass_kg

        # 5. Export per-case histogram CSVs
        safe_label = label.replace(" ", "_").replace("/", "_")
        for j, elem in enumerate(elements):
            safe_elem = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in elem)
            export_histogram_csv(
                elem_mass_kg[:, j],
                dir_hist / f"{file_prefix}_hist_{safe_label}_{safe_elem}.csv",
            )
        export_histogram_csv(
            mat_mass_kg,
            dir_hist / f"{file_prefix}_hist_{safe_label}_TotalMass.csv",
        )

        # 6. Distribution figure
        save_distribution_figure(
            label, elements, elem_mass_kg, mat_mass_kg,
            color, title_prefix, dir_dist, file_prefix,
        )

        # 7. Sensitivity heatmap
        save_sensitivity_heatmap(
            label, elements, elem_mass_kg, mat_mass_kg, mean_fractions,
            title_prefix, dir_sens, file_prefix,
        )

        # 8. Summary rows
        for j, elem in enumerate(elements):
            x = elem_mass_kg[:, j]
            summary_rows.append(build_summary_row(
                title_prefix, label, elem, x, float(np.mean(mean_fractions[:, j]))
            ))
        summary_rows.append(build_summary_row(
            title_prefix, label, "TotalMass", mat_mass_kg, 1.0
        ))

        print(f"    → figures, histograms, sensitivity saved.")

    return mc_accum


# ────────────────────────────────────────────────────────────────────────────
# GRAND TOTALS PER SEGMENT GROUP — full MC (sample-wise sum)
# ────────────────────────────────────────────────────────────────────────────
def process_grand_totals(
    mc_accum: Dict[Tuple[str, str], Dict],
    summary_rows: list,
) -> None:
    """
    For each (segment, stream) combination, the MC arrays have already been
    accumulated sample-by-sample in process_stream().  Here we generate:
      - histogram CSVs for each element and total mass
      - distribution figure
      - sensitivity heatmap
      - summary rows
    """
    # [NEW] Per-SEGMENT element fractions, combining all four material streams.
    #
    # The per-stream fractions written further down describe composition WITHIN a
    # stream -- what the copper stream is made of, what the NdFeB stream is made of.
    # They cannot be combined without knowing each stream's share of total motor
    # mass, and a consumer holding only the motor domain's total mass has no way to
    # recover that. So the combined split is computed here, where every stream for a
    # segment is in hand at once, and written as one array per segment:
    #
    #     element_mass[draw, year] = motor_mass[draw, year] x fraction[draw, element]
    #
    # Elements are unioned across streams and summed where they appear in more than
    # one (iron occurs in both steels, for instance), so the fractions describe the
    # whole motor rather than any single stream.
    #
    # THE DENOMINATOR MUST BE THE WHOLE MOTOR, NOT THE PART THIS MODEL RESOLVES.
    # This is the defect that the first version of this block shipped with, and it is
    # worth stating plainly because the wrong version looked completely healthy: its
    # fractions summed to 1.0000 to four decimals, on every segment.
    #
    # They summed to 1 over the WRONG TOTAL. This model resolves four material
    # streams into elements -- cast Fe steel, copper, electrical steel, NdFeB. A motor
    # in ElectricMotorMC is made of SIX materials: those four plus Aluminium and
    # Plastic, which have no elemental breakdown (aluminium IS an element; plastic is
    # not resolved further). Dividing by the sum of the four streams therefore gives
    # "fraction of the elementally-resolved part of a motor", which is a perfectly
    # self-consistent quantity and the wrong one to hand downstream.
    #
    # The consumer (RAWCLICStockAndFlow stage 04_02) multiplies these fractions by
    # tools/mc_composition.py's Motors mass, and that mass is the WHOLE motor. Mixing
    # the two denominators inflates every motor element by 1/(1 - unresolved share):
    #
    #     segment   Al + Plastic     inflation if unfixed
    #     AB              10.32%                   +11.5%
    #     CD              17.67%                   +21.5%
    #     EF              22.18%                   +28.5%
    #
    # Nd, Dy and motor copper would all have come out high by that much, with nothing
    # in the output to show for it.
    #
    # So the denominator is ElectricMotorMC's own per-draw `total_mass_kg`, and the
    # two unresolved materials are carried explicitly: bulk Aluminium is added into
    # the `Al` element, because aluminium metal is the element aluminium, and Plastic
    # is carried under its own name so the fractions still sum to exactly 1 and the
    # unresolved part is visible rather than hidden in a shortfall.
    #
    # Row i is THE SAME SIMULATED MOTOR in both models -- this model reads
    # ElectricMotorMC's draws directly (see load_material_draws) rather than
    # resampling them -- so this division is exact per draw, not an assumed pairing.
    # AN ELEMENT IS IDENTIFIED BY THE MATERIAL IT SITS IN, NOT BY ITS SYMBOL ALONE.
    #
    # `S__esteel` and `S__copper` are both sulfur and they are NOT the same
    # quantity: one is an alloying addition in the electrical steel, the other an
    # impurity in the copper winding. They are different materials in different
    # parts of the motor, they behave differently in recycling, and adding them
    # would produce a number that describes nothing. Same for the iron in four
    # streams. So the name carries the stream, and nothing merges across materials.
    #
    # COPPER IS THE ONE EXCEPTION, by decision. It is the element this whole chain
    # exists to quantify and it is wanted as ONE total for the motor -- the winding
    # plus whatever copper appears as a trace elsewhere -- so it accumulates under
    # a plain `Cu` across every stream.
    CROSS_MATERIAL = {"Cu"}

    _by_seg: Dict[str, Dict[str, np.ndarray]] = {}
    _res_by_seg: Dict[str, np.ndarray] = {}
    for (seg, stream), data in mc_accum.items():
        em = np.asarray(data["elem_mass"], dtype=float)
        tm = np.asarray(data["total_mass"], dtype=float)
        acc = _by_seg.setdefault(seg, {})
        for j, el in enumerate(data["elements"]):
            key = el if el in CROSS_MATERIAL else f"{el}__{stream}"
            acc[key] = acc.get(key, 0.0) + em[:, j]
        _res_by_seg[seg] = _res_by_seg.get(seg, 0.0) + tm

    ELEM_DRAWS_DIR.mkdir(parents=True, exist_ok=True)
    for seg, acc in _by_seg.items():
        els = [e for e, v in acc.items() if np.any(v != 0)]
        if not els:
            continue
        n_draws = len(acc[els[0]])
        tot_full, al_bulk, plastic = motor_mass_and_unresolved(seg, n_draws)

        acc = dict(acc)
        # Bulk aluminium is its own material -- ElectricMotorMC's `Aluminum` stream,
        # the housing and frame -- so it is named for that material like every other
        # entry, NOT folded into the aluminium that sits inside the electrical steel
        # or the magnet.
        acc["Al__bulk"] = acc.get("Al__bulk", 0.0) + al_bulk
        acc["Plastic"] = plastic                      # NOT an element; kept visible
        # "Al__bulk", not "Al": the two unresolved materials are appended by name,
        # and bulk aluminium now carries its material like every other entry. Naming
        # the wrong key here does not raise -- the column is simply left out and the
        # motor comes up short. The partition check below is what catches it.
        els = [e for e in (*els, "Al__bulk", "Plastic") if e in acc]
        els = list(dict.fromkeys(els))
        els = [e for e in els if np.any(np.asarray(acc[e]) != 0)]

        mass = np.column_stack([np.asarray(acc[e], dtype=float) for e in els])

        # RECONCILIATION. The four resolved streams plus Aluminium plus Plastic must
        # BE the motor -- the elements decompose it, so anything else means a stream
        # is missing or double-counted. Checked per draw, not on the mean, because a
        # mean can reconcile while individual draws do not.
        #
        # What is left over is carried, not absorbed. The named elements fall ~5e-5
        # short of the motor (see MOTOR_FRAC_TOL), because the copper specification
        # lists Cu plus impurities in ppm and does not quite close. Dropping that
        # would make the fractions sum to slightly under 1 and quietly rescale every
        # element when a consumer normalised them; hiding it in a loose tolerance
        # would make it invisible. It gets a name instead.
        residual = tot_full - mass.sum(axis=1)
        rel = residual / np.maximum(tot_full, 1e-12)

        if np.any(rel > MOTOR_FRAC_TOL):
            i = int(np.argmax(rel))
            raise ValueError(
                f"motor composition falls short for {seg}: "
                f"{int((rel > MOTOR_FRAC_TOL).sum()):,} of {n_draws:,} draws leave "
                f"more than {MOTOR_FRAC_TOL:.1e} of the motor unaccounted. Worst "
                f"draw {i}: elements+Al+Plastic = {mass.sum(axis=1)[i]:.6f} kg vs "
                f"ElectricMotorMC total_mass_kg = {tot_full[i]:.6f} kg "
                f"({rel[i]:.2e}). A material stream is missing from mc_accum.")

        if np.any(rel < -MOTOR_FRAC_TOL):
            i = int(np.argmin(rel))
            raise ValueError(
                f"motor composition OVERSHOOTS for {seg}: draw {i} has "
                f"elements+Al+Plastic = {mass.sum(axis=1)[i]:.6f} kg against a motor "
                f"of {tot_full[i]:.6f} kg ({rel[i]:.2e}). The parts cannot outweigh "
                f"the whole -- a stream is being counted twice, or TotalMass has "
                f"leaked in as if it were an element.")

        els = [*els, "Unspecified"]
        mass = np.column_stack([mass, residual])

        frac = np.zeros_like(mass)
        nz = tot_full > 0
        frac[nz] = mass[nz] / tot_full[nz, None]
        np.save(ELEM_DRAWS_DIR / f"motors_{seg}_fractions.npy", frac.astype(np.float32))
        (ELEM_DRAWS_DIR / f"motors_{seg}_elements.txt").write_text("\n".join(els))
        _s = frac.sum(axis=1)
        print(f"      combined draws -> element_draws/motors_{seg}_fractions.npy "
              f"{frac.shape}  sum(frac) mean={_s.mean():.8f} "
              f"[{_s.min():.8f}-{_s.max():.8f}]")
        # A READ-OUT, not a computation. Column names now carry their material, so
        # an element is a GROUP of columns -- aluminium is Al__bulk plus the Al in
        # the electrical steel. Summing them here is a display total for a human
        # reading the log; nothing downstream uses it. Looking a bare name up with
        # .index() is what broke when the names gained their material.
        def _el_frac(sym: str) -> float:
            cols = [i for i, e in enumerate(els) if e == sym or e.startswith(f"{sym}__")]
            return float(frac[:, cols].sum(axis=1).mean()) if cols else float("nan")

        print(f"        motor mass {tot_full.mean():7.3f} kg   "
              f"Cu {_el_frac('Cu'):.5f}   "
              f"Al {_el_frac('Al'):.5f}   "
              f"Plastic {_el_frac('Plastic'):.5f}   "
              f"Unspecified {rel.mean():.2e} (max {rel.max():.2e})")

    for (seg, stream), data in mc_accum.items():
        elem_mass_kg  = data["elem_mass"]    # (N_SAMPLES, n_elem)
        total_mass_kg = data["total_mass"]   # (N_SAMPLES,)
        elements      = data["elements"]

        # [NEW] Persist this (segment, stream)'s per-draw element FRACTIONS.
        # Fractions rather than masses, because the consumer scales them by its own
        # year-resolved stream mass; see ELEM_DRAWS_DIR above. Rows where the stream
        # mass is zero would divide by zero, so they are left at zero -- a stream with
        # no mass contributes no element mass either way.
        ELEM_DRAWS_DIR.mkdir(parents=True, exist_ok=True)
        _tot = np.asarray(total_mass_kg, dtype=float)
        _frac = np.zeros_like(np.asarray(elem_mass_kg, dtype=float))
        _nz = _tot > 0
        _frac[_nz] = np.asarray(elem_mass_kg, dtype=float)[_nz] / _tot[_nz, None]
        np.save(ELEM_DRAWS_DIR / f"motors_{seg}_{stream}_fractions.npy",
                _frac.astype(np.float32))
        (ELEM_DRAWS_DIR / f"motors_{seg}_{stream}_elements.txt").write_text(
            "\n".join(map(str, elements)))
        print(f"      draws -> {ELEM_DRAWS_DIR.name}/motors_{seg}_{stream}_fractions.npy "
              f"{_frac.shape}")

        spec         = STREAMS[stream]
        color        = spec.color
        title_prefix = spec.label
        file_prefix  = spec.key
        out_root     = spec.folder

        dir_hist = out_root / "histograms_csv"
        dir_dist = out_root / "distribution_figures"
        dir_sens = out_root / "sensitivity_figures"

        label = f"GRAND_TOTAL_{seg}"
        print(f"\n  [{title_prefix}] Grand Total {seg}")

        # Histogram CSVs
        for j, elem in enumerate(elements):
            safe_elem = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in elem)
            export_histogram_csv(
                elem_mass_kg[:, j],
                dir_hist / f"{file_prefix}_hist_{label}_{safe_elem}.csv",
            )
        export_histogram_csv(
            total_mass_kg,
            dir_hist / f"{file_prefix}_hist_{label}_TotalMass.csv",
        )

        # Distribution figure
        save_distribution_figure(
            label, elements, elem_mass_kg, total_mass_kg,
            color, title_prefix, dir_dist, file_prefix,
        )

        # Sensitivity heatmap — use elem_mass / total_mass as proxy for fraction
        # (grand total fractions are not directly meaningful, but the heatmap
        #  shows which elements drive the total mass variance)
        with np.errstate(divide="ignore", invalid="ignore"):
            grand_fractions = np.where(
                total_mass_kg[:, None] > 0,
                elem_mass_kg / total_mass_kg[:, None],
                0.0,
            )
        save_sensitivity_heatmap(
            label, elements, elem_mass_kg, total_mass_kg, grand_fractions,
            title_prefix, dir_sens, file_prefix,
        )

        # Summary rows
        for j, elem in enumerate(elements):
            x = elem_mass_kg[:, j]
            summary_rows.append(build_summary_row(
                title_prefix, label, elem, x,
                float(np.mean(grand_fractions[:, j]))
            ))
        summary_rows.append(build_summary_row(
            title_prefix, label, "TotalMass", total_mass_kg, 1.0
        ))

        print(f"    → Grand Total {seg} figures, histograms, sensitivity saved.")


# ────────────────────────────────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────────────────────────────────
def main() -> None:
    if not XLSX_FILE.exists():
        raise FileNotFoundError(f"Element definitions not found: {XLSX_FILE}")
    if not MAT_HIST_DIR.exists():
        raise FileNotFoundError(
            f"Material histograms folder not found: {MAT_HIST_DIR}\n"
            "Run ElectricMotorMC.py first."
        )

    rng = np.random.default_rng(RNG_SEED)

    print("Loading grade definitions...")
    for key, spec in STREAMS.items():
        g = load_grades(XLSX_FILE, spec)
        print(f"  {spec.label:20s} sheet {spec.sheet:22s} grades {list(g)}")

    summary_rows: list = []
    all_mc_accum: Dict[Tuple[str, str], Dict] = {}

    # ── Process every stream in the table ────────────────────────────────────
    # No per-material branches. Adding a material to STREAMS is the whole change.
    for key, spec in STREAMS.items():
        found = sorted({f for g in spec.hist_globs for f in MAT_HIST_DIR.glob(g)})
        print(f"\nFound {len(found)} {spec.label} histogram CSV(s)")
        if not found:
            continue
        print("=" * 60)
        print(f"Processing {spec.label.upper()} stream...")
        mc = process_stream(key, rng, summary_rows)
        all_mc_accum.update(mc)

    if not all_mc_accum:
        raise FileNotFoundError(
            f"No matching histogram CSVs found in {MAT_HIST_DIR}.\n"
            "Run ElectricMotorMC.py first. Expected files matching:\n  "
            + "\n  ".join(g for spec in STREAMS.values() for g in spec.hist_globs))

    # ── Grand totals per segment group (full MC) ─────────────────────────────
    if all_mc_accum:
        print("\n" + "=" * 60)
        print("Computing MC Grand Totals per segment group (AB / CD / EF)...")
        process_grand_totals(all_mc_accum, summary_rows)

    # ── Combined summary CSV ─────────────────────────────────────────────────
    df_sum = pd.DataFrame(summary_rows)
    for root in [CU_ROOT, ESTL_ROOT, MAGNET_ROOT, CFSTEEL_ROOT]:
        df_sum.to_csv(root / "summary_csv" / "elemental_summary.csv", index=False)

    print("\n" + "=" * 60)
    print("Done.")
    print(f"  Copper outputs       → {CU_ROOT}")
    print(f"  Electrical Steel out → {ESTL_ROOT}")
    print(f"  Magnet outputs       → {MAGNET_ROOT}  (strontium ferrite)")
    print(f"  Cast Fe Steel out    → {CFSTEEL_ROOT}")
    print(f"  Combined summary     → elemental_summary.csv (in all summary_csv folders)")


if __name__ == "__main__":
    main()
