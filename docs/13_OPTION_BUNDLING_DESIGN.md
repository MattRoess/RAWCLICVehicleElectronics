# Driver G — option bundling — design note

**Purpose.** Decide how many *independent* choices a car buyer actually makes
about ADAS hardware. The sensor model currently assumes twelve. Real cars are
sold in trim levels and packages, so the true number is nearer three.

Written 2026-08-13. **Designed, measured, and deliberately NOT built.** The
measurement in §9 is the reason. Read §9 first — the rest is the reasoning
behind it, kept because the question will be asked again.

Companions: `04_SENSOR_MODEL_DESIGN.md`, `11_BRAND_ORIGIN_DESIGN.md` (Driver E),
`12_JOINT_MC_DESIGN.md` §2.

---

## 1. The defect this addresses

On 2026-08-13 the sensor model's ADAS presence became a per-vehicle Bernoulli:
presence 0.3 means 30% of cars carry the component and 70% carry none, rather
than every car carrying 0.3 of it. That was correct and necessary.

But each of the twelve ADAS components was given **its own independent coin
flip**. That is the opposite error to the one it fixed, and it is mine — it was
introduced by that change, not inherited.

Independent flips let a car have surround cameras but no parking ECU, corner
radars but no domain controller to read them. Those cars are not sold. And
because independent draws average out, the spread of the ADAS total is far
narrower than reality: twelve coins land near their mean, one coin does not.

**Neither extreme is right.** Twelve independent choices is too many; one choice
for the whole car is too few.

---

## 2. Why a scenario axis rather than a number

The honest position is that we do not know the packaging mix of the European
fleet, and no data in this project measures it. The project's rule for that case
is already settled: **where prediction is impossible, use scenarios and let the
band span them.** Driver C (sensor content post-2040) and Driver F (motor
content) both work this way.

So Driver G is not a correlation coefficient to be guessed. It is a scenario
axis with named, defensible end points, sampled like the others.

---

## 3. The bundles

Three functional bundles plus a regulatory floor. These are read off the
component list in `19_ADAS_sensor_adoption.xlsx` by **function**, not fitted —
they are how packages are actually named and sold.

| bundle | components | note |
|---|---|---|
| **Regulatory** | Front ADAS camera · Front long-range radar · Driver monitoring camera | **Not optional.** GSR-2 mandates these on new registrations; ADDW from July 2026. No draw at all |
| **Parking** | Ultrasonic sensors · Rear view camera · Side / mirror cameras · Parking assist ECU | the classic "Parking Package" |
| **Highway assist** | Corner short/mid-range radars · ADAS domain controller / fusion ECU · ADAS camera ECU (basic) | the classic "Driver Assistance Package" |
| **Autonomy** | LiDAR sensor · Automated driving central computer | top of range; lidar is additionally governed by Driver B |

Twelve components, four groups. The controller sits in the same bundle as the
sensors it reads — that pairing is the whole point, and it is what independent
flips break.

**Why the industry is consolidating.** Every option combination is another
wiring harness variant. Fewer, larger bundles are a manufacturing decision
before they are a marketing one — which makes this driver a direct concern of
the model it feeds.

---

## 4. The three scenarios

Named in plain words, because a scenario nobody can explain to a non-specialist
is not usable in a report:

| scenario | what it means, in one sentence | resembles |
|---|---|---|
| **Every option chosen separately** | a buyer ticks each feature on its own | German premium, historic long option lists |
| **Sold in packages** | features come in a few bundles, take it or leave it | VW, Stellantis, most volume EU |
| **One spec for all** | the car either has the technology or it does not | Tesla, Volvo, BYD-in-Europe |

`Active_Scenario = SAMPLE` draws one per vehicle by weight, so a single run's
band spans all three. Pinning it to one name runs that world alone. Identical
control to Driver F.

The marginal presence is **unchanged** in every scenario — only the correlation
between components changes. So the mean ADAS content is untouched and only the
band moves. That is the property to assert in validation.

---

## 5. What this does NOT model

**Brand origin is Driver E, not this.** `11_BRAND_ORIGIN_DESIGN.md` found that
BYD's European DiPilot 100 ships 12 cameras, 5 radars and 12 ultrasonics on an
A-segment car against roughly 4–6 cameras on a VW ID.3. That is a difference in
**how much hardware**, i.e. the tier — Driver A. Driver G is about **how the
optional part is grouped**. They are related and both point at the same
manufacturers, but they act on different quantities and must stay separate or
the effect is counted twice.

**Country mix is out of scope.** Specification genuinely differs between, say,
Germany and Poland. But this model is a European fleet average and the country
mix is already inside the segment averages. Making it explicit would add an axis
with no data behind it. Recorded as a stated limitation.

**Segment does not need its own bundling rule.** The intuition that EF is more
optional is backwards: EF carries the longest option list but the highest
*standard-fit* rate — a large luxury car has most of this as standard, so its
optional variance is small. AB has the widest base-to-top gap in relative terms.
The tier shares already carry this, so Driver G stays segment-independent unless
evidence appears otherwise.

---

## 6. Expected effect — read this before deciding it is worth building

| | |
|---|---|
| ADAS / sensor series band | **widens materially** — this is the point |
| sensor **total** band | small change; ~192 non-ADAS rows dominate its variance |
| **total per-vehicle** band | **barely moves** |

Measured in `12_JOINT_MC_DESIGN.md` §4: Sensors contribute ~0.0% of the total
variance, against Wiring 58.5% and Motors 42.8%.

So Driver G is worth building for the **sensor model's own honesty** — the
quantity a reader of the ADAS series would quote. It is **not** a fix for the
headline per-vehicle number, and should not be sold as one.

---

## 7. Validation to add

| | check |
|---|---|
| **G1** | marginal presence per component is unchanged from the `A_la_carte` case, within Monte Carlo noise. Only correlation changes, never the mean |
| **G2** | `Single_spec` band ⊇ `Packages` band ⊇ `A_la_carte` band, on the ADAS domain total. More bundling can only widen |
| **G3** | components within a bundle are perfectly rank-correlated under `Packages`; components in different bundles are not |
| **G4** | regulatory components are present in 100% of vehicles in every scenario |

---

## 8. The scenario weights, had it been built

Driver F's weights came from a judgement recorded in `10_MOTOR_MODEL_DESIGN.md`.
There is no equivalent evidence here. Equal thirds would have been the proposal,
on the same reasoning as the Driver B bands: the three are scenarios, not a
fitted distribution, and equal weight asserts nothing.

---

## 9. MEASURED: it does not matter. Do not build it.

Before building, the question was put directly — *does the bundling assumption
change any answer, or is it lost inside a band that is already wide?*

Measured on the ADAS sensor total, 60,000 draws, all three assumptions applied to
the real presence matrix and the real per-component counts. **Band width as a
percentage of its own mean:**

| | every option separately | sold in packages | one spec for all |
|---|---|---|---|
| AB 2030 | 111% | 116% | 120% |
| AB 2040 | 97% | 104% | 108% |
| CD 2030 | 90% | 97% | 102% |
| CD 2040 | 50% | 56% | 64% |
| EF 2030 | 46% | 51% | 63% |
| EF 2040 | 26% | 29% | 29% |

**The whole span of the assumption is 3–17 percentage points, on bands that are
already 26–120% wide.** The largest effect anywhere is EF 2030, 46% → 63%. Both
of those numbers support exactly the same statement: this is not known.

On the **total per vehicle** it is invisible. `12_JOINT_MC_DESIGN.md` §4 measured
Sensors at ~0.0% of total variance, against Wiring 58.5% and Motors 42.8%.

### Decision

**Not built.** It is real work, it needs a weight nobody can source, and it
changes no conclusion. Building it would add apparent sophistication and no
information.

### What is done instead

The assumption is **stated**, not modelled. In `02_MODEL_STATUS.md` and
`04_SENSOR_MODEL_DESIGN.md`:

> Optional ADAS components are drawn independently of one another. Real cars are
> sold in trim levels and packages, so components that in reality arrive
> together — surround cameras with the parking ECU, corner radars with the
> domain controller — are here allowed to arrive separately. This makes the ADAS
> band **narrower than reality by 3–17 percentage points**, measured against the
> fully-bundled alternative (`13_OPTION_BUNDLING_DESIGN.md` §9). It does not
> affect the mean, and it is not visible in the total per vehicle.

That sentence is worth more than the model would have been: it is honest, it is
quantified, and a reader can act on it.

### If it is ever reopened

Two things would change the verdict, and only these:

1. **Sensor composition stops being frozen at 2025.** Sensors carry ~0% of total
   variance largely because their composition uncertainty is excluded by
   decision. Include it and sensors start to matter, and so does this.
2. **Evidence appears for the actual package mix.** A real distribution replaces
   a scenario span, and the question becomes measurement rather than judgement.
