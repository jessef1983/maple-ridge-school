"""Generate an ARES Commander .scr for the sap house east awning + north porch.

Draws, on new EXT-* layers:
  - Plan: east awning (enclosed, 3:12 shed sistered to the existing rafters over
    the 108-116" long beam) that continues north as the east skirt of a north
    porch; the porch is a lower, separate gable centered on the building, with
    3:12 skirts out to eave post lines 6' past each wall and a steeper center
    gable between the wall lines. French drain along the uphill (SE) side.
  - Section A: through the awning, with the existing beam, 4x6 rafter, battens
    and shakes, the sistered tie-in, the let-in outside beam and kickboard.
  - Section B: across the north porch, looking south at the north gable.

Coordinates are in the drawing's own frame (inches, +Y = north), taken from
"School Sap House - Ground Floor.dxf". Existing building faces come from the
timber frame and Jesse's field measurements (magicplan report, 2026-08-22, plus
2026-11-03 corrections), NOT from the gray `walls` polylines (those use a 9.84"
placeholder thickness).

The plan geometry is written for an awning on the WEST wall and mirrored about
the building centerline when AWNING_SIDE = "east", so variable names say
west/east as drawn before the mirror. The porch is symmetric.

Re-running the script first erases everything on EXT-* layers, so it replaces
an earlier run instead of stacking on top of it.

Edit the parameters below and re-run: python make_awning_scr.py
"""
from pathlib import Path

# --- Existing building ---------------------------------------------------
# 2" board-and-batten siding, 155.5" x 359" inside, 159.5" x 363" outside.
# 7.5x7.5 posts flush to the siding. Long (N-S) beams 7.5 wide, 108" to the
# bottom, 116" to the top; cross beams top at 94". 4x6 rafters bear on the long
# beams and rise to 172" (bottom of rafters) at the ridge, under 2" battens and
# cedar shakes, with 11" overhangs.
WALL_T = 2.0
IN_W, IN_L = 155.5, 359.0
CX, CY = 6.12, 54.88                  # frame centerline (from DXF post/beam inserts)
W_FACE = CX - IN_W / 2 - WALL_T       # west exterior face  (-73.63)
E_FACE = CX + IN_W / 2 + WALL_T       # east exterior face  ( 85.87)
N_FACE = CY + IN_L / 2 + WALL_T       # north exterior face ( 236.38)
S_FACE = CY - IN_L / 2 - WALL_T       # south exterior face (-126.62)
N_INT = N_FACE - WALL_T
FRAME_ROWS_Y = [N_INT - 3.75, N_INT - 119.25, N_INT - 263.75, N_INT - 355.25]  # post centers
EX_POST = 7.5
LONG_BEAM_BOT, LONG_BEAM_TOP = 108.0, 116.0
MAIN_PEAK = 172.0                     # bottom of main rafters at ridge
MAIN_PITCH = (MAIN_PEAK - LONG_BEAM_TOP) / (IN_W / 2)          # ~8.6:12
EX_RAFTER_D = 6.0                     # 4x6
BATTEN, SHAKE = 2.0, 1.0
EX_OVERHANG = 11

# --- New work (Jesse, 2026-11-02/03) ----------------------------------------
AWNING_SIDE = "east"  # access road is on the west; SE bank limits it to the middle bay
DEPTH = 72          # awning post centerline 6' from the wall
PORCH_DEPTH = 96    # porch front post line 8' from the north wall
OVERHANG = 24       # rafter tail past the outside face of the eave beam
FRONT_OH = 12       # porch gable overhang past the front post line (assumed)
RAKE = 6            # awning rake at its south end (assumed)
SKIRT = 3 / 12      # awning and porch skirts
GABLE = 5 / 12      # porch center gable (assumed; 6:12 leaves only ~4" under the main rafters)
TIE_Z = 126         # porch rafter ties, lower third of the gable rise (assumed)
POST = 5.5          # 6x6 actual
PIER = 20           # stone pier, bluestone cap at PIER_TOP
PIER_TOP = 30
FOOTING_DEPTH = 48  # below grade, frost (confirm with engineer / town)
EAVE_BEAM = (3.0, 9.25)               # double 2x10, let 2" into the outside face of posts, 1" proud
LET_IN = 2.0
KICK = (3.0, 9.25)                    # PT kickboard beam, let in the same way (assumed 2x10 double)
BREAK_BEAM = (3.0, 11.25)             # porch break beams, double 2x12 (size by engineer)
RAFTER_W, RAFTER_D = 1.5, 9.25        # 2x10
NEW_ROOFING = 1.25                    # sheathing + asphalt shingle
OC = 24                               # assumed to match existing rafter spacing (confirm)

vdepth = lambda d, p: d * (1 + p ** 2) ** 0.5                  # vertical depth on slope
# New rafter bottom line, u = distance out from the exterior wall face. It sits on
# the top outside edge of the existing long beam (u = -WALL_T, z = 116).
# Engineer: birdsmouth at both bearings. The seat runs the full 7.5" width of the
# existing beam (heel butts its outside face), so the underside line passes 116"
# at the beam's INSIDE edge and drops 3:12 from there.
SEAT_IN = -(WALL_T + 7.5)                                     # inside face of existing beam
rb = lambda u: LONG_BEAM_TOP - (u - SEAT_IN) * SKIRT
# Existing rafter bottom line, same origin, rising inward.
eb = lambda u: LONG_BEAM_TOP - (u + WALL_T) * MAIN_PITCH
ex_top = lambda u: eb(u) + vdepth(EX_RAFTER_D, MAIN_PITCH)
ex_roof = lambda u: ex_top(u) + vdepth(BATTEN + SHAKE, MAIN_PITCH)
new_top = lambda u: rb(u) + vdepth(RAFTER_D, SKIRT)
new_roof = lambda u: new_top(u) + vdepth(NEW_ROOFING, SKIRT)

POST_OUT = DEPTH + POST / 2                                    # outside face of posts (74.75)
EB_IN, EB_OUT = POST_OUT - LET_IN, POST_OUT - LET_IN + EAVE_BEAM[0]   # 72.75 .. 75.75
EAVE_BEAM_TOP = rb(EB_IN)                                      # seat spans the beam top, heel at outside face
EAVE_BEAM_BOT = EAVE_BEAM_TOP - EAVE_BEAM[1]
TAIL = EB_OUT + OVERHANG

WX = W_FACE - DEPTH                   # west eave post line (-145.63)
EX = CX + (CX - WX)                   # east eave post line, mirrored (157.87)
WF, EF = W_FACE - TAIL, E_FACE + TAIL # skirt fascia lines
PY = N_FACE + PORCH_DEPTH             # porch front post line (332.38)
PF = PY + FRONT_OH                    # porch front roof edge

BREAK_HALF = CX - W_FACE                                       # 79.75
BWX, BEX = W_FACE - BREAK_BEAM[0] / 2, E_FACE + BREAK_BEAM[0] / 2
BREAK_Z = rb(0)                                                # break beam top, at the wall line
RIDGE_RB = BREAK_Z + BREAK_HALF * GABLE
BREAK_BEAM_BOT = BREAK_Z - BREAK_BEAM[1]

# Awning posts: south end on the existing frame row at the south edge of the
# middle bay; the enclosure's north corner post sits flush with the north wall.
S_END = FRAME_ROWS_Y[2]                                        # -29.37
west_posts_y = [S_END, None, None, N_FACE - POST / 2, PY]
span = (west_posts_y[3] - west_posts_y[0]) / 3
west_posts_y[1] = west_posts_y[0] + span
west_posts_y[2] = west_posts_y[0] + 2 * span
S_WALL = S_END - POST / 2                                      # enclosure south wall outside face

front_posts_x = [WX, BWX, BEX, EX]
pier_posts = [(x, PY) for x in front_posts_x] + [(EX, N_FACE + POST / 2)]

out = []
def cmd(*parts): out.extend(str(p) for p in parts)
MIRROR = False                         # set while drawing the plan
def pt(x, y):
    if MIRROR: x = 2 * CX - x
    return f"{x:.2f},{y:.2f}"
def layer(name, color):
    cmd("_-LAYER", "_M", name, "_C", color, "", "")
def line(a, b): cmd("_LINE", pt(*a), pt(*b), "")
def pline(pts, closed=False): cmd("_PLINE", *[pt(*p) for p in pts], "_C" if closed else "")
def box(x1, y1, x2, y2): pline([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], True)
def sq(x, y, s): box(x - s / 2, y - s / 2, x + s / 2, y + s / 2)
def text(x, y, h, s): cmd("_TEXT", f"{x:.2f},{y:.2f}", h, 0, s)   # never mirrored
def dim(a, b, at): cmd("_DIMLINEAR", pt(*a), pt(*b), pt(*at))

TITLE_H, NOTE_H, NOTE_GAP = 5.0, 3.0, 7.0
CHAR_W = 1.0                                   # generous char width / height, so columns never touch

def callouts(to_xy, notes, col_u, side):
    """Stack notes in a column beside a section with a leader line to each target.
    notes: [(target_u, target_z, text)]; side "R" = text starts at col_u,
    side "L" = text ends at col_u. Text is placed in target-height order so
    leaders don't cross, and never closer than NOTE_GAP."""
    prev = None
    for tu, tz, s_ in sorted(notes, key=lambda n: -n[1]):
        z = tz - NOTE_H / 2 if prev is None else min(tz - NOTE_H / 2, prev - NOTE_GAP)
        prev = z
        w = len(s_) * NOTE_H * CHAR_W
        x0 = col_u if side == "R" else col_u - w
        text(*to_xy(x0, z), NOTE_H, s_)
        end = (col_u - 2, z + NOTE_H / 2) if side == "R" else (col_u + 2, z + NOTE_H / 2)
        line(to_xy(tu, tz), to_xy(*end))

def dim_style():
    cmd("_DIMSCALE", 18, "_DIMLUNIT", 4, "_DIMDEC", 3, "_DIMTIH", 0, "_DIMTOH", 0)

cmd("_UNDO", "_BE", "_OSMODE", 0)
cmd("""(if (setq ss (ssget "_X" '((8 . "EXT-*")))) (command "_.ERASE" ss ""))""")
# Jesse asked to drop the old gable elevation (layer elev-existing, plus its window
# outline and label on `windows` -- the plan's window blocks on that layer stay).
cmd("""(if (setq ss (ssget "_X" '((8 . "elev-existing")))) (command "_.ERASE" ss ""))""")
cmd("""(if (setq ss (ssget "_X" '((8 . "windows") (-4 . "<NOT") (0 . "INSERT") (-4 . "NOT>")))) (command "_.ERASE" ss ""))""")
# magicplan only offered round posts (blocks F-0-0..F-0-7; F-0-1 was never placed). Replace
# them with the real 7.5 x 7.5 square posts on EXIST-POST, which re-runs also clear first.
cmd("""(if (setq ss (ssget "_X" '((0 . "INSERT") (2 . "F-0-0,F-0-1,F-0-2,F-0-3,F-0-4,F-0-5,F-0-6,F-0-7")))) (command "_.ERASE" ss ""))""")
cmd("""(if (setq ss (ssget "_X" '((8 . "EXIST-POST")))) (command "_.ERASE" ss ""))""")
layer("EXIST-POST", 4)
for px in (CX - (IN_W / 2 - EX_POST / 2), CX + (IN_W / 2 - EX_POST / 2)):   # flush to the siding
    for py in FRAME_ROWS_Y:
        sq(px, py, EX_POST)

# ===== PLAN ==================================================================
MIRROR = AWNING_SIDE == "east"
mx = lambda x: 2 * CX - x if MIRROR else x                     # final x, for text

layer("EXT-PIER", 8)
for x, y in pier_posts:
    sq(x, y, PIER)

layer("EXT-POST", 30)
posts = [(WX, y) for y in west_posts_y] + [(x, PY) for x in front_posts_x[1:]] \
        + [(EX, N_FACE + POST / 2), (BWX, N_FACE + POST / 2), (BEX, N_FACE + POST / 2)]
for x, y in posts:
    sq(x, y, POST)

layer("EXT-BEAM", 4)
# eave beams let into the outside face of the posts (outward = -x before mirror)
box(WX - POST / 2 - 1, S_WALL - RAKE, WX - POST / 2 + LET_IN, PF)
box(EX + POST / 2 - LET_IN, N_FACE, EX + POST / 2 + 1, PF)
box(BWX - BREAK_BEAM[0] / 2, N_FACE, BWX + BREAK_BEAM[0] / 2, PF)
box(BEX - BREAK_BEAM[0] / 2, N_FACE, BEX + BREAK_BEAM[0] / 2, PF)

layer("EXT-RAFTER", 2)
heel = W_FACE + WALL_T + EX_POST                               # inside edge of the existing beam
y = S_WALL - RAKE + RAFTER_W / 2                               # awning (sistered) + skirt
while y < PF:
    line((heel if y < N_FACE else W_FACE, y), (WF, y)); y += OC
y = N_FACE + 1.5 + RAFTER_W / 2                                # porch: other skirt + center gable
while y < PF:
    line((E_FACE, y), (EF, y))
    line((W_FACE, y), (CX, y)); line((E_FACE, y), (CX, y))
    y += OC
line((CX, N_FACE), (CX, PF))                                   # ridge

layer("EXT-ROOF", 1)
pline([(W_FACE, S_WALL - RAKE), (WF, S_WALL - RAKE), (WF, PF), (EF, PF), (EF, N_FACE), (E_FACE, N_FACE)])

layer("EXT-WALL", 8)                                           # board & batten on kickboard / eave beam
o = WX - POST / 2 - 1
box(o, S_WALL, o + 2, N_FACE)                                  # long wall
box(o + 2, S_WALL, W_FACE, S_WALL + 2)                         # south end
box(o + 2, N_FACE - 2, W_FACE, N_FACE)                         # north end (continues building's)

# Drainage, drawn in REAL coordinates (awning on the east, road and catch basin
# on the west). High point at the SE corner by the bank; two legs run downhill
# to the existing catch basin near the NW corner: one up the east awning drip
# line and across the porch front, one along the south end and up the west side.
# A floor drain at the yard hydrant (SE corner of the center bay) ties into the
# south leg with solid pipe.
MIRROR = False
d_off = 24
D_W = W_FACE - d_off                                           # west run, 2' off the west wall
CB = (D_W, N_FACE + 12)                                        # existing catch basin - LOCATE
HP = (E_FACE + d_off, S_FACE - d_off)                          # SE high point
# Trench drain: 12" x 43" grate on the post line at the south end of the center
# bay, from the yard hydrant (on the east post) west to the evaporator arch.
TD_W, TD_L = 12, 43
TD_E = E_FACE - WALL_T - EX_POST                               # west face of the east post
TD = (TD_E - TD_L, FRAME_ROWS_Y[2] - TD_W / 2, TD_E, FRAME_ROWS_Y[2] + TD_W / 2)
FD = (TD_E - 6, FRAME_ROWS_Y[2])                               # outlet at the hydrant end
layer("EXT-DRAIN", 5)
pline([HP, (HP[0], S_WALL - RAKE), (EF, S_WALL - RAKE), (EF, PF + 12), (D_W, PF + 12), CB])   # east leg
pline([HP, (D_W, HP[1]), CB])                                                                # south/west leg
pline([FD, (FD[0], HP[1])])                                                                  # floor drain line
box(*TD)
cmd("_CIRCLE", pt(*CB), 9)
MIRROR = AWNING_SIDE == "east"

layer("EXT-TEXT", 7)
text(mx(W_FACE) + (8 if MIRROR else -DEPTH + 8), (S_WALL + N_FACE) / 2, 4, "ENCLOSED")
text(CX - 20, N_FACE + 45, 4, "NORTH PORCH")
text(D_W + 6, S_FACE - d_off - 10, 3, "FRENCH DRAIN - 4in PERF IN GRAVEL, SOLID PIPE TO CB, 1% MIN FALL")
text(HP[0] + 6, HP[1] - 8, 3, "HIGH POINT")
text(CB[0] + 12, CB[1] - 2, 3, "EXIST. CATCH BASIN - LOCATE")
text(TD[0], TD[3] + 4, 3, f'{TD_W}" x {TD_L}" TRENCH DRAIN, HYDRANT TO ARCH')
for i, s_ in enumerate([
        'NEW ROOFS: ASPHALT SHINGLE, 2x10 @ 24" OC (MATCH EXIST. RAFTERS), 6x6 POSTS',
        'AWNING RAFTERS BIRDSMOUTHED ON EXIST. 116" BEAM, SISTERED TO EXIST. 4x6 - SEE SECTION A',
        f'EAVE BEAMS DBL 2x10 LET 2" INTO POSTS; PORCH GABLE {GABLE * 12:g}:12 - SEE SECTION B',
        f'{PIER}" STONE PIERS, BLUESTONE CAP AT {PIER_TOP}"; PAVER FLOORS']):
    text(WF, PF + 52 - i * 7, 3.5, s_)
dim_style()
dim((W_FACE, S_WALL), (WX, S_WALL), (0, S_WALL - 30))
dim((E_FACE, N_FACE), (E_FACE, PY), (EF + 30, 0))
for a, b in zip(west_posts_y, west_posts_y[1:]):
    dim((WX, a), (WX, b), (WF - 30, 0))
for a, b in zip(front_posts_x, front_posts_x[1:]):
    dim((a, PY), (b, PY), (0, PF + 20))
MIRROR = False

# ===== SECTION A: awning (u = out from the wall face, z = height) ===========
OX, OZ = 520.0, -120.0
def S(u, z): return (OX + u, OZ + z)
def sline(a, b): line(S(*a), S(*b))
def spline(pts, closed=False): pline([S(*p) for p in pts], closed)
def sbox(u1, z1, u2, z2): box(*S(u1, z1), *S(u2, z2))

IN_U = -60                                                     # how far inside to draw
B_IN, B_OUT = -WALL_T - EX_POST, -WALL_T                       # existing beam / post faces
EX_TAIL = EX_OVERHANG

layer("EXT-SECTION-EXIST", 8)
sline((IN_U, 0), (TAIL + 40, 0))                               # grade / paver surface
sbox(B_OUT, 0, 0, LONG_BEAM_BOT)                               # siding below beam
sbox(B_IN, 0, B_OUT, LONG_BEAM_BOT)                            # existing post
sbox(B_IN, LONG_BEAM_BOT, B_OUT, LONG_BEAM_TOP)                # long beam 7.5 x 8
spline([(IN_U, eb(IN_U)), (B_IN, eb(B_IN)), (B_IN, LONG_BEAM_TOP), (B_OUT, LONG_BEAM_TOP),
        (EX_TAIL, eb(EX_TAIL)), (EX_TAIL, ex_top(EX_TAIL)), (IN_U, ex_top(IN_U))], True)   # 4x6 rafter
spline([(IN_U, ex_top(IN_U)), (EX_TAIL, ex_top(EX_TAIL)), (EX_TAIL, ex_roof(EX_TAIL)),
        (IN_U, ex_roof(IN_U))], True)                          # battens + shakes

layer("EXT-SECTION", 2)
spline([(B_IN, LONG_BEAM_TOP), (B_OUT, LONG_BEAM_TOP), (B_OUT, rb(B_OUT)),   # birdsmouth 1
        (EB_IN, EAVE_BEAM_TOP), (EB_OUT, EAVE_BEAM_TOP), (EB_OUT, rb(EB_OUT)),     # birdsmouth 2
        (TAIL, rb(TAIL)), (TAIL, new_top(TAIL)), (B_IN, new_top(B_IN))], True)    # 2x10 sistered
sbox(DEPTH - POST / 2, 0, POST_OUT, EAVE_BEAM_TOP)             # 6x6 post
sbox(EB_IN, EAVE_BEAM_BOT, EB_OUT, EAVE_BEAM_TOP)              # dbl 2x10 let in 2"
sbox(EB_IN, 0, EB_OUT, KICK[1])                                # PT kickboard, let in
sbox(POST_OUT, KICK[1], EB_OUT, EAVE_BEAM_BOT)                 # 1" boards between
sbox(DEPTH - 9, -FOOTING_DEPTH, DEPTH + 9, -FOOTING_DEPTH + 10)   # footing
sbox(DEPTH - 5, -FOOTING_DEPTH + 10, DEPTH + 5, 0)             # pier/form tube to grade
dr = TAIL                                                      # French drain at the drip line
sbox(dr - 6, -30, dr + 6, -4)
cmd("_CIRCLE", pt(*S(dr, -26)), 2)
# Kick flashing over the pitch break: from up the old roof, over the break, onto the new roof.
brk = next(u / 4 for u in range(-200, 40) if ex_roof(u / 4) <= new_roof(u / 4))
spline([(brk - 18, ex_roof(brk - 18) + 0.5), (brk, max(ex_roof(brk), new_roof(brk)) + 0.5),
        (brk + 12, new_roof(brk + 12) + 0.5)])

layer("EXT-TEXT", 7)
text(*S(IN_U, 170), TITLE_H, f"SECTION A - {AWNING_SIDE.upper()} AWNING")
callouts(S, [
    (-40, (eb(-40) + ex_top(-40)) / 2, "EXIST. 4x6 RAFTERS, 2in BATTENS, CEDAR SHAKES"),
    (-20, ex_roof(-20), "REMOVE 1 COURSE SHAKES + BATTENS"),
    (B_IN + 3.75, LONG_BEAM_BOT + 4, "EXIST. LONG BEAM 7.5x8, 108-116"),
    (B_OUT + 1, LONG_BEAM_TOP - 2, "NOTCH SIDING FOR EACH RAFTER HEEL"),
    (B_IN + 3.75, 50, "EXIST. 7.5 POST, 2in BOARD + BATTEN"),
], IN_U - 40, "L")
callouts(S, [
    (brk, new_roof(brk) + 0.5, "HEAVY KICK FLASHING OVER PITCH BREAK"),
    (40, new_top(40), "2x10 @ 24 OC, 3:12, ASPHALT SHINGLE, DBL UNDERLAYMENT"),
    (-5, LONG_BEAM_TOP + 4, 'SISTER TO EXIST. 4x6, (2) 1/4" STRUCT. SCREWS'),
    (EB_OUT, EAVE_BEAM_TOP, "BIRDSMOUTH AT BOTH BEARINGS"),
    (EB_OUT, EAVE_BEAM_BOT + 4, 'DBL 2x10 LET 2" INTO 6x6 POSTS, 1" PROUD'),
    (EB_OUT, 45, "1in BOARD + BATTEN"),
    (EB_OUT, 5, "PT KICKBOARD, LET IN"),
    (40, 0, "PAVERS ON COMPACTED BASE"),
    (dr, -20, "FRENCH DRAIN, 4in PERF IN GRAVEL"),
    (DEPTH, -FOOTING_DEPTH + 5, "FOOTING BELOW FROST - BY ENGINEER"),
], TAIL + 45, "R")
dim(S(0, 0), S(DEPTH, 0), S(0, -62))
dim(S(EB_OUT, 0), S(TAIL, 0), S(0, -62))
dim(S(TAIL + 12, 0), S(TAIL + 12, EAVE_BEAM_BOT), S(TAIL + 12, 0))
dim(S(TAIL + 24, 0), S(TAIL + 24, rb(TAIL)), S(TAIL + 24, 0))
dim(S(IN_U - 15, 0), S(IN_U - 15, LONG_BEAM_TOP), S(IN_U - 15, 0))

# ===== SECTION B: across the porch, looking south (u = x - CX) ===========
OX, OZ = 1130.0, -120.0
def B(u, z): return (OX + u, OZ + z)
def bline(a, b): line(B(*a), B(*b))
def bpline(pts, closed=False): pline([B(*p) for p in pts], closed)
def bbox(u1, z1, u2, z2): box(*B(u1, z1), *B(u2, z2))
HW = IN_W / 2 + WALL_T                                         # 79.75
BRK_U = HW                                                     # break at the wall line
EAVE_POST_U = CX - WX                                          # 151.75
TAIL_U = HW + TAIL

def porch_rb(a):                                               # rafter bottom, a = |u|
    return RIDGE_RB - a * GABLE if a <= BRK_U else rb(a - HW)
def porch_top(a):
    return porch_rb(a) + vdepth(RAFTER_D, GABLE if a <= BRK_U else SKIRT)

layer("EXT-SECTION-EXIST", 8)
bline((-TAIL_U - 20, 0), (TAIL_U + 20, 0))
for s in (-1, 1):
    bpline([(s * HW, 0), (s * HW, LONG_BEAM_BOT)])
    bbox(s * (HW - WALL_T), LONG_BEAM_BOT, s * (HW - WALL_T - EX_POST), LONG_BEAM_TOP)
bpline([(-HW - EX_OVERHANG, eb(EX_OVERHANG)), (0, MAIN_PEAK), (HW + EX_OVERHANG, eb(EX_OVERHANG))])
bpline([(-HW - EX_OVERHANG, ex_roof(EX_OVERHANG)), (0, MAIN_PEAK + vdepth(EX_RAFTER_D + BATTEN + SHAKE, MAIN_PITCH)),
        (HW + EX_OVERHANG, ex_roof(EX_OVERHANG))])

layer("EXT-SECTION", 2)
for s in (-1, 1):
    eu, bu = s * EAVE_POST_U, s * (HW + BREAK_BEAM[0] / 2)
    bbox(eu - PIER / 2, 0, eu + PIER / 2, PIER_TOP)
    bbox(bu - PIER / 2, 0, bu + PIER / 2, PIER_TOP)
    bbox(eu - POST / 2, PIER_TOP, eu + POST / 2, EAVE_BEAM_TOP)
    bbox(bu - POST / 2, PIER_TOP, bu + POST / 2, BREAK_BEAM_BOT)
    ob = s * (HW + EB_OUT)                                     # let-in eave beam, outside edge
    bbox(ob, EAVE_BEAM_BOT, ob - s * EAVE_BEAM[0], EAVE_BEAM_TOP)
    bbox(bu - BREAK_BEAM[0] / 2, BREAK_BEAM_BOT, bu + BREAK_BEAM[0] / 2, BREAK_Z)
    t = s * TAIL_U
    bpline([(s * BRK_U, BREAK_Z), (t, porch_rb(TAIL_U)), (t, porch_top(TAIL_U)),
            (s * BRK_U, BREAK_Z + vdepth(RAFTER_D, SKIRT))], True)          # skirt rafter
    bpline([(0, RIDGE_RB), (s * BRK_U, BREAK_Z), (s * BRK_U, BREAK_Z + vdepth(RAFTER_D, GABLE)),
            (0, RIDGE_RB + vdepth(RAFTER_D, GABLE))], True)                  # gable rafter
tie_u = (RIDGE_RB - TIE_Z) / GABLE
bline((-tie_u, TIE_Z), (tie_u, TIE_Z))

layer("EXT-TEXT", 7)
text(*B(-TAIL_U, 215), TITLE_H, "SECTION B - NORTH PORCH, LOOKING SOUTH")
callouts(B, [
    (-30, eb(30 - HW), f"EXIST. MAIN GABLE BEYOND, {MAIN_PITCH * 12:.1f}:12"),
    (-62, eb(62 - HW), "TRIM MAIN RAKE WHERE PORCH ROOF MEETS IT"),
    (-HW - 30, porch_top(HW + 30), "3:12 SKIRT, BIRDSMOUTH AT BEAMS"),
    (-EAVE_POST_U, 60, "6x6 POST"),
    (-EAVE_POST_U - PIER / 2, PIER_TOP - 2, f'{PIER}" STONE PIER, BLUESTONE CAP AT {PIER_TOP}"'),
], -TAIL_U - 15, "L")
callouts(B, [
    (25, porch_top(25), f'{GABLE * 12:g}:12 GABLE, ASPHALT SHINGLE'),
    (35, TIE_Z, f'2x RAFTER TIES AT {TIE_Z}"'),
    (HW + BREAK_BEAM[0] / 2, BREAK_BEAM_BOT + 4, "BREAK BEAM DBL 2x12 - BY ENGINEER"),
    (HW + EB_OUT, EAVE_BEAM_BOT + 4, 'DBL 2x10 EAVE BEAM, LET INTO POSTS'),
], TAIL_U + 50, "R")
dim(B(-EAVE_POST_U, 0), B(-HW, 0), B(0, -20))
dim(B(-HW, 0), B(HW, 0), B(0, -20))
dim(B(HW, 0), B(EAVE_POST_U, 0), B(0, -20))
dim(B(TAIL_U + 12, 0), B(TAIL_U + 12, EAVE_BEAM_BOT), B(TAIL_U + 12, 0))
dim(B(TAIL_U + 24, 0), B(TAIL_U + 24, BREAK_BEAM_BOT), B(TAIL_U + 24, 0))
dim(B(TAIL_U + 36, 0), B(TAIL_U + 36, RIDGE_RB), B(TAIL_U + 36, 0))

cmd("_UNDO", "_E")

dest = Path(__file__).with_name("sap-house-awning.scr")
dest.write_text("\n".join(out) + "\n", encoding="ascii")
print(dest)
for x, yy in posts:
    print(f"post {(2 * CX - x if AWNING_SIDE == 'east' else x):8.2f} {yy:8.2f}")
print("awning bays", [round(b - a, 1) for a, b in zip(west_posts_y, west_posts_y[1:])])
print("front bays", [round(b - a, 1) for a, b in zip(front_posts_x, front_posts_x[1:])])
print(f"main pitch {MAIN_PITCH * 12:.1f}:12   pitch break at u={brk:.1f}  new roof {new_roof(brk):.1f}")
print(f"awning: rafter bottom at wall {rb(0):.2f}, eave beam {EAVE_BEAM_BOT:.2f}-{EAVE_BEAM_TOP:.2f}, tail bottom {rb(TAIL):.2f}")
print(f"porch: break {BREAK_Z:.2f} (beam bottom {BREAK_BEAM_BOT:.2f}), ridge rb {RIDGE_RB:.2f}, "
      f"ridge top {porch_top(0) + NEW_ROOFING:.2f} vs main rafter bottom {MAIN_PEAK}")
clash = [a for a in range(0, int(HW) + 12) if porch_top(a) + NEW_ROOFING > eb(a - HW)]
print(f"porch roof above main rake from {clash[0] if clash else None}\" off center outward")
