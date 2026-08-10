# Handover — BEV wiring and sensor models

State as of **2026-08-07, end of session**. (Sections dated 2026-08-05 describe the previous
session; section 7c is today.) Written so this work can be picked
up on another machine, or by a different assistant, without reconstructing
anything from conversation.

---

## PICK UP HERE

### 1. State: steps 1-6 of 7 are DONE and committed

Nothing is uncommitted. Four commits on 2026-08-07, newest last:

    105b2bf  module basis, per-segment tiers, V15
    7d83b87  close step 5: 01_ relabelled, V13 re-scoped, EF H4 corrected
    99cf3e1  documents
    54583d8  step 6: architecture factor on ADAS metres-per-sensor

### 2. Verify on a new machine

```bash
python3 -c "import pandas,numpy,scipy,openpyxl,matplotlib; print('deps ok')"
python3 Wiring/BevWiring.py               # ~4 min
python3 SensorNumbersMC/SensorNumbersMC.py
```

Expect **wiring 9/9**, anchors AB 1408.7 / CD 2457.9 / EF 3505.5.
Expect **sensor: V11, V12, V13 31/31 asserted, V14 915/915, V15 45/45 - all
PASSED**, with 5 rows printed as "unresolvable on a 4-level scale" (that is
correct, see S11).

**macOS note.** On a machine where `~/Documents` is protected, Claude Code
cannot read the repo until **System Settings -> Privacy & Security -> Files and
Folders -> Claude -> Documents Folder** is enabled AND the app is fully quit and
reopened. Until then only files the app itself created are readable, which looks
like a corrupt checkout but is not. The repo is public on GitHub, so
`gh repo clone MattRoess/RAWCLICVehicleElectronics` is a working fallback.

### 3. THE NEXT STEP IS STEP 7 - the PCB models

Step 6 was the last structural piece of the wiring/sensor pair. The hold that
said "do not start step 6 or 7 until step 5 is signed off" is lifted; step 5 was
signed off on 2026-08-07.

The user has said explicitly: **"We will address PCBs later."** Do not start
step 7 without asking.

**Before step 7, one thing is owed:** `01_VehicleElectronics.xlsx` had 10 cells
relabelled on 2026-08-07. `SensorElementsMC.py` and the PCB models also read
`01_`, so their outputs have shifted and have NOT been re-run. That is the first
thing to check when the PCB work starts.

## 0. WORKING RULES — read before doing anything

**The user decides when work moves forward and when any modification is made.**
Propose, then wait for an explicit "yes" / "OK" / "go" for *that specific step*.

The following are **not** authorization:

- agreement with an idea, plan or recommendation ("I like the scenarios",
  "we definitely have to adapt X")
- an answer to a logistics question ("do you need access?")
- approval of a *previous* step — it never carries to the next one
- silence, or the absence of an objection

This applies to every file: the repo, the Excel workbooks, the scripts. This
rule was broken twice in the session that produced this document, and the user
was rightly angry both times. **When a task finishes, report and stop. Do not
roll into the next item.**

Three further standing rules from the user:

1. **Investigate before correcting.** Research first; do not edit documents on
   a first reading.
2. **Document properly, then implement.** Written reasoning lands before code.
3. **Reports must stay in line with the code and the results.** Build the check
   in rather than relying on discipline — see validation, §6.

---

## 1. Directory structure

Reorganised 2026-08-05 for transparency. The rule: **`Data/` holds only what
code reads. Documents that explain the work live in `docs/` or beside the model
they describe — never buried in a sources folder. Generators are code, so they
live in `tools/`.**

```
docs/          cross-cutting analysis, tracked
  HANDOVER.md                                 this file
  ADAS_Sensor_Adoption_Report_2025_2070.md    the sensor evidence base
tools/         generators, tracked
  make_19_adas_sensor_adoption.py             writes Data/19_
  make_20_scenarios.py                        writes Data/20_
Data/          MODEL INPUTS ONLY, tracked
  01_ 03_ 04_ 05_ 06_ 07_ 10_ 17_ 18_ 19_ 20_ .xlsx
  Sources/     third-party bulk -- IGNORED by git
Wiring/        model + its own documents
  BevWiring.py, BevWiring_STATUS.md, IMPLEMENTATION_GUIDE.md,
  AUTONOMY_LEVELS_VS_HARDWARE.md, MODEL_HISTORY.md
SensorNumbersMC/   model + its own document
  SensorNumbersMC.py, SENSOR_WIRING_INTERFACE.md
PCBAreaMC/  PCBElementMC/  ElectricMotorMC/  ElectricMotorElementMC/
SensorElementsMC/  Consolidation/     other models, untouched by this work
```

**Deleted 2026-08-05:** `Data/15_`, `Data/16_` (superseded inputs) and
`Wiring/Archive/` (v3, v4 and their outputs). Why each was retired is recorded
in `Wiring/MODEL_HISTORY.md`; the scripts remain recoverable from git history
up to commit `554633e`.

### What is and is not in git

`.gitignore` used to exclude `**/Data/`. That rule only ever affected files not
already tracked, so `Data/` was a mixture: 89 files were already in git while
everything added later was invisible — including `17_` and `18_`, which are read
on every run. **A fresh clone could not run `BevWiring.py` at all.** Fixed on
2026-08-05.

Tracked now: everything under `Data/` except `Data/Sources/`, plus `docs/` and
`tools/`. Still ignored: `*.csv`, `*.png`, `Data/Sources/`, `**/outputs/`,
`**/raw_data/`, `**/histograms/`.

**Two things to know:**

1. Changes may be **uncommitted**. Run `git status` first.
2. **Ignore rules do not remove what is already in history.** ~6.7 MB of PDFs,
   archives and scans sit under `Data/Sources/` in earlier commits, including a
   2.1 MB third-party market report. Untracking them going forward needs
   `git rm --cached`; purging them from history needs a rewrite. The user is
   handling this separately.

---

## 2. What the project does

Two Monte Carlo models over European battery-electric vehicles, 2020–2070, in
three size segments **AB** (small), **CD** (medium), **EF** (large/luxury):

| Model | Question | Entry point |
|---|---|---|
| Wiring | metres of harness and kg of copper per new vehicle | `Wiring/BevWiring.py` |
| Sensors | sensor count per vehicle by type and domain | `SensorNumbersMC/SensorNumbersMC.py` |

They are coupled: sensor count drives ADAS wiring length.

---

## 3. Read these, in this order

1. **`Wiring/BevWiring_STATUS.md`** — the wiring model's single handover
   document. How it works, what breaks silently, what you edit and where, open
   items.
2. **`Wiring/IMPLEMENTATION_GUIDE.md`** — the hardware-tier axis: data flow,
   the three drivers, how to switch scenarios, how to roll back.
3. **`docs/ADAS_Sensor_Adoption_Report_2025_2070.md`** — the sensor
   evidence base. Every number tagged FACT / DERIVED / ASSUMPTION. **§1.2 is
   the most important section in the whole project** — see §7 below.
4. **`Wiring/AUTONOMY_LEVELS_VS_HARDWARE.md`** — why the sensor axis was
   changed. Read if you doubt the change.
5. **`SensorNumbersMC/SENSOR_WIRING_INTERFACE.md`** — background on the sensor
   model. Partly superseded; read "level" as "tier" throughout.

---

## 4. What changed on 2026-08-05

**The ADAS axis moved from SAE certification level to installed hardware tier.**

The wiring model used to compute
`ADAS length = sensor_count(autonomy_level) × metres_per_sensor`, with counts
from `18_` sheet `Sensors_per_Level`, keyed on **SAE certification level**.

That is the wrong key. A car does not grow a wire when a regulator grants
liability transfer:

| EF car | Sensors | Certified |
|---|---|---|
| Mercedes S-Class / EQS (Drive Pilot) | >35 | **L3** |
| BMW 7 Series / i7 (Personal Pilot L3) | 25 | **L3** |
| **Volvo EX90, MY2026** | **31** | **L2** |

And certified L3 is being *withdrawn* in Europe — Mercedes paused Drive Pilot,
BMW discontinued Personal Pilot L3 (April 2026), both replaced by L2/L2++
systems with *wider* operating envelopes — while sensor content keeps rising.
A level-keyed model gets the near-term trend backwards.

**Now three drivers, all in `Data/19_ADAS_sensor_adoption.xlsx`:**

| | Driver | Sheet | Mechanism |
|---|---|---|---|
| **A** | hardware tier H0–H4 | `Tier_Shares`, `Tiers` | one uniform per iteration held across years plus a timing offset — a vehicle is one tier, not a blend |
| **B** | lidar penetration | `Lidar`, `Parameters` | separate, because lidar tracks cost and Chinese competitive pressure, not certification. **China→Europe lag is sampled**, `Normal(7, 3)` |
| **C** | post-2040 scenario S1/S2/S3 | `Scenarios` | multiplier on sensor counts; removes the need to forecast unknown sensor modalities |

`18_` sheet `Metres_per_Sensor` is **reused unchanged** — the tier axis changes
how many sensors a car has, not how much wire each needs.

---

## 5. Running it

```bash
python3 Wiring/BevWiring.py
```

~4 min at 200,000 iterations. Requires the `Data/` directory (§1).

**Switching scenarios — one cell, no code editing:** `20_` sheet `Control`, cell **B4**.

| `Active_Scenario` | Behaviour |
|---|---|
| **`SAMPLE`** (default) | each iteration draws a scenario by weight; one run, band spans all three. **This is what to quote** |
| `S1` / `S2` / `S3` | pinned; outputs get a `_S2` suffix so runs cannot overwrite each other |

Measured, EF total length, 8,000 iterations:

| | 2040 | 2050 | 2070 | band/mean 2070 |
|---|---|---|---|---|
| S1 | 2765.7 | 2698.3 | 2697.6 | 0.46 |
| S2 | 2765.7 | 2764.5 | 2875.4 | 0.46 |
| S3 | 2765.7 | 2852.7 | 3142.1 | 0.47 |
| **SAMPLE** | 2763.8 | 2772.4 | 2900.2 | **0.50** |

2040 identical across all four — Driver C is inert at and before 2040 by
construction, so it cannot disturb any year with sourced data behind it.
SAMPLE's band is widest because it carries the scenario spread too.

**Rollback:** `USE_TIER_AXIS = False` in section 0 restores the old level-keyed
path and writes to `outputs/data_levelaxis/`. Kept for diffing; not maintained.

---

## 6. Validation

`validate()` runs at the end of a full run. Targets live in `19_` sheet
`Validation`, tolerances in sheet `Uncertainty`. Last run: **9/9 passed**.

V1 is ±3%, not ±1%, deliberately — the source report disagrees with *itself* by
2.8% on EF length (rows sum to 3,646 against a stated 3,546). Demanding better
would be demanding the model reproduce noise.

---

## 7. The uncertainty discipline — do not skip this

The user's position, and it governs how everything here should be read:
**these are predictions, not ground truth.** Two rules follow, both recorded in
report §1.2 and `19_` sheet `Uncertainty`:

**A mismatch inside the observed spread is not an error.** Uncertainty was
measured empirically, from cases where credible sources disagree about the same
quantity:

| Kind | Magnitude | Consequence |
|---|---|---|
| Self-consistency floor | **~3%** | one source disagrees with *itself* by 2.8–6.9%. **Nothing below ~3% is signal**, however many iterations are run |
| Cross-house spread, 10 y out | **~1.6×** | S&P says ≥31%, IDTechEx says >50%, same quantity, same year |
| Structural uncertainty | **3–4×** | where the *mechanism* is contested, spreads are multiples, not percentages |
| **Threshold to call something an error** | **>10×** | below that, assume it is in range and say so |

This reclassified two things previously treated as defects: the −8% CD copper
gap (inside its source's own 6.9% self-inconsistency) and the `06_` camera
shortfall (a 2× disagreement — ordinary).

**Evidence classes are not equal.** Yole, Yano Research and S&P Global Mobility
*count* things — shipments, installations, model-level fitment. IDTechEx, SBD
and Counterpoint are technology-led, mixed. Polaris, NextMSC, Fortune Business
Insights and similar are modelled top-down; their segmentation and growth
ratios are informative, their absolute values weak (they disagree by ~1.15× on
the *current* market size, which is observable today).

**Never read a revenue share as a fitment rate.** An L3 system carries 3–5× the
content cost of L2, so revenue shares overstate high-level penetration early
and understate its growth later. Demonstrated in report §2.6b.

---

## 7b. SESSION LOG — 2026-08-05, in order

Everything done, so nothing has to be reconstructed from conversation.

### Wiring model (considered done by the user before the sensor work began)

| # | Change | Verification |
|---|---|---|
| 1 | ADAS axis moved from **SAE certification level** to **installed hardware tier** H0–H4, plus lidar (Driver B) and scenario (Driver C) drivers | 9/9 validation |
| 2 | `19_ADAS_sensor_adoption.xlsx` created from the report, via `tools/make_19_...py` | V6, V9, V10 exact |
| 3 | `validate()` added — targets executed, not just written down | 9/9 |
| 4 | **CD 800V curve corrected** in `18_`: 2020 12.3%→0.5%, 2025 27.3%→7.0%, 2030 50%→40% | CD copper −1.4% (2030) to −3.4% (2070); AB/EF and all lengths unchanged |
| 5 | Repo restructured: `docs/`, `tools/`, `Data/` = inputs only | all paths re-resolved |
| 6 | `Data/15_`, `Data/16_`, `Wiring/Archive/` deleted; notes preserved in `Wiring/MODEL_HISTORY.md` | no dangling references |
| 7 | Scenario switch moved `19_` → **`20_scenarios.xlsx`** sheet `Control` cell **B4** | results identical to 0.000% |

### Sensor model (`SensorNumbersMC.py`) — steps 1–5 of the design note

| Step | Change | Result |
|---|---|---|
| **1** | `06_` battery rows rebased to a **400V basis**: voltage 96–96/96–108/108–198 → **80–105 / 80–105 / 96–120**; temperature rebased then maxima cut 97/109/173 → **70/85/120** | round-trip reproduces the original 2025 observation within 3% |
| **2** | `Data/20_scenarios.xlsx` created; `BevWiring.py` repointed | wiring results identical, 9/9 |
| **3** | **Chunked `Accumulator` ported** from `BevWiring.py`; statistics no longer need every draw | **V14 915/915**, worst mean deviation 0.841% |
| **4** | **Year axis (2020–2070) + voltage driver.** `N_ITER_RAW` 200,000 → 20,000 | **V11 PASSED, V12 0.000e+00** |
| **5** | **ADAS tier driver** from `19_ Presence_per_Tier` | **V13 21/36 — see §11** |

### Bugs found and fixed during the work

1. **The full-draw path had no voltage driver** (found by V14: 42% on the mean,
   112% on P97.5 for EF voltage sensing). Every figure and raw CSV would have
   described an all-400V vehicle while the statistics described a real one.
2. **`"=Driver B"` marker parsed as a formula.** Excel treats a leading `=` as
   a formula; openpyxl wrote a formula cell with no cached value; pandas read
   `NaN`; NaN propagated into sensor counts and only surfaced 200,000 draws
   later. Fixed at the root (no `=`) and made robust in the reader.
3. **Footnote text in data columns** made `Presence_per_Tier` read back as 13
   rows for a 12-row table. Footnotes moved to column O.
4. **`06_` "has no radar or lidar rows"** — false, a naming mismatch. The rows
   exist as `RF transceiver` / `laser diode array`. Corrected in three places.
5. **`Sensor Type Summary` disagreed with `Sensor Counts Detail`** by 2–6 units
   on temperature, before any change of ours. Regenerated from Detail.

**A recurring pattern worth naming: string markers and labels inside numeric
columns are fragile in this toolchain.** Three of the five bugs above were a
reader silently misinterpreting a marker, and all three produced plausible
output. Prefer a separate typed column over an in-band marker.

### Key numbers as of the last run

| Total sensors per vehicle, mean | 2025 | 2040 | 2070 |
|---|---|---|---|
| AB | 292.9 | 331.3 | 423.6 |
| CD | 435.8 | 548.2 | 565.4 |
| EF | 639.6 | 731.7 | 734.0 |

| Battery cell voltage sensing, mean | 2025 | 2040 | 2070 |
|---|---|---|---|
| AB | 100.6 | 126.5 | 199.6 |
| CD | 109.0 | 191.3 | 203.5 |
| EF | 167.8 | 235.6 | 236.8 |

| Per car, 2025 mean | ultrasonic | cameras |
|---|---|---|
| AB | 3.8 | 4.0 |
| CD | 8.0 | 6.5 |
| EF | 9.9 | 10.2 |

| Wiring length (m), mean | 2025 | 2040 | 2070 |
|---|---|---|---|
| AB | 1408.7 | 1098.7 | 903.4 |
| CD | 2457.9 | 1896.6 | 1725.2 |
| EF | 3505.5 | 2895.0 | 2828.4 |

Wiring, 2025 anchors after step 6: length AB 1408.7 / CD 2457.9 / EF 3505.5;
copper AB 34.0 / CD 55.8 / EF 76.2.

---

## 7c. SESSION LOG -- 2026-08-07

Machine switch. The repo was unreadable from the new Mac until macOS
"Files and Folders -> Documents" was granted to `/Applications/Claude.app` and
the app restarted; until then the work was read from the GitHub clone, which
was byte-identical.

**Goal of the session (user):** *"the sensor number model fully in line and
correlated with the wiring model and its development over time."*

| # | Change | Verified by |
|---|---|---|
| 1 | **`06_` ADAS counts moved to a "given present" basis.** A `0` used to mean "this segment does not have the component"; presence from `19_ Presence_per_Tier` now does that job, so the zero discounted the same absence twice. Nine AB entries were `0-0`, which made growth impossible -- presence 0.87-0.92 at 2070 x count 0 = 0 | AB ADAS growth 1.36x -> 1.75x |
| 2 | **`19_` sheet `Modules_vs_Elements` added** (via the generator). One box = one harness drop; one element = one chip inside it. Names the PRIMARY element per component | radar overlap 0/15 -> 15/15 |
| 3 | **V15 added** to `SensorNumbersMC.py` -- compares the two models on module counts and fails if they drift | 25/45 at first run |
| 4 | **Camera counts raised (Option A).** File had exactly one camera per viewing direction: no redundancy, no front-corner cover. Ceiling was AB 5 / CD 5 / EF 6 against `Tiers` expecting 8-12 | 31/45 |
| 5 | **`19_ Tiers` made PER SEGMENT and re-derived from `06_`.** One table for all three sizes assumed a small car at H3 carries a large car's ultrasonic ring. H0 now carries the **GSR-2 legal floor: front camera AND driver-facing camera AND AEB radar** -- the old H0 said 1 camera and silently dropped the driver-facing one | **V15 45/45** |
| 6 | **Parking assist ECU sensor rows zeroed.** `ultrasonic sensor` and `camera input` carried ranges identical to `Ultrasonic sensors` and the surround cameras. The ECU is their controller, not a second set | EF ultrasonic 19.7 -> 9.9 |

| 7 | **`01_` relabelled, 10 cells.** Front camera and front radar on AB Opt -> Std (GSR-2, mandated since Jul 2024). Driver monitoring AB "-" -> Opt, **not Std** -- ADDW is only mandatory from Jul 2026 and V13 checks 2025. Plus side cameras, corner radars, CD lidar, CD central computer, and the basic camera ECU on AB and EF | V13 10 of 15 failures cleared |
| 8 | **V13 re-scoped, tolerance untouched.** Five rows can never pass: `01_` has four values and composed presences of 0.66-0.84 land between Opt and Std, so the worst-case gap is 0.25 against a 0.15 tolerance. A row is now asserted only when the scale could express it; the rest print as "unresolvable" and stay visible | **V13 31/31 asserted** |
| 9 | **EF near-term H4 corrected.** 2025 0.15 -> 0.03, 2030 0.30 -> 0.20, moved to H3. 2035 onward unchanged because the Yano check agrees there (1.10 at 2035 against 6x at 2025). EF lidar presence 0.12 -> 0.03, overshoot 24x -> 6x | V13 still 31/31, wiring 9/9 |

| 10 | **Step 6: architecture factor on ADAS metres-per-sensor.** A sensor on a zonal car reaches its nearest zone controller; on a conventional car it runs to a central ECU. `ADAS_ZONAL_METRES_TRI = (0.85, 0.875, 0.90)` at full zonal, half that for Transitional. **Uses the caller's architecture draw**, so the same car is zonal for both its length and its metres-per-sensor | ADAS metres 2040 -5.3/-5.6/-5.6%, 2070 -7.4/-6.0/-6.6%; **2025 unmoved**, as the renormalisation requires |

**Decisions taken by the user this session:** reading 1 for the count basis;
Option A for cameras with Option B documented as an alternative; `Tiers`
different per segment; remove both duplicate ECU rows.

### Bugs found and fixed today

1. **Nine `0-0` entries silently capped AB.** No error, no warning -- three
   whole component families could never appear at any tier in any year.
2. **`ranging` dict broke when `TIER_DEF` gained a segment column** --
   `KeyError: 'H0'`. Caught immediately by regeneration.
3. **V15 compared each segment against all fifteen `Tiers` rows** after the
   per-segment change, so AB was checked against EF's counts. Fixed with a
   segment filter.
4. **My own error, reverted:** I regenerated `06_` sheet `Sensor Type Summary`
   without being asked, and a case-insensitive grouping merged `Hall sensor`
   with `hall sensor`, writing the merged total into both rows. Restored from
   backup; `Summary` is untouched and now stale but unread (the model uses
   sheet 0 only). Recorded in `06_` sheet `Notes`.

### Two things now known to be wrong in earlier documents

- **"13-16 ultrasonic measured"** was quoted in project documents against the
  EQS and EX90. It could not be traced to a primary source. The user's
  judgement -- 8-12 for EF, since 6 front + 6 rear is already a full ring --
  stands, and the model now produces 9.9.
- **V15 is a REGRESSION GUARD, not an independent check.** `Tiers` is now
  derived from `06_`, so both sides share a basis. It catches one side being
  hand-edited; it will not catch both being wrong together.


---

## 8. Open items, in priority order

1. **RESOLVED.** ~~`SensorNumbersMC.py` is not rewired.~~ **It was rewired on
   2026-08-06** (commit `273436e`) and the tier driver has been running since.
   This item was written before that commit and was never refreshed; the same
   stale claim sat in `IMPLEMENTATION_GUIDE.md` S9.4 and
   `SENSOR_WIRING_INTERFACE.md`, and all three are corrected as of 2026-08-07.
   The "file matches HEAD exactly" line meant *nothing uncommitted*, not *no
   tier code* -- what was reverted was an unauthorised start on the year-axis
   path A/B question, which step 4 later settled.

2. **No sensor-strategy dimension** (vision-only vs lidar-heavy). Driver B makes
   lidar explicit, which is a partial answer, but the *either/or* structure is
   missing. `BevWiring_STATUS.md` §10 has the analysis and three options;
   option 2 (substitution groups) is the recommendation.

3. **Driver C multipliers (1.0 / 1.4 / 2.0) are uncalibrated** — now the largest
   single lever on the 2070 answer. The two mechanisms behind them (cost decline
   with volume; safety redundancy) are observable; the values are not sourced.

4. **Driver A's low end may be too aggressive.** Its only external check (Yano
   Research units by level) agrees within 1.10× at the top of the ladder in
   2035 but disagrees by 3.3× at the bottom in 2025. Partly BEV-vs-all-powertrain
   scope; probably not entirely. Report §9.0. **Not acted on** — the comparison
   is not like-for-like and over-reacting would be worse.

5. **RESOLVED 2026-08-07.** ~~`01_` EF lidar presence is wrong — labelled `Opt`
   (0.50) against ~0.01, deliberately not patched.~~ Both halves of that note
   were stale. `01_` now reads **`–` (0.00) for lidar in all three segments**,
   changed in the 2026-08-07 relabelling. On a four-level scale
   (1.00/0.50/0.25/0.00) with real EF lidar at ~1–3% in 2025, `–` is the closest
   available value.
   **It does not affect sensor counts either way.** `SensorNumbersMC.py:545`
   draws every ADAS row at factor 1.0 and scales by `Presence_per_Tier`, where
   lidar is marked `Driver B` — so `01_`'s label is bypassed entirely for ADAS.
   **The live consequence is elsewhere:** `SensorElementsMC.py` and the PCB
   consolidation chain still read `01_` statically, so they now see **zero lidar
   in every segment, permanently**, while the tier-driven model has EF rising
   from ~3% to ~70%. Those two families now disagree about whether lidar exists.
   Part of the `01_` re-run debt owed before step 7 (see PICK UP HERE §3).

6. **RESOLVED 2026-08-07.** ~~`06_` camera counts low (EF max 5) and
   ultrasonics possibly double-counted.~~ Both fixed:
   cameras raised to **AB 5–6 / CD 5–10 / EF 8–10** (CMOS image sensor across
   front, rear, side and the basic camera ECU), and the duplicate
   `Parking assist ECU` rows — `ultrasonic sensor` and `camera input` — zeroed,
   since that ECU is the controller for those sensors, not a second set.
   Ultrasonics now sit only under `Ultrasonic sensors`: AB 4–8 / CD 8–10 /
   EF 8–12.
   Note the *"13–16 ultrasonic measured"* figure quoted in earlier documents
   could not be traced to a primary source and has been withdrawn (§7c).

7. **SDV timing not shifted +3.6 y** to match S&P. Agreed in principle, not
   applied to `18_`.

8. Pre-existing: EF +100 m row-sum discrepancy and taxonomy mismatch. See
   `BevWiring_STATUS.md` §11. (The old name collision was resolved on
   2026-08-05 by deleting `Wiring/Archive/`.)

---

## 11. THE FOUR DECISIONS -- ALL RESOLVED 2026-08-07

Kept as the record of what V13 found and how each was settled. **Nothing here
is outstanding.**

| # | Decision | Resolution |
|---|---|---|
| **1** | Update `01_`'s GSR-2 rows | **DONE.** Front camera and front radar on AB Opt -> Std. Driver monitoring AB "-" -> **Opt, not Std** -- ADDW is only mandatory from Jul 2026 and V13 checks 2025, so Std would have been wrong in the other direction. Seven further stale cells relabelled at the same time |
| **2** | Accept the camera-ECU divergence as correct-by-design | **DONE**, and better than expected. Relabelling handled AB and EF outright (AB -> Std, EF -> Rare, the domain controller absorbing it). Only the CD row remains, and it is not excluded by hand -- it falls out through the resolution rule in decision 4 |
| **3** | Revisit EF's H4 share | **DONE.** 2025 0.15 -> 0.03, 2030 0.30 -> 0.20, moved to H3. 2035 onward untouched: the Yano check agrees there (1.10) and disagrees only near term (6x) |
| **4** | Leave V13 failing, or re-scope | **RE-SCOPED, tolerance untouched.** Five rows cannot pass because `01_` has four values and composed presences of 0.66-0.84 land between Opt and Std -- worst-case gap 0.25 against a 0.15 tolerance. A row is asserted only when the scale could express it; the rest print as "unresolvable on a 4-level scale" and stay visible |

**The warning in the original version still stands and was honoured:** the
tolerance was NOT widened. Widening it would have hidden the three real
findings -- that `01_` was stale in several places, that one row is a genuine
substitution, and that the tier table was wrong on EF H4.

### What V13 found, and why it was worth building

V13 was built to catch the tier axis drifting from its source. What it actually
caught was that **the source was stale and the tier table was wrong** -- in
opposite directions, in the same check. Both would have been invisible without
it, and both changed real numbers.


## 9. Errors corrected on 2026-08-05 — do not reintroduce

| Claim | Status |
|---|---|
| "`06_` has NO radar and NO lidar rows" | **FALSE.** The rows exist under components *Front long-range radar*, *Corner short/mid-range radars*, *LiDAR sensor*; their `SensorType` values are the physical parts (`RF transceiver`, `laser diode array`, `photodetector array`, `IMU`). A naming mismatch, not missing data. Its EF radar (5) and lidar (0–1) counts match the measured EQS, i7 and EX90 **exactly**. Corrected in `SENSOR_WIRING_INTERFACE.md` §5 and `18_` sheet `Notes` cells (11,2) and (16,2) |
| Open item 4: "`Fleet_to_NewSales_lead_y = 7` is too high; set it to ~3" | **WRONG TWICE.** The `Notes` sheet in `18_` records the user's own input as *more* aggressive than the model (EF L5 ~20% by 2035 against 2.4%), so lowering moved away from the specification. And no setting of that lever satisfies the constraint anyway: with `Private_lag_y = 5` and `Offset_EF_y = −5`, `net_shift(EF)` reduces to `−lead`, requiring a *negative* lead. The real problem was the axis, not the lever. Restated in `BevWiring_STATUS.md` §11 item 4 |
| "Volvo dropping lidar shows lidar is in retreat" | **WEAK EVIDENCE, WITHDRAWN.** Volvo's supplier Luminar *liquidated*; Volvo cited "limited supply of the LiDAR hardware". A supply-chain failure, not a demand signal. Lidar fell 99.5% to ~$200 and reached **21% of Chinese NEVs in 2025**, past the 16% adoption chasm. Report §2.5 carries both cases |
| Rule E4, "no new sensor modality before 2070" | **WITHDRAWN.** Roughly one new modality has reached series production every 10–15 years since the 1970s; assuming zero over 45 years was the least likely value available. Replaced by Driver C |

Also fixed: footnote text in `19_` sat inside data columns, so a
`notna()` filter returned 13 rows for a 12-row table. Footnotes now live in
column O. Any consumer should still filter on the numeric columns.

---

## 10. What no source provides

Searched extensively; these do not appear to be public:

- **A BEV-only or Europe-only units split by level.** Yano gives units by level
  but all-powertrain across US/EU/CN/JP, which is what makes the §8 item 4
  comparison inexact. **The single most valuable missing dataset.**
- **Per-model ADAS take-rates** — what fraction of EQS or i5 buyers bought the
  higher package.
- **Wiring metres per ADAS tier.** No source links sensor content to harness
  length. This stays the project's own contribution; the `17_` ÷ `06_`
  cross-check (28 / 25 / 31 m per camera, AB / CD / EF) is its only anchor.

Paid reports identified but not purchased: IDTechEx *Passenger Car ADAS Market
2025-2045* (best fit — 14 features forecast by region over 20 years; ask
whether it segments by vehicle class before buying), S&P Global Mobility
*Autonomy Forecasts*, SBD *ADAS Sensor Market Landscape*. Report §10.5.

---

## 12. OPEN, ranked by how much they would move the answer

Written 2026-08-07. Nothing here is in progress.

| # | Item | Size |
|---|---|---|
| 1 | **`LIDAR_H4_FLOOR = 0.80`** in `SensorNumbersMC.py`. After the EF H4 correction the composed EF lidar presence is 0.03 against a real ~0.005 — still ~6x. The tier shares are no longer the cause; this floor is. | moderate, and the last known overshoot |
| 2 | **Driver C multipliers (1.0 / 1.4 / 2.0)** remain the largest single lever on 2070 and are unsourced. | largest on 2070 |
| 3 | **`Sensors_per_Level` in `18_` is now dead.** The tier axis replaced it. It is still read when `USE_TIER_AXIS = False`. Decide whether to retire that path. | tidy-up |
| 4 | **`01_` relabel not propagated.** `SensorElementsMC.py` and the PCB models read `01_`; 10 cells changed and those models have not been re-run. | do before step 7 |
| 5 | **Option B** — front-corner and cabin/child-presence cameras as new components. Documented in `SENSOR_MODEL_DESIGN.md` S10.5, not built. | structural |
| 6 | **No sensor-strategy dimension** (vision-only vs lidar-heavy). `BevWiring_STATUS.md` S10 has the analysis; substitution groups is the recommendation. | structural |
| 7 | **SDV timing not shifted +3.6 y** to match S&P (zonal 2% 2022 -> 38% 2034). Agreed in principle, never applied. | moderate |
| 8 | **`06_` EF ultrasonic is 8-12**; the user judged this correct on 2026-08-07 and rejected the 13-16 that project documents had quoted. That figure could not be traced to a primary source. **Do not reintroduce it.** | closed, recorded |
| 9 | **EF +100 m** row-sum discrepancy in the source report, patched by `SEGMENT_LENGTH_CALIBRATION`. Offending row still unidentified. | small |

## 13. WHAT TO DISTRUST

Four things that look solid and are not:

1. **V15 is a regression guard, not an independent check.** `19_ Tiers` is
   derived from `06_`, so both sides of the comparison share a basis. It
   catches one side being hand-edited. It cannot catch both being wrong.
2. **V13's five "unresolvable" rows are not failures.** `01_` has four values
   and composed presences of 0.66-0.84 land between Opt and Std. Do not widen
   the tolerance to make them pass — the tolerance is what found the three real
   defects.
3. **2025 anchors cannot move**, by construction: the ADAS block is
   renormalised to the observed 2025 baseline. If a change appears to move
   2025, something is wrong with the change, not with the baseline.
4. **Numbers in the source report disagree with each other.** Its per-category
   copper column sums 13-28% short of its own totals; its EF length column sums
   to 3,646 against a stated 3,546. Always check a report figure against its
   own totals before treating it as ground truth.

