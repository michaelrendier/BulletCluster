#!/usr/bin/env python3
"""make_field_svg.py (2026-11-20): a zoomable SVG vector field + subdued field lines over a scaffold composite.  Reads only; writes viewers/<name>.html and viewers/<name>.svg.
Everything is computed in the COMPOSITE'S OWN PIXEL FRAME: each object/cell is projected through the composite's sidecar WCS, and its direction is taken by projecting a point 1 arcsec
along its position angle, so registration is exact for any image orientation.  The data are AXIAL (an orientation mod 180 deg, no arrow in the data): the harpoon's head side is a
drawing convention (the head points toward the top of the image; horizontal ones point right), not a measured direction.
Vector = one thin shaft with a one-sided (harpoon) barb; length ~ amplitude (clamped); stroke width does not change with zoom, geometry does.  Field lines are streamlines of the
smoothed orientation field (doubled-angle average), drawn faint behind the vectors.  Cells with too few objects but inside the data footprint are FILLED from their neighbours and drawn fainter.
Usage: BulletCluster/.venv/bin/python make_field_svg.py --kind shear|pol --composite PNG --name NAME --title T [--catalog NPY | --pol JSON] [--cell ARCSEC] [--minn N] [--ref AMP] [--color #hex]"""
import sys, os, json, argparse, html, math
import numpy as np
from PIL import Image
ap = argparse.ArgumentParser()
ap.add_argument("--kind", required=True); ap.add_argument("--target", default=""); ap.add_argument("--composite", required=True); ap.add_argument("--name", required=True); ap.add_argument("--title", required=True)
ap.add_argument("--catalog"); ap.add_argument("--pol"); ap.add_argument("--cell", type=float, default=6.0); ap.add_argument("--minn", type=int, default=6); ap.add_argument("--ref", type=float, default=0.3)
ap.add_argument("--color", default="#c6ff00"); ap.add_argument("--linecolor", default=None); ap.add_argument("--note", default=""); ap.add_argument("--fill", type=int, default=1); ap.add_argument("--initial", default="data")
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__)); SC = os.path.dirname(HERE); OUT = os.path.join(HERE, "viewers"); os.makedirs(OUT, exist_ok=True)
comp = os.path.join(SC, a.composite); sc = json.load(open(comp + ".wcs.json")); W0, H0 = Image.open(comp).size
def tan_xy(ra, dec, ra0, dec0):
    ra, dec = np.radians(ra), np.radians(dec); r0, d0 = np.radians(ra0), np.radians(dec0)
    c = np.sin(d0) * np.sin(dec) + np.cos(d0) * np.cos(dec) * np.cos(ra - r0)
    return np.degrees(np.cos(dec) * np.sin(ra - r0) / c) * 3600, np.degrees((np.cos(d0) * np.sin(dec) - np.sin(d0) * np.cos(dec) * np.cos(ra - r0)) / c) * 3600
def to_pix(ra, dec):
    xi, eta = tan_xy(ra, dec, *sc["crval"]); cd = np.array(sc["cd"]) * 3600.0; d = np.linalg.solve(cd, np.vstack([xi, eta]))
    sh = sc.get("shift", [0, 0]); return sc["crpix"][0] - 1 + d[0] + sh[0], ((sc["H"] - 1 - (sc["crpix"][1] - 1 + d[1])) if sc["flipud"] else (sc["crpix"][1] - 1 + d[1])) + sh[1]
arcpix = float(np.sqrt(abs(np.linalg.det(np.array(sc["cd"]))))) * 3600
# ---- objects -> composite pixel frame: position, axis angle theta (pixel frame, y down), amplitude, weight
if a.kind == "shear":
    cat = np.load(a.catalog); ra, dec, amp, pa, wgt = cat[:, 0], cat[:, 1], cat[:, 2], np.radians(cat[:, 3]), np.ones(len(cat))
else:
    j = json.load(open(a.pol)); cs = j["cells"]; ra = np.array([c["ra"] for c in cs]); dec = np.array([c["dec"] for c in cs]); amp = np.array([c["p"] for c in cs]); pa = np.radians([c["pa"] for c in cs]); wgt = np.array([c["I"] for c in cs])
x, y = to_pix(ra, dec); x2, y2 = to_pix(ra + np.sin(pa) / (3600 * np.cos(np.radians(dec))), dec + np.cos(pa) / 3600)
th = np.arctan2(y2 - y, x2 - x); ok = (x >= 0) & (x < W0) & (y >= 0) & (y < H0); x, y, th, amp, wgt = x[ok], y[ok], th[ok], amp[ok], wgt[ok]
print(a.kind, "objects in the composite:", len(x))
# ---- bin into cells (pixel frame)
cp = a.cell / arcpix; nx, ny = int(math.ceil(W0 / cp)), int(math.ceil(H0 / cp)); ci, cj = np.minimum((x // cp).astype(int), nx - 1), np.minimum((y // cp).astype(int), ny - 1)
Cs = np.zeros((ny, nx)); Sn = np.zeros((ny, nx)); Wt = np.zeros((ny, nx)); Nn = np.zeros((ny, nx), int); Mx = np.zeros((ny, nx)); My = np.zeros((ny, nx))
np.add.at(Cs, (cj, ci), wgt * amp * np.cos(2 * th)); np.add.at(Sn, (cj, ci), wgt * amp * np.sin(2 * th)); np.add.at(Wt, (cj, ci), wgt); np.add.at(Nn, (cj, ci), 1); np.add.at(Mx, (cj, ci), x); np.add.at(My, (cj, ci), y)
meas = Nn >= a.minn
# smoothed field (Gaussian, 1.3 cells) of the doubled-angle vector, for filling and for the field lines
from scipy.ndimage import gaussian_filter
sg = 1.3; sC, sS, sW = gaussian_filter(Cs, sg), gaussian_filter(Sn, sg), gaussian_filter(Wt, sg); sN = gaussian_filter(Nn.astype(float), sg)
have = gaussian_filter((Nn > 0).astype(float), 2.0) > 0.08                              # inside the data footprint
cells = []                                                                              # (cx, cy, theta, amp, interpolated)
for j_ in range(ny):
    for i_ in range(nx):
        if meas[j_, i_]:
            cx, cy = Mx[j_, i_] / Nn[j_, i_], My[j_, i_] / Nn[j_, i_]; cells.append((cx, cy, 0.5 * math.atan2(Sn[j_, i_], Cs[j_, i_]), math.hypot(Cs[j_, i_], Sn[j_, i_]) / Wt[j_, i_], False))
        elif a.fill and have[j_, i_] and sN[j_, i_] > 0.35 * a.minn / 4 and sW[j_, i_] > 0:
            cells.append(((i_ + .5) * cp, (j_ + .5) * cp, 0.5 * math.atan2(sS[j_, i_], sC[j_, i_]), math.hypot(sC[j_, i_], sS[j_, i_]) / sW[j_, i_], True))
print("cells:", len(cells), "measured", sum(1 for c in cells if not c[4]), "interpolated", sum(1 for c in cells if c[4]), "| cell", round(cp, 1), "px =", a.cell, "arcsec")
# ---- field lines: streamlines of the smoothed orientation field in pixel space
def field(px, py):
    i_, j_ = int(px // cp), int(py // cp)
    if i_ < 0 or j_ < 0 or i_ >= nx or j_ >= ny or not have[j_, i_] or sW[j_, i_] <= 0: return None
    ang = 0.5 * math.atan2(sS[j_, i_], sC[j_, i_]); return np.array([math.cos(ang), math.sin(ang)])
occ = {}; dsep = 1.1 * cp; lines = []
def free(px, py, lid): k = (int(px // dsep), int(py // dsep)); return all(occ.get((k[0] + i, k[1] + j), lid) == lid for i in (-1, 0, 1) for j in (-1, 0, 1))
for sx in np.arange(cp, W0, 1.5 * cp):
    for sy in np.arange(cp, H0, 1.5 * cp):
        if field(sx, sy) is None or not free(sx, sy, -1): continue
        lid = len(lines); pts = []
        for sgn in (+1, -1):
            p = np.array([sx, sy]); prev = None; seg = []
            for _ in range(220):
                v = field(*p)
                if v is None or not free(p[0], p[1], lid): break
                if prev is not None and np.dot(v, prev) < 0: v = -v
                if prev is None: v = v * sgn
                occ[(int(p[0] // dsep), int(p[1] // dsep))] = lid; seg.append(p.copy()); prev = v; p = p + v * 0.4 * cp
            pts.append(seg)
        line = pts[1][::-1] + pts[0][1:]
        if len(line) >= 8: lines.append(np.array(line))
print("field lines:", len(lines))
# ---- SVG paths
def vec_paths(cs_, harpoon=True):
    shaft, barb = [], []
    for cx, cy, t, am, interp in cs_:
        L = cp * 0.88 * min(1.0, max(0.3, am / a.ref)); vx, vy = math.cos(t), math.sin(t)
        if vy > 1e-9 or (abs(vy) < 1e-9 and vx < 0): vx, vy = -vx, -vy                       # head toward the top of the image; horizontal -> right
        tx, ty = cx - vx * L / 2, cy - vy * L / 2; hx, hy = cx + vx * L / 2, cy + vy * L / 2
        shaft.append(f"M{tx:.1f} {ty:.1f}L{hx:.1f} {hy:.1f}")
        if harpoon:
            lb = max(0.30 * L, 1.0); ang = math.radians(26); c_, s_ = math.cos(ang), math.sin(ang)
            bx, by = -(vx * c_ - vy * s_) * lb, -(vx * s_ + vy * c_) * lb                    # barb on one (the right-hand) side only
            barb.append(f"M{hx:.1f} {hy:.1f}L{hx + bx:.1f} {hy + by:.1f}")
    return "".join(shaft), "".join(barb)
sm_, bm_ = vec_paths([c for c in cells if not c[4]]); si_, bi_ = vec_paths([c for c in cells if c[4]])
lines_d = "".join("M" + "L".join(f"{p[0]:.1f} {p[1]:.1f}" for p in ln[::2]) for ln in lines)
col = a.color; lcol = a.linecolor or a.color; rel = os.path.relpath(comp, OUT)
if a.initial == "data" and cells:
    xs = [c[0] for c in cells]; ys = [c[1] for c in cells]; pad = 0.08 * max(max(xs) - min(xs), max(ys) - min(ys)) + 2 * cp
    vb = (max(0, min(xs) - pad), max(0, min(ys) - pad), min(W0, max(xs) + pad) - max(0, min(xs) - pad), min(H0, max(ys) + pad) - max(0, min(ys) - pad))
else: vb = (0, 0, W0, H0)
svg_inner = (f'<image id="bg" href="{html.escape(rel)}" x="0" y="0" width="{W0}" height="{H0}"/>'
  f'<g id="lines"><path d="{lines_d}" fill="none" stroke="{lcol}" stroke-opacity="0.42" stroke-width="0.9" vector-effect="non-scaling-stroke" stroke-linecap="round" stroke-linejoin="round"/></g>'
  f'<g id="interp"><path d="{si_}{bi_}" fill="none" stroke="#000" stroke-opacity="0.35" stroke-width="2.4" vector-effect="non-scaling-stroke" stroke-linecap="round"/>'
  f'<path d="{si_}{bi_}" fill="none" stroke="{col}" stroke-opacity="0.5" stroke-width="1" vector-effect="non-scaling-stroke" stroke-linecap="round"/></g>'
  f'<g id="vec"><path d="{sm_}{bm_}" fill="none" stroke="#000" stroke-opacity="0.6" stroke-width="2.4" vector-effect="non-scaling-stroke" stroke-linecap="round" stroke-linejoin="round"/>'
  f'<path d="{sm_}{bm_}" fill="none" stroke="{col}" stroke-width="1.1" vector-effect="non-scaling-stroke" stroke-linecap="round" stroke-linejoin="round"/></g>')
open(f"{OUT}/{a.name}.svg", "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W0} {H0}" width="{W0}" height="{H0}">{svg_inner}</svg>')
leg = ("Harpoon = orientation, drawn pointing toward the top of the image (the data are axial: the head side is a drawing convention). Length ~ amplitude. Faint lines = field lines of the smoothed orientation field. "
       "Fainter vectors = filled from neighbouring cells where too few objects fall in a cell. Wheel = zoom, drag = pan, double-click = fit data, F = full image.")
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(a.title)}</title><meta name="gallery-target" content="{html.escape(a.target)}"><meta name="gallery-kind" content="{html.escape(a.kind)}">
<style>:root{{--bg:#0b0d14;--p:#141826;--l:#262d44;--t:#e6e9f5;--m:#98a2c3;--acc:#e8b84a}}@media(prefers-color-scheme:light){{:root{{--bg:#f3f4f8;--p:#fff;--l:#cdd2e3;--t:#161a2b;--m:#566086;--acc:#9a6b00}}}}
*{{box-sizing:border-box}}html,body{{height:100%;margin:0}}body{{background:var(--bg);color:var(--t);font:14px/1.4 system-ui,sans-serif;display:flex;flex-direction:column}}
header{{padding:8px 14px;border-bottom:1px solid var(--l);display:flex;flex-wrap:wrap;gap:12px;align-items:center}}h1{{font-size:16px;margin:0}}.m{{color:var(--m);font-size:12px}}
button,label{{background:var(--p);color:var(--t);border:1px solid var(--l);border-radius:6px;padding:4px 9px;font:inherit;cursor:pointer}}label{{display:inline-flex;gap:5px;align-items:center}}
#stage{{flex:1;min-height:0;background:#000;position:relative;cursor:grab;overflow:hidden}}#stage svg{{width:100%;height:100%;display:block}}#note{{padding:6px 14px;border-top:1px solid var(--l);color:var(--m);font-size:12px;max-height:110px;overflow:auto}}</style></head><body>
<header><h1>{html.escape(a.title)}</h1><button id="zi">+</button><button id="zo">−</button><button id="fit">Fit data</button><button id="full">Full image</button>
<label><input type="checkbox" id="tv" checked>vectors</label><label><input type="checkbox" id="tl" checked>field lines</label><label><input type="checkbox" id="ti" checked>filled</label><label><input type="checkbox" id="tb" checked>image</label>
<span class="m" id="zl"></span></header>
<div id="stage"><svg id="s" xmlns="http://www.w3.org/2000/svg" viewBox="{vb[0]:.1f} {vb[1]:.1f} {vb[2]:.1f} {vb[3]:.1f}" preserveAspectRatio="xMidYMid meet">{svg_inner}</svg></div>
<div id="note">{html.escape(a.note)}<br>{html.escape(leg)}</div>
<script>const S=document.getElementById("s"),ST=document.getElementById("stage"),FULL=[0,0,{W0},{H0}],DATA={[round(float(v),1) for v in vb]};let vb=DATA.slice();
function setvb(){{S.setAttribute("viewBox",vb.join(" "));document.getElementById("zl").textContent="zoom x"+({W0}/vb[2]).toFixed(1)}}
function svgpt(cx,cy){{const p=S.createSVGPoint();p.x=cx;p.y=cy;return p.matrixTransform(S.getScreenCTM().inverse())}}
function zoom(f,cx,cy){{const r=ST.getBoundingClientRect(),c=svgpt(cx===undefined?r.left+r.width/2:cx,cy===undefined?r.top+r.height/2:cy);
 const nw=Math.min({W0}*3,Math.max(8,vb[2]/f)),k=nw/vb[2];vb=[c.x-(c.x-vb[0])*k,c.y-(c.y-vb[1])*k,nw,vb[3]*k];setvb()}}
ST.addEventListener("wheel",e=>{{e.preventDefault();zoom(e.deltaY<0?1.2:1/1.2,e.clientX,e.clientY)}},{{passive:false}});
let drag=null;ST.addEventListener("mousedown",e=>{{drag=[e.clientX,e.clientY];ST.style.cursor="grabbing"}});addEventListener("mouseup",()=>{{drag=null;ST.style.cursor="grab"}});
addEventListener("mousemove",e=>{{if(!drag)return;const a=svgpt(drag[0],drag[1]),b=svgpt(e.clientX,e.clientY);vb[0]+=a.x-b.x;vb[1]+=a.y-b.y;drag=[e.clientX,e.clientY];setvb()}});
ST.addEventListener("dblclick",()=>{{vb=DATA.slice();setvb()}});
document.getElementById("zi").onclick=()=>zoom(1.4);document.getElementById("zo").onclick=()=>zoom(1/1.4);document.getElementById("fit").onclick=()=>{{vb=DATA.slice();setvb()}};document.getElementById("full").onclick=()=>{{vb=FULL.slice();setvb()}};
addEventListener("keydown",e=>{{if(e.key==="+"||e.key==="=")zoom(1.4);if(e.key==="-")zoom(1/1.4);if(e.key==="f"||e.key==="F"){{vb=FULL.slice();setvb()}}}});
for(const [cb,id] of [["tv","vec"],["tl","lines"],["ti","interp"],["tb","bg"]])document.getElementById(cb).onchange=e=>document.getElementById(id).style.display=e.target.checked?"":"none";{{const h=new URLSearchParams(location.hash.slice(1)).get("vb");if(h){{const q=h.split(",").map(Number);if(q.length===4&&q.every(isFinite))vb=q}}}}setvb();</script></body></html>"""
open(f"{OUT}/{a.name}.html", "w").write(page); print("wrote", f"viewers/{a.name}.html", f"({len(page)//1024} KB)")
