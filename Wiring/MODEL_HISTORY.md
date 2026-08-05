# Wiring model — version history and retired inputs

Record of why earlier generations of the model, and the data files behind them,
were replaced. **Nothing here is current.** The live model is `BevWiring.py`
and the living handover document is `BevWiring_STATUS.md`.

Written 2026-08-05, consolidating `Wiring/Archive/README.md` and
`Wiring/Archive/BevWiringV4_STATUS.md` before that directory was deleted. The
scripts themselves (`BevWiring.py` v3, `BevWiringV4.py`) and their outputs are
recoverable from git history up to commit `554633e`.

---

## 1. Version history

| Generation | Why it was replaced |
|---|---|
| **v3** (`BevWiring.py`, archived) | Read `15_`, which reproduces its source report only at 2025. Spliced three snapshots with a spline plus two blended era seams, producing a peak at 2020 and a hard brake at 2030. Also used one shared percentile with 0.05 jitter, forcing correlation ≈ 1 across all categories |
| **v4** (`BevWiringV4.py`) | Single 2025 anchor and sampled timing — the right structure — but **share-weighted** the transitions, so uncertainty did not widen mid-transition. ADAS growth was wrongly tied to zonal architecture |
| **v5** (`BevWiring.py`, current) | Discrete architecture states, three independent drivers. ADAS content re-keyed from SAE certification level to installed hardware tier on 2026-08-05 |

---

## 2. Why `15_BEV_wiring_harness_data.xlsx` was retired, then deleted

Six verified, reproducible defects. This is the reason the file no longer
exists, and the reason no future version should reintroduce it:

1. **It reproduces its own source report only at 2025.** At 2020 it is
   0.70–0.76× the report; at 2030 it is 1.00–1.25×. The report's AB trajectory
   is a symmetric −44% / −44%; the workbook turns it into −19.8% / −30.1%.
   That asymmetry is what v3's spline converted into a peak and a plunge.
2. **The report's trajectories are pure exponentials** — AB length ratios
   0.560 / 0.560, AB copper −48% / −48%. An exponential has no kinks, so the
   kinks were an artefact of the workbook, not the source.
3. **It merges two independent transitions into one 2030 event.** 800V and
   SDV/zonal are separate, hit different quantities, and run on different
   timelines.
4. **Its `AWG` / `Cross_Section_mm2` are stale** — identical across all three
   periods, so they do not track the 400→800V switch at all.
5. **Its copper columns are `length × a constant`.** Implied Cu/m is identical
   at min, mode and max, so they carry no independent diameter information.
6. **It puts all segments at 100% 800V by 2030.** The report says A/B is 15% by
   2030 and that 400V *persists* through 2030 for A/B.

`16_BEV_wiring_transition_parameters.xlsx` was v4's timing input, superseded by
`18_` when the model moved to discrete states. Deleted at the same time.

---

## 3. Two contradictions found inside the source report

Both were found while building `17_`, both still matter, and both are carried
forward in `BevWiring_STATUS.md`. Recorded here because this is where the
evidence was first assembled.

### 3.1 The per-category copper column does not sum

| Segment | Σ length | stated | Σ copper (report's own column) | stated |
|---|---|---|---|---|
| AB | 1,392 ✓ | 1,392 | **26.4** | 33.9 |
| CD | 2,486 ✓ | 2,486 | **43.3** | 60.3 |
| EF | 3,646 ✗ | 3,546 | **65.1** | 74.6 |

Length sums exactly for AB and CD; copper is 13–28% short everywhere.
Rebuilding copper from length × gauge lands within 1–7% instead.

**Consequence, still binding:** the model never reads copper as a given. It is
always `length × Cu-per-metre`, with Cu-per-metre from the conductor gauge.
The direct copper figures in *both* sources are unreliable.

EF length is 100 m over its own stated total — the 2.8% self-inconsistency that
now sets the **noise floor for the whole chain**. The offending row has never
been identified.

### 3.2 The report contradicts itself on SDV depth, by ~4×

| Segment | from its mechanisms (§6.2/§8.4) | its stated totals (§6.3/§7.1) |
|---|---|---|
| AB | 1,223 m (−12%) | 780 m (−44%) |
| CD | 2,216 m (−11%) | 1,492 m (−40%) |
| EF | 3,256 m (−8%) | 2,730 m (−23%) |

Reaching the stated totals requires CAN → ×0.00, LIN → ×0.00, LV_BODY → ×0.03.
§6.2 claims none of that.

**Decision taken (yours, 2026-08-04):** do not pick a side. SDV depth is a
sampled MC parameter spanning both readings. This is why the AB band is wide —
the disagreement is real. Still in force, via `17_` sheet `SDV_Depth`.

---

## 4. User decisions on record

Taken during v4 development and still binding unless explicitly revisited:

| Decision | Choice |
|---|---|
| Output basis | per new vehicle **sold**, not parc; turnover stays in RAWCLICStockAndFlow |
| AB 800V timing | override the report; ~0% 2030, 50% ~2045 |
| CD / EF 800V timing | pull toward report (45% by 2028, 75% by 2027) |
| AB curve shape | slowest segment, slowest ramp |
| Category taxonomy | adopt the report's 28 codes |
| SDV depth conflict | sample across both readings, do not choose |
| Model start year | 2020, not 2010 — the report has nothing earlier and v3's 2010 backcast was invented |

---

## 5. Items from v4 that are still open

Carried into `BevWiring_STATUS.md` §11 unless noted:

1. **EF +100 m** — see §3.1. Patched by `SEGMENT_LENGTH_CALIBRATION`; bad row
   unfound.
2. **SDV `T_FULL` values are inferred** from platform-availability dates plus an
   assumed lag to new-sales share. That lag is not in the report.
3. **2020–2025 legacy correction is applied uniformly** across categories,
   because the report gives no per-category split for 2020. Ethernet and ADAS
   were growing over that period, so their 2020–2025 shape is the weakest part
   of the early output.
4. **Taxonomy is not 1:1** with the old 28 wire types — see `17_` sheet
   `Mapping`. Downstream consumers expecting the old names need updating.
