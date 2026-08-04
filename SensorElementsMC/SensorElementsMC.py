"""
Monte Carlo Simulation for BEV Sensor Elemental Composition by Segment
Pure NumPy/Pandas implementation (mirrors the structure of PCBAreaMC.py / BEVSensorCountMC.py)

Two-stage model, combined per Monte Carlo draw:
  Stage 1 (sensor COUNT):  exactly reproduces BEVSensorCountMC.py -- for every
      (Domain, Component, SensorType) row, the rectangular [min,max] sensor-count
      range is scaled by the segment's Std/Opt/Rare presence factor for that
      Domain+Component, then a uniform draw is taken.
  Stage 2 (per-unit ELEMENT MASS): for every (SensorType, Element) pair with a
      nonzero max, a triangular [min, mode, max] draw (mg per sensor unit) is taken.
      Per the user's explicit instruction, each (Domain, Component, SensorType) row
      gets its OWN INDEPENDENT mass draw (not shared with other locations of the
      same SensorType).
  Combination: for a given draw index, row element mass = count_draw * mass_draw
      (same draw index for both -- i.e. paired/correlated draws, not resampled
      independently). Rows are then summed per Element to get total element mass
      per vehicle, per segment.

Inputs:
- Data/BEV_Electronics_Verified.xlsx       (all tabs; Std/Opt/Rare status, as before)
- Data/BEV_Sensor_Types_List-3.xlsx        (first tab only; sensor count ranges, as before)
- Data/07_VehicleSensorComposition.xlsx    (sheet 'Sensor Details'; per-unit element mass
                                             triangular distributions, mg per sensor)

Filtering rule (per user instruction): a (SensorType, Element) pair is only simulated
if that element's max_mg > 0 for that SensorType. In this dataset this means:
  - 'camera input' is dropped entirely (it is a signal reference, not physical hardware --
     Overall_Weight_Max_mg = 0 and every element max = 0 for that row).
  - Elements 'Sr' and 'Nb' have max_mg = 0 for every SensorType in this file and therefore
    produce no output at all (skipped silently, confirmed with user).
  - All other (SensorType, Element) zero-max combinations are simply not simulated --
    this is normal sparsity (most sensors don't contain most elements), not a data error.

Explicit element exclusion (per user instruction): O, N, C, P are fully excluded from the
Monte Carlo regardless of their data -- not simulated, no summary stats, no CSV rows, no
histograms, no figures. This is a stronger/different exclusion than the Sr/Nb case above:
O, N, C, and P DO have nonzero composition data in this file, they are excluded by explicit
request (not relevant for critical/strategic raw material reporting), not because the data
is empty.

Data cleaning notes (consistent with BEVSensorCountMC.py):
- Component names with non-breaking spaces (\xa0) are normalized.
- SensorType casing is normalized to lowercase before matching across files. This file
  contains an exact duplicate row pair ('Hall sensor' / 'hall sensor', identical in every
  numeric column) -- the duplicate is dropped defensively.
- Note for context: across all sensor types in this file, the 33 tracked elements only
  account for roughly 25-50% of a sensor's total weight at the mode (IQR); the remainder
  is untracked material (plastics, ceramics, housings, etc.) -- this is expected and does
  not indicate a data error.

Outputs:
- element_segment_comparison.png / .csv          (grand total per element, by segment)
- element_sensitivity_by_segment.png              (top SensorTypes by variance contribution, per element)
- element_monte_carlo_{ELEMENT}_{SEG}_segment.png (per element x segment, detail figure)
- element_sensortype_breakdown_{SEG}_segment.csv  (per SensorType x Element stats, per segment)
- csv_sensitivity/element_sensitivity_{ELEMENT}_{SEG}_segment.csv
- histograms/histogram_{SEG}_{ELEMENT}.csv  (50-bin histograms, total mass per element)
- raw_data/raw_distribution_{SEG}_elements.csv (raw per-draw element totals)
- distribution_index.csv (root)

Notes:
- ndraws = 200,000 per segment, fully vectorized.
- The sensor-count simulation is regenerated internally (not loaded from prior CSVs),
  using the identical model/logic as BEVSensorCountMC.py, so this script is self-contained.
"""

import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


# ============================================================================
# PATH HANDLING (ROBUST)
# ============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
DATA_DIR = BASE_DIR / "Data"

os.makedirs(SCRIPT_DIR / 'histograms', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'raw_data', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'figures_segment', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'figures_monte_carlo', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'figures_sensitivity', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'csv_segment', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'csv_monte_carlo', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'csv_sensitivity', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'csv_sensortype', exist_ok=True)

np.random.seed(42)

print("="*80)
print("LOADING DATA FILES")
print("="*80)
print(f"Script location: {SCRIPT_DIR}")
print(f"Base directory: {BASE_DIR}")
print(f"Data directory: {DATA_DIR}")

ELEC_FILE = DATA_DIR / '01_VehicleElectronics.xlsx'
SENSOR_FILE = DATA_DIR / '06_VehicleSensorNumbers.xlsx'
COMPOSITION_FILE = DATA_DIR / '07_VehicleSensorComposition.xlsx'

for f in (ELEC_FILE, SENSOR_FILE, COMPOSITION_FILE):
    if not f.exists():
        raise FileNotFoundError(f"Required file not found: {f}")


# ============================================================================
# TEXT NORMALIZATION HELPERS
# ============================================================================

def norm_text(s):
    """Normalize whitespace (incl. non-breaking spaces \xa0) without changing case."""
    s = str(s).replace('\xa0', ' ')
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def norm_key(s):
    """Lowercased normalized text, used purely for matching keys."""
    return norm_text(s).lower()


def safe_filename(s):
    """Make a name filesystem-safe."""
    s = re.sub(r'[^\w\-]+', '_', s)
    return s.strip('_')


SEG_COL = {'AB': 'A-B', 'CD': 'C-D', 'EF': 'E-F'}
segments = ['AB', 'CD', 'EF']
STATUS_FACTOR = {'Std': 1.0, 'Opt': 0.5, 'Rare': 0.25, '–': 0.0, '-': 0.0}
ndraws = 200000


# ============================================================================
# STAGE 1 DATA: SENSOR COUNT MODEL (identical to BEVSensorCountMC.py)
# ============================================================================

print(f"\nLoading electronics status file (all tabs)...")
xl_elec = pd.ExcelFile(ELEC_FILE)

status_frames = []
for sheet in xl_elec.sheet_names:
    df = pd.read_excel(xl_elec, sheet_name=sheet,
                        usecols=['Domain', 'Component', 'A-B Segment', 'C-D Segment', 'E-F Segment'])
    status_frames.append(df)
status_df = pd.concat(status_frames, ignore_index=True)

status_df['Domain'] = status_df['Domain'].map(norm_text)
status_df['Component'] = status_df['Component'].map(norm_text)
status_df['_key'] = status_df['Domain'].map(norm_key) + '||' + status_df['Component'].map(norm_key)

before_dedup = len(status_df)
status_df = status_df.drop_duplicates(
    subset=['_key', 'A-B Segment', 'C-D Segment', 'E-F Segment'], keep='first'
)
n_dropped = before_dedup - len(status_df)
if n_dropped:
    print(f"  Note: dropped {n_dropped} exact duplicate status row(s) (same Domain+Component+status).")

dup_keys = status_df['_key'][status_df['_key'].duplicated(keep=False)]
if len(dup_keys):
    print("  WARNING: Domain+Component combinations with multiple, DIFFERING status rows "
          "-- only the first is used:")
    for k in dup_keys.unique():
        print(f"    {k}")
    status_df = status_df.drop_duplicates(subset=['_key'], keep='first')

for seg, col in SEG_COL.items():
    seg_col_name = f'{col} Segment'
    status_df[f'factor_{seg}'] = status_df[seg_col_name].map(STATUS_FACTOR)
    unmapped = status_df[status_df[f'factor_{seg}'].isna()]
    if len(unmapped):
        raise ValueError(f"Unrecognized status value(s) in '{seg_col_name}': "
                          f"{unmapped[seg_col_name].unique().tolist()}")

print(f"  Loaded status for {len(status_df)} unique Domain+Component combinations.")

print(f"\nLoading sensor counts file (first tab only)...")
xl_sensor = pd.ExcelFile(SENSOR_FILE)
first_sheet = xl_sensor.sheet_names[0]
print(f"  Using sheet: '{first_sheet}'")

sensor_df = pd.read_excel(xl_sensor, sheet_name=first_sheet)
sensor_df['Domain'] = sensor_df['Domain'].map(norm_text)
sensor_df['Component'] = sensor_df['Component'].map(norm_text)
sensor_df['SensorType'] = sensor_df['SensorType'].map(norm_text).str.lower()
sensor_df['_key'] = sensor_df['Domain'].map(norm_key) + '||' + sensor_df['Component'].map(norm_key)

count_rows = sensor_df.merge(
    status_df[['_key', 'factor_AB', 'factor_CD', 'factor_EF']],
    on='_key', how='left'
)
unmatched = count_rows[count_rows['factor_AB'].isna()]
if len(unmatched):
    raise ValueError(
        "The following sensor rows have no matching Domain+Component status row:\n"
        + unmatched[['Domain', 'Component', 'SensorType']].to_string()
    )

count_rows = count_rows.reset_index(drop=True)
count_rows['_row_idx'] = np.arange(len(count_rows))
print(f"  Loaded {len(count_rows)} (Domain, Component, SensorType) count rows.")


# ============================================================================
# STAGE 2 DATA: ELEMENTAL COMPOSITION MODEL
# ============================================================================

print(f"\nLoading elemental composition file ('Sensor Details' sheet)...")
comp_df = pd.read_excel(COMPOSITION_FILE, sheet_name='Sensor Details')

ELEMENTS = ['Si', 'Cu', 'Ni', 'Fe', 'Mn', 'Co', 'Au', 'Ag', 'Pt', 'Al', 'Ga', 'As', 'In',
            'Pb', 'Zr', 'Ti', 'Nd', 'B', 'Dy', 'Ba', 'Sr', 'O', 'N', 'Sn', 'Ge', 'C', 'Li',
            'P', 'W', 'Ta', 'Cr', 'Zn', 'Nb']

required_cols = ['SensorType', 'Overall_Weight_Min_mg', 'Overall_Weight_Mode_mg', 'Overall_Weight_Max_mg']
for e in ELEMENTS:
    required_cols += [f'{e}_min_mg', f'{e}_mode_mg', f'{e}_max_mg']
missing_cols = [c for c in required_cols if c not in comp_df.columns]
if missing_cols:
    raise ValueError(f"Composition file is missing expected columns: {missing_cols}")

comp_df['SensorType_norm'] = comp_df['SensorType'].map(norm_text).str.lower()

# De-duplicate exact-duplicate SensorType rows (e.g. 'Hall sensor' / 'hall sensor').
before_comp_dedup = len(comp_df)
numeric_check_cols = [c for c in comp_df.columns if c.endswith('_mg')]
comp_df['_dupe_signature'] = comp_df[numeric_check_cols].astype(str).agg('|'.join, axis=1)
comp_df = comp_df.drop_duplicates(subset=['SensorType_norm', '_dupe_signature'], keep='first')
n_comp_dropped = before_comp_dedup - len(comp_df)
if n_comp_dropped:
    print(f"  Note: dropped {n_comp_dropped} exact duplicate composition row(s) "
          f"(same SensorType + identical mass values).")

dup_comp_keys = comp_df['SensorType_norm'][comp_df['SensorType_norm'].duplicated(keep=False)]
if len(dup_comp_keys):
    print("  WARNING: SensorTypes with multiple, DIFFERING composition rows "
          "-- only the first is used:")
    for k in dup_comp_keys.unique():
        print(f"    {k}")
    comp_df = comp_df.drop_duplicates(subset=['SensorType_norm'], keep='first')

# Validate triangular distribution constraints (min <= mode <= max) for every column triple.
def validate_triangular(df, min_col, mode_col, max_col, label):
    bad = df[~((df[min_col] <= df[mode_col]) & (df[mode_col] <= df[max_col]))]
    if len(bad):
        raise ValueError(f"Triangular distribution constraint (min<=mode<=max) violated for "
                          f"{label} in rows:\n{bad[['SensorType', min_col, mode_col, max_col]].to_string()}")

validate_triangular(comp_df, 'Overall_Weight_Min_mg', 'Overall_Weight_Mode_mg', 'Overall_Weight_Max_mg', 'Overall_Weight')
for e in ELEMENTS:
    validate_triangular(comp_df, f'{e}_min_mg', f'{e}_mode_mg', f'{e}_max_mg', e)

# Drop sensor types with zero overall max weight (per user instruction: only run/output
# if at least the max value is > 0). In this dataset this is 'camera input'.
zero_weight_types = comp_df.loc[comp_df['Overall_Weight_Max_mg'] <= 0, 'SensorType'].tolist()
if zero_weight_types:
    print(f"  Excluding sensor type(s) with zero max weight (per '>0' rule): {zero_weight_types}")
comp_df = comp_df[comp_df['Overall_Weight_Max_mg'] > 0].reset_index(drop=True)
comp_df = comp_df.set_index('SensorType_norm')

print(f"  {len(comp_df)} sensor types retained for elemental composition modeling.")

# Elements fully excluded from the Monte Carlo per explicit user instruction -- these are not
# simulated at all: no summary stats, no CSV rows, no histograms, no figures. This is a
# different (stronger) exclusion than skipping elements with zero max everywhere -- O, N, C, P
# DO have nonzero data in this file, they are excluded by request regardless of mass/relevance
# (e.g. not relevant for critical/strategic raw material reporting).
USER_EXCLUDED_ELEMENTS = {'O', 'N', 'C', 'P'}
print(f"  Excluding element(s) per explicit user instruction (not simulated at all): "
      f"{sorted(USER_EXCLUDED_ELEMENTS)}")

# Determine which elements have at least one sensor type with max > 0 -- elements that are
# zero everywhere (Sr, Nb in this dataset) are skipped entirely, confirmed with user.
active_elements = [e for e in ELEMENTS
                   if e not in USER_EXCLUDED_ELEMENTS and (comp_df[f'{e}_max_mg'] > 0).any()]
skipped_elements = [e for e in ELEMENTS
                     if e not in USER_EXCLUDED_ELEMENTS and e not in active_elements]
if skipped_elements:
    print(f"  Skipping element(s) with zero max across every sensor type: {skipped_elements}")
print(f"  {len(active_elements)} active elements: {', '.join(active_elements)}")

# Check coverage between count-side SensorTypes and composition-side SensorTypes.
count_types = set(count_rows['SensorType'].unique())
comp_types = set(comp_df.index)
no_composition = count_types - comp_types
if no_composition:
    print(f"\n  Note: {len(no_composition)} count-side SensorType(s) have no (nonzero) "
          f"composition match and will not contribute to element totals: {sorted(no_composition)}")


# ============================================================================
# MONTE CARLO SIMULATION - PER SEGMENT, PER ELEMENT
# ============================================================================

def approx_mode(x, bins=200):
    """Approximate mode for continuous data using the highest-count histogram bin."""
    counts, edges = np.histogram(x, bins=bins)
    i = np.argmax(counts)
    return 0.5 * (edges[i] + edges[i + 1])


### MEMORY NOTE ###
# With ~200 sensor-count rows x 200,000 draws x up to ~31 elements x 3 segments, keeping every
# raw per-draw array (count draws, mass draws, per-SensorType breakdowns) in memory at once would
# require several GB and risks an out-of-memory kill on modest hardware. To keep this robust on
# any machine, only ONE element is processed at a time per segment: the (n_rows, ndraws) count
# and mass matrices are created, combined, reduced to what's needed, and then discarded before
# moving to the next element. Only compact summary statistics are retained for every SensorType;
# the only full (ndraws,) arrays kept in memory afterward are the grand TOTAL per element per
# segment (needed for histograms/figures) -- a comparatively small and bounded amount of memory
# (n_elements x n_segments x ndraws).

all_segment_element_results = {}    # segment -> element -> 1D array (ndraws,) total mass (kept)
all_segment_sensortype_stats = {}   # segment -> element -> sensortype -> stats dict (kept, small)
all_sensitivity = {}                # segment -> element -> {'variance_contrib':..,'correlations':..} (kept, small)

for segment in segments:
    print("\n" + "="*70)
    print(f"RUNNING MONTE CARLO SIMULATION FOR {segment} SEGMENT")
    print("="*70)
    print(f"Number of simulations: {ndraws:,}")
    print(f"Number of (Domain, Component, SensorType) rows: {len(count_rows)}\n")

    element_results = {}
    sensortype_stats = {}
    sensitivity = {}

    for element in active_elements:
        mn_col, mo_col, mx_col = f'{element}_min_mg', f'{element}_mode_mg', f'{element}_max_mg'

        # Which SensorTypes have a nonzero max for this element?
        elem_valid_types = set(comp_df.index[comp_df[mx_col] > 0])
        row_mask = count_rows['SensorType'].isin(elem_valid_types).to_numpy()

        if not row_mask.any():
            continue  # should not happen given active_elements filter, but defensive

        sensor_types_for_rows = count_rows.loc[row_mask, 'SensorType'].to_numpy()
        n_active_rows = int(row_mask.sum())

        # Count draws for exactly the rows relevant to this element (not the full 196-row matrix).
        col_prefix = SEG_COL[segment]
        row_min = count_rows.loc[row_mask, f'{col_prefix}_Min'].to_numpy()[:, None]
        row_max = count_rows.loc[row_mask, f'{col_prefix}_Max'].to_numpy()[:, None]
        factor = count_rows.loc[row_mask, f'factor_{segment}'].to_numpy()[:, None]
        count_draws_e = np.random.uniform(row_min * factor, row_max * factor, size=(n_active_rows, ndraws))

        mn_vals = comp_df.loc[sensor_types_for_rows, mn_col].to_numpy()[:, None]
        mo_vals = comp_df.loc[sensor_types_for_rows, mo_col].to_numpy()[:, None]
        mx_vals = comp_df.loc[sensor_types_for_rows, mx_col].to_numpy()[:, None]

        # Independent triangular mass draw per (Domain, Component, SensorType) row,
        # per the user's explicit instruction (not shared across locations of the same type).
        mass_draws = np.random.triangular(mn_vals, mo_vals, mx_vals, size=(n_active_rows, ndraws))

        # Paired with the count draw at the SAME draw index (correlated, per user instruction).
        row_element_mass = count_draws_e * mass_draws
        del count_draws_e, mass_draws  # free promptly -- no longer needed once combined

        total_values = row_element_mass.sum(axis=0)
        element_results[element] = total_values
        total_var = np.var(total_values)

        # Per-SensorType breakdown: reduce to stats immediately, never retain the raw array.
        sensortype_stats[element] = {}
        variance_contrib = {}
        correlations = {}
        for st in sorted(set(sensor_types_for_rows)):
            st_row_mask = sensor_types_for_rows == st
            st_total = row_element_mass[st_row_mask, :].sum(axis=0)
            st_var = np.var(st_total)

            sensortype_stats[element][st] = {
                'mean': np.mean(st_total),
                'mode': approx_mode(st_total, bins=200) if st_var > 0 else float(st_total[0]),
                'median': np.percentile(st_total, 50),
                'std': np.std(st_total),
                'p025': np.percentile(st_total, 2.5),
                'p975': np.percentile(st_total, 97.5),
                'n_locations': int(st_row_mask.sum()),
            }
            variance_contrib[st] = st_var / total_var if total_var > 0 else np.nan
            correlations[st] = (np.corrcoef(st_total, total_values)[0, 1]
                                 if st_var > 0 else np.nan)
            del st_total

        sensitivity[element] = {'variance_contrib': variance_contrib, 'correlations': correlations}
        del row_element_mass  # free the (n_active_rows, ndraws) matrix before next element

    all_segment_element_results[segment] = element_results
    all_segment_sensortype_stats[segment] = sensortype_stats
    all_sensitivity[segment] = sensitivity

    print(f"{segment} Simulation complete! ({len(element_results)} elements simulated)")


# ============================================================================
# CALCULATE STATISTICS PER ELEMENT, PER SEGMENT
# ============================================================================

all_element_stats = {}

for segment in segments:
    element_results = all_segment_element_results[segment]
    stats = {}
    for element, values in element_results.items():
        stats[element] = {
            'mean': np.mean(values),
            'mode': approx_mode(values, bins=200),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'p025': np.percentile(values, 2.5),
            'p25': np.percentile(values, 25),
            'p50': np.percentile(values, 50),
            'p75': np.percentile(values, 75),
            'p975': np.percentile(values, 97.5)
        }
    all_element_stats[segment] = stats

    print("\n" + "="*70)
    print(f"MONTE CARLO SIMULATION RESULTS - {segment} SEGMENT (mg per vehicle)")
    print("="*70)

    for element in active_elements:
        if element not in stats:
            continue
        v = stats[element]
        print(f"\n{element}:")
        print(f"  Mean:   {v['mean']:>12.3f}")
        print(f"  Mode:   {v['mode']:>12.3f}")
        print(f"  Median: {v['p50']:>12.3f}")
        print(f"  Std:    {v['std']:>12.3f}")
        print(f"  Min:    {v['min']:>12.3f}")
        print(f"  P025:   {v['p025']:>12.3f}")
        print(f"  P25:    {v['p25']:>12.3f}")
        print(f"  P75:    {v['p75']:>12.3f}")
        print(f"  P975:   {v['p975']:>12.3f}")
        print(f"  Max:    {v['max']:>12.3f}")


# ============================================================================
# SEGMENT COMPARISON (per element)
# ============================================================================

print("\n" + "="*70)
print("SEGMENT COMPARISON (mean total mass per element, mg per vehicle)")
print("="*70)

comparison_rows = []
for element in active_elements:
    row = {'Element': element}
    for segment in segments:
        st = all_element_stats[segment].get(element)
        row[f'Mean_{segment}'] = st['mean'] if st else np.nan
        row[f'Std_{segment}'] = st['std'] if st else np.nan
        row[f'P025_{segment}'] = st['p025'] if st else np.nan
        row[f'P975_{segment}'] = st['p975'] if st else np.nan
    comparison_rows.append(row)

comparison_df = pd.DataFrame(comparison_rows).sort_values('Mean_EF', ascending=False)
print("\n", comparison_df[['Element', 'Mean_AB', 'Mean_CD', 'Mean_EF']].to_string(index=False))


# ============================================================================
# SENSITIVITY ANALYSIS SUMMARY (already computed during the main simulation loop)
# ============================================================================

print("\n" + "="*70)
print("SENSITIVITY ANALYSIS BY ELEMENT AND SEGMENT")
print("="*70)

for segment in segments:
    print(f"\n{segment} SEGMENT - Top SensorType by variance contribution, per element (top 10 elements by mass):")
    print("-" * 70)
    top_elements_by_mass = sorted(active_elements,
                                   key=lambda e: all_element_stats[segment].get(e, {}).get('mean', 0),
                                   reverse=True)[:10]
    for element in top_elements_by_mass:
        if element not in all_sensitivity[segment]:
            continue
        vc = all_sensitivity[segment][element]['variance_contrib']
        top_st = sorted(vc.items(), key=lambda kv: (kv[1] if kv[1] == kv[1] else -1), reverse=True)[:3]
        top_str = ", ".join(f"{st} ({v*100:.1f}%)" for st, v in top_st)
        print(f"  {element:3s}: {top_str}")


# ============================================================================
# CRITICAL & STRATEGIC ELEMENT CLASSIFICATION
# ============================================================================
# Per user instruction: drop Oxygen (O) from all figures entirely (still computed/saved in
# CSVs, just not plotted). Plot ALL remaining elements, with extra emphasis on elements
# classified as "critical" or "strategic" raw materials under the EU Critical Raw Materials
# Act (2023), plus two borderline cases the user asked to include: Zirconium (Zr, on the EU's
# previous 2020 list but dropped in 2023) and Indium (In, not on the EU list but flagged
# critical by other frameworks, e.g. US DOE/USGS, due to its use in ITO transparent conductors).
#
# This is a classification of the ELEMENT, independent of how much mass this dataset assigns
# to it -- a low-mass element like Co or Dy can still be "critical" due to supply risk, not
# tonnage. Iron (Fe) and Aluminium (Al) are NOT critical/strategic raw materials by this
# definition, but the user explicitly asked to keep them in the figures regardless (they are
# the dominant elements by mass and remain useful context).
#
# Note: Carbon (C) and Phosphorus (P) would also normally appear on this list, but both are
# in USER_EXCLUDED_ELEMENTS above and so never reach this point -- they are omitted here to
# keep this set an accurate reflection of what can actually appear in active_elements.

CRM_STRATEGIC_ELEMENTS = {
    'Al', 'As', 'B', 'Ba', 'Co', 'Cu', 'Dy', 'Ga', 'Ge', 'Li', 'Mn',
    'Nd', 'Ni', 'Pt', 'Si', 'Ta', 'Ti', 'W', 'Zr', 'In'
}

# O was previously excluded from figures only; it is now fully excluded upstream via
# USER_EXCLUDED_ELEMENTS, so active_elements already reflects every exclusion -- no further
# figure-only filtering is needed.
plot_elements = list(active_elements)
plot_elements_sorted_by_mass = sorted(plot_elements,
                                       key=lambda e: all_element_stats['EF'].get(e, {}).get('mean', 0),
                                       reverse=True)
critical_elements = [e for e in plot_elements_sorted_by_mass if e in CRM_STRATEGIC_ELEMENTS]
noncritical_elements = [e for e in plot_elements_sorted_by_mass if e not in CRM_STRATEGIC_ELEMENTS]

print(f"\nCritical/strategic elements ({len(critical_elements)}, by descending E-F mass): {critical_elements}")
print(f"Other elements ({len(noncritical_elements)}, by descending E-F mass): {noncritical_elements}")


# ============================================================================
# VISUALIZATIONS
# ============================================================================

print("\n" + "="*70)
print("GENERATING VISUALIZATIONS")
print("="*70)


def element_label(e):
    """Element symbol with a small marker for critical/strategic status, for plot labels."""
    return f"{e}*" if e in CRM_STRATEGIC_ELEMENTS else e


# ---- Figure 1: Segment comparison, ALL plotted elements (critical/strategic highlighted) ----
fig1, axes = plt.subplots(2, 1, figsize=(max(14, len(plot_elements_sorted_by_mass) * 0.45), 14))
fig1.suptitle('BEV Sensor Elemental Composition - All Elements by Segment\n'
              '(* = critical/strategic raw material, EU CRM Act 2023 + Zr/In)',
              fontsize=15, fontweight='bold')

ax1 = axes[0]
width = 0.25
x = np.arange(len(plot_elements_sorted_by_mass))
bar_colors_by_seg = ['#a6c8ff', '#7fae57', '#d96459']
for i, segment in enumerate(segments):
    vals = [all_element_stats[segment].get(e, {}).get('mean', 0) for e in plot_elements_sorted_by_mass]
    ax1.bar(x + (i - 1) * width, vals, width, label=f'{segment} Segment', color=bar_colors_by_seg[i])
ax1.set_xticks(x)
tick_labels = [element_label(e) for e in plot_elements_sorted_by_mass]
ax1.set_xticklabels(tick_labels, rotation=45, ha='right')
for tick, e in zip(ax1.get_xticklabels(), plot_elements_sorted_by_mass):
    if e in CRM_STRATEGIC_ELEMENTS:
        tick.set_fontweight('bold')
        tick.set_color('darkred')
ax1.set_ylabel('Mean Total Mass (mg per vehicle, log scale)')
ax1.set_title('All Elements, Sorted by E-F Mean Mass (descending)')
ax1.set_yscale('log')
ax1.legend()
ax1.grid(True, alpha=0.3, axis='y')

ax2 = axes[1]
x2 = np.arange(len(critical_elements))
for i, segment in enumerate(segments):
    vals = [all_element_stats[segment].get(e, {}).get('mean', 0) for e in critical_elements]
    ax2.bar(x2 + (i - 1) * width, vals, width, label=f'{segment} Segment', color=bar_colors_by_seg[i])
ax2.set_xticks(x2)
ax2.set_xticklabels(critical_elements, rotation=45, ha='right', fontweight='bold', color='darkred')
ax2.set_ylabel('Mean Total Mass (mg per vehicle, log scale)')
ax2.set_title('Critical / Strategic Elements Only, Sorted by E-F Mean Mass (descending)')
ax2.set_yscale('log')
ax2.legend()
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(SCRIPT_DIR / 'figures_segment' / 'element_segment_comparison.png', dpi=300, bbox_inches='tight')
print("✓ Saved: figures_segment/element_segment_comparison.png")


# ---- Figure 2: Overview grid -- ALL plotted elements, one small histogram panel each ----
# Two separate grids: critical/strategic elements first (the user's stated focus), then the
# remaining elements, so the critical-element grid can be scanned on its own.
def make_overview_grid(element_list, title, filename):
    if not element_list:
        return
    ncols = 5
    nrows = int(np.ceil(len(element_list) / ncols))
    fig, axes_grid = plt.subplots(nrows, ncols, figsize=(4 * ncols, 3 * nrows))
    fig.suptitle(title, fontsize=16, fontweight='bold')
    axes_flat = np.atleast_1d(axes_grid).flatten()

    for idx, element in enumerate(element_list):
        ax = axes_flat[idx]
        for segment, color in zip(segments, ['#a6c8ff', '#7fae57', '#d96459']):
            values = all_segment_element_results[segment].get(element)
            if values is not None:
                ax.hist(values, bins=40, alpha=0.5, label=segment, color=color)
        ax.set_title(element_label(element), fontsize=12,
                     fontweight='bold' if element in CRM_STRATEGIC_ELEMENTS else 'normal',
                     color='darkred' if element in CRM_STRATEGIC_ELEMENTS else 'black')
        ax.set_xlabel('mg/vehicle', fontsize=8)
        ax.tick_params(labelsize=7)
        if idx == 0:
            ax.legend(fontsize=7)

    for idx in range(len(element_list), len(axes_flat)):
        axes_flat[idx].axis('off')

    plt.tight_layout()
    plt.savefig(SCRIPT_DIR / 'figures_segment' / filename, dpi=200, bbox_inches='tight')
    print(f"✓ Saved: figures_segment/{filename}")


make_overview_grid(critical_elements,
                    'Critical & Strategic Elements - Distribution Overview (all segments)',
                    'element_overview_grid_critical.png')
make_overview_grid(noncritical_elements,
                    'Other (Non-Critical) Elements - Distribution Overview (all segments)',
                    'element_overview_grid_other.png')


# ---- Figure 3: Full detail figure for EVERY plotted element, per segment ----
# (As before -- histogram + top-5 SensorType variance contribution -- but now for all
# elements, not just the top 10. Saved into the same figures_monte_carlo folder.)
for segment in segments:
    n_saved = 0
    for element in plot_elements_sorted_by_mass:
        if element not in all_segment_element_results[segment]:
            continue
        values = all_segment_element_results[segment][element]
        stats_e = all_element_stats[segment][element]
        sensitivity = all_sensitivity[segment][element]['variance_contrib']

        fig2, axes2 = plt.subplots(1, 2, figsize=(14, 6))
        crm_tag = ' [critical/strategic]' if element in CRM_STRATEGIC_ELEMENTS else ''
        fig2.suptitle(f'{element}{crm_tag} - {segment} Segment', fontsize=14, fontweight='bold')

        ax1 = axes2[0]
        ax1.hist(values, bins=50, alpha=0.7, color='steelblue')
        ax1.axvline(stats_e['mean'], color='red', linestyle='--', linewidth=2,
                    label=f"Mean: {stats_e['mean']:.2f}")
        ax1.axvline(stats_e['p025'], color='orange', linestyle='--', linewidth=1.5,
                    label=f"P025: {stats_e['p025']:.2f}")
        ax1.axvline(stats_e['p975'], color='orange', linestyle='--', linewidth=1.5,
                    label=f"P975: {stats_e['p975']:.2f}")
        ax1.set_xlabel(f'{element} Total Mass (mg per vehicle)')
        ax1.set_ylabel('Frequency')
        ax1.set_title('Distribution of Total Mass')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        ax2 = axes2[1]
        top5_st = sorted(sensitivity.items(), key=lambda kv: (kv[1] if kv[1] == kv[1] else -1), reverse=True)[:5]
        st_names = [s[0] for s in top5_st]
        st_vals = [s[1] * 100 for s in top5_st]
        ax2.barh(st_names, st_vals, color='teal')
        ax2.set_xlabel('Variance Contribution to Total (%)')
        ax2.set_title('Top 5 SensorTypes by Variance Contribution')
        ax2.grid(True, alpha=0.3, axis='x')

        plt.tight_layout()
        fname = f'element_monte_carlo_{safe_filename(element)}_{segment}_segment.png'
        plt.savefig(SCRIPT_DIR / 'figures_monte_carlo' / fname, dpi=300, bbox_inches='tight')
        plt.close(fig2)
        n_saved += 1

    print(f"✓ Saved {n_saved} per-element detail figures for {segment} segment")

# ---- Figure 4: Sensitivity overview, ALL critical/strategic elements (E-F segment) ----
# Split into multiple grids of 6 if needed, since there are more than 6 critical elements.
def make_sensitivity_grid(element_list, title, filename):
    if not element_list:
        return
    ncols = 3
    nrows = int(np.ceil(len(element_list) / ncols))
    fig, axes_grid = plt.subplots(nrows, ncols, figsize=(6 * ncols, 4 * nrows))
    fig.suptitle(title, fontsize=16, fontweight='bold')
    axes_flat = np.atleast_1d(axes_grid).flatten()

    for idx, element in enumerate(element_list):
        ax = axes_flat[idx]
        vc = all_sensitivity['EF'][element]['variance_contrib']
        top5 = sorted(vc.items(), key=lambda kv: (kv[1] if kv[1] == kv[1] else -1), reverse=True)[:5]
        labels = [t[0] for t in top5]
        values = [t[1] for t in top5]
        colors_pie = plt.cm.Set3(np.linspace(0, 1, len(labels)))
        ax.pie(values, labels=labels, autopct='%1.1f%%', colors=colors_pie, startangle=90,
               textprops={'fontsize': 7})
        ax.set_title(element_label(element), fontweight='bold')

    for idx in range(len(element_list), len(axes_flat)):
        axes_flat[idx].axis('off')

    plt.tight_layout()
    plt.savefig(SCRIPT_DIR / 'figures_sensitivity' / filename, dpi=200, bbox_inches='tight')
    print(f"✓ Saved: figures_sensitivity/{filename}")


make_sensitivity_grid(critical_elements,
                      'Sensitivity Analysis - Critical & Strategic Elements (E-F Segment)',
                      'element_sensitivity_critical.png')
make_sensitivity_grid(noncritical_elements,
                      'Sensitivity Analysis - Other Elements (E-F Segment)',
                      'element_sensitivity_other.png')

plt.close('all')


# ============================================================================
# SAVE RESULTS
# ============================================================================

print("\n" + "="*70)
print("SAVING RESULTS")
print("="*70)

comparison_df.to_csv(SCRIPT_DIR / 'csv_segment' / 'element_segment_comparison.csv', index=False)
print("✓ Saved: csv_segment/element_segment_comparison.csv")

for segment in segments:
    stats_df = pd.DataFrame(all_element_stats[segment]).T
    stats_df.index.name = 'Element'
    stats_df.to_csv(SCRIPT_DIR / 'csv_monte_carlo' / f'element_monte_carlo_{segment}_summary_stats.csv')
    print(f"✓ Saved: csv_monte_carlo/element_monte_carlo_{segment}_summary_stats.csv")

    results_df = pd.DataFrame(all_segment_element_results[segment])
    results_df.to_csv(SCRIPT_DIR / 'csv_monte_carlo' / f'element_monte_carlo_{segment}_detailed_results.csv',
                       index=False)
    print(f"✓ Saved: csv_monte_carlo/element_monte_carlo_{segment}_detailed_results.csv")

# Per-SensorType breakdown, per element, per segment (the "calculate for each sensor type" output)
for segment in segments:
    rows = []
    for element in active_elements:
        if element not in all_segment_sensortype_stats[segment]:
            continue
        for st, stt in all_segment_sensortype_stats[segment][element].items():
            rows.append({
                'Element': element,
                'SensorType': st,
                'N_Locations': stt['n_locations'],
                'Mean_Mass_mg': stt['mean'],
                'Mode_Mass_mg': stt['mode'],
                'Median_Mass_mg': stt['median'],
                'Std_Mass_mg': stt['std'],
                'P025_Mass_mg': stt['p025'],
                'P975_Mass_mg': stt['p975'],
            })
    breakdown_df = pd.DataFrame(rows).sort_values(['Element', 'Mean_Mass_mg'], ascending=[True, False])
    breakdown_df.to_csv(SCRIPT_DIR / 'csv_sensortype' / f'element_sensortype_breakdown_{segment}_segment.csv',
                         index=False)
    print(f"✓ Saved: csv_sensortype/element_sensortype_breakdown_{segment}_segment.csv")

# Sensitivity CSVs, per element, per segment
for segment in segments:
    for element in active_elements:
        if element not in all_sensitivity[segment]:
            continue
        sens = all_sensitivity[segment][element]
        sts = list(sens['variance_contrib'].keys())
        sens_df = pd.DataFrame({
            'SensorType': sts,
            'Variance_Contribution': [sens['variance_contrib'][st] for st in sts],
            'Correlation_with_Total': [sens['correlations'][st] for st in sts]
        }).sort_values('Variance_Contribution', ascending=False)
        fname = f'element_sensitivity_{safe_filename(element)}_{segment}_segment.csv'
        sens_df.to_csv(SCRIPT_DIR / 'csv_sensitivity' / fname, index=False)
    print(f"✓ Saved sensitivity CSVs for {segment} segment ({len(active_elements)} elements)")

print("\n" + "="*70)
print("ANALYSIS COMPLETE!")
print("="*70)


# ============================================================================
# SAVE HISTOGRAM DISTRIBUTIONS FOR BOOTSTRAPPING
# ============================================================================

print("\n" + "="*70)
print("SAVING HISTOGRAM DISTRIBUTIONS FOR BOOTSTRAPPING")
print("="*70)

n_bins = 50
index_data = []

for segment in segments:
    element_results = all_segment_element_results[segment]
    for element in active_elements:
        if element not in element_results:
            continue
        values = element_results[element]
        counts, bin_edges = np.histogram(values, bins=n_bins)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        hist_df = pd.DataFrame({
            'bin_center': bin_centers,
            'bin_left_edge': bin_edges[:-1],
            'bin_right_edge': bin_edges[1:],
            'count': counts,
            'frequency': counts / ndraws
        })
        elem_name = safe_filename(element)
        filename = SCRIPT_DIR / 'histograms' / f'histogram_{segment}_{elem_name}.csv'
        hist_df.to_csv(filename, index=False)

        index_data.append({
            'type': 'element',
            'segment': segment,
            'label': element,
            'histogram_file': f'histograms/histogram_{segment}_{elem_name}.csv',
            'raw_data_file': f'raw_data/raw_distribution_{segment}_elements.csv',
            'n_simulations': ndraws,
            'n_bins': n_bins
        })
    print(f"  ✓ Saved {len(element_results)} element histograms for {segment} segment")

for segment in segments:
    results_df = pd.DataFrame(all_segment_element_results[segment])
    filename = SCRIPT_DIR / 'raw_data' / f'raw_distribution_{segment}_elements.csv'
    results_df.to_csv(filename, index=False)
    print(f"  ✓ Saved: raw_data/raw_distribution_{segment}_elements.csv")

index_df = pd.DataFrame(index_data)
index_df.to_csv(SCRIPT_DIR / 'distribution_index_elements.csv', index=False)
print("  ✓ Saved: distribution_index_elements.csv")

print("\n" + "="*70)
print("HISTOGRAM DISTRIBUTIONS SAVED!")
print("="*70)
print(f"\nActive elements simulated: {len(active_elements)}")
print(f"Elements excluded per explicit user instruction (not simulated at all): {sorted(USER_EXCLUDED_ELEMENTS)}")
print(f"Skipped elements (zero max everywhere): {skipped_elements}")
print(f"Sensor types excluded (zero max weight): {zero_weight_types}")
print(f"Total histogram files: {len(index_data)}")
print(f"Total raw data files: {len(segments)}")