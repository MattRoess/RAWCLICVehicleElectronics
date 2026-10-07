"""ONE simulated vehicle, shared by every model — the per-draw random state.

**Copyright notice:** Copyright © 2025 & 2026 Empa, Matthias Roesslein

WHY THIS EXISTS. Each model draws its own vehicles. That is correct when a model
runs alone, and wrong the moment their outputs are added together, because the
four domains are not independent: a car that is zonal, 800 V and carrying H4
hardware is all of those things in its wiring AND its sensors AND its boards AND
its motors, at the same time. Summing four independently drawn fleets produces a
total band that is too NARROW, because the common-mode variation cancels.

    tools/plot_composition.py before 2026-08-13 did exactly that, and justified
    it in a comment: "separate models with independent draws, so independent
    sampling is the right assumption between them". Separate SOFTWARE is not
    independent PHYSICS. Three of the four models read the same driver workbook.

So the drivers that more than one model reads are drawn ONCE, here, and handed
to every model as the same vehicle. A model given a VehicleState must use it
instead of drawing its own; a model given None draws exactly as it always has,
so every existing single-model output stays reproducible from its own seed.

    from vehicle_state import draw_vehicle_state
    st = draw_vehicle_state(rng, n=5000, years=YEARS)

WHAT IS IN HERE AND WHAT IS NOT. Only the drivers that are genuinely SHARED. A
quantity used by one model alone stays that model's business and keeps being
drawn inside it -- putting it here would centralise randomness for its own sake
and make every model depend on a field nothing else reads.

    shared, lives here          read by
    ------------------------    --------------------------------
    architecture state          Wiring, PCB
    ADAS hardware tier          Wiring, Sensors, PCB
    800 V voltage state         Wiring, Sensors
    post-2040 scenario          Wiring, Motors
    lidar (Driver B)            Wiring, Sensors

    NOT shared, stays in its model
    -----------------------------
    wire gauge, SDV depth, height adder     Wiring
    per-row sensor count within min-max     Sensors
    board length/width, q calibration       PCB
    motor mass, gearbox, housing split      Motors

EVERY FIELD IS ONE DRAW PER VEHICLE, HELD ACROSS ALL YEARS. That is what makes
iteration i a consistent adoption percentile: one design, on one timeline, for
its whole life. Redrawing per year would let a car be zonal in 2040 and
conventional in 2041, which averages the transition away and returns a smeared
mean matching no real fleet. See drivers.draw_tier_state for the same argument.

A NOTE ON WHAT IS NOT YET SHARED. Vehicle SIZE is common-mode in reality -- a
big car is big in every domain -- and only the wiring model carries it today
(CV_VEHICLE = 0.10). Adding it here would widen the joint band correctly, but it
changes the marginal distribution of three models that currently have no size
factor at all, so it is a modelling decision and not a defect fix. Deliberately
left out pending that decision; see docs/12_JOINT_MC_DESIGN.md.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Per-vehicle spread on WHEN a manufacturer transitions. UNIT: years, 1 sigma.
# Imported rather than redefined -- drivers.py is the single source, and
# BevWiring.py carries a constant of the same name that must agree with it.
from drivers import TRANSITION_TIMING_SPREAD_Y


@dataclass
class VehicleState:
    """The shared random state of `n` simulated vehicles.

    Every array is (n,) -- one value per vehicle, held across all years.

    Fields:
        u_arch:       architecture adoption percentile.        UNIT: [0,1]
        d_arch:       architecture transition timing offset.   UNIT: years,
                      positive = this manufacturer moves LATER
        u_tier:       ADAS hardware-tier adoption percentile.  UNIT: [0,1]
        d_tier:       tier transition timing offset.           UNIT: years
        u_volt:       800 V adoption percentile.               UNIT: [0,1]
        u_scen:       post-2040 scenario percentile.           UNIT: [0,1]
        u_lidar_band: which Driver-B band this vehicle lives in. UNIT: [0,1]
        d_lidar_lag:  DEVIATION from the mean China->Europe lidar lag.
                      UNIT: years. Not the lag itself -- 19_'s anchors already
                      carry the mean, so passing the lag would double-count it.

    WHY SEPARATE u_arch AND u_tier. A manufacturer that moves early on zonal
    architecture is not necessarily early on ADAS hardware; they are different
    supply chains and different cost curves. Sharing ONE uniform between them
    would impose a rank correlation of exactly 1, which is a stronger claim than
    any of the source data supports. They are drawn independently here, which
    asserts nothing. If evidence for a correlation ever appears, this is the
    one place to put it.
    """

    u_arch: np.ndarray
    d_arch: np.ndarray
    u_tier: np.ndarray
    d_tier: np.ndarray
    u_volt: np.ndarray
    u_scen: np.ndarray
    u_lidar_band: np.ndarray
    d_lidar_lag: np.ndarray

    def __len__(self) -> int:
        return len(self.u_arch)

    def slice(self, lo: int, hi: int) -> "VehicleState":
        """Vehicles [lo:hi) as their own state, for chunked accumulation.

        The joint Monte Carlo runs in chunks so memory stays independent of the
        iteration count. Slicing rather than redrawing is what keeps chunk k of
        one model describing the SAME cars as chunk k of another.
        """
        return VehicleState(**{f: getattr(self, f)[lo:hi]
                               for f in self.__dataclass_fields__})


def draw_vehicle_state(rng, n, years=None, lidar_lag=None) -> VehicleState:
    """Draw `n` vehicles' shared state from one generator.

    Args:
        rng:       np.random.Generator. ONE generator for the whole joint run,
                   so the entire composition is reproducible from a single seed.
        n:         number of vehicles.
        years:     unused; accepted so callers can pass their year grid without
                   having to know that no field currently depends on it.
        lidar_lag: (mean_y, sd_y) from drivers.load_lidar_bands. Required --
                   d_lidar_lag is a deviation and cannot be drawn without the
                   mean it deviates from. Passing None raises rather than
                   silently defaulting, because a wrong lidar lag is invisible
                   in the output and shifts every lidar-bearing series.

    Returns:
        VehicleState with every field of length n.
    """
    if lidar_lag is None:
        raise ValueError(
            "lidar_lag is required -- pass drivers.load_lidar_bands(years)[1]. "
            "d_lidar_lag is a DEVIATION from the mean lag; drawing it without "
            "the mean would silently shift every lidar-bearing series.")
    lag_mean, lag_sd = lidar_lag
    return VehicleState(
        u_arch=rng.random(n),
        d_arch=rng.normal(0.0, TRANSITION_TIMING_SPREAD_Y, size=n),
        u_tier=rng.random(n),
        d_tier=rng.normal(0.0, TRANSITION_TIMING_SPREAD_Y, size=n),
        u_volt=rng.random(n),
        u_scen=rng.random(n),
        u_lidar_band=rng.random(n),
        d_lidar_lag=rng.normal(lag_mean, lag_sd, size=n) - lag_mean,
    )


def pick_from_uniform(u, weights):
    """Discrete choice from a per-vehicle uniform -- the injectable form of
    rng.choice(k, p=weights).

    Args:
        u:       (n,) one uniform per vehicle. UNIT: [0,1].
        weights: (k,) probabilities, summing to 1.

    Returns:
        (n,) integer index in [0, k).

    WHY NOT rng.choice. rng.choice consumes the generator, so two models asked
    to pick "the same vehicle's scenario" would get different answers unless
    they happened to consume their generators in lockstep. Deriving the pick
    from a stored uniform makes the same vehicle give the same scenario in every
    model, which is the entire point of the shared state.
    """
    w = np.asarray(weights, float)
    return np.searchsorted(np.cumsum(w / w.sum()), np.asarray(u, float),
                           side="right").clip(0, len(w) - 1)
