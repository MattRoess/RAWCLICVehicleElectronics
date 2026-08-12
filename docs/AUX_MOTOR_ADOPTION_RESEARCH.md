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

---

## 7. SECOND PASS 2026-08-11 — the ceiling and the counter-trend

Two user judgements set the direction here, and the evidence supports both.

> *"I think it is not so dynamic."*
> *"It will be controlled by costs for AB and CD."*

### 7.1 The 4.7%/yr headline must NOT be carried forward

**Power windows are the test case, because they are a mature motor-bearing
feature with published fitment data:**

| | | tag |
|---|---|---|
| Front-door power windows, EU (Spain) | **>95% of new cars — saturated** | FACT |
| Powered windows per car | **3.2 (2018) → 3.8 (2025)** | FACT |
| implied rate | **~+2.5%/yr, and decelerating** | DERIVED |

**That is roughly half the 4.7%/yr headline** — and it is the *right* half to
believe for the future. The 2010→2025 figure covers a wave of feature
introduction that is now largely complete: growth has moved from *adding the
feature* (front windows, 0→95%) to *extending it* (rear and quarter windows),
which is a smaller and self-limiting increment.

**This corroborates the user's "not so dynamic" judgement with numbers.**
DERIVED. A model built on 4.7%/yr would overstate 2070 motor content
substantially; ~2.5%/yr decaying toward zero is the defensible shape.

### 7.2 The ceiling is a cost ceiling for AB and CD, not a technical one

**User's judgement, and it resolves what the market reports could not.** No
source gives a technical maximum motor count, and looking for one was the wrong
search: **nothing physically prevents an AB car from carrying EF's motor
content — price does.**

Supporting evidence:

| | | tag |
|---|---|---|
| Smart motors (integrated electronics, anti-pinch) | **25–40% price premium** over conventional geared assemblies | FACT |
| their share of OEM-sourced motors by value, 2026 | 15–20% | FACT |
| Power liftgate, compact/subcompact | ~20% (2025) → >40% (2030) | FACT |
| Power liftgate, premium | already >62% hands-free capable | FACT |

**The compact curve is a cost-down curve, not a capability curve.** Premium
adopts at launch; AB and CD adopt as unit cost falls. So the ceiling for AB/CD
is set by **content cost per vehicle**, and EF functions as the practical upper
bound AB/CD converge toward — slowly, and never fully within the model horizon.

**This is a better-founded structure than an invented numeric ceiling**, and it
uses a quantity the model already has: EF's own motor count.

### 7.3 The integration counter-trend is real but weakly evidenced

Searching for it returned **patents, not fitment data** — multifunction and
multi-input actuators (US 6,075,298; 6,107,759; 12,054,021), one motor driving
locks plus windows plus wipers. The stated motivation is consistent and
credible: *"the traditional need for such a multiplicity of electromagnetic
devices has increased vehicle weight and cost while proving difficult to package
in small spaces."* FACT (as a statement of intent).

**But patents show intent, not deployment**, and this idea recurs across
decades. If it were materially reducing motor counts it would appear in fitment
statistics, and it does not — the measured direction is still upward
(3.2→3.8 windows/car). **ASSUMPTION:** integration currently offsets rather than
reverses growth, and belongs in the model as a downward pressure on the *rate*,
not as a decline.

### 7.4 Where this leaves the driver

**Now defensible, without inventing a parameter:**

| | |
|---|---|
| near-term rate | **~2.5%/yr**, from saturating-feature evidence, not 4.7% |
| shape | decelerating — feature *introduction* is giving way to feature *extension* |
| AB / CD ceiling | **cost-driven convergence toward EF content**, EF as the practical bound |
| EF | near-saturated already; slowest growth |
| integration | a brake on the rate, not a reversal |

**Still missing:** anything past 2035 (35 of 50 modelled years remain
extrapolation), the stepper/DC mix shift, and a quantified cost-elasticity for
the AB/CD convergence. The last of these is now the binding gap — the structure
is right, the speed is not yet pinned.

**Assessment:** this is close to buildable. The remaining choice — how fast
AB/CD converge on EF — is a scenario parameter with a defensible band rather
than a fabricated point value, which is exactly what the project's
`Share_Min/Mode/Max` convention exists to carry.

---

## 8. THIRD PASS 2026-08-12 — Chinese EF interior content

**User's question:** Chinese EF-segment BEVs offer massage in multiple seats, so
do they carry many more motors than `05_` assumes?

**Answer: yes, but far less than a naive count suggests — and the first estimate
made in this project was wrong.**

### 8.1 The correction — massage is PNEUMATIC

**FACT.** A pneumatic massage system is *one air pump* plus a valve device
feeding a matrix of air bladders. Li Auto's *"SPA-level ten-point massage"* means
**ten air pockets, not ten motors**. Solenoid valves are not motors. A fluidic
switching module can serve several bladders — and in some designs several seats —
from a single pump.

**So a 10-point massage seat adds roughly ONE motor, not ten.**

**`MOTOR_MODEL_DESIGN.md` §9's build-up — "seats alone ~30–40 motors" —
overstated this** by treating massage points as motors. Corrected here.
Electro-active polymer alternatives are emerging and are also not motors.

### 8.2 What Chinese interiors *do* add, motor by motor

| feature | motors added | is it a motor? |
|---|---|---|
| **Powered rear seats** (recline, legrest, zero-gravity) | 2 seats × 4–8 = **8–16** | **yes — the dominant term** |
| **Seat ventilation** | 1–2 fans per seat × 4 = **4–8** | **yes** |
| Massage | 1 pump per seat, sometimes shared = **1–4** | yes, but few |
| Seat heating | 0 | no — resistive |
| Massage "points"/bladders | 0 | no — pneumatic valves |

**Realistic addition for a fully-equipped Chinese-style EF interior: ~13–28
motors** on a base of 58.8. DERIVED.

### 8.3 Fitment — high in the relevant price band, low overall

| | rate | tag |
|---|---|---|
| Seat massage, **all** Chinese vehicles (2023) | **1.1%** | FACT |
| Seat massage, **RMB 200,000–350,000 models** | **49.0%** | FACT |
| Seat heating, front row / second row (2023) | 7.8% / 3.9% | FACT |
| Third-row seat heating | mainstream since 2022 (Li L8/L9, NIO ES8) | FACT |
| Li Auto standard fit | 4-seat ventilation, 10-point front massage | FACT |
| Massage-seat market growth | **>10% CAGR** | FACT |

**The 1.1% headline is the wrong comparator** — it averages over the whole
Chinese fleet including cheap cars. **49% in the RMB 200k–350k band (~€25–45k)**
is the number that matters, and that band is *below* EF pricing, so EF-class
fitment is higher still.

### 8.4 Effect on the EF headroom anchor

Adding **13–28 motors** to a base of **58.8** is **+22% to +48%**.

| EF headroom | value | verdict |
|---|---|---|
| Min | 1.05 | **too low** if this content arrives at all |
| **Mode** | **1.15** | **arguably low** — sits under the +22% floor |
| Max | 1.30 | **plausible**, mid-range of the estimate |

**Conclusion: the anchors are defensible but the band sits low.** The honest
reading is that EF's **Mode** should probably move up toward 1.25 and the **Max**
toward 1.45–1.50, which would put the estimate range inside the band rather than
straddling its top.

**Still an ASSUMPTION either way** — this is an order-of-magnitude build-up from
component counts, not a fitment survey of European-market EF BEVs. **Not
changed. The anchors live in `05_` sheet `Motor_Growth`; §8.4 is the argument for
changing them if the user chooses.**

### 8.5 Sources

- Research in China / PRNewswire — automotive comfort system report 2024, seat
  function penetration:
  <https://www.prnewswire.com/news-releases/global-and-china-automotive-comfort-system-seating-system-air-conditioning-system-research-report-2024-the-penetration-of-comfort-functions-rises-and-zero-gravity-seats-usher-in-a-boom-period-302089333.html>
- Li Auto official — standard seat specification:
  <https://www.liauto.com/L6>
- PlasticsToday — electro-active polymers vs mechanical massage:
  <https://www.plasticstoday.com/automotive-mobility/electro-active-polymers-offer-alternative-to-mechanical-massaging-in-car-seats>
