"""Shared driver curves — ONE implementation, read by every model.

**Copyright notice:** Copyright © 2025 & 2026 Empa, Matthias Roesslein

WHY THIS EXISTS. Before 2026-08-10 the same curve reader lived twice, in
Wiring/BevWiring.py and SensorNumbersMC/SensorNumbersMC.py. They were logically
identical but separately maintained, and step 7 was about to add a THIRD copy in
PCBAreaMC. That is the failure V12 exists to catch: two models computing the
same share from the same file and drifting apart.

The project's own rule, from 04_SENSOR_MODEL_DESIGN.md section 6.1:

    Do not recompute the tier shares. Read the same source the wiring model
    reads. If it is computed twice it will diverge.

Everything here is a pure reader: it opens a workbook, interpolates anchors, and
returns arrays. No sampling, no randomness, no state. The MODELS draw; this
module only says what they are drawing from.

    from drivers import monotone_curve, load_800v_share, load_architecture_shares

Import it by putting tools/ on sys.path — the models do this at their top.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "Data"

PENETRATION_FILE = DATA_DIR / "18_BEV_technology_penetration.xlsx"
ADAS_FILE = DATA_DIR / "19_ADAS_sensor_adoption.xlsx"

SEGMENTS = ["AB", "CD", "EF"]
ARCH_STATES = ["Conventional", "Transitional", "SDV_Zonal"]
TIERS = ["H0", "H1", "H2", "H3", "H4"]

# 19_ Presence_per_Tier marks lidar as governed by Driver B, not by tier.
LIDAR_H4_FLOOR = 0.80


def monotone_curve(years, anchor_years, anchor_vals):
    """PCHIP through share anchors, clipped to [0, 1].

    C1 and non-overshooting, so a share stays in range and there is no kink at
    the 5-year anchors. np.interp was tried first and its slope discontinuities
    were visible as corners in the output bands (BevWiring_STATUS.md S5 item 4).
    Outside the anchor range the end values are held flat.
    """
    from scipy.interpolate import PchipInterpolator
    x = np.asarray(anchor_years, float)
    y = np.asarray(anchor_vals, float)
    o = np.argsort(x)
    x, y = x[o], y[o]
    if len(x) < 2:
        return np.full(len(years), y[0] if len(y) else 0.0)
    f = PchipInterpolator(x, y, extrapolate=False)
    return np.clip(np.nan_to_num(f(np.clip(years, x[0], x[-1]))), 0.0, 1.0)


def _penetration(sheet="Penetration"):
    if not PENETRATION_FILE.exists():
        raise FileNotFoundError(f"Penetration workbook not found: {PENETRATION_FILE}")
    p = pd.read_excel(PENETRATION_FILE, sheet_name=sheet, header=4)
    return p[p["Driver"].notna()]


def load_800v_share(years, band="Share_Mode"):
    """800V share of new sales per segment. {segment: (n_years,)}.

    Single source of truth for the voltage driver. Validation V12 checks that
    the sensor model and the wiring model get the same array from this.

    band selects Share_Min / Share_Mode / Share_Max. The Min/Max band is real
    uncertainty (+/-0.12 on the share) and callers that ignore it are throwing
    away spread the project asked to keep.
    """
    pen = _penetration()
    out = {}
    for seg in SEGMENTS:
        d = pen[(pen.Driver == "Voltage") & (pen.Segment == seg)
                & (pen.State == "800V")].sort_values("Year")
        out[seg] = monotone_curve(years, d.Year.to_numpy(float),
                                  d[band].to_numpy(float))
    return out


def load_architecture_shares(years, band="Share_Mode"):
    """Architecture state shares per segment. {segment: (n_states, n_years)}.

    Rows are ARCH_STATES in order; columns are renormalised to sum to 1 after
    interpolation, because PCHIP through three independent anchor sets does not
    preserve the sum.

    THE STATES ARE DISCRETE. A vehicle is one architecture, never a blend. A
    caller must draw a state per iteration and hold it across years -- see
    BevWiring.comonotonic_state. Share-weighting instead collapses a bimodal
    mixture into its mean and destroys the band; that error is why generation 4
    of the wiring model was replaced (MODEL_HISTORY.md).
    """
    pen = _penetration()
    out = {}
    for seg in SEGMENTS:
        m = []
        for st in ARCH_STATES:
            d = pen[(pen.Driver == "Architecture") & (pen.Segment == seg)
                    & (pen.State == st)].sort_values("Year")
            m.append(monotone_curve(years, d.Year.to_numpy(float),
                                    d[band].to_numpy(float)))
        m = np.vstack(m)
        out[seg] = m / np.maximum(m.sum(axis=0, keepdims=True), 1e-12)
    return out


def load_tier_shares(years):
    """ADAS hardware-tier shares per segment. {segment: (n_tiers, n_years)}.

    Rows are TIERS in order, columns renormalised to sum to 1. Discrete, same
    caveat as load_architecture_shares.
    """
    if not ADAS_FILE.exists():
        raise FileNotFoundError(
            f"ADAS adoption workbook not found: {ADAS_FILE}\n"
            f"Generate it with: python3 tools/make_19_adas_sensor_adoption.py")
    ts = pd.read_excel(ADAS_FILE, sheet_name="Tier_Shares", header=3)
    ts = ts[ts["Segment"].notna()]
    out = {}
    for seg in SEGMENTS:
        d = ts[ts.Segment == seg].sort_values("Year")
        m = np.vstack([monotone_curve(years, d.Year.to_numpy(float),
                                      d[t].to_numpy(float)) for t in TIERS])
        out[seg] = m / np.maximum(m.sum(axis=0, keepdims=True), 1e-12)
    return out


def load_lidar_share(years, band="Share_Mode"):
    """Driver B — lidar-equipped share of new BEV sales, Europe. (n_years,)."""
    ld = pd.read_excel(ADAS_FILE, sheet_name="Lidar", header=3)
    ld = ld[ld["Year"].notna()].sort_values("Year")
    return monotone_curve(years, ld.Year.to_numpy(float), ld[band].to_numpy(float))


def load_presence_per_tier(years):
    """presence(component, segment, year) for every ADAS component in 19_.

    Returns {component: {segment: (n_years,)}}.

        presence = SUM_tier  share(tier, segment, year) x presence(component|tier)

    Lidar is NOT tier-governed: 19_ marks its H3/H4 cells with a text marker and
    the value comes from Driver B instead, floored at LIDAR_H4_FLOOR for H4.

    A cell that is not a finite number IS that marker. Checking for a string is
    not enough -- if the marker is ever written with a leading "=", Excel stores
    it as a formula and every reader sees NaN. That happened once and produced
    NaN sensor counts 200,000 draws later.
    """
    shares = load_tier_shares(years)
    lidar = load_lidar_share(years)

    pr = pd.read_excel(ADAS_FILE, sheet_name="Presence_per_Tier", header=3)
    pr = pr[pr["Component"].notna() & pr[TIERS].notna().any(axis=1)]

    out = {}
    for _, r in pr.iterrows():
        comp = str(r["Component"]).strip()
        per_tier = [None if (isinstance(r[t], str) or pd.isna(r[t])) else float(r[t])
                    for t in TIERS]
        out[comp] = {}
        for seg in SEGMENTS:
            acc = np.zeros(len(years))
            for ti, t in enumerate(TIERS):
                p = per_tier[ti]
                if p is None:
                    p = lidar if t == "H3" else np.maximum(lidar, LIDAR_H4_FLOOR)
                acc = acc + shares[seg][ti] * p
            out[comp][seg] = np.clip(acc, 0.0, 1.0)
    return out


# Per-vehicle spread on WHEN a manufacturer transitions. UNIT: years, 1 sigma.
# Must match Wiring/BevWiring.py's constant of the same name.
TRANSITION_TIMING_SPREAD_Y = 5.0


def shift_shares(shares, years, delta):
    """Re-read the share curves with each vehicle's own time offset.

    Ported from BevWiring._shift_shares 2026-08-11, vectorised. This is the
    ONLY coherent way to put uncertainty on a set of shares that must sum to 1.

    WHY NOT PERTURB EACH SHARE INDEPENDENTLY. Taking 18_'s Share_Min for all
    three architecture states at once and renormalising does NOT give a
    slow-adoption scenario -- it gives an incoherent mixture. Measured on EF
    SDV_Zonal at 2040: min 1.000, mode 0.975, max 0.791, i.e. the "minimum"
    scenario has MORE zonal adoption than the "maximum" one. After
    renormalisation whichever state was perturbed least dominates and the
    scenario labels stop meaning anything. That approach was written and
    reverted; see 06_PCB_MODEL_DESIGN.md 2.2m.

    Shifting the whole curve in TIME keeps the states coherent by construction,
    and "this manufacturer is five years behind" is a scenario that means
    something physically.

    Args:
        shares: (n_states, n_years) marginal shares.
        years:  (n_years,) UNIT: calendar years. Must be a uniform 1-year grid.
        delta:  (n_iter,)  per-vehicle offset. UNIT: years. Positive = that
                manufacturer transitions LATER.

    Returns:
        (n_states, n_iter, n_years), renormalised to sum to 1 over states.
        End values are held flat outside the anchor range, as np.interp does.
    """
    shares = np.asarray(shares, float)
    years = np.asarray(years, float)
    delta = np.atleast_1d(np.asarray(delta, float))
    n_states, n_years = shares.shape

    x = np.clip(years[None, :] - delta[:, None], years[0], years[-1])
    pos = x - years[0]                                   # uniform grid, step 1
    i0 = np.clip(np.floor(pos).astype(int), 0, n_years - 2)
    frac = pos - i0
    out = np.empty((n_states, len(delta), n_years))
    for k in range(n_states):
        s = shares[k]
        out[k] = s[i0] * (1.0 - frac) + s[i0 + 1] * frac
    out = np.clip(out, 0.0, None)
    return out / np.maximum(out.sum(axis=0, keepdims=True), 1e-12)


# ==========================================================================
# DISCRETE PER-VEHICLE STATE                              added 2026-08-13
#
# WHY THIS SECTION EXISTS. load_presence_per_tier() above returns the presence
# already MIXED over tiers:
#
#     presence(comp, seg, year) = SUM_tier share(tier,seg,year) x p(comp|tier)
#
# That number is the fleet average, and it is the right thing to plot. It is
# the WRONG thing to hand to a Monte Carlo draw, because it gives every
# simulated vehicle 0.62 of a lidar instead of giving 62% of vehicles one lidar
# and the rest none. The mean survives; the band does not. This is the same
# error that caused generation 4 of the wiring model to be replaced -- see the
# warning in load_architecture_shares above.
#
# So a model that draws vehicles needs the UNMIXED table p(comp|tier) plus a
# per-vehicle tier state, which is what the three functions below provide.
# BevWiring has carried its own copy of this scheme since 2026-08-05; these are
# the shared versions, written so the sensor and PCB models can adopt the
# identical construction rather than a third variant of it.
# ==========================================================================

def load_presence_matrix(years):
    """presence(component, tier, year) UNMIXED -- the value for a vehicle that
    IS that tier, never an average across tiers.

    Args:
        years: (n_years,) UNIT: calendar years, uniform 1-year grid.

    Returns:
        presence:  {component: (n_tiers, n_years)} in [0,1]. Rows follow TIERS.
        lidar_gov: {component: (n_tiers,) bool} True in the cells that came
                   from the "Driver B" text marker rather than a number. The
                   caller MUST realise those cells as a per-vehicle Bernoulli
                   draw (see draw_lidar_share), because a lidar share is a
                   fraction of vehicles, not a fraction of a lidar.

    IN A GOVERNED CELL THE MATRIX HOLDS THE FLOOR, NOT THE SHARE. H3 gets 0.0
    and H4 gets LIDAR_H4_FLOOR, and the caller takes

        p(lidar | this vehicle, year) = max(that vehicle's Driver-B share, floor)

    Storing the Mode share here instead would bake one band into the table and
    the floor would then be silently lost the moment a caller substituted its
    own sampled band -- which is exactly the bug this construction avoids.

    A cell that is not a finite number IS the marker -- the same rule, and the
    same reason, as load_presence_per_tier: a marker written with a leading "="
    is stored by Excel as a formula and reaches every reader as NaN.
    """
    pr = pd.read_excel(ADAS_FILE, sheet_name="Presence_per_Tier", header=3)
    pr = pr[pr["Component"].notna() & pr[TIERS].notna().any(axis=1)]

    presence, lidar_gov = {}, {}
    for _, r in pr.iterrows():
        comp = str(r["Component"]).strip()
        mat = np.zeros((len(TIERS), len(years)))
        gov = np.zeros(len(TIERS), dtype=bool)
        for ti, t in enumerate(TIERS):
            v = r[t]
            if isinstance(v, str) or pd.isna(v):
                gov[ti] = True
                # The FLOOR for this tier, not the share -- see the docstring.
                # By the time a manufacturer builds H4 hardware, lidar is taken
                # to be present well above whatever the fleet share is doing.
                mat[ti] = LIDAR_H4_FLOOR if t == "H4" else 0.0
            else:
                mat[ti] = float(v)
        presence[comp] = np.clip(mat, 0.0, 1.0)
        lidar_gov[comp] = gov
    return presence, lidar_gov


def load_lidar_bands(years):
    """Driver B inputs: the three equipped-share curves and the sampled lag.

    Returns:
        bands: (3, n_years) Min / Mode / Max equipped share of new EU BEV sales.
        lag:   (mean_y, sd_y) UNIT: years. China -> Europe lag. SAMPLED, not
               fixed, so "China leads and Europe follows" stays a testable
               hypothesis rather than a baked-in assumption.

    The Lidar sheet already embeds the MEAN lag in its anchors, so a caller
    shifts the curve by the DEVIATION from the mean, never by the lag itself.
    """
    ld = pd.read_excel(ADAS_FILE, sheet_name="Lidar", header=3)
    ld = ld[ld["Year"].notna()].sort_values("Year")
    yr = ld.Year.to_numpy(float)
    bands = np.vstack([monotone_curve(years, yr, ld[c].to_numpy(float))
                       for c in ("Share_Min", "Share_Mode", "Share_Max")])
    pr = pd.read_excel(ADAS_FILE, sheet_name="Parameters", header=2)
    pr = pr[pr["Parameter"].notna()].set_index("Parameter")["Value"]
    return bands, (float(pr["Lidar_Europe_Lag_Y_Mean"]),
                   float(pr["Lidar_Europe_Lag_Y_SD"]))


def draw_tier_state(u_tier, d_tier, shares, years):
    """Per-vehicle ADAS hardware tier, comonotonic across years.

    Args:
        u_tier: (n_iter,) ONE uniform per vehicle, held across years. UNIT:
                [0,1]. Read it as "this vehicle's adoption percentile".
        d_tier: (n_iter,) that vehicle's own transition timing offset.
                UNIT: years. Positive = this manufacturer moves LATER.
        shares: (n_tiers, n_years) marginal tier shares, columns summing to 1.
        years:  (n_years,) UNIT: calendar years, uniform 1-year grid.

    Returns:
        (n_iter, n_years) integer index into TIERS.

    Holding u_tier fixed across years is what makes a vehicle ONE hardware tier
    on ONE timeline for its whole life. Redrawing per year would let a car have
    H4 hardware in 2040 and H1 in 2041, which averages the fork away and
    returns a smeared mean matching no real fleet.
    """
    sh_i = shift_shares(shares, np.asarray(years, float), d_tier)
    u = np.asarray(u_tier, float)
    return (u[None, :, None] > np.cumsum(sh_i, axis=0)).sum(axis=0)


def pick_at_tier(mat, st_tier):
    """Read a per-tier table at each vehicle's own drawn tier.

    Args:
        mat:     (n_tiers, n_years) any per-tier quantity -- presence, a floor,
                 a sensor count.
        st_tier: (n_iter, n_years) tier index from draw_tier_state.

    Returns:
        (n_iter, n_years) the value for the tier THAT vehicle is in, that year.

    The naive mat[st_tier] does NOT do this: it indexes the tier axis and keeps
    the whole year axis behind it, giving (n_iter, n_years, n_years) and a
    silently wrong answer that still has a plausible shape. Use this.
    """
    mat = np.asarray(mat, float)
    return np.take_along_axis(mat[:, None, :], st_tier[None, :, :], axis=0)[0]


def draw_lidar_share(u_band, d_lag_dev, bands, years):
    """Driver B: THIS vehicle's own lidar-equipped share curve.

    Args:
        u_band:    (n_iter,) picks the band this vehicle lives in. UNIT: [0,1].
                   Below 1/3 -> Min (lidar loses to cheaper radar), below 2/3
                   -> Mode, else Max (cost collapse). Equal thirds because the
                   three curves are scenarios, not a fitted distribution.
        d_lag_dev: (n_iter,) DEVIATION from the mean China->Europe lag.
                   UNIT: years. Not the lag itself -- the anchors already carry
                   the mean, so passing the lag would double-count it.
        bands:     (3, n_years) from load_lidar_bands.
        years:     (n_years,) UNIT: calendar years, uniform 1-year grid.

    Returns:
        (n_iter, n_years) share in [0,1].

    THIS RETURNS A SHARE, NOT AN EQUIPPED FLAG. The caller floors it with the
    tier's own floor from load_presence_matrix and only then draws the
    Bernoulli:

        p = np.maximum(share, floor_at_this_vehicles_tier)
        equipped = (u_equip < p)

    Returning the flag directly was tried first and silently discarded the H4
    floor, because the floor is a property of the TIER and this function does
    not know the tier.

    WHAT CHANGES IF THE THIRDS ARE EDITED: the width of the lidar band, and
    with it the spread of every lidar-bearing sensor and wiring series. The
    central estimate barely moves; the tails move a lot.

    NOTE ON THE MEAN. Sampling the three bands in thirds gives a mean of
    (Min+Mode+Max)/3, which is NOT the Mode curve that load_presence_per_tier
    reports. For lidar the bands are asymmetric, so the sampled mean sits a few
    points below the Mode. That is a real property of the band, not an error,
    and BevWiring has sampled it this way since 2026-08-05.
    """
    years = np.asarray(years, float)
    bands = np.asarray(bands, float)
    u_band = np.asarray(u_band, float)
    n_iter, n_years = len(u_band), len(years)

    pick = np.where(u_band < 1.0 / 3.0, 0, np.where(u_band < 2.0 / 3.0, 1, 2))
    band_i = bands[pick]                                        # (n_iter,n_years)

    # shift each vehicle's own curve in time -- vectorised np.interp on a
    # uniform 1-year grid, end values held flat, exactly as shift_shares does
    x = np.clip(years[None, :] - np.asarray(d_lag_dev, float)[:, None],
                years[0], years[-1])
    pos = x - years[0]
    i0 = np.clip(np.floor(pos).astype(int), 0, n_years - 2)
    frac = pos - i0
    rows = np.arange(n_iter)[:, None]
    share = band_i[rows, i0] * (1.0 - frac) + band_i[rows, i0 + 1] * frac
    return np.clip(share, 0.0, 1.0)
