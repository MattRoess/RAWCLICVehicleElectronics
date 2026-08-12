# Auxiliary motors — design note (year axis)

**Written 2026-08-11. M-a is done; M-b to M-d are not implemented.**

> **Sheet-addition safety, recorded because it went wrong once.** Adding a
> `Notes` sheet to `01_` on 2026-08-09 broke *both* sensor models — their
> readers apply fixed `usecols` to every sheet. `ElectricMotorMC` was checked
> *before* writing rather than assumed safe: it filters with
> `if sh in KNOWN_MAT_SHEETS`, so an unrecognised sheet is skipped. `05_` has
> exactly one reader. Verified after the fact by a full re-run.

Companions: `MOTOR_MODEL_DIAGNOSTIC.md` (what is broken today),
`AUX_MOTOR_ADOPTION_RESEARCH.md` (the evidence), `PCB_MODEL_DESIGN.md` (the
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
| ~~**M-d**~~ | ~~Flow the year axis into `ElectricMotorElementMC`~~ | **CANCELLED 2026-08-12 — the model stays static, permanently.** Same decision and same reasoning as `SensorElementsMC` (`PCB_MODEL_DESIGN.md` §7.1): the **composition** of a motor in 2070 — how much copper, electrical steel, NdFeB, cast iron — is not forecastable, and a fitted curve would be a fabricated parameter. `10_`/the material sheets stay the **scenario lever**: edit them to explore a case rather than have the model assert a trajectory |

**What is and is not year-resolved for motors, after this decision:**

| | |
|---|---|
| **Motor COUNTS and MASS** (`ElectricMotorMC`) | **year-resolved** — M-c. Counts are forecastable: they follow feature content, and that trend is sourced (`AUX_MOTOR_ADOPTION_RESEARCH.md`) |
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
