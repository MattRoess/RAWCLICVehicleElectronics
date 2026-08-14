#!/usr/bin/env python3
"""
ElectricMotorElementMC.py
────
Monte Carlo elemental analysis for four material streams produced by
ElectricMotorMC.py:

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
MAT_HIST_DIR = HERE.parent / "ElectricMotorMC" / "materials_histograms_csv"

# Output roots
CU_ROOT       = HERE / "CopperElemental"
ESTL_ROOT     = HERE / "ElectricalSteelElemental"
NDFEB_ROOT    = HERE / "NdFeBElemental"
CFSTEEL_ROOT  = HERE / "CastFeSteelElemental"

for root in [CU_ROOT, ESTL_ROOT, NDFEB_ROOT, CFSTEEL_ROOT]:
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

PPM_COLS = [
    "O_ppm", "Ag_ppm", "Pb_ppm", "Bi_ppm", "Fe_ppm",
    "Sb_ppm", "As_ppm", "Sn_ppm", "Zn_ppm", "Ni_ppm",
    "S_ppm",  "P_ppm",  "Se_ppm", "Te_ppm", "Cd_ppm", "Mn_ppm",
]
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

MAT_SAMPLES_DIR = HERE.parent / "ElectricMotorMC" / "materials_samples_csv"

# Which column of ElectricMotorMC's per-draw sample file each stream reads.
# The stream keys are this model's internal names; the column names are
# ElectricMotorMC's material names, listed in the companion .json.
# NOTE cfsteel -> "Steel": ElectricMotorMC calls it Steel, this model calls the
# same material Cast Fe Steel. Same quantity, two names.
STREAM_MATERIAL_COL = {
    "copper":  "mass_kg__Copper",
    "esteel":  "mass_kg__ElectricalSteel",
    "ndfeb":   "mass_kg__NdFeB",
    "cfsteel": "mass_kg__Steel",
}


def load_material_draws(stem: str, stream: str, n: int) -> np.ndarray:
    """ElectricMotorMC's OWN per-draw material mass, in kg. (n,)

    Args:
        stem:   the histogram stem this case was discovered under, e.g.
                "hist_materialmass_CD_MediumDCMotors_metal_Steel". Only used to
                recover the case; the histogram itself is not read.
        stream: "copper" | "esteel" | "ndfeb" | "cfsteel".
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
    if stream not in STREAM_MATERIAL_COL:
        raise KeyError(f"no material column mapped for stream {stream!r}")

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
    want = STREAM_MATERIAL_COL[stream]
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

    if stream == "ndfeb":
        seg, motor_token = parse_csv_filename(stem)
        if seg and motor_token:
            # Use the canonical motor key name (not the lowercase token)
            motor_name = NDFEB_MOTOR_MAP[motor_token]
            return f"{seg}_{motor_name}"
        # fallback
        return "_".join(inner)
    else:
        return "_".join(inner)


# ────────────────────────────────────────────────────────────────────────────
# COPPER — grade loading & composition sampling
# ────────────────────────────────────────────────────────────────────────────
def load_copper_grades(xlsx: Path) -> Dict[str, Dict[str, Tuple[float, float]]]:
    df = pd.read_excel(xlsx, sheet_name="Copper", header=0)
    df.columns = [str(c).strip() for c in df.columns]
    df["Grade"] = df["Grade"].astype(str).str.strip()
    df["Range"] = df["Range"].astype(str).str.strip().str.lower()

    grades: Dict[str, Dict[str, Tuple[float, float]]] = {}
    for grade in CU_GRADES:
        sub     = df[df["Grade"] == grade]
        row_min = sub[sub["Range"] == "min"].iloc[0]
        row_max = sub[sub["Range"] == "max"].iloc[0]
        elems: Dict[str, Tuple[float, float]] = {}
        for col in RATIO_COLS:
            elems[col] = (float(row_min[col]), float(row_max[col]))
        for col in PPM_COLS:
            elems[col] = (float(row_min[col]) / 1e6, float(row_max[col]) / 1e6)
        grades[grade] = elems
    return grades


def sample_copper_composition(
    grades: Dict[str, Dict[str, Tuple[float, float]]],
    rng: np.random.Generator,
    n: int,
) -> Tuple[List[str], np.ndarray]:
    """Equal-weight mean of ETP, OF, OFE grades."""
    elements = list(next(iter(grades.values())).keys())
    n_elem   = len(elements)
    acc      = np.zeros((n, n_elem), dtype=float)
    for grade, weight in CU_WEIGHTS.items():
        for e_idx, elem in enumerate(elements):
            lo, hi = grades[grade][elem]
            acc[:, e_idx] += weight * uniform(rng, lo, hi, n)
    return elements, acc


# ────────────────────────────────────────────────────────────────────────────
# ELECTRICAL STEEL — grade loading & composition sampling
# ────────────────────────────────────────────────────────────────────────────
def load_esteel_grades(xlsx: Path) -> Dict[str, Dict[str, Tuple[float, float]]]:
    df = pd.read_excel(xlsx, sheet_name="ElectricalSteel", header=0)
    df.columns = [str(c).strip() for c in df.columns]
    df["Grade"] = df["Grade"].astype(str).str.strip()
    df["Range"] = df["Range"].astype(str).str.strip().str.lower()

    grades: Dict[str, Dict[str, Tuple[float, float]]] = {}
    for grade in df["Grade"].unique():
        sub = df[df["Grade"] == grade]
        if sub[sub["Range"] == "min"].empty or sub[sub["Range"] == "max"].empty:
            continue
        row_min = sub[sub["Range"] == "min"].iloc[0]
        row_max = sub[sub["Range"] == "max"].iloc[0]
        elems: Dict[str, Tuple[float, float]] = {}
        for col in ESTL_ELEMENTS:
            elems[col] = (float(row_min[col]), float(row_max[col]))
        grades[grade] = elems
    return grades


def sample_esteel_composition(
    grades: Dict[str, Dict[str, Tuple[float, float]]],
    weights: Dict[str, float],
    rng: np.random.Generator,
    n: int,
) -> Tuple[List[str], np.ndarray]:
    """Weighted mean across grades; Fe = 1 − Σ(others), clamped to [0,1]."""
    total_w = sum(weights.values())
    norm_w  = {g: w / total_w for g, w in weights.items()}

    n_other = len(ESTL_ELEMENTS)
    acc     = np.zeros((n, n_other), dtype=float)
    for grade, weight in norm_w.items():
        if grade not in grades:
            raise KeyError(f"Grade '{grade}' not found in ElectricalSteel sheet.")
        for e_idx, elem in enumerate(ESTL_ELEMENTS):
            lo, hi = grades[grade][elem]
            acc[:, e_idx] += weight * uniform(rng, lo, hi, n)

    fe        = np.clip(1.0 - acc.sum(axis=1), 0.0, 1.0)
    fractions = np.column_stack([fe, acc])
    elements  = ["Fe"] + ESTL_ELEMENTS
    return elements, fractions


# ────────────────────────────────────────────────────────────────────────────
# NdFeB — grade loading & composition sampling
# ────────────────────────────────────────────────────────────────────────────
def load_ndfeb_grades(xlsx: Path) -> Dict[str, Dict[str, Tuple[float, float]]]:
    df = pd.read_excel(xlsx, sheet_name="PermanentMagnetNdFeB", header=0)
    df.columns = [str(c).strip() for c in df.columns]
    df["Grade"] = df["Grade"].astype(str).str.strip()
    df["Range"] = df["Range"].astype(str).str.strip().str.lower()

    grades: Dict[str, Dict[str, Tuple[float, float]]] = {}
    for grade in df["Grade"].unique():
        sub = df[df["Grade"] == grade]
        rows_min = sub[sub["Range"] == "min"]
        rows_max = sub[sub["Range"] == "max"]
        if rows_min.empty or rows_max.empty:
            continue
        row_min = rows_min.iloc[0]
        row_max = rows_max.iloc[0]
        elems: Dict[str, Tuple[float, float]] = {}
        for col in NDFEB_ELEMENTS:
            elems[col] = (float(row_min[col]), float(row_max[col]))
        grades[grade] = elems
    return grades


def sample_ndfeb_composition(
    grades: Dict[str, Dict[str, Tuple[float, float]]],
    weights: Dict[str, float],
    rng: np.random.Generator,
    n: int,
) -> Tuple[List[str], np.ndarray]:
    """
    Weighted mean composition across NdFeB grades. Fe is the BALANCE element.
    Weights are normalised to sum=1.
    Returns (element_names, mean_fractions[n, n_elem]).

    FE IS COMPUTED AS 1 - sum(others), NOT DRAWN. Fixed 2026-08-13.

    Until then every element including Fe was drawn independently between its
    own min and max, and nothing made the eleven fractions sum to 1. Measured
    over the twelve cases the sum ran from 0.982 to 1.113, mean 1.041 -- so a
    kilogram of magnet was turned into 1.041 kg of elements, and the error was
    worst where NdFeB content is highest. The other three streams never had
    this problem: Cast Fe Steel and Electrical Steel already treat Fe as the
    balance, which is the pattern followed here.

    This is the physically right constraint as well as the arithmetically right
    one: NdFeB is Nd2Fe14B with substitutions, iron makes up the remainder by
    definition, and the sheet's Fe row is a reported range rather than an
    independent degree of freedom. The drawn balance is checked against that
    reported range below.
    """
    total_w = sum(weights.values())
    norm_w  = {g: w / total_w for g, w in weights.items()}

    others = [e for e in NDFEB_ELEMENTS if e != "Fe"]
    acc    = np.zeros((n, len(others)), dtype=float)
    fe_lo  = fe_hi = 0.0

    for grade, weight in norm_w.items():
        if grade not in grades:
            raise KeyError(
                f"NdFeB grade '{grade}' not found in NdFeB sheet. "
                f"Available: {list(grades.keys())}"
            )
        for e_idx, elem in enumerate(others):
            lo, hi = grades[grade][elem]
            acc[:, e_idx] += weight * uniform(rng, lo, hi, n)
        g_lo, g_hi = grades[grade]["Fe"]
        fe_lo += weight * g_lo
        fe_hi += weight * g_hi

    fe = np.clip(1.0 - acc.sum(axis=1), 0.0, 1.0)

    # The balance must land inside the range the sheet reports for Fe. If it
    # does not, the non-Fe ranges and the Fe range disagree and the sheet needs
    # looking at -- silently clamping would hide that.
    if not (fe_lo - NDFEB_FE_TOL <= fe.mean() <= fe_hi + NDFEB_FE_TOL):
        print(f"    WARNING: NdFeB balance Fe = {fe.mean():.4f} sits outside the "
              f"sheet's weighted Fe range [{fe_lo:.4f}, {fe_hi:.4f}]. The non-Fe "
              f"ranges and the Fe range in PermanentMagnetNdFeB disagree.")

    # reassemble in the declared NDFEB_ELEMENTS order so downstream columns and
    # figures are unchanged
    col = {e: acc[:, i] for i, e in enumerate(others)}
    col["Fe"] = fe
    fractions = np.column_stack([col[e] for e in NDFEB_ELEMENTS])
    return NDFEB_ELEMENTS, fractions


# ────────────────────────────────────────────────────────────────────────────
# CAST FE STEEL — grade loading & composition sampling
# ────────────────────────────────────────────────────────────────────────────
def load_castfesteel_grades(xlsx: Path) -> Dict[str, Dict[str, Tuple[float, float]]]:
    """Read DC01 from the CastFeSteel sheet."""
    df = pd.read_excel(xlsx, sheet_name="CastFeSteel", header=0)
    df.columns = [str(c).strip() for c in df.columns]
    df["Grade"] = df["Grade"].astype(str).str.strip()
    df["Range"] = df["Range"].astype(str).str.strip().str.lower()

    grades: Dict[str, Dict[str, Tuple[float, float]]] = {}
    for grade in ["DC01"]:
        sub = df[df["Grade"] == grade]
        if sub[sub["Range"] == "min"].empty or sub[sub["Range"] == "max"].empty:
            continue
        row_min = sub[sub["Range"] == "min"].iloc[0]
        row_max = sub[sub["Range"] == "max"].iloc[0]
        elems: Dict[str, Tuple[float, float]] = {}
        for col in CFSTEEL_ELEMENTS:
            elems[col] = (float(row_min[col]), float(row_max[col]))
        grades[grade] = elems
    return grades


def sample_castfesteel_composition(
    grades: Dict[str, Dict[str, Tuple[float, float]]],
    rng: np.random.Generator,
    n: int,
) -> Tuple[List[str], np.ndarray]:
    """DC01 only; Fe = 1 - sum(others), clamped to [0,1]."""
    grade = "DC01"
    if grade not in grades:
        raise KeyError(
            f"CastFeSteel grade '{grade}' not found in CastFeSteel sheet. "
            f"Available: {list(grades.keys())}"
        )

    n_other = len(CFSTEEL_ELEMENTS)
    acc     = np.zeros((n, n_other), dtype=float)
    for e_idx, elem in enumerate(CFSTEEL_ELEMENTS):
        lo, hi = grades[grade][elem]
        acc[:, e_idx] = uniform(rng, lo, hi, n)

    fe        = np.clip(1.0 - acc.sum(axis=1), 0.0, 1.0)
    fractions = np.column_stack([fe, acc])
    elements  = ["Fe"] + CFSTEEL_ELEMENTS
    return elements, fractions


# ────────────────────────────────────────────────────────────────────────────
# GENERIC STREAM PROCESSOR
# Returns a dict keyed by (seg, stream) → {"elem_mass": ndarray, "total_mass": ndarray}
# for use in grand-total MC aggregation.
# ────────────────────────────────────────────────────────────────────────────
def process_stream(
    hist_csvs: List[Path],
    rng: np.random.Generator,
    stream: str,                    # "copper" | "esteel" | "ndfeb" | "cfsteel"
    cu_grades: Dict | None,
    estl_grades: Dict | None,
    ndfeb_grades: Dict | None,
    summary_rows: list,
    cfsteel_grades: Dict | None = None,
) -> Dict[Tuple[str, str], Dict]:
    """
    Process all histogram CSVs for one material stream.
    Returns mc_accum: dict keyed by (segment, stream) with accumulated MC arrays
    for grand-total computation.
    """
    if stream == "copper":
        color        = COPPER_COLOR
        title_prefix = "Copper"
        file_prefix  = "copper"
        out_root     = CU_ROOT
    elif stream == "esteel":
        color        = ESTL_COLOR
        title_prefix = "Electrical Steel"
        file_prefix  = "esteel"
        out_root     = ESTL_ROOT
    elif stream == "cfsteel":
        color        = CFSTEEL_COLOR
        title_prefix = "Cast Fe Steel"
        file_prefix  = "cfsteel"
        out_root     = CFSTEEL_ROOT
    else:  # ndfeb
        color        = NDFEB_COLOR
        title_prefix = "NdFeB"
        file_prefix  = "ndfeb"
        out_root     = NDFEB_ROOT

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

        # 2. Sample composition
        if stream == "copper":
            elements, mean_fractions = sample_copper_composition(cu_grades, rng, N_SAMPLES)

        elif stream == "esteel":
            if seg_token not in ESTL_SEGMENT_WEIGHTS:
                print(f"    WARNING: unknown segment '{seg_token}', skipping.")
                continue
            weights = ESTL_SEGMENT_WEIGHTS[seg_token]
            elements, mean_fractions = sample_esteel_composition(
                estl_grades, weights, rng, N_SAMPLES
            )

        elif stream == "cfsteel":
            elements, mean_fractions = sample_castfesteel_composition(
                cfsteel_grades, rng, N_SAMPLES
            )

        else:  # ndfeb
            if motor_token_lower is None:
                print(f"    WARNING: cannot resolve motor type from '{stem}', skipping.")
                continue
            motor_key = NDFEB_MOTOR_MAP[motor_token_lower]
            if seg_token not in NDFEB_GRADE_WEIGHTS[motor_key]:
                print(f"    WARNING: segment '{seg_token}' not in NdFeB table for "
                      f"'{motor_key}', skipping.")
                continue
            weights  = NDFEB_GRADE_WEIGHTS[motor_key][seg_token]
            elements, mean_fractions = sample_ndfeb_composition(
                ndfeb_grades, weights, rng, N_SAMPLES
            )

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

        if stream == "copper":
            color        = COPPER_COLOR
            title_prefix = "Copper"
            file_prefix  = "copper"
            out_root     = CU_ROOT
        elif stream == "esteel":
            color        = ESTL_COLOR
            title_prefix = "Electrical Steel"
            file_prefix  = "esteel"
            out_root     = ESTL_ROOT
        elif stream == "cfsteel":
            color        = CFSTEEL_COLOR
            title_prefix = "Cast Fe Steel"
            file_prefix  = "cfsteel"
            out_root     = CFSTEEL_ROOT
        else:
            color        = NDFEB_COLOR
            title_prefix = "NdFeB"
            file_prefix  = "ndfeb"
            out_root     = NDFEB_ROOT

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
    cu_grades       = load_copper_grades(XLSX_FILE)
    estl_grades     = load_esteel_grades(XLSX_FILE)
    ndfeb_grades    = load_ndfeb_grades(XLSX_FILE)
    cfsteel_grades  = load_castfesteel_grades(XLSX_FILE)
    print(f"  Copper grades      : {list(cu_grades.keys())}")
    print(f"  E-Steel grades     : {list(estl_grades.keys())}")
    print(f"  NdFeB grades       : {list(ndfeb_grades.keys())}")
    print(f"  CastFeSteel grades : {list(cfsteel_grades.keys())}")
    print(f"  CastFeSteel active : {CFSTEEL_ELEMENTS}")
    print(f"  CastFeSteel excluded: {sorted(_CFSTEEL_EXCLUDED)}  (max=0 for DC01)")

    # ── Discover histogram CSVs ──────────────────────────────────────────────
    copper_csvs = sorted(MAT_HIST_DIR.glob("hist_materialmass_*_Copper.csv"))

    esteel_csvs = sorted(
        set(MAT_HIST_DIR.glob("hist_materialmass_*_ElectricalSteel.csv")) |
        set(MAT_HIST_DIR.glob("hist_materialmass_*_electrosteel.csv"))
    )

    # NdFeB: filename may contain extra tokens (e.g. _Ferrite_) before _NdFeB.csv
    ndfeb_csvs = sorted(
        set(MAT_HIST_DIR.glob("hist_materialmass_*_NdFeB.csv")) |
        set(MAT_HIST_DIR.glob("hist_materialmass_*_ndfeb.csv"))
    )

    # CastFeSteel: support multiple naming conventions
    cfsteel_csvs = sorted(
        set(MAT_HIST_DIR.glob("hist_materialmass_*_CastFeSteel.csv")) |
        set(MAT_HIST_DIR.glob("hist_materialmass_*_castfesteel.csv")) |
        set(MAT_HIST_DIR.glob("hist_materialmass_*_CastFe Steel.csv")) |
        set(MAT_HIST_DIR.glob("hist_materialmass_*_Steel.csv")) |
        set(MAT_HIST_DIR.glob("hist_materialmass_*_steel.csv"))
    )

    print(f"\nFound {len(copper_csvs)} Copper histogram CSV(s)")
    print(f"Found {len(esteel_csvs)} Electrical Steel histogram CSV(s)")
    print(f"Found {len(ndfeb_csvs)} NdFeB histogram CSV(s)")
    print(f"Found {len(cfsteel_csvs)} Cast Fe Steel histogram CSV(s)")

    if not copper_csvs and not esteel_csvs and not ndfeb_csvs and not cfsteel_csvs:
        raise FileNotFoundError(
            f"No matching histogram CSVs found in {MAT_HIST_DIR}.\n"
            "Expected files matching:\n"
            "  hist_materialmass_*_Copper.csv\n"
            "  hist_materialmass_*_ElectricalSteel.csv  (or *_electrosteel.csv)\n"
            "  hist_materialmass_*_NdFeB.csv            (or *_ndfeb.csv)\n"
            "  hist_materialmass_*_CastFeSteel.csv      (or *_Steel.csv)"
        )

    summary_rows: list = []
    # Combined MC accumulator across all streams
    all_mc_accum: Dict[Tuple[str, str], Dict] = {}

    # ── Process Copper ───────────────────────────────────────────────────────
    if copper_csvs:
        print("\n" + "=" * 60)
        print("Processing COPPER stream...")
        mc = process_stream(copper_csvs, rng, "copper",
                            cu_grades, None, None, summary_rows)
        all_mc_accum.update(mc)

    # ── Process Electrical Steel ─────────────────────────────────────────────
    if esteel_csvs:
        print("\n" + "=" * 60)
        print("Processing ELECTRICAL STEEL stream...")
        mc = process_stream(esteel_csvs, rng, "esteel",
                            None, estl_grades, None, summary_rows)
        all_mc_accum.update(mc)

    # ── Process NdFeB ────────────────────────────────────────────────────────
    if ndfeb_csvs:
        print("\n" + "=" * 60)
        print("Processing NdFeB stream...")
        mc = process_stream(ndfeb_csvs, rng, "ndfeb",
                            None, None, ndfeb_grades, summary_rows)
        all_mc_accum.update(mc)

    # ── Process Cast Fe Steel ────────────────────────────────────────────────
    if cfsteel_csvs:
        print("\n" + "=" * 60)
        print("Processing CAST FE STEEL stream...")
        mc = process_stream(cfsteel_csvs, rng, "cfsteel",
                            None, None, None, summary_rows,
                            cfsteel_grades=cfsteel_grades)
        all_mc_accum.update(mc)

    # ── Grand totals per segment group (full MC) ─────────────────────────────
    if all_mc_accum:
        print("\n" + "=" * 60)
        print("Computing MC Grand Totals per segment group (AB / CD / EF)...")
        process_grand_totals(all_mc_accum, summary_rows)

    # ── Combined summary CSV ─────────────────────────────────────────────────
    df_sum = pd.DataFrame(summary_rows)
    for root in [CU_ROOT, ESTL_ROOT, NDFEB_ROOT, CFSTEEL_ROOT]:
        df_sum.to_csv(root / "summary_csv" / "elemental_summary.csv", index=False)

    print("\n" + "=" * 60)
    print("Done.")
    print(f"  Copper outputs       → {CU_ROOT}")
    print(f"  Electrical Steel out → {ESTL_ROOT}")
    print(f"  NdFeB outputs        → {NDFEB_ROOT}")
    print(f"  Cast Fe Steel out    → {CFSTEEL_ROOT}")
    print(f"  Combined summary     → elemental_summary.csv (in all summary_csv folders)")


if __name__ == "__main__":
    main()
