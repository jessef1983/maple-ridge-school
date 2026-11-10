"""Generate an ARES Commander .scr for the sap arch rebuild (school-arch drawing).

Draws, on ARCH-* layers:
  - Section A: long section on the arch centerline. x = station (inches back from
    the inside of the firebox front), z = height off the floor.
  - Front elevation: arch front, fire door opening, cross brace, ash louver.
  - Section B: cross section through the back bays, looking toward the chimney.

Geometry from docs/session-notes/2026-10-30.md and sap-house/arch/2026-11-03-field-notes.md
(final plan 2026-11-05, front decisions 2026-11-09/10), plus material-list-2026-11-10.md.
Fin depths (7" flue, 4" filter, below the rim) are ASSUMED until measured with the pan seated.

Notes sit in columns beside each view with leader lines, never on the geometry.
Re-running the script first erases everything on ARCH-* layers, so it replaces an
earlier run instead of stacking on top of it.

Edit the parameters below and re-run: python make_arch_scr.py
"""
from math import atan, degrees
from pathlib import Path

# --- Existing arch (inches) -----------------------------------------------
RIM = 32.5                    # top of pan rail off the floor
RIM_L = 113.75                # inside rim length
FIREBOX_D = 36.0
GRATE_Z = 7.0
# Back of the firebox is vertical to grate height, then the existing ramp rises
# 4.5" over 9" (about 27 deg) to 21" below the rim at 45.5 (10-30 notes).
RAMP = ((36.5, GRATE_Z), (45.5, RIM - 21.0))
FLOOR_RISE = 2.125 / 12                          # existing floor slope behind the ramp
REAR_X = 115.0
old_floor = lambda x: RAMP[1][1] + (x - RAMP[1][0]) * FLOOR_RISE
ANGLES = {59.0: RIM - 15.0, 87.75: RIM - 11.25}  # existing cross angles: station -> top z
ANGLE_LEG = 2.0                                  # assumed size, for drawing only
FINISH_BRACE_X = 37.0                            # rim-level brace under the finish pan; station NOT measured
SHELL_W = 38.5                                   # inside, at fin height (chimney end)

# Pans and fins
FINISH = (1.0, 37.0)
FLUE = (37.0, 97.0)
FILTER = (97.0, 113.0)
PAN_W, PAN_DEPTH = 36.0, 8.0                     # pan depth assumed, for drawing only
FLUE_FIN, FILTER_FIN = 7.0, 4.0                  # ASSUMED depth below the rim
FIN_SPAN = 30.75

# Front
FRONT_W_TOP, FRONT_W_BOT, FRONT_H = 40.0, 34.0, 31.75
DOOR_W, DOOR_H, DOOR_BOT = 27.5, 20.5, 8.5
BRACE_H = 2.0                                    # assumed, for drawing only
LOUVER_W, LOUVER_H = 31.0, 8.0

# Grates: 2x2x1/4 angle, point down, V open up so it fills with ash
GRATE_N, GRATE_OC, GRATE_X0, GRATE_LEG = 10, 3.5, 2.5, 2.0

# --- New work ------------------------------------------------------------
BRICK, BLANKET = 2.5, 1.0
LINING = BLANKET + BRICK
BAR_T, BAR_W, BAR_OC, N_BARS = 0.375, 2.0, 9.0625, 5
MIN_GAP = 0.5
# Floor line: bars sit on top of the existing 87.75 angle, slope set by the 1/2" minimum
# gap under the flue fins at 97.
X1, X2 = 87.75, 97.0
BT1 = ANGLES[X1] + BAR_T + BRICK                 # brick top at 87.75
BT2 = RIM - FLUE_FIN - MIN_GAP                   # brick top at 97
SLOPE = (BT2 - BT1) / (X2 - X1)
brick_top = lambda x: BT1 + (x - X1) * SLOPE
bar_top = lambda x: brick_top(x) - BRICK
X0, X_END = 59.0, 113.0                          # bars run from the 59 angle to the rear
EXT_59 = bar_top(X0) - BAR_T - ANGLES[X0]        # flat-bar extension above the 59 angle
# New ramp plate: from the top of the existing ramp to the top of the 59 angle.
# Its lined face (3.5" off the plate) meets the floor brick at 59.
PLATE = (RAMP[1], (X0, ANGLES[X0]))
PM = (PLATE[1][1] - PLATE[0][1]) / (PLATE[1][0] - PLATE[0][0])
FACE_OFF = LINING * (1 + PM ** 2) ** 0.5
EM = (RAMP[1][1] - RAMP[0][1]) / (RAMP[1][0] - RAMP[0][0])
EX_OFF = LINING * (1 + EM ** 2) ** 0.5

out = []
def cmd(*parts): out.extend(str(p) for p in parts)
OX, OY = 0.0, 0.0                                # view origin offset
def pt(x, y): return f"{x + OX:.2f},{y + OY:.2f}"
def layer(name, color):
    cmd("_-LAYER", "_M", name, "_C", color, "", "")
def line(a, b): cmd("_LINE", pt(*a), pt(*b), "")
def pline(pts, closed=False): cmd("_PLINE", *[pt(*p) for p in pts], "_C" if closed else "")
def box(x1, y1, x2, y2): pline([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], True)
def text(x, y, h, s): cmd("_TEXT", pt(x, y), h, 0, s)
def dim(a, b, at): cmd("_DIMLINEAR", pt(*a), pt(*b), pt(*at))
def angle_l(x, ztop, leg=ANGLE_LEG):            # angle seen end-on, legs down and back
    pline([(x, ztop - leg), (x, ztop), (x + leg, ztop)])

TITLE_H, NOTE_H, NOTE_GAP = 2.5, 1.25, 2.6
f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")
eighth = lambda v: f(round(v * 8) / 8)

def callouts(notes, col_x, side, top):
    """Stack notes in a column at col_x with a leader to each target.
    notes: [(tx, tz, text)], placed in target-height order so leaders don't cross.
    side "R": text starts at col_x; "L": text ends at col_x."""
    layer("ARCH-NOTE", 2)
    z = top
    for tx, tz, s in sorted(notes, key=lambda n: -n[1]):
        z = min(z, tz)
        w = len(s) * NOTE_H * 0.9
        x0 = col_x if side == "R" else col_x - w
        text(x0, z, NOTE_H, s)
        end = (col_x - 1, z + NOTE_H / 2) if side == "R" else (col_x + 1, z + NOTE_H / 2)
        line((tx, tz), end)
        z -= NOTE_GAP

cmd("_UNDO", "_BE", "_OSMODE", 0)
cmd("""(if (setq ss (ssget "_X" '((8 . "ARCH-*")))) (command "_.ERASE" ss ""))""")
cmd("_DIMSCALE", 4, "_DIMLUNIT", 4, "_DIMDEC", 3, "_DIMTIH", 0, "_DIMTOH", 0)

# ===== SECTION A: long section ================================================
OX, OY = 0.0, 0.0
layer("ARCH-EXIST", 8)
pline([(0, 0), (FIREBOX_D, 0), (FIREBOX_D, GRATE_Z), RAMP[0], RAMP[1],
       (REAR_X, old_floor(REAR_X))])                                      # old floor + ramp
line((0, RIM), (RIM_L, RIM))                                              # rim line
layer("ARCH-EXIST-BRACE", 6)                                              # existing cross braces
for x, zt in ANGLES.items():
    angle_l(x, zt)
angle_l(FINISH_BRACE_X, RIM - 0.5)                                        # under the finish pan, location assumed
layer("ARCH-PAN", 5)
box(FINISH[0], RIM, FILTER[1], RIM + PAN_DEPTH)
for (x0, x1), d in ((FLUE, FLUE_FIN), (FILTER, FILTER_FIN)):
    box(x0, RIM - d, x1, RIM)
    for k in range(1, int(x1 - x0) // 4):
        line((x0 + 4 * k, RIM - d), (x0 + 4 * k, RIM))                   # fin hatch
layer("ARCH-FRONT", 7)
line((0, 0), (0, DOOR_BOT - BRACE_H))
box(-1, DOOR_BOT - BRACE_H, 0, DOOR_BOT)                                  # cross brace
line((0, DOOR_BOT + DOOR_H), (0, RIM))
line((-1.5, DOOR_BOT), (-1.5, DOOR_BOT + DOOR_H))                         # fire door (closed)
line((-0.75, DOOR_BOT - BRACE_H), (-0.75, 0.5))                           # louver (closed)
layer("ARCH-GRATE", 1)
for k in range(GRATE_N):
    x = GRATE_X0 + GRATE_OC * k
    pline([(x - 1, GRATE_Z), (x, GRATE_Z - 1.4), (x + 1, GRATE_Z)])       # point down, V up
layer("ARCH-NEW-STEEL", 30)
pline(list(PLATE))                                                        # new ramp plate
box(X0 - BAR_T, ANGLES[X0], X0, ANGLES[X0] + EXT_59)                      # 59 extension
pline([(X0, bar_top(X0)), (X_END, bar_top(X_END))])                       # bars, top
pline([(X0, bar_top(X0) - BAR_T), (X_END, bar_top(X_END) - BAR_T)])       # bars, bottom
layer("ARCH-BRICK", 1)
pline([(X0, brick_top(X0)), (X_END, brick_top(X_END))])                   # floor brick top
line((X_END, brick_top(X_END)), (X_END, bar_top(X_END)))
pline([(FIREBOX_D - LINING, 0), (FIREBOX_D - LINING, GRATE_Z + EX_OFF - LINING * EM),
       (RAMP[1][0], RAMP[1][1] + EX_OFF),
       (X0, PLATE[1][1] + FACE_OFF)])                                     # lined firebox back + ramp face
layer("ARCH-FILL", 9)
line((X0 + 1, bar_top(X0 + 1) - BAR_T - 0.1), (X_END - 6, old_floor(X_END - 6)))  # perlite fill (schematic)
# gap marks
layer("ARCH-NOTE", 2)
gaps = []
for x in (X0, 87.75, 97.0, X_END):
    fin = FLUE_FIN if x < 97 else FILTER_FIN
    g = RIM - fin - brick_top(x)
    line((x, brick_top(x)), (x, RIM - fin))
    gaps.append((x, brick_top(x) + g / 2, f"STA {f(x)}: {eighth(g)}\" BRICK TO FIN"))
g97 = RIM - FILTER_FIN - brick_top(97.0)
gaps.append((97.5, brick_top(97.0) + g97 - 0.5, f"STA 97: {eighth(g97)}\" UNDER FILTER FINS"))
text(0, RIM + PAN_DEPTH + 12, TITLE_H, "SECTION A - LONG SECTION")
text(0, RIM + PAN_DEPTH + 8.5, NOTE_H, f"FIN DEPTHS ASSUMED {f(FLUE_FIN)}\" FLUE / {f(FILTER_FIN)}\" FILTER BELOW RIM - MEASURE WITH PAN SEATED")
callouts(gaps + [
    ((FILTER[0] + FILTER[1]) / 2, RIM + PAN_DEPTH / 2, "FILTER PAN"),
    (X_END - 4, bar_top(X_END - 4), "BARS LAND ON OLD FLOOR - SHIM"),
    (87.75 + 1, ANGLES[87.75], "EXIST. BRACE 87.75 (TOP 11.25 BELOW RIM) - BARS ON TOP, AS IS"),
    (100, bar_top(100) - BAR_T / 2, f"2x3/8 FLAT, {N_BARS} @ {f(BAR_OC)} OC, ~{f(round(X_END - X0 + 1))}\" ONE PIECE"),
], col_x=125, side="R", top=RIM + PAN_DEPTH)
callouts([
    ((FLUE[0] + FLUE[1]) / 2, RIM + PAN_DEPTH / 2, "FLUE PAN"),
    ((FINISH[0] + FINISH[1]) / 2, RIM + PAN_DEPTH / 2, "FINISH PAN"),
    (X0 - BAR_T / 2, ANGLES[X0] + EXT_59 / 2, f"EXIST. BRACE 59 (TOP 15 BELOW RIM) + {eighth(EXT_59)}\" FLAT = TOP OF RAMP"),
    (FINISH_BRACE_X, RIM - 1.5, f"EXIST. BRACE UNDER FINISH PAN AT STA {f(FINISH_BRACE_X)} - LOCATION NOT MEASURED"),
    (-0.5, DOOR_BOT - BRACE_H / 2, "EXIST. FRONT CROSS BRACE - STAYS"),
    (52, PLATE[0][1] + (52 - PLATE[0][0]) * PM, f"NEW 3/16 RAMP PLATE ~{f(round(degrees(atan(PM))))} DEG, LINED 3.5\""),
    (41, RAMP[0][1] + (41 - RAMP[0][0]) * EM, f"EXIST. RAMP ~{f(round(degrees(atan(EM))))} DEG"),
    (GRATE_X0 + GRATE_OC * 4, GRATE_Z - 0.7, "GRATES 2x2x1/4, POINT DOWN, FILL WITH ASH"),
    (FIREBOX_D, GRATE_Z / 2, "FIREBOX BACK VERTICAL TO GRATE HT"),
], col_x=-28, side="L", top=RIM + PAN_DEPTH)
dim((0, RIM), (0, 0), (-6, RIM / 2))
dim((0, -6), (FIREBOX_D, -6), (FIREBOX_D / 2, -8))
dim((FIREBOX_D, -6), (X0, -6), ((FIREBOX_D + X0) / 2, -8))
dim((X0, -6), (87.75, -6), ((X0 + 87.75) / 2, -8))
dim((87.75, -6), (X_END, -6), ((87.75 + X_END) / 2, -8))

# ===== FRONT ELEVATION =========================================================
OX, OY = -160.0, 0.0
layer("ARCH-FRONT", 7)
pline([(-FRONT_W_BOT / 2, 0), (FRONT_W_BOT / 2, 0),
       (FRONT_W_TOP / 2, FRONT_H), (-FRONT_W_TOP / 2, FRONT_H)], True)
box(-DOOR_W / 2, DOOR_BOT, DOOR_W / 2, DOOR_BOT + DOOR_H)                 # door opening
box(-FRONT_W_BOT / 2, DOOR_BOT - BRACE_H, FRONT_W_BOT / 2, DOOR_BOT)      # cross brace
layer("ARCH-NEW-STEEL", 30)
lv_top = DOOR_BOT - BRACE_H
box(-LOUVER_W / 2, lv_top - LOUVER_H, LOUVER_W / 2, lv_top)               # louver (overlaps pit front)
for hx in (-LOUVER_W / 2 + 4, LOUVER_W / 2 - 8):
    box(hx, lv_top - 0.5, hx + 4, lv_top + 0.5)                           # barrel hinges
pline([(LOUVER_W / 2 - 2, lv_top - LOUVER_H + 1), (LOUVER_W / 2 + 2, lv_top - 1)])  # quadrant arm
layer("ARCH-NOTE", 2)
text(-FRONT_W_TOP / 2, FRONT_H + 12, TITLE_H, "FRONT ELEVATION")
callouts([
    (0, DOOR_BOT + DOOR_H - 2, f"FIRE DOOR OPENING {f(DOOR_W)} x {f(DOOR_H)}"),
    (-FRONT_W_BOT / 2 + 1, DOOR_BOT - BRACE_H / 2, "EXIST. CROSS BRACE - STAYS"),
    (-LOUVER_W / 2 + 6, lv_top, "BARREL HINGES (2)"),
    (-LOUVER_W / 2 + 2, lv_top - LOUVER_H / 2, f"LOUVER ~{f(LOUVER_W)} x {f(LOUVER_H)}, FIELD-FIT"),
], col_x=-FRONT_W_TOP / 2 - 6, side="L", top=FRONT_H)
callouts([
    (LOUVER_W / 2 + 1, lv_top - LOUVER_H / 2, "QUADRANT ARM, AWAY FROM DOOR LATCH"),
], col_x=FRONT_W_TOP / 2 + 6, side="R", top=FRONT_H)
dim((-FRONT_W_TOP / 2, FRONT_H), (FRONT_W_TOP / 2, FRONT_H), (0, FRONT_H + 5))
dim((-FRONT_W_BOT / 2, 0), (FRONT_W_BOT / 2, 0), (0, -6))
dim((-DOOR_W / 2, DOOR_BOT + DOOR_H), (DOOR_W / 2, DOOR_BOT + DOOR_H), (0, DOOR_BOT + DOOR_H + 2.5))
dim((FRONT_W_TOP / 2, 0), (FRONT_W_TOP / 2, FRONT_H), (FRONT_W_TOP / 2 + 3, FRONT_H / 2))
dim((DOOR_W / 2, 0), (DOOR_W / 2, DOOR_BOT), (DOOR_W / 2 + 6, DOOR_BOT / 2))

# ===== SECTION B: cross section through the back bays =========================
XS = 70.0
OX, OY = 250.0, 0.0
hw = SHELL_W / 2
layer("ARCH-EXIST", 8)
pline([(-hw, old_floor(XS)), (hw, old_floor(XS))])
layer("ARCH-FRONT", 7)
pline([(-hw, 0), (-hw, RIM), (-hw - 2.5, RIM)])                            # shell + rim (schematic)
pline([(hw, 0), (hw, RIM), (hw + 2.5, RIM)])
layer("ARCH-PAN", 5)
box(-PAN_W / 2, RIM, PAN_W / 2, RIM + PAN_DEPTH)
for k in range(16):
    fx = -FIN_SPAN / 2 + k * (FIN_SPAN - 0.9) / 15
    box(fx, RIM - FLUE_FIN, fx + 0.9, RIM)
layer("ARCH-NEW-STEEL", 30)
bt = bar_top(XS)
x0 = -(N_BARS - 1) * BAR_OC / 2
for k in range(N_BARS):
    bx = x0 + k * BAR_OC
    box(bx - BAR_W / 2, bt - BAR_T, bx + BAR_W / 2, bt)
layer("ARCH-BRICK", 1)
for k in range(N_BARS - 1):
    bx = x0 + k * BAR_OC
    box(bx, bt, bx + 9.0, bt + BRICK)                                     # floor brick, crosswise
side_top = RIM - FLUE_FIN - 0.5
side_in = (SHELL_W - FIN_SPAN - 1) / 2                                     # lining allowance per side
for s in (-1, 1):
    xi = s * (hw - side_in)
    box(min(s * hw, xi), bt + BRICK, max(s * hw, xi), side_top)           # blanket + brick on edge
    box(min(xi, xi + s * BRICK), bt + BRICK, max(xi, xi + s * BRICK), side_top)
layer("ARCH-NOTE", 2)
text(-hw, RIM + PAN_DEPTH + 12, TITLE_H, f"SECTION B - BACK BAYS AT STA {f(XS)}")
text(-hw, RIM + PAN_DEPTH + 8.5, NOTE_H, "LOOKING TOWARD THE CHIMNEY")
callouts([
    (0, RIM - FLUE_FIN / 2, "FLUE PAN FINS"),
    (hw - side_in / 2, (bt + side_top) / 2, f"BRICK ON EDGE + ~7/8 BLANKET, {eighth(side_in)}\"/SIDE"),
    (x0 + BAR_OC / 2, bt + BRICK / 2, "FULL BRICK LAID CROSSWISE"),
    (x0 + BAR_OC, bt - BAR_T / 2, f"{N_BARS} BARS 2x3/8 @ {f(BAR_OC)} OC"),
    (0, old_floor(XS), "OLD FLOOR; PERLITE FILL BELOW BARS"),
], col_x=hw + 8, side="R", top=RIM + PAN_DEPTH)
dim((-hw, 2), (hw, 2), (0, -4))
dim((x0, bt), (x0 + BAR_OC, bt), (x0 + BAR_OC / 2, bt - 3))

cmd("_UNDO", "_E", "_ZOOM", "_Fit")            # ARES has no ZOOM Extents; Fit is the equivalent

dest = Path(__file__).with_name("school-arch.scr")
dest.write_text("\n".join(out) + "\n", encoding="ascii")
print(dest)
print(f"floor line: brick top {BT1:.2f} at 87.75, {BT2:.2f} at 97, slope {SLOPE * 12:.2f}\"/ft")
print(f"ramp plate {degrees(atan(PM)):.1f} deg; lined face at 59 {PLATE[1][1] + FACE_OFF:.2f} vs floor brick {brick_top(X0):.2f}")
print(f"59 extension {EXT_59:.2f}\", bar length {X_END - X0:.1f}\"")
for x in (X0, 87.75, 97, 113):
    print(f"sta {x:6.2f}: bar top {RIM - bar_top(x):.2f} below rim, old floor {RIM - old_floor(x):.2f} below rim")
