#!/usr/bin/env python3
"""
pixel_vector_field.py — Native-pixel-resolution polarization (shear) vector field.

field_lines.py builds the (e1, e2) shear field on an 80x80 grid — plenty for the
streamplot/E-B discriminant, but coarse relative to the JWST pixel grid. This
script re-interpolates the SAME source measurements (source_catalog.fits) onto
the FULL native pixel grid instead, so "pixel by pixel" means what it says: one
(e1, e2) vector per JWST pixel, not per 80x80 bin.

Honest caveat, stated once here instead of re-derived every time this is read:
the underlying information content is still only ~2500 discrete background/
cluster galaxies. Interpolating to ~14M native pixels does not add new
measurements — it resamples the same smoothed field at higher density. The
smoothing scale (smooth_px, in NATIVE pixels here, matching field_lines.py's
physical smoothing radius) is the real resolution limit regardless of grid
size. This is useful for: overlay precision against the JWST image, absorbing
this into other pixel-registered products (X-ray, RM maps). It is not useful
for: claiming sub-smoothing-scale structure that isn't there.

Outputs (per label ALL/BG/CL), written to optical/jwst/prepped/pixel_field/:
    E1_<label>.npy, E2_<label>.npy   — float32, shape (ny, nx), native pixel grid
    quiver_<label>.png               — subsampled-for-legibility visualization
                                        (data is full-res; a quiver plot of 14M
                                        arrows is not readable, so display only)
"""

import sys
_sys_paths = [p for p in sys.path if '/usr/lib/python3/dist-packages' in p]
_user_paths = [p for p in sys.path if '/usr/lib/python3/dist-packages' not in p]
sys.path = _user_paths + _sys_paths

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator
from scipy.ndimage import gaussian_filter
from astropy.io import fits
from pathlib import Path
import warnings, time
warnings.filterwarnings('ignore')

REPO = Path(__file__).resolve().parents[2]   # BulletCluster/
OUT  = REPO / "optical/jwst/prepped"
CAT  = OUT / "source_catalog.fits"
PIXOUT = OUT / "pixel_field"
PIXOUT.mkdir(exist_ok=True)

FITS_ROOT = REPO / "optical/jwst/4598/mastDownload/JWST"
SMOOTH_PX = 60   # same physical smoothing radius as field_lines.py, now in native px

ref_fits = list(FITS_ROOT.rglob("*f444w_i2d.fits"))[0]
with fits.open(ref_fits) as h:
    ny, nx = h['SCI'].data.shape
print(f"Native grid: {nx} x {ny} = {nx*ny/1e6:.1f}M pixels")

with fits.open(CAT) as h:
    t = h[1].data
x_all = t['X_PX'].astype(float)
y_all = t['Y_PX'].astype(float)
a_all = t['A_PX'].astype(float)
b_all = t['B_PX'].astype(float)
theta_all = t['THETA'].astype(float)
is_bg = t['IS_BG'].astype(bool)
is_cl = t['IS_CLUSTER'].astype(bool)

def ellip_components(a, b, theta):
    denom = np.maximum(a + b, 1e-6)
    e = np.clip((a - b) / denom, 0, 0.9)
    return e, e * np.cos(2*theta), e * np.sin(2*theta)

e_all, e1_all, e2_all = ellip_components(a_all, b_all, theta_all)

# native pixel grid, built once, reused per label (cheap: coordinate arrays only)
gx = np.arange(nx, dtype=np.float32)
gy = np.arange(ny, dtype=np.float32)
GX, GY = np.meshgrid(gx, gy)

def interpolate_native(x, y, values):
    mask = np.isfinite(values) & np.isfinite(x) & np.isfinite(y)
    pts = np.column_stack([x[mask], y[mask]])
    vals = values[mask].astype(np.float64)
    lin = LinearNDInterpolator(pts, vals, fill_value=np.nan)
    grid = lin(GX, GY).astype(np.float32)
    # LinearNDInterpolator leaves NaN outside the convex hull of sources;
    # fill that with nearest-neighbour so the array has no holes, same
    # convention field_lines.py used (fill_value=0.0 via griddata), except
    # here we fill with nearest instead of zero to avoid a false E/B edge.
    nan_mask = np.isnan(grid)
    if nan_mask.any():
        near = NearestNDInterpolator(pts, vals)
        grid[nan_mask] = near(GX[nan_mask], GY[nan_mask]).astype(np.float32)
    return gaussian_filter(grid, sigma=SMOOTH_PX)

for label, mask in [('ALL', np.ones(len(x_all), bool)), ('BG', is_bg), ('CL', is_cl)]:
    t0 = time.time()
    x, y = x_all[mask], y_all[mask]
    e1, e2 = e1_all[mask], e2_all[mask]
    print(f"{label}: {mask.sum()} sources -> interpolating to {nx}x{ny} native grid...")

    E1 = interpolate_native(x, y, e1)
    E2 = interpolate_native(x, y, e2)
    np.save(PIXOUT / f"E1_{label}.npy", E1)
    np.save(PIXOUT / f"E2_{label}.npy", E2)
    print(f"  done in {time.time()-t0:.1f}s -> E1_{label}.npy, E2_{label}.npy "
          f"({E1.nbytes/1e6:.1f} MB each)")

    # legibility-bounded quiver: full-res data, sparse display sampling.
    # step chosen so ~120 arrows span the long axis regardless of native size.
    step = max(1, nx // 120)
    qx, qy = GX[::step, ::step], GY[::step, ::step]
    qe1, qe2 = E1[::step, ::step], E2[::step, ::step]
    qmag = np.sqrt(qe1**2 + qe2**2)

    # arrow length (data units) = magnitude/scale; size arrows to ~0.9*step
    # at the TYPICAL (median) magnitude so most arrows read clearly and only
    # strong outliers overlap their neighbours.
    typical_mag = np.median(qmag[qmag > 1e-6]) if (qmag > 1e-6).any() else 1.0
    scale = typical_mag / (0.9 * step)

    fig, ax = plt.subplots(figsize=(14, 7), facecolor='#090c12')
    ax.set_facecolor('#090c12')
    ax.quiver(qx, qy, qe1, qe2, qmag, cmap='cool', pivot='mid',
               angles='xy', scale_units='xy', scale=scale,
               width=0.0018, headwidth=3, headlength=4)
    ax.set_title(f'Bullet Cluster — pixel-resolution shear field ({label})\n'
                 f'{nx}x{ny} native grid ({nx*ny/1e6:.1f}M vectors), displayed every {step}px',
                 color='#c8d8e8', fontsize=10)
    ax.set_aspect('equal')
    ax.tick_params(colors='#5a7090')
    for spine in ax.spines.values():
        spine.set_edgecolor('#1e2a3a')
    fig.savefig(PIXOUT / f"quiver_{label}.png", dpi=150, bbox_inches='tight',
                facecolor='#090c12', edgecolor='none')
    plt.close()
    print(f"  -> quiver_{label}.png")

print("\nDone.")
