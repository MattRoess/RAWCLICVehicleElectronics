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
- pcb_monte_carlo_{SEG}_detailed_results.csv (per segment)
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
"""

import os
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


# ====
# MONTE CARLO SIMULATION - ALL SEGMENTS
# ====

segments = ['AB', 'CD', 'EF']
ndraws = 200000

all_segment_results = {}

for segment in segments:
    print("\n" + "="*70)
    print(f"RUNNING MONTE CARLO SIMULATION FOR {segment} SEGMENT")
    print("="*70)
    print(f"Number of simulations: {ndraws:,}\n")

    results = run_batch_simulation(pcb_dist, segment, ndraws)

    all_segment_results[segment] = results
    print(f"\n{segment} Simulation complete!\n")


# ====
# CALCULATE STATISTICS FOR ALL SEGMENTS
# ====

def approx_mode(x, bins=200):
    """Approximate mode for continuous data using the highest-count histogram bin."""
    counts, edges = np.histogram(x, bins=bins)
    i = np.argmax(counts)
    return 0.5 * (edges[i] + edges[i + 1])

all_stats = {}

for segment in segments:
    results = all_segment_results[segment]
    stats = {}

    for key, values in results.items():
        stats[key] = {
            'mean': np.mean(values),
            'mode' : approx_mode(values, bins=200),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'p025': np.percentile(values, 2.5),
            'p25': np.percentile(values, 25),
            'p50': np.percentile(values, 50),
            'p75': np.percentile(values, 75),
            'p975': np.percentile(values, 97.5)
        }

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
    results = all_segment_results[segment]

    print(f"\n{segment} SEGMENT:")
    print("-" * 70)

    total_var = np.var(results['total_area'])
    small_area_contribution = np.var(results['total_small_area']) / total_var if total_var > 0 else np.nan
    medium_area_contribution = np.var(results['total_medium_area']) / total_var if total_var > 0 else np.nan
    large_area_contribution = np.var(results['total_large_area']) / total_var if total_var > 0 else np.nan

    print("\nVariance Contribution to Total PCB Area:")
    print(f"  Small PCBs:  {small_area_contribution*100:>6.2f}%")
    print(f"  Medium PCBs: {medium_area_contribution*100:>6.2f}%")
    print(f"  Large PCBs:  {large_area_contribution*100:>6.2f}%")

    print("\nCorrelation with Total Area:")
    correlations = {}
    for key in ['total_small_area', 'total_medium_area', 'total_large_area']:
        corr = np.corrcoef(results[key], results['total_area'])[0, 1]
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
    ax1.hist(all_segment_results[segment]['total_area'], bins=50, alpha=0.5,
             label=f'{segment} Segment')
ax1.set_xlabel('Total PCB Area (cm²)')
ax1.set_ylabel('Frequency')
ax1.set_title('Total PCB Area Distribution by Segment')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Box Plot Comparison
ax2 = axes[0, 1]
box_data = [all_segment_results[seg]['total_area'] for seg in segments]
bp = ax2.boxplot(box_data, tick_labels=segments, patch_artist=True)
colors = ['lightblue', 'lightgreen', 'lightcoral']
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
ax2.set_ylabel('Total PCB Area (cm²)')
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
    results = all_segment_results[segment]
    stats = all_stats[segment]

    fig2, axes2 = plt.subplots(2, 2, figsize=(14, 10))
    fig2.suptitle(f'PCB Monte Carlo Results - {segment} Segment', fontsize=16, fontweight='bold')

    ax1 = axes2[0, 0]
    ax1.hist(results['total_small_pcbs'], bins=50, alpha=0.6, label='Small', color='blue')
    ax1.hist(results['total_medium_pcbs'], bins=50, alpha=0.6, label='Medium', color='green')
    ax1.hist(results['total_large_pcbs'], bins=50, alpha=0.6, label='Large', color='red')
    ax1.set_xlabel('Number of PCBs')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Distribution of PCB Counts by Size')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2 = axes2[0, 1]
    ax2.hist(results['total_small_area'], bins=50, alpha=0.6, label='Small', color='blue')
    ax2.hist(results['total_medium_area'], bins=50, alpha=0.6, label='Medium', color='green')
    ax2.hist(results['total_large_area'], bins=50, alpha=0.6, label='Large', color='red')
    ax2.set_xlabel('Total Area (cm²)')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Distribution of PCB Areas by Size')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    ax3 = axes2[1, 0]
    ax3.hist(results['total_area'], bins=50, alpha=0.7, color='purple')
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
    box_data = [results['total_small_area'], results['total_medium_area'], results['total_large_area']]
    bp = ax4.boxplot(box_data, tick_labels=['Small', 'Medium', 'Large'], patch_artist=True)
    colors_box = ['lightblue', 'lightgreen', 'lightcoral']
    for patch, color in zip(bp['boxes'], colors_box):
        patch.set_facecolor(color)
    ax4.set_ylabel('Total Area (cm²)')
    ax4.set_title('PCB Area Distribution by Size Category')
    ax4.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(SCRIPT_DIR / 'figures_monte_carlo' / f'pcb_monte_carlo_{segment}_segment.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: figures_monte_carlo/pcb_monte_carlo_{segment}_segment.png")

# Figure 3: Sensitivity Analysis by Segment
fig3, axes3 = plt.subplots(2, 3, figsize=(18, 12))
fig3.suptitle('Sensitivity Analysis by Segment', fontsize=16, fontweight='bold')

for idx, segment in enumerate(segments):
    results = all_segment_results[segment]
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
    results_df = pd.DataFrame(all_segment_results[segment])
    results_df.to_csv(SCRIPT_DIR / 'csv_monte_carlo' / f'pcb_monte_carlo_{segment}_detailed_results.csv', index=False)
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

        batch = run_batch_simulation(category_components, segment, ndraws)

        # Map batch keys (total_small_pcbs, ...) to this block's key names (small_pcbs, ...)
        cat_results = {
            'small_pcbs': batch['total_small_pcbs'],
            'medium_pcbs': batch['total_medium_pcbs'],
            'large_pcbs': batch['total_large_pcbs'],
            'small_area': batch['total_small_area'],
            'medium_area': batch['total_medium_area'],
            'large_area': batch['total_large_area'],
            'total_area': batch['total_area']
        }

        category_segment_results[segment][category] = cat_results

        # stats for this category
        category_stats[segment][category] = {
            'small_pcbs_mean': np.mean(cat_results['small_pcbs']),
            'medium_pcbs_mean': np.mean(cat_results['medium_pcbs']),
            'large_pcbs_mean': np.mean(cat_results['large_pcbs']),
            'small_area_mean': np.mean(cat_results['small_area']),
            'medium_area_mean': np.mean(cat_results['medium_area']),
            'large_area_mean': np.mean(cat_results['large_area']),
            'total_area_mean': np.mean(cat_results['total_area']),
            'total_area_mode' : approx_mode(cat_results['total_area'], bins=200),
            'total_area_median' : np.percentile(cat_results['total_area'], 50),
            'total_area_std': np.std(cat_results['total_area']),
            'total_area_p025': np.percentile(cat_results['total_area'], 2.5),
            'total_area_p975': np.percentile(cat_results['total_area'], 97.5),
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
        dist = category_segment_results[segment][cat]['total_area']
        ax.hist(dist, bins=50, alpha=0.7, color=colors_cat[categories.index(cat)])
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
    results = all_segment_results[segment]

    segment_histograms = {}

    # Only save area metrics (not PCB counts)
    for metric in ['total_small_area', 'total_medium_area', 'total_large_area', 'total_area']:

        # Calculate histogram
        counts, bin_edges = np.histogram(results[metric], bins=n_bins)
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

            # Calculate histogram
            counts, bin_edges = np.histogram(cat_results[metric], bins=n_bins)
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

# Segment-level raw data
for segment in segments:
    results_df = pd.DataFrame(all_segment_results[segment])
    filename = SCRIPT_DIR / 'raw_data' / f'raw_distribution_{segment}_segment.csv'
    results_df.to_csv(filename, index=False)
    print(f"  ✓ Saved: raw_data/raw_distribution_{segment}_segment.csv")

# Category-level raw data
for segment in segments:
    for category in categories:
        cat_results_df = pd.DataFrame(category_segment_results[segment][category])
        filename = SCRIPT_DIR / 'raw_data' / f'raw_distribution_{segment}_{category}.csv'
        cat_results_df.to_csv(filename, index=False)
        print(f"  ✓ Saved: raw_data/raw_distribution_{segment}_{category}.csv")

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
            'raw_data_file': f'raw_data/raw_distribution_{segment}_segment.csv',
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
                'raw_data_file': f'raw_data/raw_distribution_{segment}_{category}.csv',
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