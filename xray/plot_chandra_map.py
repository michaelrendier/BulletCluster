#!/usr/bin/env python3
"""Quicklook for the merged Chandra map. Imports matplotlib/scipy BEFORE
astropy so the apt numcodecs / numpy-2 clash cannot poison the import graph."""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from constants_shim import DM_NW, DM_SE, GAS_NW, GAS_SE

f = fits.open('bullet_chandra_0.5-7keV.fits')
img, hdr = f[0].data, f[0].header
w = WCS(hdr)
sm = gaussian_filter(img, 2.0)
fig, ax = plt.subplots(figsize=(9, 9), subplot_kw={'projection': w})
ax.imshow(np.arcsinh(sm / max(sm.max(), 1e-9) * 60), origin='lower', cmap='inferno')
for p, c, mk in [(DM_NW,'cyan','o'), (DM_SE,'cyan','o'),
                 (GAS_NW,'lime','x'), (GAS_SE,'lime','x')]:
    ax.scatter(p['ra'], p['dec'], transform=ax.get_transform('world'),
               s=120, facecolors='none', edgecolors=c, marker=mk, lw=1.8, label=p['label'])
ax.set_title(f"Chandra 0.5-7 keV   {hdr['EXPOSURE']/1e3:.0f} ks   {hdr['NOBS']} ObsIDs   "
             f"{img.sum():.0f} counts")
ax.legend(loc='upper right', fontsize=8, framealpha=.4)
ax.grid(color='white', alpha=.15)
plt.savefig('bullet_chandra_0.5-7keV.png', dpi=140, bbox_inches='tight')
print('wrote bullet_chandra_0.5-7keV.png')
print(f"peak count pixel: {img.max():.0f}   total: {img.sum():.0f}")
