"""Generate an ARES Commander .scr for the sap arch rebuild (school-arch drawing).

Draws, on ARCH-* layers:
  - Section A: long section on the arch centerline. x = station (inches back from
    the inside of the firebox front), z = height off the floor.
  - Front elevation: arch front, fire door opening, cross brace, ash louver.
  - Section B: cross section through the back bays, looking toward the chimney.

Geometry from docs/session-notes/2026-10-30.md and sap-house/arch/2026-11-03-field-notes.md
(final plan 2026-11-05, front decisions 2026-11-09/10), plus material-list-2026-11-10.md.
Fin depths (7" flue, 4" filter, below the rim) are ASSUMED until measured with the pan seated.

Re-running the script first erases everything on ARCH-* layers, so it replaces an
earlier run instead of stacking on top of it.

Edit the parameters below and re-run: python make_arch_scr.py
"""
from pathlib import Path

# --- Existing arch (inches) -----------------------------------------------
RIM = 32.5                    # top of pan rail off the floor
RIM_L = 113.75                # inside rim length
FIREBOX_D = 36.0
FIREBOX_W = 29.0
GRATE_Z = 7.0
RAMP = ((36.5, 0.0), (45.5, RIM - 21.0))        # existing steep ramp behind the firebox
FLOOR_RISE = 2.125 / 12                          # existing floor slope behind the ramp
REAR_X = 115.0
old_floor = lambda x: RAMP[1][1] + (x - RAMP[1][0]) * FLOOR_RISE
ANGLES = {59.0: RIM - 15.0, 87.75: RIM - 11.25}  # existing cross angles: station -> top z
ANGLE_LEG = 2.0                                  # assumed size, for drawing only
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

# --- New work ------------------------------------------------------------
BRICK, BLANKET = 2.5, 1.0
BAR_T, BAR_W, BAR_OC, N_BARS = 0.375, 2.0, 9.0625, 5
MIN_GAP = 0.5
# Floor line: bars sit on top of the existing 87.75 angle, slope set by the 1/2" minimum
# gap under the flue fins at 97. Brick top z as a function of station.
X1, X2 = 87.75, 97.0
BT1 = ANGLES[X1] + BAR_T + BRICK                 # brick top at 87.75
BT2 = RIM - FLUE_FIN - MIN_GAP                   # brick top at 97
SLOPE = (BT2 - BT1) / (X2 - X1)
brick_top = lambda x: BT1 + (x - X1) * SLOPE
bar_top = lambda x: brick_top(x) - BRICK
# 45 deg ramp: continue the existing ramp plate at 45 deg from its top; the finished
# brick face sits 3.5" (blanket + brick) off the plate.
LINING = BLANKET + BRICK
RAMP_OFF = LINING * 2 ** 0.5                     # vertical offset of the finished face at 45 deg
ramp_face = lambda x: RAMP[1][1] + (x - RAMP[1][0]) + RAMP_OFF
# where the 45 deg finished face meets the floor line
RX = (BT1 - X1 * SLOPE - RAMP[1][1] + RAMP[1][0] - RAMP_OFF) / (1 - SLOPE)
RZ = brick_top(RX)
X_END = 113.0
EXT_59 = bar_top(59.0) - BAR_T - ANGLES[59.0]    # flat-bar extension above the 59 angle

out = []
def cmd(*parts): out.extend(str(p) for p in parts)
OX, OY = 0.0, 0.0                                # view origin offset
def pt(x, y): return f"{x + OX:.2f},{y + OY:.2f}"
def layer(name, color, ltype=None):              # ltype kept for intent; existing work is gray
    cmd("_-LAYER", "_M", name, "_C", color, "", "")
def line(a, b): cmd("_LINE", pt(*a), pt(*b), "")
def pline(pts, closed=False): cmd("_PLINE", *[pt(*p) for p in pts], "_C" if closed else "")
def box(x1, y1, x2, y2): pline([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], True)
def text(x, y, h, s): cmd("_TEXT", pt(x, y), h, 0, s)
def dim(a, b, at): cmd("_DIMLINEAR", pt(*a), pt(*b), pt(*at))
def angle_l(x, ztop, leg=ANGLE_LEG):            # angle seen end-on, legs down and back
    pline([(x, ztop - leg), (x, ztop), (x + leg, ztop)])

TITLE_H, NOTE_H = 3.0, 1.5
f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")

cmd("_UNDO", "_BE", "_OSMODE", 0)
cmd("""(if (setq ss (ssget "_X" '((8 . "ARCH-*")))) (command "_.ERASE" ss ""))""")
cmd("_DIMSCALE", 4, "_DIMLUNIT", 4, "_DIMDEC", 3, "_DIMTIH", 0, "_DIMTOH", 0)

# ===== SECTION A: long section ================================================
OX, OY = 0.0, 0.0
layer("ARCH-EXIST", 8, "DASHED")
pline([(0, 0), RAMP[0], RAMP[1], (REAR_X, old_floor(REAR_X))])          # old floor
for x, zt in ANGLES.items():
    angle_l(x, zt)
line((0, RIM), (RIM_L, RIM))                                              # rim line
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
for k in range(10):
    x = 2 + 3.5 * k
    pline([(x - 1, GRATE_Z - 1.4), (x, GRATE_Z), (x + 1, GRATE_Z - 1.4)])  # V-up angle
layer("ARCH-NEW-STEEL", 30)
pline([RAMP[1], (RX - 1.5, RAMP[1][1] + RX - 1.5 - RAMP[1][0])])          # 45 deg ramp plate
angle_l(RX - ANGLE_LEG, bar_top(RX) - BAR_T)                              # cross member at top of ramp
box(59.0 - BAR_T, ANGLES[59.0], 59.0, ANGLES[59.0] + EXT_59)              # 59 extension
pline([(RX - ANGLE_LEG, bar_top(RX - ANGLE_LEG)), (X_END, bar_top(X_END))])   # bar top
pline([(RX - ANGLE_LEG, bar_top(RX - ANGLE_LEG) - BAR_T), (X_END, bar_top(X_END) - BAR_T)])
layer("ARCH-BRICK", 1)
pline([(RX - ANGLE_LEG, brick_top(RX - ANGLE_LEG)), (X_END, brick_top(X_END))])
line((RX - ANGLE_LEG, brick_top(RX - ANGLE_LEG)), (RX - ANGLE_LEG, bar_top(RX - ANGLE_LEG)))
line((X_END, brick_top(X_END)), (X_END, bar_top(X_END)))
pline([(RAMP[1][0], ramp_face(RAMP[1][0])), (RX, RZ)])                    # 45 deg brick face
pline([(RAMP[0][0] - LINING, 0), (RAMP[1][0] - LINING * 0.6, ramp_face(RAMP[1][0]))])  # lined old ramp
layer("ARCH-FILL", 9, "DASHED")
line((RX, bar_top(RX) - BAR_T - 0.1), (X_END - 6, old_floor(X_END - 6)))  # perlite fill (schematic)
layer("ARCH-NOTE", 2)
text(0, RIM + PAN_DEPTH + 10, TITLE_H, "SECTION A - LONG SECTION ON CENTERLINE (LOOKING AT RIGHT SIDE)")
text(0, RIM + PAN_DEPTH + 6, NOTE_H,
     f"FIN DEPTHS ASSUMED {f(FLUE_FIN)}\" FLUE / {f(FILTER_FIN)}\" FILTER BELOW RIM - MEASURE WITH PAN SEATED")
for x in (RX, 59.0, 87.75, 97.0, X_END):
    gap = RIM - (FLUE_FIN if x < 97 else FILTER_FIN) - brick_top(x)
    line((x, brick_top(x)), (x, brick_top(x) + gap))
    text(x + 0.5, brick_top(x) + gap / 2 - 0.75, NOTE_H, f"{f(round(gap * 8) / 8)}\" GAP")
    text(x - 2, -4, NOTE_H, f"STA {f(round(x * 4) / 4)}")
text(97.5, brick_top(97) + 4.5, NOTE_H, f"{f(RIM - FILTER_FIN - brick_top(97))}\" UNDER FILTER FINS")
text(RX + 2, bar_top(RX) - 6, NOTE_H, f"2x3/8 FLAT BARS, {N_BARS} @ {f(BAR_OC)} OC, ONE PIECE ~{f(round(X_END - RX + ANGLE_LEG))}\"")
text(60, ANGLES[59.0] - 4, NOTE_H, f"59 ANGLE + {f(round(EXT_59 * 8) / 8)}\" FLAT EXTENSION")
text(88.5, ANGLES[87.75] - 4, NOTE_H, "87.75 ANGLE AS IS - BARS ON TOP")
text(RX - 14, RZ + 3, NOTE_H, f"45 DEG RAMP TO STA {f(round(RX))}")
text(2, GRATE_Z + 2, NOTE_H, "GRATES 10 x 2x2x1/4 V-UP @ 3.5")
text(-14, DOOR_BOT + DOOR_H / 2, NOTE_H, "FIRE DOOR")
text(-14, 3, NOTE_H, "LOUVER")
text(40, RIM + PAN_DEPTH / 2, NOTE_H, "FLUE PAN")
text(5, RIM + PAN_DEPTH / 2, NOTE_H, "FINISH PAN")
text(98, RIM + PAN_DEPTH / 2, NOTE_H, "FILTER")
dim((0, RIM), (0, 0), (-20, RIM / 2))
dim((0, DOOR_BOT), (0, DOOR_BOT + DOOR_H), (-8, DOOR_BOT + DOOR_H / 2))
dim((0, -8), (FIREBOX_D, -8), (FIREBOX_D / 2, -10))

# ===== FRONT ELEVATION =========================================================
OX, OY = -90.0, 0.0
cx = 0.0
layer("ARCH-FRONT", 7)
pline([(cx - FRONT_W_BOT / 2, 0), (cx + FRONT_W_BOT / 2, 0),
       (cx + FRONT_W_TOP / 2, FRONT_H), (cx - FRONT_W_TOP / 2, FRONT_H)], True)
box(cx - DOOR_W / 2, DOOR_BOT, cx + DOOR_W / 2, DOOR_BOT + DOOR_H)        # door opening
box(cx - FRONT_W_BOT / 2, DOOR_BOT - BRACE_H, cx + FRONT_W_BOT / 2, DOOR_BOT)  # cross brace
layer("ARCH-NEW-STEEL", 30)
box(cx - LOUVER_W / 2, DOOR_BOT - BRACE_H - LOUVER_H + 1.5, cx + LOUVER_W / 2, DOOR_BOT - BRACE_H + 1.5)
for hx in (cx - LOUVER_W / 2 + 4, cx + LOUVER_W / 2 - 8):
    box(hx, DOOR_BOT - BRACE_H, hx + 4, DOOR_BOT - BRACE_H + 1)            # barrel hinges
pline([(cx + LOUVER_W / 2 - 1, 1.5), (cx + LOUVER_W / 2 + 3, 8)])         # quadrant arm (schematic)
layer("ARCH-NOTE", 2)
text(cx - FRONT_W_TOP / 2, FRONT_H + 10, TITLE_H, "FRONT ELEVATION")
text(cx - 10, DOOR_BOT + DOOR_H / 2, NOTE_H, f"FIRE DOOR OPENING {f(DOOR_W)} x {f(DOOR_H)}")
text(cx - 14, DOOR_BOT - 1.5, NOTE_H, "EXIST. CROSS BRACE (STAYS)")
text(cx - 14, 2.5, NOTE_H, f"LOUVER ~{f(LOUVER_W)} x {f(LOUVER_H)}, BARREL HINGES AT TOP")
text(cx + LOUVER_W / 2 + 4, 6, NOTE_H, "QUADRANT ARM")
dim((cx - FRONT_W_TOP / 2, FRONT_H), (cx + FRONT_W_TOP / 2, FRONT_H), (cx, FRONT_H + 5))
dim((cx - FRONT_W_BOT / 2, 0), (cx + FRONT_W_BOT / 2, 0), (cx, -5))
dim((cx - DOOR_W / 2, DOOR_BOT + DOOR_H), (cx + DOOR_W / 2, DOOR_BOT + DOOR_H), (cx, DOOR_BOT + DOOR_H + 2.5))
dim((cx + FRONT_W_BOT / 2, 0), (cx + FRONT_W_TOP / 2, FRONT_H), (cx + FRONT_W_TOP / 2 + 6, FRONT_H / 2))
dim((cx - DOOR_W / 2, 0), (cx - DOOR_W / 2, DOOR_BOT), (cx - DOOR_W / 2 - 4, DOOR_BOT / 2))

# ===== SECTION B: cross section through the back bays =========================
XS = 70.0
OX, OY = 150.0, 0.0
hw = SHELL_W / 2
layer("ARCH-EXIST", 8, "DASHED")
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
    xo = s * hw
    xi = s * (hw - side_in)
    box(min(xo, xi), bt + BRICK, max(xo, xi), side_top)                   # blanket + brick on edge
    box(min(xi, xi + s * BRICK), bt + BRICK, max(xi, xi + s * BRICK), side_top)
layer("ARCH-NOTE", 2)
text(-hw, RIM + PAN_DEPTH + 10, TITLE_H, f"SECTION B - BACK BAYS AT STA {f(XS)}, LOOKING TO CHIMNEY")
text(-hw, bt - 5, NOTE_H, f"{N_BARS} BARS 2x3/8 @ {f(BAR_OC)} OC, BRICK CROSSWISE")
text(-hw, RIM + PAN_DEPTH + 6, NOTE_H, f"SIDES: BRICK ON EDGE + ~7/8 BLANKET ({f(side_in)}\"/SIDE AT {f(SHELL_W)} SHELL)")
dim((-hw, 2), (hw, 2), (0, -3))
dim((x0, bt), (x0 + BAR_OC, bt), (x0 + BAR_OC / 2, bt - 2.5))

cmd("_UNDO", "_E", "_ZOOM", "_E")

dest = Path(__file__).with_name("school-arch.scr")
dest.write_text("\n".join(out) + "\n", encoding="ascii")
print(dest)
print(f"floor line: brick top {BT1:.2f} at 87.75, {BT2:.2f} at 97, slope {SLOPE * 12:.2f}\"/ft")
print(f"ramp top: sta {RX:.2f}, brick top z {RZ:.2f} ({RIM - RZ:.2f} below rim)")
print(f"59 extension {EXT_59:.2f}\", bar length {X_END - RX + ANGLE_LEG:.1f}\"")
for x in (RX, 59, 87.75, 97, 113):
    print(f"sta {x:6.2f}: bar top {RIM - bar_top(x):.2f} below rim, old floor {RIM - old_floor(x):.2f} below rim")
