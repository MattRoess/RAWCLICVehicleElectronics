# Documentation — read in this order

The files are numbered in reading order. **You rarely need all of them.** Pick
your path below.

---

## Pick your path

| you want to… | read |
|---|---|
| **run the model or a scenario** | **01** |
| **use the numbers** in a report or another model | **02**, then **01 §6–7** |
| **publish or write it up** | **03**, then the evidence notes 05, 08, 09 |
| **change an assumption** | **01 §5**, then the design note for that domain |
| **extend or debug the code** | **02**, then the design note, then the latest handover |
| **know what happened when** | `handover/` |

---

## 1 — Using the system

| | | |
|---|---|---|
| **01** | [`01_USER_GUIDE.md`](01_USER_GUIDE.md) | **Start here to run anything.** Setup, run order, how to switch scenarios (one spreadsheet cell), where every assumption lives, how to read the output, troubleshooting. Assumes no Python knowledge |
| **02** | [`02_MODEL_STATUS.md`](02_MODEL_STATUS.md) | **The authoritative status.** What each model produces, which are year-resolved and which are static *by decision*, the shared machinery, validation inventory, data-file map, known gaps, **and how the results must be quoted** |
| **03** | [`03_METHODS.md`](03_METHODS.md) | **The approach, for publication.** Scope, why Monte Carlo scenarios, the uncertainty calibration, data provenance separating internet-sourced FACTs from the ten judgments J1–J10, limitations, and the full reference list |

**If you read only one file, read 02.** If you are about to quote a number,
read 02 §2.

---

## 2 — Sensors

| | | |
|---|---|---|
| **04** | [`04_SENSOR_MODEL_DESIGN.md`](04_SENSOR_MODEL_DESIGN.md) | Design of the sensor count model |
| **05** | [`05_ADAS_SENSOR_ADOPTION_REPORT.md`](05_ADAS_SENSOR_ADOPTION_REPORT.md) | **The evidence base for driver-assistance adoption**, and **§1.2 defines the uncertainty calibration used across the whole project** — the 3% / 1.6× / 3–4× / >10× scale |

---

## 3 — Printed circuit boards

| | | |
|---|---|---|
| **06** | [`06_PCB_MODEL_DESIGN.md`](06_PCB_MODEL_DESIGN.md) | Design and full step log, P-a → P-g. Includes the finding that ADAS is only 3.9% of board area, the substitution-group mechanism, and **P-g — the largest unquantified effect in the project** |
| **07** | [`07_STATIC_MODELS_DIAGNOSTIC.md`](07_STATIC_MODELS_DIAGNOSTIC.md) | What was frozen in time before the year axis was added, and why lidar reads as zero in the static models |

---

## 4 — Auxiliary motors

Read in this order — each one depends on the last.

| | | |
|---|---|---|
| **08** | [`08_MOTOR_MODEL_DIAGNOSTIC.md`](08_MOTOR_MODEL_DIAGNOSTIC.md) | **Why `05_` is the count basis.** Establishes that `12_` is an ECU-attributed subset omitting window, mirror and wiper motors entirely |
| **09** | [`09_AUX_MOTOR_ADOPTION_RESEARCH.md`](09_AUX_MOTOR_ADOPTION_RESEARCH.md) | **The evidence** for motor content growth: fitment data, the cost-ceiling argument, and the Chinese-interior analysis |
| **10** | [`10_MOTOR_MODEL_DESIGN.md`](10_MOTOR_MODEL_DESIGN.md) | The convergence mechanism, the anchors, validation targets M1–M5, and Driver F — **why the Chinese-interior question became scenarios rather than a wider band** |

---

## 5 — Designed but not implemented

| | | |
|---|---|---|
| **11** | [`11_BRAND_ORIGIN_DESIGN.md`](11_BRAND_ORIGIN_DESIGN.md) | Driver E — brand origin. **Designed, never built.** Kept because the reasoning is still valid |

---

## 6 — Session history

[`handover/`](handover/) — one file per working session, newest last. Each
records what changed, what was decided, and what was left open.

| | |
|---|---|
| `HANDOVER_2026-08-09.md` | the long-running project handover |
| `HANDOVER_2026-08-10.md` | accumulator port (step P-d) |
| `HANDOVER_2026-08-12.md` | superseded by the next one |
| **`HANDOVER_2026-08-13.md`** | **the current one — start here if you are picking the project up** |

---

## Where the outputs are

| | |
|---|---|
| **`Data/30_BEV_electronics_composition.csv`** | **the deliverable** — grams per vehicle by year, segment, domain, component type and element. What a stock-and-flow model consumes |
| `Composition/figures/` | six figures of the overall electronics |
| `Composition/csv/` | the tables behind those figures |
| each model's own folder | its own figures, histograms and summaries |

**Figures are not in git** by decision. They are regenerable, but only from a
matching data state, and **re-running a model overwrites them** — copy anything
you need for a paper out of the model folders first.
