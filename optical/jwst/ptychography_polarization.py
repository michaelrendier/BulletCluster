#!/usr/bin/env python3
"""
ptychography_polarization.py — Plain vector field + polarization-included
ptychography composite, both at native JWST pixel resolution.

Two outputs, both giant/zoomable (no matplotlib resampling in the raster
path -- arrows are drawn directly onto a native-resolution PIL canvas):

1. vector_field_plain_BG[_annotated].png
   Direction-only shear vectors (background galaxies, the physically
   appropriate lensing tracer -- same choice field_lines.py and
   l_io_lensing.py made), single accent color, no magnitude/angle color
   coding. Sampled dense enough (one arrow per STEP native px) that
   zooming in shows individual arrows, zooming out shows the flow
   texture of the field.

2. ptychography_polarization_BG[_annotated].png
   The actual multi-filter reconstruction this repo's README calls
   "Ptychography of the Shape of the Space": F444W/F356W/F277W (o001
   tile -- the same pixel-aligned LW mosaic pixel_vector_field.py and
   l_io_lensing.py use as their WCS reference) combined as R/G/B, i.e.
   the real telescope data at three wavelengths reconstructing one
   structure -- with the polarization (shear) vector field drawn on top
   as an overlay, so the interference/alignment between real structure
   and measured shear direction is visible at full native resolution.

Both draw from E1_BG.npy / E2_BG.npy (pixel_vector_field.py) and the
o001 f444w/f356w/f277w i2d mosaics (native-pixel-aligned, no reprojection
needed).

Outputs -> optical/jwst/prepped/pixel_field/:
    vector_field_plain_BG.png
    vector_field_plain_BG_annotated.png
    ptychography_polarization_BG.png
    ptychography_polarization_BG_annotated.png
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
from astropy.visualization import AsinhStretch, PercentileInterval
import astropy.units as u
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

REPO = Path(__file__).resolve().parents[2]
PIXOUT = REPO / "optical/jwst/prepped/pixel_field"
FITS_ROOT = REPO / "optical/jwst/4598/mastDownload/JWST"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

STEP = 12          # native px between sampled arrows
ARROW_COL = (74, 240, 255)     # accent cyan, "plain" field = single color

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
    return ann

# ── Load shear + reference WCS ──────────────────────────────────────────
ref_fits = list(FITS_ROOT.rglob("*f444w_i2d.fits"))[0]  # o001 tile, first match
with fits.open(ref_fits) as h:
    wcs = WCS(h['SCI'].header)

MARKERS = [
    (sky2px(DM_NW_coord, wcs),  'DM NW',            (122, 180, 255)),
    (sky2px(DM_SE_coord, wcs),  'DM SE (bullet)',   (74, 240, 255)),
    (sky2px(GAS_NW_coord, wcs), 'Gas NW',           (255, 96, 144)),
    (sky2px(GAS_SE_coord, wcs), 'Gas SE (shocked)', (255, 128, 48)),
]

E1 = np.load(PIXOUT / "E1_BG.npy")
E2 = np.load(PIXOUT / "E2_BG.npy")
ny, nx = E1.shape
print(f"Shear grid: {nx}x{ny} native px")

mag = np.sqrt(E1**2 + E2**2)
vmax = np.nanpercentile(mag, 99)
arrow_len = np.clip(mag / max(vmax, 1e-9), 0.15, 1.0) * (STEP * 0.9)
ang = np.arctan2(E2, E1)   # draw at native shear angle (not doubled -- visual direction)

def build_vector_layer(base_rgb, color, width=2):
    """Draw arrows on a copy of base_rgb (PIL Image), return new PIL Image."""
    canvas = base_rgb.copy()
    draw = ImageDraw.Draw(canvas, 'RGBA')
    ys = np.arange(0, ny, STEP)
    xs = np.arange(0, nx, STEP)
    for y in ys:
        y_img = ny - y   # flip to PIL's top-down convention
        row_ang = ang[y, xs]
        row_len = arrow_len[y, xs]
        for x, a, l in zip(xs, row_ang, row_len):
            dx, dy = l * np.cos(a), -l * np.sin(a)   # -sin: FITS y-up -> PIL y-down
            x0, y0 = x - dx/2, y_img - dy/2
            x1, y1 = x + dx/2, y_img + dy/2
            draw.line([(x0, y0), (x1, y1)], fill=color + (230,), width=width)
    return canvas

# ── 1. Plain vector field (dark background, arrows only) ───────────────
print("Building plain vector field (dense, native resolution)...")
dark = Image.new('RGB', (nx, ny), (9, 12, 18))
plain = build_vector_layer(dark, ARROW_COL, width=2)
raw_path = PIXOUT / "vector_field_plain_BG.png"
plain.save(raw_path, optimize=True)
print(f"  -> {raw_path}  ({raw_path.stat().st_size/1e6:.1f} MB, {plain.size})")
ann = annotate(plain, MARKERS, nx, ny)
ann_path = PIXOUT / "vector_field_plain_BG_annotated.png"
ann.save(ann_path, optimize=True)
print(f"  -> {ann_path}  ({ann_path.stat().st_size/1e6:.1f} MB)")

# ── 2. Ptychography composite (real F444W/F356W/F277W) + polarization ──
print("Building ptychography RGB composite (F444W/F356W/F277W, o001 tile)...")
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
    black = np.nanpercentile(a, 45)     # sky background floor -> 0
    white = np.nanpercentile(a, 99.9)   # bright sources -> 1
    a = np.clip((a - black) / max(white - black, 1e-12), 0, 1)
    return stretch(a)

rgb = np.stack([norm_chan(r), norm_chan(g), norm_chan(b)], axis=-1)
rgb8 = (rgb * 255).astype(np.uint8)
composite = Image.fromarray(rgb8, mode='RGB')

# overlay polarization vectors, re-sliced to the composite's (possibly
# smaller) crop -- E1/E2 are on the full (ny, nx) f444w grid already
E1c, E2c = E1[:crop_ny, :crop_nx], E2[:crop_ny, :crop_nx]
magc = np.sqrt(E1c**2 + E2c**2)
vmaxc = np.nanpercentile(magc, 99)
angc = np.arctan2(E2c, E1c)
arrow_lenc = np.clip(magc / max(vmaxc, 1e-9), 0.15, 1.0) * (STEP * 0.9)

draw = ImageDraw.Draw(composite, 'RGBA')
ys = np.arange(0, crop_ny, STEP)
xs = np.arange(0, crop_nx, STEP)
for y in ys:
    y_img = crop_ny - y
    for x in xs:
        a, l = angc[y, x], arrow_lenc[y, x]
        dx, dy = l * np.cos(a), -l * np.sin(a)
        x0, y0 = x - dx/2, y_img - dy/2
        x1, y1 = x + dx/2, y_img + dy/2
        draw.line([(x0, y0), (x1, y1)], fill=(74, 240, 255, 200), width=2)

pty_path = PIXOUT / "ptychography_polarization_BG.png"
composite.save(pty_path, optimize=True)
print(f"  -> {pty_path}  ({pty_path.stat().st_size/1e6:.1f} MB, {composite.size})")

ann2 = annotate(composite, MARKERS, crop_nx, crop_ny)
ann2_path = PIXOUT / "ptychography_polarization_BG_annotated.png"
ann2.save(ann2_path, optimize=True)
print(f"  -> {ann2_path}  ({ann2_path.stat().st_size/1e6:.1f} MB)")

print("\nDone.")
