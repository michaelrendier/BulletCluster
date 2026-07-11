#!/usr/bin/env python3
"""
topo_map.py — Topographic SVG contour map of the Bullet Cluster DM density field.

Like a topo map of two mountains — the iso-density lines trace the shape of
each DM halo and the interaction saddle between them.

Computes TWO overlaid fields:
  DATA:  KDE of background galaxy positions  (measured signal, proxy for κ)
  NFW:   Superposition of two NFW halos       (particle-DM null hypothesis)

The interaction zone between the halos is where they diverge.
  Smooth saddle → standard CDM / NFW
  Extra closed loops / ripple nodes → wave DM / ΛCDRM

Output: topo_map.svg  (dark background, topo lines, DM/gas peaks marked)
        topo_map_comparison.png  (data vs NFW side-by-side)
"""

import sys
_sys_paths = [p for p in sys.path if '/usr/lib/python3/dist-packages' not in p]
_sys_paths += [p for p in sys.path if '/usr/lib/python3/dist-packages' in p]
sys.path = _sys_paths

import numpy as np
from scipy.stats import gaussian_kde
from scipy.ndimage import gaussian_filter
from skimage import measure
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ── Paths ──────────────────────────────────────────────────────────────────────
OUT  = Path("/media/rendier/0123-4567/bullet_cluster/optical/jwst/prepped")
CAT  = OUT / "source_catalog.fits"
FITS_ROOT = Path("/media/rendier/0123-4567/bullet_cluster/optical/jwst/4598/mastDownload/JWST")

# ── Cluster geometry ───────────────────────────────────────────────────────────
DM_NW  = SkyCoord(ra=104.6383*u.deg, dec=-55.9252*u.deg)   # Clowe+2006
DM_SE  = SkyCoord(ra=104.5726*u.deg, dec=-55.9563*u.deg)
GAS_NW = SkyCoord(ra=104.625 *u.deg, dec=-55.930 *u.deg)
GAS_SE = SkyCoord(ra=104.569 *u.deg, dec=-55.961 *u.deg)

# ── Load WCS from best available F-band ───────────────────────────────────────
for pattern in ["*f277w_i2d.fits", "*f444w_i2d.fits"]:
    hits = list(FITS_ROOT.rglob(pattern))
    if hits:
        with fits.open(hits[0]) as h:
            wcs = WCS(h['SCI'].header)
            ny, nx = h['SCI'].data.shape
        break

def sky2px(coord):
    x, y = wcs.world_to_pixel(coord)
    return float(x), float(y)

dm_nw = sky2px(DM_NW);  dm_se = sky2px(DM_SE)
gas_nw= sky2px(GAS_NW); gas_se= sky2px(GAS_SE)
pscl  = abs(wcs.pixel_scale_matrix[1,1]) * 3600   # arcsec/px
print(f"Image: {nx}×{ny}  pscl={pscl:.4f}\"/px")
print(f"DM_NW px: ({dm_nw[0]:.0f}, {dm_nw[1]:.0f})")
print(f"DM_SE px: ({dm_se[0]:.0f}, {dm_se[1]:.0f})")

# ── Load BG galaxies ───────────────────────────────────────────────────────────
with fits.open(CAT) as h:
    t = h[1].data
mask = t['IS_BG'].astype(bool)
x_bg = t['X_PX'][mask].astype(float)
y_bg = t['Y_PX'][mask].astype(float)
print(f"BG galaxies: {mask.sum()}")

# ── Grid (focus on the footprint where sources exist) ─────────────────────────
pad    = 200   # px border
x_lo   = max(0,    int(min(x_bg)) - pad)
x_hi   = min(nx-1, int(max(x_bg)) + pad)
y_lo   = max(0,    int(min(y_bg)) - pad)
y_hi   = min(ny-1, int(max(y_bg)) + pad)
GRID_N = 200
gx     = np.linspace(x_lo, x_hi, GRID_N)
gy     = np.linspace(y_lo, y_hi, GRID_N)
GX, GY = np.meshgrid(gx, gy)

print(f"Grid footprint: x=[{x_lo},{x_hi}] y=[{y_lo},{y_hi}]  {GRID_N}×{GRID_N}")

# ── Field 1: KDE of BG galaxy positions (measured κ proxy) ────────────────────
print("Computing KDE density field...")
kde     = gaussian_kde(np.vstack([x_bg, y_bg]), bw_method=0.08)
pts_flat= np.vstack([GX.ravel(), GY.ravel()])
kde_map = kde(pts_flat).reshape(GRID_N, GRID_N)
# Smooth slightly
kde_smooth = gaussian_filter(kde_map, sigma=2.5)
kde_norm   = (kde_smooth - kde_smooth.min()) / (kde_smooth.max() - kde_smooth.min())

# ── Field 2: NFW superposition (particle-DM null hypothesis) ──────────────────
print("Computing NFW null model...")

def nfw_projected(rx, ry, cx, cy, rs_px, amplitude=1.0):
    """
    Simplified NFW projected surface density (dimensionless).
    κ ∝ f(R/rs) where f is the projected NFW convergence function.
    """
    R = np.sqrt((rx - cx)**2 + (ry - cy)**2) / rs_px
    R = np.maximum(R, 0.01)
    # NFW projected profile: f(x) = 1/(x²-1) × g(x), analytic form
    f = np.where(
        R < 1,
        1.0/(R**2 - 1) * (1 - 2/np.sqrt(1-R**2) * np.arctanh(np.sqrt((1-R)/(1+R)))),
        np.where(
            R > 1,
            1.0/(R**2 - 1) * (1 - 2/np.sqrt(R**2-1) * np.arctan(np.sqrt((R-1)/(R+1)))),
            1.0/3.0   # R=1 limit
        )
    )
    return amplitude * np.abs(f)

# Scale radii in pixels: ~300 kpc for main halo, ~150 kpc for bullet
# At z=0.296: 1 arcmin ≈ 206 kpc;  pscl arcsec/px → px/kpc = 60/(pscl*206)
px_per_kpc = 60.0 / (pscl * 206.0)
rs_main = 300 * px_per_kpc   # r_s ~ 300 kpc for main halo
rs_sub  = 150 * px_per_kpc   # r_s ~ 150 kpc for bullet (c~9.72 → smaller rs)

nfw_main = nfw_projected(GX, GY, dm_nw[0], dm_nw[1], rs_main, amplitude=1.0)
nfw_sub  = nfw_projected(GX, GY, dm_se[0], dm_se[1], rs_sub,  amplitude=0.1)  # mass ratio ~10:1
nfw_sum  = gaussian_filter(nfw_main + nfw_sub, sigma=2.0)
nfw_sum  = np.clip(nfw_sum, 0, np.nanpercentile(nfw_sum, 99.5))
nfw_norm = (nfw_sum - nfw_sum.min()) / (nfw_sum.max() - nfw_sum.min() + 1e-10)

# ── PNG comparison (matplotlib) ────────────────────────────────────────────────
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(16, 7), facecolor='#090c12')
    titles = ['DATA  (BG galaxy KDE, measured κ proxy)',
              'NFW NULL  (particle-DM prediction, 10:1 mass ratio)']
    fields = [kde_norm, nfw_norm]
    cmaps  = ['Blues',  'Purples']

    for ax, field, title, cmap in zip(axes, fields, titles, cmaps):
        ax.set_facecolor('#090c12')
        ax.imshow(field, origin='lower', cmap=cmap,
                  extent=[x_lo, x_hi, y_lo, y_hi],
                  vmin=0, vmax=1, aspect='equal')
        # Topo contour lines
        levels = np.linspace(0.05, 0.95, 16)
        ct = ax.contour(gx, gy, field, levels=levels,
                        colors='white', linewidths=0.5, alpha=0.6)

        # Mark peaks
        for (px, py), lbl, col, mk in [
            (dm_nw,  'DM NW',  '#7ab4ff', 'o'),
            (dm_se,  'DM SE',  '#4af0ff', 'o'),
            (gas_nw, 'Gas NW', '#ff6090', 's'),
            (gas_se, 'Gas SE', '#ff8030', 's'),
        ]:
            if x_lo < px < x_hi and y_lo < py < y_hi:
                ax.scatter(px, py, s=120, marker=mk, color=col,
                           edgecolors='white', linewidths=1, zorder=6)
                ax.text(px+40, py+40, lbl, color=col, fontsize=8, zorder=7)

        # Interaction zone box (between the two DM peaks)
        ix_lo = min(dm_nw[0], dm_se[0]) + 0.1*(dm_nw[0]-dm_se[0])
        ix_hi = max(dm_nw[0], dm_se[0]) - 0.1*(dm_nw[0]-dm_se[0])
        iy_lo = min(dm_nw[1], dm_se[1])
        iy_hi = max(dm_nw[1], dm_se[1])
        from matplotlib.patches import Rectangle
        r = Rectangle((ix_lo, iy_lo), ix_hi-ix_lo, iy_hi-iy_lo,
                       fill=False, edgecolor='yellow', linewidth=0.8,
                       linestyle='--', alpha=0.5, zorder=5)
        ax.add_patch(r)

        ax.set_title(title, color='#c8d8e8', fontsize=10)
        ax.set_xlabel('x (px)', color='#5a7090')
        ax.set_ylabel('y (px)', color='#5a7090')
        ax.tick_params(colors='#5a7090')

    fig.suptitle('Bullet Cluster — Topographic DM Density Map\nΛCDRipple test: does the interaction saddle show smooth interpolation or ripple nodes?',
                 color='#c8d8e8', fontsize=11)
    fig.patch.set_facecolor('#090c12')
    out_png = OUT / 'topo_map_comparison.png'
    fig.savefig(out_png, dpi=150, bbox_inches='tight',
                facecolor='#090c12', edgecolor='none')
    plt.close()
    print(f"PNG → {out_png}")
except Exception as e:
    print(f"PNG skipped: {e}")

# ── SVG topo map ───────────────────────────────────────────────────────────────
print("Building SVG topo map...")

# SVG canvas (scaled from grid coords)
SVG_W  = 900
SVG_H  = int(SVG_W * (y_hi - y_lo) / (x_hi - x_lo))

def grid2svg(gx_val, gy_val):
    sx = (gx_val - x_lo) / (x_hi - x_lo) * SVG_W
    sy = SVG_H - (gy_val - y_lo) / (y_hi - y_lo) * SVG_H  # flip y
    return sx, sy

def px2svg(px, py):
    return grid2svg(px, py)

# Color ramp: low → dark blue, mid → cyan, high → white
def level_color(level, alpha=1.0):
    """level ∈ [0,1] → hex color"""
    if level < 0.3:
        r, g, b = 20, 40 + int(level/0.3 * 80), 80 + int(level/0.3 * 100)
    elif level < 0.6:
        t = (level - 0.3) / 0.3
        r, g, b = int(t*60), 120 + int(t*80), 180 + int(t*60)
    else:
        t = (level - 0.6) / 0.4
        r, g, b = int(t*220), 200 + int(t*55), 240
    r = min(255, max(0, r))
    g = min(255, max(0, g))
    b = min(255, max(0, b))
    return f"rgb({r},{g},{b})"

svg = []
svg.append(f'<?xml version="1.0" encoding="UTF-8"?>')
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
           f'width="{SVG_W}" height="{SVG_H}" '
           f'viewBox="0 0 {SVG_W} {SVG_H}">')
svg.append(f'<rect width="{SVG_W}" height="{SVG_H}" fill="#090c12"/>')
svg.append(f'<!-- Bullet Cluster topographic DM density map -->')
svg.append(f'<!-- DATA: KDE of {mask.sum()} background galaxies -->')
svg.append(f'<!-- NFW NULL: particle-DM superposition, mass ratio 10:1 -->')

# ── Background heat fill (DATA field) ─────────────────────────────────────────
# Rasterise the kde_norm field as a grid of colored rects
CELL_W = SVG_W / GRID_N
CELL_H = SVG_H / GRID_N
svg.append('<g id="heatmap" opacity="0.55">')
for j in range(GRID_N):
    for i in range(GRID_N):
        v = kde_norm[j, i]
        if v < 0.04: continue
        sx  = i * CELL_W
        sy  = SVG_H - (j + 1) * CELL_H
        col = level_color(v)
        svg.append(f'<rect x="{sx:.1f}" y="{sy:.1f}" '
                   f'width="{CELL_W:.1f}" height="{CELL_H:.1f}" '
                   f'fill="{col}" opacity="{min(1.0,v*1.5):.2f}"/>')
svg.append('</g>')

# ── Topo contour lines — DATA (measured) ──────────────────────────────────────
svg.append('<g id="topo-data">')
levels_data = np.linspace(0.08, 0.92, 18)
for lv in levels_data:
    contours = measure.find_contours(kde_norm, level=lv)
    col = level_color(lv)
    lw  = 0.6 + lv * 1.2   # thicker at higher levels
    for contour in contours:
        # contour[:,0] = row (y-index), contour[:,1] = col (x-index)
        pts = []
        for row_idx, col_idx in contour:
            gx_c = x_lo + col_idx / GRID_N * (x_hi - x_lo)
            gy_c = y_lo + row_idx / GRID_N * (y_hi - y_lo)
            sx, sy = grid2svg(gx_c, gy_c)
            pts.append(f"{sx:.1f},{sy:.1f}")
        if len(pts) < 3: continue
        d = "M " + " L ".join(pts)
        if len(contour) > 20:  # close long contours
            d += " Z"
        svg.append(f'<path d="{d}" fill="none" stroke="{col}" '
                   f'stroke-width="{lw:.1f}" opacity="0.75"/>')
svg.append('</g>')

# ── Topo contour lines — NFW NULL (dashed, for comparison) ────────────────────
svg.append('<g id="topo-nfw" opacity="0.35">')
levels_nfw = np.linspace(0.08, 0.92, 12)
for lv in levels_nfw:
    contours = measure.find_contours(nfw_norm, level=lv)
    for contour in contours:
        pts = []
        for row_idx, col_idx in contour:
            gx_c = x_lo + col_idx / GRID_N * (x_hi - x_lo)
            gy_c = y_lo + row_idx / GRID_N * (y_hi - y_lo)
            sx, sy = grid2svg(gx_c, gy_c)
            pts.append(f"{sx:.1f},{sy:.1f}")
        if len(pts) < 3: continue
        d = "M " + " L ".join(pts)
        if len(contour) > 20:
            d += " Z"
        svg.append(f'<path d="{d}" fill="none" stroke="#ff9040" '
                   f'stroke-width="0.5" stroke-dasharray="3,3"/>')
svg.append('</g>')

# ── DM and Gas peak markers ────────────────────────────────────────────────────
svg.append('<g id="peaks">')
for (px, py), lbl, col, shape in [
    (dm_nw,  'DM NW\n(Clowe 2006)',  '#7ab4ff', 'circle'),
    (dm_se,  'DM SE\nbullet',        '#4af0ff', 'circle'),
    (gas_nw, 'Gas NW',              '#ff6090', 'square'),
    (gas_se, 'Gas SE\n(bow shock)', '#ff8030', 'square'),
]:
    if not (x_lo < px < x_hi and y_lo < py < y_hi):
        continue
    sx, sy = px2svg(px, py)
    if shape == 'circle':
        svg.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="8" '
                   f'fill="none" stroke="{col}" stroke-width="2"/>')
        svg.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="2" fill="{col}"/>')
    else:
        svg.append(f'<rect x="{sx-6:.1f}" y="{sy-6:.1f}" width="12" height="12" '
                   f'fill="none" stroke="{col}" stroke-width="2"/>')
    for i, line in enumerate(lbl.split('\n')):
        svg.append(f'<text x="{sx+12:.1f}" y="{sy + i*13:.1f}" '
                   f'fill="{col}" font-size="11" font-family="monospace" '
                   f'font-weight="bold">{line}</text>')
svg.append('</g>')

# ── Interaction zone annotation ────────────────────────────────────────────────
svg.append('<g id="interaction-zone">')
# midpoint between DM peaks
mid_px = (dm_nw[0] + dm_se[0]) / 2
mid_py = (dm_nw[1] + dm_se[1]) / 2
mid_sx, mid_sy = px2svg(mid_px, mid_py)

# line connecting DM peaks
if x_lo < dm_nw[0] < x_hi and x_lo < dm_se[0] < x_hi:
    snwx, snwy = px2svg(dm_nw[0], dm_nw[1])
    ssex, ssey = px2svg(dm_se[0], dm_se[1])
    svg.append(f'<line x1="{snwx:.1f}" y1="{snwy:.1f}" '
               f'x2="{ssex:.1f}" y2="{ssey:.1f}" '
               f'stroke="white" stroke-width="0.5" '
               f'stroke-dasharray="6,4" opacity="0.3"/>')
    svg.append(f'<text x="{mid_sx:.1f}" y="{mid_sy-18:.1f}" '
               f'fill="#ffff60" font-size="9" font-family="monospace" '
               f'text-anchor="middle" opacity="0.8">⟵ interaction zone ⟶</text>')
    svg.append(f'<text x="{mid_sx:.1f}" y="{mid_sy-6:.1f}" '
               f'fill="#ffff60" font-size="8" font-family="monospace" '
               f'text-anchor="middle" opacity="0.6">smooth saddle=CDM | ripple nodes=ΛCDRM</text>')
svg.append('</g>')

# ── Legend ─────────────────────────────────────────────────────────────────────
svg.append('<g id="legend">')
svg.append(f'<rect x="10" y="{SVG_H-80}" width="220" height="70" '
           f'rx="4" fill="#090c12" fill-opacity="0.8" stroke="#1e2a3a"/>')
svg.append(f'<text x="20" y="{SVG_H-62}" fill="#c8d8e8" '
           f'font-size="10" font-family="monospace">SOLID — data (BG galaxy KDE)</text>')
svg.append(f'<line x1="20" y1="{SVG_H-52}" x2="60" y2="{SVG_H-52}" '
           f'stroke="#60c0ff" stroke-width="1.5"/>')
svg.append(f'<text x="65" y="{SVG_H-48}" fill="#9ab0c8" '
           f'font-size="9" font-family="monospace">iso-κ contours (measured)</text>')
svg.append(f'<line x1="20" y1="{SVG_H-34}" x2="60" y2="{SVG_H-34}" '
           f'stroke="#ff9040" stroke-width="1" stroke-dasharray="4,3"/>')
svg.append(f'<text x="65" y="{SVG_H-30}" fill="#9ab0c8" '
           f'font-size="9" font-family="monospace">NFW null (particle-DM, 10:1)</text>')
svg.append(f'<text x="20" y="{SVG_H-16}" fill="#ffff60" '
           f'font-size="8" font-family="monospace">ΛCDRM test: Bullet Cluster 1E0657-558</text>')
svg.append('</g>')

svg.append('</svg>')

out_svg = OUT / 'topo_map.svg'
with open(out_svg, 'w') as f:
    f.write('\n'.join(svg))

# Count SVG elements
n_paths = sum(1 for l in svg if '<path' in l)
n_rects = sum(1 for l in svg if '<rect' in l and 'id' not in l)
print(f"SVG → {out_svg}  ({n_paths} contour paths, ~{n_rects} heat cells)")
print(f"\nReading the map:")
print(f"  SOLID lines   = measured data (BG galaxy density)")
print(f"  DASHED orange = NFW particle-DM null hypothesis")
print(f"  Where they AGREE  → consistent with particle DM")
print(f"  Where data shows extra closed loops between the peaks")
print(f"    → ripple nodes → wave DM → ΛCDRM signature")
