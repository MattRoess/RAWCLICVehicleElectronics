# Methods — a scenario model of BEV electronics material content, 2020–2070

**Intended as the basis of a scientific publication.** It states the approach,
separates what was *measured* from what was *judged*, and lists every external
source.

---

## 1. Scope and research question

**How much material sits inside the electronics of a European battery-electric
passenger car, and how does that change to 2070?**

| in scope | out of scope |
|---|---|
| low- and high-voltage **wiring harness** | traction motor and battery cells |
| **printed circuit boards** and their elements | vehicle structure, glass, interior trim |
| **sensors** and their elements | manufacturing and use-phase energy |
| **auxiliary electric motors** — windows, seats, pumps, wipers | recycling and end of life |

Three size segments — **AB** (small), **CD** (medium), **EF** (large/luxury) —
following the European A–F convention, paired to keep sample sizes meaningful.

**Geography: Europe.** Where the strongest evidence is Chinese or US, that is
stated and treated as a leading indicator rather than a substitute.

---

## 2. Why a Monte Carlo scenario model

Component counts, board sizes and adoption rates are all uncertain, and the
uncertainties are **large — often larger than the trend being estimated**. A
deterministic model would hide that.

**Design principles, applied throughout:**

1. **Distributions, not point values.** Every input is `Min`/`Mode`/`Max` and is
   sampled. 200,000 vehicles per run.
2. **Discrete states, drawn once per vehicle and held across all years.** A
   vehicle is one design on one timeline for its whole life. Share-weighting a
   bimodal mixture would collapse it to a mean that describes no real vehicle.
3. **Structural forks become scenarios, not wider bands.** A band expresses
   *measurement* uncertainty. Whether a technology transition happens is a fork,
   and averaging two coherent futures produces a third that nobody expects.
4. **Every number is tagged FACT, DERIVED or ASSUMPTION**, and assumptions live
   in spreadsheets so they can be changed without touching code.
5. **Validation targets test mechanisms, not values.** The most useful checks
   assert that two models draw the same driver, or that a segment ordering
   cannot invert.

### 2.1 Calibrating disagreement

Sources disagree. We adopted an explicit scale, derived from observed spread
between published forecasts:

| spread | interpretation |
|---|---|
| ~3% | self-consistency floor — noise |
| ~1.6× | normal cross-house forecast disagreement |
| 3–4× | **structural** disagreement — different definitions |
| >10× | treat as an **error** and investigate |

This mattered in practice. Two auxiliary-motor sources differ **4×**; rather
than averaging, we identified a definition gap (BEV-specific auxiliaries versus
all body motors) and kept them separate.

---

## 3. Model structure

```
01_ component list ─┬─→ 11_ ─→ PCBAreaMC ─→ PCBElementMC ─┐
                    └─→ 12_ (diagnostic only)             │
05_ motor inventory ──→ ElectricMotorMC ──→ MotorElementMC┤
06_ sensor counts ────→ SensorNumbersMC ──→ SensorElemMC  ├─→ 30_ composition
17_ wiring baseline ──→ BevWiring ────────────────────────┘
18_/19_/20_ drivers ──→ (shared by all of the above)
```

**Four drivers, each a curve read from a spreadsheet:**

| driver | what it moves | source |
|---|---|---|
| **Voltage** 400 V → 800 V | power electronics consolidation | `18_` |
| **Architecture** conventional → domain → zonal | ECU count, harness length | `18_` |
| **ADAS hardware tier** H0–H4 | sensor counts | `19_` |
| **Motor content** | auxiliary motor counts | `20_`, `05_` |

Drivers are implemented **once**, in `tools/drivers.py`, and read by every model.
An early version had the same curve computed independently in two models; a
validation exists specifically to detect them drifting apart.

### 3.1 The ADAS axis is *installed hardware*, not certification level

A key methodological choice. Certification level (SAE L2/L3) is a poor predictor
of sensor content: a vehicle certified at L2 may carry **31 sensors**, while an
L3-certified vehicle carries **25**. We therefore key sensor content to an
**installed hardware tier (H0–H4)**, which is observable from specifications.

### 3.2 Renormalisation at the base year

Every driver is anchored so that **2025 reproduces the observed 2025 fleet**.
Applying an adoption curve from zero would double-count what has already
happened. This is the single most common failure mode we encountered.

### 3.3 What is *not* forecast, and why

**Composition — what a sensor or motor is made of — is held at 2025.** Counts
follow sourced feature trends; the material split inside a unit does not have a
defensible trajectory to 2070, and fitting one would introduce a fabricated
parameter at the centre of the model. Those files are exposed as **scenario
levers** instead.

---

## 4. Data provenance — what came from where

### 4.1 Curated inputs (project-generated, expert-assembled)

| file | content | how derived |
|---|---|---|
| `01_` | 101 electronic components, presence per segment on a four-level scale (Std/Opt/Rare/–) | expert assembly from teardowns and specifications |
| `03_` | PCB size classes | measurement |
| `04_`, `07_`, `10_` | element composition of PCBs, sensors, motors | literature and supplier data |
| `05_` | auxiliary motor counts and masses per segment | expert assembly |
| `17_` | 2025 wiring baseline | expert assembly |

**The four-level ordinal scale is a real limitation.** It cannot express a
presence of 0.137, so where a modelled value falls between two labels the
disagreement is **quantisation, not error**. Validations exempt those rows
explicitly rather than widening a tolerance until they pass.

### 4.2 Obtained from the internet (all FACT-tagged)

**Power electronics and 800 V**

- Creepage: 800 V DC at pollution degree 2, material group IIIa requires **8 mm**
  versus ~2.5–4 mm at 400 V; IEC 60664-1 relaxes this for PCBs, and CTI ≥600
  material nearly halves it.
- SiC: ~**3× smaller die area** at 750 V vs 1200 V; **3.5–8%** better efficiency
  than 400 V IGBT.
- Power density of integrated OBC + DC/DC: **1.5–2 kW/L (2018–20) → >5 kW/L**;
  one cited unit delivers 37.5 kW in 92 × 80 mm.
- Ratings rose in parallel: OBC **6.6 kW at 400 V → 11–22 kW at 800 V**.
- **Conclusion (DERIVED):** area *per kW* falls ~3×, but absolute area per
  vehicle is roughly flat (−33% to +10%). The real effect is **consolidation**.

**Architecture and ECU count**

- A premium 2020 vehicle carries **80–150 discrete ECUs**; a fully zonal
  architecture reduces this to **under 20**.
- VW SSP targets **ECUs down >50%, wiring down 40%** from 2026.
- Integrated inverter/OBC/DC-DC market **$2.82 bn (2024) → $12.08 bn (2033)**,
  17.6% CAGR; integrated OBC+DC/DC ~20% CAGR.

**Auxiliary motors**

- All motors per vehicle: **20–30 (2010) → 40–60 (2025)**, premium **>80**.
  BEV motor content **35–50** vs **20–30** for a comparable ICE vehicle.
- A narrower BEV-specific definition gives **10–15** auxiliaries, **~8 (2026) →
  12–14 (2035)**. The two differ ~4× — a **definition gap**, not an error.
- Power windows: **>95%** front-door fitment (saturated); **3.2 → 3.8** powered
  windows per car since 2018 → **~2.5%/yr and decelerating**.
- Power liftgate: compact/subcompact **~20% (2025) → >40% (2030)**; premium
  platforms **>62%** hands-free capable; EU **>85%** of new registrations by the
  early 2030s.
- E-latches: **10.7% CAGR** 2025–2033.
- Seat massage: **1.1%** of all Chinese vehicles but **49.0%** of the RMB
  200,000–350,000 band; seat heating front/second row **7.8% / 3.9%** (2023).
- **Massage is pneumatic** — a "ten-point massage" is ten air bladders driven by
  **one** pump. Solenoid valves are not motors. This correction reduced an
  earlier estimate of the effect by roughly an order of magnitude.
- Smart motors with integrated electronics carry a **25–40% price premium**.

**Evidence classes.** Following the project's own convention: *primary* sources
that count things (teardowns, component censuses) outrank *technology-led*
analyst reports, which outrank *modelled top-down* market-size reports. Most
market reports above are top-down: **their growth ratios are informative, their
absolute values weak.** Where an absolute value was used it was used only to
corroborate a number the project already had.

### 4.3 Where judgment was used — the complete list

**These are the model's ASSUMPTIONS. Everything else derives from §4.1 or §4.2.**

| # | judgment | magnitude | basis |
|---|---|---|---|
| J1 | Which components exist in each architecture state (BCM, domain controllers, zone controller) | 7 components, 8.2% of PCB area | `01_` component names map one-to-one onto the three states |
| J2 | ABS/ESC survives in a zonal architecture | ~1.3% of EF area | braking is safety-critical with its own hardware |
| J3 | ADAS domain controller persists into zonal | ~1.3% | avoids double-counting the tier driver |
| J4 | Architecture transition timing spread | σ = **5 years** per vehicle | inherited from the wiring model |
| J5 | Label quantisation is triangular, peaked at the recorded label | ±0.125 bin | uniform was tried and biased `Std` down 12.5% |
| J6 | Motor headroom per segment | AB 1.25–1.85, EF 1.02–1.65 by scenario | fitment trends in §4.2 |
| J7 | Motor cost-down time constant τ | **20/30/50 years** | no direct source |
| J8 | Motor type mix held constant | affects mass, not counts | growth features are mostly DC, but nothing quantifies the shift |
| J9 | Scenario weights | 0.40 / 0.35 / 0.25 | judgment about relative likelihood |
| J10 | Composition frozen at 2025 | sensors and motors | **deliberate** — see §3.3 |

**J7 and J9 are the weakest.** Neither has a direct source. Both are exposed in
spreadsheets and both are single-parameter sensitivities.

---

## 5. Principal results

**Material per vehicle, 2025 (grams):**

| | AB | CD | EF |
|---|---|---|---|
| Auxiliary motors | 23,393 | 45,573 | 95,791 |
| Wiring (Cu) | 33,933 | 56,168 | 75,736 |
| PCB elements | 483 | 617 | 715 |
| Sensor elements | 113 | 168 | 212 |
| **Total** | **57.9 kg** | **102.5 kg** | **172.5 kg** |

**Change to 2070: AB −13.6%, CD −10.1%, EF −0.5%.**

**The mechanism is a partial cancellation.** Wiring copper falls as zonal
architecture shortens the harness; auxiliary motor content rises with feature
adoption (**AB +31.6%, CD +24.6%, EF +17.8%**). Small cars see the largest net
decline because their wiring reduction is proportionally larger and their motor
base smaller.

**Counter-intuitive but robust: the segment gradient for motors is the reverse
of that for driver assistance.** ADAS diffuses downward from a premium frontier;
auxiliary motors are a feature set that large cars have largely completed and
small cars are still acquiring.

---

## 6. Limitations — stated plainly

1. **The largest single effect is unquantified.** Zonal consolidation could
   touch ~50.7% of PCB area; only 8.2% is modelled, because per-component
   consolidation depth is not documented anywhere. **PCB results move only a few
   percent for that reason, and must not be read as evidence that circuit-board
   material demand is flat.**
2. **35 of the 50 motor years are extrapolation.** Every source stops at 2035.
3. **Composition is frozen at 2025** by design (§3.3).
4. **Motor anchors rest on an adjustment-axis build-up** — one motor per powered
   "way" — not a fitment survey of European-market vehicles.
5. **Sensor element mass scales with count, not with sensor design.** A future
   lidar may be nothing like a 2025 lidar.
6. **The four-level presence scale limits resolution** to ~0.25 (§4.1).
7. **Europe only.** Chinese evidence is used as a leading indicator, explicitly.

---

## 7. Reproducibility

All models are seeded (`seed = 42`) and deterministic. Inputs are spreadsheets;
scenario selection is a single cell (`20_` `Control!B4`). `docs/USER_GUIDE.md`
gives the run order. Validation suites (V1–V15, P1–P5, M1–M5) run automatically
and print PASS/FAIL.

**Two methodological cautions we learned the hard way, offered as
generalisable:**

- **A cross-check that stops at the input does not validate the model.** A
  published figure was compared against an input file and read as corroboration;
  a factor-two error in the model's output survived that check.
- **Widening a band to accommodate a structural disagreement produces a mode
  that describes no real case.** Use scenarios.

---

## 8. References

**Power electronics**

1. STMicroelectronics — SiC traction inverter, die area and efficiency, APEC 2020.
   <https://www.st.com/content/dam/AME/2020/apec-2020/presentations/APEC2020_Traction-Inverter-virtual-FINAL2.pdf>
2. IEC 60664-1 — insulation coordination, creepage and clearance.

**Auxiliary motors and comfort features**

3. IndexBox — automotive micro DC motors, forecast to 2035.
   <https://www.indexbox.io/blog/automotive-micro-dc-motors-market-forecast-points-higher-toward-2035-driven-by-vehicle-electrification-and-feature-proliferation/>
4. IndexBox — EU automotive auxiliary motors market.
   <https://www.indexbox.io/store/european-union-automotive-auxiliary-motors-market-analysis-forecast-size-trends-and-insights/>
5. Fortune Business Insights — power tailgate system market.
   <https://www.fortunebusinessinsights.com/power-tailgate-system-market-109861>
6. Market Data Forecast — Europe tailgate market.
   <https://www.marketdataforecast.com/market-reports/europe-tailgate-market>
7. Dataintelo — automotive e-latch market.
   <https://dataintelo.com/report/automotive-elatch-market>
8. Research in China / PRNewswire — automotive comfort system report 2024, seat
   function penetration.
   <https://www.prnewswire.com/news-releases/global-and-china-automotive-comfort-system-seating-system-air-conditioning-system-research-report-2024-the-penetration-of-comfort-functions-rises-and-zero-gravity-seats-usher-in-a-boom-period-302089333.html>
9. Li Auto — standard seat specification.
   <https://www.liauto.com/L6>
10. PlasticsToday — electro-active polymers as an alternative to mechanical
    massage seating.
    <https://www.plasticstoday.com/automotive-mobility/electro-active-polymers-offer-alternative-to-mechanical-massaging-in-car-seats>

**Driver assistance** — see `ADAS_Sensor_Adoption_Report_2025_2070.md`, which
carries its own reference list and defines the uncertainty calibration in §1.2.

**Internal documents** — `MODEL_STATUS.md` (status and how to quote results),
`PCB_MODEL_DESIGN.md`, `MOTOR_MODEL_DESIGN.md`,
`AUX_MOTOR_ADOPTION_RESEARCH.md`, `MOTOR_MODEL_DIAGNOSTIC.md`,
`STATIC_MODELS_DIAGNOSTIC.md`.
