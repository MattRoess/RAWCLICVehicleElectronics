# Archive — superseded wiring models

Kept for reference only. **Nothing here is current.**
The live model is `../BevWiringV5.py`; the handover document is
`../BevWiring_STATUS.md`.

| File | What it was | Why superseded |
|---|---|---|
| `BevWiring.py` | v3 | Read `15_`, which reproduces its source report only at 2025. Spliced three snapshots with a spline plus two blended era seams, producing a peak at 2020 and a hard brake at 2030. |
| `BevWiringV4.py` | v4 | Single 2025 anchor and sampled timing, but share-WEIGHTED the transitions, so uncertainty did not widen mid-transition. ADAS growth was wrongly tied to zonal architecture. |
| `BevWiringV4_STATUS.md` | v4 handover | Superseded by `../BevWiring_STATUS.md`. Still the best record of the `15_` data-source defects. |
| `outputs/`, `outputs_v4/` | old results | Produced by the above. Do not compare against v5 output without reading why each was replaced. |

Both scripts still run if you want to reproduce the old behaviour.
