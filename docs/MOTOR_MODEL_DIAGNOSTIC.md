# Auxiliary motors — diagnostic before any modelling

**Written 2026-08-11. No motor model or motor data was changed.** This
answers the question the user set: *which count source should the year axis be
built on?* — by measuring, not by choosing.

**Scope reminder (§8 of `PCB_MODEL_DESIGN.md`):** `ElectricMotorMC` covers
**auxiliary motors — window lifts, seats, pumps, wipers, tailgate — not the
traction powertrain.** Magnet chemistry and AWD share are traction concerns and
do not apply.

---

## 1. Headline — the two count sources do not describe the same vehicle

There are two independent statements of how many auxiliary motors a BEV has.

| | source | segments | read by |
|---|---|---|---|
| **`05_`** `NumberMotors` sheet | curated directly | **A–F** (six) | `ElectricMotorMC` |
| **`12_`** `Motor_Distribution.csv` | generated from `01_` by `BEVElectronicsClassification.py` | AB/CD/EF | **nothing** |

**At the total level they look fine** — 0.81× / 0.90× / 1.24× (05÷12,
midpoints), comfortably inside the project's uncertainty framing.

**That agreement is coincidence.** Per motor type:

| type (05÷12) | AB | CD | EF |
|---|---|---|---|
| Stepper_Small | 0.62× | 0.55× | 0.74× |
| DC_Medium | 1.33× | 2.95× | **5.58×** |

`05_` puts EF medium DC motors at **33.5**; `12_` puts them at **6.0**. The
totals reconcile only because `05_` is *low* on small steppers and *high* on
medium DC, and the two errors cancel.

**The taxonomies do not match either:**

| `05_` | `12_` |
|---|---|
| SmallStepperMotors | StepperMotor_Small |
| **MediumStepperMotors** | *no counterpart* |
| — | **DCMotor_Small** *(no counterpart in `05_`)* |
| MediumDCMotors | DCMoter_Medium *(sic — typo in the column name)* |

**They do not partition the motor population the same way.**

### 1a. RESOLVED — the size labels are the problem, not the counts

**User's hypothesis, 2026-08-11: "calling them medium or small, but based on the
power they belong to another category." Tested and confirmed.**

Pooling by motor *technology* and ignoring the size labels:

| pooled (05÷12) | AB | CD | EF |
|---|---|---|---|
| Stepper | 1.12× | 1.06× | 1.40× |
| DC | 0.56× | 0.78× | **1.14×** |

**EF DC collapses from 5.58× to 1.14×**, and the worst case anywhere falls to
0.56×. The counts were never really in conflict; the *labels* were.

`05_`'s `Mass` sheet shows why — the classes are **mass bands, and they
overlap**:

| `05_` type | mass |
|---|---|
| SmallStepperMotors | 150–300 g |
| MediumStepperMotors | 500–1000 g |
| **MediumDCMotors_plastic** | **400–800 g** |
| MediumDCMotors_metal | 500–1500 g |

**`05_` has no "Small DC" class at all.** Every DC motor is called Medium —
including 400 g plastic units that are lighter than a "Medium" stepper and sit
inside the small band. `01_`/`12_` *does* split DC into Small and Medium. So the
same physical motor is Medium in one file and Small in the other.

**The correspondence that actually holds:**

    05_ MediumDC (plastic + metal)    ==   12_ DCMotor_Small + DCMoter_Medium
    05_ SmallStepper + MediumStepper  ==   12_ StepperMotor_Small

**Consequence:** a per-type year axis must not be built on the size labels as
they stand. Either the labels are redefined against a stated mass or power
threshold, or the model works at the technology level (stepper vs DC) where the
two sources agree to within 1.4×. **The residual AB DC gap of 0.56× — `12_`
gives roughly twice as many — is the one real disagreement left, and it is
bounded and worth explaining.**

Against the project's calibration (`ADAS_Sensor_Adoption_Report` §1.2):
~3% self-consistency floor, ~1.6× cross-house spread, **3–4× structural
disagreement**, >10× before calling something an error — **5.58× is past
structural and needs explaining, not averaging.**

---

## 2. Other findings

1. **`12_` is dead.** Generated on every run of
   `BEVElectronicsClassification.py`, read by no model. Either it becomes the
   count source or it should stop being written.
2. **`ElectricMotorMC` uses `HIST_BINS = 140`.** The project convention is
   **50 bins and is documented as non-negotiable** — every other exported
   histogram in the suite uses it. Motor histograms are therefore not
   comparable with the rest, and **`ElectricMotorElementMC` samples from these
   CSVs**, so the non-standard binning propagates into element masses.
3. **No year axis**, like the other static models. 200,000 draws, seeded (42).
4. **`ElectricMotorElementMC` reads `ElectricMotorMC/materials_histograms_csv/`**
   — the same file-coupling as the PCB chain, so it needs the P-f treatment
   whenever motors gain a time axis.
5. **`05_` is six-segment (A–F)** while everything else in the project is
   AB/CD/EF. `ElectricMotorMC` already pairs them internally via
   `SEGMENT_GROUPS`, so its *outputs* are AB/CD/EF — the six-segment structure
   is input-only, and is an asset rather than a problem: it is finer-grained
   than the rest of the suite.

---

## 3. What would actually drive auxiliary motor counts over time

Not yet researched — listed so the scope is visible.

**Does not apply:** zonal consolidation moves motor *drivers* into zone
controllers, which is a PCB effect. The motor itself stays. This is the
mistake §8 warns about, in a new form.

**Candidates, all feature-content rather than materials:**

| direction | mechanism |
|---|---|
| **up** | mechanical → electric substitution: e-latches, electric door handles, active aero shutters, powered tailgates, HVAC flap actuators |
| **up** | feature democratisation — AB gains what EF already has (the premium-first gradient seen in every other driver here) |
| **down** | saturation in EF: power seats/mirrors/windows are already universal, so little headroom |
| **down** | integration — one multi-function actuator replacing two single-function ones |

**Implication:** AB should grow fastest and EF slowest, the *opposite* of the
ADAS tier picture. Worth stating up front so the result is not mistaken for an
error when it appears.

---

## 4. Recommendation on the count source

**Neither file can be adopted as-is.** The honest options:

- **(A) Work at the technology level.** Stepper vs DC, where the two sources
  agree to 1.06–1.40× (§1a). Sidesteps the broken size labels entirely.
  **Recommended.** The remaining task is the AB DC 0.56× gap, which is one
  segment and one technology — bounded.
- **(A2) Redefine the size classes first.** State an explicit mass or power
  threshold and re-label both files against it. More work, but it is the only
  route to a per-size year axis, and `ElectricMotorMC`'s mass sampling is
  currently keyed to these classes.
- **(B) Keep `05_`.** Least disruption; `ElectricMotorMC` keeps its input and
  gains only a year axis. But motor counts stay disconnected from the `01_`
  component list the rest of the suite is built on, and `12_` stays dead.
- **(C) Move to `01_`/`12_`.** Motors join the shared presence mechanism, `12_`
  comes alive, and the architecture driver applies for free. But `12_` is the
  source that says EF has 6 medium DC motors, which is the figure most in doubt.

**Not decided.**

---

## 5. What this diagnostic did NOT do

- No fix to `05_`, `12_`, or any motor model. (`01_` *was* corrected in the same
  commit, but for the PCB zonal labels — unrelated to motors. See
  `PCB_MODEL_DESIGN.md` §2.2h.)
- No year axis, no driver, no research into the feature-content trend.
- No view on whether `HIST_BINS = 140` should change — flagged only.
