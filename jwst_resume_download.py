#!/usr/bin/env python3
"""
JWST Program 4598 — Resumable Mosaic Download
Bullet Cluster 1E 0657-558

Survives power loss: tracks completed files in jwst_download_state.json
Resume by re-running — already-complete files are skipped.

Usage:
    python3 jwst_resume_download.py
    nohup python3 jwst_resume_download.py > jwst_download.log 2>&1 &

Requirements:
    pip install astroquery requests tqdm
"""

import json
import os
import sys
import time
import hashlib
import requests
from pathlib import Path
from datetime import datetime

# ── Target ────────────────────────────────────────────────────────────────────
PROGRAM_ID = 4598
TARGET_RA  = 104.6098
TARGET_DEC = -55.9446
SEARCH_RADIUS_ARCMIN = 4.0

BASE_DIR   = Path(__file__).parent / "optical" / "jwst" / str(PROGRAM_ID)
STATE_FILE = Path(__file__).parent / "jwst_download_state.json"
LOG_FILE   = Path(__file__).parent / "jwst_download.log"

# Filters in priority order (science-critical first)
PRIORITY_FILTERS = [
    "F277W",   # weak lensing shear — most critical
    "F444W",   # already partial
    "F115W", "F150W", "F200W",
    "F356W", "F410M", "F606W", "F814W",
    "F090W", "F140M", "F162M", "F182M", "F210M",
]

MAST_API = "https://mast.stsci.edu/api/v0.1"
MAST_DL  = "https://mast.stsci.edu/api/v0.1/Download/file"

# ── State management ──────────────────────────────────────────────────────────

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"completed": [], "failed": [], "started": str(datetime.now())}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# ── MAST query ────────────────────────────────────────────────────────────────

def query_mast_products():
    """Query MAST for all JWST products from program 4598 around Bullet Cluster."""
    log("Querying MAST for program 4598 products...")

    # Cone search
    params = {
        "ra": TARGET_RA,
        "dec": TARGET_DEC,
        "radius": SEARCH_RADIUS_ARCMIN / 60.0,
        "service": "Mast.Caom.Cone",
        "format": "json",
        "pagesize": 5000,
    }
    r = requests.post(f"{MAST_API}/invoke", data={"request": json.dumps({
        "service": "Mast.Caom.Cone",
        "format": "json",
        "params": params,
    })}, timeout=60)
    r.raise_for_status()
    obs = r.json().get("data", [])

    # Filter to JWST program 4598
    jwst_obs = [o for o in obs
                if str(o.get("proposal_id", "")) == str(PROGRAM_ID)
                and o.get("obs_collection", "") in ("JWST", "HST")]

    log(f"  Found {len(jwst_obs)} JWST observations")
    if not jwst_obs:
        log("  Falling back to direct product name list from prior session...")
        return _known_products()

    # Get product lists
    products = []
    obs_ids = [o["obsid"] for o in jwst_obs]
    r2 = requests.post(f"{MAST_API}/invoke", data={"request": json.dumps({
        "service": "Mast.Caom.Products",
        "format": "json",
        "params": {"obsid": ",".join(str(x) for x in obs_ids)},
    })}, timeout=120)
    r2.raise_for_status()
    all_prods = r2.json().get("data", [])

    # Want science (_drz, _cal, _i2d) FITS files, skip previews
    sci = [p for p in all_prods
           if p.get("type") == "S"
           and any(p.get("productFilename", "").endswith(ext)
                   for ext in ("_drz.fits", "_cal.fits", "_i2d.fits", ".fits"))
           and not p.get("productFilename", "").endswith("_thumb.jpg")]

    log(f"  {len(sci)} science products identified")
    return sci

def _known_products():
    """Fallback: products identified in prior session."""
    return [
        {"productFilename": f"jw0{PROGRAM_ID:04d}_F444W_mosaic_i2d.fits",
         "dataURI": f"mast:JWST/product/jw0{PROGRAM_ID:04d}_F444W_mosaic_i2d.fits",
         "size": 300_000_000},
    ]

# ── Download with resume ──────────────────────────────────────────────────────

def download_file(uri, dest_path, expected_size=None):
    """Download with byte-range resume. Returns True on success."""
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = dest_path.with_suffix(dest_path.suffix + ".part")

    resume_byte = tmp_path.stat().st_size if tmp_path.exists() else 0

    headers = {}
    if resume_byte > 0:
        headers["Range"] = f"bytes={resume_byte}-"
        log(f"  Resuming from {resume_byte/1e6:.1f} MB")

    url = f"{MAST_DL}?uri={uri}"
    try:
        r = requests.get(url, headers=headers, stream=True, timeout=300)
        if r.status_code == 416:
            # Range not satisfiable — file may already be complete
            if expected_size and tmp_path.stat().st_size >= expected_size:
                tmp_path.rename(dest_path)
                return True
            resume_byte = 0
            r = requests.get(url, stream=True, timeout=300)

        r.raise_for_status()
        total = int(r.headers.get("content-length", 0)) + resume_byte
        mode = "ab" if resume_byte > 0 else "wb"

        downloaded = resume_byte
        with open(tmp_path, mode) as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):  # 1 MB chunks
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    pct = downloaded / total * 100 if total else 0
                    print(f"\r    {downloaded/1e6:.1f} / {total/1e6:.1f} MB  ({pct:.1f}%)",
                          end="", flush=True)

        print()
        tmp_path.rename(dest_path)
        log(f"  ✓ Complete: {dest_path.name} ({downloaded/1e6:.1f} MB)")
        return True

    except Exception as e:
        log(f"  ✗ Error: {e}")
        return False

# ── Logging ───────────────────────────────────────────────────────────────────

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log("=" * 60)
    log("BulletCluster JWST Resume Download")
    log(f"Program: {PROGRAM_ID}  Target: RA={TARGET_RA} Dec={TARGET_DEC}")
    log("=" * 60)

    state = load_state()
    completed = set(state["completed"])
    failed = set(state["failed"])

    try:
        products = query_mast_products()
    except Exception as e:
        log(f"MAST query failed: {e}")
        log("Check network and try again.")
        sys.exit(1)

    if not products:
        log("No products found. Check program ID and coordinates.")
        sys.exit(1)

    # Sort by filter priority
    def filter_priority(p):
        fn = p.get("productFilename", "")
        for i, f in enumerate(PRIORITY_FILTERS):
            if f.lower() in fn.lower():
                return i
        return len(PRIORITY_FILTERS)

    products.sort(key=filter_priority)

    log(f"\nTotal products to download: {len(products)}")
    log(f"Already completed: {len(completed)}")
    log(f"Previously failed: {len(failed)}")
    log("")

    success_count = 0
    fail_count = 0

    for i, prod in enumerate(products):
        fname = prod.get("productFilename", f"product_{i}.fits")
        uri   = prod.get("dataURI", "")
        size  = prod.get("size", 0)

        if fname in completed:
            log(f"[{i+1}/{len(products)}] SKIP (done): {fname}")
            continue

        log(f"[{i+1}/{len(products)}] Downloading: {fname}  ({size/1e6:.0f} MB)")

        # Determine destination path
        filter_name = "unknown"
        for f in PRIORITY_FILTERS:
            if f.lower() in fname.lower():
                filter_name = f
                break

        dest = BASE_DIR / "mastDownload" / filter_name / fname

        ok = download_file(uri, dest, expected_size=size)

        if ok:
            completed.add(fname)
            if fname in failed:
                failed.discard(fname)
            success_count += 1
            state["completed"] = list(completed)
            state["failed"] = list(failed)
            save_state(state)
        else:
            failed.add(fname)
            fail_count += 1
            state["failed"] = list(failed)
            save_state(state)
            log(f"  Will retry on next run.")
            time.sleep(5)

    log("")
    log("=" * 60)
    log(f"Session complete: {success_count} downloaded, {fail_count} failed")
    log(f"State saved to: {STATE_FILE}")
    if fail_count > 0:
        log("Re-run this script to retry failed files.")
    log("=" * 60)

if __name__ == "__main__":
    main()
