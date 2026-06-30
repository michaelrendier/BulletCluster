"""
bullet_engine.py — Bullet Cluster σ-face Faraday Diagnostic Engine
Ainulindale / PtolemyHolcus

The engine measures. It does not fit. It does not renormalise.
The data either shows a Faraday screen at the DM mass peaks or it does not.

Usage:
    from bullet_engine import BulletEngine
    engine = BulletEngine()
    engine.run()              # full run
    engine.run(use_real=True) # swap in real MGCLS cubes once SARAO access granted

The σ-face hypothesis (Ainulindale):
    σ = ½ is the ZD boundary — the surface between stuff and no-stuff.
    If DM = ZD (zero divisor, no plasma): no Faraday screen at κ peaks.
    If DM = CD (stuff, plasma):            Faraday screen present, ΔRM > threshold.
    The threshold is set in constants.py BEFORE looking at the data.
"""

import os
import sys
import json
import numpy as np
from pathlib import Path

ENGINE_DIR = Path(__file__).parent
sys.path.insert(0, str(ENGINE_DIR / 'modules'))

from constants import (BASE, DM_NW, DM_SE, GAS_NW, GAS_SE,
                       RM_THRESHOLD_RADM2, D_STAR, SIGMA_HALF)
from synthetic  import generate_cubes, OUT_DIR as SYNTH_DIR
from transect   import (transect_endpoints, sample_points,
                        extract_profile_from_fits,
                        extract_rm_from_qu_cubes,
                        compute_diagnostic, print_diagnostic)

BASE_PATH = Path(BASE)


class BulletEngine:
    """
    Single-entry-point engine for the Bullet Cluster DM diagnostic.

    Data sources (all optional — engine degrades gracefully):
        Chandra X-ray   : xray_chandra.fits  (viewer layer, or full evt2)
        MeerKAT Q/U     : synthetic (default) or SARAO real cubes
        Planck SZ       : sz_planck.fits (after tgz extract)
        Lensing κ       : lensing_kappa.fits (NFW model or published)
    """

    def __init__(self, use_real_radio=False, transect_length_arcmin=10.0,
                 n_transect_points=200, output_dir=None):
        self.use_real_radio = use_real_radio
        self.transect_length = transect_length_arcmin
        self.n_points = n_transect_points
        self.output_dir = Path(output_dir or ENGINE_DIR / 'output')
        self.output_dir.mkdir(exist_ok=True)
        self.results = {}

    # ── Data paths ────────────────────────────────────────────────────────────

    @property
    def xray_path(self):
        return BASE_PATH / 'xray' / 'chandra' / 'merged_xray.fits'

    @property
    def kappa_path(self):
        return BASE_PATH / 'optical' / 'lensing' / 'kappa_model.fits'

    @property
    def sz_path(self):
        return BASE_PATH / 'mm_sz' / 'planck' / 'sz_ymap_cutout.fits'

    @property
    def radio_q_path(self):
        if self.use_real_radio:
            # SARAO MGCLS enhanced products — Stokes Q cube
            return BASE_PATH / 'radio' / 'meerkat' / 'MGCLS_1E0657-558_Q_cube.fits'
        return Path(SYNTH_DIR) / 'synthetic_Q_wave.fits'

    @property
    def radio_u_path(self):
        if self.use_real_radio:
            return BASE_PATH / 'radio' / 'meerkat' / 'MGCLS_1E0657-558_U_cube.fits'
        return Path(SYNTH_DIR) / 'synthetic_U_wave.fits'

    @property
    def radio_freq_path(self):
        if self.use_real_radio:
            return BASE_PATH / 'radio' / 'meerkat' / 'MGCLS_freqs.dat'
        return Path(SYNTH_DIR) / 'synthetic_freqs_wave.dat'

    # ── Setup ─────────────────────────────────────────────────────────────────

    def setup_synthetic(self, dm_model='wave'):
        """Generate synthetic Q/U cubes if not present."""
        synth_q = Path(SYNTH_DIR) / f'synthetic_Q_{dm_model}.fits'
        if not synth_q.exists():
            print(f"  Generating synthetic cubes (dm_model={dm_model}) ...")
            generate_cubes(dm_model=dm_model)

    def setup_transect(self):
        """Define the measurement transect across the DM band."""
        t = transect_endpoints(length_arcmin=self.transect_length)
        ra, dec, offset = sample_points(t, n_points=self.n_points)
        self.transect  = t
        self.ra_arr    = ra
        self.dec_arr   = dec
        self.offset    = offset   # arcmin from DM band midpoint
        print(f"  Transect: {self.transect_length:.1f}' perpendicular to merger axis")
        print(f"  Midpoint: RA={t['mid_ra']:.4f}  Dec={t['mid_dec']:.4f}")
        print(f"  PA: {t['pa_deg']:.1f}°  Points: {self.n_points}")

    # ── Measurements (each one raw, no modification) ──────────────────────────

    def measure_xray(self):
        """Chandra X-ray surface brightness along transect."""
        print("  [X-ray] Chandra ACIS-I 0.5–7 keV ...")
        # Try viewer-generated layer first, then full merged evt2
        for candidate in [
            ENGINE_DIR.parent / 'viewer' / 'layers' / 'xray_chandra.png',
            self.xray_path,
        ]:
            if candidate.exists():
                # For PNG: load as greyscale
                if str(candidate).endswith('.png'):
                    from PIL import Image
                    img = np.array(Image.open(candidate).convert('L')).astype(float)
                    # Project transect coordinates to PNG pixel space (800×800, 1"/px)
                    size, scale = 800, 1.0/3600
                    from constants import RA0, DEC0
                    px = size/2 - (self.ra_arr - RA0) / scale
                    py = size/2 + (self.dec_arr - DEC0) / scale
                    from transect import _interp2d
                    profile = _interp2d(img, px, py)
                    self.results['xray'] = profile
                    print(f"    Loaded from {candidate.name}")
                    return
                else:
                    profile = extract_profile_from_fits(str(candidate),
                                                         self.ra_arr, self.dec_arr)
                    if profile is not None:
                        self.results['xray'] = profile
                        return
        print("    X-ray: no data — run generate_layers.py first")
        self.results['xray'] = None

    def measure_kappa(self):
        """Gravitational lensing convergence κ along transect."""
        print("  [Lensing] κ map ...")
        # Use viewer PNG layer (NFW model)
        png = ENGINE_DIR.parent / 'viewer' / 'layers' / 'lensing_kappa.png'
        if png.exists():
            from PIL import Image
            img = np.array(Image.open(png).convert('L')).astype(float)
            size, scale = 800, 1.0/3600
            from constants import RA0, DEC0
            px = size/2 - (self.ra_arr - RA0) / scale
            py = size/2 + (self.dec_arr - DEC0) / scale
            from transect import _interp2d
            profile = _interp2d(img, px, py)
            self.results['kappa'] = profile
            print(f"    κ from NFW model (Clowe+2006 parameters)")
        else:
            self.results['kappa'] = None
            print("    κ: no data")

    def measure_rm(self):
        """RM synthesis along transect from Q/U cubes."""
        print("  [Radio] RM synthesis ...")
        if not self.radio_q_path.exists():
            if not self.use_real_radio:
                self.setup_synthetic()
            else:
                print("    Real MGCLS cubes not found — register at archive.sarao.ac.za")
                self.results['rm'] = None
                self.results['pi'] = None
                return

        rm, pi, evpa = extract_rm_from_qu_cubes(
            str(self.radio_q_path), str(self.radio_u_path),
            str(self.radio_freq_path),
            self.ra_arr, self.dec_arr,
        )
        self.results['rm']   = rm
        self.results['pi']   = pi
        self.results['evpa'] = evpa
        src = 'REAL MGCLS' if self.use_real_radio else 'SYNTHETIC (wave model)'
        print(f"    RM synthesis complete ({src})")

    def measure_sz(self):
        """Planck SZ Compton-y along transect."""
        print("  [SZ] Planck y-map ...")
        png = ENGINE_DIR.parent / 'viewer' / 'layers' / 'sz_planck.png'
        if png.exists() and png.stat().st_size > 5000:
            from PIL import Image
            img = np.array(Image.open(png).convert('L')).astype(float)
            size, scale = 800, 1.0/3600
            from constants import RA0, DEC0
            px = size/2 - (self.ra_arr - RA0) / scale
            py = size/2 + (self.dec_arr - DEC0) / scale
            from transect import _interp2d
            self.results['sz'] = _interp2d(img, px, py)
            print("    SZ from Planck MILCA y-map")
        else:
            self.results['sz'] = None
            print("    SZ: still downloading (11 GB tgz)")

    # ── Diagnostic ────────────────────────────────────────────────────────────

    def run_diagnostic(self):
        """The core measurement: does ΔRM exist at the DM κ peaks?"""
        print("\n  [Diagnostic] σ-face Faraday test ...")
        diagnostic = compute_diagnostic(
            rm_profile    = self.results.get('rm'),
            kappa_profile = self.results.get('kappa'),
            offset_arcmin = self.offset,
        )
        self.results['diagnostic'] = diagnostic
        print_diagnostic(diagnostic)
        return diagnostic

    # ── Save ──────────────────────────────────────────────────────────────────

    def save_results(self):
        """Save all profiles to numpy archive and JSON summary."""
        out_np = self.output_dir / 'transect_profiles.npz'
        save_dict = {'offset_arcmin': self.offset}
        for key, val in self.results.items():
            if isinstance(val, np.ndarray):
                save_dict[key] = val
        np.savez(out_np, **save_dict)

        # JSON summary (diagnostic verdict)
        diag = self.results.get('diagnostic', {})
        summary = {
            'verdict':           diag.get('verdict', 'NOT RUN'),
            'dm_model_favoured': diag.get('dm_model_favoured', 'unknown'),
            'max_abs_delta_rm':  diag.get('max_abs_delta_rm', None),
            'threshold_radm2':   RM_THRESHOLD_RADM2,
            'data_source':       'REAL MGCLS' if self.use_real_radio else 'SYNTHETIC',
            'transect_length_arcmin': self.transect_length,
            'n_points': self.n_points,
            'sigma_half': SIGMA_HALF,
            'd_star': D_STAR,
        }
        out_json = self.output_dir / 'diagnostic_summary.json'
        with open(out_json, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"  Saved: {out_np}")
        print(f"  Saved: {out_json}")

    # ── Full run ──────────────────────────────────────────────────────────────

    def run(self, use_real=None):
        """Run the complete diagnostic pipeline."""
        if use_real is not None:
            self.use_real_radio = use_real

        print("\n" + "═"*60)
        print("  BULLET CLUSTER DM DIAGNOSTIC ENGINE")
        print("  Ainulindale / PtolemyHolcus")
        print(f"  Radio source: {'REAL MGCLS' if self.use_real_radio else 'SYNTHETIC'}")
        print("═"*60)

        self.setup_transect()

        print("\n── Measurements ─────────────────────────────────────")
        self.measure_xray()
        self.measure_kappa()
        self.measure_rm()
        self.measure_sz()

        print("\n── Diagnostic ───────────────────────────────────────")
        self.run_diagnostic()
        self.save_results()

        print("\n── Complete ─────────────────────────────────────────")
        print(f"  Output: {self.output_dir}")
        print("  To swap in real MGCLS data: engine.run(use_real=True)")
        print("  SARAO archive: https://archive.sarao.ac.za/")
        print("  Proposal: SSV-20180624-FC-01\n")

        return self.results


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Bullet Cluster DM Diagnostic Engine')
    p.add_argument('--real', action='store_true',
                   help='Use real MGCLS data instead of synthetic')
    p.add_argument('--length', type=float, default=10.0,
                   help='Transect length in arcmin (default: 10)')
    p.add_argument('--points', type=int, default=200,
                   help='Number of transect sample points (default: 200)')
    args = p.parse_args()

    engine = BulletEngine(
        use_real_radio=args.real,
        transect_length_arcmin=args.length,
        n_transect_points=args.points,
    )
    engine.run()
