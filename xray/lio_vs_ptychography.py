#!/usr/bin/env python3
"""
lio_vs_ptychography.py — VALIDATING "the ptychography and the L_(I|O) match up".

Two questions, both with a built-in null.

Q1. IS psi (= L_(I|O) - L) SIGNAL, OR INTEGRATED NOISE?
    psi is a DOUBLE INTEGRAL of kappa (grad^2 psi = 2 kappa). Integration is a
    steep low-pass: it amplifies large scales enormously. So NOISE in kappa
    becomes a SMOOTH LARGE-SCALE GRADIENT in psi -- which is exactly what the
    slingshot map's middle panel looks like.
    NULL: run the identical pipeline on the B-mode (shear rotated 45 deg, which
    carries no lensing signal). If psi_B is just as smooth and just as large,
    psi_E is integrated noise.

Q2. DOES THE EMISSION ("ptychography") CORRELATE WITH psi / |alpha|?
    NULL: the same correlation against the B-mode products. A real light-traces-
    mass correlation appears in E and NOT in B. A sampling systematic -- shear is
    measured AT galaxy positions, so its sampling density follows the light --
    appears in BOTH.
"""
import sys, glob
import numpy as np
from astropy.io import fits

sys.path.insert(0, "/home/rendier/Projects/ThePlace/ValaQuenta/modules/l_io_photon_path")
from maths import bounded_lensing_pipeline

PIX   = "/home/rendier/Projects/ThePlace/BulletCluster/optical/jwst/prepped/pixel_field"
FITSR = "/home/rendier/Projects/ThePlace/BulletCluster/optical/jwst/4598/mastDownload/JWST"
BIN, PSCL = 32, 1.929

def block_average(a, b):
    ny, nx = a.shape
    ny_c, nx_c = ny//b, nx//b
    return a[:ny_c*b, :nx_c*b].reshape(ny_c, b, nx_c, b).mean(axis=(1, 3))

E1 = np.load(f"{PIX}/E1_BG.npy"); E2 = np.load(f"{PIX}/E2_BG.npy")
g1, g2 = block_average(E1, BIN), block_average(E2, BIN)
ny, nx = g1.shape

E = bounded_lensing_pipeline(g1, g2, PSCL, taper_frac=0.1, pad_factor=2.0)
B = bounded_lensing_pipeline(-g2, g1, PSCL, taper_frac=0.1, pad_factor=2.0)

aE = np.hypot(E['alpha1'], E['alpha2'])
aB = np.hypot(B['alpha1'], B['alpha2'])

print("="*70)
print("Q1. IS psi SIGNAL OR INTEGRATED NOISE?")
print("="*70)
print(f"{'quantity':<16}{'E-mode':>14}{'B-mode':>14}{'E/B':>9}")
for nm, e_, b_ in [('kappa  rms', E['kappa'], B['kappa']),
                   ('psi    rms', E['psi'],  B['psi']),
                   ('|alpha| rms', aE, aB),
                   ('psi    p-p', None, None)]:
    if e_ is None:
        pe = np.nanmax(E['psi'])-np.nanmin(E['psi'])
        pb = np.nanmax(B['psi'])-np.nanmin(B['psi'])
        print(f"{nm:<16}{pe:>14.3f}{pb:>14.3f}{pe/pb:>9.3f}")
    else:
        re_, rb_ = np.nanstd(e_), np.nanstd(b_)
        print(f"{nm:<16}{re_:>14.5f}{rb_:>14.5f}{re_/rb_:>9.3f}")

# how much of psi is a single large-scale mode?
def largescale_frac(m):
    m = np.nan_to_num(m - np.nanmean(m))
    F = np.fft.fftshift(np.fft.fft2(m)); P = np.abs(F)**2
    cy, cx = np.array(P.shape)//2
    y, x = np.indices(P.shape); r = np.sqrt((y-cy)**2+(x-cx)**2)
    return float(P[r <= 3].sum()/P.sum())
print(f"\npower in the 3 lowest wavenumbers (a pure gradient -> ~1.0):")
print(f"  psi_E {largescale_frac(E['psi']):.4f}    psi_B {largescale_frac(B['psi']):.4f}")
print(f"  kap_E {largescale_frac(E['kappa']):.4f}    kap_B {largescale_frac(B['kappa']):.4f}")

# ── Q2. emission vs L_(I|O) ─────────────────────────────────────────────────
ref = sorted(glob.glob(f"{FITSR}/**/*f444w_i2d.fits", recursive=True))[0]
sci = fits.open(ref)['SCI'].data
sci = sci[:E1.shape[0], :E1.shape[1]]
emis = block_average(np.nan_to_num(sci), BIN)
emis = np.log10(np.clip(emis, np.nanpercentile(emis, 5), None))

def pear(a, b):
    m = np.isfinite(a) & np.isfinite(b)
    a, b = a[m]-a[m].mean(), b[m]-b[m].mean()
    return float((a*b).sum()/np.sqrt((a*a).sum()*(b*b).sum()))

def shift_null(a, b, n=1500, seed=1):
    rng = np.random.default_rng(seed); out=[]
    for _ in range(n):
        out.append(pear(np.roll(np.roll(a, rng.integers(1,ny),0), rng.integers(1,nx),1), b))
    return np.array(out)

print("\n" + "="*70)
print("Q2. DOES THE EMISSION TRACK L_(I|O)?   (B-mode is the null)")
print("="*70)
print(f"{'comparison':<26}{'r':>9}{'z vs shift-null':>18}")
for nm, fld in [('emission vs kappa_E', E['kappa']), ('emission vs kappa_B', B['kappa']),
                ('emission vs psi_E',   E['psi']),   ('emission vs psi_B',   B['psi']),
                ('emission vs |alpha|_E', aE),       ('emission vs |alpha|_B', aB)]:
    r  = pear(emis, fld)
    nl = shift_null(emis, fld)
    print(f"{nm:<26}{r:>9.4f}{(r-nl.mean())/nl.std():>18.2f}")

print("\n" + "="*70)
print("READING")
print("="*70)
print("  If E and B give the SAME answer, the structure is not lensing signal.")
print("  psi_E/psi_B ~ 1 would mean the smooth gradient in the slingshot map's")
print("  middle panel is integrated noise, not the Fermat potential.")
