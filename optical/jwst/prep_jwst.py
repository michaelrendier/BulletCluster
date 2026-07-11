#!/usr/bin/env python3
"""
prep_jwst.py — JWST data prep for Bullet Cluster gradient analysis.

Coordinate system (matches 3D viewer / bullet_cluster.scad):
  x = East   (RA  decreasing → East positive)
  y = North  (Dec increasing → North positive)
  1 unit = 100 kpc  (1 arcmin ≈ 2.06 units at z=0.296)

Prime resolution ladder (F090W at 0.030 arcsec/px):
  Prime 1:  1 px  = 0.030 arcsec = 0.09 kpc   ← atomic sample
  Prime 2:  2 px  = 0.060 arcsec = 0.18 kpc   ← gradient emerges
  Prime 3:  3 px  = 0.090 arcsec = 0.27 kpc   ← curvature emerges
  Prime 5:  5 px  = 0.150 arcsec = 0.46 kpc
  Prime 7:  7 px  = 0.210 arcsec = 0.64 kpc
  ...
  Prime ~2000: ~1 arcmin = DM halo scale       ← gradient test lives here

Outputs (written to optical/jwst/prepped/):
  centroid_cutouts/   — stamp images centred on DM NW and DM SE for each filter
  radial_profiles/    — radial brightness profiles at each DM peak
  source_catalog/     — detected source list with positions + fluxes
  wcs_grid.fits       — common WCS grid for reprojecting all filters
"""

import numpy as np
from pathlib import Path
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.nddata import Cutout2D

# ── Paths ─────────────────────────────────────────────────────────────────────
JWST_DIR  = Path("/media/rendier/0123-4567/bullet_cluster/optical/jwst")
DATA_DIR  = JWST_DIR / "4598/mastDownload/JWST"
OUT_DIR   = JWST_DIR / "prepped"
OUT_DIR.mkdir(exist_ok=True)
(OUT_DIR / "centroid_cutouts").mkdir(exist_ok=True)
(OUT_DIR / "radial_profiles").mkdir(exist_ok=True)

# ── Cluster geometry (from constants.py / CLAUDE_PRIMER) ─────────────────────
CENTROID = SkyCoord(ra=104.6098*u.deg, dec=-55.9446*u.deg)
DM_NW    = SkyCoord(ra=104.6383*u.deg, dec=-55.9252*u.deg)  # Clowe+2006
DM_SE    = SkyCoord(ra=104.5726*u.deg, dec=-55.9563*u.deg)  # Clowe+2006
GAS_NW   = SkyCoord(ra=104.625 *u.deg, dec=-55.930 *u.deg)  # Markevitch+2002
GAS_SE   = SkyCoord(ra=104.569 *u.deg, dec=-55.961 *u.deg)  # Markevitch+2002
MERGER_PA = 135.0  # degrees, NW→SE

# Cutout size: 3 arcmin = covers DM halo + surrounding field for profile
CUTOUT_SIZE = 3.0 * u.arcmin

# Radial profile bins: prime-spaced out to 1.5 arcmin
# These primes are in pixel units of F090W (0.030 arcsec/px)
# 1 arcmin = 2000 px at F090W; we sample at prime pixel radii mapped to arcmin
PRIME_BINS_ARCMIN = np.array([
    2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,
    59,61,67,71,73,79,83,89,97
]) * 0.030 / 60.0  # px → arcmin (F090W scale)

# Also bin at physical scales: prime × 10 kpc steps (1 arcmin ≈ 206 kpc)
KPC_PER_ARCMIN = 206.0
PRIME_BINS_KPC  = np.array([2,3,5,7,11,13,17,19,23,29,31,37,41,43,47]) * 10.0
PRIME_BINS_ARCMIN_PHYSICAL = PRIME_BINS_KPC / KPC_PER_ARCMIN


def load_filter(fname):
    """Load SCI extension, return (data, wcs, header)."""
    # Files land in subdirs: DATA_DIR/<filter_dir>/<fname>
    path = DATA_DIR / fname
    if not path.exists():
        # Try one level deep (astroquery puts files in per-obs subdirs)
        matches = list(DATA_DIR.rglob(fname))
        if not matches:
            return None, None, None
        path = matches[0]
    with fits.open(path) as hdul:
        data = hdul['SCI'].data.astype(np.float32)
        hdr  = hdul['SCI'].header
        wcs  = WCS(hdr)
    return data, wcs, hdr


def sky_to_pix(coord, wcs):
    """SkyCoord → (x, y) pixel floats."""
    x, y = wcs.world_to_pixel(coord)
    return float(x), float(y)


def radial_profile(data, cx, cy, bins_px, mask_nan=True):
    """
    Compute mean surface brightness in annular bins centred on (cx,cy).
    bins_px: array of outer radii in pixels (inner = previous bin outer).
    Returns (r_mid_px, mean_flux, std_flux, n_pixels).
    """
    ny, nx = data.shape
    yy, xx = np.ogrid[:ny, :nx]
    rr = np.sqrt((xx - cx)**2 + (yy - cy)**2)

    if mask_nan:
        valid = np.isfinite(data)
    else:
        valid = np.ones_like(data, dtype=bool)

    r_mid, mean_f, std_f, n_px = [], [], [], []
    r_inner = 0.0
    for r_outer in bins_px:
        ring = valid & (rr >= r_inner) & (rr < r_outer)
        if ring.sum() > 0:
            vals = data[ring]
            r_mid.append(0.5 * (r_inner + r_outer))
            mean_f.append(np.nanmean(vals))
            std_f.append(np.nanstd(vals))
            n_px.append(ring.sum())
        r_inner = r_outer

    return (np.array(r_mid), np.array(mean_f),
            np.array(std_f),  np.array(n_px, dtype=int))


def gradient_sign(r, flux):
    """
    Fit a linear gradient to flux vs r (in the outer half of the profile).
    Returns: +1 (edge-bright, wave/cymatic), -1 (center-bright, NFW/particle), 0 (flat).
    """
    mid = len(r) // 2
    if mid < 2:
        return 0, 0.0
    slope = np.polyfit(r[mid:], flux[mid:], 1)[0]
    return int(np.sign(slope)), slope


# ── Main processing loop ──────────────────────────────────────────────────────
FILTERS = {
    'f090w': 'jw04598-o001_t001_nircam_clear-f090w_i2d.fits',
    'f277w': 'jw04598-o001_t001_nircam_clear-f277w_i2d.fits',
    'f444w': 'jw04598-o001_t001_nircam_clear-f444w_i2d.fits',
}

PEAKS = {
    'DM_NW': DM_NW,
    'DM_SE': DM_SE,
    'GAS_NW': GAS_NW,
    'GAS_SE': GAS_SE,
    'CENTROID': CENTROID,
}

results = {}  # filter → peak → profile

for filt, fname in FILTERS.items():
    print(f"\n{'='*60}")
    print(f"Processing {filt}: {fname}")
    data, wcs, hdr = load_filter(fname)
    if data is None:
        print(f"  [MISSING — skipping]")
        continue

    ny, nx = data.shape
    pscale = abs(wcs.pixel_scale_matrix[1,1]) * 3600  # arcsec/px
    print(f"  {nx} x {ny} px   {pscale:.4f} arcsec/px")
    print(f"  Data range: {np.nanmin(data):.4e} – {np.nanmax(data):.4e} MJy/sr")
    print(f"  Finite pixels: {np.isfinite(data).sum()} / {data.size}")

    # Convert prime bins from F090W px to this filter's px
    bins_px = PRIME_BINS_ARCMIN * 60.0 / pscale  # arcmin → px

    results[filt] = {}

    for peak_name, peak_coord in PEAKS.items():
        cx, cy = sky_to_pix(peak_coord, wcs)
        if not (0 < cx < nx and 0 < cy < ny):
            print(f"  {peak_name}: outside image ({cx:.0f}, {cy:.0f})")
            continue

        print(f"  {peak_name}: pixel ({cx:.1f}, {cy:.1f})")

        # Cutout stamp
        stamp = Cutout2D(data, peak_coord, CUTOUT_SIZE, wcs=wcs, mode='partial')
        stamp_path = OUT_DIR / "centroid_cutouts" / f"{filt}_{peak_name}_cutout.fits"
        fits.writeto(stamp_path, stamp.data.astype(np.float32),
                     stamp.wcs.to_header(), overwrite=True)

        # Radial profile
        scx, scy = sky_to_pix(peak_coord, stamp.wcs)
        r_px, mean_f, std_f, n_px = radial_profile(stamp.data, scx, scy, bins_px)
        r_arcmin = r_px * pscale / 60.0

        # Gradient sign
        sign, slope = gradient_sign(r_arcmin, mean_f)
        grad_label = {1: '+  (EDGE-BRIGHT → wave/cymatic)',
                      -1: '-  (CENTER-BRIGHT → NFW/particle)',
                       0: '0  (flat)'}[sign]

        print(f"    Radial gradient: {grad_label}  (slope={slope:.4e})")

        results[filt][peak_name] = {
            'r_arcmin': r_arcmin,
            'r_kpc':    r_arcmin * KPC_PER_ARCMIN,
            'mean_flux': mean_f,
            'std_flux':  std_f,
            'n_pixels':  n_px,
            'gradient_sign': sign,
            'gradient_slope': slope,
            'cx_px': cx, 'cy_px': cy,
        }

        # Save profile
        prof_path = OUT_DIR / "radial_profiles" / f"{filt}_{peak_name}_profile.npz"
        np.savez(prof_path, **results[filt][peak_name])

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("GRADIENT SUMMARY")
print(f"{'='*60}")
print(f"{'Peak':<12}  {'Filter':<8}  {'Sign':<4}  {'Slope':>12}  {'Interpretation'}")
print("-"*60)
for filt in results:
    for peak in results[filt]:
        r = results[filt][peak]
        s = r['gradient_sign']
        label = {1:'+ wave?', -1:'- particle?', 0:'flat'}[s]
        print(f"{peak:<12}  {filt:<8}  {s:>+d}    {r['gradient_slope']:>12.4e}  {label}")

print(f"\nOutputs written to: {OUT_DIR}")
print("Next: run interference_sim.py to generate the cymatic prediction for comparison")
