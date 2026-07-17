#!/usr/bin/env python3
"""
final_dm_lio_polarization.py — THE synthesis image: real-shear dark-matter
density ("ptychography" pockets) + L_(I|O) photon-deflection field, both
prominent/central, with the polarization (shear) vector field drawn subdued
underneath for alignment comparison. Built for Inkscape tracing (large,
high-contrast, transparent background so it layers over the other real-data
PNGs already in this repo).

All three inputs are real, already computed from real JWST pixels:
  kappa    (optical/jwst/prepped/l_io/kappa.npy)     — Kaiser-Squires convergence,
             i.e. the actual reconstructed dark-matter surface density, from
             l_io_lensing.py, fed by the real background-galaxy shear this
             repo measured on real JWST F444W/F277W detections
             (source_extract.py -> pixel_vector_field.py). Mass-sheet
             degenerate: relative structure only, NOT clipped/renormalised —
             shown as measured, diverging about its own zero.
  alpha    (optical/jwst/prepped/l_io/alpha1.npy, alpha2.npy) — the L_(I|O)
             deflection ("slingshot") field, same real-shear origin, on the
             same coarse grid as kappa (both BIN=32 native f444w px).
  E1_BG/E2_BG (optical/jwst/prepped/pixel_field/) — native-pixel polarization
             (shear) vector field, background galaxies only, same source
             catalog.

Outputs:
  optical/jwst/prepped/l_io/final_dm_lio_polarization.png             (clean, transparent bg — for tracing)
  optical/jwst/prepped/l_io/final_dm_lio_polarization_annotated.png   (+ markers/legend)
  BulletCluster/Ptychography_DM_Pockets_LIO_Polarization.png          (copy of the clean version, top-level)
"""
import json, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import zoom
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

REPO = Path("/storage/emulated/0/ThePlace/BulletCluster")
PIXOUT = REPO / "optical/jwst/prepped/pixel_field"
LIOOUT = REPO / "optical/jwst/prepped/l_io"
FITS_ROOT = REPO / "optical/jwst/4598/mastDownload/JWST"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

UPSAMPLE = 16            # kappa/alpha coarse-cell -> canvas px (smooth display only, no new data)
LIO_STEP_CELLS = 3       # coarse cells between L_(I|O) arrows (legibility -- same idea as
                          # l_io_lensing.py's own quiver step = nx_c//40)
POL_STEP_NATIVE = 28     # native px between subdued polarization arrows (coarser = more subdued)
POL_COL = (74, 240, 255)      # cyan, same convention as the rest of this repo
LIO_COL = (255, 179, 71)      # gold, same convention

DM_NW_coord = SkyCoord(ra=104.6383*u.deg, dec=-55.9252*u.deg)
DM_SE_coord = SkyCoord(ra=104.5726*u.deg, dec=-55.9563*u.deg)
GAS_NW_coord = SkyCoord(ra=104.625*u.deg, dec=-55.930*u.deg)
GAS_SE_coord = SkyCoord(ra=104.569*u.deg, dec=-55.961*u.deg)

def sky2px(coord, wcs):
    x, y = wcs.world_to_pixel(coord)
    return float(x), float(y)

# ── Load real data ───────────────────────────────────────────────────────
kappa = np.load(LIOOUT / "kappa.npy")
alpha1 = np.load(LIOOUT / "alpha1.npy")
alpha2 = np.load(LIOOUT / "alpha2.npy")
with open(LIOOUT / "l_io_deficit.json") as f:
    lio_meta = json.load(f)
BIN = lio_meta["bin_factor"]
ny_c, nx_c = kappa.shape
print(f"kappa/alpha coarse grid: {nx_c}x{ny_c} (BIN={BIN} native px, {lio_meta['pixel_scale_coarse_arcsec']:.3f} arcsec/px)")

E1 = np.load(PIXOUT / "E1_BG.npy")
E2 = np.load(PIXOUT / "E2_BG.npy")
ny_n, nx_n = E1.shape
print(f"polarization native grid: {nx_n}x{ny_n}")

ref_fits = list(FITS_ROOT.rglob("*f444w_i2d.fits"))[0]
with fits.open(ref_fits) as h:
    wcs = WCS(h['SCI'].header)
MARKERS = [
    (sky2px(DM_NW_coord, wcs),  'DM NW',            (122, 180, 255)),
    (sky2px(DM_SE_coord, wcs),  'DM SE (bullet)',   (74, 240, 255)),
    (sky2px(GAS_NW_coord, wcs), 'Gas NW',           (255, 96, 144)),
    (sky2px(GAS_SE_coord, wcs), 'Gas SE (shocked)', (255, 128, 48)),
]

# ── Canvas geometry: upsample the coarse (kappa/alpha) grid for smooth   ──
# ── display only -- the underlying data stays exactly what was measured ──
CW, CH = nx_c * UPSAMPLE, ny_c * UPSAMPLE
print(f"Canvas: {CW}x{CH}")

# ── Layer 1: kappa density -- "ptychography" dark-matter pockets, central ──
# Diverging about its own zero, exactly as reconstructed (mass-sheet
# degenerate -- no renormalisation, no clipping to "clean it up").
kappa_up = zoom(kappa, UPSAMPLE, order=3)  # cubic smoothing for display, not new information
vlim = np.nanpercentile(np.abs(kappa_up), 98)
kappa_norm = np.clip(kappa_up / vlim, -1, 1)   # -1..1

cmap = plt.get_cmap('RdBu_r')
rgba = cmap((kappa_norm + 1) / 2)   # (H,W,4) in 0..1
rgb_arr = (rgba[..., :3] * 255).astype(np.uint8)
# alpha follows |kappa| -- transparent near the (arbitrary) zero level,
# opaque at the real over/under-density peaks -- so this composites as a
# layer, and the densest pockets are exactly where it reads most solid.
alpha_arr = np.clip(np.abs(kappa_norm) ** 0.7, 0, 1) * 235
base = np.dstack([rgb_arr, alpha_arr.astype(np.uint8)])
canvas = Image.fromarray(base, mode='RGBA')
if canvas.size != (CW, CH):
    canvas = canvas.resize((CW, CH), Image.BICUBIC)
print(f"kappa layer built (|kappa| 98th pct = {vlim:.4f}, mass-sheet-degenerate units)")

def coarse_to_canvas(i, j):
    """coarse cell (col i, row j, row0=south) -> canvas px (row0=top/north)."""
    x = (i + 0.5) * UPSAMPLE
    y = CH - (j + 0.5) * UPSAMPLE
    return x, y

def native_to_canvas(x_native, y_native):
    x = x_native / BIN * UPSAMPLE
    y = CH - y_native / BIN * UPSAMPLE
    return x, y

# ── Layer 2: polarization (shear), subdued, drawn FIRST so L_(I|O) and    ──
# ── the DM density read on top of it, not the other way round             ──
print("Drawing polarization field (subdued)...")
draw = ImageDraw.Draw(canvas, 'RGBA')
mag = np.sqrt(E1**2 + E2**2)
vmaxp = np.nanpercentile(mag, 99)
ang = np.arctan2(E2, E1)
step_canvas = POL_STEP_NATIVE / BIN * UPSAMPLE
for y in np.arange(0, ny_n, POL_STEP_NATIVE):
    for x in np.arange(0, nx_n, POL_STEP_NATIVE):
        m, a = mag[y, x], ang[y, x]
        l = np.clip(m / max(vmaxp, 1e-9), 0.2, 1.0) * step_canvas * 0.9
        cx, cy = native_to_canvas(x, y)
        dx, dy = l * np.cos(a), -l * np.sin(a)
        draw.line([(cx - dx/2, cy - dy/2), (cx + dx/2, cy + dy/2)],
                  fill=POL_COL + (130,), width=1)   # low alpha, hairline -- subdued

# ── Layer 3: L_(I|O) deflection field, gold, prominent/central ───────────
print("Drawing L_(I|O) deflection field (prominent)...")
dmag = np.sqrt(alpha1**2 + alpha2**2)
dvmax = np.nanpercentile(dmag, 98)
dang = np.arctan2(alpha2, alpha1)
lio_span = LIO_STEP_CELLS * UPSAMPLE
for j in range(0, ny_c, LIO_STEP_CELLS):
    for i in range(0, nx_c, LIO_STEP_CELLS):
        # average the block this arrow represents, not just its corner cell
        jb, ib = slice(j, min(j+LIO_STEP_CELLS, ny_c)), slice(i, min(i+LIO_STEP_CELLS, nx_c))
        a1b, a2b = alpha1[jb, ib].mean(), alpha2[jb, ib].mean()
        m, a = np.hypot(a1b, a2b), np.arctan2(a2b, a1b)
        l = np.clip(m / max(dvmax, 1e-9), 0.3, 1.0) * lio_span * 0.85
        cx, cy = coarse_to_canvas(i + LIO_STEP_CELLS/2 - 0.5, j + LIO_STEP_CELLS/2 - 0.5)
        dx, dy = l * np.cos(a), -l * np.sin(a)
        x0, y0, x1, y1 = cx - dx/2, cy - dy/2, cx + dx/2, cy + dy/2
        draw.line([(x0, y0), (x1, y1)], fill=LIO_COL + (235,), width=4)
        head = 9
        hx, hy = -dx/max(l, 1e-9)*head, -dy/max(l, 1e-9)*head
        perp = np.array([-hy, hx]) * 0.5
        draw.polygon([(x1, y1), (x1+hx+perp[0], y1+hy+perp[1]),
                      (x1+hx-perp[0], y1+hy-perp[1])], fill=LIO_COL + (235,))

clean_path = LIOOUT / "final_dm_lio_polarization.png"
canvas.save(clean_path, optimize=True)
print(f"-> {clean_path}  ({clean_path.stat().st_size/1e6:.1f} MB, {canvas.size})")

# ── Annotated copy: markers + legend ──────────────────────────────────────
ann = canvas.copy()
adraw = ImageDraw.Draw(ann, 'RGBA')
font = ImageFont.truetype(FONT, max(18, CW // 90))

def draw_cross(dr, x, y, color, r, w):
    dr.line([(x-r, y), (x+r, y)], fill=color, width=w)
    dr.line([(x, y-r), (x, y+r)], fill=color, width=w)
    dr.ellipse([x-r*1.6, y-r*1.6, x+r*1.6, y+r*1.6], outline=color, width=max(2, w//2))

r_mark = max(14, CW // 120)
for (px, py), lbl, color in MARKERS:
    cx, cy = native_to_canvas(px, py)
    if 0 <= cx < CW and 0 <= cy < CH:
        draw_cross(adraw, cx, cy, color, r=r_mark, w=max(3, r_mark//6))
        adraw.text((cx + r_mark + 6, cy - r_mark), lbl, fill=color, font=font,
                    stroke_width=2, stroke_fill=(9, 12, 18))

legend_font = ImageFont.truetype(FONT, max(20, CW // 80))
legend = [
    ('kappa -- Kaiser-Squires convergence (real shear, mass-sheet degenerate)', (200, 60, 60)),
    ('L_(I|O) deflection alpha -- photon slingshot vector', LIO_COL),
    ('polarization E(e1,e2) -- background-galaxy shear (subdued)', POL_COL),
]
ly0 = CH - (len(legend) * (legend_font.size + 12)) - 20
for k, (txt, col) in enumerate(legend):
    y = ly0 + k * (legend_font.size + 12)
    adraw.line([(24, y + legend_font.size//2), (84, y + legend_font.size//2)], fill=col + (255,), width=6)
    adraw.text((96, y), txt, fill=(210, 222, 235), font=legend_font,
               stroke_width=2, stroke_fill=(9, 12, 18))

ann_path = LIOOUT / "final_dm_lio_polarization_annotated.png"
ann.save(ann_path, optimize=True)
print(f"-> {ann_path}  ({ann_path.stat().st_size/1e6:.1f} MB)")

top_level = REPO / "Ptychography_DM_Pockets_LIO_Polarization.png"
shutil.copy(clean_path, top_level)
print(f"-> {top_level}")
print("\nDone.")
