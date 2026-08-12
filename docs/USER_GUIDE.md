# User guide — running the model and its scenarios

**For someone who has not worked on this project.** No Python knowledge is
assumed. If you can open a spreadsheet and paste a line into a terminal, you can
run every scenario in this system.

---

## 1. What this system does

It estimates **how much material is inside the electronics of a battery-electric
car**, for European vehicles, from 2020 to 2070, split into three size classes:

| | |
|---|---|
| **AB** | small cars (VW Polo, Renault Zoe class) |
| **CD** | medium (VW ID.4, Tesla Model 3 class) |
| **EF** | large and luxury (BMW i7, Mercedes EQS class) |

It covers **four domains**: the wiring harness, printed circuit boards, sensors,
and auxiliary electric motors (window lifts, seats, pumps — **not** the traction
motor that drives the car).

Everything is a **Monte Carlo** model: rather than one number, it draws 200,000
simulated vehicles and reports the distribution. **The output is a range, not a
prediction.**

---

## 2. One-time setup

You need Python with a few standard packages. From a terminal, in the project
folder:

```bash
python3 -m venv .venv
.venv/bin/pip install numpy pandas scipy matplotlib openpyxl
```

That creates a self-contained environment in `.venv`. You only do this once.

**Everywhere below, `.venv/bin/python` means "the Python we just set up".**

---

## 3. The fastest possible run

To produce everything from scratch, run these **in this order** — order matters,
because later models read what earlier ones write:

```bash
.venv/bin/python BEVElectronicsClassification.py
.venv/bin/python Wiring/BevWiring.py
.venv/bin/python SensorNumbersMC/SensorNumbersMC.py
.venv/bin/python SensorElementsMC/SensorElementsMC.py
.venv/bin/python PCBAreaMC/PCBAreaMC.py
.venv/bin/python PCBElementMC/PCBElementMC.py
.venv/bin/python ElectricMotorMC/ElectricMotorMC.py
.venv/bin/python ElectricMotorElementMC/ElectricMotorElementMC.py
.venv/bin/python tools/build_composition.py
```

**Expect 20–40 minutes in total.** Some models take several minutes; that is
normal, they are simulating 200,000 vehicles each.

The final command produces the file most people actually want:

**`Data/30_BEV_electronics_composition.csv`** — material grams per vehicle, per
segment, per year.

---

## 4. Running a scenario — the part you came for

A **scenario** is a coherent story about how the future unfolds. The system has
two scenario axes, and both are changed **in a spreadsheet, not in code.**

### 4.1 Where the switch is

Open **`Data/20_scenarios.xlsx`**, sheet **`Control`**, **cell B4**.

That single cell controls the whole system. Put one of these in it:

| value in B4 | what happens |
|---|---|
| `SAMPLE` | each simulated vehicle draws its own scenario, weighted. **The default.** Use this for an overall view with full uncertainty |
| a scenario **name** | every vehicle lives in that one world. Use this to study a specific future |

**Save the file, then re-run the models** (§3). Nothing else needs changing.

### 4.2 Which scenario names exist

**Sensor-count scenarios** — sheet `Scenarios`:

| name | story |
|---|---|
| `Cost-driven convergence` | sensors get cheap but converge on a minimal set — camera plus radar, redundancy done in software |
| `Regulated redundancy` | type approval for hands-off driving requires independent sensor redundancy. **The central case** |
| `Full fail-operational` | every sensing function duplicated for driverless operation |

**Motor-content scenarios** — sheet `Motor_Scenarios`:

| name | story |
|---|---|
| `European_Content` | European interiors stay as they are; small cars keep catching up |
| `Chinese_Convergence` | Chinese-style luxury interiors — powered rear seats, leg rests, foot rests — become the European norm |
| `Cost_Constrained` | affordability limits how much equipment gets fitted |

### 4.3 A worked example

*"What if Chinese-style interiors take over in Europe?"*

1. Open `Data/20_scenarios.xlsx`, sheet `Control`, cell **B4**.
2. Type `Chinese_Convergence`. Save and close.
3. Run:
   ```bash
   .venv/bin/python ElectricMotorMC/ElectricMotorMC.py
   .venv/bin/python ElectricMotorElementMC/ElectricMotorElementMC.py
   .venv/bin/python tools/build_composition.py
   ```
4. Open `Data/30_BEV_electronics_composition.csv` and compare with your previous
   copy. **Rename the old file first**, or it will be overwritten.

The model prints its scenario at the top of the run, so you can always confirm
which world you are in:

```
Driver F scenarios: European_Content, Chinese_Convergence, Cost_Constrained
weights [0.4, 0.35, 0.25]   active = Chinese_Convergence
```

---

## 5. Changing the assumptions themselves

Beyond picking a scenario, you can change the numbers behind one. **All of them
live in spreadsheets.** You never need to edit code.

| I want to change… | open | sheet |
|---|---|---|
| how much extra equipment a segment ultimately gains | `Data/20_scenarios.xlsx` | `Motor_Scenarios` |
| how fast that arrives (cost decline) | `Data/05_VehicleElectricMotorsWeight.xlsx` | `Motor_Growth` |
| how fast zonal architecture is adopted | `Data/18_BEV_technology_penetration.xlsx` | `Penetration` |
| how fast driver-assistance hardware spreads | `Data/19_ADAS_sensor_adoption.xlsx` | `Tier_Shares` |
| **what materials are inside a sensor** | `Data/07_…` | — |
| **what materials are inside a motor** | `Data/10_…` | — |

**The last two are important.** The system deliberately does *not* forecast what
a sensor or motor is made of in 2070 — nobody can. Those files are yours to edit
if you want to explore, for example, a future with less copper.

**Every scenario column comes in three values — `Min`, `Mode`, `Max`.** `Mode`
is the most likely value; `Min` and `Max` bound it. The model draws between them,
which is where the uncertainty band comes from.

---

## 6. Reading the output

`Data/30_BEV_electronics_composition.csv` has one row per year, segment, domain
and element:

| column | meaning |
|---|---|
| `Year` | 2020–2070 |
| `Segment` | AB, CD or EF |
| `Domain` | Wiring, PCB, Sensors, Motors |
| `Element` | Cu, Fe, Au, Nd … |
| `Mass_g_per_vehicle` | **grams per vehicle** |
| `Basis` | `modelled` = the model produced this year directly; `scaled` = 2025 composition × a modelled trend |

**To get total copper per car in 2040:** filter `Year = 2040`, `Element = Cu`,
and sum `Mass_g_per_vehicle` for your segment.

Typical magnitudes at 2025 — useful for spotting a broken run:

| g/vehicle | AB | CD | EF |
|---|---|---|---|
| Motors | 23,400 | 45,600 | 95,800 |
| Wiring | 33,900 | 56,200 | 75,700 |
| PCB | 483 | 617 | 715 |
| Sensors | 196 | 296 | 368 |
| **total** | **58 kg** | **103 kg** | **173 kg** |

---

## 7. Three things to know before quoting any number

1. **These are scenarios, not predictions.** Every figure carries a wide band,
   and the band is the point.
2. **The printed-circuit-board trend is bounded by what is modelled.** The
   architecture driver reaches only 8.2% of board area, so PCB totals move only
   a few percent. That is *not* a finding that circuit-board material demand is
   flat — it means the biggest possible effect has not been quantified yet
   (see `MODEL_STATUS.md`, item `P-g`).
3. **35 of the 50 motor years are extrapolation.** Published data stops at 2035.

---

## 8. If something goes wrong

| symptom | cause and fix |
|---|---|
| `FileNotFoundError` on `11_` or `12_` | run `BEVElectronicsClassification.py` first |
| `No inputs found` from `build_composition.py` | run the models first (§3) |
| A model reports `out-of-range` draws | harmless if small; it means a few simulated vehicles fell outside the histogram range |
| A file looks empty (0 bytes) | **iCloud has not downloaded it.** Open the folder in Finder and wait for the download to finish. This has caused confusion before |
| A validation prints `FAIL` | **stop and read it.** The checks are designed to fail loudly when an assumption breaks |

**Validations are not decoration.** They caught a bug that made every motor mass
in this project twice too large. If one fails, the number it guards is wrong.
