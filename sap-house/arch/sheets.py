"""Lay out the views recorded by make_arch_scr.py as print sheets: one Letter-landscape page
per view, drawn to a standard scale, with the view's tag legend under the drawing.

Writes an HTML file; print it to PDF with headless Chrome (see make_arch_scr.py's docstring).
"""
from html import escape
from math import ceil

PAGE_W, PAGE_H, MARGIN = 11.0, 8.5, 0.4          # inches, Letter landscape
HEADER_H, FOOTER_H = 0.65, 0.25
ROW_H = 0.17                                     # legend row height, inches
SCALES = [2, 3, 4, 6, 8, 12, 16, 24, 32]         # 1:N
SCALE_NAME = {2: '6" = 1\'-0"', 3: '4" = 1\'-0"', 4: '3" = 1\'-0"', 6: '2" = 1\'-0"',
              8: '1-1/2" = 1\'-0"', 12: '1" = 1\'-0"', 16: '3/4" = 1\'-0"',
              24: '1/2" = 1\'-0"', 32: '3/8" = 1\'-0"'}


def ftin(v):
    v = abs(v)
    ft, inch = divmod(round(v * 8) / 8, 12)
    whole, frac = int(inch), inch - int(inch)
    fr = {0: "", 0.125: " 1/8", 0.25: " 1/4", 0.375: " 3/8", 0.5: " 1/2", 0.625: " 5/8",
          0.75: " 3/4", 0.875: " 7/8"}[round(frac * 8) / 8]
    s = f'{whole}{fr}"'
    return f"{int(ft)}'-{s}" if ft else s


def dim_geom(a, b, at):
    """Horizontal or vertical linear dimension, like DIMLINEAR picks from the placement."""
    if abs(b[0] - a[0]) >= abs(b[1] - a[1]):
        y = at[1]
        return (a[0], y), (b[0], y), [(a, (a[0], y)), (b, (b[0], y))], abs(b[0] - a[0]), "h"
    x = at[0]
    return (x, a[1]), (x, b[1]), [(a, (x, a[1])), (b, (x, b[1]))], abs(b[1] - a[1]), "v"


def bbox(items, n):
    xs, ys = [], []
    for it in items:
        kind = it[1]
        if kind == "pl":
            for x, y in it[2]:
                xs.append(x); ys.append(y)
        elif kind == "tx":
            _, _, x, y, h, s = it
            h = max(h, 0.09 * n)
            xs += [x, x + len(s) * h * 0.6]; ys += [y, y + h]
        elif kind == "tag":
            _, _, x, y, _ = it
            r = max(1.0, 0.1 * n)
            xs += [x - r, x + r]; ys += [y - r, y + r]
        elif kind == "dim":
            p1, p2, ext, _, _ = dim_geom(*it[2:])
            for p in (p1, p2, *[q for e in ext for q in e]):
                xs.append(p[0]); ys.append(p[1])
            xs += [(p1[0] + p2[0]) / 2 - 0.6 * n, (p1[0] + p2[0]) / 2 + 0.6 * n]
            ys += [min(p1[1], p2[1]) - 0.15 * n, max(p1[1], p2[1]) + 0.15 * n]
    pad = 1.0
    return min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad


def svg(items, n):
    x0, y0, x1, y1 = bbox(items, n)
    w, h = x1 - x0, y1 - y0
    Y = lambda y: y1 - y                          # flip: model z up, SVG y down
    sw = 0.012 * n
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w / n:.3f}in" height="{h / n:.3f}in" '
           f'viewBox="{x0:.3f} 0 {w:.3f} {h:.3f}" font-family="Arial, sans-serif">']
    for it in items:
        c, kind = it[0], it[1]
        if kind == "pl":
            pts = " ".join(f"{x:.3f},{Y(y):.3f}" for x, y in it[2])
            tag = "polygon" if it[3] else "polyline"
            out.append(f'<{tag} points="{pts}" fill="none" stroke="{c}" stroke-width="{sw:.3f}" '
                       f'stroke-linejoin="round"/>')
        elif kind == "tx":
            _, _, x, y, hh, s = it
            fs = max(hh, 0.09 * n)
            out.append(f'<text x="{x:.3f}" y="{Y(y):.3f}" font-size="{fs:.3f}" fill="{c}">{escape(s)}</text>')
        elif kind == "tag":
            _, _, x, y, label = it
            r = max(1.0, 0.1 * n)
            out.append(f'<circle cx="{x:.3f}" cy="{Y(y):.3f}" r="{r:.3f}" fill="#fff" stroke="#a07800" '
                       f'stroke-width="{sw:.3f}"/>')
            out.append(f'<text x="{x:.3f}" y="{Y(y) + r * 0.35:.3f}" font-size="{r * (0.95 if len(label) < 3 else 0.75):.3f}" '
                       f'text-anchor="middle" font-weight="bold" fill="#000">{escape(label)}</text>')
        elif kind == "dim":
            p1, p2, ext, val, d = dim_geom(*it[2:])
            dc = "#555"
            for a, b in ext:
                out.append(f'<line x1="{a[0]:.3f}" y1="{Y(a[1]):.3f}" x2="{b[0]:.3f}" y2="{Y(b[1]):.3f}" '
                           f'stroke="{dc}" stroke-width="{sw * 0.6:.3f}"/>')
            out.append(f'<line x1="{p1[0]:.3f}" y1="{Y(p1[1]):.3f}" x2="{p2[0]:.3f}" y2="{Y(p2[1]):.3f}" '
                       f'stroke="{dc}" stroke-width="{sw * 0.8:.3f}"/>')
            t = 0.04 * n
            for p in (p1, p2):                      # architectural ticks
                out.append(f'<line x1="{p[0] - t:.3f}" y1="{Y(p[1]) + t:.3f}" x2="{p[0] + t:.3f}" '
                           f'y2="{Y(p[1]) - t:.3f}" stroke="{dc}" stroke-width="{sw * 1.5:.3f}"/>')
            fs = 0.09 * n
            mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
            if d == "h":
                out.append(f'<text x="{mx:.3f}" y="{Y(my) - 0.2 * fs:.3f}" font-size="{fs:.3f}" '
                           f'text-anchor="middle" fill="{dc}">{ftin(val)}</text>')
            else:
                out.append(f'<text transform="translate({mx - 0.25 * fs:.3f},{Y(my):.3f}) rotate(-90)" '
                           f'font-size="{fs:.3f}" text-anchor="middle" fill="{dc}">{ftin(val)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def pick_scale(items, max_w, max_h):
    for n in SCALES:
        x0, y0, x1, y1 = bbox(items, n)
        if (x1 - x0) / n <= max_w and (y1 - y0) / n <= max_h:
            return n
    return SCALES[-1]


def write_sheets(sheets, dest, project="Sap arch rebuild - school-arch", date="2026-11-10"):
    css = f"""@page {{ size: {PAGE_W}in {PAGE_H}in; margin: {MARGIN}in; }}
body {{ margin: 0; font-family: Arial, sans-serif; color: #111; }}
.sheet {{ width: {PAGE_W - 2 * MARGIN}in; height: {PAGE_H - 2 * MARGIN}in; display: flex;
  flex-direction: column; page-break-after: always; overflow: hidden; }}
.sheet:last-child {{ page-break-after: auto; }}
.head {{ height: {HEADER_H}in; border-bottom: 1.5px solid #000; display: flex;
  justify-content: space-between; align-items: flex-end; padding-bottom: 3px; }}
.head h1 {{ font-size: 15pt; margin: 0; }} .head .sub {{ font-size: 9pt; color: #333; }}
.head .scale {{ font-size: 10pt; text-align: right; }}
.draw {{ flex: 1; display: flex; align-items: center; justify-content: center; }}
.legend {{ columns: 2; column-gap: 0.3in; font-size: 8pt; line-height: {ROW_H}in; }}
.legend div {{ break-inside: avoid; }} .legend b {{ display: inline-block; width: 0.38in; }}
.foot {{ height: {FOOTER_H}in; border-top: 1px solid #999; font-size: 7.5pt; color: #555;
  display: flex; justify-content: space-between; align-items: center; }}"""
    pages = []
    names = list(sheets)
    for k, name in enumerate(names, 1):
        sh = sheets[name]
        rows = ceil(len(sh["legend"]) / 2)
        legend_h = rows * ROW_H + 0.1
        avail_w = PAGE_W - 2 * MARGIN
        avail_h = PAGE_H - 2 * MARGIN - HEADER_H - FOOTER_H - legend_h - 0.15
        n = pick_scale(sh["items"], avail_w, avail_h)
        legend = "".join(f"<div><b>{escape(t)}</b>{escape(s)}</div>" for t, s in sh["legend"])
        pages.append(f"""<div class="sheet">
<div class="head"><div><h1>{escape(sh['title'])}</h1><div class="sub">{escape(sh['subtitle'])}</div></div>
<div class="scale">Scale 1:{n} ({SCALE_NAME[n]})<br>Tags {name}1-{name}{len(sh['legend'])}</div></div>
<div class="draw">{svg(sh['items'], n)}</div>
<div class="legend">{legend}</div>
<div class="foot"><span>{escape(project)}</span><span>{date}</span><span>Sheet {k} of {len(names)}</span></div>
</div>""")
    dest.write_text(f"<!doctype html><meta charset='utf-8'><title>{escape(project)}</title>"
                    f"<style>{css}</style>\n" + "\n".join(pages), encoding="utf-8")
