# The autonomy axis: installed assistance systems vs SAE certification

**The problem in one sentence:** the model predicts *wiring*, wiring follows
*installed sensor hardware*, but the autonomy axis in `18_` is keyed on *SAE
certification level* — and those two things have come apart.

Written 2026-08-05. Companion to `BevWiring_STATUS.md` (section 9, open item 4)
and `../SensorNumbersMC/SENSOR_WIRING_INTERFACE.md`.

---

## 0. Scope note — read first

An earlier draft of this document argued from the **top 10 best-selling BEVs in
Europe**. That list is Model Y, Elroq, Model 3, T03, Enyaq, R5, ID.4, ID.3,
ID.7, iX1 — **A, B, C and D segment cars. Not one of them is EF.**

Nothing about EF can be concluded from that list. It has been demoted to §5,
where it is evidence about **AB and CD only**.

Everything in §2 below is EF-specific: E- and F-segment BEVs sold in Europe.

---

## 1. The two axes are not the same variable

| | **SAE certification level** | **Installed assistance hardware** |
|---|---|---|
| What it measures | who is legally liable when the system is engaged | how many sensors and ECUs are physically in the car |
| Who sets it | type-approval authority (UNECE R157, national road law) | OEM product planning and cost targets |
| Changes when | a regulation or an approval is granted | a model generation launches |
| Granularity | 6 discrete levels, L0–L5 | continuous, and rising steadily inside "L2" |
| **Drives wiring** | **no** | **yes** |

A car does not grow a wire when a regulator grants liability transfer. It grows
a wire when an OEM fits another camera.

**The model currently uses column 1 to predict column 2.** That worked while the
two moved together. In EF they no longer do — and EF is where they diverge most.

---

## 2. EF-specific evidence

### 2.1 EF is exactly where certified L3 lived

Every certified L3 passenger car ever sold is an EF car:

| Car | Segment | System | Status |
|---|---|---|---|
| Mercedes S-Class / EQS | **F** | Drive Pilot (2021–) | **paused**; not on the facelifted 2026 S-Class |
| BMW 7 Series / i7 | **F** | Personal Pilot L3 (2024–) | **discontinued** at the facelift, late April 2026 |

So the AB/CD observation "no volume BEV is L3" was never the interesting one.
The interesting one is that **L3 existed only in EF, and EF is now removing it.**

### 2.2 Three independent EF withdrawals, all in 2026

| OEM | What was withdrawn | Replaced by | Stated reason |
|---|---|---|---|
| **Mercedes** (F) | Drive Pilot L3 | MB.Drive Assist Pro, **"L2++"** | L3 cost vs narrow use case |
| **BMW** (F) | Personal Pilot L3 | Motorway Assistant, **L2**, hands-off to 130 km/h. €6,000 → €1,450 | same |
| **Volvo / Polestar** (E) | **lidar removed** from EX90, ES90, Polestar 3 for MY2026 | camera + radar only | Luminar liquidation; "customer demand and limited supply" |

Three OEMs, three separate decisions, one direction. In the EF segment,
**certified L3 penetration peaked around 2024–25 and its first derivative is now
negative.**

This is the opposite of what `18_` assumes for EF.

### 2.3 But EF sensor counts are high — measured, not assumed

The same three cars, by installed hardware:

| EF car | Cameras | Radar | Lidar | Ultrasonic | Total | Certified |
|---|---|---|---|---|---|---|
| Mercedes S-Class / EQS (Drive Pilot) | 6 | 5 | 1 | 13 | **>35** | L3 |
| BMW 7 Series / i7 (Personal Pilot L3) | n/s | n/s | 1 | 12 | **25** | L3 |
| **Volvo EX90, MY2026** | 8 ext + 2 int | 5 | **0** | 16 | **31** | **L2** |

**The Volvo row is the whole argument in one line.** It has *more total sensors*
than the L3-certified BMW, and it is certified L2. Sensor count and SAE level are
not the same variable, and in EF they now point in opposite directions.

These are the first **sourced** EF sensor counts in this project. `18_` sheet
`Sensors_per_Level` currently has none.

### 2.4 A cross-check on the segment offset

Yole's fleet-wide **detection-and-ranging** count (radar + lidar only, *not*
cameras or ultrasonics) runs **2.5 per vehicle in 2025 → 5.5 by 2035**.

The EF cars above, counted the same way: Volvo 5, Mercedes 6, BMW ~5–6.

**EF in 2025–26 is already at the value Yole projects for the whole fleet in
2035** — a lead of roughly **10 years**, not the 5 encoded in `Offset_EF_y = −5`.

Treat this as an order-of-magnitude check, not a calibration: Yole's base is
global and includes ICE, and three cars are not a segment. But it points one
way, and it points further than the model currently assumes.

### 2.5 Lidar — the most contested input in the whole chain

**Correction to an earlier draft of this section.** It read the European
withdrawals as a lidar retreat. That reading does not survive the cost and
volume data, and one of its three data points was misused:

> **The Volvo case is weak evidence.** Volvo did not drop lidar because it
> judged lidar unnecessary — **its supplier, Luminar, liquidated**, and Volvo's
> own stated reason cites *"limited supply of the LiDAR hardware"*. That is a
> Western supplier failing to compete with Chinese vendors on cost. It is
> evidence about the **supply chain**, not about demand for lidar.

Likewise, BMW's and Mercedes' cost argument was made against a **2023–24 cost
structure that no longer exists.**

#### The case that lidar grows

| Fact | Value | Source |
|---|---|---|
| Long-range lidar unit price, China | **~$4,100 → $150–200** | Hesai / market reports |
| Cost reduction over 8 years | **99.5%** | market analysis |
| Hesai ATX | **$200**, in mass production since 2025 | Hesai |
| **Lidar penetration, Chinese NEVs** | **21% in 2025** — past the 16% "chasm threshold" | China supply-chain research |
| Global automotive lidar market 2025 | **>$1 bn, +60% YoY** | Yole |
| Passenger-vehicle lidar units 2025 | **3.7 m** (≈3.1 m primary ADAS) | Yole |
| Chinese share of global lidar supply | **~95%** (Hesai 43%) | Yole |
| Overseas ADAS lidar shipments by 2030 | 3 m units | Goldman Sachs |
| Automotive lidar market by 2035 | $25.75 bn | Astute Analytica |

21% penetration past the chasm threshold, at $200 a unit, growing 60% a year, is
**mass adoption** — not a niche in retreat. A cost argument built on $500–1,000
lidar has already expired.

#### The case for caution

- **Rain favours radar, not lidar.** This matters for the European-climate
  argument and cuts against the intuitive version of it. Peer-reviewed results:
  4D mmWave radar is *minimally* affected by fog, rain and snow because its
  wavelength greatly exceeds the particle size, while **lidar and cameras suffer
  moderate-to-severe degradation**; lidar-camera perception "collapses in fog"
  from backscatter. The robust configurations are lidar **+** 4D radar, or radar
  substituting for lidar.
  **So the climate argument is an argument for more sensors of more types — it
  does not single out lidar.** Either way it increases wiring.
- **Supply concentration.** ~95% of lidar comes from Chinese suppliers. European
  adoption could be slowed by tariffs, procurement policy or supply-security
  rules for reasons unrelated to cost or capability. Luminar's liquidation
  removed a Western alternative.
- **A live counter-current exists.** Tesla remains vision-only; Volvo's EX60 is
  planned without lidar; the "is lidar still necessary" argument is being had in
  the Chinese trade press too.

#### What follows for the model

The two cases above are **both credible, and they disagree.** That is the
finding. It should not be resolved by choosing a side.

Lidar penetration in Europe 2030–2070 is the **single most contested input in
this chain**, and this is a Monte Carlo model — the correct response to a
genuinely contested input is a **wide, explicit distribution on its own driver**,
not a point assumption buried inside an autonomy level.

`18_` currently routes lidar in via rising L3 *certification*. That mechanism is
wrong regardless of which case wins: certification is not what puts lidar in
cars — cost, supply and OEM sensing strategy are.

**Lidar must become its own driver, with a band wide enough to contain both
cases above.** The China-leads-Europe-follows mechanism the user raises is a
strong candidate for its central path, with the lag itself sampled.

### 2.6 EF volume in Europe is contracting

| Model | Segment | Status |
|---|---|---|
| Mercedes EQE sedan + SUV | E | production ends **2026**, four years after launch |
| Mercedes EQS | F | never exceeded 30,000/yr globally; being wound down |
| Audi Q8 e-tron | E/F | discontinued **February 2025** (Brussels plant closed) |

Replacements are *smaller*: the electric C-Class and GLC EQ, and the CLA — a
C-segment car that took European Car of the Year 2026 and 6,686 German
registrations in June 2026 alone.

**Implication:** EF per-vehicle wiring content may keep rising while EF's *share
of BEV sales* falls. If segment results are ever weighted by units sold, these
are two separate trends and must not be conflated.

---

## 3. How this breaks the model, concretely

`BevWiring.py` computes

    ADAS length = sensor_count(autonomy_level) × metres_per_sensor

with `sensor_count` from sheet `Sensors_per_Level` in `18_`, and the level drawn
from shares derived from a **certification-based** global fleet table
(`Report_Scenarios`).

1. **The boundary is in the wrong place.** The big hardware step is L2 → L2++
   (roughly 5 sensors → 25–35, plus a domain controller). The step L2++ → L3 is
   small — add lidar, add redundancy. The SAE axis puts its only boundary at the
   small step and none at the big one. Volvo's EX90 crossed *down* the SAE axis
   while keeping 31 sensors.
2. **The trend sign is wrong for EF at the near end.** Certified L3 in EF is
   heading to zero through 2026–27; installed content is not.
3. **It corrupts the weakest input.** `Sensors_per_Level` is unsourced and
   supplies ~22–24% of the 2070 answer. Keying it on the wrong variable means
   even good sensor data, once obtained, would be indexed against the wrong
   thing.

---

## 4. Open item 4 revisited

Open item 4 in `BevWiring_STATUS.md` frames `Fleet_to_NewSales_lead_y = 7` as
set too high, breaching the report's "private L4/L5 < 5% through 2035". That
framing does not survive the EF data:

| EF, share of new sales | `Notes` (your input) | model, lead=7 | EF reality 2026 |
|---|---|---|---|
| L3 present in 2025 | yes | 16.0% | **certified: ~0% and falling; L3-grade hardware: high** |
| L4 by 2030 | ~20% | 11.8% | — |
| L5 by 2035 | ~20% | 2.4% | — |

**It is not a calibration problem and no setting of that lever fixes it** — with
`Private_lag_y = 5` and `Offset_EF_y = −5`, `net_shift(EF)` reduces to `−lead`,
so meeting the report constraint would need a *negative* lead. The inconsistency
is in the choice of axis, not in the value of the lever.

Your `Notes` line *"EF already L3 in 2025"* is **right about the hardware and
wrong about the certificate.** That is the whole finding in one sentence.

---

## 5. What the AB/CD data shows (demoted from the earlier draft)

The Europe top-10 BEV list (Feb 2026) is entirely A–D segment. All ten top out
at L2: Tesla FSD (Supervised), VW/Škoda Travel Assist, Renault Active Driver
Assist, BMW Driving Assistant Professional, and basic LKA/ACC on the Leapmotor
T03. Useful for the **AB and CD** rows of any tier table, and as the floor that
EU GSR-2 pins from July 2024. **Not evidence about EF.**

---

## 6. Proposed fix: re-key on a hardware tier

Replace SAE level as the model's internal driver with an **ADAS hardware tier**;
let SAE level become a descriptive attribute, not the index.

| Tier | Typical name | Cameras | Radar | Lidar | Ultrasonic | SAE label seen |
|---|---|---|---|---|---|---|
| **H0** | GSR-2 mandated basics | 1 | 1 | 0 | 0–4 | L0 / L1 |
| **H1** | ACC + lane keeping | 1–2 | 1–3 | 0 | 8–12 | L2 |
| **H2** | hands-off highway | 5–8 | 3–5 | 0 | 12 | L2+ |
| **H3** | urban + highway "L2++" | 8–12 | 5 | 0–1 | 12–16 | L2++ **or** L3 |
| **H4** | redundant, liability transfer | 6–12 | 5–6 | 1–3 | 12–13 | L3 |

H3 and H4 rows are now **anchored on the measured EF cars in §2.3**, not
invented: EX90 sits in H3 at L2, Drive Pilot in H4 at L3, and they differ by
about one lidar. H0–H2 remain placeholders pending the data in §8.

Two properties this buys:

- The big hardware step (H1 → H2/H3) becomes an explicit boundary, so the
  quantity that drives wiring is the quantity being modelled.
- A car can move H3 → H3 while moving L3 → L2 (the Volvo case) without the
  wiring result changing — which is correct.

Mapping onto the existing structure: `Sensors_per_Level` → `Sensors_per_Tier`,
`Autonomy_Derived` emits tier shares instead of level shares, `Metres_per_Sensor`
unchanged.

**Lidar becomes its own driver**, independent of tier, because §2.5 shows it no
longer tracks either tier or segment.

---

## 7. Analyst and technology-monitor sources

Searched 2026-08-05. **The thesis in §1 is the consensus position of every
analyst house checked** — not an inference of ours. Detailed figures are
paywalled; below is what is public.

### 7.1 The consensus

| Source | Statement |
|---|---|
| **IDTechEx** | L2+ outpaces L3 in Europe. L3 hit "significant regulatory setbacks"; only Germany and Japan have limited deployment while L2+ (Super Cruise, BlueCruise) spread across 20+ models. L2+/L3 global adoption >50% by 2035 |
| **S&P Global Mobility** | "the adoption of Level 2+ will significantly outpace that of Level 3 systems throughout the 2024–2030 period". German premium OEMs are "subtly easing off their Level 3 ambitions as their latest Level 2+ systems come to market" — i.e. **explicitly about EF** |
| **SBD Automotive** | L2+ is the "responsible and commercially sound bridge"; L3 blocked by liability, cross-country regulation, and too narrow an operational domain |

The S&P line is the most directly EF-relevant public statement found: it names
the German premium OEMs and describes exactly the retreat observed in §2.2.

### 7.2 Quantitative anchors in public material

| Quantity | Value | Source |
|---|---|---|
| **Ranging sensors (radar+lidar) per vehicle** | **2.5 (2025) → 5.5 (2035)** | Yole via IndexBox |
| Radar share of ranging-sensor units | 65–75% in 2026 | Yole via IndexBox |
| Lidar attach rate, A/B segment | <15% until at least 2028 | suppliers via IndexBox |
| Global ADAS penetration | 66% (2025) → 94% (2035) | Counterpoint |
| L2+/L3 share of global new sales | ≥31% by 2035 | S&P Global Mobility |
| L2 vs **L3** compute cost per vehicle | $200–400 vs **$800–1,500** | SBD / TechAD 2026 |
| Automotive lidar market | $9.5 bn by 2034 | IDTechEx |
| Lidar + thermal share of sensor revenue | 26% by 2036 | IDTechEx |

The compute-cost row corroborates the §2.2 withdrawals from an independent
direction: a 3–4× compute step on top of the lidar cost.

### 7.3 Reports worth buying, ranked by fit to EF

1. **IDTechEx — _Passenger Car ADAS Market 2025-2045_** (report 1080).
   **Best fit.** 14 major L1–L2+/L3 features, adoption forecast **by region
   (US, Europe, China, Japan) over 20 years**, with sensor-suite comparisons and
   SoC analysis. Feature-level adoption by region is the tier axis §6 needs.
   **Ask before buying: does it segment by vehicle class?** If it forecasts only
   at market level, it fixes the tier axis but not the EF question.
   <https://www.idtechex.com/en/research-report/passenger-car-adas-market-2025-2045-technology-market-analysis-and-forecasts/1080>
2. **S&P Global Mobility — _Autonomy Forecasts_.** The only source found that
   forecasts **L2+ as its own category**, and the one already making
   EF-specific statements. Also the reference for open item 3 (SDV timing).
   Subscription, not a one-off.
   <https://www.spglobal.com/mobility/en/products/autonomy-forecasts.html>
3. **SBD Automotive — _ADAS Sensor Market Landscape_.** Sensor-count-per-vehicle
   framing, the exact gap in `Sensors_per_Level`. Free preview PDF exists; it
   resisted text extraction here (no `pypdf`/`pdftotext` on this machine) and
   should be opened by hand.
   <https://insight.sbdautomotive.com/rs/164-IYW-366/images/Preview%20-%20ADAS%20Sensor%20Market%20Landscape.pdf>
4. **Yole Group** — radar/lidar/camera reports; source of the 2.5 → 5.5 series
   and the sub-15% lidar attach rate. Best for the per-sensor-type split and §2.5.
5. **IDTechEx — _Automotive Radar Market 2025-2045_ (1061), _Sensor Market
   2026-2036_ (1137).** Narrower fallbacks.
6. **Counterpoint Research** — independent check on the top-line curve; thin on
   hardware.

### 7.4 What none of them appears to publish

- **Per-model take-rates.** Every source forecasts feature or category
  penetration; none publishes what fraction of i5 or EQS buyers actually bought
  the higher ADAS package. May not exist publicly.
- **Sensor content split by vehicle segment.** The critical gap for this
  project. §2.3 had to be assembled car-by-car from press material.
- **Wiring or harness length per tier.** No source connects ADAS tier to harness
  metres. That link stays this project's own contribution; the `17_` ÷ `06_`
  check (28 / 25 / 31 m per camera) remains its only empirical anchor.

---

## 8. What still has to be found

1. **EF-segment tier shares over time** — the replacement for the
   certification-derived autonomy mix. Needs §7.3 item 1 or 2.
2. **Sensor counts for tiers H0–H2**, sourced (H3/H4 now anchored).
3. **Lidar attach rate, Europe vs China, split by segment** — §2.5 shows one
   number will not do.
4. **EF share of European BEV new sales, and its trend** — §2.6 suggests it is
   falling; needed only if results are weighted by volume.
5. **Take-rates** (§7.4), if obtainable at all.

---

## 9. Sources

**§2 — EF evidence**

- electrive, 2026-02-23 — BMW abandons Level 3, following Mercedes:
  <https://www.electrive.com/2026/02/23/following-mercedes-bmw-also-abandons-level-3-automated-driving/>
- WardsAuto — Mercedes shifts to L2++ in the 2026 S-Class:
  <https://www.wardsauto.com/news/mercedes-benz-shifts-autonomous-driving-tech-in-2026-s-class/811431/>
- AutoBuzz, 2025-12-01 — no more lidar for Volvo EX90, ES90, Polestar 3 in 2026:
  <https://autobuzz.my/2025/12/01/no-more-lidar-sensors-for-volvo-ex90-es90-and-polestar-3-in-2026/>
- The Drive — Volvo drops Luminar and lidar for 2026 models:
  <https://www.thedrive.com/news/volvo-has-dropped-luminar-and-lidar-for-2026-models>
- Mercedes-Benz Group — Drive Pilot sensor set:
  <https://group.mercedes-benz.com/innovation/case/autonomous/drive-pilot-2.html>
- BimmerToday, 2024-12-09 — BMW 7 Series G70 Personal Pilot L3 sensor setup:
  <https://www.bimmertoday.de/2024/12/09/bmw-7er-g70-video-erklart-personal-pilot-l3-sensor-setup/>
- CnEVPost, 2026-05-09 — BYD Seagull, first entry-level EV with lidar:
  <https://cnevpost.com/2026/05/09/byd-launch-2026-seagull-may-11-lidar/>
- KrASIA — Hesai's USD 200 lidar model:
  <https://kr-asia.com/china-lidar-maker-hesai-looks-to-prove-musk-wrong-with-usd-200-model>
- BigGo Finance — lidar costs down 99.5% in 8 years, optional extra to standard:
  <https://finance.biggo.com/news/ZU6xbZ4BrAZSr0oSetvc>
- ChinaEVHome, 2026-05-06 — Hesai leads global ADAS lidar shipments, Chinese
  suppliers at 95% share; 2025 market >$1 bn, +60% YoY, 3.7 m units:
  <https://chinaevhome.com/2026/05/06/hesai-leads-global-adas-lidar-shipments-as-china-suppliers-take-95-share/>
- Tianxia Gongchang — China intelligent driving supply chain 2026; lidar
  penetration 21% of NEVs in 2025, past the 16% chasm threshold:
  <https://faxiangongchang.com/en/reports/china-intelligent-driving-2026>
- Astute Analytica, 2026-01-20 — automotive lidar market to $25.75 bn by 2035:
  <https://www.globenewswire.com/news-release/2026/01/20/3222187/0/en/Automotive-LiDAR-Market-Projected-to-Reach-US-25-75-Billion-by-2035-Supported-by-Increasing-Series-Production-Adoption-Says-Astute-Analytica.html>
- Yole via Hesai — no.1 in long-range ADAS lidar shipments 2025:
  <https://www.hesaitech.com/hesai-secures-no-1-in-long-range-adas-lidar-shipments-in-2025-by-yole-group/>
- L4DR: LiDAR-4DRadar fusion for weather-robust 3D detection (AAAI) — lidar and
  camera degrade in fog/rain, 4D radar minimally affected:
  <https://arxiv.org/html/2408.03677v3>
- 4D Radar Meets LiDAR and Camera: cooperative perception under adverse weather
  (CVPR 2026 workshop): <https://arxiv.org/html/2606.00416v1>
- SCMP — China's low-cost EVs fitted with lidar:
  <https://www.scmp.com/business/china-evs/article/3350948/chinas-low-cost-evs-be-fitted-lidar-systems-usually-reserved-luxury-models>
- Dealroom — BAIC signs Hesai lidar contract for 2026 models:
  <https://app.dealroom.co/news/feed/baic-signs-hesai-lidar-contract-for-2026-models-as-china-s-l3-autonomy-push-accelerates-adoption>
- EV.com / CarBuzz — Mercedes to phase out EQE sedan and SUV by 2026:
  <https://ev.com/news/mercedes-benz-phase-out-eqe-sedan-suv-by-2026>
- Autoblog — Mercedes quietly preparing to end the EQS:
  <https://www.autoblog.com/news/mercedes-is-quietly-preparing-to-end-the-slow-selling-eqs>

**§5 — AB/CD evidence**

- best-selling-cars.com — Europe, February 2026, best-selling electric models:
  <https://www.best-selling-cars.com/europe/2026-february-europe-best-selling-electric-car-brands-and-models/>

**§7 — analyst material**

- IDTechEx — L2+ ADAS outpaces L3 in Europe, US$4 B by 2042:
  <https://www.idtechex.com/en/research-article/l2-adas-outpaces-l3-in-europe-us-4b-by-2042/32860>
  (fetchable mirror: <https://www.signalintegrityjournal.com/articles/3895-l2-adas-outpaces-l3-in-europe-us4-b-by-2042>)
- S&P Global Mobility — From 'eyes-off' hype to 'hands-free' reality: premium
  OEMs bet big on L2+:
  <https://autotechinsight.spglobal.com/news/5287492/from-eyes-off-hype-to-hands-free-reality-premium-oems-bet-big-on-l2->
- Counterpoint Research, 2026-03-26 — global ADAS penetration to 94% by 2035:
  <https://counterpointresearch.com/en/insights/Global-ADAS-Penetration-to-Reach-94-Percent-by-2035>
- IndexBox (citing Yole) — detection and ranging sensor outlook to 2035:
  <https://www.indexbox.io/blog/automotive-detection-and-ranging-sensor-market-forecast-points-higher-toward-2035-driven-by-adas-mandates-and-sensor-fusion-advances/>
- Focal Point Positioning — TechAD Europe 2026, L2/L3 compute cost split:
  <https://focalpointpositioning.com/resources/insights/blogs/adas-trends-2026-key-insights-from-tech-ad-europe-in-berlin/>
- IDTechEx report pages: 1080 ADAS, 1061 radar, 1137 sensors — see §7.3.
