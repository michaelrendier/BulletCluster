#!/usr/bin/env python3
"""shear_cells.py: re-bin a saved shear catalog (from shear_measure.py) into cells of a different size, with no mosaic read.
Usage: python shear_cells.py CATALOG.npy TAG OUT_DIR CELL_ARCSEC [MIN_N] [MOSAIC_NAME] [N_STARS]"""
import sys, os, json, numpy as np
cat = np.load(sys.argv[1]); tag, outdir, cell = sys.argv[2], sys.argv[3], float(sys.argv[4]); minn = int(sys.argv[5]) if len(sys.argv) > 5 else 20
e, PA = cat[:, 2], np.radians(cat[:, 3]); dec0 = float(np.mean(cat[:, 1]))
E = (cat[:, 0] - cat[:, 0].mean()) * np.cos(np.radians(dec0)) * 3600; N = (cat[:, 1] - dec0) * 3600
ci, cj = np.floor(E / cell).astype(int), np.floor(N / cell).astype(int); sig_e = float(np.std(e * np.cos(2 * PA))); cells = []
for key in set(zip(ci, cj)):
    m = (ci == key[0]) & (cj == key[1])
    if m.sum() < minn: continue
    c, s = np.mean(e[m] * np.cos(2 * PA[m])), np.mean(e[m] * np.sin(2 * PA[m])); amp = float(np.hypot(c, s))
    cells.append(dict(ra=float(cat[m, 0].mean()), dec=float(cat[m, 1].mean()), n=int(m.sum()), amp=amp, pa=float((0.5 * np.degrees(np.arctan2(s, c))) % 180), snr=float(amp / (sig_e / np.sqrt(m.sum())))))
os.makedirs(outdir, exist_ok=True)
json.dump(dict(mosaic=sys.argv[6] if len(sys.argv) > 6 else tag, tag=tag, cell_arcsec=cell, n_galaxies=int(len(cat)), sigma_e=sig_e, min_n=minn,
               method="shear_measure.py catalog re-binned by shear_cells.py; uncalibrated; cluster members / nebular structure not removed", cells=cells), open(os.path.join(outdir, f"{tag}_shear.json"), "w"))
print(tag, "cells", len(cells), "cell", cell, "arcsec; min N", minn, "; extent E", round(E.min()), round(E.max()), "N", round(N.min()), round(N.max()), "arcsec")
