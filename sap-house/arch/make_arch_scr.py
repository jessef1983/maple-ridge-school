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

Also writes school-arch-sheets.html: one Letter-landscape page per view at a standard scale,
with that view's tag legend (see sheets.py). Print it to PDF with headless Chrome:
  chrome --headless=new --no-pdf-header-footer --print-to-pdf=school-arch-sheets.pdf school-arch-sheets.html

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
REAR_X = RIM_L
ANGLES = {59.0: RIM - 15.0, 87.75: RIM - 11.25}  # existing cross braces: station -> top z
# Floor behind the ramp = the long 2x2 side angles, ONE straight piece each from the top of
# the old steep ramp (45.5) to the back. The two cross braces stand on them; their measured
# tops set the slope, so they stand the same height above the long angles.
FLOOR_SLOPE = (ANGLES[87.75] - ANGLES[59.0]) / (87.75 - 59.0)
# The 2x2 braces sit on the floor, so the floor surface is 2" under their tops. That puts the
# top of the steep ramp about 2" above the 21"-below-rim reading (taken to the underside).
RAMP = (RAMP[0], (45.5, ANGLES[59.0] - 2.0 - (59.0 - 45.5) * FLOOR_SLOPE))
def old_floor(x):
    if x <= RAMP[1][0]:
        return RAMP[0][1] + (x - RAMP[0][0]) * (RAMP[1][1] - RAMP[0][1]) / (RAMP[1][0] - RAMP[0][0])
    return RAMP[1][1] + (x - RAMP[1][0]) * FLOOR_SLOPE
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
SILL_LEG = 1.0                                   # new 1x1x1/4 sill angle at floor level, louver stop
LOUVER_W = 31.0
LOUVER_H = (DOOR_BOT - BRACE_H) - SILL_LEG + 1.0 # opening plus 1/2" overlap top and bottom

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
EM = (RAMP[1][1] - RAMP[0][1]) / (RAMP[1][0] - RAMP[0][0])      # existing steep ramp slope
EX_OFF = LINING * (1 + EM ** 2) ** 0.5                            # vertical offset of its lined face
ramp_face = lambda x: RAMP[0][1] + (x - RAMP[0][0]) * EM + EX_OFF
# One break: the steep ramp continues at its own angle until its lined face meets the
# floor-brick plane; a new cross brace there starts the bars.
XB = (BT1 - X1 * SLOPE - RAMP[0][1] + RAMP[0][0] * EM - EX_OFF) / (EM - SLOPE)
X0, X_END = XB, 113.0                            # bars run from the new brace to the rear
EXT_59 = bar_top(59.0) - BAR_T - ANGLES[59.0]    # flat-bar extension above the 59 brace
# Ramp plate: continues the old ramp at its own angle from its top to the new brace.
PLATE = (RAMP[1], (XB, RAMP[1][1] + (XB - RAMP[1][0]) * EM))
PM, FACE_OFF = EM, EX_OFF
NEWB_EXT = bar_top(XB) - BAR_T - (old_floor(XB) + ANGLE_LEG)

out = []
def cmd(*parts): out.extend(str(p) for p in parts)
OX, OY = 0.0, 0.0                                # view origin offset
# Every primitive is also recorded per view, in view-local inches, for the PDF sheets.
VIEW, SHEETS, COLOR = None, {}, "#000"
ACI = {1: "#d00000", 2: "#a07800", 3: "#008a00", 5: "#0030c0", 6: "#c000c0", 7: "#000000",
       8: "#808080", 9: "#a0a0a0", 30: "#e06000"}
def begin_view(name, ox, oy, title, subtitle=""):
    global VIEW, OX, OY
    VIEW, OX, OY = name, ox, oy
    SHEETS[name] = {"title": title, "subtitle": subtitle, "items": [], "legend": []}
def rec(*item):
    if VIEW: SHEETS[VIEW]["items"].append((COLOR,) + item)
def pt(x, y): return f"{x + OX:.2f},{y + OY:.2f}"
def layer(name, color):
    global COLOR
    COLOR = ACI.get(color, "#000")
    cmd("_-LAYER", "_M", name, "_C", color, "", "")
def line(a, b): cmd("_LINE", pt(*a), pt(*b), ""); rec("pl", [a, b], False)
def pline(pts, closed=False):
    cmd("_PLINE", *[pt(*p) for p in pts], "_C" if closed else ""); rec("pl", list(pts), closed)
def box(x1, y1, x2, y2): pline([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], True)
def text(x, y, h, s, sheet=True):
    cmd("_TEXT", pt(x, y), h, 0, s)
    if sheet: rec("tx", x, y, h, s)
def dim(a, b, at): cmd("_DIMLINEAR", pt(*a), pt(*b), pt(*at)); rec("dim", a, b, at)
def angle_l(x, ztop, leg=ANGLE_LEG, t=0.25):    # angle seen end-on, legs down and back, with thickness
    pline([(x, ztop - leg), (x, ztop), (x + leg, ztop), (x + leg, ztop - t),
           (x + t, ztop - t), (x + t, ztop - leg)], True)

TITLE_H, NOTE_H, NOTE_GAP = 2.5, 1.25, 2.6
f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")
eighth = lambda v: f(round(v * 8) / 8)

def callouts(notes, legend_x, legend_top, off=(2.0, 2.0), prefix="", clear=1.8):
    """Numbered tags: a circled number beside each target with a leader, and a legend of
    the full notes under the view. notes: [(tx, tz, text)].
    Tags are placed one by one: each tries the default offset first, then longer leaders
    in other directions, until it clears every tag already placed (and every target) by
    about two tag radii. `clear` is the tag radius as printed on the sheet, in model inches."""
    from math import cos, sin, radians, hypot
    layer("ARCH-NOTE", 2)
    r = 1.0
    targets = [(tx, tz) for tx, tz, _ in notes]
    placed = []
    dirs = [45, 135, -45, -135, 90, -90, 20, 160, -20, -160, 0, 180]
    def ok(cx, cy):
        return (all(hypot(cx - px, cy - py) >= 2.3 * clear for px, py in placed) and
                all(hypot(cx - qx, cy - qy) >= 1.3 * clear for qx, qy in targets))
    for i, (tx, tz, s) in enumerate(notes, 1):
        cands = [(tx + off[0], tz + off[1])]
        for dist in (3.0, 4.5, 6.0, 8.0, 10.0, 13.0):
            cands += [(tx + dist * cos(radians(d)), tz + dist * sin(radians(d))) for d in dirs]
        cx, cy = next((c for c in cands if ok(*c)), cands[-1])
        placed.append((cx, cy))
        d = hypot(cx - tx, cy - tz) or 1.0
        line((tx, tz), (cx - (cx - tx) / d * r, cy - (cy - tz) / d * r))   # leader stops at the circle
        cmd("_CIRCLE", pt(cx, cy), r); rec("tag", cx, cy, f"{prefix}{i}")
        text(cx - (0.45 if i < 10 else 0.85), cy - 0.5, 1.0, str(i), sheet=False)
        text(legend_x, legend_top - (i - 1) * NOTE_GAP, NOTE_H, f"{prefix}{i}  {s}", sheet=False)
        if VIEW: SHEETS[VIEW]["legend"].append((f"{prefix}{i}", s))

def angle_up(x, ztop, deg, leg=ANGLE_LEG, t=0.25, forward=False):
    """Cross angle seen end-on, sitting on a slope of `deg`: one leg lies flat on the
    slope (welded down), the other stands up square to it with its top edge at (x, ztop)."""
    from math import cos, sin, radians
    a = radians(deg)
    sv, nv = (cos(a), sin(a)), (-sin(a), cos(a))        # along the slope (to the rear), square to it
    if forward:
        sv = (-sv[0], -sv[1])                           # flat leg points forward instead
    F = (x - nv[0] * leg, ztop - nv[1] * leg)           # foot of the upstand, on the slope
    P = lambda p, q: (F[0] + sv[0] * p + nv[0] * q, F[1] + sv[1] * p + nv[1] * q)
    pline([P(0, 0), P(leg, 0), P(leg, t), P(t, t), P(t, leg), P(0, leg)], True)

cmd("_UNDO", "_BE", "_OSMODE", 0)
cmd("""(if (setq ss (ssget "_X" '((8 . "ARCH-*")))) (command "_.ERASE" ss ""))""")
cmd("_DIMSCALE", 4, "_DIMLUNIT", 4, "_DIMDEC", 3, "_DIMTIH", 0, "_DIMTOH", 0)

# ===== SECTION A: long section ================================================
begin_view("A", 0.0, 0.0, "Section A - long section on the centerline",
           f"Fin depths assumed {f(FLUE_FIN)}\" flue / {f(FILTER_FIN)}\" filter below the rim - measure with the pan seated.")
layer("ARCH-EXIST", 8)
pline([(0, 0), (FIREBOX_D, 0), (FIREBOX_D, GRATE_Z), RAMP[0], RAMP[1],
       (REAR_X, old_floor(REAR_X))])                                      # old ramp + long angles
line((0, RIM), (RIM_L, RIM))                                              # rim line
layer("ARCH-EXIST-BRACE", 6)                                              # existing cross braces
# The two back braces are 2x2 cross angles sitting on the long 2x2 angles that frame
# the floor, so they tilt with it.
for x, zt in ANGLES.items():
    angle_up(x, zt, degrees(atan(FLOOR_SLOPE)))                          # 2x2 brace standing on the long angles
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
line((-0.75, DOOR_BOT - BRACE_H + 0.5), (-0.75, SILL_LEG - 0.5))         # louver (closed)
angle_l(-0.25, SILL_LEG, leg=SILL_LEG)                                    # sill angle
layer("ARCH-BRICK", 1)
pline([(1.75, SILL_LEG), (1.75 + 4.5, 0)])                                # beveled front course: sill top to floor
layer("ARCH-FRONT", 7)
layer("ARCH-GRATE", 1)
for k in range(GRATE_N):
    x = GRATE_X0 + GRATE_OC * k
    pline([(x - 1, GRATE_Z), (x, GRATE_Z - 1.4), (x + 1, GRATE_Z)])       # point down, V up
layer("ARCH-NEW-STEEL", 30)
pline(list(PLATE))                                                        # new ramp plate
box(59.0 - BAR_T, ANGLES[59.0], 59.0, ANGLES[59.0] + EXT_59)              # 59 extension
angle_up(XB, old_floor(XB) + ANGLE_LEG, degrees(atan(FLOOR_SLOPE)))       # new cross brace at the break
box(XB - BAR_T, old_floor(XB) + ANGLE_LEG, XB, bar_top(XB) - BAR_T)       # its flat strip up to bar level
REAR_SUP = X_END                                                          # back face of the rear support
REAR_LEG = 1.0                                                            # 1x1x1/4 angle
angle_up(REAR_SUP, old_floor(REAR_SUP) + REAR_LEG, degrees(atan(FLOOR_SLOPE)), leg=REAR_LEG, forward=True)  # back bottom corner
REAR_EXT = bar_top(REAR_SUP) - BAR_T - (old_floor(REAR_SUP) + REAR_LEG)  # shim under the bars
pline([(X0, bar_top(X0)), (X_END, bar_top(X_END))])                       # bars, top
pline([(X0, bar_top(X0) - BAR_T), (X_END, bar_top(X_END) - BAR_T)])       # bars, bottom
layer("ARCH-BRICK", 1)
pline([(X0, brick_top(X0)), (X_END, brick_top(X_END))])                   # floor brick top
line((X_END, brick_top(X_END)), (X_END, bar_top(X_END)))
pline([(FIREBOX_D - LINING, 0), (FIREBOX_D - LINING, GRATE_Z + EX_OFF - LINING * EM),
       (RAMP[1][0], RAMP[1][1] + EX_OFF),
       (X0, PLATE[1][1] + FACE_OFF)])                                     # lined firebox back + ramp face
layer("ARCH-INSUL", 3)                                                    # 1" rigid board under the ramp brick
B_OFF = BLANKET * (1 + EM ** 2) ** 0.5
pline([(FIREBOX_D - BLANKET, 0), (FIREBOX_D - BLANKET, GRATE_Z + B_OFF - BLANKET * EM),
       (XB, RAMP[0][1] + (XB - RAMP[0][0]) * EM + B_OFF)])
layer("ARCH-FILL", 9)
line((X0 + 1, bar_top(X0 + 1) - BAR_T - 0.1), (X_END - 6, old_floor(X_END - 6)))  # perlite fill (schematic)
# gap marks
layer("ARCH-NOTE", 2)
gaps = []
for x in (XB, 59.0, 87.75, 97.0, X_END):
    fin = FLUE_FIN if x <= 97 else FILTER_FIN
    g = RIM - fin - brick_top(x)
    line((x, brick_top(x)), (x, RIM - fin))
    gaps.append((x, brick_top(x) + g / 2, f"STA {f(x)}: {eighth(g)}\" BRICK TO FIN"))
g97 = RIM - FILTER_FIN - brick_top(97.0)
gaps.append((97.5, brick_top(97.0) + g97 - 0.5, f"STA 97: {eighth(g97)}\" UNDER FILTER FINS"))
text(0, RIM + PAN_DEPTH + 12, TITLE_H, "SECTION A - LONG SECTION (TAGS A1-)", sheet=False)
text(0, RIM + PAN_DEPTH + 8.5, NOTE_H, f"FIN DEPTHS ASSUMED {f(FLUE_FIN)}\" FLUE / {f(FILTER_FIN)}\" FILTER BELOW RIM - MEASURE WITH PAN SEATED", sheet=False)
callouts([
    (-0.5, DOOR_BOT - BRACE_H / 2, "EXIST. FRONT CROSS BRACE - STAYS"),
    (GRATE_X0 + GRATE_OC * 4, GRATE_Z - 0.7, "GRATES 2x2x1/4, POINT DOWN, FILL WITH ASH"),
    (FIREBOX_D, GRATE_Z / 2, "FIREBOX BACK VERTICAL TO GRATE HT"),
    (42, RAMP[0][1] + (42 - RAMP[0][0]) * EM + B_OFF / 2, "1\" RIGID CERAMIC BOARD ON THE STEEL, THEN 2.5\" BRICK, MORTARED"),
    (41, RAMP[0][1] + (41 - RAMP[0][0]) * EM, f"EXIST. RAMP, 2x2 ANGLE FRAME, ~{f(round(degrees(atan(EM))))} DEG"),
    (75, old_floor(75), "EXIST. FLOOR ON LONG 2x2 ANGLES, ONE STRAIGHT PIECE, TOP OF RAMP TO BACK"),
    (RAMP[1][0], RAMP[1][1], "TOP OF OLD RAMP (2x2 ANGLE FRAME) - NEW PLATE STARTS HERE"),
    ((PLATE[0][0] + PLATE[1][0]) / 2, (PLATE[0][1] + PLATE[1][1]) / 2, f"NEW 3/16 RAMP STRIP, 38 x 4, CONTINUES OLD RAMP ~{f(round(degrees(atan(PM))))} DEG"),
    (XB - BAR_T / 2, old_floor(XB) + ANGLE_LEG + NEWB_EXT / 2, f"NEW BRACE STA {eighth(XB)}: 2x2x1/4 x 38 ON FLOOR + 2x3/8 x 38 STRIP"),
    (59.0 - BAR_T / 2, ANGLES[59.0] + EXT_59 / 2, f"EXIST. BRACE 59 (TOP 15 BELOW RIM) + {eighth(EXT_59)}\" FLAT"),
    (87.75 + 1, ANGLES[87.75], "EXIST. BRACE 87.75 (TOP 11.25 BELOW RIM) - BARS ON TOP, AS IS"),
    (100, bar_top(100) - BAR_T / 2, f"2x3/8 FLAT, {N_BARS} @ {f(BAR_OC)} OC, ~{f(round(X_END - X0 + 1))}\" ONE PIECE"),
    (REAR_SUP, bar_top(REAR_SUP) - BAR_T - 0.5, f"NEW REAR SUPPORT: 1x1x1/4 ANGLE IN BACK BOTTOM CORNER, ~{eighth(REAR_EXT)}\" SHIM"),
    (FINISH_BRACE_X, RIM - 1.5, f"EXIST. BRACE UNDER FINISH PAN AT STA {f(FINISH_BRACE_X)} - LOCATION NOT MEASURED"),
    (-1.5, DOOR_BOT + DOOR_H * 0.75, "DOOR LINER: 1 IN. BOARD + FLOATING 3/16 PLATE 28 x 21 ON 304 STUDS"),
    (-1.5, DOOR_BOT + DOOR_H * 0.3, "DOOR ROPE GASKET 3/4 GRAPHITE, IN DOOR LIP"),
    (20, RIM, "PAN RAIL GASKET 1/4 x 1-1/2 TAPE ON EXIST. RIM"),
] + gaps + [
    ((FINISH[0] + FINISH[1]) / 2, RIM + PAN_DEPTH / 2, "FINISH PAN"),
    ((FLUE[0] + FLUE[1]) / 2, RIM + PAN_DEPTH / 2, "FLUE PAN"),
    ((FILTER[0] + FILTER[1]) / 2, RIM + PAN_DEPTH / 2, "FILTER PAN"),
    (4, SILL_LEG / 2, "FRONT COURSE OF ASH PIT FLOOR CUT TO A WEDGE: FLOOR UP TO SILL TOP, RAKE SLIDES OUT"),
], legend_x=0, legend_top=-14, prefix="A")
dim((0, RIM), (0, 0), (-6, RIM / 2))
dim((0, -6), (FIREBOX_D, -6), (FIREBOX_D / 2, -8))
dim((FIREBOX_D, -6), (XB, -6), ((FIREBOX_D + XB) / 2, -8))
dim((XB, -6), (59.0, -6), ((XB + 59.0) / 2, -8))
dim((59.0, -6), (87.75, -6), ((59.0 + 87.75) / 2, -8))
dim((87.75, -6), (X_END, -6), ((87.75 + X_END) / 2, -8))

# ===== FRONT ELEVATION =========================================================
begin_view("F", -160.0, 0.0, "Front elevation", "Looking at the front of the arch.")
layer("ARCH-FRONT", 7)
pline([(-FRONT_W_BOT / 2, 0), (FRONT_W_BOT / 2, 0),
       (FRONT_W_TOP / 2, FRONT_H), (-FRONT_W_TOP / 2, FRONT_H)], True)
box(-DOOR_W / 2, DOOR_BOT, DOOR_W / 2, DOOR_BOT + DOOR_H)                 # door opening
box(-FRONT_W_BOT / 2, DOOR_BOT - BRACE_H, FRONT_W_BOT / 2, DOOR_BOT)      # cross brace
layer("ARCH-NEW-STEEL", 30)
lv_top = DOOR_BOT - BRACE_H
box(-LOUVER_W / 2, lv_top - LOUVER_H + 0.5, LOUVER_W / 2, lv_top + 0.5)   # louver, 1/2" overlap top and bottom
box(-FRONT_W_BOT / 2, 0, FRONT_W_BOT / 2, SILL_LEG)                       # new sill angle at floor level
for hx in (-LOUVER_W / 2 + 4, LOUVER_W / 2 - 8):
    box(hx, lv_top - 0.5, hx + 4, lv_top + 0.5)                           # barrel hinges
pline([(-LOUVER_W / 2 + 2, lv_top - LOUVER_H + 1), (-LOUVER_W / 2 - 2, lv_top - 1)])  # quadrant arm, hinge (left) side
layer("ARCH-NOTE", 2)
text(-FRONT_W_TOP / 2, FRONT_H + 12, TITLE_H, "FRONT ELEVATION (TAGS F1-)", sheet=False)
callouts([
    (0, DOOR_BOT + DOOR_H - 2, f"FIRE DOOR OPENING {f(DOOR_W)} x {f(DOOR_H)}, HINGED LEFT"),
    (-DOOR_W / 2, DOOR_BOT + DOOR_H * 0.6, "NEW DOOR FRAME 2x2x1/4: SIDES 22, TOP 31-1/2 (IF EXIST. FRAME TOO WARPED)"),
    (DOOR_W / 2, DOOR_BOT + DOOR_H * 0.5, "CAM/WEDGE LATCH + SPRING HANDLE, RIGHT SIDE"),
    (-FRONT_W_BOT / 2 + 1, DOOR_BOT - BRACE_H / 2, "EXIST. CROSS BRACE - STAYS"),
    (-LOUVER_W / 2 + 6, lv_top, "BARREL HINGES (2), 4-6 IN., 5/8 PIN"),
    (-LOUVER_W / 2 + 2, lv_top - LOUVER_H / 2, f"LOUVER 3/16 PLATE ~{f(LOUVER_W)} x {f(LOUVER_H)}, FIELD-FIT"),
    (-LOUVER_W / 2 - 1, lv_top - LOUVER_H / 2, "QUADRANT ARM 1/4 x 1-1/2 x 10, LEFT SIDE (AWAY FROM LATCH)"),
    (0, lv_top - LOUVER_H + 0.5, "LOUVER STIFFENER 1x1x1/4 x 31 + SPRING HANDLE"),
    (-FRONT_W_BOT / 2 + 3, SILL_LEG / 2, "NEW SILL 1x1x1/4 x 34 AT FLOOR - LOUVER STOP, TAPE GASKET ON IT"),
    (LOUVER_W / 2 - 3, lv_top - 1, "LOUVER TAPE GASKET 1/8 x 1 (BRACE, SIDES, SILL)"),
], legend_x=-FRONT_W_TOP / 2, legend_top=-12, prefix="F")
dim((-FRONT_W_TOP / 2, FRONT_H), (FRONT_W_TOP / 2, FRONT_H), (0, FRONT_H + 5))
dim((-FRONT_W_BOT / 2, 0), (FRONT_W_BOT / 2, 0), (0, -6))
dim((-DOOR_W / 2, DOOR_BOT + DOOR_H), (DOOR_W / 2, DOOR_BOT + DOOR_H), (0, DOOR_BOT + DOOR_H + 2.5))
dim((FRONT_W_TOP / 2, 0), (FRONT_W_TOP / 2, FRONT_H), (FRONT_W_TOP / 2 + 3, FRONT_H / 2))
dim((DOOR_W / 2, 0), (DOOR_W / 2, DOOR_BOT), (DOOR_W / 2 + 6, DOOR_BOT / 2))

# ===== SECTION B: cross section through the back bays =========================
XS = 70.0
begin_view("B", 250.0, 0.0, f"Section B - back bays at station {f(XS)}", "Looking toward the chimney.")
hw = SHELL_W / 2
layer("ARCH-EXIST", 8)
pline([(-hw, old_floor(XS)), (hw, old_floor(XS))])
layer("ARCH-EXIST-BRACE", 6)
box(-hw, ANGLES[87.75] - ANGLE_LEG, hw, ANGLES[87.75])                    # 87.75 brace, beyond, full width
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
side_top = RIM - 0.25                                                    # side lining runs up to just under the rim, beside the fins
side_in = (SHELL_W - FIN_SPAN - 1) / 2                                     # lining allowance per side
for s in (-1, 1):
    xi = s * (hw - side_in)
    box(min(s * hw, xi), bt + BRICK, max(s * hw, xi), side_top)           # blanket + brick on edge
    box(min(xi, xi + s * BRICK), bt + BRICK, max(xi, xi + s * BRICK), side_top)
layer("ARCH-NOTE", 2)
text(-hw, RIM + PAN_DEPTH + 12, TITLE_H, f"SECTION B - BACK BAYS AT STA {f(XS)} (TAGS B1-)", sheet=False)
text(-hw, RIM + PAN_DEPTH + 8.5, NOTE_H, "LOOKING TOWARD THE CHIMNEY", sheet=False)
callouts([
    (0, RIM - FLUE_FIN / 2, "FLUE PAN FINS"),
    (hw - side_in / 2, (bt + side_top) / 2, f"BRICK ON EDGE + ~7/8 BLANKET, {eighth(side_in)}\"/SIDE"),
    (x0 + BAR_OC / 2, bt + BRICK / 2, "FULL BRICK LAID CROSSWISE"),
    (x0 + BAR_OC, bt - BAR_T / 2, f"{N_BARS} BARS 2x3/8 @ {f(BAR_OC)} OC"),
    (0, old_floor(XS), "OLD FLOOR; PERLITE FILL BELOW BARS"),
    (-hw + 3, ANGLES[87.75] - ANGLE_LEG / 2, "EXIST. BRACE 87.75 BEYOND, WALL TO WALL"),
], legend_x=-hw, legend_top=-10, prefix="B")
dim((-hw, 2), (hw, 2), (0, -4))
dim((x0, bt), (x0 + BAR_OC, bt), (x0 + BAR_OC / 2, bt - 3))

cmd("_UNDO", "_E")                              # no ZOOM: ARES rejects Extents and Fit from a script

VIEW = None
from sheets import write_sheets
write_sheets(SHEETS, Path(__file__).with_name("school-arch-sheets.html"))

dest = Path(__file__).with_name("school-arch.scr")
dest.write_text("\n".join(out) + "\n", encoding="ascii")
print(dest)
print(f"floor line: brick top {BT1:.2f} at 87.75, {BT2:.2f} at 97, slope {SLOPE * 12:.2f}\"/ft")
print(f"break at sta {XB:.2f}, brick top {RIM - brick_top(XB):.2f} below rim; new brace strip {NEWB_EXT:.2f}; plate {((XB - RAMP[1][0]) * (1 + EM**2) ** 0.5):.1f} along slope")
print(f"59 extension {EXT_59:.2f}, bar length {X_END - X0:.1f}, rear strip {REAR_EXT:.2f}")
for x in (X0, 87.75, 97, 113):
    print(f"sta {x:6.2f}: bar top {RIM - bar_top(x):.2f} below rim, old floor {RIM - old_floor(x):.2f} below rim")
