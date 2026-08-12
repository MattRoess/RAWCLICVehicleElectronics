#!/usr/bin/env python3
"""Figures for the OVERALL vehicle electronics, from 30_.

Every model plots its own domain. Nothing plotted the combined picture, so this
does -- wiring, PCB, sensors and motors together, per segment, 2020-2070.

    python3 tools/plot_composition.py

Reads  Data/30_BEV_electronics_composition.csv
Writes Composition/figures/*.png   and Composition/csv/*.csv

Figures
    1  total material per vehicle, all segments
    2  stacked composition by domain, one panel per segment
    3  the elements that carry the mass, over time
    4  2025 vs 2070 by component type -- what actually moves
    5  wiring by functional group -- the HV/LV split
    6  share of total by domain

Every figure is a MEAN per vehicle. Bands live in the source models; this file
is the central estimate.
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
print(f"Loaded {len(df):,} rows from {SRC.name}")


def save(fig, name):
    p = FIG / f"{name}.png"
    fig.savefig(p, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> Composition/figures/{name}.png")


def kg(g):
    return g / 1000.0


# ---------------------------------------------------------------- 1. TOTALS
tot = (df.groupby(["Year", "Segment"])["Mass_g_per_vehicle"].sum()
         .unstack("Segment").sort_index())
tot.to_csv(CSV / "total_material_per_vehicle.csv")

fig, ax = plt.subplots(figsize=(10, 6))
for s in SEGMENTS:
    ax.plot(tot.index, kg(tot[s]), lw=2.4, color=SEG_COLOR[s], label=SEG_LABEL[s])
    ax.annotate(f"{kg(tot[s].loc[END]):.1f} kg", (END, kg(tot[s].loc[END])),
                xytext=(6, 0), textcoords="offset points", va="center",
                color=SEG_COLOR[s], fontweight="bold")
ax.axvline(BASE, color="0.5", ls=":", lw=1)
ax.annotate("2025 baseline", (BASE, ax.get_ylim()[1]), xytext=(4, -14),
            textcoords="offset points", color="0.4", fontsize=9)
ax.set_xlabel("Year")
ax.set_ylabel("Material per vehicle  (kg)")
ax.set_title("Total electronics material per vehicle\n"
             "wiring + auxiliary motors + PCB + sensors", fontweight="bold")
ax.grid(alpha=0.3)
ax.legend(frameon=False)
ax.set_xlim(2020, END + 4)
save(fig, "01_total_material_per_vehicle")

# ------------------------------------------------------- 2. STACKED BY DOMAIN
fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), sharey=True)
for ax, s in zip(axes, SEGMENTS):
    d = (df[df.Segment == s].groupby(["Year", "Domain"])["Mass_g_per_vehicle"]
           .sum().unstack("Domain").reindex(columns=DOMAINS).sort_index())
    ax.stackplot(d.index, *[kg(d[c]) for c in DOMAINS], labels=DOMAINS,
                 colors=[DOM_COLOR[c] for c in DOMAINS], alpha=0.9)
    ax.set_title(SEG_LABEL[s], fontweight="bold")
    ax.set_xlabel("Year")
    ax.grid(alpha=0.25)
    ax.set_xlim(2020, END)
axes[0].set_ylabel("Material per vehicle  (kg)")
axes[-1].legend(loc="upper right", frameon=False)
fig.suptitle("Composition of vehicle electronics by domain", fontweight="bold", y=1.02)
save(fig, "02_composition_by_domain")

# ------------------------------------------------------------- 3. ELEMENTS
top = (df[df.Year == BASE].groupby("Element")["Mass_g_per_vehicle"].sum()
         .sort_values(ascending=False).head(6).index.tolist())
fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), sharey=True)
for ax, s in zip(axes, SEGMENTS):
    d = (df[(df.Segment == s) & (df.Element.isin(top))]
           .groupby(["Year", "Element"])["Mass_g_per_vehicle"].sum()
           .unstack("Element").sort_index())
    for el in top:
        if el in d:
            ax.plot(d.index, kg(d[el]), lw=2, label=el)
    ax.set_title(SEG_LABEL[s], fontweight="bold")
    ax.set_xlabel("Year"); ax.grid(alpha=0.25); ax.set_xlim(2020, END)
axes[0].set_ylabel("Mass per vehicle  (kg)")
axes[-1].legend(frameon=False, ncol=2)
fig.suptitle(f"The elements that carry the mass  (top {len(top)} at {BASE})",
             fontweight="bold", y=1.02)
save(fig, "03_elements_over_time")

# ------------------------------------------- 4. WHAT MOVES, BY COMPONENT TYPE
chg = []
for s in SEGMENTS:
    d = df[df.Segment == s]
    a = d[d.Year == BASE].groupby(["Domain", "Component_Type"])["Mass_g_per_vehicle"].sum()
    b = d[d.Year == END].groupby(["Domain", "Component_Type"])["Mass_g_per_vehicle"].sum()
    j = pd.concat([a.rename("y2025"), b.rename("y2070")], axis=1).fillna(0)
    j["delta_g"] = j.y2070 - j.y2025
    j["Segment"] = s
    chg.append(j.reset_index())
chg = pd.concat(chg, ignore_index=True)
chg.to_csv(CSV / "change_by_component_type.csv", index=False)

ef = chg[chg.Segment == "EF"].copy()
ef = ef.reindex(ef.delta_g.abs().sort_values(ascending=False).index).head(14)
ef = ef.sort_values("delta_g")
fig, ax = plt.subplots(figsize=(10, 7))
cols = [DOM_COLOR.get(d, "0.5") for d in ef.Domain]
ax.barh([f"{r.Component_Type}  ({r.Domain})" for r in ef.itertuples()],
        ef.delta_g / 1000.0, color=cols)
ax.axvline(0, color="0.3", lw=1)
ax.set_xlabel(f"Change {BASE} → {END}  (kg per vehicle)")
ax.set_title("EF segment: which components actually move\n"
             "largest 14 absolute changes", fontweight="bold")
ax.grid(alpha=0.3, axis="x")
save(fig, "04_what_moves_EF")

# ------------------------------------------------------- 5. WIRING HV vs LV
w = df[df.Domain == "Wiring"]
fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), sharey=True)
for ax, s in zip(axes, SEGMENTS):
    d = (w[w.Segment == s].groupby(["Year", "Component_Type"])["Mass_g_per_vehicle"]
           .sum().unstack("Component_Type").sort_index())
    for c in d.columns:
        ax.plot(d.index, kg(d[c]), lw=2, label=c)
    ax.set_title(SEG_LABEL[s], fontweight="bold")
    ax.set_xlabel("Year"); ax.grid(alpha=0.25); ax.set_xlim(2020, END)
axes[0].set_ylabel("Copper per vehicle  (kg)")
axes[-1].legend(frameon=False)
fig.suptitle("Wiring copper by functional group — the HV / LV split",
             fontweight="bold", y=1.02)
save(fig, "05_wiring_by_group")

# ------------------------------------------------------------ 6. DOMAIN SHARE
fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(SEGMENTS)); wdt = 0.38
for k, yr in enumerate((BASE, END)):
    bottom = np.zeros(len(SEGMENTS))
    for dom in DOMAINS:
        v = np.array([df[(df.Segment == s) & (df.Year == yr) & (df.Domain == dom)]
                      ["Mass_g_per_vehicle"].sum() for s in SEGMENTS])
        share = v / np.array([df[(df.Segment == s) & (df.Year == yr)]
                              ["Mass_g_per_vehicle"].sum() for s in SEGMENTS]) * 100
        ax.bar(x + (k - 0.5) * wdt, share, wdt * 0.92, bottom=bottom,
               color=DOM_COLOR[dom], label=dom if k == 0 else None,
               edgecolor="white", lw=0.6)
        bottom += share
for k, yr in enumerate((BASE, END)):
    for i in x:
        ax.annotate(str(yr), (i + (k - 0.5) * wdt, 101), ha="center",
                    fontsize=8, color="0.35")
ax.set_xticks(x); ax.set_xticklabels([SEG_LABEL[s] for s in SEGMENTS])
ax.set_ylabel("Share of total electronics material  (%)")
ax.set_title(f"Where the material sits, {BASE} vs {END}", fontweight="bold")
ax.legend(frameon=False, ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.16))
ax.set_ylim(0, 106)
save(fig, "06_domain_share")

# ---------------------------------------------------------------- SUMMARY
print("\n  Total material per vehicle (kg):")
print(f"    {'seg':6}{BASE:>9}{END:>9}{'change':>10}")
for s in SEGMENTS:
    a, b = kg(tot[s].loc[BASE]), kg(tot[s].loc[END])
    print(f"    {s:6}{a:9.1f}{b:9.1f}{b/a - 1:+9.1%}")
print(f"\n  -> Composition/csv/  (2 tables)")
