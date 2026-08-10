"""Streaming statistics for Monte Carlo draws — ONE implementation.

WHY THIS EXISTS. The point of the accumulator is that **memory stops depending
on the number of draws**. Instead of holding every draw, each chunk is folded
into a fixed-bin histogram plus a few running sums, so 200,000 draws and
200,000,000 draws cost the same.

That matters concretely for the PCB model. Holding the draws costs:

    today, 1 year     235 MB   (34 MB top level + 202 MB across 6 categories)
    at P-e, 51 years  12.0 GB  <-- does not fit
    accumulator        1.2 MB  at any draw count

Before 2026-08-10 the class lived in Wiring/BevWiring.py and again in
SensorNumbersMC/SensorNumbersMC.py, and PCBAreaMC was about to make a third
copy. Same reasoning as tools/drivers.py: two copies of the same statistics
code drift, and the drift shows up as a validation that quietly compares a
model against itself. This module is the union of both versions --
BevWiring's mode()/edges() and SensorNumbersMC's std/min/max/1-D handling.

WHAT IS EXACT AND WHAT IS NOT. Worth knowing before trusting a number:

    exact    mean, std, variance, min, max, and every correlation from
             CoMoments -- these are running sums, not binned
    binned   percentiles and the mode, resolved to 1/N_ACC_BINS of the
             pilot range and linearly interpolated inside the containing bin

Validation P5 ("accumulator vs full draw", +/-3%) exists to bound the binned
half. The exact half needs no tolerance.
"""

from __future__ import annotations

import numpy as np

# 50-bin histograms are a project convention and are not negotiable: every
# exported histogram in the suite has 50 bins so they can be compared by eye.
N_HIST_BINS = 50

# INTERNAL resolution. Percentiles read off a 50-bin histogram are quantised to
# 2% of the range, which is far too coarse for a p2.5 or p97.5. 1000 bins are
# held internally and summed down to 50 only on export.
N_ACC_BINS = 1000

# Fractional widening of the pilot range. The pilot is a short pre-run used to
# find lo/hi; the padding covers draws beyond anything the pilot happened to
# see. Values outside the range are still COUNTED (under/over) rather than
# silently dropped, so a bad range is detectable instead of invisible.
PILOT_PAD = 0.35

assert N_ACC_BINS % N_HIST_BINS == 0, "N_ACC_BINS must be a multiple of N_HIST_BINS"


class Accumulator:
    """Fixed-bin histogram accumulator. Memory independent of the draw count.

    The trailing axis is a generic SERIES axis. It is length 1 for a scalar
    metric, and becomes the year axis when a model grows a time dimension --
    without this class changing at all.

        acc = Accumulator(lo, hi, n_series)
        for chunk in chunks:          # chunk: (n_chunk,) or (n_chunk, n_series)
            acc.add(chunk)
        acc.mean, acc.std, acc.percentile(50), acc.coarse(0)
    """

    def __init__(self, lo, hi, n_series=1, n_bins=N_ACC_BINS):
        lo = np.atleast_1d(np.asarray(lo, dtype=float))
        hi = np.atleast_1d(np.asarray(hi, dtype=float))
        span = np.where(hi - lo <= 0, 1.0, hi - lo)
        self.lo = lo - PILOT_PAD * span / 2.0
        self.hi = hi + PILOT_PAD * span / 2.0
        self.width = np.where((self.hi - self.lo) / n_bins <= 0, 1.0,
                              (self.hi - self.lo) / n_bins)
        self.n_bins = n_bins
        self.counts = np.zeros((n_series, n_bins), dtype=np.int64)
        self.total = np.zeros(n_series)
        self.total_sq = np.zeros(n_series)
        self.vmin = np.full(n_series, np.inf)
        self.vmax = np.full(n_series, -np.inf)
        self.n = 0
        # Draws falling outside [lo, hi] are counted, never dropped. A nonzero
        # under/over means the pilot range was too narrow and the percentiles
        # are not trustworthy -- check it rather than assuming it is zero.
        self.under = np.zeros(n_series, dtype=np.int64)
        self.over = np.zeros(n_series, dtype=np.int64)

    def add(self, arr):
        """arr: (n_chunk,) or (n_chunk, n_series)."""
        arr = np.asarray(arr, dtype=float)
        if arr.ndim == 1:
            arr = arr[:, None]
        self.n += arr.shape[0]
        self.total += arr.sum(axis=0)
        self.total_sq += (arr ** 2).sum(axis=0)
        self.vmin = np.minimum(self.vmin, arr.min(axis=0))
        self.vmax = np.maximum(self.vmax, arr.max(axis=0))
        idx = np.floor((arr - self.lo[None, :]) / self.width[None, :]).astype(np.int64)
        self.under += (idx < 0).sum(axis=0)
        self.over += (idx >= self.n_bins).sum(axis=0)
        np.clip(idx, 0, self.n_bins - 1, out=idx)
        for s in range(arr.shape[1]):
            self.counts[s] += np.bincount(idx[:, s], minlength=self.n_bins)

    # ---- exact: running sums, no binning involved -------------------------

    @property
    def mean(self):
        return self.total / max(self.n, 1)

    @property
    def var(self):
        """Population variance, matching np.var's default ddof=0."""
        n = max(self.n, 1)
        return np.maximum(self.total_sq / n - (self.total / n) ** 2, 0.0)

    @property
    def std(self):
        return np.sqrt(self.var)

    @property
    def vmin_(self):
        return self.vmin

    @property
    def vmax_(self):
        return self.vmax

    # ---- binned: resolution is 1/n_bins of the pilot range -----------------

    def percentile(self, q):
        """q in 0..100. Linear interpolation within the containing bin."""
        out = np.empty(self.counts.shape[0])
        for s in range(self.counts.shape[0]):
            c = np.cumsum(self.counts[s])
            target = q / 100.0 * c[-1]
            i = int(np.searchsorted(c, target))
            i = min(i, self.n_bins - 1)
            below = c[i - 1] if i > 0 else 0
            frac = (target - below) / max(self.counts[s][i], 1)
            out[s] = self.lo[s] + (i + frac) * self.width[s]
        return out

    def mode(self):
        """Mode at FINE resolution (n_bins)."""
        i = self.counts.argmax(axis=1)
        return self.lo + (i + 0.5) * self.width

    def edges(self, s=0):
        return self.lo[s] + np.arange(self.n_bins + 1) * self.width[s]

    def coarse(self, s=0, n_out=N_HIST_BINS):
        """Sum the fine bins down to exactly n_out bins.

        Returns (edges, counts) with len(counts) == n_out. Exact, because
        N_ACC_BINS is constrained to be a multiple of N_HIST_BINS.
        """
        k = self.n_bins // n_out
        counts = self.counts[s].reshape(n_out, k).sum(axis=1)
        w = self.width[s] * k
        edges = self.lo[s] + np.arange(n_out + 1) * w
        return edges, counts

    def coarse_mode(self):
        """Mode read off the SAME 50-bin histogram that gets exported, so the
        reported Mode can always be reproduced from the histogram file."""
        out = np.empty(self.counts.shape[0])
        for s in range(self.counts.shape[0]):
            e, c = self.coarse(s)
            i = int(np.argmax(c))
            out[s] = 0.5 * (e[i] + e[i + 1])
        return out


class CoMoments:
    """Running co-moments for EXACT correlations without keeping the draws.

    A histogram accumulator holds marginals only, so it cannot answer "how does
    total_small_area co-vary with total_area?" -- and PCBAreaMC's sensitivity
    block asks exactly that, via np.corrcoef on the raw arrays.

    Pearson's r needs only five sums per pair:

        r = (n*Sxy - Sx*Sy) / sqrt((n*Sxx - Sx^2) * (n*Syy - Sy^2))

    so the correlations survive the port EXACTLY -- not to a tolerance. This is
    a case where streaming is not an approximation of the full-draw answer, it
    is the same answer.

    Keys are the metric names; every pair is tracked against `ref`.
    """

    def __init__(self, keys, ref):
        self.keys = list(keys)
        self.ref = ref
        self.n = 0
        self.s = {k: 0.0 for k in self.keys}
        self.ss = {k: 0.0 for k in self.keys}
        self.sxy = {k: 0.0 for k in self.keys}

    def add(self, chunk: dict):
        """chunk: {key: (n_chunk,)} including the reference key."""
        y = np.asarray(chunk[self.ref], dtype=float)
        self.n += y.shape[0]
        for k in self.keys:
            x = np.asarray(chunk[k], dtype=float)
            self.s[k] += x.sum()
            self.ss[k] += (x * x).sum()
            self.sxy[k] += (x * y).sum()

    def corr(self, k):
        n = self.n
        sx, sy = self.s[k], self.s[self.ref]
        sxx, syy = self.ss[k], self.ss[self.ref]
        num = n * self.sxy[k] - sx * sy
        den = np.sqrt(max(n * sxx - sx * sx, 0.0) * max(n * syy - sy * sy, 0.0))
        return float(num / den) if den > 0 else np.nan

    def var(self, k):
        """Population variance of key k, ddof=0, matching np.var."""
        n = max(self.n, 1)
        return float(max(self.ss[k] / n - (self.s[k] / n) ** 2, 0.0))
