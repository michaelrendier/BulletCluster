#!/usr/bin/env python3
"""
source_extract.py — JWST source extraction + cluster/background separation
                    for the Bullet Cluster gradient test.

Steps:
  1. Load F277W + F444W (matched pixel scale 0.060 arcsec/px)
  2. Background estimate + subtraction
  3. Source detection (SEP — SExtractor in Python)
  4. Dual-image photometry: detect on F444W, measure on both filters
  5. Color separation: F277W-F444W colour splits cluster (red) from background (blue)
  6. Radial profiles at DM_SE (in field), GAS_NW, CENTROID
     — cluster members  → trace stellar mass (should be NFW / center-bright)
     — background only  → proxy for lensing convergence (the actual DM gradient test)
  7. Gradient sign report: + (edge-bright, wave) or - (center-bright, particle)

Output: prepped/source_catalog.fits  +  prepped/gradient_report.txt
"""

import numpy as np
import sep
from pathlib import Path
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
import warnings
warnings.filterwarnings('ignore')

# ── Paths & constants ─────────────────────────────────────────────────────────
DATA  = Path("/media/rendier/0123-4567/bullet_cluster/optical/jwst/4598/mastDownload/JWST")
OUT   = Path("/media/rendier/0123-4567/bullet_cluster/optical/jwst/prepped")
OUT.mkdir(exist_ok=True)

CENTROID = SkyCoord(ra=104.6098*u.deg, dec=-55.9446*u.deg)
DM_NW    = SkyCoord(ra=104.6383*u.deg, dec=-55.9252*u.deg)
DM_SE    = SkyCoord(ra=104.5726*u.deg, dec=-55.9563*u.deg)
GAS_NW   = SkyCoord(ra=104.625 *u.deg, dec=-55.930 *u.deg)
GAS_SE   = SkyCoord(ra=104.569 *u.deg, dec=-55.961 *u.deg)
PEAKS    = {'CENTROID': CENTROID, 'DM_SE': DM_SE, 'GAS_NW': GAS_NW, 'GAS_SE': GAS_SE}

# Cluster redshift + colour cut
Z_CLUSTER      = 0.296
# F277W − F444W colour: cluster red-sequence members are redder
# At z=0.296: rest-frame ~2.1μm and ~3.4μm → old stars dominate both
# Background galaxies at z>0.5 are bluer in F277W−F444W
COLOUR_CUT     = 0.15   # mag; sources REDDER than this → cluster members
DETECT_THRESH  = 5.0    # sigma above background (JWST is deep, 3σ overloads buffer)
MIN_AREA_PX    = 9      # minimum 3x3 pixel island (prime 3!)

# Radial profile bins in arcmin (prime-spaced physical scale)
R_BINS_ARCMIN  = np.array([0.05, 0.10, 0.15, 0.20, 0.30, 0.40,
                            0.55, 0.70, 0.90, 1.10, 1.35, 1.60])


# ── Loaders ───────────────────────────────────────────────────────────────────
def find_fits(pattern):
    hits = list(DATA.rglob(pattern))
    return hits[0] if hits else None

def load(pattern):
    p = find_fits(pattern)
    if p is None:
        raise FileNotFoundError(f"No file matching {pattern}")
    print(f"  Loading {p.name}")
    with fits.open(p) as h:
        data = h['SCI'].data.astype(np.float32)
        wcs  = WCS(h['SCI'].header)
        pscl = abs(wcs.pixel_scale_matrix[1,1]) * 3600  # arcsec/px
    return data, wcs, pscl


# ── Background estimation ──────────────────────────────────────────────────────
def estimate_bkg(data, box=128, filt=5):
    d = np.array(data, dtype=np.float64)
    bkg = sep.Background(d, bw=box, bh=box, fw=filt, fh=filt)
    return bkg


# ── Source detection (SEP) ────────────────────────────────────────────────────
def detect(data, bkg, thresh=DETECT_THRESH, minarea=MIN_AREA_PX):
    d   = np.array(data, dtype=np.float64)
    sub = d - bkg.back()
    err = bkg.rms()
    sep.set_extract_pixstack(5_000_000)
    objs = sep.extract(sub, thresh, err=err, minarea=minarea,
                       deblend_nthresh=32, deblend_cont=0.005)
    return objs, sub


# ── Dual-image photometry ─────────────────────────────────────────────────────
def aperture_flux(data, objs, r_px=3.0):
    """Circular aperture flux on data at positions from objs."""
    d = np.array(data, dtype=np.float64)
    flux, ferr, flag = sep.sum_circle(d, objs['x'], objs['y'],
                                      r_px * np.ones(len(objs)),
                                      err=np.sqrt(np.abs(d) + 1e-12))
    return flux, ferr, flag


# ── Colour-based cluster/background split ─────────────────────────────────────
def colour_split(flux277, flux444, colour_cut=COLOUR_CUT):
    """
    F277W − F444W in magnitudes (AB system, same zero-point since both in MJy/sr).
    Redder (larger value) = cluster member at z=0.296.
    Bluer (smaller value) = background galaxy at z>0.3 (the lensing sources).
    Returns: is_cluster (bool array)
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        colour = -2.5 * np.log10(np.abs(flux277) / np.abs(flux444))
    is_cluster  = colour > colour_cut
    is_bg       = ~is_cluster & np.isfinite(colour)
    return is_cluster, is_bg, colour


# ── Radial number density profile ─────────────────────────────────────────────
def number_density_profile(x_px, y_px, cx, cy, pscl_arcsec, r_bins_arcmin):
    """
    Count sources in annuli centred on (cx,cy).
    Returns (r_mid_arcmin, density_per_arcmin2, n_sources).
    """
    r_bins_px  = r_bins_arcmin * 60.0 / pscl_arcsec
    dx = x_px - cx;  dy = y_px - cy
    r  = np.sqrt(dx**2 + dy**2)

    r_mid, dens, ns = [], [], []
    r_in = 0.0
    for r_out in r_bins_px:
        ring = (r >= r_in) & (r < r_out)
        n    = ring.sum()
        # annulus area in arcmin²
        area = np.pi * ((r_out * pscl_arcsec / 60.)**2 -
                        (r_in  * pscl_arcsec / 60.)**2)
        r_mid.append(0.5 * (r_in + r_out) * pscl_arcsec / 60.)
        dens.append(n / area if area > 0 else 0)
        ns.append(n)
        r_in = r_out

    return np.array(r_mid), np.array(dens), np.array(ns, dtype=int)


# ── Gradient sign ─────────────────────────────────────────────────────────────
def grad_sign(r, density, outer_frac=0.5):
    """Linear fit to outer half of profile. Sign = gradient direction."""
    mid = max(1, int(len(r) * (1.0 - outer_frac)))
    if len(r[mid:]) < 2:
        return 0, 0.0
    slope = np.polyfit(r[mid:], density[mid:], 1)[0]
    return int(np.sign(slope)), slope


# ══════════════════════════════════════════════════════════════════════════════
print("=" * 62)
print(" Bullet Cluster JWST Source Extraction")
print("=" * 62)

print("\n[1] Loading F444W (detection image)...")
d444, wcs, pscl = load("*f444w_i2d.fits")
ny, nx = d444.shape

print("\n[2] Loading F277W (colour image)...")
d277, wcs277, _ = load("*f277w_i2d.fits")

print(f"\n  Image: {nx}×{ny} px  |  {pscl:.4f} arcsec/px")

# Pixel coords of all peaks
def sky2px(coord):
    x, y = wcs.world_to_pixel(coord)
    return float(x), float(y)

peak_px = {k: sky2px(v) for k, v in PEAKS.items()}
print("\n  Peak pixel positions (F444W frame):")
for k, (px, py) in peak_px.items():
    flag = "" if (0 < px < nx and 0 < py < ny) else "  ← OUTSIDE"
    print(f"    {k:<12} ({px:7.1f}, {py:7.1f}){flag}")

print("\n[3] Background estimation & subtraction (F444W)...")
bkg444 = estimate_bkg(d444)
print(f"  Global bkg: {bkg444.globalback:.4e} ± {bkg444.globalrms:.4e} MJy/sr")

print("\n[4] Source detection on F444W...")
objs, sub444 = detect(d444, bkg444)
print(f"  Detected {len(objs)} sources  (thresh={DETECT_THRESH}σ, minarea={MIN_AREA_PX}px)")

# Repeat for F277W
print("\n[5] Background estimation (F277W)...")
bkg277 = estimate_bkg(d277)
_, sub277 = detect(d277, bkg277)

print("\n[6] Dual-image photometry (aperture r=3px on both filters)...")
fl444, fe444, fg444 = aperture_flux(d444, objs, r_px=3.0)
fl277, fe277, fg277 = aperture_flux(d277, objs, r_px=3.0)

print("\n[7] Colour separation (F277W − F444W)...")
is_cl, is_bg, colour = colour_split(fl277, fl444)
n_cl  = is_cl.sum();  n_bg = is_bg.sum()
print(f"  Cluster members (red):   {n_cl:5d}  ({100*n_cl/len(objs):.1f}%)")
print(f"  Background (blue):       {n_bg:5d}  ({100*n_bg/len(objs):.1f}%)")
print(f"  Ambiguous/saturated:     {len(objs)-n_cl-n_bg:5d}")

# ── Save source catalog ───────────────────────────────────────────────────────
ra_arr, dec_arr = wcs.pixel_to_world_values(objs['x'], objs['y'])
col_x    = fits.Column(name='X_PX',     format='E', array=objs['x'])
col_y    = fits.Column(name='Y_PX',     format='E', array=objs['y'])
col_ra   = fits.Column(name='RA',       format='D', array=ra_arr)
col_dec  = fits.Column(name='DEC',      format='D', array=dec_arr)
col_f444 = fits.Column(name='FLUX_F444',format='E', array=fl444)
col_f277 = fits.Column(name='FLUX_F277',format='E', array=fl277)
col_col  = fits.Column(name='COLOUR',   format='E', array=colour)
col_cl   = fits.Column(name='IS_CLUSTER',format='L',array=is_cl)
col_bg   = fits.Column(name='IS_BG',   format='L', array=is_bg)
col_a    = fits.Column(name='A_PX',    format='E', array=objs['a'])
col_b    = fits.Column(name='B_PX',    format='E', array=objs['b'])
col_th   = fits.Column(name='THETA',   format='E', array=objs['theta'])
col_e    = fits.Column(name='ELLIP',   format='E',
                        array=1.0 - objs['b']/np.maximum(objs['a'], 1e-6))

hdu = fits.BinTableHDU.from_columns([
    col_x, col_y, col_ra, col_dec,
    col_f444, col_f277, col_col, col_cl, col_bg,
    col_a, col_b, col_th, col_e
])
hdu.header['PIXSCL']  = (pscl,    'arcsec/px')
hdu.header['ZCLUST']  = (Z_CLUSTER,'cluster redshift')
hdu.header['COLCUT']  = (COLOUR_CUT,'F277-F444 colour cut (mag)')
hdu.header['NDET']    = (len(objs), 'total detections')
hdu.header['NCL']     = (n_cl,     'cluster members')
hdu.header['NBG']     = (n_bg,     'background sources')
cat_path = OUT / "source_catalog.fits"
fits.HDUList([fits.PrimaryHDU(), hdu]).writeto(cat_path, overwrite=True)
print(f"\n  Catalog saved: {cat_path}")

# ── Radial profiles + gradient test ───────────────────────────────────────────
print("\n[8] Radial profiles + gradient test")
print("=" * 62)
print(f"{'Peak':<12} {'Sample':<12} {'Gradient':>10}  {'Slope':>14}  {'Interpretation'}")
print("-" * 62)

report_lines = []

for peak_name, (cx, cy) in peak_px.items():
    if not (0 < cx < nx and 0 < cy < ny):
        continue

    for label, mask in [('ALL', np.ones(len(objs), bool)),
                         ('CLUSTER', is_cl),
                         ('BG_ONLY', is_bg)]:
        xs = objs['x'][mask];  ys = objs['y'][mask]
        if len(xs) < 5:
            continue
        r, dens, ns = number_density_profile(xs, ys, cx, cy, pscl, R_BINS_ARCMIN)
        sign, slope  = grad_sign(r, dens)
        sym   = {1: '+', -1: '-', 0: '~'}[sign]
        interp = {1: 'edge-bright → wave?',
                  -1: 'center-bright → NFW?',
                   0: 'flat'}[sign]
        line = f"{peak_name:<12} {label:<12} {sym:>10}   {slope:>13.3e}  {interp}"
        print(line)
        report_lines.append(line)

        # Save profile
        np.savez(OUT / f"profile_{peak_name}_{label}.npz",
                 r_arcmin=r, density=dens, n_sources=ns,
                 slope=slope, gradient_sign=sign)

# ── Write report ──────────────────────────────────────────────────────────────
rpt = OUT / "gradient_report.txt"
with open(rpt, 'w') as f:
    f.write("Bullet Cluster JWST Gradient Report\n")
    f.write(f"Colour cut F277W-F444W: {COLOUR_CUT} mag  (redder = cluster)\n")
    f.write(f"Detection: {len(objs)} sources  |  cluster: {n_cl}  |  bg: {n_bg}\n\n")
    f.write(f"{'Peak':<12} {'Sample':<12} {'Gradient':>10}  {'Slope':>14}  Interpretation\n")
    f.write("-"*70 + "\n")
    for l in report_lines:
        f.write(l + "\n")

print(f"\nReport: {rpt}")
print("\nNext: interference_sim.py — cymatic prediction for comparison")
