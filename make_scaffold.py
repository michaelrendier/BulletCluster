# SPDX-License-Identifier: GPL-3.0-only
"""
make_scaffold.py: raw and false-colour images of JWST data on disk (the Witch's Hat background scaffolds).

Algorithm (restored from BulletCluster commit 8e482d2, optical/jwst/make_background.py, and generalised):
  1. read each filter's level-3 `i2d` mosaic (SCI, MJy/sr), block-averaged in strips so large mosaics fit in memory;
  2. reproject every filter of a group onto one north-up tangent-plane grid (order-1 interpolation through world coordinates);
  3. chromatic assignment: filters sorted by wavelength, shortest third -> blue, middle -> green, longest -> red (filters sharing a channel are averaged);
  4. white-balance each channel by its 99th percentile of positive values; black point = 1st percentile of positives;
  5. Lupton et al. (2004, PASP 116, 133) asinh stretch (astropy make_lupton_rgb; Q = 8, stretch = 99.5th percentile of R+G+B / 6).
One filter: asinh-stretched 'inferno' false colour. IFU cubes (s3d): thirds of the wavelength axis -> B, G, R.
RAW image = one filter's own pixel grid, asinh grey stretch (orientation as stored, row 0 at the bottom of the sky).
Usage: python3 make_scaffold.py OUTDIR TARGET_NAME DIR [DIR ...]
"""
import os, re, sys, glob, gc, warnings
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy.visualization import make_lupton_rgb
from scipy.ndimage import map_coordinates
from PIL import Image
import matplotlib
matplotlib.use("Agg")
from matplotlib import cm
warnings.filterwarnings("ignore")
OUTMAX = 2200      # longest side of a false-colour composite, pixels
RAWMAX = 1600      # longest side of a raw image


def wavelength_um(name):
    m = re.search(r"[fF](\d{3,4})[wWmMnN]", name)
    if not m: return 0.0
    v = int(m.group(1)); return v / 100.0 if (v >= 400 and "miri" in name.lower()) else v / 100.0


def load_reduced(path, maxside):
    """Block-mean the SCI plane in strips; returns (array, wcs, factor, native_scale_arcsec)."""
    with fits.open(path, memmap=True) as h:
        sci = h["SCI"]; ny, nx = sci.shape; w = WCS(sci.header)
        f = max(1, int(np.ceil(max(ny, nx) / maxside)))
        oy, ox = ny // f, nx // f
        out = np.full((oy, ox), np.nan, np.float32)
        step = 256 * f
        for y0 in range(0, oy * f, step):
            y1 = min(y0 + step, oy * f)
            strip = np.array(sci.data[y0:y1, :ox * f], dtype=np.float32)
            strip[strip == 0] = np.nan
            blk = strip.reshape((y1 - y0) // f, f, ox, f)
            with np.errstate(all="ignore"):
                out[y0 // f:y1 // f] = np.nanmean(blk, axis=(1, 3))
        scale = float(np.sqrt(abs(np.linalg.det(w.pixel_scale_matrix)))) * 3600
        w2 = w.deepcopy(); w2.wcs.crpix = (np.array(w.wcs.crpix) - 0.5 - (f - 1) / 2) / f + 0.5
        if w2.wcs.has_cd(): w2.wcs.cd = w.wcs.cd * f
        else: w2.wcs.cdelt = np.array(w.wcs.cdelt) * f
        return out, w2, f, scale


def asinh_gray(a, lo=1, hi=99.7):
    v = a[np.isfinite(a) & (a > 0)]
    if v.size == 0: return np.zeros(a.shape, np.uint8)
    l, h = np.percentile(v, [lo, hi]); x = np.clip((np.nan_to_num(a) - l) / max(h - l, 1e-12), 0, 1)
    return (np.arcsinh(10 * x) / np.arcsinh(10) * 255).astype(np.uint8)


def save(arr, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(np.flipud(arr)).save(path, optimize=True)


def composite(files, outdir, tag):
    """files: list of i2d paths of ONE pointing/instrument. Writes raw per filter and one false-colour composite."""
    items = []
    for p in files:
        name = os.path.basename(p); a, w, f, sc = load_reduced(p, RAWMAX)
        save(asinh_gray(a), os.path.join(outdir, "raw", name.replace("_i2d.fits", "_raw.png")))
        items.append((wavelength_um(name), name, a, w, sc * f))
    items.sort(key=lambda t: t[0])
    if len(items) == 1:
        a = items[0][2]; g = asinh_gray(a); rgb = (matplotlib.colormaps["inferno"](g / 255.0)[..., :3] * 255).astype(np.uint8)
        save(rgb, os.path.join(outdir, "false_color", f"{tag}_{items[0][1].split('_i2d')[0]}_inferno.png")); return [items[0][1]]
    # common grid from the union of footprints
    corners = []
    for _, _, a, w, _ in items:
        ny, nx = a.shape; x = np.array([0, nx - 1, nx - 1, 0]); y = np.array([0, 0, ny - 1, ny - 1])
        ra, dec = w.wcs_pix2world(x, y, 0); corners.append(np.stack([ra, dec], 1))
    c = np.vstack(corners); ra0, dec0 = np.degrees(np.angle(np.mean(np.exp(1j * np.radians(c[:, 0]))))) % 360, c[:, 1].mean()
    tw = WCS(naxis=2); tw.wcs.ctype = ["RA---TAN", "DEC--TAN"]; tw.wcs.crval = [ra0, dec0]
    # footprint in tangent plane (degrees)
    xi = (((c[:, 0] - ra0 + 180) % 360) - 180) * np.cos(np.radians(dec0)); eta = c[:, 1] - dec0
    spanx, spany = xi.max() - xi.min(), eta.max() - eta.min(); pix = max(spanx, spany) / OUTMAX
    pix = max(pix, min(i[4] for i in items) / 3600)
    nx, ny = int(np.ceil(spanx / pix)) + 2, int(np.ceil(spany / pix)) + 2
    tw.wcs.cdelt = [-pix, pix]; tw.wcs.crpix = [(nx + 1) / 2 - (xi.max() + xi.min()) / 2 / (-pix) * -1 * -1 if False else (nx + 1) / 2 + (xi.min() + xi.max()) / 2 / pix, (ny + 1) / 2 - (eta.min() + eta.max()) / 2 / pix]
    yy, xx = np.mgrid[0:ny, 0:nx]; ra, dec = tw.wcs_pix2world(xx.ravel(), yy.ravel(), 0)
    planes = []
    for lam, name, a, w, sc in items:
        sx, sy = w.wcs_world2pix(ra, dec, 0)
        out = map_coordinates(np.nan_to_num(a), [sy, sx], order=1, mode="constant", cval=0.0)
        out[(sx < 0) | (sx > a.shape[1] - 1) | (sy < 0) | (sy > a.shape[0] - 1)] = 0
        planes.append((lam, name, out.reshape(ny, nx).astype(np.float32))); del sx, sy, out; gc.collect()
    n = len(planes); idx = np.array_split(np.arange(n), 3) if n >= 3 else [[0], list(range(n)), [n - 1]]
    B, G, R = [np.mean([planes[i][2] for i in g], axis=0) for g in idx]
    def lup(R, G, B, skysub):
        def prep(a):
            pos = a[a > 0]
            if pos.size == 0: return a
            if skysub: a = np.clip(a - float(np.percentile(pos, 15)), 0, None)   # per-channel sky pedestal (10-20th percentile of positive pixels)
            pos = a[a > 0]; ref = float(np.percentile(pos, 99)) if pos.size else 1.0
            return a / max(ref, 1e-12)
        Rn, Gn, Bn = prep(R), prep(G), prep(B)
        mn = 0.0 if skysub else min(float(np.percentile(x[x > 0], 1)) if (x > 0).any() else 0.0 for x in (Rn, Gn, Bn))
        stretch = float(np.percentile(Rn + Gn + Bn, 99.5)) / 6.0
        rgb = make_lupton_rgb(Rn, Gn, Bn, minimum=mn, stretch=max(stretch, 1e-6), Q=8)
        rows = np.where(rgb.any(axis=(1, 2)))[0]; cols = np.where(rgb.any(axis=(0, 2)))[0]
        return rgb[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1] if rows.size else rgb
    # image row 0 = south; save() flips so the PNG has north up
    save(lup(R, G, B, True), os.path.join(outdir, "false_color", f"{tag}_rgb_lupton.png"))
    save(lup(R, G, B, False), os.path.join(outdir, "false_color", f"{tag}_rgb_lupton_nosky.png"))
    with open(os.path.join(outdir, "false_color", f"{tag}_rgb_lupton.txt"), "w") as fh:
        fh.write("_rgb_lupton.png = sky-subtracted (per-channel 15th percentile of positive pixels removed); _rgb_lupton_nosky.png = the original BulletCluster algorithm without sky subtraction\nchannels (blue -> red): " + " | ".join(",".join(planes[i][1].split("_i2d")[0] for i in g) for g in idx) + f"\ngrid {nx}x{ny}, pixel {pix * 3600:.3f} arcsec\n")
    return [p[1] for p in planes]


def cube(path, outdir):
    """IFU cube: raw = collapsed median image; false colour = thirds of the wavelength axis as B, G, R."""
    name = os.path.basename(path).replace("_s3d.fits", "")
    with fits.open(path, memmap=True) as h:
        d = np.array(h["SCI"].data, dtype=np.float32)
    d[d == 0] = np.nan
    if d.ndim != 3 or d.shape[0] < 3: return None
    with np.errstate(all="ignore"):
        med = np.nanmedian(d, axis=0); thirds = [np.nanmean(d[s], axis=0) for s in np.array_split(np.arange(d.shape[0]), 3)]
    up = lambda a: np.kron(a, np.ones((max(1, 600 // max(a.shape)),) * 2, dtype=a.dtype))
    save(up(asinh_gray(med)), os.path.join(outdir, "raw", name + "_collapsed_raw.png"))
    R, G, B = [np.nan_to_num(t) for t in thirds[::-1]][::-1]
    B, G, R = [np.nan_to_num(t) for t in thirds]
    def norm(a):
        pos = a[a > 0]; ref = float(np.percentile(pos, 99)) if pos.size else 1.0; return a / max(ref, 1e-12)
    Rn, Gn, Bn = norm(R), norm(G), norm(B)
    mn = min(float(np.percentile(x[x > 0], 1)) if (x > 0).any() else 0.0 for x in (Rn, Gn, Bn))
    rgb = make_lupton_rgb(Rn, Gn, Bn, minimum=mn, stretch=max(float(np.percentile(Rn + Gn + Bn, 99.5)) / 6.0, 1e-6), Q=8)
    sc = max(1, 600 // max(rgb.shape[:2])); rgb = np.kron(rgb, np.ones((sc, sc, 1), dtype=np.uint8))
    save(rgb, os.path.join(outdir, "false_color", name + "_cube_thirds_rgb.png"))
    return name


def groups(dirs):
    files = sorted({p for d in dirs for p in glob.glob(os.path.join(d, "**", "*_i2d.fits"), recursive=True)})
    g = {}
    for p in files:
        n = os.path.basename(p); inst = "miri" if "miri" in n.lower() else ("nircam" if "nircam" in n.lower() else "other")
        m = re.search(r"-?(o\d{3})_", n); key = (inst, m.group(1) if m else "")
        g.setdefault(key, []).append(p)
    return g, sorted({p for d in dirs for p in glob.glob(os.path.join(d, "**", "*_s3d.fits"), recursive=True)})


if __name__ == "__main__":
    out, target, dirs = sys.argv[1], sys.argv[2], sys.argv[3:]
    g, cubes = groups(dirs); odir = os.path.join(out, target)
    for (inst, obs), fl in sorted(g.items()):
        tag = f"{target}_{inst}{('_' + obs) if obs else ''}"
        print(tag, len(fl), "files", flush=True)
        fc = os.path.join(odir, "false_color")
        if os.path.isdir(fc) and any(x.startswith(tag) for x in os.listdir(fc)): print("  exists, skipped", flush=True); continue
        try: print("  ->", composite(fl, odir, tag), flush=True)
        except Exception as e: print("  FAILED", tag, type(e).__name__, e, flush=True)
    for c in cubes:
        nm = os.path.basename(c).replace("_s3d.fits", "")
        if os.path.exists(os.path.join(odir, "false_color", nm + "_cube_thirds_rgb.png")): continue
        try: cube(c, odir)
        except Exception as e: print("  CUBE FAILED", os.path.basename(c), type(e).__name__, e, flush=True)
    print("cubes:", len(cubes))
