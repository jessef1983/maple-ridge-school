"""North elevation of the sap house with the east awning (Phase 1) and north porch (Phase 2).

Geometry comes from make_awning_scr.py (single source of truth). Writes north-elevation.html,
two Letter-landscape pages at 1/4" = 1'-0": page 1 after Phase 1, page 2 after Phase 2.
Looking south, so EAST IS ON THE LEFT.

Existing north-wall window: 53" wide, centered (magicplan report, 51/53/51). Its sill and head
heights are estimated from the 2026-08-22 photo (scaled off the 159.5" wall width), as are the
cupola's size and height (see make_awning_scr.py).

Print to PDF with headless Chrome:
  chrome --headless=new --no-pdf-header-footer --print-to-pdf=north-elevation.pdf north-elevation.html
"""
import contextlib
import io
import runpy
from html import escape
from pathlib import Path

HERE = Path(__file__).parent
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(str(HERE / "make_awning_scr.py"))
globals().update({k: v for k, v in g.items() if k.isupper() or k in (
    "rb", "eb", "ex_top", "ex_roof", "new_top", "new_roof", "vdepth")})
assert AWNING_SIDE == "east"

WIN_W, WIN_SILL, WIN_HEAD = 53.0, 32.0, 78.0     # sill/head estimated from photo
HW = IN_W / 2 + WALL_T                           # wall face, off center
EAVE_POST_U = HW + DEPTH                         # porch eave post line, off center
TAIL_U = HW + TAIL
BU = HW + BREAK_BEAM[0] / 2                      # purlin / break post line, off center
ROOF_V = vdepth(NEW_ROOFING, SKIRT)
porch_rb = lambda a: RIDGE_RB - a * GABLE        # one 3:12 line, eave to ridge
porch_top = lambda a: porch_rb(a) + vdepth(RAFTER_D, GABLE)
assert abs(porch_rb(TAIL_U) - rb(TAIL)) < 0.01   # porch skirt continues the awning roof
RIDGE_TOP = MAIN_PEAK + vdepth(EX_RAFTER_D + BATTEN + SHAKE, MAIN_PITCH)
roof_at = lambda a: RIDGE_TOP - a * MAIN_PITCH   # main roof surface, a off center
TIE_U = (RIDGE_RB - TIE_Z) / GABLE


def ftin(v):
    v = abs(v)
    ft, inch = divmod(round(v * 8) / 8, 12)
    whole, frac = int(inch), inch - int(inch)
    fr = {0: "", 0.125: " 1/8", 0.25: " 1/4", 0.375: " 3/8", 0.5: " 1/2", 0.625: " 5/8",
          0.75: " 3/4", 0.875: " 7/8"}[round(frac * 8) / 8]
    s = f'{whole}{fr}"'
    return f"{int(ft)}'-{s}" if ft else s


SCALE = 48                                       # 1/4" = 1'-0"
H0, H1 = -TAIL_U - 18, TAIL_U + 90               # screen x = -h - H0 (east on the left)
Z0, Z1 = -34, STACK_TOP + 14


class View:
    """SVG in drawing inches. h = offset from the building centerline, + toward EAST, drawn
    on the LEFT (we're looking south). z = height above the paver floor / grade."""
    def __init__(self):
        self.s, self.n_clip = [], 0

    def P(self, h, z): return (-h - H0, Z1 - z)

    def poly(self, pts, cls, extra=""):
        self.s.append('<polygon points="%s" class="%s"%s/>' % (
            " ".join("%.2f,%.2f" % self.P(*p) for p in pts), cls, extra))

    def box(self, h1, z1, h2, z2, cls, extra=""):
        self.poly([(h1, z1), (h2, z1), (h2, z2), (h1, z2)], cls, extra)

    def ln(self, a, b, cls):
        self.s.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" class="%s"/>' % (*self.P(*a), *self.P(*b), cls))

    def tx(self, h, z, s, cls="t", anchor="start", rot=0):
        u, v = self.P(h, z)
        tr = f' transform="rotate({rot} {u:.2f} {v:.2f})"' if rot else ""
        self.s.append(f'<text x="{u:.2f}" y="{v:.2f}" class="{cls}" text-anchor="{anchor}"{tr}>{escape(s)}</text>')

    def clip(self, pts):
        self.n_clip += 1
        cid = f"c{id(self)}_{self.n_clip}"
        self.s.append(f'<clipPath id="{cid}"><polygon points="%s"/></clipPath>' % " ".join(
            "%.2f,%.2f" % self.P(*p) for p in pts))
        return cid

    def battens(self, h_from, h_to, spacing, z_lo, outline, cls):
        cid = self.clip(outline)
        self.s.append(f'<g clip-path="url(#{cid})">')
        h, step = h_from, spacing if h_to > h_from else -spacing
        while (h - h_to) * step < 0:
            self.box(h - 1.25, z_lo, h + 1.25, 400, cls); h += step
        self.s.append("</g>")

    def label(self, target, at, s, anchor="start", tail=False):
        """Leader from target to the text's start (or, with tail=True, to its end)."""
        if tail:
            end = (at[0] - len(s) * 2.55 - 1.5, at[1] + 1.2)    # h decreases to the right
        else:
            end = (at[0] + (1.5 if anchor == "end" else -1.5), at[1] + 1.2)
        self.ln(target, end, "lead")
        self.tx(*at, s, "t", anchor)

    def hdim(self, h1, h2, z, ref_z=None):
        for h in (h1, h2):
            if ref_z is not None: self.ln((h, ref_z), (h, z - 2), "ext")
        self.ln((h1, z), (h2, z), "dim")
        for h in (h1, h2):
            u, v = self.P(h, z)
            self.s.append(f'<line x1="{u - 2:.2f}" y1="{v + 2:.2f}" x2="{u + 2:.2f}" y2="{v - 2:.2f}" class="tick"/>')
        self.tx((h1 + h2) / 2, z + 1.8, ftin(h2 - h1), "d", "middle")

    def level(self, h_from, z, s, h_tag):
        self.ln((h_from, z), (h_tag + 3, z), "lvl")
        u, v = self.P(h_tag, z)
        self.s.append(f'<polygon points="{u:.2f},{v:.2f} {u - 2.6:.2f},{v - 4:.2f} {u + 2.6:.2f},{v - 4:.2f}" class="lvltri"/>')
        self.tx(h_tag - 5, z + 1.2, f"{ftin(z)}  {s}", "d")

    def svg(self):
        w, h = H1 - H0, Z1 - Z0
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w / SCALE:.3f}in" height="{h / SCALE:.3f}in" '
                f'viewBox="0 0 {w:.2f} {h:.2f}">' + "".join(self.s) + "</svg>")


def existing_back(v):
    """Stack and cupola, over the center bay (behind the north wall)."""
    cw, ce = CUPOLA_W / 2, RIDGE_TOP + CUPOLA_WALL
    cpk = ce + cw * CUPOLA_PITCH
    v.box(-STACK_OD / 2, roof_at(STACK_OD / 2), STACK_OD / 2, STACK_TOP, "stack")
    v.poly([(-12, STACK_TOP + 2), (12, STACK_TOP + 2), (8, STACK_TOP + 6), (-8, STACK_TOP + 6)], "stack")
    v.poly([(cw, roof_at(cw)), (cw, ce), (-cw, ce), (-cw, roof_at(cw))], "ex-wall")
    v.battens(-cw + 4, cw, 8, 0, [(cw, roof_at(cw)), (cw, ce), (-cw, ce), (-cw, roof_at(cw))], "ex-bat")
    oh = CUPOLA_OH
    v.poly([(cw + oh, ce - oh * CUPOLA_PITCH), (0, cpk), (-cw - oh, ce - oh * CUPOLA_PITCH),
            (-cw - oh, ce - oh * CUPOLA_PITCH + 5), (0, cpk + 5), (cw + oh, ce - oh * CUPOLA_PITCH + 5)], "ex-roof")
    v.box(-8, ce - 14, 8, ce - 4, "louver")


def existing_wall(v):
    gable = [(HW, 0), (HW, eb(0)), (0, MAIN_PEAK), (-HW, eb(0)), (-HW, 0)]
    v.poly(gable, "ex-wall")
    v.battens(HW - 5, -HW, 10, 0, gable, "ex-bat")
    v.box(-WIN_W / 2, WIN_SILL, WIN_W / 2, WIN_HEAD, "win")
    for k in (1, 2):
        v.ln((-WIN_W / 2 + k * WIN_W / 3, WIN_SILL), (-WIN_W / 2 + k * WIN_W / 3, WIN_HEAD), "mun")
    v.ln((-WIN_W / 2, (WIN_SILL + WIN_HEAD) / 2), (WIN_W / 2, (WIN_SILL + WIN_HEAD) / 2), "mun")
    v.box(-WIN_W / 2 - 1.5, WIN_SILL - 1.5, WIN_W / 2 + 1.5, WIN_SILL, "sill")


def existing_rake(v):
    """Main roof's north rake edge (11" proud of the wall): rafter, battens, shakes."""
    t = HW + EX_OVERHANG
    for s in (1, -1):
        v.poly([(0, MAIN_PEAK), (s * t, eb(EX_OVERHANG)), (s * t, ex_top(EX_OVERHANG)),
                (0, MAIN_PEAK + vdepth(EX_RAFTER_D, MAIN_PITCH))], "ex-raft")
        v.poly([(0, MAIN_PEAK + vdepth(EX_RAFTER_D, MAIN_PITCH)), (s * t, ex_top(EX_OVERHANG)),
                (s * t, ex_roof(EX_OVERHANG)), (0, RIDGE_TOP)], "ex-roof")


def awning(v):
    """Phase 1 east awning, north end wall (flush with the building's north wall)."""
    H = lambda u: HW + u                          # east = +h
    top = lambda u: rb(u)
    outline = [(H(0), 0), (H(EB_OUT), 0), (H(EB_OUT), top(EB_OUT)), (H(0), top(0))]
    v.poly(outline, "p1-wall")
    v.battens(H(EB_OUT / 16), H(EB_OUT), EB_OUT / 8, KICK[1], outline, "p1-bat")
    v.box(H(0), 0, H(EB_OUT), KICK[1], "p1-kick")
    v.box(H(DEPTH - POST / 2), KICK[1], H(POST_OUT), EAVE_BEAM_BOT, "hidden")
    v.box(H(EB_IN), EAVE_BEAM_BOT, H(EB_OUT), EAVE_BEAM_TOP, "p1")
    # end rafter (outside the existing wall), roofing, fascia on the tail
    v.poly([(H(0), rb(0)), (H(TAIL), rb(TAIL)), (H(TAIL), new_top(TAIL)), (H(0), new_top(0))], "p1")
    v.poly([(H(0), new_top(0)), (H(TAIL), new_top(TAIL)), (H(TAIL), new_roof(TAIL)),
            (H(0), new_roof(0))], "p1-roof")
    v.box(H(TAIL), new_top(TAIL) - 7.25, H(TAIL + 0.75), new_top(TAIL), "p1")


def porch(v):
    """Phase 2 north porch, front (gable) face."""
    # behind the front: rafter ties, seen through the gable
    v.box(-TIE_U, TIE_Z - 2.75, TIE_U, TIE_Z + 2.75, "p2-back")
    for s in (1, -1):
        e, b = s * EAVE_POST_U, s * BU
        for x in (e, b):                                        # stone pier + bluestone cap
            v.box(x - PIER / 2, 0, x + PIER / 2, PIER_TOP - 2, "pier")
            v.box(x - 11, PIER_TOP - 2, x + 11, PIER_TOP, "cap")
            v.box(x - 3.5, PIER_TOP, x + 3.5, PIER_TOP + 1, "base")
        v.box(e - POST / 2, PIER_TOP + 1, e + POST / 2, EAVE_BEAM_TOP, "p2")
        v.box(b - POST / 2, PIER_TOP + 1, b + POST / 2, BREAK_BEAM_BOT, "p2")
        ob = s * (HW + EB_OUT)                                  # eave beam, let into the post
        v.box(ob, EAVE_BEAM_BOT, ob - s * EAVE_BEAM[0], EAVE_BEAM_TOP, "p2")
        v.box(b - BREAK_BEAM[0] / 2, BREAK_BEAM_BOT, b + BREAK_BEAM[0] / 2, BREAK_Z, "p2")
        t = s * TAIL_U                                          # fly rafter + rake board
        v.poly([(0, RIDGE_RB), (t, porch_rb(TAIL_U)), (t, porch_top(TAIL_U)), (0, porch_top(0))], "p2")
        v.poly([(0, porch_top(0)), (t, porch_top(TAIL_U)), (t, porch_top(TAIL_U) + ROOF_V),
                (0, porch_top(0) + ROOF_V)], "p2-roof")
        v.box(t, porch_top(TAIL_U) - 7.25, t + s * 0.75, porch_top(TAIL_U), "p2")
    v.box(-0.75, porch_top(0) - 11.25, 0.75, porch_top(0), "p2")  # ridge board end


def page(phase):
    v = View()
    v.ln((H0 + 10, 0), (H1 - 10, 0), "grade")
    v.box(H0 + 10, -6, H1 - 10, 0, "earth")
    existing_back(v)
    existing_wall(v)
    awning(v)
    existing_rake(v)
    if phase == 2:
        porch(v)
    L = -TAIL_U - 30                                            # label column, west (right)
    R = TAIL_U + 16                                             # level tags column
    # labels
    if phase == 1:
        v.label((-STACK_OD / 2, STACK_TOP - 10), (-40, STACK_TOP - 6), 'STACK, 12" ID INSUL., TOP ~' + ftin(STACK_TOP))
        v.label((-CUPOLA_W / 2, RIDGE_TOP + 16), (-60, RIDGE_TOP + 30), "EXIST. CUPOLA (SIZE EST. FROM PHOTOS)")
        v.label((-HW + 20, eb(-20) + 4), (-HW - 20, MAIN_PEAK - 6), "EXIST. CEDAR SHAKES ON 2\" BATTENS, 8.6:12")
        v.label((-HW + 15, 60), (-HW - 20, 74), "EXIST. 1x BOARD + BATTEN")
        v.label((-WIN_W / 2, WIN_HEAD - 6), (-HW - 20, 54), 'EXIST. WINDOW 53" W (HEIGHTS EST.)')
        col = TAIL_U + 12                                       # east-side label column, top left
        # longest text on top so each leader drops clear of the labels below it
        v.label((HW + 35, 70), (col, 232), "AWNING END WALL, 1x10 B + 1x3 BATTEN", tail=True)
        v.label((HW + 50, new_roof(50)), (col, 222), "3:12 ASPHALT SHINGLE", tail=True)
        v.label((HW + DEPTH, 50), (col, 212), "6x6 POST A4 (HIDDEN)", tail=True)
        v.label((HW + EB_OUT - 1, EAVE_BEAM_TOP - 3), (col, 202), "DBL 2x10 EAVE BEAM", tail=True)
        v.tx(HW + EB_OUT / 2, 3, "PT KICKBOARD", "t", "middle")
    else:
        v.label((0, STACK_TOP - 10), (-30, STACK_TOP - 6), 'STACK, TOP ~' + ftin(STACK_TOP))
        v.label((-HW + 20, eb(-20) + 4), (-HW - 20, MAIN_PEAK - 6), "EXIST. ROOF; TRIM RAKE OVERHANG")
        v.tx(-HW - 20, MAIN_PEAK - 12, f"FROM ~59\" OFF CENTER OUT")
        v.label((-40, porch_top(40) + 1), (-HW - 26, 140), "PORCH 3:12 ASPHALT SHINGLE, EAVE TO RIDGE")
        v.label((-BU, BREAK_BEAM_BOT + 6), (-HW - 60, 112), "DBL 2x12 PURLIN (ENGINEER)")
        v.label((-30, TIE_Z), (-30, TIE_Z - 14), '2x6 TIES @ 10\'')
        v.label((-(HW + EB_OUT) + 1, EAVE_BEAM_BOT + 3), (-TAIL_U - 4, 76), "DBL 2x10 EAVE BEAM")
        v.label((-EAVE_POST_U, 55), (-TAIL_U - 4, 58), "6x6 POST")
        v.label((-EAVE_POST_U - PIER / 2, 12), (-TAIL_U - 4, 18), '20" STONE PIER,')
        v.tx(-TAIL_U - 4, 12, 'BLUESTONE CAP')
        v.label((-WIN_W / 2 + 5, WIN_HEAD - 4), (-40, 96), "EXIST. WINDOW")
        v.label((HW + 35, 70), (TAIL_U + 12, 150), "AWNING END WALL (PH. 1)", tail=True)
        for m, h in (("N1", -EAVE_POST_U), ("N2", -BU), ("N3", BU), ("N4", EAVE_POST_U)):
            v.tx(h, -16, m, "mark", "middle")
    # levels
    lv = [(0, "PAVERS / GRADE")]
    if phase == 1:
        lv += [(EAVE_BEAM_BOT, "UNDER EAVE BEAM"), (eb(0), "EXIST. EAVE AT WALL"), (RIDGE_TOP, "EXIST. RIDGE"),
               (STACK_TOP, "STACK (APPROX.)")]
    else:
        lv += [(PIER_TOP, "PIER CAP"), (EAVE_BEAM_BOT, "UNDER EAVE BEAM"), (BREAK_BEAM_BOT, "UNDER PURLIN"),
               (porch_top(0) + ROOF_V, "PORCH RIDGE"), (RIDGE_TOP, "EXIST. RIDGE")]
    for z, s in lv:
        v.level(-TAIL_U - 4 if phase == 2 else -HW - 12, z, s, -R)
    # horizontal dims (below grade line)
    if phase == 1:
        v.hdim(-HW, HW, -14)
        v.hdim(HW, HW + DEPTH, -14)
        v.hdim(HW + EB_OUT, HW + TAIL, -24)
    else:
        xs = [-EAVE_POST_U, -BU, BU, EAVE_POST_U]
        for a, b in zip(xs, xs[1:]):
            v.hdim(a, b, -24)
        v.hdim(-TAIL_U, TAIL_U, -32)
    return v.svg()


TITLES = {1: ("North Elevation - After Phase 1", "Existing sap house with the enclosed east awning. "
              "The awning roof stops at the north wall line until the porch continues it."),
          2: ("North Elevation - After Phase 2", "North porch added: one 3:12 gable, eave to ridge, "
              "its east skirt continuing the awning roof. Back posts N5-N7 and A4 are hidden behind N1-N4.")}
pages = "".join(f"""<div class="page"><div class="hdr"><div><h1>{TITLES[p][0]}</h1>
<div class="sub">{escape(TITLES[p][1])} Looking south: <b>east is on the left</b>. Scale 1/4" = 1'-0".</div></div>
<div class="key"><span class="sw ex"></span>Existing <span class="sw k1"></span>Phase 1 <span class="sw k2"></span>Phase 2</div></div>
{page(p)}
<div class="foot">Generated by north_elevation.py from make_awning_scr.py. Window sill/head and cupola size are
estimated from the 2026-08-22 photos. Heights are from the paver floor.</div></div>""" for p in (1, 2))

html = f"""<!doctype html><html><head><meta charset="utf-8"><title>Sap House North Elevation</title>
<style>
@page {{ size: letter landscape; margin: 0.35in; }}
body {{ font-family: Arial, Helvetica, sans-serif; margin: 0; color: #000; background: #fff; }}
.page {{ page-break-after: always; }} .page:last-child {{ page-break-after: auto; }}
.hdr {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 12pt; }}
h1 {{ font-size: 14pt; margin: 0 0 2pt; }} .sub {{ font-size: 8pt; color: #333; max-width: 7.4in; }}
.key {{ font-size: 8pt; white-space: nowrap; }} .foot {{ font-size: 7pt; color: #555; }}
.sw {{ display: inline-block; width: 9pt; height: 9pt; vertical-align: -1pt; margin: 0 2pt 0 8pt; border: 0.5pt solid #000; }}
.sw.ex {{ background: #e8e4dc; }} .sw.k1 {{ background: #f6d9b8; }} .sw.k2 {{ background: #cfe0f0; }}
svg {{ display: block; margin: 2pt auto 0; }} svg text {{ font-family: Arial, Helvetica, sans-serif; }}
polygon {{ stroke-linejoin: round; }}
.ex-wall {{ fill: #e8e4dc; stroke: #000; stroke-width: 0.6; }} .ex-bat {{ fill: #d4cec2; stroke: #8a8578; stroke-width: 0.2; }}
.ex-raft {{ fill: #b5aea0; stroke: #000; stroke-width: 0.5; }} .ex-roof {{ fill: #6d6a64; stroke: #000; stroke-width: 0.5; }}
.stack {{ fill: #9aa0a6; stroke: #000; stroke-width: 0.5; }} .louver {{ fill: #555; stroke: none; }}
.win {{ fill: #c9d6df; stroke: #000; stroke-width: 0.6; }} .mun {{ stroke: #000; stroke-width: 0.6; }}
.sill {{ fill: #b5aea0; stroke: #000; stroke-width: 0.4; }}
.p1, .p1-wall {{ fill: #f6d9b8; stroke: #8a4510; stroke-width: 0.6; }} .p1-bat {{ fill: #ecc49a; stroke: #8a4510; stroke-width: 0.2; }}
.p1-kick {{ fill: #c9a27a; stroke: #8a4510; stroke-width: 0.6; }} .p1-roof {{ fill: #4f4a45; stroke: #000; stroke-width: 0.5; }}
.p2 {{ fill: #cfe0f0; stroke: #1f4f80; stroke-width: 0.6; }} .p2-back {{ fill: #e4eef8; stroke: #1f4f80; stroke-width: 0.4; }}
.p2-roof {{ fill: #3c4650; stroke: #000; stroke-width: 0.5; }}
.pier {{ fill: #bdb8ae; stroke: #000; stroke-width: 0.6; }} .cap {{ fill: #7d8b95; stroke: #000; stroke-width: 0.5; }}
.base {{ fill: #888; stroke: #000; stroke-width: 0.3; }}
.hidden {{ fill: none; stroke: #8a4510; stroke-width: 0.5; stroke-dasharray: 3 2; }}
.grade {{ stroke: #000; stroke-width: 1.2; }} .earth {{ fill: #efece6; stroke: none; }}
.lead {{ stroke: #000; stroke-width: 0.3; }} .ext {{ stroke: #555; stroke-width: 0.3; }}
.dim {{ stroke: #000; stroke-width: 0.45; }} .tick {{ stroke: #000; stroke-width: 0.7; }}
.lvl {{ stroke: #777; stroke-width: 0.3; stroke-dasharray: 2 2; }} .lvltri {{ fill: #000; }}
.t {{ font-size: 4.6px; }} .d {{ font-size: 4.6px; }} .mark {{ font-size: 7px; font-weight: bold; }}
</style></head><body>{pages}</body></html>"""
out = HERE / "north-elevation.html"
out.write_text(html, encoding="utf-8")
print(out)
