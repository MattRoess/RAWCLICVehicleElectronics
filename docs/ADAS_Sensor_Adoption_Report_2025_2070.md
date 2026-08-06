# ADAS sensor adoption, 2025–2070

**Purpose.** Supply the sensor-adoption basis for two models that currently
disagree about what drives sensor content:

- `Wiring/BevWiring.py` — reads `18_` sheet `Sensors_per_Level`, keyed on **SAE
  certification level**, entirely unsourced, supplying ~22–24% of the 2070 answer.
- `SensorNumbersMC/SensorNumbersMC.py` — reads `01_` and `06_`, keyed on a
  **static** Std/Opt/Rare presence factor with **no time and no level dimension
  at all**.

This report replaces both keys with three explicit drivers —

| | Driver | Sheet in `19_` | Why separate |
|---|---|---|---|
| **A** | ADAS hardware tier | `Tier_Shares` | wiring follows installed hardware, not the certificate (§1, §3) |
| **B** | lidar penetration | `Lidar` | tracks cost and Chinese competitive pressure, not tier or certification (§5) |
| **C** | post-2040 sensor-count scenario | `Scenarios` | removes the need to forecast unknown modalities (§7.2) |

— and states the extrapolation rules that carry the sourced data (which ends
~2035) out to 2070.

Written 2026-08-05. Companion to `Wiring/AUTONOMY_LEVELS_VS_HARDWARE.md`,
`Wiring/BevWiring_STATUS.md`, `SensorNumbersMC/SENSOR_WIRING_INTERFACE.md`.

---

## 1. Method — how to read every number here

Every value carries one of three tags. **Nothing is untagged.**

| Tag | Meaning | How to challenge it |
|---|---|---|
| **FACT** | observed, sourced, dated | check the source in §10 |
| **DERIVED** | computed from FACTs by a stated rule | check the rule |
| **ASSUMPTION** | judgment; no source exists | argue with the reasoning given |

This mirrors the yellow / orange / green convention already used in `17_` and
`18_`. The point is that the 2070 answer is mostly ASSUMPTION propagated through
DERIVED rules, and that must be visible rather than buried.

**Central principle of this report:** where credible sources disagree, the
disagreement is preserved as a *band*, not resolved by picking a side. This is a
Monte Carlo model; contested inputs belong in the distribution.

### 1.1 These are predictions, not ground truth

Everything past 2026 in this document is a forecast, and forecasts about
technology adoption 45 years out are wrong in ways that cannot be quantified
from inside the forecast. Two working rules follow.

**Rule 1 — a mismatch inside the observed spread is not an error.**
Before calling any disagreement a bug, check it against §1.2. Several numbers in
this project have been treated as errors when they sit comfortably inside the
range that credible sources already disagree by.

**Rule 2 — use the disagreements to size the bands.**
Where two credible sources give different values for the *same* quantity, that
gap is a **measurement** of the real uncertainty. It is the only empirical
handle available on band width in a chain where most inputs have a single
source or none. Band widths in §4.2, §5.3 and §7 are set from §1.2, not invented.

### 1.2 Uncertainty measured from source disagreement

| Quantity | Source A | A | Source B | B | Spread |
|---|---|---|---|---|---|
| L2+/L3 share of global new sales, 2035 | S&P Global Mobility | ≥31% | IDTechEx | >50% | **1.6×** |
| Ranging sensors per vehicle, 2035 | Yole | 5.5 | this report §4.1 | 4.6 | 1.20× |
| AB→EF adoption lag | `18_` offsets | 10 y | this report §4.1 | 15 y | 5 y |
| CD copper per vehicle, 2025 | model, length-first | 56.4 kg | source report, stated | 60.3 kg | 6.9% |
| **EF wiring length, 2025** | report row sum | 3646 m | **same report**, stated total | 3546 m | **2.8%** |
| SDV total length reduction | `17_` per-category mechanisms | −12/−11/−8% | `17_` stated totals | −44/−40/−23% | **3–4×** |
| EF cameras, 2025 | `06_` max | 5 | measured EQS / EX90 | 6 / 10 | 2× |
| EF lidar presence, 2025 | `01_` label "Opt" | 0.50 | measured + Driver B | 0.01 | **50×** |
| Europe lidar share, 2070 | this report Min | 0.25 | this report Max | 0.90 | 3.6× |
| Global ADAS market size, 2025 | Polaris | $39.32 bn | NextMSC | $34.2 bn | 1.15× |
| L2+ share, 2035 | NextMSC (**revenue**) | 25.2% | Yano (**units**) | 37.9% | 1.50× |
| H2+H3 / L2+ share, 2025 | this report §4.1 | 40.5% | Yano units | 12.4% | 3.3× |

**A note on evidence class.** The sources above are not equally strong, and
mixing them without saying so would be a mistake:

| Class | Sources | Basis |
|---|---|---|
| **Primary — counts things** | Yole, Yano Research, S&P Global Mobility | shipment counts, installation counts, model-level fitment tracking |
| **Technology-led** | IDTechEx, SBD, Counterpoint | component and roadmap analysis, mixed primary/modelled |
| **Modelled top-down** | Polaris, NextMSC, Fortune Business Insights, and similar | market sizing derived from growth assumptions; internally consistent by construction, which is not the same as accurate |

The third class disagrees with itself by ~1.15× on the *current* market size —
a quantity that is in principle observable today. Treat its **segmentation and
growth ratios** as informative and its **absolute values** as weak.

**What this calibrates:**

| Kind of uncertainty | Magnitude | Consequence |
|---|---|---|
| **Self-consistency floor** | **~3%** | A single source disagrees *with itself* by 2.8–6.9%. **No result from this chain can claim better precision than that**, however many Monte Carlo iterations are run. 200,000 iterations buy sampling precision, not accuracy |
| **Cross-house forecast spread, 10 y out** | **~1.6×** | Two top-tier analyst houses, same quantity, same year. Any single-source forecast band narrower than this is over-confident |
| **Structural / mechanism uncertainty** | **3–4×** | SDV depth, lidar 2070. Where the *mechanism* is contested rather than the value, spreads are multiples, not percentages |
| **Threshold for calling something an error** | **>10×** | Below that, assume it is within range and say so. `01_` lidar at 50× clears it. `06_` cameras at 2× **does not** — that is normal disagreement, not a defect |

Two consequences worth stating plainly:

- The **−8% CD copper gap** (`BevWiring_STATUS.md` §7) sits inside the 6.9%
  self-consistency band of its own source. It has been recorded as "a finding,
  not a bug" — §1.2 supports that reading and puts a number on it.
- The `06_` **camera shortfall** flagged in §2.3 is a 2× disagreement, which is
  ordinary. Update the counts, but do not treat the file as broken.

---

## 2. Fact base

### 2.1 The certification / hardware split — FACT

| Observation | Date | Source |
|---|---|---|
| Certified L3 sold only on Mercedes S-Class/EQS and BMW 7 Series/i7 — both F-segment | 2021–2026 | §10.1 |
| Mercedes pauses Drive Pilot; 2026 S-Class gets "L2++" MB.Drive Assist Pro | 2026 | §10.1 |
| BMW discontinues Personal Pilot L3 at the 7 Series facelift | Apr 2026 | §10.1 |
| BMW replacement: L2 Motorway Assistant, hands-off to 130 km/h, €6,000 → €1,450 | 2026 | §10.1 |
| Volvo removes lidar from EX90, ES90, Polestar 3 — **supplier (Luminar) liquidated**, "limited supply of the LiDAR hardware" | MY2026 | §10.1 |
| No top-10 European BEV exceeds L2 | Feb 2026 | §10.2 |
| EU GSR-2 mandates front camera + AEB on every new registration | since Jul 2024 | §10.4 |

**Read this correctly.** The withdrawals are of *certification*, not of hardware.
BMW's replacement is hands-off to 130 km/h — a **wider** operational envelope
than the L3 system it replaced, at a quarter of the price. Capability rose;
the certificate was dropped.

### 2.2 Measured sensor counts, EF segment — FACT

| EF car | Cameras | Radar | Lidar | Ultrasonic | Total | Certified |
|---|---|---|---|---|---|---|
| Mercedes S-Class / EQS, Drive Pilot | 6 | 5 | 1 | 13 | >35 | **L3** |
| BMW 7 Series / i7, Personal Pilot L3 | n/s | n/s | 1 | 12 | 25 | **L3** |
| Volvo EX90, MY2026 | 8 ext + 2 int | 5 | **0** | 16 | 31 | **L2** |

The Volvo has more total sensors than the L3-certified BMW and is certified L2.
**This single row is why the axis has to change.**

### 2.3 `06_` already agrees with reality better than anyone thought — FACT

Cross-checking `06_VehicleSensorNumbers.xlsx` EF maxima against §2.2:

| Sensor | `06_` EF max | EQS | i7 | EX90 | verdict |
|---|---|---|---|---|---|
| Radar (RF transceiver) | 1 front + 4 corner = **5** | 5 | n/s | 5 | **exact** |
| Lidar | **0–1** | 1 | 1 | 0 | **exact** |
| Ultrasonic | 8–**12** | 13 | 12 | 16 | within 0–4 |
| Cameras (CMOS) | **5** | 6 | n/s | 10 | **low by 1–5** |

`06_`'s EF radar and lidar counts reproduce three independently measured 2025–26
flagships exactly. It needs a **time and tier dimension and a camera-count
update** — not a rebuild.

> **CORRECTION to `SENSOR_WIRING_INTERFACE.md` §5 and `18_` sheet `Notes`.**
> Both state that `06_` has *"NO radar and NO lidar rows at all."* **That is
> wrong.** The rows exist — as components *Front long-range radar*, *Corner
> short/mid-range radars* and *LiDAR sensor* — but their `SensorType` values are
> the physical parts (`RF transceiver`, `laser diode array`, `photodetector
> array`, `IMU`), not the words "radar" and "lidar". The gap was a naming
> mismatch, not missing data. Both documents must be corrected.

### 2.4 Lidar — FACT

| Observation | Value | Date |
|---|---|---|
| Long-range lidar unit price, China | **~$4,100 → $150–200** | 2017 → 2026 |
| Cost reduction over 8 years | **99.5%** | 2026 |
| Hesai ATX price / status | **$200**, mass production | since 2025 |
| **Lidar penetration, Chinese NEVs** | **21%** — past the 16% "chasm threshold" | 2025 |
| Global automotive lidar market | **>$1 bn, +60% YoY** | 2025 |
| Passenger-vehicle lidar units | **3.7 m** (≈3.1 m primary ADAS) | 2025 |
| Chinese share of global lidar supply | **~95%** (Hesai 43%) | 2025 |
| Lidar on an A-segment car | BYD Seagull, ~$10,300 | 2026 |
| Overseas ADAS lidar shipments forecast | 3 m units by 2030 | Goldman Sachs |
| Automotive lidar market forecast | $25.75 bn by 2035 | Astute Analytica |

### 2.5 Weather performance — FACT (peer-reviewed)

4D mmWave radar is **minimally affected** by fog, rain and snow — its wavelength
greatly exceeds the particle size. **Lidar and cameras degrade moderate-to-severe**;
lidar-camera perception collapses in fog from backscatter. Weather-robust
configurations are lidar **+** 4D radar, or radar substituting for lidar.

**Consequence for the European-climate argument:** adverse weather does *not*
single out lidar. It argues for **more sensors of more types** — which raises
wiring under either sensing strategy. This makes the wiring conclusion robust to
the lidar question, which is the useful part.

### 2.6 Market-level adoption — FACT

| Quantity | Value | Source |
|---|---|---|
| Ranging sensors (radar+lidar) per vehicle, global | **2.5 (2025) → 5.5 (2035)** | Yole |
| Radar share of ranging-sensor units | 65–75% (2026) | Yole |
| Lidar attach rate, A/B segment | <15% until at least 2028 | suppliers via Yole |
| Global ADAS penetration | 66% (2025) → **94% (2035)** | Counterpoint |
| L2+/L3 share of global new sales | **≥31% by 2035** | S&P Global Mobility |
| L2+/L3 global adoption | **>50% by 2035** | IDTechEx |
| L2 vs L3 compute cost per vehicle | $200–400 vs **$800–1,500** | SBD / TechAD 2026 |

Note Yole's 2.5 → 5.5 counts **radar + lidar only**, not cameras or ultrasonics,
and its base is global and all-powertrain. European BEVs sit above it.

### 2.6b Yano Research — the missing units-based level split — FACT

§9.3 of the first issue said no public source gives a level split **in units
rather than revenue**. That was wrong. Yano Research publishes one, covering
**US, Europe, China and Japan**, all powertrains:

| Level | 2025 (k units) | % | 2030 (k) | 2035 (k) | % |
|---|---|---|---|---|---|
| L1 | 20,062 | 33.4 | 14,692 | 13,968 | 16.6 |
| L2 | 32,180 | 53.6 | — | 25,635 | 30.5 |
| **L2+** | **7,459** | **12.4** | **22,554** | **31,810** | **37.9** |
| L3 | 325 | 0.5 | 3,369 | 6,520 | 7.8 |
| L4 | — | — | 800 | 6,065 | 7.2 |
| **Total** | **60,026** | | 73,471 | **83,998** | |

The 2035 column sums to 83,998 exactly, so the table is internally consistent.

Three things this settles:

1. **L2+ is a real, separately tracked category** — it becomes the *largest*
   single class by 2035 at 37.9%, overtaking L2. Independent confirmation that
   the plain SAE axis is inadequate and that the industry already inserts an
   intermediate tier. This is the core claim of §1, arrived at from a different
   direction.
2. **Certified L3 in 2025 is 0.5% of units** — 325,000 across four major
   markets, all powertrains. Consistent with §2.1: L3 exists only in F-segment
   flagships.
3. **The revenue-vs-units trap is measurable.** NextMSC puts L2+ at 15.8% of
   *revenue* in 2025 and 25.2% in 2035; Yano puts it at 12.4% and 37.9% of
   *units*. The revenue/unit ratio therefore falls from **1.27 to 0.66** — a
   ~48% decline in L2+ price relative to the market average. **That is a direct
   empirical measurement of the cost-decline mechanism underlying Driver C**
   (§7.2), obtained by crossing two independent sources. Indicative only — the
   two vendors define scope differently — but the direction and rough magnitude
   support the premise that cost stops binding.

**Never read a revenue share as a fitment rate.** An L3 system carries 3–5× the
content cost of L2 (§2.6), so revenue shares overstate high-level penetration
early and understate its growth later, as the tables above demonstrate.

### 2.7 EF market structure — FACT

EQE sedan+SUV production ends 2026; EQS being wound down (never exceeded
30,000/yr globally); Audi Q8 e-tron discontinued Feb 2025. Replacements are
smaller (CLA, GLC EQ). **EF per-vehicle content and EF share of sales move in
opposite directions** — never conflate them when weighting by volume.

---

## 3. The hardware tier axis

Replaces SAE level as the model's internal driver. SAE level becomes a
descriptive attribute.

| Tier | Name | Cameras | Radar | Ultrasonic | Lidar | Ranging (rad+lid) | SAE label seen | Tag |
|---|---|---|---|---|---|---|---|---|
| **H0** | GSR-2 mandated floor | 1 | 1 | 0–4 | 0 | **1** | L0 / L1 | DERIVED from §2.1 |
| **H1** | ACC + lane keeping | 1–2 | 1–3 | 8–12 | 0 | **2** | L2 | ASSUMPTION |
| **H2** | hands-off highway | 5–8 | 3–5 | 12 | 0 | **4** | L2+ | ASSUMPTION |
| **H3** | urban + highway "L2++" | 8–12 | 5 | 12–16 | 0–1 | **5.3** | L2++ *or* L3 | FACT-anchored (EX90) |
| **H4** | redundant, liability transfer | 6–12 | 5–6 | 12–13 | 1–3 | **7** | L3 | FACT-anchored (EQS, i7) |

**H3 and H4 are anchored on measured cars** (§2.2). H0 is pinned by GSR-2. H1
and H2 are ASSUMPTION and are the weakest rows — see §9.2.

**Why the boundary moved.** The large hardware step is **H1 → H2/H3**
(≈5 sensors → 25–35, plus a domain controller). The step H3 → H4 is small: add
lidar, add redundancy. The SAE axis placed its only boundary at the *small* step
and had none at the large one.

---

## 4. Driver A — tier shares of new sales

Share of new BEV sales in each segment, by tier. **Mode** shown; band in §4.2.

### 4.1 Mode — DERIVED from §2.6 market totals, ASSUMPTION on the segment split

**EF**

| Year | H0 | H1 | H2 | H3 | H4 | Ranging | Check |
|---|---|---|---|---|---|---|---|
| 2025 | 0.00 | 0.10 | 0.25 | 0.50 | 0.15 | **4.9** | vs measured 5–6 ✓ |
| 2030 | 0.00 | 0.05 | 0.15 | 0.50 | 0.30 | 5.6 | |
| 2035 | 0.00 | 0.00 | 0.10 | 0.45 | 0.45 | 5.9 | |
| 2040 | 0.00 | 0.00 | 0.05 | 0.40 | 0.55 | 6.2 | |
| 2050+ | 0.00 | 0.00 | 0.00 | 0.35 | 0.65 | 6.4 | saturation, §7 |

**CD**

| Year | H0 | H1 | H2 | H3 | H4 | Ranging |
|---|---|---|---|---|---|---|
| 2025 | 0.10 | 0.45 | 0.35 | 0.10 | 0.00 | 2.9 |
| 2030 | 0.05 | 0.25 | 0.40 | 0.28 | 0.02 | 3.9 |
| 2035 | 0.00 | 0.10 | 0.30 | 0.45 | 0.15 | 4.8 |
| 2040 | 0.00 | 0.05 | 0.20 | 0.50 | 0.25 | 5.3 |
| 2050+ | 0.00 | 0.00 | 0.10 | 0.50 | 0.40 | 5.9 |

**AB**

| Year | H0 | H1 | H2 | H3 | H4 | Ranging |
|---|---|---|---|---|---|---|
| 2025 | 0.45 | 0.45 | 0.10 | 0.00 | 0.00 | 1.8 |
| 2030 | 0.25 | 0.45 | 0.25 | 0.05 | 0.00 | 2.4 |
| 2035 | 0.10 | 0.35 | 0.40 | 0.15 | 0.00 | 3.2 |
| 2040 | 0.05 | 0.25 | 0.40 | 0.28 | 0.02 | 3.9 |
| 2050+ | 0.00 | 0.10 | 0.30 | 0.45 | 0.15 | 4.8 |

**Consistency check — DERIVED.** Weighting AB/CD/EF at 30/50/20 gives a
sales-weighted ranging count of **3.0 in 2025** and **4.6 in 2035**, against
Yole's global **2.5 → 5.5**. Above at 2025 and below at 2035, both explicable:
European BEVs carry more ADAS than the global all-powertrain fleet in 2025, and
this table is deliberately conservative on the late ramp. **If Yole's 5.5 is
taken as binding, every 2035 row shifts up by roughly half a tier.** That is a
legitimate alternative and is what the Max band encodes.

**Note the AB pattern.** AB at 2050 sits where CD is at 2035 and EF at 2025 —
a lag of roughly 15 years AB→EF, against the 10 years currently implied by
`Offset_AB_y − Offset_EF_y` in `18_`. See §9.1.

### 4.2 Band — ASSUMPTION

Timing uncertainty, applied as a **time shift on the whole tier curve**, which
keeps shares summing to 1 by construction:

| Band | Shift | Reasoning |
|---|---|---|
| **Min** | **+5 years** | regulatory friction, cost pressure, weak consumer take-up |
| **Mode** | 0 | as tabulated |
| **Max** | **−5 years** | Chinese-style competitive escalation reaching Europe |

±5 y is the same convention already used for architecture transitions in `18_`,
kept deliberately so the two drivers remain comparable.

---

## 5. Driver B — lidar penetration, separate and contested

**Lidar gets its own driver.** It is the single most contested input in this
chain, and §2.1 vs §2.4 show it does not track tier, segment or certification.

### 5.1 Why it must not sit inside the tier axis

| | |
|---|---|
| `18_` today | lidar arrives with rising **L3 certification** |
| Reality | lidar arrives with **falling cost and Chinese competitive pressure**; certified L3 is being withdrawn *while* lidar volumes grow 60% a year |

Both premises of the current mechanism are wrong: certification is not what puts
lidar in cars, and premium-Europe-leads is not how it is spreading.

### 5.2 The two credible cases — both preserved

**Case HIGH — lidar becomes standard.** Cost has fallen 99.5% to ~$200 and keeps
falling. China is at 21% of NEVs, past the adoption chasm. Weather redundancy
(§2.5) and any future L3/L4 regulation both argue for a third modality. China
leads BEV development; Europe follows.

**Case LOW — 4D imaging radar substitutes.** Radar is the genuinely
weather-robust modality (§2.5) at a fraction of the cost. ~95% of lidar supply is
Chinese, and Luminar's liquidation removed the Western alternative — tariffs or
supply-security policy could throttle European adoption regardless of cost.
Tesla remains vision-only; Volvo's EX60 is planned without lidar.

**Neither case is dismissed.** The band below spans both.

### 5.3 Lidar-equipped share of new BEV sales, Europe

| Year | Min (LOW) | Mode | Max (HIGH) | Tag |
|---|---|---|---|---|
| 2025 | 0.00 | **0.01** | 0.02 | FACT (EQS, i7 only) |
| 2030 | 0.03 | **0.12** | 0.30 | DERIVED — Goldman 3 m overseas units by 2030 |
| 2035 | 0.08 | **0.28** | 0.55 | ASSUMPTION |
| 2040 | 0.12 | **0.45** | 0.70 | ASSUMPTION |
| 2050 | 0.18 | **0.60** | 0.85 | ASSUMPTION |
| 2070 | 0.25 | **0.70** | 0.90 | ASSUMPTION, §7 |

**Mode mechanism — China leads, Europe follows.** China reached 21% in 2025;
Mode puts Europe at 21% around **2032–33**, a lag of ~7 years. **The lag itself
should be sampled**, not fixed: `LIDAR_EUROPE_LAG_Y ~ Normal(7, 3)`, so the
China-follows hypothesis is testable rather than assumed.

**Segment dependence — ASSUMPTION.** Apply the §4.2 offsets, but *weakly*: the
BYD Seagull shows lidar entering at A-segment, so the premium-first assumption is
much weaker for lidar than for tier. Suggested: **half** the segment offset used
for Driver A.

### 5.4 Lidar units per equipped vehicle — ASSUMPTION

1 (Mode) at H3; 1–3 at H4. Measured: EQS 1, i7 1. No European car has shipped
with more than one. Multi-lidar suites exist only in Chinese flagships and
robotaxis.

---

## 6. Guideline for the sensor model — making a static factor dynamic

This section is the instruction set for `SensorNumbersMC.py`.

### 6.1 The mechanism to change

Today, `SensorNumbersMC.py` scales min/max counts by a **static** presence factor
read from `01_`:

    Std 1.00   Opt 0.50   Rare 0.25   "–" 0.00        presence(component, segment)

That factor is already a **penetration share** — "what fraction of vehicles in
this segment carry this component". Making it dynamic therefore requires no
rewrite, only one more index:

    presence(component, segment, year)
        = Σ_tier  share(tier, segment, year) × presence(component | tier)

`share(tier, segment, year)` comes from §4. **Read it from the same source the
wiring model reads. Do not recompute it** — if it is computed twice the two
models will diverge, which is the exact failure this coupling exists to prevent.

### 6.2 `presence(component | tier)` for the 12 ADAS components in `01_`

Rows are the ADAS sheet of `01_VehicleElectronics.xlsx`, unchanged and in order.

| # | Component | H0 | H1 | H2 | H3 | H4 | Tag / basis |
|---|---|---|---|---|---|---|---|
| 1 | Front ADAS camera | **1.00** | 1.00 | 1.00 | 1.00 | 1.00 | FACT — GSR-2 mandated |
| 2 | Rear view camera | 0.50 | 0.90 | 1.00 | 1.00 | 1.00 | ASSUMPTION |
| 3 | Side / mirror cameras | 0.00 | 0.25 | 0.80 | 1.00 | 1.00 | ASSUMPTION — 360° needs ≥4 |
| 4 | Front long-range radar | **1.00** | 1.00 | 1.00 | 1.00 | 1.00 | FACT — GSR-2 AEB |
| 5 | Corner short/mid-range radars | 0.00 | 0.30 | 0.85 | 1.00 | 1.00 | FACT-anchored — 5 radar at H3 (§2.3) |
| 6 | **LiDAR sensor** | 0.00 | 0.00 | 0.00 | **Driver B** | **max(Driver B, 0.80)** | §5 — *not* tier-governed |
| 7 | Ultrasonic sensors | 0.30 | 0.90 | 1.00 | 1.00 | 1.00 | ASSUMPTION |
| 8 | Driver monitoring camera | 0.20 | 0.50 | 0.90 | 1.00 | 1.00 | DERIVED — GSR-2 drowsiness/attention warning |
| 9 | ADAS camera ECU (basic) | 1.00 | 1.00 | **0.50** | **0.20** | **0.10** | ASSUMPTION — **declines**, see below |
| 10 | ADAS domain controller / fusion ECU | 0.00 | 0.10 | 0.70 | 1.00 | 1.00 | ASSUMPTION |
| 11 | Automated driving central computer | 0.00 | 0.00 | 0.10 | 0.50 | 1.00 | ASSUMPTION |
| 12 | Parking assist ECU | 0.20 | 0.80 | 1.00 | 1.00 | 1.00 | ASSUMPTION |

**Row 9 is the important one.** `ADAS camera ECU (basic)` **falls** as rows 10
and 11 rise — the smart camera is absorbed into the domain controller. This is a
genuine **substitution**, and it is invisible to the current static model, which
can only ever hold a component constant or grow it. It is the same structural
problem as `BevWiring_STATUS.md` §10 (substitution within an architecture state),
appearing here in the sensor model. Any component pair like this must be drawn
jointly, not independently.

### 6.3 Backward compatibility

At 2025, §4.1 tier shares composed with §6.2 must reproduce the existing static
Std/Opt/Rare labels in `01_` to within ~0.15. Worked example, EF 2025 shares
(H1 0.10, H2 0.25, H3 0.50, H4 0.15):

| Component | composed presence | `01_` says | agrees? |
|---|---|---|---|
| Side / mirror cameras | 0.025+0.20+0.50+0.15 = **0.88** | Std (1.00) | close |
| Corner radars | 0.03+0.2125+0.50+0.15 = **0.89** | Std (1.00) | close |
| LiDAR sensor | Driver B 2025 ≈ **0.01** | Opt (0.50) | **`01_` too high** |
| ADAS domain controller | 0.01+0.175+0.50+0.15 = **0.84** | Std (1.00) | close |

Three of four land close, which validates the composition. The lidar row does
not, and `01_` is the one that is wrong: EF lidar presence in 2025 is ~1%, not
50%. **This is the first concrete error the new axis catches.**

### 6.4 What else must change in the sensor files

1. **`06_` camera counts are low** (§2.3): EF max 5 CMOS against 6–10 measured.
   Raise EF to 8–12, CD to 5–8, AB to 1–2, at H3/H4.
2. **Possible ultrasonic double-count.** `06_` carries ultrasonics under both
   *Ultrasonic sensors* (8–12) and *Parking assist ECU* (8–12). Measured cars
   have 12–16 total. **Check before summing** — this may be a 2× error.
3. **`01_` lidar presence** — see §6.3.
4. **Add a `Year` and `Tier` dimension** to both files, or emit the composed
   presence as a CSV the models read.

---

## 7. Extrapolation, 2035 → 2070

**Every source in §2 ends by 2035. Everything after that is this section.**
Roughly two-thirds of the model's time axis rests on it.

### 7.1 Rules

| # | Rule | Justification | Tag |
|---|---|---|---|
| **E1** | Tier shares **saturate** and hold flat after 2050 | H4 is the maximum sensing *configuration* this taxonomy describes. Growth beyond it is handled by Driver C, not by more tiers | ASSUMPTION |
| **E2** | The **AB→EF lag persists** at ~15 years, and does not close | Cost hierarchy between segments is structural, not transitional. If it did close, AB 2050 would jump ~1.5 ranging sensors | ASSUMPTION |
| **E3** | Lidar continues to rise after 2050 but **decelerates**, reaching 0.70 Mode at 2070 | Cost curve flattens near a materials floor; residual segment is served by radar + camera | ASSUMPTION |

A fourth rule — *"no new sensor modality appears before 2070"* — was carried in
the first issue of this report and has been **withdrawn**. It was the weakest
statement in the document: roughly one new automotive sensing modality has
reached series production every 10–15 years since the 1970s (lambda ~1976,
inertial ~1995, radar 1998, ultrasonic ~2000s, vision ~2007, lidar 2017, 4D
radar and IR driver monitoring ~2022), so assuming zero over 45 years was the
least likely value available. It is replaced by §7.2.

### 7.2 Driver C — post-2040 sensor-count scenarios

**The insight that removes the need to forecast unknown technology:** a wiring
model does not care *which* sensor arrives, only *how many*. And the count is
set by two mechanisms that are both observable today.

| Mechanism | Evidence | Effect |
|---|---|---|
| **Cost decline with volume** | Lidar −99.5% in 8 years to ~$200 (§2.4); radar >140 m units/yr | By ~2040–45 sensor cost is negligible against vehicle price, so **cost stops being the binding constraint on count** |
| **Safety redundancy** | GSR-2 mandates; L3+ needs fail-operational sensing; weather robustness needs *multiple modalities*, not one better one (§2.5) | Once cost is not binding, **required redundancy sets the count** |

A new modality, if one arrives, simply shows up as "more sensors" — which is the
only thing the wiring model consumes. The scenarios therefore span the outcome
without naming the technology.

| | Mechanism | Multiplier at 2070 | Effect on EF total length |
|---|---|---|---|
| **S1 Cost-driven convergence** | Sensors get cheap, but sensing converges on a minimal efficient set (camera + radar); redundancy is achieved in compute, not hardware. The vision-only thesis | **×1.0** | 0% |
| **S2 Regulated redundancy** *(Mode)* | Cost decline makes redundancy affordable; type approval for L3/L4 requires independent modality redundancy for fail-operational behaviour | **×1.4** | +8% |
| **S3 Full fail-operational** | Private L4 requires dual-redundant sensing across every modality plus degraded-mode operation. Each sensing function duplicated | **×2.0** | +21% |

**Anchors — editable, PCHIP-interpolated, same as every other curve here:**

| Scenario | 2040 | 2050 | 2060 | 2070 | Default weight |
|---|---|---|---|---|---|
| S1 | 1.00 | 1.00 | 1.00 | 1.00 | 0.25 |
| S2 | 1.00 | 1.15 | 1.28 | 1.40 | 0.50 |
| S3 | 1.00 | 1.35 | 1.70 | 2.00 | 0.25 |

All three start at 1.00 in 2040, because that is when the cost mechanism above
stops binding. **Before 2040 the scenarios are identical by construction** and
Driver C has no effect.

**A property worth noting: the band widens after ~2045 by construction.** That
is correct and deliberate. Uncertainty about 2070 genuinely should exceed
uncertainty about 2035. The withdrawn E4, paired with E1, made the band *narrow*
into the far future — which was the clearest symptom that it was wrong.

**S2 lands at +8% on EF 2070 total length**, which independently reproduces the
estimate obtained by extrapolating the historical modality-arrival rate. Two
different routes to the same number is mild corroboration of both.

### 7.3 How to select a scenario

One cell in `20_` sheet `Control`. **No code editing.**

```
Active_Scenario:   SAMPLE
```

| Value | Behaviour |
|---|---|
| **`SAMPLE`** *(default)* | Each Monte Carlo iteration draws a scenario by weight. **One run; the output band contains all three.** The scenario uncertainty lands inside P2.5–P97.5, where it belongs |
| `S1` / `S2` / `S3` | Every iteration pinned to that scenario. For comparing the three as separate answers |

When pinned, outputs take a suffix (`bev_wiring_stats_S2.csv`, `plots_S2/`) so
runs cannot silently overwrite each other. `SAMPLE` keeps the existing filenames.

`SCENARIO_OVERRIDE` in `BevWiring.py` section 0 takes precedence over the sheet,
for scripted sweeps across all three without editing Excel.

**`SAMPLE` is the default on purpose.** Pinning to S2 produces a narrower band
than the evidence supports — it silently discards the S1/S3 spread. Pinned runs
are for *understanding* the scenarios; `SAMPLE` is what should be quoted.

**E1 and an existing open item.** `BevWiring_STATUS.md` open item 5 notes the
model already goes flat after ~2050 because every share in `18_` saturates. E1
keeps tier shares flat, but Driver C now supplies post-2040 growth, so the
flatness is no longer total — and where it remains it is a stated claim rather
than an artefact.

---

## 8. Validation targets

These are the numbers the code must reproduce. **They belong in `19_` sheet
`Validation` and in an assertion in `BevWiring.py`, so that a report drifting
from the code becomes a test failure rather than a later discovery.**

| # | Target | Value | Tolerance | Source |
|---|---|---|---|---|
| V1 | 2025 length AB / CD / EF | 1392 / 2486 / 3546 m | ±1% | existing anchor |
| V2 | Metres per camera at 2025, AB / CD / EF | 28 / 25 / 31 m | ±15% | `17_` ÷ `06_` |
| V3 | EF ranging sensors (radar+lidar) at 2025 | 4.9 | ±1.0 | §2.2 measured |
| V4 | Sales-weighted ranging sensors at 2025 | 3.0 | ±1.0 | §4.1 vs Yole 2.5 |
| V5 | Lidar-equipped share, Europe, 2025 | 0.01 | ±0.01 | §2.4 |
| V6 | Tier shares sum to 1, every segment-year | 1.000 | 1e-9 | construction |
| V7 | Composed presence vs `01_` static labels at 2025 | agree | ±0.15 | §6.3 |
| V8 | ADAS share of total length, AB/CD/EF at 2025 | 6 / 9 / 11 % | ±3 pp | `SENSOR_WIRING_INTERFACE.md` §1 |
| V9 | Driver C multiplier at 2040, all scenarios | 1.000 | 1e-9 | §7.2 — scenarios identical before 2040 |
| V10 | Scenario weights sum to 1 | 1.000 | 1e-9 | construction |

V7 is the cross-model check: it is the only target that fails if the wiring model
and the sensor model drift apart. V9 guards the property that makes Driver C
safe — it must not perturb any year for which sourced data exists.

---

## 9. Open questions and known weaknesses

### 9.0 First external check on Driver A — and it is not comfortable

Mapping the Yano units table (§2.6b) onto the tier axis — Yano L1 → H0/H1,
L2 → H1, L2+ → H2+H3, L3 → H4 — and weighting §4.1 at AB/CD/EF = 30/50/20:

| | | this report | Yano | ratio |
|---|---|---|---|---|
| **2025** | H0+H1 (L1, L2) | 56.5% | 87.0% | 0.65 |
| | H2+H3 (L2+) | **40.5%** | **12.4%** | **3.3×** |
| | H4 (L3) | 3.0% | 0.5% | 6× |
| **2035** | H0+H1 | 18.5% | 47.1% | 0.39 |
| | H2+H3 | 65.0% | 37.9% | 1.7× |
| | **H4 (L3+L4)** | **16.5%** | **15.0%** | **1.10** |

**Read this carefully before reacting.** Yano covers **all powertrains** across
US/Europe/China/Japan. This report covers **European BEVs only**, which are
newer, more expensive and more electronically sophisticated than the global
all-powertrain average. A gap in this direction is expected.

What is genuinely informative:

- **The top of the axis agrees well.** H4 at 2035 is 16.5% here against Yano's
  15.0% — a 1.10 ratio, well inside the 1.6× cross-house spread of §1.2. The
  high-tier trajectory is corroborated.
- **The low end does not.** A 3.3× gap at 2025 exceeds the 1.6× band, though it
  is far below the >10× error threshold. Some of it is BEV-vs-all-powertrain;
  it is unlikely to be all of it.
- **Direction of the correction:** §4.1 is probably too aggressive at the bottom
  of the ladder in the near term — too few vehicles left in H0/H1 around 2025–30.
  That would make near-term ADAS length slightly high and understate later
  growth.

This is the **first external check Driver A has ever had**, and it changes §9.2:
the segment split moves up the weakness ranking. Resolving it needs a
BEV-only or Europe-only units split, which still has not been found.

### 9.1 The segment offset may be wrong in `18_`

EF sits at 5–6 ranging sensors today; Yole puts the global fleet there in 2035 —
a **~10-year** lead. §4.1 implies **~15 years** AB→EF. `18_` currently encodes
**10** (`Offset_AB_y +5` minus `Offset_EF_y −5`). All three disagree. Resolving
this needs segment-split sensor data, which no public source provides (§9.3).

### 9.2 Weakest inputs, ranked

1. **Driver C multipliers** (§7.2) — the S1/S2/S3 endpoints are reasoned from
   two observable mechanisms, but the specific values 1.0 / 1.4 / 2.0 are
   ASSUMPTION. This is now the largest single lever on the 2070 answer.
   Its *structure* is defensible; its *calibration* is not sourced.
2. **H1 and H2 sensor counts** (§3) — pure ASSUMPTION; H3/H4 are anchored on
   measured cars.
3. **Lidar 2040–2070** (§5.3) — a 3.6× spread between Min and Max at 2070.
   Correctly wide; it is genuinely unknown.
4. **Segment split of tier shares** (§4.1) — market totals are sourced, the
   split across AB/CD/EF is not.

Note the improvement from the first issue: the weakest item used to be an
assumption known to be *false* (E4). It is now an assumption known to be
*uncalibrated*, which is a better class of problem — the mechanism is right and
only the numbers are soft, so new evidence can refine it rather than overturn it.

### 9.3 What no public source provides

- Sensor content **split by vehicle segment** — §2.2 had to be assembled
  car-by-car from press material.
- **Per-model take-rates** — what fraction of EQS or i5 buyers actually bought
  the higher ADAS package.
- **A BEV-only or Europe-only units split by level.** Yano (§2.6b) gives units
  by level but for all powertrains across four regions, which is what makes the
  §9.0 comparison inexact. This is now the single most valuable missing dataset.
- **Wiring metres per tier** — no source links ADAS content to harness length.
  This stays the project's own contribution; V2 remains its only anchor.

*Removed from this list on 2026-08-05: "a level split in units rather than
revenue" — Yano Research publishes one (§2.6b).*

---

## 10. Sources

### 10.1 Certification and OEM decisions
- electrive, 2026-02-23 — BMW abandons L3, following Mercedes: <https://www.electrive.com/2026/02/23/following-mercedes-bmw-also-abandons-level-3-automated-driving/>
- WardsAuto — Mercedes shifts to L2++ in the 2026 S-Class: <https://www.wardsauto.com/news/mercedes-benz-shifts-autonomous-driving-tech-in-2026-s-class/811431/>
- AutoBuzz, 2025-12-01 — no more lidar for EX90, ES90, Polestar 3: <https://autobuzz.my/2025/12/01/no-more-lidar-sensors-for-volvo-ex90-es90-and-polestar-3-in-2026/>
- The Drive — Volvo drops Luminar and lidar for 2026: <https://www.thedrive.com/news/volvo-has-dropped-luminar-and-lidar-for-2026-models>
- Mercedes-Benz Group — Drive Pilot sensor set: <https://group.mercedes-benz.com/innovation/case/autonomous/drive-pilot-2.html>
- BimmerToday, 2024-12-09 — BMW 7 Series Personal Pilot L3 sensor setup: <https://www.bimmertoday.de/2024/12/09/bmw-7er-g70-video-erklart-personal-pilot-l3-sensor-setup/>
- Just Auto — China approves first L3 vehicles: <https://www.just-auto.com/news/china-approves-first-level-3-autonomous-driving-vehicles/>

### 10.2 Market volumes
- best-selling-cars.com — Europe, Feb 2026 BEV models: <https://www.best-selling-cars.com/europe/2026-february-europe-best-selling-electric-car-brands-and-models/>
- EV.com — Mercedes phases out EQE sedan and SUV by 2026: <https://ev.com/news/mercedes-benz-phase-out-eqe-sedan-suv-by-2026>
- Autoblog — Mercedes preparing to end the EQS: <https://www.autoblog.com/news/mercedes-is-quietly-preparing-to-end-the-slow-selling-eqs>

### 10.3 Lidar
- KrASIA — Hesai's $200 lidar: <https://kr-asia.com/china-lidar-maker-hesai-looks-to-prove-musk-wrong-with-usd-200-model>
- BigGo Finance — lidar cost down 99.5% in 8 years: <https://finance.biggo.com/news/ZU6xbZ4BrAZSr0oSetvc>
- ChinaEVHome, 2026-05-06 — Hesai leads shipments; Chinese suppliers 95%: <https://chinaevhome.com/2026/05/06/hesai-leads-global-adas-lidar-shipments-as-china-suppliers-take-95-share/>
- Tianxia Gongchang — China intelligent driving 2026; lidar 21% of NEVs: <https://faxiangongchang.com/en/reports/china-intelligent-driving-2026>
- CnEVPost, 2026-05-09 — BYD Seagull with lidar: <https://cnevpost.com/2026/05/09/byd-launch-2026-seagull-may-11-lidar/>
- SCMP — low-cost Chinese EVs fitted with lidar: <https://www.scmp.com/business/china-evs/article/3350948/chinas-low-cost-evs-be-fitted-lidar-systems-usually-reserved-luxury-models>
- Astute Analytica, 2026-01-20 — lidar to $25.75 bn by 2035: <https://www.globenewswire.com/news-release/2026/01/20/3222187/0/en/Automotive-LiDAR-Market-Projected-to-Reach-US-25-75-Billion-by-2035-Supported-by-Increasing-Series-Production-Adoption-Says-Astute-Analytica.html>
- Yole via Hesai — no.1 long-range ADAS lidar shipments 2025: <https://www.hesaitech.com/hesai-secures-no-1-in-long-range-adas-lidar-shipments-in-2025-by-yole-group/>

### 10.4 Analyst and technical
- IDTechEx — L2+ ADAS outpaces L3 in Europe: <https://www.idtechex.com/en/research-article/l2-adas-outpaces-l3-in-europe-us-4b-by-2042/32860> (fetchable mirror: <https://www.signalintegrityjournal.com/articles/3895-l2-adas-outpaces-l3-in-europe-us4-b-by-2042>)
- S&P Global Mobility — premium OEMs bet big on L2+: <https://autotechinsight.spglobal.com/news/5287492/from-eyes-off-hype-to-hands-free-reality-premium-oems-bet-big-on-l2->
- Counterpoint, 2026-03-26 — ADAS penetration to 94% by 2035: <https://counterpointresearch.com/en/insights/Global-ADAS-Penetration-to-Reach-94-Percent-by-2035>
- IndexBox citing Yole — ranging sensor outlook to 2035: <https://www.indexbox.io/blog/automotive-detection-and-ranging-sensor-market-forecast-points-higher-toward-2035-driven-by-adas-mandates-and-sensor-fusion-advances/>
- Focal Point Positioning — TechAD Europe 2026, L2/L3 compute cost: <https://focalpointpositioning.com/resources/insights/blogs/adas-trends-2026-key-insights-from-tech-ad-europe-in-berlin/>
- L4DR: LiDAR-4DRadar fusion, weather-robust 3D detection (AAAI): <https://arxiv.org/html/2408.03677v3>
- 4D Radar Meets LiDAR and Camera under adverse weather (CVPR 2026 workshop): <https://arxiv.org/html/2606.00416v1>

### 10.4b Market-research vendors (see the evidence-class note in §1.2)
- **Yano Research** — global ADAS / autonomous driving systems to 83,998 k units by 2035, split by level **in units**. The most useful of this group by a wide margin: <https://www.yanoresearch.com/press/press.php/3693>
- **NextMSC** — ADAS market $34.2 bn (2025) → $112.6 bn (2035); segments **L2 Plus as its own category**, by revenue: <https://www.nextmsc.com/report/advanced-driver-assistance-systems-adas-market-1-at4947>
- **Polaris Market Research** — ADAS market $39.32 bn (2025) → $88.97 bn (2034), 9.5% CAGR; BEVs 47.6% of the ADAS market by EV type, passenger cars 75.2%. No public level or sensor split: <https://www.polarismarketresearch.com/industry-analysis/advanced-driver-assistance-systems-adas-market>
- **Fortune Business Insights, *ADAS Simulation Market*** — **not relevant to this report.** Covers simulation and validation software (SIL/HIL/MIL/DIL), $3.48 bn in 2025. Contains no sensors-per-vehicle and no fitment data. Recorded here so it is not chased again: <https://www.fortunebusinessinsights.com/adas-simulation-market-115978>

### 10.5 Paid reports not purchased
- IDTechEx *Passenger Car ADAS Market 2025-2045* (1080) — 14 ADAS features forecast by region over 20 years. Best available fit; ask whether it segments by vehicle class before buying.
- S&P Global Mobility *Autonomy Forecasts* — the only source found that forecasts L2+ as its own category.
- SBD Automotive *ADAS Sensor Market Landscape* — free preview PDF exists, resisted text extraction here; open by hand.

---

## 11. Revision log

| Date | Change |
|---|---|
| 2026-08-05 | First issue. Tier axis (§3), Driver A (§4), Driver B (§5), sensor-model guideline (§6), extrapolation rules (§7), validation targets (§8). Corrects the "`06_` has no radar/lidar rows" claim in `SENSOR_WIRING_INTERFACE.md` §5 and `18_` sheet `Notes` (§2.3). Corrects `01_` EF lidar presence (§6.3). |
| 2026-08-05 | Added §1.1–§1.2: predictions are not ground truth; uncertainty calibrated from observed source disagreement, with a ~3% self-consistency floor, ~1.6× cross-house spread, 3–4× structural spread, and a >10× threshold before calling anything an error. Band widths in §4.2, §5.3 and §7 now derive from §1.2 rather than being asserted. Machine-readable extract issued as `Data/19_ADAS_sensor_adoption.xlsx`, generated by `tools/make_19_adas_sensor_adoption.py`. |
| 2026-08-05 | Market-research vendors reviewed (§10.4b). **Yano Research units-by-level table added (§2.6b)** — supplies the units-based level split previously listed as unavailable, and independently confirms L2+ as a separate, and by 2035 the largest, category. **First external check on Driver A (§9.0):** the high tiers agree within 1.10× at 2035, the low end disagrees by 3.3× at 2025 — partly BEV-vs-all-powertrain, probably not entirely. Evidence-class hierarchy added to §1.2, plus the revenue-vs-units trap: never read a revenue share as a fitment rate. Fortune Business Insights *ADAS Simulation* recorded as out of scope. |
| 2026-08-05 | **Rule E4 withdrawn** ("no new sensor modality before 2070") and replaced by **Driver C**, the post-2040 sensor-count scenarios S1/S2/S3 (§7.2). Rationale: a wiring model needs *how many* sensors, not *which*, and the count is governed by two observable mechanisms — cost decline with volume, and safety redundancy. This removes the need to forecast unknown technology. Scenario selection documented in §7.3 (`Active_Scenario` cell, default `SAMPLE`). Validation targets V9 and V10 added (§8). Weakest-input ranking updated (§9.2): the top item is now uncalibrated rather than false. |
