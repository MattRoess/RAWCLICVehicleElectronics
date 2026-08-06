# BEV wiring model — living status

**Current model: `Wiring/BevWiring.py`** (generation 5; v3 and v4 were deleted
on 2026-08-05 — `MODEL_HISTORY.md` records why each was replaced).
Last updated 2026-08-05. This is the single handover document.

    python3 Wiring/BevWiring.py          # ~4 min at 200,000 iterations

> **2026-08-05 — the ADAS axis changed.** Sensor content is no longer keyed on
> SAE certification level. It is keyed on an installed **hardware tier** H0–H4,
> plus a separate lidar driver and a post-2040 scenario driver, all in
> `Data/19_ADAS_sensor_adoption.xlsx`. Read
> **`IMPLEMENTATION_GUIDE.md`** before touching the code and
> **`AUTONOMY_LEVELS_VS_HARDWARE.md`** for why. Sections 2, 8, 9 and 11 below
> are updated; the rest is unchanged.

---

## 1. Files

| File | Role |
|---|---|
| `Wiring/BevWiring.py` | **the model** |
| `Wiring/IMPLEMENTATION_GUIDE.md` | **how the tier axis works, and how to switch scenarios** |
| `Wiring/AUTONOMY_LEVELS_VS_HARDWARE.md` | why certification was the wrong key |
| `docs/ADAS_Sensor_Adoption_Report_2025_2070.md` | the sensor-adoption reasoning; every number tagged FACT / DERIVED / ASSUMPTION |
| `Wiring/outputs/data/bev_wiring_stats.csv` | 20,808 rows — mean, P2.5, median, mode, P97.5, every year |
| `Wiring/outputs/data/bev_wiring_histograms.csv` | 142,800 rows — 408 series × 7 snapshot years × **50 bins** |
| `Wiring/outputs/plots/` | 38 figures — 8 trajectory, 30 histogram |
| `Data/17_BEV_wiring_baseline_2025.xlsx` | 2025 baseline, gauges, SDV factors, SDV depth |
| `Data/18_BEV_technology_penetration.xlsx` | architecture / voltage shares. Its `Metres_per_Sensor` is still read; its **`Sensors_per_Level` is not** |
| `Data/19_ADAS_sensor_adoption.xlsx` | **tier shares, sensor counts per tier, lidar, scenarios, validation targets** |
| `Data/20_scenarios.xlsx` | **PROJECT-WIDE scenario selection — sheet `Control` cell B4 drives every model** |
| `tools/make_19_adas_sensor_adoption.py` | regenerates `19_` from the report |
| `tools/make_20_scenarios.py` | regenerates `20_` |
| `Wiring/MODEL_HISTORY.md` | why v3 and v4 were replaced, why `15_`/`16_` were retired, and the user decisions still in force |

---

## 2. How it works

One anchor year (2025), independent drivers, no splines and no era seams.

    length(cat,t) = baseline_2025 x architecture_state_factor x variability
    ADAS length   = sensor_count(hardware_tier) x scenario_mult x metres_per_sensor
    cu_per_m(t)   = gauge x 8.96 x (1 - 0.425 if 800V)          [HV only]
    Cu (kg)       = sum(length x cu_per_m) / 1000

| Driver | States | Affects | Source |
|---|---|---|---|
| Architecture | Conventional / Transitional / SDV_Zonal | LV + signal LENGTH | `18_` |
| Voltage | 400V / 800V | HV Cu-per-METRE | `18_` |
| **A — hardware tier** | **H0 … H4** | ADAS + sensor LENGTH, via sensor counts | `19_` |
| **B — lidar** | equipped / not, lag sampled | lidar count only | `19_` |
| **C — scenario** | S1 / S2 / S3, post-2040 | multiplier on all sensor counts | **`20_`** |

Independent, so architecture shortens wiring while sensors lengthen it. That is
why CD flattens near 1,750 m and EF near 2,850 m after 2040 rather than falling.

**Why tier and not SAE level.** A car does not grow a wire when a regulator
grants liability transfer. Volvo's EX90 carries 31 sensors and is certified L2;
BMW's i7 carried 25 and was certified L3. Certified L3 is being *withdrawn* in
Europe (Mercedes paused Drive Pilot, BMW discontinued Personal Pilot L3) while
sensor content keeps rising — so a level-keyed model gets the near-term trend
backwards. Full argument in `AUTONOMY_LEVELS_VS_HARDWARE.md`.

The old autonomy driver still exists behind `USE_TIER_AXIS = False`, for
comparison runs only. It is not maintained.

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

7. **Validation is now executed, not just written down.** `validate()` runs at
   the end of a full run and checks the targets in `19_` sheet `Validation`.
   Tolerances come from sheet `Uncertainty` and are deliberately no tighter than
   the sources agree with each other — V1 is ±3%, not ±1%, because the source
   report disagrees with *itself* by 2.8% on EF length. A report drifting from
   the code is now a test failure. **Nothing below ~3% is signal.**

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
| **Which ADAS scenario is active** | **`20_` sheet `Control`, cell B4** — `SAMPLE` (default) / `S1` / `S2` / `S3` |
| **Tier adoption by segment and year** | **`19_` sheet `Tier_Shares`** |
| **Sensor counts per tier** | **`19_` sheet `Tiers`** |
| **Lidar path and band** | **`19_` sheet `Lidar`** |
| **China→Europe lidar lag** | **`19_` sheet `Parameters`** |
| **Scenario multipliers / weights** | **`20_` sheet `Scenarios`** (project-wide) |
| Metres per sensor | `18_` sheet `Metres_per_Sensor` (unchanged) |
| Conductor gauges, 2025 lengths | `17_` sheet `Baseline_2025` |
| SDV mechanism-vs-totals conflict | `17_` sheet `SDV_Depth` |
| Iterations / memory / plot years | `BevWiring.py` section 0 |
| ~~Sensors per autonomy level~~ | ~~`18_` sheet `Sensors_per_Level`~~ — **no longer read** |
| ~~Autonomy scenario / override~~ | ~~`18_` sheets `Conversion`, `Autonomy_Derived`~~ — **no longer drive ADAS** |

Yellow = editable. Orange = assumption with no source. Green = fact / override.

`19_` is **generated** from
`docs/ADAS_Sensor_Adoption_Report_2025_2070.md` by
`tools/make_19_adas_sensor_adoption.py`. Editing the workbook works, but the next
regeneration overwrites it — for a permanent change, edit the report and the
generator together. Anchor years are read through PCHIP, so adding or deleting
year columns needs no code change.

---

## 9. NEXT: the sensor model

**This is now the largest outstanding item.** `BevWiring.py` has been rewired
onto the hardware-tier axis; `SensorNumbersMC.py` has **not**. Until it is, the
two models sit on different axes — precisely the divergence the coupling exists
to prevent.

The ADAS block still supplies roughly a quarter of the 2070 answer:

| share of total length from the sensor block | 2025 | 2040 | 2070 |
|---|---|---|---|
| AB | 6% | 15% | 22% |
| CD | 9% | 19% | 24% |
| EF | 11% | 19% | 21% |

**The instruction set is `docs/ADAS_Sensor_Adoption_Report_2025_2070.md`
§6**, with the numbers in `19_` sheet `Presence_per_Tier` — 12 ADAS components
× tiers H0–H4, already written and validated but **not yet consumed by any
code**. `SensorNumbersMC/SENSOR_WIRING_INTERFACE.md` still holds the useful
background; read "level" as "tier" throughout it.

The fix stays small because the sensor model's **Std / Opt / Rare presence
factor is already a penetration share**. It only needs one more index:

    presence(component, segment, year)
        = Σ_tier  share(tier, segment, year) × presence(component | tier)

Three warnings:

- **Do not recompute the tier shares.** Read `19_` sheet `Tier_Shares`, the same
  source `BevWiring.py` reads. Computing them twice guarantees divergence.
- **`01_` EF lidar presence is wrong** — labelled `Opt` (0.50) against a real
  2025 value near 0.01. A 50× gap, far outside every spread recorded in `19_`
  sheet `Uncertainty`. It bites the moment this model is rewired.
- **`06_` camera counts are low** (EF max 5 against 6–10 measured) and
  **ultrasonics may be double-counted** (under both *Ultrasonic sensors* and
  *Parking assist ECU*, 8–12 each, against 12–16 measured).

`06_` does **have** radar and lidar rows — the earlier claim that it did not was
a naming mismatch and has been corrected in both that spec and `18_` sheet
`Notes`. Its EF radar (5) and lidar (0–1) counts match the measured EQS, i7 and
EX90 exactly.

Preserve the cross-check: `17_` ÷ `06_` gives 28 / 25 / 31 m per camera across
AB / CD / EF. Two independently built datasets agreeing is real corroboration.
Re-run it at 2025 after any change (validation V2).

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

1. **`SensorNumbersMC.py` not yet rewired** — see section 9. **Biggest gap.**
   `19_` sheet `Presence_per_Tier` is written and validated but consumed by
   nothing, so the two models are on different axes.
2. **No sensor-strategy dimension** (vision-only vs lidar-heavy) — see
   section 10. The substitution the model cannot express at all. Driver B now
   makes lidar an explicit driver, which is a partial answer, but the
   *either/or* structure is still missing.
3. **SDV timing not yet shifted +3.6 y** to match S&P (zonal 2% in 2022 → 38%
   in 2034). Agreed in principle, not applied to `18_`.
4. ~~**`Fleet_to_NewSales_lead_y = 7`** pushes L4/L5 above the report's own
   "private L4/L5 < 5% through 2035" constraint.~~ **RESOLVED / RESTATED
   2026-08-05.** The old framing was wrong twice over. It called for lowering
   the lever, but (a) the `Notes` sheet in `18_` records *your* input as
   *more* aggressive than the model — EF L5 ~20% by 2035 against the model's
   2.4% — so lowering it moved *away* from the specification; and (b) no
   setting of that lever satisfies the constraint anyway, since with
   `Private_lag_y = 5` and `Offset_EF_y = −5`, `net_shift(EF)` reduces to
   `−lead`, requiring a *negative* lead. The real problem was neither the lever
   nor the constraint but **the axis**: certification level was never the right
   key for sensor content. Superseded by the tier axis; the conversion levers
   no longer drive ADAS at all. Kept here because the reasoning is worth not
   losing.
5. **Flat after ~2050** for architecture, because every share in `18_`
   saturates. Not a model artefact — a claim that no further architectural
   change happens. Driver C now supplies post-2040 *sensor* growth, so the
   totals are no longer flat, but the architecture side still is.
6. **Driver C multipliers (1.0 / 1.4 / 2.0) are uncalibrated** and are now the
   largest single lever on the 2070 answer. The two mechanisms behind them —
   cost decline with volume, safety redundancy — are observable; the values are
   not sourced. See the report §9.2.
7. **Driver A's low end may be too aggressive.** Its first external check
   (Yano Research units by level) agrees within 1.10× at the top of the ladder
   in 2035 but disagrees by 3.3× at the bottom in 2025. Part of that is
   BEV-vs-all-powertrain scope; probably not all. Report §9.0.
8. **EF +100 m.** The report's EF length column sums to 3,646 against its own
   stated 3,546. Patched by `SEGMENT_LENGTH_CALIBRATION`; bad row unfound.
   Note this 2.8% self-inconsistency is what sets the **noise floor for the
   whole chain** — see `19_` sheet `Uncertainty`.
9. **Radar and lidar METRES-PER-SENSOR are assumptions.** (Corrected
   2026-08-05: this item used to add "`06_` has neither", meaning neither radar
   nor lidar rows. That was wrong — `06_` has both; it was a naming mismatch.
   The metres-per-sensor figures in `18_` remain assumptions, which is the part
   that still stands.)
10. **Taxonomy.** Output uses the report's 28 category codes, not the old 28
    wire types; not 1:1 (`17_` sheet `Mapping`).
11. ~~**Name collision inside the repo.**~~ **RESOLVED 2026-08-05** by deleting
    `Wiring/Archive/`. There is now exactly one `BevWiring.py`.
