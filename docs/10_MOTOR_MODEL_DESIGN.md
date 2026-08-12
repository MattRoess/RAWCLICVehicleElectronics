# Auxiliary motors — design note (year axis)

**Written 2026-08-11. M-a is done; M-b to M-d are not implemented.**

> **Sheet-addition safety, recorded because it went wrong once.** Adding a
> `Notes` sheet to `01_` on 2026-08-09 broke *both* sensor models — their
> readers apply fixed `usecols` to every sheet. `ElectricMotorMC` was checked
> *before* writing rather than assumed safe: it filters with
> `if sh in KNOWN_MAT_SHEETS`, so an unrecognised sheet is skipped. `05_` has
> exactly one reader. Verified after the fact by a full re-run.

Companions: `08_MOTOR_MODEL_DIAGNOSTIC.md` (what is broken today),
`09_AUX_MOTOR_ADOPTION_RESEARCH.md` (the evidence), `06_PCB_MODEL_DESIGN.md` (the
same job, for PCB).

**Scope.** Auxiliary motors only — window lifts, seats, pumps, wipers, tailgate,
mirrors. **Not the traction powertrain.**

---

## 1. What is settled before this note

| | |
|---|---|
| Count source | **`05_` `NumberMotors`.** `12_` is an ECU-attributed subset that omits window, mirror and wiper motors entirely — diagnostic §6 |
| 2025 level | **corroborated externally**: `05_` EF 38–63 against an independent 40–60 (premium >80) |
| Near-term rate | **~2.5%/yr and decelerating**, from saturating-feature fitment data — *not* the 4.7%/yr headline |
| Ceiling type | **cost, not capability** — nothing physical stops AB carrying EF content, price does |
| Segment order | **AB fastest, EF slowest** — opposite of the ADAS gradient |
| Integration | a brake on the rate, **not** a reversal (patents, not fitment) |

---

## 2. The mechanism

Each segment approaches its own **saturated content**, at a **cost-controlled
rate**:

    N(seg, y) = C(seg) − ( C(seg) − N(seg, BASE_YEAR) ) · exp( −(y − BASE_YEAR) / τ(seg) )

    C(seg) = N(seg, BASE_YEAR) × headroom(seg)

**Why exponential approach rather than a growth rate.** A constant rate cannot
be right — 4.7%/yr to 2070 gives 300–500 motors per car. Saturation is the
observed behaviour (front windows 0→95%, now extending to rear only), and this
form has saturation built in rather than bolted on. It also needs **no separate
ceiling year**: the curve flattens by construction.

**Why headroom is multiplicative on each segment's own 2025 content, not a
common ceiling.** An AB car will not carry EF's motor count even when cost
allows — it has fewer doors, smaller seats, less glass. The physical content
differs, not only the price. A common ceiling would force AB to become EF.

---

## 3. Proposed anchors — **these are the judgement calls, and they need review**

Everything below is **ASSUMPTION** bounded by evidence, not FACT. Carried as
`Min` / `Mode` / `Max` in the project's usual convention.

### 3.1 Headroom — how much content a segment still has to gain

| segment | Min | **Mode** | Max | reasoning |
|---|---|---|---|---|
| **AB** | 1.30 | **1.50** | 1.80 | most to gain; compact liftgate ~20%→>40% by 2030, e-latches at 10.7% CAGR |
| **CD** | 1.20 | **1.35** | 1.60 | mid |
| **EF** | 1.05 | **1.15** | 1.30 | near-saturated; >62% already hands-free capable |

### 3.2 τ — the cost-down time constant, in years

| | Min | **Mode** | Max |
|---|---|---|---|
| τ, all segments | 20 | **30** | 50 |

Larger τ = slower cost decline = later adoption. Applied per vehicle as one
draw held across years, like every other scenario axis here.

### 3.3 What these imply — computed against `05_`'s actual 2025 counts

Not illustrative: run against the real `NumberMotors` sheet, 2026-08-11.

| seg | 2025 | 2070 min | **2070 mode** | 2070 max | mode change | initial rate |
|---|---|---|---|---|---|---|
| **AB** | 14.5 | 17.1 | **20.1** | 24.9 | **+38.8%** | 1.67%/yr |
| **CD** | 27.5 | 30.8 | **35.0** | 42.3 | **+27.2%** | 1.17%/yr |
| **EF** | 58.8 | 60.5 | **65.6** | 74.5 | **+11.7%** | 0.50%/yr |

**Consistent with "not so dynamic":** initial rates 0.5–1.7%/yr, below the
~2.5%/yr measured on power windows — which is right, because that figure is a
single feature still actively extending, not a whole-vehicle average.

**Both mechanism tests pass on these anchors:**

    M2  AB 2070 < EF 2070      20.1 < 65.6      PASS
    M4  AB% > CD% > EF%        39% > 27% > 12%  PASS

**If these anchors look wrong, this is the place to change them** — they are the
only invented numbers in the design, and §5 exists to catch them.

---

## 4. The motor-type mix

`ElectricMotorMC` samples `SmallStepper`, `MediumStepper` and `MediumDC`
separately with **different masses**, so growth cannot be applied as a single
aggregate without deciding how the mix moves.

**Proposal: hold the mix constant — apply the same growth to all three types.**
ASSUMPTION.

**Stated honestly:** this is almost certainly slightly wrong. The features
driving growth — tailgates, e-latches, seat functions — are predominantly **DC**,
so the DC share should rise. But nothing sourced quantifies it, and inventing a
mix shift would put a second fabricated parameter next to the first.

**Consequence if wrong:** motor *mass* is under- or over-stated by the mass
difference between types (`MediumDC_metal` 500–1500 g vs `SmallStepper`
150–300 g). Counts are unaffected. **Flagged as the largest known weakness.**

---

## 5. Validation targets

| # | Target | Tolerance | Catches |
|---|---|---|---|
| **M1** | 2025 motor counts reproduce `05_` | **exact** | the year axis changing the present |
| **M2** | 2070 AB total < 2070 EF total | ordering | AB overtaking EF, which the cost mechanism forbids |
| **M3** | Initial growth rate: AB 1–3%/yr, CD 0.8–2.5%/yr, **EF 0.3–1.5%/yr** | ±0.5 pp | anchors implying an implausible near-term rate |
| **M4** | AB growth % > CD > EF over 2025→2070 | ordering | the segment gradient inverting |
| **M5** | Accumulator vs full draw at 2025 | ±3% | the port itself |

**M3 is deliberately segment-specific.** A single 1–3%/yr band across all
segments was written first and would have **failed EF at 0.50%/yr** — but EF is
near-saturated, so sub-1% is the expected answer, not a defect. A validation
that fires on correct behaviour is worse than no validation.

**M2 and M4 are the ones that matter** — they test the *mechanism*, not the
numbers, and they would fail loudly if the headroom anchors were mis-ordered.

---

## 6. Proposed order

| Step | Work | Verified by |
|---|---|---|
| ~~**M-a**~~ | ~~Add the anchors to a new sheet in `05_`~~ | **DONE 2026-08-11.** `Motor_Growth` sheet written, header row 26, reads exactly 3 rows. `ElectricMotorMC` re-run: exit 0, 4 material sheets loaded — unchanged |
| **M-b1** | ~~`HIST_BINS 140 -> 50`~~ | **DONE 2026-08-11.** Imported from `tools/accumulator.py`, not redeclared. Histogram CSVs 140 rows -> 50, `ElectricMotorMC` exit 0 |
| **M-b2** | Port the accumulator into `ElectricMotorMC` | **NOT DONE.** Bigger than the PCB port: this model holds `N_SAMPLES` arrays through a three-deep nested loop, so chunking means restructuring the main body. Not a blocker for M-c (51 years is ~82 MB/metric, uncomfortable not fatal) |
| ~~**M-b3**~~ | ~~Raw samples CSV -> `.npy`~~ | **DONE 2026-08-11.** 24 files converted to float32 `.npy` + `.json` sidecars, all verified `(200000, n)` and finite before the old CSVs were removed. `ElectricMotorMC/` **812 MB -> 154 MB, 657 MB freed** — more than the 522 MB cleared from PCBAreaMC |

**Histogram CSVs are deliberately NOT converted.** User, 2026-08-11: *"it was
the idea to pass the output of the MC as PDF to potential users of the data"* —
the histograms **are** the product, the probability density function handed to
downstream users. They stay CSV: small (136 KB), human-readable, openable
anywhere. Only the write-only intermediate sample draws went binary.

**Open question this raises.** M-b1 took the histograms 140 bins -> 50 for
suite-wide comparability, which **coarsens the delivered PDF**. The project's
own answer is in `tools/accumulator.py`: hold 1000 bins internally and sum down
to 50 only on export, so percentiles are not quantised to 2% of the range.
`coarse(s, n_out=...)` can emit any divisor of 1000. **Decide at M-b2** whether
motors should export a finer PDF alongside the comparable 50-bin one — it
becomes a parameter once the accumulator is in, rather than a code change.
| **M-c** | Year axis + the convergence curve, per-vehicle τ draw held across years | **M1–M4** |
| ~~**M-d**~~ | ~~Flow the year axis into `ElectricMotorElementMC`~~ | **CANCELLED 2026-08-12 — the model stays static, permanently.** Same decision and same reasoning as `SensorElementsMC` (`06_PCB_MODEL_DESIGN.md` §7.1): the **composition** of a motor in 2070 — how much copper, electrical steel, NdFeB, cast iron — is not forecastable, and a fitted curve would be a fabricated parameter. `10_`/the material sheets stay the **scenario lever**: edit them to explore a case rather than have the model assert a trajectory |

**What is and is not year-resolved for motors, after this decision:**

| | |
|---|---|
| **Motor COUNTS and MASS** (`ElectricMotorMC`) | **year-resolved** — M-c. Counts are forecastable: they follow feature content, and that trend is sourced (`09_AUX_MOTOR_ADOPTION_RESEARCH.md`) |
| **Element COMPOSITION** (`ElectricMotorElementMC`) | **static, by decision.** A 2025 snapshot, driven by whatever material split the user puts in the data |

This is a clean split rather than an inconsistency: *how many motors and how
heavy* has evidence behind it; *what they are made of in 2070* does not.
`ElectricMotorElementMC` outputs must be labelled a 2025 snapshot, exactly like
`SensorElementsMC`.

**Do `HIST_BINS = 140 → 50` as part of M-b**, not separately: it breaks the
project's histogram convention and propagates into `ElectricMotorElementMC`
(diagnostic §2). Changing it while already touching that code is cheaper than a
second pass, and M5 will catch any side effect.

---

## 7. What this design does NOT claim

- **35 of the 50 modelled years are extrapolation.** Every source stops at 2035.
  The curve past then is the *shape* argued in §2, not evidence.
- **No source gives a saturation ceiling.** §3.1's headroom is the substitute,
  and it is a judgement.
- **The mix is assumed static** (§4) and probably is not.
- **Integration is not modelled explicitly** — it is absorbed into headroom
  being modest rather than appearing as its own downward term.

**Expected magnitude: AB roughly +39%, EF roughly +14% by 2070.** If the result
is quoted, it must be quoted with §7 attached.


---

## 8. M-c DONE 2026-08-12 — and a pre-existing bug it exposed

**M1–M4 all pass.** `motor_counts_by_year.csv` written per segment per year.

| | 2025 → 2070 | design note predicted |
|---|---|---|
| AB | **+39.7%** | +38.8% |
| CD | **+28.5%** | +27.2% |
| EF | **+12.4%** | +11.7% |

M1 holds **exactly** (`reldiff 0.00e+00`), not to a tolerance: dividing the
convergence equation by `N_2025` gives `g(y) = h − (h−1)·exp(−(y−2025)/τ)`,
which contains no base count, so `g(2025) = 1` by construction. Mass follows the
same multiplier exactly because `05_`'s `Mass` sheet has no year dimension.

### 8.1 THE BUG — `sample_motor_counts` sums the segment pair

**Found by M-c, pre-existing, NOT introduced by it.**

`sample_motor_counts` adds segment A's rows **and** segment B's rows, so an "AB
vehicle" is credited with an A-segment car's motors *plus* a B-segment car's:

| group | A+B summed | averaged | model reports |
|---|---|---|---|
| AB | 29.0 | 14.5 | **28.07** |
| CD | 55.0 | 27.5 | **52.62** |
| EF | 117.5 | 58.8 | **111.83** |

**The external anchor decides it.** `09_AUX_MOTOR_ADOPTION_RESEARCH.md` §1 gives
all-motor content as **40–60 per vehicle, premium >80** (FACT). EF averaged
(58.8) lands inside. EF summed (111.8) is **nearly double the top of the premium
range** — not a plausible count for one car.

**Why it survived until now.** Nothing external had ever been compared against
the model's *output*. Yesterday's research corroborated `05_`'s **input** band
(EF 38–63 against 40–60) and that was taken as the model being sound. It
confirmed the input, not the output. **A cross-check that stops at the input
does not validate the model.**

**Fix, if approved:** average rather than sum in `sample_motor_counts`, i.e.
divide the pair total by the number of contributing segments. Roughly a
**2× reduction in every motor count and mass** the model reports, propagating
into `ElectricMotorElementMC` element masses.

**M-c is unaffected either way** — it is a multiplier on whatever base the model
produces, so the growth percentages above stand. Only the absolute level moves.

### 8.2 FIXED 2026-08-12

`sample_motor_counts` now **averages** across the segments in a group instead of
summing them. A segment group is one representative vehicle spanning A and B,
not two vehicles.

| | before | after | published band |
|---|---|---|---|
| AB | 28.07 | **14.03** | — |
| CD | 52.62 | **26.31** | — |
| **EF** | **111.83** | **55.91** | **40–60, premium >80** |

**EF now lands inside the independently published band.** Before the fix it sat
at nearly twice the top of the premium range.

**M1–M4 still all pass, and the growth percentages are IDENTICAL** — +39.7% /
+28.5% / +12.4%, unchanged to the decimal. That is not a coincidence but a
confirmation: `g(y)` contains no base count, so halving the base cannot move the
trajectory. The two results being bit-identical in percentage terms is the
cleanest available evidence that M-c and this bug were genuinely independent.

`ElectricMotorElementMC` re-run afterwards, since it resamples the changed
histograms. **Every motor mass and element mass this project has ever reported
was ~2× too high until this commit.**

---

## 9. KNOWN LIMITATION 2026-08-12 — Chinese-style EF interior content

**User's question, and it is a real gap:** Chinese EF-segment BEVs offer massage
in multiple seats, which implies a large number of motors. Is that captured?

**Largely no.**

- `12_` lists *"Seat ventilation/massage modules"* with EF medium-DC motors
  **`0.0–0.0`** — the component exists and is credited with **zero motors**.
  (`12_` is not the count basis, but nothing else counts massage seating either.)
- `05_` EF averages **58.8** motors (13.2 small stepper + 12.0 medium stepper +
  33.5 medium DC).

**Rough build-up for a four-massage-seat EF BEV:**

| | motors |
|---|---|
| front seats, full power adjust | 2 × 8–10 = 16–20 |
| rear executive seats | 2 × 6–8 = 12–16 |
| massage pumps / compressors | 2–4 |
| **seats alone** | ~~**~30–40**~~ **OVERSTATED — see `09_AUX_MOTOR_ADOPTION_RESEARCH.md` §8.1** |

> **Correction 2026-08-12.** This build-up counted massage *points* as motors.
> Massage is **pneumatic**: a "ten-point massage" is ten air bladders driven by
> **one** air pump, and solenoid valves are not motors. A massage seat adds
> roughly **one** motor. The real adders are **powered rear seats (8–16)** and
> **ventilation fans (4–8)**. Revised total: **~13–28 motors**, i.e. **+22% to
> +48%** on EF's base of 58.8 — which makes the EF headroom **Mode of 1.15 look
> low** and the **Max of 1.30 plausible**. See §8.4 of the research note.

Plus windows 4–6, mirrors 4–6, HVAC flaps 8–15, wipers 2–3, pumps 5–8,
tailgate 2–3, charge port. **That reaches 70–100+, above `05_`'s F range of
53–81 and well above the EF group average of 58.8.** DERIVED, order-of-magnitude.

### Where it bites: the EF headroom anchor, not the 2025 level

EF headroom is **1.05 / 1.15 / 1.30** — "near-saturated, little left to gain".
That reasoning rests on **European** fitment data: power seats and windows
already universal, liftgate >62% hands-free capable.

**It assumes the feature set is complete. Chinese premium interiors say it is
not** — massage, ventilation, powered rear seats and rear-entertainment
actuators are an additional layer on top. If those spread to Europe, EF's
remaining headroom exceeds 1.15 and **the Max of 1.30 may be too low.**

**This is structurally the same argument the user made about lidar**
(`ADAS_Sensor_Adoption_Report`): China leads, Europe follows, because Chinese
OEMs sell into Europe and European OEMs respond competitively. That argument was
right for lidar; the mechanism here is identical.

### Not changed, and why

The anchors are the **only invented numbers in the motor design**. Raising them
on a plausible argument rather than evidence would weaken exactly the property
that makes them reviewable. **Options, in preference order:**

1. **Research it** — massage/ventilated seat fitment in Chinese premium BEVs and
   their European launches. Bounded, like the power-liftgate search.
2. **Then raise the EF band** if the evidence supports it — e.g. Mode 1.15 →
   1.25, Max 1.30 → 1.60.
3. **Or leave it** and treat this section as the caveat on EF results.

**Status: recorded, not acted on.** EF motor growth of +12.4% to 2070 should be
read as *conditional on European feature content*, and is the figure most likely
to be revised upward.

---

## 10. DRIVER F — motor content SCENARIOS, 2026-08-12

**User: *"in situations like this, it might also be reflected in scenarios?"* —
yes, and it is the better mechanism, not an addition to the band.**

### 10.1 Why a band was the wrong shape

A triangular Min/Mode/Max says *"the truth lies in this range, most likely near
the mode"*. Correct for **measurement** uncertainty — does an EF car carry 55 or
60 motors?

Whether Chinese-style executive interiors become the European norm is **not**
measurement uncertainty. It is a **structural fork**: either they do or they do
not. Two worlds, not two points on a continuum.

Raising EF to a flat `1.15 / 1.35 / 1.60` made **1.35 the mode — a world nobody
expects**, the average of *Europe stays European* (~1.15) and *Europe adopts
Chinese content* (~1.50). No real fleet looks like that average.

**This is exactly what §2.2d of `06_PCB_MODEL_DESIGN.md` forbids for architecture:**

> *A vehicle is one design, never a blend. Share-weighting collapses a bimodal
> mixture into its mean and destroys the band.*

The flat raise applied to motors the error the project already rejects for
architecture. **Scenarios fix it.**

### 10.2 The scenarios — `20_` sheet `Motor_Scenarios`

| | weight | AB | CD | EF |
|---|---|---|---|---|
| **MS1 `European_Content`** | 0.40 | 1.25/1.40/1.60 | 1.15/1.28/1.45 | **1.05/1.12/1.22** |
| **MS2 `Chinese_Convergence`** | 0.35 | 1.35/1.55/1.85 | 1.30/1.48/1.70 | **1.30/1.45/1.65** |
| **MS3 `Cost_Constrained`** | 0.25 | 1.10/1.20/1.35 | 1.05/1.15/1.28 | **1.02/1.08/1.18** |

Weights sum to 1.000. Selected by `20_` `Control!B4` — **the same project-wide
cell the ADAS driver already uses**, so choosing a scenario once applies it
everywhere. `SAMPLE` draws per vehicle by weight; a name pins every vehicle.

**The gradient AB > CD > EF holds INSIDE every scenario**, not merely on the
weighted mean. M4 tests the mechanism, so satisfying it only on average would be
passing for the wrong reason.

### 10.3 Three draws per vehicle, all held across years

| | |
|---|---|
| **scenario** | which world this vehicle lives in |
| **h** | how much content its segment gains *in that world* |
| **τ** | how fast cost delivers it |

A vehicle sits on **one** trajectory in **one** world for its whole life.
Redrawing per year would average the fork away and return a smeared mean
matching no real fleet.

### 10.4 Result — M1–M4 all pass

| | 2025 | 2070 | |
|---|---|---|---|
| AB | 14.0 | 18.5 | **+31.6%** |
| CD | 26.3 | 32.8 | **+24.6%** |
| EF | 55.9 | 65.8 | **+17.8%** |

M1 exact (`0.00e+00`), M2 `18.5 < 65.8`, M3 within every band, M4 `32% > 25% >
18%`.

**EF's +17.8% is the weighted mixture of three coherent worlds**, sitting between
the European-only anchors (+12.4%) and the flat raise (+27.3%). The distribution
behind it is **bimodal, which is the truth** — not the smeared unimodal band the
flat raise produced.

### 10.5 How to use it

- **A specific study?** Pin `Control!B4` to `European_Content`,
  `Chinese_Convergence` or `Cost_Constrained` for one internally coherent world.
- **An overall view?** Leave it `SAMPLE`.
- **Disagree with the fork's likelihood?** The weights are in the sheet.

**Still ASSUMPTION.** The EF numbers rest on an adjustment-**axis** build-up —
one motor per "way" — not a fitment survey of European-market EF BEVs
(`09_AUX_MOTOR_ADOPTION_RESEARCH.md` §8). The scenario structure makes the
disagreement explicit rather than hiding it in a mode.
