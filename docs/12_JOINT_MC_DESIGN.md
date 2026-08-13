# Joint Monte Carlo across the four domains

**Why this document exists.** The composition figure carried an uncertainty band
that was not Monte Carlo. This is the record of what was wrong, what was fixed,
and what is still open.

Started 2026-08-13. Steps 1-4 complete and validated (C1-C4). Section 8 lists
what remains open.

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

---

## 5. Motor mass — two defects, found and fixed

Building step 3 surfaced a motor composition that was **1.57–1.79× the motor
model's own mass**. The elements decompose the motors, so that is impossible.
Diagnosis, in order:

**The gap was not uniform** (1.075–1.98 by motor type) and tracked the housing
material — metal-housing motors overshot most, plastic least. That ruled out a
unit error.

**Upstream was clean.** `ElectricMotorMC`'s six materials sum to 27.591 kg for
CD, exactly its own motor mass. The defect was downstream.

**Every stream was over by exactly 2.00×**, which is the signature of a double
count, not a modelling disagreement.

### Defect 1 — `TotalMass` was summed as if it were an element

Each stream reports its elements *and* that same stream's mass again:

| row | kg |
|---|---|
| `Cu` | 1.685386 |
| trace elements (ppm) | ~0.0003 |
| **`TotalMass`** | **1.685836** ← the same mass, again |

`Cu` + traces ≈ `TotalMass`, so summing every row counted each stream twice.

### Defect 2 — Aluminium and Plastic were missing entirely

`ElectricMotorElementMC` runs **four** material streams. A motor is made of
**six**. Aluminium and Plastic have no elemental breakdown — aluminium *is* an
element, plastic is not resolved further — and were dropped: **17.7% of motor
mass**.

The two defects partly cancelled, which is why the ratio looked like a plausible
1.6× rather than an obvious 2×.

### After the fix

| segment | elements + Al + Plastic | ElectricMotorMC mass | error |
|---|---|---|---|
| AB | 13.041 kg | 13.044 kg | **0.02%** |
| CD | 27.728 kg | 27.591 kg | **0.50%** |
| EF | 61.755 kg | 61.182 kg | **0.94%** |

The residual is histogram-reconstruction noise: the element model resamples each
material mass from an exported 50-bin histogram rather than the original draws,
which cannot reproduce a mean exactly.

Fixed in **both** `tools/build_composition.py` (so `Data/30_` is corrected) and
`tools/mc_composition.py`. The joint MC now **asserts** the reconciliation
against `MOTOR_RECON_TOL = 0.03` and raises if a stream is ever double-counted
or a material dropped again — the check that would have caught both defects.

### What it moved

Total mass per vehicle fell by about 23%:

| 2040 | Wiring | Motors | PCB | Sensors | **Total** | was |
|---|---|---|---|---|---|---|
| AB | 23.76 | 15.09 | 0.48 | 0.118 | **39.46 kg** | 51.44 |
| CD | 36.62 | 31.12 | 0.61 | 0.173 | **68.52 kg** | 88.55 |
| EF | 57.69 | 67.21 | 0.70 | 0.215 | **125.82 kg** | 162.86 |

`Data/30_BEV_electronics_composition.csv` carried the inflated figure and has
been rebuilt.

---

## 6. Motor elements — two more defects (item A2)

Fixing §5 left the composition still 0.50% (CD) and 0.94% (EF) off. Chasing that
residual found two further defects, both real maths errors.

### A2a — the element model discarded its own draws and resampled a histogram

`sample_from_histogram()` read an **exported 50-bin histogram** of each material
mass and drew from it, even though `ElectricMotorMC` writes its actual 200,000
per-draw material masses to `materials_samples_csv/*.npy`.

This is the same *class* of error as `_lognormal_from_band` in §1 — real
information exists and is thrown away — though far milder, since it used the
true shape rather than an invented one.

**The worse half was the pairing.** Each stream was resampled from its own
histogram *independently*, so "draw i" of copper and "draw i" of steel came from
two unrelated motors. A heavy motor is heavy in every material at once;
independent resampling destroys that, and every grand total formed by summing
streams inherited the error.

**Fix:** `load_material_draws()` reads the `.npy` column directly. It takes the
**first n rows, not a random subset** — the draws are i.i.d. so the first n are a
valid sample, and using the *same* row indices for every stream is what keeps a
motor's copper and its steel belonging to the same motor.

Alone, this fixed AB (0.02% → 0.004%) but barely moved CD and EF. That pointed
at something else.

### A2b — NdFeB fractions did not sum to 1

| stream | sum(elements) / TotalMass, before |
|---|---|
| Cast Fe Steel | 1.0000 |
| Electrical Steel | 1.0000 |
| Copper | 0.9999 |
| **NdFeB** | **0.982 – 1.113, mean 1.041** |

`sample_ndfeb_composition()` drew **every** element, Fe included, independently
between its own min and max, with nothing forcing the eleven fractions to sum to
1. So a kilogram of magnet became 1.041 kg of elements on average — worst where
NdFeB content is highest.

The other three streams never had this problem: Cast Fe Steel and Electrical
Steel already compute `Fe = 1 - sum(others)`.

**Fix:** Fe is now the **balance element** in NdFeB too, matching the pattern
already in the file. This is the physically correct constraint as well as the
arithmetically correct one — NdFeB is Nd₂Fe₁₄B with substitutions and iron makes
up the remainder by definition. The drawn balance is checked against the range
the sheet reports for Fe, warning (not silently clamping) if they disagree;
`NDFEB_FE_TOL = 0.02`.

### A3 — motor draws are now consumed, not resampled

The joint MC previously bootstrapped motor mass from the saved pool *with
replacement*. Correct in distribution, but still resampling: it adds noise that
is not in the model and lets one motor stand in for several vehicles. It now
walks the pool in step with the run, so each of the 200,000 saved draws is used
**exactly once**.

### Result

| segment | Motors 2025 | ElectricMotorMC mass | error |
|---|---|---|---|
| AB | 13.0470 kg | 13.0442 kg | **0.021%** |
| CD | 27.5973 kg | 27.5912 kg | **0.022%** |
| EF | 61.1874 kg | 61.1822 kg | **0.008%** |

All four streams now sum to 1.0000. `MOTOR_RECON_TOL` was tightened from 0.03 to
**0.005** to match — at 0.03 the guard would not have noticed NdFeB, which is 9%
of motor mass, going wrong by a third.

---

## 7. Step 4 — the figures (item A1)

`tools/plot_composition.py` now reads `Composition/csv/joint_mc_stats.csv`.
`_lognormal_from_band()`, `_model_totals()`, `mc_total()` and the 40,000-draw
resampler are **deleted**.

Where every band in the figures comes from:

| | source | status |
|---|---|---|
| domain and total bands (figs 1, 2, 3) | `joint_mc_stats.csv` | real Monte Carlo, summed per draw |
| component bands (figs 5, 7, 8) | `Data/30_` | each model's own band, exact |
| anything summed over components (`agg()`) | — | **comonotonic bound**, labelled as such |

Two things improved beyond deleting the invention:

- **Domain bands are now real too.** The old code took the *relative* width of a
  PCB **area** band and a sensor **count** band and pasted it onto the mass mean.
  They now come from the joint run's own per-draw domain masses.
- **Figure 3 averages across segments instead of summing.** Adding three
  segments' percentiles and dividing by their summed mean answers a different
  question — the width of a fleet holding one car from each segment — and reads
  deceptively narrow.

Figure 1 draws the comonotonic bound behind the joint band, so the gap between
"what it could be if everything moved together" and "what it is" is visible
rather than asserted.

### Validation C1–C4

`mc_composition.py` now asserts four arithmetic facts over all 153
(segment, year) cells. These are not calibration checks; if one fails the
summation or the accumulator is wrong.

| | check | result |
|---|---|---|
| C1 | joint band within the comonotonic bound | 0 bad |
| C2 | mean inside its own band | 0 bad |
| C3 | P2.5 ≤ P97.5 | 0 bad |
| C4 | sum(domain means) == total mean | **8.79e-16** |

C4 is the one that proves the summation is genuinely per-draw: means add
exactly, to machine precision, in a way percentiles never can.

### The answer

Total electronics material per vehicle, mean [90% joint-MC band], kg:

| segment | 2025 | 2070 | change |
|---|---|---|---|
| AB | 47.6 [32.3–73.9] | 36.4 [29.7–44.1] | −23.4% |
| CD | 84.5 [60.1–127.7] | 69.8 [56.3–85.3] | −17.4% |
| EF | 137.9 [108.3–173.6] | 130.9 [104.0–163.3] | −5.1% |

**Run order matters:** `mc_composition.py` must run before
`plot_composition.py`, which now exits with a clear message if the joint stats
file is missing rather than inventing a band.

---

## 8. `_shift_shares` deduplicated (item A5)

`BevWiring.py` carried its own copy of `shift_shares` while the sensor and PCB
models called `drivers.shift_shares`. Same maths, two implementations, free to
drift — the duplication the project's own rule forbids and V12 exists to catch.
The copy is deleted; `BevWiring._shift_shares` is now an alias.

**Measured before doing it**, because "mechanical" is a claim that needs testing:

| | |
|---|---|
| shifted-share elements differing | 122,449 of 1,020,000 |
| largest difference | 2.22e-16 (one ULP) |
| **rows of `bev_wiring_stats.csv` that changed** | **0 of 20,808** |

The internal floats differ in the last bit; **no reported number moves at all**,
on Mean, P2.5, P97.5 or Median. The shares are consumed by a *discrete*
comparison — `u > cumsum(shares)` selects an integer state — and a 2e-16 nudge
essentially never flips which side of a boundary a uniform lands on. 9/9 wiring
validations still pass.

Worth recording as a general point: an intermediate difference of one ULP is not
evidence of an output difference, and an output difference is what matters.

---

## 9. Still open

**The shared vehicle-size factor — undecided.** Only the wiring model carries a
per-vehicle size factor (`CV_VEHICLE = 0.10`). A big car is big in every domain,
so this is genuinely common-mode, and adding it would widen the joint band
correctly. But it changes the marginal distribution of three models that have no
size factor at all, so it is a modelling decision, not a defect fix.
Deliberately left out.

**Carried over, not addressed here:** `LIDAR_H4_FLOOR = 0.80` (EF lidar still
~6× above observation); Driver C multipliers (1.0/1.4/2.0) unsourced; the `01_`
relabel — CLOSED 2026-08-13, the chain was already current (verified by
regenerating: `11_`/`12_` byte-identical, `SensorElementsMC` zero difference).
