#!/usr/bin/env python3
"""
dust_confound_test.py — Proof-of-the-opposite-effect: does ordinary
foreground "stuff" (zodiacal/interstellar dust scattering) upset a
polarization field on its own, and if so, can the existing pipeline tell
it apart from the real DM signal?

Cody, 2026-07-18: before trusting L_(I|O)'s signal on the Bullet Cluster
(or the 7 new SPARC/JWST galaxies), we need the negative case demonstrated,
not assumed — the "Brian May dust" precedent (his PhD: zodiacal light
scattering as a real, physically taken-seriously foreground contaminant in
faint diffuse-light astronomy). This script builds a synthetic dust-only
polarization field, runs it through the EXACT SAME machinery already used
on the real data (field_lines.py's E/B decomposition; l_io_photon_path's
Kaiser-Squires -> Poisson -> deflection pipeline), and checks two things:

  1. DOES dust alone perturb the field?  (it should — proving "stuff" is a
     real confound, not a strawman)
  2. Is the dust-only perturbation's SPATIAL SIGNATURE distinguishable from
     the real BG shear's signature — specifically, is it un-peaked at
     DM_NW/DM_SE (Clowe+2006), unlike the real signal?

Dust model (documented, not hidden): zodiacal/interstellar scattering
varies on degree-to-sky scales, far larger than this ~7'x16' JWST F444W
tile — so across THIS frame it is modelled as a smooth, large-scale,
low-amplitude polarization field: fixed intrinsic angle (assumed, since the
real Sun-target scattering angle at each exposure's epoch is not looked up
here) plus a large-scale-smoothed random column-density modulation
(grain-density fluctuations), amplitude set to a realistic zodiacal
polarization degree (~1-3%), completely independent of DM_NW/DM_SE/GAS_NW/
GAS_SE coordinates by construction. This is a LIMITATION worth being
explicit about: the exact intrinsic angle would need the real Sun-observer-
target ecliptic geometry per exposure epoch, not assumed here.
"""
import sys, json
_sys_paths  = [p for p in sys.path if '/usr/lib/python3/dist-packages' in p]
_user_paths = [p for p in sys.path if '/usr/lib/python3/dist-packages' not in p]
sys.path = _user_paths + _sys_paths

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from scipy.ndimage import gaussian_filter
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/storage/emulated/0/ThePlace')
from ValaQuenta.modules.l_io_photon_path.maths import bounded_lensing_pipeline

REPO   = Path("/storage/emulated/0/ThePlace/BulletCluster")
PIXOUT = REPO / "optical/jwst/prepped/pixel_field"
FITS_ROOT = REPO / "optical/jwst/4598/mastDownload/JWST"
OUT    = REPO / "optical/jwst/prepped/dust_confound"
OUT.mkdir(parents=True, exist_ok=True)

BIN = 32  # match l_io_lensing.py's coarse-grid factor

DM_NW_coord  = SkyCoord(ra=104.6383*u.deg, dec=-55.9252*u.deg)
DM_SE_coord  = SkyCoord(ra=104.5726*u.deg, dec=-55.9563*u.deg)
GAS_NW_coord = SkyCoord(ra=104.625 *u.deg, dec=-55.930 *u.deg)
GAS_SE_coord = SkyCoord(ra=104.569 *u.deg, dec=-55.961 *u.deg)

ref_fits = list(FITS_ROOT.rglob("*f444w_i2d.fits"))[0]
with fits.open(ref_fits) as h:
    wcs = WCS(h['SCI'].header)
pscl_native = abs(wcs.pixel_scale_matrix[1, 1]) * 3600  # arcsec/native px

def sky2px(coord):
    x, y = wcs.world_to_pixel(coord)
    return float(x), float(y)

dm_nw_px, dm_se_px   = sky2px(DM_NW_coord),  sky2px(DM_SE_coord)
gas_nw_px, gas_se_px = sky2px(GAS_NW_coord), sky2px(GAS_SE_coord)

print("Loading real native-pixel BG shear field (E1_BG, E2_BG)...")
E1_real = np.load(PIXOUT / "E1_BG.npy")
E2_real = np.load(PIXOUT / "E2_BG.npy")
ny, nx  = E1_real.shape
print(f"Native grid: {nx}x{ny}  ({pscl_native:.5f} arcsec/px)")

# ── Dust/zodiacal-scattering confound model ──────────────────────────────
rng = np.random.default_rng(seed=7)          # fixed seed, reproducible
DUST_AMP        = 0.02                        # ~2% polarization degree — realistic zodiacal level
DUST_ANGLE_DEG  = 15.0                        # assumed intrinsic EVPA, NOT the merger PA (135 deg)
DUST_SMOOTH_PX  = 900                         # much larger than SMOOTH_PX=60 used for the real field
                                               # (dust column density varies on far larger scales
                                               # than this ~7'x16' tile)

print(f"\nBuilding synthetic dust confound: amp={DUST_AMP}, angle={DUST_ANGLE_DEG} deg, "
      f"smooth={DUST_SMOOTH_PX}px (vs real field's 60px)")

# large-scale grain-density modulation, mean 1.0, small fractional variation
patchiness = 1.0 + 0.3 * gaussian_filter(
    rng.standard_normal((ny, nx)).astype(np.float32), sigma=DUST_SMOOTH_PX)

theta = np.deg2rad(DUST_ANGLE_DEG)
E1_dust = (DUST_AMP * patchiness * np.cos(2 * theta)).astype(np.float32)
E2_dust = (DUST_AMP * patchiness * np.sin(2 * theta)).astype(np.float32)

E1_mixed = E1_real + E1_dust
E2_mixed = E2_real + E2_dust

# ── Second dust variant: CLUMPY, structured at the REAL field's own scale ──
# First-pass result (see below): a smooth, large-scale (900px) dust field
# turned out to be essentially invisible to the derivative-based E/B
# statistic — worth keeping as an honest finding, not discarding. But it
# means the smooth model alone does not answer "can stuff upset the
# pattern" fairly: a real, adversarial confound would have structure at
# THE SAME spatial scale as the real signal (SMOOTH_PX=60), not a much
# smoother scale. This variant tests that harder, more realistic case —
# grain-density AND alignment-angle fluctuations both varying at 60px,
# same amplitude as above.
CLUMPY_SMOOTH_PX = 60   # matches pixel_vector_field.py's SMOOTH_PX exactly
clump_amp   = gaussian_filter(rng.standard_normal((ny, nx)).astype(np.float32),
                               sigma=CLUMPY_SMOOTH_PX)
clump_angle = gaussian_filter(rng.standard_normal((ny, nx)).astype(np.float32),
                               sigma=CLUMPY_SMOOTH_PX)
patchiness_clumpy = 1.0 + 0.3 * clump_amp
theta_clumpy = np.deg2rad(DUST_ANGLE_DEG) + 0.5 * clump_angle  # angle wobble, same scale

E1_clumpy = (DUST_AMP * patchiness_clumpy * np.cos(2 * theta_clumpy)).astype(np.float32)
E2_clumpy = (DUST_AMP * patchiness_clumpy * np.sin(2 * theta_clumpy)).astype(np.float32)
E1_clumpy_mixed = E1_real + E1_clumpy
E2_clumpy_mixed = E2_real + E2_clumpy

# ── Third dust variant: BROWNIAN — random-walk scattering, Cody's correction ──
# Cody (2026-07-18): "none of the polarizations are invisible... the random
# scattered polarizations from a 'stuff' interacting with the light... adding
# a brownian motion random walk to the photons in their unclean path."
# Right call: the smooth (900px) and clumpy (60px, still spatially
# CORRELATED) variants above are both the wrong shape for real scattering.
# Multiple scattering off dust grains is a diffusion process — each photon
# takes many small independent random kicks along its path. By the central
# limit theorem, summing N independent per-scattering-event kicks converges
# to a single draw from Normal(0, step_kick^2 * N) — so the random walk does
# NOT need to be simulated step-by-step; it is generated directly as
# UNCORRELATED (white-noise) per-pixel scatter, with only its local
# VARIANCE (not its structure) modulated by a smooth column-density envelope
# (more dust along that sightline -> more scattering events -> bigger walk).
# Unlike the smooth/clumpy variants, this has full power at the highest
# spatial frequency the grid supports -- exactly what a derivative-based
# (gradient) statistic like E/B decomposition is most sensitive to.
STEP_KICK = 0.02   # per-event kick scale, same order as DUST_AMP for a fair comparison
N_scatter = np.clip(patchiness, 0.1, None)   # reuse the smooth column-density envelope
E1_brown = (rng.standard_normal((ny, nx)).astype(np.float32)
            * STEP_KICK * np.sqrt(N_scatter))
E2_brown = (rng.standard_normal((ny, nx)).astype(np.float32)
            * STEP_KICK * np.sqrt(N_scatter))
E1_brown_mixed = E1_real + E1_brown
E2_brown_mixed = E2_real + E2_brown

# ── E/B decomposition — EXACT SAME formula as field_lines.py ────────────
# (divergence = E-mode/mass; curl = B-mode/wave-interference signature)
def eb_decompose(E1, E2):
    dE1_dx = np.gradient(E1, axis=1)
    dE1_dy = np.gradient(E1, axis=0)
    dE2_dx = np.gradient(E2, axis=1)
    dE2_dy = np.gradient(E2, axis=0)
    E_mode = dE1_dx + dE2_dy
    B_mode = dE2_dx - dE1_dy
    return E_mode, B_mode

print("\nComputing E/B decomposition for: real BG, smooth-dust-only, real+smooth-dust, "
      "clumpy-dust-only, real+clumpy-dust...")
E_real,   B_real   = eb_decompose(E1_real,   E2_real)
E_dust,   B_dust   = eb_decompose(E1_dust,   E2_dust)
E_mixed,  B_mixed  = eb_decompose(E1_mixed,  E2_mixed)
E_clumpy, B_clumpy = eb_decompose(E1_clumpy, E2_clumpy)
E_clumpy_mixed, B_clumpy_mixed = eb_decompose(E1_clumpy_mixed, E2_clumpy_mixed)
E_brown, B_brown = eb_decompose(E1_brown, E2_brown)
E_brown_mixed, B_brown_mixed = eb_decompose(E1_brown_mixed, E2_brown_mixed)

def px_to_native(px, py):
    return int(round(px)), int(round(py))

def in_bounds(px, py, shape):
    return 0 <= py < shape[0] and 0 <= px < shape[1]

def local_stats(field, px, py, half=60):
    x, y = px_to_native(px, py)
    y0, y1 = max(0, y-half), min(field.shape[0], y+half)
    x0, x1 = max(0, x-half), min(field.shape[1], x+half)
    patch = field[y0:y1, x0:x1]
    return float(np.nanmean(np.abs(patch)))

dm_peaks_in_frame = [(name, px, py) for name, (px, py) in
                     [('DM_NW', dm_nw_px), ('DM_SE', dm_se_px)]
                     if in_bounds(px, py, E1_real.shape)]
print(f"\nDM peaks actually inside this tile: {[n for n,_,_ in dm_peaks_in_frame]} "
      f"(this JWST tile does not cover the full cluster field, per field_lines.py's own bounds check)")

report = {'dust_model': {'amplitude': DUST_AMP, 'angle_deg': DUST_ANGLE_DEG,
                          'smooth_px': DUST_SMOOTH_PX, 'seed': 7},
          'dm_peaks_in_frame': [n for n, _, _ in dm_peaks_in_frame]}

for label, Ef, Bf in [('real', E_real, B_real),
                       ('smooth_dust_only', E_dust, B_dust),
                       ('real_plus_smooth_dust', E_mixed, B_mixed),
                       ('clumpy_dust_only', E_clumpy, B_clumpy),
                       ('real_plus_clumpy_dust', E_clumpy_mixed, B_clumpy_mixed),
                       ('brownian_dust_only', E_brown, B_brown),
                       ('real_plus_brownian_dust', E_brown_mixed, B_brown_mixed)]:
    global_E = float(np.nanmean(np.abs(Ef)))
    global_B = float(np.nanmean(np.abs(Bf)))
    dm_E = np.mean([local_stats(Ef, px, py) for _, px, py in dm_peaks_in_frame])
    dm_B = np.mean([local_stats(Bf, px, py) for _, px, py in dm_peaks_in_frame])
    report[label] = {
        'global_mean_abs_E': global_E, 'global_mean_abs_B': global_B,
        'dm_peak_mean_abs_E': float(dm_E), 'dm_peak_mean_abs_B': float(dm_B),
        'dm_peak_E_over_global': float(dm_E / global_E) if global_E > 0 else None,
        'dm_peak_B_over_global': float(dm_B / global_B) if global_B > 0 else None,
    }
    print(f"  {label:15s}  global|E|={global_E:.3e}  global|B|={global_B:.3e}  "
          f"DM-peak|E|/global={report[label]['dm_peak_E_over_global']:.3f}  "
          f"DM-peak|B|/global={report[label]['dm_peak_B_over_global']:.3f}")

with open(OUT / "dust_confound_report.json", 'w') as f:
    json.dump(report, f, indent=2)

# ── Kaiser-Squires kappa/deflection on dust-only field (same pipeline as real) ─
def block_average(a, bin_):
    ny_, nx_ = a.shape
    ny_c, nx_c = ny_ // bin_, nx_ // bin_
    a = a[:ny_c*bin_, :nx_c*bin_]
    return a.reshape(ny_c, bin_, nx_c, bin_).mean(axis=(1, 3))

pscl_coarse = pscl_native * BIN
g1_dust, g2_dust     = block_average(E1_dust, BIN),   block_average(E2_dust, BIN)
g1_clumpy, g2_clumpy = block_average(E1_clumpy, BIN), block_average(E2_clumpy, BIN)
g1_brown, g2_brown   = block_average(E1_brown, BIN),  block_average(E2_brown, BIN)
g1_real, g2_real     = block_average(E1_real, BIN),   block_average(E2_real, BIN)

print("\nRunning bounded_lensing_pipeline on smooth-dust-only field...")
res_dust = bounded_lensing_pipeline(g1_dust, g2_dust, pscl_coarse, taper_frac=0.1, pad_factor=2.0)
print("Running bounded_lensing_pipeline on clumpy-dust-only field...")
res_clumpy = bounded_lensing_pipeline(g1_clumpy, g2_clumpy, pscl_coarse, taper_frac=0.1, pad_factor=2.0)
print("Running bounded_lensing_pipeline on brownian-dust-only field...")
res_brown = bounded_lensing_pipeline(g1_brown, g2_brown, pscl_coarse, taper_frac=0.1, pad_factor=2.0)
print("Running bounded_lensing_pipeline on real BG field (for comparison)...")
res_real = bounded_lensing_pipeline(g1_real, g2_real, pscl_coarse, taper_frac=0.1, pad_factor=2.0)

kappa_dust, kappa_clumpy, kappa_brown, kappa_real = (
    res_dust['kappa'], res_clumpy['kappa'], res_brown['kappa'], res_real['kappa'])
report['kappa_comparison'] = {
    'smooth_dust_only': {'mean': float(np.nanmean(kappa_dust)), 'std': float(np.nanstd(kappa_dust)),
                          'max_abs': float(np.nanmax(np.abs(kappa_dust)))},
    'clumpy_dust_only':  {'mean': float(np.nanmean(kappa_clumpy)), 'std': float(np.nanstd(kappa_clumpy)),
                          'max_abs': float(np.nanmax(np.abs(kappa_clumpy)))},
    'brownian_dust_only': {'mean': float(np.nanmean(kappa_brown)), 'std': float(np.nanstd(kappa_brown)),
                           'max_abs': float(np.nanmax(np.abs(kappa_brown)))},
    'real':      {'mean': float(np.nanmean(kappa_real)), 'std': float(np.nanstd(kappa_real)),
                  'max_abs': float(np.nanmax(np.abs(kappa_real)))},
}
with open(OUT / "dust_confound_report.json", 'w') as f:
    json.dump(report, f, indent=2)
for k in ('smooth_dust_only', 'clumpy_dust_only', 'brownian_dust_only', 'real'):
    v = report['kappa_comparison'][k]
    print(f"kappa ({k:19s}): mean={v['mean']:.3e}  std={v['std']:.3e}  max|.|={v['max_abs']:.3e}")

# ── Figure: E/B maps, real vs dust-only vs mixed ─────────────────────────
GRID_DS = 8  # downsample for plotting only (native grid is 2505x5647)
def ds(a): return a[::GRID_DS, ::GRID_DS]

fig, axes = plt.subplots(4, 2, figsize=(12, 18), facecolor='#090c12')
rows = [('real BG (actual JWST shear)', E_real, B_real),
        ('smooth dust-only (900px, 1st attempt)', E_dust, B_dust),
        ('clumpy dust-only (60px)', E_clumpy, B_clumpy),
        ('brownian dust-only (random-walk scatter)', E_brown, B_brown)]
for row_i, (title, Ef, Bf) in enumerate(rows):
    for col_i, (data, name, cmap) in enumerate([(Ef, 'E-mode (div)', 'RdBu_r'),
                                                  (Bf, 'B-mode (curl)', 'PiYG')]):
        ax = axes[row_i, col_i]
        ax.set_facecolor('#090c12')
        d = ds(data)
        vlim = max(abs(np.nanpercentile(d, 2)), abs(np.nanpercentile(d, 98))) or 1e-9
        im = ax.imshow(d, origin='lower', cmap=cmap, vmin=-vlim, vmax=vlim, aspect='equal')
        for (px, py), col in [(dm_nw_px, '#7ab4ff'), (dm_se_px, '#4af0ff')]:
            ax.scatter(px/GRID_DS, py/GRID_DS, s=80, marker='+', color=col, linewidths=1.5, zorder=5)
        ax.set_title(f'{title}\n{name}', color='#c8d8e8', fontsize=9)
        ax.tick_params(colors='#5a7090')
        fig.colorbar(im, ax=ax, shrink=0.7)

fig.suptitle('Dust/zodiacal-scattering confound test — does "stuff" upset the polarization pattern?\n'
             'same E/B formula as field_lines.py  |  + markers = DM_NW/DM_SE (Clowe+2006)',
             color='#c8d8e8', fontsize=11)
fig.savefig(OUT / "dust_confound_EB.png", dpi=130, bbox_inches='tight',
            facecolor='#090c12', edgecolor='none')
plt.close()

print(f"\nDone. See:")
print(f"  {OUT / 'dust_confound_report.json'}")
print(f"  {OUT / 'dust_confound_EB.png'}")
