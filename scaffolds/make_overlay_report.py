#!/usr/bin/env python3
"""make_overlay_report.py (2026-11-20): overlay_report.html = for each scaffold, the shear image and the polarization image (composite + transparent overlay).
Reads overlays/<target>/{shear,pol}_overlay_<composite>.png (from build_overlays.py) and writes merged previews to overlays/report/.  stdlib + Pillow."""
import os, json, html
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); R = f"{HERE}/overlays/report"; os.makedirs(R, exist_ok=True)
SC = [  # target, title, composite png (relative to scaffolds/), shear note, pol note when absent
 ("BulletCluster", "Bullet Cluster (JWST NIRCam, program 4598)", "BulletCluster/false_color/BulletCluster_nircam_o001_rgb_lupton.png",
  "No real radio/optical polarization on disk: MeerKAT is Stokes I only (its Q/U files are simulated, not data), and the SARAO/ASKAP polarization data are not retrieved."),
 ("CrabNebula", "Crab Nebula (JWST NIRCam scaffold; HST polarization)", "CrabNebula/false_color/CrabNebula_nircam_o006_rgb_lupton.png", ""),
 ("HE_0435-1223", "HE 0435-1223 (JWST NIRCam)", "HE_0435-1223/false_color/HE_0435-1223_nircam_rgb_lupton.png",
  "The VLA (12B-030) and ALMA (2024.1.00291.S) data are on disk but unreduced; no polarization map exists yet."),
 ("Pillars_of_Creation", "Pillars of Creation (JWST NIRCam)", "Pillars_of_Creation/false_color/Pillars_of_Creation_nircam_o001_rgb_lupton.png",
  "ALMA 2023.1.00675.S is on disk as raw correlator data (full-polarization correlations present); it needs CASA calibration. Planck 353 GHz is a single 5-arcminute beam here."),
]
cards = []
for tgt, title, comp, why in SC:
    ov = json.load(open(f"{HERE}/overlays/{tgt}/overlay_data.json")) if os.path.exists(f"{HERE}/overlays/{tgt}/overlay_data.json") else {}
    stem = os.path.basename(comp)[:-4]; base = Image.open(f"{HERE}/{comp}").convert("RGBA") if os.path.exists(f"{HERE}/{comp}") else None
    panels = []
    for kind, label in (("shear", "Shear field (JWST)"), ("pol", "Polarization field (HST, real data)")):
        p = f"{HERE}/overlays/{tgt}/{kind}_overlay_{stem}.png"
        if base is not None and os.path.exists(p) and kind in ov:
            out = f"{R}/{tgt}_{kind}.png"; Image.alpha_composite(base, Image.open(p).convert("RGBA")).convert("RGB").save(out, optimize=True)
            panels.append((label, f"overlays/report/{tgt}_{kind}.png", ov[kind].get("note", ""), len(ov[kind]["cells"]), len(ov[kind]["streams"])))
        else:
            panels.append((label, None, why if kind == "pol" else "No JWST shear measurement for this scaffold.", 0, 0))
    cards.append((title, panels))
FAV = open(os.path.join(HERE, "favicon_datauri.txt")).read().strip()
css = ":root{--bg:#0b0d14;--p:#141826;--l:#262d44;--t:#e6e9f5;--m:#98a2c3}@media(prefers-color-scheme:light){:root{--bg:#f3f4f8;--p:#fff;--l:#cdd2e3;--t:#161a2b;--m:#566086}}body{background:var(--bg);color:var(--t);font:15px/1.45 system-ui,sans-serif;margin:0;padding:16px}h1{font-size:19px;margin:0 0 4px}.lead{color:var(--m);margin:0 0 18px;max-width:1100px}section{margin:0 0 30px}h2{font-size:16px;margin:0 0 8px}.row{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media(max-width:900px){.row{grid-template-columns:1fr}}figure{margin:0;background:var(--p);border:1px solid var(--l);border-radius:8px;overflow:hidden}figure img{width:100%;display:block;background:#000}figcaption{padding:8px 10px;font-size:13px;color:var(--m)}figcaption b{color:var(--t)}.none{padding:26px 14px;color:var(--m)}"
body = ["<h1>Shear and real polarization on the scaffolds</h1><p class='lead'>Each image is the false-colour composite with a transparent overlay: sticks are the field direction (length = amplitude), faint lines behind them are the field lines. Lime = shear, magenta = polarization; both have a dark halo so they read on any background. Where a panel has no image, the reason is the caption: no real data was invented. The gallery (gallery.html) has the same overlays as selectable layers on both raw and false-colour images.</p>"]
for title, panels in cards:
    body.append(f"<section><h2>{html.escape(title)}</h2><div class='row'>")
    for label, img, note, n, nl in panels:
        if img: body.append(f"<figure><img src='{img}' alt='{html.escape(label)}'><figcaption><b>{html.escape(label)}</b> · {n} cells, {nl} field lines<br>{html.escape(note)}</figcaption></figure>")
        else: body.append(f"<figure><div class='none'><b>{html.escape(label)}</b><br>{html.escape(note)}</div></figure>")
    body.append("</div></section>")
open(f"{HERE}/overlay_report.html", "w").write(f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Scaffold overlays</title><link rel='icon' type='image/png' href='{FAV}'><style>{css}</style></head><body>{''.join(body)}</body></html>")
print("overlay_report.html written;", sum(1 for _, ps in cards for p in ps if p[1]), "images")

import contact; _p = f"{HERE}/overlay_report.html"; open(_p, "w").write(contact.inject(open(_p).read()))
