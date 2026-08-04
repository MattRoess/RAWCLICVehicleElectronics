> **SUPERSEDED 2026-08-04.** The current model is `BevWiringV5.py` and the
> living handover document is `BevWiring_STATUS.md`. This file is kept as the
> record of v4 and the data-source findings that led to it.

# BEV wiring model — status and handover

**Last updated:** 2026-08-04
**Read this first when picking the work back up.**

---

## 1. Where things stand

`BevWiringV4.py` is written, runs end to end, and reproduces the source
report's 2025 anchor. It is ready for you to test.

`BevWiring.py` (v3) is **untouched and still runs**. Nothing was deleted.
v4 is a separate module with its own output folder.

| File | Role | Status |
|---|---|---|
| `Wiring/BevWiringV4.py` | the model | new, working |
| `Wiring/BevWiring.py` | old v3 model | untouched, superseded |
| `Data/17_BEV_wiring_baseline_2025.xlsx` | 2025 baseline, gauges, SDV factors | new |
| `Data/16_BEV_wiring_transition_parameters.xlsx` | 800V + SDV timing | new |
| `Data/15_BEV_wiring_harness_data.xlsx` | old input | **no longer read** |

Run it with:

    python3 Wiring/BevWiringV4.py

Outputs land in `Wiring/outputs_v4/` — two CSVs and eight plots.

---

## 2. Why v4 exists

v3 produced a peak at 2020 and a hard brake at 2030 in every category. The
cause was not the spline. It was the input data.

Verified findings, all reproducible:

1. **`15_` reproduces its own source report only at 2025.** At 2020 it is
   0.70–0.76× the report; at 2030 it is 1.00–1.25×. The report's AB trajectory
   is a symmetric −44%/−44%; the workbook turns it into −19.8%/−30.1%. That
   asymmetry is what the spline converted into a peak and a plunge.
2. **The report's trajectories are pure exponentials.** AB length ratios
   0.560 / 0.560; AB copper −48%/−48%. An exponential has no kinks.
3. **`15_` merges two independent transitions into one 2030 event.** 800V and
   SDV/zonal are separate, hit different quantities, and run on different
   timelines.
4. **`15_`'s `AWG` / `Cross_Section_mm2` are stale** — identical across all
   three periods, so they do not track the 400→800V switch at all.
5. **`15_`'s copper columns are `length × a constant`.** Implied Cu/m is
   identical at min, mode and max, so they carry no independent diameter
   information. The direct-vs-length comparison could not discriminate.
6. **`15_` puts all segments at 100% 800V by 2030.** The report says A/B is
   15% by 2030 and that 400V *persists* through 2030 for A/B.

---

## 3. Two contradictions inside the report itself

Both found while building `17_`. Both matter.

### 3.1 The report's per-category copper column does not sum

| Segment | Σ length | stated | Σ copper (report's own column) | stated |
|---|---|---|---|---|
| AB | 1,392 ✓ | 1,392 | **26.4** | 33.9 |
| CD | 2,486 ✓ | 2,486 | **43.3** | 60.3 |
| EF | 3,646 ✗ | 3,546 | **65.1** | 74.6 |

Length sums exactly for AB and CD. Copper is 13–28% short everywhere.
Rebuilding copper from length × gauge (Appendix A) lands within 1–7% instead.

**Consequence:** the model never reads copper as a given. It is always
`length × Cu-per-metre`, with Cu-per-metre from the conductor gauge.
This is why the length-first approach is the right one — the direct copper
figures in *both* sources are unreliable.

EF length is 100 m over its own stated total. Handled by
`SEGMENT_LENGTH_CALIBRATION` in the model (EF × 0.9726). Set it to 1.0 to use
raw figures. **The offending row has not been identified.**

### 3.2 The report contradicts itself on SDV depth, by ~4×

| Segment | from its mechanisms (§6.2/§8.4) | its stated totals (§6.3/§7.1) |
|---|---|---|
| AB | 1,223 m (−12%) | 780 m (−44%) |
| CD | 2,216 m (−11%) | 1,492 m (−40%) |
| EF | 3,256 m (−8%) | 2,730 m (−23%) |

Reaching the stated totals requires CAN → ×0.00, LIN → ×0.00, LV_BODY → ×0.03.
§6.2 claims none of that.

**Decision taken (yours, agreed 2026-08-04):** do not pick a side. SDV depth is
a sampled MC parameter spanning both readings. This is why the AB band is wide
— the disagreement is real.

---

## 4. Decisions on record

| Decision | Choice | Who |
|---|---|---|
| Output is per new vehicle sold, not parc | new sales; turnover stays in RAWCLICStockAndFlow | you |
| AB 800V timing | override the report; ~0% 2030, 50% ~2045 | you |
| CD / EF 800V timing | pull toward report (45% by 2028, 75% by 2027) | you |
| AB curve shape | option B — slowest segment, slowest ramp | you |
| SDV/zonal gets same T50/T_FULL structure | yes | you |
| Category taxonomy | **(a)** adopt the report's 28 codes | you |
| SDV depth conflict | sample across both readings | you |
| Model placement | new module; leave `BevWiring.py` alone | you |

---

## 5. How the model works

One anchor year (2025), then two smooth penetration curves. No splines, no era
seams, no blend widths — nothing that can kink.

    length(cat, seg, t) = L2025 × sdv_multiplier(t) × legacy(t) × variability
    cu_per_m(cat, t)    = gauge × 8.96 × (1 − 0.425 × share_800V(t))   [HV only]
    Cu (kg)             = Σ length × cu_per_m / 1000

- **800V** → changes HV cable Cu-per-metre only. Never length.
- **SDV/zonal** → changes LV/signal/sensor length only. Never gauge.
- Both timings are **sampled per iteration**, so trajectories do not all turn
  the corner in the same year. This is the "MC on the changes" v3 lacked.

**Car-to-car variability** is split into a shared vehicle-level term (±10%,
report §8.5) and an independent per-category term (the remainder of the ±17.5%
category-level spread). v3 instead used one shared percentile with 0.05 jitter,
which forced correlation ≈ 1 across all categories.

**Two renormalisations, easy to miss.** The 2025 baseline is an *observed*
figure, so it already contains the SDV and 800V penetration present in 2025.
Applying either effect from zero subtracts it twice. Both are divided by their
value at `BASE_YEAR`. Without this, CD copper came out ~10% low.

---

## 6. Validation as of last run

| | model 2025 | report | gap |
|---|---|---|---|
| Length AB / CD / EF | 1394 / 2486 / 3544 | 1392 / 2486 / 3546 | ≤0.2% |
| Cu AB / CD / EF | 33.5 / 55.7 / 76.3 | 33.9 / 60.3 / 74.6 | −1% / −7% / +2% |

The copper gap is the length-first reconstruction disagreeing with the report's
stated copper density. It matches the independent hand-calculation exactly
(−1/−7/+6%), so it is a real finding, not a coding error.

---

## 7. What you can change without touching code

| Want to change | Edit |
|---|---|
| When a segment adopts 800V or SDV | `16_`, sheet `Parameters`, yellow cells |
| Scenario vs uncertainty | `Mode_Year` = scenario; `Min`/`Max` = MC band |
| The SDV mechanism-vs-totals conflict | `17_`, sheet `SDV_Depth`. Set min=mode=max to collapse to one reading |
| Per-category SDV effect | `17_`, `Baseline_2025`, `SDV_Base_Length_Factor` |
| Conductor gauges | `17_`, `Baseline_2025`, `Gauge_Min/Max_mm2` |
| Copper density | `17_`, `Baseline_2025`, cell `B4` |

Every yellow cell is an input. Everything else is derived.

---

## 8. Open items

1. **EF +100 m.** The report's EF length column sums to 3,646 against its own
   stated 3,546. Currently patched by a scale factor; the bad row is unfound.
2. **SDV T_FULL values are inferred.** Derived from platform-availability dates
   plus an assumed lag to new-sales share. That lag is not in the report.
3. **EF 800V at 2027** is 58% in the model against the report's 75%. Matching
   fully needs T50 ≈ 2022, implying 66% already in 2025, which fights the 2035
   full-adoption year you gave.
4. **Model starts at 2020, not 2010.** The report has nothing earlier and v3's
   2010 backcast was invented. If RAWCLICStockAndFlow needs pre-2020, it must be
   added as an explicit, documented extrapolation.
5. **2020–2025 legacy correction is applied uniformly** across categories,
   because the report gives no per-category split for 2020. Ethernet and ADAS
   were growing over that period, so their 2020–2025 shape is the weakest part
   of the output.
6. **`15_` is superseded but not deleted.** Decide whether it should be retired
   or kept for reference.
7. **Taxonomy change.** Output now uses the report's 28 codes, not the old
   28 wire types. They are not 1:1 — see `17_`, sheet `Mapping`. Downstream
   consumers expecting the old names will need updating.
