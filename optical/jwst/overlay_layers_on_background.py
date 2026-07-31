#!/usr/bin/env python3
"""
overlay_layers_on_background.py — the same 3 real-data layers used in
final_dm_lio_polarization.py (kappa density, L_(I|O) deflection alpha,
polarization E), each at 33% opacity, composited directly onto the real
JWST NIRCam color background (JWST_Bullet_Cluster_background.png) instead
of a blank transparent canvas.

Alignment is exact, not eyeballed-resize: background pixels live in
make_background.py's target_wcs (F277W footprint, bin=2), which this repo's
own build showed has ZERO crop offset (row0=col0=0, verified against the
cached R/G/B/gas arrays) -- so the only geometric transform between the
background frame and target_wcs is a vertical flip (flipud applied once in
composite()). kappa/alpha/E all live in the F444W native-pixel WCS. Every
point placed on the background goes through the real chain:
F444W native px -> RA/Dec (F444W WCS) -> target_wcs px -> flip -> background px.
No manual resize-to-fit.

Output: BulletCluster/optical/jwst/prepped/l_io/three_layers_on_background.png
        BulletCluster/Three_Layers_On_JWST_Background.png (top-level copy)
"""
import json, shutil, sys
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
from astropy.io import fits
from astropy.wcs import WCS
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).parent))
from make_background import build_target_wcs

REPO = Path("/storage/emulated/0/ThePlace/BulletCluster")
PIXOUT = REPO / "optical/jwst/prepped/pixel_field"
LIOOUT = REPO / "optical/jwst/prepped/l_io"
FITS_ROOT = REPO / "optical/jwst/4598/mastDownload/JWST"
BG_PATH = REPO / "JWST_Bullet_Cluster_background.png"

LAYER_ALPHA = 0.33          # each layer's opacity, as requested
KAPPA_DOWNSAMPLE = 8        # compute kappa raster on a coarse grid, upscale (cheap)
LIO_STEP_CELLS = 3
POL_STEP_NATIVE = 28
POL_COL = (74, 240, 255)
LIO_COL = (255, 179, 71)
ARROW_SCALE = 6.0           # native-px offset used to sample arrow direction before WCS transform

# ── Load real data (all already computed, no new fitting) ──────────────────
kappa = np.load(LIOOUT / "kappa.npy")
alpha1 = np.load(LIOOUT / "alpha1.npy")
alpha2 = np.load(LIOOUT / "alpha2.npy")
with open(LIOOUT / "l_io_deficit.json") as f:
    lio_meta = json.load(f)
BIN = lio_meta["bin_factor"]
ny_c, nx_c = kappa.shape

E1 = np.load(PIXOUT / "E1_BG.npy")
E2 = np.load(PIXOUT / "E2_BG.npy")
ny_n, nx_n = E1.shape

ref_fits = list(FITS_ROOT.rglob("*f444w_i2d.fits"))[0]
with fits.open(ref_fits) as h:
    f444w_wcs = WCS(h['SCI'].header)

target_wcs, (TH, TW) = build_target_wcs()
bg = Image.open(BG_PATH).convert('RGBA')
assert bg.size == (TW, TH), f"background {bg.size} != target grid {(TW, TH)}"
print(f"background {bg.size}, target grid TH={TH} TW={TW} (crop offset verified 0,0)")

def native_to_bg(x_native, y_native):
    """F444W native px -> background px, via real WCS chain + the one verified flip."""
    ra, dec = f444w_wcs.wcs_pix2world(x_native, y_native, 0)
    x_t, y_t = target_wcs.wcs_world2pix(ra, dec, 0)
    return x_t, (TH - 1 - y_t)   # flipud, zero crop offset

# ── Layer 1: kappa -- inverse-mapped raster, coarse grid then upscaled ─────
print("Building kappa layer (inverse-mapped, coarse then upscaled)...")
oh, ow = TH // KAPPA_DOWNSAMPLE, TW // KAPPA_DOWNSAMPLE
rr, cc = np.mgrid[0:oh, 0:ow]
bg_x = (cc * KAPPA_DOWNSAMPLE).astype(float)
bg_y = (rr * KAPPA_DOWNSAMPLE).astype(float)
# invert native_to_bg: background px -> pre-flip target px -> RA/Dec -> F444W native px
y_t = TH - 1 - bg_y
ra, dec = target_wcs.wcs_pix2world(bg_x, y_t, 0)
x_native, y_native = f444w_wcs.wcs_world2pix(ra, dec, 0)
ix = np.round(x_native / BIN).astype(int)
iy = np.round(y_native / BIN).astype(int)
valid = (ix >= 0) & (ix < nx_c) & (iy >= 0) & (iy < ny_c)
kappa_small = np.full((oh, ow), np.nan)
kappa_small[valid] = kappa[iy[valid], ix[valid]]

vlim = np.nanpercentile(np.abs(kappa_small), 98)
knorm = np.clip(np.nan_to_num(kappa_small) / vlim, -1, 1)
cmap = plt.get_cmap('RdBu_r')
rgba_small = (cmap((knorm + 1) / 2) * 255).astype(np.uint8)
rgba_small[..., 3] = (np.clip(np.abs(knorm) ** 0.7, 0, 1) * 255).astype(np.uint8)
rgba_small[~valid] = 0
kappa_layer = Image.fromarray(rgba_small, 'RGBA').resize((TW, TH), Image.BICUBIC)
print("  kappa layer done")

# ── Layer 2: L_(I|O) deflection, arrows drawn via real coordinate chain ────
print("Drawing L_(I|O) deflection layer...")
lio_layer = Image.new('RGBA', (TW, TH), (0, 0, 0, 0))
draw_lio = ImageDraw.Draw(lio_layer, 'RGBA')
dmag = np.sqrt(alpha1**2 + alpha2**2)
dvmax = np.nanpercentile(dmag, 98)
for j in range(0, ny_c, LIO_STEP_CELLS):
    for i in range(0, nx_c, LIO_STEP_CELLS):
        jb, ib = slice(j, min(j+LIO_STEP_CELLS, ny_c)), slice(i, min(i+LIO_STEP_CELLS, nx_c))
        a1b, a2b = alpha1[jb, ib].mean(), alpha2[jb, ib].mean()
        m = np.hypot(a1b, a2b)
        if not np.isfinite(m) or m == 0:
            continue
        xn = (i + LIO_STEP_CELLS/2 - 0.5) * BIN
        yn = (j + LIO_STEP_CELLS/2 - 0.5) * BIN
        scale = np.clip(m / max(dvmax, 1e-9), 0.3, 1.0) * ARROW_SCALE * BIN
        xn2, yn2 = xn + a1b/m*scale, yn + a2b/m*scale
        x0, y0 = native_to_bg(xn, yn)
        x1, y1 = native_to_bg(xn2, yn2)
        draw_lio.line([(x0, y0), (x1, y1)], fill=LIO_COL + (255,), width=4)
print("  L_(I|O) layer done")

# ── Layer 3: polarization, subdued lines via the same real chain ──────────
print("Drawing polarization layer...")
pol_layer = Image.new('RGBA', (TW, TH), (0, 0, 0, 0))
draw_pol = ImageDraw.Draw(pol_layer, 'RGBA')
mag = np.sqrt(E1**2 + E2**2)
vmaxp = np.nanpercentile(mag, 99)
for y in range(0, ny_n, POL_STEP_NATIVE):
    for x in range(0, nx_n, POL_STEP_NATIVE):
        m = mag[y, x]
        if not np.isfinite(m) or m == 0:
            continue
        e1, e2 = E1[y, x], E2[y, x]
        l = np.clip(m / max(vmaxp, 1e-9), 0.2, 1.0) * ARROW_SCALE * BIN * 0.5
        x2, y2 = x + e1/m*l, y + e2/m*l
        x0, y0 = native_to_bg(x, y)
        x1, y1 = native_to_bg(x2, y2)
        draw_pol.line([(x0, y0), (x1, y1)], fill=POL_COL + (255,), width=2)
print("  polarization layer done")

# ── Composite: background <- kappa(33%) <- polarization(33%) <- L_(I|O)(33%) ─
def blend(base, layer, opacity):
    layer_arr = np.array(layer).astype(np.float32)
    layer_arr[..., 3] *= opacity
    return Image.alpha_composite(base, Image.fromarray(layer_arr.astype(np.uint8), 'RGBA'))

canvas = bg.copy()
canvas = blend(canvas, kappa_layer, LAYER_ALPHA)
canvas = blend(canvas, pol_layer, LAYER_ALPHA)
canvas = blend(canvas, lio_layer, LAYER_ALPHA)

out_path = LIOOUT / "three_layers_on_background.png"
canvas.convert('RGB').save(out_path, optimize=True)
print(f"-> {out_path}  ({canvas.size})")

top_level = REPO / "Three_Layers_On_JWST_Background.png"
shutil.copy(out_path, top_level)
print(f"-> {top_level}")
