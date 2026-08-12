# Model suite — status, scope and how to read the results

**The authoritative status document.** Last updated 2026-08-12.

If you read one file before using these results, read this one. Every other note
is either the evidence behind a decision or the record of how something was
built.

---

## 1. The suite at a glance

| model | what it produces | time axis | reads |
|---|---|---|---|
| `Wiring/BevWiring.py` | wire length, copper mass | **2020–2070** | `17_`, `18_`, `19_` |
| `SensorNumbersMC` | sensor counts per vehicle | **2020–2070** | `01_`, `06_`, `18_`, `19_` |
| `PCBAreaMC` | PCB area, board counts | **2020–2070** | `11_` (from `01_`), `03_` |
| `PCBElementMC` | element mass in PCBs | **2020–2070** | `04_`, PCBAreaMC histograms |
| `ElectricMotorMC` | auxiliary motor counts, mass | **2020–2070** | `05_` |
| `SensorElementsMC` | element mass in sensors | **static, by decision** | `01_`, `06_`, `07_` |
| `ElectricMotorElementMC` | element mass in motors | **static, by decision** | `10_`, ElectricMotorMC histograms |

**Five of seven are year-resolved. The two that are not are static
deliberately** — see §3. That is a stated scope boundary, not unfinished work.

---

## 2. How to read the results — the part that matters most

### 2.1 The PCB numbers are bounded by an 8.2% driver

PCB area 2025 → 2070: **AB +0.4%, CD −1.1%, EF −2.0%.**
Element mass: **AB −0.30%, CD −1.41%, EF −1.68%.**

**This is NOT a finding that BEV electronics material demand is flat to 2070.**
It is the measured reach of the architecture driver **as currently scoped** —
8.2% of board area (`PCB_MODEL_DESIGN.md` §2.2f). A driver reaching 8.2% cannot
move a total by more than a few percent, whatever it does.

**The unsourced gap that bounds this: `P-g`.** Zonal consolidation could touch
the *other* ~49 controller-like components — **50.7% of EF board area**. The
project's own evidence says a premium 2020 vehicle carried 80–150 discrete ECUs
and a zonal architecture reduces that to under 20. **None of that is modelled**,
because how far it goes per component is not recorded anywhere. **That, not the
current result, is where a real material trend would come from.**

### 2.2 The motor numbers extrapolate 35 of 50 years

Motor counts 2025 → 2070: **AB +39.7%, CD +28.5%, EF +12.4%** (AB fastest —
the opposite of the ADAS gradient, and correct: EF is already near-saturated).

**Every source stops at 2035.** The curve past then is the *shape* argued in
`MOTOR_MODEL_DESIGN.md` §2, not evidence. The headroom and τ anchors in `05_`
sheet `Motor_Growth` are **ASSUMPTION** bounded by evidence — the only invented
numbers in the motor design.

### 2.3 These are scenarios, not predictions

Standing instruction from the user, and it governs every number above:
*"predictions are not science, but different types of scenarios, which have an
uncertainty."*

Every year-resolved model draws its scenario **per vehicle, held across all
years** — a vehicle is one design on one timeline for its whole life. Redrawing
per year would average the band away and hand back the mode.

**What carries a band today:**

| | |
|---|---|
| architecture adoption timing | `shift_shares`, σ = 5 years per vehicle |
| label quantisation | `01_`'s 4-level scale, triangular within the bin |
| motor headroom and τ | `Motor_Growth` Min/Mode/Max |
| board size and count | `03_` and `01_` min/mode/max |

**What does not:** the PCB total band is still dominated by board-size sampling
(15–17%), not by technology adoption — again because the driver reaches 8.2%.

---

## 3. The two static models — why, and what that means

**Decision 2026-08-12.** `SensorElementsMC` and `ElectricMotorElementMC` stay
static permanently.

> *"It is impossible to predict future composition of these types of sensors.
> Data could be modified to reflect certain scenarios. But it is outside of the
> scope to have a development until 2070."*

**The split is principled:**

| forecastable | not forecastable |
|---|---|
| **how many** sensors/motors a car has — feature content, sourced trends | **what they are made of** in 2070 |

Counts have evidence behind them and are year-resolved. Composition does not,
and a fitted curve would be a fabricated parameter — the thing this project has
refused throughout.

**Consequences to be labelled, not fixed:**

- Both models output a **2025 snapshot**.
- `SensorElementsMC` reports **lidar elements as zero in every year**, because
  `01_` records lidar as `–` for 2025. That is correct *as a 2025 statement*
  (European lidar penetration is ~1–3%) and wrong only if read as a forecast.
  The year-resolved half of the project says EF reaches 0.765 lidar
  units/vehicle by 2070 (`STATIC_MODELS_DIAGNOSTIC.md` §1).
- `07_` and `10_` are the **scenario levers**: edit composition to explore a
  case, rather than have the model assert a trajectory.

---

## 4. Shared machinery — one implementation each

| module | holds |
|---|---|
| `tools/drivers.py` | every driver curve: 800V share, architecture shares, ADAS tier shares, lidar share, tier presence, `shift_shares` |
| `tools/accumulator.py` | `Accumulator` (fixed-bin, memory independent of draw count), `CoMoments` (exact correlations), the 50/1000-bin constants |

**Why this exists.** The same curve reader once lived in `BevWiring` *and*
`SensorNumbersMC`, and a third copy was about to appear in `PCBAreaMC`. Two
models computing the same share from the same file and drifting apart is exactly
what validation V12 exists to catch — so the duplication was removed rather than
validated.

**What is exact and what is binned** (`tools/accumulator.py`):

| exact | mean, std, variance, min, max, **all correlations** |
|---|---|
| **binned** | percentiles and mode, to 1/1000 of the range |

**Known remaining duplication:** `BevWiring` still carries its own
`_shift_shares`. Proven numerically identical to the shared one at **3.3e-16**.
Unify when convenient.

---

## 5. Validation inventory

| model | checks | status |
|---|---|---|
| `BevWiring` | V1, V6, V8, V9, V10 | **9/9 pass** |
| `SensorNumbersMC` | V11–V15 | **all pass**; V14 915/915, V15 45/45 |
| `PCBAreaMC` | P1, P3, P5 | **pass**. P3 = `0.000e+00` |
| `ElectricMotorMC` | M1–M4 | **all pass**. M1 exact (`0.00e+00`) |

**Not written:** P2 (PCB and sensor models compose the same ADAS presence) and
P4 (ADAS share of PCB area ≈3.9% ±1pp). M5 is moot until the accumulator port.

**Validations that matter most are the ones testing a mechanism, not a number:**
P3 (two models draw the same architecture shares), M2 and M4 (the segment
gradient cannot invert), V12 (one curve, two models).

---

## 6. Data files

| file | role | year axis |
|---|---|---|
| `01_VehicleElectronics.xlsx` | component list, presence on a 4-level scale | no — a 2025 observation |
| `03_VehiclePCBSize.xlsx` | board size min/mode/max | no |
| `04_VehiclePCBComposition.xlsx` | PCB element composition | no — see §3 |
| `05_VehicleElectricMotorsWeight.xlsx` | motor counts, masses, materials; **`Motor_Growth` anchors** | growth anchors only |
| `06_VehicleSensorNumbers.xlsx` | sensor counts per component | no |
| `07_` / `10_` | sensor / motor element composition | no — **scenario levers** |
| `11_PCB_Distribution_Classified.csv` | generated from `01_` | no |
| `12_Motor_Distribution.csv` | generated from `01_`, **read by nothing** | — |
| `17_`, `18_`, `19_` | wiring baseline, technology penetration, ADAS adoption | **yes** |

**`01_`'s four-level scale (1.00 / 0.50 / 0.25 / 0.00) cannot express an
arbitrary share.** Where a composed value falls between two labels the
disagreement is *quantisation, not error* — validations V13 and the PCB
equivalent exempt those rows rather than widening tolerance.

---

## 7. Known gaps, honestly stated

1. **`P-g`** — 50.7% of PCB area, unsourced. **The largest open item.**
2. **`M-b2`** — accumulator not ported into `ElectricMotorMC`. ~82 MB/metric at
   51 years: uncomfortable, not fatal.
3. **Motor type mix held constant** — growth features are predominantly DC, so
   the DC share should rise. Counts unaffected; **mass is**.
4. **`12_Motor_Distribution.csv`** generated and read by nothing. It is an
   ECU-attributed view that omits window, mirror and wiper motors entirely —
   rename it to say so, or stop generating it.
5. **P2 and P4** unwritten.
6. **`BevWiring._shift_shares`** duplicates the shared module.

---

## 8. Three traps that have each bitten once

1. **Adding a sheet to a workbook can break readers** that apply fixed `usecols`
   to every sheet. Adding `Notes` to `01_` broke *both* sensor models.
   **Check the reader before writing.**
2. **A footnote in a data column silently changes the row count.**
   `Presence_per_Tier` read 13 rows for 12; `BASE_YEAR` did it again in
   `Motor_Growth`. **Park notes in a far column.**
3. **Non-breaking spaces in `11_` component names**
   (`Body\xa0Control\xa0Module`). Exact-match lookup returns nothing **with no
   error**. Normalise whitespace before matching.

**And one about method.** Several mechanisms were written from scratch that this
project had already solved elsewhere — the V13 presence rule, `shift_shares`,
the accumulator. **Ask "has this been solved here already?" before designing.**

**And one about validation.** The motor 2× count bug survived because an
external figure was checked against the model's *input* rather than its
*output*. **A cross-check that stops at the input does not validate the model.**

---

## 9. Document map

| file | what it is |
|---|---|
| **`MODEL_STATUS.md`** | **this file — start here** |
| `PCB_MODEL_DESIGN.md` | PCB design, evidence and step log (P-a … P-g) |
| `MOTOR_MODEL_DESIGN.md` | motor design and step log (M-a … M-d) |
| `MOTOR_MODEL_DIAGNOSTIC.md` | why `05_` is the motor count basis |
| `AUX_MOTOR_ADOPTION_RESEARCH.md` | the motor growth evidence |
| `ADAS_Sensor_Adoption_Report_2025_2070.md` | the ADAS tier evidence; **§1.2 defines the uncertainty calibration used throughout** |
| `SENSOR_MODEL_DESIGN.md` | sensor design |
| `STATIC_MODELS_DIAGNOSTIC.md` | what was frozen before step 7 |
| `BRAND_ORIGIN_DESIGN.md` | Driver E — designed, **not implemented** |
| `HANDOVER*.md` | session handovers |
