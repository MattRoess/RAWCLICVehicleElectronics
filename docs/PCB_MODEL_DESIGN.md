# PCB models — design note (step 7)

**Purpose.** Give `PCBAreaMC` and `PCBElementMC` a time axis and couple them to
the drivers the wiring and sensor models already use.

Written 2026-08-10. **Status 2026-08-11: P-a, P-b', P-c, P-d and P-e are
implemented and committed; P-b is deferred and P-f, P-g are not started.**
P-e is committed with a KNOWN FAILING validation -- P1 for AB -- see §2.2j.
The step table in §6 is the authoritative status.

Companions: `SENSOR_MODEL_DESIGN.md` (the same job, for sensors),
`STATIC_MODELS_DIAGNOSTIC.md` (what is currently frozen),
`../Wiring/IMPLEMENTATION_GUIDE.md`.

---

## 1. The finding that decides the design

I assumed the ADAS tier driver would carry this work, as it did for sensors.
**It will not.** Measured where PCB area actually sits, EF:

| Domain | area mm² | share |
|---|---|---|
| **HV Powertrain** | 7,955 | **30.8%** |
| **Infotainment** | 3,438 | **13.3%** |
| Body | 1,575 | 6.1% |
| Thermal | 1,536 | 5.9% |
| HMI | 1,438 | 5.6% |
| Control | 1,348 | 5.2% |
| LV Power | 1,043 | 4.0% |
| **ADAS** | **1,011** | **3.9%** |
| everything else | 6,508 | 25.2% |

**ADAS is eighth, under 4%.**

It is 8.3% of board *count* but only 3.9% of *area*, because ADAS components
carry almost entirely **small** boards (35 mm² at mode) while area is dominated
by medium (168 mm²) and large (550 mm²) boards elsewhere. **No ADAS component
carries a large board at all** — even the domain controller and the central
computer are medium.

So the drivers that matter here are the **two oldest ones in the project**, not
the newest:

| Rank | Driver | Reaches | Already exists? |
|---|---|---|---|
| **1** | **Voltage 400V/800V** | HV Powertrain — OBC, DC/DC, inverters, e-axle — **30.8%** | **yes**, `18_` |
| **2** | **Architecture SDV/zonal** | Control, Body, LV Power, Infotainment consolidation — **~29%** | **yes**, `18_` |
| 3 | ADAS hardware tier | ADAS — 3.9% | yes, `19_` |

Had this note not been written first, step 7 would have added the tier driver,
moved the answer by about 1%, and declared PCB "in line" while the two effects
that actually matter stayed frozen.

---

## 2. What each driver does to PCB, physically

### 2.1 Voltage — the largest block

The top of the component list is almost entirely HV power electronics:

| Component | EF area | share |
|---|---|---|
| Combined OBC + DC/DC module | 1,370 | 5.3% |
| HV-LV DC/DC converter | 1,094 | 4.2% |
| On-board charger (OBC) | 1,094 | 4.2% |
| Main traction inverter (front) | 926 | 3.6% |
| Rear traction inverter | 926 | 3.6% |
| Integrated e-axle | 926 | 3.6% |

800V changes these — SiC rather than Si switches, different gate-drive and
filtering, and a strong integration trend (note that *both* "Combined OBC +
DC/DC module" and the separate OBC and DC/DC appear as distinct components,
which is the consolidation already represented in `01_`).

**Direction is not obvious and must not be assumed.** SiC dies are smaller and
switch faster, which shrinks magnetics and heatsinking; but 800V needs greater
creepage and clearance, which grows board area. These oppose.

### 2.1a RESEARCHED 2026-08-10 — step P-a result

**The shrink wins, but the dominant effect turns out to be consolidation, not
scaling.**

**Growth force — creepage.** 800V DC at pollution degree 2, material group IIIa
requires **8 mm** minimum creepage, against roughly **2.5–4 mm** at 400V working
voltage. Close to a doubling. Two things limit it: IEC 60664-1 gives PCBs
*relaxed* requirements compared with other insulators, and material choice moves
it a long way — a CTI ≥600 material (group I) needs **nearly half** the creepage
of group IIIa. It also applies only at HV isolation barriers, not across the
whole board. FACT.

**Shrink force — SiC.** Roughly **3× smaller die area** at 750V versus 1200V
configurations, with reduced footprint and simplified cooling, and 3.5–8% better
efficiency than 400V IGBT. FACT.

**The decisive measurement — power density.** Integrated OBC + DC/DC modules have
gone from **1.5–2 kW/L (2018–20) to over 5 kW/L**, a 200–300% increase. One
cited part delivers 37.5 kW of conversion in a **92 × 80 mm** package. FACT.

**But power ratings rose at the same time** — OBC from **6.6 kW at 400V to
11–22 kW at 800V**. Since volume = power ÷ density and both roughly tripled:

| | direction |
|---|---|
| area **per kW** | falls sharply, ~3× |
| **absolute** area per vehicle | **roughly flat**, bounded about −33% to +10% |

**So the earlier worry was wrong in both directions.** 800V does not inflate
board area, and it does not greatly shrink it either. DERIVED.

**What it does do is consolidate.** Two-stage OBC + DC/DC designs are being
replaced by integrated single modules — and `01_` **already represents this**,
carrying *"Combined OBC + DC/DC module"* as a distinct component alongside the
separate *"On-board charger"* and *"HV-LV DC/DC converter"*.

**Consequence for the design: the 800V effect is expressible through the same
presence mechanism as everything else.** As 800V penetrates, presence shifts
toward the combined module and away from the two separate ones. No new scaling
factor is needed for the count — only a modest residual area term, whose band
should span zero.

Structurally identical to the ADAS camera ECU declining into the domain
controller. Third appearance of that pattern in this project.

### 2.2 Architecture — the second block

Zonal consolidation replaces distributed ECUs with fewer, larger controllers.
`01_` already represents this as **separate components** whose presence differs
by segment:

| Consolidating away | Consolidating into |
|---|---|
| Body Control Module, Door control modules | Zone controllers |
| Front power distribution centre (fuses) | Zonal PDU |
| Digital instrument cluster + head unit | Combined cluster+infotainment SoC |
| discrete domain ECUs | Powertrain / Chassis domain controller |

The wiring model already quantifies the same mechanism from the other side:
`17_` gives `LV_FUSE` an SDV factor of **0.65** and `CAN_BUS` **0.45**. The PCB
side of that trade has never been modelled.

**Magnitude anchors** (FACT): a premium 2020 vehicle carried **80–150 discrete
ECUs**; a fully realised zonal architecture reduces that to **fewer than 20**.
VW's SSP, from 2026, targets **ECUs down >50% and wiring down 40%** — and `17_`
already has wiring at −25% to −55% by category, so the two are consistent.
**55.5% of EF PCB area** sits in controller-like components (64 of 101), which
is the pool this driver can touch.

### 2.2a SUBSTITUTION GROUPS — the P-b mechanism, and a present-day defect

**Researched 2026-08-10. This changes P-b from a scaling table into a much
smaller and safer thing, and fixes an error that exists today.**

#### The problem, concretely

A car needs its battery charged from the wall (**on-board charger**) and needs
12 V made for lights and windows (**DC/DC converter**). Older designs use two
separate boxes; newer designs put both jobs in one **Combined OBC + DC/DC
module**. **A car has one arrangement or the other, never both.**

`01_` lists all three, and marks each `Std` for EF — which the model reads as
*"every car has this"*. So an EF vehicle is credited with a charger, a
converter, **and** a box that is a charger-and-converter.

| EF, board area | mm² |
|---|---|
| On-board charger | 1,094 |
| HV-LV DC/DC converter | 1,094 |
| Combined OBC + DC/DC module | 1,370 |
| **counted today** | **3,558** |
| a real car would carry | ~1,370–2,188 |
| **overcount** | **~2,189 = 8.5% of EF area** |

The same happens in the cockpit — separate head unit and instrument cluster
listed alongside the *Combined cluster+infotainment SoC*: another **5.1%**.

**Across both, roughly 12–14% of PCB area per segment.** The entire ADAS domain,
for comparison, is 3.9%.

**User's reading, confirmed 2026-08-10: these are alternatives — a mixture of
two designs, not additive.**

#### The five groups

Every one of them already exists in `01_` as separate rows. **No new components
are needed.**

| # | Group total | Discrete option | Integrated option | Split driven by |
|---|---|---|---|---|
| **G1** | charging + 12 V conversion, 1 per car | OBC **+** HV-LV DC/DC | **Combined OBC + DC/DC module** | voltage (800V) + integration trend |
| **G2** | drive units, 1–2 per car by AWD | Main / Rear traction inverter **+** motor | **Integrated e-axle (motor+inv+gear)** | integration trend |
| **G3** | cockpit compute, 1 per car | Head unit **+** digital instrument cluster | **Combined cluster+infotainment SoC** | architecture (SDV) |
| **G4** | vehicle control | BCM, door modules, discrete ECUs | domain controllers → **Zone controller** | **architecture, directly** |
| **G5** | ADAS compute | ADAS camera ECU (basic) | domain controller → central computer | ADAS tier — **already built**, `Presence_per_Tier` row 9 |

#### G4 needs no new data at all

This is the useful discovery. `01_`'s components map **one-to-one onto the three
architecture states the model already samples**:

| Architecture state (`18_`) | `01_` components |
|---|---|
| Conventional | BCM, door control modules, discrete ECUs |
| Transitional | Powertrain / Chassis / Body-comfort **domain controllers** |
| SDV_Zonal | **Zone controller (front/rear/etc.)**, central compute |

So G4's split probability **is** the architecture share already in `18_` sheet
`Penetration`. Nothing to invent, nothing to source. The one group with the
largest reach is the one that costs nothing to specify.

#### Is the shift a trend, or just a design preference?

**A trend, and it is measurable** (FACT):

| | |
|---|---|
| Integrated inverter-OBC-DC/DC market | **$2.82 bn (2024) → $12.08 bn (2033)**, 17.6% CAGR |
| Integrated OBC + DC/DC market | $2.5 bn (2025), **20% CAGR** |
| Status in 2026 | described as the **mainstream trend** — weight, cost, efficiency, reliability |

Integration goes further than two-in-one: **3-in-1** units fold the traction
inverter in as well, which is G1 and G2 merging.

`01_` already encodes the same trend as a *segment* gradient — the combined
module is `Opt` for AB, `Std` for CD and EF. Premium first, like every other
transition in this project.

#### How to sample it

`BevWiring_STATUS.md` §10 analysed the identical structure for CAN versus
Ethernet and recommended **option 2, substitution groups**:

> *Draw the GROUP total first, then draw the split between members.
> Anti-correlation within the group is then guaranteed by construction and the
> group total stays well-behaved. No invented correlation coefficients.*

Applied here:

    1. group total   -- 1 charging/conversion function per car (G1)
    2. draw the design:  integrated  or  discrete
           P(integrated | segment, year), rising with 800V and SDV share
    3. integrated -> one box;   discrete -> two boxes

**One draw per vehicle, held across years** — the same comonotonic scheme as
architecture and voltage. A car is one design, never a blend.

**This is the fourth appearance of this pattern** — CAN vs Ethernet, the ADAS
camera ECU declining into the domain controller, the 800V consolidation, and now
these five groups. It would be the first time it is actually built.

#### Two consequences

1. **The ~12% overcount disappears as a side effect** — not as a patch, but
   because the accounting becomes right. The group sums to one car's worth by
   construction.
2. **P-b shrinks.** It becomes a handful of *split probabilities* rather than a
   per-component scaling factor for 25–30 components. Smaller to specify, and
   much harder to get wrong.

### 2.2b P-b′ APPLIED, 2026-08-10 — the overcount is fixed

**15 cells changed in `01_`.** G1 and G3 members set to `Opt` in all three
segments — the 50/50 mixture, one of only three mixtures a four-level scale can
express self-consistently (0%, 50%, 100%; p = 0.25 and 0.75 would need a
presence of 0.75, which is not on the scale).

| | boxes per car, before → after |
|---|---|
| **G1** charging, AB / CD / EF | 2.50 → **1.50** / 3.00 → **1.50** / 3.00 → **1.50** |
| **G3** cockpit, AB / CD / EF | 1.75 → **1.50** / 2.50 → **1.50** / 3.00 → **1.50** |

A car has either one integrated box or two discrete ones, so a 50/50 mixture
averages 1.50. That is now true **by construction**.

**Measured effect on the model:**

| | before | after | |
|---|---|---|---|
| AB mean total area | 16,906.5 | **15,417.9** | **−8.80%** |
| CD | 23,309.1 | **20,633.0** | **−11.48%** |
| EF | 27,159.1 | **23,914.5** | **−11.95%** |
| **AB large PCBs** | 10.4 | **8.5** | **−18.1%** |
| **CD large PCBs** | 13.2 | **10.0** | **−24.5%** |
| **EF large PCBs** | 14.0 | **10.0** | **−28.6%** |

Large boards move most, which is the right signature: the charging and cockpit
modules are precisely the large-board components, while small and medium boards
shift only 2–4%.

**The PCB numbers were 9–12% too high**, and had been since before this work
started. This is a **correction to a counting error, not a change of model.**

**Why 50/50 and not a segment gradient:** the same decision as the `06_` battery
rows, which were rebased to a 400V *basis* so the file holds a neutral anchor
and the driver carries the transition. `01_` is now the neutral 2025 anchor; the
G1/G3 split probability will carry the trend, including the segment gradient —
which a driver expresses continuously instead of in four coarse steps.

#### G2 also fixed, 2026-08-10

Unlike G1 and G3, the group total here is not one unit but **one or two drive
units depending on AWD**, so it needed an AWD share.

**Evidence:** AWD is **45.4% of the European electric SUV market in 2025**
(FACT). SUVs skew high, so all-BEV AWD is lower and rises with segment. AB's
volume sellers are effectively all single-motor (Renault 5, Leapmotor T03,
ID.3); CD's are mostly RWD with AWD variants (Model Y, ID.4, Enyaq); EF is the
most AWD-heavy (iX is AWD-only, Taycan mostly AWD).

| | front inverter | rear inverter | e-axle | units/car | implied AWD |
|---|---|---|---|---|---|
| **AB** | `Std`→`Opt` | `Opt`→`–` | `Opt` | 2.00 → **1.00** | 0% |
| **CD** | `Std`→`Opt` | `Std`→`Rare` | `Std`→`Opt` | 3.00 → **1.25** | 25% |
| **EF** | `Std`→`Opt` | `Std`→`Opt` | `Std`→`Opt` | 3.00 → **1.50** | 50% |

Front unit always present, split 50/50 discrete vs integrated — the same neutral
anchor as G1 and G3. **The rear inverter's presence carries the AWD share**,
which is the only genuinely new judgment.

**Measured effect of G2 alone:**

| | before | after | |
|---|---|---|---|
| AB mean area | 15,417.9 | **14,385.1** | **−6.70%** |
| CD | 20,633.0 | **18,824.8** | **−8.76%** |
| EF | 23,914.5 | **22,365.3** | **−6.48%** |
| **CD large PCBs** | 10.0 | **7.4** | **−26.3%** |

Again concentrated in large boards — drive-unit electronics are large-board
components — with medium boards moving under 1.2%.

**Known limitation:** EF at 50% AWD is arguably low; 60–70% is probably truer.
But the four-level scale offers only 50% or 100% at that point, and 100% would
be clearly wrong. Same quantisation ceiling V13 hit. It is an argument for the
split eventually living in a **driver** rather than a label — which is exactly
what P-b will do.

#### Combined effect of P-b′ (G1 + G3 + G2)

| | original | after G1+G3 | after G2 | total |
|---|---|---|---|---|
| AB | 16,906.5 | 15,417.9 | **14,385.1** | **−14.9%** |
| CD | 23,309.1 | 20,633.0 | **18,824.8** | **−19.2%** |
| EF | 27,159.1 | 23,914.5 | **22,365.3** | **−17.6%** |
| EF large PCBs | 14.0 | 10.0 | **7.8** | **−44.3%** |

**PCB area was 15–19% too high**, and large-board counts were nearly double what
they should have been. All of it a counting error present before this work
started, none of it a modelling change.

**Verified after G2:** `SensorNumbersMC` V11 PASSED, V12 PASSED, V13 31/31,
V14 915/915, V15 PASSED; `SensorElementsMC` exit 0; `PCBAreaMC` exit 0;
wiring 9/9.

#### A warning for anyone editing `01_`

**Do not add a `Notes` sheet to `01_VehicleElectronics.xlsx`.**

I did, to protocol this change, and it **broke both sensor models**.
`SensorNumbersMC.py:126` and `SensorElementsMC.py:148` iterate *every* sheet in
the workbook with a fixed `usecols=['Domain','Component','A-B Segment',
'C-D Segment','E-F Segment']`. Any sheet lacking those five columns raises
`ValueError: Usecols do not match columns`.

`06_` and `18_` tolerate a `Notes` sheet because their readers name one sheet.
`01_` does not. The sheet was removed and this note is where that protocol now
lives instead. Caught only because `SensorElementsMC` failed loudly — it would
have been a silent breakage in a less strict reader.

### 2.3 ADAS tier — real but small

3.9% of area, and the tier composition is already built (`19_`
`Presence_per_Tier`). Cheapest of the three to wire in, and the least
consequential.

---

## 3. What is missing

**`01_` has no per-component architecture or voltage factor.** `17_` has
`SDV_Base_Length_Factor` for every wire category; `01_` has nothing equivalent.

So the work needs a new table, in the same shape as `Presence_per_Tier`:

    presence(component, segment, year)
        = Σ_state  share(state, segment, year) × presence(component | state)

with `state ∈ {Conventional, Transitional, SDV_Zonal}` for the architecture-
sensitive components, and `{400V, 800V}` for the HV ones.

**This is new data, not plumbing.** It is the same class of task as building
`Presence_per_Tier` was, and it needs the same FACT / DERIVED / ASSUMPTION
discipline. Roughly 25–30 of the 101 components are affected; the rest are
genuinely static and should stay so.

---

## 4. Architecture of the change

### 4.1 Share the presence logic, do not reimplement it

`SensorNumbersMC.py` already has `load_presence_per_tier(years)`. If
`PCBAreaMC` grows its own copy, the two will diverge — the exact failure V12
exists to catch, and the reason `_derive_autonomy` was never duplicated.

**Proposal: extract the presence composition into one small shared module**
(e.g. `tools/presence.py`) imported by both. Minimal refactor; single
implementation; the divergence check becomes trivial.

### 4.2 `11_` becomes an intermediate that cannot carry a year

`11_PCB_Distribution_Classified.csv` is a flat per-segment table. Adding a year
axis makes it 101 × 3 × 51 ≈ 15,000 rows, and puts the presence logic in a
third place.

**Proposal: `PCBAreaMC` reads `01_` + `19_` + `18_` directly**, composing
presence itself via the shared module, and `11_` stops being the PCB path's
input. It can remain as a diagnostic export.

*(This also disposes of the gitignored-input problem in
`STATIC_MODELS_DIAGNOSTIC.md` §5: `11_` stops being a required input.)*

### 4.3 Memory — the same wall, the same trick

101 rows × 200,000 draws × 51 years × 3 segments ≈ **24.7 GB**. Not possible.

But only ~25–30 of 101 rows are year-dependent. Same approach as the sensor
model: draw the year-independent base once per chunk, adjust only the affected
rows per year, and accumulate. Port the `Accumulator` from `SensorNumbersMC.py`
— which was itself ported from `BevWiring.py`, so this would be its third use
and the pattern is proven.

### 4.4 `PCBElementMC` follows for free

It reads `04_` — composition in mg/cm² per PCB category — and multiplies by
area. Once area is year-resolved, element mass is too. **No new driver needed**,
only the year dimension flowing through.

---

### 2.2c P-b RESCOPED 2026-08-10 — measure G4 first, defer G1–G3

**Per-unit board area for each group member (mode sizes) — the check that
changed the plan:**

| Group | discrete option | integrated option | saving from integrating |
|---|---|---|---|
| **G1** charging | OBC 1,094 + DC/DC 1,094 = **2,188** | Combined **1,370** | **−818 mm²** (−37%) |
| **G2** drive | inverter **926** | e-axle **926** | **zero** |
| **G3** cockpit | head unit 1,028 + cluster 287 = **1,315** | Combined SoC **1,028** | −287 mm² (−22%) |

**For G2 the integration split does nothing to PCB area**, and that is physically
right: integrating motor, inverter and gearbox saves *housing, cooling and
cabling*, not circuit board — the inverter electronics are the same either way.
**G2 therefore needs an AWD trend, not an integration trend.**

**What each curve is worth**, full 0→100% swing against EF's 22,365 mm²:

| | lever | max swing |
|---|---|---|
| **G2** | AWD share | 926 mm² (**4.1%**) |
| **G1** | integration share | 818 mm² (3.5%) |
| **G3** | integration share | 287 mm² (1.3%) |

**Under 9% combined**, and that is the full range, not the realistic 2025→2070
movement. Meanwhile ~~**G4 reaches 55.5% of PCB area**~~ **G4's split
probability is already in `18_`.**

> **CORRECTION 2026-08-11 — see §2.2f.** The "55.5%" in the struck sentence was
> the *pool* of controller-like components (§1, 64 of 101), not G4's reach.
> Measured, **G4+G5 as specified reach 8.2% of EF area** — the same size as
> G1+G2+G3's ~8.9%, not six times larger. The comparison above was pool against
> swing. Option B still stands, but on the "G4 is free, G1–G3 need new data"
> argument alone.

**DECISION (user, 2026-08-10): option B.** Skip the G1–G3 curves for now. Go
straight to P-c/P-d/P-e with **G4 and G5 only**, since neither needs new data,
measure what architecture consolidation actually does, and only then decide
whether curves worth a few percent are worth specifying.

Rationale: P-b as originally written would front-load the least valuable data
work while the largest and best-grounded driver waited on code.

### 2.2d UNCERTAINTY — carried, not collapsed

**User's standing requirement, restated 2026-08-10: this is a Monte Carlo model
and the uncertainties are large. Point estimates are not the deliverable.**

Three independent sources of spread must survive into the PCB result, and all
three already exist — none has to be invented:

| Source | Where it lives | Spread |
|---|---|---|
| Architecture share | `18_` `Penetration`, `Share_Min`/`Mode`/`Max` | **±0.12** on the share |
| Boards per component | `01_` `PCB_total_min` / `_max` and the size split | typically 1–3 boards |
| Board size per class | `03_` min / mode / max | small 9–80 mm², large 300–1,125 mm² |

Read against `ADAS_Sensor_Adoption_Report_2025_2070.md` §1.2: the project's
**self-consistency floor is ~3%**, cross-house forecast spread **~1.6×**, and
structural disagreement **3–4×**. **The whole G1+G2+G3 block, at under 9%, sits
close to that floor** — which is a second, independent reason to measure G4
before spending effort on them.

**Implication for P-e:** the architecture driver must be drawn as a *discrete
state per vehicle, comonotonic across years*, exactly like the wiring model —
not applied as a share-weighted average. Share-weighting would collapse a
bimodal mixture into its mean and destroy precisely the band the user is asking
to see.

---

### 2.2e P-c DONE 2026-08-10 — the shared driver module

Commit `36b21a4`. `tools/drivers.py`, 180 lines, six readers:

| | |
|---|---|
| `monotone_curve` | the PCHIP anchor reader that was duplicated |
| `load_800v_share` | voltage driver |
| `load_architecture_shares` | **new** — what P-e needs for G4 |
| `load_tier_shares`, `load_lidar_share` | ADAS drivers A and B |
| `load_presence_per_tier` | the tier composition |

Pure readers: open a workbook, interpolate anchors, return arrays. No sampling,
no state. **The models draw; this module only says what they draw from.**

**Scope widened beyond what §6 specified.** The note asked only for
`SensorNumbersMC`, but `_monotone_curve` existed in `BevWiring.py` too —
logically identical, separately maintained. Repointing one and not the other
would have left V12 comparing two implementations that happen to agree, which
is the condition V12 exists to detect, not a pass. Both were repointed.

**Verified before and after, not assumed:**

| model | evidence |
|---|---|
| `SensorNumbersMC` | 2641 lines of stdout **byte-identical** to the pre-change HEAD version. The model is seeded (`np.random.seed(42)`), so this is exact, not "within tolerance". −65 lines |
| `BevWiring` | 18 comparisons (3 segments × 3 years × Length/Cu) agree to **4.98e-07**, under the 5e-07 half-ulp of the 6-decimal stored baseline. `validate()` **9/9** |
| V12 | shared-curve agreement `0.000e+00` — now one implementation used twice |

**One subtlety, recorded because it nearly looked like a bug.** The shared
architecture curves are renormalised at *load* time; `BevWiring` renormalised at
*draw* time instead (`arch_sh /= arch_sh.sum(...)`). The raw PCHIP columns are
up to **2.3e-02** off unity, and `comonotonic_state` computes
`(u > cum).sum()` while documenting its input as "columns summing to 1" — so a
column summing to 0.9798 appears to yield state index 3, out of range for three
states. It cannot: the draw-time renormalisation runs first. `inp.arch` has
exactly one consumer and that renormalisation is its very next statement, so
pre-normalising is a no-op. Confirmed by the reproduced baseline.

**Lesson for future baselines:** the wiring baseline was stored rounded to 6
decimals, so an exact-match test against `== 0.0` could never pass. Store
comparison baselines at full precision.

**Consequence for P-d/P-e:** `PCBAreaMC` imports this module. It does not grow
a third copy.

---

### 2.2f MEASURED 2026-08-11 — what G4 and G5 actually reach

Checked before writing any P-e code, against `11_` with mode board areas from
`03_` (small 35, medium 168, large 550 mm²), EF segment:

| | components | EF area |
|---|---|---|
| "controller-like" pool (§1) | 56 of 101 | **50.7%** |
| **G4 as specified** — BCM, ABS/ESC, 4 domain controllers, zone controller, central computer | 7 | **8.1%** |
| **G5 as specified** — ADAS camera ECU (basic) | 1 | **0.1%** |
| **G4 + G5** | 8 | **8.2%** |
| G1 + G2 + G3 full swing (§2.2c) | | ~8.9% |

(The pool figure corroborates §1's 55.5% to within a regex definition — 56 vs 64
components, 50.7% vs 55.5%. The pool claim is sound; only its *reuse* as G4's
reach was wrong.)

**The G4 mapping is real and the data is there.** All seven components exist in
`11_` and their presence factors already encode the architecture gradient
without anything being invented:

| | AB | CD | EF |
|---|---|---|---|
| Body Control Module, ABS/ESC | 1.00 | 1.00 | 1.00 |
| Powertrain / Body-comfort domain controller | 0.25 | 0.50 | 1.00 |
| Chassis / ADAS domain controller | 0.00 | 0.50 | 1.00 |
| Zone controller | 0.00 | 0.25 | 1.00 |
| Automated driving central computer | 0.00 | 0.00 | 0.50 |

Conventional flat at 1.0, domain controllers rising with segment, zonal premium
first — the same premium-first gradient as every other transition here.

**Why 8.2% and not 51%.** The seven named components are the visible tip. §1's
own anchor — 80–150 discrete ECUs collapsing to under 20, VW SSP targeting ECUs
down >50% — implies the other ~49 controller-like components also collapse.
Modelling that means stating *which* ones and *how far*, which is precisely §7
open question 3: **the PCB equivalent of zonal consolidation is not recorded
anywhere.** It needs sourcing, not assertion.

**DECISION (user, 2026-08-11):** build P-e narrow — year axis, the 7 named
components, and the ADAS tier. Free, no new data. The broad question becomes
its own step **P-g**, with proper evidence behind it.

**Honest expectation for P-e:** PCB area moves by order 8%, not half. The
deliverable of P-e is the *year axis itself* — the thing that makes the PCB
chain stop being a 2025 snapshot — not the size of the architecture effect.

---

### 2.2g P-e SPECIFICATION — presence per architecture state

The mapping in §2.2a is prose. The model needs cells. Proposed
`presence(component | state)`, to be drawn discretely per vehicle and held
across years:

| `11_` component | Conventional | Transitional | SDV_Zonal | confidence |
|---|---|---|---|---|
| Body Control Module (BCM) | **1** | **1** | **0** | high — this is the textbook casualty of zonal |
| Powertrain domain controller | **0** | **1** | **0** | high |
| Chassis domain controller | **0** | **1** | **0** | high |
| Body/comfort domain controller | **0** | **1** | **0** | high |
| Zone controller (front/rear/etc.) | **0** | **0** | **1** | high |
| Automated driving central computer | **0** | **0** | **1** | high |
| ABS/ESC control module (EBCM) | **1** | **1** | **1** | **JUDGEMENT** — see below |
| ADAS domain controller / fusion ECU | **0** | **1** | **1** | **JUDGEMENT** — see below |

**The two judgement cells, stated rather than buried:**

1. **ABS/ESC survives all three states.** Braking is safety-critical with its own
   ASIL rating and hydraulic hardware; it is not usually collapsed into a zone
   controller even in fully zonal designs. If this is wrong, EF loses another
   ~1.3% of area at high zonal share.
2. **ADAS domain controller persists into SDV_Zonal.** It could instead be
   absorbed by the central computer, making it `0`. Kept at `1` because `19_`
   already governs ADAS compute through the tier axis (G5), and zeroing it here
   would double-count a consolidation the tier driver is already applying.

**Renormalisation at `BASE_YEAR = 2025` is mandatory.** The static `11_` factors
are the *observed* 2025 blend, so composing presence from state shares and
applying it from zero would double-count. Same treatment as `BevWiring`'s
`exp_base`: divide by the expected presence at 2025 given that year's shares, so
the ensemble mean is anchored while the spread is untouched. **This is the #1
documented silent breaker in this project.**

**Draw discipline:** one architecture state per iteration, comonotonic across
years (§2.2d). A vehicle is one design, never a blend.

---

## 5. Validation targets

| # | Target | Tolerance | Catches |
|---|---|---|---|
| **P1** | 2025 PCB area reproduces today's static result | ±3% | the rewrite changing the answer |
| **P2** | PCB and sensor models compose the same ADAS presence for the same year | exact | the two models describing different vehicles |
| **P3** | PCB and wiring models draw the same architecture and voltage state | exact | the same, for the two big drivers |
| **P4** | ADAS share of PCB area at 2025 | 3.9% ± 1 pp | the tier driver being mis-scaled |
| **P5** | accumulator vs full draw at 2025 | ±3% | the port itself |

P3 is the important one and it is new: the PCB model would be the **first**
consumer of the architecture and voltage drivers outside `BevWiring.py`.

---

## 6. Proposed order

| Step | Work | Verified by |
|---|---|---|
| ~~**P-a**~~ | ~~Research the 800V PCB effect~~ | **DONE 2026-08-10, §2.1a.** Absolute area roughly flat (−33% to +10%); the real effect is **consolidation**, expressible through the existing presence mechanism |
| ~~**P-b**~~ | **DEFERRED 2026-08-10, §2.2c — option B.** The G1–G3 curves are worth under 9% combined, close to the project's ~3% noise floor. G2's split is worth *nothing* to PCB area (e-axle and discrete inverter carry identical boards). **G4 needs no new data and reaches 55.5% of area** — measure it first, then decide whether G1–G3 are worth specifying | deferred |
| ~~**P-b′**~~ | ~~Fix the present-day overcount~~ | **DONE 2026-08-10, §2.2b.** G1, G2 and G3 all fixed. PCB area fell **14.9 / 19.2 / 17.6%** (AB/CD/EF); EF large boards **−44.3%**. All validation green |
| ~~**P-c**~~ | ~~Extract the shared presence module; repoint `SensorNumbersMC` at it~~ | **DONE 2026-08-10, §2.2e — commit `36b21a4`.** Scope widened to `BevWiring` as well. `SensorNumbersMC` stdout **byte-identical** (2641 lines); `BevWiring` reproduces its baseline to 4.98e-07. V11–V15 pass, `validate()` 9/9 |
| ~~**P-d**~~ | ~~Port the accumulator into `PCBAreaMC`, no drivers~~ | **DONE 2026-08-10, commit `d02f266`.** Memory 235 MB → 1.2 MB (12 GB → 1.2 MB at 51 years). P1/P5 **125 of 126** statistics inside ±3%; `total_area` mean ≤0.012%. The one exception is `AB total_large_area` **mode** (+3.21%), whose definition changed deliberately to the exported 50 bins. Raw draws CSV → float32 `.npy`; 522 MB of superseded CSV deleted |
| **P-e** | Add the year axis and the drivers — **G4 and G5 only, NARROW** per §2.2f: the 7 named components + ADAS tier, reach **8.2%**. Architecture must be a **discrete per-vehicle state, comonotonic across years**, not a share-weighted average (§2.2d) | **P2**, **P3**, **P4** |
| **P-g** | **NEW 2026-08-11, §2.2f.** How far zonal consolidation collapses the *other* ~49 controller-like components (the pool is 50.7% of EF area). Needs a sourced specification — §7 open question 3. Anchors: 80–150 ECUs → under 20; VW SSP ECUs down >50% | not yet specified |
| **P-f** | Flow the year axis into `PCBElementMC` | element mass at 2025 unchanged |

~~**P-a comes first and produces no code.**~~ **Done.** It was worth doing first:
the answer was neither of the two things assumed. The largest block does not
scale much in either direction — it *consolidates* — which means P-b is a
presence table rather than a scaling table, and no new area factor has to be
invented for it.

~~**P-b is now the first step with work in it**~~ — superseded. P-b is deferred
(§2.2c) and P-b′ and P-c are done. **`P-d` is the next step**, and it is
deliberately the boring one: port the accumulator, change no numbers. The year
axis and the drivers arrive at P-e, after the plumbing is proven not to have
moved anything.

---

## 6a. Sources for §2.1a

- ST — SiC traction inverter, die area and efficiency: <https://www.st.com/content/dam/AME/2020/apec-2020/presentations/APEC2020_Traction-Inverter-virtual-FINAL2.pdf>
- IEEE — comparison of IGBT and SiC inverter loss for 400V and 800V DC bus EV drivetrains: <https://ieeexplore.ieee.org/document/9236202/>
- Renesas — OBC and DC/DC topologies, power density 1.5–2 → >5 kW/L, 6.6 kW at 400V → 11–22 kW at 800V: <https://www.renesas.com/en/blogs/how-board-charger-obc-and-dcdc-converter-topologies-shape-next-gen-ev-power-electronics>
- Nexperia — OBC + DC/DC techbook: <https://www.nexperia.com/dam/jcr:445b12dc-e4a4-4bf2-a397-ccb9347039d1/OBC+DCDC_Techbook_final.pdf>
- Vicor — 400V/800V fast-charging compatibility, 37.5 kW in 92 × 80 mm: <https://www.vicorpower.com/industries-and-innovations/automotive/dc-fast-charging>
- Infineon — insulation coordination in automotive power modules, IEC 60664-1:2020: <https://community.infineon.com/t5/Knowledge-Base-Articles/Insulation-Coordination-in-Automotive-Power-Module-IEC60664-1-2020/ta-p/865520>
- TI — demystifying clearance and creepage for high-voltage equipment: <https://www.ti.com/lit/pdf/slup419>
- Sierra Circuits — PCB line spacing, creepage and clearance; relaxed PCB rules and CTI material groups: <https://www.protoexpress.com/blog/importance-pcb-line-spacing-creepage-clearance/>

**Sources for §2.2a**

- Promwad — zonal architecture in production, 2026: 80–150 discrete ECUs in a 2020 premium car, fewer than 20 under full zonal: <https://promwad.com/news/zonal-architecture-automotive-2026-practical-implementation>
- Promwad — central compute vs zonal; VW SSP from 2026, ECUs down >50%, wiring down 40%: <https://promwad.com/news/future-of-ecus-central-compute-vs-zonal-automotive-architecture>
- Dataintelo — integrated inverter-OBC-DC/DC unit market, $2.82 bn (2024) → $12.08 bn (2033), 17.6% CAGR: <https://dataintelo.com/report/integrated-inverter-obc-dcdc-unit-market/amp>
- Data Insights — integrated OBC DC-DC converter market, $2.5 bn (2025), 20% CAGR: <https://www.datainsightsmarket.com/reports/integrated-obc-dc-dc-converter-803484>
- Ovar Tech — independent DC-DC vs integrated OBC+DC-DC; integrated described as the mainstream trend in 2026: <https://ovartech.com/independent-dc-dc-vs-integrated-obc-dc-dc/>
- Siemens Capital — E/E architecture evolution, trends to watch: <https://blogs.sw.siemens.com/ee-systems/2024/09/12/e-e-architecture-evolution-part-2-trends-to-watch/>

*Market-research houses in this list are the **modelled top-down** evidence
class — see `ADAS_Sensor_Adoption_Report_2025_2070.md` §1.2. Their growth ratios
are informative; their absolute values are weak. The ECU-count and VW SSP
figures are the stronger anchors.*

---

## 7. Open questions

1. **Is `SensorElementsMC` in scope?** It is static in the same way, but it is a
   *sensor* model reading `01_`/`06_`/`07_`, not a PCB one. It would inherit the
   year axis almost free once the shared presence module exists. Not assumed in.
2. ~~**Does 800V grow or shrink power-electronics board area?**~~ **ANSWERED
   2026-08-10, §2.1a.** Neither much: absolute area is roughly flat, bounded
   about −33% to +10%, because power density tripled while power ratings also
   roughly tripled. The material effect that *does* matter is **consolidation**
   into the combined OBC + DC/DC module, already a component in `01_`.
   Remaining sub-question: the residual per-component area term. Its band should
   span zero, and it is now a second-order input rather than the largest unknown.
3. **How far does zonal consolidation actually go?** `17_` says CAN drops to
   0.45 and fuses to 0.65 by length. The PCB equivalent is not recorded
   anywhere.
4. **`04_` has no year or technology dimension.** If PCB *composition* changes
   with SiC, higher layer counts or substrate changes, `PCBElementMC` needs more
   than a year axis. Out of scope here; worth flagging.
5. **`12_Motor_Distribution.csv` is generated and read by nothing** — noted in
   the diagnostic, relevant when the auxiliary-motor work starts.

---

## 8. Note on the motor work that follows

Recorded because an earlier assumption was wrong. `ElectricMotorMC` covers
**auxiliary motors, not the traction powertrain** — window lifts, seats, pumps,
wipers, tailgate. So the drivers proposed for it earlier (magnet chemistry, AWD
share) were traction-motor concerns and do **not** apply.

Auxiliary motor counts already sit in `01_` as the `StepperMotor_*` and
`DCMotor_*` columns, feeding the currently-unused `12_`. That means the motor
work would share the **same presence mechanism** as PCB, and is likely cheaper
than first estimated — architecture (zonal moves motor drivers into zone
controllers) and feature content, not materials science.

---

### 2.2h P-e BLOCKED 2026-08-11 — the state mapping contradicts `11_`

Found by checking the §2.2g table against the observed 2025 factors *before*
writing code. **P-e cannot be implemented as specified.**

Composed presence (from `18_` architecture shares) vs observed (`11_`), 2025:

| component | seg | observed | composed | renorm |
|---|---|---|---|---|
| Zone controller | EF | 1.00 | 0.137 | **7.30×** |
| Zone controller | AB | 0.00 | 0.090 | **0** |
| Automated driving central computer | CD | 0.00 | 0.113 | **0** |
| ADAS domain controller | AB | 0.00 | 0.773 | **0** |
| Powertrain domain controller | EF | 1.00 | 0.797 | 1.25× |

2025 architecture shares, EF: **6.6% Conventional / 79.7% Transitional /
13.7% SDV_Zonal**.

**The contradiction.** `18_` says 13.7% of EF cars are zonal; `11_` marks the
zone controller `Std`, i.e. every EF car has one. Both cannot hold under a
binary state→component mapping.

**Why they disagree — they answer different questions.** `11_`'s ordinal label
means *"is this component typical in this segment?"*. A transitional 2025
premium car can carry one or two zone controllers without being a zonal
architecture. Component presence is **not** conditional on the architecture
state in the way §2.2a's prose mapping assumes.

**Why renormalisation would have hidden it, in two different bad ways:**

1. **A 7.3× multiplier** on the EF zone controller to force 2025 agreement —
   distortion presented as calibration.
2. **Where observed is 0.00** (AB zone controller, CD central computer, AB ADAS
   domain controller) the multiplicative renormaliser gives **zero**, and the
   component is dead in *every* year to 2070 even at 90% zonal share. This is
   exactly the lidar-dead-forever failure in `STATIC_MODELS_DIAGNOSTIC.md`,
   rebuilt in a new place.

**Also found: non-breaking spaces in `11_` component names.** The BCM is stored
as `'Body\xa0Control\xa0Module\xa0(BCM)'` (U+00A0). Exact-match lookup returns
nothing and **fails silently** — it skipped the component without error. Any
name-keyed code must normalise whitespace first.

**Options for resolving, none yet chosen:**

- **(a) Presence multiplier, not presence replacement.** Keep `11_`'s observed
  factor as the 2025 anchor and let the architecture state apply a *relative*
  multiplier that starts at 1.0 in 2025 — additive-in-log rather than
  multiplicative-from-zero. Survives the observed-zero case.
- **(b) Fix the disagreement at source.** Decide whether `11_`'s zonal labels or
  `18_`'s zonal share is the one that is wrong, and correct that file. Cleanest
  conceptually; touches a validated input.
- **(c) Split the concept.** "Has a zone controller" and "is a zonal
  architecture" become two different variables, the first driven by the second
  but not equal to it.

Option (a) is the smallest change and the only one that cannot resurrect the
dead-component bug. **Not decided — needs the user.**

### 2.2i OPTION (a) TESTED 2026-08-11 — it does not work, in either form

User chose option (a) on 2026-08-11. Implemented numerically before coding.
**It fails, and §2.2h's claim that it "survives the observed-zero case" was
wrong.** Recorded because the failure is informative.

**(a) multiplicative** — `presence = observed x m(state)`. Fails immediately:
`0 x anything = 0`, so every component whose 2025 factor is 0.00 stays dead
through 2070. The bug it was chosen to avoid.

**(a) additive, delta solved after clipping to [0,1]** — anchor becomes exact
(2.2e-16), and the trajectories collapse:

| | delta | 2025 | 2040 | 2070 |
|---|---|---|---|---|
| BCM, all segments | +1.00 | 1.000 | 1.000 | **1.000** — never declines |
| AB zone controller | −2.00 | 0.000 | 0.000 | **0.000** — dead |
| AB/CD central computer | −2.00 | 0.000 | 0.000 | **0.000** — dead |

When the observed value is 0 and every state target is >= 0, the only offset
that hits the anchor drives all three states to 0 permanently. Symmetrically,
observed 1.0 pins everything at 1.0 and the BCM never consolidates away.

**Why no offset scheme can work.** A single scalar per (component, segment)
cannot both hit a 2025 anchor and permit growth from zero against binary
targets. This is not a tuning problem: `11_` saying *AB has no zone controllers*
and `18_` saying *9% of AB is zonal* are inconsistent statements. An anchoring
scheme cannot reconcile inconsistent inputs, only choose which to honour.

**What does work — convex blend (call it option (d)):**

    presence(comp, seg, y | state k) = (1 - w(y)) * observed(comp,seg) + w(y) * t(comp,k)
    w(BASE_YEAR) = 0,  rising to 1 by T_FULL

Verified: 2025 anchor **exact to 0.0**, all values in [0,1] by construction (a
convex combination cannot leave the range, so no clipping and no anchor
damage), AB zone controller 0.000 -> 0.699 (2040) -> 0.999 (2070), BCM
1.000 -> 0.001.

**But it has two honest defects:**

1. **`T_FULL` is invented.** Nothing sources it. The project's standing rule is
   no unsourced parameters, and this would be one.
2. **It double-counts the timing.** The architecture state shares in `18_`
   already carry *when* the transition happens; `w(y)` applies a second timing
   on top. At `T_FULL = 2040` the EF BCM reaches 0.025 by 2040 — too fast to
   defend.

**Recommendation: option (b), fix the disagreement at source.** Now that the
inconsistency is measured rather than suspected, patching around it in the model
is the worse move. Either `11_`'s zonal labels are optimistic (a `Std` zone
controller in 2025 EF is hard to defend against a 13.7% zonal share) or `18_`'s
zonal share is too conservative. **One of the two files is wrong and should be
corrected.** That is a data question with evidence behind it, not a modelling
trick.

### 2.2j P-e IMPLEMENTED 2026-08-11 — first attempt, mapping wrong (FIXED in §2.2k)

**Committed deliberately with a failing validation.** The code is sound and the
failure is a modelling error in the presence table, recorded here so it is not
mistaken for a plumbing bug.

**What works:**

| | |
|---|---|
| year axis | 2020–2070 in `PCBAreaMC`, via the P-d accumulator's series axis — the class did not change |
| architecture states | discrete, **one uniform per vehicle held across all 51 years** (§2.2d) |
| presence rule | V13 composed-authoritative, as `SensorNumbersMC` has done since 2026-08-07 |
| **P3** — same architecture shares as `BevWiring` | **PASS, `0.000e+00`** |
| component lookup | 9 of 9 dynamic components found through non-breaking-space normalisation |

**What fails — P1, AB only:**

| | static 2025 | year-axis 2025 | |
|---|---|---|---|
| AB | 14,383.4 | 15,045.3 | **+4.60%** — outside ±3% |
| CD | 18,822.5 | 19,081.6 | +1.38% |
| EF | 22,096.1 | 21,821.1 | −1.24% |

**Cause: the `G4_PRESENCE` table is wrong.** Each of the four domain
controllers carries `t = (0, 1, 0)`, which asserts that **every** transitional
vehicle has a Powertrain **and** a Chassis **and** a Body/comfort domain
controller — all three at AB's 68.3% transitional share:

| AB 2025 | `01_` | composed |
|---|---|---|
| Chassis domain controller | **0.00** | 0.683 |
| ADAS domain controller | **0.00** | 0.773 |
| Powertrain domain controller | 0.25 | 0.683 |
| Body/comfort domain controller | 0.25 | 0.683 |

A real transitional car has one or two domain controllers, not the full set.
`01_` saying AB has no chassis or ADAS domain controller is **correct**, and the
mapping overrode it. The error scales with how many domain controllers a segment
does *not* have, which is why AB fails while CD and EF pass.

**Fix required:** presence-within-state must vary by segment —
`t(component, state, segment)` rather than `t(component, state)`, expressing how
many domain controllers a transitional car *in that segment* actually carries.
**A modelling judgement; not yet made.**

**Do not read the trend yet.** All three segments currently move **−2.0%**
from 2025 to 2070. That is consistent with G4+G5 reaching only 8.2% (four
components decline, two rise), but three different base areas landing on the
same figure deserves confirmation once the mapping is corrected.


### 2.2k P-e FIXED 2026-08-11 — conditional presence q, P1 passes

The §2.2j failure was the mapping asserting that **every** transitional vehicle
carries all three domain controllers. Replaced by a per-segment **conditional
probability**: *given* a vehicle is in a state that can carry this component,
does it actually have one?

    composed_2025 = q * SUM_k t_k * share_k(2025)  ==  observed
    q = observed / c25,  clipped to [0, 1]

**q is derived from `01_`, not invented.** It is what makes the segments differ.

**The trap, and the guard.** Where the carrying state's own 2025 share is below
what the 4-level scale can resolve (0.15), an observed `0.00` means *not yet*,
not *never*. Taking q = 0 there kills the component through 2070 — the
lidar-dead-forever bug, and the same trap that sank both schemes in §2.2i. AB's
zone controller is exactly this case (c25 = 0.090, label reads 0.00), so q stays
1 and it grows.

**Result — P1 passes, and the segments now separate:**

| | 2025 vs static | 2025 → 2070 |
|---|---|---|
| AB | **+0.17%** | **+0.4%** |
| CD | **−0.27%** | −1.1% |
| EF | **−1.24%** | −2.0% |

P3 still `0.000e+00`. The identical −2.0% across all three segments in §2.2j is
gone. EF consolidates most because it *has* domain controllers to lose; AB
barely moves because it never adopted them and goes conventional → zonal
directly. **Leapfrogging is an output here, not an input.**

### 2.2l UNCERTAINTY STILL COLLAPSED — the next step, and the honest caveat

**User, 2026-08-11: *"predictions are not science, but different types of
scenarios, which have an uncertainty."*** Two collapses are live in P-e today:

1. **The architecture share band is discarded.** `18_` carries
   `Share_Min`/`Mode`/`Max`, a documented **±0.12** on the share (§2.2d), and
   `PCBAreaMC` reads `Share_Mode` only. `drivers.load_architecture_shares`
   already takes a `band` argument, so nothing new is needed to fix this.
2. **`q` is a point estimate** derived from a label quantised to four levels.
   An observed 0.25 could defensibly be 0.20 or 0.30, and that spread is not
   represented.

**Neither needs new research.** Until both are carried, the year-resolved output
is a single line presented where a band belongs.

**How to read the current numbers.** AB +0.4% / CD −1.1% / EF −2.0% to 2070 is
**not** a forecast that PCB area barely changes. It says the architecture
driver *as scoped* touches 8.2% of board area (§2.2f) and therefore cannot move
the total much. The 50.7% controller pool in **P-g** is where a real trend would
come from, and it is unsourced. Quoting these figures without that framing would
misrepresent them.

### 2.2m UNCERTAINTY — the wrong way, then the right way (2026-08-11)

User: *"add the uncertainty band."* The first attempt was **written and
reverted**; recorded because the failure is the informative part.

**WRONG — perturb each share independently.** Read `18_`'s
`Share_Min`/`Mode`/`Max` per architecture state, sample inside the band, then
renormalise so the states sum to 1. It looks right and it is not. Measured, EF
`SDV_Zonal`:

| year | Share_Min | Share_Mode | Share_Max |
|---|---|---|---|
| 2025 | 0.025 | 0.137 | 0.189 |
| **2040** | **1.000** | 0.975 | **0.791** |

**The "minimum" scenario has MORE zonal adoption than the "maximum" one.** After
renormalising three independently perturbed shares, whichever state was
perturbed least dominates, and the scenario labels stop meaning anything. The
band in `18_` is real (max |Max−Min| up to 0.337), so this was not a harmless
no-op — it was actively wrong. Reverted before commit.

**RIGHT — shift the whole curve in time.** `BevWiring` has done this since it
was written, and it should have been the first place to look:

    d ~ Normal(0, TRANSITION_TIMING_SPREAD_Y = 5.0)     UNIT: years, per vehicle
    shares_i = shift_shares(shares, years, d)

One offset per vehicle, held across all years. All three states move together,
so the mixture stays coherent by construction, and *"this manufacturer is five
years behind"* is a scenario that means something physically.

Now in `tools/drivers.py` as `shift_shares` — vectorised, and verified against
`BevWiring._shift_shares` at **3.3e-16**, i.e. the same function. (`BevWiring`
still carries its own loop version; unifying it is a follow-up, and the numbers
are already proven identical.)

**Result: P1 and P3 still pass, and the total band does not visibly widen.**

| 90% band (P975−P025) | 2025 | 2070 |
|---|---|---|
| AB | 17.2% | 17.1% |
| CD | 15.3% | 14.2% |
| EF | 15.1% | 13.8% |

**This was predicted before implementing, and it is not a failure of the
mechanism.** The 9 dynamic components are **8.2%** of board area (§2.2f), while
the existing sampling band — triangular board dimensions and uniform counts
across 101 components — is already **15–17%** wide. A ±0.12 share acting on
8.2% of area contributes order 0.2–1%, which cannot show against that.

**What this buys and what it does not.** The scenario axis is now correct and
coherent, so the model *is* producing scenarios rather than a point prediction.
But the visible uncertainty in PCB area is still dominated by board-size and
count sampling, not by technology adoption. **Uncertainty large enough to see at
the total level would have to come from P-g's 50.7% controller pool** — which
remains unsourced. Quoting the current band as "the uncertainty in PCB area to
2070" would credit the architecture scenario with spread it did not produce.

**Still collapsed:** `q` remains a point estimate derived from a label quantised
to four levels (half-step 0.125). Cheap to add on the same per-vehicle pattern;
not done.

### 2.2n THE q BAND — 2026-08-11

The second collapse from §2.2l, now carried. `q` was a point estimate derived
from a label on a four-level scale; it is now drawn per vehicle.

**The bins are asymmetric, because the scale is.** `01_`'s levels are
1.00 / 0.50 / 0.25 / 0.00 — *not* evenly spaced — so each label stands for a
different width of truth, bounded by the midpoints to its neighbours:

| label | true value lies in |
|---|---|
| 1.00 `Std` | [0.750, 1.000] |
| 0.50 `Opt` | [0.375, 0.750] |
| 0.25 `Rare` | [0.125, 0.375] |
| 0.00 `–` | [0.000, 0.125] |

A flat ±0.125 would have been wrong for `Opt` and `Std`. Derived from the scale,
not invented.

**Uniform was tried first and was wrong.** Spreading a `Std` label evenly over
[0.75, 1.00] gives it an expected value of **0.875** — silently marking every
standard-fit component down 12.5%. EF moved −1.67% → −2.32% on that alone.
**Triangular peaked at the recorded label** is right: the curator's label is the
best estimate and must stay the mode; the bin only bounds how far truth can sit
from it.

A residual downward pull on `Std` remains by construction —
triangular(0.75, 1.00, 1.00) has mean 0.917 — and that is correct rather than a
defect: on a four-level scale `Std` genuinely cannot be distinguished from 90%
fitment.

**Three draws per vehicle now, every one held across all years:**

| | |
|---|---|
| `d` | when this manufacturer transitions (years, §2.2m) |
| `u` | which architecture state, given that timeline |
| `v` | where inside its quantisation bin each label actually sits |

`q` is calibrated against **that vehicle's own** shifted scenario, so every
vehicle reproduces its own 2025 observation rather than only the ensemble mean
reproducing the mode.

**Result — this one is visible, unlike the timing scenario:**

| 90% band | 2025 | 2070 |
|---|---|---|
| AB | 17.2% → **17.7%** | 17.1% → **18.0%** |
| CD | 15.3% → **16.3%** | 14.2% → **15.0%** |
| EF | 15.1% → **15.4%** | 13.8% → **13.7%** |

**AB now widens with time** (17.7% → 18.0%) instead of staying flat, which is
what carrying uncertainty forward is supposed to look like. The label
quantisation contributes more spread than the ±0.12 adoption band does —
unsurprising once §2.2f is taken seriously: presence uncertainty acts on the
whole of each dynamic component, while the adoption band only moves the mixture
between them.

**Both collapses from §2.2l are now closed.** What remains true is the framing:
the total band is still dominated by board-size and count sampling, and
technology adoption cannot dominate it while the driver reaches 8.2% of area.
