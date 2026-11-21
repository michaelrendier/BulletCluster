#!/usr/bin/env python3
"""build_overlays.py (2026-11-20): turn the measured shear cells and polarization cells into (1) gallery data with sky-coordinate field lines and
(2) static TRANSPARENT PNG overlays on a composite's own pixel grid.  Reads: <target>/*_shear.json, <target>/pol_*.json, composite sidecars (<png>.wcs.json).
Writes: <target>/overlay_data.json and <target>/<kind>_overlay_<composite>.png  (RGBA, alpha = 0 where nothing is drawn).
Usage: BulletCluster/.venv/bin/python build_overlays.py TARGET COMPOSITE_PNG [--shear NAME_shear.json] [--pol pol_acs.json] [--cell-arcsec A]
Field lines: the line-field orientation (position angle, headless) is smoothed on a grid in the doubled-angle representation (cos 2PA, sin 2PA) and integrated from seeds
with a minimum separation; they are drawn faint BEHIND the sticks so the topography of the field shows."""
import sys, os, json, argparse
import numpy as np
from PIL import Image
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
ap = argparse.ArgumentParser(); ap.add_argument("target"); ap.add_argument("composite"); ap.add_argument("--shear"); ap.add_argument("--pol"); ap.add_argument("--cell-arcsec", type=float, default=None)
ap.add_argument("--min-snr-shear", type=float, default=1.0); ap.add_argument("--note-shear", default=""); ap.add_argument("--note-pol", default=""); a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__)); SC = os.path.dirname(HERE)
COL = {"shear": "#c6ff00", "pol": "#ff3df2"}            # contrasting pair; the dark halo makes both read on any background
REF = {"shear": 0.12, "pol": 0.30}                        # amplitude (e or p) that draws a full-length stick
def tan_xy(ra, dec, ra0, dec0):
    ra, dec = np.radians(ra), np.radians(dec); r0, d0 = np.radians(ra0), np.radians(dec0)
    c = np.sin(d0) * np.sin(dec) + np.cos(d0) * np.cos(dec) * np.cos(ra - r0)
    xi = np.cos(dec) * np.sin(ra - r0) / c; eta = (np.cos(d0) * np.sin(dec) - np.sin(d0) * np.cos(dec) * np.cos(ra - r0)) / c
    return np.degrees(xi) * 3600, np.degrees(eta) * 3600                                         # arcsec East, North
def inv_tan(xi, eta, ra0, dec0):
    xi, eta = np.radians(np.asarray(xi) / 3600), np.radians(np.asarray(eta) / 3600); r0, d0 = np.radians(ra0), np.radians(dec0)
    den = np.cos(d0) - eta * np.sin(d0); ra = r0 + np.arctan2(xi, den); dec = np.arctan2(np.sin(d0) + eta * np.cos(d0), np.hypot(xi, den))
    return np.degrees(ra) % 360, np.degrees(dec)
def coarsen(cells, size, kind, ra0, dec0):
    """re-bin cells to `size` arcsec: sum the doubled-angle vectors weighted by amplitude x weight."""
    if not cells: return []
    x, y = tan_xy(np.array([c["ra"] for c in cells]), np.array([c["dec"] for c in cells]), ra0, dec0)
    amp = np.array([c["amp" if kind == "shear" else "p"] for c in cells]); pa = np.radians([c["pa"] for c in cells])
    wgt = np.array([c["n"] if kind == "shear" else c["I"] for c in cells], float)
    key = list(zip(np.floor(x / size).astype(int), np.floor(y / size).astype(int))); out = []
    for k in set(key):
        m = np.array([kk == k for kk in key]); w = wgt[m]
        C = np.sum(w * amp[m] * np.cos(2 * pa[m])) / w.sum(); S = np.sum(w * amp[m] * np.sin(2 * pa[m])) / w.sum()
        xi, eta = np.average(x[m], weights=w), np.average(y[m], weights=w); ra, dec = inv_tan(xi, eta, ra0, dec0)
        d = {"ra": float(ra), "dec": float(dec), ("amp" if kind == "shear" else "p"): float(np.hypot(C, S)), "pa": float((0.5 * np.degrees(np.arctan2(S, C))) % 180), "n": int(m.sum())}
        if kind == "shear": d["snr"] = float(np.mean([c["snr"] for c, mm in zip(cells, m) if mm]) * np.sqrt(m.sum()))
        else: d["snr"] = float(np.mean([c["snr_p"] for c, mm in zip(cells, m) if mm]) * np.sqrt(m.sum()) / 2)
        out.append(d)
    return out
def streamlines(cells, kind, ra0, dec0, spacing):
    """headless line-field streamlines in the tangent plane (arcsec); returns lists of [ra, dec] polylines."""
    x, y = tan_xy(np.array([c["ra"] for c in cells]), np.array([c["dec"] for c in cells]), ra0, dec0); pa = np.radians([c["pa"] for c in cells])
    C, S = np.cos(2 * pa), np.sin(2 * pa); sig = 1.3 * spacing
    def field(px, py):
        w = np.exp(-((x - px) ** 2 + (y - py) ** 2) / (2 * sig ** 2)); sw = w.sum()
        if sw < 0.35: return None
        ang = 0.5 * np.arctan2((w * S).sum(), (w * C).sum()); return np.array([np.sin(ang), np.cos(ang)])          # (E, N) of the line direction
    occ = {}; dsep = 0.9 * spacing; lines = []
    def free(px, py, lid=-1):                                        # free of OTHER lines' points (a line may touch its own)
        k = (int(px // dsep), int(py // dsep)); return all(occ.get((k[0] + i, k[1] + j), lid) == lid for i in (-1, 0, 1) for j in (-1, 0, 1))
    seeds = [(sx, sy) for sx in np.arange(x.min(), x.max(), 1.6 * spacing) for sy in np.arange(y.min(), y.max(), 1.6 * spacing)]
    for sx, sy in seeds:
        if field(sx, sy) is None or not free(sx, sy): continue
        lid = len(lines); pts = []
        for sgn in (+1, -1):
            p = np.array([sx, sy]); prev = None; seg = []
            for _ in range(160):
                v = field(*p)
                if v is None: break
                if prev is not None and np.dot(v, prev) < 0: v = -v
                if prev is None: v = v * sgn
                k = (int(p[0] // dsep), int(p[1] // dsep))
                if not free(p[0], p[1], lid): break
                occ[k] = lid; seg.append(p.copy()); prev = v; p = p + v * 0.3 * spacing
            pts.append(seg)
        line = pts[1][::-1] + pts[0][1:]
        if len(line) >= 8:
            arr = np.array(line)[::2]; ra, dec = inv_tan(arr[:, 0], arr[:, 1], ra0, dec0); lines.append(np.column_stack([ra, dec]).round(6).tolist())
    return lines
# --- gather
tdir = os.path.join(HERE, a.target); data = {"target": a.target}
comp = os.path.join(SC, a.composite); sc = json.load(open(comp + ".wcs.json")); H, W = sc["H"], sc["W"]; sc_shift = sc.get("shift", [0, 0]); W += max(0, sc_shift[0]); H += max(0, sc_shift[1])
ra0, dec0 = sc["crval"]
def to_pix(ra, dec):                                  # sky -> PNG pixel (x right, y down) through the sidecar
    xi, eta = tan_xy(ra, dec, sc["crval"][0], sc["crval"][1]); cd = np.array(sc["cd"]) * 3600.0       # arcsec per pixel
    d = np.linalg.solve(cd, np.vstack([xi, eta])); xa = sc["crpix"][0] - 1 + d[0]; ya = sc["crpix"][1] - 1 + d[1]
    sh = sc.get("shift", [0, 0]); return xa + sh[0], ((sc["H"] - 1 - ya) if sc["flipud"] else ya) + sh[1]
layers = {}
if a.shear:
    j = json.load(open(os.path.join(tdir, a.shear))); cs = [c for c in j["cells"] if c["snr"] >= a.min_snr_shear]
    cell = a.cell_arcsec or j["cell_arcsec"]; layers["shear"] = dict(cells=cs, meta={k: j[k] for k in ("mosaic", "cell_arcsec", "n_galaxies", "method")}, spacing=cell)
if a.pol:
    j = json.load(open(os.path.join(tdir, a.pol))); size = a.cell_arcsec or 3.0
    cs = coarsen(j["cells"], size, "pol", ra0, dec0); layers["pol"] = dict(cells=cs, meta={k: j.get(k) for k in ("instrument", "date", "convention", "cross_check_vs_acs")}, spacing=size)
for kind, L in layers.items():
    cells = L["cells"]; L["streams"] = streamlines(cells, kind, ra0, dec0, L["spacing"]) if len(cells) > 6 else []
    ra = np.array([c["ra"] for c in cells]); dec = np.array([c["dec"] for c in cells]); xs, ys = to_pix(ra, dec)
    arcpix = float(np.sqrt(abs(np.linalg.det(np.array(sc["cd"]))))) * 3600; cellpix = L["spacing"] / arcpix
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis("off"); fig.patch.set_alpha(0); ax.patch.set_alpha(0)
    if L["streams"]:                                                              # faint field lines first (behind)
        segs = []
        for ln in L["streams"]:
            px, py = to_pix(np.array([p[0] for p in ln]), np.array([p[1] for p in ln])); segs.append(np.column_stack([px, py]))
        ax.add_collection(LineCollection(segs, colors=COL[kind], linewidths=0.8, alpha=0.30, zorder=1))
    amp = np.array([c["amp" if kind == "shear" else "p"] for c in cells]); pa = np.radians([c["pa"] for c in cells])
    L_ = 0.5 * cellpix * np.clip(amp / REF[kind], 0.15, 1.0)                       # half-length in pixels
    dra = np.sin(pa) / (3600 * np.cos(np.radians(dec))); ddec = np.cos(pa) / 3600          # 1 arcsec along the position angle (North through East)
    x2, y2 = to_pix(ra + dra, dec + ddec); vx, vy = x2 - xs, y2 - ys; nv = np.hypot(vx, vy); vx, vy = vx / nv, vy / nv      # direction through THIS image's own WCS
    dx, dy = vx * L_, vy * L_
    segs = np.stack([np.column_stack([xs - dx, ys - dy]), np.column_stack([xs + dx, ys + dy])], 1)
    ax.add_collection(LineCollection(segs, colors="black", linewidths=3.6, alpha=0.75, zorder=2, capstyle="round"))      # halo
    ax.add_collection(LineCollection(segs, colors=COL[kind], linewidths=1.9, alpha=1.0, zorder=3, capstyle="round"))
    outp = os.path.join(tdir, f"{kind}_overlay_{os.path.basename(a.composite).replace('.png', '')}.png")
    fig.savefig(outp, dpi=100, transparent=True); plt.close(fig)
    im = Image.open(outp); assert im.size == (W, H), (im.size, (W, H)); print(kind, len(cells), "cells,", len(L["streams"]), "field lines ->", os.path.relpath(outp, SC), im.mode, "alpha min/max", np.array(im)[..., 3].min(), np.array(im)[..., 3].max())
    data[kind] = dict(cells=cells, streams=L["streams"], meta=L["meta"], color=COL[kind], ref=REF[kind], spacing=L["spacing"], note=(a.note_shear if kind == "shear" else a.note_pol))
json.dump(data, open(os.path.join(tdir, "overlay_data.json"), "w"))
