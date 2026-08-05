# Sensor model ↔ wiring model interface

**Purpose:** give `SensorNumbersMC.py` a time and hardware-tier dimension, so
that it and `Wiring/BevWiring.py` share one sensor-adoption basis instead of
diverging.

Written 2026-08-04. Revised 2026-08-05.

> **SUPERSEDED IN PART.** The concrete instruction set now lives in
> **`../Data/Sources/ADAS_Sensor_Adoption_Report_2025_2070.md` §6**, with the
> numbers in **`../Data/19_ADAS_sensor_adoption.xlsx`** sheet
> `Presence_per_Tier`. Two things changed since this document was written:
>
> 1. **The axis is no longer SAE level.** It is an installed-hardware tier
>    H0–H4. Wiring follows hardware, not the certificate — Volvo's EX90 carries
>    31 sensors at L2, BMW's i7 carried 25 at L3, and certified L3 is being
>    *withdrawn* in Europe while sensor content rises. Rationale:
>    `../Wiring/AUTONOMY_LEVELS_VS_HARDWARE.md`.
> 2. **`Wiring/BevWiring.py` has already been rewired** onto that axis
>    (`USE_TIER_AXIS = True`). `SensorNumbersMC.py` has **not**. Until it is,
>    the two models are on different axes — which is exactly the divergence
>    §3 below warns about.
>
> §3's central insight is unchanged and is why the fix stays small: the
> Std/Opt/Rare presence factor is already a penetration share. Read "level" as
> "tier" throughout what follows.

Companion to `Wiring/BevWiring_STATUS.md` and
`Wiring/IMPLEMENTATION_GUIDE.md`.

---

## 1. Why this matters

`BevWiring.py` computes ADAS and sensor wire length as

    ADAS length = sensor_count(autonomy_level) × metres_per_sensor

The counts currently come from sheet `Sensors_per_Level` in
`Data/18_BEV_technology_penetration.xlsx`, **every value of which is an
assumption with no source behind it.** That sheet now drives:

| Share of total wire length from the unsourced sheet | 2025 | 2040 | 2070 |
|---|---|---|---|
| AB | 6% | 15% | **22%** |
| CD | 9% | 19% | **24%** |
| EF | 11% | 19% | **21%** |

About a quarter of the 2070 answer. It is the single largest unsourced input in
the whole chain.

---

## 2. What `SensorNumbersMC.py` does today

| | |
|---|---|
| Inputs | `Data/01_VehicleElectronics.xlsx` (Domain/Component status per segment), `Data/06_VehicleSensorNumbers.xlsx` (min–max counts per Domain/Component/SensorType) |
| Mechanism | presence factor per component: **Std 1.00, Opt 0.50, Rare 0.25, "–" 0.00**; scales min and max, then a uniform draw between them |
| Aggregation | sums per SensorType within and across domains, per segment |
| Outputs | `csv_monte_carlo/sensor_monte_carlo_{SEG}_summary_stats.csv` and detailed results, per segment |
| **Missing** | **no year dimension, no autonomy-level dimension** |

---

## 3. The key observation

**The Std / Opt / Rare presence factor is already a penetration share in
disguise.** It says "what fraction of vehicles in this segment carry this
component". That is exactly the quantity that changes over time as autonomy
levels rise.

So the minimal change is not a rewrite. It is to make that one factor a
function of year and autonomy level rather than a constant:

    presence(component, segment)            # today
    presence(component, segment, year)      # needed

with the year dependence coming from the autonomy mix already in `18_`:

    presence(component, segment, year)
        = Σ_level  share(level, segment, year) × presence(component | level)

`share(level, segment, year)` already exists — sheet `Autonomy_Derived` in
`18_`, or recompute it as `BevWiring._derive_autonomy()` does. **Do not
duplicate that logic; read the same source.** If it is computed twice it will
diverge.

What has to be added is `presence(component | level)`: for each ADAS-relevant
component, at which autonomy level does it become Rare, Opt, then Std. That is a
much smaller and more answerable question than "how many cameras does an L4 car
have" — and it reuses the vocabulary the electronics file already speaks.

---

## 4. Contract: what the wiring model needs back

Either write these into `18_` sheet `Sensors_per_Level`, replacing the
assumptions, or emit a CSV in the same shape and repoint the model.

| Column | Meaning | Units |
|---|---|---|
| `Level` | `L0` … `L5` | — |
| `Sensor_Type` | see naming below | — |
| `Count_Min` / `Count_Mode` / `Count_Max` | sensors per vehicle at that level | count |

Optionally add a `Segment` column; the wiring model currently assumes counts per
level are segment-independent and applies segment differences through
`Metres_per_Sensor`. If sensor counts genuinely differ by segment at the same
autonomy level, say so and the wiring model must change to match.

**Sensor type naming.** `18_` uses `camera`, `radar`, `lidar`, `ultrasonic`.
`06_` uses `camera input`, `IR camera sensor`, `ultrasonic sensor`,
`ultrasonic transducer`. A mapping is required, and note that `06_` appears to
double-count ultrasonics as both "sensor" and "transducer" — check before
summing.

---

## 5. Gaps in `06_VehicleSensorNumbers.xlsx`

> **CORRECTED 2026-08-05.** This section previously claimed `06_` has *"no
> radar rows and no lidar rows at all."* **That was wrong** — the rows exist.
> They sit under components *Front long-range radar*, *Corner short/mid-range
> radars* and *LiDAR sensor*, but their `SensorType` values are the physical
> parts (`RF transceiver`, `laser diode array`, `photodetector array`, `IMU`),
> not the words "radar" and "lidar". It was a naming mismatch, not missing data.
> The same false claim was in `18_` sheet `Notes` and has been corrected there.

**And the file is more accurate than anyone credited.** Its EF maxima against
three independently measured 2025–26 flagships:

| Sensor | `06_` EF max | Mercedes EQS | BMW i7 | Volvo EX90 | verdict |
|---|---|---|---|---|---|
| Radar | 1 front + 4 corner = **5** | 5 | n/s | 5 | **exact** |
| Lidar | **0–1** | 1 | 1 | 0 | **exact** |
| Ultrasonic | 8–**12** | 13 | 12 | 16 | within 0–4 |
| Cameras (CMOS) | **5** | 6 | n/s | 10 | low by 1–5 |

Radar and lidar reproduce measured reality exactly. What actually needs doing:

1. **No time and no tier dimension.** The real gap, and the reason this document
   exists. See §3.
2. **Camera counts are low** — EF max 5 against 6–10 measured. Raise EF to 8–12,
   CD to 5–8, AB to 1–2 at the higher tiers. Note this is a 2× disagreement,
   which is *ordinary* by the standards recorded in
   `../Data/Sources/ADAS_Sensor_Adoption_Report_2025_2070.md` §1.2 — update the
   numbers, but the file is not broken.
3. **Possible ultrasonic double-count.** Ultrasonics appear under both
   *Ultrasonic sensors* (8–12) and *Parking assist ECU* (8–12), against 12–16
   measured on real cars. **Check before summing** — this may be a 2× error.

---

## 6. The cross-check that already works — preserve it

`17_` wiring length ÷ `06_` sensor counts gives a consistent metres-per-sensor
across three independently built datasets:

| | AB | CD | EF |
|---|---|---|---|
| metres per camera | 28 | 25 | 31 |
| metres per ultrasonic | 1.8 | 0.9 | 1.7 |

This is real corroboration, not a fit. **After changing the sensor model, re-run
this check at 2025.** If metres-per-camera moves far from ~28 m, something in
the new counts is wrong — the 2025 slice must still reproduce the observed
baseline.

Radar and lidar have no such anchor (see gap 1), so their metres-per-sensor in
`18_` sheet `Metres_per_Sensor` stay assumptions. Placement guidance from the
user, already recorded there: **radar is front and front-side; lidar is mostly
roof, some rear and side-viewing.**

---

## 7. Verification after the change

1. **2025 anchor holds.** `BevWiring.py` must still reproduce the report's
   2025 totals within ~1% on length (AB 1392, CD 2486, EF 3546).
2. **Metres-per-camera stays near 28 m** at 2025 (section 6).
3. **ADAS share stays plausible.** If it moves far from the table in section 1,
   understand why before accepting it.
4. **Shares still sum to 1.** `18_` sheet `Checks` verifies this for the
   penetration table; add the equivalent for any new table.
5. **No double-counting of the autonomy mix.** The sensor model applies the
   level mix to get counts; the wiring model then applies *metres per sensor*
   only. If the wiring model were also to apply the level mix, growth would be
   squared. Check `BevWiring.run_monte_carlo` if in doubt — it draws a
   discrete level per iteration and looks up counts for that level.

---

## 8. Watch out

- **Label collision.** `BEV_Automation_Adoption_Report_2020_2050.md` names its
  three *scenarios* AB / CD / EF (Conservative / Central / Accelerated). They
  are **not** the vehicle size segments. `18_` renames them for this reason.
- **`06_` counts are dated.** AB shows 0–2 cameras, but EU GSR-2 has mandated a
  front camera and radar on every new registration since July 2024. The file
  likely predates that.
- **Formula sheets are invisible to openpyxl.** `Autonomy_Derived` in `18_` is
  formulas; their results cannot be read until Excel has opened and saved the
  file. That is why `BevWiring.py` recomputes the conversion in Python from
  `Report_Scenarios` + `Conversion`. If you change one, change the other.
