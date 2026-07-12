#!/usr/bin/env python3
"""
resume_hst.py — Resume HST Program 10200 download (Bullet Cluster, Jones Cycle13)
ACS/WFC F606W/F775W/F850LP lensing mosaics.
Deletes partial files (size < 95% of expected) and re-downloads.
"""

import sys, time
from pathlib import Path
from astroquery.mast import Observations

BASE    = Path(__file__).resolve().parent / "10200" / "mastDownload"
LOGFILE = Path(__file__).resolve().parent / "resume_hst.log"

def log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOGFILE, 'a') as f:
        f.write(line + '\n')

def find_existing(fname):
    hits = list(BASE.rglob(fname))
    if hits:
        p = hits[0]
        return p, p.stat().st_size
    return None, 0

def size_ok(actual, expected, tol=0.05):
    if expected <= 0:
        return actual > 0
    return abs(actual - expected) / expected < tol

log("=" * 60)
log("Querying MAST for HST Program 10200...")
obs = Observations.query_criteria(
    proposal_id="10200",
    obs_collection="HST",
    dataproduct_type="image",
)
log(f"Found {len(obs)} observations")

products = Observations.get_product_list(obs)
drz = products[
    (products['productType'] == 'SCIENCE') &
    ['_drz.fits' in str(fn) for fn in products['productFilename']]
]
log(f"Found {len(drz)} drizzled science products")

complete, to_get = [], []
for row in drz:
    fname    = str(row['productFilename'])
    expected = int(row['size'])
    path, actual = find_existing(fname)

    if path is None:
        log(f"  MISSING  {fname}  ({expected/1e6:.0f} MB)")
        to_get.append(row)
    elif size_ok(actual, expected):
        log(f"  COMPLETE {fname}  ({actual/1e6:.0f}/{expected/1e6:.0f} MB)")
        complete.append(fname)
    else:
        log(f"  PARTIAL  {fname}  ({actual/1e6:.0f}/{expected/1e6:.0f} MB) — deleting")
        path.unlink()
        to_get.append(row)

log(f"\nComplete: {len(complete)}  |  To download: {len(to_get)}")
if not to_get:
    log("All HST drz files complete.")
    sys.exit(0)

total_gb = sum(int(r['size']) for r in to_get) / 1e9
log(f"Total to download: {total_gb:.2f} GB\n")

import numpy as np
fnames_needed = {str(r['productFilename']) for r in to_get}
mask = np.array([str(fn) in fnames_needed for fn in products['productFilename']])
to_dl = products[mask]

for i, row in enumerate(to_get):
    fname    = str(row['productFilename'])
    expected = int(row['size'])
    log(f"[{i+1}/{len(to_get)}] Starting: {fname}  ({expected/1e6:.0f} MB)")
    t0 = time.time()
    try:
        filt = products[products['productFilename'] == row['productFilename']]
        manifest = Observations.download_products(
            filt,
            download_dir=str(BASE.parent),
            flat=False,
        )
        elapsed = time.time() - t0
        if len(manifest):
            status = manifest['Status'][0]
            local  = manifest['Local Path'][0]
            if status == 'COMPLETE' and Path(local).exists():
                got = Path(local).stat().st_size
                ok  = size_ok(got, expected)
                tag = "OK" if ok else "SIZE MISMATCH"
                log(f"[{i+1}/{len(to_get)}] {tag}  {fname}  ({got/1e6:.0f}/{expected/1e6:.0f} MB  in {elapsed:.0f}s)")
            else:
                log(f"[{i+1}/{len(to_get)}] {status}  {elapsed:.0f}s")
        else:
            log(f"[{i+1}/{len(to_get)}] No manifest returned")
    except Exception as e:
        log(f"[{i+1}/{len(to_get)}] ERROR: {e}")

log("\nHST download complete.")
