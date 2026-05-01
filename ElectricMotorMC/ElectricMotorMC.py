#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.stats import gaussian_kde, spearmanr


# ────
# PATHS & DIRECTORIES
# ────
HERE      = Path(__file__).resolve().parent
DATA_DIR  = (HERE.parent / "Data").resolve()
XLSX_FILE = DATA_DIR / "05_VehicleElectricMotorsWeight.xlsx"

DIR_SUM      = HERE / "summary_csv"
DIR_SAMP     = HERE / "samples_csv"
DIR_HIST     = HERE / "histograms_csv"
DIR_DIST     = HERE / "distribution_figures"
DIR_SENS     = HERE / "sensitivity_figures"
DIR_MAT_SUM  = HERE / "materials_summary_csv"
DIR_MAT_SAMP = HERE / "materials_samples_csv"
DIR_MAT_HIST = HERE / "materials_histograms_csv"
DIR_MAT_FIG  = HERE / "materials_figures"
DIR_MAT_SENS = HERE / "materials_sensitivity_figures"

for d in [
    DIR_SUM, DIR_SAMP, DIR_HIST, DIR_DIST, DIR_SENS,
    DIR_MAT_SUM, DIR_MAT_SAMP, DIR_MAT_HIST, DIR_MAT_FIG, DIR_MAT_SENS,
]:
    d.mkdir(parents=True, exist_ok=True)


# ────
# SETTINGS
# ────
N_SAMPLES = 200_000
RNG_SEED  = 42
HIST_BINS = 140
TOP_N_MAT = 8

SEGMENT_GROUPS = {
    "AB": ("A", "B"),
    "CD": ("C", "D"),
    "EF": ("E", "F"),
}

MOTOR_CONFIGS = {
    "SmallStepperMotors": {
        "count_col":    "SmallStepperMotors",
        "gb_type":      "stepper",
        "mass_row":     "SmallStepperMotors",
        "mat_sheet":    "SmallStepperMotors",
        "housing_type": "SmallStepper",
    },
    "MediumStepperMotors": {
        "count_col":    "MediumStepperMotors",
        "gb_type":      "stepper",
        "mass_row":     "MediumStepperMotors",
        "mat_sheet":    "MediumStepperMotors",
        "housing_type": "MediumStepper",
    },
    "MediumDCMotors_metal": {
        "count_col":    "MediumDCMotors",
        "gb_type":      "dc_metal",
        "mass_row":     "MediumDCMotors_metal",
        "mat_sheet":    "MediumDCMotors_metal",
        "housing_type": "MediumDC",
    },
    "MediumDCMotors_plastic": {
        "count_col":    "MediumDCMotors",
        "gb_type":      "dc_plastic",
        "mass_row":     "MediumDCMotors_plastic",
        "mat_sheet":    "MediumDCMotors_plastic",
        "housing_type": "MediumDC",
    },
}

MOTOR_ORDER = [
    "SmallStepperMotors",
    "MediumStepperMotors",
    "MediumDCMotors_metal",
    "MediumDCMotors_plastic",
]

COLORS = {
    "SmallStepperMotors":     "#4C72B0",
    "MediumStepperMotors":    "#DD8452",
    "MediumDCMotors_metal":   "#55A868",
    "MediumDCMotors_plastic": "#C44E52",
}

SEG_COLORS        = {"AB": "#2196F3", "CD": "#FF9800", "EF": "#4CAF50"}
GRAND_TOTAL_COLOR = "#2222"

_TOTAL_COMPONENTS = {"total_motor", "total_gearbox"}


# ────
# HELPERS
# ────
def _norm(s: str) -> str:
    return "".join(str(s).strip().lower().split())


def _find_col(df: pd.DataFrame, desired: str) -> str:
    desired_n = _norm(desired)
    for c in df.columns:
        if _norm(c) == desired_n:
            return c
    raise KeyError(f"Column not found: '{desired}'. Available: {list(df.columns)}")


def uniform(rng: np.random.Generator, low: float, high: float, n: int) -> np.ndarray:
    if low == high:
        return np.full(n, low, dtype=float)
    return rng.uniform(low, high, size=n)


def triangular_safe(
    rng: np.random.Generator, lo: float, mode: float, hi: float, n: int
) -> np.ndarray:
    lo, hi = min(lo, hi), max(lo, hi)
    mode   = np.clip(mode, lo, hi)
    if lo == hi:
        return np.full(n, lo, dtype=float)
    return rng.triangular(lo, mode, hi, size=n)


def kde_mode(x: np.ndarray, grid_points: int = 1024) -> float:
    """Estimate the mode of a sample via KDE peak."""
    if np.std(x) < 1e-12:
        return float(x[0])
    kde  = gaussian_kde(x)
    grid = np.linspace(x.min(), x.max(), grid_points)
    return float(grid[np.argmax(kde(grid))])


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
    if np.std(x) < 1e-12:
        return
    kde  = gaussian_kde(x)
    grid = np.linspace(x.min(), x.max(), 500)
    ax.plot(grid, kde(grid), color=color, linewidth=2)


def lighten_color(color: str, amount: float = 0.5) -> tuple:
    import matplotlib.colors as mc
    import colorsys
    c = colorsys.rgb_to_hls(*mc.to_rgb(color))
    return colorsys.hls_to_rgb(c[0], 1 - amount * (1 - c[1]), c[2])


def safe_name(s: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in str(s))


def aggregate_duplicate_materials(
    materials: List[str],
    material_mass_kg: np.ndarray,
    ratios: np.ndarray,
) -> Tuple[List[str], np.ndarray, np.ndarray]:
    seen: Dict[str, int] = {}
    unique_mats: List[str] = []
    agg_mass_cols: List[np.ndarray] = []
    agg_ratio_cols: List[np.ndarray] = []

    for j, mat in enumerate(materials):
        if mat in seen:
            idx = seen[mat]
            agg_mass_cols[idx]  = agg_mass_cols[idx]  + material_mass_kg[:, j]
            agg_ratio_cols[idx] = agg_ratio_cols[idx] + ratios[:, j]
        else:
            seen[mat] = len(unique_mats)
            unique_mats.append(mat)
            agg_mass_cols.append(material_mass_kg[:, j].copy())
            agg_ratio_cols.append(ratios[:, j].copy())

    return (
        unique_mats,
        np.column_stack(agg_mass_cols),
        np.column_stack(agg_ratio_cols),
    )


# ────
# READ EXCEL SHEETS
# ────
def read_number_motors(xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(xlsx, sheet_name="NumberMotors")
    df.columns = [c.strip() for c in df.columns]
    return df


def read_mass_sheet(xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(xlsx, sheet_name="Mass")
    df.columns = [c.strip() for c in df.columns]
    return df


def read_material_sheet(xlsx: Path, sheet_name: str) -> pd.DataFrame:
    df = pd.read_excel(xlsx, sheet_name=sheet_name)
    df.columns = [c.strip() for c in df.columns]

    comp_col = _find_col(df, "component")
    mat_col  = _find_col(df, "material")
    low_col  = _find_col(df, "low")
    mode_col = _find_col(df, "mode")
    high_col = _find_col(df, "high")

    out = df[[comp_col, mat_col, low_col, mode_col, high_col]].copy()
    out.columns = ["component", "material", "low", "mode", "high"]

    out["component"] = out["component"].astype(str).str.strip()
    out["material"]  = out["material"].astype(str).str.strip()

    out = out[~out["component"].str.lower().isin(_TOTAL_COMPONENTS)].copy()
    out = out[out["material"].str.lower() != "nan"].copy()
    out = out[out["material"].str.len() > 0].copy()

    for c in ["low", "mode", "high"]:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    out = out.dropna(subset=["low", "mode", "high"]).reset_index(drop=True)
    return out


def read_housing_sheet(xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(xlsx, sheet_name="Housing")
    df.columns = [c.strip() for c in df.columns]
    seg_col = _find_col(df, "Segment")
    mt_col  = _find_col(df, "MotorType")
    df[seg_col] = df[seg_col].astype(str).str.strip().str.upper()
    df[mt_col]  = df[mt_col].astype(str).str.strip()
    return df


# ────
# HOUSING Al/Fe FRACTION SAMPLING
# ────
def sample_housing_fractions(
    df_housing: pd.DataFrame,
    seg_group: Tuple[str, str],
    housing_type: str,
    rng: np.random.Generator,
    n: int,
) -> Tuple[np.ndarray, np.ndarray]:
    seg_col    = _find_col(df_housing, "Segment")
    mt_col     = _find_col(df_housing, "MotorType")
    al_min_col = _find_col(df_housing, "MotorAl_min")
    al_max_col = _find_col(df_housing, "MotorAl_max")
    fe_min_col = _find_col(df_housing, "MotorFe_min")
    fe_max_col = _find_col(df_housing, "MotorFe_max")

    seg_a, seg_b = seg_group
    ht_norm = housing_type.lower()
    mask_mt = df_housing[mt_col].str.lower().str.contains(ht_norm, na=False)

    al_samples  = np.zeros(n, dtype=float)
    fe_samples  = np.zeros(n, dtype=float)
    n_rows_used = 0

    for seg_letter in (seg_a, seg_b):
        mask_seg = df_housing[seg_col] == seg_letter.upper()
        rows = df_housing[mask_mt & mask_seg]
        if rows.empty:
            continue
        row   = rows.iloc[0]
        al_lo = float(row[al_min_col])
        al_hi = float(row[al_max_col])
        fe_lo = float(row[fe_min_col])
        fe_hi = float(row[fe_max_col])

        if al_lo > al_hi:
            al_lo, al_hi = al_hi, al_lo
        if fe_lo > fe_hi:
            fe_lo, fe_hi = fe_hi, fe_lo

        al_samples += uniform(rng, al_lo, al_hi, n)
        fe_samples += uniform(rng, fe_lo, fe_hi, n)
        n_rows_used += 1

    if n_rows_used == 0:
        raise ValueError(
            f"No Housing rows found for motor type '{housing_type}' "
            f"in segments {seg_a}/{seg_b}."
        )

    al_samples /= n_rows_used
    fe_samples /= n_rows_used

    total = al_samples + fe_samples
    total[total == 0] = 1.0
    return al_samples / total, fe_samples / total


def sample_gearbox_housing_fractions(
    df_housing: pd.DataFrame,
    seg_group: Tuple[str, str],
    housing_type: str,
    rng: np.random.Generator,
    n: int,
) -> Tuple[np.ndarray, np.ndarray]:
    seg_col    = _find_col(df_housing, "Segment")
    mt_col     = _find_col(df_housing, "MotorType")
    al_min_col = _find_col(df_housing, "GearboxAl_min")
    al_max_col = _find_col(df_housing, "GearboxAl_max")
    fe_min_col = _find_col(df_housing, "GearboxFe_min")
    fe_max_col = _find_col(df_housing, "GearboxFe_max")

    seg_a, seg_b = seg_group
    ht_norm = housing_type.lower()
    mask_mt = df_housing[mt_col].str.lower().str.contains(ht_norm, na=False)

    al_samples  = np.zeros(n, dtype=float)
    fe_samples  = np.zeros(n, dtype=float)
    n_rows_used = 0

    for seg_letter in (seg_a, seg_b):
        mask_seg = df_housing[seg_col] == seg_letter.upper()
        rows = df_housing[mask_mt & mask_seg]
        if rows.empty:
            continue
        row   = rows.iloc[0]
        al_lo = float(row[al_min_col])
        al_hi = float(row[al_max_col])
        fe_lo = float(row[fe_min_col])
        fe_hi = float(row[fe_max_col])

        if al_lo > al_hi:
            al_lo, al_hi = al_hi, al_lo
        if fe_lo > fe_hi:
            fe_lo, fe_hi = fe_hi, fe_lo

        al_samples += uniform(rng, al_lo, al_hi, n)
        fe_samples += uniform(rng, fe_lo, fe_hi, n)
        n_rows_used += 1

    if n_rows_used == 0:
        raise ValueError(
            f"No Housing rows found for motor type '{housing_type}' "
            f"in segments {seg_a}/{seg_b} (Gearbox columns)."
        )

    al_samples /= n_rows_used
    fe_samples /= n_rows_used

    total = al_samples + fe_samples
    total[total == 0] = 1.0
    return al_samples / total, fe_samples / total


# ────
# MOTOR COUNT SAMPLING
# ────
def sample_motor_counts(
    df_num: pd.DataFrame,
    seg_group: Tuple[str, str],
    count_col: str,
    rng: np.random.Generator,
    n: int,
) -> np.ndarray:
    seg_col  = _find_col(df_num, "Segment")
    low_col  = _find_col(df_num, f"{count_col}_low")
    high_col = _find_col(df_num, f"{count_col}_high")

    seg_a, seg_b = seg_group
    rows_a = df_num[df_num[seg_col].astype(str).str.strip().str.upper() == seg_a.upper()]
    rows_b = df_num[df_num[seg_col].astype(str).str.strip().str.upper() == seg_b.upper()]

    total       = np.zeros(n, dtype=float)
    max_len     = max(len(rows_a), len(rows_b))
    rows_a_list = list(rows_a.itertuples())
    rows_b_list = list(rows_b.itertuples())

    for i in range(max_len):
        for rows_list in [rows_a_list, rows_b_list]:
            if i < len(rows_list):
                row = rows_list[i]
                lo  = float(getattr(row, low_col.replace(" ", "_")))
                hi  = float(getattr(row, high_col.replace(" ", "_")))
                if hi > 0:
                    total += uniform(rng, lo, hi, n)

    return total


# ────
# GEARBOX PROBABILITY SAMPLING
# ────
def sample_gearbox_probability(
    df_num: pd.DataFrame,
    rng: np.random.Generator,
    n: int,
) -> np.ndarray:
    low_col  = _find_col(df_num, "Gearbox_low")
    high_col = _find_col(df_num, "Gearbox_high")
    valid = df_num[[low_col, high_col]].dropna()
    if valid.empty:
        raise ValueError("No valid Gearbox_low / Gearbox_high rows in NumberMotors sheet")
    lo = float(valid.iloc[0][low_col])
    hi = float(valid.iloc[0][high_col])
    return uniform(rng, lo, hi, n)


# ────
# MASS LOOKUP
# ────
def get_mass_params(df_mass: pd.DataFrame, motor_type: str, gearbox_type: str = "metal") -> dict:
    mt_col = _find_col(df_mass, "MotorType")
    df_mass["_mt_norm"] = df_mass[mt_col].astype(str).str.strip().str.lower()

    target = motor_type.lower()
    rows   = df_mass[df_mass["_mt_norm"].str.contains(target, na=False)]

    if rows.empty:
        raise KeyError(
            f"Motor type '{motor_type}' not found in Mass sheet. "
            f"Available: {df_mass[mt_col].tolist()}"
        )

    if len(rows) > 1:
        gb_col_name = _find_col(df_mass, "GearboxType") if any(
            _norm(c) == "gearboxtype" for c in df_mass.columns
        ) else None
        if gb_col_name:
            rows = rows[rows[gb_col_name].astype(str).str.lower().str.contains(gearbox_type.lower())]
        else:
            rows = rows.iloc[[0]] if gearbox_type == "metal" else rows.iloc[[1]]

    row = rows.iloc[0]

    def gcol(name):
        return float(row[_find_col(df_mass, name)])

    return {
        "motor_low":  gcol("MotorMassLow_g"),
        "motor_high": gcol("MotorMassHigh_g"),
        "gb_low":     gcol("GearboxMassLow_g"),
        "gb_high":    gcol("GearboxMassHigh_g"),
    }


# ────
# MATERIAL RATIO SAMPLING  — triangular distribution
# ────
def sample_material_ratios(
    comp_df: pd.DataFrame,
    rng: np.random.Generator,
    n: int,
) -> Tuple[List[str], np.ndarray]:
    materials = comp_df["material"].tolist()
    lo   = comp_df["low"].to_numpy(float)
    mode = comp_df["mode"].to_numpy(float)
    hi   = comp_df["high"].to_numpy(float)

    raw = np.column_stack([
        triangular_safe(rng, lo[i], mode[i], hi[i], n)
        for i in range(len(materials))
    ])
    row_sums = raw.sum(axis=1)
    row_sums[row_sums == 0] = 1.0
    return materials, raw / row_sums[:, None]


# ────
# HOUSING SPLIT
# ────
def split_housing_in_materials(
    comp_df: pd.DataFrame,
    materials: List[str],
    ratios: np.ndarray,
    al_frac: np.ndarray,
    fe_frac: np.ndarray,
) -> Tuple[List[str], np.ndarray]:
    hf_mask = (
        (comp_df["component"].str.lower() == "housingframe")
        & (comp_df["material"].str.lower() == "aluminum_steel")
    )
    hf_indices = comp_df.index[hf_mask].tolist()

    if not hf_indices:
        return materials, ratios

    hf_idx = hf_indices[0]

    new_materials: List[str] = []
    new_cols: List[np.ndarray] = []

    for i, mat in enumerate(materials):
        if i == hf_idx:
            new_materials.append("Aluminum")
            new_cols.append(ratios[:, i] * al_frac)
            new_materials.append("Steel")
            new_cols.append(ratios[:, i] * fe_frac)
        else:
            new_materials.append(mat)
            new_cols.append(ratios[:, i])

    new_ratios = np.column_stack(new_cols)
    return new_materials, new_ratios


def split_gearbox_housing_in_materials(
    materials: List[str],
    ratios: np.ndarray,
    gb_al_frac: np.ndarray,
    gb_fe_frac: np.ndarray,
) -> Tuple[List[str], np.ndarray]:
    gb_idx = None
    for i, mat in enumerate(materials):
        if mat.lower() == "aluminum_steel":
            gb_idx = i
            break

    if gb_idx is None:
        return materials, ratios

    new_materials: List[str] = []
    new_cols: List[np.ndarray] = []

    for i, mat in enumerate(materials):
        if i == gb_idx:
            new_materials.append("Aluminum")
            new_cols.append(ratios[:, i] * gb_al_frac)
            new_materials.append("Steel")
            new_cols.append(ratios[:, i] * gb_fe_frac)
        else:
            new_materials.append(mat)
            new_cols.append(ratios[:, i])

    new_ratios = np.column_stack(new_cols)
    return new_materials, new_ratios


# ────
# FIGURES — segment overview
# ────
def save_distribution_plot(
    segment: str,
    results: Dict[str, Dict[str, np.ndarray]],
) -> None:
    n_motors = len(MOTOR_ORDER)
    fig = plt.figure(figsize=(6 * n_motors, 10))
    fig.suptitle(f"Monte Carlo Distributions — {segment}", fontsize=16, fontweight="bold")
    gs  = gridspec.GridSpec(2, n_motors, figure=fig, hspace=0.35, wspace=0.25)

    for col, motor in enumerate(MOTOR_ORDER):
        color      = COLORS[motor]
        count_data = results[motor]["count"]
        mass_data  = results[motor]["mass"]

        for row, (data, label, unit) in enumerate([
            (count_data, "Motor Count", "motors"),
            (mass_data,  "Total Mass",  "kg"),
        ]):
            ax = fig.add_subplot(gs[row, col])
            ax.hist(data, bins=80, density=True, alpha=0.4, color=color, edgecolor="none")
            add_kde(ax, data, color)
            for p, ls in [(0.025, "--"), (0.50, "-"), (0.975, "--")]:
                ax.axvline(np.quantile(data, p), color="black", linestyle=ls, alpha=0.7)
            ax.axvline(np.mean(data), color="red", linestyle=":", linewidth=2)
            ax.set_title(f"{motor}\n({label})", fontsize=11, fontweight="bold")
            ax.set_xlabel(f"[{unit}]")
            ax.set_ylabel("Density")

    fig.savefig(DIR_DIST / f"distribution_{segment}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


# ────
# FIGURES — grand total distributions per segment
# ────
def save_grand_total_distribution_plot(
    segment: str,
    grand_count: np.ndarray,
    grand_mass: np.ndarray,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(f"Grand Total Distributions — {segment}", fontsize=15, fontweight="bold")
    color = SEG_COLORS.get(segment, GRAND_TOTAL_COLOR)

    for ax, data, label, unit in [
        (axes[0], grand_count, "Grand Total Count", "motors"),
        (axes[1], grand_mass,  "Grand Total Mass",  "kg"),
    ]:
        ax.hist(data, bins=100, density=True, alpha=0.4, color=color, edgecolor="none")
        add_kde(ax, data, color)
        for p, ls in [(0.025, "--"), (0.50, "-"), (0.975, "--")]:
            ax.axvline(np.quantile(data, p), color="black", linestyle=ls, alpha=0.7)
        ax.axvline(np.mean(data), color="red", linestyle=":", linewidth=2)
        ax.set_title(label, fontsize=12, fontweight="bold")
        ax.set_xlabel(f"[{unit}]")
        ax.set_ylabel("Density")

    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.savefig(DIR_DIST / f"distribution_grandtotal_{segment}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


# ────
# FIGURES — cross-segment grand total comparison
# ────
def save_grand_total_distribution_plots(
    grand_totals: Dict[str, Dict[str, np.ndarray]],
) -> None:
    for qty, label, unit, fname in [
        ("count", "Grand Total Count", "motors", "distribution_grandtotal_count_all_segments.png"),
        ("mass",  "Grand Total Mass",  "kg",     "distribution_grandtotal_mass_all_segments.png"),
    ]:
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.suptitle(f"{label} — All Segments", fontsize=14, fontweight="bold")

        for seg, color in SEG_COLORS.items():
            data = grand_totals[seg][qty]
            ax.hist(data, bins=100, density=True, alpha=0.25, color=color, edgecolor="none")
            add_kde(ax, data, color)
            for p, ls in [(0.025, "--"), (0.975, "--")]:
                ax.axvline(np.quantile(data, p), color=color, linestyle=ls, alpha=0.6)
            ax.axvline(np.mean(data), color=color, linestyle=":", linewidth=2,
                    label=f"{seg}  μ={np.mean(data):.1f}")

        ax.set_xlabel(f"[{unit}]")
        ax.set_ylabel("Density")
        ax.legend(fontsize=11)
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        fig.savefig(DIR_DIST / fname, dpi=200, bbox_inches="tight")
        plt.close(fig)


# ────
# FIGURES — sensitivity panel
# ────
def save_sensitivity_panel(
    segment: str,
    sens_data: Dict[str, Dict[str, float]],
) -> None:
    n_motors = len(MOTOR_ORDER)
    fig, axes = plt.subplots(1, n_motors, figsize=(5 * n_motors, 5), sharey=True)
    fig.suptitle(f"Sensitivity — {segment} (Total Mass)", fontsize=14, fontweight="bold")

    for ax, motor in zip(axes, MOTOR_ORDER):
        stats = sens_data[motor]
        base  = COLORS[motor]
        light = lighten_color(base, 0.45)
        labels = ["Motor Count", "Unit Mass"]
        corrs  = [abs(stats["rho_n"]), abs(stats["rho_m"])]
        shares = [stats["share_n"],    stats["share_m"]]

        for i, (label, val, clr) in enumerate(zip(labels, corrs, [base, light])):
            ax.barh(label, val, color=clr, alpha=0.9)
            ax.text(
                val + 0.02, i,
                f"ρ={val:.2f}\n{shares[i]*100:.1f}%",
                va="center", fontsize=10, fontweight="bold",
            )

        ax.set_xlim(0, 1.15)
        ax.set_title(motor, fontsize=11, fontweight="bold")
        ax.set_xlabel("|Spearman ρ|")

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.savefig(DIR_SENS / f"sensitivity_{segment}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


# ────
# FIGURES — material distributions
# ────
def save_material_distribution_figure(
    segment: str,
    motor: str,
    materials: List[str],
    material_mass_kg: np.ndarray,
) -> None:
    mean_mass = material_mass_kg.mean(axis=0)
    order     = np.argsort(mean_mass)[::-1][:min(TOP_N_MAT, len(materials))]
    mats      = [materials[i] for i in order]
    data      = material_mass_kg[:, order]
    n         = len(mats)
    base      = COLORS[motor]

    ncols = 4
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(18, 4.2 * nrows))
    axes = np.atleast_1d(axes).reshape(nrows, ncols)
    fig.suptitle(
        f"Material Mass Distributions — {segment} / {motor}",
        fontsize=15, fontweight="bold",
    )

    for idx in range(nrows * ncols):
        ax = axes[idx // ncols, idx % ncols]
        if idx >= n:
            ax.axis("off")
            continue
        x = data[:, idx]
        ax.hist(x, bins=80, density=True, alpha=0.35, color=base, edgecolor="none")
        add_kde(ax, x, base)
        for p, ls in [(0.025, "--"), (0.50, "-"), (0.975, "--")]:
            ax.axvline(np.quantile(x, p), color="black", linestyle=ls, alpha=0.7)
        ax.axvline(np.mean(x), color="red", linestyle=":", linewidth=2)
        ax.set_title(mats[idx], fontsize=11, fontweight="bold")
        ax.set_xlabel("[kg]")
        ax.set_ylabel("Density")

    fig.tight_layout(rect=[0, 0.03, 1, 0.94])
    fig.savefig(
        DIR_MAT_FIG / f"materials_distribution_{segment}_{motor}.png",
        dpi=220, bbox_inches="tight",
    )
    plt.close(fig)


# ────
# FIGURES — grand total material distribution per segment
# ────
def save_grand_total_material_figure(
    segment: str,
    materials: List[str],
    material_mass_kg: np.ndarray,
) -> None:
    mean_mass = material_mass_kg.mean(axis=0)
    order     = np.argsort(mean_mass)[::-1][:min(TOP_N_MAT, len(materials))]
    mats      = [materials[i] for i in order]
    data      = material_mass_kg[:, order]
    n         = len(mats)
    color     = SEG_COLORS.get(segment, GRAND_TOTAL_COLOR)

    ncols = 4
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(18, 4.2 * nrows))
    axes = np.atleast_1d(axes).reshape(nrows, ncols)
    fig.suptitle(
        f"Grand Total Material Distributions — {segment}",
        fontsize=15, fontweight="bold",
    )

    for idx in range(nrows * ncols):
        ax = axes[idx // ncols, idx % ncols]
        if idx >= n:
            ax.axis("off")
            continue
        x = data[:, idx]
        ax.hist(x, bins=80, density=True, alpha=0.35, color=color, edgecolor="none")
        add_kde(ax, x, color)
        for p, ls in [(0.025, "--"), (0.50, "-"), (0.975, "--")]:
            ax.axvline(np.quantile(x, p), color="black", linestyle=ls, alpha=0.7)
        ax.axvline(np.mean(x), color="red", linestyle=":", linewidth=2)
        ax.set_title(mats[idx], fontsize=11, fontweight="bold")
        ax.set_xlabel("[kg]")
        ax.set_ylabel("Density")

    fig.tight_layout(rect=[0, 0.03, 1, 0.94])
    fig.savefig(
        DIR_MAT_FIG / f"materials_distribution_{segment}_GrandTotal.png",
        dpi=220, bbox_inches="tight",
    )
    plt.close(fig)


# ────
# FIGURES — material sensitivity heatmap
# ────
def save_material_sensitivity_heatmap(
    segment: str,
    motor: str,
    materials: List[str],
    total_count: np.ndarray,
    unit_mass_g: np.ndarray,
    ratios: np.ndarray,
    material_mass_kg: np.ndarray,
) -> None:
    mean_mass = material_mass_kg.mean(axis=0)
    order     = np.argsort(mean_mass)[::-1][:min(TOP_N_MAT, len(materials))]
    mats      = [materials[i] for i in order]

    drivers = ["Total Count", "Unit Mass", "Material Ratio"]
    H       = np.zeros((3, len(order)), dtype=float)
    for j, i in enumerate(order):
        y        = material_mass_kg[:, i]
        H[0, j]  = abs(spearmanr(total_count,  y).statistic)
        H[1, j]  = abs(spearmanr(unit_mass_g,  y).statistic)
        H[2, j]  = abs(spearmanr(ratios[:, i], y).statistic)

    fig, ax = plt.subplots(figsize=(2.2 + 1.25 * len(order), 3.2))
    im = ax.imshow(H, vmin=0, vmax=1, aspect="auto")
    ax.set_yticks(np.arange(3))
    ax.set_yticklabels(drivers, fontsize=11)
    ax.set_xticks(np.arange(len(order)))
    ax.set_xticklabels(mats, rotation=45, ha="right", fontsize=10)
    ax.set_title(
        f"Material Sensitivity (|Spearman ρ|) — {segment} / {motor}",
        fontsize=12, fontweight="bold",
    )
    for r in range(H.shape[0]):
        for c in range(H.shape[1]):
            ax.text(c, r, f"{H[r,c]:.2f}", ha="center", va="center", fontsize=9)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04).set_label("|Spearman ρ|")
    fig.tight_layout()
    fig.savefig(
        DIR_MAT_SENS / f"materials_sensitivity_{segment}_{motor}.png",
        dpi=220, bbox_inches="tight",
    )
    plt.close(fig)


# ────
# HELPER — export material outputs
# ────
def _export_material_outputs(
    seg_group: str,
    motor: str,
    materials: List[str],
    ratios: np.ndarray,
    material_mass_kg: np.ndarray,
    total_count: np.ndarray,
    unit_mass_g: np.ndarray,
    mat_summary_rows: list,
) -> None:
    total_mass_kg = material_mass_kg.sum(axis=1)

    mat_df = pd.DataFrame({"total_mass_kg": total_mass_kg})
    for j, mat in enumerate(materials):
        mat_df[f"ratio__{mat}"]   = ratios[:, j]
        mat_df[f"mass_kg__{mat}"] = material_mass_kg[:, j]
    mat_df.to_csv(
        DIR_MAT_SAMP / f"materials_samples_{seg_group}_{motor}.csv",
        index=False,
    )

    for j, mat in enumerate(materials):
        x = material_mass_kg[:, j]
        sn = safe_name(mat)
        export_histogram_csv(
            x,
            DIR_MAT_HIST / f"hist_materialmass_{seg_group}_{motor}_{sn}.csv",
        )
        mat_summary_rows.append({
            "Segment":       seg_group,
            "Motor":         motor,
            "Material":      mat,
            "Mean_mass_kg":  float(np.mean(x)),
            "Std_mass_kg":   float(np.std(x)),
            "Mode_mass_kg":  float(kde_mode(x)),
            "P025_mass_kg":  float(np.quantile(x, 0.025)),
            "Median_mass_kg":   float(np.quantile(x, 0.50)),
            "P975_mass_kg":  float(np.quantile(x, 0.975)),
            "Mean_ratio":    float(np.mean(ratios[:, j])),
        })


# ────
# MAIN
# ────
def main() -> None:
    if not XLSX_FILE.exists():
        raise FileNotFoundError(f"Excel file not found: {XLSX_FILE}")

    rng = np.random.default_rng(RNG_SEED)

    print("Reading Excel sheets...")
    df_num     = read_number_motors(XLSX_FILE)
    df_mass    = read_mass_sheet(XLSX_FILE)
    df_housing = read_housing_sheet(XLSX_FILE)

    KNOWN_MAT_SHEETS = {cfg["mat_sheet"] for cfg in MOTOR_CONFIGS.values()}
    mat_sheets: Dict[str, pd.DataFrame] = {}
    xls = pd.ExcelFile(XLSX_FILE)
    for sh in xls.sheet_names:
        if sh in KNOWN_MAT_SHEETS:
            mat_sheets[sh] = read_material_sheet(XLSX_FILE, sh)
            print(f"  Loaded material sheet: {sh}  ({len(mat_sheets[sh])} material rows)")

    summary_rows     = []
    mat_summary_rows = []
    grand_totals: Dict[str, Dict[str, np.ndarray]] = {}

    for seg_group, (seg_a, seg_b) in SEGMENT_GROUPS.items():
        print(f"\n{'='*60}")
        print(f"Segment group: {seg_group}  ({seg_a} + {seg_b})")

        dc_total_count = sample_motor_counts(
            df_num, (seg_a, seg_b), "MediumDCMotors", rng, N_SAMPLES
        )
        dc_gb_prob = sample_gearbox_probability(df_num, rng, N_SAMPLES)

        seg_results = {}
        seg_sens    = {}

        grand_count    = np.zeros(N_SAMPLES, dtype=float)
        grand_mass     = np.zeros(N_SAMPLES, dtype=float)
        grand_mat_dict: Dict[str, np.ndarray] = {}

        for motor, cfg in MOTOR_CONFIGS.items():
            print(f"  Motor: {motor}")
            gb_type = cfg["gb_type"]

            # ── 1. Motor count ────
            if gb_type == "stepper":
                total_count = sample_motor_counts(
                    df_num, (seg_a, seg_b), cfg["count_col"], rng, N_SAMPLES
                )
                gb_prob     = sample_gearbox_probability(df_num, rng, N_SAMPLES)
                has_gearbox = rng.random(N_SAMPLES) < gb_prob
            elif gb_type == "dc_metal":
                total_count = dc_total_count * dc_gb_prob * 0.5
                has_gearbox = np.ones(N_SAMPLES, dtype=bool)
            elif gb_type == "dc_plastic":
                total_count = dc_total_count * dc_gb_prob * 0.5
                has_gearbox = np.ones(N_SAMPLES, dtype=bool)

            # ── 2. Mass ────
            params       = get_mass_params(df_mass, cfg["mass_row"])
            motor_mass_g = uniform(rng, params["motor_low"],  params["motor_high"],  N_SAMPLES)
            gb_mass_g    = uniform(rng, params["gb_low"],     params["gb_high"],     N_SAMPLES)
            unit_mass_g  = motor_mass_g + np.where(has_gearbox, gb_mass_g, 0.0)

            # ── 3. Total mass ────
            total_mass_kg = (total_count * unit_mass_g) / 1000.0

            seg_results[motor] = {"count": total_count, "mass": total_mass_kg}
            grand_count += total_count
            grand_mass  += total_mass_kg

            # ── 4. Base exports ────
            pd.DataFrame({
                "count":         total_count,
                "unit_mass_g":   unit_mass_g,
                "total_mass_kg": total_mass_kg,
                "has_gearbox":   has_gearbox.astype(int),
            }).to_csv(DIR_SAMP / f"samples_{seg_group}_{motor}.csv", index=False)

            export_histogram_csv(total_count,   DIR_HIST / f"hist_{seg_group}_{motor}_count.csv")
            export_histogram_csv(total_mass_kg, DIR_HIST / f"hist_{seg_group}_{motor}_mass.csv")

            # ── 5. Sensitivity ────
            rho_n = spearmanr(total_count, total_mass_kg).statistic
            rho_m = spearmanr(unit_mass_g, total_mass_kg).statistic
            v_n, v_m = rho_n**2, rho_m**2
            denom = v_n + v_m if (v_n + v_m) > 0 else 1.0
            seg_sens[motor] = {
                "rho_n":   float(rho_n),
                "rho_m":   float(rho_m),
                "share_n": float(v_n / denom),
                "share_m": float(v_m / denom),
            }

            for qty, data in [("Count", total_count), ("Mass_kg", total_mass_kg)]:
                summary_rows.append({
                    "Segment":  seg_group,
                    "Motor":    motor,
                    "Quantity": qty,
                    "Mean": float(np.mean(data)),
                    "Std":  float(np.std(data)),
                    "Mode": float(kde_mode(data)),
                    "P025": float(np.quantile(data, 0.025)),
                    "Median":  float(np.quantile(data, 0.50)),
                    "P975": float(np.quantile(data, 0.975)),
                })

            # ── 6. Material composition ────
            sheet_name = cfg["mat_sheet"]
            if sheet_name not in mat_sheets:
                print(f"    WARNING: sheet '{sheet_name}' not found, skipping materials.")
            else:
                comp_df           = mat_sheets[sheet_name]
                materials, ratios = sample_material_ratios(comp_df, rng, N_SAMPLES)

                hf_mask = (
                    (comp_df["component"].str.lower() == "housingframe")
                    & (comp_df["material"].str.lower() == "aluminum_steel")
                )
                if hf_mask.any():
                    al_frac, fe_frac = sample_housing_fractions(
                        df_housing, (seg_a, seg_b), cfg["housing_type"], rng, N_SAMPLES
                    )
                    materials, ratios = split_housing_in_materials(
                        comp_df, materials, ratios, al_frac, fe_frac
                    )
                    print(f"    HousingFrame split applied: Aluminum_Steel → Aluminum + Steel")

                gb_hsg_mask = (
                    (comp_df["component"].str.lower() == "gearbox_housing")
                    & (comp_df["material"].str.lower() == "aluminum_steel")
                )
                if gb_hsg_mask.any():
                    gb_al_frac, gb_fe_frac = sample_gearbox_housing_fractions(
                        df_housing, (seg_a, seg_b), cfg["housing_type"], rng, N_SAMPLES
                    )
                    materials, ratios = split_gearbox_housing_in_materials(
                        materials, ratios, gb_al_frac, gb_fe_frac
                    )
                    print(f"    Gearbox_Housing split applied: Aluminum_Steel → Aluminum + Steel")

                material_mass_kg = total_mass_kg[:, None] * ratios

                materials, material_mass_kg, ratios = \
                    aggregate_duplicate_materials(materials, material_mass_kg, ratios)

                for j, mat in enumerate(materials):
                    if mat not in grand_mat_dict:
                        grand_mat_dict[mat] = np.zeros(N_SAMPLES, dtype=float)
                    grand_mat_dict[mat] += material_mass_kg[:, j]

                _export_material_outputs(
                    seg_group, motor, materials, ratios, material_mass_kg,
                    total_count, unit_mass_g, mat_summary_rows,
                )
                save_material_distribution_figure(seg_group, motor, materials, material_mass_kg)
                save_material_sensitivity_heatmap(
                    seg_group, motor, materials, total_count, unit_mass_g,
                    ratios, material_mass_kg,
                )

        # ── Segment-level figures ────
        save_distribution_plot(seg_group, seg_results)
        save_sensitivity_panel(seg_group, seg_sens)

        # ── Grand total figures & exports ────
        save_grand_total_distribution_plot(seg_group, grand_count, grand_mass)

        export_histogram_csv(grand_count, DIR_HIST / f"hist_{seg_group}_GrandTotal_count.csv")
        export_histogram_csv(grand_mass,  DIR_HIST / f"hist_{seg_group}_GrandTotal_mass.csv")

        for qty, data in [("Count", grand_count), ("Mass_kg", grand_mass)]:
            summary_rows.append({
                "Segment":  seg_group,
                "Motor":    "GrandTotal",
                "Quantity": qty,
                "Mean": float(np.mean(data)),
                "Std":  float(np.std(data)),
                "Mode": float(kde_mode(data)),
                "P025": float(np.quantile(data, 0.025)),
                "Median":  float(np.quantile(data, 0.50)),
                "P975": float(np.quantile(data, 0.975)),
            })

        if grand_mat_dict:
            gt_mat_names = list(grand_mat_dict.keys())
            gt_mat_array = np.column_stack([grand_mat_dict[m] for m in gt_mat_names])
            save_grand_total_material_figure(seg_group, gt_mat_names, gt_mat_array)

            for j, mat in enumerate(gt_mat_names):
                x = gt_mat_array[:, j]
                mat_summary_rows.append({
                    "Segment":       seg_group,
                    "Motor":         "GrandTotal",
                    "Material":      mat,
                    "Mean_mass_kg":  float(np.mean(x)),
                    "Std_mass_kg":   float(np.std(x)),
                    "Mode_mass_kg":  float(kde_mode(x)),
                    "P025_mass_kg":  float(np.quantile(x, 0.025)),
                    "Median_mass_kg":   float(np.quantile(x, 0.50)),
                    "P975_mass_kg":  float(np.quantile(x, 0.975)),
                    "Mean_ratio":    float(np.nan),
                })

        grand_totals[seg_group] = {"count": grand_count, "mass": grand_mass}

    # ── Cross-segment comparison figures ────
    save_grand_total_distribution_plots(grand_totals)

    # ── Summary CSVs ────
    pd.DataFrame(summary_rows).to_csv(DIR_SUM / "mc_simulation_summary.csv", index=False)
    pd.DataFrame(mat_summary_rows).to_csv(DIR_MAT_SUM / "materials_mc_summary.csv", index=False)

    print("\n" + "=" * 60)
    print("Done.")
    print(f"  Motor summary    → {DIR_SUM / 'mc_simulation_summary.csv'}")
    print(f"  Material summary → {DIR_MAT_SUM / 'materials_mc_summary.csv'}")
    print(f"  (Aluminum & Steel from housing split are included in the material summary above)")


if __name__ == "__main__":
    main()