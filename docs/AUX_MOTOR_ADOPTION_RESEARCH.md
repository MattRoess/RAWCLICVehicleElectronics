# Auxiliary motor content, 2025–2070 — research note

**Started 2026-08-11. First pass — enough to size the driver, not yet enough to
build it.** Nothing here is implemented.

**Purpose.** `ElectricMotorMC` has no year axis, and
`MOTOR_MODEL_DIAGNOSTIC.md` §6 established that a sourced feature-content trend
is the prerequisite. This is that trend.

**Scope.** Auxiliary motors — window lifts, seats, pumps, wipers, tailgate,
mirrors. **Not the traction powertrain** (`PCB_MODEL_DESIGN.md` §8).

Tagging follows the project convention: **FACT** (sourced), **DERIVED**
(computed here), **ASSUMPTION** (judgement).

---

## 1. How many auxiliary motors a car has today

| | count | tag |
|---|---|---|
| All motors per vehicle, 2010 | 20–30 | FACT |
| All motors per vehicle, **2025** | **40–60** | FACT |
| Premium models, 2025 | **>80** | FACT |
| **BEV** motor content | **35–50** | FACT |
| ICE equivalent | 20–30 | FACT |

**A second source uses a much narrower definition** — "a typical BEV
incorporates 10–15 auxiliary motors against 6–8 in an ICE vehicle", and
"approximately 8 in 2026 rising to 12–14 by 2035". FACT.

**These differ by roughly 4×, and that is a definition gap, not an error.** The
narrow count is clearly *BEV-specific* auxiliaries (thermal management, ADAS
actuation); the broad count includes every body-comfort motor. The project's
calibration puts 3–4× at "structural disagreement" and >10× at "error"
(`ADAS_Sensor_Adoption_Report` §1.2), so this sits exactly on the structural
boundary. **Both are usable provided they are never mixed.**

### Cross-check against `05_` — the model's own numbers are sound

| segment | `05_` total, 2025 | broad-definition anchor |
|---|---|---|
| AB | 10–14 | — |
| CD | 18–29 | — |
| **EF** | **38–63** | **40–60, premium >80** |

**`05_`'s EF band lands squarely on the independent 2025 figure.** DERIVED.
This is the first external corroboration `05_` has had, and it means the
model's absolute level is not in question — only its time behaviour.

`05_` therefore matches the **broad** definition. The narrow 8→12–14 series
must not be used with it.

---

## 2. The growth rate

| basis | period | implied rate |
|---|---|---|
| 20–30 → 40–60 all motors | 2010 → 2025 | **~4.7%/yr** DERIVED |
| ~8 → 12–14 narrow auxiliaries | 2026 → 2035 | **~4.6–6.3%/yr** DERIVED |

**Two independent definitions give the same growth rate to within noise**, even
though their absolute levels differ 4×. That is a much stronger result than
either figure alone: **the trend is better constrained than the level.**

**It cannot continue at 4.7%/yr to 2070.** Compounded over 45 years that is
8×, i.e. 300–500 motors per car. The curve must saturate — which is the whole
modelling question, and §4 is where the evidence runs out.

---

## 3. The segment gradient — premium-first, and it is measurable

Power liftgate, the best-documented single feature:

| | 2025 | 2030 | tag |
|---|---|---|---|
| **Compact / subcompact** | **~20%** | **>40%** | FACT |
| EU, all new registrations | — | **>85% by early 2030s** | FACT |
| Premium platforms, hands-free capable | **>62%** | — | FACT |

E-latches (electric door releases): **10.7% CAGR 2025–2033**. FACT.

**The compact segment doubles while premium is already saturating.** DERIVED.

**This confirms the prediction made before any research** (`MOTOR_MODEL_DIAGNOSTIC.md`
§3): **AB grows fastest, EF slowest** — the *opposite* of the ADAS tier
gradient, where EF leads. The mechanism is different: ADAS is capability
diffusing downward from a frontier, auxiliary motors are a feature set EF has
largely completed and AB is still acquiring.

Recorded so the result is not later mistaken for an error.

---

## 4. What is still missing before this can be built

1. **The saturation ceiling.** No source gives a maximum plausible auxiliary
   motor count per vehicle. Without it the curve shape past ~2035 is invented.
   This is the single biggest gap.
2. **Counter-trend: motor *reduction*.** §3 of the diagnostic lists integration
   (one multi-function actuator replacing two) and the loss of ICE-specific
   motors. Nothing sourced quantifies it. If real it flattens the curve
   materially.
3. **Nothing beyond 2035.** Every source stops there. 2035–2070 — **35 of the
   model's 50 years** — would be extrapolation, and must be labelled as such.
4. **Europe-specific segment data.** The premium hands-free figures are
   US-based; the compact liftgate series is not clearly EU-only.
5. **Per-motor-type splits.** `ElectricMotorMC` samples stepper vs DC separately
   with different masses, so a single aggregate growth rate cannot drive it
   without an assumption about how the mix shifts.

---

## 5. Honest status

**Enough to size the driver, not enough to build it.** What is now established:

- `05_`'s 2025 level is externally corroborated (EF)
- growth is ~4.7%/yr recently, agreed by two independent definitions
- the segment gradient is premium-first and AB-fastest, with numbers

What is not:

- the saturation ceiling, which governs 35 of the 50 modelled years
- the integration counter-trend
- the stepper/DC mix shift

**Recommendation:** do not implement a motor year axis on this alone. A curve
fitted to 4.7%/yr with an invented ceiling would put a fabricated parameter at
the centre of the model — the thing this project has repeatedly refused. The
next step is targeted work on the ceiling and the counter-trend, not code.

---

## 6. Sources

- IndexBox — automotive micro DC motors, forecast to 2035:
  <https://www.indexbox.io/blog/automotive-micro-dc-motors-market-forecast-points-higher-toward-2035-driven-by-vehicle-electrification-and-feature-proliferation/>
- IndexBox — EU automotive auxiliary motors market:
  <https://www.indexbox.io/store/european-union-automotive-auxiliary-motors-market-analysis-forecast-size-trends-and-insights/>
- Fortune Business Insights — power tailgate system market:
  <https://www.fortunebusinessinsights.com/power-tailgate-system-market-109861>
- Dataintelo — automotive e-latch market:
  <https://dataintelo.com/report/automotive-elatch-market>
- Market Data Forecast — Europe tailgate market:
  <https://www.marketdataforecast.com/market-reports/europe-tailgate-market>

**Evidence class** (`ADAS_Sensor_Adoption_Report` §1.2): these are **modelled
top-down** market reports. Growth ratios are informative; absolute values are
weak. The `05_` cross-check in §1 is the one place an absolute figure was used,
and it was used only to corroborate a number the project already had.
