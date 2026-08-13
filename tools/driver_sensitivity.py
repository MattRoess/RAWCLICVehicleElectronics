#!/usr/bin/env python3
"""Which drivers actually carry the uncertainty, and which are swallowed by it?

    python3 tools/driver_sensitivity.py [n_iter]

WHY THIS EXISTS. A model can accumulate drivers indefinitely. Each one feels like
added realism, and each one costs code, data and explanation. The question that
decides whether a driver earns its place is not "is it real?" -- almost all of
them are real -- but "does it change the answer?"

THE TEST. Freeze one driver so every simulated car gets the same value for it,
re-run the joint Monte Carlo, and see how much the total band shrinks. That
shrinkage IS the driver's contribution: it is how much narrower the answer would
become if that one thing were known exactly.

    contribution = band width with everything varying
                 - band width with this driver frozen

A driver whose contribution is near zero is not carrying information. Its
scenarios are eaten by the uncertainty around them, and saying so is a RESULT --
it tells a reader which questions are worth arguing about.

HOW TO READ A NEGATIVE NUMBER. Freezing a driver cannot really widen the band, so
a small negative is Monte Carlo noise. It means the driver's true contribution is
below the noise floor of this run -- which is itself the finding.

WHAT THIS DOES NOT SAY. Contribution is measured on the TOTAL material per
vehicle. A driver can be negligible there and decisive for its own domain: the
ADAS tier moves the sensor numbers a great deal, but sensors are ~0.0% of the
total variance, so it is invisible in the total. Read this table as "what should
I worry about when quoting the total", never as "this driver does not matter".
"""

from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import mc_composition as M          # noqa: E402
import vehicle_state as VS          # noqa: E402

# Draws per variant. UNIT: draws. Lower than the headline run because this
# compares band WIDTHS between variants rather than reporting a band, and the
# comparison is stable well before the band itself is fully converged. Raise it
# if a contribution you care about is close to the noise floor.
N_ITER = 20_000

# Cells reported. Chosen to show mid-transition (2040) across all three segments
# plus one post-transition year, because several drivers switch off once their
# transition completes and a single year would hide that.
CELLS = [("AB", 2040), ("CD", 2040), ("EF", 2040), ("CD", 2070)]

_orig_draw = VS.draw_vehicle_state


def _const(state, field, value):
    setattr(state, field, np.full(len(state), value))


# label -> how to neutralise that driver in a freshly drawn VehicleState.
# Freezing a uniform at 0.5 gives every car the median adoption percentile;
# freezing a timing offset at 0 puts every manufacturer on the central timeline.
FREEZE = {
    "zonal architecture (D)": lambda s: (_const(s, "u_arch", .5),
                                         _const(s, "d_arch", 0.)),
    "400V -> 800V": lambda s: _const(s, "u_volt", .5),
    "post-2040 scenario (C/F)": lambda s: _const(s, "u_scen", .5),
    "ADAS hardware tier (A)": lambda s: (_const(s, "u_tier", .5),
                                         _const(s, "d_tier", 0.)),
    "lidar / China lag (B)": lambda s: (_const(s, "u_lidar_band", .5),
                                        _const(s, "d_lidar_lag", 0.)),
}


def _band_widths(freeze, n_iter):
    """{(segment, year): band width as % of mean} with `freeze` applied."""
    def patched(rng, n, years=None, lidar_lag=None):
        st = _orig_draw(rng, n, years, lidar_lag)
        if freeze:
            freeze(st)
        return st

    VS.draw_vehicle_state = patched
    M.draw_vehicle_state = patched
    try:
        with contextlib.redirect_stdout(io.StringIO()):     # the run is chatty
            df = M.run(n_iter=n_iter, chunk=2_000, seed=M.SEED)
    finally:
        VS.draw_vehicle_state = _orig_draw
        M.draw_vehicle_state = _orig_draw

    t = df[df.Series == "Total"].set_index(["Segment", "Year"])
    return {k: (t.loc[k, "P97_5_g"] - t.loc[k, "P2_5_g"]) / t.loc[k, "Mean_g"] * 100
            for k in t.index}


def main(n_iter=N_ITER):
    print(f"Measuring driver contributions at {n_iter:,} draws per variant "
          f"({len(FREEZE) + 1} runs)...\n")
    base = _band_widths(None, n_iter)
    rows = [(lbl, {c: base[c] - got[c] for c in base})
            for lbl, got in ((l, _band_widths(f, n_iter)) for l, f in FREEZE.items())]
    rows.sort(key=lambda r: -max(r[1][c] for c in CELLS))

    w = 28
    hdr = f"{'driver':{w}s}" + "".join(f"{s} {y}".rjust(11) for s, y in CELLS)
    print("HOW MUCH OF THE TOTAL BAND DOES EACH DRIVER CARRY?")
    print("points of band width lost if that driver were known exactly\n")
    print(hdr)
    print("-" * len(hdr))
    print(f"{'FULL BAND (nothing frozen)':{w}s}"
          + "".join(f"{base[c]:10.0f}%" for c in CELLS))
    print()
    for lbl, d in rows:
        print(f"{lbl:{w}s}" + "".join(f"{d[c]:10.1f} " for c in CELLS))
    print("\n  A near-zero or negative value is below Monte Carlo noise: that")
    print("  driver's scenarios are swallowed by the uncertainty around them.")
    print("  Measured on the TOTAL -- a driver can be negligible here and")
    print("  decisive for its own domain. See the module docstring.")
    return rows


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else N_ITER)
