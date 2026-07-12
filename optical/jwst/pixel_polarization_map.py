#!/usr/bin/env python3
"""
pixel_polarization_map.py — Giant native-pixel-resolution polarization map.

pixel_vector_field.py computes one (e1, e2) shear vector per native JWST
pixel (14.1M vectors) but the quiver plots it makes can only *display*
~120 arrows across (14M arrows on screen is just noise). This script
renders the SAME native-resolution field as a continuous HSV color image
instead -- hue = polarization angle (2*theta, shear's natural double-angle
symmetry), value = magnitude -- written at the array's true pixel
dimensions (5647x2505 native JWST pixels), with NO matplotlib resampling
anywhere in the raster path. Every pixel of the output PNG corresponds to
exactly one native JWST pixel's measured shear value, so the image can be
zoomed arbitrarily in a normal image viewer without hitting interpolation
artifacts -- you always land on real data, not display resampling.

Honest caveat (same one pixel_vector_field.py states, worth repeating
here since this is the "zoom in" product): the underlying measurement
density is ~2500 galaxies smoothed at sigma=60 native px. Zooming into
this image reveals the true PIXEL GRID resolution, not new information
below the smoothing scale -- the color field is smooth by construction
at that scale.

Outputs -> optical/jwst/prepped/pixel_field/:
    polarization_giant_<label>.png              (label: ALL, BG, CL)
        pure per-pixel HSV field, native resolution, no annotation
    polarization_giant_<label>_annotated.png
        same + DM/gas position crosses, native resolution
    polarization_giant_legend.png
        color wheel (hue=angle, brightness=magnitude) + marker key,
        normal-sized reference image (not giant)
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.colors as mcolors
from pathlib import Path
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
import warnings
warnings.filterwarnings('ignore')

REPO = Path(__file__).resolve().parents[2]   # BulletCluster/
PIXOUT = REPO / "optical/jwst/prepped/pixel_field"
FITS_ROOT = REPO / "optical/jwst/4598/mastDownload/JWST"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

RA0, DEC0 = 104.6098, -55.9446
DM_NW_coord = SkyCoord(ra=104.6383*u.deg, dec=-55.9252*u.deg)
DM_SE_coord = SkyCoord(ra=104.5726*u.deg, dec=-55.9563*u.deg)
GAS_NW_coord = SkyCoord(ra=104.625*u.deg, dec=-55.930*u.deg)
GAS_SE_coord = SkyCoord(ra=104.569*u.deg, dec=-55.961*u.deg)

ref_fits = list(FITS_ROOT.rglob("*f444w_i2d.fits"))[0]
with fits.open(ref_fits) as h:
    wcs = WCS(h['SCI'].header)

def sky2px(coord):
    x, y = wcs.world_to_pixel(coord)
    return float(x), float(y)

MARKERS = [
    (sky2px(DM_NW_coord),  'DM NW',            (122, 180, 255)),
    (sky2px(DM_SE_coord),  'DM SE (bullet)',   (74, 240, 255)),
    (sky2px(GAS_NW_coord), 'Gas NW',           (255, 96, 144)),
    (sky2px(GAS_SE_coord), 'Gas SE (shocked)', (255, 128, 48)),
]

def field_to_rgb8(E1, E2, vmax_pct=99):
    mag = np.sqrt(E1**2 + E2**2)
    ang = 0.5 * np.arctan2(E2, E1)          # shear double-angle, period pi
    hue = (ang % np.pi) / np.pi
    vmax = np.nanpercentile(mag, vmax_pct)
    val = np.clip(mag / max(vmax, 1e-9), 0.05, 1.0)   # floor so nothing is pure black
    sat = np.full_like(val, 0.92)
    hsv = np.stack([hue, sat, val], axis=-1)
    rgb = mcolors.hsv_to_rgb(hsv)
    return (rgb * 255).astype(np.uint8), mag, vmax

def draw_cross(draw, x, y, color, r=22, w=5):
    draw.line([(x-r, y), (x+r, y)], fill=color, width=w)
    draw.line([(x, y-r), (x, y+r)], fill=color, width=w)
    draw.ellipse([x-r*1.6, y-r*1.6, x+r*1.6, y+r*1.6], outline=color, width=3)

def make_legend(out_path, size=520):
    img = Image.new('RGB', (size, size), (9, 12, 18))
    cx = cy = size // 2
    R = size // 2 - 40
    yy, xx = np.mgrid[0:size, 0:size]
    dx, dy = xx - cx, yy - cy
    r = np.sqrt(dx**2 + dy**2) / R
    ang = (np.arctan2(dy, dx)) % np.pi / np.pi
    val = np.clip(r, 0.05, 1.0)
    sat = np.full_like(val, 0.92)
    mask = r <= 1.0
    hsv = np.stack([ang, sat, val], axis=-1)
    rgb = (mcolors.hsv_to_rgb(hsv) * 255).astype(np.uint8)
    rgb[~mask] = (9, 12, 18)
    wheel = Image.fromarray(rgb, mode='RGB')
    img.paste(wheel, (0, 0))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT, 20)
    small = ImageFont.truetype(FONT, 16)
    draw.text((cx, 14), "angle (hue, period pi)", fill=(200, 216, 232), font=small, anchor='mt')
    draw.text((cx, size - 34), "magnitude -> center=low, edge=high (99th pct)", fill=(200, 216, 232), font=small, anchor='mt')
    y0 = size + 0  # unused, placeholder to keep structure simple
    legend_h = 4 * 34 + 30
    full = Image.new('RGB', (size, size + legend_h), (9, 12, 18))
    full.paste(img, (0, 0))
    d2 = ImageDraw.Draw(full)
    ty = size + 12
    for (_, label, color) in MARKERS:
        draw_cross(d2, 30, ty + 12, color, r=12, w=3)
        d2.text((60, ty), label, fill=(220, 230, 240), font=font, anchor='lm')
        ty += 34
    full.save(out_path)
    print(f"-> {out_path}")

make_legend(PIXOUT / "polarization_giant_legend.png")

for label in ['BG', 'ALL', 'CL']:
    E1 = np.load(PIXOUT / f"E1_{label}.npy")
    E2 = np.load(PIXOUT / f"E2_{label}.npy")
    ny, nx = E1.shape
    rgb8, mag, vmax = field_to_rgb8(E1, E2)
    print(f"{label}: {nx}x{ny} native px  |alpha_e| 99th pct = {vmax:.4f}")

    img = Image.fromarray(rgb8, mode='RGB')
    raw_path = PIXOUT / f"polarization_giant_{label}.png"
    img.save(raw_path, optimize=True)
    print(f"  -> {raw_path}  ({raw_path.stat().st_size/1e6:.1f} MB, {img.size[0]}x{img.size[1]})")

    ann = img.copy()
    draw = ImageDraw.Draw(ann)
    font = ImageFont.truetype(FONT, 44)
    for (px, py), lbl, color in MARKERS:
        if 0 <= px < nx and 0 <= py < ny:
            py_img = ny - py   # FITS y is bottom-up; PIL y is top-down
            draw_cross(draw, px, py_img, color, r=34, w=7)
            draw.text((px + 40, py_img - 20), lbl, fill=color, font=font,
                       stroke_width=3, stroke_fill=(9, 12, 18))
    ann_path = PIXOUT / f"polarization_giant_{label}_annotated.png"
    ann.save(ann_path, optimize=True)
    print(f"  -> {ann_path}  ({ann_path.stat().st_size/1e6:.1f} MB)")

print("\nDone. Open in any image viewer and zoom -- every PNG pixel is one native JWST pixel.")
