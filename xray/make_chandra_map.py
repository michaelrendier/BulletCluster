#!/usr/bin/env python3
"""
make_chandra_map.py — merge the 10 Chandra ObsIDs into one 0.5-7 keV
surface-brightness map on a common WCS grid.

WHY: the shape question. Does the polarization gradient track the X-RAY GAS
(real data, Chandra) or the NFW MODEL placed at DM_NW/DM_SE (constants.py)?
Those two are spatially SEPARATED in the Bullet Cluster -- that separation is
the entire published result -- so they are cleanly distinguishable.

  gradient tracks X-ray  -> convergent: eye and algorithm found the same real thing
  gradient tracks NFW    -> circular:   it is the injection in synthetic.py

⚠ HONEST LIMITS OF THIS MAP (no CIAO installed):
  - This is an EXPOSURE-WEIGHTED COUNTS mosaic, not a true surface brightness.
  - No exposure maps: vignetting, chip gaps, QE non-uniformity are NOT corrected.
  - No background subtraction, no point-source removal.
  - Adequate for asking WHERE the gas is (a correlation/morphology question).
  - NOT adequate for photometry, temperature, or any flux measurement.
  If flux is ever needed, install CIAO and use merge_obs / fluximage.
"""
import sys, glob, os
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

BASE   = os.path.dirname(os.path.abspath(__file__))
CHAN   = os.path.join(BASE, 'chandra')
OUT_F  = os.path.join(BASE, 'bullet_chandra_0.5-7keV.fits')
OUT_P  = os.path.join(BASE, 'bullet_chandra_0.5-7keV.png')

# Bullet Cluster field (constants.py DM midpoint region)
CEN_RA, CEN_DEC = 104.6098, -55.9446
FIELD_ARCMIN    = 12.0
PIX_ARCSEC      = 2.0          # ~4x native ACIS 0.492"; good S/N for morphology

E_LO, E_HI = 500.0, 7000.0     # eV

def col_wcs(hdr, cols, xname='x', yname='y'):
    """Build a celestial WCS from an event table's TC* column keywords."""
    ix = cols.index(xname) + 1
    iy = cols.index(yname) + 1
    w = WCS(naxis=2)
    w.wcs.ctype = [hdr[f'TCTYP{ix}'], hdr[f'TCTYP{iy}']]
    w.wcs.crval = [hdr[f'TCRVL{ix}'], hdr[f'TCRVL{iy}']]
    w.wcs.crpix = [hdr[f'TCRPX{ix}'], hdr[f'TCRPX{iy}']]
    w.wcs.cdelt = [hdr[f'TCDLT{ix}'], hdr[f'TCDLT{iy}']]
    return w

# ── target grid ──────────────────────────────────────────────────────────────
npix = int(FIELD_ARCMIN * 60 / PIX_ARCSEC)
grid = WCS(naxis=2)
grid.wcs.ctype = ['RA---TAN', 'DEC--TAN']
grid.wcs.crval = [CEN_RA, CEN_DEC]
grid.wcs.crpix = [npix / 2.0, npix / 2.0]
grid.wcs.cdelt = [-PIX_ARCSEC / 3600.0, PIX_ARCSEC / 3600.0]

img      = np.zeros((npix, npix), dtype=np.float64)
tot_exp  = 0.0
per_obs  = []

print(f"grid: {npix}x{npix} @ {PIX_ARCSEC}\"/pix   field {FIELD_ARCMIN}'")
print(f"centre: RA={CEN_RA} Dec={CEN_DEC}\n")

for evt in sorted(glob.glob(os.path.join(CHAN, '*', '*evt2.fits.gz'))):
    obsid = os.path.basename(os.path.dirname(evt))
    with fits.open(evt) as f:
        h    = f['EVENTS'].header
        d    = f['EVENTS'].data
        cols = [c.name.lower() for c in f['EVENTS'].columns]
        exp  = float(h.get('EXPOSURE', 0.0))

        # energy filter
        if 'energy' in cols:
            e = d['energy']
        elif 'pi' in cols:
            e = d['pi'] * 14.6                     # PI channel -> eV, approx
        else:
            e = None
        m = np.ones(len(d), bool) if e is None else ((e >= E_LO) & (e <= E_HI))

        w  = col_wcs(h, cols)
        ra, dec = w.wcs_pix2world(d['x'][m], d['y'][m], 1)
        px, py  = grid.wcs_world2pix(ra, dec, 0)
        px = np.rint(px).astype(int); py = np.rint(py).astype(int)
        ok = (px >= 0) & (px < npix) & (py >= 0) & (py < npix)

        counts = int(ok.sum())
        np.add.at(img, (py[ok], px[ok]), 1.0)
        tot_exp += exp
        per_obs.append((obsid, len(d), int(m.sum()), counts, exp))
        print(f"  ObsID {obsid:>5}  events {len(d):>7}  in band {int(m.sum()):>7}"
              f"  on grid {counts:>7}  exp {exp/1e3:6.1f} ks")

print(f"\ntotal exposure: {tot_exp/1e3:.1f} ks   total counts on grid: {img.sum():.0f}")

# ── write ────────────────────────────────────────────────────────────────────
hdr = grid.to_header()
hdr['EXPOSURE'] = (tot_exp, 'summed livetime, seconds')
hdr['EBAND']    = (f'{E_LO/1000:.1f}-{E_HI/1000:.1f} keV', 'energy band')
hdr['NOBS']     = (len(per_obs), 'number of ObsIDs merged')
hdr['COMMENT']  = 'Exposure-weighted COUNTS mosaic. No exposure map, no vignetting'
hdr['COMMENT']  = 'correction, no background subtraction. Morphology only.'
fits.PrimaryHDU(img, header=hdr).writeto(OUT_F, overwrite=True)
print(f"wrote {OUT_F}")

# ── quicklook ────────────────────────────────────────────────────────────────
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from scipy.ndimage import gaussian_filter
    sm = gaussian_filter(img, 2.0)
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': grid})
    ax.imshow(np.arcsinh(sm / max(sm.max(), 1e-9) * 50), origin='lower', cmap='inferno')
    from constants_shim import DM_NW, DM_SE, GAS_NW, GAS_SE
    for p, c, mk in [(DM_NW, 'cyan', 'o'), (DM_SE, 'cyan', 'o'),
                     (GAS_NW, 'lime', 'x'), (GAS_SE, 'lime', 'x')]:
        ax.scatter(p['ra'], p['dec'], transform=ax.get_transform('world'),
                   s=90, facecolors='none', edgecolors=c, marker=mk, lw=1.6,
                   label=p['label'])
    ax.set_title(f'Chandra 0.5-7 keV  {tot_exp/1e3:.0f} ks  ({len(per_obs)} ObsIDs)')
    ax.legend(loc='upper right', fontsize=7, framealpha=.4)
    ax.grid(color='white', alpha=.15)
    plt.savefig(OUT_P, dpi=130, bbox_inches='tight')
    print(f"wrote {OUT_P}")
except Exception as ex:
    print(f"(quicklook skipped: {ex})")
