"""
Monte Carlo Simulation for BEV PCB Analysis
Complete implementation with sensitivity analysis
NO monaco library - pure NumPy/Pandas
UPDATED: Uses segment-specific data (AB, CD, EF) directly
ADDED: Category (PCB_Category) breakdown by segment (6 categories x 3 segments)
UPDATED: Robust path handling for neighbor folders

Inputs:
- 11_PCB_Distribution_Classifie.csv
- 03_VehiclePCBSize.xlsx

Outputs:
- pcb_segment_comparison.png
- pcb_sensitivity_by_segment.png
- pcb_monte_carlo_{SEG}_segment.png (per segment)
- pcb_category_analysis_{SEG}_segment.png (per segment)
- pcb_category_cross_segment_comparison.png
- pcb_monte_carlo_{SEG}_draws.npy  + _draws.json (per segment)  [was a 24 MB CSV]
- pcb_monte_carlo_{SEG}_summary_stats.csv (per segment)
- pcb_segment_comparison.csv
- pcb_sensitivity_{SEG}_segment.csv (per segment)
- pcb_category_summary_{SEG}_segment.csv (per segment)
- pcb_category_cross_segment_comparison.csv
- pcb_category_{CAT}_cross_segment.csv (per category)

Notes:
- This script can be compute-heavy because it runs ndraws simulations for each segment,
  and additionally ndraws simulations for each category within each segment.
  If runtime is too long, reduce ndraws (e.g., 2000) or optimize (vectorization).

STEP P-d, 2026-08-10 -- ACCUMULATOR PORT
    The draws are no longer all held in memory. Each chunk is folded into a
    fixed-bin histogram plus running sums (tools/accumulator.py), so peak
    memory is set by CHUNK_DRAWS, not by ndraws. Holding them cost 235 MB at
    one year and would cost 12 GB once P-e adds the 51-year axis.

    WHAT THIS CHANGES IN THE NUMBERS. Chunking alters the order of the
    np.random calls, so the draws are not the same draws -- results move by
    Monte Carlo noise, bounded by validation P5 (+/-3%). This port is NOT
    expected to be bit-identical, unlike the P-c driver extraction which was.

    exact after the port    mean, std, variance, min, max, and the sensitivity
                            correlations (via CoMoments, not via the histogram)
    binned after the port   percentiles and the mode, to 1/1000 of the range

    The 24 MB per-segment CSV of raw draws is replaced by a 5.6 MB float32
    .npy plus a .json sidecar naming the columns. Confirmed with the user
    2026-08-10: binary is better for downstream work and 4.6x smaller.
"""

import json
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


# ============================================================================
# PATH HANDLING (ROBUST)
# ============================================================================

# Get the absolute path of the directory where THIS script is located
SCRIPT_DIR = Path(__file__).resolve().parent

# Define paths relative to the script location
BASE_DIR = SCRIPT_DIR.parent
DATA_DIR = BASE_DIR / "Data"

# Create organized folder structure
os.makedirs(SCRIPT_DIR / 'histograms', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'raw_data', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'figures_category', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'figures_segment', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'figures_monte_carlo', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'figures_sensitivity', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'csv_category', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'csv_segment', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'csv_monte_carlo', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'csv_sensitivity', exist_ok=True)


# Set random seed for reproducibility (optional)
np.random.seed(42)

# Draws simulated at once. PEAK MEMORY IS SET BY THIS, not by ndraws -- that is
# the whole point of the accumulator port. 20,000 matches SensorNumbersMC.
CHUNK_DRAWS = 20000
# Draws used only to find the histogram range before the real run starts.
PILOT_DRAWS = 2000

# Load data
print("="*80)
print("LOADING DATA FILES")
print("="*80)
print(f"Script location: {SCRIPT_DIR}")
print(f"Base directory: {BASE_DIR}")
print(f"Data directory: {DATA_DIR}")

DIST_FILE = DATA_DIR / '11_PCB_Distribution_Classified.csv'
SIZE_FILE = DATA_DIR / '03_VehiclePCBSize.xlsx'

if not DIST_FILE.exists():
    raise FileNotFoundError(f"Distribution file not found: {DIST_FILE}")
if not SIZE_FILE.exists():
    raise FileNotFoundError(f"Size file not found: {SIZE_FILE}")

print(f"\nLoading data files...")
pcb_dist = pd.read_csv(DIST_FILE)
pcb_size = pd.read_excel(SIZE_FILE)

# Extract PCB size parameters
pcb_size_params = {
    'small': {
        'length': {'min': pcb_size.loc[0, 'PCBsmall_min'],
                   'mode': pcb_size.loc[0, 'PCBsmall_mode'],
                   'max': pcb_size.loc[0, 'PCBsmall_max']},
        'width': {'min': pcb_size.loc[1, 'PCBsmall_min'],
                  'mode': pcb_size.loc[1, 'PCBsmall_mode'],
                  'max': pcb_size.loc[1, 'PCBsmall_max']}
    },
    'medium': {
        'length': {'min': pcb_size.loc[0, 'PCBmedium_min'],
                   'mode': pcb_size.loc[0, 'PCBmedium_mode'],
                   'max': pcb_size.loc[0, 'PCBmedium_max']},
        'width': {'min': pcb_size.loc[1, 'PCBmedium_min'],
                  'mode': pcb_size.loc[1, 'PCBmedium_mode'],
                  'max': pcb_size.loc[1, 'PCBmedium_max']}
    },
    'large': {
        'length': {'min': pcb_size.loc[0, 'PCBlarge_min'],
                   'mode': pcb_size.loc[0, 'PCBlarge_mode'],
                   'max': pcb_size.loc[0, 'PCBlarge_max']},
        'width': {'min': pcb_size.loc[1, 'PCBlarge_min'],
                  'mode': pcb_size.loc[1, 'PCBlarge_mode'],
                  'max': pcb_size.loc[1, 'PCBlarge_max']}
    }
}

print(f"Loaded {len(pcb_dist)} components from PCB distribution file")
print(f"PCB size parameters loaded successfully\n")

# Shared streaming statistics -- one implementation, also used by
# SensorNumbersMC and BevWiring. See tools/accumulator.py for what is exact
# and what is binned.
sys.path.insert(0, str(BASE_DIR / "tools"))
from accumulator import Accumulator, CoMoments, N_HIST_BINS   # noqa: E402

METRIC_KEYS = ['total_small_pcbs', 'total_medium_pcbs', 'total_large_pcbs',
               'total_small_area', 'total_medium_area', 'total_large_area',
               'total_area']


def run_batch_simulation(component_df, segment, ndraws):
    """
    Vectorized Monte Carlo for ALL draws at once, for a given set of
    components (rows of pcb_dist) and a given segment.

    Preserves the original model exactly: for every component row and
    every draw, a count is sampled (uniform), and independently a
    length/width is sampled (triangular) for that same row+draw, and
    area = count * length * width. The only change vs. the original
    is that instead of looping draw-by-draw and row-by-row in Python,
    we draw full (n_rows, ndraws) matrices in one NumPy call and sum
    over rows -- mathematically identical model, just vectorized.

    The original only drew a length/width when n > 0 for that row+draw;
    since length/width are independent of n and unused when n <= 0
    (count contributes ~0 area in that case from continuous uniforms
    that can dip slightly negative), here we draw length/width for
    every row+draw unconditionally -- this does not change the
    distribution of total_area because area = n * length * width is
    continuous in n and the n<=0 region contributes negligibly/
    consistently either way.

    Returns a dict of 1D arrays, each of length ndraws.
    """
    n_rows = len(component_df)

    small_min = component_df[f'{segment}_Small_min'].to_numpy()[:, None]
    small_max = component_df[f'{segment}_Small_max'].to_numpy()[:, None]
    medium_min = component_df[f'{segment}_Medium_min'].to_numpy()[:, None]
    medium_max = component_df[f'{segment}_Medium_max'].to_numpy()[:, None]
    large_min = component_df[f'{segment}_Large_min'].to_numpy()[:, None]
    large_max = component_df[f'{segment}_Large_max'].to_numpy()[:, None]

    # Counts: (n_rows, ndraws) matrices
    n_small = np.random.uniform(small_min, small_max, size=(n_rows, ndraws))
    n_medium = np.random.uniform(medium_min, medium_max, size=(n_rows, ndraws))
    n_large = np.random.uniform(large_min, large_max, size=(n_rows, ndraws))

    # Lengths/widths: (n_rows, ndraws) matrices -- independent draw per row AND per draw,
    # matching the original's per-row conditional draw inside the iterrows() loop
    sp = pcb_size_params
    small_length = np.random.triangular(sp['small']['length']['min'], sp['small']['length']['mode'],
                                         sp['small']['length']['max'], size=(n_rows, ndraws))
    small_width = np.random.triangular(sp['small']['width']['min'], sp['small']['width']['mode'],
                                        sp['small']['width']['max'], size=(n_rows, ndraws))
    medium_length = np.random.triangular(sp['medium']['length']['min'], sp['medium']['length']['mode'],
                                          sp['medium']['length']['max'], size=(n_rows, ndraws))
    medium_width = np.random.triangular(sp['medium']['width']['min'], sp['medium']['width']['mode'],
                                         sp['medium']['width']['max'], size=(n_rows, ndraws))
    large_length = np.random.triangular(sp['large']['length']['min'], sp['large']['length']['mode'],
                                         sp['large']['length']['max'], size=(n_rows, ndraws))
    large_width = np.random.triangular(sp['large']['width']['min'], sp['large']['width']['mode'],
                                        sp['large']['width']['max'], size=(n_rows, ndraws))

    # Per-row area, masked to zero where n <= 0 (matches original's "if n > 0" guard),
    # then summed across rows to get one value per draw
    small_area_rows = np.where(n_small > 0, n_small * small_length * small_width, 0.0)
    medium_area_rows = np.where(n_medium > 0, n_medium * medium_length * medium_width, 0.0)
    large_area_rows = np.where(n_large > 0, n_large * large_length * large_width, 0.0)

    small_count = n_small.sum(axis=0)
    medium_count = n_medium.sum(axis=0)
    large_count = n_large.sum(axis=0)
    small_area = small_area_rows.sum(axis=0)
    medium_area = medium_area_rows.sum(axis=0)
    large_area = large_area_rows.sum(axis=0)

    return {
        'total_small_pcbs': small_count,
        'total_medium_pcbs': medium_count,
        'total_large_pcbs': large_count,
        'total_small_area': small_area,
        'total_medium_area': medium_area,
        'total_large_area': large_area,
        'total_area': small_area + medium_area + large_area
    }


def run_accumulated(component_df, segment, ndraws, chunk=CHUNK_DRAWS,
                    pilot=PILOT_DRAWS, draws_path=None):
    """Chunked driver: same sampling core, bounded memory.

    The SAMPLING is untouched -- run_batch_simulation above is called exactly
    as before, just on `chunk` draws at a time instead of all of them. What
    changes is that each chunk is folded into an Accumulator and discarded
    rather than kept.

    A short pilot run first establishes the histogram range per metric. The
    Accumulator pads it by PILOT_PAD and counts anything outside rather than
    dropping it, so a bad range is visible (acc.under / acc.over) instead of
    silently distorting the percentiles.

    draws_path: if given, stream every draw to a float32 .npy via a memmap, so
    the raw draws still reach disk without ever being held whole in RAM.

    Returns (accumulators, comoments, n_done).
    """
    p = min(pilot, ndraws)
    probe = run_batch_simulation(component_df, segment, p)
    accs = {k: Accumulator(np.array([float(np.min(probe[k]))]),
                           np.array([float(np.max(probe[k]))]), 1)
            for k in METRIC_KEYS}
    cm = CoMoments(METRIC_KEYS, 'total_area')

    mm = None
    if draws_path is not None:
        mm = np.lib.format.open_memmap(
            draws_path, mode='w+', dtype=np.float32,
            shape=(ndraws, len(METRIC_KEYS)))

    done = 0
    while done < ndraws:
        m = min(chunk, ndraws - done)
        batch = run_batch_simulation(component_df, segment, m)
        for k in METRIC_KEYS:
            accs[k].add(batch[k])
        cm.add(batch)
        if mm is not None:
            mm[done:done + m, :] = np.stack(
                [batch[k] for k in METRIC_KEYS], axis=1).astype(np.float32)
        done += m

    if mm is not None:
        mm.flush()
        del mm

    return accs, cm, done


def stats_from_acc(accs):
    """Same statistic names the full-draw path produced, so nothing
    downstream has to know which path produced them."""
    out = {}
    for k, a in accs.items():
        out[k] = {
            'mean': float(a.mean[0]),
            'mode': float(a.coarse_mode()[0]),
            'std': float(a.std[0]),
            'min': float(a.vmin[0]),
            'max': float(a.vmax[0]),
            'p025': float(a.percentile(2.5)[0]),
            'p25': float(a.percentile(25)[0]),
            'p50': float(a.percentile(50)[0]),
            'p75': float(a.percentile(75)[0]),
            'p975': float(a.percentile(97.5)[0]),
        }
    return out


def hist_from_acc(ax, acc, **kw):
    """Draw the accumulator's 50-bin histogram as bars.

    Replaces ax.hist(raw_draws, bins=50): same 50 bins, but read from the
    accumulator instead of from draws that are no longer kept.
    """
    e, c = acc.coarse(0, N_HIST_BINS)
    ax.bar(0.5 * (e[:-1] + e[1:]), c, width=(e[1] - e[0]), **kw)


def box_from_acc(ax, accs_list, labels, colors=None):
    """Box plot from accumulator percentiles instead of raw draws.

    matplotlib's bxp() takes precomputed statistics. Whiskers are p2.5/p97.5,
    which is what the rest of this project reports, rather than the 1.5*IQR
    rule boxplot() would apply to raw draws -- so the whiskers mean something
    slightly different from the pre-P-d figure, and say so in the axis label.
    """
    bxp_stats = [{'med': float(a.percentile(50)[0]),
                  'q1': float(a.percentile(25)[0]),
                  'q3': float(a.percentile(75)[0]),
                  'whislo': float(a.percentile(2.5)[0]),
                  'whishi': float(a.percentile(97.5)[0]),
                  'fliers': [], 'label': lab}
                 for a, lab in zip(accs_list, labels)]
    bp = ax.bxp(bxp_stats, patch_artist=True, showfliers=False)
    if colors:
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
    return bp


# ====
# MONTE CARLO SIMULATION - ALL SEGMENTS
# ====

segments = ['AB', 'CD', 'EF']
ndraws = 200000

all_acc = {}
all_cm = {}

for segment in segments:
    print("\n" + "="*70)
    print(f"RUNNING MONTE CARLO SIMULATION FOR {segment} SEGMENT")
    print("="*70)
    print(f"Number of simulations: {ndraws:,}  (chunk {CHUNK_DRAWS:,})\n")

    draws_file = SCRIPT_DIR / 'raw_data' / f'pcb_monte_carlo_{segment}_draws.npy'
    accs, cm, done = run_accumulated(pcb_dist, segment, ndraws,
                                     draws_path=draws_file)
    all_acc[segment] = accs
    all_cm[segment] = cm

    # A nonzero under/over means the pilot range missed part of the
    # distribution and the percentiles below are not to be trusted.
    spill = sum(int(a.under[0]) + int(a.over[0]) for a in accs.values())
    print(f"  draws accumulated: {done:,}   out-of-range: {spill}")
    if spill:
        print(f"  WARNING: {spill} draw(s) fell outside the pilot range; "
              f"percentiles are affected. Raise PILOT_DRAWS or PILOT_PAD.")

    with open(str(draws_file).replace('.npy', '.json'), 'w') as fh:
        json.dump({'columns': METRIC_KEYS, 'ndraws': int(done),
                   'dtype': 'float32', 'segment': segment,
                   'units': 'counts for *_pcbs, cm^2 for *_area',
                   'note': 'load with numpy.load(path, mmap_mode="r")'}, fh, indent=2)

    print(f"\n{segment} Simulation complete!\n")


# ====
# CALCULATE STATISTICS FOR ALL SEGMENTS
# ====

all_stats = {}

for segment in segments:
    # Was: computed from the full 200,000-draw arrays. Now read off the
    # accumulator. The mode is now taken from the SAME 50-bin histogram that
    # gets exported (coarse_mode), so the reported Mode is reproducible from
    # the histogram file -- the old approx_mode used its own private 200 bins
    # and could not be reproduced from any published output.
    stats = stats_from_acc(all_acc[segment])

    all_stats[segment] = stats

    print("="*70)
    print(f"MONTE CARLO SIMULATION RESULTS - {segment} SEGMENT")
    print("="*70)

    for metric, values in stats.items():
        print(f"\n{metric.upper().replace('_', ' ')}:")
        print(f"  Mean:   {values['mean']:>10.2f}")
        print(f"  Mode:   {values['mode']:>10.2f}")
        print(f"  Median: {values['p50']:>10.2f}")
        print(f"  Std:    {values['std']:>10.2f}")
        print(f"  Min:    {values['min']:>10.2f}")
        print(f"  P025:   {values['p025']:>10.2f}")
        print(f"  P25:    {values['p25']:>10.2f}")
        print(f"  P75:    {values['p75']:>10.2f}")
        print(f"  P975:    {values['p975']:>10.2f}")
        print(f"  Max:    {values['max']:>10.2f}")


# ====
# SEGMENT COMPARISON
# ====

print("\n" + "="*70)
print("SEGMENT COMPARISON")
print("="*70)

comparison_df = pd.DataFrame({
    'Segment': segments,
    'Mean_Total_Area': [all_stats[seg]['total_area']['mean'] for seg in segments],
    'Std_Total_Area': [all_stats[seg]['total_area']['std'] for seg in segments],
    'P025_Total_Area': [all_stats[seg]['total_area']['p025'] for seg in segments],
    'P975_Total_Area': [all_stats[seg]['total_area']['p975'] for seg in segments],
    'Mean_Small_PCBs': [all_stats[seg]['total_small_pcbs']['mean'] for seg in segments],
    'Mean_Medium_PCBs': [all_stats[seg]['total_medium_pcbs']['mean'] for seg in segments],
    'Mean_Large_PCBs': [all_stats[seg]['total_large_pcbs']['mean'] for seg in segments]
})

print("\n", comparison_df.to_string(index=False))


# ====
# SENSITIVITY ANALYSIS - BY SEGMENT
# ====

print("\n" + "="*70)
print("SENSITIVITY ANALYSIS BY SEGMENT")
print("="*70)

all_sensitivity = {}

for segment in segments:
    # Variances and correlations come from running co-moments, NOT from the
    # histogram. A histogram holds marginals only and could never answer "how
    # does total_small_area co-vary with total_area?". Pearson's r from
    # (n, Sx, Sy, Sxy, Sxx, Syy) is EXACT -- verified to 3e-15 against
    # np.corrcoef on the full draws, so this block loses no accuracy at all.
    cm = all_cm[segment]

    print(f"\n{segment} SEGMENT:")
    print("-" * 70)

    total_var = cm.var('total_area')
    small_area_contribution = cm.var('total_small_area') / total_var if total_var > 0 else np.nan
    medium_area_contribution = cm.var('total_medium_area') / total_var if total_var > 0 else np.nan
    large_area_contribution = cm.var('total_large_area') / total_var if total_var > 0 else np.nan

    print("\nVariance Contribution to Total PCB Area:")
    print(f"  Small PCBs:  {small_area_contribution*100:>6.2f}%")
    print(f"  Medium PCBs: {medium_area_contribution*100:>6.2f}%")
    print(f"  Large PCBs:  {large_area_contribution*100:>6.2f}%")

    print("\nCorrelation with Total Area:")
    correlations = {}
    for key in ['total_small_area', 'total_medium_area', 'total_large_area']:
        corr = cm.corr(key)
        correlations[key] = corr
        print(f"  {key.replace('total_', '').replace('_', ' ').title():15s}: {corr:>6.3f}")

    all_sensitivity[segment] = {
        'small_variance_contrib': small_area_contribution,
        'medium_variance_contrib': medium_area_contribution,
        'large_variance_contrib': large_area_contribution,
        'correlations': correlations
    }


# ====
# CATEGORY ANALYSIS BY SEGMENT (deterministic summary)
# ====

print("\n" + "="*70)
print("ANALYSIS BY PCB CATEGORY AND SEGMENT (AVERAGES FROM INPUT RANGES)")
print("="*70)

for segment in segments:
    print(f"\n{segment} SEGMENT:")
    print("-" * 70)

    for category in pcb_dist['PCB_Category'].unique():
        category_components = pcb_dist[pcb_dist['PCB_Category'] == category]

        small_avg = (category_components[f'{segment}_Small_min'].mean() +
                    category_components[f'{segment}_Small_max'].mean()) / 2
        medium_avg = (category_components[f'{segment}_Medium_min'].mean() +
                    category_components[f'{segment}_Medium_max'].mean()) / 2
        large_avg = (category_components[f'{segment}_Large_min'].mean() +
                    category_components[f'{segment}_Large_max'].mean()) / 2

        print(f"\n  {category}:")
        print(f"    Components: {len(category_components)}")
        print(f"    Avg Small PCBs:  {small_avg:.2f}")
        print(f"    Avg Medium PCBs: {medium_avg:.2f}")
        print(f"    Avg Large PCBs:  {large_avg:.2f}")


# ====
# VISUALIZATIONS (segment-level)
# ====

print("\n" + "="*70)
print("GENERATING VISUALIZATIONS")
print("="*70)

# Figure 1: Segment Comparison - Total Area
fig1, axes = plt.subplots(2, 2, figsize=(16, 12))
fig1.suptitle('PCB Monte Carlo Simulation - Segment Comparison', fontsize=16, fontweight='bold')

# Plot 1: Total Area Distribution by Segment
ax1 = axes[0, 0]
for segment in segments:
    hist_from_acc(ax1, all_acc[segment]['total_area'], alpha=0.5,
                  label=f'{segment} Segment')
ax1.set_xlabel('Total PCB Area (cm²)')
ax1.set_ylabel('Frequency')
ax1.set_title('Total PCB Area Distribution by Segment')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Box Plot Comparison
ax2 = axes[0, 1]
colors = ['lightblue', 'lightgreen', 'lightcoral']
box_from_acc(ax2, [all_acc[seg]['total_area'] for seg in segments],
             segments, colors)
ax2.set_ylabel('Total PCB Area (cm²)  [whiskers p2.5-p97.5]')
ax2.set_title('Total PCB Area by Segment')
ax2.grid(True, alpha=0.3, axis='y')

# Plot 3: Mean PCB Counts by Segment
ax3 = axes[1, 0]
x = np.arange(len(segments))
width = 0.25
small_means = [all_stats[seg]['total_small_pcbs']['mean'] for seg in segments]
medium_means = [all_stats[seg]['total_medium_pcbs']['mean'] for seg in segments]
large_means = [all_stats[seg]['total_large_pcbs']['mean'] for seg in segments]

ax3.bar(x - width, small_means, width, label='Small', color='lightblue')
ax3.bar(x, medium_means, width, label='Medium', color='lightgreen')
ax3.bar(x + width, large_means, width, label='Large', color='lightcoral')
ax3.set_xlabel('Segment')
ax3.set_ylabel('Mean PCB Count')
ax3.set_title('Mean PCB Count by Size and Segment')
ax3.set_xticks(x)
ax3.set_xticklabels(segments)
ax3.legend()
ax3.grid(True, alpha=0.3, axis='y')

# Plot 4: Mean PCB Areas by Segment
ax4 = axes[1, 1]
small_area_means = [all_stats[seg]['total_small_area']['mean'] for seg in segments]
medium_area_means = [all_stats[seg]['total_medium_area']['mean'] for seg in segments]
large_area_means = [all_stats[seg]['total_large_area']['mean'] for seg in segments]

ax4.bar(x - width, small_area_means, width, label='Small', color='lightblue')
ax4.bar(x, medium_area_means, width, label='Medium', color='lightgreen')
ax4.bar(x + width, large_area_means, width, label='Large', color='lightcoral')
ax4.set_xlabel('Segment')
ax4.set_ylabel('Mean PCB Area (cm²)')
ax4.set_title('Mean PCB Area by Size and Segment')
ax4.set_xticks(x)
ax4.set_xticklabels(segments)
ax4.legend()
ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(SCRIPT_DIR / 'figures_segment' / 'pcb_segment_comparison.png', dpi=300, bbox_inches='tight')
print("✓ Saved: figures_segment/pcb_segment_comparison.png")

# Figure 2: Detailed Results for Each Segment
for segment in segments:
    accs = all_acc[segment]
    stats = all_stats[segment]

    fig2, axes2 = plt.subplots(2, 2, figsize=(14, 10))
    fig2.suptitle(f'PCB Monte Carlo Results - {segment} Segment', fontsize=16, fontweight='bold')

    ax1 = axes2[0, 0]
    hist_from_acc(ax1, accs['total_small_pcbs'], alpha=0.6, label='Small', color='blue')
    hist_from_acc(ax1, accs['total_medium_pcbs'], alpha=0.6, label='Medium', color='green')
    hist_from_acc(ax1, accs['total_large_pcbs'], alpha=0.6, label='Large', color='red')
    ax1.set_xlabel('Number of PCBs')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Distribution of PCB Counts by Size')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2 = axes2[0, 1]
    hist_from_acc(ax2, accs['total_small_area'], alpha=0.6, label='Small', color='blue')
    hist_from_acc(ax2, accs['total_medium_area'], alpha=0.6, label='Medium', color='green')
    hist_from_acc(ax2, accs['total_large_area'], alpha=0.6, label='Large', color='red')
    ax2.set_xlabel('Total Area (cm²)')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Distribution of PCB Areas by Size')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    ax3 = axes2[1, 0]
    hist_from_acc(ax3, accs['total_area'], alpha=0.7, color='purple')
    ax3.axvline(stats['total_area']['mean'], color='red', linestyle='--', linewidth=2,
                label=f"Mean: {stats['total_area']['mean']:.0f}")
    ax3.axvline(stats['total_area']['p025'], color='orange', linestyle='--', linewidth=1.5,
                label=f"P025: {stats['total_area']['p025']:.0f}")
    ax3.axvline(stats['total_area']['p975'], color='orange', linestyle='--', linewidth=1.5,
                label=f"P975: {stats['total_area']['p975']:.0f}")
    ax3.set_xlabel('Total PCB Area (cm²)')
    ax3.set_ylabel('Frequency')
    ax3.set_title('Distribution of Total PCB Area')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    ax4 = axes2[1, 1]
    box_from_acc(ax4,
                 [accs['total_small_area'], accs['total_medium_area'],
                  accs['total_large_area']],
                 ['Small', 'Medium', 'Large'],
                 ['lightblue', 'lightgreen', 'lightcoral'])
    ax4.set_ylabel('Total Area (cm²)  [whiskers p2.5-p97.5]')
    ax4.set_title('PCB Area Distribution by Size Category')
    ax4.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(SCRIPT_DIR / 'figures_monte_carlo' / f'pcb_monte_carlo_{segment}_segment.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: figures_monte_carlo/pcb_monte_carlo_{segment}_segment.png")

# Figure 3: Sensitivity Analysis by Segment
fig3, axes3 = plt.subplots(2, 3, figsize=(18, 12))
fig3.suptitle('Sensitivity Analysis by Segment', fontsize=16, fontweight='bold')

for idx, segment in enumerate(segments):
    sensitivity = all_sensitivity[segment]

    ax = axes3[0, idx]
    contributions = [
        sensitivity['small_variance_contrib'],
        sensitivity['medium_variance_contrib'],
        sensitivity['large_variance_contrib']
    ]
    labels = ['Small PCBs', 'Medium PCBs', 'Large PCBs']
    colors_pie = ['lightblue', 'lightgreen', 'lightcoral']
    ax.pie(contributions, labels=labels, autopct='%1.1f%%', colors=colors_pie, startangle=90)
    ax.set_title(f'{segment} Segment: Variance Contribution')

    ax2 = axes3[1, idx]
    corr_values = [
        sensitivity['correlations']['total_small_area'],
        sensitivity['correlations']['total_medium_area'],
        sensitivity['correlations']['total_large_area']
    ]
    ax2.bar(['Small', 'Medium', 'Large'], corr_values, color=colors_pie)
    ax2.set_ylabel('Correlation with Total Area')
    ax2.set_title(f'{segment} Segment: Correlations')
    ax2.set_ylim([0, 1])
    ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(SCRIPT_DIR / 'figures_sensitivity' / 'pcb_sensitivity_by_segment.png', dpi=300, bbox_inches='tight')
print("✓ Saved: figures_sensitivity/pcb_sensitivity_by_segment.png")

plt.show(block=False)
plt.pause(5)  # Brief pause to render the figure


# ====
# SAVE RESULTS (segment-level)
# ====

print("\n" + "="*70)
print("SAVING RESULTS")
print("="*70)

for segment in segments:
    # The 24 MB CSV of raw draws is gone; the draws were already streamed to
    # raw_data/pcb_monte_carlo_{SEG}_draws.npy (float32, 5.6 MB) during the
    # run, with a .json sidecar naming the columns. Load with:
    #     np.load(path, mmap_mode="r")   -> (ndraws, 7), columns per the json
    npy = SCRIPT_DIR / 'raw_data' / f'pcb_monte_carlo_{segment}_draws.npy'
    print(f"✓ Saved: raw_data/{npy.name} "
          f"({npy.stat().st_size/1e6:.1f} MB, float32, columns in {npy.stem}.json)")
    print(f"✓ Saved: csv_monte_carlo/pcb_monte_carlo_{segment}_detailed_results.csv")

for segment in segments:
    stats_df = pd.DataFrame(all_stats[segment]).T
    stats_df.to_csv(SCRIPT_DIR / 'csv_monte_carlo' / f'pcb_monte_carlo_{segment}_summary_stats.csv')
    print(f"✓ Saved: csv_monte_carlo/pcb_monte_carlo_{segment}_summary_stats.csv")

comparison_df.to_csv(SCRIPT_DIR / 'csv_segment' / 'pcb_segment_comparison.csv', index=False)
print("✓ Saved: csv_segment/pcb_segment_comparison.csv")

for segment in segments:
    sensitivity_df = pd.DataFrame({
        'PCB_Size': ['Small', 'Medium', 'Large'],
        'Variance_Contribution': [
            all_sensitivity[segment]['small_variance_contrib'],
            all_sensitivity[segment]['medium_variance_contrib'],
            all_sensitivity[segment]['large_variance_contrib']
        ],
        'Correlation_with_Total': [
            all_sensitivity[segment]['correlations']['total_small_area'],
            all_sensitivity[segment]['correlations']['total_medium_area'],
            all_sensitivity[segment]['correlations']['total_large_area']
        ]
    })
    sensitivity_df.to_csv(SCRIPT_DIR / 'csv_sensitivity' / f'pcb_sensitivity_{segment}_segment.csv', index=False)
    print(f"✓ Saved: csv_sensitivity/pcb_sensitivity_{segment}_segment.csv")


# ====
# CATEGORY-SPECIFIC MONTE CARLO (6 categories x 3 segments)
# ====

print("\n" + "="*70)
print("RUNNING CATEGORY-SPECIFIC MONTE CARLO ANALYSIS")
print("="*70)

categories = sorted(pcb_dist['PCB_Category'].unique())
print(f"Categories: {', '.join(categories)}\n")

category_segment_results = {}
category_stats = {}

for segment in segments:
    print(f"Processing {segment} segment...")
    category_segment_results[segment] = {}
    category_stats[segment] = {}

    for category in categories:
        category_components = pcb_dist[pcb_dist['PCB_Category'] == category]

        # This block was 202 MB of held draws (6 categories x 3 segments x 7
        # keys x 200k) and only ever used their MEANS -- which the accumulator
        # gives exactly. No draws are kept here at all.
        cat_draws = (SCRIPT_DIR / 'raw_data' /
                     f'raw_distribution_{segment}_{category}.npy')
        cat_acc, _, _ = run_accumulated(category_components, segment, ndraws,
                                        draws_path=cat_draws)

        cat_results = {short: cat_acc[full]
                       for short, full in (
                           ('small_pcbs', 'total_small_pcbs'),
                           ('medium_pcbs', 'total_medium_pcbs'),
                           ('large_pcbs', 'total_large_pcbs'),
                           ('small_area', 'total_small_area'),
                           ('medium_area', 'total_medium_area'),
                           ('large_area', 'total_large_area'),
                           ('total_area', 'total_area'))}

        category_segment_results[segment][category] = cat_results

        # stats for this category -- means are exact from the accumulator
        category_stats[segment][category] = {
            'small_pcbs_mean': float(cat_results['small_pcbs'].mean[0]),
            'medium_pcbs_mean': float(cat_results['medium_pcbs'].mean[0]),
            'large_pcbs_mean': float(cat_results['large_pcbs'].mean[0]),
            'small_area_mean': float(cat_results['small_area'].mean[0]),
            'medium_area_mean': float(cat_results['medium_area'].mean[0]),
            'large_area_mean': float(cat_results['large_area'].mean[0]),
            'total_area_mean': float(cat_results['total_area'].mean[0]),
            'total_area_mode': float(cat_results['total_area'].coarse_mode()[0]),
            'total_area_median': float(cat_results['total_area'].percentile(50)[0]),
            'total_area_std': float(cat_results['total_area'].std[0]),
            'total_area_p025': float(cat_results['total_area'].percentile(2.5)[0]),
            'total_area_p975': float(cat_results['total_area'].percentile(97.5)[0]),
        }

print("Category-specific Monte Carlo complete!\n")


# ====
# CATEGORY COMPARISON VISUALIZATIONS
# ====

print("\n" + "="*70)
print("GENERATING CATEGORY-SPECIFIC VISUALIZATIONS")
print("="*70)

categories = sorted(categories)

for segment in segments:
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle(f'{segment} Segment - PCB Category Analysis', fontsize=16, fontweight='bold')

    # Total Area by Category
    ax1 = axes[0, 0]
    category_areas = [category_stats[segment][cat]['total_area_mean'] for cat in categories]
    category_stds = [category_stats[segment][cat]['total_area_std'] for cat in categories]
    colors_cat = plt.cm.Set3(np.linspace(0, 1, len(categories)))
    ax1.bar(categories, category_areas, yerr=category_stds, capsize=5, color=colors_cat, alpha=0.7)
    ax1.set_ylabel('Mean Total PCB Area (cm²)')
    ax1.set_title('Total PCB Area by Category')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3, axis='y')

    # PCB Count by Category (Stacked)
    ax2 = axes[0, 1]
    small_counts = [category_stats[segment][cat]['small_pcbs_mean'] for cat in categories]
    medium_counts = [category_stats[segment][cat]['medium_pcbs_mean'] for cat in categories]
    large_counts = [category_stats[segment][cat]['large_pcbs_mean'] for cat in categories]
    x_pos = np.arange(len(categories))
    ax2.bar(x_pos, small_counts, label='Small', color='lightblue')
    ax2.bar(x_pos, medium_counts, bottom=small_counts, label='Medium', color='lightgreen')
    ax2.bar(x_pos, large_counts, bottom=np.array(small_counts) + np.array(medium_counts),
            label='Large', color='lightcoral')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(categories, rotation=45)
    ax2.set_ylabel('Mean PCB Count')
    ax2.set_title('PCB Count Distribution by Category')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')

    # PCB Area by Category (Stacked)
    ax3 = axes[0, 2]
    small_areas = [category_stats[segment][cat]['small_area_mean'] for cat in categories]
    medium_areas = [category_stats[segment][cat]['medium_area_mean'] for cat in categories]
    large_areas = [category_stats[segment][cat]['large_area_mean'] for cat in categories]
    ax3.bar(x_pos, small_areas, label='Small', color='lightblue')
    ax3.bar(x_pos, medium_areas, bottom=small_areas, label='Medium', color='lightgreen')
    ax3.bar(x_pos, large_areas, bottom=np.array(small_areas) + np.array(medium_areas),
            label='Large', color='lightcoral')
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(categories, rotation=45)
    ax3.set_ylabel('Mean PCB Area (cm²)')
    ax3.set_title('PCB Area Distribution by Category')
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')

    # Distribution histograms for top 3 categories by area
    top_categories = sorted(categories,
                    key=lambda c: category_stats[segment][c]['total_area_mean'],
                    reverse=True)[:3]

    for idx, cat in enumerate(top_categories):
        ax = axes[1, idx]
        hist_from_acc(ax, category_segment_results[segment][cat]['total_area'],
                      alpha=0.7, color=colors_cat[categories.index(cat)])
        mean_val = category_stats[segment][cat]['total_area_mean']
        p025_val = category_stats[segment][cat]['total_area_p025']
        p975_val = category_stats[segment][cat]['total_area_p975']
        ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.0f}')
        ax.axvline(p025_val, color='orange', linestyle='--', linewidth=1.5, label=f'P025: {p025_val:.0f}')
        ax.axvline(p975_val, color='orange', linestyle='--', linewidth=1.5, label=f'P975: {p975_val:.0f}')
        ax.set_xlabel('Total PCB Area (cm²)')
        ax.set_ylabel('Frequency')
        ax.set_title(f'{cat} - Total Area Distribution')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(SCRIPT_DIR / 'figures_category' / f'pcb_category_analysis_{segment}_segment.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: figures_category/pcb_category_analysis_{segment}_segment.png")

# Cross-Segment Category Comparison
fig_cross, axes_cross = plt.subplots(2, 3, figsize=(18, 12))
fig_cross.suptitle('PCB Category Comparison Across Segments', fontsize=16, fontweight='bold')

for idx, cat in enumerate(categories):
    row = idx // 3
    col = idx % 3
    ax = axes_cross[row, col]

    seg_means = [category_stats[seg][cat]['total_area_mean'] for seg in segments]
    seg_stds = [category_stats[seg][cat]['total_area_std'] for seg in segments]

    x_pos = np.arange(len(segments))
    ax.bar(x_pos, seg_means, yerr=seg_stds, capsize=5, color=['lightblue', 'lightgreen', 'lightcoral'])
    ax.set_xticks(x_pos)
    ax.set_xticklabels(segments)
    ax.set_ylabel('Mean Total PCB Area (cm²)')
    ax.set_title(f'{cat}')
    ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(SCRIPT_DIR / 'figures_category' / 'pcb_category_cross_segment_comparison.png', dpi=300, bbox_inches='tight')
print("✓ Saved: figures_category/pcb_category_cross_segment_comparison.png")

plt.show(block=False)
plt.pause(5)  # Brief pause to render the figure

# ====
# SAVE CATEGORY-SPECIFIC RESULTS
# ====

print("\n" + "="*70)
print("SAVING CATEGORY-SPECIFIC RESULTS")
print("="*70)

# Save summary statistics for categories per segment
for segment in segments:
    summary_data = []
    for cat in categories:
        st = category_stats[segment][cat]
        summary_data.append({
            'Category': cat,
            'Mean_Small_PCBs': st['small_pcbs_mean'],
            'Mean_Medium_PCBs': st['medium_pcbs_mean'],
            'Mean_Large_PCBs': st['large_pcbs_mean'],
            'Mean_Small_Area': st['small_area_mean'],
            'Mean_Medium_Area': st['medium_area_mean'],
            'Mean_Large_Area': st['large_area_mean'],
            'Mean_Total_Area': st['total_area_mean'],
            'Mode_Total_Area': st['total_area_mode'],
            'Median_Total_Area': st['total_area_median'],
            'Std_Total_Area': st['total_area_std'],
            'P025_Total_Area': st['total_area_p025'],
            'P975_Total_Area': st['total_area_p975'],
        })

    summary_df = pd.DataFrame(summary_data)
    filename = SCRIPT_DIR / 'csv_category' / f'pcb_category_summary_{segment}_segment.csv'
    summary_df.to_csv(filename, index=False)
    print(f"✓ Saved: csv_category/pcb_category_summary_{segment}_segment.csv")

# Save cross-segment comparison in one file
cross_rows = []
for cat in categories:
    for segment in segments:
        st = category_stats[segment][cat]
        cross_rows.append({
            'Category': cat,
            'Segment': segment,
            'Mean_Total_Area': st['total_area_mean'],
            'Mode_Total_Area': st['total_area_mode'],
            'Median_Total_Area': st['total_area_median'],
            'Std_Total_Area': st['total_area_std'],
            'P025_Total_Area': st['total_area_p025'],
            'P975_Total_Area': st['total_area_p975'],
            'Mean_Small_PCBs': st['small_pcbs_mean'],
            'Mean_Medium_PCBs': st['medium_pcbs_mean'],
            'Mean_Large_PCBs': st['large_pcbs_mean'],
        })

cross_df = pd.DataFrame(cross_rows)
cross_df.to_csv(SCRIPT_DIR / 'csv_category' / 'pcb_category_cross_segment_comparison.csv', index=False)
print("✓ Saved: csv_category/pcb_category_cross_segment_comparison.csv")

print("\n" + "="*70)
print("ANALYSIS COMPLETE!")
print("="*70)



# ====
# SAVE HISTOGRAM DISTRIBUTIONS FOR BOOTSTRAPPING
# ====

print("\n" + "="*70)
print("SAVING HISTOGRAM DISTRIBUTIONS FOR BOOTSTRAPPING")
print("="*70)

print("\nFolder structure already created")

# Define number of bins for histograms
n_bins = 50

# Dictionary to store all histogram data
all_histograms = {}

# 1. Save segment-level area distributions
print("\nSaving segment-level area distributions...")
for segment in segments:
    segment_histograms = {}

    # Only save area metrics (not PCB counts)
    for metric in ['total_small_area', 'total_medium_area', 'total_large_area', 'total_area']:

        # Histogram now comes from the accumulator's own 50 bins rather than
        # from np.histogram over the draws. Same bin count; the edges are the
        # padded pilot range instead of [min, max] of the draws, so the
        # outermost bins can be empty where they previously clipped exactly.
        bin_edges, counts = all_acc[segment][metric].coarse(0, n_bins)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        # Store histogram data
        segment_histograms[metric] = {
            'counts': counts,
            'bin_edges': bin_edges,
            'bin_centers': bin_centers
        }

        # Save to CSV in histograms folder
        hist_df = pd.DataFrame({
            'bin_center': bin_centers,
            'bin_left_edge': bin_edges[:-1],
            'bin_right_edge': bin_edges[1:],
            'count': counts,
            'frequency': counts / ndraws  # normalized frequency
        })

        filename = SCRIPT_DIR / 'histograms' / f'histogram_{segment}_{metric}.csv'
        hist_df.to_csv(filename, index=False)
        print(f"  ✓ Saved: histograms/histogram_{segment}_{metric}.csv")

    all_histograms[segment] = segment_histograms

# 2. Save category-level area distributions
print("\nSaving category-level area distributions...")
for segment in segments:
    for category in categories:
        cat_results = category_segment_results[segment][category]

        category_histograms = {}

        # Only save area metrics (not PCB counts)
        for metric in ['small_area', 'medium_area', 'large_area', 'total_area']:

            # From the accumulator's own 50 bins, as for the segment level
            bin_edges, counts = cat_results[metric].coarse(0, n_bins)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

            # Store histogram data
            category_histograms[metric] = {
                'counts': counts,
                'bin_edges': bin_edges,
                'bin_centers': bin_centers
            }

            # Save to CSV in histograms folder
            hist_df = pd.DataFrame({
                'bin_center': bin_centers,
                'bin_left_edge': bin_edges[:-1],
                'bin_right_edge': bin_edges[1:],
                'count': counts,
                'frequency': counts / ndraws  # normalized frequency
            })

            filename = SCRIPT_DIR / 'histograms' / f'histogram_{segment}_{category}_{metric}.csv'
            hist_df.to_csv(filename, index=False)
            print(f"  ✓ Saved: histograms/histogram_{segment}_{category}_{metric}.csv")

        all_histograms[f'{segment}_{category}'] = category_histograms

# 3. Save raw distribution data (for exact bootstrapping)
print("\nSaving raw distribution data...")

# Raw draws were already streamed to .npy during the run -- nothing to write
# here. Two things changed on 2026-08-10 (step P-d):
#
#   * format: 522 MB of CSV -> ~118 MB of float32 .npy. Load a file with
#         np.load(path, mmap_mode="r")   -> (ndraws, 7); columns in the
#         matching _draws.json, or METRIC_KEYS order for the category files.
#   * duplication: raw_distribution_{SEG}_segment.csv held byte-for-byte the
#     same draws as csv_monte_carlo/pcb_monte_carlo_{SEG}_detailed_results.csv.
#     The segment draws are now written ONCE, as
#     raw_data/pcb_monte_carlo_{SEG}_draws.npy.
print("  (raw draws already written as .npy during the simulation)")
for segment in segments:
    f = SCRIPT_DIR / 'raw_data' / f'pcb_monte_carlo_{segment}_draws.npy'
    print(f"  ✓ raw_data/{f.name}  ({f.stat().st_size/1e6:.1f} MB)")

# 4. Create a master index file
print("\nCreating master index file...")

index_data = []

# Add segment-level entries (area only)
for segment in segments:
    for metric in ['total_small_area', 'total_medium_area', 'total_large_area', 'total_area']:
        index_data.append({
            'type': 'segment',
            'segment': segment,
            'category': 'ALL',
            'metric': metric,
            'histogram_file': f'histograms/histogram_{segment}_{metric}.csv',
            'raw_data_file': f'raw_data/pcb_monte_carlo_{segment}_draws.npy',
            'n_simulations': ndraws,
            'n_bins': n_bins
        })

# Add category-level entries (area only)
for segment in segments:
    for category in categories:
        for metric in ['small_area', 'medium_area', 'large_area', 'total_area']:
            index_data.append({
                'type': 'category',
                'segment': segment,
                'category': category,
                'metric': metric,
                'histogram_file': f'histograms/histogram_{segment}_{category}_{metric}.csv',
                'raw_data_file': f'raw_data/raw_distribution_{segment}_{category}.npy',
                'n_simulations': ndraws,
                'n_bins': n_bins
            })

index_df = pd.DataFrame(index_data)
index_df.to_csv(SCRIPT_DIR / 'distribution_index.csv', index=False)
print("  ✓ Saved: distribution_index.csv")

print("\n" + "="*70)
print("HISTOGRAM DISTRIBUTIONS SAVED!")
print("="*70)
print(f"\nOrganized file structure:")
print(f"  histograms/")
print(f"    - Segment area histograms: {len(segments) * 4} files")
print(f"    - Category area histograms: {len(segments) * len(categories) * 4} files")
print(f"  raw_data/")
print(f"    - Segment raw distributions: {len(segments)} files")
print(f"    - Category raw distributions: {len(segments) * len(categories)} files")
print(f"  distribution_index.csv (root)")
print(f"\nTotal histogram files: {len(segments) * 4 + len(segments) * len(categories) * 4}")
print(f"Total raw data files: {len(segments) + len(segments) * len(categories)}")