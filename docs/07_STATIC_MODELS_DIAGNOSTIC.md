# Diagnostic — the static models, before step 7

**Purpose.** Find out what the 2026-08-07 `01_` relabelling actually broke, and
what the PCB work is walking into. Run 2026-08-10.

**Nothing was fixed.** Two models were re-run and their outputs diffed against
the stored ones. That is all.

---

## 1. The headline

**Lidar is not dead. It is dead in HALF the model.**

| | 2025 | 2030 | 2040 | 2050 | 2070 |
|---|---|---|---|---|---|
| **Year-resolved** sensor model, EF lidar units/vehicle | 0.030 | 0.232 | 0.620 | 0.730 | **0.765** |
| CD | 0.001 | 0.050 | 0.425 | 0.620 | 0.670 |
| AB | 0.000 | 0.006 | 0.142 | 0.390 | 0.435 |
| **Driver B**, equipped share of new sales (mode) | 1% | 12% | 45% | 60% | **70%** |
| **Static models** (`SensorElementsMC`, PCB chain) | **0** | **0** | **0** | **0** | **0** |

`01_` records lidar as `–` in all three segments. That is **correct for 2025** —
real European lidar penetration is ~1–3%, and on a four-level scale
(1.00 / 0.50 / 0.25 / 0.00) `–` is the closest available value.

But `01_` has **no year axis**, so every model reading it statically carries that
2025 value to 2070. In their world lidar never exists — no laser diode array, no
photodetector array, no IMU, no PCB, no material.

**This is an artefact of static models reading a snapshot label. It is not a
claim by the project that lidar dies.** The dynamic half says the opposite, and
says it strongly: EF goes from 0.03 to 0.765 units per vehicle, a 25× rise.

---

## 2. The dependency chain — narrower than previously documented

```
01_VehicleElectronics.xlsx
   ├─→ SensorElementsMC.py                       (direct)
   ├─→ SensorNumbersMC.py                        (non-ADAS rows only; ADAS uses the tier axis)
   └─→ BEVElectronicsClassification.py
          ├─→ Data/11_PCB_Distribution_Classified.csv → PCBAreaMC.py
          └─→ Data/12_Motor_Distribution.csv
```

Two corrections to what earlier documents said:

- **The PCB models do not read `01_`.** `PCBAreaMC` reads `11_`, which
  `BEVElectronicsClassification.py` generates from `01_`. `PCBElementMC` reads
  `04_` and is not in this chain at all. `HANDOVER_2026-08-09.md` §3's phrase "the PCB
  models also read `01_`" is true only indirectly.
- **`Data/11_` is not empty.** An earlier note recorded it as 0 bytes and the
  chain as broken. It is 22 KB. The zero-byte reading was an **un-downloaded
  iCloud placeholder**, not a missing file. Worth remembering: on this machine a
  file can appear empty simply because iCloud has evicted it.

---

## 3. What moved

### 3.1 `11_` — 40 cells, every one in the ADAS domain

| Component | Segment | presence factor |
|---|---|---|
| **LiDAR sensor** | CD | 0.25 → **0.00** |
| **LiDAR sensor** | EF | 0.50 → **0.00** |
| Automated driving central computer | CD | 0.25 → **0.00** |
| **ADAS camera ECU (basic)** | EF | 1.00 → **0.25** |
| Front ADAS camera | AB | 0.50 → **1.00** |
| Front long-range radar | AB | 0.50 → **1.00** |
| Driver monitoring camera | AB | 0.00 → **0.50** |
| Corner radars, side cameras | AB | 0.00 → **0.25** |
| ADAS camera ECU (basic) | AB | 0.50 → **1.00** |

`12_` (motors): **zero cells changed.**

**Incidental fix:** row count 102 → 101. The duplicate
`HV Powertrain / HV junction box / PDU` row — a defect flagged in
`SensorNumbersMC`'s own docstring — is gone from `01_` and no longer propagates.

### 3.2 PCB area — moved, and in opposite directions by segment

| | before | after | |
|---|---|---|---|
| AB mean total area | 16,961.6 | 16,906.5 | **−0.32%** |
| CD | 23,575.4 | 23,309.1 | **−1.13%** |
| EF | 27,413.0 | 27,159.1 | **−0.93%** |

Board counts show the mechanism better than area does:

| | AB | CD | EF |
|---|---|---|---|
| Small PCBs | **+11.45%** | −1.90% | −4.03% |
| Medium PCBs | −1.80% | −1.72% | −1.03% |
| Large PCBs | +0.01% | −0.01% | +0.02% |

**AB gains small boards; EF loses them.** AB picks up the GSR-2-mandated front
camera, front radar and driver monitoring. EF loses lidar outright and
three-quarters of its basic camera ECU. Large PCBs do not move because none of
the relabelled components carry one.

### 3.3 Sensor elements — did not move

**Zero change: all 27 elements, all three segments, identical to the decimal.**

Not a plumbing failure — `SensorElementsMC` does apply the presence factors
(lines 176, 352), and `07_` does carry compositions for lidar's
`laser diode array`, `photodetector array` and `IMU`, so a change would
propagate. **The stored outputs were already current: the user re-ran the model
after the relabelling.** The claim in `HANDOVER_2026-08-09.md` §3 that its outputs "have
NOT been re-run" was right for the PCB chain and wrong for this model.

---

## 4. The structural finding

**The project is now split down the middle.**

| | year axis | drivers | reaches 2070 |
|---|---|---|---|
| `BevWiring.py` | 2020–2070 | architecture, voltage, tier, lidar, scenario | yes |
| `SensorNumbersMC.py` | 2020–2070 | tier, voltage, scenario | yes |
| **`SensorElementsMC.py`** | **none** | static `01_` labels | **no** |
| **`PCBAreaMC.py`** | **none** | static, via `11_` | **no** |
| **`PCBElementMC.py`** | **none** | static `04_` | **no** |

The scale of the mismatch, from the model that does have a time axis:

| Sensor count, mean | 2025 | 2070 | growth |
|---|---|---|---|
| AB | 292.9 | 423.6 | **1.45×** |
| CD | 435.8 | 565.4 | 1.30× |
| EF | 639.2 | 734.0 | 1.15× |
| **ADAS domain only, AB** | 14.2 | 23.9 | **1.69×** |

So `PCBAreaMC`'s 16,906 mm² for AB is a 2025 figure that will still read
16,906 mm² in 2070, while the sensor model behind it grows 45%. The two are not
describing the same vehicle after about 2030.

**That is the gap step 7 exists to close**, and it is the same gap steps 3–5
closed for the sensor model: port the accumulator, add the year axis, read the
shared drivers rather than a frozen label.

---

## 5. Also found: `11_` and `12_` are inputs but not in git

`.gitignore` excludes `*.csv` globally, so `Data/11_PCB_Distribution_Classified.csv`
and `Data/12_Motor_Distribution.csv` are untracked — yet `PCBAreaMC` cannot run
without `11_`.

Same class of problem as `17_`/`18_` before 2026-08-05, but milder: both files
are **regenerable** by running `BEVElectronicsClassification.py` from the repo
root. Nothing currently documents that dependency, and it was only found here by
tracing the chain by hand.

Options: track them as exceptions to the `*.csv` rule, or document the
regeneration step as a prerequisite. Not decided.

---

## 6. What this diagnostic did NOT do

- No fix to `01_`, `11_`, `12_` or any model. The two re-runs are the only
  change, and they only refreshed generated outputs.
- No decision on step 7.
- No view on whether `PCBElementMC` (reads `04_`) needs the same treatment — it
  is outside the `01_` chain and was not examined.
