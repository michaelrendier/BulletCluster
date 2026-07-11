#!/usr/bin/env python3
"""
download_mosaics.py — Download JWST Program 4598 mosaic i2d files.

Skips files that already exist AND whose on-disk size matches the MAST
catalog size within 1%. Removes and re-downloads partial files.
Logs verbosely to download_mosaics.log.
"""

import sys, time, os
from pathlib import Path
from astroquery.mast import Observations

BASE    = Path("/media/rendier/0123-4567/ThePlace/BulletCluster/optical/jwst/4598/mastDownload")
LOGFILE = Path("/media/rendier/0123-4567/ThePlace/BulletCluster/optical/jwst/download_mosaics.log")

def log(msg):
    ts   = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOGFILE, 'a') as f:
        f.write(line + '\n')

def find_existing(fname):
    """Return path + size if file exists anywhere under BASE, else None."""
    hits = list(BASE.rglob(fname))
    if hits:
        p = hits[0]
        return p, p.stat().st_size
    return None, 0

def size_ok(actual_bytes, expected_bytes, tol=0.01):
    """True if actual is within tol of expected."""
    if expected_bytes <= 0:
        return actual_bytes > 0
    return abs(actual_bytes - expected_bytes) / expected_bytes < tol

log("=" * 60)
log("Querying MAST for program 4598...")
obs = Observations.query_criteria(
    proposal_id="4598", obs_collection="JWST", dataproduct_type="image")
products = Observations.get_product_list(obs)

mosaics = products[
    (products['productType'] == 'SCIENCE') &
    ['nircam_clear' in str(fn) and str(fn).endswith('_i2d.fits')
     for fn in products['productFilename']]
]
log(f"Found {len(mosaics)} mosaic i2d files in MAST catalog")

# ── Audit existing files ───────────────────────────────────────────────────────
complete, partial, missing = [], [], []

for row in mosaics:
    fname    = str(row['productFilename'])
    expected = int(row['size'])
    path, actual = find_existing(fname)

    if path is None:
        missing.append(row)
        log(f"  MISSING  {fname}  ({expected/1e6:.0f} MB)")
    elif size_ok(actual, expected):
        complete.append(fname)
        log(f"  COMPLETE {fname}  ({actual/1e6:.0f} / {expected/1e6:.0f} MB)")
    else:
        partial.append(row)
        log(f"  PARTIAL  {fname}  ({actual/1e6:.0f} / {expected/1e6:.0f} MB) — will re-download")
        path.unlink()
        log(f"           deleted partial file")

to_get_rows = list(partial) + list(missing)
log(f"\nComplete: {len(complete)}  |  To download: {len(to_get_rows)}")

if not to_get_rows:
    log("All files complete. Nothing to do.")
    sys.exit(0)

# Build a filtered product table for download
import numpy as np
to_download_fnames = {str(r['productFilename']) for r in to_get_rows}
mask = np.array([str(fn) in to_download_fnames for fn in products['productFilename']])
to_dl = products[mask]
total_gb = sum(int(r['size']) for r in to_get_rows) / 1e9
log(f"Total to download: {total_gb:.2f} GB\n")

# ── Download one file at a time ────────────────────────────────────────────────
for i, row in enumerate(to_get_rows):
    fname    = str(row['productFilename'])
    expected = int(row['size'])
    log(f"[{i+1}/{len(to_get_rows)}] Starting: {fname}  ({expected/1e6:.0f} MB)")

    t0 = time.time()
    try:
        filt = products[products['productFilename'] == row['productFilename']]
        manifest = Observations.download_products(
            filt,
            download_dir=str(BASE.parent),
            flat=False,
        )
        elapsed = time.time() - t0
        status  = manifest['Status'][0] if len(manifest) else 'UNKNOWN'
        local   = manifest['Local Path'][0] if len(manifest) else '?'

        # Verify size
        if status == 'COMPLETE' and Path(local).exists():
            got = Path(local).stat().st_size
            if size_ok(got, expected):
                log(f"[{i+1}/{len(to_get_rows)}] OK  {fname}  ({got/1e6:.0f} MB  in {elapsed:.0f}s)")
            else:
                log(f"[{i+1}/{len(to_get_rows)}] SIZE MISMATCH  {fname}  got {got/1e6:.0f} MB expected {expected/1e6:.0f} MB")
        else:
            log(f"[{i+1}/{len(to_get_rows)}] {status}  {local}  ({elapsed:.0f}s)")

    except Exception as e:
        log(f"[{i+1}/{len(to_get_rows)}] ERROR: {e}")

log("\nAll downloads attempted.")
log("Run again to catch any failures.")

# ── Final audit ────────────────────────────────────────────────────────────────
log("\nFinal file audit:")
for row in mosaics:
    fname    = str(row['productFilename'])
    expected = int(row['size'])
    path, actual = find_existing(fname)
    status = "OK" if (path and size_ok(actual, expected)) else "MISSING/PARTIAL"
    log(f"  {status:8s}  {fname}  ({actual/1e6:.0f}/{expected/1e6:.0f} MB)")
