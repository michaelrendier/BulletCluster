#!/usr/bin/env python3
"""
field_lines.py — Map the polarization field lines of the two interacting DM halos.

Each background galaxy is a polarization vector:
    e1 = e·cos(2θ)    e2 = e·sin(2θ)     (Stokes-like shear components)
    e  = (a-b)/(a+b)  θ  = orientation angle (SEP output)

These vectors form a field across the cluster.
The field lines of (e1, e2) ARE the lensing shear field lines.

Two DM halos → two shear field sources → interference between them.
If DM is wave/cymatic:   interference nodes produce B-mode curl between the halos.
If DM is particle/NFW:   smooth superposition, E-mode only, no curl.

Outputs:
    field_lines.png       — streamplot of the polarization field (the picture)
    field_lines.svg       — same, vector format for ptol.c pathway input
    EB_decomp.png         — E-mode / B-mode separation (the discriminant)
    field_magnitude.png   — |e| shear magnitude map
"""

import sys
# User-space matplotlib (3.11, NumPy 2.x compatible) must load before
# the system package (.local takes priority but nspkg.pth can interfere)
_sys_paths = [p for p in sys.path if '/usr/lib/python3/dist-packages' in p]
_user_paths = [p for p in sys.path if '/usr/lib/python3/dist-packages' not in p]
sys.path = _user_paths + _sys_paths

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.colors import Normalize
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ── Paths ─────────────────────────────────────────────────────────────────────
OUT   = Path("/media/rendier/0123-4567/bullet_cluster/optical/jwst/prepped")
CAT   = OUT / "source_catalog.fits"
FITS_ROOT = Path("/media/rendier/0123-4567/bullet_cluster/optical/jwst/4598/mastDownload/JWST")

# ── Cluster geometry ──────────────────────────────────────────────────────────
RA0, DEC0   = 104.6098, -55.9446
DM_NW_coord = SkyCoord(ra=104.6383*u.deg, dec=-55.9252*u.deg)
DM_SE_coord = SkyCoord(ra=104.5726*u.deg, dec=-55.9563*u.deg)
GAS_NW_coord= SkyCoord(ra=104.625 *u.deg, dec=-55.930 *u.deg)
GAS_SE_coord= SkyCoord(ra=104.569 *u.deg, dec=-55.961 *u.deg)

# ── Load reference WCS (F444W) ─────────────────────────────────────────────────
ref_fits = list(FITS_ROOT.rglob("*f444w_i2d.fits"))[0]
with fits.open(ref_fits) as h:
    wcs  = WCS(h['SCI'].header)
    ny, nx = h['SCI'].data.shape
    img  = h['SCI'].data.astype(np.float32)
pscl = abs(wcs.pixel_scale_matrix[1,1]) * 3600   # arcsec/px

def sky2px(coord):
    x, y = wcs.world_to_pixel(coord)
    return float(x), float(y)

dm_nw_px  = sky2px(DM_NW_coord)
dm_se_px  = sky2px(DM_SE_coord)
gas_nw_px = sky2px(GAS_NW_coord)
gas_se_px = sky2px(GAS_SE_coord)

print(f"Image: {nx}×{ny}  |  {pscl:.4f} arcsec/px")
print(f"DM_NW px:  {dm_nw_px}")
print(f"DM_SE px:  {dm_se_px}")

# ── Load source catalog ────────────────────────────────────────────────────────
with fits.open(CAT) as h:
    t = h[1].data

x_all   = t['X_PX'].astype(float)
y_all   = t['Y_PX'].astype(float)
a_all   = t['A_PX'].astype(float)
b_all   = t['B_PX'].astype(float)
theta_all = t['THETA'].astype(float)   # radians, SEP convention
is_bg   = t['IS_BG'].astype(bool)
is_cl   = t['IS_CLUSTER'].astype(bool)

# ── Ellipticity → shear components ────────────────────────────────────────────
def ellip_components(a, b, theta):
    """Convert (a,b,theta) → (e, e1, e2) shear components."""
    denom = np.maximum(a + b, 1e-6)
    e     = (a - b) / denom
    e     = np.clip(e, 0, 0.9)
    e1    = e * np.cos(2.0 * theta)
    e2    = e * np.sin(2.0 * theta)
    return e, e1, e2

e_all, e1_all, e2_all = ellip_components(a_all, b_all, theta_all)

# ── Grid setup (full image) ───────────────────────────────────────────────────
GRID_N  = 80    # grid resolution (prime: 79 bins → each bin ~0.7 arcmin)
gx      = np.linspace(0, nx-1, GRID_N)
gy      = np.linspace(0, ny-1, GRID_N)
GX, GY  = np.meshgrid(gx, gy)

def interpolate_field(x, y, values, smooth_px=60):
    """Scatter → grid via linear interpolation + Gaussian smoothing."""
    mask = np.isfinite(values) & np.isfinite(x) & np.isfinite(y)
    pts  = np.column_stack([x[mask], y[mask]])
    vals = values[mask]
    grid_vals = griddata(pts, vals, (GX, GY), method='linear', fill_value=0.0)
    return gaussian_filter(grid_vals, sigma=smooth_px / (nx / GRID_N))

# ── Interpolate for ALL, CLUSTER, BACKGROUND ──────────────────────────────────
print("Interpolating shear fields...")

for label, mask in [('ALL', np.ones(len(x_all), bool)),
                    ('BG',  is_bg),
                    ('CL',  is_cl)]:
    x, y = x_all[mask], y_all[mask]
    e1   = e1_all[mask];  e2 = e2_all[mask];  e = e_all[mask]
    print(f"  {label}: {mask.sum()} sources")

    E1 = interpolate_field(x, y, e1)
    E2 = interpolate_field(x, y, e2)
    EM = np.sqrt(E1**2 + E2**2)

    # ── E/B mode decomposition ─────────────────────────────────────────────
    # E-mode: divergence of (e1, e2) → mass concentrations
    # B-mode: curl of (e1, e2)       → wave interference signature
    dE1_dx = np.gradient(E1, axis=1)
    dE1_dy = np.gradient(E1, axis=0)
    dE2_dx = np.gradient(E2, axis=1)
    dE2_dy = np.gradient(E2, axis=0)
    E_mode =  dE1_dx + dE2_dy     # divergence
    B_mode =  dE2_dx - dE1_dy     # curl

    # ── Plot 1: Field lines (streamplot) ──────────────────────────────────
    fig, ax = plt.subplots(figsize=(14, 7), facecolor='#090c12')
    ax.set_facecolor('#090c12')

    # Background image (log-stretched)
    img_disp = np.arcsinh(np.clip(img, 0, None) / 0.05)
    ax.imshow(img_disp, origin='lower', cmap='inferno',
              vmin=np.nanpercentile(img_disp, 5),
              vmax=np.nanpercentile(img_disp, 99.5),
              aspect='equal', alpha=0.55)

    # Shear magnitude as filled contours
    cf = ax.contourf(GX, GY, EM,
                     levels=20, cmap='Blues_r', alpha=0.35,
                     vmin=0, vmax=np.nanpercentile(EM, 97))

    # Field lines (streamplot of e1, e2)
    speed = np.sqrt(E1**2 + E2**2) + 1e-8
    lw    = 1.5 * speed / speed.max()
    strm  = ax.streamplot(gx, gy, E1, E2,
                          color=speed, cmap='cool',
                          linewidth=lw,
                          density=2.5, arrowsize=0.8,
                          integration_direction='both')

    # DM peaks
    for (px, py), lbl, col in [
        (dm_nw_px,  'DM NW\n(Clowe+2006)', '#7ab4ff'),
        (dm_se_px,  'DM SE\n(bullet)',      '#4af0ff'),
        (gas_nw_px, 'Gas NW',              '#ff6090'),
        (gas_se_px, 'Gas SE\n(shocked)',    '#ff8030'),
    ]:
        if 0 < px < nx and 0 < py < ny:
            ax.scatter(px, py, s=180, marker='+',
                       color=col, linewidths=2.0, zorder=10)
            ax.text(px+30, py+30, lbl, color=col, fontsize=7,
                    path_effects=[pe.withStroke(linewidth=2, foreground='black')],
                    zorder=11)

    # Merger axis line
    if 0 < dm_se_px[0] < nx:
        ax.plot([dm_nw_px[0], dm_se_px[0]],
                [dm_nw_px[1], dm_se_px[1]],
                '--', color='white', alpha=0.25, linewidth=0.8, zorder=5)

    cbar = fig.colorbar(strm.lines, ax=ax, pad=0.01, shrink=0.7)
    cbar.set_label('|shear|', color='#c8d8e8', fontsize=9)
    cbar.ax.yaxis.set_tick_params(color='#c8d8e8')
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color='#c8d8e8')

    ax.set_title(f'Bullet Cluster — Shear Field Lines ({label} sources)\n'
                 f'JWST F444W  |  {mask.sum()} sources  |  ΛCDRipple/Shape',
                 color='#c8d8e8', fontsize=11, pad=10)
    ax.set_xlabel('x (px)', color='#5a7090')
    ax.set_ylabel('y (px)', color='#5a7090')
    ax.tick_params(colors='#5a7090')
    for spine in ax.spines.values():
        spine.set_edgecolor('#1e2a3a')

    out_png = OUT / f"field_lines_{label}.png"
    fig.savefig(out_png, dpi=150, bbox_inches='tight',
                facecolor='#090c12', edgecolor='none')
    plt.close()
    print(f"  → {out_png}")

    # ── Plot 2: E/B mode map ──────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), facecolor='#090c12')
    for ax_, data, title, cmap in [
        (axes[0], E_mode, f'E-mode (∇·e)  — {label}\nmass concentrations', 'RdBu_r'),
        (axes[1], B_mode, f'B-mode (∇×e)  — {label}\nwave interference signature', 'PiYG'),
    ]:
        ax_.set_facecolor('#090c12')
        vlim = max(abs(np.nanpercentile(data, 2)), abs(np.nanpercentile(data, 98)))
        im = ax_.imshow(data, origin='lower', cmap=cmap,
                        vmin=-vlim, vmax=vlim, aspect='equal')
        for (px, py), col in [(dm_nw_px, '#7ab4ff'), (dm_se_px, '#4af0ff')]:
            if 0 < px < nx and 0 < py < ny:
                ax_.scatter(px/nx*GRID_N, py/ny*GRID_N,
                           s=120, marker='+', color=col, linewidths=2, zorder=5)
        ax_.set_title(title, color='#c8d8e8', fontsize=10)
        ax_.tick_params(colors='#5a7090')
        fig.colorbar(im, ax=ax_, shrink=0.8)

    fig.patch.set_facecolor('#090c12')
    out_eb = OUT / f"EB_decomp_{label}.png"
    fig.savefig(out_eb, dpi=150, bbox_inches='tight',
                facecolor='#090c12', edgecolor='none')
    plt.close()
    print(f"  → {out_eb}")

# ── Field line SVG for ptol.c pathway ─────────────────────────────────────────
print("\nWriting field_lines_BG.svg for ptol.c pathway input...")
E1_bg = interpolate_field(x_all[is_bg], y_all[is_bg], e1_all[is_bg])
E2_bg = interpolate_field(x_all[is_bg], y_all[is_bg], e2_all[is_bg])
EM_bg = np.sqrt(E1_bg**2 + E2_bg**2)
emax  = np.nanpercentile(EM_bg, 99)

svg_lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{GRID_N*8}" height="{GRID_N*4}">',
    '<rect width="100%" height="100%" fill="#090c12"/>',
    f'<!-- Bullet Cluster shear field — BG sources only -->',
    f'<!-- DM_NW: ({dm_nw_px[0]*GRID_N/nx:.1f}, {(ny-dm_nw_px[1])*GRID_N/ny:.1f}) -->',
    f'<!-- DM_SE: ({dm_se_px[0]*GRID_N/nx:.1f}, {(ny-dm_se_px[1])*GRID_N/ny:.1f}) -->',
]
# Polarization sticks at each grid point
for j in range(0, GRID_N, 2):
    for i in range(0, GRID_N, 2):
        e1v = E1_bg[j, i];  e2v = E2_bg[j, i]
        emag = EM_bg[j, i]
        if emag < 1e-6: continue
        cx = i * 8;  cy = (GRID_N - j) * 4
        # Stick: half-length proportional to |e|
        half = min(6, 6 * emag / (emax + 1e-8))
        dx = half * e1v / (emag + 1e-8)
        dy = half * e2v / (emag + 1e-8)
        alpha = min(1.0, emag / (emax * 0.3 + 1e-8))
        col_val = int(100 + 155 * alpha)
        col = f"#{col_val:02x}{col_val:02x}ff"
        svg_lines.append(
            f'<line x1="{cx-dx:.1f}" y1="{cy-dy:.1f}" '
            f'x2="{cx+dx:.1f}" y2="{cy+dy:.1f}" '
            f'stroke="{col}" stroke-width="1.2" opacity="{alpha:.2f}"/>'
        )
# DM peak markers
for (px, py), col, lbl in [
    (dm_nw_px,  '#7ab4ff', 'DM_NW'),
    (dm_se_px,  '#4af0ff', 'DM_SE'),
    (gas_nw_px, '#ff6090', 'GAS_NW'),
    (gas_se_px, '#ff8030', 'GAS_SE'),
]:
    if 0 < px < nx and 0 < py < ny:
        svx = px * GRID_N / nx * 8
        svy = (ny - py) * GRID_N / ny * 4
        svg_lines.append(f'<circle cx="{svx:.1f}" cy="{svy:.1f}" r="5" fill="none" stroke="{col}" stroke-width="2"/>')
        svg_lines.append(f'<text x="{svx+7:.1f}" y="{svy:.1f}" fill="{col}" font-size="10" font-family="monospace">{lbl}</text>')

svg_lines.append('</svg>')
svg_path = OUT / "field_lines_BG.svg"
with open(svg_path, 'w') as f:
    f.write('\n'.join(svg_lines))
print(f"  → {svg_path}")

print("\nDone. Check:")
print(f"  field_lines_BG.png   — background-only shear field lines")
print(f"  field_lines_ALL.png  — all sources")
print(f"  EB_decomp_BG.png     — E-mode (mass) / B-mode (wave interference?)")
print(f"  field_lines_BG.svg   — polarization sticks for ptol.c")
print(f"\nIf B-mode shows structure between DM_NW and DM_SE:")
print(f"  → Pattern exists → cymatic/wave → ΛCDRM confirmed")
print(f"If B-mode is white noise:")
print(f"  → No pattern → stochastic → standard ΛCDM holds")
