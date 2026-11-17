"""Post-placement floor plan for the sap house extension (east awning + north porch).

Pulls the geometry straight from make_awning_scr.py (single source of truth: change a
parameter there, re-run both) and writes post-layout.html: page 1 is a dimensioned plan
of the post / footing centers against the existing building, page 2 is a stake-out table
with two tape distances from building corners for every post.

Print to PDF with headless Chrome:
  chrome --headless=new --no-pdf-header-footer --print-to-pdf=post-layout.pdf post-layout.html
"""
import contextlib
import io
import runpy
from html import escape
from math import hypot
from pathlib import Path

HERE = Path(__file__).parent
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(str(HERE / "make_awning_scr.py"))

CX, POST, PIER = g["CX"], g["POST"], g["PIER"]
W_FACE, E_FACE, N_FACE, S_FACE = g["W_FACE"], g["E_FACE"], g["N_FACE"], g["S_FACE"]
assert g["AWNING_SIDE"] == "east"
mx = lambda x: 2 * CX - x                       # generator's plan is drawn west, then mirrored
WX, BWX, BEX, EX = (mx(x) for x in g["front_posts_x"])  # real x, east..west
WX, BWX, BEX, EX = sorted((WX, BWX, BEX, EX))           # west -> east
PY = g["PY"]
ay = g["west_posts_y"][:4]                      # awning post y, south -> north
BACK_Y = N_FACE + POST / 2
assert abs(E_FACE + g["DEPTH"] - EX) < 0.01    # east post line, 6' off the east face

# mark, x, y, phase, footing
TUBE = "12\" tube, ~3' deep, belled base"
PIERF = "20\" stone pier on 30\"x30\" footing"
posts = [
    ("A1", EX, ay[0], 1, TUBE),
    ("A2", EX, ay[1], 1, TUBE),
    ("A3", EX, ay[2], 1, TUBE),
    ("A4", EX, ay[3], 1, TUBE + " (carries porch later - engineer)"),
    ("N1", WX, PY, 2, PIERF),
    ("N2", BWX, PY, 2, PIERF),
    ("N3", BEX, PY, 2, PIERF),
    ("N4", EX, PY, 2, PIERF),
    ("N5", WX, BACK_Y, 2, PIERF),
    ("N6", BWX, BACK_Y, 2, TUBE),
    ("N7", BEX, BACK_Y, 2, TUBE),
]
CORNERS = {"NW": (W_FACE, N_FACE), "NE": (E_FACE, N_FACE),
           "SE": (E_FACE, S_FACE), "SW": (W_FACE, S_FACE)}


def ftin(v):
    v = abs(v)
    ft, inch = divmod(round(v * 8) / 8, 12)
    whole, frac = int(inch), inch - int(inch)
    fr = {0: "", 0.125: " 1/8", 0.25: " 1/4", 0.375: " 3/8", 0.5: " 1/2", 0.625: " 5/8",
          0.75: " 3/4", 0.875: " 7/8"}[round(frac * 8) / 8]
    s = f'{whole}{fr}"'
    return f"{int(ft)}'-{s}" if ft else s


def offsets(x, y):
    """Square offsets from the nearest building face lines (what you'd pull with a tape)."""
    if x > E_FACE:
        ex = f"{ftin(x - E_FACE)} E of east face"
    elif x < W_FACE:
        ex = f"{ftin(W_FACE - x)} W of west face"
    else:
        ex = (f"{ftin(x - W_FACE)} E of west face line" if x < CX
              else f"{ftin(E_FACE - x)} W of east face line")
    if y > N_FACE:
        ey = f"{ftin(y - N_FACE)} N of north face"
    else:
        ey = f"{ftin(N_FACE - y)} S of north face line"
    return ex, ey


def refs(mark, y):
    return ("NE", "SE") if mark.startswith("A") and y < N_FACE else ("NW", "NE")


# ===== Page 1: plan (SVG, drawing inches, scale 1:SCALE) ===================
SCALE = 64                                       # 3/16" = 1'-0"
x0, x1 = W_FACE - g["DEPTH"] - 60, E_FACE + g["DEPTH"] + 80
y0, y1 = S_FACE - 40, PY + 60
W_IN, H_IN = (x1 - x0) / SCALE, (y1 - y0) / SCALE
sv = []
P = lambda x, y: (x - x0, y1 - y)                # svg coords, y down
def ln(a, b, cls): sv.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" class="%s"/>' % (*P(*a), *P(*b), cls))
def rect(xa, ya, xb, yb, cls):
    (u, v), (u2, v2) = P(min(xa, xb), max(ya, yb)), P(max(xa, xb), min(ya, yb))
    sv.append(f'<rect x="{u:.2f}" y="{v:.2f}" width="{u2 - u:.2f}" height="{v2 - v:.2f}" class="{cls}"/>')
def circ(x, y, r, cls): sv.append('<circle cx="%.2f" cy="%.2f" r="%.2f" class="%s"/>' % (*P(x, y), r, cls))
def tx(x, y, s, cls="t", anchor="middle", rot=0):
    u, v = P(x, y)
    tr = f' transform="rotate({rot} {u:.2f} {v:.2f})"' if rot else ""
    sv.append(f'<text x="{u:.2f}" y="{v:.2f}" class="{cls}" text-anchor="{anchor}"{tr}>{escape(s)}</text>')

def dim(a, b, off, horiz):
    """Linear dimension a->b, offset line at `off` (y for horizontal, x for vertical)."""
    if horiz:
        pa, pb = (a[0], off), (b[0], off)
        ln(a, (a[0], off), "ext"); ln(b, (b[0], off), "ext")
        ln(pa, pb, "dim"); tx((a[0] + b[0]) / 2, off + 2.5, ftin(b[0] - a[0]), "d")
    else:
        pa, pb = (off, a[1]), (off, b[1])
        ln(a, (off, a[1]), "ext"); ln(b, (off, b[1]), "ext")
        ln(pa, pb, "dim"); tx(off - 2.5, (a[1] + b[1]) / 2, ftin(b[1] - a[1]), "d", rot=-90)
    for p in (pa, pb):
        u, v = P(*p)
        sv.append(f'<line x1="{u - 2.5:.2f}" y1="{v + 2.5:.2f}" x2="{u + 2.5:.2f}" y2="{v - 2.5:.2f}" class="tick"/>')

# existing building
rect(W_FACE, S_FACE, E_FACE, N_FACE, "bldg")
for px in (CX - (g["IN_W"] / 2 - 3.75), CX + (g["IN_W"] / 2 - 3.75)):
    for py in g["FRAME_ROWS_Y"]:
        rect(px - 3.75, py - 3.75, px + 3.75, py + 3.75, "expost")
tx(CX, (S_FACE + N_FACE) / 2 + 6, "EXISTING SAP HOUSE", "lbl")
tx(CX, (S_FACE + N_FACE) / 2 - 6, f"{ftin(E_FACE - W_FACE)} x {ftin(N_FACE - S_FACE)} outside", "sm")
for k, (cx_, cy_) in CORNERS.items():
    circ(cx_, cy_, 2.2, "ref")
    tx(cx_ + (-5 if cx_ < CX else 5), cy_ + (5 if cy_ > 0 else -9), k, "ref", "end" if cx_ < CX else "start")

# new roof outlines (light), for orientation
WF, EF, PF = mx(g["EF"]), mx(g["WF"]), g["PF"]
S_WALL, RAKE = g["S_WALL"], g["RAKE"]
sv.append('<polyline class="roof" points="%s"/>' % " ".join(
    "%.2f,%.2f" % P(*p) for p in [(E_FACE, S_WALL - RAKE), (EF, S_WALL - RAKE), (EF, PF), (WF, PF), (WF, N_FACE), (W_FACE, N_FACE)]))
rect(E_FACE, S_WALL, EX + POST / 2 + 1, N_FACE, "encl")
tx((E_FACE + EX) / 2, (S_WALL + N_FACE) / 2, "EAST AWNING", "lbl", rot=-90)
tx((E_FACE + EX) / 2 + 12, (S_WALL + N_FACE) / 2, "PHASE 1 - ENCLOSED", "sm", rot=-90)
tx(CX, N_FACE + 52, "NORTH PORCH - PHASE 2", "lbl")

# footings + posts
for m, x, y, ph, f in posts:
    if "pier" in f:
        rect(x - PIER / 2, y - PIER / 2, x + PIER / 2, y + PIER / 2, "pier")
    else:
        circ(x, y, 6, "tube")
    rect(x - POST / 2, y - POST / 2, x + POST / 2, y + POST / 2, f"post p{ph}")
    ln((x - 9, y), (x + 9, y), "cl"); ln((x, y - 9), (x, y + 9), "cl")
    lx = x + (16 if x > CX else -16)
    ly = y + (14 if y > N_FACE - 10 else 0)
    if m == "A4": lx, ly = x + 16, y - 10
    tx(lx, ly - 2.5, m, "mark", "start" if x > CX else "end")

# dimensions: awning
dE = EX + 38
dim((E_FACE, S_FACE - 14), (EX, S_FACE - 14), S_FACE - 26, True)       # 72" off east face
ln((EX, ay[0]), (EX, S_FACE - 14), "ext")
chain = ay[::-1]                                # A4 -> A1 (A4's 2 3/4" off the N face is a note)
tx(EX + 16, ay[3] - 20, f'{ftin(N_FACE - ay[3])} S of N face', "sm", "start")
for a, b in zip(chain, chain[1:]):
    dim((EX, b), (EX, a), dE, False)
dim((E_FACE, S_FACE), (E_FACE, ay[0]), dE + 22, False)                 # south face to A1
ln((E_FACE, N_FACE), (dE + 6, N_FACE), "ext")
# porch: front chain + depth
dim((WX, PY), (BWX, PY), PY + 22, True)
dim((BWX, PY), (BEX, PY), PY + 22, True)
dim((BEX, PY), (EX, PY), PY + 22, True)
dim((WX, PY), (W_FACE, N_FACE), PY + 40, True)
dim((E_FACE, N_FACE), (EX, PY), PY + 40, True)
dim((WX, N_FACE), (WX, PY), WX - 30, False)
ln((W_FACE, N_FACE), (WX - 36, N_FACE), "ext")
tx(CX, BACK_Y + 8, f'N5, N6, N7 centers {ftin(BACK_Y - N_FACE)} N of north face (tight to siding)', "sm")

# north arrow + scale
na = (x0 + 20, y1 - 30)
sv.append('<polygon class="na" points="%.2f,%.2f %.2f,%.2f %.2f,%.2f"/>' % (*P(na[0], na[1] + 14), *P(na[0] - 5, na[1]), *P(na[0] + 5, na[1])))
tx(na[0], na[1] + 18, "N", "lbl")
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_IN:.3f}in" height="{H_IN:.3f}in" '
       f'viewBox="0 0 {x1 - x0:.2f} {y1 - y0:.2f}">' + "".join(sv) + "</svg>")

# ===== Page 2: stake-out table ===========================================
rows = []
for m, x, y, ph, f in posts:
    ex, ey = offsets(x, y)
    r1, r2 = refs(m, y)
    d1 = hypot(x - CORNERS[r1][0], y - CORNERS[r1][1])
    d2 = hypot(x - CORNERS[r2][0], y - CORNERS[r2][1])
    rows.append(f"<tr><td class='m'>{m}</td><td>{ph}</td><td>{escape(ex)}</td><td>{escape(ey)}</td>"
                f"<td>{r1} {ftin(d1)}</td><td>{r2} {ftin(d2)}</td><td>{escape(f)}</td></tr>")
diag = ftin(hypot(EX - W_FACE, PY - N_FACE))
html = f"""<!doctype html><html><head><meta charset="utf-8"><title>Sap House Post Layout</title>
<style>
@page {{ size: letter portrait; margin: 0.4in; }}
body {{ font-family: Arial, Helvetica, sans-serif; margin: 0; color: #000; background: #fff; }}
.page {{ page-break-after: always; }}
.page:last-child {{ page-break-after: auto; }}
h1 {{ font-size: 15pt; margin: 0 0 2pt; }} .sub {{ font-size: 8.5pt; color: #333; margin-bottom: 6pt; }}
svg text {{ font-family: Arial, Helvetica, sans-serif; }}
.bldg {{ fill: #eee; stroke: #000; stroke-width: 1.2; }} .expost {{ fill: #888; stroke: none; }}
.roof {{ fill: none; stroke: #999; stroke-width: 0.6; stroke-dasharray: 6 4; }}
.encl {{ fill: #fff6e0; stroke: #b07a00; stroke-width: 0.6; }}
.post {{ stroke: #000; stroke-width: 0.6; }} .p1 {{ fill: #d35400; }} .p2 {{ fill: #2471a3; }}
.tube {{ fill: none; stroke: #000; stroke-width: 0.6; stroke-dasharray: 2 1.5; }}
.pier {{ fill: #ddd; stroke: #000; stroke-width: 0.6; }}
.cl {{ stroke: #c00; stroke-width: 0.4; }}
.ext {{ stroke: #555; stroke-width: 0.35; }} .dim {{ stroke: #000; stroke-width: 0.5; }} .tick {{ stroke: #000; stroke-width: 0.7; }}
.ref {{ fill: #c00; font-size: 6.5px; font-weight: bold; }}
.t, .d {{ font-size: 6px; }} .sm {{ font-size: 5.5px; fill: #444; }} .lbl {{ font-size: 7.5px; font-weight: bold; }}
.mark {{ font-size: 9px; font-weight: bold; }} .na {{ fill: #000; }}
.legend {{ font-size: 8.5pt; margin-top: 4pt; }} .sw {{ display: inline-block; width: 9pt; height: 9pt; vertical-align: -1pt; margin: 0 3pt 0 10pt; border: 0.5pt solid #000; }}
table {{ border-collapse: collapse; font-size: 9pt; width: 100%; margin-top: 6pt; }}
th, td {{ border: 0.5pt solid #000; padding: 3pt 4pt; text-align: left; vertical-align: top; }}
th {{ background: #eee; }} td:nth-child(5), td:nth-child(6) {{ white-space: nowrap; }} td.m {{ font-weight: bold; }}
ul {{ font-size: 9pt; padding-left: 14pt; }} li {{ margin-bottom: 3pt; }}
</style></head><body>
<div class="page">
<h1>Sap House Extension - Post Layout</h1>
<div class="sub">Post / footing centers. Scale 3/16" = 1'-0" (1:{SCALE}). All dimensions to post centers from the
outside face of the existing siding. Generated from make_awning_scr.py; see page 2 for stake-out distances.</div>
{svg}
<div class="legend"><span class="sw" style="background:#d35400"></span>Phase 1 post (6x6)
<span class="sw" style="background:#2471a3"></span>Phase 2 post (6x6)
<span class="sw" style="background:#ddd"></span>20" stone pier
<span class="sw" style="border-style:dashed"></span>12" sonotube
<span class="sw" style="background:#888"></span>existing 7-1/2" post</div>
</div>
<div class="page">
<h1>Stake-Out Table</h1>
<div class="sub">Two ways to set each stake: square offsets from the face lines, or swing two tapes from the
building corners (red dots on page 1). Use one as the check on the other.</div>
<table><tr><th>Post</th><th>Ph.</th><th>East-west</th><th>North-south</th><th>Tape 1</th><th>Tape 2</th><th>Footing</th></tr>
{''.join(rows)}</table>
<ul>
<li><b>Measure from the siding</b> (board face, not batten), and stretch string lines off the walls rather than
trusting one corner: the building was measured with magicplan plus field corrections, so check it's square first
(outside diagonals should both be {ftin(hypot(E_FACE - W_FACE, N_FACE - S_FACE))}).</li>
<li><b>East awning line:</b> string a line {ftin(EX - E_FACE)} off the east face, parallel to it. A1-A4 sit on it at
{ftin(ay[1] - ay[0])} centers. A1 lines up with the existing post row at the south edge of the center bay.
A4's outside face is flush with the north wall line.</li>
<li><b>Porch front line:</b> {ftin(PY - N_FACE)} off the north face. Check: NW corner to N4 and NE corner to N1 should
both read {diag}.</li>
<li><b>N6 / N7</b> sit tight to the north siding, centered {ftin(W_FACE - BWX)} outside each wall line (under the
purlins). Freestanding on their own footing, lagged to the corner frame for lateral tie only.</li>
<li><b>Tubes:</b> hole about 3' deep, tube hung a few inches off the bottom so the concrete flows out into a
20-24" base; brace the tube at grade (engineer, 2026-11-04). <b>Piers:</b> pier footings are still pending the
engineer - stake the centers now, size later.</li>
<li>The trench drain (12" x 43", hydrant to arch) and the French drain along the east drip line are dug with the
Phase 1 footings; keep the drain trench clear of the tube holes.</li>
</ul>
</div>
</body></html>"""
out = HERE / "post-layout.html"
out.write_text(html, encoding="utf-8")
print(out)
for m, x, y, ph, f in posts:
    print(m, f"{x:8.2f} {y:8.2f}", *offsets(x, y))
