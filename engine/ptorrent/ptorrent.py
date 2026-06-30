#!/usr/bin/env python3
"""
ptorrent.py — Bullet Cluster engine orchestrator.

PTorrent is the outermost harness. It sequences:
  1. Data acquisition (sarao_download.py)
  2. Layer generation (generate_layers.py in viewer/)
  3. Synthetic cube generation (modules/synthetic.py)
  4. Diagnostic run (bullet_engine.py)
  5. Results summary

Each stage is guarded — it checks what exists before running.
The engine produces the same result regardless of the order stages complete.
"""

import sys, os, json, subprocess, time
from pathlib import Path

ROOT    = Path('/media/rendier/0123-4567/bullet_cluster')
ENGINE  = ROOT / 'engine'
MODULES = ENGINE / 'modules'
OUTPUT  = ENGINE / 'output'
RADIO   = ROOT / 'radio/meerkat'
MGCLS   = RADIO / 'MGCLS_DR1'
SYNTH   = RADIO / 'synthetic'
VIEWER  = ROOT / 'viewer'

sys.path.insert(0, str(MODULES))

OUTPUT.mkdir(parents=True, exist_ok=True)


def stage_header(name):
    print(f'\n{"═"*60}')
    print(f'  {name}')
    print(f'{"═"*60}')


def stage_1_data():
    """Report data availability. Download public MGCLS data if missing."""
    stage_header('STAGE 1 — Data inventory')

    mgcls_fcube = MGCLS / 'enhanced/frequency_cubes/Bullet_aFix_pol_I_15arcsec_fcube_cor.fits.gz'
    mgcls_5pln  = MGCLS / 'enhanced/5pln_cubes/Bullet_aFix_pol_I_15arcsec_5pln_cor.fits.gz'
    real_q      = RADIO / 'MGCLS_1E0657-558_Q_cube.fits'
    real_u      = RADIO / 'MGCLS_1E0657-558_U_cube.fits'

    data_sources = {
        'MGCLS Stokes I fcube (15")': mgcls_fcube,
        'MGCLS Stokes I 5pln  (15")': mgcls_5pln,
        'MGCLS Stokes Q cube  (real)': real_q,
        'MGCLS Stokes U cube  (real)': real_u,
        'Chandra X-ray layer':         VIEWER / 'layers/xray_chandra.png',
        'Lensing κ layer':             VIEWER / 'layers/lensing_kappa.png',
        'Planck SZ layer':             VIEWER / 'layers/sz_planck.png',
    }

    all_present = True
    for label, path in data_sources.items():
        exists = Path(path).exists()
        sz = f'({Path(path).stat().st_size/1e6:.0f} MB)' if exists else ''
        status = '✓' if exists else '✗ MISSING'
        print(f'  {status}  {label} {sz}')
        if not exists:
            all_present = False

    if not mgcls_fcube.exists():
        print('\n  Downloading public MGCLS data...')
        dl_script = Path(__file__).parent / 'sarao_download.py'
        subprocess.run([sys.executable, str(dl_script), '--path', 'a'], check=False)

    if not real_q.exists():
        print('\n  NOTE: Stokes Q/U cubes for RM synthesis are not yet available.')
        print('        MGCLS DR1 does not include Q/U for the Bullet Cluster.')
        print('        New 2024/2025 S-band+UHF data is on tape at SARAO.')
        print('        To request staging:')
        print('          1. Register at ilifu.ac.za for IDIA allocation')
        print('          2. Email helpdesk@sarao.ac.za for Bullet Cluster data access')
        print('          3. Run: python3 sarao_download.py --path b')
        print()
        print('        Engine will proceed with synthetic cubes.')

    return {'real_qu_available': real_q.exists() and real_u.exists()}


def stage_2_synthetic():
    """Generate synthetic Stokes Q/U cubes for both DM models."""
    stage_header('STAGE 2 — Synthetic cube generation')
    from synthetic import generate_cubes
    for model in ['wave', 'particle']:
        print(f'  Generating {model} DM synthetic cubes...')
        result = generate_cubes(dm_model=model, overwrite=False)
        print(f'    Q: {Path(result[1]).name}  U: {Path(result[2]).name}')
    print('  Synthetic cubes ready.')
    return True


def stage_3_diagnostic(use_real=False):
    """Run the Faraday RM diagnostic."""
    stage_header(f'STAGE 3 — RM Diagnostic (use_real={use_real})')
    sys.path.insert(0, str(ENGINE))
    from bullet_engine import BulletEngine
    engine = BulletEngine()
    result = engine.run(use_real=use_real)
    return result


def stage_4_summary(diagnostic_result):
    """Print the final verdict."""
    stage_header('STAGE 4 — Results')

    summary_file = OUTPUT / 'diagnostic_summary.json'
    if summary_file.exists():
        with open(summary_file) as f:
            summary = json.load(f)
    elif diagnostic_result:
        summary = diagnostic_result
    else:
        print('  No diagnostic result found. Run stages 1-3 first.')
        return

    print(f'  Verdict:           {summary.get("verdict")}')
    print(f'  DM model favoured: {summary.get("dm_model_favoured")}')
    print(f'  Max |ΔRM|:         {summary.get("max_abs_delta_rm")} rad/m²')
    print(f'  Threshold:         {summary.get("threshold_radm2")} rad/m²')
    print(f'  Data source:       {summary.get("data_source")}')

    verdict = summary.get('dm_model_favoured', 'unknown')
    if verdict == 'wave':
        print()
        print('  → DM halos are Faraday-transparent.')
        print('    Mass that bends light is a shape, not a substance.')
        print('    Consistent with ZD boundary at σ = ½.')
    elif verdict == 'particle':
        print()
        print('  → Faraday screen detected at DM κ peaks.')
        print('    DM carries charged particles / B-field.')
        print('    Halos are above σ = ½ (CD, not ZD boundary).')


def main():
    print('\n╔══════════════════════════════════════════════════════════╗')
    print('║  Bullet Cluster σ-face Faraday Engine  (PTorrent)       ║')
    print('║  Ainulindale / PtolemyHolcus                             ║')
    print('╚══════════════════════════════════════════════════════════╝')

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--real', action='store_true',
                        help='Use real SARAO Q/U cubes if available')
    parser.add_argument('--stage', type=int, default=0,
                        help='Run only stage N (1=data, 2=synthetic, 3=diagnostic, 4=summary)')
    args = parser.parse_args()

    if args.stage in (0, 1):
        data_info = stage_1_data()
        use_real = args.real and data_info.get('real_qu_available', False)
    else:
        use_real = args.real

    if args.stage in (0, 2):
        stage_2_synthetic()

    result = None
    if args.stage in (0, 3):
        result = stage_3_diagnostic(use_real=use_real)

    if args.stage in (0, 4):
        stage_4_summary(result)

    print('\nPTorrent complete.\n')


if __name__ == '__main__':
    main()
