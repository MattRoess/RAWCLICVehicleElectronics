"""
Monte Carlo Simulation for BEV Sensor Counts by Segment
Pure NumPy/Pandas implementation (mirrors the structure of PCBAreaMC.py)

Inputs:
- Data/BEV_Electronics_Verified.xlsx  (all tabs; Domain/Component status per segment: Std/Opt/Rare/-)
- Data/BEV_Sensor_Types_List-3.xlsx   (first tab "Sensor Counts Detail" only; Domain/Component/SensorType
                                        min-max sensor counts per segment, rectangular/uniform distribution)

Model:
- For every (Domain, Component, SensorType) row in the sensor list, the min and max of the
  rectangular distribution are scaled by the segment's presence factor for that Domain+Component:
      Std  -> factor 1.00 (component is standard/present)
      Opt  -> factor 0.50 (component is optional)
      Rare -> factor 0.25 (component is rare)
      -    -> factor 0.00 (component is not present)
  A uniform draw is then taken between the scaled min and scaled max for that row, independently
  per Monte Carlo draw. This is done for all three segments: A-B, C-D, E-F.
- Per-row draws are then combined (summed) across all rows that share the same SensorType, within
  each Domain (and also across all Domains), giving the combined distribution of "number of sensors
  of type X" for each segment.
- A grand total (all sensor types, all domains) per segment is also produced.

Data cleaning notes (confirmed with user):
- Component names in the electronics file contain non-breaking spaces (\xa0) in some tabs; these
  are normalized to regular spaces before matching against the sensor list.
- SensorType strings have inconsistent capitalization (e.g. "Hall sensor" vs "hall sensor"); these
  are normalized to lowercase before combining identical sensor types.
- One exact duplicate status row exists in the electronics file (HV Powertrain / HV junction box / PDU,
  appears twice with identical Std/Opt/Rare values). It is deduplicated here defensively; the user
  is also correcting the source file directly.
- 27 components in the electronics file have no corresponding sensor rows in the sensor list at all
  (e.g. fuse boxes, VCU, BCM) -- by design these simply do not appear in the sensor list and
  contribute nothing. They are not padded in with explicit zero rows.

Outputs:
- sensor_segment_comparison.png
- sensor_sensitivity_by_segment.png
- sensor_monte_carlo_{SEG}_segment.png (per segment, grand total distribution)
- sensor_domain_analysis_{SEG}_segment.png (per segment, by domain)
- sensor_domain_cross_segment_comparison.png
- sensor_monte_carlo_{SEG}_detailed_results.csv (per segment, one column per combined SensorType + Total)
- sensor_monte_carlo_{SEG}_summary_stats.csv (per segment, stats per combined SensorType + Total)
- sensor_segment_comparison.csv
- sensor_sensitivity_{SEG}_segment.csv (per segment, variance contribution per SensorType)
- sensor_domain_summary_{SEG}_segment.csv (per segment, stats per Domain)
- sensor_domain_cross_segment_comparison.csv
- histograms/histogram_{SEG}_{sensortype}.csv (50-bin histograms for combined SensorType + Total)
- raw_data/raw_distribution_{SEG}_segment.csv (raw per-draw values for combined SensorType + Total)
- distribution_index.csv (root)

Notes:
- ndraws = 200,000 per segment, fully vectorized (no explicit Python loop over draws or rows).
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
os.makedirs(SCRIPT_DIR / 'figures_domain', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'figures_segment', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'figures_monte_carlo', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'figures_sensitivity', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'csv_domain', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'csv_segment', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'csv_monte_carlo', exist_ok=True)
os.makedirs(SCRIPT_DIR / 'csv_sensitivity', exist_ok=True)


np.random.seed(42)

print("="*80)
print("LOADING DATA FILES")
print("="*80)
print(f"Script location: {SCRIPT_DIR}")
print(f"Base directory: {BASE_DIR}")
print(f"Data directory: {DATA_DIR}")

ELEC_FILE = DATA_DIR / '01_VehicleElectronics.xlsx'
SENSOR_FILE = DATA_DIR / '06_VehicleSensorNumbers.xlsx'

if not ELEC_FILE.exists():
    raise FileNotFoundError(f"Electronics file not found: {ELEC_FILE}")
if not SENSOR_FILE.exists():
    raise FileNotFoundError(f"Sensor types file not found: {SENSOR_FILE}")


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


# ============================================================================
# LOAD ELECTRONICS FILE (ALL TABS) -> Std/Opt/Rare STATUS PER Domain+Component
# ============================================================================

print(f"\nLoading electronics status file (all tabs)...")
xl_elec = pd.ExcelFile(ELEC_FILE)

status_frames = []
for sheet in xl_elec.sheet_names:
    df = pd.read_excel(xl_elec, sheet_name=sheet,
                        usecols=['Domain', 'Component', 'A-B Segment', 'C-D Segment', 'E-F Segment'])
    status_frames.append(df)
status_df = pd.concat(status_frames, ignore_index=True)

# Normalize Domain/Component text (fixes non-breaking spaces etc.) while keeping
# the cleaned text as the display value.
status_df['Domain'] = status_df['Domain'].map(norm_text)
status_df['Component'] = status_df['Component'].map(norm_text)
status_df['_key'] = status_df['Domain'].map(norm_key) + '||' + status_df['Component'].map(norm_key)

# Defensive de-duplication of exact duplicate status rows (same key + identical Std/Opt/Rare values).
before_dedup = len(status_df)
status_df = status_df.drop_duplicates(
    subset=['_key', 'A-B Segment', 'C-D Segment', 'E-F Segment'], keep='first'
)
n_dropped = before_dedup - len(status_df)
if n_dropped:
    print(f"  Note: dropped {n_dropped} exact duplicate status row(s) (same Domain+Component+status).")

# Any remaining duplicate keys with DIFFERING status values would be a genuine data conflict --
# surface this loudly rather than silently picking one.
dup_keys = status_df['_key'][status_df['_key'].duplicated(keep=False)]
if len(dup_keys):
    print("  WARNING: the following Domain+Component combinations have multiple, "
          "DIFFERING status rows -- only the first is used:")
    for k in dup_keys.unique():
        print(f"    {k}")
    status_df = status_df.drop_duplicates(subset=['_key'], keep='first')

STATUS_FACTOR = {'Std': 1.0, 'Opt': 0.5, 'Rare': 0.25, '–': 0.0, '-': 0.0}
SEG_COL = {'AB': 'A-B', 'CD': 'C-D', 'EF': 'E-F'}
segments = ['AB', 'CD', 'EF']

for seg, col in SEG_COL.items():
    seg_col_name = f'{col} Segment'
    status_df[f'factor_{seg}'] = status_df[seg_col_name].map(STATUS_FACTOR)
    unmapped = status_df[status_df[f'factor_{seg}'].isna()]
    if len(unmapped):
        raise ValueError(f"Unrecognized status value(s) in '{seg_col_name}': "
                          f"{unmapped[seg_col_name].unique().tolist()}")

print(f"  Loaded status for {len(status_df)} unique Domain+Component combinations "
      f"across {len(xl_elec.sheet_names)} tabs.")


# ============================================================================
# LOAD SENSOR TYPES FILE (FIRST TAB ONLY) -> per-row min/max sensor counts
# ============================================================================

print(f"\nLoading sensor types file (first tab only)...")
xl_sensor = pd.ExcelFile(SENSOR_FILE)
first_sheet = xl_sensor.sheet_names[0]
print(f"  Using sheet: '{first_sheet}' (ignoring any other tabs)")

sensor_df = pd.read_excel(xl_sensor, sheet_name=first_sheet)

sensor_df['Domain'] = sensor_df['Domain'].map(norm_text)
sensor_df['Component'] = sensor_df['Component'].map(norm_text)
# SensorType: normalize whitespace AND case, so e.g. "Hall sensor" / "hall sensor" combine correctly.
sensor_df['SensorType'] = sensor_df['SensorType'].map(norm_text).str.lower()
sensor_df['_key'] = sensor_df['Domain'].map(norm_key) + '||' + sensor_df['Component'].map(norm_key)

print(f"  Loaded {len(sensor_df)} (Domain, Component, SensorType) rows.")


# ============================================================================
# MERGE: attach segment status factors to every sensor row
# ============================================================================

merged = sensor_df.merge(
    status_df[['_key', 'factor_AB', 'factor_CD', 'factor_EF']],
    on='_key', how='left'
)

unmatched = merged[merged['factor_AB'].isna()]
if len(unmatched):
    raise ValueError(
        "The following sensor rows have no matching Domain+Component status row "
        "in the electronics file -- cannot determine Std/Opt/Rare factor:\n"
        + unmatched[['Domain', 'Component', 'SensorType']].to_string()
    )

merged = merged.reset_index(drop=True)
merged['_row_idx'] = np.arange(len(merged))

print(f"\n  Merge complete: all {len(merged)} sensor rows matched to a segment status.")
print(f"  {merged['SensorType'].nunique()} distinct (normalized) sensor types found.")
print(f"  {merged['Domain'].nunique()} distinct domains found.")

domains = sorted(merged['Domain'].unique())
sensor_types = sorted(merged['SensorType'].unique())


# ============================================================================
# MONTE CARLO SIMULATION - ALL SEGMENTS
# ============================================================================

ndraws = 200000


def run_batch_simulation(df, segment, ndraws):
    """
    Vectorized Monte Carlo for ALL draws at once, for a given set of sensor rows
    (rows of `merged`, optionally pre-filtered) and a given segment.

    For every row and every draw: scaled_min = row_min * factor, scaled_max = row_max * factor,
    then a uniform draw is taken between scaled_min and scaled_max. Returns a (n_rows, ndraws)
    matrix of per-row sensor-count draws; callers sum over whichever rows they need
    (e.g. all rows sharing a SensorType, or all rows in a Domain, or everything for the grand total).
    """
    col_prefix = SEG_COL[segment]
    n_rows = len(df)

    row_min = df[f'{col_prefix}_Min'].to_numpy()[:, None]
    row_max = df[f'{col_prefix}_Max'].to_numpy()[:, None]
    factor = df[f'factor_{segment}'].to_numpy()[:, None]

    scaled_min = row_min * factor
    scaled_max = row_max * factor

    draws = np.random.uniform(scaled_min, scaled_max, size=(n_rows, ndraws))
    return draws


all_segment_draws = {}       # segment -> (n_rows, ndraws) matrix, row order == merged row order
all_segment_results = {}     # segment -> dict: sensor_type -> 1D array (ndraws,), plus 'total'

for segment in segments:
    print("\n" + "="*70)
    print(f"RUNNING MONTE CARLO SIMULATION FOR {segment} SEGMENT")
    print("="*70)
    print(f"Number of simulations: {ndraws:,}")
    print(f"Number of (Domain, Component, SensorType) rows: {len(merged)}\n")

    draws = run_batch_simulation(merged, segment, ndraws)
    all_segment_draws[segment] = draws

    results = {}
    for st in sensor_types:
        idxs = merged.loc[merged['SensorType'] == st, '_row_idx'].to_numpy()
        results[st] = draws[idxs, :].sum(axis=0)
    results['total'] = draws.sum(axis=0)

    all_segment_results[segment] = results
    print(f"{segment} Simulation complete!")


# ============================================================================
# CALCULATE STATISTICS FOR ALL SEGMENTS (per combined SensorType + Total)
# ============================================================================

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

    all_stats[segment] = stats

    print("="*70)
    print(f"MONTE CARLO SIMULATION RESULTS - {segment} SEGMENT")
    print("="*70)

    # Print Total first, then each sensor type
    for metric in ['total'] + sensor_types:
        values = stats[metric]
        label = 'TOTAL (all sensors)' if metric == 'total' else metric
        print(f"\n{label}:")
        print(f"  Mean:   {values['mean']:>10.2f}")
        print(f"  Mode:   {values['mode']:>10.2f}")
        print(f"  Median: {values['p50']:>10.2f}")
        print(f"  Std:    {values['std']:>10.2f}")
        print(f"  Min:    {values['min']:>10.2f}")
        print(f"  P025:   {values['p025']:>10.2f}")
        print(f"  P25:    {values['p25']:>10.2f}")
        print(f"  P75:    {values['p75']:>10.2f}")
        print(f"  P975:   {values['p975']:>10.2f}")
        print(f"  Max:    {values['max']:>10.2f}")


# ============================================================================
# SEGMENT COMPARISON (grand total)
# ============================================================================

print("\n" + "="*70)
print("SEGMENT COMPARISON")
print("="*70)

comparison_df = pd.DataFrame({
    'Segment': segments,
    'Mean_Total_Sensors': [all_stats[seg]['total']['mean'] for seg in segments],
    'Mode_Total_Sensors': [all_stats[seg]['total']['mode'] for seg in segments],
    'Median_Total_Sensors': [all_stats[seg]['total']['p50'] for seg in segments],
    'Std_Total_Sensors': [all_stats[seg]['total']['std'] for seg in segments],
    'P025_Total_Sensors': [all_stats[seg]['total']['p025'] for seg in segments],
    'P975_Total_Sensors': [all_stats[seg]['total']['p975'] for seg in segments],
})

print("\n", comparison_df.to_string(index=False))


# ============================================================================
# SENSITIVITY ANALYSIS - BY SEGMENT (per SensorType contribution to Total)
# ============================================================================

print("\n" + "="*70)
print("SENSITIVITY ANALYSIS BY SEGMENT")
print("="*70)

all_sensitivity = {}

for segment in segments:
    results = all_segment_results[segment]

    print(f"\n{segment} SEGMENT:")
    print("-" * 70)

    total_var = np.var(results['total'])

    variance_contrib = {}
    correlations = {}
    for st in sensor_types:
        v = np.var(results[st])
        variance_contrib[st] = v / total_var if total_var > 0 else np.nan
        corr = np.corrcoef(results[st], results['total'])[0, 1] if np.std(results[st]) > 0 else np.nan
        correlations[st] = corr

    # Rank by variance contribution, show top 10 for readability in console
    ranked = sorted(variance_contrib.items(), key=lambda kv: (kv[1] if kv[1] == kv[1] else -1), reverse=True)
    print("\nTop 10 SensorTypes by Variance Contribution to Total Sensor Count:")
    for st, vc in ranked[:10]:
        corr = correlations[st]
        corr_str = f"{corr:>6.3f}" if corr == corr else "  n/a"
        print(f"  {st:40s}: {vc*100:>6.2f}%   (corr with total: {corr_str})")

    all_sensitivity[segment] = {
        'variance_contrib': variance_contrib,
        'correlations': correlations
    }


# ============================================================================
# DOMAIN ANALYSIS BY SEGMENT (deterministic summary from input ranges)
# ============================================================================

print("\n" + "="*70)
print("ANALYSIS BY DOMAIN AND SEGMENT (AVERAGES FROM INPUT RANGES)")
print("="*70)

for segment in segments:
    col_prefix = SEG_COL[segment]
    print(f"\n{segment} SEGMENT:")
    print("-" * 70)

    for domain in domains:
        domain_rows = merged[merged['Domain'] == domain]
        scaled_min = domain_rows[f'{col_prefix}_Min'] * domain_rows[f'factor_{segment}']
        scaled_max = domain_rows[f'{col_prefix}_Max'] * domain_rows[f'factor_{segment}']
        avg = ((scaled_min + scaled_max) / 2).sum()

        print(f"  {domain:20s}: {len(domain_rows):3d} sensor rows, avg sensor count = {avg:>8.2f}")


# ============================================================================
# DOMAIN-LEVEL MONTE CARLO (one MC run per Domain x Segment)
# ============================================================================

print("\n" + "="*70)
print("RUNNING DOMAIN-SPECIFIC MONTE CARLO ANALYSIS")
print("="*70)
print(f"Domains: {', '.join(domains)}\n")

domain_segment_results = {}
domain_stats = {}

for segment in segments:
    print(f"Processing {segment} segment...")
    draws = all_segment_draws[segment]
    domain_segment_results[segment] = {}
    domain_stats[segment] = {}

    for domain in domains:
        idxs = merged.loc[merged['Domain'] == domain, '_row_idx'].to_numpy()
        domain_total = draws[idxs, :].sum(axis=0)
        domain_segment_results[segment][domain] = domain_total

        domain_stats[segment][domain] = {
            'mean': np.mean(domain_total),
            'mode': approx_mode(domain_total, bins=200),
            'median': np.percentile(domain_total, 50),
            'std': np.std(domain_total),
            'p025': np.percentile(domain_total, 2.5),
            'p975': np.percentile(domain_total, 97.5),
        }

print("Domain-specific Monte Carlo complete!\n")


# ============================================================================
# VISUALIZATIONS (segment-level, grand total)
# ============================================================================

print("\n" + "="*70)
print("GENERATING VISUALIZATIONS")
print("="*70)

# Figure 1: Segment Comparison - Total Sensor Count
fig1, axes = plt.subplots(2, 2, figsize=(16, 12))
fig1.suptitle('BEV Sensor Count Monte Carlo Simulation - Segment Comparison', fontsize=16, fontweight='bold')

ax1 = axes[0, 0]
for segment in segments:
    ax1.hist(all_segment_results[segment]['total'], bins=50, alpha=0.5, label=f'{segment} Segment')
ax1.set_xlabel('Total Number of Sensors')
ax1.set_ylabel('Frequency')
ax1.set_title('Total Sensor Count Distribution by Segment')
ax1.legend()
ax1.grid(True, alpha=0.3)

ax2 = axes[0, 1]
box_data = [all_segment_results[seg]['total'] for seg in segments]
bp = ax2.boxplot(box_data, tick_labels=segments, patch_artist=True)
colors = ['lightblue', 'lightgreen', 'lightcoral']
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
ax2.set_ylabel('Total Number of Sensors')
ax2.set_title('Total Sensor Count by Segment')
ax2.grid(True, alpha=0.3, axis='y')

ax3 = axes[1, 0]
x = np.arange(len(segments))
means = [all_stats[seg]['total']['mean'] for seg in segments]
stds = [all_stats[seg]['total']['std'] for seg in segments]
ax3.bar(x, means, yerr=stds, capsize=5, color=colors)
ax3.set_xlabel('Segment')
ax3.set_ylabel('Mean Total Sensor Count')
ax3.set_title('Mean Total Sensor Count by Segment')
ax3.set_xticks(x)
ax3.set_xticklabels(segments)
ax3.grid(True, alpha=0.3, axis='y')

ax4 = axes[1, 1]
top5 = sorted(sensor_types, key=lambda st: all_stats['EF'][st]['mean'], reverse=True)[:5]
width = 0.25
for i, segment in enumerate(segments):
    vals = [all_stats[segment][st]['mean'] for st in top5]
    ax4.bar(np.arange(len(top5)) + (i - 1) * width, vals, width, label=f'{segment} Segment')
ax4.set_xticks(np.arange(len(top5)))
ax4.set_xticklabels(top5, rotation=30, ha='right')
ax4.set_ylabel('Mean Sensor Count')
ax4.set_title('Top 5 Sensor Types by Mean Count (E-F) Across Segments')
ax4.legend()
ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(SCRIPT_DIR / 'figures_segment' / 'sensor_segment_comparison.png', dpi=300, bbox_inches='tight')
print("✓ Saved: figures_segment/sensor_segment_comparison.png")

# Figure 2: Detailed Results for Each Segment (grand total + top sensor types)
for segment in segments:
    results = all_segment_results[segment]
    stats = all_stats[segment]

    fig2, axes2 = plt.subplots(2, 2, figsize=(14, 10))
    fig2.suptitle(f'BEV Sensor Count Monte Carlo Results - {segment} Segment', fontsize=16, fontweight='bold')

    top5_seg = sorted(sensor_types, key=lambda st: stats[st]['mean'], reverse=True)[:5]

    ax1 = axes2[0, 0]
    for st in top5_seg:
        ax1.hist(results[st], bins=50, alpha=0.5, label=st)
    ax1.set_xlabel('Sensor Count')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Distribution of Top 5 SensorTypes (by mean count)')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)

    ax2 = axes2[0, 1]
    box_data = [results[st] for st in top5_seg]
    bp = ax2.boxplot(box_data, tick_labels=top5_seg, patch_artist=True)
    for patch in bp['boxes']:
        patch.set_facecolor('lightblue')
    ax2.tick_params(axis='x', rotation=30)
    ax2.set_ylabel('Sensor Count')
    ax2.set_title('Top 5 SensorTypes - Boxplot')
    ax2.grid(True, alpha=0.3, axis='y')

    ax3 = axes2[1, 0]
    ax3.hist(results['total'], bins=50, alpha=0.7, color='purple')
    ax3.axvline(stats['total']['mean'], color='red', linestyle='--', linewidth=2,
                label=f"Mean: {stats['total']['mean']:.0f}")
    ax3.axvline(stats['total']['p025'], color='orange', linestyle='--', linewidth=1.5,
                label=f"P025: {stats['total']['p025']:.0f}")
    ax3.axvline(stats['total']['p975'], color='orange', linestyle='--', linewidth=1.5,
                label=f"P975: {stats['total']['p975']:.0f}")
    ax3.set_xlabel('Total Number of Sensors')
    ax3.set_ylabel('Frequency')
    ax3.set_title('Distribution of Total Sensor Count')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    ax4 = axes2[1, 1]
    sens = all_sensitivity[segment]['variance_contrib']
    top5_var = sorted(sensor_types, key=lambda st: (sens[st] if sens[st] == sens[st] else -1), reverse=True)[:5]
    vals = [sens[st] * 100 for st in top5_var]
    ax4.barh(top5_var, vals, color='teal')
    ax4.set_xlabel('Variance Contribution to Total (%)')
    ax4.set_title('Top 5 SensorTypes by Variance Contribution')
    ax4.grid(True, alpha=0.3, axis='x')

    plt.tight_layout()
    plt.savefig(SCRIPT_DIR / 'figures_monte_carlo' / f'sensor_monte_carlo_{segment}_segment.png',
                dpi=300, bbox_inches='tight')
    print(f"✓ Saved: figures_monte_carlo/sensor_monte_carlo_{segment}_segment.png")

# Figure 3: Sensitivity Analysis by Segment
fig3, axes3 = plt.subplots(2, 3, figsize=(18, 12))
fig3.suptitle('Sensitivity Analysis by Segment (Top 5 SensorTypes)', fontsize=16, fontweight='bold')

for idx, segment in enumerate(segments):
    sens = all_sensitivity[segment]['variance_contrib']
    corr = all_sensitivity[segment]['correlations']
    top5_var = sorted(sensor_types, key=lambda st: (sens[st] if sens[st] == sens[st] else -1), reverse=True)[:5]

    ax = axes3[0, idx]
    contributions = [sens[st] for st in top5_var]
    colors_pie = plt.cm.Set3(np.linspace(0, 1, len(top5_var)))
    ax.pie(contributions, labels=top5_var, autopct='%1.1f%%', colors=colors_pie, startangle=90,
           textprops={'fontsize': 7})
    ax.set_title(f'{segment} Segment: Variance Contribution')

    ax2 = axes3[1, idx]
    corr_values = [corr[st] for st in top5_var]
    ax2.bar(range(len(top5_var)), corr_values, color=colors_pie)
    ax2.set_xticks(range(len(top5_var)))
    ax2.set_xticklabels(top5_var, rotation=45, ha='right', fontsize=7)
    ax2.set_ylabel('Correlation with Total')
    ax2.set_title(f'{segment} Segment: Correlations')
    ax2.set_ylim([0, 1])
    ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(SCRIPT_DIR / 'figures_sensitivity' / 'sensor_sensitivity_by_segment.png', dpi=300, bbox_inches='tight')
print("✓ Saved: figures_sensitivity/sensor_sensitivity_by_segment.png")

plt.show(block=False)
plt.pause(5)


# ============================================================================
# SAVE RESULTS (segment-level, all sensor types + total)
# ============================================================================

print("\n" + "="*70)
print("SAVING RESULTS")
print("="*70)

for segment in segments:
    results_df = pd.DataFrame(all_segment_results[segment])
    results_df.to_csv(SCRIPT_DIR / 'csv_monte_carlo' / f'sensor_monte_carlo_{segment}_detailed_results.csv',
                       index=False)
    print(f"✓ Saved: csv_monte_carlo/sensor_monte_carlo_{segment}_detailed_results.csv")

for segment in segments:
    stats_df = pd.DataFrame(all_stats[segment]).T
    stats_df.to_csv(SCRIPT_DIR / 'csv_monte_carlo' / f'sensor_monte_carlo_{segment}_summary_stats.csv')
    print(f"✓ Saved: csv_monte_carlo/sensor_monte_carlo_{segment}_summary_stats.csv")

comparison_df.to_csv(SCRIPT_DIR / 'csv_segment' / 'sensor_segment_comparison.csv', index=False)
print("✓ Saved: csv_segment/sensor_segment_comparison.csv")

for segment in segments:
    sens = all_sensitivity[segment]
    sensitivity_df = pd.DataFrame({
        'SensorType': sensor_types,
        'Variance_Contribution': [sens['variance_contrib'][st] for st in sensor_types],
        'Correlation_with_Total': [sens['correlations'][st] for st in sensor_types]
    }).sort_values('Variance_Contribution', ascending=False)
    sensitivity_df.to_csv(SCRIPT_DIR / 'csv_sensitivity' / f'sensor_sensitivity_{segment}_segment.csv', index=False)
    print(f"✓ Saved: csv_sensitivity/sensor_sensitivity_{segment}_segment.csv")


# ============================================================================
# DOMAIN COMPARISON VISUALIZATIONS
# ============================================================================

print("\n" + "="*70)
print("GENERATING DOMAIN-SPECIFIC VISUALIZATIONS")
print("="*70)

for segment in segments:
    fig, axes = plt.subplots(1, 2, figsize=(18, 8))
    fig.suptitle(f'{segment} Segment - Sensor Count by Domain', fontsize=16, fontweight='bold')

    ax1 = axes[0]
    domain_means = [domain_stats[segment][d]['mean'] for d in domains]
    domain_stds = [domain_stats[segment][d]['std'] for d in domains]
    order = np.argsort(domain_means)[::-1]
    domains_sorted = [domains[i] for i in order]
    means_sorted = [domain_means[i] for i in order]
    stds_sorted = [domain_stds[i] for i in order]
    colors_dom = plt.cm.tab20(np.linspace(0, 1, len(domains)))
    ax1.barh(domains_sorted, means_sorted, xerr=stds_sorted, capsize=3, color=colors_dom)
    ax1.set_xlabel('Mean Sensor Count')
    ax1.set_title('Mean Sensor Count by Domain')
    ax1.grid(True, alpha=0.3, axis='x')
    ax1.invert_yaxis()

    ax2 = axes[1]
    top3_domains = domains_sorted[:3]
    for d in top3_domains:
        ax2.hist(domain_segment_results[segment][d], bins=50, alpha=0.5, label=d)
    ax2.set_xlabel('Sensor Count')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Distribution for Top 3 Domains (by mean)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(SCRIPT_DIR / 'figures_domain' / f'sensor_domain_analysis_{segment}_segment.png',
                dpi=300, bbox_inches='tight')
    print(f"✓ Saved: figures_domain/sensor_domain_analysis_{segment}_segment.png")

# Cross-Segment Domain Comparison
n_domains = len(domains)
ncols = 4
nrows = int(np.ceil(n_domains / ncols))
fig_cross, axes_cross = plt.subplots(nrows, ncols, figsize=(20, 4 * nrows))
fig_cross.suptitle('Sensor Count by Domain Across Segments', fontsize=16, fontweight='bold')
axes_cross_flat = axes_cross.flatten()

for idx, domain in enumerate(domains):
    ax = axes_cross_flat[idx]
    seg_means = [domain_stats[seg][domain]['mean'] for seg in segments]
    seg_stds = [domain_stats[seg][domain]['std'] for seg in segments]
    x_pos = np.arange(len(segments))
    ax.bar(x_pos, seg_means, yerr=seg_stds, capsize=5, color=['lightblue', 'lightgreen', 'lightcoral'])
    ax.set_xticks(x_pos)
    ax.set_xticklabels(segments)
    ax.set_ylabel('Mean Sensor Count')
    ax.set_title(domain, fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')

for idx in range(n_domains, len(axes_cross_flat)):
    axes_cross_flat[idx].axis('off')

plt.tight_layout()
plt.savefig(SCRIPT_DIR / 'figures_domain' / 'sensor_domain_cross_segment_comparison.png',
            dpi=300, bbox_inches='tight')
print("✓ Saved: figures_domain/sensor_domain_cross_segment_comparison.png")

plt.show(block=False)
plt.pause(5)


# ============================================================================
# SAVE DOMAIN-SPECIFIC RESULTS
# ============================================================================

print("\n" + "="*70)
print("SAVING DOMAIN-SPECIFIC RESULTS")
print("="*70)

for segment in segments:
    summary_data = []
    for domain in domains:
        st = domain_stats[segment][domain]
        summary_data.append({
            'Domain': domain,
            'Mean_Sensor_Count': st['mean'],
            'Mode_Sensor_Count': st['mode'],
            'Median_Sensor_Count': st['median'],
            'Std_Sensor_Count': st['std'],
            'P025_Sensor_Count': st['p025'],
            'P975_Sensor_Count': st['p975'],
        })
    summary_df = pd.DataFrame(summary_data).sort_values('Mean_Sensor_Count', ascending=False)
    filename = SCRIPT_DIR / 'csv_domain' / f'sensor_domain_summary_{segment}_segment.csv'
    summary_df.to_csv(filename, index=False)
    print(f"✓ Saved: csv_domain/sensor_domain_summary_{segment}_segment.csv")

cross_rows = []
for domain in domains:
    for segment in segments:
        st = domain_stats[segment][domain]
        cross_rows.append({
            'Domain': domain,
            'Segment': segment,
            'Mean_Sensor_Count': st['mean'],
            'Mode_Sensor_Count': st['mode'],
            'Median_Sensor_Count': st['median'],
            'Std_Sensor_Count': st['std'],
            'P025_Sensor_Count': st['p025'],
            'P975_Sensor_Count': st['p975'],
        })

cross_df = pd.DataFrame(cross_rows)
cross_df.to_csv(SCRIPT_DIR / 'csv_domain' / 'sensor_domain_cross_segment_comparison.csv', index=False)
print("✓ Saved: csv_domain/sensor_domain_cross_segment_comparison.csv")

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
all_histograms = {}

def safe_filename(s):
    """Make a sensor type name filesystem-safe."""
    s = re.sub(r'[^\w\-]+', '_', s)
    return s.strip('_')

# 1. Save segment-level distributions (Total + every combined SensorType)
print("\nSaving segment-level sensor count distributions...")
for segment in segments:
    results = all_segment_results[segment]
    segment_histograms = {}

    for metric in ['total'] + sensor_types:
        values = results[metric]
        counts, bin_edges = np.histogram(values, bins=n_bins)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        segment_histograms[metric] = {
            'counts': counts, 'bin_edges': bin_edges, 'bin_centers': bin_centers
        }

        hist_df = pd.DataFrame({
            'bin_center': bin_centers,
            'bin_left_edge': bin_edges[:-1],
            'bin_right_edge': bin_edges[1:],
            'count': counts,
            'frequency': counts / ndraws
        })

        metric_name = 'total' if metric == 'total' else safe_filename(metric)
        filename = SCRIPT_DIR / 'histograms' / f'histogram_{segment}_{metric_name}.csv'
        hist_df.to_csv(filename, index=False)

    all_histograms[segment] = segment_histograms
    print(f"  ✓ Saved {len(sensor_types) + 1} histograms for {segment} segment")

# 2. Save domain-level total distributions
print("\nSaving domain-level sensor count distributions...")
for segment in segments:
    for domain in domains:
        values = domain_segment_results[segment][domain]
        counts, bin_edges = np.histogram(values, bins=n_bins)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        hist_df = pd.DataFrame({
            'bin_center': bin_centers,
            'bin_left_edge': bin_edges[:-1],
            'bin_right_edge': bin_edges[1:],
            'count': counts,
            'frequency': counts / ndraws
        })

        domain_name = safe_filename(domain)
        filename = SCRIPT_DIR / 'histograms' / f'histogram_{segment}_domain_{domain_name}.csv'
        hist_df.to_csv(filename, index=False)
    print(f"  ✓ Saved {len(domains)} domain histograms for {segment} segment")

# 3. Save raw distribution data (for exact bootstrapping)
print("\nSaving raw distribution data...")

for segment in segments:
    results_df = pd.DataFrame(all_segment_results[segment])
    filename = SCRIPT_DIR / 'raw_data' / f'raw_distribution_{segment}_segment.csv'
    results_df.to_csv(filename, index=False)
    print(f"  ✓ Saved: raw_data/raw_distribution_{segment}_segment.csv")

for segment in segments:
    domain_df = pd.DataFrame(domain_segment_results[segment])
    filename = SCRIPT_DIR / 'raw_data' / f'raw_distribution_{segment}_domains.csv'
    domain_df.to_csv(filename, index=False)
    print(f"  ✓ Saved: raw_data/raw_distribution_{segment}_domains.csv")

# 4. Master index file
print("\nCreating master index file...")

index_data = []
for segment in segments:
    for metric in ['total'] + sensor_types:
        metric_name = 'total' if metric == 'total' else safe_filename(metric)
        index_data.append({
            'type': 'sensor_type' if metric != 'total' else 'total',
            'segment': segment,
            'label': metric,
            'histogram_file': f'histograms/histogram_{segment}_{metric_name}.csv',
            'raw_data_file': f'raw_data/raw_distribution_{segment}_segment.csv',
            'n_simulations': ndraws,
            'n_bins': n_bins
        })

for segment in segments:
    for domain in domains:
        domain_name = safe_filename(domain)
        index_data.append({
            'type': 'domain',
            'segment': segment,
            'label': domain,
            'histogram_file': f'histograms/histogram_{segment}_domain_{domain_name}.csv',
            'raw_data_file': f'raw_data/raw_distribution_{segment}_domains.csv',
            'n_simulations': ndraws,
            'n_bins': n_bins
        })

index_df = pd.DataFrame(index_data)
index_df.to_csv(SCRIPT_DIR / 'distribution_index.csv', index=False)
print("  ✓ Saved: distribution_index.csv")

print("\n" + "="*70)
print("HISTOGRAM DISTRIBUTIONS SAVED!")
print("="*70)
print(f"\nTotal sensor types (combined, normalized): {len(sensor_types)}")
print(f"Total domains: {len(domains)}")
print(f"Total histogram files: {len(segments) * (len(sensor_types) + 1 + len(domains))}")
print(f"Total raw data files: {len(segments) * 2}")