#!/usr/bin/env python3
"""shear_measure.py (2026-11-20): weak-lensing shear field from a JWST NIRCam level-3 mosaic.  Reads only.
   Usage: python shear_measure.py MOSAIC.fits TAG OUT_DIR SCRATCH_DIR [cell_arcsec=30]
Method (crude, documented; validated against the published Lenstool model for the Bullet Cluster, see shear_validate_bullet.py):
  1. tiles of 4096^2 (+128 px overlap) read through memmap; sep.Background (128 px boxes) subtracted; sep.extract at 3 sigma, minarea 10, deblend 32 / 0.001.
  2. second moments (x2, y2, xy) of each isophotal footprint; stars = tight small-size locus among bright (S/N > 40) objects.
  3. PSF second moments at each galaxy = median of the 15 nearest stars (kd-tree); subtracted from the galaxy moments (first-order correction, no shear responsivity calibration).
  4. galaxies: S/N > 12, no sep flags, corrected trace > 0.3 x PSF trace, e < 0.9, not on a tile edge.
  5. moments rotated to the sky (East, North) with the local WCS Jacobian; position angle PA (North through East), spin-2 components e cos2PA, e sin2PA.
  6. cells of `cell_arcsec`: mean spin-2 vector (the reduced-shear estimate, diluted by cluster members and uncalibrated), N, SNR = |mean| / (sigma_e / sqrt N).
NOT done: shear calibration (multiplicative bias), cluster-member removal (no redshifts), blend rejection beyond sep flags, PSF fitted per pointing.  Treat amplitudes as relative, patterns as the result."""
import sys, os, json, time, warnings
import numpy as np, sep
from astropy.io import fits
from astropy.wcs import WCS
from scipy.spatial import cKDTree
warnings.filterwarnings("ignore")
mosaic, tag, outdir, scratch = sys.argv[1:5]; cell = float(sys.argv[5]) if len(sys.argv) > 5 else 30.0
os.makedirs(outdir, exist_ok=True); os.makedirs(scratch, exist_ok=True)
T, PAD = 4096, 128
sep.set_extract_pixstack(60_000_000); sep.set_sub_object_limit(20000)
t0 = time.time()
h = fits.open(mosaic, memmap=True); sci = h["SCI"]; ny, nx = sci.shape; w = WCS(sci.header)
pix = float(np.sqrt(abs(np.linalg.det(w.pixel_scale_matrix)))) * 3600
rows = []
for y0 in range(0, ny, T):
    for x0 in range(0, nx, T):
        ya, yb, xa, xb = max(0, y0 - PAD), min(ny, y0 + T + PAD), max(0, x0 - PAD), min(nx, x0 + T + PAD)
        d = np.array(sci.data[ya:yb, xa:xb], dtype=np.float32)
        bad = ~np.isfinite(d) | (d == 0)
        if bad.mean() > 0.95: continue
        d[bad] = 0
        try:
            bkg = sep.Background(d, mask=bad, bw=128, bh=128, fw=3, fh=3)
            dd = d - bkg.back(); rms = bkg.globalrms
            o = sep.extract(dd, 3.0, err=rms, mask=bad, minarea=10, deblend_nthresh=32, deblend_cont=0.001, clean=True)
        except Exception as e:
            print("tile fail", y0, x0, e); continue
        cx, cy = o["x"] + xa, o["y"] + ya
        keep = (cx >= x0) & (cx < x0 + T) & (cy >= y0) & (cy < y0 + T) & (o["flag"] == 0) & (o["flux"] > 0)
        # reject objects touching masked pixels
        ix = np.clip(o["x"].astype(int), 0, dd.shape[1] - 1); iy = np.clip(o["y"].astype(int), 0, dd.shape[0] - 1)
        keep &= ~bad[iy, ix]
        o = o[keep]
        snr = o["flux"] / (rms * np.sqrt(o["npix"]))
        rows.append(np.column_stack([o["x"] + xa, o["y"] + ya, o["x2"], o["y2"], o["xy"], o["flux"], snr, o["npix"], o["a"], o["b"]]))
        print(f"tile ({y0},{x0}) {len(o)} objects  {time.time() - t0:.0f}s", flush=True)
        del d, dd, bkg
C = np.vstack(rows); print("objects", len(C))
x, y, x2, y2, xy, flux, snr, npix = C[:, 0], C[:, 1], C[:, 2], C[:, 3], C[:, 4], C[:, 5], C[:, 6], C[:, 7]
s2 = x2 + y2
# stars
b = snr > 40
if b.sum() < 50: b = snr > 20
s0 = np.percentile(s2[b], 12); star = b & (np.abs(s2 - s0) < 0.18 * s0) & (np.sqrt((x2 - y2) ** 2 + 4 * xy ** 2) / s2 < 0.25)
print("bright", int(b.sum()), "stars", int(star.sum()), "star size s0", round(s0, 3), "px^2")
if star.sum() < 20: raise SystemExit("too few stars for a PSF model")
tree = cKDTree(np.column_stack([x[star], y[star]])); P = np.column_stack([x2[star], y2[star], xy[star]])
gal = (snr > 12) & ~star & (s2 > 1.0 * s0)
gi = np.where(gal)[0]; k = min(15, int(star.sum()))
_, nn = tree.query(np.column_stack([x[gi], y[gi]]), k=k)
Pm = np.median(P[nn], axis=1)                                   # (n,3) local PSF moments
qxx, qyy, qxy = x2[gi] - Pm[:, 0], y2[gi] - Pm[:, 1], xy[gi] - Pm[:, 2]
tr = qxx + qyy; ok = tr > 0.3 * (Pm[:, 0] + Pm[:, 1])
gi, qxx, qyy, qxy, tr = gi[ok], qxx[ok], qyy[ok], qxy[ok], tr[ok]
# rotate to the sky: Jacobian of (E, N) w.r.t. (x, y) at the field centre (north-up drizzle: nearly diagonal)
c0 = np.array([[nx / 2, ny / 2], [nx / 2 + 1, ny / 2], [nx / 2, ny / 2 + 1]])
ra, dec = w.wcs_pix2world(c0[:, 0], c0[:, 1], 0); cd = np.cos(np.radians(dec[0]))
J = np.array([[(ra[1] - ra[0]) * cd, (ra[2] - ra[0]) * cd], [dec[1] - dec[0], dec[2] - dec[0]]]) * 3600.0     # arcsec per pixel
QEE = J[0, 0] ** 2 * qxx + 2 * J[0, 0] * J[0, 1] * qxy + J[0, 1] ** 2 * qyy
QNN = J[1, 0] ** 2 * qxx + 2 * J[1, 0] * J[1, 1] * qxy + J[1, 1] ** 2 * qyy
QEN = J[0, 0] * J[1, 0] * qxx + (J[0, 0] * J[1, 1] + J[0, 1] * J[1, 0]) * qxy + J[0, 1] * J[1, 1] * qyy
e = np.hypot(QEE - QNN, 2 * QEN) / (QEE + QNN)
phi = 0.5 * np.arctan2(2 * QEN, QEE - QNN); PA = np.pi / 2 - phi                  # position angle, North through East
sel = e < 0.9
gi, e, PA = gi[sel], e[sel], PA[sel]
rag, decg = w.wcs_pix2world(x[gi], y[gi], 0)
cat = np.column_stack([rag, decg, e, np.degrees(PA) % 180, snr[gi], flux[gi]])
np.save(os.path.join(scratch, f"{tag}_shear_catalog.npy"), cat)
print("galaxies", len(cat), "median e", round(float(np.median(e)), 3), "pixel", round(pix, 4), "arcsec")
# cell field
dec0 = float(np.mean(cat[:, 1])); E = (cat[:, 0] - cat[:, 0].mean()) * np.cos(np.radians(dec0)) * 3600; N = (cat[:, 1] - dec0) * 3600
ci = np.floor(E / cell).astype(int); cj = np.floor(N / cell).astype(int)
cells = []
sig_e = float(np.std(e * np.cos(2 * np.radians(cat[:, 3]))))
for key in set(zip(ci, cj)):
    m = (ci == key[0]) & (cj == key[1])
    if m.sum() < 20: continue
    c = np.mean(cat[m, 2] * np.cos(2 * np.radians(cat[m, 3]))); s = np.mean(cat[m, 2] * np.sin(2 * np.radians(cat[m, 3])))
    amp = float(np.hypot(c, s)); pa = float((0.5 * np.degrees(np.arctan2(s, c))) % 180)
    cells.append(dict(ra=float(np.mean(cat[m, 0])), dec=float(np.mean(cat[m, 1])), n=int(m.sum()), amp=amp, pa=pa, snr=float(amp / (sig_e / np.sqrt(m.sum())))))
json.dump(dict(mosaic=os.path.basename(mosaic), tag=tag, pixel_arcsec=pix, cell_arcsec=cell, n_galaxies=int(len(cat)), n_stars=int(star.sum()), sigma_e=sig_e,
               method="see shear_measure.py header; uncalibrated, cluster members not removed", cells=cells), open(os.path.join(outdir, f"{tag}_shear.json"), "w"))
print("cells", len(cells), "median N", int(np.median([c["n"] for c in cells])) if cells else 0, "time", round(time.time() - t0), "s")
