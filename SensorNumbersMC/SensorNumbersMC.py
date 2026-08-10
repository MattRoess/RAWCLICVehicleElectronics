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
import sys
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

# ============================================================================
# TIME AXIS AND THE VOLTAGE DRIVER
#
# 06_ holds the 400V BASIS for the two battery-pack sensing rows (rebased
# 2026-08-05, see 06_ sheet Notes). The 400V -> 800V uplift is applied HERE,
# from the same penetration curve Wiring/BevWiring.py reads. It is deliberately
# NOT recomputed: computing the voltage mix twice guarantees the two models
# drift apart, which is the exact failure this coupling exists to prevent.
#
# PHYSICS. A BMS senses every SERIES element; cells in parallel share a node and
# are sensed once. Series count is set by pack VOLTAGE, not by vehicle size, so
# 400V -> 800V roughly doubles the sense lines. Temperature is per MODULE, so
# its uplift is smaller and genuinely uncertain.
#
# NO RENORMALISATION AT BASE_YEAR. This is the one place in the project where
# renormalising would be WRONG: 06_ is now a 400V basis, not an observed 2025
# mixture, so the uplift is applied from zero. (Contrast BevWiring, where the
# 2025 wiring baseline IS observed and must be renormalised.)
# ============================================================================

YEARS = np.arange(2020, 2071)          # UNIT: calendar years. Matches BevWiring.
BASE_YEAR = 2025                       # the anchor; 06_ describes this year
SNAPSHOT_YEARS = [2020, 2025, 2030, 2035, 2040, 2050, 2070]

PENETRATION_FILE = DATA_DIR / '18_BEV_technology_penetration.xlsx'

# 800V uplift on battery sensing | UNIT: dimensionless multiplier at full 800V.
# Voltage: series elements 400V ~ 80-96-105, 800V ~ 176-203-216, so the ratio is
# NOT a fixed 2 -- mode ~2.1, tails 1.7 to 2.5.
UPLIFT_VOLTAGE_TRI = (1.7, 2.1, 2.5)
# Temperature: per MODULE, not per series element. Floor 1.0 = module count
# unchanged, just rearranged (cell-to-pack designs remove modules entirely);
# ceiling 1.9 = modules follow series count. docs/SENSOR_MODEL_DESIGN.md 3.4.
UPLIFT_TEMPERATURE_TRI = (1.0, 1.4, 1.9)

# The only two rows the voltage driver touches. Everything else -- HVAC, cabin,
# inverter, thermal loops -- is voltage-independent, so the uplift is applied
# ROW-WISE and never to an aggregate.
BATTERY_COMPONENT = 'Traction battery pack'
BATTERY_ROWS = {'voltage sensor': UPLIFT_VOLTAGE_TRI,
                'temperature sensor': UPLIFT_TEMPERATURE_TRI}


# --- shared driver curves -------------------------------------------------
# ONE implementation, in tools/drivers.py, read by every model. Before
# 2026-08-10 this reader lived here AND in Wiring/BevWiring.py; step 7 was about
# to add a third copy in PCBAreaMC. Two models computing the same share from the
# same file and drifting apart is exactly what V12 exists to catch.
sys.path.insert(0, str(BASE_DIR / "tools"))
from drivers import (monotone_curve as _monotone_curve,      # noqa: E402
                     load_800v_share,
                     load_presence_per_tier as _load_presence_shared,
                     LIDAR_H4_FLOOR)


print("\nLoading the 800V penetration curve from 18_ (shared with BevWiring)...")
SHARE_800V = load_800v_share(YEARS)
_i25 = int(np.searchsorted(YEARS, BASE_YEAR))
print("  800V share at {}: ".format(BASE_YEAR)
      + ", ".join(f"{s} {SHARE_800V[s][_i25]:.1%}" for s in ['AB', 'CD', 'EF']))


# ============================================================================
# THE ADAS HARDWARE-TIER DRIVER
#
# 01_'s Std / Opt / Rare factor is ALREADY a penetration share -- it says what
# fraction of vehicles in a segment carry a component. It was simply frozen in
# time. For the ADAS domain it now becomes a function of year:
#
#     presence(component, segment, year)
#         = SUM_tier  share(tier, segment, year) x presence(component | tier)
#
# Both tables are read from Data/19_ADAS_sensor_adoption.xlsx -- THE SAME FILE
# Wiring/BevWiring.py reads. Never recomputed here.
#
# WHY TIER AND NOT SAE LEVEL. A car does not gain a sensor because a regulator
# grants liability transfer. Volvo's EX90 carries 31 sensors at L2; BMW's i7
# carried 25 at L3. See Wiring/AUTONOMY_LEVELS_VS_HARDWARE.md.
#
# LIDAR IS NOT TIER-GOVERNED. It tracks cost and Chinese competitive pressure,
# so its presence comes from Driver B (19_ sheet Lidar), not from the tier mix.
# ============================================================================

ADAS_DOMAIN = 'ADAS'
ADAS_FILE = DATA_DIR / '19_ADAS_sensor_adoption.xlsx'
TIERS = ['H0', 'H1', 'H2', 'H3', 'H4']
LIDAR_COMPONENT = 'LiDAR sensor'
LIDAR_H4_FLOOR = 0.80        # 19_ Presence_per_Tier: H4 = max(Driver B, 0.80)


def load_presence_per_tier(years):
    """Thin wrapper: the composition itself lives in tools/drivers.py so the
    PCB models can use the identical implementation."""
    return _load_presence_shared(years)


print("Loading the ADAS tier axis from 19_ (shared with BevWiring)...")
PRESENCE_TIER = load_presence_per_tier(YEARS)
print(f"  {len(PRESENCE_TIER)} ADAS components, {len(YEARS)} years")
print("  presence at {} (EF): ".format(BASE_YEAR) + ", ".join(
    f"{c.split('/')[0].strip()[:18]} {PRESENCE_TIER[c]['EF'][_i25]:.2f}"
    for c in ['Front ADAS camera', 'Side / mirror cameras', LIDAR_COMPONENT]))


# ----------------------------------------------------------------------------
# CHUNKED ACCUMULATION
#
# WHY THIS EXISTS. This script currently has no time axis. Adding one (step 4 of
# docs/SENSOR_MODEL_DESIGN.md) multiplies the draw matrix by the number of years:
#
#     192 rows x 200,000 draws x  1 year  x 8 bytes x 3 segments =  0.9 GB   ok
#     192 rows x 200,000 draws x 51 years x 8 bytes x 3 segments = 47.0 GB   impossible
#
# So statistics must stop depending on holding every draw. The accumulator below
# is ported from Wiring/BevWiring.py, where the same wall was hit and solved: it
# keeps fixed-bin histograms instead of samples, so its memory is independent of
# ndraws. Measured accuracy there: 0.089% on the mean, 0.44% on P2.5/P97.5 --
# far below the Monte Carlo sampling noise it removes.
#
# STEP 3 DELIBERATELY CHANGES NO BEHAVIOUR. The accumulator supplies the
# statistics; the full-draw path is kept at full size so every figure and raw
# CSV is bit-for-bit what it was. N_ITER_RAW is the knob step 4 will turn down.
# ----------------------------------------------------------------------------

N_ITER_STATS = ndraws      # draws behind the STATISTICS, via the accumulator.
                           # Memory does not scale with this.
N_ITER_RAW = 20000         # draws kept in full, for figures, the detailed CSV
                           # and the sensitivity analysis. THIS is what costs
                           # memory. Lowered from 200,000 in step 4: those
                           # outputs are single-year (BASE_YEAR) distributions
                           # and 20,000 draws render them indistinguishably,
                           # while the STATISTICS still come from the full
                           # N_ITER_STATS via the accumulator.
CHUNK_ITER = 20000         # draws simulated at once. Peak memory is set by
                           # THIS, not by N_ITER_STATS.

PILOT_ITER = 2000          # draws used only to find the accumulator range

# Accumulator, N_HIST_BINS, N_ACC_BINS and PILOT_PAD now come from
# tools/accumulator.py -- one implementation, shared with BevWiring and the PCB
# models. See that module for what is exact (mean/std/min/max/correlations) and
# what is binned (percentiles, mode).
from accumulator import (Accumulator, CoMoments,      # noqa: E402,F401
                         N_HIST_BINS, N_ACC_BINS, PILOT_PAD)


def run_batch_simulation(df, segment, ndraws, unscaled_mask=None):
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
    factor = df[f'factor_{segment}'].to_numpy(dtype=float)[:, None]

    if unscaled_mask is not None:
        # Rows whose presence is supplied by a DRIVER rather than by 01_'s
        # static label are drawn at factor 1.0 and scaled afterwards. Scaling
        # afterwards is not optional: a row labelled "-" has factor 0.00, so its
        # draws are identically zero and no later multiplication could recover
        # them -- yet the tier mix gives several such rows a real presence in
        # later years (e.g. Side / mirror cameras in AB).
        factor = np.where(np.asarray(unscaled_mask, dtype=bool)[:, None], 1.0, factor)

    scaled_min = row_min * factor
    scaled_max = row_max * factor

    draws = np.random.uniform(scaled_min, scaled_max, size=(n_rows, ndraws))
    return draws


def _battery_row_index(df, sensor_type):
    """Row of the traction battery pack for one sensor type, or None."""
    m = df[(df['Component'] == BATTERY_COMPONENT) & (df['SensorType'] == sensor_type)]
    return int(m['_row_idx'].iloc[0]) if len(m) else None


def _adas_row_map(df, adas_idx):
    """{SensorType key: positions within adas_idx}, so the ADAS contribution to
    each reported sensor type can be summed without touching the other rows."""
    st_all = df['SensorType'].to_numpy()[adas_idx]
    return {st: np.flatnonzero(st_all == st) for st in np.unique(st_all)}


def apply_adas_tier_presence(df, draws, segment, year=BASE_YEAR):
    """Scale unscaled ADAS rows by their composed tier presence at `year`.

    For the full-draw path. The accumulator applies this per year internally.
    Mutates and returns `draws`.
    """
    yi = int(np.searchsorted(YEARS, year))
    idx = np.flatnonzero((df['Domain'] == ADAS_DOMAIN).to_numpy())
    comps = df['Component'].to_numpy()[idx]
    pres = np.array([PRESENCE_TIER[c][segment][yi] for c in comps])[:, None]
    draws[idx, :] = draws[idx, :] * pres
    return draws


def apply_voltage_uplift(df, draws, segment, year=BASE_YEAR):
    """Apply the 400V -> 800V battery-sensing uplift to a full-draw matrix.

    The accumulator path applies this per year internally. The full-draw path --
    which feeds the figures, the detailed CSV, the raw distributions and the
    sensitivity analysis -- needs it too, or those outputs describe a
    hypothetical all-400V vehicle instead of a real one at `year`.

    Mutates and returns `draws`.
    """
    yi = int(np.searchsorted(YEARS, year))
    n = draws.shape[1]
    u_volt = np.random.uniform(size=n)                     # one per vehicle
    is800 = (u_volt < SHARE_800V[segment][yi]).astype(float)
    for st, tri in BATTERY_ROWS.items():
        r = _battery_row_index(df, st)
        if r is None:
            continue
        upl = np.random.triangular(*tri, size=n)
        draws[r, :] = draws[r, :] * (1.0 + is800 * (upl - 1.0))
    return draws


def _series_of(df, draws):
    """Aggregate a (n_rows, n_draw) draw matrix into the reported series."""
    out = {}
    for st in sensor_types:
        out[st] = draws[df.loc[df['SensorType'] == st, '_row_idx'].to_numpy(), :].sum(axis=0)
    for d in domains:
        out[('domain', d)] = draws[df.loc[df['Domain'] == d, '_row_idx'].to_numpy(), :].sum(axis=0)
    out['total'] = draws.sum(axis=0)
    return out


def run_accumulated(df, segment, n_iter, years=YEARS, chunk=CHUNK_ITER, verbose=True):
    """Simulate n_iter draws across every year, keeping only statistics.

    Returns {key: Accumulator}, each holding one series per year. Memory is
    independent of BOTH n_iter and the number of years.

    WHY THIS IS CHEAP. Only 2 of the 192 rows depend on the year -- the battery
    pack's voltage and temperature sensing. Everything else is voltage
    independent. So instead of building a (rows x draws x years) array, which
    would be 47 GB, the year-independent base is drawn ONCE per chunk and the
    two affected rows are adjusted per year as a delta on four series:
    the two sensor types, the HV Powertrain domain, and the total.

    The voltage state is drawn comonotonically -- one uniform per iteration,
    held across all years -- so a vehicle is one design that switches once,
    never a blend. Same scheme as the architecture driver in BevWiring.
    """
    keys = list(sensor_types) + [('domain', d) for d in domains] + ['total']
    n_years = len(years)
    share = SHARE_800V[segment]
    hv_domain_key = ('domain', 'HV Powertrain')

    rows = {st: _battery_row_index(df, st) for st in BATTERY_ROWS}
    missing = [k for k, v in rows.items() if v is None]
    if missing:
        raise ValueError(f"battery rows not found in 06_: {missing}")

    adas_mask = (df['Domain'] == ADAS_DOMAIN).to_numpy()
    adas_idx = np.flatnonzero(adas_mask)
    adas_comp = df['Component'].to_numpy()[adas_idx]
    adas_key_rows = _adas_row_map(df, adas_idx)
    adas_domain_key = ('domain', ADAS_DOMAIN)

    def chunk_series(n):
        """Yield {key: (n, n_years)} for one chunk.

        Two drivers act, on disjoint row sets:
          ADAS rows      -> tier presence, drawn unscaled then scaled per year
          battery rows   -> 800V uplift, applied as a delta per year
        Everything else is year-independent and drawn once.
        """
        base = run_batch_simulation(df, segment, n, unscaled_mask=adas_mask)

        # year-independent part: everything except ADAS
        non_adas = base.copy()
        non_adas[adas_idx, :] = 0.0
        s0 = _series_of(df, non_adas)
        del non_adas

        u_volt = np.random.uniform(size=n)                   # ONE per vehicle
        upl = {st: np.random.triangular(*BATTERY_ROWS[st], size=n) for st in BATTERY_ROWS}

        out = {k: np.repeat(s0[k][:, None], n_years, axis=1) for k in keys}
        for yi in range(n_years):
            # --- ADAS: scale each unscaled row by its composed presence
            pres = np.array([PRESENCE_TIER[c][segment][yi] for c in adas_comp])[:, None]
            adas_scaled = base[adas_idx, :] * pres
            a_tot = adas_scaled.sum(axis=0)
            for k, local_rows in adas_key_rows.items():
                out[k][:, yi] += adas_scaled[local_rows, :].sum(axis=0)
            out[adas_domain_key][:, yi] += a_tot
            out['total'][:, yi] += a_tot
            del adas_scaled

            # --- battery: 800V uplift, comonotonic across years
            is800 = (u_volt < share[yi]).astype(float)
            d_tot = np.zeros(n)
            for st in BATTERY_ROWS:
                delta = base[rows[st], :] * is800 * (upl[st] - 1.0)
                out[st][:, yi] += delta
                d_tot += delta
            out[hv_domain_key][:, yi] += d_tot
            out['total'][:, yi] += d_tot
        return out

    if verbose:
        print(f"  pilot {PILOT_ITER:,} draws to set accumulator ranges "
              f"({n_years} years)...")
    pilot = chunk_series(PILOT_ITER)
    accs = {k: Accumulator(pilot[k].min(axis=0), pilot[k].max(axis=0),
                           n_series=n_years) for k in keys}
    del pilot

    done = 0
    while done < n_iter:
        n = min(chunk, n_iter - done)
        s = chunk_series(n)
        for k in keys:
            accs[k].add(s[k])
        del s
        done += n
        if verbose and (done % (chunk * 5) == 0 or done == n_iter):
            print(f"    {done:>9,} / {n_iter:,}")
    return accs


def stats_from_accumulator(acc, yi=None):
    """Same keys as the full-draw stats dict, so downstream code is unchanged.

    yi selects the year; default is BASE_YEAR, so every existing output keeps
    describing the same vehicle it described before the time axis existed.
    """
    if yi is None:
        yi = int(np.searchsorted(YEARS, BASE_YEAR))
    return {
        'mean': float(acc.mean[yi]),
        'mode': float(acc.coarse_mode()[yi]),
        'std': float(acc.std[yi]),
        'min': float(acc.vmin[yi]),
        'max': float(acc.vmax[yi]),
        'p025': float(acc.percentile(2.5)[yi]),
        'p25': float(acc.percentile(25)[yi]),
        'p50': float(acc.percentile(50)[yi]),
        'p75': float(acc.percentile(75)[yi]),
        'p975': float(acc.percentile(97.5)[yi]),
    }


all_segment_draws = {}       # segment -> (n_rows, ndraws) matrix, row order == merged row order
all_segment_results = {}     # segment -> dict: sensor_type -> 1D array (ndraws,), plus 'total'
all_segment_accs = {}        # segment -> {key: Accumulator}  -- the statistics path

for segment in segments:
    print("\n" + "="*70)
    print(f"RUNNING MONTE CARLO SIMULATION FOR {segment} SEGMENT")
    print("="*70)
    print(f"Statistics : {N_ITER_STATS:,} draws via the accumulator "
          f"(memory independent of this)")
    print(f"Full-draw  : {N_ITER_RAW:,} draws kept, for figures and raw CSVs")
    print(f"Number of (Domain, Component, SensorType) rows: {len(merged)}\n")

    # --- statistics path: chunked, memory independent of the draw count
    all_segment_accs[segment] = run_accumulated(merged, segment, N_ITER_STATS)

    # --- full-draw path: needed by the figures, the detailed CSV, the raw
    #     distributions and the sensitivity analysis, none of which can be
    #     rebuilt from histograms. THIS is what costs memory; step 4 caps it.
    # The full-draw path describes a vehicle at BASE_YEAR, so it needs the SAME
    # drivers the accumulator applies. Without them, every figure and raw CSV
    # would silently show an all-400V, frozen-2025-ADAS vehicle. V14 compares
    # the two paths at BASE_YEAR and fails loudly if either is missed -- it
    # already caught exactly this once.
    _adas_mask = (merged['Domain'] == ADAS_DOMAIN).to_numpy()
    draws = run_batch_simulation(merged, segment, N_ITER_RAW,
                                 unscaled_mask=_adas_mask)
    draws = apply_adas_tier_presence(merged, draws, segment, BASE_YEAR)
    draws = apply_voltage_uplift(merged, draws, segment, BASE_YEAR)
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
v14 = []          # (segment, key, accumulator value, full-draw value) for the check below

for segment in segments:
    results = all_segment_results[segment]
    accs = all_segment_accs[segment]
    stats = {}

    for key, values in results.items():
        # STATISTICS COME FROM THE ACCUMULATOR (N_ITER_STATS draws, memory
        # independent). The full-draw values are computed alongside only to
        # verify the port -- see the V14 table printed after this loop.
        stats[key] = stats_from_accumulator(accs[key])

        full = {
            'mean': np.mean(values),
            'mode': approx_mode(values, bins=200),
            'std': np.std(values),
            'p025': np.percentile(values, 2.5),
            'p50': np.percentile(values, 50),
            'p975': np.percentile(values, 97.5),
        }
        for m in ('mean', 'std', 'p025', 'p50', 'p975'):
            v14.append((segment, key, m, stats[key][m], full[m]))

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
# V14 -- DOES THE ACCUMULATOR REPRODUCE THE FULL-DRAW RESULT?
#
# The whole point of step 3: the port must not change the answer. Tolerance is
# 3%, the project's self-consistency noise floor (19_ sheet Uncertainty) -- a
# single source disagrees with itself by 2.8%, so demanding better of a
# statistical estimator would be demanding it reproduce noise.
# ============================================================================

V14_TOL = 0.03

print("\n" + "="*70)
print("V14 -- ACCUMULATOR vs FULL DRAW")
print("="*70)
print(f"  accumulator: {N_ITER_STATS:,} draws, chunked, memory independent")
print(f"  full draw  : {N_ITER_RAW:,} draws held in memory")
print(f"  tolerance  : {V14_TOL:.0%} (project noise floor)\n")

worst = {}
fails = []
for seg, key, metric, acc_v, full_v in v14:
    denom = abs(full_v) if abs(full_v) > 1e-9 else 1.0
    dev = abs(acc_v - full_v) / denom
    if dev > worst.get(metric, (0, None, None))[0]:
        worst[metric] = (dev, seg, key)
    if dev > V14_TOL and abs(full_v) > 1.0:
        fails.append((seg, key, metric, acc_v, full_v, dev))

print(f"  {'metric':<8}{'worst deviation':>18}   where")
for metric in ('mean', 'std', 'p025', 'p50', 'p975'):
    if metric in worst:
        dev, seg, key = worst[metric]
        print(f"  {metric:<8}{dev:>17.3%}   {seg} / {key}")

print(f"\n  {len(v14) - len(fails)} / {len(v14)} series-metrics within tolerance")
print(f"  (metrics whose full-draw value is <= 1.0 sensor are excluded from the "
      f"pass/fail\n   count -- relative error is meaningless at that scale -- but "
      f"they still appear\n   in the worst-deviation table above.)")
if fails:
    print("  OUTSIDE TOLERANCE:")
    for seg, key, metric, a, f, d in fails[:10]:
        print(f"    {seg:>3} {str(key):<34} {metric:<6} acc {a:>10.3f}  full {f:>10.3f}  {d:>7.2%}")
    if len(fails) > 10:
        print(f"    ... and {len(fails) - 10} more")
else:
    print("  V14 PASSED -- the accumulator reproduces the full-draw result.")


# ============================================================================
# V11 / V12 -- THE VOLTAGE DRIVER
#
# V11: does the 400V basis in 06_, plus the 800V uplift, reproduce what 06_
#      ORIGINALLY recorded as the observed 2025 mixture? This is the check that
#      would have caught the CD 800V error automatically.
# V12: do the sensor model and the wiring model draw the SAME 800V share?
# ============================================================================

print("\n" + "="*70)
print("V11 / V12 -- VOLTAGE DRIVER")
print("="*70)

# --- V12 first: the two models must read one curve
print("\n  V12 -- shared 800V penetration curve")
try:
    import sys as _sys
    _sys.path.insert(0, str(BASE_DIR / "Wiring"))
    import BevWiring as _bw                              # noqa: E402
    _wire = _bw.load_inputs(YEARS)
    worst_v12 = max(float(np.abs(_wire.volt[s] - SHARE_800V[s]).max())
                    for s in segments)
    print(f"    max |sensor curve - wiring curve| over all segments "
          f"and {len(YEARS)} years: {worst_v12:.3e}")
    print("    V12 PASSED -- one curve, two models."
          if worst_v12 < 1e-12 else "    V12 FAILED -- the models disagree.")
except Exception as e:                                   # noqa: BLE001
    print(f"    skipped (could not import BevWiring: {type(e).__name__}: {e})")

# --- V11: round-trip against what 06_ originally recorded
print(f"\n  V11 -- 400V basis + uplift reproduces the original 2025 observation")
print("    Only the VOLTAGE row is an assertion. Its 400V basis was derived by")
print("    rebasing the recorded 2025 mixture, so reproducing that mixture is a")
print("    genuine round-trip -- and it is what would have caught the CD error.")
print("    The TEMPERATURE maxima were deliberately CUT on 2026-08-05 (97/109/173")
print("    -> 70/85/120, see 06_ sheet Notes), so the original observation is no")
print("    longer the target and those rows are informational only.\n")

ORIGINAL_06 = {          # observed 2025 mixture, before the 2026-08-05 rebasing
    'voltage sensor':     {'AB': 96.0, 'CD': 102.0, 'EF': 153.0},
    'temperature sensor': {'AB': 66.0, 'CD':  81.0, 'EF': 129.0},
}
ASSERTED = {'voltage sensor'}

yi25 = int(np.searchsorted(YEARS, BASE_YEAR))
print(f"    {'row':<20}{'seg':<5}{'predicted':>11}{'orig 06_':>10}{'dev':>9}   note")
v11_fail = 0
for st, tri in BATTERY_ROWS.items():
    for seg in segments:
        idx = _battery_row_index(merged, st)
        lo = merged.iloc[idx][f'{SEG_COL[seg]}_Min']
        hi = merged.iloc[idx][f'{SEG_COL[seg]}_Max']
        f = merged.iloc[idx][f'factor_{seg}']
        basis = 0.5 * (lo + hi) * f
        pred = basis * (1.0 + SHARE_800V[seg][yi25] * (np.mean(tri) - 1.0))
        orig = ORIGINAL_06[st][seg]
        dev = pred / orig - 1.0
        if st in ASSERTED:
            note = 'ASSERTED'
            if abs(dev) > 0.05:
                v11_fail += 1
                note = 'ASSERTED -- OUTSIDE 5%'
        else:
            note = 'informational (maxima cut deliberately)'
        print(f"    {st:<20}{seg:<5}{pred:>11.1f}{orig:>10.1f}{dev:>8.1%}   {note}")
print(f"\n    {'V11 PASSED' if v11_fail == 0 else f'V11 FAILED -- {v11_fail} outside 5%'}"
      f"  (voltage rows only; tolerance 5%, project noise floor ~3%)")


# ============================================================================
# V13 -- DOES THE TIER COMPOSITION REPRODUCE 01_'s STATIC LABELS AT 2025?
#
# 01_'s Std / Opt / Rare factor is a 2025 observation. The tier composition
# replaces it with a curve. At 2025 the two must agree, or the new axis is
# describing a different vehicle from the one the file recorded.
#
# Tolerance 0.15 on a share (docs/SENSOR_MODEL_DESIGN.md section 8). Loose on
# purpose: Std/Opt/Rare is a 4-level ordinal scale, so it cannot resolve better
# than ~0.25 in the first place.
# ============================================================================

print("\n" + "="*70)
print("V13 -- TIER COMPOSITION vs 01_ STATIC LABELS, AT 2025")
print("="*70)

V13_TOL = 0.15

# RE-SCOPED 2026-08-07. V13 used to assert every row at 0.15. Five rows can
# never satisfy that, and not because anything is wrong: 01_'s scale has only
# four values (Std 1.00, Opt 0.50, Rare 0.25, "-" 0.00), so a composed presence
# landing between two of them -- 0.66, 0.73, 0.75, 0.83, 0.84 all sit between
# Opt and Std -- is UNREPRESENTABLE. The largest possible gap to the nearest
# label is 0.25, which is above the tolerance by construction.
#
# The tolerance is NOT widened; widening it would hide the three real findings
# V13 made. Instead a row is only ASSERTED when the scale could express it,
# i.e. when the nearest available label is itself within tolerance. Rows the
# scale cannot represent are still printed, marked "unresolvable", so they stay
# visible and nobody mistakes silence for agreement.
STATUS_LEVELS = (1.00, 0.50, 0.25, 0.00)


def _nearest_label_gap(x):
    """Distance from x to the closest value 01_'s 4-level scale can express."""
    return min(abs(x - v) for v in STATUS_LEVELS)
print(f"\n    {'component':<36}{'seg':<5}{'composed':>10}{'01_':>7}{'diff':>8}")
v13_fail = []
v13_unres = []
for comp in sorted(PRESENCE_TIER):
    for seg in segments:
        m = status_df[status_df['Component'].map(norm_key) == norm_key(comp)]
        if not len(m):
            continue
        static = float(m.iloc[0][f'factor_{seg}'])
        composed = float(PRESENCE_TIER[comp][seg][yi25])
        diff = composed - static
        unresolvable = _nearest_label_gap(composed) > V13_TOL
        if abs(diff) <= V13_TOL:
            flag = ''
        elif unresolvable:
            flag = '  (unresolvable on a 4-level scale)'
        else:
            flag = '  <-- OUTSIDE'
            v13_fail.append((comp, seg, composed, static, diff))
        if unresolvable:
            v13_unres.append((comp, seg, composed, static))
        print(f"    {comp[:35]:<36}{seg:<5}{composed:>10.2f}{static:>7.2f}"
              f"{diff:>+8.2f}{flag}")

n_checked = sum(1 for c in PRESENCE_TIER for s in segments
                if len(status_df[status_df['Component'].map(norm_key) == norm_key(c)]))
n_assert = n_checked - len(v13_unres)
print(f"\n    {n_assert - len(v13_fail)} / {n_assert} asserted rows within {V13_TOL:.2f}")
if v13_unres:
    print(f"    {len(v13_unres)} row(s) not asserted -- the composed value falls between two")
    print(f"    of 01_'s four labels, so the file cannot express it:")
    for c, sg, comp, st in v13_unres:
        print(f"      {c[:34]:<36}{sg:<5}composed {comp:.2f}, nearest label {st:.2f}")
print("    V13 PASSED -- the tier axis reproduces the 2025 observation."
      if not v13_fail else
      f"    V13 -- {len(v13_fail)} outside tolerance, listed above.")



# ============================================================================
# V15 -- DO THE TWO MODELS COUNT THE SAME CAR?
#
# The sensor model counts ELEMENTS (chips). The wiring model reads 19_ sheet
# Tiers, which counts MODULES (boxes). A corner radar is ONE box containing an
# RF transceiver AND a temperature sensor, so an element count is double a
# module count for radar -- and a radar box takes ONE cable however many chips
# are inside.
#
# 19_ sheet Modules_vs_Elements names, per component, the PRIMARY element whose
# count EQUALS the module count. This check composes module counts the sensor
# model's way and asserts they overlap the wiring model's Tiers ranges. Without
# it the two models can drift apart silently, which is exactly what happened:
# on an element basis EF radar overlapped at 0 of 5 tiers.
#
# Ranges, not points: two ranges pass if they OVERLAP AT ALL. Both sides are
# Monte Carlo inputs, so demanding equal midpoints would be demanding that two
# independent estimates agree to the decimal.
# ============================================================================

print("\n" + "="*70)
print("V15 -- MODULE COUNTS: SENSOR MODEL vs WIRING MODEL (19_ Tiers)")
print("="*70)

_mve = pd.read_excel(ADAS_FILE, sheet_name="Modules_vs_Elements", header=3)
_mve = _mve[_mve.iloc[:, 0].notna()]
PRIMARY_ELEMENT = {str(r.iloc[0]).strip(): str(r.iloc[1]).strip()
                   for _, r in _mve.iterrows() if str(r.iloc[1]).strip() != "-"}
_tiers_tbl = pd.read_excel(ADAS_FILE, sheet_name="Tiers", header=3)
_tiers_tbl = _tiers_tbl[_tiers_tbl.Tier.notna()]

V15_GROUPS = {
    "camera":     (["Front ADAS camera", "Rear view camera", "Side / mirror cameras",
                    "Driver monitoring camera"], "Cam_min", "Cam_max"),
    "radar":      (["Front long-range radar", "Corner short/mid-range radars"],
                   "Radar_min", "Radar_max"),
    "ultrasonic": (["Ultrasonic sensors"], "Ultra_min", "Ultra_max"),
}
_SEG06 = {"AB": "A-B", "CD": "C-D", "EF": "E-F"}


def _module_range(components, seg, tier):
    """Modules per vehicle at `tier`: primary element only, scaled by presence."""
    lo = hi = 0.0
    for comp in components:
        cell = _pres_raw.loc[_pres_raw.Component.map(norm_key) == norm_key(comp), tier]
        if not len(cell) or isinstance(cell.iloc[0], str):
            continue                      # lidar reads "Driver B", not a tier value
        f = float(cell.iloc[0])
        prim = PRIMARY_ELEMENT.get(comp)
        r = sensor_df[(sensor_df['Component'].map(norm_key) == norm_key(comp)) &
                      (sensor_df['SensorType'].map(norm_key) == norm_key(prim))]
        if not len(r):
            continue
        c = _SEG06[seg]
        lo += f * float(r[f'{c}_Min'].iloc[0])
        hi += f * float(r[f'{c}_Max'].iloc[0])
    return lo, hi


_pres_raw = pd.read_excel(ADAS_FILE, sheet_name="Presence_per_Tier", header=3)
_pres_raw = _pres_raw[_pres_raw.Component.notna()]

v15_fail = []
print(f"\n    {'group':<12}{'seg':<5}{'tier':<6}{'sensor model':>16}{'wiring model':>16}   result")
for gname, (comps, cmin, cmax) in V15_GROUPS.items():
    for seg in segments:
        # Tiers is per SEGMENT since 2026-08-07 -- take only this segment's rows.
        # Without this filter each segment is compared against all fifteen rows,
        # so AB gets checked against EF's counts.
        seg_rows = _tiers_tbl[_tiers_tbl.Segment.astype(str).str.strip() == seg]
        for _, trow in seg_rows.iterrows():
            s_lo, s_hi = _module_range(comps, seg, trow.Tier)
            w_lo, w_hi = float(trow[cmin]), float(trow[cmax])
            ok = not (s_hi < w_lo or w_hi < s_lo)
            if not ok:
                v15_fail.append((gname, seg, trow.Tier, (s_lo, s_hi), (w_lo, w_hi)))
            print(f"    {gname:<12}{seg:<5}{trow.Tier:<6}"
                  f"{f'{s_lo:.1f} - {s_hi:.1f}':>16}{f'{w_lo:.0f} - {w_hi:.0f}':>16}"
                  f"   {'overlap' if ok else 'NO OVERLAP  <--'}")
_n15 = len(V15_GROUPS) * len(_tiers_tbl)   # Tiers already carries the segment
print(f"\n    {_n15 - len(v15_fail)} / {_n15} overlap")
print("    V15 PASSED -- the two models describe the same car."
      if not v15_fail else
      f"    V15 -- {len(v15_fail)} combinations do not overlap, listed above.")


# ============================================================================
# YEAR-RESOLVED STATISTICS  -- the output this whole step exists to produce
# ============================================================================

print("\n" + "="*70)
print("YEAR-RESOLVED SENSOR COUNTS")
print("="*70)

rows_out = []
for segment in segments:
    for key, acc in all_segment_accs[segment].items():
        name = key[1] if isinstance(key, tuple) else key
        level = 'Domain' if isinstance(key, tuple) else (
            'Total' if key == 'total' else 'SensorType')
        mean = acc.mean
        p025 = acc.percentile(2.5)
        p50 = acc.percentile(50)
        p975 = acc.percentile(97.5)
        mode = acc.coarse_mode()
        std = acc.std
        for yi, yr in enumerate(YEARS):
            rows_out.append({
                'Segment': segment, 'Level': level, 'Name': name, 'Year': int(yr),
                'Mean': mean[yi], 'Mode': mode[yi], 'Median': p50[yi],
                'Std': std[yi], 'P025': p025[yi], 'P975': p975[yi],
            })
year_stats = pd.DataFrame(rows_out)
year_stats.to_csv(SCRIPT_DIR / 'csv_monte_carlo' / 'sensor_year_stats.csv', index=False)
print(f"  {len(year_stats):,} rows -> csv_monte_carlo/sensor_year_stats.csv")
print(f"  ({len(segments)} segments x {len(all_segment_accs['AB'])} series "
      f"x {len(YEARS)} years)")

print("\n  TOTAL sensors per vehicle, mean, by year:")
print(f"    {'seg':<5}" + "".join(f"{y:>9}" for y in SNAPSHOT_YEARS))
for segment in segments:
    m = all_segment_accs[segment]['total'].mean
    print(f"    {segment:<5}" + "".join(
        f"{m[int(np.searchsorted(YEARS, y))]:>9.1f}" for y in SNAPSHOT_YEARS))

print("\n  Battery cell VOLTAGE sensing, mean, by year (the 800V driver):")
print(f"    {'seg':<5}" + "".join(f"{y:>9}" for y in SNAPSHOT_YEARS))
for segment in segments:
    m = all_segment_accs[segment]['voltage sensor'].mean
    print(f"    {segment:<5}" + "".join(
        f"{m[int(np.searchsorted(YEARS, y))]:>9.1f}" for y in SNAPSHOT_YEARS))


# ============================================================================
# SEGMENT COMPARISON (grand total)
# ============================================================================

print("\n" + "="*70)
print(f"SEGMENT COMPARISON  (at BASE_YEAR = {BASE_YEAR})")
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