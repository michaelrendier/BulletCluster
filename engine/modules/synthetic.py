"""
synthetic.py — Synthetic MeerKAT Stokes Q/U cubes for engine development.

Generates a physically motivated (but clearly synthetic) set of FITS cubes:
  - Stokes I  : total intensity  (synchrotron halo + relic)
  - Stokes Q  : polarised cos(2*EVPA)
  - Stokes U  : polarised sin(2*EVPA)

across the MeerKAT L-band frequency range (900–1670 MHz, 800 channels).

The synthetic model has TWO VARIANTS selected by DM_MODEL parameter:
  'particle'    : ΔRM ≠ 0 at DM peaks  → Faraday screen present
  'wave'        : ΔRM = 0 at DM peaks  → smooth gradient only from gas

This allows blind testing of the diagnostic engine before real data arrives.
Real MGCLS cubes (SARAO archive, proposal SSV-20180624-FC-01) simply replace
these files in BASE/radio/meerkat/synthetic/ when available.
"""

import os
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
import sys
sys.path.insert(0, os.path.dirname(__file__))
from constants import (RA0, DEC0, DM_NW, DM_SE, GAS_NW, GAS_SE,
                       FREQ_MIN_HZ, FREQ_MAX_HZ, N_FREQ_CHAN,
                       LAMBDA2_MIN, LAMBDA2_MAX)

BASE     = '/media/rendier/0123-4567/bullet_cluster'
OUT_DIR  = os.path.join(BASE, 'radio', 'meerkat', 'synthetic')
SIZE_PIX = 256           # spatial: 256×256 at 4"/pixel → 17' field
SCALE_DEG = 4.0 / 3600  # 4 arcsec/pixel (MeerKAT ~8" beam, Nyquist)


def make_wcs():
    w = WCS(naxis=2)
    w.wcs.crpix = [SIZE_PIX/2 + 0.5, SIZE_PIX/2 + 0.5]
    w.wcs.cdelt = [-SCALE_DEG, SCALE_DEG]
    w.wcs.crval = [RA0, DEC0]
    w.wcs.ctype = ['RA---TAN', 'DEC--TAN']
    return w


def sky_grid(wcs):
    """Return (ra, dec) 2D arrays for the spatial grid."""
    iy, ix = np.indices((SIZE_PIX, SIZE_PIX))
    ra, dec = wcs.all_pix2world(ix.ravel(), iy.ravel(), 0)
    return ra.reshape(SIZE_PIX, SIZE_PIX), dec.reshape(SIZE_PIX, SIZE_PIX)


def synchrotron_intensity(ra, dec):
    """Stokes I template — radio halo + relic (frequency-independent spatial)."""
    I = np.zeros_like(ra)
    # Radio halo: centred on cluster, Gaussian σ ≈ 2'
    for cra, cdec, amp, sig_deg in [
        (RA0,    DEC0,    0.08, 2.5/60),   # halo
        (104.44, -55.97,  0.12, 1.0/60),   # relic
    ]:
        dr  = (ra - cra)  * np.cos(np.radians(cdec))
        dd  = dec - cdec
        r2  = dr**2 + dd**2
        I  += amp * np.exp(-r2 / (2 * sig_deg**2))
    return I  # Jy/beam (arbitrary units, not fitted)


def intrinsic_evpa(ra, dec):
    """
    Intrinsic electric vector position angle (radians) at each sky position.
    Merger-aligned base field + curvature near each DM halo.
    This is B-field perpendicular to the synchrotron emission → EVPA ⊥ B.
    Merger axis PA ≈ 135° → B parallel → EVPA ≈ 45°
    """
    pa_base = np.deg2rad(45.0)    # EVPA parallel to merger axis (=B perp)
    evpa = np.full_like(ra, pa_base)
    # Curvature: field lines bend around each gas peak
    for gas_ra, gas_dec, sign in [(GAS_NW['ra'], GAS_NW['dec'], +1),
                                   (GAS_SE['ra'], GAS_SE['dec'], -1)]:
        dr  = (ra - gas_ra) * np.cos(np.radians(gas_dec))
        dd  = dec - gas_dec
        r   = np.sqrt(dr**2 + dd**2) + 1e-6
        # Azimuthal curl: d(EVPA)/dθ ∝ 1/r, falls off with distance
        theta = np.arctan2(dd, dr)
        evpa += sign * 0.4 * np.exp(-r / (3/60)) * np.cos(theta)
    return evpa


def rm_model(ra, dec, dm_model='wave'):
    """
    Rotation measure at each sky position (rad/m²).

    dm_model='wave'     : DM contributes no Faraday rotation — smooth gas gradient only.
    dm_model='particle' : DM halos add a Faraday screen localized to their κ peaks.

    This is the key diagnostic. The engine measures this directly from Stokes Q/U.
    The synthetic model lets us verify the engine recovers the correct answer.
    """
    rm = np.zeros_like(ra)

    # Gas contribution: peaks at X-ray gas centroids, sign reversal across merger axis
    for gas_ra, gas_dec, sign, amp in [
        (GAS_NW['ra'], GAS_NW['dec'], +1, 110.0),
        (GAS_SE['ra'], GAS_SE['dec'], -1,  70.0),
    ]:
        dr  = (ra - gas_ra)  * np.cos(np.radians(gas_dec))
        dd  = dec - gas_dec
        r   = np.sqrt(dr**2 + dd**2)
        rm += sign * amp * np.exp(-r / (2.5/60))

    # Background gradient along merger axis
    rm += 12 * ((ra - RA0) / np.cos(np.radians(DEC0))) / (10/60)

    if dm_model == 'particle':
        # DM halos add Faraday screen — localized to κ peaks.
        # Scale = projected NFW scale radius: r_s = r200/c ≈ 0.68'; projected
        # line-of-sight integral compresses this to ~r_s/2 ≈ 0.35' (NFW projected
        # profile narrows relative to 3D because outer shells contribute less
        # per unit area). Using 0.4' to be slightly conservative.
        # 1.5' was blatantly wrong (3.75× the projected scale).
        for dm_ra, dm_dec, sign, amp in [
            (DM_NW['ra'], DM_NW['dec'], +1, 18.0),
            (DM_SE['ra'], DM_SE['dec'], -1, 12.0),
        ]:
            dr  = (ra - dm_ra)  * np.cos(np.radians(dm_dec))
            dd  = dec - dm_dec
            r   = np.sqrt(dr**2 + dd**2)
            rm += sign * amp * np.exp(-r / (0.4/60))

    # ICM turbulent RM at beam scale (~15"): σ ≈ 2 rad/m².
    # Each pixel IS one beam measurement (4"/px Nyquist, 15" beam).
    # 8 rad/m² is the sub-beam pre-averaging value; after sqrt(beam_area/px_area)
    # ≈ sqrt(11) beam-averaging, that collapses to ~2.4 rad/m² per pixel.
    rng = np.random.default_rng(seed=42)    # fixed seed for reproducibility
    rm += rng.normal(0, 2.0, rm.shape)

    return rm


def polarised_fraction(ra, dec):
    """
    Polarised fraction p at each sky position.
    Relic: high (~35%).  Halo: moderate (~10–15%).  Background: low.
    """
    p = np.zeros_like(ra)
    for cra, cdec, amp, sig in [
        (104.44, -55.97, 0.35, 1.0/60),
        (RA0,    DEC0,   0.12, 2.5/60),
    ]:
        dr  = (ra - cra) * np.cos(np.radians(cdec))
        dd  = dec - cdec
        r2  = dr**2 + dd**2
        p  += amp * np.exp(-r2 / (2 * sig**2))
    return np.clip(p, 0, 0.5)


def generate_cubes(dm_model='wave', overwrite=False):
    """
    Generate synthetic I/Q/U FITS cubes (no frequency axis — per channel).
    Output files:
        synthetic_I.fits   — Stokes I cube (Nfreq, Ny, Nx)
        synthetic_Q.fits   — Stokes Q cube
        synthetic_U.fits   — Stokes U cube
        synthetic_freqs.dat — frequency list (Hz), one per line
        synthetic_meta.txt  — provenance note
    """
    os.makedirs(OUT_DIR, exist_ok=True)
    tag = f'_{dm_model}'

    i_path = os.path.join(OUT_DIR, f'synthetic_I{tag}.fits')
    q_path = os.path.join(OUT_DIR, f'synthetic_Q{tag}.fits')
    u_path = os.path.join(OUT_DIR, f'synthetic_U{tag}.fits')
    f_path = os.path.join(OUT_DIR, f'synthetic_freqs{tag}.dat')
    m_path = os.path.join(OUT_DIR, f'synthetic_meta{tag}.txt')

    if not overwrite and os.path.exists(i_path):
        print(f"  Synthetic cubes already exist: {OUT_DIR} (dm_model={dm_model})")
        return i_path, q_path, u_path, f_path

    print(f"  Generating synthetic cubes: dm_model='{dm_model}'")
    wcs   = make_wcs()
    ra, dec = sky_grid(wcs)

    freqs = np.linspace(FREQ_MIN_HZ, FREQ_MAX_HZ, N_FREQ_CHAN)
    c_light = 2.998e8   # m/s
    lambda2 = (c_light / freqs) ** 2   # m²

    I_cube = np.zeros((N_FREQ_CHAN, SIZE_PIX, SIZE_PIX), dtype=np.float32)
    Q_cube = np.zeros_like(I_cube)
    U_cube = np.zeros_like(I_cube)

    # Compute spatial templates (frequency-independent part)
    I_template  = synchrotron_intensity(ra, dec)
    p_template  = polarised_fraction(ra, dec)
    evpa0       = intrinsic_evpa(ra, dec)
    phi_map     = rm_model(ra, dec, dm_model=dm_model)   # rad/m²

    # Spectral index α = -0.7 (synchrotron: Sν ∝ ν^α)
    nu0 = (FREQ_MIN_HZ + FREQ_MAX_HZ) / 2
    for i, (nu, lam2) in enumerate(zip(freqs, lambda2)):
        spec = (nu / nu0) ** (-0.7)
        I_chan = I_template * spec
        # Faraday rotation: EVPA(λ²) = EVPA₀ + RM·λ²
        evpa_chan = evpa0 + phi_map * lam2
        p_chan    = p_template * spec
        Q_cube[i] = I_chan * p_chan * np.cos(2 * evpa_chan)
        U_cube[i] = I_chan * p_chan * np.sin(2 * evpa_chan)
        I_cube[i] = I_chan
        if i % 100 == 0:
            print(f"    channel {i}/{N_FREQ_CHAN}  ν={nu/1e6:.0f} MHz")

    # Build FITS header with WCS
    hdr = wcs.to_header()
    hdr['BUNIT']   = 'Jy/beam'
    hdr['DM_MODEL'] = dm_model
    hdr['NOTE']    = 'SYNTHETIC - replace with MGCLS SARAO data'
    hdr['ORIGIN']  = 'Ainulindale/PtolemyHolcus Bullet Cluster Engine'

    fits.writeto(i_path, I_cube, header=hdr, overwrite=True)
    fits.writeto(q_path, Q_cube, header=hdr, overwrite=True)
    fits.writeto(u_path, U_cube, header=hdr, overwrite=True)

    np.savetxt(f_path, freqs, fmt='%.6e', header='Frequency (Hz)')

    with open(m_path, 'w') as f:
        f.write(f"Synthetic MeerKAT L-band cubes\n")
        f.write(f"DM model: {dm_model}\n")
        f.write(f"Spatial: {SIZE_PIX}x{SIZE_PIX} pixels @ {SCALE_DEG*3600:.1f}\"/px\n")
        f.write(f"Frequency: {FREQ_MIN_HZ/1e6:.0f}–{FREQ_MAX_HZ/1e6:.0f} MHz, {N_FREQ_CHAN} channels\n")
        f.write(f"Replace with: SARAO archive proposal SSV-20180624-FC-01\n")
        f.write(f"Enhanced products: Stokes I/Q/U cubes, ~8\" resolution\n")

    print(f"  Done: {OUT_DIR}/synthetic_{{I,Q,U}}{tag}.fits")
    return i_path, q_path, u_path, f_path


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--model', choices=['wave','particle','both'], default='both')
    p.add_argument('--overwrite', action='store_true')
    args = p.parse_args()
    models = ['wave','particle'] if args.model == 'both' else [args.model]
    for m in models:
        generate_cubes(dm_model=m, overwrite=args.overwrite)
