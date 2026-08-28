# The pipeline — from raw data to the stock-and-flow input

**One page. What to run, in what order, and what comes out.**

Written 2026-08-13.

---

## 1. The shape of it

**The folders are numbered in run order.** `01_` … `07_` are the models, and the
tree itself tells you the sequence. `tools/` is unnumbered because it runs after
all of them.

```
   Data/*.xlsx  (the assumptions — you edit these)
        │
        ▼
   ┌─ classify ──────────────────────────────────────────────────┐
   │  BEVElectronicsClassification.py        (repo root)          │
   │     01_ ──► 11_PCB_Distribution_Classified.csv               │
   │             12_Motor_Distribution.csv                        │
   └──────────────────────────────────────────────────────────────┘
        │
        ▼
   ┌─ the four domains — independent of each other ──────────────┐
   │                                                              │
   │  WIRING   01_Wiring/BevWiring.py                             │
   │                                                              │
   │  SENSORS  02_SensorNumbersMC/    ──► counts                  │
   │           03_SensorElementsMC/   ──► composition             │
   │                                                              │
   │  PCB      04_PCBAreaMC/          ──► area       ─┐ order      │
   │           05_PCBElementMC/       ──► elements   ─┘ matters   │
   │                                                              │
   │  MOTORS   06_ElectricMotorMC/    ──► mass       ─┐ order      │
   │           07_ElectricMotorElementMC/ ──► elements┘ matters   │
   └──────────────────────────────────────────────────────────────┘
        │
        ▼
   ┌─ combine ───────────────────────────────────────────────────┐
   │  tools/build_composition.py  ──► Data/30_…composition.csv    │  the MEANS
   │  tools/mc_composition.py     ──► joint_mc_stats.csv          │  the BAND
   │                              ──► Composition/draws/*.npy     │  the DRAWS
   └──────────────────────────────────────────────────────────────┘
        │
        ▼
   ┌─ use it ────────────────────────────────────────────────────┐
   │  tools/plot_composition.py    the figures                    │
   │  tools/driver_sensitivity.py  which assumptions matter       │
   │  RAWCLICStockAndFlow          ◄── the actual consumer        │
   └──────────────────────────────────────────────────────────────┘
```

**Why the folders are numbered and the files are not.** A Python file whose name
starts with a digit cannot be imported — `import 01_BevWiring` is a syntax error
— and `tools/mc_composition.py` imports four of these models as libraries.
Folders carry no such restriction, because the code adds them to `sys.path` and
imports the module inside by its own name. So numbering lives on the folders.

---

## 2. Run it

**Run in folder-number order. That is the whole rule.**

```bash
.venv/bin/python BEVElectronicsClassification.py
.venv/bin/python 01_Wiring/BevWiring.py
.venv/bin/python 02_SensorNumbersMC/SensorNumbersMC.py
.venv/bin/python 03_SensorElementsMC/SensorElementsMC.py
.venv/bin/python 04_PCBAreaMC/PCBAreaMC.py
.venv/bin/python 05_PCBElementMC/PCBElementMC.py
.venv/bin/python 06_ElectricMotorMC/ElectricMotorMC.py
.venv/bin/python 07_ElectricMotorElementMC/ElectricMotorElementMC.py
.venv/bin/python tools/build_composition.py
.venv/bin/python tools/mc_composition.py
.venv/bin/python tools/plot_composition.py
```

**25–45 minutes.** Each model simulates 200,000 vehicles.

### The four order dependencies — the only ones that exist

| this | after this | because |
|---|---|---|
| `05_PCBElementMC` | `04_PCBAreaMC` | reads its histograms and year scale factors |
| `07_ElectricMotorElementMC` | `06_ElectricMotorMC` | splits its per-draw material masses |
| `mc_composition` | all four domains | pushes one car through every one |
| `plot_composition` | `mc_composition` | the bands **are** the joint Monte Carlo |

Everything else can run in any order. The four domains do not talk to each other
until stage 3.

---

## 3. What the stock-and-flow model consumes

| file | what it is | use it for |
|---|---|---|
| **`Data/30_BEV_electronics_composition.csv`** | 130,968 rows. Grams per vehicle by year, segment, domain, component type, element | the **means** |
| **`Composition/csv/joint_mc_stats.csv`** | mean, P2.5, median, mode, P97.5 per segment/domain/year | the **band** |
| **`Composition/draws/<seg>_<series>.npy`** | raw per-draw arrays, (n_iter × n_years) | pairing draw-for-draw with your own vehicle-count draws |

### The one rule that matters

**Means add. Percentiles do not.**

`30_` carries `P2_5_g` and `P97_5_g` per row. **Never sum them.** Summing
percentiles assumes every component sits at its low, or its high, at the same
moment. Measured at CD 2040: that gives 47.8 kg against a true band of 35.9 kg —
**33% too wide**.

- means → sum freely, they are exact
- band at the vehicle level → read `joint_mc_stats.csv`
- band at any other aggregation → multiply the **draws**, never the percentiles

And `30_` is **per vehicle**. Across a fleet the average is far more certain than
any single car, so per-vehicle uncertainty does not scale up unchanged.

---

## 4. Where the assumptions live

You change these, not the code:

| file | what |
|---|---|
| `Data/01_VehicleElectronics.xlsx` | which components exist, per segment |
| `Data/05_VehicleElectricMotorsWeight.xlsx` | motor masses and materials |
| `Data/10_MaterialElementDefinitions.xlsx` | **what each material is made of** |
| `Data/18_BEV_technology_penetration.xlsx` | architecture and 800 V adoption |
| `Data/19_ADAS_sensor_adoption.xlsx` | ADAS tiers and lidar |
| `Data/20_scenarios.xlsx` | scenario switch — `Active_Scenario` |

Before arguing about any of them, run:

```bash
.venv/bin/python tools/driver_sensitivity.py
```

It reports how much of the total uncertainty each one actually carries. Most
carry very little — see `02_MODEL_STATUS.md` §2.0.

---

## 5. The design rule this pipeline obeys

> **A change of composition must not change the structure or the run design.**

Which material a part is made of is **data**. It belongs in
`10_MaterialElementDefinitions.xlsx`, and changing it should require editing that
workbook and nothing else — not renaming a folder, not adding a code branch, not
altering the run order.

**The magnet switch on 2026-08-13 broke that rule.** Changing the auxiliary-motor
magnets from NdFeB to strontium ferrite — a pure composition change — required a
new loader function, a new sampler function, a new mass-column entry, edits to
two hardcoded `if stream == …` blocks, and a renamed output folder that orphaned
the old one. None of that was inherent to the change; all of it came from
`07_ElectricMotorElementMC` hardcoding one branch per material.

### Fixed — the stream table

`07_ElectricMotorElementMC/ElectricMotorElementMC.py` now holds one `Stream`
entry per material, and everything that differs lives in it as data:

```python
"magnet": Stream(
    key="magnet", label="Strontium Ferrite", folder=MAGNET_ROOT,
    sheet=FERRITE_SHEET, mass_col="mass_kg__NdFeB",
    grades=list(FERRITE_GRADES), order=FERRITE_ELEMENTS,
    balance="Fe", balance_tol=FERRITE_FE_TOL,
    weights=lambda seg, motor: FERRITE_GRADES,
    hist_globs=["hist_materialmass_*_NdFeB.csv", …],
),
```

Four loader functions collapsed into `load_grades(xlsx, spec)`. Four sampler
functions collapsed into `sample_composition(spec, …)`. Two hardcoded config
blocks became a table lookup. `main()` became a loop over `STREAMS`.

**To change or add a material now:**

1. put its grades in `Data/10_MaterialElementDefinitions.xlsx`
2. add or edit its `Stream` entry
3. re-run

**Verified byte-identical.** All 540 rows and 6 numeric columns of
`elemental_summary.csv` match the pre-refactor output exactly — max absolute
difference **0.000e+00**. The generic loop draws grade-by-grade,
element-by-element in the declared order, so it consumes the random stream in
exactly the sequence the four hand-written samplers did. The structure changed
and nothing else.

Two things the table also made explicit rather than incidental:

- **The balance element is now a declared property** (`balance="Fe"`), not three
  near-identical hand-written blocks. That is where the NdFeB normalisation bug
  survived unnoticed — its sampler was the one that forgot to do it.
- **A stream's key names its role, its label names its chemistry.** The folder is
  `MagnetElemental` whatever magnet is modelled; `label="Strontium Ferrite"`
  carries the chemistry into the `Stream` column of the data, which is where
  content belongs.

---

## 5a. Output folder naming — the same problem, visible

`07_ElectricMotorElementMC` writes one folder per material stream:

| today | names the… | problem |
|---|---|---|
| `CopperElemental` | material | — |
| `ElectricalSteelElemental` | material | — |
| `CastFeSteelElemental` | material | — |
| ~~`NdFeBElemental`~~ → `MagnetElemental` | **role** | fixed 2026-08-13 |

**Naming an output folder after its content is a bad habit.** When the magnet
chemistry changed from NdFeB to strontium ferrite, `NdFeBElemental` was orphaned
— left in the tree holding superseded numbers that a glob could still pick up.
The magnet folder is now named for its **role**, so it survives the next
chemistry change.

The other three have the same weakness. Copper windings will stay copper, so it
has not bitten — but the habit is the problem, not the odds.

**Proposed, not done:** rename all four for role.

| now | proposed |
|---|---|
| `CopperElemental` | `WindingsElemental` |
| `ElectricalSteelElemental` | `LaminationsElemental` |
| `MagnetElemental` | `MagnetElemental` ✓ |
| `CastFeSteelElemental` | `HousingElemental` |

The actual material stays recorded in the data, in the `Stream` column, which is
where content belongs.

**Two safeguards now in place regardless.** `build_composition.py` and
`mc_composition.py` used to read `sorted(glob(...))[0]` — whichever folder sorted
first. They now read **all** copies and **fail loudly** if they disagree, naming
the stale folder instead of silently trusting alphabetical order.

---

## 6. Housekeeping needed right now

The magnet rename left two orphaned folders. The guard above will refuse to run
until they are gone:

```bash
rm -rf 07_ElectricMotorElementMC/NdFeBElemental 07_ElectricMotorElementMC/FerriteElemental
```

Then re-run from `07_ElectricMotorElementMC` onward.
