#!/usr/bin/env python3
"""
l_io_polarization_composite.py — Dual vector-field composite: the L_(I|O)
photon-path (slingshot deflection alpha, from l_io_lensing.py) drawn together
with the per-native-pixel polarization (shear) field (from
pixel_vector_field.py), both on top of the real F444W/F356W/F277W ptychography
RGB (same reconstruction ptychography_polarization.py uses), at full native
JWST pixel resolution. No matplotlib resampling in the raster path.

Two fields, two colors, two native resolutions (drawn honestly at each
field's own information density, not oversampled to match the other):
    cyan  '#4af0ff' — polarization (E1_BG/E2_BG), one arrow per STEP=12 native px
    gold  '#ffb347' — L_(I|O) deflection (alpha1/alpha2), one arrow per BIN=32
                       native px cell (its actual coarse-grid resolution —
                       see l_io_lensing.py's block-averaging note)

Outputs -> optical/jwst/prepped/pixel_field/:
    l_io_polarization_composite.png
    l_io_polarization_composite_annotated.png
"""

import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
from astropy.visualization import AsinhStretch
import astropy.units as u
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

REPO = Path(__file__).resolve().parents[2]
PIXOUT = REPO / "optical/jwst/prepped/pixel_field"
LIOOUT = REPO / "optical/jwst/prepped/l_io"
FITS_ROOT = REPO / "optical/jwst/4598/mastDownload/JWST"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

STEP = 12                       # native px between polarization arrows
POL_COL = (74, 240, 255)        # cyan — polarization
LIO_COL = (255, 179, 71)        # gold — L_(I|O) deflection

DM_NW_coord = SkyCoord(ra=104.6383*u.deg, dec=-55.9252*u.deg)
DM_SE_coord = SkyCoord(ra=104.5726*u.deg, dec=-55.9563*u.deg)
GAS_NW_coord = SkyCoord(ra=104.625*u.deg, dec=-55.930*u.deg)
GAS_SE_coord = SkyCoord(ra=104.569*u.deg, dec=-55.961*u.deg)

def sky2px(coord, wcs):
    x, y = wcs.world_to_pixel(coord)
    return float(x), float(y)

def draw_cross(draw, x, y, color, r=34, w=7):
    draw.line([(x-r, y), (x+r, y)], fill=color, width=w)
    draw.line([(x, y-r), (x, y+r)], fill=color, width=w)
    draw.ellipse([x-r*1.6, y-r*1.6, x+r*1.6, y+r*1.6], outline=color, width=3)

def annotate(img, markers, nx, ny):
    ann = img.copy()
    draw = ImageDraw.Draw(ann)
    font = ImageFont.truetype(FONT, 44)
    for (px, py), lbl, color in markers:
        if 0 <= px < nx and 0 <= py < ny:
            py_img = ny - py
            draw_cross(draw, px, py_img, color, r=34, w=7)
            draw.text((px + 40, py_img - 20), lbl, fill=color, font=font,
                       stroke_width=3, stroke_fill=(9, 12, 18))
    legend_y = ny - 140
    for i, (lbl, color) in enumerate([
        ('polarization  E(e1,e2)  — per native px', POL_COL),
        ('L_(I|O) deflection  alpha  — per smoothing-scale cell', LIO_COL),
    ]):
        y = legend_y + i*50
        draw.line([(60, y), (160, y)], fill=color + (255,), width=6)
        draw.text((175, y-18), lbl, fill=(200, 216, 232), font=ImageFont.truetype(FONT, 32),
                   stroke_width=2, stroke_fill=(9, 12, 18))
    return ann

# ── Reference WCS ────────────────────────────────────────────────────────
ref_fits = list(FITS_ROOT.rglob("*f444w_i2d.fits"))[0]
with fits.open(ref_fits) as h:
    wcs = WCS(h['SCI'].header)

MARKERS = [
    (sky2px(DM_NW_coord, wcs),  'DM NW',            (122, 180, 255)),
    (sky2px(DM_SE_coord, wcs),  'DM SE (bullet)',   (74, 240, 255)),
    (sky2px(GAS_NW_coord, wcs), 'Gas NW',           (255, 96, 144)),
    (sky2px(GAS_SE_coord, wcs), 'Gas SE (shocked)', (255, 128, 48)),
]

# ── Load both vector fields ──────────────────────────────────────────────
print("Loading polarization field (native) + L_(I|O) deflection (coarse)...")
E1 = np.load(PIXOUT / "E1_BG.npy")
E2 = np.load(PIXOUT / "E2_BG.npy")
ny, nx = E1.shape

alpha1 = np.load(LIOOUT / "alpha1.npy")
alpha2 = np.load(LIOOUT / "alpha2.npy")
with open(LIOOUT / "l_io_deficit.json") as f:
    lio_meta = json.load(f)
BIN = lio_meta["bin_factor"]
ny_c, nx_c = alpha1.shape
print(f"  polarization: {nx}x{ny} native  |  L_(I|O): {nx_c}x{ny_c} coarse (BIN={BIN})")

# ── Build RGB base (F444W/F356W/F277W, same as ptychography_polarization.py) ──
print("Building ptychography RGB base...")
def load_channel(fname_glob):
    f = sorted(FITS_ROOT.rglob(fname_glob))[0]
    with fits.open(f) as h:
        return h['SCI'].data.astype(np.float64)

r = load_channel("jw04598-o001*f444w_i2d.fits")
g = load_channel("jw04598-o001*f356w_i2d.fits")
b = load_channel("jw04598-o001*f277w_i2d.fits")

crop_ny = min(r.shape[0], g.shape[0], b.shape[0], ny)
crop_nx = min(r.shape[1], g.shape[1], b.shape[1], nx)
r, g, b = r[:crop_ny, :crop_nx], g[:crop_ny, :crop_nx], b[:crop_ny, :crop_nx]
print(f"  composite crop: {crop_nx}x{crop_ny}")

stretch = AsinhStretch(a=0.1)
def norm_chan(a):
    a = np.nan_to_num(a, nan=0.0)
    black = np.nanpercentile(a, 45)
    white = np.nanpercentile(a, 99.9)
    a = np.clip((a - black) / max(white - black, 1e-12), 0, 1)
    return stretch(a)

rgb = np.stack([norm_chan(r), norm_chan(g), norm_chan(b)], axis=-1)
composite = Image.fromarray((rgb * 255).astype(np.uint8), mode='RGB')

# ── Overlay 1: polarization, per native pixel, sampled every STEP px ────
print("Drawing polarization vectors (cyan, per native px)...")
E1c, E2c = E1[:crop_ny, :crop_nx], E2[:crop_ny, :crop_nx]
magc = np.sqrt(E1c**2 + E2c**2)
vmaxc = np.nanpercentile(magc, 99)
angc = np.arctan2(E2c, E1c)
arrow_lenc = np.clip(magc / max(vmaxc, 1e-9), 0.15, 1.0) * (STEP * 0.9)

draw = ImageDraw.Draw(composite, 'RGBA')
for y in np.arange(0, crop_ny, STEP):
    y_img = crop_ny - y
    for x in np.arange(0, crop_nx, STEP):
        a, l = angc[y, x], arrow_lenc[y, x]
        dx, dy = l * np.cos(a), -l * np.sin(a)
        draw.line([(x - dx/2, y_img - dy/2), (x + dx/2, y_img + dy/2)],
                   fill=POL_COL + (190,), width=2)

# ── Overlay 2: L_(I|O) deflection, per coarse (BIN-native-px) cell ──────
print("Drawing L_(I|O) deflection vectors (gold, per smoothing-scale cell)...")
dmag = np.sqrt(alpha1**2 + alpha2**2)
dvmax = np.nanpercentile(dmag, 98)
dang = np.arctan2(alpha2, alpha1)
dlen = np.clip(dmag / max(dvmax, 1e-9), 0.2, 1.0) * (BIN * 0.9)

for j in range(ny_c):
    ny_native = j * BIN + BIN // 2
    if ny_native >= crop_ny:
        continue
    y_img = crop_ny - ny_native
    for i in range(nx_c):
        nx_native = i * BIN + BIN // 2
        if nx_native >= crop_nx:
            continue
        a, l = dang[j, i], dlen[j, i]
        dx, dy = l * np.cos(a), -l * np.sin(a)
        x0, y0 = nx_native - dx/2, y_img - dy/2
        x1, y1 = nx_native + dx/2, y_img + dy/2
        draw.line([(x0, y0), (x1, y1)], fill=LIO_COL + (235,), width=5)
        # arrowhead
        head = 8
        hx, hy = -dx/max(l, 1e-9)*head, -dy/max(l, 1e-9)*head
        perp = np.array([-hy, hx]) * 0.5
        draw.polygon([(x1, y1), (x1+hx+perp[0], y1+hy+perp[1]),
                      (x1+hx-perp[0], y1+hy-perp[1])], fill=LIO_COL + (235,))

out_path = PIXOUT / "l_io_polarization_composite.png"
composite.save(out_path, optimize=True)
print(f"-> {out_path}  ({out_path.stat().st_size/1e6:.1f} MB, {composite.size})")

ann = annotate(composite, MARKERS, crop_nx, crop_ny)
ann_path = PIXOUT / "l_io_polarization_composite_annotated.png"
ann.save(ann_path, optimize=True)
print(f"-> {ann_path}  ({ann_path.stat().st_size/1e6:.1f} MB)")

print("\nDone.")
