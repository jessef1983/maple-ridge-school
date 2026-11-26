# Sap arch: dimensions and airflow check (2026-11-11)

Use this sheet to double-check the arch rebuild numbers. Every figure is tagged by where it comes from:

- **M**: measured on site (10-30 notes, 11-03 field notes, or 11-09/10 front measurements)
- **D**: a design value in the rebuild plan (`make_arch_scr.py`, `material-list-2026-11-10.md`)
- **A**: assumed and not yet measured. Check these first.

Stations are measured in inches back from the inside of the firebox front. Heights are inches off the floor unless the text says "below rim".

---

## 1. Shell and rim

| Item | Value | Src |
|---|---|---|
| Rim (pan rail) height off floor | 32½ | M |
| Inside rim opening | 34¼ wide (the 10-30 notes say 34½) × 113¾ long | M |
| Shell outside, front | 40 wide at the top, 34 at the bottom, 31¾ tall | M |
| Shell inside width at fin height, chimney end | 38½ | M |
| Shell inside width at fin height, just past the finish-pan brace | "slightly under 38½" | M (not exact) |
| Rim construction | ~3" angle cut back; shell sits ~2½" outboard of the rim opening | M |
| Brace under the finish pan | at rim level, station **37 assumed** | A |

## 2. Pans ("boiler")

| Item | Value | Src |
|---|---|---|
| Pan width overall | 36 | M |
| Finish pan | stations 1–37 (36 long), flat bottom, no fins | M |
| Flue pan | stations 37–97 (60 long), fins **7" deep (assumed)** | M / **A** depth |
| Filter pan | stations 97–113 (16 long), fins **4" deep (assumed)** | M / **A** depth |
| Flue fin span, outside to outside | 30¾ | M |
| Flue fins | 16 fins, ~0.9 thick, ~1" gaps | M (approx.) |
| Filter fin span, count, thickness | **not measured**; the calcs below assume the same as the flue pan | **A** |
| Pan depth | 8 (drawing only) | A |
| Pan bottom area | 36 × 112 ≈ **28 sq ft** | calc |
| Flue fin surface | 16 fins × 2 sides × 7 × 60 ≈ 13,400 sq in ≈ **93 sq ft** | calc |

## 3. Firebox and grates

| Item | Value | Src |
|---|---|---|
| Firebox depth | 36 (stations 0–36) | M |
| Firebox inside width at base | 29 (fiberboard sides) | M |
| Grate height | 7 off floor, 25½ below rim | M |
| Firebox height, grate to rim | 25½ | M |
| Firebox gas cross-section above the grates | 29 × 25½ ≈ **740 sq in** (6.8 × stack) | calc |
| Grate bars | 10 × 2×2×¼ angle, 27¾ long (new bars 27½), 3½ OC, point down / V up, fill with ash | M / D |
| Grate area, gross | 29 × 36 ≈ 1,044 sq in ≈ **7.25 sq ft** | calc |
| Grate air gaps | With the angle point down (legs at 45°) the top is ~2.83 wide, so each gap is ~⅝" → 9 × 0.67 × 27¾ ≈ **167 sq in** (1.5 × stack). **Measure the actual gap between bars** | calc from **A** orientation |
| Ash pit depth, floor to grate | 7 (keep ≥ 7) | M / D |
| Ash pit floor | firebrick set into the paver line so the top stays at the old floor; front course cut to a wedge up to the sill top | D |
| Center wall | flat course + course on edge = 7 tall | D |
| Back of firebox | vertical to grate height | M |

## 4. Front: fire door and damper

| Item | Value | Src |
|---|---|---|
| Fire door opening | 27½ W × 20½ H = **564 sq in** | M |
| Door opening bottom / top | 8½ / 29 off floor | M |
| Cross brace under the door | top at 8½, **2" deep (assumed)** → bottom at 6½; stays, slightly bent | M / **A** depth |
| Door liner | 1" rigid board + floating 3/16 plate, 28 × 21, on slotted 304 studs | D |
| Door gasket | ¾ graphite rope in the door lip | D |
| New sill (louver stop) | 1×1×¼ angle × 34 at the floor, top at 1" | D |
| Ash pit front opening | brace bottom (6½) to sill top (1) = **5½ high × ~29 wide (width assumed) ≈ 160 sq in** | calc / **A** width |
| Louver | 3/16 plate ~31 × 6½: covers the opening plus ½" overlap top and bottom; hinged at the top on 2 barrel hinges (⅝ pin); quadrant arm on the left | D |

### Louver free area vs swing

Model: a top-hinged flap, L = 6½, opening 29 wide. Free area = bottom slot (29 × 2L·sin(θ/2)) + two side triangles (L²·sin θ). It's capped at the 160 sq in opening.

| Swing | Free area (sq in) | × stack (108) |
|---|---|---|
| 10° | 40 | 0.4 |
| 15° | 60 | 0.55 |
| 22½° | 90 | 0.8 |
| 30° | 119 | 1.1 |
| 45° and up | 160 (opening limits) | 1.5 |

Suggested notches on the quadrant arm: **closed, ~10° (¼), ~20° (½), 45° (full).** Full open is reached at about 45°, so the arm doesn't need to swing any further.

Primary-air path in series: louver (≤160) → grate gaps (~167, **measure**) → fire. The grate gaps are about the same size as the opening, so they won't throttle much.

## 5. Gas path under the pans

### Old floor (existing)

| Point | Height | Below rim | Src |
|---|---|---|---|
| Firebox back, top of vertical | station 36½, 7 | 25½ | M |
| Top of the old steep ramp | station 45½, **13¾** | **18¾** | D (derived) |
| Old floor at 59 / 87.75 / 113 | 15½ / 19¼ / 22½ | 17 / 13¼ / 10 | D (derived) |
| Steep ramp angle | ≈ **37°** (the "45°" was an estimate) | | calc |
| Long-angle floor slope, 45½ to rear | 1.57"/ft | | calc from braces |

> **Check this:** the 10-30 notes read the ramp top as **21 below rim**. The drawing uses **18¾**, from
> "floor = brace tops − 2" (the 2×2 braces stand on the long angles). The slope of the old floor
> comes from the two brace tops (15 below rim at 59, 11¼ at 87.75). If the 21 reading was to the
> floor surface, every old-floor number here is about 2" low.

### Existing cross braces

| Station | Top, below rim | Src |
|---|---|---|
| 59 | 15 | M |
| 87.75 | 11¼ | M |

### New floor (brick top) and gas area at each station

Assumptions for the area columns:

- Lined channel width under the fins is **31¾**: fin span + ½" each side, which is how the side lining was sized.
- Between-fin open area = (30¾ − 16 × 0.9) × fin depth + the two ½" side gaps × fin depth. That gives **121 sq in** for the flue fins (7") and **69 sq in** for the filter fins (4", assumed same fins).
- Stack = 11.75" ID stub = **108 sq in**.

| Station | Brick top below rim | Gap brick → fin | Under-fin area | + between fins | Total | × stack |
|---|---|---|---|---|---|---|
| 48.6 (new brace / ramp break) | 12⅛ | 5⅛ | 161 | 121 | 283 | **2.6** |
| 59 | 11⅛ | 4⅛ | 130 | 121 | 251 | 2.3 |
| 70 (Section B) | 10 | 3 | 97 | 121 | 218 | 2.0 |
| 87.75 | 8⅜ | 1⅜ | 44 | 121 | 165 | 1.5 |
| 97, end of flue fins | 7½ | **½ (minimum)** | 16 | 121 | 137 | **1.27** |
| 97, start of filter fins | 7½ | 3½ | 111 | 69 | 181 | 1.7 |
| 105 | 6¾ | 2¾ | 87 | 69 | 156 | 1.4 |
| 113 (rear) | 6 | 2 | 63 | 69 | 132 | **1.22** |
| Filter outlet into hood | 32 × 3½ | | | | 112 | 1.04 |
| Stack (11.75 stub) | | | | | 108 | 1.00 |

- The floor is one straight slope from 48.6 to 113: **1.14"/ft**, set by the bars sitting on the 87.75 brace and the ½" minimum at 97.
- Ramp: the old 37° ramp continues from 45½ up to the new brace at 48.6, then the bars take over (single break).
- Taper: 2.6 × stack at the front down to about 1.25 × at the end of the flue fins, which fits the "2.6 → 1.3–1.4" target in the 11-05 plan. The narrowest point is the **½" at station 97**, and it rests entirely on the 7" fin depth assumption.
- **If the flue fins hang deeper than 7", the gap at 97 is gone.** Measure with the pan seated before Dean welds the bars (material list § 1).

### Steel heights (as built)

| Station | Bar top below rim | Support |
|---|---|---|
| 48.6 | ≈14⅝ | new 2×2×¼ brace on the old floor + ≈1⅜ strip |
| 59 | ≈13⅝ | existing brace + ≈1 flat extension |
| 87.75 | ≈10⅞ | existing brace, bars sit on top as is |
| 97 | ≈10 | no support (25¼ span, 2×⅜ bar) |
| 113 | ≈8½ | new 1×1×¼ angle in the back bottom corner, ≈⅛ shim |

Bars: 5 × 2×⅜ flat at 9 1/16 OC, ≈64½ long. Brick: 2½ full firebrick crosswise on the bars. Fill under the bars: 1:4 Portland–perlite with fiber, ≈2½ ft³.

## 6. Chimney

| Item | Value | Src |
|---|---|---|
| Pipe | 4 × Selkirk Metalbestos Ultra-Temp 12UT-36 (12" ID, 113 sq in), 12 ft total, insulated, 2" clearance | M |
| Stub on the hood | 11¾ ID single wall, **108 sq in** (the controlling area) | M |
| Hood top / stack base | 75 above rim (107½ off floor) | M |
| Stack top | 251½ off floor | M |
| Effective draft height, grate to top | 251½ − 7 = 244½ = **20.4 ft** | calc |
| Clearances to confirm | 18" stub to timber and sap line; support not on the hood | open |

## 7. Draft and capacity (rough check)

### Draft (theoretical, no flow)

D (in. w.c.) = 7.64 × H × (1/T_out − 1/T_gas), with H = 20.4 ft and temperatures in °R. Outside air is taken at 30°F.

| Average gas temp in the hot column | Draft |
|---|---|
| 400°F | 0.14 in. w.c. |
| 600°F | 0.17 |
| 800°F | 0.19 |
| 1000°F | 0.21 |

### Flow the stack can pass

Q = C × A × √(2gH(T_gas − T_out)/T_gas), with A = 108 sq in.

C is a lumped loss coefficient for the louver, grates, fire bed, fins and stack together. **It is a guess (0.4–0.6).**

Conversion to boil rate, all assumptions:

- 20% moisture wood, ≈6,880 BTU/lb
- 100% excess air, ≈10.6 lb flue gas per lb wood
- 50% of the fuel heat into the sap
- 9,800 BTU per gallon of sap evaporated

| Gas temp | C | Stack velocity | Hot flow | Wood | Boil rate |
|---|---|---|---|---|---|
| 600°F | 0.4 | 10.6 ft/s | 480 acfm | ~100 lb/h | ~35 GPH |
| 600°F | 0.6 | 15.9 ft/s | 720 acfm | ~150 lb/h | ~55 GPH |
| 800°F | 0.6 | 17.0 ft/s | 770 acfm | ~140 lb/h | ~50 GPH |

**Read this as a flag, not a verdict.** The 10-30 notes' **80–125 GPH** was an estimate. This crude draft calc puts a 108 sq in stack nearer **35–60 GPH**. That would make the stub/stack area the capacity limit, not the arch.

Things that move the answer:

- Less excess air: a sealed arch with the louver controlling the air means more wood per pound of gas, about +25% at 50% excess.
- Real loss coefficients.
- Actual stack temperatures.

**Settle it at the test fire:**

- Time a measured drop in the float box, which gives GPH directly.
- Log the stack thermometer.
- Note the louver notch.

If boil rate tops out low with the louver full open and the fire bright, the stack is the limit. A larger stub or more height is then the next lever, not more air.

## 8. Open measurements that change these numbers

1. **Fin depths with the pan seated:** flue (7 assumed) and filter (4 assumed). This controls the ½" at 97.
2. **Filter pan fins:** span, count, thickness.
3. **Grate air gap** between bars, and the bar orientation.
4. **Ash pit front opening width**, and the cross-brace depth (2 assumed).
5. **Ramp top height:** 21 below rim (10-30) vs 18¾ (drawing), to the floor surface.
6. **Shell width at fin height** at 59, 88 and 97.
7. **Station of the brace under the finish pan.**
8. At the test fire: GPH, stack temperature and louver notch.

Sources: `docs/session-notes/2026-10-30.md`, `sap-house/arch/2026-11-03-field-notes.md`,
`sap-house/arch/material-list-2026-11-10.md`, geometry computed from `sap-house/arch/make_arch_scr.py`.
