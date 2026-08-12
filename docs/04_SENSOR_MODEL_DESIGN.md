# Sensor model — design note

**Purpose.** Give `SensorNumbersMC.py` a time axis and couple it to the same
drivers the wiring model uses, so the two stop describing different vehicles.

Written 2026-08-05. **Nothing in here is implemented yet.** This is the
document that gets agreed before code, per the project's own sequencing rule.

Companions: `05_ADAS_SENSOR_ADOPTION_REPORT.md` (the sensor evidence
base), `../Wiring/IMPLEMENTATION_GUIDE.md` (how the same job was done for
wiring), `../Wiring/BevWiring_STATUS.md`.

---

## 1. Decisions taken

| # | Decision | Consequence |
|---|---|---|
| 1 | **Path B — full year axis** | Sensor counts become a function of year. Every output CSV and figure gains a `Year` dimension. Forces an architecture change, see §6 |
| 2 | **Central scenario config** in one Excel file | `Data/20_scenarios.xlsx`, read by every model. One selection drives wiring, sensors and PCB alike |
| 3 | **Temperature uplift is a sampled range**, not a point factor | Consistent with the rest of the project: a contested quantity belongs in the distribution |
| 4 | **Correct `06_`'s CD row** | No contradictions between files. §5 — the fix is subtler than changing two numbers |

---

## 2. What is wrong today

`SensorNumbersMC.py` scales min/max sensor counts by a **static** presence
factor read from `01_`:

    Std 1.00   Opt 0.50   Rare 0.25   "-" 0.00      presence(component, segment)

No year. No tier. No voltage. So the model describes a 2025 vehicle and nothing
else, while `BevWiring.py` runs to 2070 on three explicit drivers. The two
models cannot presently be talking about the same car.

Three real drivers are being lost:

| Driver | Effect on sensors | Currently |
|---|---|---|
| **ADAS hardware tier** (H0–H4) | camera, radar, lidar, ultrasonic counts | frozen at 2025 |
| **Voltage** (400V/800V) | cell voltage and battery temperature sensing | **absent entirely** |
| **Architecture** (zonal) | not sensor count — but see §4, it moves wiring per sensor | absent |

---

## 3. Driver — voltage to cell sensing

### 3.1 The physics

A BMS senses every **series element**. Cells in parallel share a node and are
sensed once. So:

    series elements = pack voltage / cell voltage

Series count is set by **voltage**, not by vehicle size. Capacity is set by
parallel count, which adds no sense lines. Going 400V → 800V roughly doubles
the sense lines; making the pack bigger does not.

### 3.2 The distributions — FACT (user-supplied ranges)

| State | pack voltage | series elements | draw |
|---|---|---|---|
| **400V** | 350 – 410 V | 80 – 96 – 105 | `triangular(80, 96, 105)` |
| **800V** | 650 – 800 V, EU mode ~750 | 176 – 203 – 216 | `triangular(176, 203, 216)` |

The 800V/400V ratio is therefore **not a fixed ×2**. Median ≈ 2.1, individual
draws span 176/105 = **1.68** to 216/80 = **2.70**. A point factor would have
discarded that spread.

**Segment note.** `06_` implies AB and CD sit at ~96 series elements at 400V and
EF at ~108 — a 12% spread, bigger packs sitting at the top of the voltage
window. Not segment-*independent*, but close enough that one distribution with
a segment offset covers it.

### 3.3 Sampling

1. The voltage state is **already drawn** per iteration in the wiring model
   (`u_volt`, discrete, comonotonic across years). The sensor model must draw it
   **the same way from the same shares** — never recompute it.
2. Given the state, draw series count from its triangular.
3. Hold **one cell-count percentile per iteration across all years**, as the
   architecture driver does. A manufacturer building a high-count 400V pack
   builds a high-count 800V pack; the vehicle stays one design through its
   transition.

### 3.4 Battery temperature — decision 3, sampled

Temperature sensors are **per module**, not per series element, so the uplift is
smaller than voltage's and genuinely uncertain. Two forces oppose:

- more series elements and higher isolation risk → more monitoring
- **cell-to-pack designs are removing modules entirely** → fewer sensors,
  independent of voltage

Proposed: `TEMP_UPLIFT_800V ~ triangular(1.0, 1.4, 1.9)` — ASSUMPTION.
The floor of 1.0 says "module count unchanged, just rearranged"; the ceiling
of 1.9 says "modules follow series count". **The width is the honest part.**

### 3.5 Where the uplift applies — row level, never the aggregate

`06_`'s `Sensor Type Summary` aggregates `temperature sensor` across every
domain — battery, thermal loop, inverter, HVAC. EF reaches 202 largely through
multi-zone climate, which has nothing to do with pack voltage.

So apply at `Sensor Counts Detail` granularity:

| Row | 800V uplift |
|---|---|
| `HV Powertrain / Traction battery pack / voltage sensor` | **full**, §3.2 |
| `HV Powertrain / Traction battery pack / temperature sensor` | **partial**, §3.4 |
| `HV Powertrain / BMS`, `HV junction box`, isolation monitoring | none — fixed count |
| `Thermal / *`, HVAC, cabin, inverter, everything else | **none** |

No blended judgment factor is needed; the aggregate takes care of itself.

---

## 4. Driver — architecture to wiring per sensor

Not a sensor-count effect, but it belongs in the same shared-driver design
because it is the other half of the same physical trade.

Zonal architecture connects a sensor to its **nearest zone controller** rather
than to a central ECU. Runs shorten; zone controller PCBs appear. But the
compressible part is **already counted elsewhere** in `17_`:

| Category | SDV factor | what it is |
|---|---|---|
| `LVDS_CAM` | 0.85 | camera data links |
| `COAX_RF` | 0.95 | RF/coax |
| `ETH_BUS` | **3.00** | the backbone that replaces them |

So `ADAS_CAM` is the dedicated and power wiring on top, running to body
extremities — the least compressible part of any harness, since routing follows
looms and high-speed links carry bend-radius and EMC constraints.

Proposed: `metres_per_sensor` gains an architecture factor of
**0.85–0.90 at full zonal** — ASSUMPTION, deliberately modest.

**This changes `BevWiring.py`, not the sensor model.** Listed here so the two
are designed together rather than retrofitted.

---

## 5. Correcting `06_` — decision 4, and why it is not just two numbers

The contradiction: `06_` says CD cell sensing is **96–108**, while the corrected
curve says 7% of CD is 800V in 2025. If 7% of CD vehicles carry ~192 series
elements, the range must reach ~192.

But **a min–max uniform range cannot represent a 7/93 bimodal mixture.**
Widening CD to 96–192 and drawing uniformly gives a mean of 144 against a
correct 103. Widening the range makes the file *more* wrong, not less.

### The fix: make `06_`'s battery rows the 400V basis

Let the sheet hold the **400V-basis count**, and let the voltage driver apply
the uplift. The sheet then means one thing consistently, and the mixture lives
where mixtures belong — in the sampler.

| Segment | current | **proposed (400V basis)** |
|---|---|---|
| AB | 96 – 96 | **80 – 105** |
| CD | 96 – 108 | **80 – 105** |
| EF | 108 – 198 | **96 – 120** |

**Check — does this reproduce what `06_` originally recorded for 2025?**
Applying `N = N₄₀₀ × (1 + s₂₀₂₅ × 1.1)`:

| | 400V mean | s(2025) | predicted 2025 | `06_` originally | gap |
|---|---|---|---|---|---|
| AB | 92.5 | 1.9% | 94.4 | 96 | **−1.7%** |
| CD | 92.5 | 7.0% | 99.6 | 102 | **−2.4%** |
| EF | 108.0 | 41.9% | 157.8 | 153 | **+3.1%** |

All three within ~3% — the project's noise floor. The correction removes the
contradiction **and** reproduces the original observations. EF's 108–198 stops
being an anomaly and becomes the corroboration it always was.

---

## 6. Path B — the architecture problem

Adding a year axis is not a loop. Measured:

| draws | years | memory, 3 segments |
|---|---|---|
| 200,000 | 1 | 0.92 GB |
| 200,000 | 7 | 6.45 GB |
| **200,000** | **51** | **47 GB** |

192 rows × 200,000 draws × 51 years × 8 bytes × 3 segments. Not possible on a
17 GB machine — the same wall `BevWiring.py` hit and solved.

**Proposal: port the chunked `Accumulator` from `BevWiring.py`.** It keeps
statistics only, its memory is independent of `ndraws`, and it already enforces
the 50-bin convention. Measured accuracy there: 0.089% on the mean, 0.44% on
P2.5/P97.5 — far below the sampling noise it removes.

Benefits beyond memory: both models then share one statistical engine, one
histogram convention and one accumulator, so their outputs are directly
comparable rather than merely similar.

**This is the largest single piece of work in the plan** and should be its own
step, verified against the existing static results before any driver is added.

---

## 7. Central scenario config — decision 2

`Data/20_scenarios.xlsx`, read by every model.

| Sheet | Holds |
|---|---|
| `Control` | `Active_Scenario` — `SAMPLE` (default) / `S1` / `S2` / `S3`. **The one cell anyone changes** |
| `Scenarios` | scenario names, weights, and the multiplier anchors currently in `19_` |
| `Notes` | what each scenario means, and the warning below |

Moving the scenario table out of `19_` — `19_` is ADAS-specific and is the wrong
home for a project-wide switch. `19_` keeps tiers, lidar and presence.

### The warning that must sit in that file

**Scenarios are not low / medium / high.** S1 says *sensors converge on a
minimal set; redundancy is achieved in compute, not hardware*. So:

| | S1 | S2 | S3 |
|---|---|---|---|
| Sensor count | **lowest** | mid | highest |
| Wiring length | **lowest** | mid | highest |
| **PCB / compute area** | **highest** | mid | highest |

S1 is **anti-correlated** between sensors and PCB. Wiring S1 to "low" everywhere
would delete that substitution and understate PCB uncertainty. This is the same
structural trap as CAN-vs-Ethernet and as `Presence_per_Tier` row 9, where
`ADAS camera ECU (basic)` falls 1.00 → 0.10 as the domain controller rises.

---

## 8. New validation targets

| # | Target | Tolerance | Catches |
|---|---|---|---|
| **V11** | predicted 2025 cell-sense count reproduces `06_` per segment | ±10% | **would have caught the CD 800V error automatically** |
| **V12** | sensor model and wiring model draw the same 800V share for the same year | exact | the two models describing different vehicles |
| **V13** | composed presence at 2025 reproduces `01_`'s static labels | ±0.15 | tier composition drifting from the source file |
| **V14** | year-resolved model at 2025 reproduces the current static results | ±3% | the path B rewrite changing the answer |

V14 is the safety net for §6: the rewrite must not move 2025.

---

## 9. Proposed implementation order

Each step is separately verifiable, and each stops for approval.

| Step | Work | Verified by | STATUS 2026-08-05 |
|---|---|---|---|
| **1** | Correct `06_` battery rows to the 400V basis (§5) | recomputes the original 2025 values within 3% | **DONE** — AB −1.6%, CD −2.3%, EF +3.1% |
| **2** | Create `Data/20_scenarios.xlsx`; repoint `BevWiring.py` at it | wiring results unchanged, 9/9 still passing | **DONE** — identical to 0.000% |
| **3** | **Port the accumulator into `SensorNumbersMC.py`**, no drivers yet | **V14** — 2025 output matches today's static result | **DONE** — 915/915, worst mean 0.841% |
| **4** | Add the year axis and the voltage driver (§3) | **V11**, **V12** | **DONE** — V11 passed, V12 = 0.000e+00 |
| **5** | Add the tier driver from `19_ Presence_per_Tier` | **V13** | **IMPLEMENTED, NOT SIGNED OFF** — V13 21/36, four decisions open, see `HANDOVER_2026-08-09.md` §11 |
| **6** | Add `metres_per_sensor` architecture factor to `BevWiring.py` (§4) | wiring re-run, V1–V10 | **DONE 2026-08-07** — 9/9; ADAS metres −5.3 to −7.4% by 2070, 2025 anchor unmoved |
| **7** | PCB models, reusing all of the above | later | not started — **this is now the next step** |

**Do not start step 6 or 7 until step 5 is signed off.** Decision 3 in
`HANDOVER_2026-08-09.md` §11 changes Driver A, which the wiring model also reads — so
resolving it after step 6 would mean redoing step 6.

Step 3 is the risky one and carries no behavioural change — deliberately, so
the rewrite can be verified before anything starts moving.

---

## 10. Still open

0. **Battery temperature maxima — RESOLVED 2026-08-05.** One row
   (`Traction battery pack / temperature sensor`) outweighed all 32 other
   temperature rows combined: 60% of AB's total, 51–54% of CD's. Per-module
   arithmetic (8–18 modules × 2–4 NTC + 3–8 pack level) supports AB 18–40,
   CD 24–55, EF 28–70 against the recorded maxima of 97 / 109 / 173 — about
   2.0–2.5× high. **Counter-argument (user):** thermistors are very cheap and
   thermally critical locations plausibly carry redundant sensors, so pure
   module arithmetic understates the ceiling. **Resolution:** maxima set to
   **70 / 85 / 120** — roughly 1.7× above module arithmetic, ~70% of the
   previous values. Minima left untouched. Battery share at max falls from
   61/54/62% to **53/48/53%**. Protocolled in `06_` sheet `Notes`.
   **Still open:** the *totals* look generous — AB at 57–133 temperature
   sensors for a small car against a realistic 30–60. The 32 non-battery rows
   have not been reviewed.
1. **The `06_` EF 400V basis of 96–120** is inferred from the implied 108, not
   sourced. If EF packs are known to differ, say so.
2. **Chemistry is a latent driver.** Series count = pack voltage ÷ *cell*
   voltage, and cell voltage is chemistry-dependent — NMC ~3.7 V, LFP ~3.2 V, so
   an LFP pack needs ~15% more cells for the same pack voltage. The triangulars
   in §3.2 absorb this as spread today. Worth its own driver later, not now.
5. **OPTION B -- two camera components that do not exist yet. NOT IMPLEMENTED,
   documented 2026-08-07 at the user's request as a possible scenario.**

   Option A (done) raised the counts on the four camera components already in
   `06_`. It closed the gap at H2-H4 for CD and EF. Option B instead adds the
   two components the project has never had. It is the more faithful structure
   and it is what the user actually described: *"cameras are essential for the
   safety, therefore certain redundancy in viewing areas, avoid dead spots.
   Furthermore also monitoring the driver?"*

   | New component | Why | Today |
   |---|---|---|
   | **Front-corner / A-pillar cameras** | Cross-traffic at junctions. The front camera cannot see across the junction mouth and the side cameras look rearward, so this is a genuine dead spot, not a redundancy nicety. | Folded into `Side / mirror cameras`, which distorts what that row means |
   | **Cabin / child-presence camera** | Occupant detection in `06_` is weight/pressure mats, capacitive sensors and belt buckles -- **not vision**. Euro NCAP and GSR-2 phase 2 push camera- or radar-based child presence detection. Driver monitoring exists; the rest of the cabin is unmonitored. | Absent from `01_`, `06_` and `19_` |

   **Cost of doing it.** A new ADAS component needs a row in three files, and
   they must be added together or the tier driver breaks:

   1. `Data/01_VehicleElectronics.xlsx` -- the component master
   2. `Data/06_VehicleSensorNumbers.xlsx` -- element counts per segment
   3. `Data/19_ADAS_sensor_adoption.xlsx` sheet `Presence_per_Tier` -- when it
      arrives, per tier. **Add it to `tools/make_19_adas_sensor_adoption.py`,
      not to the workbook**, or the next regeneration deletes it.
   4. `19_` sheet `Modules_vs_Elements` -- its PRIMARY element, so V15 keeps
      holding

   A component present in `06_` but missing from `Presence_per_Tier` is
   silently skipped by the tier composition -- it will not raise an error, it
   will simply never appear. That is the failure mode to watch for.

   **Suggested starting values** (front-corner 0-2 / 0-2 / 2-2 across AB/CD/EF,
   cabin camera 0-1 / 0-1 / 1-1) with presence rising H0 0.0 -> H4 1.0 for the
   corner cameras and H0 0.0 -> H4 0.8 for the cabin camera. Not sourced --
   they would need the same FACT / DERIVED / ASSUMPTION tagging as everything
   else in the adoption report.

3. **`SensorElementsMC.py` also reads `01_` and `06_`** and will inherit the
   year axis whether or not it is planned for. It is not in the order above.
4. **`Data/11_PCB_Distribution_Classified.csv` is 0 bytes**, so `PCBAreaMC` may
   not currently run. Needs checking before step 7.
