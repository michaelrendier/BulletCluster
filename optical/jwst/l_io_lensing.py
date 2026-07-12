#!/usr/bin/env python3
"""
l_io_lensing.py — Run the L_(I|O) Photon Path Engine (GR) on REAL Bullet
Cluster shear, for the first time.

The engine (ValaQuenta/modules/l_io_photon_path/maths.py) has existed since
2026-07-10 but its own docstring says it "requires real (gamma1, gamma2)
shear data as input -- see BulletCluster/optical/jwst/pixel_vector_field.py
for the source" and until now nothing had actually fed it that data. This
script closes that loop: it takes the native-pixel shear field this repo
already computed (E1_BG/E2_BG.npy, background-galaxy ellipticities only --
the physically appropriate lensing tracer, same choice field_lines.py made)
and treats it as (gamma1, gamma2) input to the exact Kaiser-Squires ->
Poisson -> deflection -> lens-equation pipeline.

Ainulindale/wiki/52 states: "if gravity can bend light, it can slingshot
it... The light's path was not clean. The path was L_(I|O)." The
deflection field alpha computed here IS that slingshot vector, everywhere
in the frame, at once -- not asserted, computed from the real measured
shear. Where |alpha| is large, a photon passing there is bent hardest:
the most "unclean" part of the path.

Working-resolution note: E1_BG/E2_BG are already Gaussian-smoothed at
sigma=60 native px (pixel_vector_field.py's SMOOTH_PX) -- that smoothing
scale, not the native pixel grid, is the real resolution limit. Running
the FFT lensing pipeline on all 14M native pixels would burn compute
reproducing information that isn't there. This script block-averages down
to a grid cell size close to the smoothing scale (BIN factor below) before
the Poisson solve -- same information content, ~60x fewer pixels.

Outputs -> optical/jwst/prepped/l_io/:
    kappa.npy, psi.npy, alpha1.npy, alpha2.npy, deflection_mag.npy
    l_io_deficit.json           -- raw stats of L_(I|O)-L = -psi
    l_io_slingshot_map.png      -- deflection magnitude + alpha vector field
"""
import sys, json
_sys_paths = [p for p in sys.path if '/usr/lib/python3/dist-packages' in p]
_user_paths = [p for p in sys.path if '/usr/lib/python3/dist-packages' not in p]
sys.path = _user_paths + _sys_paths

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/mnt/sdcard/ThePlace')
from ValaQuenta.modules.l_io_photon_path.maths import (
    bounded_lensing_pipeline, trace_photon, l_io_deficit,
)

REPO = Path("/mnt/sdcard/ThePlace/BulletCluster")
PIXOUT = REPO / "optical/jwst/prepped/pixel_field"
OUT = REPO / "optical/jwst/prepped/l_io"
OUT.mkdir(exist_ok=True)

FITS_ROOT = REPO / "optical/jwst/4598/mastDownload/JWST"
BIN = 32  # block-average factor; SMOOTH_PX=60 in pixel_vector_field.py

RA0, DEC0 = 104.6098, -55.9446
DM_NW_coord = SkyCoord(ra=104.6383*u.deg, dec=-55.9252*u.deg)
DM_SE_coord = SkyCoord(ra=104.5726*u.deg, dec=-55.9563*u.deg)
GAS_NW_coord = SkyCoord(ra=104.625*u.deg, dec=-55.930*u.deg)
GAS_SE_coord = SkyCoord(ra=104.569*u.deg, dec=-55.961*u.deg)

ref_fits = list(FITS_ROOT.rglob("*f444w_i2d.fits"))[0]
with fits.open(ref_fits) as h:
    wcs = WCS(h['SCI'].header)
pscl_native = abs(wcs.pixel_scale_matrix[1, 1]) * 3600  # arcsec/native px
print(f"Native pixel scale: {pscl_native:.5f} arcsec/px")

def sky2px(coord):
    x, y = wcs.world_to_pixel(coord)
    return float(x), float(y)

dm_nw_px, dm_se_px = sky2px(DM_NW_coord), sky2px(DM_SE_coord)
gas_nw_px, gas_se_px = sky2px(GAS_NW_coord), sky2px(GAS_SE_coord)

print("Loading native-pixel BG shear field (E1_BG, E2_BG)...")
E1 = np.load(PIXOUT / "E1_BG.npy")
E2 = np.load(PIXOUT / "E2_BG.npy")
ny, nx = E1.shape
print(f"Native grid: {nx}x{ny}")

def block_average(a, bin_):
    ny, nx = a.shape
    ny_c, nx_c = ny // bin_, nx // bin_
    a = a[:ny_c*bin_, :nx_c*bin_]
    return a.reshape(ny_c, bin_, nx_c, bin_).mean(axis=(1, 3))

gamma1 = block_average(E1, BIN)
gamma2 = block_average(E2, BIN)
ny_c, nx_c = gamma1.shape
pscl_coarse = pscl_native * BIN
print(f"Coarse grid for lensing solve: {nx_c}x{ny_c}  ({pscl_coarse:.3f} arcsec/px)")

print("Running bounded_lensing_pipeline (Kaiser-Squires -> Poisson -> deflection)...")
result = bounded_lensing_pipeline(gamma1, gamma2, pscl_coarse, taper_frac=0.1, pad_factor=2.0)
kappa, psi, alpha1, alpha2 = result['kappa'], result['psi'], result['alpha1'], result['alpha2']

# theta = apparent (clean) position in arcsec, on the coarse grid
gx = np.arange(nx_c) * pscl_coarse
gy = np.arange(ny_c) * pscl_coarse
theta1, theta2 = np.meshgrid(gx, gy)

photon = trace_photon(theta1, theta2, alpha1, alpha2)
deficit = l_io_deficit(psi)

np.save(OUT / "kappa.npy", kappa)
np.save(OUT / "psi.npy", psi)
np.save(OUT / "alpha1.npy", alpha1)
np.save(OUT / "alpha2.npy", alpha2)
np.save(OUT / "deflection_mag.npy", photon['deflection_mag'])
with open(OUT / "l_io_deficit.json", 'w') as f:
    json.dump({
        'l_io_minus_L_stats_arcsec': deficit,
        'deflection_mag_arcsec': {
            'mean': float(np.nanmean(photon['deflection_mag'])),
            'std': float(np.nanstd(photon['deflection_mag'])),
            'max': float(np.nanmax(photon['deflection_mag'])),
            'median': float(np.nanmedian(photon['deflection_mag'])),
        },
        'bin_factor': BIN,
        'pixel_scale_coarse_arcsec': pscl_coarse,
        'grid_shape': [ny_c, nx_c],
    }, f, indent=2)

print("\nL_(I|O) - L  (= -psi, Fermat potential deficit), raw stats [arcsec]:")
for k, v in deficit.items():
    print(f"  {k}: {v:.5f}")
print(f"\n|alpha| (deflection / slingshot magnitude) [arcsec]:")
print(f"  mean={np.nanmean(photon['deflection_mag']):.5f}  "
      f"max={np.nanmax(photon['deflection_mag']):.5f}  "
      f"median={np.nanmedian(photon['deflection_mag']):.5f}")

# ── Visualization ─────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(20, 7), facecolor='#090c12')

def dm_markers(ax, scale):
    for (px, py), lbl, col in [
        (dm_nw_px, 'DM NW', '#7ab4ff'), (dm_se_px, 'DM SE\n(bullet)', '#4af0ff'),
        (gas_nw_px, 'Gas NW', '#ff6090'), (gas_se_px, 'Gas SE\n(shocked)', '#ff8030'),
    ]:
        cx, cy = px/scale, py/scale
        if 0 < cx < nx_c and 0 < cy < ny_c:
            ax.scatter(cx, cy, s=140, marker='+', color=col, linewidths=2, zorder=10)
            ax.text(cx+2, cy+2, lbl, color=col, fontsize=7, zorder=11,
                    path_effects=[pe.withStroke(linewidth=2, foreground='black')])

# Panel 1: kappa (convergence, reconstructed from real shear)
ax = axes[0]; ax.set_facecolor('#090c12')
vlim = np.nanpercentile(np.abs(kappa), 98)
im = ax.imshow(kappa, origin='lower', cmap='RdBu_r', vmin=-vlim, vmax=vlim, aspect='equal')
dm_markers(ax, BIN)
ax.set_title('kappa (Kaiser-Squires, real BG shear)\nmass-sheet degenerate -- relative structure only',
              color='#c8d8e8', fontsize=9)
fig.colorbar(im, ax=ax, shrink=0.8)

# Panel 2: L_(I|O) - L = -psi (Fermat potential deficit)
ax = axes[1]; ax.set_facecolor('#090c12')
vlim = np.nanpercentile(np.abs(psi), 98)
im = ax.imshow(-psi, origin='lower', cmap='PuOr', vmin=-vlim, vmax=vlim, aspect='equal')
dm_markers(ax, BIN)
ax.set_title('L_(I|O) - L  :=  -psi(theta)\nwiki/52 target #1, computed from real shear',
              color='#c8d8e8', fontsize=9)
fig.colorbar(im, ax=ax, shrink=0.8)

# Panel 3: |alpha| deflection/slingshot magnitude + vector field
ax = axes[2]; ax.set_facecolor('#090c12')
dmag = photon['deflection_mag']
im = ax.imshow(dmag, origin='lower', cmap='inferno',
               vmin=0, vmax=np.nanpercentile(dmag, 98), aspect='equal')
step = max(1, nx_c // 40)
qy_, qx_ = np.mgrid[0:ny_c:step, 0:nx_c:step]
ax.quiver(qx_, qy_, alpha1[::step, ::step], alpha2[::step, ::step],
          color='#4af0ff', scale_units='xy', angles='xy',
          scale=np.nanpercentile(dmag, 95)/(0.8*step) or 1.0,
          width=0.0025, headwidth=3)
dm_markers(ax, BIN)
ax.set_title('|alpha|  --  the slingshot vector field\nbeta = theta - alpha : the actual (unclean) path deviates HERE',
              color='#c8d8e8', fontsize=9)
fig.colorbar(im, ax=ax, shrink=0.8)

for ax in axes:
    ax.tick_params(colors='#5a7090')
    for spine in ax.spines.values():
        spine.set_edgecolor('#1e2a3a')

fig.suptitle('Bullet Cluster -- L_(I|O) Photon Path Engine (GR) on real JWST F444W shear\n'
             f'{nx_c}x{ny_c} grid, {pscl_coarse:.2f}"/px  |  '
             'wiki/52: "the path was not clean. The path was L_(I|O)."',
             color='#c8d8e8', fontsize=11)
fig.savefig(OUT / "l_io_slingshot_map.png", dpi=150, bbox_inches='tight',
            facecolor='#090c12', edgecolor='none')
plt.close()
print(f"\n-> {OUT / 'l_io_slingshot_map.png'}")
print("Done.")
