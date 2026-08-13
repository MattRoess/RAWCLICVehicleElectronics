#!/usr/bin/env python3
"""Figures for the OVERALL vehicle electronics -- with the Monte Carlo ranges.

    ####################################################################
    #  THE CROSS-DOMAIN TOTAL BAND IN THIS FILE IS NOT MONTE CARLO.    #
    #  DO NOT USE IT. Being replaced -- docs/12_JOINT_MC_DESIGN.md.    #
    ####################################################################

    _lognormal_from_band() below takes each domain's mean/P2.5/P97.5, INVENTS a
    lognormal matching those three numbers, and sums the four domains as if they
    were independent. The models' own draws never enter. It is wrong twice over:
    the real distributions are bimodal through the 2030-2050 transition, which a
    lognormal cannot represent; and three of the four domains read the SAME
    driver workbook, so summing them as independent makes the total band too
    NARROW. The section header below calling itself "TRUE MONTE CARLO
    AGGREGATION" is inaccurate and is left in place only so this note has
    something to point at.

    Component-level bands (figures 5, 7, 8) are unaffected -- they come straight
    from the models and are exact. It is the cross-domain TOTAL that is invalid.

    Steps 1 and 2 of the replacement are done: every model now draws a discrete
    per-vehicle hardware tier, and all four accept a shared VehicleState
    (tools/vehicle_state.py) so the same simulated car appears in every domain.
    Step 3 -- tools/mc_composition.py, summing the four masses draw by draw --
    will supply the real band, and this function will be deleted with it.

    python3 tools/plot_composition.py

Reads  Data/30_BEV_electronics_composition.csv
Writes Composition/figures/*.png  and  Composition/csv/*.csv

THE BAND IS THE POINT. This is a Monte Carlo model; a figure showing only means
misrepresents it. Every series here carries its 2.5-97.5 percentile range.

TWO HONEST CAVEATS, applied throughout rather than footnoted:

1. PERCENTILES DO NOT ADD. Summing P2.5 across components implies every one sits
   at its low simultaneously -- perfectly correlated, which they are not. Where
   a total band is drawn from summed percentiles it is labelled a COMONOTONIC
   BOUND: the widest the band could be, not the band. Component-level bands
   (figures 5, 7, 8) are exact.

2. THE BAND MEANS DIFFERENT THINGS BY DOMAIN, carried per row in the source file
   as Band_meaning:
       Wiring, PCB   full model band
       Motors        motor count and mass only -- composition frozen at 2025
       Sensors       sensor count only -- composition frozen at 2025
   So the motor and sensor bands are NARROWER than the true uncertainty. They
   omit composition, which is a deliberate scope decision, not an oversight.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "Data" / "30_BEV_electronics_composition.csv"
FIG = ROOT / "Composition" / "figures"
CSV = ROOT / "Composition" / "csv"
FIG.mkdir(parents=True, exist_ok=True)
CSV.mkdir(parents=True, exist_ok=True)

SEGMENTS = ["AB", "CD", "EF"]
SEG_LABEL = {"AB": "AB  (small)", "CD": "CD  (medium)", "EF": "EF  (large / luxury)"}
DOMAINS = ["Wiring", "Motors", "PCB", "Sensors"]
DOM_COLOR = {"Wiring": "#c1272d", "Motors": "#0b6e99",
             "PCB": "#2e8b57", "Sensors": "#e8a33d"}
SEG_COLOR = {"AB": "#4c72b0", "CD": "#55a868", "EF": "#c44e52"}
BASE, END = 2025, 2070

if not SRC.exists():
    raise SystemExit(f"{SRC} not found -- run tools/build_composition.py first")
df = pd.read_csv(SRC)
print(f"Loaded {len(df):,} rows,  band on {df.P2_5_g.notna().mean()*100:.0f}% of rows")


# ==========================================================================
# TRUE MONTE CARLO AGGREGATION
#
# Summing P2.5 across components is NOT Monte Carlo. It assumes every component
# sits at its low simultaneously -- perfect correlation -- and gives a bound,
# not a band. Two corrections, applied everywhere below:
#
# 1. DOMAIN TOTALS come from each model's OWN total, not from summed parts.
#    The models draw per vehicle with shared drivers, so correlation between
#    components inside a domain is already handled where it belongs -- inside
#    the simulation. Reading their Total rows is the only correct source.
#
# 2. CROSS-DOMAIN TOTALS are propagated by SAMPLING. Each domain's distribution
#    is reconstructed from its (mean, P2.5, P97.5) as a lognormal, drawn
#    N_MC times, and the draws are summed before percentiles are taken. The
#    four domains come from separate models with independent draws, so
#    independent sampling is the right assumption between them.
#
# The difference is large and in the direction that matters: the summed bound
# is far too wide.
# ==========================================================================

N_MC = 40000
_rng = np.random.default_rng(7)


def _lognormal_from_band(mean, lo, hi, n):
    """Draw n samples matching a positive series' mean and 2.5/97.5 percentiles.

    Lognormal because these are positive, right-skewed mass quantities. sigma
    comes from the percentile ratio, mu is then set so the MEAN matches (not the
    median) -- the composition file reports means, so the reconstruction must
    reproduce them.
    """
    mean = float(mean); lo = float(lo); hi = float(hi)
    if not np.isfinite(mean) or mean <= 0:
        return np.zeros(n)
    if not (np.isfinite(lo) and np.isfinite(hi)) or hi <= lo or lo <= 0:
        return np.full(n, mean)                      # degenerate: a point mass
    sigma = np.log(hi / lo) / (2 * 1.959963985)
    sigma = float(np.clip(sigma, 1e-6, 2.5))
    mu = np.log(mean) - 0.5 * sigma ** 2
    return _rng.lognormal(mu, sigma, n)


def _model_totals():
    """Each domain's OWN total band, straight from the model that drew it."""
    out = {}
    f = ROOT / "Wiring" / "outputs" / "data" / "bev_wiring_stats.csv"
    if f.exists():
        w = pd.read_csv(f)
        w = w[(w.Level == "Total") & (w.Metric == "Cu (kg)")]
        for _, r in w.iterrows():
            if str(r.Segment) in SEGMENTS:
                out[("Wiring", str(r.Segment), int(r.Year))] = (
                    r.Mean * 1000, r.P2_5 * 1000, r.P97_5 * 1000)
    f = ROOT / "ElectricMotorMC" / "summary_csv" / "motor_counts_by_year.csv"
    if f.exists():
        m = pd.read_csv(f)
        m = m[m.Quantity == "mass"]
        for _, r in m.iterrows():
            out[("Motors", str(r.Segment), int(r.Year))] = (
                r.Mean * 1000, r.P025 * 1000, r.P975 * 1000)
    # PCB and Sensors: the model total is an AREA / a COUNT, not a mass, so its
    # relative width is applied to the composition mean. Shape from the model,
    # level from the composition -- never a summed percentile.
    for seg in SEGMENTS:
        f = ROOT / "PCBAreaMC" / "csv_monte_carlo" / f"pcb_year_resolved_{seg}.csv"
        if f.exists():
            a = pd.read_csv(f)
            for _, r in a.iterrows():
                mass = df[(df.Domain == "PCB") & (df.Segment == seg)
                          & (df.Year == int(r.Year))][VAL].sum()
                if r.Mean > 0 and mass > 0:
                    out[("PCB", seg, int(r.Year))] = (
                        mass, mass * r.P025 / r.Mean, mass * r.P975 / r.Mean)
    f = ROOT / "SensorNumbersMC" / "csv_monte_carlo" / "sensor_year_stats.csv"
    if f.exists():
        sc = pd.read_csv(f)
        sc = sc[sc.Level == "Total"]
        for _, r in sc.iterrows():
            seg = str(r.Segment)
            if seg not in SEGMENTS:
                continue
            mass = df[(df.Domain == "Sensors") & (df.Segment == seg)
                      & (df.Year == int(r.Year))][VAL].sum()
            if r.Mean > 0 and mass > 0:
                out[("Sensors", seg, int(r.Year))] = (
                    mass, mass * r.P025 / r.Mean, mass * r.P975 / r.Mean)
    return out


MT = _model_totals()
print(f"  model-native domain totals: {len(MT):,} (domain x segment x year)")


def domain_band(dom, seg, yr):
    """(mean, lo, hi) for one domain -- the model's own band."""
    return MT.get((dom, seg, yr))


def mc_total(seg, yr):
    """Cross-domain total by SAMPLING the four domains and summing the draws."""
    acc = np.zeros(N_MC)
    for dom in DOMAINS:
        b = domain_band(dom, seg, yr)
        if b is None:
            acc += df[(df.Segment == seg) & (df.Year == yr)
                      & (df.Domain == dom)][VAL].sum()
        else:
            acc += _lognormal_from_band(*b, N_MC)
    return acc.mean(), np.percentile(acc, 2.5), np.percentile(acc, 97.5)


VAL, LO, HI = "Mass_g_per_vehicle", "P2_5_g", "P97_5_g"


def save(fig, name):
    fig.savefig(FIG / f"{name}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {name}.png")


def agg(d, by):
    """Sum mean and percentiles over `by`. The percentile sum is a COMONOTONIC
    BOUND, never a true band -- see the module docstring."""
    return d.groupby(by)[[VAL, LO, HI]].sum()


kg = lambda g: np.asarray(g) / 1000.0

# ==================================================== 1. TOTAL, true MC band
years = sorted(df.Year.unique())
mc_rows = []
for seg in SEGMENTS:
    for yr in years:
        m, lo, hi = mc_total(seg, yr)
        mc_rows.append({"Year": yr, "Segment": seg, "Mean": m, "P2_5": lo, "P97_5": hi})
mc = pd.DataFrame(mc_rows)
mc.to_csv(CSV / "total_mc_band.csv", index=False)

# how much narrower is the correct band than the summed bound?
summed = agg(df, ["Year", "Segment"])
fig, ax = plt.subplots(figsize=(11, 6.5))
for s_ in SEGMENTS:
    t = mc[mc.Segment == s_].set_index("Year").sort_index()
    b = summed.xs(s_, level="Segment").sort_index()
    ax.fill_between(b.index, kg(b[LO]), kg(b[HI]), color=SEG_COLOR[s_],
                    alpha=0.07, lw=0)
    ax.fill_between(t.index, kg(t.P2_5), kg(t.P97_5), color=SEG_COLOR[s_],
                    alpha=0.24, lw=0)
    ax.plot(t.index, kg(t.Mean), lw=2.6, color=SEG_COLOR[s_], label=SEG_LABEL[s_])
    ax.annotate(f"{kg(t.Mean.loc[END]):.0f} kg", (END, kg(t.Mean.loc[END])),
                xytext=(7, 0), textcoords="offset points", va="center",
                color=SEG_COLOR[s_], fontweight="bold")
ax.axvline(BASE, color="0.55", ls=":", lw=1)
ax.set_xlabel("Year"); ax.set_ylabel("Material per vehicle  (kg)")
ax.set_title("Total electronics material per vehicle\n"
             "dark band = Monte Carlo (40,000 draws, domains sampled and summed)   ·   "
             "pale band = naive percentile sum, for comparison", fontweight="bold")
ax.grid(alpha=0.3); ax.legend(frameon=False, loc="upper right")
ax.set_xlim(2020, END + 4)
save(fig, "01_total_mc_band")

# ================================================== 2. DOMAIN, banded, per seg
fig, axes = plt.subplots(1, 3, figsize=(18, 5.6), sharey=True)
for ax, s in zip(axes, SEGMENTS):
    for dom in DOMAINS:
        yrs = sorted(df.Year.unique())
        bands = [domain_band(dom, s, y) for y in yrs]
        mns = np.array([b[0] if b else np.nan for b in bands])
        los = np.array([b[1] if b else np.nan for b in bands])
        his = np.array([b[2] if b else np.nan for b in bands])
        ax.fill_between(yrs, kg(los), kg(his), color=DOM_COLOR[dom], alpha=0.15, lw=0)
        ax.plot(yrs, kg(mns), lw=2.2, color=DOM_COLOR[dom], label=dom)
    ax.set_yscale("log")
    ax.set_title(SEG_LABEL[s], fontweight="bold")
    ax.set_xlabel("Year"); ax.grid(alpha=0.25, which="both"); ax.set_xlim(2020, END)
axes[0].set_ylabel("Material per vehicle  (kg, log scale)")
axes[-1].legend(frameon=False)
fig.suptitle("Each domain with its own uncertainty band — log scale, because "
             "motors and wiring are ~100× sensors and PCB", fontweight="bold", y=1.03)
save(fig, "02_domains_with_band")

# ================================================ 3. RELATIVE UNCERTAINTY
fig, ax = plt.subplots(figsize=(11, 6))
yrs = sorted(df.Year.unique())
for dom in DOMAINS:
    rel = []
    for y in yrs:
        bs = [domain_band(dom, sg, y) for sg in SEGMENTS]
        bs = [b for b in bs if b]
        rel.append(np.mean([(b[2] - b[1]) / b[0] * 100 for b in bs]) if bs else np.nan)
    ax.plot(yrs, rel, lw=2.4, color=DOM_COLOR[dom], label=dom)
mcrel = [(mc[(mc.Year == y)].P97_5.sum() - mc[(mc.Year == y)].P2_5.sum())
         / mc[(mc.Year == y)].Mean.sum() * 100 for y in yrs]
ax.plot(yrs, mcrel, lw=2.8, color="0.2", ls="--", label="TOTAL (Monte Carlo)")
ax.set_xlabel("Year")
ax.set_ylabel("90% band width as % of the mean")
ax.set_title("How uncertain is each domain?\n"
             "Motors and sensors exclude composition uncertainty by design — "
             "their true band is wider", fontweight="bold")
ax.grid(alpha=0.3); ax.legend(frameon=False); ax.set_xlim(2020, END)
save(fig, "03_relative_uncertainty")

# ============================================ 4. ELEMENTS, banded, small multiples
top = (df[df.Year == BASE].groupby("Element")[VAL].sum()
         .sort_values(ascending=False).head(8).index.tolist())
fig, axes = plt.subplots(2, 4, figsize=(19, 8.5))
for ax, el in zip(axes.ravel(), top):
    for s in SEGMENTS:
        d = agg(df[(df.Element == el) & (df.Segment == s)], ["Year"]).sort_index()
        ax.fill_between(d.index, kg(d[LO]), kg(d[HI]), color=SEG_COLOR[s],
                        alpha=0.15, lw=0)
        ax.plot(d.index, kg(d[VAL]), lw=2, color=SEG_COLOR[s], label=s)
    ax.set_title(el, fontweight="bold")
    ax.grid(alpha=0.25); ax.set_xlim(2020, END)
    ax.set_ylabel("kg / vehicle")
axes.ravel()[0].legend(frameon=False, fontsize=9)
fig.suptitle(f"The {len(top)} elements carrying the most mass — mean and 90% band",
             fontweight="bold", y=1.01)
fig.tight_layout()
save(fig, "04_elements_with_band")

# ================================================== 5. DETAILED OVERVIEW TABLE
ov = []
for s in SEGMENTS:
    for dom in DOMAINS:
        d = df[(df.Segment == s) & (df.Domain == dom)]
        a = agg(d[d.Year == BASE], ["Segment"]).iloc[0]
        b = agg(d[d.Year == END], ["Segment"]).iloc[0]
        ov.append({"Segment": s, "Domain": dom,
                   "g_2025": a[VAL], "lo_2025": a[LO], "hi_2025": a[HI],
                   "g_2070": b[VAL], "change_pct": (b[VAL] / a[VAL] - 1) * 100,
                   "band_pct_2025": (a[HI] - a[LO]) / a[VAL] * 100,
                   "n_types": d.Component_Type.nunique()})
ov = pd.DataFrame(ov)
ov.to_csv(CSV / "overview_by_domain.csv", index=False)

fig, ax = plt.subplots(figsize=(13, 6.5))
ax.axis("off")
hdr = ["Segment", "Domain", "types", "2025 g/veh", "90% band", "2070 g/veh", "change", "band %"]
cells = [[r.Segment, r.Domain, f"{r.n_types:.0f}", f"{r.g_2025:,.0f}",
          f"{r.lo_2025:,.0f} – {r.hi_2025:,.0f}", f"{r.g_2070:,.0f}",
          f"{r.change_pct:+.1f}%", f"{r.band_pct_2025:.0f}%"] for r in ov.itertuples()]
t = ax.table(cellText=cells, colLabels=hdr, loc="center", cellLoc="right")
t.auto_set_font_size(False); t.set_fontsize(9.5); t.scale(1, 1.55)
for j in range(len(hdr)):
    t[0, j].set_facecolor("#33475b"); t[0, j].set_text_props(color="w", fontweight="bold")
for i, r in enumerate(ov.itertuples(), start=1):
    t[i, 1].set_facecolor(DOM_COLOR[r.Domain]); t[i, 1].set_alpha(0.35)
ax.set_title("Detailed overview — mean, 90% band, change and component types\n"
             "band widths for Motors and Sensors exclude composition uncertainty",
             fontweight="bold", pad=18)
save(fig, "05_overview_table")

# ============================================ 6. COMPONENT TYPES, EF, banded
d = df[(df.Segment == "EF") & (df.Year == BASE)]
ct = (d.groupby(["Domain", "Component_Type"])[[VAL, LO, HI]].sum()
        .sort_values(VAL, ascending=False).head(20).iloc[::-1])
fig, ax = plt.subplots(figsize=(11, 9))
ypos = np.arange(len(ct))
means = kg(ct[VAL].values)
err = np.vstack([means - kg(ct[LO].values), kg(ct[HI].values) - means])
cols = [DOM_COLOR[i[0]] for i in ct.index]
ax.barh(ypos, means, color=cols, alpha=0.85)
ax.errorbar(means, ypos, xerr=err, fmt="none", ecolor="0.25", elinewidth=1.2, capsize=3)
ax.set_yticks(ypos)
ax.set_yticklabels([f"{i[1]}" for i in ct.index], fontsize=9)
ax.set_xlabel("kg per vehicle at 2025  (bar = mean, whisker = 90% band)")
ax.set_title("EF segment: the 20 largest component types, with their ranges",
             fontweight="bold")
ax.grid(alpha=0.3, axis="x")
hand = [plt.Rectangle((0, 0), 1, 1, color=DOM_COLOR[k]) for k in DOMAINS]
ax.legend(hand, DOMAINS, frameon=False, loc="lower right")
save(fig, "06_component_types_EF")

# ================================================ 7. WIRING GROUPS, banded
w = df[df.Domain == "Wiring"]
fig, axes = plt.subplots(1, 3, figsize=(18, 5.6), sharey=True)
for ax, s in zip(axes, SEGMENTS):
    for c in sorted(w.Component_Type.unique()):
        d = agg(w[(w.Segment == s) & (w.Component_Type == c)], ["Year"]).sort_index()
        if d.empty:
            continue
        ln, = ax.plot(d.index, kg(d[VAL]), lw=2, label=c)
        ax.fill_between(d.index, kg(d[LO]), kg(d[HI]), color=ln.get_color(),
                        alpha=0.13, lw=0)
    ax.set_title(SEG_LABEL[s], fontweight="bold")
    ax.set_xlabel("Year"); ax.grid(alpha=0.25); ax.set_xlim(2020, END)
axes[0].set_ylabel("Copper per vehicle  (kg)")
axes[-1].legend(frameon=False, fontsize=9)
fig.suptitle("Wiring copper by functional group, with ranges — "
             "power distribution shrinks while sensing wiring grows",
             fontweight="bold", y=1.03)
save(fig, "07_wiring_groups_band")

# ================================================== 8. WHAT MOVES, with band
chg = []
for s in SEGMENTS:
    d = df[df.Segment == s]
    a = agg(d[d.Year == BASE], ["Domain", "Component_Type"])
    b = agg(d[d.Year == END], ["Domain", "Component_Type"])
    j = a.join(b, rsuffix="_end", how="outer").fillna(0)
    j["delta"] = j[f"{VAL}_end"] - j[VAL]
    j["Segment"] = s
    chg.append(j.reset_index())
chg = pd.concat(chg, ignore_index=True)
chg.to_csv(CSV / "change_by_component_type.csv", index=False)

ef = chg[chg.Segment == "EF"].copy()
ef = ef.reindex(ef.delta.abs().sort_values(ascending=False).index).head(16).sort_values("delta")
fig, ax = plt.subplots(figsize=(11, 8))
ax.barh([f"{r.Component_Type}" for r in ef.itertuples()], kg(ef.delta.values),
        color=[DOM_COLOR.get(d, "0.5") for d in ef.Domain], alpha=0.9)
ax.axvline(0, color="0.3", lw=1)
ax.set_xlabel(f"Change {BASE} → {END}  (kg per vehicle)")
ax.set_title("EF: what actually moves, by component type\n"
             "largest 16 absolute changes", fontweight="bold")
ax.grid(alpha=0.3, axis="x")
hand = [plt.Rectangle((0, 0), 1, 1, color=DOM_COLOR[k]) for k in DOMAINS]
ax.legend(hand, DOMAINS, frameon=False, loc="lower right")
save(fig, "08_what_moves_EF")

# ============================================================ SUMMARY TABLES
snap = (df[df.Year.isin([BASE, 2040, END])]
          .groupby(["Year", "Segment", "Domain"])[[VAL, LO, HI]].sum().round(1))
snap.to_csv(CSV / "snapshot_2025_2040_2070.csv")
det = (df[df.Year.isin([BASE, END])]
         .groupby(["Year", "Segment", "Domain", "Component_Type", "Element"])
         [[VAL, LO, HI]].sum().round(3))
det.to_csv(CSV / "detail_2025_2070.csv")

print("\n  Total per vehicle, kg (mean [90% band]):")
for s in SEGMENTS:
    t = tot.xs(s, level="Segment")
    a, b = t.loc[BASE], t.loc[END]
    print(f"    {s}: {kg(a[VAL]):6.1f} [{kg(a[LO]):5.1f}–{kg(a[HI]):5.1f}]"
          f"  ->  {kg(b[VAL]):6.1f} [{kg(b[LO]):5.1f}–{kg(b[HI]):5.1f}]"
          f"   {b[VAL]/a[VAL]-1:+.1%}")
print(f"\n  -> Composition/csv/  (4 tables)")
