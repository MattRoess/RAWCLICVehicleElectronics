# BEV wiring model — living status

**Current model: `Wiring/BevWiring.py`** (generation 5; earlier ones in
`Archive/` with a README saying why each was replaced).
Last updated 2026-08-04. This is the single handover document.

    python3 Wiring/BevWiring.py          # ~4 min at 200,000 iterations

---

## 1. Files

| File | Role |
|---|---|
| `Wiring/BevWiring.py` | **the model** |
| `Wiring/outputs/data/bev_wiring_stats.csv` | 20,808 rows — mean, P2.5, median, mode, P97.5, every year |
| `Wiring/outputs/data/bev_wiring_histograms.csv` | 142,800 rows — 408 series × 7 snapshot years × **50 bins** |
| `Wiring/outputs/plots/` | 38 figures — 8 trajectory, 30 histogram |
| `Data/17_BEV_wiring_baseline_2025.xlsx` | 2025 baseline, gauges, SDV factors, SDV depth |
| `Data/18_BEV_technology_penetration.xlsx` | architecture / voltage / autonomy shares, sensors, scenario conversion |
| `Wiring/Archive/` | v3, v4, their outputs, and why they were replaced |
| `Data/15_`, `Data/16_` | superseded, **not read** |

---

## 2. How it works

One anchor year (2025), three independent drivers, no splines and no era seams.

    length(cat,t) = baseline_2025 x architecture_state_factor x variability
    ADAS length   = sensor_count(autonomy_level) x metres_per_sensor
    cu_per_m(t)   = gauge x 8.96 x (1 - 0.425 if 800V)          [HV only]
    Cu (kg)       = sum(length x cu_per_m) / 1000

| Driver | States | Affects |
|---|---|---|
| Architecture | Conventional / Transitional / SDV_Zonal | LV + signal LENGTH |
| Voltage | 400V / 800V | HV Cu-per-METRE |
| Autonomy | L0 … L5 | ADAS + sensor LENGTH, via sensor counts |

Independent, so architecture shortens wiring while sensors lengthen it. That is
why CD flattens near 1,750 m and EF near 2,850 m after 2040 rather than falling.

**Copper is never read as a given.** Always length × gauge × density. Both
sources' direct copper figures are unreliable — the source report's own
per-category copper column sums 13–28% short of its own totals.

**States are DISCRETE, not share-weighted.** A vehicle is one design or
another. Each iteration draws one uniform per driver, held across years, plus
its own timing offset. The distribution is therefore genuinely bimodal during a
transition — visible as a second hump in the 2020/2025 histograms, which is the
Conventional fleet (CD 2025: 17% of draws at 87 kg against 83% at 50 kg, ratio
1.75, matching `CONVENTIONAL_UPLIFT` of 1.67). It is not an artefact.

---

## 3. Two execution paths

| | `run_accumulated()` | `run_monte_carlo()` |
|---|---|---|
| Keeps | statistics only | every draw |
| Memory | **independent of n_iter** (~2.2 GB, set by `CHUNK_ITER`) | (n_iter × 28 × 51) × 12 arrays |
| Used for | the two CSVs | the plots |
| Limit | none in practice | ~20,000 before memory trouble |

`N_ITER = 200000` drives the statistics. `N_ITER_PLOTS = 5000` caps the
full-draw run separately. Measured: 0.16 s per 1000 iterations, peak RSS 2.2 GB
at 200,000. Keeping every draw at 200,000 would have needed ~31 GB on a 17 GB
machine — that is why the accumulator exists.

**Accumulator accuracy**, validated by pushing identical draws through both
paths, expressed against the segment total:

| mean | median | P2.5 / P97.5 |
|---|---|---|
| exact (running sum) | 0.089% | 0.44% |

Monte Carlo sampling noise on P2.5 is ~11.6% at 3,000 draws and ~1.4% at
200,000, so the binning error is far below the noise it removes.

---

## 4. Histograms — 50 bins, fixed

**50 bins is the project convention and is not negotiable.** Enforced by
`N_HIST_BINS = 50`.

- Every series-year has **exactly 50 rows**, empty bins included, so nothing
  downstream needs to reindex.
- The **Mode** in the stats table is the centre of the fullest of those same 50
  bins, so the two files can never disagree.
- The histogram **figures** are drawn from the same 50 bins as the CSV.
- `N_ACC_BINS = 1000` is INTERNAL accumulator resolution, not a histogram. It
  exists so percentiles are not quantised to 1/50th of the range, and is summed
  down to exactly 50 for export. An assertion requires it to be a multiple of
  `N_HIST_BINS`. At 50 internal the percentile error would be 1.29% instead of
  0.30%.

---

## 5. Things that break silently

1. **Renormalisation at `BASE_YEAR`.** The 2025 baseline is *observed*, so it
   already contains that year's SDV and 800V penetration. Applying either from
   zero subtracts it twice; CD copper then comes out ~10% low with no error.
2. **`TRANSITION_TIMING_SPREAD_Y = 5.0`.** At 0 every iteration switches in the
   same year, the whole fleet turns over at once, and the curves show a
   visibly too-steep ramp with a stepped median. Rejected twice by the user.
3. **Plots show the MEAN, not the median.** The mixture is bimodal so the
   median jumps when the mixing weight crosses 50%. The mean is the anchored
   quantity and the one to multiply by units sold.
4. **Share curves must be PCHIP.** `np.interp` kinks at every 5-year anchor in
   `18_`, visible as corners in the bands.
5. **ADAS scaling uses the ENSEMBLE mean at the base year.** Per-iteration
   scaling pins every iteration to the same 2025 value and deletes sensor-count
   uncertainty exactly at the anchor.
6. **Histogram bars must be full bin width.** At 0.95 they leave white gaps
   that read as missing bins. There are no interior empty bins — checked.

---

## 6. LABEL COLLISION — read before touching `18_`

`BEV_Automation_Adoption_Report_2020_2050.md` names its three **scenarios**
"AB", "CD", "EF" — Conservative, Central, Accelerated. **These are not the
vehicle size segments of the same name.** Joining those tables onto a size
segment gives plausible-looking, entirely wrong numbers with nothing to flag it.
`18_` renames them for this reason.

Those tables are also **global in-use fleet**, not European new sales. Sheet
`Conversion` in `18_` holds the four levers that convert between them.

---

## 7. Validation, last run

| 2025, mean per new vehicle | model | report |
|---|---|---|
| Length AB / CD / EF | 1403 / 2473 / 3536 | 1392 / 2486 / 3546 |
| Cu AB / CD / EF | 34.0 / 56.4 / 75.5 | 33.9 / 60.3 / 74.6 |

Length within 1%. The CD copper gap (−8%) is the length-first reconstruction
disagreeing with the report's stated copper density — it matches the
independent hand-calculation exactly, so it is a finding, not a bug.

---

## 8. What you edit, and where

| To change | Edit |
|---|---|
| When a segment adopts SDV / 800V | `18_` sheet `Penetration`, yellow cells |
| Autonomy scenario | `18_` sheet `Conversion` (four levers) |
| Autonomy override | `18_` sheet `Autonomy_Derived`, green columns |
| Which scenario is Min/Mode/Max | `18_` sheet `Conversion`, rows 18–20 |
| Sensors per autonomy level | `18_` sheet `Sensors_per_Level` |
| Metres per sensor | `18_` sheet `Metres_per_Sensor` |
| Conductor gauges, 2025 lengths | `17_` sheet `Baseline_2025` |
| SDV mechanism-vs-totals conflict | `17_` sheet `SDV_Depth` |
| Iterations / memory / plot years | `BevWiring.py` section 0 |

Yellow = editable. Orange = assumption with no source. Green = override.

---

## 9. NEXT: the sensor model

`ADAS length = sensor_count(autonomy_level) × metres_per_sensor`. The counts
come from `18_` sheet `Sensors_per_Level`, **which is entirely unsourced** and
now supplies roughly a quarter of the 2070 answer:

| share of total length from that sheet | 2025 | 2040 | 2070 |
|---|---|---|---|
| AB | 6% | 15% | 22% |
| CD | 9% | 19% | 24% |
| EF | 11% | 19% | 21% |

**The spec is `SensorNumbersMC/SENSOR_WIRING_INTERFACE.md`. Read it first.**

Headline: the sensor model's existing **Std / Opt / Rare presence factor is
already a penetration share**, so it only has to become a function of year and
autonomy level — not a rewrite. Two warnings from that document:

- **Do not recompute the autonomy mix.** Read the same source the wiring model
  reads, or the two will silently diverge — the exact failure this coupling
  exists to prevent.
- **`06_VehicleSensorNumbers.xlsx` has no radar and no lidar rows at all**, and
  no time or level dimension. Both must be added.

Preserve the cross-check: `17_` ÷ `06_` gives 28 / 25 / 31 m per camera across
AB / CD / EF. Two independently built datasets agreeing is real corroboration.
Re-run it at 2025 after any change.

---

## 10. Correlation between wire types — what is handled, what is not

Raised 2026-08-04, deliberately NOT implemented. Documented so the reasoning is
not lost.

**The concern:** if a vehicle has one kind of wiring it will not have the
other. Ethernet replaces CAN; they are substitutes, not independent quantities.

**Largely already handled — by the discrete architecture state.** Because a
whole vehicle draws ONE architecture state, an SDV_Zonal draw sends CAN to
x0.45 and Ethernet to x3.00 in the same vehicle. Substitution therefore falls
out of the state mechanism without being coded explicitly. Measured, CD 2040,
6000 iterations:

| pair | correlation | expected |
|---|---|---|
| CAN_BUS / ETH_BUS | **-0.74** | substitutes -> negative |
| LIN_BUS / ETH_BUS | -0.69 | substitutes -> negative |
| MOST_FO / ETH_BUS | -0.78 | MOST obsoleted by Ethernet |
| LV_DIST / LV_FUSE | +0.83 | complements, both shrink with zonal PDUs |
| HV_MAIN / ETH_BUS | +0.15 | unrelated; residual shared vehicle-size factor |

**What is NOT handled: substitution WITHIN a state.** Condition on the
architecture state and the anti-correlation collapses:

    low-Ethernet subset  (mostly Conventional/Transitional): corr(CAN,ETH) = -0.82
    high-Ethernet subset (mostly SDV_Zonal):                 corr(CAN,ETH) = +0.03

The first number is just the state mixture leaking through the crude
conditioning; the second is the truth. Two OEMs both on zonal architecture, one
choosing more Ethernet and less CAN than the other, are currently INDEPENDENT
draws. The residual per-category term `cat` has no substitution structure.

**Scale of the gap.** Signal/Comm is 29% of CD length at 2040. The standard
deviation of that group total is 0.97x what fully independent parts would give
— so at group level the negative pair correlations and the positive shared
factor very nearly cancel. **The missing piece changes the total band by a few
percent, not by a factor.** It matters for statements about individual
categories, not for the segment total.

**The bigger and more real gap is the SENSOR SUITE.** corr(ADAS_CAM,
ADAS_RADAR) = +0.92, because both rise with autonomy level. Positive is right —
an L4 car has more of both. But a vision-only strategy versus a lidar-heavy one
is a genuine either/or, and there is no "sensor strategy" dimension anywhere in
the model. Camera, radar, lidar and ultrasonic counts are drawn independently
given the level. That is a substitution the model cannot currently express at
all, and it sits in the block that already supplies ~a quarter of the 2070
answer.

**If it is implemented later**, three options in increasing order of honesty:

1. **Correlation matrix on the residual.** Cholesky or a Gaussian copula on the
   `cat` draws. Cheapest, but the off-diagonal numbers would be invented.
2. **Substitution groups.** Draw the GROUP total first (e.g. all signal
   wiring), then draw the split between members. Anti-correlation within the
   group is then guaranteed by construction and the group total stays
   well-behaved. No invented correlation coefficients.
3. **Model the mechanism.** The shared quantity is communication demand or
   sensing capability; the technology split is a separate draw. Most defensible,
   most work, and it needs data neither source currently provides.

Option 2 is the recommendation: it is structural rather than parametric, and it
generalises to the sensor-strategy problem, which is where the real gap is.


---

## 11. Open items

1. **`Sensors_per_Level` unsourced** — see section 9. Biggest gap.
2. **No sensor-strategy dimension** (vision-only vs lidar-heavy) — see
   section 10. The substitution the model cannot express at all.
3. **SDV timing not yet shifted +3.6 y** to match S&P (zonal 2% in 2022 → 38%
   in 2034). Agreed in principle, not applied to `18_`.
4. **`Fleet_to_NewSales_lead_y = 7`** pushes L4/L5 above the automation
   report's own "private L4/L5 < 5% through 2035" constraint (EF ~22%). Setting
   it to ~3 roughly restores consistency. Measured effect on totals is only
   ~3%, so it is less urgent than it sounds.
5. **Flat after ~2050**, because every share in `18_` saturates. Not a model
   artefact — a claim that no further architectural change happens.
6. **EF +100 m.** The report's EF length column sums to 3,646 against its own
   stated 3,546. Patched by `SEGMENT_LENGTH_CALIBRATION`; bad row unfound.
7. **Radar and lidar metres-per-sensor are assumptions** (`06_` has neither).
8. **Taxonomy.** Output uses the report's 28 category codes, not the old 28
   wire types; not 1:1 (`17_` sheet `Mapping`).
9. **Name collision inside the repo.** `Archive/BevWiring.py` is v3;
   `Wiring/BevWiring.py` is current. Different directories, but do not move
   files between them casually.
