#!/usr/bin/env python3
"""Figures for the OVERALL vehicle electronics -- with the Monte Carlo ranges.

**Copyright notice:** Copyright © 2025 & 2026 Empa, Matthias Roesslein

    python3 tools/mc_composition.py      # must run FIRST -- supplies the band
    python3 tools/plot_composition.py

Reads  Composition/csv/joint_mc_stats.csv   the bands, from the joint Monte Carlo
       Data/30_BEV_electronics_composition.csv   the means, split by element
Writes Composition/figures/*.png  and  Composition/csv/*.csv

THE BAND IS THE POINT. This is a Monte Carlo model; a figure showing only means
misrepresents it. Every series here carries its 2.5-97.5 percentile range.

WHERE EVERY BAND IN THIS FILE COMES FROM

    domain and total bands      joint_mc_stats.csv -- real Monte Carlo. One
    (figures 1, 2, 3)           simulated car is pushed through all four models
                                with the SAME shared drivers, the four masses are
                                summed PER DRAW, and the percentiles are taken of
                                that sum. Correlation between domains is in the
                                answer by construction.

    component bands             Data/30_ -- each model's own band for that
    (figures 5, 7, 8)           series. Exact.

    anything summed across      a COMONOTONIC BOUND, labelled as such wherever
    components (agg())          it is drawn: the widest the band could be, not
                                the band. Percentiles do not add.

WHAT THIS REPLACED, 2026-08-13. The cross-domain total used to be built by
_lognormal_from_band(): it took each domain's mean/P2.5/P97.5, INVENTED a
lognormal matching those three numbers, drew from the invention, and summed the
four domains as independent. The models' own draws never entered. It was wrong
twice over -- the real distributions are bimodal through the 2030-2050
transition, which a lognormal cannot represent, and three of the four domains
read the same driver workbook, so independent summing understated the total.
That function is deleted. See docs/12_JOINT_MC_DESIGN.md.

ONE HONEST CAVEAT THAT REMAINS. The band means different things by domain,
carried per row in the source file as Band_meaning:

    Wiring, PCB   full model band
    Motors        motor count and mass only -- composition frozen at 2025
    Sensors       sensor count only -- composition frozen at 2025

So the motor and sensor bands are NARROWER than the true uncertainty. They omit
composition, which is a deliberate scope decision (02_MODEL_STATUS.md section 3),
not an oversight.
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
# THE BANDS COME FROM THE JOINT MONTE CARLO
#
# tools/mc_composition.py pushes ONE simulated car through all four models with
# the same shared drivers, sums the four masses PER DRAW, and takes percentiles
# of that sum. Every domain band and the total band below are read straight from
# its output. Nothing here reconstructs, refits or re-samples a distribution.
#
# The predecessor of this section invented a lognormal from three summary
# numbers and summed the domains as independent. It is gone; see the module
# docstring and docs/12_JOINT_MC_DESIGN.md.
# ==========================================================================

JOINT = CSV / "joint_mc_stats.csv"
if not JOINT.exists():
    raise SystemExit(
        f"{JOINT} not found -- run `python3 tools/mc_composition.py` first.\n"
        f"That script IS the band; this one only draws it.")

_j = pd.read_csv(JOINT)
print(f"Loaded joint MC: {len(_j):,} rows, "
      f"{_j.N_Iter.iloc[0]:,} draws per segment, series {sorted(_j.Series.unique())}")

# (Series, Segment, Year) -> (mean_g, p2.5_g, p97.5_g)
MT = {(r.Series, r.Segment, int(r.Year)): (r.Mean_g, r.P2_5_g, r.P97_5_g)
      for r in _j.itertuples()}


def domain_band(dom, seg, yr):
    """(mean, lo, hi) in grams for one domain -- from the joint Monte Carlo.

    `dom` may also be "Total", which is the cross-domain sum taken draw by draw
    rather than by adding percentiles.
    """
    return MT.get((dom, seg, yr))


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

# ==================================================== 1. TOTAL, joint MC band
# The dark band is the joint Monte Carlo: the four domains summed DRAW BY DRAW.
# The pale band behind it is the comonotonic bound -- the four domain bands
# added as percentages, which assumes every domain sits at its low, or its high,
# at the same moment. It is drawn only to show how much narrower the real answer
# is; it is not a result.
years = sorted(y for y in df.Year.unique() if ("Total", "AB", int(y)) in MT)
mc = pd.DataFrame([
    {"Year": yr, "Segment": seg,
     "Mean": MT[("Total", seg, yr)][0],
     "P2_5": MT[("Total", seg, yr)][1],
     "P97_5": MT[("Total", seg, yr)][2]}
    for seg in SEGMENTS for yr in years])
mc.to_csv(CSV / "total_mc_band.csv", index=False)

bound = pd.DataFrame([
    {"Year": yr, "Segment": seg,
     "P2_5": sum(domain_band(d, seg, yr)[1] for d in DOMAINS),
     "P97_5": sum(domain_band(d, seg, yr)[2] for d in DOMAINS)}
    for seg in SEGMENTS for yr in years])

fig, ax = plt.subplots(figsize=(11, 6.5))
for s_ in SEGMENTS:
    t = mc[mc.Segment == s_].set_index("Year").sort_index()
    b = bound[bound.Segment == s_].set_index("Year").sort_index()
    ax.fill_between(b.index, kg(b.P2_5), kg(b.P97_5), color=SEG_COLOR[s_],
                    alpha=0.07, lw=0)
    ax.fill_between(t.index, kg(t.P2_5), kg(t.P97_5), color=SEG_COLOR[s_],
                    alpha=0.24, lw=0)
    ax.plot(t.index, kg(t.Mean), lw=2.6, color=SEG_COLOR[s_], label=SEG_LABEL[s_])
    ax.annotate(f"{kg(t.Mean.loc[END]):.0f} kg", (END, kg(t.Mean.loc[END])),
                xytext=(7, 0), textcoords="offset points", va="center",
                color=SEG_COLOR[s_], fontweight="bold")
ax.axvline(BASE, color="0.55", ls=":", lw=1)
ax.set_xlabel("Year"); ax.set_ylabel("Material per vehicle  (kg)")
ax.set_title(
    "Total electronics material per vehicle\n"
    f"dark band = joint Monte Carlo, {int(_j.N_Iter.iloc[0]):,} draws — one car "
    "through all four domains, summed per draw   ·   "
    "pale band = comonotonic bound, for comparison", fontweight="bold")
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
yrs = years


def _rel_width(series):
    """Mean 90% band width as % of the mean, averaged over the three segments.

    Averaged, NOT summed. Adding three segments' percentiles and dividing by
    their summed mean answers a different question -- the width of a fleet made
    of one car from each segment -- and reads deceptively narrow.
    """
    out = []
    for y in yrs:
        bs = [domain_band(series, sg, y) for sg in SEGMENTS]
        bs = [b for b in bs if b and b[0] > 0]
        out.append(np.mean([(b[2] - b[1]) / b[0] * 100 for b in bs]) if bs else np.nan)
    return out


for dom in DOMAINS:
    ax.plot(yrs, _rel_width(dom), lw=2.4, color=DOM_COLOR[dom], label=dom)
ax.plot(yrs, _rel_width("Total"), lw=2.8, color="0.2", ls="--",
        label="TOTAL (joint Monte Carlo)")
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

print("\n  Total per vehicle, kg (mean [90% joint-MC band]):")
for s in SEGMENTS:
    a = domain_band("Total", s, BASE)
    b = domain_band("Total", s, END)
    print(f"    {s}: {kg(a[0]):6.1f} [{kg(a[1]):5.1f}–{kg(a[2]):5.1f}]"
          f"  ->  {kg(b[0]):6.1f} [{kg(b[1]):5.1f}–{kg(b[2]):5.1f}]"
          f"   {b[0]/a[0]-1:+.1%}")
print(f"\n  -> Composition/csv/  (5 tables)")
