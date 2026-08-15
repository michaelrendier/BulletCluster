#!/usr/bin/env python3
"""
halo_spectral_and_power.py — two products from the REAL MeerKAT L-band cube.

(1) SPECTRAL INDEX MAP   alpha, where S ~ nu^alpha, per pixel, 10 planes
    996.6 -> 1656.2 MHz. Traces electron ageing and shock acceleration.

(2) RADIO HALO POWER SPECTRUM  — THE POND TEST.
    Cody: does the halo show interference structure ("gravel in a still pond")
    rather than ordinary turbulence?

        ORDINARY ICM TURBULENCE      -> power-law P(k), NO preferred scale
        INTERFERENCE / STANDING WAVE -> a PEAK in P(k) at one wavelength

    Fit a power law to P(k); a genuine pond surface leaves a localised EXCESS
    above that fit at a characteristic k. Turbulence does not.

⚠ WHAT THIS CAN AND CANNOT SHOW.
  Dark matter does NOT disperse, refract or rotate radio light -- it has no EM
  coupling. Radio propagation effects (DM, RM, free-free) all trace THERMAL
  ELECTRONS. So this maps the GAS. The wave-DM connection is INDIRECT: if the
  DM potential has interference structure, the ICM sitting in that potential
  can inherit it. A detection here is gas responding to a potential, never DM
  seen directly.

⚠ RESOLUTION LIMIT. Beam 6.92" (Farcsec) / 15" at z=0.296 -> ~31 / ~67 kpc per
  beam. Fuzzy-DM de Broglie structure for m~1e-22 eV is ~kpc. Only the
  LARGEST-scale interference could ever appear. State this before, not after.
"""
import os, sys
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
import warnings; warnings.filterwarnings('ignore')

BASE = "/home/rendier/Projects/ThePlace/BulletCluster/radio/meerkat/MGCLS_DR1"
CUBE = f"{BASE}/enhanced/frequency_cubes/Bullet_aFix_pol_I_15arcsec_fcube_cor.fits.gz"
OUT  = "/home/rendier/Projects/ThePlace/BulletCluster/radio"
CROP = 900                      # px half-width around cluster centre
Z_CL = 0.296

print("loading cube ...")
h    = fits.open(CUBE)
hd   = h[0].header
cube = h[0].data[0]             # (nfreq, ny, nx)
nf, ny, nx = cube.shape
freqs = np.array([hd.get(f'FREQ{i:04d}', np.nan) for i in range(1, nf+1)])
ok_pl = np.isfinite(freqs)
print(f"  cube {nx}x{ny}, {nf} planes; usable {ok_pl.sum()}")
print(f"  freq {np.nanmin(freqs)/1e6:.1f} - {np.nanmax(freqs)/1e6:.1f} MHz")
bmaj = hd.get('BMAJ', 0)*3600
pscl = abs(hd.get('CDELT1'))*3600
kpc_per_arcsec = 4.45           # z=0.296, flat LCDM H0=70
print(f"  beam {bmaj:.2f}\"  pixel {pscl:.2f}\"/px  -> {bmaj*kpc_per_arcsec:.0f} kpc/beam")

# crop to the cluster
cy, cx = ny//2, nx//2
sub = cube[:, cy-CROP:cy+CROP, cx-CROP:cx+CROP][ok_pl]
fr  = freqs[ok_pl]
print(f"  crop {sub.shape[2]}x{sub.shape[1]} = {sub.shape[2]*pscl/60:.1f}'")

# noise from the outer frame of the band-averaged map
band = np.nanmean(sub, axis=0)
edge = np.concatenate([band[:80].ravel(), band[-80:].ravel(),
                       band[:, :80].ravel(), band[:, -80:].ravel()])
rms  = float(np.nanstd(edge[np.isfinite(edge)]))
print(f"  map rms  {rms*1e6:.1f} uJy/beam   peak {np.nanmax(band)*1e3:.2f} mJy/beam")

# ── (1) SPECTRAL INDEX ───────────────────────────────────────────────────────
print("\n" + "="*68)
print("(1) SPECTRAL INDEX MAP")
print("="*68)
SNR = 5.0
good = np.isfinite(sub) & (sub > 0)
det  = (good.sum(0) >= 6) & (band > SNR*rms)
print(f"  pixels with >=6 good planes and S/N>{SNR:.0f}: {det.sum():,}")

lx = np.log10(fr)[:, None]
alpha = np.full(band.shape, np.nan)
yy, xx = np.where(det)
S = sub[:, yy, xx]
m = np.isfinite(S) & (S > 0)
ly = np.where(m, np.log10(np.where(S > 0, S, 1e-12)), np.nan)
n  = m.sum(0)
sx = np.nansum(np.where(m, lx, 0), 0); sy = np.nansum(np.where(m, ly, 0), 0)
sxx= np.nansum(np.where(m, lx**2, 0), 0); sxy = np.nansum(np.where(m, lx*ly, 0), 0)
den = n*sxx - sx**2
sl  = np.where(den != 0, (n*sxy - sx*sy)/np.where(den == 0, 1, den), np.nan)
alpha[yy, xx] = sl
a = alpha[np.isfinite(alpha)]
print(f"  alpha: median {np.median(a):+.2f}   16-84% [{np.percentile(a,16):+.2f}, "
      f"{np.percentile(a,84):+.2f}]")
print("    (halo/relic synchrotron typically -1 to -2; flat ~0 = compact/thermal)")
fits.PrimaryHDU(alpha.astype('float32')).writeto(f"{OUT}/bullet_spectral_index.fits",
                                                 overwrite=True)
print(f"  wrote {OUT}/bullet_spectral_index.fits")

# ── (2) POWER SPECTRUM — THE POND TEST ───────────────────────────────────────
print("\n" + "="*68)
print("(2) RADIO HALO POWER SPECTRUM  —  power law vs preferred scale")
print("="*68)

img = band.copy()
# mask compact sources: anything > 20 sigma, dilated
from scipy.ndimage import binary_dilation, gaussian_filter, median_filter
src = binary_dilation(img > 20*rms, iterations=6)
filled = median_filter(img, size=15)
img = np.where(src, filled, img)
img = np.nan_to_num(img - np.nanmedian(img))
print(f"  compact-source pixels masked/filled: {src.sum():,} "
      f"({100*src.mean():.2f}% of crop)")

w = np.hanning(img.shape[0])[:, None] * np.hanning(img.shape[1])[None, :]
F = np.fft.fftshift(np.fft.fft2(img*w))
P = np.abs(F)**2
c0, c1 = np.array(P.shape)//2
yy2, xx2 = np.indices(P.shape)
r = np.sqrt((yy2-c0)**2 + (xx2-c1)**2).astype(int)
nb = min(c0, c1)
k = np.arange(2, nb)
Pk = np.array([P[r == i].mean() for i in k])

# angular scale per k
Ns = img.shape[0]
lam_px  = Ns / k
lam_as  = lam_px * pscl
lam_kpc = lam_as * kpc_per_arcsec

# power-law fit over scales between ~2 beams and the crop quarter
fitm = (lam_as > 2.5*bmaj) & (lam_as < Ns*pscl/4)
cf = np.polyfit(np.log10(k[fitm]), np.log10(Pk[fitm]), 1)
print(f"  power-law fit: P(k) ~ k^{cf[0]:.2f}   over {lam_kpc[fitm].min():.0f}"
      f"-{lam_kpc[fitm].max():.0f} kpc")
print(f"    (Kolmogorov 2D projection ~ -11/3 = -3.67; -3 to -4 = ordinary turbulence)")

resid = np.log10(Pk) - np.polyval(cf, np.log10(k))
sd = resid[fitm].std()
print(f"\n  {'k':>5}{'lambda (kpc)':>14}{'log excess':>12}{'sigma':>8}")
for i in range(0, fitm.sum(), max(1, fitm.sum()//12)):
    j = np.where(fitm)[0][i]
    print(f"  {k[j]:>5}{lam_kpc[j]:>14.0f}{resid[j]:>12.3f}{resid[j]/sd:>8.2f}")

jb = np.where(fitm)[0][np.argmax(resid[fitm])]
print(f"\n  largest excess: lambda = {lam_kpc[jb]:.0f} kpc  "
      f"({resid[jb]/sd:+.2f} sigma above the power law)")

print("\n" + "="*68)
print("VERDICT")
print("="*68)
if resid[jb]/sd > 3:
    print(f"  PEAK at {lam_kpc[jb]:.0f} kpc, {resid[jb]/sd:.1f}x the scatter.")
    print("  -> a preferred scale. Consistent with standing-wave structure.")
else:
    print(f"  No significant peak. Largest excess {resid[jb]/sd:+.2f} sigma at "
          f"{lam_kpc[jb]:.0f} kpc.")
    print(f"  P(k) ~ k^{cf[0]:.2f} is a clean power law -> ORDINARY TURBULENCE.")
    print("  The halo does not show a pond surface at scales this beam can reach.")
