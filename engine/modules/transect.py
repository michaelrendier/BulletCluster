"""
transect.py — Extract measurement vectors perpendicular to the merger axis.

The transect crosses the DM band center (midpoint between DM_NW and DM_SE).
All measurements are raw extractions — no fitting, no renormalization.
"""

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from constants import (RA0, DEC0, DM_NW, DM_SE, GAS_NW, GAS_SE,
                       MERGER_PA_DEG, MPC_PER_ARCMIN,
                       RM_THRESHOLD_RADM2, RM_RATIO_THRESHOLD)


# ── Geometry ──────────────────────────────────────────────────────────────────

def midpoint():
    """Midpoint between the two DM halo centres (the DM band crossing point)."""
    return dict(
        ra  = (DM_NW['ra']  + DM_SE['ra'])  / 2,
        dec = (DM_NW['dec'] + DM_SE['dec']) / 2,
    )


def transect_endpoints(length_arcmin=10.0, pa_deg=None):
    """
    Start and end (RA, Dec) for a transect of given length,
    perpendicular to the merger axis (default), centred on the DM band midpoint.

    pa_deg: position angle (deg E of N) of the transect direction.
            Default = merger_PA + 90° (perpendicular to merger).
    Returns dict with keys: ra_start, dec_start, ra_end, dec_end, n_points
    """
    if pa_deg is None:
        pa_deg = MERGER_PA_DEG          # along merger axis: shows DM_NW, GAS_NW, GAS_SE, DM_SE

    mid = midpoint()
    pa_rad = np.deg2rad(pa_deg)
    # Standard astronomical PA convention: 0=North, 90=East, 180=South, 270=West.
    # RA increases Westward, so East = -RA. Hence d_ra = -sin(PA)*half/cos(Dec).
    half = length_arcmin / 60.0   # degrees
    d_dec = half *  np.cos(pa_rad)
    d_ra  = half * -np.sin(pa_rad) / np.cos(np.deg2rad(mid['dec']))

    return dict(
        ra_start  = mid['ra']  - d_ra,
        dec_start = mid['dec'] - d_dec,
        ra_end    = mid['ra']  + d_ra,
        dec_end   = mid['dec'] + d_dec,
        pa_deg    = pa_deg,
        length_arcmin = length_arcmin,
        mid_ra    = mid['ra'],
        mid_dec   = mid['dec'],
    )


def sample_points(t, n_points=200):
    """
    Generate n_points (RA, Dec) along the transect t.
    Also returns offset in arcmin from midpoint (signed, +ve toward SE).
    """
    ra  = np.linspace(t['ra_start'],  t['ra_end'],  n_points)
    dec = np.linspace(t['dec_start'], t['dec_end'], n_points)
    # Offset from midpoint in arcmin
    dr   = (ra  - t['mid_ra'])  * np.cos(np.deg2rad(t['mid_dec'])) * 60
    dd   = (dec - t['mid_dec']) * 60
    offset = np.sqrt(dr**2 + dd**2) * np.sign(dr + dd)
    return ra, dec, offset


# ── Extractor: any 2D FITS map ────────────────────────────────────────────────

def extract_profile_from_fits(fits_path, ra_arr, dec_arr, hdu_idx=0):
    """
    Bilinear interpolation of a 2D FITS image along the transect.
    Returns 1D array of values, same length as ra_arr.
    Returns None if file missing or unreadable.
    """
    if not os.path.exists(fits_path):
        return None
    try:
        with fits.open(fits_path) as h:
            data = h[hdu_idx].data.squeeze()
            hdr  = h[hdu_idx].header
        if data.ndim != 2:
            return None
        wcs = WCS(hdr, naxis=2)
        px, py = wcs.all_world2pix(ra_arr, dec_arr, 0)
        return _interp2d(data, px, py)
    except Exception as e:
        print(f"  extract_profile: {fits_path}: {e}")
        return None


def _interp2d(arr, px, py):
    """Bilinear interpolation at sub-pixel positions px, py."""
    ny, nx = arr.shape
    x0 = np.floor(px).astype(int)
    y0 = np.floor(py).astype(int)
    fx = px - x0; fy = py - y0
    x1 = x0 + 1; y1 = y0 + 1
    x0 = np.clip(x0, 0, nx-1); x1 = np.clip(x1, 0, nx-1)
    y0 = np.clip(y0, 0, ny-1); y1 = np.clip(y1, 0, ny-1)
    v  = (arr[y0, x0] * (1-fx) * (1-fy)
        + arr[y0, x1] *    fx  * (1-fy)
        + arr[y1, x0] * (1-fx) *    fy
        + arr[y1, x1] *    fx  *    fy)
    return np.where(np.isfinite(v), v, np.nan)


# ── RM synthesis profile ──────────────────────────────────────────────────────

def extract_rm_profile(rm_fits_path, ra_arr, dec_arr):
    """Extract RM (Faraday depth peak) along transect from rmsynth3d output."""
    return extract_profile_from_fits(rm_fits_path, ra_arr, dec_arr)


def extract_rm_from_qu_cubes(q_fits, u_fits, freq_dat, ra_arr, dec_arr,
                              phi_range=(-300, 300), dphi=1.0):
    """
    Run 1D RM synthesis at each transect point using the Q/U cubes.
    Returns: rm_peak (rad/m²), pi_peak (polarised intensity), evpa_peak (deg).
    All raw — no background subtraction.
    """
    try:
        from RMtools_1D import do_RMsynth_1D
    except ImportError:
        print("  RM-Tools not installed: pip install RM-Tools")
        return None, None, None

    # Load cubes
    with fits.open(q_fits) as h:
        Q_cube = h[0].data.astype(float)
    with fits.open(u_fits) as h:
        U_cube = h[0].data.astype(float)
    freqs = np.loadtxt(freq_dat)
    lambda2 = (2.998e8 / freqs) ** 2

    # Get pixel coords for transect
    with fits.open(q_fits) as h:
        wcs = WCS(h[0].header, naxis=2)
    px, py = wcs.all_world2pix(ra_arr, dec_arr, 0)
    px_i = np.round(px).astype(int)
    py_i = np.round(py).astype(int)

    ny, nx = Q_cube.shape[1], Q_cube.shape[2]
    valid = (px_i >= 0) & (px_i < nx) & (py_i >= 0) & (py_i < ny)

    phi_arr = np.arange(phi_range[0], phi_range[1]+dphi, dphi)
    rm_peak  = np.full(len(ra_arr), np.nan)
    pi_peak  = np.full(len(ra_arr), np.nan)
    evpa_peak = np.full(len(ra_arr), np.nan)

    for i, (xi, yi) in enumerate(zip(px_i, py_i)):
        if not valid[i]: continue
        Q_spec = Q_cube[:, yi, xi]
        U_spec = U_cube[:, yi, xi]
        if not np.any(np.isfinite(Q_spec)): continue

        # RM synthesis: F(φ) = ∫ P(λ²) e^{-2iφλ²} dλ²
        P = Q_spec + 1j * U_spec
        FDF = np.array([np.nansum(P * np.exp(-2j * phi * lambda2))
                         for phi in phi_arr])
        FDF /= np.sum(np.isfinite(Q_spec))   # normalise by valid channels only

        peak_idx = np.argmax(np.abs(FDF))
        rm_peak[i]   = phi_arr[peak_idx]
        pi_peak[i]   = np.abs(FDF[peak_idx])
        evpa_peak[i] = np.rad2deg(0.5 * np.angle(FDF[peak_idx]))

    return rm_peak, pi_peak, evpa_peak


# ── Diagnostic ────────────────────────────────────────────────────────────────

def compute_diagnostic(rm_profile, kappa_profile, offset_arcmin,
                        dm_nw_offset=None, dm_se_offset=None):
    """
    The core measurement: RM ratio at known DM positions vs nearest gas peak.

    Physical logic:
        The DM positions (from weak lensing) are separated from the gas peaks
        (from X-ray). In the wave model, the ICM gas RM falls off from its peak
        toward the DM position → |RM(DM)| < |RM(gas_peak)| → ratio < 1.
        In the particle model, the DM plasma adds a Faraday screen at the DM
        position, boosting |RM(DM)| to match or exceed the gas peak → ratio ≥ 1.

    Returns a dict with the raw measurements — NO normalisation beyond the ratio.
    This is what goes in notebook 05_diagnostic.ipynb.
    """
    result = dict(rm_profile=rm_profile, kappa_profile=kappa_profile,
                  offset_arcmin=offset_arcmin)

    if rm_profile is None:
        result['verdict'] = 'NO DATA'
        return result

    # Project known DM and gas positions onto the transect (arcmin from midpoint)
    T_mid_ra  = (DM_NW['ra']  + DM_SE['ra'])  / 2
    T_mid_dec = (DM_NW['dec'] + DM_SE['dec']) / 2

    try:
        from constants import MERGER_PA_DEG as _PA
    except Exception:
        _PA = 135.0

    def _proj(obj_ra, obj_dec):
        """
        Signed offset of (obj_ra, obj_dec) along the transect (arcmin).
        Sign convention matches sample_points: NW = positive, SE = negative
        (opposite of the PA direction, because sample_points uses sign(dr+dd)
        where dr,dd are both positive in the NW direction for PA=135°).
        """
        pa_rad = np.deg2rad(_PA)
        dra    = (obj_ra  - T_mid_ra)  * np.cos(np.deg2rad(T_mid_dec))
        ddec   = obj_dec - T_mid_dec
        return (dra * np.sin(pa_rad) - ddec * np.cos(pa_rad)) * 60

    dm_nw_off  = dm_nw_offset if dm_nw_offset is not None else _proj(DM_NW['ra'],  DM_NW['dec'])
    dm_se_off  = dm_se_offset if dm_se_offset is not None else _proj(DM_SE['ra'],  DM_SE['dec'])
    gas_nw_off = _proj(GAS_NW['ra'], GAS_NW['dec'])
    gas_se_off = _proj(GAS_SE['ra'], GAS_SE['dec'])

    result['dm_nw_offset']  = dm_nw_off
    result['dm_se_offset']  = dm_se_off
    result['gas_nw_offset'] = gas_nw_off
    result['gas_se_offset'] = gas_se_off

    # Also record kappa peak offsets (for visualisation)
    if kappa_profile is not None:
        smoothed_kappa = np.where(np.isfinite(kappa_profile), kappa_profile, 0)
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(smoothed_kappa, distance=10, prominence=0.01)
        result['kappa_peak_offsets'] = offset_arcmin[peaks] if len(peaks) > 0 else []
        result['kappa_peak_values']  = kappa_profile[peaks]  if len(peaks) > 0 else []

    def _sample(off):
        """Interpolate the RM profile at a given offset (arcmin).
        Sorts offset_arcmin first because np.interp requires increasing xp."""
        idx = np.argsort(offset_arcmin)
        return float(np.interp(off, offset_arcmin[idx], rm_profile[idx],
                               left=np.nan, right=np.nan))

    WINDOW = 0.6   # arcmin half-width for local median around DM positions

    def _local_median(ref_off):
        mask = np.abs(offset_arcmin - ref_off) <= WINDOW
        if mask.sum() < 3:
            return _sample(ref_off)
        return float(np.nanmedian(rm_profile[mask]))

    # DM positions: use window median (noise-robust, DM screen is extended ~1.5')
    # Gas positions: use exact interpolated value at the gas peak (avoids
    #                dragging down the peak by including lower-RM center-side positions)
    rm_dm_nw  = _local_median(dm_nw_off)
    rm_dm_se  = _local_median(dm_se_off)
    rm_gas_nw = _sample(gas_nw_off)
    rm_gas_se = _sample(gas_se_off)

    result['rm_at_dm_nw']  = rm_dm_nw
    result['rm_at_dm_se']  = rm_dm_se
    result['rm_at_gas_nw'] = rm_gas_nw
    result['rm_at_gas_se'] = rm_gas_se

    # Ratio test (signed: preserves directional information)
    # ratio ≥ RM_RATIO_THRESHOLD means the DM position has RM matching the gas peak
    # → consistent with a Faraday screen at the DM position
    EPS = 1.0   # rad/m² noise floor below which ratio is undefined
    ratio_nw = rm_dm_nw / rm_gas_nw if abs(rm_gas_nw) > EPS else np.nan
    ratio_se = rm_dm_se / rm_gas_se if abs(rm_gas_se) > EPS else np.nan

    ratios = [r for r in [ratio_nw, ratio_se] if np.isfinite(r)]
    if not ratios:
        result['verdict'] = 'INSUFFICIENT DATA'
        return result

    max_ratio = max(ratios)
    result['ratio_nw']  = ratio_nw
    result['ratio_se']  = ratio_se
    result['max_ratio'] = max_ratio
    result['threshold'] = RM_RATIO_THRESHOLD

    if max_ratio >= RM_RATIO_THRESHOLD:
        result['verdict'] = 'FARADAY SCREEN DETECTED — consistent with PARTICLE DM'
        result['dm_model_favoured'] = 'particle'
    else:
        result['verdict'] = 'NO FARADAY SCREEN — consistent with WAVE/INTERFERENCE DM'
        result['dm_model_favoured'] = 'wave'

    return result


def print_diagnostic(result):
    """Print the diagnostic result clearly."""
    print("\n" + "="*60)
    print("  BULLET CLUSTER DM DIAGNOSTIC RESULT")
    print("="*60)
    print(f"  Verdict: {result.get('verdict','—')}")
    print(f"  Threshold: RM(DM)/RM(gas) ≥ {RM_RATIO_THRESHOLD}")
    if 'max_ratio' in result:
        print(f"  Max ratio: {result['max_ratio']:.3f}")
    for label, dm_key, gas_key, ratio_key, off_key in [
        ('NW', 'rm_at_dm_nw', 'rm_at_gas_nw', 'ratio_nw', 'dm_nw_offset'),
        ('SE', 'rm_at_dm_se', 'rm_at_gas_se', 'ratio_se', 'dm_se_offset'),
    ]:
        if dm_key in result:
            print(f"  DM_{label} at {result.get(off_key, '?'):+.2f}':  "
                  f"RM(DM)={result[dm_key]:.1f}  "
                  f"RM(gas)={result[gas_key]:.1f}  "
                  f"ratio={result.get(ratio_key, float('nan')):.3f}")
    if 'kappa_peak_offsets' in result:
        print(f"  κ peaks at: {result['kappa_peak_offsets']}")
    print("="*60 + "\n")
