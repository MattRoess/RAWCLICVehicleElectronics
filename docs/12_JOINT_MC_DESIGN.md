# Joint Monte Carlo across the four domains

**Why this document exists.** The composition figure carried an uncertainty band
that was not Monte Carlo. This is the record of what was wrong, what was fixed,
and what is still open.

Started 2026-08-13. Steps 1, 2 and 3 complete; step 4 outstanding.

---

## 1. The defect

`tools/plot_composition.py` built the total band like this:

```python
sigma = np.log(hi / lo) / (2 * 1.959963985)
mu    = np.log(mean) - 0.5 * sigma ** 2
return _rng.lognormal(mu, sigma, n)          # 40,000 draws from a MADE-UP lognormal
```

It took each domain's **three summary numbers** — mean, P2.5, P97.5 — invented a
lognormal that matched them, drew from that invention, and summed the four
domains independently. The models' own draws never entered. The comment block
above it called itself "TRUE MONTE CARLO AGGREGATION"; that label was wrong.

Three things were wrong with it:

1. **The shape was invented.** A lognormal is unimodal. The wiring
   distributions are bimodal through 2030–2050 — one hump for 400 V/domain cars
   still in the fleet, one for 800 V/zonal. That is exactly the period the
   figure is about.

2. **The domains were summed as independent.** The justification given was
   *"separate models with independent draws, so independent sampling is the
   right assumption between them."* That confuses separate **software** with
   independent **physics**. Wiring, Sensors and PCB all read the same driver
   workbook `18_BEV_technology_penetration.xlsx`. A car drawn zonal/800 V/H4 is
   all of those in every domain at once. Independent summing makes the total
   band **too narrow**.

3. **Two domains had no mass band at all.** PCB and Sensors produce an *area*
   and a *count*; the script took their relative band width and pasted it onto
   the composition mean.

It also had never run: the script was saved 12 Aug 15:42, the CSVs in
`Composition/csv/` were from 15:34, and `total_mc_band.csv` did not exist.

---

## 2. Step 1 — the tier had to become a per-vehicle draw

Before this could be fixed, a prior defect had to be: **Sensors and PCB never
drew a hardware tier at all.** They multiplied every vehicle by the
share-weighted average presence:

```python
pres = np.array([PRESENCE_TIER[c][segment][yi] for c in adas_comp])[:, None]
adas_scaled = base[adas_idx, :] * pres        # same scalar for EVERY vehicle
```

Every car got 0.62 of a lidar instead of 62% of cars getting one and the rest
none. This is the error `tools/drivers.py` already warned about in writing:

> Share-weighting instead collapses a bimodal mixture into its mean and destroys
> the band; that error is why generation 4 of the wiring model was replaced.

Two consequences: there was **no tier state to correlate on**, so the joint MC
was not implementable; and the sensor and PCB bands were already too narrow,
independently of the composition figure.

### What was implemented

Five shared functions in `tools/drivers.py`, so the tier is sampled by *one*
implementation rather than three variants:

| Function | Purpose |
|---|---|
| `load_presence_matrix` | presence(component, tier, year) **unmixed** |
| `load_lidar_bands` | Driver B's three curves + the sampled China→Europe lag |
| `draw_tier_state` | one uniform per vehicle + its own timing offset → discrete tier |
| `draw_lidar_share` | that vehicle's own lidar-equipped share curve |
| `pick_at_tier` | reads a per-tier table at each vehicle's drawn tier |

`SensorNumbersMC.py` now draws a discrete tier in **both** the accumulator path
and the full-draw path. `PCBAreaMC.py` does the same for its tier-governed
component, at both draw sites.

**A second half of the same defect was found while implementing.** Presence was
still being applied as a *multiplier* after the tier was drawn. It is defined as
a fraction of **vehicles** — `04_SENSOR_MODEL_DESIGN.md` §3: *"what fraction of
vehicles in this segment carry this component"* — so it is now a per-vehicle
Bernoulli. Presence 0.3 means 30% of cars carry the full 8–12 ultrasonic set and
70% carry none, not every car carrying 2.4–3.6 of them.

### Two design points worth keeping

**In a lidar-governed cell the presence matrix holds the FLOOR, not the share.**
H3 gets 0.0 and H4 gets `LIDAR_H4_FLOOR`, and the caller takes
`max(that vehicle's Driver-B share, floor)`. Storing the Mode share instead bakes
one band into the table, and the floor is then silently lost the moment a caller
substitutes its own sampled band. That bug was written first and caught by the
mean-preservation check below.

**`pick_at_tier` exists because the naive `mat[st_tier]` is silently wrong.** It
indexes the tier axis and keeps the whole year axis behind it, returning
`(n_iter, n_years, n_years)` — a wrong answer with a plausible shape.

### Verification

The discrete draw reproduces the old share-weighted presence in the mean to
within **0.042 absolute** across every component, segment and year. The residual
is two intended effects: the timing-offset smoothing, and lidar's bands being
sampled in thirds (mean `(Min+Mode+Max)/3`) rather than pinned to the Mode.

All validations pass: **V11, V12, V13, V15, P1, P3**. V14 improved from 2
series-metrics outside the 3% tolerance to 1.

### What it did to the numbers

| Series | Mean | Band |
|---|---|---|
| ADAS domain, AB 2025 | +7.1% | **5.2× wider** |
| ADAS domain, AB 2040 | −0.8% | **4.1× wider** |
| ADAS domain, EF 2070 | −0.1% | **1.3× wider** |
| Lidar elements | unchanged | **0.1% → 130–700%** |
| Sensor **total** | ±0.3% | 1.00–1.11× |
| PCB total | ±0.0% | 1.00× |

The lidar row is the clearest case: its band was **0.0–0.2%**, a spike —
essentially zero uncertainty on a quantity nobody can predict. It is now a
genuine two-point distribution.

Two honest notes. The sensor **total** barely moved, because ~192 non-ADAS rows
dominate its variance. PCB is unchanged at 1.00×, because its tier-governed
component is one small board in a total dominated by board dimensions. Both
fixes are still required — without a per-vehicle tier there is nothing for step 3
to correlate on — but neither moved the headline number.

The +7.1% on AB 2025 ADAS is the timing-offset smoothing at a steep part of the
tier curve. V13, which checks the 2025 anchor against `01_`'s static labels,
still passes.

---

## 3. Step 2 — the shared vehicle state

`tools/vehicle_state.py` holds `VehicleState`: the per-draw random state of one
simulated car, in the drivers that **more than one model reads**.

| shared, lives in VehicleState | read by |
|---|---|
| architecture state (`u_arch`, `d_arch`) | Wiring, PCB |
| ADAS hardware tier (`u_tier`, `d_tier`) | Wiring, Sensors, PCB |
| 800 V voltage state (`u_volt`) | Wiring, Sensors |
| post-2040 scenario (`u_scen`) | Wiring, Motors |
| lidar / Driver B (`u_lidar_band`, `d_lidar_lag`) | Wiring, Sensors |

Anything read by one model alone stays inside that model: wire gauge and SDV
depth, the per-row sensor count within min–max, board dimensions and the `q`
calibration, motor mass and the housing split.

**Every model takes `state=None` and, given None, draws exactly what it always
drew.** The RNG consumption order is unchanged, so all standalone outputs stay
reproducible from their own seed.

`u_arch` and `u_tier` are drawn **independently**. A manufacturer early on zonal
architecture is not necessarily early on ADAS hardware — different supply chains,
different cost curves. Sharing one uniform would impose a rank correlation of
exactly 1, a stronger claim than any source supports. If evidence for a
correlation appears, `vehicle_state.py` is the one place to put it.

`pick_from_uniform` replaces `rng.choice` for the scenario, because `rng.choice`
consumes the generator: two models asked for "the same vehicle's scenario" would
otherwise disagree unless they happened to consume their generators in lockstep.

### Verification

| check | result |
|---|---|
| Wiring output vs before, 20,808 rows | **bit-identical**, 9/9 validations |
| Sensor output vs before, 11,781 rows | **bit-identical** |
| PCB output vs before, all three segments | **bit-identical** |
| Motor output vs before, 306 rows | **bit-identical** |
| Wiring's `_shift_shares` vs `drivers.shift_shares` on one state | **0 of 204,000 cells disagree** |
| Same state + same seed | reproducible |
| Different fleet | different draws |

The per-vehicle link is real, not nominal. 2040 CD, ADAS wire metres by the tier
each car drew: H1 155 m, H2 249 m, H3 267 m, H4 277 m; correlation 0.41.

---

## 4. Step 3 — the joint run

`tools/mc_composition.py`. One vehicle at a time through every domain:

```python
st    = draw_vehicle_state(rng, m)          # the shared drivers, drawn ONCE
total = wiring(st) + sensors(st) + pcb(st) + motors(st)
acc.add(total)                              # summed PER DRAW, then binned
```

200,000 draws × 3 segments × 4 domains runs in **2 minutes**, memory flat.
Outputs `Composition/csv/joint_mc_stats.csv` and `joint_mc_histograms.csv`
(50 bins per series-year, empty bins included).

**Library/script split.** `SensorNumbersMC.py` and `PCBAreaMC.py` had no main
guard, so importing either triggered a full 200,000-draw run. Both now carry
`_RUN = __name__ == "__main__"` with the run/figure/export sections wrapped in
`if _RUN:` — one region in the sensor model, three in PCB. Import cost fell from
a full run to **~1 s**, and direct execution is **bit-identical** (sensors 11,781
rows, PCB all segments, all validations passing).

### The four mass mappings

| domain | mapping | why it is exact |
|---|---|---|
| Wiring | Cu kg × 1000 | the model reports mass directly |
| Sensors | count(type) × mg(type) | `07_` gives mg per element per type; the product is exact |
| PCB | area × g/cm² | PCBElementMC derives mass *from* area; the ratio moves 0.08% across all years |
| Motors | 2025 element mass × growth | the 2025 per-draw masses are the motor model's **own** 200,000 draws from `samples_csv/*.npy`, not a refit |

Reading motor draws from disk is legitimate because the 2025 motor mass shares
no driver with any other domain. Only the growth trajectory does, through
`u_scen`, and that **is** drawn here and injected.

### The result — and it is not the one that was expected

| | 2040 CD, share of total variance |
|---|---|
| Wiring | **58.5%** |
| Motors | **42.8%** |
| Sensors | 0.0% |
| PCB | 0.0% |

Cross-domain correlation of the same simulated cars, 2040 CD:

| pair | correlation | shares |
|---|---|---|
| Wiring ↔ PCB | **+0.157** | architecture |
| Wiring ↔ Sensors | −0.070 | tier, 800 V, lidar |
| Wiring ↔ Motors | −0.014 | scenario only |
| all other pairs | ≈ 0 | nothing |

So the joint band lands **essentially on the independent band** and about 25%
below the comonotonic bound:

| | mean | independent | **JOINT** | comonotonic |
|---|---|---|---|---|
| AB 2040 | 51.4 kg | 24.7 | **25.6** | 34.1 |
| CD 2040 | 88.6 kg | 41.5 | **42.1** | 58.7 |
| EF 2040 | 162.9 kg | 70.6 | **70.7** | 97.8 |

**Read this honestly.** The old code's independence assumption was wrong *in
principle* and very nearly right *in magnitude*, for this model structure. The
reason is that the two domains carrying ~all the variance — Wiring and Motors —
share only the scenario driver, while the two domains that share the most
drivers (Sensors, PCB) contribute essentially none of the variance. The real
defects in the old band were therefore the **invented lognormal shape** and the
fact that **it had never been run**, not the independence.

The joint machinery is still the right answer: it now *measures* the correlation
instead of assuming a value for it, and it will track automatically if the
balance of variance shifts — which it will, if the sensor or PCB models ever
gain the composition uncertainty they currently freeze at 2025.

### Found while building it — motor mass does not reconcile

The motor element decomposition does not match the motor model's own mass:

| segment | element sum | ElectricMotorMC mass | ratio |
|---|---|---|---|
| AB | 23.393 kg | 13.044 kg | **1.79** |
| CD | 45.573 kg | 27.591 kg | **1.65** |
| EF | 95.791 kg | 61.182 kg | **1.57** |

The elements decompose the motors, so these should be equal. The four `Stream`
values are complementary materials (Cast Fe Steel, Copper, Electrical Steel,
NdFeB), not duplicate runs, so summing them is correct — this is a genuine
disagreement between `ElectricMotorMC` and `ElectricMotorElementMC`.

**Not introduced here.** `tools/build_composition.py` behaves the same way, so
`Data/30_BEV_electronics_composition.csv` already carries it. The element sum is
kept in the joint MC so the band stays comparable with the published
deliverable. Whichever way it is resolved, the Motors *level* moves and the
total moves with it; the band shape and correlation structure do not.

---

## 5. Still open

**Step 4 — the figures.** Rebuild the band from `joint_mc_stats.csv` and delete
`_lognormal_from_band` entirely.

**The shared vehicle-size factor — undecided.** Only the wiring model carries a
per-vehicle size factor (`CV_VEHICLE = 0.10`). A big car is big in every domain,
so this is genuinely common-mode, and adding it would widen the joint band
correctly. But it changes the marginal distribution of three models that have no
size factor at all, so it is a modelling decision, not a defect fix.
Deliberately left out.

**Carried over, not addressed here:** `LIDAR_H4_FLOOR = 0.80` (EF lidar still
~6× above observation); Driver C multipliers (1.0/1.4/2.0) unsourced; the `01_`
relabel not propagated to `SensorElementsMC.py` and the PCB models.
