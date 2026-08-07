# Implementation guide — the ADAS hardware-tier axis

Short guide to what changed in `BevWiring.py`, how to run it, and where every
number comes from. Written 2026-08-05.

Full reasoning: `../docs/ADAS_Sensor_Adoption_Report_2025_2070.md`.
Model handover: `BevWiring_STATUS.md`. Argument for the change:
`AUTONOMY_LEVELS_VS_HARDWARE.md`.

---

## 1. What changed, in one line

ADAS sensor content used to be keyed on **SAE certification level**. It is now
keyed on **installed hardware tier**, plus two further drivers.

**Why:** a car does not grow a wire when a regulator grants liability transfer.
Volvo's EX90 carries 31 sensors and is certified L2; BMW's i7 carried 25 and was
certified L3. Certified L3 is being *withdrawn* in Europe while sensor content
keeps rising, so the old key had the near-term trend backwards.

Nothing else changed. Architecture, voltage, gauges, copper, the accumulator,
the 50-bin convention and every output format are untouched.

---

## 2. Data flow

```
docs/ADAS_Sensor_Adoption_Report_2025_2070.md      the reasoning
        |                                                  (every number tagged
        |  make_19_adas_sensor_adoption.py                   FACT/DERIVED/ASSUMPTION)
        v
Data/19_ADAS_sensor_adoption.xlsx                          the machine-readable input
        |     Tier_Shares  Tiers  Lidar  Scenarios  Presence_per_Tier
        |     Parameters   Uncertainty   Validation
        v
Wiring/BevWiring.py  _load_tier_axis()  ->  _adas_metres_tier()
        v
outputs/data/bev_wiring_stats.csv, ..._histograms.csv, outputs/plots/
```

The workbook is **generated, not hand-maintained**. Edit the report, regenerate:

```bash
python3 tools/make_19_adas_sensor_adoption.py
```

Editing the workbook directly also works — the model reads whatever is there —
but the next regeneration overwrites it. For a permanent change, change the
report and the generator together.

---

## 3. Running it

```bash
python3 Wiring/BevWiring.py
```

Unchanged: ~4 min at 200,000 iterations, same output paths, same filenames.

---

## 4. Switching scenarios

**One cell: `20_` sheet `Control`, cell B4.**

| `Active_Scenario` | What happens |
|---|---|
| **`SAMPLE`** *(default)* | Each iteration draws a scenario by weight. One run; the band spans all three. **This is what to quote.** |
| `S1` / `S2` / `S3` | Every iteration pinned. Outputs go to `outputs/data_S2/`, `outputs/plots_S2/` with `_S2` in the filenames, so runs cannot overwrite each other |

For scripted sweeps, `SCENARIO_OVERRIDE` in section 0 beats the cell:

```python
SCENARIO_OVERRIDE = "S3"     # None = obey the sheet
```

Measured effect on EF total length (8,000 iterations, seed 11):

| | 2040 | 2050 | 2070 | band width / mean, 2070 |
|---|---|---|---|---|
| S1 | 2765.7 | 2698.3 | 2697.6 | 0.46 |
| S2 | 2765.7 | 2764.5 | 2875.4 | 0.46 |
| S3 | 2765.7 | 2852.7 | 3142.1 | 0.47 |
| **SAMPLE** | 2763.8 | 2772.4 | 2900.2 | **0.50** |

Two things to read here. **2040 is identical across all four** — Driver C is
inert at and before 2040 by construction, so it cannot disturb any year for
which sourced data exists. And **SAMPLE's band is wider than any pinned run**,
because it carries the scenario spread as well as the within-scenario spread.
That is exactly why pinned runs must not be quoted as the answer.

---

## 5. The three drivers

All in `_adas_metres_tier()`, sampled independently per iteration.

| | Driver | Sheet | Mechanism |
|---|---|---|---|
| **A** | hardware tier H0–H4 | `Tier_Shares`, `Tiers` | One uniform per iteration held across years plus its own timing offset — the same comonotonic scheme as the architecture driver, so a vehicle is one tier and not a blend |
| **B** | lidar penetration | `Lidar`, `Parameters` | Separate from tier, because lidar tracks cost and Chinese competitive pressure, not certification. Band membership drawn per iteration; **the China→Europe lag is sampled** (`Normal(7, 3)`), so "China leads, Europe follows" is testable rather than assumed |
| **C** | post-2040 scenario | `Scenarios` | Multiplier on every sensor count. Removes the need to forecast unknown sensor modalities — a wiring model needs *how many*, not *which* |

`Metres_per_Sensor` in `18_` is **reused unchanged**. The tier axis changes how
many sensors a car has, not how much wire each one needs.

---

## 6. Validation

`validate()` runs automatically at the end of a full run and prints a table.
Targets live in `19_` sheet `Validation`; tolerances come from sheet
`Uncertainty`.

```
[ok  ] V1   2025 length AB    got 1407.2602  want 1392.000  tol 0.03
[ok  ] V6   tier shares sum to 1                            tol 1e-09
[ok  ] V8   ADAS share EF %   got   10.9410  want   11.000  tol 3
[ok  ] V9   scenario multiplier at 2040                     tol 1e-09
[ok  ] V10  scenario weights sum                            tol 1e-09
9/9 passed
```

**On the tolerances.** V1 is ±3%, not ±1%. That is deliberate: the source report
disagrees *with itself* by 2.8% on EF length (its rows sum to 3,646 against a
stated 3,546). Demanding better than 3% would be demanding that the model
reproduce noise. See `19_` sheet `Uncertainty` — it records the observed spread
between credible sources and sets a **>10× threshold before calling any
mismatch an error**.

`validate()` returns its results and raises nothing; the caller decides what is
fatal. V1 and V8 wobble at low iteration counts.

---

## 7. Editing

| To change | Edit |
|---|---|
| Tier adoption by segment and year | `19_` sheet `Tier_Shares`, yellow cells. **EF near-term H4 corrected 2026-08-07**: 2025 0.15 -> 0.03, 2030 0.30 -> 0.20 (report S9.0 Yano check, 6x high at 2025; 2035+ agrees and is unchanged) |
| Sensor counts per tier **per segment** | `19_` sheet `Tiers` -- 15 rows since 2026-08-07 |
| Which chip equals one box | `19_` sheet `Modules_vs_Elements` |
| Lidar path or its band | `19_` sheet `Lidar` |
| China→Europe lidar lag | `19_` sheet `Parameters` |
| Scenario multipliers or weights | `20_` sheet `Scenarios` (project-wide) |
| Which scenario is active | `20_` sheet `Control` cell **B4** |
| Metres per sensor | `18_` sheet `Metres_per_Sensor` (unchanged) |

Anchor years are read through PCHIP, so **adding or deleting year columns and
rows needs no code change** — same behaviour as the existing share tables.

---

## 8. Rolling back

```python
USE_TIER_AXIS = False        # section 0
```

Restores the old SAE-level path reading `18_` sheet `Sensors_per_Level`, and
writes to `outputs/data_levelaxis/` so a comparison run cannot overwrite the
current output. Kept for diffing only — it is not maintained, and it encodes the
mechanism this change exists to replace.

---

## 9. Known limits

1. **Driver C multipliers (1.0 / 1.4 / 2.0) are the weakest input** and the
   largest single lever on 2070. The two mechanisms behind them — cost decline
   with volume, and safety redundancy — are observable; the specific values are
   not sourced.
2. **Measured scenario spread is slightly below the report's estimate**: S2 came
   out +6.6% on EF 2070 against a predicted +8%, S3 +16.5% against +21%. The
   ADAS block is a slightly smaller share of the total than §7.2 assumed. Not a
   defect, but the report's headline percentages are ~1 pp optimistic.
3. **Substitution is still not modelled.** `Presence_per_Tier` row 9
   (`ADAS camera ECU (basic)`) *declines* as rows 10 and 11 rise — the smart
   camera is absorbed into the domain controller. That is a real substitution,
   and like the CAN/Ethernet case in `BevWiring_STATUS.md` §10 it is currently
   drawn as independent. It affects category-level statements, not segment totals.
4. **CORRECTED 2026-08-07.** ~~`Presence_per_Tier` is not yet consumed by any
   code.~~ It **is** consumed -- `SensorNumbersMC.py` has read it since
   2026-08-06 (`load_presence_per_tier`, `apply_adas_tier_presence`). This
   paragraph predated that commit by six minutes and was never refreshed.

5. **`01_` EF lidar presence is wrong** — labelled `Opt` (0.50) against a real
   2025 value near 0.01. A 50× gap, far outside every spread in sheet
   `Uncertainty`. Not yet fixed, and it will matter as soon as
   `SensorNumbersMC.py` is rewired.
