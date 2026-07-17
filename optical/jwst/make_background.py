#!/usr/bin/env python3
"""
make_background.py — real JWST NIRCam color composite + Chandra X-ray gas overlay.

This is the "background" layer: true multi-filter JWST color (chromatic
channel assignment, blue filters -> blue channel etc., asinh/Lupton stretch —
the same algorithm family used for public HST/JWST release images) with the
hot intracluster gas added back in from Chandra X-ray events, in the
traditional Bullet-Cluster pink. JWST near-IR does not see this gas at all —
it only sees starlight — so without this overlay the "missing" ICM plasma
that gives the Bullet Cluster its name would not be in the picture.

Real data only. 8 JWST Program 4598 filters (o001 pointing) + 10 Chandra
ACIS-I obsids, WCS-reprojected onto a common tangent-plane grid.

Output: BulletCluster/JWST_Bullet_Cluster_background.png
"""
import gc, warnings
import numpy as np
from pathlib import Path
from astropy.io import fits
from astropy.wcs import WCS
from astropy.visualization import make_lupton_rgb
from scipy.ndimage import map_coordinates, gaussian_filter
from PIL import Image
warnings.filterwarnings('ignore')

BASE     = Path('/storage/emulated/0/ThePlace/BulletCluster')
JWST_DIR = BASE / 'optical/jwst/4598/mastDownload/JWST'
XRAY_DIR = BASE / 'xray/chandra'
OUT      = BASE / 'JWST_Bullet_Cluster_background.png'
CACHE    = BASE / 'optical/jwst/prepped/background_cache.npz'

# Chromatic channel assignment: reddest JWST filters -> red, bluest -> blue.
FILTERS = {
    'f090w': ('blue',  JWST_DIR/'jw04598-o001_t001_nircam_clear-f090w/jw04598-o001_t001_nircam_clear-f090w_i2d.fits'),
    'f115w': ('blue',  JWST_DIR/'jw04598-o001_t001_nircam_clear-f115w/jw04598-o001_t001_nircam_clear-f115w_i2d.fits'),
    'f150w': ('green', JWST_DIR/'jw04598-o001_t001_nircam_clear-f150w/jw04598-o001_t001_nircam_clear-f150w_i2d.fits'),
    'f200w': ('green', JWST_DIR/'jw04598-o001_t001_nircam_clear-f200w/jw04598-o001_t001_nircam_clear-f200w_i2d.fits'),
    'f277w': ('red',   JWST_DIR/'jw04598-o001_t001_nircam_clear-f277w/jw04598-o001_t001_nircam_clear-f277w_i2d.fits'),
    'f356w': ('red',   JWST_DIR/'jw04598-o001_t001_nircam_clear-f356w/jw04598-o001_t001_nircam_clear-f356w_i2d.fits'),
    'f410m': ('red',   JWST_DIR/'jw04598-o001_t001_nircam_clear-f410m/jw04598-o001_t001_nircam_clear-f410m_i2d.fits'),
    'f444w': ('red',   JWST_DIR/'jw04598-o001_t001_nircam_clear-f444w/jw04598-o001_t001_nircam_clear-f444w_i2d.fits'),
}
CHANDRA_OBSIDS = ['554', '3184', '4984', '4985', '4986', '5355', '5356', '5357', '5358', '5361']


def build_target_wcs(bin_=2):
    """F277W's own footprint (longwave native grid), binned 2x for a cheap-but-sharp background."""
    ref = JWST_DIR / 'jw04598-o001_t001_nircam_clear-f277w/jw04598-o001_t001_nircam_clear-f277w_i2d.fits'
    with fits.open(ref) as h:
        hdr = h['SCI'].header.copy()
    nx, ny = hdr['NAXIS1'] // bin_, hdr['NAXIS2'] // bin_
    hdr['NAXIS1'], hdr['NAXIS2'] = nx, ny
    hdr['CRPIX1'] = hdr['CRPIX1'] / bin_
    hdr['CRPIX2'] = hdr['CRPIX2'] / bin_
    hdr['CDELT1'] = hdr['CDELT1'] * bin_
    hdr['CDELT2'] = hdr['CDELT2'] * bin_
    return WCS(hdr), (ny, nx)


def reproject_filter(path, world_ra, world_dec, out_shape):
    with fits.open(path) as h:
        data = np.nan_to_num(h['SCI'].data.astype(np.float32))
        wcs = WCS(h['SCI'].header)
    src_x, src_y = wcs.wcs_world2pix(world_ra, world_dec, 0)
    out = map_coordinates(data, [src_y, src_x], order=1, mode='constant', cval=0.0)
    bad = (src_x < 0) | (src_x >= data.shape[1]) | (src_y < 0) | (src_y >= data.shape[0])
    out[bad] = 0.0
    del data, src_x, src_y, bad
    gc.collect()
    return out.reshape(out_shape).astype(np.float32)


def build_rgb_and_gas():
    target_wcs, (TH, TW) = build_target_wcs()
    print(f"Target grid: {TW} x {TH}")

    yy, xx = np.mgrid[0:TH, 0:TW]
    world_ra, world_dec = target_wcs.wcs_pix2world(xx.ravel(), yy.ravel(), 0)
    del xx, yy

    channels = {'blue': [], 'green': [], 'red': []}
    for name, (chan, path) in FILTERS.items():
        print(f"  reprojecting {name} -> {chan}")
        channels[chan].append(reproject_filter(path, world_ra, world_dec, (TH, TW)))

    R = np.mean(channels['red'], axis=0)
    G = np.mean(channels['green'], axis=0)
    B = np.mean(channels['blue'], axis=0)
    del channels
    gc.collect()

    # ── Chandra X-ray gas: the plasma JWST near-IR cannot see ──────────────
    print("building Chandra X-ray gas map")
    gas = np.zeros((TH, TW), dtype=np.float64)
    total = 0
    for obsid in CHANDRA_OBSIDS:
        matches = list((XRAY_DIR / obsid).glob('*evt2.fits.gz'))
        if not matches:
            continue
        with fits.open(matches[0]) as h:
            ev = h['EVENTS']
            hdr = ev.header
            d = ev.data
            mask = (d['energy'] >= 500) & (d['energy'] <= 7000)
            cols = list(ev.columns.names)
            xcol, ycol = cols.index('x') + 1, cols.index('y') + 1
            crpx, crpy = hdr[f'TCRPX{xcol}'], hdr[f'TCRPX{ycol}']
            crvl_ra, crvl_dec = hdr[f'TCRVL{xcol}'], hdr[f'TCRVL{ycol}']
            cdlt_ra, cdlt_dec = hdr[f'TCDLT{xcol}'], hdr[f'TCDLT{ycol}']
            xp, yp = d['x'][mask].astype(float), d['y'][mask].astype(float)
            ra = crvl_ra + (xp - crpx) * cdlt_ra
            dec = crvl_dec + (yp - crpy) * cdlt_dec
            px, py = target_wcs.wcs_world2pix(ra, dec, 0)
            ix, iy = np.round(px).astype(int), np.round(py).astype(int)
            valid = (ix >= 0) & (ix < TW) & (iy >= 0) & (iy < TH)
            np.add.at(gas, (iy[valid], ix[valid]), 1)
            total += int(valid.sum())
            print(f"  obsid {obsid}: {int(valid.sum()):,} events on grid")
    print(f"total X-ray events on grid: {total:,}")
    gas = gaussian_filter(gas, sigma=3.0)

    CACHE.parent.mkdir(exist_ok=True)
    np.savez_compressed(CACHE, R=R, G=G, B=B, gas=gas)
    return R, G, B, gas


def make_color(R, G, B, Q=8, stretch_div=6.0, weights=(1.0, 1.0, 1.0)):
    """White-balance each JWST filter channel, then apply the Lupton et al. (2004)
    asinh stretch — the same algorithm family behind public HST/JWST release images."""
    wr, wg, wb = weights

    def norm(a, w):
        pos = a[a > 0]
        ref = float(np.nanpercentile(pos, 99.0)) if pos.size else 1.0
        return a * (w / max(ref, 1e-12))

    Rn, Gn, Bn = norm(R, wr), norm(G, wg), norm(B, wb)

    def robust_min(a):
        pos = a[a > 0]
        return float(np.nanpercentile(pos, 1.0)) if pos.size else 0.0

    mn = min(robust_min(Rn), robust_min(Gn), robust_min(Bn))
    stretch = float(np.nanpercentile(Rn + Gn + Bn, 99.5)) / stretch_div
    return make_lupton_rgb(Rn, Gn, Bn, minimum=mn, stretch=stretch, Q=Q)


def composite(rgb, gas, lo_pct=88, hi_pct=99.9, gamma=1.6, max_alpha=0.72, mode='blend'):
    """Blend the Chandra gas map onto the JWST RGB. Tunable without re-reprojecting."""
    pos = gas[gas > 0]
    lo, hi = np.nanpercentile(pos, [lo_pct, hi_pct]) if pos.size else (0.0, 1.0)
    gas_norm = np.clip((gas - lo) / max(hi - lo, 1e-9), 0, 1) ** gamma

    pink = np.array([255, 70, 150], dtype=np.float32)
    out = rgb.astype(np.float32)
    alpha = (gas_norm * max_alpha)[..., None]
    if mode == 'blend':
        out = out * (1 - alpha) + pink[None, None, :] * alpha
    else:  # additive glow — keeps stars visible under the gas
        out = out + pink[None, None, :] * alpha
    out = np.clip(out, 0, 255).astype(np.uint8)

    # FITS row 0 = south (bottom of sky); flip so north-side content sits at
    # the top of the PNG, matching normal image-viewer orientation.
    out = np.flipud(out)

    # Trim the all-zero rotation-padding border down to the real footprint.
    nonzero_rows = np.where(out.any(axis=(1, 2)))[0]
    nonzero_cols = np.where(out.any(axis=(0, 2)))[0]
    if nonzero_rows.size and nonzero_cols.size:
        out = out[nonzero_rows[0]:nonzero_rows[-1]+1, nonzero_cols[0]:nonzero_cols[-1]+1]
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true', help='recompute reprojection cache')
    ap.add_argument('--lo', type=float, default=88)
    ap.add_argument('--hi', type=float, default=99.9)
    ap.add_argument('--gamma', type=float, default=1.6)
    ap.add_argument('--alpha', type=float, default=0.72)
    ap.add_argument('--mode', choices=['blend', 'additive'], default='blend')
    ap.add_argument('--out', default=str(OUT))
    ap.add_argument('--wr', type=float, default=1.0, help='red channel white-balance weight')
    ap.add_argument('--wg', type=float, default=1.0, help='green channel white-balance weight')
    ap.add_argument('--wb', type=float, default=1.0, help='blue channel white-balance weight')
    ap.add_argument('--Q', type=float, default=8.0, help='Lupton asinh softening')
    ap.add_argument('--stretch-div', type=float, default=6.0)
    args = ap.parse_args()

    if CACHE.exists() and not args.force:
        print(f"loading cached reprojection from {CACHE}")
        z = np.load(CACHE)
        R, G, B, gas = z['R'], z['G'], z['B'], z['gas']
    else:
        R, G, B, gas = build_rgb_and_gas()

    rgb = make_color(R, G, B, Q=args.Q, stretch_div=args.stretch_div,
                      weights=(args.wr, args.wg, args.wb))
    out = composite(rgb, gas, lo_pct=args.lo, hi_pct=args.hi, gamma=args.gamma,
                     max_alpha=args.alpha, mode=args.mode)
    Image.fromarray(out, 'RGB').save(args.out)
    print(f"Saved {args.out}  ({out.shape[1]}x{out.shape[0]})")


if __name__ == '__main__':
    main()
