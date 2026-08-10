# PCB models — design note (step 7)

**Purpose.** Give `PCBAreaMC` and `PCBElementMC` a time axis and couple them to
the drivers the wiring and sensor models already use.

Written 2026-08-10. **Nothing here is implemented.**

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
| **P-b** | **REDEFINED 2026-08-10 by §2.2a.** Not a scaling table — a **substitution-group table**: five groups (G1–G5), each with a group total and a split probability. **G4's split is already in `18_`** and G5 is already built. Only G1–G3 need new numbers | group totals sum to one car's worth; 2025 composition reproduces observed board counts |
| ~~**P-b′**~~ | ~~Fix the present-day overcount~~ | **DONE 2026-08-10, §2.2b.** G1, G2 and G3 all fixed. PCB area fell **14.9 / 19.2 / 17.6%** (AB/CD/EF); EF large boards **−44.3%**. All validation green |
| **P-c** | Extract the shared presence module; repoint `SensorNumbersMC` at it | sensor results unchanged, V11–V15 still pass |
| **P-d** | Port the accumulator into `PCBAreaMC`, no drivers | **P5**, **P1** |
| **P-e** | Add the year axis and all three drivers | **P2**, **P3**, **P4** |
| **P-f** | Flow the year axis into `PCBElementMC` | element mass at 2025 unchanged |

~~**P-a comes first and produces no code.**~~ **Done.** It was worth doing first:
the answer was neither of the two things assumed. The largest block does not
scale much in either direction — it *consolidates* — which means P-b is a
presence table rather than a scaling table, and no new area factor has to be
invented for it.

**P-b is now the first step with work in it**, and the architecture side of it
(§2.2) is the part with no data behind it at all.

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
