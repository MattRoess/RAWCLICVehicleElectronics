# Driver E — brand origin — design note

**Purpose.** The European market is no longer one population. Chinese-brand
vehicles are ~10% of it and carry markedly different sensor content. The models
currently represent this with a single blended curve, which cannot express a
mixture.

Written 2026-08-10. **Nothing here is implemented.** This is the document that
gets agreed before code, per the project's sequencing rule.

Companions: `SENSOR_MODEL_DESIGN.md`, `ADAS_Sensor_Adoption_Report_2025_2070.md`,
`../Wiring/IMPLEMENTATION_GUIDE.md`.

---

## 1. The finding that shaped this note

I began from the assumption that Chinese brands would pull lidar into Europe.
**They do not.** They de-specify for the European market:

| BYD system | Market | Content |
|---|---|---|
| DiPilot 300 | **China only** | RoboSense lidar, 350 m range |
| **DiPilot 100** | **Europe**, incl. Dolphin Surf | **12 cameras, 5 radars, 12 ultrasonics — no lidar** |

FACT. Reporting is explicit that European versions lack the camera suite of the
latest Chinese ADAS releases.

But look at what Europe *does* receive: **12 cameras and 5 radars on an
A-segment car.** A VW ID.3 carries roughly 4–6 cameras and 1–3 radars.

**So the effect is on the hardware TIER, not on lidar.** That relocates the
whole driver: it modifies **Driver A (tier shares)**, and leaves **Driver B
(lidar) untouched**. The existing China→Europe lidar lag stays exactly as it is.

This is the opposite of what the naive "China leads, Europe follows" story
predicts, and it is why this note exists rather than a parameter tweak.

---

## 2. Why a blended curve cannot do the job

`Tier_Shares` in `19_` is one table per segment. It was calibrated against
observed European market data — which **already contains ~10% Chinese-brand
vehicles**. So it is a blend of two very different populations:

    observed = (1 - s) x European-brand + s x Chinese-brand

A single curve reproduces the *mean* and destroys the *mixture*. The
consequences are the ones this project has met three times already:

- the band is too narrow, because bimodality is averaged away;
- the correlation is lost — a Chinese-brand car has more cameras **and** more
  radars **and** a different architecture *together*, not independently;
- and the trend is wrong, because `s` is moving fast (5% → 10% of plugins in
  twelve months) while the blend treats the population as fixed.

Same structural error as the 400V/800V mixture inside a min–max range, and as
share-weighting the architecture states before they were made discrete.

---

## 3. Driver E — the state

A **discrete per-vehicle brand-origin state**, drawn from one uniform per
iteration and held across years, exactly like architecture and voltage.

    origin ∈ { European-brand, Chinese-brand }

**Brand, not build location.** This distinction is load-bearing and the data
forces it:

| | 2024 | Q1 2026 |
|---|---|---|
| BEVs **built in** China, share of EU BEV | 22% | **17%** (falling) |
| Chinese **brands**, share of European market | 4.5% | **10.9%** (rising) |

The two are diverging. A Cupra Tavascan built in Shanghai carries European
sensor spec; a BYD built in Szeged carries BYD's. **Sensor content follows the
brand's product decisions, not the factory's postcode.** Tariffs target build
location, which is precisely why localisation defeats them.

---

## 4. The share curve

### 4.1 Anchors

| Year | Value | Tag | Basis |
|---|---|---|---|
| 2020 | ~0.01 | FACT | Chinese brands barely present |
| 2025 | **0.05** | FACT | 5% of European plugins, June 2025 |
| **2026** | **0.10** | **FACT** | 10% of European plugins, June 2026; 10.9% of the total market |
| 2035 | **0.15 / 0.22 / 0.30** | see §4.2 | T&E bracket |

**One honest gap.** No source publishes Chinese-brand share of **BEV alone**.
What exists is share of *plugins* (BEV+PHEV, ~10%) and share of the *total*
market (10.9%). Much of their European volume is PHEV — CleanTechnica flags the
BYD Atto 2's 13,100 June units as "mostly PHEV" — so their **BEV-only share is
plausibly slightly below 10%**. The 2026 anchor is therefore DERIVED, not FACT,
and should carry a band of roughly 0.08–0.12.

**A figure to discard.** One source claims 31% of the European BEV market by
March 2026. It exceeds T&E's own 2035 projection under weakened targets, its
provenance is untraceable, and it is inconsistent with every other measure.
Recorded here so it is not picked up later.

### 4.2 Scenarios

Each keyed to an **observable policy lever**, not a tuned number. Both levers
are decided within roughly 18 months.

| | Mechanism | 2030 | **2035** | long-run ceiling |
|---|---|---|---|---|
| **C1 Contained** | CO₂ targets hold; the 70% local-content rule is enacted and enforced; plants underrun | 0.13 | **0.15** | ~0.20 |
| **C2 Localisation** *(mode)* | Plants ramp as announced, local content is met, rules soften | 0.18 | **0.22** | ~0.35 |
| **C3 Open** | CO₂ targets weakened; cost advantage wins | 0.25 | **0.30** | ~0.45 |

The 2035 column is **T&E's published bracket**: ~15% under current CO₂ targets,
~30% under weakened targets. C2 interpolates. Independent check: AlixPartners
puts Chinese brands at 17% of the *total* European market by 2031.

None of the ceilings reach dominance — brand loyalty, dealer networks and fleet
channels are real. ASSUMPTION, and the weakest part of the curve.

### 4.3 Evidence class — read with §1.2 of the report

**T&E is an advocacy organisation** (clean transport). Its bracket is useful and
its mechanism is real, but the "weakened targets" branch is framed as a warning
and it is not neutral forecasting in the way Yole or S&P shipment data is. It
belongs in the *technology-led / modelled* class, not the *counts things* class.

---

## 5. What the state changes

### 5.1 Tier shares, split in two

Given the state, a different tier distribution applies. The **published
`Tier_Shares` is the blend**, so the European-brand table must be **backed out**,
never assumed:

    European = (observed - s x Chinese) / (1 - s)

**This is the renormalisation trap for the fourth time in this project.**
Applying a Chinese-brand uplift on top of the existing table without backing the
blend out would count the same 10% twice — exactly the failure documented as the
#1 silent breaker in `BevWiring_STATUS.md` §5.

**Anchor for the Chinese-brand table.** DiPilot 100 — 12 cameras, 5 radars,
12 ultrasonics — maps onto **H3** in `19_` sheet `Tiers` (8–12 cameras, 5 radar,
12–16 ultrasonic). And it ships on an **A-segment** car, where the current AB mix
has H0 0.45 / H1 0.45 / H2 0.10 / **H3 0.00**.

So a Chinese-brand AB vehicle sits roughly **two to three tiers above** its
European equivalent. That gap, not the share alone, is what moves the answer.

### 5.2 Lidar — unchanged in the base case, but the flip is now modelled

Driver B is untouched *while de-specification holds*. Chinese brands do not
bring lidar to Europe today (§1). But that is a strategy, not a law, and the
hardware already exists in volume production — so the end of de-specification is
sampled rather than excluded. See **§5.4**.

A €25k car with 12 cameras forces European OEMs to respond or lose the segment.
So a higher Chinese share does not merely *add* high-tier cars — it **pulls the
European-brand tier curve up too**.

Proposed mechanism, reusing machinery that already exists: the scenario applies
a **timing offset** to the European-brand tier curve — C3 pulls European
adoption earlier by a few years, C1 by none. ASSUMPTION, and it should be
sampled rather than fixed.

**This is what the 7-year lidar lag was crudely approximating.** Made explicit,
a lag can fall out of the mechanism instead of being asserted.

### 5.4 `T_DESPEC_END` — when de-specification ends

**The trigger is regulatory, and it is NOT urban driving.** This took research
to establish and it inverts the obvious assumption:

| Path | Regulation | Status | Requires lidar? |
|---|---|---|---|
| Urban hands-off assistance | **UN R171 (DCAS)**, 02 series **voted 24 June 2026** | **open** — enables hands-off on highway and "highway-like" roads, system-initiated manoeuvres, and manoeuvres in **non-highway** environments | **No** |
| Liability transfer | UN R157 (ALKS) | exists; Mercedes paused Drive Pilot, BMW discontinued Personal Pilot L3 | **Yes** |

R171 is explicitly Level 2 — *"DCAS only assists the driver but never replaces
the driver… there is no transfer in the driver's responsibility."* And BYD
proves the point commercially: God's Eye C / DiPilot 100 is **camera-and-radar
only** and already performs urban work in China.

**So urban NOA arriving in Europe does not force lidar.** What forces lidar is
**L3 liability transfer** — the path European OEMs just retreated from.

Deployment dates, from the OEMs themselves (FACT):

| | Highway NOA | Urban NOA |
|---|---|---|
| MG (SAIC — Chinese) | **2027** | **no earlier than 2028** |
| BMW | — | urban system on German roads **2026**; first in Germany with DCAS approval |

Note **BMW is ahead of MG on urban in Europe.** For this market the binding
constraint is European homologation and European road data, where European OEMs
start advantaged — MG's 1.2 million km across 24 countries is them buying past
exactly that constraint.

**What changes the calculus: the EU Automotive Omnibus** (COM(2025) 95 final).
It creates type approval for **unlimited-series** production with automated
driving functions, harmonised on-road ADS testing procedures, and regulatory
sandboxes from 2026 — and it is a **2026 legislative priority** in the Joint
Declaration of Parliament, Council and Commission.

This is the gate R157 never provided. R157 permitted L3 only as a narrow,
per-model, geofenced approval, which is precisely why Mercedes and BMW found it
uneconomic. Unlimited-series ADS approval changes that.

**Proposed parameter:**

    T_DESPEC_END ~ triangular(2028, 2031, 2038),  P(never) = 0.20

    before T:  Chinese-brand lidar attach in Europe = 0   (as today)
    after  T:  ramps toward the Chinese domestic rate

| Bound | Basis |
|---|---|
| **2028** earliest | MG's own stated urban date; no Chinese brand has yet sought R157 approval in Europe |
| **2031** mode | Omnibus on a 2026–28 legislative timetable; Waymo commercial in Munich/Berlin from 2027 builds HD mapping, supplier base and public acceptance that private L3 also needs |
| **2038** latest | slow legislative passage plus continued OEM reluctance |
| **P(never) = 0.20** | R171 gives European OEMs a **lidar-free** route to urban hands-off driving, which may simply prove commercially sufficient |

**Why this belongs on Driver E and not Driver B.** Numerically the flip lands
inside Driver B's existing Max band — a 2030 flip at C2 share with ~80% attach
adds ~14 pp, taking 2030 from Mode 0.12 to ~0.26 against a Max of 0.30. But
Driver B's Max represents *cost collapse and regulatory pull on European OEMs*.
Reaching the right number through the wrong mechanism is the error this project
keeps catching. And the flip is **correlated with origin** — the lidar arrives on
cars that already carry 12 cameras and 5 radars — which two independent drivers
cannot express.

---

## 6. Where it plugs in

Both models, from one source — like the 800V share.

| Model | Effect |
|---|---|
| `SensorNumbersMC.py` | tier state → `Presence_per_Tier` composition → sensor counts |
| `Wiring/BevWiring.py` | tier state → sensor counts → ADAS metres |

Data would live in `19_` as two new sheets — `Brand_Origin_Share` and
`Tier_Shares_Chinese` — with the scenario selection in `20_` alongside
S1/S2/S3, as a **second independent axis**. Not folded into S1/S2/S3: those are
about *sensing philosophy*, this is about *market composition*, and they are
orthogonal.

---

## 7. Validation targets

| # | Target | Tolerance | Catches |
|---|---|---|---|
| **V16** | blend of the two tier tables at 2026 reproduces the current `Tier_Shares` | 1e-9 | **the double-count in §5.1** |
| **V17** | Chinese-brand share at 2026 | 0.10 ± 0.02 | the anchor drifting |
| **V18** | composed camera count, Chinese-brand AB vehicle, 2026 | 12 ± 3 | the DiPilot 100 anchor |
| **V19** | both models draw the same origin state for the same year | exact | the two models describing different vehicles |

V16 is the important one and it is the same shape as V11.

---

## 8. Weakest inputs, ranked

1. **The de-specification assumption — now sampled, not assumed (§5.4).** The
   base case rests on Chinese brands not shipping lidar to Europe. That is true
   today and sourced, and the research strengthened it: the regulatory gate that
   is opening (R171 DCAS, urban hands-off) is **Level 2 and needs no lidar**,
   while the gate that would force lidar (R157, liability transfer) is the one
   European OEMs just abandoned. The residual risk is handled by
   `T_DESPEC_END`, with `P(never) = 0.20`. **Still the item to monitor** — the
   hardware exists in volume production, so a strategy change would show up in
   product within one model cycle.
   **Watch item:** Waymo's European platform partner is **Zeekr**, a Chinese
   brand. If the highest-sensor-content vehicles operating in European cities
   are Chinese-built, that cuts against de-specification in a way not yet
   quantified. Fleet, not private sales, so outside the model — but the sort of
   thing that precedes a strategy change.
2. **Chinese-brand BEV share is inferred**, not published (§4.1).
3. **The competitive-response offset** (§5.3) is pure assumption.
4. **The long-run ceilings** (§4.2) are assumption.
5. **T&E's bracket is advocacy-sourced** (§4.3).

---

## 9. Proposed implementation order

| Step | Work | Verified by |
|---|---|---|
| **E1** | Add `Brand_Origin_Share` to `19_`, scenarios to `20_`. No code. | sheets load; weights sum to 1 |
| **E2** | Back out the European-brand tier table from the blend (§5.1) | **V16** |
| **E3** | Add the origin state to `SensorNumbersMC.py` | **V17**, **V18** |
| **E3b** | Add `T_DESPEC_END` (§5.4) — sampled, with "never" admissible | **V20**: lidar attach on Chinese-brand cars is exactly 0 before the drawn year |
| **E4** | Add the same state to `BevWiring.py` | **V19**, wiring V1–V10 unchanged at 2025 |
| **E5** | Competitive-response offset (§5.3) | sensitivity run, both models |

E2 is the risky one. E3b is small — one parameter and one conditional — and
belongs inside E3 rather than after it. E5 is separable and could be dropped
without losing the rest.

---

## 10. What this does NOT address

- **PCB.** Step 7 of the sensor plan is still untouched, and the `01_` re-run
  debt is still owed before it starts.
- **Production location.** Deliberately out of scope (§3). If tariffs or local
  content ever bind on *content* rather than *assembly*, that becomes a separate
  question.
- **Non-Chinese non-European brands** — Korean (Hyundai/Kia on E-GMP, 800V and
  well-equipped), Japanese, American. Lumped into "European-brand" today, which
  is a simplification worth revisiting if the origin split proves useful.

---

## 11. Sources

- Automotive News — Chinese brands hit record 10.9% share in Europe in June: <https://www.autonews.com/retail/sales/ane-europe-chinese-sales-june-2026-0721/>
- CleanTechnica, 2026-08-02 — Europe EV sales report; Chinese OEMs 5% → 10% of plugins: <https://cleantechnica.com/2026/08/02/europe-ev-sales-report-bevs-jump-50-reach-26-market-share/>
- Transport & Environment — presence of Chinese automakers in the EU car market; 2035 BEV bracket, made-in-China share 22% → 17%: <https://www.transportenvironment.org/articles/presence_chinese_automakers_eu_car_market>
- T&E — are the EV tariffs working: <https://www.transportenvironment.org/articles/are-the-ev-tariffs-working-western-carmakers-shifted-production-to-eu-but-chinese-brands-continue-to-grow-analysis>
- Automotive News — EU to propose 70% local content rules: <https://www.autonews.com/manufacturing/automakers/ane-local-content-eu-0217/>
- BusinessWorld — EU Industrial Accelerator Act, 2026-03-04: <https://www.bworldonline.com/world/2026/03/04/734159/eu-to-lay-out-local-content-rules-to-strengthen-manufacturing-cut-china-reliance/>
- SCMP — China-EU price undertakings replacing tariffs: <https://www.scmp.com/business/china-business/article/3339914/china-eu-tariff-agreement-evs-seen-cutting-shipments-boosting-profitability>
- electrive, 2026-02-02 — BYD begins trial production in Hungary: <https://www.electrive.com/2026/02/02/byd-begins-trial-production-of-passenger-cars-in-hungary/>
- CnEVPost — Chery JV plant Spain first car: <https://cnevpost.com/2024/11/25/chery-jv-plant-spain-sees-1st-car-off-line/>
- InsideEVs — Stellantis to build Leapmotor B10 in Spain: <https://insideevs.com/news/788910/stellantis-leapmotor-b10-spain-production/>
- CarNewsChina — BYD entry-level hatchbacks with lidar (China): <https://carnewschina.com/2026/01/09/byd-entry-level-hatchbacks-to-feature-lidar-sensors-in-china/>
- Inside China Auto — BYD DiPilot 100 / 300 split: <https://insidechinaauto.com/2025/02/11/byd-rolls-out-autonomous-driving-features-free-to-entire-range/>

**Regulatory timeline (§5.4)**

- UNECE — new UN regulation on DCAS; R171 in force 30 Sept 2024: <https://unece.org/media/press/395206>
- UNECE — proposal for the new **02 series** of amendments to UN R171, voted 24 June 2026: <https://unece.org/transport/documents/2025/11/working-documents/tf-adas-proposal-new-02-series-amendments-un>
- Applied Intuition — understanding DCAS and UN R171: <https://www.appliedintuition.com/blog/navigating-dcas-regulations>
- Future Transport News — **MG roadmap**: highway NOA 2027, urban NOA no earlier than 2028, 1.2 m km across 24 European countries: <https://futuretransport-news.com/mg-outlines-roadmap-for-deploying-driver-assistance-technology/>
- **EU Automotive Omnibus, COM(2025) 95 final** — unlimited-series ADS type approval, harmonised on-road testing, regulatory sandboxes from 2026: <https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex:52025DC0095>
- ETSC briefing on the Automotive Omnibus, March 2026: <https://etsc.eu/wp-content/uploads/2026-03-ETSC-briefing-automotive-omnibus-final.pdf>
- Taylor Wessing — legal framework for automated driving in the EU and Germany: <https://www.taylorwessing.com/en/insights-and-events/insights/2026/02/legal-frameworks-for-autonomous-driving-and-teledriving>

*Waymo's European entry (London 2026, German subsidiary, commercial 2027) was
supplied by the user. It sits outside the model's population — private new BEV
sales, not fleets — but informs the `T_DESPEC_END` mode via the mapping,
supplier-base and acceptance effects, and via the Omnibus it helped motivate.*
