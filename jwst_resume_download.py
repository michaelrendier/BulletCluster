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
import requests
from pathlib import Path
from datetime import datetime

# ── Target ────────────────────────────────────────────────────────────────────
PROGRAM_ID        = 4598
TARGET_RA         = 104.6098
TARGET_DEC        = -55.9446
SEARCH_RADIUS_DEG = 0.07          # 4.2 arcmin

BASE_DIR   = Path(__file__).parent / "optical" / "jwst" / str(PROGRAM_ID) / "mastDownload"
STATE_FILE = Path(__file__).parent / "jwst_download_state.json"
LOG_FILE   = Path(__file__).parent / "jwst_download.log"

# Filters in priority order (science-critical first)
PRIORITY_FILTERS = [
    "F277W",   # weak lensing shear — most critical for polarization analysis
    "F444W",   # already partially downloaded
    "F115W", "F150W", "F200W",
    "F356W", "F410M",
    "F606W", "F814W",
    "F090W", "F140M", "F162M", "F182M", "F210M",
]

# ── State management ──────────────────────────────────────────────────────────

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"completed": [], "failed": [], "started": str(datetime.now())}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# ── MAST query via astroquery ─────────────────────────────────────────────────

def query_products():
    """Query MAST for JWST program 4598 around Bullet Cluster."""
    try:
        from astroquery.mast import Observations
        from astropy.coordinates import SkyCoord
        import astropy.units as u
        log("Using astroquery.mast...")
    except ImportError:
        log("ERROR: astroquery not installed. Run: pip install astroquery")
        sys.exit(1)

    coord = SkyCoord(ra=TARGET_RA, dec=TARGET_DEC, unit="deg")
    log(f"Querying MAST: Program {PROGRAM_ID}, radius={SEARCH_RADIUS_DEG*60:.1f} arcmin")

    obs = Observations.query_criteria(
        coordinates=coord,
        radius=SEARCH_RADIUS_DEG * u.deg,
        obs_collection="JWST",
        proposal_id=str(PROGRAM_ID),
    )
    log(f"  Found {len(obs)} observations")

    if len(obs) == 0:
        log("  No observations found — check program ID and coordinates")
        return []

    products = Observations.get_product_list(obs)
    log(f"  {len(products)} total products")

    # Science products only — calibrated or mosaic FITS
    mask = (
        (products["type"] == "S") &
        (products["dataproduct_type"].astype(str) != "preview") &
        [fname.endswith((".fits", "_drz.fits", "_cal.fits", "_i2d.fits"))
         for fname in products["productFilename"].astype(str)]
    )
    sci = products[mask]
    log(f"  {len(sci)} science products after filtering")
    return sci

# ── Download with byte-range resume ──────────────────────────────────────────

def download_file(uri, dest_path, expected_size=0):
    """Resumable download. Returns True on success."""
    from astroquery.mast import Observations

    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = dest_path.with_suffix(dest_path.suffix + ".part")

    # If destination already exists and size matches, skip
    if dest_path.exists():
        if expected_size == 0 or dest_path.stat().st_size >= expected_size * 0.99:
            log(f"  ✓ Already complete: {dest_path.name}")
            return True

    resume_byte = tmp_path.stat().st_size if tmp_path.exists() else 0

    try:
        # Get the direct download URL from astroquery
        url = f"https://mast.stsci.edu/api/v0.1/Download/file?uri={uri}"
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"}
        if resume_byte > 0:
            headers["Range"] = f"bytes={resume_byte}-"
            log(f"  Resuming {dest_path.name} from {resume_byte/1e6:.1f} MB")
        else:
            log(f"  Starting {dest_path.name}")

        r = requests.get(url, headers=headers, stream=True, timeout=300)

        if r.status_code == 416:
            # Already complete
            if tmp_path.exists():
                tmp_path.rename(dest_path)
            return True

        r.raise_for_status()
        total = int(r.headers.get("content-length", 0)) + resume_byte
        mode = "ab" if resume_byte > 0 else "wb"
        downloaded = resume_byte

        with open(tmp_path, mode) as f:
            for chunk in r.iter_content(chunk_size=2 * 1024 * 1024):  # 2 MB chunks
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    pct = downloaded / total * 100 if total else 0
                    print(f"\r    {downloaded/1e6:.0f} / {total/1e6:.0f} MB  ({pct:.1f}%)",
                          end="", flush=True)

        print()
        tmp_path.rename(dest_path)
        log(f"  ✓ {dest_path.name}  ({downloaded/1e6:.0f} MB)")
        return True

    except KeyboardInterrupt:
        log(f"\n  Interrupted — partial file saved to {tmp_path}")
        raise
    except Exception as e:
        log(f"  ✗ Error downloading {dest_path.name}: {e}")
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
    log(f"Program: {PROGRAM_ID}  RA={TARGET_RA} Dec={TARGET_DEC}")
    log("=" * 60)

    state = load_state()
    completed = set(state.get("completed", []))
    failed    = set(state.get("failed", []))

    try:
        products = query_products()
    except Exception as e:
        log(f"Query failed: {e}")
        sys.exit(1)

    if not len(products):
        log("No products returned.")
        sys.exit(1)

    # Sort by filter priority
    def filter_priority(row):
        fn = str(row["productFilename"])
        for i, f in enumerate(PRIORITY_FILTERS):
            if f.lower() in fn.lower():
                return i
        return len(PRIORITY_FILTERS)

    try:
        products_sorted = sorted(products, key=filter_priority)
    except Exception:
        products_sorted = list(products)

    log(f"\nTotal: {len(products_sorted)} products  |  Done: {len(completed)}  |  Failed: {len(failed)}\n")

    success_count = 0
    fail_count = 0

    for i, prod in enumerate(products_sorted):
        try:
            fname = str(prod["productFilename"])
            uri   = str(prod["dataURI"])
            size  = int(prod.get("size", 0) or 0)
        except Exception:
            continue

        if fname in completed:
            continue

        log(f"[{i+1}/{len(products_sorted)}] {fname}  ({size/1e6:.0f} MB)")

        # Determine destination — group by filter
        filter_dir = "misc"
        for f in PRIORITY_FILTERS:
            if f.lower() in fname.lower():
                filter_dir = f
                break

        dest = BASE_DIR / filter_dir / fname

        try:
            ok = download_file(uri, dest, expected_size=size)
        except KeyboardInterrupt:
            log("Interrupted by user — state saved.")
            save_state(state)
            sys.exit(0)

        if ok:
            completed.add(fname)
            failed.discard(fname)
            success_count += 1
        else:
            failed.add(fname)
            fail_count += 1
            time.sleep(10)

        state["completed"] = list(completed)
        state["failed"] = list(failed)
        save_state(state)

    log("")
    log("=" * 60)
    log(f"Done: {success_count} downloaded, {fail_count} failed")
    if fail_count:
        log("Re-run to retry failed files.")
    log("=" * 60)


if __name__ == "__main__":
    main()
