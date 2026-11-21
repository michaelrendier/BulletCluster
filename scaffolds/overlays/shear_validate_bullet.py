#!/usr/bin/env python3
"""shear_validate_bullet.py (2026-11-20): does shear_measure.py recover a real lensing signal?  Bullet Cluster, JWST NIRCam F200W (prog 4598).
Control = the published Lenstool model of Rihtarsic et al. 2026 (CANUCS), v1 best-fit kappa/gamma1/gamma2 at 50 mas, scaled to Dls/Ds = 1.
Steps: (1) find the model's mass peaks; (2) fix the gamma1/gamma2 sign convention from the MODEL ALONE (its shear must be tangential about its own peak);
(3) measured tangential ellipticity profile about the peak, with a 45-degree-rotated (B-mode) null; (4) correlation of each galaxy's orientation with the model shear
direction, against a shuffle null.  Usage: BulletCluster/.venv/bin/python shear_validate_bullet.py CATALOG.npy MODELDIR OUT.json"""
import sys, json, numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from scipy.ndimage import gaussian_filter, map_coordinates
cat = np.load(sys.argv[1]); MD = sys.argv[2].rstrip("/") + "/"; out = sys.argv[3]
ra, dec, e, PA, snr = cat[:, 0], cat[:, 1], cat[:, 2], np.radians(cat[:, 3]), cat[:, 4]
K = fits.open(MD + "kappa.fits")[0]; G1 = fits.open(MD + "gamma1.fits")[0].data; G2 = fits.open(MD + "gamma2.fits")[0].data
w = WCS(K.header); kap = K.data; ps = abs(K.header["CDELT2"]) * 3600
# (1) peaks of the 4-arcsec-smoothed kappa (log, to tame the singular cores)
blk = int(round(2.0 / ps)); sm = gaussian_filter(np.log10(np.clip(kap, 1e-3, None)), blk)
peaks = []; tmp = sm.copy()
for _ in range(2):
    iy, ix = np.unravel_index(np.argmax(tmp), tmp.shape); peaks.append((ix, iy)); 
    r0 = int(60 / ps); tmp[max(0, iy - r0):iy + r0, max(0, ix - r0):ix + r0] = -9
pk = [tuple(map(float, w.wcs_pix2world(ix, iy, 0))) for ix, iy in peaks]
print("model kappa peaks (RA, Dec):", [(round(a, 4), round(b, 4)) for a, b in pk])
def enu(ra_, dec_, ra0, dec0): return (ra_ - ra0) * np.cos(np.radians(dec0)) * 3600, (dec_ - dec0) * 3600       # arcsec East, North
# (2) convention from the model alone, ring of 30-90 arcsec around peak 0
ix0, iy0 = peaks[0]; ang = np.linspace(0, 2 * np.pi, 720, endpoint=False); res = {}
for rr in np.arange(30, 91, 10):
    xs = ix0 + (rr / ps) * np.cos(ang); ys = iy0 + (rr / ps) * np.sin(ang)           # pixel offsets; +x = West, +y = North (CDELT1 < 0)
    g1 = map_coordinates(G1, [ys, xs], order=1); g2 = map_coordinates(G2, [ys, xs], order=1)
    psi = np.arctan2(-(xs - ix0), (ys - iy0))                                          # PA of radial vector, North through East
    for name, (s_e, s_g2) in {"A: x=West, phi CCW": (-1, +1), "B: x=East, phi CCW": (+1, +1), "C: x=West, phi CW": (-1, -1), "D: x=East, phi CW": (+1, -1)}.items():
        phi = 0.5 * np.arctan2(s_g2 * g2, g1); PAm = np.arctan2(s_e * np.cos(phi), np.sin(phi))
        res.setdefault(name, []).append(float(np.mean(-np.cos(2 * (PAm - psi)))))          # +1 = tangential
conv = {k: float(np.mean(v)) for k, v in res.items()}; best = max(conv, key=conv.get)
print("model tangential alignment by convention:", {k: round(v, 3) for k, v in conv.items()}, "-> best", best)
s_e, s_g2 = {"A": (-1, +1), "B": (+1, +1), "C": (-1, -1), "D": (+1, -1)}[best[0]]
# (3) measured tangential profile about the main peak (all galaxies within 200")
E, N = enu(ra, dec, pk[0][0], pk[0][1]); r = np.hypot(E, N); psi = np.arctan2(E, N)
et = -e * np.cos(2 * (PA - psi)); ex = e * np.sin(2 * (PA - psi))                       # tangential (E-mode) and 45-degree (B-mode)
bins = [(15, 30), (30, 50), (50, 80), (80, 120), (120, 200), (200, 400)]; prof = []
for a, b in bins:
    m = (r >= a) & (r < b)
    if m.sum() < 20: continue
    prof.append(dict(r_lo=a, r_hi=b, n=int(m.sum()), et=float(et[m].mean()), et_err=float(et[m].std() / np.sqrt(m.sum())), ex=float(ex[m].mean())))
for p in prof: print(f"  r {p['r_lo']:3d}-{p['r_hi']:3d}\"  N {p['n']:4d}  <e_t> {p['et']:+.4f} +- {p['et_err']:.4f}   <e_x (B-mode null)> {p['ex']:+.4f}")
# (4) per-galaxy orientation vs model shear direction
x, y = w.wcs_world2pix(ra, dec, 0); ok = (x > 0) & (y > 0) & (x < kap.shape[1] - 1) & (y < kap.shape[0] - 1)
g1 = map_coordinates(G1, [y[ok], x[ok]], order=1); g2 = map_coordinates(G2, [y[ok], x[ok]], order=1); kk = map_coordinates(kap, [y[ok], x[ok]], order=1)
phi = 0.5 * np.arctan2(s_g2 * g2, g1); PAm = np.arctan2(s_e * np.cos(phi), np.sin(phi))
wgt = np.clip(np.hypot(g1, g2) / np.clip(np.abs(1 - kk), 0.3, None), 0, 0.6)
eo, PAo = e[ok], PA[ok]
C = float(np.sum(wgt * eo * np.cos(2 * (PAo - PAm))) / np.sum(wgt * eo))
rng = np.random.default_rng(0); null = []
for _ in range(2000):
    pi = rng.permutation(len(PAm)); null.append(np.sum(wgt[pi] * eo * np.cos(2 * (PAo - PAm[pi]))) / np.sum(wgt[pi] * eo))
null = np.array(null); z = (C - null.mean()) / null.std()
print(f"model-direction correlation C = {C:+.4f}  shuffle null {null.mean():+.4f} +- {null.std():.4f}  z = {z:.1f}  (N = {ok.sum()})")
json.dump(dict(peaks=pk, convention_scores=conv, convention=best, profile=prof, correlation=dict(C=C, null_mean=float(null.mean()), null_sd=float(null.std()), z=float(z), n=int(ok.sum()))), open(out, "w"), indent=1)
