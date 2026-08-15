#!/usr/bin/env python3
"""
kappa_vs_xray_vs_nfw.py — THE SHAPE TEST.

Does the Kaiser-Squires convergence (kappa, from REAL JWST background-galaxy
shear) track:
    (A) the X-RAY GAS        -- real Chandra, 577 ks, 1.01M counts
    (B) the NFW MODEL        -- placed at DM_NW/DM_SE in constants.py

Gas and mass are SPATIALLY SEPARATED in the Bullet Cluster -- that separation is
the entire published result -- so A and B are cleanly distinguishable.

    kappa tracks X-ray  -> CONVERGENT: eye and algorithm found the same real thing
    kappa tracks NFW    -> CIRCULAR:   the answer was put in by hand

⚠ WHY A SHIFT NULL IS MANDATORY. Both fields are smooth and spatially
autocorrelated. Pearson r between any two smooth maps is large by construction
and its textbook p-value is meaningless (effective N << pixel count). So every
r below is quoted against a null built by CIRCULARLY SHIFTING one map, which
preserves its autocorrelation structure while destroying the alignment.
Read the z-score, never the raw r.
"""
import sys, glob, os
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.cosmology import FlatLambdaCDM
from reproject import reproject_interp

REPO  = "/home/rendier/Projects/ThePlace/BulletCluster"
LIO   = f"{REPO}/optical/jwst/prepped/l_io"
XRAY  = f"{REPO}/xray/bullet_chandra_0.5-7keV.fits"
FITSR = f"{REPO}/optical/jwst/4598/mastDownload/JWST"
BIN   = 32

DM_NW  = dict(ra=104.6383, dec=-55.9252, M200=3.7e14, c=5.0, label='DM NW')
DM_SE  = dict(ra=104.5726, dec=-55.9563, M200=1.5e14, c=4.5, label='DM SE')
Z_CL   = 0.296                      # Bullet Cluster redshift

# ── 1. reconstruct the coarse kappa WCS ──────────────────────────────────────
ref = sorted(glob.glob(f"{FITSR}/**/*f444w_i2d.fits", recursive=True))[0]
with fits.open(ref) as h:
    wn = WCS(h['SCI'].header)
print(f"reference mosaic : {os.path.basename(ref)}")

kappa = np.load(f"{LIO}/kappa.npy")
ny, nx = kappa.shape
print(f"kappa grid       : {nx} x {ny}")

# binning: new pixel 1 covers old pixels 1..BIN  ->  crpix' = (crpix-0.5)/BIN + 0.5
wk = wn.deepcopy()
wk.wcs.crpix = (wn.wcs.crpix - 0.5) / BIN + 0.5
try:
    wk.wcs.cd = wn.wcs.cd * BIN
except Exception:
    wk.wcs.cdelt = wn.wcs.cdelt * BIN
wk.array_shape = kappa.shape
scale = np.abs(wk.pixel_scale_matrix[1, 1]) * 3600
print(f"coarse pix scale : {scale:.3f} arcsec/px "
      f"({nx*scale/60:.2f}' x {ny*scale/60:.2f}' field)")

# ── 2. X-ray, reprojected onto the kappa grid ────────────────────────────────
with fits.open(XRAY) as h:
    xr_img, xr_hdr = h[0].data, h[0].header
xray, _ = reproject_interp((xr_img, WCS(xr_hdr)), wk, shape_out=kappa.shape)
print(f"chandra          : {xr_hdr['EXPOSURE']/1e3:.0f} ks reprojected")

# ── 3. NFW convergence template at DM_NW / DM_SE ─────────────────────────────
cos = FlatLambdaCDM(H0=70, Om0=0.3)
DA  = cos.angular_diameter_distance(Z_CL).to(u.kpc).value      # kpc
rhoc = cos.critical_density(Z_CL).to(u.Msun / u.kpc**3).value

def nfw_sigma(Rkpc, M200, conc):
    """Projected NFW surface density, Wright & Brainerd (2000). Arbitrary norm."""
    r200 = (3 * M200 / (4 * np.pi * 200 * rhoc)) ** (1/3.)
    rs   = r200 / conc
    dc   = (200/3.) * conc**3 / (np.log(1+conc) - conc/(1+conc))
    x    = np.clip(Rkpc / rs, 1e-6, None)
    f    = np.empty_like(x)
    lo, hi = x < 1, x > 1
    eq   = ~(lo | hi)
    xl, xh = x[lo], x[hi]
    f[lo] = (1 - 2/np.sqrt(1-xl**2) * np.arctanh(np.sqrt((1-xl)/(1+xl)))) / (xl**2 - 1)
    f[hi] = (1 - 2/np.sqrt(xh**2-1) * np.arctan (np.sqrt((xh-1)/(1+xh)))) / (xh**2 - 1)
    f[eq] = 1/3.
    return 2 * rs * dc * rhoc * f

yy, xx = np.mgrid[0:ny, 0:nx]
sky = wk.pixel_to_world(xx, yy)
nfw = np.zeros(kappa.shape)
for h_ in (DM_NW, DM_SE):
    c = SkyCoord(ra=h_['ra']*u.deg, dec=h_['dec']*u.deg)
    sep_kpc = sky.separation(c).to(u.rad).value * DA
    nfw += nfw_sigma(sep_kpc, h_['M200'], h_['c'])
print("nfw template     : two halos, Wright & Brainerd projection")

# ── 4. correlate, with a shift null ──────────────────────────────────────────
def pearson(a, b, m):
    a, b = a[m], b[m]
    a = a - a.mean(); b = b - b.mean()
    return float((a*b).sum() / np.sqrt((a*a).sum() * (b*b).sum()))

good = np.isfinite(kappa) & np.isfinite(xray) & np.isfinite(nfw)
print(f"usable pixels    : {good.sum()} / {kappa.size}")

def shift_null(k, other, m, n=2000, seed=0):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        dy = rng.integers(1, ny); dx = rng.integers(1, nx)
        ks = np.roll(np.roll(k, dy, 0), dx, 1)
        mm = m & np.isfinite(ks)
        if mm.sum() > 100:
            out.append(pearson(ks, other, mm))
    return np.array(out)

print("\n" + "="*70)
print("RESULT   (read the z, not the r -- both fields are autocorrelated)")
print("="*70)
print(f"{'comparison':<26}{'r':>9}{'null mean':>11}{'null sd':>9}{'z':>8}")
res = {}
for name, other in [('kappa vs X-RAY (real)', xray), ('kappa vs NFW  (model)', nfw)]:
    r  = pearson(kappa, other, good)
    nl = shift_null(kappa, other, good)
    z  = (r - nl.mean()) / nl.std()
    res[name] = (r, z)
    print(f"{name:<26}{r:>9.4f}{nl.mean():>11.4f}{nl.std():>9.4f}{z:>8.2f}")

# cross-check: how similar are the two templates to each other?
print(f"\n{'X-RAY vs NFW':<26}{pearson(xray, nfw, good):>9.4f}"
      "   <- if ~1, the test cannot discriminate")

print("\n" + "="*70)
zx = res['kappa vs X-RAY (real)'][1]; zn = res['kappa vs NFW  (model)'][1]
print(f"  X-ray z = {zx:+.2f}      NFW z = {zn:+.2f}")
if abs(zx) > abs(zn) + 1:
    print("  ==> kappa tracks the X-RAY GAS more than the NFW model.")
elif abs(zn) > abs(zx) + 1:
    print("  ==> kappa tracks the NFW MODEL more than the gas.")
else:
    print("  ==> NO CLEAR PREFERENCE. The test does not discriminate here.")
print("="*70)
