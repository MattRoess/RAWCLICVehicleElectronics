"""
PCB Element Composition Monte Carlo Simulation - COMPLETE VERSION (FIXED)
================================================================================

This script performs comprehensive Monte Carlo simulation for element composition in PCBs.
FIXED: Correctly parses histogram filenames with multi-word category names (e.g., PE_HVS).
UPDATED: All mass outputs now in grams (g) instead of milligrams (mg).

Author: Generated for BEV Electronics Analysis
Date: 2026-02-13
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from scipy.stats import triang
import seaborn as sns
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

# ============================================================================
# PATH HANDLING (ROBUST)
# ============================================================================

# Get the absolute path of the directory where THIS script is located
SCRIPT_DIR = Path(__file__).resolve().parent

# Define paths relative to the script location
BASE_DIR = SCRIPT_DIR.parent
HISTOGRAM_FOLDER = BASE_DIR / "PCBAreaMC" / "histograms"
COMPOSITION_FILE = BASE_DIR / "Data" / "04_VehiclePCBComposition.xlsx"

# Output folders (created inside PCBElementMC/)
OUTPUT_FOLDERS = {
    'figures_all_combinations': SCRIPT_DIR / 'figures_all_combinations',
    'figures_grand_totals': SCRIPT_DIR / 'figures_grand_totals',
    'figures_sensitivity_detailed': SCRIPT_DIR / 'figures_sensitivity_detailed',
    'csv_results': SCRIPT_DIR / 'csv_results',
    'csv_grand_totals': SCRIPT_DIR / 'csv_grand_totals',
    'csv_sensitivity': SCRIPT_DIR / 'csv_sensitivity'
}

# ============================================================================
# CONFIGURATION
# ============================================================================

# Monte Carlo parameters
N_SIMULATIONS = 100000

# Segments, categories, and sizes
SEGMENTS = ['AB', 'CD', 'EF']
CATEGORIES = ['BMS', 'PE_HVS', 'VCC', 'ITC', 'SSS', 'MLIS']
SIZES = ['small', 'medium', 'large']

# ============================================================================
# SETUP
# ============================================================================

print("="*80)
print("PCB ELEMENT COMPOSITION MONTE CARLO SIMULATION - COMPLETE VERSION")
print("="*80)
print(f"\nScript location: {SCRIPT_DIR}")
print(f"Base directory: {BASE_DIR}")

# Create output folders
print("\nCreating output folder structure...")
for folder_name, folder_path in OUTPUT_FOLDERS.items():
    os.makedirs(folder_path, exist_ok=True)
    print(f"  ✓ {folder_path.name}/")

# ============================================================================
# LOAD DATA
# ============================================================================

print("\n" + "="*80)
print("LOADING DATA")
print("="*80)

# Load composition data
print(f"\nLoading composition data from:\n  {COMPOSITION_FILE}")
if not COMPOSITION_FILE.exists():
    raise FileNotFoundError(f"Composition file not found: {COMPOSITION_FILE}")

composition_df = pd.read_excel(COMPOSITION_FILE)

# Clean column names and values
composition_df.columns = composition_df.columns.str.strip()
composition_df['PCBCategory'] = composition_df['PCBCategory'].str.strip()
composition_df['Element'] = composition_df['Element'].str.strip()

print(f"  ✓ Loaded {len(composition_df)} rows")
print(f"  ✓ Columns: {composition_df.columns.tolist()}")
print(f"  ✓ PCB Categories: {composition_df['PCBCategory'].unique().tolist()}")
print(f"  ✓ Elements: {composition_df['Element'].unique().tolist()}")

# Load histogram files
print(f"\nLoading histogram files from:\n  {HISTOGRAM_FOLDER}")
if not HISTOGRAM_FOLDER.exists():
    raise FileNotFoundError(f"Histogram folder not found: {HISTOGRAM_FOLDER}")

histogram_files = list(HISTOGRAM_FOLDER.glob('histogram_*.csv'))
print(f"  ✓ Found {len(histogram_files)} histogram files")

if len(histogram_files) == 0:
    raise FileNotFoundError(f"No histogram files found in {HISTOGRAM_FOLDER}")

# Parse histogram files into a dictionary
# FIXED: Handle multi-word category names like PE_HVS
histograms = {}
print("\nParsing histogram files...")

for file_path in histogram_files:
    filename = file_path.stem
    # Remove 'histogram_' prefix
    parts = filename.replace('histogram_', '').split('_')

    # Expected format: histogram_SEGMENT_CATEGORY_SIZE_area
    # Example: histogram_AB_PE_HVS_large_area -> ['AB', 'PE', 'HVS', 'large', 'area']

    if len(parts) < 4:
        print(f"  ⚠ Skipping malformed filename: {filename}")
        continue

    # Last part should be 'area'
    if parts[-1] != 'area':
        print(f"  ⚠ Skipping (no 'area' suffix): {filename}")
        continue

    # Second to last is the size
    size = parts[-2]

    if size not in SIZES:
        print(f"  ⚠ Skipping (invalid size '{size}'): {filename}")
        continue

    # First part is the segment
    segment = parts[0]

    if segment not in SEGMENTS:
        print(f"  ⚠ Skipping (invalid segment '{segment}'): {filename}")
        continue

    # Everything between segment and size is the category
    # Join with underscore to reconstruct multi-word categories
    category = '_'.join(parts[1:-2])

    if category not in CATEGORIES:
        print(f"  ⚠ Skipping (unknown category '{category}'): {filename}")
        continue

    # Store the histogram
    key = (segment, category, size)
    histograms[key] = pd.read_csv(file_path)
    print(f"  ✓ Parsed: {segment} | {category} | {size}")

print(f"\n  ✓ Successfully parsed {len(histograms)} histogram distributions")

# Get list of all elements
ALL_ELEMENTS = composition_df['Element'].unique().tolist()
print(f"  ✓ Total unique elements: {len(ALL_ELEMENTS)}")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def bootstrap_from_histogram(hist_df, n_samples=1):
    """
    Bootstrap samples from a histogram distribution.

    Parameters:
    -----------
    hist_df : DataFrame
        Histogram data with columns: bin_center, frequency
    n_samples : int
        Number of samples to generate

    Returns:
    --------
    samples : array
        Bootstrap samples
    """
    valid_bins = hist_df[hist_df['frequency'] > 0].copy()

    if len(valid_bins) == 0:
        return np.zeros(n_samples)

    bin_centers = valid_bins['bin_center'].values
    frequencies = valid_bins['frequency'].values

    # Normalize frequencies
    frequencies = frequencies / frequencies.sum()

    # Sample from the distribution
    samples = np.random.choice(bin_centers, size=n_samples, p=frequencies)

    return samples


def sample_triangular(min_val, mode_val, max_val, n_samples=1):
    """
    Sample from a triangular distribution.

    Parameters:
    -----------
    min_val : float
        Minimum value (left)
    mode_val : float
        Mode value (peak)
    max_val : float
        Maximum value (right)
    n_samples : int
        Number of samples

    Returns:
    --------
    samples : array
        Samples from triangular distribution
    """
    if max_val == min_val:
        return np.full(n_samples, mode_val)

    c = (mode_val - min_val) / (max_val - min_val)

    # Sample from triangular distribution
    samples = triang.rvs(c, loc=min_val, scale=max_val - min_val, size=n_samples)

    return samples


def approx_mode(x, bins=200):
    """Approximate mode for continuous data using the highest-count histogram bin."""
    counts, edges = np.histogram(x, bins=bins)
    i = np.argmax(counts)
    return 0.5 * (edges[i] + edges[i + 1])


# ============================================================================
# MAIN SIMULATION LOOP
# ============================================================================

print("\n" + "="*80)
print("RUNNING MONTE CARLO SIMULATIONS")
print("="*80)

# Storage for all results
results_storage = {}  # (segment, category, size) -> DataFrame
sensitivity_data = []

# Counter for progress
total_combinations = len(SEGMENTS) * len(CATEGORIES) * len(SIZES)
completed = 0

for segment in SEGMENTS:
    print(f"\n{'='*80}")
    print(f"SEGMENT: {segment}")
    print(f"{'='*80}")

    for category in CATEGORIES:
        print(f"\n  Category: {category}")

        for size in SIZES:
            key = (segment, category, size)

            # Check if histogram exists
            if key not in histograms:
                print(f"    Size: {size}... ⚠ No histogram found, skipping")
                completed += 1
                continue

            print(f"    Size: {size}...", end=" ")

            # Get composition data for this category
            comp_data = composition_df[composition_df['PCBCategory'] == category].copy()

            if comp_data.empty:
                print(f"⚠ No composition data, skipping")
                completed += 1
                continue

            # Get histogram
            hist_df = histograms[key]

            # Bootstrap PCB areas
            area_samples = bootstrap_from_histogram(hist_df, N_SIMULATIONS)

            # Initialize results DataFrame
            sim_df = pd.DataFrame({'area_cm2': area_samples})

            # Sample element concentrations and calculate masses
            for _, row in comp_data.iterrows():
                element = row['Element']
                min_val = row['mg_cm2_min']
                mode_val = row['mg_cm2_mode']
                max_val = row['mg_cm2_max']

                # Sample concentration (mg/cm²)
                conc_samples = sample_triangular(min_val, mode_val, max_val, N_SIMULATIONS)

                # Calculate total mass in mg, then convert to grams
                mass_samples_mg = conc_samples * area_samples
                mass_samples_g = mass_samples_mg / 1000.0  # Convert mg to g

                # Store in DataFrame (concentration still in mg/cm², mass in g)
                sim_df[f'{element}_conc_mg_cm2'] = conc_samples
                sim_df[f'{element}_mass_g'] = mass_samples_g

                # Calculate sensitivity (Contribution to Variance)
                # Using Spearman correlation to measure influence
                corr_area, _ = stats.spearmanr(area_samples, mass_samples_g)
                corr_conc, _ = stats.spearmanr(conc_samples, mass_samples_g)

                # Normalize contributions
                total_sq = (corr_area**2) + (corr_conc**2)

                if total_sq > 0:
                    area_contrib = (corr_area**2) / total_sq
                    conc_contrib = (corr_conc**2) / total_sq
                else:
                    area_contrib = 0
                    conc_contrib = 0

                sensitivity_data.append({
                    'Segment': segment,
                    'Category': category,
                    'Size': size,
                    'Element': element,
                    'Area_Contribution': area_contrib,
                    'Concentration_Contribution': conc_contrib,
                    'Corr_Area': corr_area,
                    'Corr_Concentration': corr_conc
                })

            # Store results
            results_storage[key] = sim_df

            completed += 1
            print(f"✓ Completed ({completed}/{total_combinations})")

print("\n" + "="*80)
print("MONTE CARLO SIMULATIONS COMPLETED")
print("="*80)
print(f"  ✓ Total combinations simulated: {len(results_storage)}")

# ============================================================================
# CALCULATE GRAND TOTALS
# ============================================================================

print("\n" + "="*80)
print("CALCULATING GRAND TOTALS")
print("="*80)

# Grand totals structure:
# grand_totals[size][segment][element] = array of N_SIMULATIONS values
# size can be: 'small', 'medium', 'large', or 'Total'

grand_totals = {}

# Initialize structure
for size in SIZES + ['Total']:
    grand_totals[size] = {}
    for segment in SEGMENTS:
        grand_totals[size][segment] = {el: np.zeros(N_SIMULATIONS) for el in ALL_ELEMENTS}

# Accumulate masses
for segment in SEGMENTS:
    print(f"  Processing segment: {segment}")

    # Segment total (all sizes combined)
    segment_total = {el: np.zeros(N_SIMULATIONS) for el in ALL_ELEMENTS}

    for size in SIZES:
        # Size total (all categories combined)
        size_total = {el: np.zeros(N_SIMULATIONS) for el in ALL_ELEMENTS}

        for category in CATEGORIES:
            key = (segment, category, size)

            if key not in results_storage:
                continue

            df = results_storage[key]

            for element in ALL_ELEMENTS:
                col = f'{element}_mass_g'
                if col in df.columns:
                    mass_values = df[col].values
                    size_total[element] += mass_values
                    segment_total[element] += mass_values

        # Store size total
        grand_totals[size][segment] = size_total

    # Store segment total
    grand_totals['Total'][segment] = segment_total

print("  ✓ Grand totals calculated")

# ============================================================================
# SAVE RESULTS TO CSV
# ============================================================================

print("\n" + "="*80)
print("SAVING RESULTS TO CSV")
print("="*80)

# Save individual combination results
print("\nSaving individual combination results...")
n_saved = 0
for key, df in results_storage.items():
    segment, category, size = key
    filename = OUTPUT_FOLDERS['csv_results'] / f'results_{segment}_{category}_{size}.csv'
    df.to_csv(filename, index=False)
    n_saved += 1
print(f"  ✓ Saved {n_saved} result files")

# Save grand totals
print("\nSaving grand totals...")
n_saved = 0
for size in SIZES + ['Total']:
    for segment in SEGMENTS:
        df = pd.DataFrame(grand_totals[size][segment])
        filename = OUTPUT_FOLDERS['csv_grand_totals'] / f'grand_total_{segment}_{size}.csv'
        df.to_csv(filename, index=False)
        n_saved += 1
print(f"  ✓ Saved {n_saved} grand total files")

# Save sensitivity analysis
print("\nSaving sensitivity analysis...")
sens_df = pd.DataFrame(sensitivity_data)
filename = OUTPUT_FOLDERS['csv_sensitivity'] / 'sensitivity_all.csv'
sens_df.to_csv(filename, index=False)
print(f"  ✓ Saved sensitivity analysis")

# Save summary statistics
print("\nSaving summary statistics...")
summary_list = []
for key, df in results_storage.items():
    segment, category, size = key
    for element in ALL_ELEMENTS:
        col = f'{element}_mass_g'
        if col in df.columns:
            values = df[col].values
            summary_list.append({
                'Segment': segment,
                'Category': category,
                'Size': size,
                'Element': element,
                'Mean_g': np.mean(values),
                'Mode_g': approx_mode(values, bins=200),
                'Median_g': np.median(values),
                'Std_g': np.std(values),
                'Min_g': np.min(values),
                'P025_g': np.percentile(values, 2.5),
                'P25_g': np.percentile(values, 25),
                'P75_g': np.percentile(values, 75),
                'P975_g': np.percentile(values, 97.5),
                'Max_g': np.max(values)
            })

summary_df = pd.DataFrame(summary_list)
filename = OUTPUT_FOLDERS['csv_results'] / 'summary_statistics.csv'
summary_df.to_csv(filename, index=False)
print(f"  ✓ Saved summary statistics ({len(summary_list)} rows)")

# ============================================================================
# GENERATE FIGURES - ALL COMBINATIONS
# ============================================================================

print("\n" + "="*80)
print("GENERATING FIGURES - ALL COMBINATIONS")
print("="*80)

sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 150

def plot_element_distributions(data_dict, title, save_path):
    """
    Plot distributions for all elements in a grid layout.
    """
    n_elements = len(data_dict)
    if n_elements == 0:
        return

    n_cols = 3
    n_rows = int(np.ceil(n_elements / n_cols))

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4*n_rows))

    if n_elements == 1:
        axes = [axes]
    else:
        axes = axes.flatten()

    for idx, (element, values) in enumerate(data_dict.items()):
        ax = axes[idx]

        # Plot histogram with KDE
        ax.hist(values, bins=50, alpha=0.6, color='skyblue', edgecolor='black', density=True)

        # Add KDE
        from scipy.stats import gaussian_kde
        if len(values) > 1 and np.std(values) > 0:
            kde = gaussian_kde(values)
            x_range = np.linspace(values.min(), values.max(), 200)
            ax.plot(x_range, kde(x_range), 'r-', linewidth=2, label='KDE')

        # Add statistics
        mean_val = np.mean(values)
        median_val = np.median(values)
        ax.axvline(mean_val, color='green', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.3f}')
        ax.axvline(median_val, color='orange', linestyle='--', linewidth=2, label=f'Median: {median_val:.3f}')

        ax.set_xlabel(f'{element} Mass (g)', fontsize=10)
        ax.set_ylabel('Density', fontsize=10)
        ax.set_title(f'{element}', fontsize=11, fontweight='bold')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    # Hide unused subplots
    for idx in range(n_elements, len(axes)):
        axes[idx].axis('off')

    plt.suptitle(title, fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()


print("\nGenerating figures for all combinations...")
n_plots = 0

for key, df in results_storage.items():
    segment, category, size = key

    # Extract element masses
    data_dict = {}
    for element in ALL_ELEMENTS:
        col = f'{element}_mass_g'
        if col in df.columns:
            data_dict[element] = df[col].values

    if len(data_dict) == 0:
        continue

    title = f'Element Mass Distribution: {segment} | {category} | {size.capitalize()}'
    save_path = OUTPUT_FOLDERS['figures_all_combinations'] / f'dist_{segment}_{category}_{size}.png'

    plot_element_distributions(data_dict, title, save_path)
    n_plots += 1

    if n_plots % 10 == 0:
        print(f"  ✓ Generated {n_plots} plots...")

print(f"  ✓ Total plots generated: {n_plots}")

# ============================================================================
# GENERATE FIGURES - GRAND TOTALS
# ============================================================================

print("\n" + "="*80)
print("GENERATING FIGURES - GRAND TOTALS")
print("="*80)

print("\nGenerating grand total figures...")
n_plots = 0

for size in SIZES + ['Total']:
    for segment in SEGMENTS:
        data_dict = grand_totals[size][segment]

        # Filter out zero elements
        data_dict_filtered = {el: vals for el, vals in data_dict.items() if np.sum(vals) > 0}

        if len(data_dict_filtered) == 0:
            continue

        title = f'Grand Total Element Mass: {segment} | Size: {size.capitalize()}'
        save_path = OUTPUT_FOLDERS['figures_grand_totals'] / f'grand_total_{segment}_{size}.png'

        plot_element_distributions(data_dict_filtered, title, save_path)
        n_plots += 1

print(f"  ✓ Total grand total plots generated: {n_plots}")

# ============================================================================
# GENERATE FIGURES - SENSITIVITY ANALYSIS
# ============================================================================

print("\n" + "="*80)
print("GENERATING FIGURES - SENSITIVITY ANALYSIS")
print("="*80)

print("\nGenerating sensitivity analysis figures...")

# Create sensitivity plots for each element
n_plots = 0

for element in ALL_ELEMENTS:
    el_sens = sens_df[sens_df['Element'] == element]

    if el_sens.empty:
        continue

    # Aggregate by category and size
    plot_data = el_sens.groupby(['Category', 'Size'])[['Area_Contribution', 'Concentration_Contribution']].mean().reset_index()
    plot_data['Label'] = plot_data['Category'] + " (" + plot_data['Size'] + ")"

    # Create stacked bar chart
    fig, ax = plt.subplots(figsize=(14, 6))

    x_pos = np.arange(len(plot_data))

    ax.bar(x_pos, plot_data['Area_Contribution'], label='Area Uncertainty', color='steelblue', alpha=0.8)
    ax.bar(x_pos, plot_data['Concentration_Contribution'], 
           bottom=plot_data['Area_Contribution'], 
           label='Composition Uncertainty', color='coral', alpha=0.8)

    ax.set_xticks(x_pos)
    ax.set_xticklabels(plot_data['Label'], rotation=45, ha='right', fontsize=9)
    ax.set_ylabel("Contribution to Variance", fontsize=11)
    ax.set_title(f"Uncertainty Source Analysis: {element}", fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim([0, 1.05])

    plt.tight_layout()
    save_path = OUTPUT_FOLDERS['figures_sensitivity_detailed'] / f'sensitivity_{element}.png'
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()

    n_plots += 1

print(f"  ✓ Total sensitivity plots generated: {n_plots}")

# ====
# ADVANCED ELEMENT-LEVEL COMPARISON
# ====

print("\n" + "="*80)
print("GENERATING ADVANCED ELEMENT COMPARISON FIGURES")
print("="*80)

element_compare_folder = SCRIPT_DIR / "figures_element_comparison_advanced"
os.makedirs(element_compare_folder, exist_ok=True)

sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 150

# ---------------------------------------------------------
# 1️⃣ KDE OVERLAY DISTRIBUTIONS (AB vs CD vs EF)
# ---------------------------------------------------------

for element in ALL_ELEMENTS:

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    axes = axes.flatten()

    for idx, size in enumerate(SIZES + ['Total']):

        ax = axes[idx]

        for segment, color in zip(SEGMENTS, ['steelblue', 'darkorange', 'seagreen']):

            values = grand_totals[size][segment][element]

            if np.sum(values) == 0:
                continue

            sns.kdeplot(values, ax=ax, label=segment,
                        fill=True, alpha=0.3, color=color)

        ax.set_title(f"{size.capitalize()} PCBs", fontsize=12, fontweight='bold')
        ax.set_xlabel("Mass (g)")
        ax.set_ylabel("Density")
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.suptitle(f"KDE Distribution Comparison\nElement: {element}",
                 fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(element_compare_folder / f"kde_comparison_{element}.png",
                bbox_inches='tight')
    plt.close()

print("  ✓ KDE distribution comparisons generated")


# ---------------------------------------------------------
# 2️⃣ MEAN ± (2.5–97.5%) UNCERTAINTY BAR PLOTS
# ---------------------------------------------------------

for element in ALL_ELEMENTS:

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    axes = axes.flatten()

    for idx, size in enumerate(SIZES + ['Total']):

        ax = axes[idx]

        means = []
        p025s = []
        p975s = []

        for segment in SEGMENTS:

            values = grand_totals[size][segment][element]

            if np.sum(values) == 0:
                means.append(0)
                p025s.append(0)
                p975s.append(0)
                continue

            means.append(np.mean(values))
            p025s.append(np.percentile(values, 5))
            p975s.append(np.percentile(values, 95))

        means = np.array(means)
        p025s = np.array(p025s)
        p975s = np.array(p975s)

        error_low = means - p025s
        error_high = p975s - means

        ax.bar(SEGMENTS, means,
               yerr=[error_low, error_high],
               capsize=6,
               color=['steelblue', 'darkorange', 'seagreen'],
               alpha=0.8)

        ax.set_title(f"{size.capitalize()} PCBs", fontsize=12, fontweight='bold')
        ax.set_ylabel("Mass (g)")
        ax.grid(True, alpha=0.3, axis='y')

    plt.suptitle(f"Mean ± 2.5–97.5% Interval\nElement: {element}",
                 fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(element_compare_folder / f"mean_interval_{element}.png",
                bbox_inches='tight')
    plt.close()

print("  ✓ Mean ± interval comparisons generated")


# ---------------------------------------------------------
# 3️⃣ VARIABILITY RANKING (TOTAL SIZE ONLY)
# ---------------------------------------------------------

print("\nGenerating variability ranking (Total PCBs)...")

ranking_data = []

for element in ALL_ELEMENTS:

    for segment in SEGMENTS:

        values = grand_totals['Total'][segment][element]

        if np.sum(values) == 0:
            continue

        std = np.std(values)
        mean = np.mean(values)

        ranking_data.append({
            "Element": element,
            "Segment": segment,
            "Mean_g": mean,
            "Std_g": std,
            "CV": std / mean if mean > 0 else 0
        })

ranking_df = pd.DataFrame(ranking_data)

# Plot coefficient of variation (uncertainty intensity)

plt.figure(figsize=(12, 6))

sns.barplot(data=ranking_df,
            x="Element",
            y="CV",
            hue="Segment")

plt.xticks(rotation=45)
plt.ylabel("Coefficient of Variation (Std / Mean)")
plt.title("Element Uncertainty Ranking (Total PCBs)")
plt.grid(True, alpha=0.3, axis='y')
plt.tight_layout()

plt.savefig(element_compare_folder / "uncertainty_ranking_total.png",
            bbox_inches='tight')
plt.close()

print("  ✓ Variability ranking generated")

print("\n" + "="*80)
print("ADVANCED ELEMENT COMPARISON COMPLETE")
print("="*80)

# ============================================================================
# ADD AGGREGATED ROWS TO SUMMARY STATISTICS
# ============================================================================

print("\nCalculating aggregated summary statistics...")

extra_rows = []

for segment in SEGMENTS:
    for element in ALL_ELEMENTS:

        # ------------------------------------------------------------------
        # 1) Size totals: sum small+medium+large, per Segment × Category
        # ------------------------------------------------------------------
        for category in CATEGORIES:
            combined = np.zeros(N_SIMULATIONS)
            for size in SIZES:
                key = (segment, category, size)
                if key not in results_storage:
                    continue
                col = f'{element}_mass_g'
                if col in results_storage[key].columns:
                    combined += results_storage[key][col].values

            if np.sum(combined) == 0:
                continue

            extra_rows.append({
                'Segment':  segment,
                'Category': category,
                'Size':     'all',
                'Element':  element,
                'Mean_g':   np.mean(combined),
                'Mode_g':   approx_mode(combined, bins=200),
                'Median_g': np.median(combined),
                'Std_g':    np.std(combined),
                'Min_g':    np.min(combined),
                'P025_g':   np.percentile(combined, 2.5),
                'P25_g':    np.percentile(combined, 25),
                'P75_g':    np.percentile(combined, 75),
                'P975_g':   np.percentile(combined, 97.5),
                'Max_g':    np.max(combined),
            })

        # ------------------------------------------------------------------
        # 2) Grand total: sum across ALL categories AND all sizes, per Segment
        # ------------------------------------------------------------------
        grand_total = np.zeros(N_SIMULATIONS)
        for category in CATEGORIES:
            for size in SIZES:
                key = (segment, category, size)
                if key not in results_storage:
                    continue
                col = f'{element}_mass_g'
                if col in results_storage[key].columns:
                    grand_total += results_storage[key][col].values

        if np.sum(grand_total) == 0:
            continue

        extra_rows.append({
            'Segment':  segment,
            'Category': 'TOTAL',
            'Size':     'all',
            'Element':  element,
            'Mean_g':   np.mean(grand_total),
            'Mode_g':   approx_mode(grand_total, bins=200),
            'Median_g': np.median(grand_total),
            'Std_g':    np.std(grand_total),
            'Min_g':    np.min(grand_total),
            'P025_g':   np.percentile(grand_total, 2.5),
            'P25_g':    np.percentile(grand_total, 25),
            'P75_g':    np.percentile(grand_total, 75),
            'P975_g':   np.percentile(grand_total, 97.5),
            'Max_g':    np.max(grand_total),
        })

# Append and re-save
extra_df = pd.DataFrame(extra_rows)
summary_df_extended = pd.concat([summary_df, extra_df], ignore_index=True)

filename = OUTPUT_FOLDERS['csv_results'] / 'summary_statistics.csv'
summary_df_extended.to_csv(filename, index=False)
print(f"  ✓ Added {len(extra_rows)} aggregated rows")
print(f"  ✓ Total rows in summary_statistics.csv: {len(summary_df_extended)}")


# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "="*80)
print("SIMULATION COMPLETE")
print("="*80)
print(f"\nTotal simulations per configuration: {N_SIMULATIONS:,}")
print(f"Segments analyzed: {len(SEGMENTS)}")
print(f"Categories analyzed: {len(CATEGORIES)}")
print(f"Sizes analyzed: {len(SIZES)}")
print(f"Elements tracked: {len(ALL_ELEMENTS)}")
print(f"\nOutput folders:")
for folder_name, folder_path in OUTPUT_FOLDERS.items():
    n_files = len(list(folder_path.glob('*')))
    print(f"  {folder_path.name}/: {n_files} files")

print("\n" + "="*80)
print("DONE!")
print("="*80)
